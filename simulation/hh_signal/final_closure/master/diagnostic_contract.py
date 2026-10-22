"""Fixed diagnostic contract; no acquisition or authority construction."""
import hashlib,json,re
SCHEMA='HH_G2_EFFECTIVE_DIAGNOSTIC_V1'
TOOLS=('/usr/bin/systemctl','/usr/bin/python3','/usr/bin/timeout')
SOURCE_NAMES=('diagnostic_tools.py','diagnostic_contract.py','diagnostic_capture.py','diagnostic_validate.py')
PER_CHILD=8192;AGGREGATE=32768;RECEIPT_CAP=131072;READ_CAP=256;MAX_LEVELS=8
CG_FIELDS=('cgroup.controllers','cgroup.subtree_control','cgroup.procs','cgroup.type','cgroup.events','cpu.max','memory.max','memory.swap.max','pids.max')
PROPS=('ControlGroup','Delegate','CPUAccounting','MemoryAccounting','MemoryMax','MemorySwapMax','CPUQuotaPerSecUSec','TasksMax','ActiveState','SubState','InvocationID','MainPID','User')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def need(ok,why):
 if not ok:raise ValueError(why)
def u64(v):
 need(type(v) is int and 0<=v<=2**64-1,'CANONICAL_U64');return v
def load(raw,cap=RECEIPT_CAP):
 need(type(raw) is bytes and len(raw)<=cap,'INPUT_BOUND')
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
  return d
 def bad(s):raise ValueError('NONCANONICAL_NUMBER')
 # Integer spelling checked before json loses negative-zero distinctions.
 def integer(s):need(re.fullmatch(r'0|[1-9][0-9]*',s) is not None and int(s)<=2**64-1,'CANONICAL_U64');return int(s)
 return json.loads(raw,object_pairs_hook=pairs,parse_int=integer,parse_float=bad,parse_constant=bad)
def argvs(uid):
 u64(uid);need(uid>0,'NONROOT')
 common=['/usr/bin/systemctl','--no-pager','--no-ask-password']
 manager=['show','--property=Version','--property=SystemState']
 return [common+['--system']+manager,common+['--user']+manager,
  common+['--system','show',f'user@{uid}.service']+['--property='+p for p in PROPS]]
def environment(uid):
 return {'PATH':'/usr/bin','LANG':'C','LC_ALL':'C','SYSTEMD_COLORS':'0','SYSTEMD_PAGER':'',
  'XDG_RUNTIME_DIR':f'/run/user/{uid}',
  'DBUS_SYSTEM_BUS_ADDRESS':'unix:path=/run/dbus/system_bus_socket',
  # v255 fallback is directed at a guaranteed invalid FD, never the session bus.
  'DBUS_SESSION_BUS_ADDRESS':'unix:path=/proc/self/fd/-1'}
def checked_scope(scope):
 need(scope.get('schema')=='HH_G2_DIAGNOSTIC_SCOPE_V1','SCOPE_SCHEMA')
 need(set(scope['tool_sha256'])==set(TOOLS),'EXACT_TOOL_SET')
 for value in scope['tool_sha256'].values():need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'BLOCKED_TOOL_IDENTITY')
 need(set(scope['source_sha256'])==set(SOURCE_NAMES),'EXACT_SOURCE_SET')
 for value in scope['source_sha256'].values():need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,'SOURCE_IDENTITY')
 need(type(scope['source_revision']) is str and re.fullmatch('[0-9a-f]{40}',scope['source_revision']) is not None,'SOURCE_REVISION')
 uid=u64(scope['uid']);u64(scope['gid']);need(uid>0 and scope['argvs']==argvs(uid),'FIXED_ARGV')
 need(scope['environment']==environment(uid),'FIXED_ENVIRONMENT')
 need(scope['output']== '/home/btu/simulations/hh_final_closure/g2_effective_diagnostic_01','FIXED_PRIVATE_OUTPUT')
 need(scope.get('authorization_reference') is not None and re.fullmatch('[0-9a-f]{64}',scope['authorization_reference']) is not None,'BLOCKED_AUTHORIZATION')
 need(scope['limits']=={'child_seconds':5,'cleanup_seconds':1,'adapter_soft_seconds':30,'per_child_bytes':PER_CHILD,'aggregate_bytes':AGGREGATE,'receipt_bytes':RECEIPT_CAP,'max_levels':MAX_LEVELS},'EXACT_LIMITS')
 for value in scope['limits'].values():u64(value)
 need(scope.get('systemd_source_family_review')=='255_DIRECT_PRIVATE_NO_AUTOSTART_WITH_POISONED_FALLBACK','VERSION_REVIEW_REQUIRED')
 return scope
