"""Synthetic V2 traces only. Never constructs a real cgroup or authorization."""
import copy,unittest
from . import g2_protocol as p
from .contract import canonical,sha

def fixture():
 parent={'dev':1,'inode':20}
 def role(pid,uid,ino):return {'pid':pid,'start_ticks':100+pid,'uid':uid,'group':{'dev':1,'inode':ino}}
 identity={'boot_id':'11111111-1111-4111-8111-111111111111','run_nonce':'22222222-2222-4222-8222-222222222222',
  'InvocationID':'a'*32,'cgroup':parent,'source_sha256':'b'*64,'config_sha256':'c'*64,'evidence_slot_sha256':'d'*64}
 c={'schema':'HH_G2_TRACE_CONTRACT_V2','identity':identity,'profile':'S4','boundary':'B_V2_PROPOSED_NOT_ACCEPTED',
  'memory_event_scope':'HIERARCHICAL_DEFAULT_VERIFIED','role_registry':{'controller':role(2,1000,21),'worker':role(3,1000,21),'collector':role(4,1001,22)},
  'observer':role(5,1002,30),'observer_source_sha256':'e'*64,'early_cpu_usec':3000000,'early_wall_ns':10000000000,
  'term_grace_ns':500000000,'admission_ns':100,'cpu_rate':{'quota_usec':3000,'period_usec':10000},'phase_budget_ns':{n:1000000000 for n in p.PHASES}}
 rows=[]
 for i,phase in enumerate(p.PHASES):
  states={'controller':'NOT_STARTED' if i<2 else 'RUNNING' if i<6 else 'EXITED',
   'worker':'NOT_STARTED' if i<3 else 'RUNNING' if i<5 else 'EXITED',
   'collector':'NOT_STARTED' if i<1 else 'RUNNING' if i<8 else 'EXITED'}
  events=''.join(k+' 0\n' for k in p.MEMORY_KEYS)
  raw={'cpu.stat':f'usage_usec {i*100}\nuser_usec {i*100}\nsystem_usec 0\n','cpu.max':'3000 10000\n','memory.max':'536870912\n',
   'memory.current':'100\n','memory.peak':str(100+i)+'\n','memory.events':events,'memory.events.local':events,
   'memory.swap.max':'0\n','memory.swap.current':'0\n','cgroup.events':f'populated {0 if i in (0,8) else 1}\nfrozen 0\n','cgroup.procs':''}
  row={'phase':phase,'sequence':i,'identity':copy.deepcopy(identity),'role_registry_sha256':sha(canonical(c['role_registry'])),
   'sample_start_ns':100+i*100000000,'sample_end_ns':101+i*100000000,'cause':None,'role_states':states,
   'membership_complete':True,'all_registered_roles_under_parent':True,'observed_members':[n for n,s in states.items() if s=='RUNNING'],
   'raw':raw,'actor':copy.deepcopy(c['observer'] if i in (0,8) else c['role_registry']['collector'])}
  if i==8:row.update(actor_source_sha256=c['observer_source_sha256'],observed_collector_exit=copy.deepcopy(c['role_registry']['collector']),
   postmortem_sha256='f'*64,slot_commit={'identity':identity['evidence_slot_sha256'],'complete':True})
  rows.append(row)
 return rows,c

