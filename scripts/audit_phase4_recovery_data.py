#!/usr/bin/env python3
"""Independently audit frozen DATA caches against the V2 native regression.

Read-only CSV/JSON/ROOT inputs; exactly one new JSON output. No plots or ROOT
files are written. Invoke inside atlas-hh-root from the repository workspace.
"""
import argparse
import collections
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path

BASE = 'd823593b42889592897263819138170470f4dc47'
DATA_SHA = '01bfa7cee25c7f32c3701e458d171f65def834d96e6071e119532421a64bd5f7'
PHASE2_NAMES = {'photon_pt', 'photon_eta', 'jet_pt', 'jet_eta', 'm_gg', 'm_jj', 'deltaR_gg'}
SELECTED = {'m_gg_preselection': (70, 100, 170, ('m_gg',)),
            'm_jj_preselection': (80, 0, 800, ('m_jj',)),
            'photon_pt_selected': (60, 0, 300, ('photon1_pt', 'photon2_pt')),
            'jet_pt_selected': (60, 0, 300, ('jet1_pt', 'jet2_pt'))}
KINEMATIC = ('photon1_pt', 'photon2_pt', 'photon1_eta', 'photon2_eta',
             'jet1_pt', 'jet2_pt', 'jet1_eta', 'jet2_eta', 'm_gg', 'm_jj',
             'deltaEta_gg', 'deltaPhi_gg', 'deltaR_gg', 'deltaEta_jj', 'deltaPhi_jj', 'deltaR_jj')
FLAGS = ('p1_tight_id', 'p2_tight_id', 'p1_tight_iso', 'p2_tight_iso')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def records(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)),
                'Missing/duplicate CSV header: ' + str(path))
        rows = list(reader)
    require(all(None not in row and all(v is not None for v in row.values()) for row in rows),
            'Malformed CSV rows: ' + str(path))
    return rows


def numeric(text):
    if text == '':
        return None
    value = float(text)
    require(math.isfinite(value), 'Nonfinite encoded numeric value: ' + text)
    return value


def same_number(a, b):
    # Formatting may differ (17 versus 21 significant digits); require exact
    # binary64 equality after parsing, with no numerical tolerance introduced.
    return numeric(a) == numeric(b)


def identifier(row):
    return {k: int(row[k]) for k in ('entry', 'run', 'event')}


def index_events(rows):
    indexed = {}
    identities = set()
    for row in rows:
        entry = int(row['entry'])
        require(entry not in indexed, 'Duplicate DATA entry ' + str(entry))
        identity = (int(row['run']), int(row['event']))
        require(identity not in identities, 'Duplicate run/event identity ' + str(identity))
        identities.add(identity)
        indexed[entry] = row
    require(list(indexed) == list(range(100, 63195)), 'DATA interval/order is not exactly [100,63195)')
    return indexed


def compare_cache(cache, harness, version):
    mismatches = []
    direct = ('entry', 'run', 'event', 'photon_n', 'jet_n', 'roundoff_objects') + FLAGS
    mapped = ('valid',) + KINEMATIC
    comparisons = 0
    for entry, row in cache.items():
        other = harness[entry]
        require(other['mode'] == 'DATA' and other['dsid'] == '0', 'Non-DATA harness identity')
        for field in direct:
            comparisons += 1
            if not same_number(row[field], other[field]):
                mismatches.append({**identifier(row), 'field': field, 'cache': row[field], 'harness': other[field]})
        for field in mapped:
            comparisons += 1
            if not same_number(row[field], other[version + '_' + field]):
                mismatches.append({**identifier(row), 'field': field, 'cache': row[field], 'harness': other[version + '_' + field]})
        comparisons += 1
        if row['issue'] != other[version + '_issue']:
            mismatches.append({**identifier(row), 'field': 'issue', 'cache': row['issue'], 'harness': other[version + '_issue']})
    return {'status': 'PASS' if not mismatches else 'FAIL', 'entries': len(cache),
            'exact_field_comparisons': comparisons, 'mismatches': mismatches}


def configuration(path):
    result = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        name, value = line.split('=', 1)
        require(name not in result, 'Duplicate selection configuration')
        result[name] = value if name == 'definition_version' else float(value)
    require(len(result) == 10 and result['definition_version'] == 'study-preselection-v1', 'Unexpected configuration')
    return result


