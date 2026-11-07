#!/usr/bin/env python3
"""Umbrel Drive sync and backup for Linux. Python 3.10+, standard library only."""
import argparse
import fcntl
import fnmatch
import getpass
import hashlib
import json
import os
import secrets
import ssl
import stat
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener

CHUNK = 1024**2
RECOVERY = ".umbrel-drive-recovery"
TEMP_PREFIX = ".umbrel-drive-part-"


class SyncError(Exception):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, base, token, ca_file=None, allow_loopback_http=False):
        url = urlsplit(base)
        if (url.scheme != "https" and not (allow_loopback_http and url.scheme == "http"
                and url.hostname in ("localhost", "127.0.0.1", "::1"))):
            raise SyncError("Use a trusted HTTPS Umbrel Drive URL.")
        if not url.hostname or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
            raise SyncError("Enter the app origin, including its port if required.")
        self.base = base.rstrip("/")
        self.token = token
        self.opener = build_opener(NoRedirects(), HTTPSHandler(context=ssl.create_default_context(cafile=ca_file)))

    def request(self, endpoint, method="GET", body=None, length=None, expected=None):
        headers = {"Authorization": "Bearer " + self.token}
        if length is not None:
            headers["Content-Length"] = str(length)
        if expected is not None:
            headers["X-Drive-Revision"] = str(expected)
        request = Request(self.base + "/api/" + endpoint, data=body, headers=headers, method=method)
        try:
            return self.opener.open(request, timeout=120)
        except HTTPError as error:
            with error:
                try:
                    detail = json.loads(error.read(8192)).get("error", "")
                except (ValueError, UnicodeError):
                    detail = ""
            raise SyncError(f"Drive returned HTTP {error.code}. {detail}".strip()) from error

    def json(self, *args, **kwargs):
        with self.request(*args, **kwargs) as response:
            return json.load(response)

    def put(self, path, source, expected, local_hash):
        with source.open("rb") as file, tempfile.TemporaryFile() as snapshot:
            hash_ = hashlib.sha256()
            length = 0
            for block in iter(lambda: file.read(CHUNK), b""):
                length += len(block)
                if length > 2 * 1024**3:
                    raise SyncError(f"File exceeds the 2 GiB limit: {source}")
                hash_.update(block)
                snapshot.write(block)
            if hash_.hexdigest() != local_hash:
                raise SyncError(f"Local file changed during sync: {source}")
            snapshot.seek(0)
            return self.json(endpoint(path), "PUT", body=snapshot, length=length, expected=expected)


def endpoint(path, rev=None):
    query = {"path": path}
    if rev is not None:
        query["rev"] = rev
    return "file?" + urlencode(query)


def checksum(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(CHUNK), b""):
        result.update(block)
    return result.hexdigest()


def file_hash(path):
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(mode):
        raise SyncError(f"Path is occupied by a directory, symlink, or special file: {path}")
    with path.open("rb") as stream:
        return checksum(stream)


def validate_path(path):
    if (not path or len(path.encode()) > 1024
            or any(ord(char) < 32 or char in '\\:*?"<>|' for char in path)):
        raise SyncError("Unsupported file name")
    if any(part in ("", ".", "..", RECOVERY) or part.startswith(TEMP_PREFIX) or len(part.encode()) > 255
           for part in path.split("/")):
        raise SyncError("Unsupported path component")
    return path


def local_path(root, path):
    validate_path(path)
    target = root / path
    for parent in target.parents:
        if parent == root:
            break
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise SyncError(f"Parent is occupied or a symlink: {parent}")
    return target


def scan(root, excluded):
    def fail(error):
        raise error

    found = set()
    for directory, dirs, names in os.walk(root, onerror=fail, followlinks=False):
        parent = Path(directory)
        dirs[:] = [name for name in dirs if name != RECOVERY and not name.startswith(TEMP_PREFIX)
                   and not (parent / name).is_symlink()]
        for name in names:
            path = parent / name
            if name.startswith(TEMP_PREFIX) or path.is_symlink():
                continue
            if not stat.S_ISREG(path.lstat().st_mode):
                continue
            relative = path.relative_to(root).as_posix()
            if not excluded(relative):
                found.add(relative)
    return found


def ensure_unchanged(target, expected):
    if file_hash(target) != expected:
        raise SyncError(f"Local file changed during sync: {target}")


