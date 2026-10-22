#!/bin/bash
set -euo pipefail
coop_repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
melon_source=${MELONDS_SOURCE_DIR:-/workspace/references/melonds}
melon_build=${MELONDS_BUILD_DIR:-/workspace/tools/melonds-core-build}
cmake -S "$melon_source" -B "$melon_build" -G Ninja \
  -DBUILD_QT_SDL=OFF -DENABLE_JIT=OFF -DENABLE_OGLRENDERER=OFF \
  -DENABLE_GDBSTUB=OFF -DENABLE_LTO_RELEASE=OFF
cmake --build "$melon_build" -j 3
g++ -std=c++20 -O2 -I"$melon_source/src" -I"$melon_build/src" \
  "$coop_repo/mods/coop/tests/melon_test.cpp" \
  "$coop_repo/mods/coop/tests/platform.cpp" "$melon_source/src/net/LocalMP.cpp" \
  "$melon_build/src/libcore.a" "$melon_build/src/teakra/src/libteakra.a" \
  -pthread -ldl -lm -o "$coop_repo/build/coop/melon-test"
