#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
build_dir="${1:?Choose a new build directory outside the source tree}"
: "${CONDA_PREFIX:?Activate atlas-hh-root first}"
[[ "${CONDA_DEFAULT_ENV:-}" == atlas-hh-root && ! -e "$build_dir" ]]
python -c 'if not __debug__: raise RuntimeError("Python assertion checks must be enabled")'
prefix="$(realpath "$CONDA_PREFIX")"
build_dir="$(realpath -m "$build_dir")"
[[ "$build_dir" != "$repo_dir" && "$build_dir" != "$repo_dir/"* ]]
for program in root-config cmake ninja ctest python; do
  [[ "$(realpath "$(command -v "$program")")" == "$prefix/"* ]]
done
[[ "$(realpath "$(root-config --prefix)")" == "$prefix" ]]
[[ "$(root-config --version)" == 6.40.04 && "$(root-config --cxxstandard)" == 20 ]]
compiler="$prefix/bin/$(root-config --cxx)"
[[ -x "$compiler" ]]
python -B "$repo_dir/scripts/freeze_phase5_baseline.py" "$repo_dir/metadata/phase5_baseline_preservation.json" --verify
source_snapshot="$(mktemp "$repo_dir/.local/phase5_test_sources.XXXXXX.json")"
python - "$repo_dir" "$source_snapshot" <<'PY'
import hashlib,json,sys
from pathlib import Path
repo,output=map(Path,sys.argv[1:])
files=[]
for directory in ('apps','include','src','tests','scripts'):
    files.extend(p for p in (repo/directory).rglob('*') if p.is_file() and p.suffix in ('.h','.cxx','.py','.sh'))
files.extend(repo/name for name in ('CMakeLists.txt','metadata/phase3_selection_config.ini'))
output.write_text(json.dumps({p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sorted(files)},indent=2)+'\n')
PY
cmake -S "$repo_dir" -B "$build_dir" -G Ninja -DCMAKE_CXX_COMPILER="$compiler" \
  -DCMAKE_PREFIX_PATH="$prefix" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DBUILD_TESTING=ON \
  -DATLAS_BUILD_PHASE1=ON -DATLAS_BUILD_PHASE2=ON -DATLAS_BUILD_PHASE3=ON -DATLAS_BUILD_PHASE4=ON -DATLAS_BUILD_PHASE5=ON
cmake --build "$build_dir" --parallel 2
python - "$build_dir" "$compiler" "$prefix" <<'PY'
import json,shlex,sys,subprocess
from pathlib import Path
build,compiler,prefix=map(Path,sys.argv[1:])
commands=json.loads((build/'compile_commands.json').read_text())
for command in commands:
    args=command.get('arguments') or shlex.split(command['command'])
    assert Path(args[0]).resolve()==compiler.resolve()
    assert [a for a in args if a.startswith('-std=')]==['-std=c++20']
linkages={}
for app in ('root_smoke','phase4_mc_reconstruction','phase4_numerical_regression','test_cartesian_stability',
            'test_normalization','test_shape_comparison','test_control_regions','phase5_region_inventory'):
    linkage=subprocess.check_output(['ldd',str(build/app)],text=True)
    assert 'not found' not in linkage
    for line in linkage.splitlines():
        if any(name in line for name in ('libCore.so','libRIO.so','libTree.so','libHist.so','libstdc++.so','libgcc_s.so')):
            path=line.split('=>',1)[1].strip().split()[0]
            assert Path(path).resolve().is_relative_to(prefix.resolve()),line
    linkages[app]=linkage
    print('PASS conda compiler/C++20/ROOT linkage:',app)
(build/'phase5_linkage.json').write_text(json.dumps({'compiler':str(compiler),'prefix':str(prefix),'linked':linkages},indent=2)+'\n')
PY
env -u DISPLAY ctest --test-dir "$build_dir" --verbose --output-on-failure --output-junit "$build_dir/phase5_ctest.xml"
python - "$repo_dir" "$source_snapshot" "$build_dir" <<'PY'
import hashlib,json,sys
from pathlib import Path
repo,snapshot,build=map(Path,sys.argv[1:])
raw=snapshot.read_bytes()
for name,expected in json.loads(raw).items():
    assert hashlib.sha256((repo/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected,name
(build/'phase5_test_source_hashes.json').write_bytes(raw)
print('PASS source identity before/after compilation and CTest')
PY
python -B "$repo_dir/scripts/freeze_phase5_baseline.py" "$repo_dir/metadata/phase5_baseline_preservation.json" --verify
printf 'PHASE5_BUILD_DIR=%s\n' "$build_dir"
