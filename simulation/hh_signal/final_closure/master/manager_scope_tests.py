"""Source/security fixtures only. No manager, cgroup, WSL, or physics dispatch."""
import ast,base64,copy,importlib,os,re,stat,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from . import manager_scope_fs as fs,manager_scope_contract as c,manager_scope_loader as loader,manager_scope_validate as validator,manager_scope_bootstrap as bootstrap
from . import diagnostic_contract as prior,tool_binding_review as history
from .diagnostic_tests import fixture as old_fixture
def fixture():
 """Entirely SYNTHETIC approval/storage/manager fixture, never a real authorization."""
 scope,value=old_fixture();scope['source_revision']='b'*40;scope['source_sha256']=dict(c.ORIGINAL_SHA);scope['tool_sha256']=dict(c.TOOLS);scope['authorization_reference']=None;scope['execution_authorized']=False
 hashes={n:c.ORIGINAL_SHA.get(n,'3'*64) for n in c.CLOSURE}
 filesystem={'classification':'LINUX_NATIVE_FILESYSTEM_CONFIRMED','fs_type':'ext4','fs_magic':0xef53,'fsid':'0123456789abcdef','mount_id':1,'device':2,'mount_root':'/','mount_namespace_inode':42}
 def store(path,ino):return {'path':path,'policy':{'uid':1000,'filesystem':dict(filesystem),'directory_identity':{'st_dev':2,'st_ino':ino,'st_uid':1000}}}
 m={'schema':'HH_G2_NATIVE_RUNTIME_MANIFEST_V1','source_revision':'b'*40,'uid':1000,'gid':1000,'python_version':[3,12,3],'source_closure_sha256':hashes,'scope_store':store('/home/btu/simulations/hh_final_closure/g2_manager_scope_private_01',11),'source_store':store('/home/btu/simulations/hh_final_closure/g2_manager_source_private_01',12),'output_parent_store':store('/home/btu/simulations/hh_final_closure',13),'dependencies':{'status':'EXTERNALLY_REVIEWED_FIXED_CLOSURE','files':[{'path':'/usr/bin/python3.12','sha256':c.TOOLS['/usr/bin/python3'],'kind':'ELF'}],'required_import_origins':{'os':'frozen'},'filesystem_scan':False,'host_attestation':False},'no_wsl_startup':True,'no_root_fallback':True}
 manifest_raw=c.canonical(m);scope=c.pending(scope,hashes,c.sha(manifest_raw))
 record={'provenance':'USER_PROVIDED_VERBATIM_APPROVAL_REPORTED','identity_attestation':False,'operation':'G2_MANAGER_DIAGNOSTIC_ONCE','maximum_attempts':1,'approval_text':'SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_AUTHORIZATION','pending_scope_canonical_sha256':c.sha(c.canonical(scope)),'runtime_manifest_sha256':c.sha(manifest_raw),'source_revision':'b'*40,'excluded_architecture_acceptance':True}
 record_raw=c.canonical(record);scope['authorization_reference']=c.sha(record_raw);scope_raw=c.canonical(scope)
 value.update(source_revision='b'*40,source_sha256=scope['source_sha256'],tool_sha256=scope['tool_sha256'],authorization_reference=c.sha(record_raw),scope_sha256=c.sha(c.canonical(scope)))
 def row(name,digest,size,ino,mode):return {'name':name,'sha256':digest,'identity':{'st_dev':2,'st_ino':ino,'st_uid':1000,'st_gid':1000,'st_mode':stat.S_IFREG|mode,'st_nlink':1,'st_size':size,'st_mtime_ns':1,'st_ctime_ns':1}}
 def storeproof(key):return {'filesystem':m[key]['policy']['filesystem'],'directory_identity':m[key]['policy']['directory_identity'],'mode':0o700,'posix_acl':'ABSENT_CONFIRMED_BY_FD_XATTR','ancestors_bound':3,'host_admin_excluded':False}
 proof={'scope_store':storeproof('scope_store'),'source_store':storeproof('source_store'),'inputs':[row('scope.json',c.sha(scope_raw),len(scope_raw),20,0o600),row('approval.json',c.sha(record_raw),len(record_raw),21,0o600),row('runtime_manifest.json',c.sha(manifest_raw),len(manifest_raw),22,0o600)],'source_files':[row(n,h,100,100+i,0o400) for i,(n,h) in enumerate(sorted(hashes.items()))]}
 receipt_raw=c.canonical(value)
 security={'schema':'HH_G2_MANAGER_SECURITY_RECEIPT_V1','source_revision':'b'*40,'source_closure_sha256':hashes,'scope_raw_sha256':c.sha(scope_raw),'approval_record_sha256':c.sha(record_raw),'runtime_manifest_sha256':c.sha(manifest_raw),'original_manager_receipt_sha256':c.sha(receipt_raw),'before_launch':proof,'after_capture':copy.deepcopy(proof),'dependencies':{'status':'FIXED_EXTERNAL_ALLOWLIST_MATCHED_WITH_LIMITS','file_count':1,'host_attestation':False,'automatic_dependency_discovery':False,'transitive_mapping_attested':False},'host_attestation':False,'actual_job_enforcement':False,'automatic_retry':False}
 return scope,value,record,m,security
