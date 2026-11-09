#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
build_dir=${1:?Pass an empty build directory}
mkdir -p "$build_dir"
build_dir=$(cd "$build_dir" && pwd)
git clone --branch stable-35.0.2 --depth 1 https://github.com/nextcloud/android.git "$build_dir/source"
python3 "$root/clients/brand.py" android "$build_dir/source"
docker build -t umbrel-drive-android-builder -f "$root/clients/Dockerfile.android" "$root/clients"
docker run --rm --cpus 4 --memory 10g -v "$build_dir/source:/src:Z" \
  -v "$build_dir/gradle-cache:/root/.gradle:Z" umbrel-drive-android-builder \
  ./gradlew --no-daemon --max-workers=3 assembleGenericRelease
printf 'Unsigned release APKs are in %s/source/app/build/outputs/apk/generic/release/\n' "$build_dir"
