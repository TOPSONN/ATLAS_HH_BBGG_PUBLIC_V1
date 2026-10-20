"""Exact pure/mock regression set with actual forbidden-operation audit.

No service, namespace/proc readback, ioctl, native compiler or physics import
is allowed. Only Git fixture commands can become real subprocesses. Hosted
success is source/offline evidence, never local kernel acceptance.
"""
from __future__ import annotations
import argparse
# Preload the standard ctypes Python-runtime binding before the audit. No
# project CDLL/filter/syscall function is called here or allowed by the tests.
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest

MODULES = (
    'test_archive_io','test_backend','test_fixtures','test_worker_adapters',
    'test_allocation_guard','test_publication','test_service_probe',
    'test_full_controller','test_full_publication','test_mount_attestation',
    'test_namespace_attestation','test_controller_recovery','test_recovery_publication',
    'test_controller_io','test_controller_guard','test_mount_policy','test_storage_transport',
    'test_workflow_evidence','test_autonomous_publication')
HERE = Path(__file__).resolve().parent
COUNTS = {'git_processes':0,'forbidden_attempts':[], 'unresolved_directory_fd_events':0}


def forbidden(reason):
    COUNTS['forbidden_attempts'].append(reason)
    raise RuntimeError('OFFLINE_FORBIDDEN:'+reason)


def audit(event,args):
    if event == 'subprocess.Popen':
        exe=os.fsdecode(args[0])
        if exe not in ('git','/usr/bin/git'):
            forbidden('PROCESS:'+Path(exe).name)
        COUNTS['git_processes']+=1
    elif event in ('os.fork','os.forkpty','os.posix_spawn','os.exec','os.kill','os.killpg',
                   'fcntl.ioctl','ctypes.dlopen','os.system','os.spawn','pty.spawn'):
        forbidden(event)
    elif event in ('open','os.listdir','os.scandir'):
        target=args[0]
        if isinstance(target,(str,bytes,os.PathLike)):
            path=os.path.normpath(os.path.abspath(os.fsdecode(target)))
            if (path=='/proc' or path.startswith('/proc/') or path=='/sys/fs/cgroup' or
                path.startswith('/sys/fs/cgroup/') or path=='/run/user' or
                path.startswith('/run/user/') or path in ('/dev/fuse','/dev/mqueue')):
                forbidden('KERNEL_READBACK')
        elif event in ('os.listdir','os.scandir') and type(target) is int:
            # tempfile cleanup uses directory FDs. Audit events do not disclose
            # their targets; trusted fixed-source review remains necessary.
            COUNTS['unresolved_directory_fd_events']+=1
    elif event == 'import':
        name=args[0]
        if any(part.lower() in ('madgraph','mg5','pythia8','delphes') for part in name.split('.')):
            forbidden('PHYSICS_IMPORT')


def ids(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from ids(item)
        else:yield item.id()


def snapshot():
    paths=sorted(HERE.glob('*.py'))+sorted((HERE/'tests').glob('test_*.py'))+sorted((HERE/'config').glob('*.json'))
    return [{'path':p.relative_to(HERE).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in paths]


def run():
    before=snapshot()
    # All applicable data fixtures are loaded only after the audit is active.
    sys.addaudithook(audit)
    suite=unittest.TestLoader().loadTestsFromNames([
        'simulation.hh_signal.final_closure.resource_closure.tests.'+n for n in MODULES])
    selected=list(ids(suite))
    if len(selected)!=len(set(selected)):
        raise RuntimeError('DUPLICATE_TEST_IDS')
    output=io.StringIO();start=time.monotonic()
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    after=snapshot()
    receipt={'schema':'PHASE7I_AUTONOMOUS_OFFLINE_V1',
             'status':'PASS_SOURCE_OFFLINE_ONLY' if result.wasSuccessful() and before==after and
                        not COUNTS['forbidden_attempts'] and not result.skipped else 'FAIL_OFFLINE',
             'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'skipped':len(result.skipped),'unique_test_ids':len(set(selected)),
             'source_unchanged':before==after,'source_rows':before,
             'wall_seconds':time.monotonic()-start,'audit':COUNTS,
             'audit_scope':'REVIEWED_FIXED_TESTS_NOT_A_GENERAL_SANDBOX',
             'audit_limitations':['stat/readlink and symlink aliases require source review',
                                  'directory-FD targets are not disclosed by Python audit events'],
             'kernel_services_executed':0,'actual_namespace_ioctls':0,
             'FULL_LAUNCH_ENVELOPE_VERIFIED':False}
    return receipt,selected,output.getvalue()


def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    # This is an offline report path, not an execution authorization/output.
    if args.output.exists():raise ValueError('PRESERVE_EXISTING_OFFLINE_RECEIPT')
    receipt,selected,log=run()
    for path,value in ((args.output,json.dumps(receipt,indent=2)+'\n'),
                       (args.output.with_suffix('.txt'),log),
                       (args.output.with_name(args.output.stem+'_test_ids.json'),json.dumps(selected,indent=2)+'\n')):
        with path.open('x',encoding='utf-8') as stream:stream.write(value)
    print(log,end='')
    print(json.dumps({k:v for k,v in receipt.items() if k!='source_rows'}))
    return 0 if receipt['status']=='PASS_SOURCE_OFFLINE_ONLY' else 2


if __name__=='__main__':raise SystemExit(main())