def recover(root, path, target, expected):
    destination = local_path(root, path)
    if destination != target:
        raise SyncError("Recovery path changed")
    recovery = root / RECOVERY
    recovery.mkdir(mode=0o700, exist_ok=True)
    if recovery.is_symlink():
        raise SyncError("Recovery folder is a symlink")
    holding = recovery / secrets.token_hex(8)
    holding.mkdir(mode=0o700)
    ensure_unchanged(target, expected)
    os.rename(target, holding / target.name)
    print(f"Moved {path} to {holding.relative_to(root)}", flush=True)


def pull(client, root, remote_path, path, target, row, local, preserve=False):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=TEMP_PREFIX, delete=False) as file:
        temporary = Path(file.name)
        try:
            with client.request(endpoint(remote_path, row["id"])) as response:
                for block in iter(lambda: response.read(CHUNK), b""):
                    if file.tell() + len(block) > row["size"]:
                        raise SyncError(f"Download exceeded expected size: {path}")
                    file.write(block)
            file.flush()
            os.fsync(file.fileno())
            if file.tell() != row["size"] or file_hash(temporary) != row["hash"]:
                raise SyncError(f"Download verification failed: {path}")
            if preserve:
                recover(root, path, target, local)
                local = None
            ensure_unchanged(local_path(root, path), local)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)


def conflict_name(path, local_hash, remote_id):
    parent, separator, name = path.rpartition("/")
    # The suffix preserves provenance while keeping the UTF-8 name below 255 bytes.
    suffix = f".conflict-{local_hash[:16]}-r{remote_id}"
    short = name.encode()[:255 - len(suffix)].decode(errors="ignore")
    return parent + separator + short + suffix


def reconcile(client, root, prefix, path, local, row, previous, remote, mode):
    target = local_path(root, path)
    remote_path = prefix + path
    remote_hash = row["hash"] if row else None
    revision = row["id"] if row else 0

    if local == remote_hash:
        return [local, revision]
    if mode == "backup":
        if local is not None and (previous is None or previous[0] != local):
            result = client.put(remote_path, target, revision, local)
            return [result["hash"], result["id"]]
        return previous
    if mode == "download":
        if row and remote_hash is not None:
            pull(client, root, remote_path, path, target, row, local, preserve=local is not None)
        elif previous and previous[0] is not None and local is not None:
            recover(root, path, target, local)
        else:
            return previous
        return [remote_hash, revision]

    local_changed = previous is None or previous[0] != local
    remote_changed = previous is None or previous[1] != revision
    if local_changed and remote_changed and local is not None and remote_hash is not None:
        conflict = conflict_name(path, local, revision)
        existing = remote.get(conflict)
        if existing and existing["hash"] != local:
            raise SyncError(f"Conflict copy path is occupied: {conflict}")
        if not existing:
            saved = client.put(prefix + conflict, target, 0, local)
            if saved["hash"] != local:
                raise SyncError(f"Local file changed while uploading conflict: {path}")
        pull(client, root, remote_path, path, target, row, local)
        print(f"Preserved conflicting edit as {conflict}", flush=True)
        return [remote_hash, revision]
    if local_changed and (local is not None or not remote_changed):
        if local is None:
            # Detect a local recreation before propagating a deletion.
            ensure_unchanged(target, None)
            result = client.json(endpoint(remote_path), "DELETE", expected=revision)
        else:
            result = client.put(remote_path, target, revision, local)
        return [result["hash"], result["id"]]
    if remote_hash is None:
        if local is not None:
            recover(root, path, target, local)
    else:
        pull(client, root, remote_path, path, target, row, local)
    return [remote_hash, revision]


def save_json(path, data):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
            descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            temporary.unlink(missing_ok=True)


@contextmanager
def lock(path):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SyncError("This job is already running.")
        yield


