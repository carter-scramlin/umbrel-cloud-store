#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
build_dir=${1:?Pass an empty build directory}
mkdir -p "$build_dir"
build_dir=$(cd "$build_dir" && pwd)
git clone --branch v35.0.3 --depth 1 https://github.com/nextcloud/desktop.git "$build_dir/source"
python3 "$root/clients/brand.py" linux "$build_dir/source"
docker run --rm --cpus 4 --memory 10g \
  -v "$build_dir/source:/src:Z" \
  -e DESKTOP_CLIENT_ROOT=/src -e APPNAME='Umbrel Drive' -e EXECUTABLE_NAME=umbrel-drive \
  -e BUILD_UPDATER=OFF -e BUILDNR=1 -e VERSION_SUFFIX=umbrel-drive \
  -e CMAKE_BUILD_PARALLEL_LEVEL=4 \
  ghcr.io/nextcloud/continuous-integration-client-appimage-qt6:client-appimage-el9-6.11.2-5@sha256:24966737e70a4d815aac38e8964e034aa3e3bc39a1cfaa60894c09629fcc151f \
  bash /src/admin/linux/build-appimage.sh
