"""Native OS fixtures are CI-only; pure/mock positives never claim ext4 acceptance."""
import ast,contextlib,copy,errno,json,os,re,stat,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from . import manager_dependency_contract as c,manager_native_contract as nc,manager_native_evidence as capture,manager_dependency_validate as validator,manager_capsule_v2 as capsule,manager_scope_fs as fs
from .manager_dependency_tests import fixture_approval,file_fixture
ROOT=Path(__file__).parent
def posix_flags():
 stack=contextlib.ExitStack()
 for name,value in (('O_NOFOLLOW',0x20000),('O_CLOEXEC',0x80000),('O_NONBLOCK',0x800)):
  if not hasattr(os,name):stack.enter_context(patch.object(os,name,value,create=True))
 return stack
def evidence_fixture():
 scope,sr,rr,now=fixture_approval();ancestor={'identity':{'st_uid':0,'st_mode':stat.S_IFDIR|0o755},'type':'DIRECTORY'};key=c.sha(c.canonical(ancestor));node=file_fixture('/usr/bin/systemctl');node['sha256']=nc.SYSTEMCTL;node.pop('ancestor_instances');node['ancestor_instance_refs']=[key]
 filesystem={'classification':'LINUX_NATIVE_FILESYSTEM_CONFIRMED','fs_type':'ext4','fs_magic':0xef53,'mount_id':4,'device':1,'mount_namespace_inode':5};proof={'filesystem':filesystem,'posix_acl':'ABSENT_CONFIRMED_BY_FD_XATTR','host_admin_excluded':False,'mode':0o700,'directory_identity':{'st_uid':1000}}
 v={'schema':c.SCHEMA,'evidence_origin':'SYNTHETIC_TEST_FIXTURE','source_revision':scope['source_revision'],'source_closure_sha256':scope['source_closure_sha256'],'scope_sha256':c.sha(sr),'approval_record_sha256':c.sha(rr),'uid':1000,'gid':1000,'automatic_retry':False,'manager_queries':0,'other_children':0,'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False,'started_monotonic_ns':1,'finished_monotonic_ns':2,'files':[node],'ancestor_table':{key:ancestor},'unavailable_files':[{'path':r['path'],'reason':'MISSING'} for r in scope['files'] if r['path']!=node['requested']],'native_parent':{'host_attestation':False,'actual_private_source_staged':False,'actual_private_scope_staged':False,'proof':proof},'output_store':proof,'static_graph':{'status':'OBSERVED_BOUNDED_ELF_NODES_NOT_LOADER_RESOLUTION','COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False,'edges_reviewed':False,'parsed_nodes':{}},'python':{'schema':'PYTHON_RUNTIME_IMPORT_EVIDENCE_V1','version':[3,12,3],'isolated':True,'no_site':True,'no_bytecode_write':True,'modules':[],'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False,'sys_path':['/usr/lib/python3.12']},'session':{'created_session':False,'mount_namespace_inode':5},'bus_metadata':[{'path':p,'status':'UNKNOWN_MISSING_SOCKET','connected':False} for p in scope['socket_metadata_only']],'mapping':{'status':'UNKNOWN_UNLISTED_OR_UNBOUND_CURRENT_MAPPING','lifetime_coverage':False,'future_child_identity_bound':False}}
 return scope,sr,rr,now,v
def checked_fixture(v=None,**kwargs):
 scope,sr,rr,now,default=evidence_fixture();v=default if v is None else v;raw=c.canonical(v);return validator.review(raw,c.sha(raw),sr,c.sha(sr),rr,c.sha(rr),scope['source_closure_sha256'],now=now,allow_fixture=True,**kwargs)
class IndependentEvidenceTests(unittest.TestCase):
 def test_complete_fixture_is_explicitly_not_guest_observation(self):self.assertEqual(checked_fixture()['status'],'PASS_TEST_FIXTURE_ONLY')
 def test_fixture_rejected_by_actual_validation_mode(self):
  s,sr,rr,now,v=evidence_fixture();raw=c.canonical(v);self.assertEqual(validator.review(raw,c.sha(raw),sr,c.sha(sr),rr,c.sha(rr),s['source_closure_sha256'],now=now)['status'],'FAIL_NATIVE_EVIDENCE_BINDING')
 def test_source_scope_uid_and_approval_changes_rejected(self):
  for key,value in (('source_revision','2'*40),('scope_sha256','a'*64),('uid',0),('approval_record_sha256','a'*64),('manager_queries',1),('COMPLETE_DYNAMIC_RESOLUTION_ATTESTED',True)):
   *_,v=evidence_fixture();v[key]=value
   with self.subTest(key=key):self.assertEqual(checked_fixture(v)['status'],'FAIL_NATIVE_EVIDENCE_BINDING')
 def test_duplicate_and_missing_file_coverage_rejected(self):
  for change in ('duplicate','missing','unknown'):
   *_,v=evidence_fixture()
   if change=='duplicate':v['files'].append(copy.deepcopy(v['files'][0]))
   elif change=='missing':v['unavailable_files'].pop()
   else:v['unavailable_files'][0]['reason']='IGNORED'
   with self.subTest(change=change):self.assertEqual(checked_fixture(v)['status'],'FAIL_NATIVE_EVIDENCE_BINDING')
 def test_stage_independent_positive_and_mode_link_count_negatives(self):
  scope,sr,rr,now=fixture_approval('NATIVE_STAGE_ONCE');proof=evidence_fixture()[-1]['output_store'];rows=[]
  for i,name in enumerate(sorted(c.CLOSURE)):
   s=file_fixture()['identity'];s.update(st_uid=1000,st_mode=stat.S_IFREG|0o400,st_ino=i+10);rows.append({'name':name,'sha256':scope['source_closure_sha256'][name],'identity':s})
  value={'schema':'HH_G2_NATIVE_FINITE_STAGE_RECEIPT_V1','evidence_origin':'SYNTHETIC_TEST_FIXTURE','source_revision':scope['source_revision'],'source_closure_sha256':scope['source_closure_sha256'],'scope_sha256':c.sha(sr),'approval_record_sha256':c.sha(rr),'source_files':13,'source_bytes':13*8,'source_mode':0o400,'scope_mode':0o600,'manager_queries':0,'automatic_retry':False,'host_attestation':False,'store':proof,'source_instances':rows,'pending_scope_A_sha256':c.sha(c.canonical(nc.pending(scope['source_revision'],scope['source_closure_sha256'],'NATIVE_READ_ONLY_ONCE')))}
  def verify(v):
   raw=c.canonical(v);return validator.stage_review(raw,c.sha(raw),sr,c.sha(sr),rr,c.sha(rr),allow_fixture=True,now=now)
  self.assertEqual(verify(value)['status'],'PASS_TEST_FIXTURE_ONLY')
  for field,x in (('st_nlink',2),('st_mode',stat.S_IFREG|0o600),('st_uid',0)):
   bad=copy.deepcopy(value);bad['source_instances'][0]['identity'][field]=x
   with self.subTest(field=field),self.assertRaises(ValueError):verify(bad)
 def test_ancestor_table_replacement_and_acl_rejected(self):
  for change in ('acl','ancestor','mode','namespace'):
   *_,v=evidence_fixture()
   if change=='acl':v['output_store']['posix_acl']='UNKNOWN'
   elif change=='ancestor':v['ancestor_table'][next(iter(v['ancestor_table']))]['identity']['st_uid']=1000
   elif change=='mode':v['output_store']['mode']=0o755
   else:v['session']['mount_namespace_inode']=6
   with self.subTest(change=change):self.assertEqual(checked_fixture(v)['status'],'FAIL_NATIVE_EVIDENCE_BINDING')
 def test_replay_clock_import_path_and_mapping_promotion_rejected(self):
  *_,v=evidence_fixture();raw=c.canonical(v);self.assertEqual(checked_fixture(v,seen=(c.sha(raw),))['status'],'FAIL_NATIVE_EVIDENCE_BINDING')
  for change in ('clock','path','mapping'):
   *_,v=evidence_fixture()
   if change=='clock':v['finished_monotonic_ns']=0
   elif change=='path':v['python']['sys_path']=['/mnt/c/project']
   else:v['mapping']['lifetime_coverage']=True
   with self.subTest(change=change):self.assertEqual(checked_fixture(v)['status'],'FAIL_NATIVE_EVIDENCE_BINDING')
class CapsuleAndSafetyTests(unittest.TestCase):
 def test_documented_pending_commands_compile_and_stop_without_file_reads(self):
  from . import manager_provider_docs as docs
  text=docs.command('1'*40,{n:'0'*64 for n in c.CLOSURE});chunks=re.findall(r"```bash\n/usr/bin/python3 -I -S -B - <<'PY'\n(.*?)\nPY\n```",text,re.S);self.assertEqual(len(chunks),2)
  for code in chunks:
   with patch.object(os,'open',side_effect=AssertionError('PENDING MUST NOT READ')),self.assertRaisesRegex(SystemExit,'STOP_PENDING_NEW_INDEPENDENT_APPROVAL'):exec(compile(code,'pending_reviewed_command','exec'),{})
 def test_new_safe_profile_fixed_sixteen_stages_and_no_live_worker_calls(self):
  from . import manager_provider_runner as runner
  self.assertEqual(len(runner.STAGES),16);tree=ast.parse(Path(runner.__file__).read_bytes());worker=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
  for node in ast.walk(worker):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):self.assertNotIn(node.func.attr,('collect','stage','launch','capture','execute'))
 def test_native_publication_rejects_private_receipts_and_approvals(self):
  from . import manager_provider_publication as pub
  for raw in (b'{"schema":"HH_G2_NATIVE_DEPENDENCY_EVIDENCE_V1"}',b'{"schema":"HH_G2_NATIVE_FINITE_STAGE_RECEIPT_V1"}',b'{"approval_text":"secret"}',b'{"boot_id":"private"}'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):pub.validate(pub.REPORTS+'FINAL_STATUS.json',raw)
 def fixture(self):
  raws={n:b'VALUE=1\n' for n in c.CLOSURE};return raws,{n:c.sha(b) for n,b in raws.items()}
 def test_v2_closure_does_not_rebind_v1(self):
  from . import manager_scope_contract as old
  self.assertEqual(len(old.CLOSURE),10);self.assertEqual(len(c.CLOSURE),13);self.assertEqual(c.CLOSURE,capsule.NAMES);self.assertNotEqual(c.CAPSULE_SCHEMA,old.PROFILE)
 def test_compile_exact_reviewed_memory_and_no_extra_fallback(self):
  raws,hashes=self.fixture()
  with capsule.Capsule(raws,hashes):
   module=__import__(capsule.PACKAGE+'.manager_elf',fromlist=['VALUE']);self.assertEqual(module.VALUE,1)
   with self.assertRaises(ValueError):__import__(capsule.PACKAGE+'.evil',fromlist=['x'])
 def test_capsule_missing_hash_drift_and_preloaded_substitution(self):
  raws,hashes=self.fixture();bad=dict(raws);bad['manager_elf.py']=b'VALUE=2\n'
  with self.assertRaises(ValueError):capsule.Capsule(bad,hashes)
  bad=dict(raws);bad.pop('manager_elf.py')
  with self.assertRaises(ValueError):capsule.Capsule(bad,hashes)
  with patch.dict(sys.modules,{capsule.PACKAGE:types.ModuleType(capsule.PACKAGE)}),self.assertRaises(ValueError):
   with capsule.Capsule(raws,hashes):pass
 def test_unapproved_bootstrap_stops_before_any_source_or_guest_read(self):
  with patch.object(os,'open',side_effect=AssertionError('NO READ')),self.assertRaisesRegex(ValueError,'STOP_PENDING'):capsule.launch('/untrusted',b'{}',b'{}',None,None)
 def test_collector_and_stager_missing_approval_stop_before_metadata(self):
  with patch.object(capture,'interpreter',side_effect=AssertionError('NO RUNTIME READ')):
   for action in (capture.collect,capture.stage,capture.execute):
    with self.subTest(action=action.__name__),self.assertRaises(ValueError):action(b'{}',b'{}','a'*64,'b'*64,{})
 def test_fixed_scope_cannot_expand_io_or_authorize_manager(self):
  s=nc.pending('1'*40,{n:'0'*64 for n in c.CLOSURE},'NATIVE_STAGE_ONCE');nc.check(s);self.assertFalse(s['manager_authorized']);self.assertEqual(s['systemctl_children'],0)
  for key,value in (('parent','/etc'),('uid',0),('manager_authorized',True),('limits',{})):
   changed=copy.deepcopy(s);changed[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):nc.check(changed)
 def test_no_target_subprocess_or_network_or_host_configuration_code(self):
  for name in c.RUNTIME:
   raw=(ROOT/name).read_bytes();tree=ast.parse(raw)
   for node in ast.walk(tree):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):self.assertNotIn(node.func.attr,('Popen','run','system','execv','execve','connect','mount','chmod','chown'))
   self.assertNotIn(b'os.system(',raw);self.assertNotIn(b'subprocess',raw)
 def test_source_input_replaced_after_hash_is_rejected(self):
  a=types.SimpleNamespace(st_mode=stat.S_IFREG|0o400,st_nlink=1,st_size=8,st_dev=1,st_ino=1,st_mtime_ns=1,st_ctime_ns=1);b=copy.copy(a);b.st_ino=2
  with posix_flags(),patch.object(os,'open',return_value=9),patch.object(os,'fstat',side_effect=[a,b]),patch.object(os,'read',side_effect=[b'VALUE=1\n',b'']),self.assertRaises(ValueError):capsule.read_source('/inert',c.sha(b'VALUE=1\n'),[])
