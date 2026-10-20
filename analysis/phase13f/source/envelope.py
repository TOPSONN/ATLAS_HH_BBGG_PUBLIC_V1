"""Fixed harmless full-workflow service envelope. No arbitrary command dispatcher.
Every data preflight/worker/receipt/postflight runs under systemd resource policy.
The host controller is transport/termination only; it never imports MG5.
"""
from __future__ import annotations
import hashlib,json,os,re,signal,subprocess,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve();REPO=HERE.parents[3]
PROFILE_PATH=HERE.parents[1]/'config/full_job_profile.json'
PHASES=('preflight','child','receipt','postflight')
MODES=('cpu','ram','wall','disk','abnormal')
CASES=('normal',)+tuple(a+'_'+b for a in PHASES for b in MODES)+('aggregate_cpu','orphan','controller_loss','pids','source_write','cgroup_write','namespace_escape','stdout_overflow','disk_inodes','legacy_missing_approval')
ZERO={'MG5_invocations':0,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0}
PROFILE={'schema_version':1,'profile_id':'PHASE13F_FULL_JOB_SYNTHETIC_V1','authorization':'SYNTHETIC_RESOURCE_FIXTURES_ONLY; NO_MG5_OR_PHYSICS','aggregate_CPU_seconds':4,'aggregate_wall_seconds':13,'unit_start_seconds':2,'unit_run_seconds':10,'unit_stop_seconds':0.1,'cpu_quota_percent':30,'cpu_quota_period_usec':10000,'CPU_watchdog_stop_usec':2500000,'aggregate_memory_bytes':536870912,'swap_bytes':0,'per_process_address_space_bytes':536870912,'per_process_CPU_seconds':2,'tmpfs_bytes':8388608,'tmpfs_inodes':1024,'per_regular_file_bytes':65536,'host_log_files':2,'host_metadata_bytes':65536,'host_metadata_files':4,'aggregate_disk_bytes':9437184,'max_tasks':8,'child_original_cpu_seconds':2,'child_original_wall_seconds':3,'child_original_AS_bytes':536870912,'poll_seconds':0.02,'full_parser_execution_authorized':False,'MG5_invocations':0,'new_ME_calls':0,'new_integrals':0,'new_events':0}
def require(ok,reason):
 if not ok:raise ValueError(reason)
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def load_profile(path=PROFILE_PATH):
 value=json.loads(Path(path).read_text());require(value==PROFILE and set(value)==set(PROFILE) and all(type(value[k]) is type(v) for k,v in PROFILE.items()),'RESOURCE_PROFILE_DRIFT');return value
def fresh(path):
 p=Path(path);require(p.is_absolute() and '..' not in p.parts and not p.exists() and not any(q.is_symlink() for q in (p,*p.parents)) and p.parent.is_dir(),'FRESH_REAL_OUTPUT_REQUIRED')
 return p
def new_json(path,value):
 raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode();require(len(raw)<=65536,'HOST_RECEIPT_BOUND')
 with Path(path).open('xb') as stream:stream.write(raw)
def host_env():return {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','HOME':str(Path.home()),'XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid()),'DBUS_SESSION_BUS_ADDRESS':'unix:path=/run/user/'+str(os.getuid())+'/bus','GIT_OPTIONAL_LOCKS':'0','PYTHONDONTWRITEBYTECODE':'1'}
def properties(output):
 p=load_profile();w=Path(output)/'work'
 return ['Type=exec','RemainAfterExit=yes','CPUAccounting=yes','MemoryAccounting=yes','TasksAccounting=yes',
  'MemoryMax='+str(p['aggregate_memory_bytes']),'MemorySwapMax=0','OOMPolicy=kill',
  'CPUQuota=30%','CPUQuotaPeriodSec=10ms','RuntimeMaxSec=10s','TimeoutStartSec=2s','TimeoutStopSec=100ms',
  'KillMode=control-group','KillSignal=SIGKILL','FinalKillSignal=SIGKILL','SendSIGKILL=yes','TasksMax=8',
  'LimitCPU=2','LimitAS=536870912','LimitFSIZE=65536','LimitNOFILE=64','LimitCORE=0',
  'PrivateUsers=yes','PrivateNetwork=yes','PrivateIPC=yes','ProtectSystem=strict','ProtectHome=read-only',
  'ProtectControlGroups=yes','NoNewPrivileges=yes','RestrictNamespaces=yes','CapabilityBoundingSet=',
  'ReadOnlyPaths=/dev /proc /sys','InaccessiblePaths=/run/user/'+str(os.getuid()),
  'TemporaryFileSystem='+str(w)+':rw,size=8388608,nr_inodes=1024,nodev,nosuid,noexec',
  'WorkingDirectory='+str(w),'StandardInput=null','StandardOutput=file:'+str(Path(output)/'stdout.log'),
  'StandardError=file:'+str(Path(output)/'stderr.log'),
  'Environment=PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 GIT_OPTIONAL_LOCKS=0 TMPDIR='+str(w)+'/tmp HOME='+str(w)+'/home']
