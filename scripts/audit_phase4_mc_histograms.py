#!/usr/bin/env python3
"""Compare actual old/new native MC TH1s with both V2 harness versions.

Only existing histogram files are read; no native ROOT event is read and no
ROOT file or figure is written. The output JSON must be a new path.
"""
import argparse
import json
from pathlib import Path

from audit_phase4_recovery_data import require, root_histograms, sha

DSIDS = (343981, 346214, 423103)
NAMES = {'mc_m_gg', 'mc_m_jj', 'mc_deltaR_gg', 'mc_deltaR_jj',
         'mc_photon_pt', 'mc_jet_pt', 'mc_m_gg_C9', 'mc_m_jj_C9',
         'mc_photon_pt_C9', 'mc_jet_pt_C9'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('new_run_directory', type=Path)
    parser.add_argument('new_audit_json', type=Path)
    args = parser.parse_args()
    require(not args.new_audit_json.exists(), 'Refusing to overwrite any audit output')
    repo = Path(__file__).resolve().parents[1]
    new = args.new_run_directory.resolve()
    sources = {}
    for dsid in DSIDS:
        sources[dsid] = {
            'original': repo / 'outputs/phase4_v1' / str(dsid) / 'reconstruction/histograms.root',
            'corrected': new / str(dsid) / 'reconstruction/histograms.root',
            'harness': new / str(dsid) / 'regression/histograms.root'}
    require(all(path.is_file() for sample in sources.values() for path in sample.values()),
            'Actual native MC histogram evidence missing')
    files = {str(path): {'bytes': path.stat().st_size, 'sha256': sha(path)}
             for sample in sources.values() for path in sample.values()}
    import ROOT
    ROOT.gROOT.SetBatch(True)
    require(ROOT.gROOT.GetVersion() == '6.40.04', 'Wrong ROOT environment')
    audits = {}
    for dsid, paths in sources.items():
        harness = root_histograms(ROOT, paths['harness'])
        require(set(harness) == {name + '__' + version for name in NAMES for version in ('original', 'corrected')},
                'Wrong harness histogram inventory for DSID ' + str(dsid))
        native = {version: root_histograms(ROOT, paths[version]) for version in ('original', 'corrected')}
        version_checks = {}
        for version, histograms in native.items():
            require(set(histograms) == NAMES, 'Wrong native histogram inventory for DSID ' + str(dsid) + '/' + version)
            comparisons = {}
            for name in sorted(NAMES):
                actual, reference = histograms[name], harness[name + '__' + version]
                require(actual == reference,
                        'Native bins/errors/edges/entries differ from harness: ' + str(dsid) + '/' + version + '/' + name)
                comparisons[name] = {'status': 'PASS', 'bins_including_flow': actual['bins'] + 2,
                                     'axis_edges_checked': len(actual['edges']), 'entries': actual['entries'],
                                     'full_native_histogram': actual}
            version_checks[version] = {'status': 'PASS', 'histograms': len(comparisons),
                'bins_including_flow': sum(h['bins_including_flow'] for h in comparisons.values()), 'comparisons': comparisons}
        changes = []
        for name in sorted(NAMES):
            old, fresh = native['original'][name], native['corrected'][name]
            require(old['bins'] == fresh['bins'] and old['edges'] == fresh['edges'],
                    'Histogram binning changed for DSID ' + str(dsid) + '/' + name)
            for index, (a, b) in enumerate(zip(old['contents_with_flow'], fresh['contents_with_flow'])):
                if a != b:
                    changes.append({'histogram': name, 'bin': index,
                        'bin_class': 'UNDERFLOW' if index == 0 else ('OVERFLOW' if index == old['bins'] + 1 else 'REGULAR'),
                        'original_content': a, 'corrected_content': b, 'delta': b - a})
        audits[str(dsid)] = {'status': 'PASS', 'versions': version_checks, 'changed_bins': changes,
                            'changed_bin_count': len(changes)}
    for sample in sources.values():
        for path in sample.values():
            require(sha(path) == files[str(path)]['sha256'], 'Read-only MC histogram input changed during audit')
    evidence = {'schema': 'phase4-v2-independent-native-mc-histogram-audit', 'status': 'PASS',
        'root_version': ROOT.gROOT.GetVersion(), 'dsids': list(DSIDS), 'new_native_event_reads': 0,
        'comparison_policy': 'exact native TH1 bin contents and errors including underflow/overflow, all X-axis edges and GetEntries; all ten histogram names required for every DSID/version',
        'files': files, 'samples': audits, 'preservation': 'PASS input hashes unchanged before/after read-only audit',
        'normalization': 'RAW_UNWEIGHTED; no generator weights, scale factors or luminosity applied', 'figures_generated': False}
    args.new_audit_json.parent.mkdir(parents=True, exist_ok=True)
    with args.new_audit_json.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(evidence, output, indent=2, allow_nan=False)
        output.write('\n')
    print('PASS independent MC native histograms: 3 DSIDs x 10 histograms x 2 versions; full bins/errors/edges/entries; audit=' + str(args.new_audit_json))


if __name__ == '__main__':
    main()
