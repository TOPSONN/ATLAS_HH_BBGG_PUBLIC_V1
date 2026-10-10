#!/usr/bin/env bash
# Study-defined unweighted preselection, reusing the pinned Phase 2 derived cache.
set -euo pipefail
[[ $# == 3 ]] || { printf 'Usage: run_phase3_cache.sh phase2_events.csv new_output_dir phase3_build\n' >&2; exit 1; }
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
input_csv="$(realpath "$1")"; output_dir="$(realpath -m "$2")"; build_dir="$(realpath "$3")"
[[ ! -e "$output_dir" && -x "$build_dir/phase3_cutflow" ]]
python - "$repo_dir" "$input_csv" <<'PY'
import csv,hashlib,json,sys
from pathlib import Path
repo,cache=map(Path,sys.argv[1:])
with (repo/'metadata/phase2_artifact_manifest.csv').open() as f:
    matches=[r for r in csv.DictReader(f) if (repo/r['path']).resolve()==cache]
assert len(matches)==1 and hashlib.sha256(cache.read_bytes()).hexdigest()==matches[0]['sha256']
with (repo/'metadata/phase2_unit_evidence.csv').open() as f:
    evidence=list(csv.DictReader(f))
assert len(evidence)==8 and all(r['classification'] in ['VERIFIED','PROVISIONAL'] for r in evidence)
assert json.loads((repo/'metadata/phase2_run_manifest.json').read_text())['verdict']=='PASS_PROVISIONAL_RECONSTRUCTION'
PY
"$build_dir/phase3_cutflow" "$input_csv" "$repo_dir/metadata/phase3_selection_config.ini" "$output_dir" PROVISIONAL