def unit_properties(unit):
 require(re.fullmatch(r'atlas-hh-phase13f-[0-9a-f]{32}\.service',unit),'FOREIGN_UNIT_FORBIDDEN')
 done=subprocess.run(['systemctl','--user','show',unit,'--property=Id,LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,MainPID,ExecMainStartTimestampMonotonic,ExecMainExitTimestampMonotonic,ControlGroup,CPUUsageNSec,MemoryPeak,MemoryCurrent,TasksCurrent,RuntimeMaxUSec,CPUQuotaPerSecUSec,CPUQuotaPeriodUSec,MemoryMax,MemorySwapMax,TasksMax,LimitCPU,LimitAS,LimitFSIZE,KillMode,KillSignal,ProtectSystem,ProtectControlGroups,PrivateUsers,TemporaryFileSystem'],env=host_env(),capture_output=True,text=True,timeout=2)
 require(len(done.stdout)<16384 and len(done.stderr)<2048,'SYSTEMD_STATUS_BOUND')
 return dict(line.split('=',1) for line in done.stdout.splitlines() if '=' in line)
def owned_cgroup(unit,relative):
 root=Path('/sys/fs/cgroup/user.slice')/('user-'+str(os.getuid())+'.slice')/('user@'+str(os.getuid())+'.service')/'app.slice'
 require(relative=='/'+str(root.relative_to('/sys/fs/cgroup'))+'/'+unit,'FOREIGN_CGROUP_FORBIDDEN')
 return Path('/sys/fs/cgroup')/relative.lstrip('/')
def cgroup_read(path):
 result={}
 for name in ('cpu.stat','memory.peak','memory.events','cgroup.procs','cgroup.events','pids.events','cpu.max','cpu.max.burst','memory.max','memory.swap.max','pids.max'):
  try:result[name]=(path/name).read_text()[:4096]
  except (OSError,ValueError):pass
 return result
def cpu_usec(snapshot):
 return int(dict(line.split() for line in snapshot.get('cpu.stat','').splitlines()).get('usage_usec',0))
def kill_owned(unit,cgroup):
 if cgroup is not None and (cgroup/'cgroup.kill').exists():
  (cgroup/'cgroup.kill').write_text('1')
 else:subprocess.run(['systemctl','--user','kill','--kill-whom=all','--signal=SIGKILL',unit],env=host_env(),capture_output=True,timeout=2)
def wait_empty(cgroup,deadline):
 if cgroup is None:return True
 while True:
  snapshot=cgroup_read(cgroup)
  populated=dict(line.split() for line in snapshot.get('cgroup.events','').splitlines()).get('populated','0')
  if not snapshot.get('cgroup.procs','').strip() and populated=='0':return True
  if time.monotonic()>=deadline:return False
  kill_owned(cgroup.name,cgroup);time.sleep(.01)
def records(path):
 if not Path(path).exists():return []
 require(Path(path).stat().st_size<=65536,'HOST_LOG_BOUND')
 result=[]
 for line in Path(path).read_text(errors='replace').splitlines():
  if len(line)>16384:continue
  try:value=json.loads(line)
  except ValueError:continue
  if isinstance(value,dict):result.append(value)
 return result
