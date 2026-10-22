"""Synthetic receipts and inert owned children; no actual systemctl/proc capture."""
import base64,copy,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import diagnostic_contract as c,diagnostic_validate as v,diagnostic_capture as a
def fixture():
 scope={'schema':'HH_G2_DIAGNOSTIC_SCOPE_V1','source_revision':'c'*40,'tool_sha256':{p:'a'*64 for p in c.TOOLS},'source_sha256':{p:'b'*64 for p in c.SOURCE_NAMES},
  'uid':1000,'gid':1000,'argvs':c.argvs(1000),'environment':c.environment(1000),
  'output':'/home/btu/simulations/hh_final_closure/g2_effective_diagnostic_01','authorization_reference':'d'*64,
  'limits':{'child_seconds':5,'cleanup_seconds':1,'adapter_soft_seconds':30,'per_child_bytes':8192,'aggregate_bytes':32768,'receipt_bytes':131072,'max_levels':8},
  'systemd_source_family_review':'255_DIRECT_PRIVATE_NO_AUTOSTART_WITH_POISONED_FALLBACK'}
 fields={'cgroup.controllers':'cpu memory pids\n','cgroup.subtree_control':'cpu memory\n','cgroup.procs':'666\n','cgroup.type':'domain\n',
  'cgroup.events':'populated 1\nfrozen 0\n','cpu.max':'max 100000\n','memory.max':'max\n','memory.swap.max':'max\n','pids.max':'1000\n'}
 levels=[{'path':name,'device':1,'inode':n,'uid':0,'gid':0,'mode':493,'fields':{k:{'status':'OBSERVED','text':text} for k,text in fields.items()}} for n,name in enumerate(('synthetic','.'),1)]
 snap={'monotonic_ns':10,'boot_id':'00000000-0000-0000-0000-000000000001','uid':1000,'gid':1000,'pid':666,'start_ticks':1,'membership':'/synthetic','pid1_comm':'systemd','pid1_start_ticks':1,'levels':levels}
 snap['namespace_inodes']={'mnt':1,'cgroup':2,'pid':3}
 after=copy.deepcopy(snap);after['monotonic_ns']=50
 props={'ControlGroup':'/user.slice/user-1000.slice/user@1000.service','Delegate':'yes','CPUAccounting':'yes','MemoryAccounting':'yes',
  'MemoryMax':'infinity','MemorySwapMax':'infinity','CPUQuotaPerSecUSec':'infinity','TasksMax':'1000','ActiveState':'active','SubState':'running','InvocationID':'e'*32,'MainPID':'800','User':'1000'}
 queries=[]
 for i,argv in enumerate(scope['argvs']):
  output=b'Version=255.4\nSystemState=running\n' if i<2 else ''.join(k+'='+props[k]+'\n' for k in c.PROPS).encode()
  queries.append({'argv':argv,'environment_sha256':c.sha(c.canonical(scope['environment'])),'start_ns':11+i*10,'end_ns':12+i*10,'pid':700+i,'start_ticks':100+i,
   'exit_code':0,'exit_signal':None,'cleanup':'VERIFIED_GROUP_ABSENT','stop_reason':None,'stdout_b64':base64.b64encode(output).decode(),'stderr_b64':'','stdout_bytes':len(output),'stderr_bytes':0})
 return scope,{'schema':c.SCHEMA,'scope_sha256':c.sha(c.canonical(scope)),'source_sha256':scope['source_sha256'],'source_revision':scope['source_revision'],'tool_sha256':scope['tool_sha256'],
  'before':snap,'queries':queries,'after':after,'failure':None,'authorization_reference':scope['authorization_reference'],'start_ns':1,'end_ns':60,'autostart_fallback':False,'hard_resource_envelope':False}
def review(scope,receipt):
 raw=c.canonical(receipt);s=c.canonical(scope);return v.review(raw,c.sha(raw),s,c.sha(s),scope['authorization_reference'])