def negative_cases():
 """Named semantic failures, emitted verbatim as synthetic test evidence."""
 changes=[
 ('boolean_sequence',lambda r,c:r[0].update(sequence=False),'LIFECYCLE_TRANSITION'),
 ('boolean_identity',lambda r,c:r[-1]['identity']['cgroup'].update(dev=True),'CGROUP_IDENTITY'),
 ('numeric_slot_complete',lambda r,c:r[-1]['slot_commit'].update(complete=1),'SLOT_COMMIT'),
 ('foreign_boot',lambda r,c:r[-1]['identity'].update(boot_id='33333333-3333-4333-8333-333333333333'),'JOB_IDENTITY'),
 ('replayed_invocation',lambda r,c:r[-1]['identity'].update(InvocationID='0'*32),'JOB_IDENTITY'),
 ('foreign_cgroup',lambda r,c:r[-1]['identity']['cgroup'].update(inode=99),'JOB_IDENTITY'),
 ('replayed_run_nonce',lambda r,c:r[-1]['identity'].update(run_nonce='33333333-3333-4333-8333-333333333333'),'JOB_IDENTITY'),
 ('wrong_source',lambda r,c:r[-1]['identity'].update(source_sha256='0'*64),'JOB_IDENTITY'),
 ('wrong_config',lambda r,c:r[-1]['identity'].update(config_sha256='0'*64),'JOB_IDENTITY'),
 ('wrong_slot',lambda r,c:r[-1]['slot_commit'].update(identity='0'*64),'SLOT_COMMIT'),
 ('uncommitted_slot',lambda r,c:r[-1]['slot_commit'].update(complete=False),'SLOT_COMMIT'),
 ('observer_self_exit_claim',lambda r,c:r[-1].update(actor=c['role_registry']['collector']),'OBSERVER_IDENTITY'),
 ('observer_pid_start_substitution',lambda r,c:r[-1]['actor'].update(start_ticks=999),'OBSERVER_IDENTITY'),
 ('observer_source_substitution',lambda r,c:r[-1].update(actor_source_sha256='0'*64),'OBSERVER_IDENTITY'),
 ('collector_exit_unbound',lambda r,c:r[-1]['observed_collector_exit'].update(start_ticks=999),'EXIT_BINDING'),
 ('role_registry_substitution',lambda r,c:r[-1].update(role_registry_sha256='0'*64),'REGISTRY_SUBSTITUTION'),
 ('unknown_member',lambda r,c:r[3]['observed_members'].append('other'),'UNREGISTERED'),
 ('duplicate_member',lambda r,c:r[3]['observed_members'].append('worker'),'DUPLICATE_MEMBERS'),
 ('membership_not_complete',lambda r,c:r[-1].update(membership_complete=False),'MEMBERSHIP_UNVERIFIED'),
 ('membership_escape',lambda r,c:r[-1].update(all_registered_roles_under_parent=False),'MEMBERSHIP_UNVERIFIED'),
 ('collector_loss',lambda r,c:r[5]['role_states'].update(collector='LOST'),'ROLE_LOST'),
 ('controller_loss',lambda r,c:r[4].update(cause='CONTROLLER_LOSS'),'FAILURE_EVENT'),
 ('resurrection',lambda r,c:r[-1]['role_states'].update(worker='RUNNING'),'RESURRECTION'),
 ('duplicate_record',lambda r,c:r.__setitem__(4,copy.deepcopy(r[3])),'TRANSITION'),
 ('wrong_wall_endpoint',lambda r,c:r[-1].update(phase='MAIN_EXIT'),'TRANSITION'),
 ('replayed_timestamp',lambda r,c:r[-1].update(sample_start_ns=r[-2]['sample_end_ns']),'OVERLAPPING_SAMPLE'),
 ('final_cleanup_not_empty',lambda r,c:r[-1]['raw'].update({'cgroup.events':'populated 1\nfrozen 0\n'}),'CLEANUP'),
 ('aggregate_CPU_overrun',lambda r,c:r[-1]['raw'].update({'cpu.stat':'usage_usec 4000001\nuser_usec 4000001\nsystem_usec 0\n'}),'CPU_OVERRUN'),
 ('CPU_counter_reset',lambda r,c:r[-1]['raw'].update({'cpu.stat':'usage_usec 1\nuser_usec 1\nsystem_usec 0\n'}),'COUNTER_RESET'),
 ('CPU_parts_contradiction',lambda r,c:r[-1]['raw'].update({'cpu.stat':'usage_usec 1\nuser_usec 900\nsystem_usec 0\n'}),'PARTS_CONTRADICTION'),
 ('missing_CPU',lambda r,c:r[-1]['raw'].update({'cpu.stat':'user_usec 1\nsystem_usec 0\n'}),'COUNTER_MISSING'),
 ('duplicate_flat_counter',lambda r,c:r[-1]['raw'].update({'cpu.stat':'usage_usec 1\nusage_usec 2\n'}),'DUPLICATE'),
 ('unlimited_CPU_rate',lambda r,c:r[-1]['raw'].update({'cpu.max':'max 100000\n'}),'FINITE_CPU'),
 ('rate_changed',lambda r,c:r[-1]['raw'].update({'cpu.max':'6000 10000\n'}),'RATE_CONFIGURATION'),
 ('unlimited_RAM',lambda r,c:r[-1]['raw'].update({'memory.max':'max\n'}),'EFFECTIVE_MEMORY'),
 ('unlimited_swap',lambda r,c:r[-1]['raw'].update({'memory.swap.max':'max\n'}),'EFFECTIVE_MEMORY'),
 ('swap_usage',lambda r,c:r[-1]['raw'].update({'memory.swap.current':'1\n'}),'SWAP_FAILURE'),
 ('missing_peak',lambda r,c:r[-1]['raw'].pop('memory.peak'),'RAW_COUNTER_SET'),
 ('peak_reset',lambda r,c:r[-1]['raw'].update({'memory.peak':'1\n'}),'COUNTER_RESET'),
 ('peak_overrun',lambda r,c:r[-1]['raw'].update({'memory.peak':'536870913\n'}),'RAM_PEAK'),
 ('OOM',lambda r,c:r[-1]['raw'].update({'memory.events':r[-1]['raw']['memory.events'].replace('oom_kill 0','oom_kill 1')}),'OOM_FAILURE'),
 ('negative_usage',lambda r,c:r[-1]['raw'].update({'memory.current':'-1\n'}),'COUNTER_SYNTAX'),
 ('overflow_usage',lambda r,c:r[-1]['raw'].update({'memory.current':str(2**64)+'\n'}),'COUNTER_RANGE'),
 ('failure_cause',lambda r,c:r[-1].update(cause='TIMEOUT'),'FAILURE_EVENT'),
 ('phase_timeout',lambda r,c:r[-1].update(sample_end_ns=12000000100),'PHASE_OR_TOTAL'),
 ]
 results=[]
 for name,change,reason in changes:
  rows,c=fixture();change(rows,c)
  try:p.review_trace(rows,c)
  except ValueError as e:results.append({'case':name,'status':'PASS_REJECTED' if reason in str(e) else 'FAIL_WRONG_REASON','reason':str(e),'evidence_kind':'SYNTHETIC'})
  else:results.append({'case':name,'status':'FAIL_ACCEPTED','reason':None,'evidence_kind':'SYNTHETIC'})
 return results

