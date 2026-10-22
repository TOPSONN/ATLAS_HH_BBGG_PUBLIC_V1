"""User-statement binding, synthetic version/ELF and preserved diagnostic regression."""
import ast,base64,copy,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import tool_binding_review as r,tool_binding_version_probe as probe,tool_binding_elf as elf,diagnostic_contract as c,diagnostic_validate as independent
from .diagnostic_tests import fixture as old_fixture,review as old_review
def version_fixture():
 out=b'systemd 255 (255.4-1ubuntu8)\n+PAM +AUDIT\n'
 return {'argv':['/usr/bin/systemctl','--version'],'environment_sha256':c.sha(c.canonical(c.environment(1000))),
  'stdout_b64':base64.b64encode(out).decode(),'stderr_b64':'','stdout_bytes':len(out),'stderr_bytes':0,'start_ns':1,'end_ns':2,'pid':123,'start_ticks':1,'cleanup':'VERIFIED_GROUP_ABSENT','stop_reason':None,'exit_code':0,'exit_signal':None}
def elf_fixture():
 raw=bytearray(256);raw[:16]=b'\x7fELF\x02\x01\x01'+b'\0'*9
 struct.pack_into('<HHIQQQIHHHHHH',raw,16,3,62,1,0,64,0,0,64,56,2,0,0,0)
 struct.pack_into('<IIQQQQQQ',raw,64,1,5,0,0,0,256,256,4096)
 text=b'/lib64/ld-linux-x86-64.so.2\0';struct.pack_into('<IIQQQQQQ',raw,120,3,4,200,0,0,len(text),len(text),1);raw[200:200+len(text)]=text
 return bytes(raw)
def version_receipt_fixture():
 scope=probe.pending('a'*40,{name:'b'*64 for name in probe.EXTRA});scope['authorization_reference']='d'*64 # SYNTHETIC ONLY, not human approval.
 value={'schema':'HH_G2_VERSION_ONLY_RECEIPT_V1','source_revision':scope['source_revision'],'scope_sha256':c.sha(c.canonical(scope)),
  'source_sha256':scope['source_sha256'],'tool_sha256':dict(r.TOOLS),'authorization_reference':scope['authorization_reference'],
  'uid':1000,'gid':1000,'python_version':[3,12,3],'start_ns':0,'end_ns':3,'query':version_fixture(),'bus_queries':0,'complete_diagnostic_executed':False,'dependency_closure_verified':False}
 return scope,value
