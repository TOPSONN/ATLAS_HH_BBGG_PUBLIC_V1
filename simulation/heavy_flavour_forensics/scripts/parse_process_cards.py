#!/usr/bin/env python3
"""Parse reviewed MG5 candidates/construct tree diagrams, never export or run events."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
CONFIG = REPO / 'simulation/heavy_flavour_forensics/config/process_candidates_v1.json'
MODEL = 'import model sm-no_b_mass'
PROTON = 'define p = g u c d s b u~ c~ d~ s~ b~'
JET = 'define j4 = g u c d s u~ c~ d~ s~'
PROCESSES = {
    'bb_gamma_j': 'p p > b b~ a j4 QCD=3 QED=1',
    'tth': 'p p > t t~ h QCD=2 QED=1',
    'zh': 'p p > z h QCD=0 QED=2',
    'zh_z_to_bb': 'p p > z h QCD=0 QED=2, z > b b~',
    'tth_semileptonic_e_one_charge': 'p p > t t~ h QCD=2 QED=1, (t > b w+, w+ > e+ ve), (t~ > b~ w-, w- > j4 j4)',
    'ordinary_sm_higgs_diphoton_negative': 'h > a a',
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def commands(path, candidate):
    lines = [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip() and not line.lstrip().startswith('#')]
    wanted = [MODEL, PROTON] + ([JET] if candidate == 'bb_gamma_j' else []) + ['generate ' + PROCESSES[candidate]]
    if lines != wanted:
        raise ValueError('Candidate must equal reviewed import/define/generate commands; no output/launch or alternate model: ' + candidate)
    return lines


def reviewed_commands(candidate):
    return [MODEL, PROTON] + ([JET] if candidate in ('bb_gamma_j', 'tth_semileptonic_e_one_charge') else []) + ['generate ' + PROCESSES[candidate]]


def installation(path):
    spec = importlib.util.spec_from_file_location('phase6e_mg5_installation', REPO / 'simulation/mg5/scripts/installation.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    config = json.loads(path.read_text())
    mg5, identity = mod.verify(config)
    return config, mg5, identity, mod


def amplitude_records(amplitude, model):
    if 'amplitudes' in amplitude:
        records = []
        for child in amplitude.get('amplitudes'):
            records.extend(amplitude_records(child, model))
        for child in amplitude.get('decay_chains'):
            records.extend(amplitude_records(child, model))
        return records
    process = amplitude.get('process')
    diagrams = amplitude.get('diagrams')
    orders = set()
    for diagram in diagrams:
        diagram.calculate_orders(model)
        orders.add(tuple(sorted((name, value) for name, value in diagram.get('orders').items() if name != 'WEIGHTED')))
    return [{'initial_pdgs': [leg.get('id') for leg in process.get('legs') if not leg.get('state')],
             'final_pdgs': [leg.get('id') for leg in process.get('legs') if leg.get('state')],
             'diagram_count': len(diagrams), 'actual_amplitude_orders': [dict(order) for order in sorted(orders)]}]


def worker(request_path, result_path):
    request = json.loads(request_path.read_text())
    config, mg5, identity, verifier = installation(Path(request['installation']))
    if str(mg5) != request['mg5_path']:
        raise ValueError('Worker installation differs from verified source')
    for item in request['checks']:
        if item['commands'] != reviewed_commands(item['id']):
            raise ValueError('Worker accepts only exact reviewed import/define/generate; export/launch forbidden')
        if item['negative'] is not item['id'].endswith('_negative'):
            raise ValueError('Negative-check contract changed')
    sys.path.insert(0, str(mg5))
    import madgraph
    madgraph.ReadWrite = False  # before importing import_ufo: suppress new model pickle/cache writes.
    from madgraph.interface.madgraph_interface import MadGraphCmd
    results = []
    for item in request['checks']:
        cmd = MadGraphCmd()
        cmd.options['auto_convert_model'] = False
        cmd.options['auto_update'] = 0
        for line in item['commands'][:-1]:
            cmd.exec_cmd(line, errorhandling=False, printcmd=False, precmd=True)
        try:
            cmd.exec_cmd(item['commands'][-1], errorhandling=False, printcmd=False, precmd=True)
            records = []
            for amplitude in cmd._curr_amps:
                records.extend(amplitude_records(amplitude, cmd._curr_model))
            if item['negative']:
                raise RuntimeError('Ordinary SM unexpectedly accepted HAA tree decay')
            if not records or any(record['diagram_count'] <= 0 for record in records):
                raise RuntimeError('No nonzero diagram records')
            expected = item.get('expected_orders')
            if expected and any(order != expected for record in records for order in record['actual_amplitude_orders']):
                raise RuntimeError('Retained tree amplitude orders differ from reviewed production component')
            results.append({'id': item['id'], 'status': 'PASS_PARSE_AND_TREE_DIAGRAM_CONSTRUCTION',
                            'commands': item['commands'], 'amplitude_records': records,
                            'record_count': len(records), 'physical_events': 0, 'cross_section_pb': 'UNKNOWN_NOT_INTEGRATED'})
        except Exception as error:
            if not item['negative']:
                raise
            text = str(error)
            if 'No amplitudes generated' not in text and 'No diagram' not in text:
                raise RuntimeError('Negative HAA check failed for an unrelated reason: ' + type(error).__name__) from error
            results.append({'id': item['id'], 'status': 'PASS_EXPECTED_NO_TREE_DIAGRAMS', 'commands': item['commands'],
                            'error_class': type(error).__name__, 'reason': 'ordinary sm-no_b_mass has no HAA tree vertex', 'physical_events': 0})
        if cmd._export_dir is not None or cmd._done_export:
            raise RuntimeError('Unexpected MG5 export state')
    verifier.verify(config)
    result_path.write_text(json.dumps({'status': 'PASS_PARSE_ONLY', 'checks': results, 'events_generated': 0}, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, default=Path(os.environ.get('MG5_LOCAL_CONFIG', REPO / '.local/mg5_installation.json')))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker-request', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--worker-result', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_request:
        worker(args.worker_request, args.worker_result)
        return 0
    if not args.output:
        parser.error('--output NEW_LOCAL_DIRECTORY is required')
    contract = json.loads(CONFIG.read_text())
    contract_sha_before = sha256(CONFIG.read_bytes())
    checks = []
    cards = []
    for item in contract['candidates']:
        path = REPO / item['card']
        checks.append({'id': item['id'], 'commands': commands(path, item['id']), 'negative': False, 'expected_orders': item['expected_diagram_orders']})
        cards.append({'id': item['id'], 'path': item['card'], 'sha256': sha256(path.read_bytes())})
    for item in contract['additional_parse_only_checks']:
        if item['process'] != PROCESSES[item['id']] or item.get('definitions', []) not in ([], [JET]):
            raise ValueError('Additional parse check changed from reviewed contract')
        checks.append({'id': item['id'], 'commands': [MODEL, PROTON] + item.get('definitions', []) + ['generate ' + item['process']], 'negative': item['id'].endswith('_negative')})
    config, mg5, identity, verifier = installation(args.installation)
    output = args.output.expanduser().resolve()
    local_scratch = REPO / '.local/phase6e'
    if output.exists() or output == REPO or (REPO in output.parents and local_scratch not in output.parents):
        raise ValueError('Use a new local directory outside tracked repository (or ignored .local/phase6e scratch)')
    if output == mg5 or mg5 in output.parents:
        raise ValueError('Do not write parser output into MG5 installation')
    output.mkdir(parents=True)
    request = output / 'parser_request.local.json'
    result = output / 'parser_result.json'
    request.write_text(json.dumps({'mg5_path': str(mg5), 'installation': str(args.installation.resolve()), 'checks': checks}, indent=2) + '\n')
    log = output / 'mg5_parse.log'
    python = Path(config['toolchain_prefix']) / 'bin/python'
    try:
        with log.open('wb') as stream:
            executed = subprocess.run([str(python), '-B', str(Path(__file__).resolve()), '--worker-request', str(request), '--worker-result', str(result)], cwd=output, stdout=stream, stderr=subprocess.STDOUT, timeout=300)
        if executed.returncode != 0:
            raise RuntimeError('MG5 parse worker failed; inspect retained local log')
        verifier.verify(config)
        if sha256(CONFIG.read_bytes()) != contract_sha_before or any(sha256((REPO / item['path']).read_bytes()) != item['sha256'] for item in cards):
            raise RuntimeError('Process card/configuration changed during parsing')
        parsed = json.loads(result.read_text())
        receipt = {'schema_version': 1, 'status': 'PASS_PARSE_ONLY', 'mg5_version': '3.5.16',
                   'mg5_source_commit': identity['source_commit'], 'mg5_source_tag': config['source_tag'],
                   'mg5_source_identity_unchanged_after_parsing': True,
                   'configuration_path': CONFIG.relative_to(REPO).as_posix(), 'configuration_sha256': sha256(CONFIG.read_bytes()),
                   'cards': cards, 'checks': parsed['checks'], 'events_generated': 0, 'output_or_launch_executed': False,
                   'model_merge_install_or_width_calculation_executed': False,
                   'physical_cross_sections_branching_ratios_and_decay_closure': 'NOT_EVALUATED',
                   'parser_source_sha256': sha256(Path(__file__).read_bytes())}
        (output / 'process_parse_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'status': receipt['status'], 'checks': len(checks), 'events_generated': 0}, indent=2))
        return 0
    except Exception as error:
        (output / 'partial_status.json').write_text(json.dumps({'status': 'PARTIAL_FAILED', 'events_generated': 0, 'error': type(error).__name__, 'reason': str(error)}, indent=2) + '\n')
        raise


if __name__ == '__main__':
    raise SystemExit(main())
