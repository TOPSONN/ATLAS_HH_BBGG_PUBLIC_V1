#!/usr/bin/env python3
"""Compare preserved/new MC evidence without ROOT reads or physics promotion.

Usage: audit_phase4_recovery_matching.py ORIGINAL NEW NEW_AUDIT_DIR
       [--regression NEW_NUMERICAL_REGRESSION_DIR]
The existing geometry auditor is executed on both populations. Raw flag values
were not persisted by the historical MC driver: that limitation is explicit.
"""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
from functools import lru_cache
import json
import math
from pathlib import Path
import struct
import subprocess
import sys


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames
        require(header and len(header) == len(set(header)), f'Invalid/duplicate CSV header: {path.name}')
        result = list(reader)
        require(all(None not in row and all(value is not None for value in row.values()) for row in result),
                f'Malformed CSV row width: {path.name}')
    return header, result


def exact_float(value):
    result = float(value)
    require(math.isfinite(result), 'Nonfinite raw diagnostic value')
    return struct.pack('!d', result)


def native_float32(text):
    # objects.csv uses Float32 max_digits10, not a Double decimal expansion.
    # Recover the native float exactly before independent geometric arithmetic.
    return struct.unpack('!f', struct.pack('!f', float(text)))[0]


def angular_distance(first, second):
    delta_phi = math.remainder(first[2] - second[2], 2 * math.pi)
    return math.hypot(first[1] - second[1], delta_phi)


def small_graph_optimum(reco, truth, threshold):
    edges = [[(j, angular_distance(a, b)) for j, b in enumerate(truth)
              if angular_distance(a, b) < threshold] for a in reco]
    combinations = math.prod(len(candidates) + 1 for candidates in edges)
    if len(reco) > 12 or len(truth) > 24 or combinations > 50000:
        return None

    @lru_cache(None)
    def visit(position, used):
        if position == len(edges):
            return 0, 0.0
        best = visit(position + 1, used)
        for target, distance in edges[position]:
            if used & (1 << target):
                continue
            cardinality, cost = visit(position + 1, used | (1 << target))
            candidate = cardinality + 1, cost + distance
            if candidate[0] > best[0] or (candidate[0] == best[0] and candidate[1] < best[1]):
                best = candidate
        return best

    return visit(0, 0)


