#!/usr/bin/env bash
# Add native alternative views from pinned V2 per-figure histogram objects only.
set -euo pipefail
[[ $# == 2 || $# == 3 ]] || { printf 'Usage: render_alternative_mass_plots.sh build_dir new_output_dir [ORIGINAL_DATA_POINTS|HATCHED_STEP|BOTH]\n' >&2; exit 1; }
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="$(realpath "$1")";output_dir="$(realpath -m "$2")";mode="${3:-ORIGINAL_DATA_POINTS}"
[[ ! -e "$output_dir" && -x "$build_dir/render_histogram_modes" ]]
python - "$repo_dir" "$build_dir" "$output_dir" "$mode" <<'PY'
import csv,hashlib,json,subprocess,sys
from pathlib import Path
import ROOT
repo,build,output=map(Path,sys.argv[1:4]);mode=sys.argv[4]
assert mode in ('ORIGINAL_DATA_POINTS','HATCHED_STEP','BOTH')
assert ROOT.gROOT.GetVersion()=='6.40.04'
ROOT.gROOT.SetBatch(True)
with (repo/'metadata/atlas_publication_v2_artifact_manifest.csv').open() as f:
    manifest=list(csv.DictReader(f))
sources=[('phase2','m_gg',None),('phase3','m_gg_preselection',(105.,160.))]
prepared=[]
for phase,name,support in sources:
    stem=repo/'outputs/atlas_publication_v2_20261011'/phase/name
    for ext in ('.root','.plot.json'):
        path=Path(str(stem)+ext)
        manifest_path=path.relative_to(repo).as_posix()
        # Sidecar in the tracked V2 export is an identical copy of the native sidecar.
        if ext=='.plot.json':manifest_path=f'reports/figures/atlas_v2/{phase}/{name}.plot.json'
        rows=[r for r in manifest if r['path']==manifest_path]
        assert len(rows)==1 and path.is_file(),manifest_path
        data=path.read_bytes()
        assert len(data)==int(rows[0]['size_bytes']) and hashlib.sha256(data).hexdigest()==rows[0]['sha256'],manifest_path
    metadata=json.loads(Path(str(stem)+'.plot.json').read_text())
    assert metadata['sample_kind']=='DATA' and metadata['weighting']=='Raw unweighted counts'
    assert metadata['record']=='93915' and metadata['period']=='2015 periodD'
    assert metadata['unit_status']=='PROVISIONAL' and metadata['energy_tev']==13
    with ROOT.TFile.Open(str(stem)+'.root','READ') as source:
        assert source and not source.IsZombie()
        assert json.loads(source.Get('atlas_plot_metadata').GetTitle())==metadata
        histogram=source.Get(name)
        assert histogram and histogram.ClassName()=='TH1D'
        assert (histogram.GetNbinsX(),histogram.GetXaxis().GetXmin(),histogram.GetXaxis().GetXmax())==((80,0,400) if phase=='phase2' else (70,100,170))
    if support:
        config=repo/'metadata/phase3_selection_config.ini'
        config_rows=[r for r in manifest if r['path']=='metadata/phase3_selection_config.ini']
        assert len(config_rows)==1 and hashlib.sha256(config.read_bytes()).hexdigest()==config_rows[0]['sha256']
        settings=dict(line.split('=',1) for line in (repo/'metadata/phase3_selection_config.ini').read_text().splitlines() if line and not line.startswith('#'))
        assert (float(settings['diphoton_mass_low_gev']),float(settings['diphoton_mass_high_gev']))==support
        # Existing inclusive [105,160] selection is unchanged. Only full display
        # bins inside these bounds get a band; excluded bins must be structural zeros.
    display_support=support if mode!='ORIGINAL_DATA_POINTS' else None
    args=[str(build/'render_histogram_modes'),str(stem)+'.root',name,str(output/phase),mode,
          metadata['record'],metadata['period'],metadata['selection'],metadata['unit_status'],
          *(str(metadata[key]) for key in ('inspected','accepted','start','end')),str(metadata['energy_tev']),
          *((str(v) for v in display_support) if display_support else ('NONE','NONE')),'PINNED_NATIVE_PLOT_SOURCE']
    prepared.append(args)
for args in prepared:subprocess.run(args,check=True)
expected=4 if mode=='BOTH' else 2
subprocess.run([sys.executable,str(repo/'scripts/validate_plot_outputs.py'),str(output),'--expected-count',str(expected),
                '--render-dir',str(output/'pdf_renders'),'--report',str(output/'pdf_quality.json')],check=True)
print('PASS pinned native mass rendering; no remote inputs and no collision event reads')
PY
