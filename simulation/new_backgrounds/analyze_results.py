"""Independent cutflow/statistical readback of physically validated ROOT rows.

No new events, detector decisions, luminosity or normalization are invented.
Raw source weights and a separately validated model Higgs BR remain distinct.
"""
from pathlib import Path
import argparse
import csv
from decimal import Decimal, localcontext
import json
import math
import re

from .delphes_stage import require, sha_file, save_json

STAGES = ('00_input', '01_photons', '02_jets', '03_two_btags', '04_mgg_105_160')
CONTROL = ('control_00_input', 'control_01_one_photon', 'control_02_jets', 'control_03_two_btags')
HASH = re.compile(r'^[0-9a-f]{64}$')


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate numerical evidence JSON key')
        result[key] = value
    return result


def strict_json(text):
    def invalid(token):
        raise RuntimeError('nonfinite numerical evidence JSON: ' + token)
    value = json.loads(text, object_pairs_hook=_pairs, parse_constant=invalid)
    def finite(item):
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)
        elif isinstance(item, float):
            require(math.isfinite(item), 'nonfinite parsed numerical evidence')
    finite(value)
    return value


def interval(k, n):
    """Wilson two-sided95 and exact zero/all boundary one-sided95 limits."""
    require(type(k) is int and type(n) is int and 0 <= k <= n and n > 0, 'invalid interval counts')
    z = 1.959963984540054
    p, d = k / n, 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {'estimate': p, 'binomial_plugin_standard_error': math.sqrt(p * (1 - p) / n),
            'wilson95_low': 0.0 if k == 0 else max(0.0, center - half),
            'wilson95_high': 1.0 if k == n else min(1.0, center + half),
            'zero_survivor_one_sided95_upper': -math.expm1(math.log(0.05) / n) if k == 0 else None,
            'all_survivor_one_sided95_lower': math.exp(math.log(0.05) / n) if k == n else None,
            'zero_means': 'OBSERVED_ZERO_IS_NOT_PROOF_OF_ZERO_BACKGROUND' if k == 0 else None}


def weighted_statistics(values):
    """Sampling SE of mean raw weight times selection; denominator fullN.

    values include zero for every rejected original source event. Integration
    uncertainty is an independent generator quantity, never this estimator.
    """
    require(len(values) > 1, 'full source sample required for weighted sampling uncertainty')
    with localcontext() as context:
        context.prec = 60
        contributions = [Decimal(str(value)) for value in values]
        require(all(value.is_finite() for value in contributions), 'nonfinite source contribution')
        n = Decimal(len(contributions))
        total = sum(contributions, Decimal(0))
        sum2 = sum((value * value for value in contributions), Decimal(0))
        variance = n / (n - 1) * (sum2 - total * total / n)
        require(variance >= 0, 'invalid source sampling variance')
        return {'source_weight_sum_pb': float(total), 'source_weight_sum_squared_pb2': float(sum2),
                'source_sampling_variance_pb2': float(variance),
                'source_sampling_standard_error_pb': float(variance.sqrt()),
                'definition': 'N/(N-1)*(sum(c_i^2)-sum(c_i)^2/N); c_i=XWGTUP_i/N*selection_i'}


def _finite(value, name, nullable=False):
    if value is None and nullable:
        return
    require(type(value) in (float, int) and math.isfinite(value) and value >= 0, 'invalid observable: ' + name)


