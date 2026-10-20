#!/usr/bin/env python3
"""Actual fixed inert fixtures. Every attempted case and failure is retained."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from envelope import *
def loss_case(output):
 started=time.monotonic();snapshot=source_snapshot()
 p=subprocess.run(['/usr/bin/python3','-I','-B',str(Path(__file__).with_name('controller_loss_fixture.py')),'--output',str(output)],capture_output=True,text=True,timeout=5)
 require(p.returncode==0,'CONTROLLER_FIXTURE_ENTRY_FAILED:'+p.stderr[-1000:]);handoff=json.loads((output/'controller_return.json').read_text());unit=handoff['unit'];cg=None;last={};observed=[]
 try:
  while time.monotonic()-started<13.2:
   last=unit_properties(unit)
   if last.get('ControlGroup'):
    cg=owned_cgroup(unit,last['ControlGroup']);observed.append(cgroup_read(cg))
   if last.get('ActiveState') in ('failed','inactive') or last.get('LoadState')=='not-found':break
   time.sleep(.02)
  require(last.get('Result')=='timeout','SYSTEMD_FAILED_TO_ENFORCE_RUNTIME_WITHOUT_CONTROLLER')
  require(cg is not None and not cgroup_read(cg).get('cgroup.procs','').strip(),'CONTROLLER_LOSS_LEFT_PROCESS')
 finally:
  if cg is not None:kill_owned(unit,cg)
  subprocess.run(['systemctl','--user','stop',unit],env=host_env(),capture_output=True,timeout=3)
  require(wait_empty(cg,started+13),'CONTROLLER_LOSS_RESIDUAL_POPULATED_CGROUP')
 cpu=max([cpu_usec(v) for v in observed]+[int(last.get('CPUUsageNSec','0'))//1000])
 elapsed=time.monotonic()-started
 require(2_500_000<=cpu<=4_000_000 and elapsed<=13,'CONTROLLER_LOSS_CPU_OR_WALL_NOT_PROVEN')
 require(source_snapshot()==snapshot,'CONTROLLER_LOSS_SOURCE_DRIFT')
 require(not list((output/'work').iterdir()),'CONTROLLER_LOSS_HOST_MOUNT_NOT_EMPTY')
 require((output/'readonly_canary.txt').read_text()=='INERT_READ_ONLY_CANARY\n','CONTROLLER_LOSS_CANARY_CHANGED')
 value={'schema_version':1,'evidence_class':'SYNTHETIC_METHOD_ONLY','case':'controller_loss','unit':unit,'controller_exit':0,'controller_PID':handoff['controller_PID'],'observer_is_separate_process':os.getpid()!=handoff['controller_PID'],'last_unit_properties':last,'stdout_records':records(output/'stdout.log'),'last_observed_cgroup':observed[-1] if observed else {},'elapsed_including_host_cleanup_seconds':elapsed,'resource_stop':'SYSTEMD_RUNTIME_MAX_WITH_CONTROLLER_GONE','residual_processes_after_cleanup':[],'max_observed_CPU_usec':cpu,'source_snapshot_identity':snapshot['identity'],'canary_preserved':True,'host_work_directory_empty':True,'cgroup_empty_and_unpopulated_verified':True,**ZERO}
 new_json(output/'result.json',value);return value

def assess(row):
 case=row['case'];logs=row['stdout_records'];entered=[v['phase'] for v in logs if v.get('kind')=='ENTER'];exited=[v['phase'] for v in logs if v.get('kind')=='EXIT'];complete=any(v.get('kind')=='COMPLETE' for v in logs)
 require(any(v.get('kind')=='ATTESTED' and v.get('valid') is True for v in logs),'NO_EFFECTIVE_KERNEL_PROOF')
 if case=='normal':require(entered==list(PHASES) and exited==list(PHASES) and complete and row.get('resource_stop') is None and row['last_unit_properties'].get('Result')=='success' and row['last_unit_properties'].get('ExecMainStatus')=='0','NORMAL_FOUR_PHASE_FLOW_FAILED')
 elif case=='controller_loss':require(row['last_unit_properties'].get('Result')=='timeout' and row['observer_is_separate_process'] and row.get('cgroup_empty_and_unpopulated_verified') is True and 2_500_000<=row.get('max_observed_CPU_usec',0)<=4_000_000 and row.get('elapsed_including_host_cleanup_seconds',100)<=13,'CONTROLLER_LOSS_NOT_PROVEN')
 elif case=='orphan':require(row['resource_stop']=='RESIDUAL_CGROUP_PROCESSES' and row['residual_pids_detected'] and not complete,'ORPHAN_NOT_REAPED_BY_CGROUP')
 elif case=='aggregate_cpu':require(row['resource_stop']=='AGGREGATE_CPU_EARLY_STOP' and row['max_observed_CPU_usec']>=2_500_000 and row['max_observed_CPU_usec']<=4_000_000,'AGGREGATE_CPU_STOP_NOT_PROVEN')
 elif case in ('source_write','cgroup_write','namespace_escape','pids','legacy_missing_approval'):
  expected={'source_write':'READONLY_CANARY','cgroup_write':'CGROUP_READONLY','namespace_escape':'NAMESPACE_ESCAPE_DENIED','pids':'TASKS_MAX','legacy_missing_approval':'LEGACY_MISSING_APPROVAL'}[case]
  require(any(v.get('kind')=='CONTAINED' and v.get('check')==expected for v in logs),'EXPECTED_REJECTION_MISSING')
 elif case=='stdout_overflow':require(row['last_unit_properties'].get('ExecMainStatus')=='25' and not complete,'STDOUT_FSIZE_NOT_ENFORCED')
 elif case=='disk_inodes':require(any(v.get('errno')==28 and v.get('tmpfs_free_inodes')==0 for v in logs),'INODE_QUOTA_NOT_ENFORCED')
 else:
  phase,mode=case.split('_',1);require(entered and entered[-1]==phase and not complete and phase not in exited,'FAILED_PHASE_CONTINUED')
  if mode=='disk':
   details=[v for x in logs for v in x.get('details',[])];require(any(v.get('errno')==28 for v in logs+details),'AGGREGATE_DISK_ENOSPC_MISSING')
  elif mode=='ram':require(row['last_unit_properties'].get('Result')=='oom-kill','AGGREGATE_MEMORY_OOM_NOT_PROVEN')
  elif mode=='abnormal':require(row['last_unit_properties'].get('ExecMainStatus') in ('87','78'),'ABNORMAL_EXIT_NOT_PROPAGATED')
  elif mode=='wall':require(row['last_unit_properties'].get('Result')=='timeout' or any('CHILD_WALL_STOP' in v.get('reason','') for v in logs),'TOTAL_WALL_NOT_ENFORCED')
  elif mode=='cpu':require(row['last_unit_properties'].get('ExecMainStatus')=='9' or row.get('resource_stop')=='AGGREGATE_CPU_EARLY_STOP' or any('CHILD_WALL_STOP' in v.get('reason','') for v in logs),'CPU_CONTAINMENT_NOT_PROVEN')
 require(not row['residual_processes_after_cleanup'],'RESIDUAL_PROCESS');return True

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append',choices=CASES);a=p.parse_args()
 output=fresh(a.output);output.mkdir(mode=0o700);chosen=a.case or list(CASES);results=[];failure=None
 for case in chosen:
  try:
   row=loss_case(output/case) if case=='controller_loss' else run_case(case,output/case)
   assess(row);results.append({'case':case,'status':'PASS_EXPECTED_RESULT','CPU_usec':row['max_observed_CPU_usec'],'wall_seconds':row['elapsed_including_host_cleanup_seconds']});print(case,'PASS',flush=True)
  except BaseException as error:
   failure={'case':case,'reason':str(error),'type':type(error).__name__};print('STOP',failure,flush=True);break
 summary={'schema_version':1,'evidence_class':'SYNTHETIC_METHOD_ONLY','status':'PASS_REQUESTED_FIXTURE_CASES' if failure is None else 'BLOCKED_FULL_JOB_FIXTURE_FAILURE','all_required_cases_executed':chosen==list(CASES),'FULL_LAUNCH_ENVELOPE_VERIFIED':failure is None and chosen==list(CASES),'profile':PROFILE,'source_snapshot':source_snapshot(),'results':results,'failure':failure,'parser_or_physics_authorized':False,**ZERO};new_json(output/'suite_summary.json',summary)
 return 0 if failure is None else 2
if __name__=='__main__':raise SystemExit(main())
