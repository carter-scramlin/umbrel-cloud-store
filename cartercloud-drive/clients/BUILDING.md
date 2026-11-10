# Building the native clients

Install Git, Python 3 with Pillow, Docker, and enough free disk space for the
upstream toolchains. Source revisions are pinned in `sources.json`; `brand.py`
refuses to modify a different revision. Android keeps upstream Java package
names internally while changing application ID, account/provider authorities,
visible branding, colors, launcher graphics, and help/source links.

```sh
./clients/build-linux.sh /path/to/empty/linux-build
./clients/build-android.sh /path/to/empty/android-build
```

The Linux build uses the pinned upstream Qt 6.11.2 AppImage build container.
The Android build uses JDK 21, Android SDK 37.0, Build Tools 36.0.0, NDK
29.0.14206865, and CMake 4.1.2. The generic flavor avoids Google Play signing
and push-service credentials. The resulting Android release is **unsigned**.

Sign updates using the original private PKCS12 signing backup. Keep the password
in a private file and pass it to `apksigner` with `--ks-pass file:PATH`; do not put
it in command history or commit it. Verify signatures with `apksigner verify
--verbose --print-certs`, and check zip alignment with `zipalign -c -P 16 4`.
The initial APK signing certificate SHA-256 fingerprint is:

`4ccb80a94c3cffae93bdc2f35e122a09a19bb6bd0917e69c9322846286f57235`

The source archives distributed alongside the binaries contain the exact local
branded client trees, excluding build caches. The Linux tree also has idempotent
mkdir calls in the packaging script and a non-cached updater URL to support local
build retries. These do not change the sync engine. Build inputs are pinned;
bit-for-bit reproducible archives are not claimed.

Upstream copyright and license notices are preserved. Consult `LICENSES/` and
`COPYING` in the source archives. Qt and other shared libraries bundled by the
upstream AppImage builder retain their original licenses; their build recipes are
in [Nextcloud continuous-integration](https://github.com/nextcloud/continuous-integration).

Android client 1.1.0 retains the original package ID and signing key. Its version
code is 350000291, above the initial upstream-derived 350000290; the visible
version is independent of the pinned Nextcloud engine version. The branding step
replaces the actual login logo and gives the splash name/tagline separate lines.