def check_fixture(parts=None,seen=()):
 s,v,a,m,e=fixture() if parts is None else parts
 sr,vr,ar,mr=map(c.canonical,(s,v,a,m));e=copy.deepcopy(e);e['original_manager_receipt_sha256']=c.sha(vr);er=c.canonical(e)
 return validator.review(vr,c.sha(vr),sr,c.sha(sr),ar,c.sha(ar),mr,er,c.sha(er),seen)
class SecurityPolicyTests(unittest.TestCase):
 def test_fixed_argv_env_and_original_four_preserved(self):
  self.assertEqual(c.fixed_argvs(),prior.argvs(1000));self.assertEqual(c.fixed_env(),prior.environment(1000));self.assertEqual(c.LIMITS,history.LIMITS)
  for n,h in c.ORIGINAL_SHA.items():self.assertEqual(c.sha((Path(__file__).parent/n).read_bytes()),h)
 def test_windows_drvfs_unknown_and_ext4_classification(self):
  for magic,name,out in ((0xef53,'ext4','LINUX_NATIVE_FILESYSTEM_CONFIRMED'),(0x01021997,'9p','DRVFS_OR_WINDOWS_BACKED'),(0x01021994,'tmpfs','UNKNOWN_FILESYSTEM'),(0xef53,'9p','DRVFS_OR_WINDOWS_BACKED')):self.assertEqual(fs.classify(magic,name),out)
 def test_no_json_or_path_only_filesystem_pass(self):
  actual=fixture()[3]['scope_store']['policy']['filesystem']
  for wanted in ({},None,dict(actual,mount_id=True),dict(actual,fsid=None),dict(actual,classification='DRVFS_OR_WINDOWS_BACKED'),dict(actual,mount_id=100)):
   with self.subTest(wanted=wanted),self.assertRaises(ValueError):fs.check_fs(actual,wanted)
 def test_owner_modes_type_hardlink_and_size_rejected(self):
  base=dict(st_mode=stat.S_IFREG|0o600,st_uid=1000,st_nlink=1,st_size=1)
  fs.checked_stat(types.SimpleNamespace(**base),1000,mode=0o600)
  for k,v in (('st_mode',stat.S_IFREG|0o660),('st_mode',stat.S_IFLNK|0o600),('st_uid',0),('st_nlink',2),('st_size',131073)):
   d=dict(base);d[k]=v
   with self.subTest(key=k,value=v),self.assertRaises(ValueError):fs.checked_stat(types.SimpleNamespace(**d),1000,mode=0o600)
 def test_acl_extended_unknown_and_absent(self):
  with patch.object(fs.os,'getxattr',return_value=b'extended',create=True),self.assertRaisesRegex(ValueError,'ACL_REJECTED'):fs.no_acl(123,True)
  with patch.object(fs.os,'getxattr',side_effect=OSError(95,'unsupported'),create=True),self.assertRaisesRegex(ValueError,'UNKNOWN_POSIX_ACL'):fs.no_acl(123,False)
  with patch.object(fs.os,'getxattr',side_effect=OSError(61,'no data'),create=True):
   with patch.object(fs.errno,'ENODATA',61):fs.no_acl(123,True)
 def test_pending_bootstrap_never_touches_native_files(self):
  with patch.object(bootstrap.os,'open',side_effect=AssertionError('NO_NATIVE_READ')):
   with self.assertRaisesRegex(ValueError,'BLOCKED_PENDING_REVIEW'):bootstrap.launch(None,None,None,None,None,None)
 def test_consumed_approval_rejected_before_native(self):
  for consumed in c.CONSUMED:
   with patch.object(bootstrap.os,'open',side_effect=AssertionError('NO_NATIVE_READ')),self.assertRaisesRegex(ValueError,'CONSUMED_VERSION_APPROVAL'):bootstrap.launch('/unused','/unused','/unused','1'*64,'2'*64,consumed)
 def test_wrong_platform_interpreter_and_nonisolated_refused(self):
  with patch.object(bootstrap,'EXTERNAL_BOOTSTRAP_SHA256','1'*64,create=True),self.assertRaisesRegex(ValueError,'ISOLATED_REVIEWED_INTERPRETER'):bootstrap.launch('/unused','/unused','/unused','1'*64,'2'*64,'3'*64)
 def test_missing_cold_start_binding_stops_before_reads(self):
  with patch.object(bootstrap.os,'open',side_effect=AssertionError('NO_NATIVE_READ')),self.assertRaisesRegex(ValueError,'BLOCKED_COLD_START_BINDING'):bootstrap.launch('/unused','/unused','/unused','1'*64,'2'*64,'3'*64)
 def test_frozen_import_uses_verified_bytes_without_disk_reread(self):
  raws={n:b'VALUE=41\n' for n in c.CLOSURE}
  with bootstrap.Capsule(raws,'/synthetic-reviewed'):
   raws['diagnostic_tools.py']=b'VALUE=99\n';module=importlib.import_module(loader.PACKAGE+'.diagnostic_tools');self.assertEqual(module.VALUE,41)
   with self.assertRaisesRegex(ValueError,'CAPSULE_IMPORT_CLOSURE'):importlib.import_module(loader.PACKAGE+'.unreviewed')
 def test_preloaded_capsule_rejected(self):
  with patch.dict(sys.modules,{loader.PACKAGE:types.ModuleType(loader.PACKAGE)}),self.assertRaisesRegex(ValueError,'PRELOADED_CAPSULE_REJECTED'):
   with bootstrap.Capsule({n:b'x=1' for n in c.CLOSURE},'/synthetic'):pass
 def test_synthetic_full_observation_never_promotes_delegation_or_enforcement(self):
  r=check_fixture();self.assertEqual(r['status'],'PASS_EFFECTIVE_READ_ONLY_OBSERVATION');self.assertEqual(r['future_delegation'],'UNKNOWN_FUTURE_DELEGATION');self.assertFalse(r['actual_job_enforcement'])
 def test_storage_acl_mode_fs_source_or_fd_identity_change_rejected(self):
  for mutation in ('acl','mode','filesystem','source_hash','link','replace','missing'):
   p=list(fixture());e=p[4]
   if mutation=='acl':e['before_launch']['scope_store']['posix_acl']='UNKNOWN'
   elif mutation=='mode':e['before_launch']['scope_store']['mode']=0o755
   elif mutation=='filesystem':e['before_launch']['scope_store']['filesystem']=dict(e['before_launch']['scope_store']['filesystem'],classification='DRVFS_OR_WINDOWS_BACKED')
   elif mutation=='source_hash':e['before_launch']['source_files'][0]['sha256']='0'*64
   elif mutation=='link':e['before_launch']['inputs'][0]['identity']['st_nlink']=2
   elif mutation=='replace':e['after_capture']['inputs'][0]['identity']['st_ino']=999
   else:e.pop('before_launch')
   with self.subTest(mutation=mutation):self.assertEqual(check_fixture(tuple(p))['status'],'FAIL_SCOPE_SECURITY')
 def test_replay_and_version_authorization_reuse_rejected(self):
  p=fixture();vr=c.canonical(p[1]);self.assertEqual(check_fixture(p,seen=(c.sha(vr),))['status'],'FAIL_SCOPE_SECURITY')
  p=list(fixture());p[0]['authorization_reference']=next(iter(c.CONSUMED));self.assertEqual(check_fixture(tuple(p))['status'],'BLOCKED_AUTHORIZATION')
 def test_wrong_uid_gid_or_scope_command_rejected(self):
  for mutation in ('uid','gid','argv','env'):
   p=list(fixture())
   if mutation in ('uid','gid'):p[0][mutation]=0
   elif mutation=='argv':p[0]['argvs'][0].append('--all')
   else:p[0]['environment']['DBUS_SESSION_BUS_ADDRESS']='autolaunch:'
   with self.subTest(mutation=mutation):self.assertNotEqual(check_fixture(tuple(p))['status'],'PASS_EFFECTIVE_READ_ONLY_OBSERVATION')
 def test_missing_bus_inactive_or_nonexistent_user_manager(self):
  p=list(fixture());p[1]['queries'][1]={'argv':p[0]['argvs'][1],'skipped':'NO_EXISTING_OWNED_SOCKET'};self.assertEqual(check_fixture(tuple(p))['status'],'UNKNOWN_USER_MANAGER')
  for state in ('inactive','failed'):
   p=list(fixture());q=p[1]['queries'][2];raw=base64.b64decode(q['stdout_b64']).replace(b'ActiveState=active',('ActiveState='+state).encode());q['stdout_b64']=base64.b64encode(raw).decode();q['stdout_bytes']=len(raw)
   with self.subTest(state=state):self.assertEqual(check_fixture(tuple(p))['status'],'UNKNOWN_USER_MANAGER')
 def test_output_bound_timeout_stderr_cleanup_and_partial(self):
  for key,value in (('cleanup','UNKNOWN'),('stop_reason','TIMEOUT'),('exit_code',1)):
   p=list(fixture());p[1]['queries'][0][key]=value
   with self.subTest(key=key):self.assertEqual(check_fixture(tuple(p))['status'],'UNKNOWN_MANAGER_STATE')
  p=list(fixture());q=p[1]['queries'][0];q['stdout_b64']=base64.b64encode(b'x'*8193).decode();q['stdout_bytes']=8193;self.assertNotEqual(check_fixture(tuple(p))['status'],'PASS_EFFECTIVE_READ_ONLY_OBSERVATION')
 def test_wrong_invocation_invalid_properties_and_delegation_rejected(self):
  for old,new in ((b'Delegate=yes',b'Delegate=maybe'),(b'ActiveState=active',b'ActiveState=nonsense'),(b'User=1000',b'User=0')):
   p=list(fixture());q=p[1]['queries'][2];raw=base64.b64decode(q['stdout_b64']);self.assertIn(old,raw);raw=raw.replace(old,new);q['stdout_b64']=base64.b64encode(raw).decode();q['stdout_bytes']=len(raw);self.assertNotEqual(check_fixture(tuple(p))['status'],'PASS_EFFECTIVE_READ_ONLY_OBSERVATION')
 def test_duplicate_json_original_bytes_and_dependency_closure(self):
  with self.assertRaisesRegex(ValueError,'DUPLICATE_JSON_KEY'):c.load(b'{"x":1,"x":2}')
  p=list(fixture());p[4]['dependencies']['transitive_mapping_attested']=True;self.assertEqual(check_fixture(tuple(p))['status'],'BLOCKED_DEPENDENCY_CLOSURE')
 def test_source_has_no_privilege_or_software_dispatch(self):
  for name in c.ADDED:
   raw=(Path(__file__).parent/name).read_bytes();ast.parse(raw)
   self.assertNotIn(b'subprocess.Popen(',raw);self.assertNotIn(b'subprocess.run(',raw);self.assertNotIn(b'os.system(',raw);self.assertNotIn(b'os.chmod(',raw)
 def test_safe_dag_stage_table_never_dispatches_live_capture(self):
  from . import manager_scope_runner as runner
  self.assertEqual(len(runner.STAGES),13)
  tree=ast.parse(Path(runner.__file__).read_bytes())
  for node in tree.body:
   if isinstance(node,ast.FunctionDef) and re.fullmatch(r't[0-9]+',node.name):
    for call in ast.walk(node):
     if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute):self.assertNotIn(call.func.attr,('capture','launch','snapshot','Popen','probe'))
 def test_publication_rejects_raw_figures_approval_and_private_identity(self):
  from . import manager_scope_publication as pub
  for name,raw in ((pub.REPORTS+'FINAL_STATUS.json',b'{"schema":"HH_G2_MANAGER_SECURITY_RECEIPT_V1"}'),(pub.REPORTS+'FINAL_STATUS.json',b'{"approval_text":"raw"}'),(pub.REPORTS+'figure.png',b'bad'),(pub.REPORTS+'FINAL_STATUS.json',b'{"boot_id":"private"}')):
   with self.subTest(name=name),self.assertRaises(ValueError):pub.validate(name,raw)
 def test_dynamic_resolution_gate_cannot_be_bypassed_by_allowlist_status(self):
  from . import manager_scope_capture as capture
  code=Path(capture.__file__).read_text(encoding='utf-8')
  self.assertIn("dependencies['transitive_mapping_attested'] is True",code)
  self.assertIn('BLOCKED_DEPENDENCY_CLOSURE_DYNAMIC_RESOLUTION_NOT_VERIFIED',code)