class ProtocolTests(unittest.TestCase):
 def test_complete_parent_with_child_groups_is_consistency_only(self):
  rows,c=fixture();r=p.review_trace(rows,c)
  self.assertFalse(r['actual_job_enforcement_verified']);self.assertFalse(r['execution_authorized'])
  self.assertEqual(p.decode_snapshot(rows[3]['raw'])['direct_pids'],[])
  self.assertEqual(p.decode_snapshot(rows[3]['raw'])['populated'],1)
 def test_named_semantic_negatives(self):
  bad=[r for r in negative_cases() if r['status']!='PASS_REJECTED'];self.assertEqual(bad,[])
 def test_duplicate_pid_in_seqfile_is_not_proof_of_duplicate_process(self):
  rows,c=fixture();raw=rows[3]['raw'];raw['cgroup.procs']='5\n5\n'
  d=p.decode_snapshot(raw);self.assertEqual(d['direct_pid_duplicate_count'],1);self.assertEqual(d['direct_pids'],[5])
  with self.assertRaisesRegex(ValueError,'NO_INTERNAL_PROCESS'):p.review_trace(rows,c)
 def test_original_raw_reader_hierarchy_defect_is_reproduced_without_kernel(self):
  from ..resource_closure import job_envelope as old
  raw={n:(v+'\n').encode() for n,v in old.EFFECTIVE.items()}
  rows,_=fixture()
  for n in ('cpu.stat','memory.current','memory.peak','memory.swap.current','memory.events','cgroup.events','cgroup.procs'):raw[n]=rows[3]['raw'][n].encode()
  with self.assertRaisesRegex(ValueError,'POPULATED_PROCESS_CONTRADICTION'):
   old.parse_cgroup_raw(raw,aggregate_cgroup='/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/atlas-hh-phase7i-test.service',cgroup_identity={'dev':1,'inode':2},reader_pid=1,sample_start_ns=1,sample_end_ns=2)
 def test_missing_malformed_overflow_and_boolean_contract_fields(self):
  for key,value in (('early_cpu_usec',True),('early_wall_ns',-1),('admission_ns',2**64-1),('term_grace_ns',None)):
   rows,c=fixture();c[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):p.review_trace(rows,c)
  for f in (lambda c:c['observer'].update(uid=1000),lambda c:c['observer'].update(uid=1001),lambda c:c['observer'].update(pid=4),lambda c:c['role_registry']['collector'].update(uid=1000),lambda c:c['role_registry']['worker'].update(uid=0),lambda c:c.update(memory_event_scope='UNKNOWN'),lambda c:c['phase_budget_ns'].update(WORKER=13000000001)):
   rows,c=fixture();f(c)
   with self.assertRaises(ValueError):p.review_trace(rows,c)
 def test_cumulative_pool_not_each_process_budget(self):
  rows,c=fixture();rows[-1]['raw']['cpu.stat']='usage_usec 5000000\nuser_usec 5000000\nsystem_usec 0\n'
  with self.assertRaisesRegex(ValueError,'AGGREGATE_CPU'):p.review_trace(rows,c)
 def test_checked_arithmetic(self):
  self.assertEqual(p.checked_mul(14400,1000000000),14400000000000)
  for f in (lambda:p.checked_add(2**64-1,1),lambda:p.checked_mul(2**63,2),lambda:p.checked_add(True),lambda:p.checked_add(-1)):
   with self.assertRaises(ValueError):f()
 def test_stop_term_kill_and_observer_are_requests_only(self):
  _,c=fixture();args=dict(cpu_usec=3000000,elapsed_ns=1,stop_elapsed_ns=0,c=c)
  a=p.stop_decision('RUNNING','POLL',**args);self.assertEqual(a['state'],'TERM_REQUESTED');self.assertFalse(a['accept'])
  args.update(stop_elapsed_ns=500000000,elapsed_ns=1000000000)
  self.assertEqual(p.stop_decision('TERM_REQUESTED','POLL',**args)['state'],'KILL_REQUESTED')
  self.assertEqual(p.stop_decision('KILL_REQUESTED','WORKER_DOMAIN_EXITED',**args)['state'],'DRAINING_COLLECTOR')
  self.assertEqual(p.stop_decision('DRAINING_COLLECTOR','COLLECTOR_EXITED',**args)['state'],'WAIT_OBSERVER')
  self.assertFalse(p.stop_decision('WAIT_OBSERVER','FINAL_ACCEPTED',**args)['accept'])
  with self.assertRaisesRegex(ValueError,'CLOCK_CONTRADICTION'):p.stop_decision('TERM_REQUESTED','POLL',cpu_usec=0,elapsed_ns=1,stop_elapsed_ns=2,c=c)
 def test_timeout_controller_collector_observer_loss_are_fail_closed(self):
  _,c=fixture()
  for event in set(p.FAILURES)-{'COLLECTOR_LOSS'}:
   self.assertEqual(p.stop_decision('RUNNING',event,cpu_usec=0,elapsed_ns=1,stop_elapsed_ns=0,c=c)['state'],'TERM_REQUESTED')
  for event,cpu,wall in (('OBSERVER_LOST',0,1),('COLLECTOR_LOSS',0,1),('POLL',4000001,1),('POLL',0,13000000001)):
   self.assertEqual(p.stop_decision('WAIT_OBSERVER',event,cpu_usec=cpu,elapsed_ns=wall,stop_elapsed_ns=0,c=c)['state'],'UNKNOWN')
 def test_unknown_does_not_automatically_retry(self):
  _,c=fixture();r=p.stop_decision('UNKNOWN','POLL',cpu_usec=0,elapsed_ns=0,stop_elapsed_ns=0,c=c)
  self.assertEqual(r['action'],'PRESERVE_COMMITTED_ONLY');self.assertFalse(r['accept'])
 def test_tmpfs_resident_plan_requires_nonzero_runtime_and_reserves(self):
  x={'work_resident':8*2**20,'private_resident':2**20,'process_runtime':256*2**20,'collector':64*2**20,'kernel_and_cache':64*2**20,'safety_reserve':64*2**20}
  r=p.memory_plan('S4',x,fresh_private_tmpfs=True,ancestor_exclusivity_verified=True);self.assertFalse(r['actual_memory_enforcement_verified'])
  for key,value in (('process_runtime',0),('collector',None),('kernel_and_cache',True),('safety_reserve',0)):
   bad=dict(x);bad[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):p.memory_plan('S4',bad,fresh_private_tmpfs=True,ancestor_exclusivity_verified=True)
 def test_BUILD_tmpfs_full_ceiling_fails_even_before_runtime(self):
  x={'work_resident':2**31,'private_resident':2**28,'process_runtime':1,'collector':1,'kernel_and_cache':1,'safety_reserve':1}
  with self.assertRaisesRegex(ValueError,'EXCEEDS_POOL'):p.memory_plan('BUILD',x,fresh_private_tmpfs=True,ancestor_exclusivity_verified=True)
  with self.assertRaisesRegex(ValueError,'PRECHARGED'):p.memory_plan('BUILD',x,fresh_private_tmpfs=False,ancestor_exclusivity_verified=True)
 def test_nonatomic_memory_current_can_exceed_earlier_peak(self):
  rows,c=fixture();rows[-1]['raw']['memory.current']='200\n';p.review_trace(rows,c)

if __name__=='__main__':unittest.main()