class BindingTests(unittest.TestCase):
 def test_actual_user_report_is_observed_not_verified(self):
  raw=c.canonical(r.observation());v=r.binding_report(raw,c.sha(raw),'a'*40);self.assertTrue(v['TOOL_IDENTITY_OBSERVED']);self.assertFalse(v['TOOL_IDENTITY_VERIFIED']);self.assertFalse(v['INSTALLED_SYSTEMD_VERSION_VERIFIED'])
 def test_exact_original_four_sources_preserved(self):
  for name,h in r.SOURCES.items():self.assertEqual(c.sha((Path(__file__).parent/name).read_bytes()),h)
 def test_observation_digest_or_identity_change_rejected(self):
  raw=c.canonical(r.observation())
  with self.assertRaisesRegex(ValueError,'OBSERVATION_BYTE_BINDING'):r.check_observation(raw,'0'*64)
  for key,value in (('uid',0),('gid',1001),('python_version',[3,12,4]),('tool_identity_attested',True),('execution_authorized',True)):
   v=r.observation();v[key]=value;raw=c.canonical(v)
   with self.subTest(key=key),self.assertRaises(ValueError):r.check_observation(raw,c.sha(raw))
 def test_duplicate_keys_and_replay_rejected(self):
  raw=b'{"uid":1000,"uid":1000}'
  with self.assertRaisesRegex(ValueError,'DUPLICATE_JSON_KEY'):r.check_observation(raw,c.sha(raw))
  raw=c.canonical(r.observation());h=c.sha(raw)
  with self.assertRaisesRegex(ValueError,'OBSERVATION_REPLAY'):r.binding_report(raw,h,'a'*40,seen=(h,))
 def test_pending_scope_contract_fixed_argv_and_all_limits(self):
  s=r.pending_scope('a'*40);v=r.scope_review(s);self.assertTrue(v['tool_values_bound']);self.assertFalse(v['full_diagnostic_ready']);self.assertIsNone(s['authorization_reference']);self.assertEqual(s['argvs'],c.argvs(1000));self.assertEqual(s['limits'],r.LIMITS)
 def test_pending_scope_cannot_create_authority_or_relax_limits(self):
  for invalid in ([],None,'scope'):
   with self.assertRaisesRegex(ValueError,'SCOPE_SCHEMA'):r.scope_review(invalid)
   with self.assertRaisesRegex(ValueError,'VERSION_SCOPE'):probe.check(invalid)
  for key,value in (('execution_authorized',True),('authorization_reference','d'*64),('gid',False)):
   s=r.pending_scope('a'*40);s[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):r.scope_review(s)
  s=r.pending_scope('a'*40);s['limits']['child_seconds']=6
  with self.assertRaises(ValueError):r.scope_review(s)
 def test_version_query_without_authority_never_reads_live_tool(self):
  s=probe.pending('a'*40,{name:'b'*64 for name in probe.EXTRA})
  with patch.object(probe.tools,'identity',side_effect=AssertionError('LIVE_READ')),self.assertRaisesRegex(ValueError,'BLOCKED_AUTHORIZATION'):probe.run(s)
 def test_version_positive_is_only_client_self_report(self):
  v=r.version_result(version_fixture());self.assertTrue(v['verified']);self.assertFalse(v['manager_version_verified']);self.assertFalse(v['dependency_closure_verified'])
 def test_other_version_not_silently_accepted(self):
  row=version_fixture();out=b'systemd 256 (256.1)\n';row.update(stdout_b64=base64.b64encode(out).decode(),stdout_bytes=len(out));self.assertEqual(r.version_result(row)['status'],'BLOCKED_VERSION_FAMILY_MISMATCH')
 def test_version_partial_output_bound_timeout_cleanup(self):
  for key,value in (('cleanup','UNKNOWN'),('stop_reason','TIMEOUT_OR_INHERITED_PIPE'),('exit_code',1),('end_ns',6_000_000_002)):
   row=version_fixture();row[key]=value;self.assertFalse(r.version_result(row)['verified'])
  row=version_fixture();row['stdout_bytes']=8193
  with self.assertRaises(ValueError):r.version_result(row)
 def test_version_argv_and_boolean_exit_rejected(self):
  row=version_fixture();row['argv'].append('show')
  with self.assertRaisesRegex(ValueError,'FIXED_VERSION_ARGV'):r.version_result(row)
  row=version_fixture();row['exit_code']=False
  with self.assertRaisesRegex(ValueError,'CANONICAL_U64'):r.version_result(row)
 def test_elf_static_interpreter_is_not_dependency_closure(self):
  v=elf.inspect(elf_fixture());self.assertEqual(v['interpreter'],'/lib64/ld-linux-x86-64.so.2');self.assertFalse(v['transitive_dynamic_closure_verified']);self.assertIsNone(v['interpreter_binary_sha256'])
 def test_elf_header_truncation_architecture_and_segments_rejected(self):
  raw=elf_fixture()
  for value in (raw[:60],raw[:150],raw[:18]+b'\x03\0'+raw[20:],b'not ELF'+raw[7:]):
   with self.assertRaises(ValueError):elf.inspect(value)
 def test_original_independent_validator_partial_missing_bus(self):
  s,receipt=old_fixture();receipt['queries'][1]={'argv':s['argvs'][1],'skipped':'NO_EXISTING_OWNED_SOCKET'}
  v=old_review(s,receipt);self.assertEqual(v['status'],'UNKNOWN_MANAGER_STATE');self.assertFalse(v['actual_job_enforcement'])
 def test_original_validator_original_bytes_identity_and_limits(self):
  s,receipt=old_fixture();receipt['tool_sha256']=dict(r.TOOLS);s['tool_sha256']=dict(r.TOOLS);receipt['scope_sha256']=c.sha(c.canonical(s))
  self.assertEqual(old_review(s,receipt)['status'],'UNKNOWN_DELEGATION')
  receipt['after']['gid']=1001;self.assertEqual(old_review(s,receipt)['status'],'FAIL_SOURCE_OR_RECEIPT_MISMATCH')
 def test_publication_denies_raw_and_unapproved_payloads(self):
  from . import tool_binding_publication as p
  for name,raw in ((p.REPORTS+'G2_ACTUAL_TOOL_BINDING.json',b'{"schema":"HH_G2_VERSION_ONLY_RECEIPT_V1"}'),(p.REPORTS+'FINAL_STATUS.json',b'{"boot_id":"private"}'),(p.REPORTS+'figure.pdf',b'{}'),('private/receipt.json',b'{}')):
   with self.subTest(name=name),self.assertRaises(ValueError):p.validate(name,raw)
 def test_new_input_composite_and_source_binding(self):
  from . import tool_binding_runner as runner
  with tempfile.TemporaryDirectory() as where:
   path=Path(where)/'observation.json';raw=c.canonical(r.observation())+b'\n';path.write_bytes(raw)
   context={'scope_identity':'old','inputs_sha256':'f'*64}
   with patch.object(runner,'ORIGINAL_BINDING',return_value=context),patch.object(runner,'git',return_value=(r.BASE+'\n').encode()):value=runner.binding('unused',guest='unused',observation=path)
   self.assertNotEqual(value['inputs_sha256'],'f'*64);self.assertEqual(value['tool_observation']['sha256'],c.sha(raw));self.assertIn('tool_binding_version_probe.py',{Path(x['path']).name for x in value['source_rows']})
 def test_safe_stages_never_dispatch_version_or_diagnostic(self):
  from . import tool_binding_runner as runner
  tree=ast.parse(Path(runner.__file__).read_bytes())
  for node in tree.body:
   if isinstance(node,ast.FunctionDef) and node.name in ('t0','t1','t2','t3','t4','t5'):
    for call in ast.walk(node):
     if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute):self.assertNotIn(call.func.attr,('run','capture','snapshot','child','probe','Popen'))
 def test_independent_version_original_bytes_and_scope(self):
  s,v=version_receipt_fixture();raw=c.canonical(v);scope=c.canonical(s);result=r.review_version_receipt(raw,c.sha(raw),scope,c.sha(scope),s['authorization_reference']);self.assertTrue(result['original_bytes_bound']);self.assertFalse(result['TOOL_IDENTITY_VERIFIED'])
  with self.assertRaisesRegex(ValueError,'VERSION_ORIGINAL_BYTES'):r.review_version_receipt(raw,'0'*64,scope,c.sha(scope),s['authorization_reference'])
 def test_independent_version_replay_and_scope_escalation(self):
  s,v=version_receipt_fixture();raw=c.canonical(v);scope=c.canonical(s)
  with self.assertRaisesRegex(ValueError,'VERSION_RECEIPT_REPLAY'):r.review_version_receipt(raw,c.sha(raw),scope,c.sha(scope),s['authorization_reference'],seen=(c.sha(raw),))
  v['bus_queries']=1;raw=c.canonical(v)
  with self.assertRaisesRegex(ValueError,'VERSION_SCOPE_ESCALATION'):r.review_version_receipt(raw,c.sha(raw),scope,c.sha(scope),s['authorization_reference'])
 def test_independent_version_uid_and_observation_order(self):
  s,v=version_receipt_fixture();scope=c.canonical(s);v['gid']=1001;raw=c.canonical(v)
  with self.assertRaisesRegex(ValueError,'VERSION_RUNTIME_IDENTITY'):r.review_version_receipt(raw,c.sha(raw),scope,c.sha(scope),s['authorization_reference'])
  s,v=version_receipt_fixture();v['query']['end_ns']=4;raw=c.canonical(v)
  with self.assertRaisesRegex(ValueError,'VERSION_OBSERVATION_ORDER'):r.review_version_receipt(raw,c.sha(raw),c.canonical(s),c.sha(c.canonical(s)),s['authorization_reference'])
if __name__=='__main__':unittest.main()