@unittest.skipUnless(sys.platform=='linux','POSIX_FD_FIXTURE_ONLY_NOT_USER_WSL_EVIDENCE')
class NativeFileFixtures(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=Path.home());self.root=Path(self.tmp.name);self.store=None;fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
  try:proof=fs.fs_identity(fd);s=os.fstat(fd)
  finally:os.close(fd)
  if proof['classification']!='LINUX_NATIVE_FILESYSTEM_CONFIRMED':self.tmp.cleanup();self.skipTest('CI_FS_NOT_EXT4_NO_NATIVE_STORAGE_PASS')
  policy={'uid':os.getuid(),'filesystem':proof,'directory_identity':{k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')}}
  try:self.store=fs.Store(str(self.root),policy)
  except BaseException:self.tmp.cleanup();raise
 def tearDown(self):
  if self.store:self.store.close()
  self.tmp.cleanup()
 def test_private_creation_read_and_exclusive_overwrite(self):
  p=self.store.write_new('scope.json',b'{"inert":true}');self.assertEqual(p.raw,b'{"inert":true}');p.verify();p.close()
  with self.assertRaises(FileExistsError):self.store.write_new('scope.json',b'{}')
 def test_file_replacement_inplace_mutation_and_hardlink(self):
  p=self.store.write_new('scope.json',b'old');os.rename(self.root/'scope.json',self.root/'old.json');(self.root/'scope.json').write_bytes(b'new')
  with self.assertRaises(ValueError):p.verify()
  p.close();os.link(self.root/'old.json',self.root/'link.json')
  with self.assertRaises(ValueError):self.store.pin('link.json',fs.sha(b'old'))
 def test_symlink_unsafe_ancestor_and_directory_replacement(self):
  os.symlink('/etc/passwd',self.root/'link.json')
  with self.assertRaises(OSError):self.store.pin('link.json','0'*64)
  bad=self.root/'unsafe';bad.mkdir(mode=0o777);os.chmod(bad,0o777)
  policy=dict(self.store.policy,directory_identity={'st_dev':os.stat(bad).st_dev,'st_ino':os.stat(bad).st_ino,'st_uid':os.getuid()})
  with self.assertRaisesRegex(ValueError,'UNSAFE'):fs.Store(str(bad),policy)
 def test_inert_source_staging_readonly_exact_bytes(self):
  raws={n:b'VALUE=1\n' for n in c.CLOSURE};hashes={n:fs.sha(b) for n,b in raws.items()};v=loader.stage_sources(self.store,raws,hashes);self.assertEqual(v['files'],10)
  pins,data=loader.pin_sources(self.store,hashes)
  try:self.assertEqual(data,raws)
  finally:
   for p in pins:p.close()
