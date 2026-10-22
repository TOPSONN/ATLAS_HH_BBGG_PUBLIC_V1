"""Independent original-byte validator: never imports or invokes the collector."""
import base64,json,re
from pathlib import Path
from . import diagnostic_contract as c
def require(test,why):
 if not test:raise ValueError(why)
def number(value):
 require(type(value) is int and 0<=value<2**64,'NUMERIC_VALUE');return value
def decimal(text):
 require(type(text) is str and re.fullmatch(r'0|[1-9][0-9]*',text) is not None and len(text)<=20,'COUNTER_SYNTAX')
 return number(int(text))
def properties(raw,allowed):
 result={}
 text=raw.decode('ascii');require('\x00' not in text,'PROPERTY_NUL')
 for line in text.splitlines():
  require('=' in line,'PROPERTY_SYNTAX');key,value=line.split('=',1)
  require(key in allowed and key not in result and len(value)<=512,'PROPERTY_KEY_OR_BOUND');result[key]=value
 return result
def check_snapshot(v):
 require(type(v) is dict,'MISSING_SNAPSHOT')
 for name in ('uid','gid','pid','start_ticks','monotonic_ns','pid1_start_ticks'):number(v[name])
 require(v['uid']>0 and v['pid']>0 and v['start_ticks']>0 and v['pid1_comm']=='systemd','SNAPSHOT_IDENTITY')
 require(re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',v['boot_id']) is not None,'BOOT_SYNTAX')
 path=v['membership'];require(type(path) is str and path.startswith('/') and '//' not in path and '..' not in path.split('/') and len(path)<=512,'CGROUP_PATH')
 expected=[path.lstrip('/') or '.']
 while expected[-1]!='.':expected.append(str(Path(expected[-1]).parent).replace('\\','/'))
 require(len(v['levels'])==len(expected)<=c.MAX_LEVELS,'LINEAGE_BOUND_OR_MISSING')
 missing=[];limits={};membership_checked=False
 for i,(row,name) in enumerate(zip(v['levels'],expected)):
  require(row['path']==name,'LINEAGE_ORDER')
  for key in ('device','inode','uid','gid','mode'):number(row[key])
  require(row['inode']>0 and set(row['fields'])==set(c.CG_FIELDS),'LINEAGE_FIELDS')
  for field,value in row['fields'].items():
   require(type(value) is dict and value.get('status') in ('UNKNOWN','OBSERVED'),'FIELD_STATUS')
   if value['status']=='UNKNOWN':
    number(value['errno']);missing.append({'level':i,'field':field,'root_nonroot_semantics':name=='.' and field not in ('cgroup.controllers','cgroup.subtree_control','cgroup.procs')});continue
   raw=value['text'];require(type(raw) is str and len(raw.encode('ascii'))<=c.READ_CAP,'FIELD_BOUND')
   text=raw.strip()
   if field in ('memory.max','memory.swap.max','pids.max'):limits[f'{i}:{field}']='UNLIMITED' if text=='max' else decimal(text)
   elif field=='cpu.max':
    pair=text.split();require(len(pair)==2,'CPU_MAX_FIELDS');limits[f'{i}:{field}']={'quota':'UNLIMITED' if pair[0]=='max' else decimal(pair[0]),'period':decimal(pair[1])};require(limits[f'{i}:{field}']['period']>0,'CPU_PERIOD')
   elif field=='cgroup.procs':
    pids=[decimal(x) for x in text.splitlines()] if text else [];require(all(p>0 for p in pids),'PID_VALUE')
    if i==0:require(v['pid'] in pids,'SELF_MEMBERSHIP');membership_checked=True
   elif field=='cgroup.events':
    pairs=[x.split() for x in text.splitlines()];require(all(len(x)==2 for x in pairs),'CGROUP_EVENTS')
    require(len({x[0] for x in pairs})==len(pairs),'DUPLICATE_EVENT');events={k:decimal(x) for k,x in pairs}
    require('populated' in events and all(x in (0,1) for x in events.values()),'EVENT_VALUE')
    if i==0:require(events['populated']==1,'POPULATED_CONTRADICTION')
   elif field=='cgroup.type':require(text in ('domain','domain threaded','domain invalid','threaded'),'CGROUP_TYPE')
   else:require(all(re.fullmatch('[a-z][a-z0-9_]*',t) for t in text.split()),'CONTROLLER_SYNTAX')
 require(membership_checked,'MISSING_SELF_MEMBERSHIP')
 return missing,limits

def review(raw,expected_sha,scope_raw,expected_scope_sha,authorization_reference):
 try:
  require(c.sha(raw)==expected_sha and c.sha(scope_raw)==expected_scope_sha,'ORIGINAL_BYTES_MISMATCH')
  scope=c.load(scope_raw);c.checked_scope(scope)
  require(authorization_reference==scope['authorization_reference'],'AUTHORIZATION_BINDING')
  v=c.load(raw);require(v['schema']==c.SCHEMA and v['scope_sha256']==c.sha(c.canonical(scope)),'SCOPE_BINDING')
  require(v['source_sha256']==scope['source_sha256'] and v['source_revision']==scope['source_revision'],'SOURCE_BINDING')
  require(v['tool_sha256']==scope['tool_sha256'],'TOOL_BINDING')
  require(v['authorization_reference']==authorization_reference,'AUTHORIZATION_BINDING')
  require(v['autostart_fallback'] is False and v['hard_resource_envelope'] is False,'FORBIDDEN_FALLBACK_OR_HARD_CLAIM')
  start=number(v['start_ns']);end=number(v['end_ns']);require(start<=end,'CLOCK_ORDER')
  require(len(v['queries'])<=3 and [x['argv'] for x in v['queries']]==scope['argvs'][:len(v['queries'])],'FIXED_QUERY_SEQUENCE')
  retained=0
  for row in v['queries']:
   if 'skipped' in row:require(row['skipped']=='NO_EXISTING_OWNED_SOCKET','SKIP_REASON');continue
   count=0
   for stream in ('stdout','stderr'):
    data=base64.b64decode(row[stream+'_b64'],validate=True);require(number(row[stream+'_bytes'])==len(data),'OUTPUT_SIZE');count+=len(data)
   retained+=count;require(count<=c.PER_CHILD and retained<=c.AGGREGATE,'OUTPUT_BOUND')
   require(start<=number(row['start_ns'])<=number(row['end_ns'])<=end,'QUERY_CLOCK')
   require(row['environment_sha256']==c.sha(c.canonical(scope['environment'])),'ENVIRONMENT_BINDING')
   require(row['cleanup'] in ('UNKNOWN','VERIFIED_GROUP_ABSENT'),'CLEANUP_ENUM')
   if row['exit_code'] is not None:number(row['exit_code'])
   if row['exit_signal'] is not None:number(row['exit_signal'])
   require(not(row['exit_code'] is not None and row['exit_signal'] is not None),'EXIT_CONTRADICTION')
  if v['before'] is None or v['after'] is None:
   require(v['failure'] is not None,'UNEXPLAINED_PARTIAL');return {'status':'UNKNOWN_MANAGER_STATE','partial_receipt':True,'cleanup':'UNKNOWN','freshness':'UNVERIFIED','actual_job_enforcement':False}
  before=v['before'];after=v['after'];missing,limits=check_snapshot(before);m2,_=check_snapshot(after);missing+=m2
  for key in ('boot_id','uid','gid','pid','start_ticks','membership','pid1_start_ticks'):require(before[key]==after[key],'BEFORE_AFTER_IDENTITY')
  require(set(before['namespace_inodes'])=={'mnt','cgroup','pid'} and before['namespace_inodes']==after['namespace_inodes'],'NAMESPACE_BINDING')
  for value in before['namespace_inodes'].values():require(number(value)>0,'NAMESPACE_INODE')
  require(before['uid']==scope['uid'] and before['gid']==scope['gid'],'UID_GID_SCOPE')
  require([(r['path'],r['device'],r['inode']) for r in before['levels']]==[(r['path'],r['device'],r['inode']) for r in after['levels']],'CGROUP_REPLACED')
  require(start<=before['monotonic_ns']<=after['monotonic_ns']<=end,'SNAPSHOT_CLOCK')
  require(len(v['queries'])<=3 and [x['argv'] for x in v['queries']]==scope['argvs'][:len(v['queries'])],'FIXED_QUERY_SEQUENCE')
  total=0;previous=before['monotonic_ns'];answers=[];unknown=[]
  for i,row in enumerate(v['queries']):
   if 'skipped' in row:require(row['skipped']=='NO_EXISTING_OWNED_SOCKET','SKIP_REASON');answers.append(None);unknown.append(i);continue
   a=number(row['start_ns']);b=number(row['end_ns']);require(previous<=a<=b<=after['monotonic_ns'],'QUERY_CLOCK');previous=b
   output={}
   for stream in ('stdout','stderr'):
    data=base64.b64decode(row[stream+'_b64'],validate=True);require(number(row[stream+'_bytes'])==len(data),'OUTPUT_SIZE');output[stream]=data
   count=sum(map(len,output.values()));total+=count;require(count<=c.PER_CHILD and total<=c.AGGREGATE,'OUTPUT_BOUND')
   require(row['environment_sha256']==c.sha(c.canonical(scope['environment'])),'ENVIRONMENT_BINDING')
   if row['cleanup']=='VERIFIED_GROUP_ABSENT':require(number(row['pid'])>0 and number(row['start_ticks'])>0,'CHILD_IDENTITY')
   require(row['cleanup'] in ('UNKNOWN','VERIFIED_GROUP_ABSENT'),'CLEANUP_ENUM')
   if row['exit_code'] is not None:number(row['exit_code'])
   if row['exit_signal'] is not None:number(row['exit_signal'])
   require(not(row['exit_code'] is not None and row['exit_signal'] is not None),'EXIT_CONTRADICTION')
   if row['cleanup']!='VERIFIED_GROUP_ABSENT' or row['stop_reason'] is not None or b-a>6_000_000_000:
    unknown.append(i);answers.append(None);continue
   if row['exit_code']!=0 or row['exit_signal'] is not None or output['stderr']:unknown.append(i);answers.append(None);continue
   allowed=('Version','SystemState') if i<2 else c.PROPS
   props=properties(output['stdout'],allowed)
   if set(props)!=set(allowed):unknown.append(i);answers.append(None);continue
   if i<2:require(re.fullmatch(r'255(?:[.\-+~ ][ -~]*)?',props['Version']) is not None and props['SystemState'] in ('initializing','starting','running','degraded','maintenance','stopping','offline','unknown'),'MANAGER_VERSION_OR_STATE')
   else:
    for key in ('Delegate','CPUAccounting','MemoryAccounting'):require(props[key] in ('yes','no'),'ACCOUNTING_PROPERTY')
    decimal(props['MainPID']);require(props['User']==str(scope['uid']),'USER_UNIT_IDENTITY')
    for key in ('MemoryMax','MemorySwapMax','TasksMax'):
     if props[key]!='infinity':decimal(props[key])
    quota=props['CPUQuotaPerSecUSec']
    require(quota=='infinity' or re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:us|ms|s|min|h|d|w|month|y)(?: (?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:us|ms|s|min|h|d|w|month|y))*',quota) is not None,'SYSTEMD_FORMATTED_DURATION')
    require(re.fullmatch('[0-9a-f]{32}',props['InvocationID']) is not None,'INVOCATION_ID')
    require(props['ControlGroup'].startswith('/') and '..' not in props['ControlGroup'].split('/'),'UNIT_CGROUP')
   answers.append(props)
  complete=len(v['queries'])==3 and not unknown and v['failure'] is None and end-start<=30_000_000_000 and not any(not x['root_nonroot_semantics'] for x in missing)
  manager=answers[0] if len(answers)>0 else None;user=answers[1] if len(answers)>1 else None
  return {'status':'UNKNOWN_DELEGATION' if complete else 'UNKNOWN_MANAGER_STATE',
   'observation_status':'PASS_READ_ONLY_OBSERVED' if complete else 'PARTIAL_READ_ONLY_OBSERVATION',
   'system_manager':None if manager is None else manager['SystemState'],'user_manager':None if user is None else user['SystemState'],
   'current_boot_consistent':True,'uid_gid_consistent':True,'lineage_count':len(before['levels']),'missing_fields':missing,
   'observed_limits':limits,'future_job_delegation':'UNKNOWN_DELEGATION','future_controller_collector_ownership':'UNKNOWN',
   'unit_accounting_observed':None if len(answers)<3 or answers[2] is None else {k:answers[2][k] for k in ('Delegate','CPUAccounting','MemoryAccounting','ActiveState')},
   'partial_query_indexes':unknown,'all_query_records_complete':complete,'current_freshness':'OBSERVATION_INTERVAL_ONLY_NOT_NOW',
   'actual_job_enforcement':False,'source_or_tool_attestation':False,'host_VM_costs_measured':False}
 except (ValueError,KeyError,TypeError,UnicodeError,OverflowError) as e:
  reason=str(e);status='BLOCKED_TOOL_IDENTITY' if reason=='BLOCKED_TOOL_IDENTITY' else 'BLOCKED_AUTHORIZATION' if reason in ('BLOCKED_AUTHORIZATION','AUTHORIZATION_BINDING') else 'FAIL_SOURCE_OR_RECEIPT_MISMATCH'
  return {'status':status,'reason':reason[:120],'actual_job_enforcement':False}

def main(argv=None):
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False)
 for n in ('receipt','scope','expected-sha256','expected-scope-sha256','authorization-reference'):p.add_argument('--'+n,required=True)
 a=p.parse_args(argv)
 def bounded(path):
  with Path(path).open('rb') as f:return f.read(c.RECEIPT_CAP+1)
 v=review(bounded(a.receipt),a.expected_sha256,bounded(a.scope),a.expected_scope_sha256,a.authorization_reference)
 print(json.dumps(v,indent=2));return 0 if v['status'] in ('PASS_READ_ONLY_OBSERVED','UNKNOWN_DELEGATION','UNKNOWN_MANAGER_STATE') else 2
if __name__=='__main__':raise SystemExit(main())
