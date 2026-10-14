#!/usr/bin/env python3
"""Audit a no-event Pythia decay-table probe; never run a physics pilot."""
from __future__ import annotations
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
DECAY_IDS = ('Z_to_b_bbar', 'H_to_gamma_gamma')
BASELINE = REPO / 'simulation/pythia8/config/baseline_shower.cmnd'
CPP = REPO / 'simulation/zh_pilot/src/inspect_decay_tables.cxx'
OVERLAY = REPO / 'simulation/zh_pilot/cards/preferred_higgs_decay.cmnd'


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(data):
    def reject(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(data, parse_constant=reject)


def exact_probability(value):
    result = exact_decimal(value)
    if not result.is_finite() or not Decimal(0) <= result <= Decimal(1):
        raise ValueError('Probability outside finite [0,1]')
    return result


def exact_decimal(value):
    if not isinstance(value, str):
        raise ValueError('Require an exact decimal numeric string')
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('Invalid exact decimal numeric string') from error
    if not result.is_finite():
        raise ValueError('Require a finite decimal numeric string')
    return result


def ids(values):
    if not isinstance(values, list) or any(not isinstance(value, str) or value not in DECAY_IDS for value in values) or len(set(values)) != len(values):
        raise ValueError('Decay ledger requires unique canonical IDs')
    return set(values)


def validate_decay_contract(contract, allow_planning=True):
    if not isinstance(contract, dict):
        raise ValueError('Decay contract must be a JSON object')
    if type(allow_planning) is not bool:
        raise ValueError('allow_planning must be a literal Boolean')
    if type(contract.get('schema_version')) is not int or contract.get('schema_version') != 1 or contract.get('contract_id') != 'PHASE6F_ZH_DECAY_CONTRACT_V1':
        raise ValueError('Unknown decay contract')
    if contract.get('physical_decay_validation') != 'NOT_EXECUTED' or contract.get('external_lhe_weight_closure') != 'UNKNOWN':
        raise ValueError('This readiness contract cannot invent a physical closure receipt')
    if contract.get('physical_production_authorized') is not False or contract.get('apply_physical_BR_to_nominal_weights') is not False:
        raise ValueError('Physical production/nominal-weight BR modification forbidden')
    if contract.get('nominal_weight_columns') != ['input_contribution_pb', 'LHE_XWGTUP_pb', 'Pythia_Info_weight_pb', 'converter_weight_0_pb']:
        raise ValueError('Require the exact actual nominal weight column names')
    if contract.get('units') != {'cross_section': 'PB', 'LHE_XWGTUP': 'PB_FOR_ABS_IDWTUP4',
                                 'Pythia_Info_weight': 'PB_FOR_ABS_IDWTUP4', 'Pythia_sigmaGen': 'MB',
                                 'pb_per_mb': '1000000000'}:
        raise ValueError('Require the supported dimensional weight and pb/mb conversion convention')
    if contract.get('preferred_route') != 'B_MG5_ZBB_STABLE_H' or contract.get('preferred_lhe_profile') != 'ZH_ZBB_STABLE_H':
        raise ValueError('Preferred source/decay route changed')
    if ids(contract['required_physical_decay_ids']) != set(DECAY_IDS) or contract['source_included_decay_ids'] != ['Z_to_b_bbar']:
        raise ValueError('Missing/duplicate or incorrect source Z decay ledger')
    if contract['planning_missing_external_decay_ids'] != ['H_to_gamma_gamma'] or contract['already_applied_decay_ids'] != []:
        raise ValueError('Do not reapply source Z decay or invent an applied BR')
    if contract['nominal_decay_ids_in_pythia_weight'] != 'UNKNOWN' or contract['missing_external_decay_ids'] != 'UNKNOWN_UNTIL_MEASURED_CLOSURE':
        raise ValueError('External nominal BR inclusion is not yet measured')
    if contract['slha_policy']['readFrom'] != 0 or contract['pythia_forcing_switches'] != ['25:onMode = off', '25:onIfMatch = 22 22']:
        raise ValueError('Preferred route must keep source Z decay and audited SM width policy')
    if contract['mass_inputs_gev'] != {'Z': '91.188', 'H': '125'}:
        raise ValueError('MG5/Pythia mass input contract mismatch')
    if set(contract['decays']) != set(DECAY_IDS):
        raise ValueError('Both distinct canonical decay records required')
    for name, record in contract['decays'].items():
        if any(record.get(field) != 'UNKNOWN' for field in ('physical_adopted_BR', 'physical_adopted_total_width_gev', 'physical_adopted_partial_width_gev')) or record['model_value_status'] != 'PROBED_MODEL_VALUE_NOT_PHYSICAL_ADOPTION':
            raise ValueError('Model BR must not be silently adopted as a physical BR')
        total = exact_decimal(record['model_total_width_gev'])
        partial = exact_decimal(record['model_partial_width_gev'])
        br = exact_probability(record['model_inclusive_BR'])
        if not total.is_finite() or not partial.is_finite() or not 0 < partial <= total:
            raise ValueError('Missing/invalid model width source')
        if abs(partial / total - br) > Decimal('2e-12'):
            raise ValueError('Width/BR dependency inconsistent')
        if not record.get('model_source_evidence') or not record.get('physical_reference_comparison', {}).get('source_url'):
            raise ValueError('Width/BR provenance missing')
    probe_binding = contract.get('probe_evidence', {})
    if not probe_binding.get('sha256'):
        raise ValueError('Actual no-event probe binding missing')
    receipt = strict_json(checked_binding(probe_binding).read_text(encoding='utf-8'))
    if receipt.get('status') != 'PASS_NO_EVENT_TABLE_COMPATIBILITY_ONLY' or receipt.get('new_physics_events') != 0 or receipt.get('next_calls') != 0:
        raise ValueError('Actual no-event receipt scope changed')
    validate_probe(receipt['tables'])
    for binding in contract.get('file_bindings', []):
        checked_binding(binding)
    if not contract.get('file_bindings'):
        raise ValueError('Card/source hash bindings missing')
    table = receipt['tables']['inclusive_after_init']
    for decay_id, particle, products in (('Z_to_b_bbar', 'Z', [5, -5]), ('H_to_gamma_gamma', 'H', [22, 22])):
        record = contract['decays'][decay_id]
        actual = target_channel(table[particle], products)
        if (record['model_total_width_gev'] != table[particle]['total_width_gev'] or
                record['model_partial_width_gev'] != actual['partial_width_gev'] or
                record['model_inclusive_BR'] != actual['stored_inclusive_br']):
            raise ValueError('Contract model values differ from actual table probe')
    if not allow_planning:
        raise ValueError('Physical validation/weight closure still blocked; only planning allowed')
    return {'status': 'METHOD_ONLY', 'physical_decay_validation': 'NOT_EXECUTED',
            'external_lhe_weight_closure': 'UNKNOWN', 'events_generated': 0,
            'preferred_lhe_profile': 'ZH_ZBB_STABLE_H', 'source_included_decay_ids': ['Z_to_b_bbar'],
            'planning_missing_external_decay_ids': ['H_to_gamma_gamma']}


def checked_binding(binding):
    if not isinstance(binding, dict) or not isinstance(binding.get('path'), str) or not isinstance(binding.get('sha256'), str):
        raise ValueError('Malformed file hash binding')
    relative = Path(binding['path'])
    path = (REPO / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or REPO.resolve() not in path.parents:
        raise ValueError('Require a repository-relative safe binding')
    if len(binding['sha256']) != 64 or any(c not in '0123456789abcdef' for c in binding['sha256']) or file_sha(path) != binding['sha256']:
        raise ValueError('Bound source/card/probe bytes changed: ' + binding['path'])
    return path


def synthetic_missing_br_factor(*, source_included_decay_ids, nominal_additional_decay_ids,
                                already_applied_decay_ids, branching_ratios,
                                fixture_scope='SYNTHETIC_METHOD_ONLY'):
    if fixture_scope != 'SYNTHETIC_METHOD_ONLY':
        raise ValueError('This algebra helper supplies no physical closure or event weights')
    ledgers = [ids(value) for value in (source_included_decay_ids, nominal_additional_decay_ids, already_applied_decay_ids)]
    if any(ledgers[i] & ledgers[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError('Decay factor duplicated across source/additional/applied ledgers')
    if set(branching_ratios) != set(DECAY_IDS):
        raise ValueError('Both canonical decay BR records required')
    probabilities = {name: exact_probability(value) for name, value in branching_ratios.items()}
    missing = set(DECAY_IDS) - set.union(*ledgers)
    factor = Decimal(1)
    for name in sorted(missing):
        factor *= probabilities[name]
    return factor, sorted(missing)


def target_channel(table, products):
    expected = sorted(products)
    matches = [channel for channel in table['channels'] if sorted(channel['products']) == expected]
    if len(matches) != 1:
        raise ValueError('Target decay channel must occur exactly once')
    return matches[0]


def validate_probe(probe):
    if probe['pythia_version_integer'] != 8317 or probe['physical_events_generated'] != 0 or probe['next_calls'] != 0:
        raise ValueError('Probe must be pinned 8.317 with zero events/next calls')
    if probe['status'] != 'PASS_NO_EVENT_DECAY_TABLE_PROBE':
        raise ValueError('Probe did not complete')
    for name in ('inclusive_after_init', 'forced_A_Z_and_H_after_init', 'preferred_B_H_only_after_init'):
        state = probe[name]
        if (state['initialized_without_process'] is not True or state['process_level_all'] is not False or
                state['parton_level_all'] is not False or state['hadron_level_all'] is not False or
                state['slha_read_from'] != 0 or state['pdf_p_set'] != '8' or
                state['frame_type'] != 1 or state['n_accepted'] != 0):
            raise ValueError('No-process initialization/event-count contract failed')
        expected_Z_binary64 = Decimal(format(float('91.188'), '.17g'))
        if Decimal(state['Z']['mass_gev']) != expected_Z_binary64 or Decimal(state['H']['mass_gev']) != Decimal('125'):
            raise ValueError('MG5/Pythia target mass mismatch')
        for particle, products in (('Z', [5, -5]), ('H', [22, 22])):
            table = state[particle]
            channel = target_channel(table, products)
            total = Decimal(table['total_width_gev'])
            partial = Decimal(channel['partial_width_gev'])
            br = exact_probability(channel['stored_inclusive_br'])
            if not total.is_finite() or not partial.is_finite() or total <= 0 or not 0 < partial <= total:
                raise ValueError('Missing/nonfinite/nonpositive model widths')
            if abs(partial / total - br) > Decimal('2e-12'):
                raise ValueError('Initialized model partial/total width differs from stored inclusive BR')
    for name, forced in (('forced_A_Z_and_H_after_init', ('Z', 'H')), ('preferred_B_H_only_after_init', ('H',))):
        for particle in forced:
            table = probe[name][particle]
            products = [5, -5] if particle == 'Z' else [22, 22]
            enabled = [channel for channel in table['channels'] if channel['on_mode'] in (1, 2)]
            if len(enabled) != 1 or sorted(enabled[0]['products']) != sorted(products):
                raise ValueError('Forced table does not select exactly the requested channel')
    if probe['preferred_B_H_only_after_init']['Z'] != probe['inclusive_after_init']['Z']:
        raise ValueError('Preferred route unexpectedly changed unforced Z table')
    for particle in ('Z', 'H'):
        reference = probe['inclusive_after_init'][particle]
        for name in ('forced_A_Z_and_H_after_init', 'preferred_B_H_only_after_init'):
            forced = probe[name][particle]
            if forced['total_width_gev'] != reference['total_width_gev']:
                raise ValueError('Forcing unexpectedly changed model total width')
            for original, selected in zip(reference['channels'], forced['channels'], strict=True):
                for key in ('stored_inclusive_br', 'partial_width_gev', 'products', 'me_mode', 'index'):
                    if original[key] != selected[key]:
                        raise ValueError('Forcing changed inclusive model decay data')
    return 'PASS_NO_EVENT_TABLE_COMPATIBILITY_ONLY'


def run_probe(args):
    config = strict_json(args.installation.read_text())
    prefix = Path(config['pythia_prefix']).resolve()
    xml = Path(config['xml_path']).resolve()
    output = args.output.expanduser().resolve()
    scratch = REPO / '.local/phase6f'
    if output.exists() or output == prefix or prefix in output.parents or (REPO in output.parents and scratch not in output.parents):
        raise ValueError('Choose a fresh local probe directory outside repository/installation (or .local/phase6f scratch)')
    env = dict(os.environ)
    env['PYTHIA8DATA'] = str(xml)
    env['LD_LIBRARY_PATH'] = os.pathsep.join([str(prefix / 'lib'), str(Path(config['hepmc3_prefix']) / 'lib')])
    sys.path.insert(0, str(REPO / 'simulation/pythia8/scripts'))
    import shower_sample
    saved = dict(os.environ)
    try:
        os.environ.update(env)
        before = shower_sample.verify_installation(config)
        source_sha = file_sha(CPP)
        baseline_sha = file_sha(BASELINE)
        overlay_sha = file_sha(OVERLAY)
        output.mkdir(parents=True)
        binary = output / 'inspect_decay_tables'
        raw = output / 'raw_decay_tables.json'
        log = output / 'probe.local.log'
        compiler = shutil.which('g++')
        if not compiler:
            raise ValueError('Existing g++ compiler unavailable; no installation attempted')
        command = [compiler, '-std=c++20', '-O2', '-I' + str(prefix / 'include'),
                   '-I' + str(REPO / 'simulation/pythia8/include'), str(CPP), '-L' + str(prefix / 'lib'),
                   '-Wl,-rpath,' + str(prefix / 'lib'), '-lpythia8', '-o', str(binary)]
        with log.open('wb') as stream:
            subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)
            linked = subprocess.check_output(['ldd', str(binary)], env=env, text=True)
            if 'not found' in linked:
                raise ValueError('Probe library dependency unavailable')
            for line in linked.splitlines():
                if 'libpythia8.so' in line:
                    loaded = Path(line.split('=>', 1)[1].split()[0]).resolve()
                    if loaded != (prefix / 'lib/libpythia8.so').resolve():
                        raise ValueError('Probe loaded a different Pythia library')
            subprocess.run([str(binary), str(xml), str(BASELINE), str(OVERLAY), str(raw)], env=env, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=60)
        after = shower_sample.verify_installation(config)
        stable_before = {key: value for key, value in before.items() if key != 'runtime_dependencies'}
        stable_after = {key: value for key, value in after.items() if key != 'runtime_dependencies'}
        if stable_before != stable_after or file_sha(CPP) != source_sha or file_sha(BASELINE) != baseline_sha or file_sha(OVERLAY) != overlay_sha:
            raise ValueError('Installation/probe source/baseline changed during probe')
        probe = strict_json(raw.read_text())
        validate_probe(probe)
        source_root = Path(config.get('pythia_source_root', Path.home() / '.local/share/atlas-hh-phase6b/src/pythia8317'))
        sources = ['src/SigmaProcess.cc', 'src/ProcessContainer.cc', 'src/PhaseSpace.cc', 'src/LesHouches.cc', 'src/ResonanceWidths.cc', 'src/Pythia.cc', 'src/Info.cc', 'include/Pythia8/Info.h', 'include/Pythia8Plugins/HepMC3.h', 'src/SLHAinterface.cc', 'src/BeamSetup.cc', 'share/Pythia8/xmldoc/PDFSelection.xml', 'share/Pythia8/xmldoc/ResonanceDecays.xml', 'share/Pythia8/xmldoc/ParticleDataScheme.xml']
        receipt = {'schema_version': 1, 'status': 'PASS_NO_EVENT_TABLE_COMPATIBILITY_ONLY',
                   'physical_decay_validation': 'NOT_EXECUTED', 'external_lhe_weight_closure': 'UNKNOWN',
                   'new_physics_events': 0, 'next_calls': 0, 'pythia_version': '8.317',
                   'pythia_source_commit': config['pythia_source_commit'],
                   'probe_cpp_sha256': source_sha, 'checker_python_sha256': file_sha(Path(__file__)),
                   'baseline_settings_path': BASELINE.relative_to(REPO).as_posix(), 'baseline_settings_sha256': baseline_sha,
                   'preferred_overlay_path': OVERLAY.relative_to(REPO).as_posix(), 'preferred_overlay_sha256': file_sha(OVERLAY),
                   'pythia_library_sha256': file_sha(prefix / 'lib/libpythia8.so'),
                   'particle_data_xml_sha256': file_sha(xml / 'ParticleData.xml'),
                   'versioned_primary_source_sha256': {name: file_sha(source_root / name) for name in sources},
                   'compiler_version': subprocess.check_output([compiler, '--version'], text=True).splitlines()[0],
                   'installation_identity_unchanged_after_probe': True, 'probe_binary_sha256': file_sha(binary),
                   'numeric_scope': 'Initialized Pythia model values and forced-table controls; not physical BR adoption or an external-LHE event run',
                   'tables': probe}
        (output / 'decay_tables.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'status': receipt['status'], 'events': 0, 'output': str(args.output)}, indent=2))
        return 0
    finally:
        os.environ.clear()
        os.environ.update(saved)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, default=Path(os.environ.get('PYTHIA8_LOCAL_CONFIG', REPO / '.local/pythia8_installation.json')))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-evidence', type=Path)
    args = parser.parse_args()
    if args.verify_evidence:
        receipt = strict_json(args.verify_evidence.read_text())
        print(validate_probe(receipt['tables']))
        return 0
    if not args.output:
        parser.error('--output NEW_LOCAL_DIRECTORY required for actual no-event probe')
    return run_probe(args)


if __name__ == '__main__':
    raise SystemExit(main())
