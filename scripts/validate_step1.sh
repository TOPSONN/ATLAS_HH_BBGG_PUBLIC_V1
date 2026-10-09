#!/usr/bin/env bash
# Build and validate synthetic infrastructure only; install and publish nothing.
set -euo pipefail

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
build_dir="${1:-$HOME/build/atlas_hh_bbgg_public_v1}"
[[ -n "${CONDA_PREFIX:-}" ]] || fail 'Activate atlas-hh-root first.'
[[ "$(basename -- "$CONDA_PREFIX")" == atlas-hh-root ]] || fail 'Use the dedicated atlas-hh-root environment.'
prefix="$(realpath -- "$CONDA_PREFIX")"
for command in root-config cmake ninja ctest python; do
  executable="$(command -v -- "$command")" || fail "Missing command: $command"
  [[ "$(realpath -- "$executable")" == "$prefix/"* ]] || fail "$command must come from the active environment."
done
[[ "$(realpath -- "$(root-config --prefix)")" == "$prefix" ]] || fail 'ROOT prefix differs from the compiler environment.'
[[ "$(root-config --version | tr / .)" == 6.40.04 ]] || fail 'ROOT 6.40.04 is required.'
[[ " $(root-config --cflags) " == *' -std=c++20 '* ]] || fail 'ROOT must be built with C++20.'
# The installed cxx-compiler 2.0.0 supplies binaries without setting CXX.
# Select ROOT's named compiler explicitly when CXX is absent.
CXX="${CXX:-$prefix/bin/$(root-config --cxx)}"
compiler="$(command -v -- "$CXX")" || fail "Cannot locate CXX=$CXX"
compiler="$(realpath -- "$compiler")"
[[ "$compiler" == "$prefix/"* ]] || fail "CXX must come from the active environment: $compiler"

build_dir="$(realpath -m -- "$build_dir")"
[[ "$build_dir" != "$source_dir" && "$build_dir" != "$source_dir/"* ]] || fail 'Place build products outside the source repository.'
mkdir -p -- "$build_dir"
evidence_dir="$(mktemp -d "$build_dir/step1_validation_$(date -u +%Y%m%dT%H%M%SZ).XXXXXX")"
if [[ -f "$build_dir/CMakeCache.txt" ]]; then
  cached_compiler="$(sed -n -E 's/^CMAKE_CXX_COMPILER:(FILEPATH|STRING)=//p' "$build_dir/CMakeCache.txt")"
  cached_source="$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' "$build_dir/CMakeCache.txt")"
  [[ -n "$cached_compiler" && "$(realpath -- "$cached_compiler")" == "$compiler" ]] \
    || fail 'Existing build uses another compiler; choose a new build directory.'
  [[ "$cached_source" == "$source_dir" ]] || fail 'Existing build belongs to another source tree; choose a new build directory.'
fi

{
  printf 'DATE_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'SOURCE_DIR=%s\nBUILD_DIR=%s\nCONDA_PREFIX=%s\n' "$source_dir" "$build_dir" "$prefix"
  printf 'ROOT_VERSION=%s\nROOT_PREFIX=%s\nROOT_CFLAGS=%s\n' \
    "$(root-config --version)" "$(root-config --prefix)" "$(root-config --cflags)"
  printf 'ROOT_BUILD_COMPILER=%s\nACTIVATED_CXX=%s\n' "$(root-config --cxx)" "$compiler"
  "$compiler" --version
  cmake --version
  printf 'NINJA_VERSION=%s\n' "$(ninja --version)"
  python - <<'PY'
import json
import os
from pathlib import Path
prefix = Path(os.environ['CONDA_PREFIX'])
names = {'root_base', 'root_cxx_standard', 'cxx-compiler', 'gxx_impl_linux-64',
         'gcc_impl_linux-64', 'libstdcxx', 'libgcc', 'sysroot_linux-64', 'cmake', 'ninja'}
records = [json.loads(p.read_text()) for p in (prefix / 'conda-meta').glob('*.json')]
for record in sorted(records, key=lambda r: r['name']):
    if record['name'] in names:
        print(f"PACKAGE={record['name']}={record['version']}={record['build']}")
PY
} | tee "$evidence_dir/step1_runtime_environment.txt"