class ReceiptTests(unittest.TestCase):
 def test_complete_observation_never_future_delegation(self):
  s,r=fixture();x=review(s,r);self.assertEqual(x['observation_status'],'PASS_READ_ONLY_OBSERVED');self.assertEqual(x['status'],'UNKNOWN_DELEGATION');self.assertFalse(x['actual_job_enforcement']);self.assertEqual(x['observed_limits']['0:memory.swap.max'],'UNLIMITED')
 def test_original_bytes_and_scope_digests(self):
  s,r=fixture();raw=c.canonical(r);x=v.review(raw,'0'*64,c.canonical(s),c.sha(c.canonical(s)),s['authorization_reference']);self.assertEqual(x['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_input_bound_before_hash_or_capture(self):
  s,r=fixture()
  with patch.object(c,'sha',side_effect=AssertionError('HASH_BEFORE_BOUND')):self.assertEqual(v.review(b'x'*(c.RECEIPT_CAP+1),'unused',b'{}','unused','unused')['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
  with tempfile.TemporaryDirectory() as where:
   path=Path(where)/'scope.json';path.write_bytes(b'x'*(c.RECEIPT_CAP+1))
   with self.assertRaisesRegex(ValueError,'INPUT_BOUND'):a.bounded_bytes(path)
 def test_duplicate_and_canonical_numbers(self):
  for raw in (b'{"a":1,"a":2}',b'{"a":-0}',b'{"a":1.0}',b'{"a":-1}',b'{"a":18446744073709551616}',b'{"a":NaN}'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):c.load(raw)
 def test_pending_scope_cannot_acquire(self):
  s,_=fixture();s['tool_sha256']['/usr/bin/systemctl']=None
  with patch.object(a,'snapshot',side_effect=AssertionError('LIVE')),self.assertRaisesRegex(ValueError,'BLOCKED_TOOL_IDENTITY'):a.capture(s)
  s,_=fixture();s['authorization_reference']=None
  with patch.object(a,'snapshot',side_effect=AssertionError('LIVE')),self.assertRaisesRegex(ValueError,'BLOCKED_AUTHORIZATION'):a.capture(s)
 def test_identity_and_boolean_corruptions(self):
  changes=(lambda r:r['after'].__setitem__('boot_id','00000000-0000-0000-0000-000000000002'),lambda r:r['after'].__setitem__('uid',1001),lambda r:r['after']['levels'][0].__setitem__('inode',42),lambda r:r.__setitem__('autostart_fallback',0),lambda r:r['before'].__setitem__('pid',True),lambda r:r.__setitem__('source_revision','f'*40),lambda r:r['tool_sha256'].__setitem__('/usr/bin/timeout','f'*64))
  for change in changes:
   s,r=fixture();r=copy.deepcopy(r);change(r);self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_numeric_limit_strictness(self):
  for field,value in (('memory.max','-1'),('memory.swap.max','MAX'),('pids.max','01'),('cpu.max','max 0'),('cgroup.events','populated 1\npopulated 0'),('cgroup.procs','0')):
   s,r=fixture();r['before']['levels'][0]['fields'][field]['text']=value;self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_numeric_finite_limits(self):
  s,r=fixture();r['before']['levels'][0]['fields']['memory.swap.max']['text']='0';self.assertEqual(review(s,r)['observed_limits']['0:memory.swap.max'],0)
 def test_partial_user_manager_and_unknown_cleanup(self):
  s,r=fixture();r['queries'][1]={'argv':s['argvs'][1],'skipped':'NO_EXISTING_OWNED_SOCKET'};x=review(s,r);self.assertEqual(x['status'],'UNKNOWN_MANAGER_STATE');self.assertIsNone(x['user_manager'])
  s,r=fixture();r['queries'][0]['cleanup']='UNKNOWN';self.assertEqual(review(s,r)['status'],'UNKNOWN_MANAGER_STATE')
 def test_missing_field_and_delegation_not_silently_passed(self):
  s,r=fixture();r['before']['levels'][0]['fields']['cgroup.subtree_control']={'status':'UNKNOWN','errno':13};x=review(s,r);self.assertNotEqual(x['observation_status'],'PASS_READ_ONLY_OBSERVED');self.assertTrue(x['missing_fields'])
 def test_partial_capture_still_rejects_unbounded_or_foreign_query(self):
  s,r=fixture();r['after']=None;r['failure']='INERT_FAILURE';r['queries'][0]['argv'].append('start');self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_no_fallback_environment_and_fixed_argv(self):
  self.assertEqual(c.environment(1000)['DBUS_SESSION_BUS_ADDRESS'],'unix:path=/proc/self/fd/-1');self.assertNotIn('SYSTEMCTL_FORCE_BUS',c.environment(1000))
  s,_=fixture();s['argvs'][0].append('--host=remote')
  with self.assertRaisesRegex(ValueError,'FIXED_ARGV'):c.checked_scope(s)
 def test_duplicate_properties_and_output_size(self):
  s,r=fixture();data=b'Version=255\nVersion=255\nSystemState=running\n';r['queries'][0].update(stdout_b64=base64.b64encode(data).decode(),stdout_bytes=len(data));self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
  s,r=fixture();r['queries'][0]['stdout_bytes']+=1;self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_query_order_and_time(self):
  s,r=fixture();r['queries'].reverse();self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
  s,r=fixture();r['queries'][1]['start_ns']=1;self.assertEqual(review(s,r)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_manager_does_not_prove_service_or_accounting(self):
  s,r=fixture();r['queries']=r['queries'][:2];r['failure']='PARTIAL';self.assertEqual(review(s,r)['status'],'UNKNOWN_MANAGER_STATE')
 def test_os_gap_preserves_existing_controller(self):
  text=(Path(__file__).parent/'g2_protocol.py').read_text(encoding='utf-8');self.assertNotIn('diagnostic_capture',text)
 def test_systemd_finite_duration_and_boolean_limit(self):
  s,r=fixture();row=r['queries'][2];raw=base64.b64decode(row['stdout_b64']).replace(b'CPUQuotaPerSecUSec=infinity',b'CPUQuotaPerSecUSec=1s');row.update(stdout_b64=base64.b64encode(raw).decode(),stdout_bytes=len(raw));self.assertEqual(review(s,r)['status'],'UNKNOWN_DELEGATION')
  s,_=fixture();s['limits']['cleanup_seconds']=True
  with self.assertRaisesRegex(ValueError,'CANONICAL_U64'):c.checked_scope(s)
 @unittest.skipUnless(sys.platform=='linux','POSIX inert timeout only')
 def test_inert_child_timeout_and_group_cleanup(self):
  fd=os.open(sys.executable,os.O_RDONLY)
  try:row=a.child([sys.executable,'-I','-B','-c','import time;time.sleep(10)'],fd,{'PATH':'/usr/bin','LC_ALL':'C'})
  finally:os.close(fd)
  self.assertEqual(row['cleanup'],'VERIFIED_GROUP_ABSENT');self.assertEqual(row['stop_reason'],'TIMEOUT_OR_INHERITED_PIPE');self.assertIsNone(row['exit_code']);self.assertEqual(row['exit_signal'],9)
 @unittest.skipUnless(sys.platform=='linux','POSIX inert owned child only')
 def test_inert_child_actual_positive_and_output_stop(self):
  for code in ('print("inert")','import os;os.write(1,b"x"*9000)'):
   fd=os.open(sys.executable,os.O_RDONLY)
   try:row=a.child([sys.executable,'-I','-B','-c',code],fd,{'PATH':'/usr/bin','LC_ALL':'C'})
   finally:os.close(fd)
   self.assertEqual(row['cleanup'],'VERIFIED_GROUP_ABSENT');self.assertLessEqual(row['stdout_bytes']+row['stderr_bytes'],8192)
   if '9000' in code:self.assertEqual(row['stop_reason'],'OUTPUT_BOUND')
 def test_exclusive_private_write_fixture(self):
  if sys.platform!='linux':self.skipTest('dir_fd POSIX fixture only')
  with tempfile.TemporaryDirectory() as where:
   fd=os.open(where,os.O_RDONLY|os.O_DIRECTORY)
   try:
    a.write_private(fd,'receipt.json',b'{}');self.assertEqual(os.stat(Path(where)/'receipt.json').st_mode&0o777,0o600)
    with self.assertRaises(FileExistsError):a.write_private(fd,'receipt.json',b'other')
   finally:os.close(fd)
if __name__=='__main__':unittest.main()
