"""Independent critical-tail oracle, a subset; not a second kernel enforcer."""
def review(rows,c):
 def equal(a,b):
  if type(a) is not type(b):return False
  if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
  if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
  return a==b
 def n(v):
  if not isinstance(v,str) or not v or any(ch<'0' or ch>'9' for ch in v) or (len(v)>1 and v[0]=='0'):raise ValueError('INDEPENDENT_DECIMAL')
  value=int(v)
  if value>=18446744073709551616:raise ValueError('INDEPENDENT_RANGE')
  return value
 if len(rows)!=9 or rows[0]['phase']!='ADMISSION' or rows[-1]['phase']!='INDEPENDENT_FINAL_OBSERVATION':raise ValueError('INDEPENDENT_ENDPOINTS')
 expected=c['identity'];last=-1
 for row in rows:
  if not equal(row['identity'],expected) or row['sample_start_ns']<=last or row['sample_end_ns']<row['sample_start_ns']:raise ValueError('INDEPENDENT_IDENTITY_CLOCK')
  if row.get('cause') is not None:raise ValueError('INDEPENDENT_FAILURE_EVENT')
  last=row['sample_end_ns']
 final=rows[-1];actor=final['actor'];collector=c['role_registry']['collector']
 if not equal(actor,c['observer']) or actor['pid']==collector['pid'] or actor['uid']==c['role_registry']['worker']['uid']:raise ValueError('INDEPENDENT_OBSERVER')
 if not equal(final['observed_collector_exit'],collector) or final['actor_source_sha256']!=c['observer_source_sha256']:raise ValueError('INDEPENDENT_EXIT_SOURCE_BINDING')
 if set(final['role_states'].values())!={'EXITED'} or final['observed_members']!=[] or final['membership_complete'] is not True:raise ValueError('INDEPENDENT_CLEANUP')
 def fields(text):
  result={}
  for line in text.splitlines():
   key,value=line.split()
   if key in result:raise ValueError('INDEPENDENT_DUPLICATE')
   result[key]=n(value)
  return result
 cpu=fields(final['raw']['cpu.stat'])['usage_usec'];cg=fields(final['raw']['cgroup.events'])
 profile={'S4':(4000000,13000000000,536870912),'BUILD':(14400000000,14400000000000,2147483648)}[c['profile']]
 elapsed=last-c['admission_ns']
 if cg['populated']!=0 or final['raw']['cgroup.procs']!='' or cpu>profile[0] or elapsed>profile[1] or elapsed<0:raise ValueError('INDEPENDENT_FINAL_BUDGET_OR_EMPTY')
 if n(final['raw']['memory.max'].strip())!=profile[2] or n(final['raw']['memory.swap.max'].strip())!=0:raise ValueError('INDEPENDENT_EFFECTIVE_LIMIT')
 if n(final['raw']['memory.peak'].strip())>profile[2] or n(final['raw']['memory.swap.current'].strip())!=0:raise ValueError('INDEPENDENT_MEMORY_FAILURE')
 if not equal(final['slot_commit'],{'identity':expected['evidence_slot_sha256'],'complete':True}):raise ValueError('INDEPENDENT_SLOT')
 return {'status':'PASS_INDEPENDENT_CRITICAL_TAIL_SUBSET','evidence_kind':'SYNTHETIC','CPU_usec':cpu,'wall_ns':elapsed,'actual_enforcement_proven':False}
