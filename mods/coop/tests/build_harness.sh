#!/bin/bash
set -euo pipefail
coop_repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
melon_source=${MELONDS_SOURCE_DIR:-/workspace/references/melonds}
melon_build=${MELONDS_BUILD_DIR:-/workspace/tools/melonds-core-build}
coop_gdb=${COOP_ENABLE_GDB:-OFF}
coop_cppflags=()
if [[ "$coop_gdb" == ON ]]; then coop_cppflags+=(-DGDBSTUB_ENABLED); fi
cmake -S "$melon_source" -B "$melon_build" -G Ninja \
  -DBUILD_QT_SDL=OFF -DENABLE_JIT=OFF -DENABLE_OGLRENDERER=OFF \
  -DENABLE_GDBSTUB="$coop_gdb" -DENABLE_LTO_RELEASE=OFF
cmake --build "$melon_build" -j 3
g++ -std=c++20 -O2 "${coop_cppflags[@]}" -I"$melon_source/src" -I"$melon_build/src" \
  "$coop_repo/mods/coop/tests/melon_test.cpp" \
  "$coop_repo/mods/coop/tests/platform.cpp" "$melon_source/src/net/LocalMP.cpp" \
  "$melon_build/src/libcore.a" "$melon_build/src/teakra/src/libteakra.a" \
  -pthread -ldl -lm -o "${COOP_HARNESS_OUTPUT:-$coop_repo/build/coop/melon-test}"