class StoreEdgeTests(unittest.TestCase):
 def test_initial_parent_observation_never_follows_symlink_ancestor(self):
  directory=types.SimpleNamespace(st_mode=stat.S_IFDIR|0o755,st_uid=0)
  with posix_flags(),patch.object(os,'O_DIRECTORY',0x10000,create=True),patch.object(os,'open',side_effect=[1,2,OSError(errno.ELOOP,'inert symlink')]) as opened,patch.object(os,'fstat',return_value=directory),patch.object(os,'close') as closed,patch.object(fs,'no_acl'),patch.object(fs,'fs_identity',side_effect=AssertionError('MUST NOT OBSERVE TARGET')),self.assertRaises(OSError):capture.observed_store('/home/btu/private',True)
  self.assertEqual([call.args[0] for call in opened.call_args_list],['/','home','btu']);self.assertEqual(opened.call_args_list[1].kwargs['dir_fd'],1);self.assertEqual(opened.call_args_list[2].kwargs['dir_fd'],2);self.assertEqual(closed.call_count,2)
 def test_acl_absent_empty_unsupported_default_and_permission(self):
  with patch.object(os,'getxattr',create=True,side_effect=OSError(errno.ENODATA,'absent')):fs.no_acl(1,True)
  with patch.object(os,'getxattr',create=True,return_value=b''):fs.no_acl(1,True)
  for result in (OSError(errno.ENOTSUP,'unsupported'),OSError(errno.EACCES,'denied'),b'extended'):
   with self.subTest(result=str(result)),patch.object(os,'getxattr',create=True,**({'side_effect':result} if isinstance(result,OSError) else {'return_value':result})),self.assertRaises(ValueError):fs.no_acl(1,True)
 def fake(self):
  store=object.__new__(fs.Store);store.fd=1;store.policy={'uid':1000};store.verify=lambda:True;store.pin=lambda *a:types.SimpleNamespace(raw=b'abc');s=types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=1000,st_nlink=1,st_size=0);return store,s
 def test_zero_write_is_failure_and_preserves_partial_file(self):
  store,s=self.fake()
  with posix_flags(),patch.object(os,'open',return_value=9),patch.object(os,'fstat',return_value=s),patch.object(fs,'no_acl'),patch.object(os,'write',return_value=0),patch.object(os,'close') as close,self.assertRaisesRegex(ValueError,'WRITE_NO_PROGRESS'):store.write_new('inert.json',b'abc')
  close.assert_called_once_with(9)
 def test_partial_write_progress_and_fsync(self):
  store,s=self.fake();seen=[]
  def write(fd,view):seen.append(bytes(view));return 1
  with posix_flags(),patch.object(os,'open',return_value=9),patch.object(os,'fstat',return_value=s),patch.object(fs,'no_acl'),patch.object(os,'write',side_effect=write),patch.object(os,'close'),patch.object(os,'fsync') as sync:store.write_new('inert.json',b'abc')
  self.assertEqual(seen,[b'abc',b'bc',b'c']);self.assertEqual(sync.call_count,2)
 def test_interrupted_write_does_not_retry_or_unlink(self):
  store,s=self.fake()
  with posix_flags(),patch.object(os,'open',return_value=9),patch.object(os,'fstat',return_value=s),patch.object(fs,'no_acl'),patch.object(os,'write',side_effect=InterruptedError()) as write,patch.object(os,'close'),self.assertRaises(InterruptedError):store.write_new('inert.json',b'abc')
  self.assertEqual(write.call_count,1)
 def test_same_fd_bytes_change_after_first_read(self):
  s=types.SimpleNamespace(st_dev=1,st_ino=1,st_uid=1000,st_gid=1000,st_mode=stat.S_IFREG|0o600,st_nlink=1,st_size=3,st_mtime_ns=1,st_ctime_ns=1);store=types.SimpleNamespace(fd=1,verify=lambda:True);pin=fs.Pinned(store,'scope',9,b'old',s)
  with posix_flags(),patch.object(os,'open',return_value=10),patch.object(os,'close'),patch.object(fs,'fs_identity',return_value={'mount_id':1}),patch.object(os,'fstat',return_value=s),patch.object(os,'stat',return_value=s),patch.object(fs,'no_acl'),patch.object(os,'lseek'),patch.object(fs,'bounded_fd',return_value=b'new'),self.assertRaisesRegex(ValueError,'SAME_FD'):pin.verify()
 def test_filesystem_and_mount_namespace_identity_cannot_be_substituted(self):
  expected={'classification':'LINUX_NATIVE_FILESYSTEM_CONFIRMED','fs_magic':0xef53,'mount_id':1,'device':1,'mount_namespace_inode':1,'fsid':'1'*16}
  for key in ('mount_id','mount_namespace_inode','fsid','device'):
   actual=dict(expected);actual[key]='2'*16 if key=='fsid' else 2
   with self.subTest(key=key),self.assertRaises(ValueError):fs.check_fs(actual,expected)
 def test_same_inode_lookup_on_different_mount_is_rejected(self):
  root=types.SimpleNamespace(st_dev=1,st_ino=1,st_uid=0,st_mode=stat.S_IFDIR|0o755);directory=types.SimpleNamespace(st_dev=1,st_ino=2,st_uid=1000,st_mode=stat.S_IFDIR|0o700);store=object.__new__(fs.Store);store.fd=2;store.chain=[(None,None,1,root),(1,'private',2,directory)];store.policy={'uid':1000};store.private=True
  with posix_flags(),patch.object(os,'O_DIRECTORY',0x10000,create=True),patch.object(os,'fstat',side_effect=lambda fd:root if fd==1 else directory),patch.object(os,'stat',return_value=directory),patch.object(fs,'no_acl'),patch.object(os,'open',return_value=3),patch.object(os,'close'),patch.object(fs,'fs_identity',side_effect=lambda fd:{'mount_id':2 if fd==3 else 1}),self.assertRaisesRegex(ValueError,'ANCESTOR_MOUNT_SUBSTITUTION'):store.verify()