def audit_reco_geometry(args, result):
    require(args.regression is not None, 'Independent reconstructed geometry requires --regression')
    summary = json.loads((args.updated / 'summary.json').read_text(encoding='utf-8'))
    _, event_rows = rows(args.updated / 'events.csv')
    events = {int(row['entry']): row for row in event_rows}
    require(len(events) == len(event_rows) == summary['entries_read'], 'Duplicate or missing native MC event')
    require(set(events) == set(range(summary['start_entry'], summary['end_exclusive'])), 'Incomplete native event range')
    _, object_rows = rows(args.regression / 'objects.csv')
    _, truth_rows = rows(args.updated / 'truth_objects.csv')
    reconstructed, provided_truth = defaultdict(dict), defaultdict(dict)
    for rows_to_check, target, reco in [(object_rows, reconstructed, True), (truth_rows, provided_truth, False)]:
        for row in rows_to_check:
            entry = int(row['entry'])
            require(entry in events, 'Object outside reconstructed event range')
            event = events[entry]
            require(all(row[key] == event[key] for key in ['dsid', 'run', 'event']), 'Raw object/native event identity mismatch')
            group = row['group'] if reco else row['object_group']
            require(group in {'photon', 'jet'}, 'Unexpected object group')
            index = int(row['input_index'] if reco else row['index'])
            require(index not in target[(entry, group)] and index >= 0, 'Duplicate/negative native object index')
            if reco:
                require(row['mode'] == 'MC' and row['collection_valid'] == '1', 'Invalid reconstructed collection in geometric evidence')
            vector = tuple(native_float32(row[field]) for field in ['raw_pt', 'raw_eta', 'raw_phi'])
            require(all(math.isfinite(value) for value in vector) and vector[0] >= 0 and abs(vector[2]) <= math.pi + 1e-5,
                    'Nonfinite/invalid native direction tuple')
            scale = summary['scale_to_gev'] if reco else summary['truth_scale_to_gev']
            target[(entry, group)][index] = (vector[0] * scale, vector[1], vector[2])
    for entry, event in events.items():
        for group in ['photon', 'jet']:
            require(set(reconstructed[(entry, group)]) == set(range(int(event[group + '_n']))),
                    f'Raw reconstructed multiplicity/index coverage mismatch at entry {entry}')
            require(set(provided_truth[(entry, group)]) == set(range(len(provided_truth[(entry, group)]))),
                    f'Non-contiguous supplied truth index coverage at entry {entry}')
    eligible_reco, eligible_truth = {}, {}
    for entry in events:
        for group in ['photon', 'jet']:
            eta_max = 2.37 if group == 'photon' else 2.5
            for source, target in [(reconstructed, eligible_reco), (provided_truth, eligible_truth)]:
                target[(entry, group)] = {index: vector for index, vector in source[(entry, group)].items()
                                          if vector[0] > 25 and abs(vector[1]) < eta_max}
    _, assignment_rows = rows(args.updated / 'matching_assignments.csv')
    assignments = defaultdict(list)
    maximum_dr_error = 0.0
    used_reco, used_truth = defaultdict(set), defaultdict(set)
    thresholds = {'photon': summary['photon_matching_thresholds'], 'jet': summary['jet_matching_thresholds']}
    for row in assignment_rows:
        entry, group, threshold, scope = int(row['entry']), row['object_group'], float(row['threshold']), row['scope']
        require(entry in events and group in thresholds and threshold in thresholds[group] and scope in {'ALL_VALID', 'C9'},
                'Unexpected assignment event/group/threshold/scope')
        event = events[entry]
        require(all(row[key] == event[key] for key in ['dsid', 'run', 'event']) and event['valid'] == '1',
                'Assignment native event identity/validity mismatch')
        require(scope != 'C9' or event['C9_selected'] == '1', 'Assignment outside declared C9 population')
        ri, ti = int(row['reco_index']), int(row['truth_index'])
        require(ri in eligible_reco[(entry, group)] and ti in eligible_truth[(entry, group)], 'Assignment references ineligible raw object')
        key = entry, group, threshold, scope
        require(ri not in used_reco[key] and ti not in used_truth[key], 'Assignment object is reused')
        used_reco[key].add(ri)
        used_truth[key].add(ti)
        expected = angular_distance(eligible_reco[(entry, group)][ri], eligible_truth[(entry, group)][ti])
        observed = float(row['delta_r'])
        error = abs(expected - observed)
        maximum_dr_error = max(maximum_dr_error, error)
        require(math.isfinite(observed) and 0 <= observed < threshold and expected < threshold and
                error <= 1e-12, 'Stored assignment DeltaR differs from independent native directions')
        assignments[key].append((ri, ti, observed))
    _, threshold_rows = rows(args.updated / 'matching_threshold_summary.csv')
    seen, denominator_checks = set(), []
    for row in threshold_rows:
        group, threshold, scope = row['object_group'], float(row['threshold']), row['scope']
        key = group, threshold, scope
        require(group in thresholds and threshold in thresholds[group] and scope in {'ALL_VALID', 'C9'} and key not in seen,
                'Unexpected/duplicate threshold summary row')
        seen.add(key)
        population = [entry for entry, event in events.items() if event['valid'] == '1' and
                      (scope == 'ALL_VALID' or event['C9_selected'] == '1')]
        n_reco = sum(len(eligible_reco[(entry, group)]) for entry in population)
        n_truth = sum(len(eligible_truth[(entry, group)]) for entry in population)
        matched = sum(len(assignments[(entry, group, threshold, scope)]) for entry in population)
        require(int(row['events']) == len(population) and int(row['truth_available_events']) == len(population) and
                int(row['truth_missing_events']) == 0, 'Truth-available scoped event denominator differs')
        require(int(row['reco_provided']) == sum(len(reconstructed[(entry, group)]) for entry in population) and
                int(row['truth_provided']) == sum(len(provided_truth[(entry, group)]) for entry in population), 'Provided object denominator differs')
        require(int(row['eligible_reco']) == n_reco and int(row['eligible_truth']) == n_truth and
                int(row['matched_pairs']) == matched and int(row['unmatched_reco']) == n_reco - matched and
                int(row['unmatched_truth']) == n_truth - matched, 'Independent eligible/unmatched/matched denominator differs')
        for field, denominator in [('geometric_reco_match_fraction', n_reco), ('geometric_truth_match_fraction', n_truth)]:
            require((row[field] == '') if denominator == 0 else math.isclose(float(row[field]), matched / denominator, rel_tol=1e-14, abs_tol=1e-15),
                    'Geometric fraction does not use independently recomputed denominator')
        denominator_checks.append({'group': group, 'threshold': threshold, 'scope': scope, 'events': len(population),
                                   'eligible_reco': n_reco, 'eligible_truth': n_truth, 'matched': matched})
    require(seen == {(group, threshold, scope) for group in thresholds for threshold in thresholds[group] for scope in ['ALL_VALID', 'C9']},
            'Missing threshold/scope summary')
    oracle_tested, oracle_skipped, scope_copies = 0, 0, 0
    maximum_cost_error, skipped_populations = 0.0, Counter()
    for entry, event in events.items():
        if event['valid'] != '1':
            continue
        for group in thresholds:
            reco = list(eligible_reco[(entry, group)].values())
            truth = list(eligible_truth[(entry, group)].values())
            for threshold in thresholds[group]:
                all_pairs = sorted(assignments[(entry, group, threshold, 'ALL_VALID')])
                selected_pairs = sorted(assignments[(entry, group, threshold, 'C9')])
                require(selected_pairs == (all_pairs if event['C9_selected'] == '1' else []), 'C9 associations differ from same-event ALL_VALID assignment')
                scope_copies += 1
                optimum = small_graph_optimum(reco, truth, threshold)
                if optimum is None:
                    oracle_skipped += 1
                    skipped_populations[group] += 1
                    continue
                oracle_tested += 1
                cardinality, minimum_cost = optimum
                cost = sum(pair[2] for pair in all_pairs)
                error = abs(cost - minimum_cost)
                maximum_cost_error = max(maximum_cost_error, error)
                require(len(all_pairs) == cardinality and error <= 1e-12 + 1e-12 * abs(minimum_cost),
                        'Saved assignment differs from independent exhaustive maximum-cardinality/minimum-cost oracle')
    result['independent_reco_geometry'] = {'status': 'PASS', 'native_reco_objects': len(object_rows),
        'provided_truth_objects': len(truth_rows), 'assignment_rows': len(assignment_rows),
        'maximum_delta_r_absolute_error': maximum_dr_error, 'scoped_denominators': denominator_checks,
        'same_event_C9_copy_checks': scope_copies, 'small_graph_oracle_tested': oracle_tested,
        'small_graph_oracle_skipped': oracle_skipped, 'oracle_skipped_groups': dict(skipped_populations),
        'oracle_budget': 'at most12 reco,24 truth,product(1+candidate_degree)<=50000; no claim for skipped optimum checks',
        'maximum_oracle_sum_delta_r_error': maximum_cost_error,
        'objects_sha256': sha256(args.regression / 'objects.csv'), 'truth_objects_sha256': sha256(args.updated / 'truth_objects.csv'),
        'eligibility': 'native provided objects, photon pt>25 and abs(eta)<2.37; jet pt>25 and abs(eta)<2.5; no crack/ID/isolation/origin/flavour cut',
        'classification': 'PROVISIONAL_GEOMETRIC_ONLY_NOT_ORIGIN_PURITY_OR_OFFICIAL_EFFICIENCY'}


