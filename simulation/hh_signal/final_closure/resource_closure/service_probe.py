"""One-shot non-stress service compatibility diagnostic, never full closure.

The only service executable is /usr/bin/true. No filter installation, business
imports in the service, stress, authorization, parser, build or native dispatch.
Host diagnostic scaffolding is not claimed to be a full launch envelope.
"""
from __future__ import annotations
import argparse,json,re,subprocess,time,uuid
from pathlib import Path
from . import backend

STATUS_OK='SERVICE_CONFIGURATION_ACCEPTED_EXEC_TRUE_SUCCESS'
STATUS_BLOCKED='BLOCKED_EXACT_USER_SERVICE_CONFIGURATION'
FIELDS=('Id,LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,MainPID,'
        'ControlGroup,CPUUsageNSec,MemoryPeak,MemoryMax,MemorySwapMax,RuntimeMaxUSec,'
        'TimeoutStartUSec,TimeoutStopUSec,CPUQuotaPerSecUSec,CPUQuotaPeriodUSec,'
        'TasksMax,PrivateUsers,PrivateNetwork,ProtectSystem,ProtectControlGroups')

def command(output,unit):
    backend.require(re.fullmatch(backend.UNIT_PATTERN,unit) is not None,
                    'FOREIGN_UNIT_FORBIDDEN')
    profile=backend.load_profile()
    backend.require(profile['RAM_profile_review_status']=='EXPLICIT_HUMAN_APPROVED_RAM_ONLY',
                    'RAM_PROFILE_NOT_EXPLICITLY_REVIEWED')
    # Same namespace/limit settings; this diagnostic has no archive, mutex or
    # human TTY and never installs the worker allocation filter.
    props=[v for v in backend.properties(output) if not v.startswith(
        ('OpenFile=','StandardOutput=','StandardError='))]
    props+=['StandardOutput=null','StandardError=null']
    return ['/usr/bin/systemd-run','--user','--quiet','--unit',unit,
            *[v for prop in props for v in ('--property',prop)],'/usr/bin/true']

def call(argv,timeout):
    done=subprocess.run(argv,env=backend.host_env(),capture_output=True,timeout=timeout)
    backend.require(len(done.stdout)<=32768 and len(done.stderr)<=4096,
                    'DIAGNOSTIC_RESPONSE_BOUND')
    return {'returncode':done.returncode,
            'stdout':done.stdout.decode('utf-8',errors='replace'),
            'stderr':done.stderr.decode('utf-8',errors='replace')}

def show(unit):
    result=call(['/usr/bin/systemctl','--user','show',unit,'--property='+FIELDS],2)
    backend.require(result['returncode']==0,'UNIT_QUERY_FAILED')
    data=dict(v.split('=',1) for v in result['stdout'].splitlines() if '=' in v)
    backend.require(data.get('Id')==unit,'FOREIGN_UNIT_RESPONSE')
    return result,data

def classify(launch,properties):
    # Manager configuration readback is not kernel proof. A missing exit status,
    # failed launch or unknown final state must not become successful execution.
    return STATUS_OK if (launch.get('returncode')==0 and
        properties.get('LoadState')=='loaded' and
        properties.get('ActiveState')=='active' and
        properties.get('SubState')=='exited' and
        properties.get('Result')=='success' and
        properties.get('ExecMainCode')=='1' and
        properties.get('ExecMainStatus')=='0' and
        properties.get('MainPID')=='0') else STATUS_BLOCKED

def optional_int(mapping,key):
    raw=mapping.get(key)
    return int(raw) if isinstance(raw,str) and raw.isdigit() else None

def cleanup_unit(unit,cg):
    backend.require(re.fullmatch(backend.UNIT_PATTERN,unit) is not None,'FOREIGN_UNIT_FORBIDDEN')
    result={}
    # A failed/timeout kill must never skip stop or status readback.
    for name,argv in (
        ('kill',['/usr/bin/systemctl','--user','kill','--kill-whom=all','--signal=SIGKILL',unit]),
        ('stop',['/usr/bin/systemctl','--user','stop',unit])):
        try:result[name]=call(argv,2)
        except BaseException as error:
            result[name]={'error_type':type(error).__name__,'error':str(error)[:1024]}
    after={}
    try:
        query,after=show(unit);result['query']=query;result['manager_properties']=after
        result['manager_stopped_verified']=(query['returncode']==0 and after.get('Id')==unit and
            after.get('ActiveState') in ('failed','inactive') and after.get('MainPID')=='0')
    except BaseException as error:
        result['query_error']={'type':type(error).__name__,'reason':str(error)[:1024]}
        result['manager_stopped_verified']=False
    result['kernel_cleanup']='NOT_OBSERVED'
    if cg is not None:
        try:
            if not cg.exists():result['kernel_cleanup']='KNOWN_CGROUP_REMOVED'
            else:
                snapshot=backend.cgroup_read(cg);result['kernel_snapshot']=snapshot
                events=dict(line.split() for line in snapshot.get('cgroup.events','').splitlines())
                if ('cgroup.procs' in snapshot and not snapshot['cgroup.procs'].strip() and
                    events.get('populated')=='0'):
                    result['kernel_cleanup']='OBSERVED_EMPTY_AND_UNPOPULATED'
                else:result['kernel_cleanup']='NOT_PROVEN_EMPTY'
        except BaseException as error:
            result['kernel_cleanup']='READBACK_ERROR'
            result['kernel_error']={'type':type(error).__name__,'reason':str(error)[:1024]}
    result['cleanup_verified']=(result['manager_stopped_verified'] and result['kernel_cleanup'] in
        ('KNOWN_CGROUP_REMOVED','OBSERVED_EMPTY_AND_UNPOPULATED'))
    return result