def sync(client, config, state_path):
    root = Path(config["folder"])
    if not root.is_dir() or root.resolve() != root:
        raise SyncError("The configured local folder is missing or has been replaced by a symlink.")
    root_stat = root.stat()
    identity = [client.json("identity")["id"], str(root), root_stat.st_dev, root_stat.st_ino,
                config["remote"], config["mode"]]
    state = json.loads(state_path.read_text()) if state_path.exists() else {"identity": identity, "files": {}}
    if state["identity"] != identity:
        raise SyncError("The server, local folder, or job settings changed. Configure a new job after checking both copies.")
    prefix = config["remote"] + "/" if config["remote"] else ""
    patterns = config.get("exclude", [])

    def excluded(path):
        return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)

    local_files = scan(root, excluded)
    remote = {row["path"][len(prefix):]: row for row in client.json("files")
              if row["path"].startswith(prefix) and not excluded(row["path"][len(prefix):])}
    previous = state["files"]
    errors = []
    original = previous.copy()
    for path in sorted(local_files | remote.keys() | {key for key in previous if not excluded(key)}):
        try:
            target = local_path(root, path)
            row = remote.get(path)
            if target.is_dir() and path not in local_files and (not row or row["hash"] is None):
                continue
            local = file_hash(target)
            updated = reconcile(client, root, prefix, path, local, row, previous.get(path), remote, config["mode"])
            if updated is not None and updated != [None, 0]:
                previous[path] = updated
            else:
                previous.pop(path, None)
        except (SyncError, OSError, ValueError) as error:
            errors.append(f"{path}: {error}")
    if previous != original or not state_path.exists():
        save_json(state_path, state)
    if errors:
        raise SyncError("\n".join(errors))
    print(f"Sync complete · {len(previous)} tracked paths", flush=True)


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", default="default", help="Named sync job (default: default)")
    sub = parser.add_subparsers(dest="command", required=True)
    configure = sub.add_parser("configure", help="Save settings for a new job")
    configure.add_argument("--url", required=True)
    configure.add_argument("--folder", required=True, type=Path)
    configure.add_argument("--remote", default="", help="Remote folder, relative to My Drive")
    configure.add_argument("--mode", choices=("two-way", "backup", "download"), default="two-way")
    configure.add_argument("--exclude", action="append", default=[], help="Exclude a relative path glob, repeatable")
    configure.add_argument("--ca-file", help="PEM certificate authority for this Umbrel")
    configure.add_argument("--allow-loopback-http", action="store_true", help=argparse.SUPPRESS)
    sub.add_parser("once", help="Run one sync pass")
    watch = sub.add_parser("watch", help="Run sync repeatedly in the background")
    watch.add_argument("--interval", type=int, default=60)
    return parser.parse_args()


def main():
    args = arguments()
    if not args.job or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in args.job):
        raise SyncError("Use letters, numbers, hyphens, or underscores in job names.")
    config_base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "umbrel-drive"
    state_base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "umbrel-drive"
    config_path = config_base / (args.job + ".json")
    state_path = state_base / (args.job + ".json")
    with lock(state_base / (args.job + ".lock")):
        if args.command == "configure":
            if config_path.exists() or state_path.exists():
                raise SyncError("This job already exists. Choose another --job name.")
            root = args.folder.resolve(strict=True)
            if not root.is_dir() or root in (Path("/"), Path.home().resolve()):
                raise SyncError("Choose a dedicated sync folder.")
            for other in config_base.glob("*.json"):
                other_root = Path(json.loads(other.read_text())["folder"])
                if root == other_root or root in other_root.parents or other_root in root.parents:
                    raise SyncError("Local sync jobs must use separate, non-overlapping folders.")
            remote = validate_path(args.remote) if args.remote else ""
            token = getpass.getpass("Umbrel Drive device key: ").strip()
            config = {"folder": str(root), "url": args.url, "token": token, "remote": remote,
                      "mode": args.mode, "exclude": args.exclude, "ca_file": args.ca_file,
                      "allow_loopback_http": args.allow_loopback_http}
            Client(args.url, token, args.ca_file, args.allow_loopback_http).json("identity")
            save_json(config_path, config)
            print(f"Saved job {args.job}. Run once to sync.")
            return
        config = json.loads(config_path.read_text())
        client = Client(config["url"], config["token"], config["ca_file"], config["allow_loopback_http"])
        if args.command == "once":
            return sync(client, config, state_path)
        if args.interval < 15:
            raise SyncError("Use an interval of at least 15 seconds.")
        while True:
            try:
                sync(client, config, state_path)
            except (SyncError, OSError, URLError, ValueError) as error:
                print(error, file=sys.stderr, flush=True)
            time.sleep(args.interval)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (SyncError, OSError, URLError, ValueError) as error:
        sys.exit(str(error))