def selection(row, c):
    np, nj = int(row['photon_n']), int(row['jet_n'])
    pt = [numeric(row[k]) for k in ('photon1_pt', 'photon2_pt')]
    pe = [numeric(row[k]) for k in ('photon1_eta', 'photon2_eta')]
    jt = [numeric(row[k]) for k in ('jet1_pt', 'jet2_pt')]
    je = [numeric(row[k]) for k in ('jet1_eta', 'jet2_eta')]
    mgg, mjj = numeric(row['m_gg']), numeric(row['m_jj'])
    valid = row['valid'] == '1' and np >= 0 and nj >= 0
    for n, p, e, mass in ((np, pt, pe, mgg), (nj, jt, je, mjj)):
        valid = valid and all(p[i] is not None and p[i] >= 0 and e[i] is not None for i in range(min(n, 2)))
        if n >= 2:
            valid = valid and mass is not None and mass >= 0 and p[0] is not None and p[1] is not None and p[0] >= p[1]
    acceptance = np >= 2 and all(e is not None and abs(e) < c['photon_abs_eta_max'] and
                    not c['photon_crack_low'] < abs(e) < c['photon_crack_high'] for e in pe)
    individual = [True, valid, np >= 2,
                  np >= 2 and pt[0] is not None and pt[0] > c['photon_leading_pt_min_gev'],
                  np >= 2 and pt[1] is not None and pt[1] > c['photon_subleading_pt_min_gev'], acceptance,
                  np >= 2 and mgg is not None and c['diphoton_mass_low_gev'] <= mgg <= c['diphoton_mass_high_gev'],
                  nj >= 2, nj >= 2 and all(p is not None and p > c['jet_pt_min_gev'] for p in jt),
                  nj >= 2 and all(e is not None and abs(e) < c['jet_abs_eta_max'] for e in je)]
    cumulative = []
    for passed in individual:
        cumulative.append(bool(passed and (not cumulative or cumulative[-1])))
    return cumulative


def histogram(h):
    n = int(h.GetNbinsX())
    return {'bins': n, 'edges': [float(h.GetXaxis().GetBinLowEdge(i)) for i in range(1, n + 2)],
            'contents_with_flow': [float(h.GetBinContent(i)) for i in range(n + 2)],
            'errors_with_flow': [float(h.GetBinError(i)) for i in range(n + 2)], 'entries': float(h.GetEntries())}


def root_histograms(ROOT, path):
    handle = ROOT.TFile.Open(str(path), 'READ')
    require(handle and not handle.IsZombie(), 'Cannot read native ROOT histograms: ' + str(path))
    result = {}
    try:
        for key in handle.GetListOfKeys():
            obj = key.ReadObj()
            if obj.InheritsFrom('TH1'):
                require(obj.GetDimension() == 1 and key.GetName() not in result, 'Unexpected duplicate/multidimensional histogram')
                result[key.GetName()] = histogram(obj)
    finally:
        handle.Close()
    return result


def hist_inventory(h):
    contents = h['contents_with_flow']
    return {'filled_values': h['entries'], 'in_range': sum(contents[1:-1]),
            'underflow': contents[0], 'overflow': contents[-1]}


def check_inventory(path, hists):
    rows = records(path)
    require(len(rows) == len(hists) and {r['name'] for r in rows} == set(hists), 'Histogram inventory membership mismatch: ' + str(path))
    for row in rows:
        expected = hist_inventory(hists[row['name']])
        require(all(numeric(row[k]) == value for k, value in expected.items()), 'Inventory moments mismatch: ' + str(path) + '/' + row['name'])
    return {name: hist_inventory(h) for name, h in hists.items()}