cmake -S "$source_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_CXX_COMPILER="$compiler" -DCMAKE_PREFIX_PATH="$prefix" \
  -DROOT_DIR="$prefix/cmake" 2>&1 | tee "$evidence_dir/step1_configure.log"

python - "$build_dir" "$compiler" "$prefix" <<'PY'
import json
import shlex
import sys
from pathlib import Path
build, compiler, prefix = map(Path, sys.argv[1:])
facts = dict(line.split('=', 1) for line in (build / 'step1_cmake_environment.txt').read_text().splitlines())
assert Path(facts['CXX_COMPILER']).resolve() == compiler, facts
assert facts['ROOT_CXX_STANDARD'] == facts['PROJECT_CXX_STANDARD'] == '20', facts
assert facts['CXX_STANDARD_REQUIRED'] == 'ON' and facts['CXX_EXTENSIONS'] == 'OFF', facts
assert Path(facts['ROOT_DIR']).resolve().is_relative_to(prefix), facts
commands = json.loads((build / 'compile_commands.json').read_text())
assert len(commands) == 4, f'Expected four compiled executables, got {len(commands)}'
for entry in commands:
    arguments = entry.get('arguments') or shlex.split(entry['command'])
    assert Path(arguments[0]).resolve() == compiler, arguments
    assert [a for a in arguments if a.startswith('-std=')] == ['-std=c++20'], arguments
    print(f"PASS compiler/standard: {Path(entry['file']).name} -> {compiler} -std=c++20")
# ROOT's installed build metadata names a compiler executable, not its version.
root_command = __import__('subprocess').check_output(['root-config', '--cxx'], text=True).strip()
root_compiler = Path(shlex.split(root_command)[0]).name
assert (prefix / 'bin' / root_compiler).resolve() == compiler, f'ROOT compiler {root_compiler} differs from project compiler {compiler}'
print(f'PASS project uses the compiler executable named by ROOT: {root_compiler}')
PY
cp -- "$build_dir/step1_cmake_environment.txt" "$build_dir/compile_commands.json" \
  "$build_dir/CMakeCache.txt" "$evidence_dir/"

cmake --build "$build_dir" --parallel 2 2>&1 | tee "$evidence_dir/step1_build.log"

python - "$build_dir" "$prefix" <<'PY' | tee "$evidence_dir/step1_linkage.log"
import re
import subprocess
import sys
from pathlib import Path
build, prefix = map(Path, sys.argv[1:])
seen = set()
for name in ('root_smoke', 'test_root_io', 'test_rdataframe', 'test_root_statistics'):
    result = subprocess.run(['ldd', str(build / name)], capture_output=True, text=True, check=True)
    assert 'not found' not in result.stdout, result.stdout
    print(f'EXECUTABLE={name}\n{result.stdout}')
    for line in result.stdout.splitlines():
        match = re.match(r'\s*(lib\S+)\s+=>\s+(\S+)', line)
        if not match:
            continue
        library, path = match.groups()
        if library.startswith(('libstdc++', 'libgcc_s')) or (prefix / 'lib' / library).exists():
            assert Path(path).resolve().is_relative_to(prefix), f'Library outside environment: {line}'
        seen.add(library)
for component in ('Core', 'RIO', 'Tree', 'Hist', 'ROOTDataFrame', 'RooFit', 'RooStats'):
    assert any(s == f'lib{component}.so' or s.startswith(f'lib{component}.so.') for s in seen), \
        f'Missing linked ROOT component: {component}'
assert any(s.startswith('libstdc++') for s in seen) and any(s.startswith('libgcc_s') for s in seen)
print('PASS ROOT components and C++ runtimes resolve inside the active environment.')
PY

# Batch mode is set in each executable; DISPLAY is deliberately absent for validation.
env -u DISPLAY "$build_dir/root_smoke" 2>&1 | tee "$evidence_dir/step1_smoke.log"
env -u DISPLAY ctest --test-dir "$build_dir" --verbose --output-on-failure \
  2>&1 | tee "$evidence_dir/step1_ctest.log"
cp -- "$build_dir/Testing/Temporary/LastTest.log" "$evidence_dir/"
printf 'PASS Step 1 build, smoke, compiler/linkage checks, and three CTest tests.\n'
printf 'Evidence: %s\nSynthetic ROOT outputs: %s\n' "$evidence_dir" "$build_dir"
