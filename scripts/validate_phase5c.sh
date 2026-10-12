#!/usr/bin/env bash
# Offline regressions only; no input acquisition or physical-closure claim.
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
build_dir="${1:-$HOME/build/atlas_phase5c}"
[[ -n "${CONDA_PREFIX:-}" && "$(basename -- "$CONDA_PREFIX")" == atlas-hh-root ]] || {
  printf 'Activate the existing atlas-hh-root environment.\n' >&2; exit 1;
}
prefix="$(realpath -- "$CONDA_PREFIX")"
for tool in root-config cmake ninja ctest python; do
  [[ "$(realpath -- "$(command -v -- "$tool")")" == "$prefix/"* ]] || exit 1
done
[[ "$(root-config --version | tr / .)" == 6.40.04 ]] || exit 1
[[ " $(root-config --cflags) " == *' -std=c++20 '* ]] || exit 1
[[ "$(realpath -- "$(root-config --prefix)")" == "$prefix" ]] || exit 1
compiler="$(realpath -- "$prefix/bin/$(root-config --cxx)")"
[[ "$compiler" == "$prefix/"* ]] || exit 1
build_dir="$(realpath -m -- "$build_dir")"
[[ "$build_dir" != "$source_dir" && "$build_dir" != "$source_dir/"* ]] || exit 1
if [[ -f "$build_dir/CMakeCache.txt" ]]; then
  cached_compiler="$(sed -n -E 's/^CMAKE_CXX_COMPILER:(FILEPATH|STRING)=//p' "$build_dir/CMakeCache.txt")"
  cached_source="$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' "$build_dir/CMakeCache.txt")"
  [[ -n "$cached_compiler" && "$(realpath -- "$cached_compiler")" == "$compiler" ]] || exit 1
  [[ "$cached_source" == "$source_dir" ]] || exit 1
fi
cmake -S "$source_dir" -B "$build_dir" -G Ninja -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_COMPILER="$compiler" -DCMAKE_PREFIX_PATH="$prefix" \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=ON \
  -DATLAS_BUILD_PHASE1=ON -DATLAS_BUILD_PHASE2=ON -DATLAS_BUILD_PHASE3=ON \
  -DATLAS_BUILD_PHASE4=ON -DATLAS_BUILD_PHASE5=ON -DATLAS_BUILD_PHASE5B=ON \
  -DATLAS_BUILD_PHASE5C=ON
cmake --build "$build_dir" --parallel 4
ctest --test-dir "$build_dir" --output-on-failure --output-junit "$build_dir/ctest.xml"