def selected_audit(ROOT, cache, harness, version, c, phase3, selected_hists):
    counts = [0] * 10
    flags = [0, 0, 0]
    memory = {name: ROOT.TH1D('data_audit_' + version + '_' + name, '', *definition[:3]) for name, definition in SELECTED.items()}
    for h in memory.values():
        h.SetDirectory(0)
    selected_ids = []
    for entry, row in cache.items():
        cuts = selection(row, c)
        require(all(int(harness[entry][version + '_C' + str(i)]) == int(p) for i, p in enumerate(cuts)), 'Independent selection differs at entry ' + str(entry))
        counts = [n + int(p) for n, p in zip(counts, cuts)]
        if not cuts[-1]:
            continue
        selected_ids.append(identifier(row))
        values = [numeric(row[k]) for k in FLAGS]
        flags[2] += any(v is None for v in values)
        flags[0] += values[0] == values[1] == 1
        flags[1] += all(v == 1 for v in values)
        for name, definition in SELECTED.items():
            for field in definition[3]:
                memory[name].Fill(numeric(row[field]))
    independent = {name: histogram(h) for name, h in memory.items()}
    require(independent == selected_hists, 'Independent selected-event full bins differ from harness ' + version)
    rows = records(phase3 / 'cutflow.csv')
    require(len(rows) == 10, 'Unexpected Phase3 cutflow rows')
    for i, row in enumerate(rows):
        before = counts[i - 1] if i else counts[0]
        require(row['selection_name'].startswith('C' + str(i) + '_') and row['definition_version'] == c['definition_version'], 'Cut identity/version mismatch')
        require(int(row['events_before']) == before and int(row['events_after']) == counts[i] and int(row['rejected_events']) == before - counts[i], 'Actual Phase3 cutflow differs')
        require(numeric(row['conditional_fraction']) == (counts[i] / before if before else None) and numeric(row['cumulative_fraction']) == counts[i] / counts[0], 'Cutflow fractions differ')
        require(row['validation_status'] == 'PROVISIONAL_EXPLORATORY', 'Phase3 scientific status changed')
    optional = records(phase3 / 'optional_photon_flags.csv')
    require(len(optional) == 2, 'Unexpected optional-flag rows')
    for i, row in enumerate(optional):
        require(row['diagnostic'] == ('raw_tightID_both', 'raw_tightID_and_tightIso_both')[i], 'Optional-flag name changed')
        require(int(row['base_C9_events']) == counts[9] and int(row['flag_true_events']) == flags[i] and int(row['missing_flag_events']) == flags[2], 'Optional flags disagree')
    inventory = check_inventory(phase3 / 'histogram_inventory.csv', independent)
    return {'status': 'PASS', 'counts': counts, 'optional_flag_counts': flags, 'selected_event_ids': selected_ids,
            'histogram_inventory': inventory, 'independent_selected_bin_comparison': 'PASS',
            'phase3_native_file_check': 'NOT_AVAILABLE_NO_PHASE3_ROOT_FILE; persisted inventory checked against independent selected fills and harness native bins'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('new_data_directory', type=Path)
    parser.add_argument('new_audit_json', type=Path)
    args = parser.parse_args()
    require(not args.new_audit_json.exists(), 'Refusing to overwrite audit output')
    repo = Path(__file__).resolve().parents[1]
    old2, old3 = repo / 'outputs/phase2_20261010T092242Z', repo / 'outputs/phase3_20261010T092242Z'
    new = args.new_data_directory.resolve()
    regression, new2, new3 = new / 'regression', new / 'phase2', new / 'phase3'
    config_path = repo / 'metadata/phase3_selection_config.ini'
    files = [old2 / n for n in ('events.csv', 'phase2_diagnostics.root', 'histogram_inventory.csv', 'summary.json')]
    files += [old3 / n for n in ('cutflow.csv', 'optional_photon_flags.csv', 'histogram_inventory.csv', 'summary.json')]
    files += [new2 / n for n in ('events.csv', 'phase2_diagnostics.root', 'histogram_inventory.csv', 'summary.json')]
    files += [new3 / n for n in ('cutflow.csv', 'optional_photon_flags.csv', 'histogram_inventory.csv', 'summary.json')]
    files += [regression / n for n in ('events.csv', 'pairs.csv', 'histograms.root', 'histogram_bins.csv', 'cutflow.csv', 'optional_photon_flags.csv', 'event_histogram_diff.csv', 'summary.json')]
    files += [config_path, new.parent / 'execution.json']
    require(all(p.is_file() for p in files), 'Required actual DATA evidence missing')
    before_hashes = {str(p): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files}
    import ROOT
    ROOT.gROOT.SetBatch(True)
    require(ROOT.gROOT.GetVersion() == '6.40.04', 'Wrong ROOT environment')
    execution = json.loads((new.parent / 'execution.json').read_text())
    inputs = [r for r in execution['input_files'] if r['sample'] == 'DATA93915']
    require(len(inputs) == 1 and inputs[0]['sha256'] == DATA_SHA and inputs[0]['bytes'] == 17541818 and inputs[0]['range'] == [100, 63195], 'Pinned DATA execution identity mismatch')
    source = Path(inputs[0]['path'])
    if not source.is_absolute():
        source = repo / source
    source = source.resolve()
    require(source.is_file() and source.stat().st_size == 17541818 and sha(source) == DATA_SHA,
            'Pinned DATA source bytes do not match historical identity')
    files.append(source)
    before_hashes[str(source)] = {'bytes': source.stat().st_size, 'sha256': DATA_SHA}
    summary = json.loads((regression / 'summary.json').read_text())
    declared_source = Path(summary['input_path'])
    if not declared_source.is_absolute():
        declared_source = repo / declared_source
    require(declared_source.resolve() == source, 'Regression source path differs from pinned execution source')
    require(summary['original_kernel_commit'] == BASE and summary['mode'] == 'DATA' and summary['dsid'] == 0 and
            summary['entries_read'] == 63095 and summary['start_entry'] == 100 and summary['end_exclusive'] == 63195 and
            summary['unit_status'] == 'PROVISIONAL' and summary['scale_to_gev'] == 1 and not summary['normalization_applied'] and not summary['scale_factors_applied'], 'Unexpected DATA regression provenance')
    historical = index_events(records(old2 / 'events.csv'))
    corrected = index_events(records(new2 / 'events.csv'))
    harness = index_events(records(regression / 'events.csv'))
    cache_checks = {'historical_vs_harness_original': compare_cache(historical, harness, 'original'),
                    'fresh_phase2_vs_harness_corrected': compare_cache(corrected, harness, 'corrected')}
    require(all(v['status'] == 'PASS' for v in cache_checks.values()), 'Exact DATA cache field mismatch; inspect audit exception before approval')
    native_harness = root_histograms(ROOT, regression / 'histograms.root')
    require(set(native_harness) == {name + '__' + v for name in PHASE2_NAMES | set(SELECTED) for v in ('original', 'corrected')}, 'Unexpected harness DATA histogram membership')
    hist_checks = {}
    for directory, version in ((old2, 'original'), (new2, 'corrected')):
        native = root_histograms(ROOT, directory / 'phase2_diagnostics.root')
        require(set(native) == PHASE2_NAMES, 'Unexpected Phase2 histogram membership')
        require(all(h == native_harness[name + '__' + version] for name, h in native.items()), 'Native Phase2 full bin/flow/error/edge/entry mismatch: ' + version)
        hist_checks[version] = {'status': 'PASS', 'histograms': len(native), 'bins_including_flow': sum(h['bins'] + 2 for h in native.values()),
                                'inventory': check_inventory(directory / 'histogram_inventory.csv', native)}
    bin_rows = records(regression / 'histogram_bins.csv')
    expected_bin_keys = {(name, i) for name in PHASE2_NAMES | set(SELECTED) for i in range(native_harness[name + '__original']['bins'] + 2)}
    require(len(bin_rows) == len(expected_bin_keys) and {(r['histogram'], int(r['bin'])) for r in bin_rows} == expected_bin_keys, 'Histogram-bin CSV completeness mismatch')
    bin_differences = []
    for row in bin_rows:
        name, index = row['histogram'], int(row['bin'])
        a, b = (native_harness[name + '__' + v] for v in ('original', 'corrected'))
        old, fresh = a['contents_with_flow'][index], b['contents_with_flow'][index]
        require(numeric(row['original_content']) == old and numeric(row['corrected_content']) == fresh and numeric(row['delta']) == fresh - old and numeric(row['original_entries']) == a['entries'] and numeric(row['corrected_entries']) == b['entries'], 'Native versus bin CSV mismatch')
        if old != fresh:
            bin_differences.append({'histogram': name, 'bin': index, 'bin_class': row['bin_class'], 'old': old, 'new': fresh, 'delta': fresh - old})
    c = configuration(config_path)
    phase3_checks = {}
    for cache, phase3, version in ((historical, old3, 'original'), (corrected, new3, 'corrected')):
        selected = {name: native_harness[name + '__' + version] for name in SELECTED}
        phase3_checks[version] = selected_audit(ROOT, cache, harness, version, c, phase3, selected)
    actual_cutflow = records(regression / 'cutflow.csv')
    actual_optional = records(regression / 'optional_photon_flags.csv')
    require(len(actual_cutflow) == 10 and len(actual_optional) == 2, 'Harness selection evidence rows missing')
    for i, row in enumerate(actual_cutflow):
        old, fresh = (phase3_checks[v]['counts'][i] for v in ('original', 'corrected'))
        require(row['cut'] == 'C' + str(i) and int(row['original_events']) == old and int(row['corrected_events']) == fresh and int(row['delta']) == fresh - old and row['definition_version'] == c['definition_version'], 'Harness cutflow mismatch')
    for row in actual_optional:
        expected = phase3_checks[row['version']]
        require(int(row['C9_events']) == expected['counts'][9] and [int(row[k]) for k in ('raw_tight_id_both', 'raw_tight_id_and_tight_iso_both', 'missing_flags')] == expected['optional_flag_counts'] and row['usage'] == 'DIAGNOSTIC_ONLY_NOT_SELECTION', 'Harness optional flags mismatch')
    invalid = [r for r in historical.values() if r['valid'] == '0']
    require(len(invalid) == 37 and all(r['issue'] == 'gg_negative_or_nonfinite_pair_mass2' for r in invalid), 'Historical 37-event baseline discrepancy')
    invalid_entries = {int(r['entry']) for r in invalid}
    pairs = records(regression / 'pairs.csv')
    require(len(pairs) == 2 * 63095 and {(int(r['entry']), r['group']) for r in pairs} ==
            {(entry, group) for entry in range(100, 63195) for group in ('photon', 'jet')}, 'Pair evidence incomplete/duplicate')
    invalid_details = []
    for row in pairs:
        require(row['mode'] == 'DATA' and row['dsid'] == '0' and identifier(row) == identifier(harness[int(row['entry'])]),
                'Pair identity differs from DATA event identity')
        if row['group'] != 'photon' or int(row['entry']) not in invalid_entries:
            continue
        require(row['original_valid'] == '0' and row['original_issue'] == 'negative_or_nonfinite_pair_mass2', 'Historical invalid-pair reconstruction mismatch')
        old_m2, new_m2, reference_m2, bound = (Decimal(row[k]) for k in
            ('original_mass2', 'corrected_mass2', 'reference_mass2', 'half_ulp_mass2_bound'))
        require(all(v.is_finite() for v in (old_m2, new_m2, reference_m2, bound)) and old_m2 < 0 and bound >= 0,
                'Invalid original-pair diagnostic values')
        compatible = abs(reference_m2) <= bound
        if reference_m2 < 0:
            require(new_m2 < 0 and row['corrected_valid'] == '0' and row['corrected_issue'] == 'negative_or_nonfinite_pair_mass2',
                    'Negative native reference pair was accepted or hidden')
            classification = ('NEGATIVE_SUPPLIED_FLOAT32_TUPLE_HALF_ULP_COMPATIBLE_ORIGIN_UNKNOWN' if compatible else
                              'NEGATIVE_SUPPLIED_FLOAT32_TUPLE_OUTSIDE_HALF_ULP_BOUND_ORIGIN_UNKNOWN')
        else:
            require(new_m2 >= 0 and row['corrected_valid'] == '1', 'Nonnegative native reference pair remains invalid')
            classification = 'OLD_NEGATIVE_PAIR_WITH_NONNEGATIVE_NATIVE_REFERENCE'
        require(int(row['mass2_zero_half_ulp_compatible']) == int(compatible), 'Half-ULP diagnostic flag disagrees with actual bound')
        if reference_m2 < 0:
            require(row['mass2_classification'] == classification, 'Harness negative-reference classification differs from independent numeric assessment')
        invalid_details.append({**identifier(row), 'original_mass2': numeric(row['original_mass2']),
            'corrected_mass2': numeric(row['corrected_mass2']), 'native_cartesian_reference_mass2': numeric(row['reference_mass2']),
            'corrected_valid': int(row['corrected_valid']), 'corrected_issue': row['corrected_issue'],
            'classification': classification, 'harness_classification': row['mass2_classification'],
            'recorded_decimal_mass2': {k: row[k] for k in ('original_mass2', 'corrected_mass2', 'reference_mass2', 'half_ulp_mass2_bound')},
            'half_ulp_mass2_bound': numeric(row['half_ulp_mass2_bound']), 'half_ulp_compatible': int(compatible),
            'assessment': 'independent exact Decimal sign/bound comparison of recorded diagnostics',
            'origin': 'UNKNOWN; half-ULP compatibility is diagnostic, not proof of rounding or physical validity'})
    require(len(invalid_details) == 37, 'Missing historical invalid-pair IDs')
    changed_validity = [identifier(r) for e, r in historical.items() if r['valid'] != corrected[e]['valid']]
    changes = {}
    for field in KINEMATIC:
        entries = [identifier(r) for e, r in historical.items() if not same_number(r[field], corrected[e][field])]
        if entries:
            changes[field] = {'changed_count': len(entries), 'event_ids': entries}
    changed_selection = [identifier(harness[e]) for e in harness if any(harness[e]['original_C' + str(i)] != harness[e]['corrected_C' + str(i)] for i in range(10))]
    histogram_changes = records(regression / 'event_histogram_diff.csv')
    histogram_ids = sorted({(int(r['entry']), int(r['run']), int(r['event'])) for r in histogram_changes})
    delta_by_bin = collections.Counter()
    for row in histogram_changes:
        require(identifier(row) == identifier(harness[int(row['entry'])]), 'Histogram changed-event identity mismatch')
        delta_by_bin[(row['histogram'], int(row['bin']))] += int(row['delta'])
    require({k: v for k, v in delta_by_bin.items() if v} == {(r['histogram'], r['bin']): r['delta'] for r in bin_differences}, 'Per-event histogram changes do not explain full native bin delta')
    require(len(changed_validity) == summary['event_validity_changes'] and len(changed_selection) == summary['cumulative_selection_changes'] and len(histogram_ids) == summary['histogram_event_changes'] and len(histogram_changes) == summary['histogram_contribution_changes'] and len(bin_differences) == summary['differing_histogram_bins'], 'Actual change-count summary mismatch')
    for path in files:
        require(sha(path) == before_hashes[str(path)]['sha256'], 'Read-only input changed during audit: ' + str(path))
    evidence = {'audit_schema': 'phase4-v2-independent-data-cache-histogram-audit', 'status': 'PASS', 'root_version': ROOT.gROOT.GetVersion(),
        'base_commit': BASE, 'range': [100, 63195], 'entries': 63095, 'source_identity': inputs[0],
        'source_bytes_sha256_verification': 'PASS independently hashed pinned native input; no ROOT event reads', 'new_native_event_reads': 0,
        'comparison_policy': 'exact parsed binary64 cache equality; exact native histogram bins/errors/edges/entries including both flow bins; independent Python selection and in-memory selected-bin filling',
        'files': before_hashes, 'cache_checks': cache_checks, 'phase2_native_histograms': hist_checks, 'phase3_checks': phase3_checks,
        'historical_invalid_photon_pairs': invalid_details, 'historical_invalid_classifications': dict(collections.Counter(r['classification'] for r in invalid_details)),
        'changed_validity_event_ids': changed_validity, 'changed_selection_event_ids': changed_selection, 'changed_kinematic_fields': changes,
        'changed_histogram_event_ids': [dict(zip(('entry', 'run', 'event'), row)) for row in histogram_ids], 'histogram_bin_differences': bin_differences,
        'preservation': 'PASS input hashes unchanged before/after this read-only audit', 'scientific_scope': 'PROVISIONAL units; no weights/SFs/luminosity, b flavour, prompt purity or physical rounding-origin claim'}
    args.new_audit_json.parent.mkdir(parents=True, exist_ok=True)
    with args.new_audit_json.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(evidence, output, indent=2, allow_nan=False)
        output.write('\n')
    print('PASS independent DATA audit entries=63095 invalid_pairs=37 C9_old=' + str(phase3_checks['original']['counts'][9]) +
          ' C9_new=' + str(phase3_checks['corrected']['counts'][9]) + ' changed_histogram_bins=' + str(len(bin_differences)) +
          ' audit=' + str(args.new_audit_json))


if __name__ == '__main__':
    main()
