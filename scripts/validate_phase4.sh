#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${1:?Choose a new build directory outside the source tree}"
: "${CONDA_PREFIX:?Activate atlas-hh-root first}"
[[ "${CONDA_DEFAULT_ENV:-}" == atlas-hh-root && ! -e "$build_dir" ]]
[[ "$(root-config --version)" == 6.40.04 && "$(root-config --cxxstandard)" == 20 ]]
compiler="$CONDA_PREFIX/bin/$(root-config --cxx)"
[[ -x "$compiler" && "$(realpath "$(command -v cmake)")" == "$CONDA_PREFIX"/* ]]
cmake -S "$repo_dir" -B "$build_dir" -G Ninja -DCMAKE_CXX_COMPILER="$compiler" \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=ON \
  -DATLAS_BUILD_PHASE1=ON -DATLAS_BUILD_PHASE2=ON -DATLAS_BUILD_PHASE3=ON -DATLAS_BUILD_PHASE4=ON
cmake --build "$build_dir" --parallel 2
python - "$build_dir" "$compiler" "$CONDA_PREFIX" <<'PY'
import json,shlex,sys,subprocess
from pathlib import Path
build,compiler,prefix=map(Path,sys.argv[1:])
commands=json.loads((build/'compile_commands.json').read_text())
for c in commands:
    args=c.get('arguments') or shlex.split(c['command'])
    assert Path(args[0]).resolve()==compiler.resolve()
    assert [a for a in args if a.startswith('-std=')]==['-std=c++20']
for app in ('phase4_mc_reconstruction','phase4_numerical_regression','test_mc_events','test_mc_matching','test_synthetic_matching','test_cartesian_stability'):
    linkage=subprocess.check_output(['ldd',str(build/app)],text=True)
    assert 'not found' not in linkage
    for line in linkage.splitlines():
        if any(name in line for name in ('libCore.so','libRIO.so','libTree.so','libstdc++.so','libgcc_s.so')):
            path=line.split('=>',1)[1].strip().split()[0]
            assert Path(path).resolve().is_relative_to(prefix.resolve()),line
    print('PASS conda compiler/C++20/ROOT linkage:',app)
PY
env -u DISPLAY ctest --test-dir "$build_dir" --verbose --output-on-failure
printf 'PHASE4_BUILD_DIR=%s\n' "$build_dir"
