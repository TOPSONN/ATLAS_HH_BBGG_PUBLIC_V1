#!/usr/bin/env bash
# Replot native Phase 2 histograms and exact Phase 3 derived cache; zero raw reads.
set -euo pipefail
[[ $# == 2 ]] || { printf 'Usage: regenerate_standard_plots.sh build_dir new_output_dir\n' >&2; exit 1; }
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="$(realpath "$1")";output_dir="$(realpath -m "$2")"
[[ ! -e "$output_dir" && -x "$build_dir/render_phase2_histograms" && -x "$build_dir/phase3_cutflow" ]]
python - "$repo_dir" <<'PY'
import csv,hashlib,json,sys
from pathlib import Path
repo=Path(sys.argv[1])
required=['outputs/phase2_20261010T092242Z/phase2_diagnostics.root','outputs/phase2_20261010T092242Z/events.csv','metadata/phase3_selection_config.ini']
entries=[]
for phase in [2,3]:
    with (repo/f'metadata/phase{phase}_artifact_manifest.csv').open() as f:entries+=list(csv.DictReader(f))
for name in required:
    hashes={r['sha256'] for r in entries if r['path']==name}
    assert len(hashes)==1 and hashlib.sha256((repo/name).read_bytes()).hexdigest() in hashes,name
assert json.loads((repo/'metadata/phase2_run_manifest.json').read_text())['verdict']=='PASS_PROVISIONAL_RECONSTRUCTION'
PY
"$build_dir/render_phase2_histograms" "$repo_dir/outputs/phase2_20261010T092242Z/phase2_diagnostics.root" \
  "$output_dir/phase2" 63095 63058 100 63195 PROVISIONAL PINNED_RECORD_93915
bash "$repo_dir/scripts/run_phase3_cache.sh" "$repo_dir/outputs/phase2_20261010T092242Z/events.csv" "$output_dir/phase3" "$build_dir"
python "$repo_dir/scripts/validate_plot_outputs.py" "$output_dir" --expected-count 11 \
  --render-dir "$output_dir/pdf_renders" --report "$output_dir/pdf_quality.json"