def audit(args, result):
    original, updated, destination = args.original, args.updated, args.destination
    for directory in [original, updated]:
        require(directory.is_dir(), f'Missing local evidence directory: {directory}')
    require(original.resolve() != updated.resolve(), 'Historical and new evidence must remain distinct')
    old = json.loads((original / 'summary.json').read_text(encoding='utf-8'))
    new = json.loads((updated / 'summary.json').read_text(encoding='utf-8'))
    result.update(dsid=old['dsid'], entry_range=[old['start_entry'], old['end_exclusive']],
                  original_mass_gate=old['mass_closure_status'], corrected_mass_gate=new['mass_closure_status'])
    require(old['dsid'] == new['dsid'] and old['start_entry'] == new['start_entry'] and
            old['end_exclusive'] == new['end_exclusive'] and old['entries_read'] == new['entries_read'],
            'DSID/range/population changed')
    require(new['mass_closure_status'] == 'PASS' and new['mass_closure_failures'] == 0,
            'Corrected MC mass-closure gate did not execute successfully')
    require(new['unit_status'] == 'PROVISIONAL' and new['weighting'] == 'RAW_UNWEIGHTED' and
            new['normalization_applied'] is False and new['scale_factors_applied'] is False,
            'Scientific unit/weighting contract changed')
    allowed_summary = {'mass_closure_status', 'mass_closure_failures', 'mass_max_absolute_deviation',
                       'mass_max_relative_deviation'}
    require(set(old) == set(new), 'MC reconstruction summary fields changed unexpectedly')
    summary_differences = {key: {'original': old[key], 'corrected': new[key]} for key in old if old[key] != new[key]}
    result['summary_differences'] = summary_differences
    require(set(summary_differences) <= allowed_summary, 'Non-numerical MC summary fields changed')
    result['immutable_payloads'] = {}
    immutable = ['matching_assignments.csv', 'matching_threshold_summary.csv', 'truth_objects.csv',
                 'native_bindings.csv', 'normalization_sf_diagnostics.csv', 'weight_diagnostics.json', 'cutflow.csv']
    for name in immutable:
        old_hash, new_hash = sha256(original / name), sha256(updated / name)
        result['immutable_payloads'][name] = {'original_sha256': old_hash, 'corrected_sha256': new_hash,
                                            'byte_identical': old_hash == new_hash}
        require(old_hash == new_hash, f'Expected invariant payload differs: {name}')
    old_header, old_rows = rows(original / 'events.csv')
    new_header, new_rows = rows(updated / 'events.csv')
    require(old_header == new_header and len(old_rows) == len(new_rows) == old['entries_read'],
            'MC event schema or count changed')
    allowable_event = {'m_gg', 'm_jj', 'cartesian_mass_closure_pass'}
    mass_changes = {name: {'events': 0, 'maximum_absolute': Decimal(0), 'witness': None} for name in ['m_gg', 'm_jj']}
    closure_changes = []
    expected_entries = list(range(old['start_entry'], old['end_exclusive']))
    require([int(row['entry']) for row in old_rows] == expected_entries and
            [int(row['entry']) for row in new_rows] == expected_entries, 'MC event entry coverage/order changed')
    for before, after in zip(old_rows, new_rows):
        require(all(before[field] == after[field] for field in old_header if field not in allowable_event),
                f'Native identity, object order, direction, raw weight, validity or C9 changed at entry {before["entry"]}')
        for field in ['m_gg', 'm_jj']:
            require(bool(before[field]) == bool(after[field]), f'Pair availability changed at entry {before["entry"]}')
            if before[field] != after[field]:
                difference = abs(Decimal(after[field]) - Decimal(before[field]))
                stats = mass_changes[field]
                stats['events'] += 1
                if difference > stats['maximum_absolute']:
                    stats['maximum_absolute'] = difference
                    stats['witness'] = {key: before[key] for key in ['dsid', 'entry', 'run', 'event']}
        require(after['cartesian_mass_closure_pass'] == '1', f'Corrected event closure failed at entry {before["entry"]}')
        if before['cartesian_mass_closure_pass'] != after['cartesian_mass_closure_pass']:
            closure_changes.append({key: before[key] for key in ['dsid', 'entry', 'run', 'event']})
    for stats in mass_changes.values():
        stats['maximum_absolute'] = str(stats['maximum_absolute'])
    result.update(event_rows=len(new_rows), event_invariant_columns=[field for field in old_header if field not in allowable_event],
                  pair_mass_changes=mass_changes, event_closure_status_changes=closure_changes)
    result['events_sha256'] = {'original': sha256(original / 'events.csv'), 'corrected': sha256(updated / 'events.csv')}
    result['summary_sha256'] = {'original': sha256(original / 'summary.json'), 'corrected': sha256(updated / 'summary.json')}
    _, native = rows(updated / 'native_bindings.csv')
    result['raw_photon_flag_bindings'] = [row for row in native if row['branch'] in
                                        ['photon_isTightID', 'photon_isLooseID', 'photon_isTightIso', 'photon_isLooseIso']]
    result['historical_raw_photon_flag_value_comparison'] = 'NOT_AVAILABLE_HISTORICAL_MC_DRIVER_DID_NOT_PERSIST_RAW_FLAG_VALUES'
    if args.regression:
        _, regression = rows(args.regression / 'events.csv')
        require(len(regression) == len(new_rows), 'Regression/native MC population mismatch')
        for row, event in zip(regression, new_rows):
            require(all(row[key] == event[key] for key in ['dsid', 'entry', 'run', 'event']), 'Regression/native event identity mismatch')
            require(exact_float(row['raw_generator_weight']) == exact_float(event['mc_weight']), 'Raw generator weight changed in regression')
            require(row['original_C9'] == row['corrected_C9'] == event['C9_selected'], 'Regression/native C9 changed')
        _, flags = rows(args.regression / 'optional_photon_flags.csv')
        require(len(flags) == 2 and flags[0]['version'] == 'original' and flags[1]['version'] == 'corrected', 'Missing original/corrected flag counts')
        require(all(flags[0][key] == flags[1][key] for key in flags[0] if key != 'version'), 'Original/corrected raw flag diagnostics changed')
        result['regression_raw_flag_diagnostics'] = {'A_B_counts_identical': True, 'counts': flags,
            'historical_value_comparison': 'NOT_AVAILABLE',
            'events_sha256': sha256(args.regression / 'events.csv'),
            'flag_counts_sha256': sha256(args.regression / 'optional_photon_flags.csv')}
        audit_reco_geometry(args, result)
    auditor = Path(__file__).with_name('audit_phase4_matching.py')
    require(auditor.is_file(), 'Existing independent matching auditor is missing')
    result['independent_matching_auditor_sha256'] = sha256(auditor)
    result['independent_matching_audits'] = {}
    for label, source in [('original', original), ('corrected', updated)]:
        target = destination / f'{label}_matching.json'
        run = subprocess.run([sys.executable, '-E', '-B', str(auditor), str(source), str(target)],
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        (destination / f'{label}_matching.log').write_text(run.stdout, encoding='utf-8')
        result['independent_matching_audits'][label] = {'exit_code': run.returncode, 'output': target.name}
        require(run.returncode == 0 and target.is_file(), f'Existing {label} matching audit failed; log retained')
        matching = json.loads(target.read_text(encoding='utf-8'))
        require(matching['csv_identity_uniqueness_threshold_denominator_scope_checks'] == 'PASS',
                f'Existing {label} matching audit did not pass')
        result['independent_matching_audits'][label].update(assignment_rows=matching['assignment_rows'],
                                                          threshold_summary_rows=matching['threshold_summary_rows'],
                                                          audit_sha256=sha256(target))
    result['claim'] = 'Exact preserved geometry and scoped denominators; PROVISIONAL geometric association only, not origin purity, official efficiency, b-tag performance or physical normalization'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('updated', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--regression', type=Path)
    parser.add_argument('--geometry-only', action='store_true', help='Add independent reco/denominator/DeltaR/oracle evidence without repeating existing matching audits')
    args = parser.parse_args()
    if args.destination.exists():
        parser.error('Audit output exists; refusing overwrite of any evidence')
    args.destination.mkdir(parents=True)
    result = {'schema': 'phase4-recovery-matching-audit-v1', 'status': 'FAIL',
              'original_directory': str(args.original), 'corrected_directory': str(args.updated),
              'ROOT_input_reads': 0, 'normalization_applied': False, 'figures_generated': False}
    try:
        if args.geometry_only:
            for name in ['matching_assignments.csv', 'matching_threshold_summary.csv', 'truth_objects.csv']:
                require(sha256(args.original / name) == sha256(args.updated / name), f'Immutable matching payload changed: {name}')
            audit_reco_geometry(args, result)
        else:
            audit(args, result)
        result['status'] = 'PASS'
    except Exception as error:
        result['error'] = str(error)
    (args.destination / 'audit.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
