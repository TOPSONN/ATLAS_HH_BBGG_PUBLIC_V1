"""Pure proposed-job accounting/observer protocol. No OS reader or dispatcher.

All positive results are input consistency, including authentic-looking inputs.
Trusted acquisition, privilege isolation and kernel enforcement remain external.
Historical readers are preserved; V2 supports an aggregate with child cgroups.
"""
import re,uuid
from .contract import LIMITS,canonical,need,sha
from .readiness_validation import cgroup_number,cgroup_pairs,cgroup_limit

U64=2**64-1
PHASES=('ADMISSION','ACTIVATION','CONTROLLER_START','WORKER','TERMINATION','POSTMORTEM',
 'DESCENDANT_CLEANUP','COLLECTOR_FINALIZATION','INDEPENDENT_FINAL_OBSERVATION')
MEMORY_KEYS=('low','high','max','oom','oom_kill','oom_group_kill')
IDENTITY_KEYS={'boot_id','InvocationID','run_nonce','cgroup','source_sha256','config_sha256','evidence_slot_sha256'}
FAILURES=('OOM','TIMEOUT','CONTROLLER_LOSS','COLLECTOR_LOSS','ENOSPC','COUNTER_MISSING','IDENTITY_CHANGED')

def integer(n):return type(n) is int and 0<=n<=U64
def checked_add(*values):
 total=0
 for value in values:
  need(integer(value) and value<=U64-total,'INTEGER_OVERFLOW_OR_TYPE');total+=value
 return total
