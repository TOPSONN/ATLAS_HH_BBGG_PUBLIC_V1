#!/usr/bin/env bash
# An explicit reproduction reads [10,100) once, then [100,min(100000,N)) once.
# No remote operation is performed. Use a fresh output directory.
set -euo pipefail
[[ $# == 3 ]] || { printf 'Usage: run_phase2_local.sh audited_local.root new_output_parent phase2_build\n' >&2; exit 1; }
input_file="$(realpath "$1")"; output_parent="$(realpath -m "$2")"; build_dir="$(realpath "$3")"
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ ! -e "$output_parent" && -x "$build_dir/probe_kinematic_units" && -x "$build_dir/phase2_diagnostics" ]]
python - "$input_file" <<'PY'
import hashlib,sys,zlib
from pathlib import Path
p=Path(sys.argv[1]); data=p.read_bytes()
assert len(data)==17541818 and f'{zlib.adler32(data)&0xffffffff:08x}'=='037f48e7'
assert hashlib.sha256(data).hexdigest()=='01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7'
PY
mkdir -p "$output_parent"
"$build_dir/probe_kinematic_units" "$input_file" "$output_parent/unit_probe.csv" 10 100
python "$repo_dir/scripts/audit_phase2_units.py" "$output_parent/unit_probe.csv" "$output_parent/unit_evidence.csv" "$output_parent/unit_summary.json"
"$build_dir/phase2_diagnostics" "$input_file" "$output_parent/diagnostics" 100 100000 1 PROVISIONAL
