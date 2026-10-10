#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${1:-$HOME/build/atlas_hh_phase1_$(date -u +%Y%m%dT%H%M%SZ)}"
: "${CONDA_PREFIX:?Activate atlas-hh-root first}"
[[ "${CONDA_DEFAULT_ENV:-}" == atlas-hh-root ]]
[[ "$(root-config --version)" == 6.40.04 ]]
[[ "$(root-config --cxxstandard)" == 20 ]]
compiler="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-c++"
[[ -x "$compiler" && ! -e "$build_dir" ]]
[[ "$(realpath "$(command -v root-config)")" == "$CONDA_PREFIX"/* ]]
[[ "$(realpath "$(command -v cmake)")" == "$CONDA_PREFIX"/* ]]
cmake -S "$repo_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_CXX_COMPILER="$compiler" -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DATLAS_BUILD_PHASE1=ON -DBUILD_TESTING=ON
cmake --build "$build_dir" --parallel 2
ctest --test-dir "$build_dir" --output-on-failure
printf 'PHASE1_BUILD_DIR=%s\n' "$build_dir"