def checked_mul(a,b):
 need(integer(a) and integer(b) and (a==0 or b<=U64//a),'INTEGER_OVERFLOW_OR_TYPE');return a*b
def digest(s):return type(s) is str and re.fullmatch('[a-f0-9]{64}',s) is not None
def group(g):
 need(type(g) is dict and set(g)=={'dev','inode'} and all(integer(n) and n>0 for n in g.values()),'CGROUP_IDENTITY')
 return g
def process(p):
 need(type(p) is dict and set(p)=={'pid','start_ticks','uid','group'} and all(integer(p[k]) for k in ('pid','start_ticks','uid')) and p['pid']>0 and p['start_ticks']>0,'PROCESS_IDENTITY')
 group(p['group']);return p
def identity(v):
 need(type(v) is dict and set(v)==IDENTITY_KEYS,'JOB_IDENTITY_FIELDS')
 for name in ('boot_id','run_nonce'):need(type(v[name]) is str and str(uuid.UUID(v[name]))==v[name],'UUID_IDENTITY')
 need(type(v['InvocationID']) is str and re.fullmatch('[a-f0-9]{32}',v['InvocationID']) is not None,'INVOCATION_ID')
 need(all(digest(v[k]) for k in ('source_sha256','config_sha256','evidence_slot_sha256')),'SOURCE_CONFIG_SLOT_IDENTITY')
 group(v['cgroup']);return v

def contract_review(c):
 need(type(c) is dict and c.get('schema')=='HH_G2_TRACE_CONTRACT_V2' and c.get('profile') in LIMITS,'CONTRACT_SCHEMA')
 identity(c['identity']);profile=LIMITS[c['profile']]
 need(c.get('boundary')=='B_V2_PROPOSED_NOT_ACCEPTED','NO_ORIGINAL_A_ENFORCEMENT_CLAIM')
 need(c.get('memory_event_scope')=='HIERARCHICAL_DEFAULT_VERIFIED','HIERARCHICAL_EVENT_SCOPE_UNVERIFIED')
 roles=c['role_registry'];need(type(roles) is dict and {'controller','worker','collector'}<=set(roles) and 3<=len(roles)<=64,'ROLE_REGISTRY')
 ids=[]
 for name,p in roles.items():
  need(type(name) is str and re.fullmatch('[a-z_]{1,32}',name) is not None,'ROLE_NAME');process(p);need(p['uid']>0,'NONROOT_JOB_ROLES_REQUIRED')
  ids.append((p['pid'],p['start_ticks']))
  need(p['group']!=c['identity']['cgroup'],'DOMAIN_PARENT_MUST_HOST_ONLY_CHILD_GROUPS')
 need(len(ids)==len(set(ids)) and len({p['pid'] for p in roles.values()})==len(ids),'DUPLICATE_PROCESS_IDENTITY')
 need(roles['collector']['uid'] not in (roles['worker']['uid'],roles['controller']['uid']),'COLLECTOR_NOT_PROTECTED_FROM_WORKER_CONTROLLER_UID')
 observer=process(c['observer'])
 need(observer['pid'] not in {p['pid'] for p in roles.values()} and observer['group']!=c['identity']['cgroup'] and observer['group'] not in [p['group'] for p in roles.values()],'OBSERVER_IN_JOB_DEATH_DOMAIN')
 need(observer['uid'] not in {p['uid'] for p in roles.values()} and digest(c.get('observer_source_sha256')),'OBSERVER_PROTECTION_OR_SOURCE')
 cpu=checked_mul(profile['CPU_seconds'],1000000);wall=checked_mul(profile['wall_seconds'],1000000000)
 need(integer(c.get('early_cpu_usec')) and 0<c['early_cpu_usec']<cpu,'EARLY_CPU_THRESHOLD')
 need(integer(c.get('early_wall_ns')) and 0<c['early_wall_ns']<wall,'EARLY_WALL_THRESHOLD')
 need(integer(c.get('term_grace_ns')) and 0<c['term_grace_ns']<=wall-c['early_wall_ns'],'TERMINATION_GRACE')
 need(integer(c.get('admission_ns')) and c['admission_ns']<=U64-wall,'DEADLINE_OVERFLOW')
 rate=c.get('cpu_rate');need(type(rate) is dict and set(rate)=={'quota_usec','period_usec'} and all(integer(n) for n in rate.values()) and rate['quota_usec']>0 and 1000<=rate['period_usec']<=1000000,'EXACT_CPU_RATE')
 fields=c.get('phase_budget_ns');need(type(fields) is dict and set(fields)==set(PHASES) and all(integer(n) and n>0 for n in fields.values()),'PHASE_BUDGETS')
 need(checked_add(*fields.values())<=wall,'PHASE_BUDGET_SUM')
 return {'CPU_usec':cpu,'wall_ns':wall,'RAM_bytes':profile['RAM_bytes'],'deadline_ns':checked_add(c['admission_ns'],wall)}

def decode_snapshot(raw):
 """Strict text subset. cgroup.procs lists direct members, not descendants."""
 required={'cpu.stat','cpu.max','memory.max','memory.current','memory.peak','memory.events',
  'memory.events.local','memory.swap.max','memory.swap.current','cgroup.events','cgroup.procs'}
 need(type(raw) is dict and set(raw)==required,'EXACT_RAW_COUNTER_SET')
 need(all(type(t) is str and len(t.encode())<=4096 and '\r' not in t and '\x00' not in t for t in raw.values()),'RAW_TEXT_BOUND')
 need(sum(len(t.encode()) for t in raw.values())<=32768,'RAW_AGGREGATE_BOUND')
 cpu=cgroup_pairs(raw['cpu.stat']);need({'usage_usec','user_usec','system_usec'}<=set(cpu),'CPU_COUNTER_MISSING')
 # Linux6.6 rstat cputime_adjust derives parts from runtime. Retain rounding
 # tolerance; this is consistency for that reviewed ABI, not counter attestation.
 parts=checked_add(cpu['user_usec'],cpu['system_usec']);need(abs(parts-cpu['usage_usec'])<=2,'CPU_PARTS_CONTRADICTION')
 events=cgroup_pairs(raw['memory.events']);local=cgroup_pairs(raw['memory.events.local'])
 need(set(MEMORY_KEYS)<=set(events) and set(MEMORY_KEYS)<=set(local),'MEMORY_COUNTER_MISSING')
 cg=cgroup_pairs(raw['cgroup.events']);need({'populated','frozen'}<=set(cg) and all(cg[k] in (0,1) for k in ('populated','frozen')),'CGROUP_EVENTS')
 quota=raw['cpu.max'].split();need(len(quota)==2,'CPU_RATE_SHAPE')
 q=cgroup_limit('cpu.max:quota',quota[0]);period=cgroup_number(quota[1])
 need(q!='UNLIMITED' and q>0 and 1000<=period<=1000000,'FINITE_CPU_BANDWIDTH_REQUIRED')
 pids=[cgroup_number(x) for x in raw['cgroup.procs'].splitlines()]
 need(len(pids)<=256 and all(n>0 for n in pids),'DIRECT_PID_BOUND')
 # Duplicated PIDs may occur in a live seq_file read. Deduplication is explicit;
 # populated=1 with an empty direct list is valid for a parent with live children.
 return {'cpu':cpu,'events':events,'local_events':local,'populated':cg['populated'],'frozen':cg['frozen'],
  'direct_pids':sorted(set(pids)),'direct_pid_duplicate_count':len(pids)-len(set(pids)),
  'memory_max':cgroup_limit('memory.max',raw['memory.max'].strip()),
  'swap_max':cgroup_limit('memory.swap.max',raw['memory.swap.max'].strip()),
  'current':cgroup_number(raw['memory.current'].strip()),'peak':cgroup_number(raw['memory.peak'].strip()),
  'swap_current':cgroup_number(raw['memory.swap.current'].strip()),'quota_usec':q,'period_usec':period,
  'raw_sha256':sha(canonical(raw))}

def review_trace(rows,c):
 limit=contract_review(c)
 need(type(rows) is list and len(rows)==len(PHASES) and len(canonical(rows))<=262144,'TRACE_BOUND_OR_MISSING_PHASE')
 roles=c['role_registry'];prior=None;states={n:'NOT_STARTED' for n in roles};last_cpu=None;last_events=None;last_local=None;last_peak=None
 for index,(phase,row) in enumerate(zip(PHASES,rows)):
  need(type(row) is dict and row.get('phase')==phase and integer(row.get('sequence')) and row.get('sequence')==index,'LIFECYCLE_TRANSITION')
  identity(row.get('identity'));need(canonical(row['identity'])==canonical(c['identity']),'JOB_IDENTITY_REPLAY_OR_SUBSTITUTION')
  process(row.get('actor'))
  need(row.get('role_registry_sha256')==sha(canonical(roles)),'ROLE_REGISTRY_SUBSTITUTION')
  start=row.get('sample_start_ns');end=row.get('sample_end_ns')
  need(integer(start) and integer(end) and start<=end and start>=c['admission_ns'],'SAMPLE_CLOCK')
  need(prior is None or start>prior,'REPLAYED_OR_OVERLAPPING_SAMPLE')
  beginning=c['admission_ns'] if prior is None else prior
  need(end-beginning<=c['phase_budget_ns'][phase] and end<=limit['deadline_ns'],'PHASE_OR_TOTAL_WALL_OVERRUN')
  prior=end
  need(row.get('cause') is None,'FAILURE_EVENT_NOT_SUCCESS')
  current=row.get('role_states');need(type(current) is dict and set(current)==set(roles),'ROLE_STATES_MISSING')
  for name,state in current.items():
   need(state in ('NOT_STARTED','RUNNING','EXITED'),'ROLE_LOST_OR_UNKNOWN')
   need(not (states[name]=='EXITED' and state!='EXITED') and not (states[name]=='RUNNING' and state=='NOT_STARTED'),'ROLE_RESURRECTION')
  states=current
  need(row.get('membership_complete') is True and row.get('all_registered_roles_under_parent') is True,'MEMBERSHIP_UNVERIFIED')
  members=row.get('observed_members');need(type(members) is list and len(members)<=64 and len(members)==len(set(members)) and set(members)<=set(roles),'UNREGISTERED_OR_DUPLICATE_MEMBERS')
  need(set(members)=={n for n,s in states.items() if s=='RUNNING'},'MEMBERSHIP_ROLE_CONTRADICTION')
  sample=decode_snapshot(row.get('raw'));cpu=sample['cpu'];events=sample['events']
  need(sample['quota_usec']==c['cpu_rate']['quota_usec'] and sample['period_usec']==c['cpu_rate']['period_usec'],'CPU_RATE_CONFIGURATION_CHANGED')
  need(not sample['direct_pids'],'NO_INTERNAL_PROCESS_PARENT_REQUIRED')
  need(sample['memory_max']==limit['RAM_bytes'] and sample['swap_max']==0,'EFFECTIVE_MEMORY_SWAP_LIMITS')
  need(sample['peak']<=limit['RAM_bytes'] and sample['current']<=limit['RAM_bytes'] and sample['swap_current']==0,'RAM_PEAK_OR_SWAP_FAILURE')
  need(events['oom']==events['oom_kill']==events['oom_group_kill']==0 and sample['local_events']['oom']==sample['local_events']['oom_kill']==sample['local_events']['oom_group_kill']==0,'OOM_FAILURE')
  need(cpu['usage_usec']<=limit['CPU_usec'],'AGGREGATE_CPU_OVERRUN')
  if last_cpu is not None:need(all(cpu[k]>=last_cpu[k] for k in ('usage_usec','user_usec','system_usec')) and all(events[k]>=last_events[k] and sample['local_events'][k]>=last_local[k] for k in MEMORY_KEYS) and sample['peak']>=last_peak,'COUNTER_RESET')
  last_cpu=cpu;last_events=events;last_local=sample['local_events'];last_peak=sample['peak']
  if index==0:
   need(start==c['admission_ns'] and cpu['usage_usec']==0 and sample['populated']==0 and set(states.values())=={'NOT_STARTED'},'FRESH_EMPTY_ADMISSION_REQUIRED')
  if phase=='CONTROLLER_START':need(states['controller']=='RUNNING','CONTROLLER_START_MISSING')
  if phase=='WORKER':need(states['worker']=='RUNNING' and states['controller']=='RUNNING' and states['collector']=='RUNNING','WORKER_PHASE_MEMBERSHIP')
  if index>=PHASES.index('POSTMORTEM'):need(states['worker']=='EXITED','WORKER_NOT_EXITED_BEFORE_POSTMORTEM')
  if phase=='COLLECTOR_FINALIZATION':need(states['collector']=='RUNNING' and all(s=='EXITED' for n,s in states.items() if n!='collector'),'COLLECTOR_FINALIZATION_STATE')
  if index==len(PHASES)-1:
   need(row.get('actor')==c['observer'] and row.get('actor_source_sha256')==c['observer_source_sha256'],'INDEPENDENT_OBSERVER_IDENTITY')
   process(row.get('observed_collector_exit'));need(canonical(row['observed_collector_exit'])==canonical(roles['collector']),'COLLECTOR_PID_START_EXIT_BINDING')
   need(set(states.values())=={'EXITED'} and sample['populated']==0 and members==[],'FINAL_CLEANUP_NOT_PROVEN')
   slot=row.get('slot_commit')
   need(digest(row.get('postmortem_sha256')) and type(slot) is dict and set(slot)=={'identity','complete'} and slot['identity']==c['identity']['evidence_slot_sha256'] and slot['complete'] is True,'POSTMORTEM_OR_SLOT_COMMIT_MISSING')
  else:need(row.get('actor') in (c['observer'],roles['collector']),'UNREVIEWED_READER_ACTOR')
 return {'status':'PASS_G2_TRACE_INPUT_CONSISTENCY_ONLY','scope':'REPORTED_OR_SYNTHETIC_BYTES_NOT_KERNEL_ATTESTATION',
  'CPU_usec':last_cpu['usage_usec'],'wall_ns':prior-c['admission_ns'],'counter_boundary':'ONE_PARENT_NO_PER_ROLE_BUDGET',
  'actual_job_enforcement_verified':False,'observer_actually_deployed':False,'original_A_satisfied':False,
  'FULL_LAUNCH_ENVELOPE_VERIFIED':False,'execution_authorized':False}

def stop_decision(state,event,*,cpu_usec,elapsed_ns,stop_elapsed_ns,c):
 """Bounded declarative state machine. Returns requests; executes nothing."""
 limit=contract_review(c)
 need(state in ('RUNNING','TERM_REQUESTED','KILL_REQUESTED','DRAINING_COLLECTOR','WAIT_OBSERVER','UNKNOWN'),'STOP_STATE')
 need(event in ('POLL','WORKER_DOMAIN_EXITED','COLLECTOR_EXITED','FINAL_ACCEPTED','OBSERVER_LOST',*FAILURES),'STOP_EVENT')
 need(all(integer(n) for n in (cpu_usec,elapsed_ns,stop_elapsed_ns)),'STOP_COUNTER_TYPE')
 need(stop_elapsed_ns<=elapsed_ns,'STOP_GRACE_CLOCK_CONTRADICTION')
 if state=='UNKNOWN':return {'state':'UNKNOWN','action':'PRESERVE_COMMITTED_ONLY','accept':False}
 if event in ('OBSERVER_LOST','COLLECTOR_LOSS') or elapsed_ns>limit['wall_ns'] or cpu_usec>limit['CPU_usec']:return {'state':'UNKNOWN','action':'REQUEST_MANAGER_ALL_JOB_CLEANUP_RETAIN_COMMITTED_ONLY','accept':False}
 if event=='COLLECTOR_EXITED':
  need(state=='DRAINING_COLLECTOR','UNEXPECTED_COLLECTOR_EXIT')
  return {'state':'WAIT_OBSERVER','action':'REQUIRE_INDEPENDENT_FINAL_READBACK','accept':False}
 if event=='WORKER_DOMAIN_EXITED':
  need(state in ('RUNNING','TERM_REQUESTED','KILL_REQUESTED'),'UNEXPECTED_WORKER_DOMAIN_EXIT')
  return {'state':'DRAINING_COLLECTOR','action':'REQUEST_BOUNDED_COLLECTOR_POSTMORTEM_AND_EXIT','accept':False}
 if state=='RUNNING' and (event in FAILURES or cpu_usec>=c['early_cpu_usec'] or elapsed_ns>=c['early_wall_ns']):return {'state':'TERM_REQUESTED','action':'REQUEST_WORKER_CONTROLLER_TERM_KEEP_COLLECTOR_ACCOUNTED','accept':False}
 if state=='TERM_REQUESTED' and stop_elapsed_ns>=c['term_grace_ns']:return {'state':'KILL_REQUESTED','action':'REQUEST_MANAGER_WORKER_DOMAIN_KILL','accept':False}
 # A message called FINAL_ACCEPTED cannot replace review_trace and protected
 # acquisition; no stop decision can authorize a job or accept its outcome.
 return {'state':state,'action':'OBSERVE_BOUNDED_TRANSITION','accept':False}

def memory_plan(profile,components,*,fresh_private_tmpfs,ancestor_exclusivity_verified):
 need(profile in LIMITS and type(components) is dict and set(components)=={'work_resident','private_resident','process_runtime','collector','kernel_and_cache','safety_reserve'},'MEMORY_COMPONENTS')
 need(all(integer(n) for n in components.values()),'UNKNOWN_OR_INVALID_MEMORY_ALLOCATION')
 need(fresh_private_tmpfs is True and ancestor_exclusivity_verified is True,'SHARED_OR_PRECHARGED_PAGES_UNVERIFIED')
 total=checked_add(*components.values());need(total<=LIMITS[profile]['RAM_bytes'],'RAM_ALLOCATION_SUM_EXCEEDS_POOL')
 need(components['process_runtime']>0 and components['collector']>0 and components['kernel_and_cache']>0 and components['safety_reserve']>0,'RUNTIME_OR_FAILURE_RESERVE_MISSING')
 return {'status':'PASS_MEMORY_PLAN_ARITHMETIC_ONLY','resident_bytes':total,'unassigned_bytes':LIMITS[profile]['RAM_bytes']-total,'actual_memory_enforcement_verified':False}
