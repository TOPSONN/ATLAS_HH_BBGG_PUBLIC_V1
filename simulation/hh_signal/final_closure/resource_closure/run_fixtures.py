"""Strict data assessor and actual fixed harmless campaign; no HH dispatch."""
from __future__ import annotations
import argparse,copy,json,math,os,re,subprocess,sys,time
from pathlib import Path
from .fixtures import CASES,PHASES,MODES,ZERO,spec,require

def flattened(records):
 out=[]
 for row in records:
  if not isinstance(row,dict):raise ValueError('NONSCALAR_PROTOCOL_ROW')
  out.append(row)
  details=row.get('details',[])
  require(type(details) is list and len(details)<=16,'CHILD_DETAILS_BOUND')
  require(all(type(v) is dict for v in details),'CHILD_DETAILS_SCHEMA')
  out.extend(details)
 return out

def finite_number(value):
 return type(value) in (int,float) and math.isfinite(value)

def kernel_proof(row,proof):
 from . import allocation_guard
 p=row['profile'];effective=proof.get('effective',{})
 guard=proof.get('allocation_guard',{})
 require(type(proof.get('pid')) is int and proof['pid']>0 and
         guard.get('schema')=='HH_ALLOCATION_BYPASS_GUARD_V1' and
         guard.get('installed') is True and type(guard.get('pid')) is int and
         guard['pid']==proof['pid'] and
         guard.get('program_sha256')==allocation_guard.program_identity() and
         guard.get('instruction_count')==len(allocation_guard.program()),
         'EXACT_SAME_PID_ALLOCATION_FILTER_IDENTITY_MISSING')
 lock=proof.get('exclusive_job_lock',{})
 require(lock.get('acquired') is True and lock.get('read_only') is True and
         type(lock.get('pid')) is int and lock['pid']==proof['pid'] and
         lock.get('path')==str(Path.home()/'simulations/.resource_envelope.lock') and
         type(lock.get('dev')) is int and lock['dev']>0 and
         type(lock.get('inode')) is int and lock['inode']>0,
         'EXCLUSIVE_SINGLE_JOB_LOCK_NOT_PROVEN')
 require(type(guard.get('seccomp_mode')) is int and guard['seccomp_mode']==2 and
         type(guard.get('no_new_privs')) is int and guard['no_new_privs']==1 and
         type(guard.get('filter_count_before')) is int and guard['filter_count_before']>=0 and
         type(guard.get('filter_count_after')) is int and
         guard['filter_count_after']==guard['filter_count_before']+1 and
         guard.get('native_architecture')=='x86_64' and guard.get('x32_action')=='KILL_PROCESS' and
         guard.get('default_action')=='ALLOW' and guard.get('denied_action')=='ERRNO_EPERM' and
         guard.get('denied_syscalls')==allocation_guard.DENIED and
         guard.get('safe_readonly_tty_requests')==list(allocation_guard.SAFE_TTY_REQUESTS) and
         guard.get('physical_or_build_authorization') is False,
         'EFFECTIVE_INHERITED_ALLOCATION_FILTER_NOT_PROVEN')
 quota=str(p['cpu_quota_percent']*p['cpu_quota_period_usec']//100)+' '+str(p['cpu_quota_period_usec'])
 expected={'cpu.max':quota,'cpu.max.burst':'0','memory.max':str(p['aggregate_memory_bytes']),
  'memory.swap.max':'0','memory.oom.group':'1','pids.max':str(p['max_tasks'])}
 require(effective==expected,'EFFECTIVE_KERNEL_VALUES_MISMATCH')
 limits={'AS':[p['per_process_address_space_bytes']]*2,'CPU':[p['per_process_CPU_seconds']]*2,
         'FSIZE':[p['per_regular_file_bytes']]*2,'CORE':[0,0]}
 require(proof.get('limits')==limits,'EFFECTIVE_HARD_RLIMIT_VALUES_MISMATCH')
 require(proof.get('mode')=='fixture' and proof.get('source_identity')==row.get('source_snapshot_identity'),
         'ATTESTED_SOURCE_IDENTITY_MISMATCH')
 import hashlib
 identity=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 require(proof.get('profile_identity')==identity,'ATTESTED_PROFILE_IDENTITY_MISMATCH')
 require(proof.get('repository_readonly') is True and proof.get('cgroup_readonly') is True and
         proof.get('affinity_count')==1,'READONLY_OR_AFFINITY_PROOF_MISSING')
 mounts=proof.get('mounts',[])
 require(type(mounts) is list and len(mounts)==2,'EXACT_TWO_TMPFS_PROOF_REQUIRED')
 work=[v for v in mounts if str(v.get('path','')).endswith('/work')]
 tmp=[v for v in mounts if v.get('path')=='/tmp']
 require(len(work)==len(tmp)==1,'PRIVATE_WORK_AND_TMP_PROOF_REQUIRED')
 require(proof.get('writable_mounts')==sorted([work[0]['path'],'/tmp']),
         'UNACCOUNTED_WRITABLE_MOUNT_PROOF')
 for rows,bytecap,inodecap in ((work,p['work_tmpfs_bytes'],p['work_tmpfs_inodes']),
                              (tmp,p['tmp_tmpfs_bytes'],p['tmp_tmpfs_inodes'])):
  require(rows[0].get('bytes')==bytecap and rows[0].get('inodes')==inodecap and
          rows[0].get('filesystem')=='tmpfs','EFFECTIVE_TMPFS_VALUES_MISMATCH')
 exports=row.get('host_payload_files')
 expected_names={'chunk_00.bin','chunk_01.bin','index.bin','stdout.log','stderr.log'}
 require(type(exports) is list and len(exports)==5 and
         {v.get('path') for v in exports}==expected_names,'FIXED_TRANSPORT_INVENTORY_MISSING')
 for item in exports:
  require(type(item.get('bytes')) is int and 0<=item['bytes']<=p['per_regular_file_bytes'] and
          type(item.get('allocated_bytes')) is int and
          0<=item['allocated_bytes']<=p['per_regular_file_bytes'] and
          re.fullmatch('[0-9a-f]{64}',item.get('sha256','')) is not None,
          'TRANSPORT_SIZE_ALLOCATION_OR_IDENTITY_MISMATCH')
 allocated=sum(v['allocated_bytes'] for v in exports)
 require(type(row.get('measured_host_payload_allocated_bytes')) is int and
         row['measured_host_payload_allocated_bytes']==allocated,'EXPORT_ALLOCATED_SUM_MISMATCH')
 canary=row.get('host_canary_allocated_bytes')
 require(type(canary) is int and 0<=canary<=p['host_allocation_granule_bytes'],
         'CANARY_ALLOCATED_BOUND_MISMATCH')
 upper=(p['work_tmpfs_bytes']+p['tmp_tmpfs_bytes']+allocated+
        p['host_metadata_files']*p['host_metadata_bytes']+p['source_control_reserve_bytes']+canary)
 require(type(row.get('actual_data_disk_upper_bytes')) is int and
         row['actual_data_disk_upper_bytes']==upper and upper<p['aggregate_disk_bytes'],
         'ACTUAL_ALLOCATED_DISK_ENVELOPE_MISMATCH')

def assess(row):
 require(type(row) is dict and row.get('case') in CASES,'FIXED_CASE_REQUIRED')
 case=row['case'];p=row['profile'];logs=row['stdout_records'];flat=flattened(logs)
 require(row.get('evidence_class')=='SYNTHETIC_METHOD_ONLY','HARMLESS_EVIDENCE_ONLY')
 proof=[v for v in logs if v.get('kind')=='ATTESTED']
 require(len(proof)==1 and proof[0].get('valid') is True,'NO_EFFECTIVE_KERNEL_PROOF')
 kernel_proof(row,proof[0])
 for key in ('MG5_invocations','new_ME_calls','new_integrals','new_hard_events',
             'new_Pythia_events','new_Delphes_events'):
  require(type(row.get(key)) is int and row[key]==0,'NONZERO_OR_MISSING_PHYSICAL_COUNTER:'+key)
 require(row.get('formal_build_executed') is False and
         row.get('full_parser_or_physics_authorized') is False,'FORMAL_EXECUTION_FORBIDDEN')
 require(row.get('cgroup_empty_and_unpopulated_verified') is True and
         row.get('residual_processes_after_cleanup')==[],'UNPROVEN_CGROUP_CLEANUP')
 require(row.get('host_work_directory_empty') is True and row.get('canary_preserved') is True,
         'SOURCE_OR_WORK_PRESERVATION_MISSING')
 require(re.fullmatch('[0-9a-f]{64}',row.get('source_snapshot_identity','')) is not None,
         'SOURCE_SNAPSHOT_IDENTITY_MISSING')
 cpu=row.get('max_observed_CPU_usec');wall=row.get('payload_wall_seconds')
 require(type(cpu) is int and 0<cpu<=p['aggregate_CPU_seconds']*1000000,
         'ACTUAL_CPU_MISSING_OR_EXCEEDED')
 require(finite_number(wall) and 0<wall<=p['aggregate_wall_seconds'],
         'ACTUAL_PAYLOAD_WALL_MISSING_OR_EXCEEDED')
 require(finite_number(row.get('elapsed_including_host_cleanup_seconds')) and
  row['elapsed_including_host_cleanup_seconds']<=p['aggregate_wall_seconds']+.5,
  'HOST_CLEANUP_WALL_EXCEEDED')
 peak=row.get('max_observed_memory_bytes')
 require(type(peak) is int and 0<peak<=p['aggregate_memory_bytes'],
         'ACTUAL_MEMORY_MISSING_OR_EXCEEDED')
 last=row['last_unit_properties'];entered=[v['phase'] for v in logs if v.get('kind')=='ENTER']
 exited=[v['phase'] for v in logs if v.get('kind')=='EXIT']
 completed=[v for v in logs if v.get('kind')=='COMPLETE']
 require(entered==list(PHASES[:len(entered)]) and
         exited==list(PHASES[:len(exited)]),'PHASE_ORDER_OR_DUPLICATE')
 if case=='normal':
  require(entered==list(PHASES) and exited==list(PHASES) and len(completed)==1 and
   completed[0].get('all_six_phases') is True and row.get('resource_stop') is None and
   last.get('Result')=='success' and last.get('ExecMainStatus')=='0',
   'NORMAL_SIX_PHASE_FLOW_FAILED')
  require(not any(v.get('kind') in ('FAILED','LIMIT_ERROR','NEGATIVE_COMPLETE') for v in flat),
          'NORMAL_FLOW_HID_FAILURE')
  return True
 selected=spec(case);phase=selected['phase'];mode=selected['mode']
 require(entered and entered[-1]==phase and phase not in exited and not completed,
         'NEGATIVE_WORKFLOW_CONTINUED')
 if mode in MODES:
  injections=[v for v in logs if v.get('kind')=='INJECTED']
  site='child' if phase in ('compile','loader') else 'supervisor'
  require(len(injections)==1 and injections[0].get('phase')==phase and
    injections[0].get('mode')==mode and injections[0].get('execution_site')==site,
    'DECLARED_PHASE_ACTION_NOT_OBSERVED')
  if mode=='ram':
   require(last.get('Result')=='oom-kill' and peak==p['aggregate_memory_bytes'],
           'AGGREGATE_MEMORY_OOM_NOT_PROVEN')
  elif mode=='disk':
   require(any(v.get('errno')==28 for v in flat),'AGGREGATE_DISK_ENOSPC_MISSING')
  elif mode=='abnormal':
   direct=site=='supervisor' and last.get('ExecMainStatus')=='87'
   child=site=='child' and last.get('ExecMainStatus') in ('2','78') and any(
    v.get('kind') in ('CHILD_MEASURED','CHILD_RESULT') and v.get('exit')==87 for v in flat)
   require(direct or child,'ABNORMAL_EXIT_NOT_PROPAGATED')
  elif mode=='wall':
   timeout=last.get('Result')=='timeout'
   child_stop=any(v.get('kind')=='CHILD_WALL_STOP' and
                  finite_number(v.get('wall_seconds')) and v['wall_seconds']>=2.8 for v in flat)
   require(timeout or (site=='child' and child_stop),'TOTAL_OR_CHILD_WALL_NOT_ENFORCED')
  else:
   signal_stop=last.get('ExecMainStatus') in ('9','24') or any(
    v.get('exit') in (-9,-24) for v in flat)
   cumulative=row.get('resource_stop')=='AGGREGATE_CPU_EARLY_STOP' and cpu>=2500000
   require((signal_stop and cpu>=1800000) or cumulative,'ACTUAL_CPU_STOP_NOT_PROVEN')
 elif case=='job_lock':
  found=[v for v in flat if v.get('kind')=='CONTAINED' and v.get('check')=='JOB_LOCK']
  require(len(found)==1,'ACTUAL_JOB_LOCK_PROBE_MISSING')
  probe=found[0].get('job_lock_probe',{})
  require(type(probe.get('owner_pid')) is int and probe['owner_pid']==proof[0]['pid'] and
          probe.get('separate_open_description') is True and probe.get('denied') is True and
          type(probe.get('errno')) is int and probe['errno']==11 and
          probe.get('path')==str(Path.home()/'simulations/.resource_envelope.lock'),
          'SEPARATE_DESCRIPTION_SINGLE_JOB_LOCK_DENIAL_NOT_PROVEN')
 elif case=='allocation_bypass':
  found=[v for v in flat if v.get('kind')=='CONTAINED' and
         v.get('check')=='ALLOCATION_BYPASS']
  require(len(found)==1,'ACTUAL_ALLOCATION_PROBE_MISSING')
  probe=found[0].get('allocation_probe',{})
  checks=probe.get('checks',[])
  require(probe.get('program_sha256')==proof[0]['allocation_guard']['program_sha256'] and
          type(probe.get('pid')) is int and probe['pid']==proof[0]['pid'],
          'PROBE_ALLOCATION_PROGRAM_OR_PID_BINDING_MISMATCH')
  require(probe.get('installed') is True and probe.get('all_denied') is True and
          type(probe.get('pid')) is int and probe['pid']>0 and
          re.fullmatch('[0-9a-f]{64}',probe.get('program_sha256','')) is not None,
          'INHERITED_ALLOCATION_GUARD_NOT_PROVEN')
  require(type(checks) is list and 3<=len(checks)<=32 and
          all(type(v) is dict for v in checks),'ALLOCATION_CHECK_SCHEMA')
  names=[v.get('operation') for v in checks]
  require(len(set(names))==len(names) and
          {'fallocate_keep_size','ioctl_clone','setxattr'}<=set(names),
          'REQUIRED_ALLOCATION_SYSCALL_PROBES_MISSING')
  require(all(type(v.get('errno')) is int and v['errno']==1 and
          type(v.get('return_code')) is int and v['return_code']==-1 for v in checks),
          'ALLOCATION_MUTATOR_SYSCALL_NOT_EPERM')
  syscall_by_operation={v['operation']:v.get('syscall') for v in checks}
  require(syscall_by_operation['fallocate_keep_size']=='fallocate' and
          syscall_by_operation['ioctl_clone']=='ioctl' and
          syscall_by_operation['setxattr']=='fsetxattr','ACTUAL_ALLOCATION_SYSCALL_KIND_MISSING')
  before=probe.get('allocated_bytes_before');after=probe.get('allocated_bytes_after')
  logical_before=probe.get('logical_bytes_before');logical_after=probe.get('logical_bytes_after')
  require(type(before) is int and before>=0 and type(after) is int and after==before and
          type(logical_before) is int and logical_before>=0 and
          type(logical_after) is int and logical_after==logical_before,
          'HOST_ALLOCATION_INCREASE_OR_MISSING_MEASUREMENT')
 elif case=='aggregate_cpu':
  require(row.get('resource_stop')=='AGGREGATE_CPU_EARLY_STOP' and cpu>=2500000,
          'CUMULATIVE_CPU_WATCHDOG_NOT_PROVEN')
 elif case=='controller_loss':
  require(last.get('Result')=='timeout' and row.get('controller_exited_verified') is True and
   row.get('observer_is_separate_process') is True and cpu>=2500000,
   'AUTONOMOUS_BUSY_CONTROLLER_LOSS_NOT_PROVEN')
 elif case=='orphan':
  require(row.get('resource_stop')=='RESIDUAL_CGROUP_PROCESSES' and
   row.get('residual_pids_detected') and any(v.get('kind')=='ORPHAN_CREATED' and
   v.get('setsid') is True for v in flat),'SETSID_ORPHAN_NOT_REAPED')
 elif case in ('source_write','cgroup_write','namespace_escape','pids',
               'legacy_missing_approval','archive_bound'):
  expected={'source_write':'READONLY_CANARY','cgroup_write':'CGROUP_READONLY',
   'namespace_escape':'NAMESPACE_ESCAPE_DENIED','pids':'TASKS_MAX',
   'legacy_missing_approval':'LEGACY_MISSING_APPROVAL','archive_bound':'ARCHIVE_BOUND'}[case]
  require(any(v.get('kind')=='CONTAINED' and v.get('check')==expected for v in flat),
          'EXPECTED_REJECTION_MISSING')
 elif case in ('stdout_overflow','chunk_overflow'):
  require(last.get('ExecMainStatus')=='25' or any(v.get('errno')==27 for v in flat),
          'HOST_REGULAR_FILE_CAP_NOT_ENFORCED')
 elif case in ('disk_inodes','tmp_inodes'):
  root='/tmp' if case=='tmp_inodes' else None
  require(any(v.get('errno')==28 and v.get('tmpfs_free_inodes')==0 and
   (root is None or v.get('root')==root) for v in flat),'PRIVATE_INODE_CAP_NOT_PROVEN')
 elif case=='tmp_disk':
  require(any(v.get('errno')==28 and v.get('root')=='/tmp' for v in flat),
          'PRIVATE_TMP_ENOSPC_NOT_PROVEN')
 else:raise ValueError('UNASSESSED_CASE')
 return True

def save_new(path,value):
 raw=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
 require(len(raw)<=65536,'BOUNDED_CAMPAIGN_METADATA_REQUIRED')
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw)