@unittest.skipUnless(sys.platform=='linux' and os.environ.get('CI')=='true','CI_ELF_INPUT_ONLY_NOT_USER_GUEST_EVIDENCE')
class ExistingCiElfInput(unittest.TestCase):
 def test_root_owned_elf_read_without_execution(self):
  from . import manager_dependency_io as dio,manager_elf as elf
  pin=dio.AliasPin('/usr/bin/true',{})
  try:self.assertEqual(elf.parse(pin.raw)['format'],'ELF64_LE_X86_64');pin.verify();validator.file_proof(pin.proof(),{'path':'/usr/bin/true','sha256':None,'aliases':{}})
  finally:pin.close()
 def test_actual_reviewed_usrmerge_alias(self):
  from . import manager_dependency_io as dio
  pin=dio.AliasPin('/bin/true',{'/bin':'usr/bin'})
  try:self.assertEqual(pin.physical,'/usr/bin/true');validator.file_proof(pin.proof(),{'path':'/bin/true','sha256':None,'aliases':{'/bin':'usr/bin'}})
  finally:pin.close()
@unittest.skipUnless(sys.platform=='linux' and os.environ.get('CI')=='true','CI_ONLY_NATIVE_POSITIVE_FIXTURE; USER_WSL_REQUIRES_NEW_SCOPE_B')
class NativePositive(unittest.TestCase):
 def setUp(self):
  self.tmp=None;self.store=None;self.reasons=[]
  # Three fixed candidate parents. Never change ACLs/modes/mounts or use sudo.
  candidates=[str(Path.home()),os.environ.get('RUNNER_TEMP','/nonexistent'),'/mnt']
  for base in dict.fromkeys(candidates):
   try:
    fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:s=os.fstat(fd);proof=fs.fs_identity(fd)
    finally:os.close(fd)
    policy={'uid':os.getuid(),'filesystem':proof,'directory_identity':{k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')}};parent=fs.Store(base,policy,private=False);parent.close()
    self.tmp=tempfile.TemporaryDirectory(dir=base);root=Path(self.tmp.name);s=root.stat();policy['directory_identity']={k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')};self.store=fs.Store(str(root),policy);break
   except (OSError,ValueError) as exc:
    self.reasons.append(type(exc).__name__+':'+(str(exc) if isinstance(exc,ValueError) else 'OS_PERMISSION_OR_MISSING'))
    if self.tmp:self.tmp.cleanup();self.tmp=None
  if self.store is None:self.skipTest('BLOCKED_NO_QUALIFIED_CI_EXT4_PARENT: '+','.join(self.reasons))
 def tearDown(self):
  if self.store:self.store.close()
  if self.tmp:self.tmp.cleanup()
 def test_valid_ext4_store_scope_same_fd_and_exclusive_output(self):
  self.assertEqual(self.store.proof()['filesystem']['classification'],'LINUX_NATIVE_FILESYSTEM_CONFIRMED');pin=self.store.write_new('scope.json',b'{"inert":true}');pin.verify();pin.close()
  with self.assertRaises(FileExistsError):self.store.write_new('scope.json',b'{}')
 def test_source_0400_exact_bytes_and_no_acl(self):
  p=self.store.write_new('source.py',b'VALUE=1\n',0o400);self.assertEqual(p.raw,b'VALUE=1\n');fs.no_acl(p.fd,False);p.verify();p.close()
 def test_replace_symlink_and_hardlink_rejected(self):
  root=Path(self.tmp.name);p=self.store.write_new('scope.json',b'old');os.rename(root/'scope.json',root/'old.json');os.symlink(root/'old.json',root/'scope.json')
  with self.assertRaises((ValueError,OSError)):p.verify()
  p.close();os.link(root/'old.json',root/'linked')
  with self.assertRaises(ValueError):self.store.pin('linked',c.sha(b'old'))
 def test_private_output_creation_replay_and_pre_post_identity(self):
  root=Path(self.tmp.name);s=root.stat();policy={'uid':os.getuid(),'filesystem':self.store.proof()['filesystem'],'directory_identity':{k:getattr(s,k) for k in ('st_dev','st_ino','st_uid')}};parent=fs.Store(str(root),policy,private=False)
  try:
   output=fs.create_private(parent,'output');p=output.write_new('receipt.json',b'{}');p.verify();p.close();output.close()
   with self.assertRaises(FileExistsError):fs.create_private(parent,'output')
  finally:parent.close()