def validate_reco_row(row, ordinal, process):
    require(row['process'] == process and row['source_event_index'] == ordinal and
            row['original_source_events'] == 1000, 'independent source/process/denominator mismatch')
    for name in ('source_event_sha256', 'hepmc_event_sha256'):
        require(type(row[name]) is str and HASH.fullmatch(row[name]) is not None, 'invalid source event digest')
    for name in ('photon_multiplicity', 'jet_multiplicity', 'selected_photons', 'eligible_jets', 'tagged_bit0'):
        require(type(row[name]) is int and 0 <= row[name] <= 100000, 'invalid reconstructed object count')
    require(row['selected_photons'] <= row['photon_multiplicity'] and
            row['tagged_bit0'] <= row['eligible_jets'] <= row['jet_multiplicity'], 'invalid object subset counts')
    for name in ('raw_LHE_XWGTUP_pb', 'source_contribution_pb'):
        require(type(row[name]) in (float, int) and math.isfinite(row[name]), 'nonfinite source weight')
    require(math.isclose(row['source_contribution_pb'], row['raw_LHE_XWGTUP_pb'] / 1000,
                         rel_tol=1e-12, abs_tol=1e-12), 'source weight was normalized again or denominator changed')
    for first, second, n in (('pT_gamma1', 'pT_gamma2', 'photon_multiplicity'),
                             ('pT_jet1', 'pT_jet2', 'jet_multiplicity'),
                             ('pT_selected_gamma1', 'pT_selected_gamma2', 'selected_photons')):
        for index, name in enumerate((first, second)):
            require((row[name] is None) == (row[n] <= index), 'absent-object pT null contract failed')
            _finite(row[name], name, nullable=True)
        if row[second] is not None:
            require(row[first] >= row[second], 'leading pT order failed')
    photons = row['selected_photons'] >= 2
    jets = row['eligible_jets'] >= 2
    tags = row['tagged_bit0'] >= 2
    available = {'m_gamma_gamma': photons, 'DeltaR_gamma_gamma': photons,
                 'm_jj': jets, 'm_bb': tags, 'DeltaR_bb': tags,
                 'm_bb_gamma_gamma': photons and tags}
    for name, has_pair in available.items():
        require((row[name] is not None) == has_pair, 'missing-pair observable null contract failed: ' + name)
        _finite(row[name], name, nullable=True)
    photon_cut = photons and row['pT_selected_gamma1'] > 35
    jet_cut = photon_cut and jets
    tag_cut = jet_cut and tags
    mass_cut = tag_cut and 105 <= row['m_gamma_gamma'] <= 160
    one_photon_cut = row['selected_photons'] >= 1 and row['pT_selected_gamma1'] > 35
    predicates = {'cut_photons': photon_cut, 'cut_jets': jet_cut, 'cut_two_btags': tag_cut, 'cut_mgg': mass_cut,
                  'control_cut_one_photon': one_photon_cut, 'control_cut_jets': one_photon_cut and jets,
                  'control_cut_two_btags': one_photon_cut and jets and tags}
    for key, value in predicates.items():
        require(type(row[key]) is bool and row[key] is value, 'independent original cut predicate mismatch: ' + key)
    return [True, photon_cut, jet_cut, tag_cut, mass_cut], [True, one_photon_cut, one_photon_cut and jets,
                                                        one_photon_cut and jets and tags]


def _model_br_contract(value, process):
    if value is None:
        return None
    require(process in ('zh', 'tth'), 'B06 must not receive a Higgs branching-ratio factor')
    require(value['status'] == 'PASS_MODEL_BR_WEIGHT_CLOSURE' and value['scope'] == 'MODEL_BR_ONLY',
            'unverified or precision physical BR convention')
    require(type(value['factor']) in (float, int) and math.isfinite(value['factor']) and 0 < value['factor'] < 1,
            'invalid actually initialized Higgs model BR')
    require(type(value['ledger_sha256']) is str and HASH.fullmatch(value['ledger_sha256']) is not None,
            'model BR missing exact source ledger identity')
    require(value.get('factor_applications') == 1 and value.get('weight_closure') == 'PASS',
            'missing factor closure or repeated BR application')
    return value


