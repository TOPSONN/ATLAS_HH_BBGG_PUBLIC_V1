#!/usr/bin/env python3
"""ZH100 self-service controller: dry-run by default choice, separate explicit gate."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import json
import os
import signal
import sys
import time
import uuid
from decimal import Decimal

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO/'simulation/zh_pilot/scripts'))
sys.path.insert(0, str(REPO/'simulation/zh_pilot/phase6g/scripts'))
from simulation.zh_pilot.phase6g.common import (ACK, BASE, Monitor, availability, bridge_identity,
    claim_ticket, request, require, save_json, sha_file, strict_json, validate_ticket, reserve_campaign, CAMPAIGN)
from prepare_pilot import (bound_bundle, load_json, safe_output, protected_paths,
    create_plan, cross_contract_check)
from check_environment import verify_environment


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--process', required=True)
    p.add_argument('--events', required=True, type=int)
    p.add_argument('--seed', required=True, type=int)
    p.add_argument('--energy', required=True, type=float)
    p.add_argument('--output', type=Path)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--max-hours', type=float, default=2)
    p.add_argument('--max-disk-gb', type=float, default=5)
    return p


def semantics(policy):
    from validate_profiles import validate_card_contract, validate_profile_config
    from check_decay_tables import validate_decay_contract
    folder = REPO/'simulation/zh_pilot/config'
    gen = load_json(folder/'generator_contract.json')
    decay = load_json(folder/'decay_contract.json')
    profiles = load_json(folder/'input_profiles.json')
    return {'generator': validate_card_contract(gen), 'decay': validate_decay_contract(decay),
            'profiles': validate_profile_config(profiles),
            'cross_contracts': cross_contract_check(gen, decay, profiles, policy)}


def prepare(args, requested, identity, bindings, installed, available, output, policy, snapshots, claimed_authorization=None):
    from simulation.zh_pilot.phase6g.mg5_stage import prepare_mg5_stage
    legacy = create_plan(args, policy, snapshots, installed, available, output, semantic=semantics(policy))
    mgcfg = strict_json(REPO/'.local/mg5_installation.json')
    mgplan = prepare_mg5_stage(output/'mg5', repo=REPO, installation=mgcfg,
                             seed=args.seed, events=args.events, energy_gev=args.energy)
    claimed = claimed_authorization is not None
    if claimed:
        ticket_path = Path(claimed_authorization['path'])
        require(sha_file(ticket_path) == claimed_authorization['sha256'] and
                ticket_path.name.endswith('.consumed-'+claimed_authorization['id']), 'unclaimed authorization descriptor')
        validate_ticket(ticket_path, requested, identity)
    plan = {'schema_version': 1, 'status': 'PREPARED_FOR_CLAIMED_EXECUTION' if claimed else 'PASS_PHASE6G_DRY_RUN_NOT_AUTHORIZED',
            'task': 'PHASE6G_ZH_100_EVENT_PHYSICAL_PILOT_V1', 'requested': requested,
            'reviewed_base_head': BASE, 'bridge_sha256': identity, 'bridge_sources': bindings,
            'authorization_command_required': ACK, 'physical_execution_authorized': claimed,
            'claimed_authorization': claimed_authorization,
            'events_generated': 0, 'original_source_denominator': 100,
            'smoke_scope': 'first10 of same100 source; not extra independent hard statistics',
            'physical_BR_adoption': None, 'exclusive_physical_normalization': 'BLOCKED',
            'resources': available, 'installed_identity': installed, 'mg5_prepared': mgplan,
            'frozen_card_config_files': len(legacy['cards_and_contracts']),
            'future_outputs': {'lhe': 'mg5/process/Events/zh100/unweighted_events.lhe.gz',
                'prefix10': 'pythia/prefix10/shower.hepmc3', 'hepmc': 'pythia/full100/shower.hepmc3',
                'hepmc_gz': 'pythia/full100/shower.hepmc3.gz', 'root': 'delphes/detector.root',
                'cutflow': 'delphes/cutflow.csv', 'receipts': 'validation/'},
            'gates': {'A': 'PASS_HISTORY_CHECKED_SEPARATELY', 'B': 'PASS_FROZEN_CONFIGURATION',
                      'C': 'PASS_CLAIMED_ONE_USE_AUTHORIZATION' if claimed else 'NOT_AUTHORIZED',
                      **{k: 'NOT_EVALUATED' for k in 'DEFGHIJKL'}},
            'scope': 'actual preflight and text preparation only; no integration/next/Delphes execution'}
    save_json(output/'execution_plan.json', plan)
    return plan


def native_stage_receipt(output, stage, requested, identity, ticket, ticket_sha, source, build):
    child = output/'pythia'/stage
    require(not child.exists(), 'downstream stage already exists; no automatic rerun')
    child.mkdir(parents=True)
    record = {'schema_version': 1, 'status': 'AUTHORIZED_EXECUTION_IN_PROGRESS',
        'authorization_command': ACK, 'reviewed_base_head': BASE, 'source_request': requested,
        'ticket_id': ticket['ticket_id'], 'bridge_sha256': identity,
        'authorization_receipt_sha256': ticket_sha, 'child_stage': stage, 'child_output': str(child),
        'source_total_events': 100, 'source_original_sha256': source['original_sha256'],
        'source_lhe_path': str(source['plain_path']), 'source_lhe_sha256': source['plain_sha256'],
        'source_index_path': str(source['index_path']), 'source_index_sha256': source['index_sha256'],
        'native_runner_sha256': build['binaries']['zh_shower']['sha256'],
        'native_validator_sha256': build['binaries']['validate_zh_hepmc3']['sha256'],
        'controller_sha256': sha_file(Path(__file__)), 'created_at_utc': datetime.now(timezone.utc).isoformat()}
    record['deadline_epoch_seconds'] = min(datetime.fromisoformat(ticket['expires_at_utc']).timestamp(),
        time.time()+max(0, requested['max_hours']*3600-(time.monotonic()-source['controller_started_monotonic'])))
    save_json(child/'execution_authorization.json', record)
    return child/'execution_authorization.json'


def weight_ledger(source, shower_directory):
    from simulation.zh_pilot.phase6g.validate_lhe import validate_downstream_binding
    path = Path(shower_directory)/'hepmc_ancestry.jsonl'
    require(path.stat().st_size <= 32*1024**2, 'oversized ancestry/weight sidecar')
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    records = [{'source_file_sha256': source['source_file_sha256'],
                'source_event_index': row['source_event_index'],
                'source_event_sha256': row['source_event_content_hash'],
                'source_total_events': row['source_total_events'],
                'weight_names': row['weight_names'], 'weight_values': row['weights_pb']} for row in rows]
    binding = validate_downstream_binding(source, records, expected_output_count=100)
    ratios = []
    zero = 0
    for row in records:
        raw, info = Decimal(str(row['weight_values'][1])), Decimal(str(row['weight_values'][2]))
        if raw:
            ratios.append(info/raw)
        else:
            zero += 1
    model_br = Decimal('0.0022965313147512443')
    summary_path = Path(shower_directory)/'run_summary.json'
    actual_model = strict_json(summary_path)['initialized_higgs_decay']
    actual_br = Decimal(str(actual_model['inclusive_model_BR_gamma_gamma']))
    require(actual_br.is_finite() and 0 < actual_br <= 1 and
            Decimal(str(actual_model['conditional_forced_probability'])) == 1,
            'invalid actual inclusive/conditional initialized H model table')
    tables = {'inclusive_table_sha256':'decay_tables_inclusive_initialized.json',
              'effective_table_sha256':'decay_tables_initialized.json',
              'original_preinit_table_sha256':'decay_tables_original_preinit.json',
              'original_particle_data_sha256':'original_particle_data.xml',
              'inclusive_particle_data_sha256':'inclusive_initialized_particle_data.xml',
              'effective_particle_data_sha256':'effective_particle_data.xml'}
    for key, filename in tables.items():
        require(sha_file(Path(shower_directory)/filename) == actual_model[key], 'actual initialized model/table snapshot changed')
    identity_transfer = bool(ratios) and all(abs(r-1) <= Decimal('1e-10') for r in ratios)
    model_transfer = bool(ratios) and all(abs(r-model_br) <= Decimal('1e-10')*max(1, abs(r)) for r in ratios)
    initialized_transfer = bool(ratios) and all(abs(r-actual_br) <= Decimal('1e-10')*max(1, abs(r)) for r in ratios)
    return {'schema_version': 1, 'status': 'OBSERVED_RAW_WEIGHT_TRANSFER_ONLY', 'binding': binding,
        'source_included_decay_ids': ['Z_to_b_bbar'], 'source_Z_BR_reapplied': False,
        'physical_BR_adoption': None, 'external_BR_factors_applied': [],
        'planning_missing_decay_ids': ['H_to_gamma_gamma'], 'full_original_source_denominator': 100,
        'nominal_transfer_class': 'IDENTITY' if identity_transfer else 'MATCHES_PHASE6F_MODEL_BR_REFERENCE_ONLY' if model_transfer else 'UNRESOLVED',
        'Info_to_LHE_ratio_min': str(min(ratios)) if ratios else None,
        'Info_to_LHE_ratio_max': str(max(ratios)) if ratios else None,
        'zero_weight_events_ratio_unidentifiable': zero,
        'Pythia_model_BR_reference_only': str(model_br), 'CERN_YR4_BR_reference_only': '0.002270',
        'actual_initialized_higgs_decay': actual_model, 'actual_model_summary_sha256': sha_file(summary_path),
        'ratio_matches_actual_initialized_model_BR_numeric_only': initialized_transfer,
        'ratio_match_establishes_factor_inclusion': False,
        'physical_BR_factor': None, 'exclusive_cross_section_pb': None,
        'exclusive_physical_normalization': 'BLOCKED_BR_WEIGHT_CLOSURE',
        'scope': 'measured native named columns; identity does not authorize physical BR adoption or prove all corrections absent'}


def preserve_observed_counters(output, state, executions):
    """Read actual partial receipts; a failed validation never resets writes to0."""
    output = Path(output)
    stages = {row['stage'] for row in executions}
    observations = {}
    lhe_path = output/'mg5/process/Events/zh100/unweighted_events.lhe.gz'
    if 'mg5_100_event_generation' in stages:
        state['MG5_events_generated'] = 'UNKNOWN_UNTIL_COMPLETE_RECORD_COUNT'
    if lhe_path.is_file():
        try:
            from simulation.zh_pilot.phase6g.validate_lhe import bounded_bytes, parse_xml
            raw, digest = bounded_bytes(lhe_path)
            xml = parse_xml(raw)
            count = len(xml.findall('event'))
            state['MG5_events_generated'] = count
            observations['MG5_complete_XML_event_count'] = {'events':count,'file_sha256':digest,
                'scope':'actual complete CRC/XML count; physics validation separate'}
        except (ValueError, OSError) as error:
            observations['MG5_complete_XML_event_count'] = {'events':'UNKNOWN','error':str(error)}
    for name in ('prefix10','full100'):
        directory = output/'pythia'/name
        if 'zh_shower_'+name in stages and name == 'full100':
            state['Pythia_events_written'] = 'UNKNOWN_UNTIL_NATIVE_RECEIPT'
        if 'zh_reader_'+name in stages and name == 'full100':
            state['HepMC_validated_events'] = 'UNKNOWN_UNTIL_NATIVE_RECEIPT'
        for filename in ('run_summary.json','zh_hepmc_validation.json','generic_physics_validation.json'):
            path = directory/filename
            if path.is_file():
                try:
                    value = strict_json(path)
                    observations[name+'/'+filename] = value
                    if name == 'full100' and filename == 'run_summary.json':
                        state['Pythia_events_written'] = value.get('N_written','UNKNOWN')
                    if name == 'full100' and filename == 'zh_hepmc_validation.json':
                        state['HepMC_validated_events'] = value.get('N_passed_validation','UNKNOWN')
                except (ValueError, OSError) as error:
                    observations[name+'/'+filename] = {'error':str(error),'counts':'UNKNOWN'}
    if 'delphes_full100' in stages:
        state['Delphes_ROOT_entries'] = 'UNKNOWN_UNTIL_NATIVE_READBACK'
    native = output/'delphes/native_validation.json'
    if native.is_file():
        try:
            value = strict_json(native)
            observations['Delphes_native_readback'] = value
            state['Delphes_ROOT_entries'] = value.get('ROOT_entries','UNKNOWN')
        except (ValueError, OSError) as error:
            observations['Delphes_native_readback'] = {'error':str(error),'counts':'UNKNOWN'}
    state['actual_partial_observations'] = observations


def execute(output, requested, ticket, consumed, ticket_sha, plan, installed_before, started, campaign):
    from simulation.zh_pilot.phase6g.mg5_stage import execute_mg5_stage
    from simulation.zh_pilot.phase6g.validate_lhe import validate_file, ValidationError
    from simulation.zh_pilot.phase6g.delphes_stage import native_environment, build_root_analyzer, execute_delphes
    from build_stage import compile_bridge
    from shower_stage import source_index_bytes, run_stage
    mgcfg = strict_json(REPO/'.local/mg5_installation.json')
    pycfg = strict_json(REPO/'.local/pythia8_installation.json')
    delcfg = strict_json(REPO/'.local/delphes_installation.json')
    monitor = Monitor(output, requested, native_environment(delcfg, pycfg, mgcfg, output), started,
                      readonly_roots=(mgcfg['mg5_path'], mgcfg['toolchain_prefix']))
    monitor.install_signals()
    state = {'schema_version': 1, 'status': 'AUTHORIZED_EXECUTION_IN_PROGRESS',
        'task': plan['task'], 'request': requested, 'bridge_sha256': plan['bridge_sha256'],
        'authorization_receipt': {'path': str(consumed), 'sha256': ticket_sha, 'id': ticket['ticket_id']},
        'ticket_id': ticket['ticket_id'],
        'campaign_reservation': campaign,
        'physical_BR_adoption': None, 'exclusive_physical_normalization': 'BLOCKED_BR_WEIGHT_CLOSURE',
        'MG5_events_generated': 0, 'Pythia_events_written': 0, 'HepMC_validated_events': 0,
        'Delphes_ROOT_entries': 0, 'stages': {},
        'gates': {'A': 'PASS_RETAINED_ENVIRONMENT_PRECHECK', 'B': 'PASS_FROZEN_CONFIGURATION',
                  'C': 'PASS_EXPLICIT_ONE_USE_AUTHORIZATION', **{k: 'NOT_EVALUATED' for k in 'DEFGHIJKL'}}}
    def guard(argv, cwd, stage, env=None, expected_exit_code=0):
        require(bridge_identity()[0] == plan['bridge_sha256'] and sha_file(consumed) == ticket_sha,
                'reviewed source or consumed human authorization changed during run')
        require(strict_json(consumed) == ticket, 'authorization content changed')
        return monitor.run_command(argv, cwd, stage, env=env, expected_exit_code=expected_exit_code)
    save_json(output/'run_manifest.json', state)
    try:
        validation = output/'validation';validation.mkdir()
        native_build = compile_bridge(output/'native_build', pycfg, run_command=guard)
        root_build = build_root_analyzer(output/'root_build', delcfg, run_command=guard)
        state['stages']['native_build'] = native_build;state['stages']['root_build'] = root_build
        mg = execute_mg5_stage(plan['mg5_prepared'], run_command=guard)
        state['MG5_reported_generated_events'] = mg['generation']['events']
        mg['authorization_receipt'] = state['authorization_receipt']
        save_json(validation/'mg5_execution.json', mg)
        cards = {'profile': 'ZH_ZBB_STABLE_H', **{k: Path(v['path']).read_text(encoding='utf-8')
                 for k, v in plan['mg5_prepared']['cards'].items()}}
        try:
            lhe = validate_file(mg['lhe_path'], expected_seed=requested['seed'], card_contract=cards, provenance=mg)
        except ValidationError as error:
            save_json(validation/'lhe_validation.json', error.report)
            state['MG5_events_generated'] = error.report.get('actual_events', 'UNKNOWN')
            state['gates']['E'] = 'FAILED_PHYSICAL_VALIDATION'
            raise
        save_json(validation/'lhe_validation.json', lhe)
        state['MG5_events_generated'] = lhe['actual_events'];state['stages']['MG5'] = mg
        state['gates']['D'] = 'PASS_ACTUAL_100_RECORDS';state['gates']['E'] = 'PASS_LHE_RECORDS'
        plain = validation/'original_full100.lhe'
        with gzip.open(mg['lhe_path'], 'rb') as source, plain.open('xb') as target:
            while chunk := source.read(1024**2):
                monitor.check();target.write(chunk)
        require(sha_file(plain) == lhe['decompressed_file_sha256'], 'plain LHE differs from CRC-validated original')
        index = validation/'source_events.dat';index.write_bytes(source_index_bytes(lhe))
        source = {'original_sha256': lhe['source_file_sha256'], 'plain_path': plain, 'plain_sha256': sha_file(plain),
                  'index_path': index, 'index_sha256': sha_file(index), 'controller_started_monotonic': started}
        for stage in ('prefix10', 'full100'):
            auth = native_stage_receipt(output, stage, requested, plan['bridge_sha256'], ticket, ticket_sha, source, native_build)
            result = run_stage(authorization_file=auth, stage=stage,
                build_receipt=output/'native_build/build_receipt.json', source_validation=lhe,
                xml_path=pycfg['xml_path'], run_id=str(uuid.uuid4()), run_command=guard)
            state['stages'][stage] = result
            require(result['status'] == 'PASS_RAW_SHOWER_AND_HEPMC_RECORDS', 'downstream '+stage+' failed')
            save_json(validation/(stage+'_validation.json'), result)
        full = output/'pythia/full100';reader = state['stages']['full100']['reader_report']
        state['Pythia_events_written'] = 100;state['HepMC_validated_events'] = reader['N_readback']
        state['gates']['F'] = 'PASS_ACTUAL_H_Z_ANCESTRY';state['gates']['G'] = 'PASS_ACTUAL_READER_ASCII'
        ledger = weight_ledger(lhe, full);save_json(validation/'weight_and_BR_ledger.json', ledger)
        state['weight_and_BR_ledger'] = ledger;state['gates']['H'] = 'PASS_RAW_NAMED_COLUMN_TRANSFER'
        state['gates']['I'] = 'BLOCKED_PHYSICAL_BR_ADOPTION; NO_DUPLICATE_Z_FACTOR'
        shower = {'status': 'PASS_READER_ASCII_RECORDS', 'validated_events': reader['N_readback'],
            'hepmc_path': str(full/'shower.hepmc3'), 'hepmc_path_sha256': reader['decompressed_file_sha256'],
            'input_index_path': str(full/'input_event_index.dat'), 'input_index_path_sha256': reader['input_index_sha256'],
            'truth_index_path': str(full/'zh_truth_index.dat'), 'truth_index_path_sha256': reader['truth_index_sha256']}
        reco = execute_delphes(output/'delphes', shower, delcfg, root_build, requested['seed'], guard)
        save_json(validation/'detector_validation.json', reco);state['stages']['Delphes'] = reco
        state['Delphes_ROOT_entries'] = reco['ROOT_entries'];state['gates']['J'] = 'PASS_ACTUAL_NATIVE_ROOT'
        state['gates']['K'] = 'PASS_RAW_COUNTS_AND_SOURCE_CONTRIBUTIONS_ONLY'
        # Deterministic gzip copy; immutable plain records remain for independent QA.
        with (full/'shower.hepmc3').open('rb') as source, (full/'shower.hepmc3.gz').open('xb') as destination:
            with gzip.GzipFile(filename='', mode='wb', fileobj=destination, mtime=0) as zipped:
                while chunk := source.read(1024**2):
                    monitor.check();zipped.write(chunk)
        require(verify_environment() == installed_before, 'retained environment changed during physical run')
        require(bridge_identity()[0] == plan['bridge_sha256'], 'bridge source changed during physical run')
        require(sha_file(mg['lhe_path']) == lhe['source_file_sha256'], 'original source LHE changed during downstream processing')
        monitor.check()
        state['status'] = 'BLOCKED_BR_WEIGHT_CLOSURE'
        state['scope'] = 'complete raw simulation diagnostics if all actual gates above pass; no adopted exclusive physical normalization'
        state['gates']['L'] = 'NOT_EVALUATED_PUBLICATION_REQUIRES_SEPARATE_SELECTED_REFERENCE_QA'
        return state
    except BaseException as error:
        attempted_generation = any(row['stage']=='mg5_100_event_generation' for row in monitor.executions)
        state['status'] = 'PARTIAL_PHYSICAL_PILOT' if attempted_generation else 'FAILED_PRE_GENERATION_STAGE'
        state['error'] = str(error)
        raise
    finally:
        try:
            preserve_observed_counters(output, state, monitor.executions)
        except (OSError, ValueError, RuntimeError) as error:
            state['partial_observation_error'] = str(error)
        try:
            state['resources_measured'] = monitor.metrics()
        except (OSError, ValueError, RuntimeError) as error:
            state['resources_measured'] = {'status': 'PARTIAL_RESOURCE_ACCOUNTING', 'error': str(error)}
        save_json(output/'run_manifest.json', state)
        monitor.restore_signals()


def main(argv=None):
    started = time.monotonic();args = parser().parse_args(argv)
    try:
        authorization_path = os.environ.get('PHASE6G_AUTHORIZATION_FILE')
        if not args.dry_run:
            require(authorization_path, 'NOT_AUTHORIZED: wait for '+ACK+' and its separate one-use receipt')
            require(not CAMPAIGN.exists(), 'PHASE6G_SINGLE_RUN_LIMIT: one source attempt already reserved')
        requested = request(args)
        identity, bindings = bridge_identity()
        if not args.dry_run:
            validate_ticket(authorization_path, requested, identity)
        policy, snapshots = bound_bundle()
        semantics(policy)
        installed = verify_environment()
        candidate = args.output or Path.home()/'simulations/zh_pilot_plans'/('phase6g_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
        output = safe_output(candidate, protected_paths())
        requested['output'] = str(output)
        available = availability(output, requested)
        require(requested['max_disk_gb']*1024**3 >= sum(map(len, snapshots.values()))+128*1024,
                'BLOCKED_RESOURCES: disk budget cannot contain frozen text/driver reserve')
        require(time.monotonic()-started < requested['max_hours']*3600,
                'BLOCKED_RESOURCES: preflight reached total elapsed ceiling')
        ticket = consumed = ticket_sha = campaign = None
        if not args.dry_run:
            ticket, consumed, ticket_sha = claim_ticket(authorization_path, requested, identity)
            campaign = reserve_campaign(requested, ticket['ticket_id'], identity)
        descriptor = {'path': str(consumed), 'sha256': ticket_sha, 'id': ticket['ticket_id']} if consumed else None
        plan = prepare(args, requested, identity, bindings, installed, available, output, policy, snapshots, descriptor)
        if args.dry_run:
            print(json.dumps({'status': plan['status'], 'output': str(output), 'events_generated': 0,
                              'authorization': 'NOT_AUTHORIZED', 'bridge_sha256': identity}, indent=2))
            return 0
        result = execute(output, requested, ticket, consumed, ticket_sha, plan, installed, started, campaign)
        print(json.dumps({'status': result['status'], 'output': str(output),
                          'events_generated': result['MG5_events_generated'], 'exclusive_physical_normalization': 'BLOCKED'}, indent=2))
        return 0  # Raw diagnostics completion is separate from physical normalization.
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print('BLOCKED_OR_FAILED: '+str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