def source_snapshot():
 paths=sorted((REPO/'analysis/phase13f/source').glob('*.py'))+sorted((REPO/'analysis/phase13f/scripts').glob('*.py'))+[PROFILE_PATH]
 require(len(paths)<=32 and all(p.stat().st_size<=65536 for p in paths),'SOURCE_SNAPSHOT_BOUND')
 return {'paths':[{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in paths], 'identity':canonical([{'path':str(p.relative_to(REPO)),'sha256':digest(p)} for p in paths])}
def run_case(case,output,*,lose_controller=False):
 require(case in CASES and lose_controller==(case=='controller_loss'),'UNREVIEWED_FIXTURE_OR_CONTROL_MODE')
 load_profile();output=fresh(output);output.mkdir(mode=0o700);(output/'work').mkdir(mode=0o700)
 canary=output/'readonly_canary.txt';canary.write_text('INERT_READ_ONLY_CANARY\n');canary_before=digest(canary)
 unit='atlas-hh-phase13f-'+uuid.uuid4().hex+'.service';snapshot=source_snapshot()
 cmd=['systemd-run','--user','--quiet','--unit',unit,*[x for prop in properties(output) for x in ('--property',prop)],'/usr/bin/python3','-I','-B',str(HERE.with_name('workflow.py')),'--case',case,'--canary',str(canary),'--source-identity',snapshot['identity']]
 start=time.monotonic();done=subprocess.run(cmd,env=host_env(),capture_output=True,text=True,timeout=3)
 require(done.returncode==0,'SERVICE_LAUNCH_FAILED:'+done.stderr[:1000]);new_json(output/'launch.json',{'unit':unit,'case':case,'command':cmd,'source_snapshot':snapshot,'profile':PROFILE,'launch_exit':done.returncode})
 if lose_controller:
  deadline=time.monotonic()+2
  while time.monotonic()<deadline:
   q=unit_properties(unit)
   if q.get('ControlGroup') and any(v.get('kind')=='ATTESTED' for v in records(output/'stdout.log')):
    cg=owned_cgroup(unit,q['ControlGroup']);return {'unit':unit,'output':str(output),'controller_loss_simulated':True,'initial':cgroup_read(cg),'controller_PID':os.getpid()}
   time.sleep(.02)
  raise ValueError('CONTROLLER_LOSS_FIXTURE_NEVER_ATTESTED')
 cgroup=None;observed=[];last={};stop=None;initial=None;leftovers=[]
 try:
  while True:
   last=unit_properties(unit)
   if last.get('ControlGroup'):
    cgroup=owned_cgroup(unit,last['ControlGroup']);value=cgroup_read(cgroup);observed.append(value)
    if initial is None:initial=value
    if cpu_usec(value)>=PROFILE['CPU_watchdog_stop_usec']:
     stop='AGGREGATE_CPU_EARLY_STOP';kill_owned(unit,cgroup);break
   if last.get('SubState')=='exited' or last.get('ActiveState') in ('failed','inactive') or last.get('LoadState')=='not-found':break
   if time.monotonic()-start>PROFILE['aggregate_wall_seconds']:
    stop='TOTAL_WALL_EARLY_STOP';kill_owned(unit,cgroup);break
   time.sleep(.02)
  if cgroup is not None:
   end=time.monotonic()+.5
   while time.monotonic()<end:
    value=cgroup_read(cgroup);observed.append(value)
    if not value.get('cgroup.procs','').strip():break
    if stop is not None:kill_owned(unit,cgroup)
    time.sleep(.02)
   leftovers=[int(n) for n in cgroup_read(cgroup).get('cgroup.procs','').split()]
   if leftovers:stop='RESIDUAL_CGROUP_PROCESSES';kill_owned(unit,cgroup)
  last=unit_properties(unit)
 finally:
  if cgroup is not None:kill_owned(unit,cgroup)
  stopped=subprocess.run(['systemctl','--user','stop',unit],env=host_env(),capture_output=True,text=True,timeout=3)
  require(wait_empty(cgroup,start+PROFILE['aggregate_wall_seconds']),'RESIDUAL_PROCESS_AFTER_CGROUP_KILL')
 elapsed=time.monotonic()-start
 logs=records(output/'stdout.log');stderr=records(output/'stderr.log')
 cpu=max([cpu_usec(v) for v in observed]+[int(last.get('CPUUsageNSec','0'))//1000 if last.get('CPUUsageNSec','0').isdigit() else 0])
 peak=max([int(v.get('memory.peak','0')) for v in observed]+[int(last.get('MemoryPeak','0')) if last.get('MemoryPeak','0').isdigit() else 0])
 require(digest(canary)==canary_before,'READONLY_CANARY_WAS_MODIFIED')
 require(source_snapshot()==snapshot,'RESOURCE_SOURCE_CHANGED_DURING_FIXTURE')
 require(not list((output/'work').iterdir()),'TMPFS_DID_NOT_ISOLATE_HOST_DIRECTORY')
 proof=[row for row in logs if row.get('kind')=='ATTESTED']
 require(proof and proof[0].get('valid') is True,'EFFECTIVE_KERNEL_LIMIT_ATTESTATION_MISSING')
 require(cpu<=4_000_000 and elapsed<=13.5,'ACTUAL_AGGREGATE_CPU_OR_WALL_LIMIT_VIOLATED')
 actual={'schema_version':1,'evidence_class':'SYNTHETIC_METHOD_ONLY','case':case,'unit':unit,'profile':PROFILE,'initial_cgroup':initial,'last_unit_properties':last,'max_observed_CPU_usec':cpu,'max_observed_memory_bytes':peak,'elapsed_including_host_cleanup_seconds':elapsed,'resource_stop':stop,'residual_pids_detected':leftovers,'residual_processes_after_cleanup':[],'stdout_records':logs,'stderr_records':stderr,'last_observed_cgroup':observed[-1] if observed else {},'source_snapshot_identity':snapshot['identity'],'host_work_directory_empty':True,'canary_preserved':True,'full_parser_or_physics_authorized':False,**ZERO}
 new_json(output/'result.json',actual);return actual