def controller_handoff(output):
 from . import backend
 handoff=backend.start_job('controller_loss',output)
 try:
  until=min(handoff['deadline'],time.monotonic()+3)
  while time.monotonic()<until:
   records=backend.records(Path(output)/'stdout.log')
   if any(v.get('kind')=='ATTESTED' and v.get('valid') is True for v in records):
    require(handoff.get('controller_pid')==os.getpid(),
            'START_JOB_CONTROLLER_IDENTITY_MISMATCH')
    backend.new_json(Path(output)/'handoff.json',handoff)
    os._exit(0)
   time.sleep(.02)
  raise ValueError('CONTROLLER_LOSS_ATTESTATION_TIMEOUT')
 except BaseException:
  backend.kill_owned(handoff['unit'])
  raise

def loss_case(output):
 from . import backend
 result=subprocess.run(['/usr/bin/python3','-B','-m',__package__+'.run_fixtures',
  '--controller-handoff','--output',str(output)],cwd=backend.REPO,
  env=backend.host_env(),capture_output=True,text=True,timeout=5)
 require(result.returncode==0,'CONTROLLER_FIXTURE_ENTRY_FAILED:'+result.stderr[-1000:])
 handoff=json.loads((Path(output)/'handoff.json').read_text())
 require(type(handoff.get('controller_pid')) is int and handoff['controller_pid']>0 and
         handoff['controller_pid']!=os.getpid(),'CONTROLLER_OBSERVER_NOT_SEPARATE')
 return backend.monitor_job(handoff)

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',required=True,type=Path)
 parser.add_argument('--case',choices=CASES,action='append')
 parser.add_argument('--controller-handoff',action='store_true',help=argparse.SUPPRESS)
 args=parser.parse_args(argv)
 if args.controller_handoff:
  require(not args.case,'CONTROLLER_HANDOFF_HAS_NO_CUSTOM_CASE')
  return controller_handoff(args.output)
 from . import backend
 output=backend.fresh(args.output);output.mkdir(mode=0o700)
 chosen=args.case or list(CASES)
 require(len(chosen)==len(set(chosen)),'DUPLICATE_FIXTURE_CASE')
 results=[];failure=None
 for case in chosen:
  try:
   row=loss_case(output/case) if case=='controller_loss' else backend.run_job(case,output/case)
   assess(row)
   results.append({'case':case,'status':'PASS_EXPECTED_RESULT','CPU_usec':
    row['max_observed_CPU_usec'],'payload_wall_seconds':row['payload_wall_seconds']})
   print(case,'PASS',flush=True)
  except BaseException as error:
   failure={'case':case,'type':type(error).__name__,'reason':str(error)[:2000]}
   print('STOP',json.dumps(failure,sort_keys=True),flush=True);break
 full=chosen==list(CASES)
 summary={'schema_version':1,'evidence_class':'SYNTHETIC_METHOD_ONLY',
  'status':'PASS_REQUESTED_HARMLESS_CASES' if failure is None else 'BLOCKED_RESOURCE_FIXTURE_FAILURE',
  'all_required_cases_executed':full and failure is None,'required_cases':list(CASES),
  'requested_cases':chosen,'results':results,'failure':failure,
  'FULL_LAUNCH_ENVELOPE_VERIFIED':failure is None and full,
  'FORMAL_BUILD_ENVELOPE_VERIFIED':False,'parser_or_physics_authorized':False,
  'source_snapshot':backend.source_snapshot(),**ZERO}
 save_new(output/'suite_summary.json',summary)
 return 0 if failure is None else 2

if __name__=='__main__':raise SystemExit(main())