def summarize_detector(report, model_br=None, generator_integration_uncertainty_pb=None):
    require(report['status'] == 'PASS_NATIVE_BACKGROUND_RECORD_READBACK' and
            report['ROOT_entries'] == report['processed'] == report['source_events'] == 1000 and
            report['invalid'] == report['skipped'] == 0, 'full1000 actual native ROOT PASS required')
    process = report['process']
    require(process in ('zh', 'tth', 'bbgj'), 'unknown detector process')
    for name in ('reco_events.jsonl', 'cutflow.csv'):
        path = report['reco_events_path'] if name.endswith('jsonl') else report['cutflow_path']
        require(sha_file(path) == report['derived_files_sha256'][name], 'derived actual detector evidence changed')
    rows, conditions = [], []
    with Path(report['reco_events_path']).open(encoding='utf-8') as stream:
        for line in stream:
            require(len(line) <= 8 * 1024 * 1024 and len(rows) < 1000, 'bounded full1000 numerical rows required')
            row = strict_json(line)
            diphoton, control = validate_reco_row(row, len(rows) + 1, process)
            rows.append(row)
            conditions.append(diphoton + (control if process == 'bbgj' else []))
    require(len(rows) == 1000, 'full1000 numerical rows required')
    stages = STAGES + (CONTROL if process == 'bbgj' else ())
    summaries = []
    for index, stage in enumerate(stages):
        mask = [condition[index] for condition in conditions]
        count = sum(mask)
        values = [row['source_contribution_pb'] if selected else 0.0 for row, selected in zip(rows, mask)]
        summaries.append({'stage': stage, 'raw_events': count, 'original_source_events': 1000,
                          'acceptance': interval(count, 1000), **weighted_statistics(values)})
    with Path(report['cutflow_path']).open(encoding='utf-8', newline='') as stream:
        native = list(csv.DictReader(stream))
    require(len(native) == len(summaries), 'native/independent cutflow stage count mismatch')
    bystage = {row['stage']: row for row in native}
    require(len(bystage) == len(native), 'duplicate native cutflow stage')
    for item in summaries:
        original = bystage[item['stage']]
        require(int(original['raw_events']) == item['raw_events'], 'native/independent raw cutflow mismatch')
        for field in ('source_weight_sum_pb', 'source_weight_sum_squared_pb2'):
            require(math.isclose(float(original[field]), item[field], rel_tol=2e-12, abs_tol=1e-12),
                    'native/independent weighted cutflow mismatch: ' + field)
    br = _model_br_contract(model_br, process)
    if generator_integration_uncertainty_pb is not None:
        _finite(generator_integration_uncertainty_pb, 'generator integration uncertainty')
    if br:
        for item in summaries:
            factor = br['factor']
            item['MODEL_BR_ONLY_weight_sum_pb'] = item['source_weight_sum_pb'] * factor
            item['MODEL_BR_ONLY_weight_sum_squared_pb2'] = item['source_weight_sum_squared_pb2'] * factor * factor
            item['MODEL_BR_ONLY_sampling_standard_error_pb'] = item['source_sampling_standard_error_pb'] * factor
    return {'schema_version': 1, 'status': 'PASS_INDEPENDENT_FULL1000_NUMERICAL_READBACK',
            'process': process, 'source_events': 1000, 'native_root_sha256': report['root_sha256'],
            'reco_events_sha256': report['derived_files_sha256']['reco_events.jsonl'],
            'cutflow_sha256': report['derived_files_sha256']['cutflow.csv'], 'cutflow': summaries,
            'generator_integration_uncertainty_pb': generator_integration_uncertainty_pb,
            'uncertainty_scope': 'source sampling includes this one realized tag/detector stream; integration error separate',
            'tag_sampling_variance': 'NOT_SEPARATELY_MEASURED; no additional detector or tag redraws',
            'event_correlations': 'cuts nested within each source event; stage uncertainties must not be combined independently',
            'model_br_contract': br, 'official_detector_or_br_calibration': 'BLOCKED',
            'B06_photon_fake_rate': 'BLOCKED_UNCALIBRATED' if process == 'bbgj' else 'NOT_APPLICABLE',
            'background_overlap': 'BLOCKED_NO_VALIDATED_OVERLAP_OR_MATCHING_SCHEME',
            'luminosity_applied': False, 'selection_optimized': False}


def main():
    parser = argparse.ArgumentParser(description='Independent read-only full1000 detector numerical analysis')
    parser.add_argument('--native-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-br-contract', type=Path)
    parser.add_argument('--integration-uncertainty-pb', type=float)
    args = parser.parse_args()
    require(not args.output.exists(), 'preserve previous numerical evidence')
    report = strict_json(args.native_report.read_text(encoding='utf-8'))
    model = strict_json(args.model_br_contract.read_text(encoding='utf-8')) if args.model_br_contract else None
    save_json(args.output, summarize_detector(report, model, args.integration_uncertainty_pb))


if __name__ == '__main__':
    main()