def run_once(output):
    output=backend.fresh(output)
    profile=backend.load_profile()
    backend.require(profile['RAM_profile_review_status']=='EXPLICIT_HUMAN_APPROVED_RAM_ONLY',
                    'RAM_PROFILE_NOT_EXPLICITLY_REVIEWED')
    # This directory has never held an HH build or physical sample.
    output.mkdir(mode=0o700);(output/'work').mkdir(mode=0o700)
    unit='atlas-hh-phase7i-resource-'+uuid.uuid4().hex+'.service'
    cmd=command(output,unit);start=time.monotonic()
    result={'schema_version':1,'diagnostic':'ONE_SHOT_TRUE_SERVICE_COMPATIBILITY_ONLY',
        'output':str(output),'unit':unit,'command':cmd,
        'source_snapshot':backend.source_snapshot(),'profile':profile,
        'service_executable':'/usr/bin/true','service_executable_sha256':backend.digest('/usr/bin/true'),
        'service_attempts':1,'stress_attempts':0,'filter_install_attempts':0,
        'resource_matrix_cases_executed':0,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,
        'formal_build_executed':False,'human_authorizations_created':0,**backend.ZERO}
    launch={};last={};cg=None
    try:
        launch=call(cmd,profile['unit_start_seconds']+1)
        result['launch']=launch
        # Read once after a failed start. Only a successful asynchronous start
        # may need bounded queries while this one true invocation exits.
        deadline=time.monotonic()+1
        while True:
            queried,last=show(unit)
            result['last_query']=queried
            if (launch['returncode']!=0 or last.get('SubState')=='exited' or
                last.get('ActiveState') in ('failed','inactive') or
                last.get('LoadState')=='not-found' or time.monotonic()>=deadline):break
            time.sleep(.02)
        result['manager_properties']=last
        if last.get('ControlGroup'):
            cg=backend.owned_cgroup(unit,last['ControlGroup'])
            result['kernel_snapshot_before_cleanup']=backend.cgroup_read(cg)
        result['status']=classify(launch,last)
        result['CPU_usage_ns_manager']=optional_int(last,'CPUUsageNSec')
        result['memory_peak_bytes_manager']=optional_int(last,'MemoryPeak')
    except BaseException as error:
        result['status']=STATUS_BLOCKED
        result['error']={'type':type(error).__name__,'reason':str(error)[:2048]}
    finally:
        # Only the fresh exact unit can be touched; never reset-failed, retry,
        # weaken properties, or remove the failed workspace/evidence.
        result['cleanup']=cleanup_unit(unit,cg)
        result['cleanup_verified']=result['cleanup']['cleanup_verified']
        if not result['cleanup_verified']:result['status']=STATUS_BLOCKED
        result['host_diagnostic_elapsed_seconds']=time.monotonic()-start
        result['effective_resource_enforcement']='NOT_TESTED_BY_TRUE_PROBE'
        result['scope_limit']='Host diagnostic is not fully enclosed; no stress or full workflow was dispatched.'
        raw=(json.dumps(result,indent=2,allow_nan=False)+'\n').encode()
        backend.require(len(raw)<=65536,'PROBE_RECEIPT_BOUND')
        with (output/'probe.json').open('xb') as stream:stream.write(raw)
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    row=run_once(args.output)
    print(json.dumps({k:row[k] for k in ('status','unit','cleanup_verified',
        'resource_matrix_cases_executed','FULL_LAUNCH_ENVELOPE_VERIFIED','new_ME_calls','new_integrals')},
        sort_keys=True))
    return 0 if row['status']==STATUS_OK else 2

if __name__=='__main__':raise SystemExit(main())
