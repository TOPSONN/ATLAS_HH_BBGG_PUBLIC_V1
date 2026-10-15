#!/usr/bin/env python3
"""Physically executable dry-run; deliberately contains no production backend."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.contracts import REPO, require, verify_bundle, read_json, write_json, sha

def safe_output(value, repo=REPO):
    raw=Path(value).expanduser()
    require(raw.is_absolute() and '..' not in raw.parts, 'UNSAFE_OUTPUT_PATH')
    p=raw.resolve()
    allowed=(Path.home()/'simulations/hh_signal_runs').resolve()
    require(p != allowed and p.is_relative_to(allowed) and not p.is_relative_to(repo.resolve()),
            'OUTPUT_MUST_BE_FRESH_LOCAL_SIGNAL_DIRECTORY')
    require(not raw.exists() and not raw.is_symlink(), 'PRESERVE_EXISTING_OUTPUT')
    for parent in raw.parents:
        require(not parent.is_symlink(), 'SYMLINK_OUTPUT_FORBIDDEN')
    return p

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--process',required=True,choices=['ggf_hh_sm'])
    parser.add_argument('--events',required=True,type=int)
    parser.add_argument('--seed',required=True,type=int)
    parser.add_argument('--energy',required=True,type=int)
    parser.add_argument('--output',required=True)
    parser.add_argument('--max-hours',required=True,type=float)
    parser.add_argument('--max-disk-gb',required=True,type=float)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(argv)
    # Fail before checking/installing tools, making directories, or running any
    # subprocess. No authorization token or environment variable bypass exists.
    require(args.dry_run, 'PHYSICAL_SIGNAL_GENERATION_NOT_AUTHORIZED')
    require(os.name=='posix' and Path('/proc/meminfo').is_file(), 'WSL_LINUX_REQUIRED')
    require(1<=args.events<=1000 and 1<=args.seed<=900000000 and args.energy==13000,
            'ONLY_FROZEN_FUTURE_13TEV_UP_TO_1000_REQUEST_SUPPORTED')
    require(math.isfinite(args.max_hours) and 0<args.max_hours<=4 and
            math.isfinite(args.max_disk_gb) and 0<args.max_disk_gb<=10,
            'FUTURE_CAPS_EXCEEDED')
    out=safe_output(args.output)
    manifest=verify_bundle()
    sys.path.insert(0,str(REPO/'simulation/zh_pilot/scripts'))
    from check_environment import verify_environment
    environment=verify_environment()
    from verify_loop_model import inspect_installed_model
    installed=inspect_installed_model()
    mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines()
                 if x.startswith('MemAvailable:')))*1024
    parent=out.parent
    while not parent.exists(): parent=parent.parent
    disk=shutil.disk_usage(parent).free
    require(mem>=2*1024**3 and disk>=(args.max_disk_gb+0.5)*1024**3, 'INSUFFICIENT_RESOURCES')
    require(len(os.sched_getaffinity(0))>=1, 'NO_CPU')
    receipt={'schema_version':1,'status':'PASS_EXECUTED_DRY_RUN_ONLY',
             'request':{k:v for k,v in vars(args).items() if k!='output'},
             'output_role':'fresh_local_signal_run','physical_signal_events':0,
             'integration_invocations':0,'shower_invocations':0,'detector_invocations':0,
             'source_cross_section_pb':'NOT_EVALUATED_UNTIL_REAL_INTEGRATION',
             'model_manifest_sha256':sha(REPO/'metadata/phase7a_model_manifest.json'),
             'installed_model':installed,'environment':environment,
             'project_bindings':manifest['project_bindings'],
             'policy':read_json(REPO/'simulation/hh_signal/config/resource_policy.json'),
             'checks':{'model_source_hashes':True,'process_and_couplings':True,'PDF_scale_contract':True,
                       'decay_BR_contract':True,'toolchain_identity':True,'output_safety':True,
                       'memory_available_bytes':mem,'disk_free_bytes':disk,'workers':1},
             'real_decay_weight_closure':'NOT_EVALUATED',
             'physical_production':'NOT_AUTHORIZED_NO_BACKEND'}
    # Snapshot exact reviewed cards for a future review, not an event manifest.
    out.mkdir(parents=True,exist_ok=False)
    (out/'cards').mkdir()
    for path in (REPO/'simulation/hh_signal/cards').iterdir():
        require(path.is_file() and not path.is_symlink(), 'UNSAFE_CARD')
        shutil.copyfile(path,out/'cards'/path.name)
    write_json(out/'dry_run_receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'events_generated':0,
                      'receipt':str(out/'dry_run_receipt.json')}))
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError) as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(2)
