#!/usr/bin/env python3
"""Local ZH readiness planning. Physical execution is deliberately disabled."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from check_environment import verify_environment

REPO = Path(__file__).resolve().parents[3]
MODULE = REPO/'simulation/zh_pilot'
CONFIG = MODULE/'config'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    data = Path(path).read_bytes()
    if len(data) > 2*1024**2:
        raise ValueError('oversized planning configuration')
    def reject(value):
        raise ValueError('nonfinite JSON number: '+value)
    def unique(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:
                raise ValueError('duplicate JSON key: '+key)
            obj[key]=value
        return obj
    obj = json.loads(data, parse_constant=reject,object_pairs_hook=unique)
    if not isinstance(obj, dict) or type(obj.get('schema_version')) is not int or obj['schema_version'] != 1:
        raise ValueError('unreviewed schema')
    return obj


def bound_bundle(repo=REPO):
    repo = Path(repo).resolve()
    module = repo/'simulation/zh_pilot'
    bundle = load_json(module/'config/bundle.json')
    if bundle.get('physical_production_authorized') is not False:
        raise ValueError('Phase6F bundle cannot authorize physical production')
    files = bundle.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('missing frozen card/config bundle')
    snapshots = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {'path','sha256'}:
            raise ValueError('invalid bundle descriptor')
        path = item['path']
        if not isinstance(path, str) or not path.startswith('simulation/zh_pilot/'):
            raise ValueError('bundle escapes ZH module')
        if path in snapshots or any(part in {'.','..'} for part in path.split('/')) or '\\' in path:
            raise ValueError('duplicate/unsafe bundle path')
        full = (repo/path).resolve()
        if not full.is_relative_to(module.resolve()) or (repo/path).is_symlink() or not full.is_file():
            raise ValueError('missing/outside bundle file')
        if full.suffix not in {'.json','.dat','.mg5','.cmnd'}:
            raise ValueError('unreviewed bundle file type')
        raw = full.read_bytes()
        if not isinstance(item['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', item['sha256']) or sha(raw) != item['sha256']:
            raise ValueError('frozen card/config changed: '+path)
        snapshots[path] = raw
    required = {f'simulation/zh_pilot/config/{name}.json' for name in
                ('preflight_policy','generator_contract','decay_contract','input_profiles')}
    if not required <= set(snapshots):
        raise ValueError('incomplete physics planning bundle')
    for path in required:
        load_json(repo/path)
    actual_cards = {p.relative_to(repo).as_posix() for p in (module/'cards').rglob('*') if p.is_file()}
    if not actual_cards or not actual_cards <= set(snapshots):
        raise ValueError('unbound generator/decay card')
    policy = load_json(repo/'simulation/zh_pilot/config/preflight_policy.json')
    if policy.get('physical_production_authorized') is not False or policy.get('physical_execution_gate') != 'NOT_AUTHORIZED':
        raise ValueError('unauthorized policy change')
    if policy.get('process') != 'zh' or any(type(policy.get(key)) is not int or policy[key]!=value for key,value in
            (('events',100),('energy_gev',13000),('workers',1))):
        raise ValueError('unreviewed pilot request policy')
    if policy.get('required_decay_ids') != ['Z_to_b_bbar','H_to_gamma_gamma']:
        raise ValueError('ambiguous decay IDs')
    return policy, snapshots


def validate_request(args):
    if type(args.events) is not int or type(args.seed) is not int or type(args.dry_run) is not bool or any(
            type(x) not in (int,float) for x in (args.energy,args.max_hours,args.max_disk_gb)):
        raise ValueError('literal integer/count/seed, Boolean dry-run and finite numeric limits required')
    if args.process != 'zh' or args.events != 100 or args.energy != 13000:
        raise ValueError('only the reviewed zh/100-event/13000-GeV readiness plan is supported')
    if not 1 <= args.seed <= 900000000:
        raise ValueError('seed must be in [1,900000000] for the proposed MG5/Pythia/Delphes seeds')
    if any(not math.isfinite(x) or x <= 0 for x in (args.max_hours,args.max_disk_gb)) or not math.isfinite(args.max_disk_gb*1024**3) or not math.isfinite(args.max_hours*3600):
        raise ValueError('finite positive time/disk administrative limits required')
    if not args.dry_run:
        raise ValueError('NOT_AUTHORIZED: physical execution and unvalidated decay/BR configurations are rejected; use --dry-run')


def cross_contract_check(generator,decay,profiles,policy):
    names=['input_contribution_pb','LHE_XWGTUP_pb','Pythia_Info_weight_pb','converter_weight_0_pb']
    if decay['nominal_weight_columns'] != names or profiles['nominal_weight_names'] != names:
        raise ValueError('generator/shower/profile named-weight convention is inconsistent')
    preferred=generator['preferred_profile']
    if decay['preferred_lhe_profile'] != preferred or decay['source_included_decay_ids'] != generator['profiles'][preferred]['source_included_decay_ids']:
        raise ValueError('source decay scope differs across contracts')
    for species in ('Z','H'):
        if Decimal(decay['mass_inputs_gev'][species]) != Decimal(str(generator['physics']['masses_gev'][species])) or \
           Decimal(decay['source_MG_widths_gev'][species]) != Decimal(str(generator['physics']['widths_gev'][species])):
            raise ValueError('source mass/width convention differs across contracts')
    if generator['pilot_policy']['events'] != policy['events'] or generator['pilot_policy']['energy_gev'] != policy['energy_gev'] or \
       profiles['target_independent_source_events'] != policy['events']:
        raise ValueError('original source denominator/request differs across contracts')
    return {'status':'METHOD_CONTRACTS_MUTUALLY_CONSISTENT','physical_validation':'NOT_EXECUTED'}


def safe_output(output, protected, repo=REPO):
    repo = Path(repo).resolve()
    raw = Path(output).expanduser()
    output = raw.resolve()
    if output.exists():
        raise ValueError('output exists; preserve it and choose a new directory')
    if any(c.isspace() or c in "\"';\r\n" for c in str(output)):
        raise ValueError('unsupported output path characters')
    for target in [repo,*map(Path,protected)]:
        target = target.resolve()
        if output == target or output.is_relative_to(target) or target.is_relative_to(output):
            raise ValueError('output overlaps repository/installed/protected data')
    return output


def resources(output, max_disk_gb):
    ancestor = Path(output)
    while not ancestor.exists():
        ancestor = ancestor.parent
    cpus = len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else (os.cpu_count() or 1)
    disk = shutil.disk_usage(ancestor)
    if type(max_disk_gb) not in (int,float) or not math.isfinite(max_disk_gb) or max_disk_gb <= 0 or not math.isfinite(max_disk_gb*1024**3):
        raise ValueError('invalid administrative disk budget')
    budget = math.ceil(max_disk_gb*1024**3)
    if disk.free < budget:
        raise ValueError('available disk cannot support the administrative budget')
    memory = {}
    if Path('/proc/meminfo').is_file():
        for line in Path('/proc/meminfo').read_text().splitlines():
            key,value = line.split(':',1)
            if key in {'MemAvailable','MemTotal'}:
                memory[key] = int(value.split()[0])*1024
    return {'available_logical_cpus':cpus,'requested_workers':1,
            'cpu_requirement': 'one worker requested; integration cost UNKNOWN',
            'ram_available_bytes':memory.get('MemAvailable','UNKNOWN'),
            'ram_total_bytes':memory.get('MemTotal','UNKNOWN'),
            'disk_free_bytes':disk.free,'administrative_disk_budget_bytes':budget,
            'disk_budget_units':'GiB (1024^3 bytes)',
            'projected_wall_seconds':'UNKNOWN','projected_peak_ram_bytes':'UNKNOWN',
            'projected_storage_bytes':'UNKNOWN',
            'scope':'measured current availability; no ZH throughput/RAM/storage benchmark or capacity guarantee'}


def configured_protected_paths(cfg):
    result=[]
    for key in ('mg5_path','toolchain_prefix','pythia_prefix','hepmc3_prefix','delphes_prefix','root_prefix',
                'source_dir','source_path','build_dir'):
        if cfg.get(key): result.append(str(cfg[key]))
    for key in ('runner_path','validator_path','analyzer_path','delphes_binary'):
        if cfg.get(key): result.append(str(Path(cfg[key]).parent))
    source_paths=[str(Path(path).parent) for path in cfg.get('source_sha256',{})]
    result.extend(source_paths)
    if source_paths:
        try:
            common=Path(os.path.commonpath(source_paths))
            if common!=Path(common.anchor): result.append(str(common))
        except ValueError:
            pass
    for value in cfg.get('phase6b_runs',{}).values():
        result.extend([value,str(Path(value).parent)])
    # Also preserve the retained isolated compiler/source/build state roots.
    for value in result[:]:
        path=Path(value)
        for parent in [path,*path.parents]:
            if re.fullmatch(r'atlas-hh-phase6[a-z]',parent.name):
                result.append(str(parent));break
    return result


def protected_paths(repo=REPO):
    result=[]
    for name in ('mg5_installation','pythia8_installation','delphes_installation'):
        cfg=json.loads((Path(repo)/f'.local/{name}.json').read_text())
        result.extend(configured_protected_paths(cfg))
    # Existing full detector runs must never become the planning output.
    for path in result[:]:
        if '/pythia8_runs/' in path:
            result.append(str(Path(path).parent.parent/'delphes_runs'))
    return result


def requested_run_card(raw, args):
    """Prepare exact text for the allowed per-request seed/count/beam overrides."""
    text=raw.decode('utf-8')
    overrides={'nevents':str(args.events),'iseed':str(args.seed),
               'ebeam1':format(args.energy/2,'.17g'),'ebeam2':format(args.energy/2,'.17g')}
    for key,value in overrides.items():
        pattern=re.compile(r'^(\s*)[^\n=!]+(\s*=\s*'+re.escape(key)+r'\b[^\n]*)$',re.M)
        text,count=pattern.subn(lambda m:m[1]+value+m[2],text)
        if count!=1:
            raise ValueError('missing/duplicate run-card request field: '+key)
    return text.encode('utf-8'),overrides


def create_plan(args, policy, snapshots, installed, available, output, repo=REPO, semantic=None):
    # Recheck every frozen file immediately before local text creation.
    for path,raw in snapshots.items():
        if (Path(repo)/path).read_bytes()!=raw:
            raise ValueError('configuration changed during preflight')
    run_path='simulation/zh_pilot/cards/run_card.dat'
    if run_path not in snapshots:
        raise ValueError('frozen full run card required')
    prepared_run,overrides=requested_run_card(snapshots[run_path],args)
    plan={'schema_version':1,'status':'PASS_DRY_RUN_WITH_PHYSICAL_GATES_BLOCKED',
          'physical_execution_gate':'NOT_AUTHORIZED','new_physics_events_generated':0,
          'publication':'LOCAL_ONLY_NO_AUTOMATIC_GIT',
          'requested':{'process':args.process,'events':args.events,'energy_gev':args.energy,
                       'seeds':{'MG5':args.seed,'Pythia':args.seed,'Delphes':args.seed},
                       'max_hours':args.max_hours,'max_disk_gb':args.max_disk_gb},
          'seed_scope':'proposed separate generator streams; actual independence and source-event identity checked in future pilot',
          'resources':available,'installed_identity':installed,'semantic_contract_checks':semantic,
          'cards_and_contracts':[{'path':p,'sha256':sha(raw)} for p,raw in sorted(snapshots.items())],
          'prepared_run_card':{'path':'prepared/run_card.dat','sha256':sha(prepared_run),
               'template_sha256':sha(snapshots[run_path]),'request_overrides':overrides,
               'scope':'complete future card text prepared only; not parsed by a physical generation job'},
          'expected_future_outputs':policy['expected_outputs'],
          'expected_output_scope':'planned relative paths only; no LHE/HepMC/ROOT created or validated',
          'blocked_gates':['subsequent explicit physical-pilot authorization','actual source integration and decay ancestry',
             'actual widths/effective BR tables','external LHE/Info/HepMC nominal weight closure',
             'exactly-once production/exclusive BR ledger','new native detector-profile execution'],
          'created_utc':datetime.now(timezone.utc).isoformat()}
    output.mkdir(parents=True,exist_ok=False)
    cards=output/'frozen';cards.mkdir()
    for path,raw in sorted(snapshots.items()):
        destination=cards/Path(path).relative_to('simulation/zh_pilot')
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw)
    prepared=output/'prepared';prepared.mkdir()
    (prepared/'run_card.dat').write_bytes(prepared_run)
    (output/'readiness_plan.json').write_bytes((json.dumps(plan,indent=2)+'\n').encode())
    return plan


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--process',required=True)
    parser.add_argument('--events',type=int,required=True)
    parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--energy',type=float,required=True,help='total pp energy in GeV')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--max-hours',type=float,default=2)
    parser.add_argument('--max-disk-gb',type=float,default=5,help='administrative budget in GiB')
    args=parser.parse_args(argv)
    try:
        validate_request(args)
        policy,snapshots=bound_bundle()
        from validate_profiles import validate_card_contract,validate_profile_config
        from check_decay_tables import validate_decay_contract
        generator=load_json(CONFIG/'generator_contract.json')
        decay=load_json(CONFIG/'decay_contract.json')
        profiles=load_json(CONFIG/'input_profiles.json')
        semantic={
            'generator':validate_card_contract(generator),
            'input_profiles':validate_profile_config(profiles),
            'decay':validate_decay_contract(decay),
            'cross_contracts':cross_contract_check(generator,decay,profiles,policy)}
        installed=verify_environment()
        output=safe_output(args.output or Path.home()/'simulations/zh_pilot_plans'/
            f'zh_100_seed{args.seed}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")}',protected_paths())
        available=resources(output,args.max_disk_gb)
        if available['administrative_disk_budget_bytes'] < sum(map(len,snapshots.values()))+65536:
            raise ValueError('disk budget is smaller than the text planning payload reserve')
        plan=create_plan(args,policy,snapshots,installed,available,output,semantic=semantic)
        print(json.dumps({'status':plan['status'],'output':str(output),
                          'physical_execution_gate':'NOT_AUTHORIZED','events_generated':0},indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print('BLOCKED: '+str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
