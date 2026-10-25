"""Synthetic ELF/import/evidence tests: no guest access or target execution."""
import copy,datetime,stat,struct,unittest
from . import manager_dependency_contract as c,manager_elf as elf,manager_dependency_provider as p,manager_dependency_validate as v,manager_native_contract as nc
def image(needed=(),soname=None,interp=None,rpath=None,runpath=None):
 raw=bytearray(2048);raw[:16]=b'\x7fELF\x02\x01\x01'+b'\0'*9;count=2+bool(interp);struct.pack_into('<HHIQQQIHHHHHH',raw,16,3,62,1,0,64,0,0,64,56,count,0,0,0)
 struct.pack_into('<IIQQQQQQ',raw,64,1,5,0,0x400000,0,len(raw),len(raw),4096)
 strings=bytearray(b'\0');tags=[]
 for tag,values in ((1,needed),(14,() if soname is None else (soname,)),(15,() if rpath is None else (rpath,)),(29,() if runpath is None else (runpath,))):
  for val in values:tags.append((tag,len(strings)));strings.extend(val.encode()+b'\0')
 tags += [(5,0x400000+1024),(10,len(strings)),(0,0)];size=len(tags)*16;struct.pack_into('<IIQQQQQQ',raw,120,2,6,512,0x400200,0,size,size,8)
 for i,row in enumerate(tags):struct.pack_into('<qQ',raw,512+i*16,*row)
 raw[1024:1024+len(strings)]=strings
 if interp:
  b=interp.encode()+b'\0';raw[256:256+len(b)]=b;struct.pack_into('<IIQQQQQQ',raw,176,3,4,256,0x400100,0,len(b),len(b),1)
 return bytes(raw)
def graph_fixture(cycle=False):
 blobs={'/usr/bin/demo':image(('liba.so',),interp='/lib64/ld.so'),'/usr/lib/ld.so':image(soname='ld.so'),'/usr/lib/liba.so':image(('libb.so',),soname='liba.so'),'/usr/lib/libb.so':image(('liba.so',) if cycle else (),soname='libb.so')}
 edges=[{'from':'/usr/bin/demo','needed':'liba.so','to':'/usr/lib/liba.so','provenance':'REVIEWED_EXACT_FILE_SET'},{'from':'/usr/lib/liba.so','needed':'libb.so','to':'/usr/lib/libb.so','provenance':'REVIEWED_EXACT_FILE_SET'}]
 if cycle:edges.append({'from':'/usr/lib/libb.so','needed':'liba.so','to':'/usr/lib/liba.so','provenance':'REVIEWED_EXACT_FILE_SET'})
 return blobs,['/usr/bin/demo'],edges,{'/lib64/ld.so':'/usr/lib/ld.so'}
def fixture_approval(operation='NATIVE_READ_ONLY_ONCE'):
 hashes={n:'0'*64 for n in c.CLOSURE};scope=nc.pending('1'*40,hashes,operation);now=datetime.datetime(2026,10,25,tzinfo=datetime.timezone.utc)
 record={'provenance':'SYNTHETIC_TEST_FIXTURE','operation':operation,'source_revision':scope['source_revision'],'maximum_attempts':1,'manager_authorized':False,'pending_scope_sha256':c.sha(c.canonical(scope)),'identity_attestation':False,'approval_text':'INERT TEST FIXTURE ONLY; NOT HUMAN AUTHORIZATION','expires_utc':'2026-10-25T01:00:00Z'}
 rr=c.canonical(record);scope['authorization_reference']=c.sha(rr);sr=c.canonical(scope);return scope,sr,rr,now
def file_fixture(path='/usr/lib/a.py'):
 ident={'st_dev':1,'st_ino':2,'st_uid':0,'st_gid':0,'st_mode':stat.S_IFREG|0o644,'st_nlink':1,'st_size':8,'st_mtime_ns':1,'st_ctime_ns':1,'device_major':0,'device_minor':1}
 return {'requested':path,'physical':path,'sha256':'a'*64,'identity':ident,'aliases':[],'ancestor_instances':[{'type':'DIRECTORY','identity':dict(ident,st_mode=stat.S_IFDIR|0o755)}],'acl':'ABSENT_BY_SAME_FD','mount_namespace_inode':5,'bytes_equality_rechecked':True}
class ElfTests(unittest.TestCase):
 def test_valid_elf64_all_fields(self):
  result=elf.parse(image(('a.so',),'b.so','/lib64/ld.so','/usr/lib','/usr/lib'));self.assertEqual(result['needed'],['a.so']);self.assertEqual(result['soname'],'b.so');self.assertEqual(result['interpreter'],'/lib64/ld.so');self.assertEqual(result['runpath'],'/usr/lib')
 def test_wrong_class_endian_architecture_and_version(self):
  for offset,val in ((4,1),(5,2),(6,0),(18,183)):
   raw=bytearray(image());raw[offset]=val
   with self.subTest(offset=offset),self.assertRaises(ValueError):elf.parse(bytes(raw))
 def test_truncated_file_and_program_headers(self):
  raw=image()
  for n in (0,32,63,100,520,1025):
   with self.subTest(n=n),self.assertRaises(ValueError):elf.parse(raw[:n])
 def test_program_header_overflow_rejected(self):
  raw=bytearray(image());struct.pack_into('<Q',raw,32,2**64-8)
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
 def test_malformed_dynamic_length(self):
  raw=bytearray(image());struct.pack_into('<Q',raw,120+32,17)
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
 def test_dynamic_segment_outside_load(self):
  raw=bytearray(image());struct.pack_into('<Q',raw,64+32,128)
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
 def test_missing_string_table(self):
  raw=bytearray(image(('a.so',)));struct.pack_into('<q',raw,528,30)
  with self.assertRaisesRegex(ValueError,'STRTAB'):elf.parse(bytes(raw))
 def test_needed_bad_offset_and_duplicate(self):
  raw=bytearray(image(('a.so',)));struct.pack_into('<Q',raw,520,99999)
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
  with self.assertRaises(ValueError):elf.parse(image(('a.so','a.so')))
 def test_unterminated_interp(self):
  raw=bytearray(image(interp='/lib/ld.so'));raw[266]=1
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
 def test_search_path_escape_empty_and_dynamic_token(self):
  for val in ('/usr/../etc',':/usr/lib','relative','$LIB','/usr/lib:'):
   with self.subTest(val=val),self.assertRaises(ValueError):elf.parse(image(rpath=val))
 def test_audit_plugins_not_silently_ignored(self):
  raw=bytearray(image());struct.pack_into('<q',raw,512,0x6ffffefc)
  with self.assertRaisesRegex(ValueError,'AUDIT_FILTER'):elf.parse(bytes(raw))
 def test_corrupt_section_and_alignment(self):
  raw=bytearray(image());struct.pack_into('<Q',raw,40,2000);struct.pack_into('<HHH',raw,58,64,2,0)
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
 def test_data_after_null_and_duplicate_tag(self):
  raw=bytearray(image(('a.so',)));struct.pack_into('<q',raw,544,5)
  with self.assertRaises(ValueError):elf.parse(bytes(raw))
class GraphTests(unittest.TestCase):
 def test_complete_transitive_graph_and_interpreter(self):
  args=graph_fixture();result=p.graph(*args);self.assertEqual(result['status'],'PASS_STATIC_ELF_GRAPH');self.assertEqual(len(result['edges']),3);self.assertFalse(result['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED']);self.assertEqual(v.static_recompute(args[0],result,*args[1:]),result)
 def test_cycles_terminate_without_dropping_edges(self):
  r=p.graph(*graph_fixture(True));self.assertEqual(len(r['edges']),4);self.assertTrue(r['cycle_nodes'])
 def test_missing_library_and_missing_interpreter(self):
  for remove in ('/usr/lib/libb.so','/usr/lib/ld.so'):
   args=list(graph_fixture());args[0].pop(remove)
   with self.subTest(remove=remove),self.assertRaises(ValueError):p.graph(*args)
 def test_duplicate_soname_rejected(self):
  args=list(graph_fixture());args[0]['/usr/lib/libother.so']=image(soname='libb.so')
  with self.assertRaisesRegex(ValueError,'SONAME'):p.graph(*args)
 def test_duplicate_edge_and_incorrect_soname(self):
  args=list(graph_fixture());args[2].append(dict(args[2][0]))
  with self.assertRaises(ValueError):p.graph(*args)
  args=list(graph_fixture());args[2][0]['to']='/usr/lib/libb.so'
  with self.assertRaises(ValueError):p.graph(*args)
 def test_unreviewed_search_resolution(self):
  args=list(graph_fixture());args[0]['/usr/bin/demo']=image(('liba.so',),interp='/lib64/ld.so',runpath='/other')
  with self.assertRaises(ValueError):p.graph(*args)
 def test_unknown_resolution_provenance(self):
  args=list(graph_fixture());args[2][0]['provenance']='LD_SO_CACHE_GUESSED'
  with self.assertRaises(ValueError):p.graph(*args)
 def test_reviewed_origin_runpath_is_exact_and_bounded(self):
  blobs={'/usr/lib/app':image(('liba.so',),runpath='$ORIGIN/lib'),'/usr/lib/lib/liba.so':image(soname='liba.so')};edges=[{'from':'/usr/lib/app','needed':'liba.so','to':'/usr/lib/lib/liba.so','provenance':'REVIEWED_RUNPATH'}];self.assertEqual(p.graph(blobs,['/usr/lib/app'],edges,{})['status'],'PASS_STATIC_ELF_GRAPH')
  with self.assertRaises(ValueError):elf.parse(image(runpath='$ORIGIN/../outside'))
 def test_unreachable_or_extra_input(self):
  args=list(graph_fixture());args[0]['/usr/lib/unneeded.so']=image(soname='unneeded.so')
  with self.assertRaises(ValueError):p.graph(*args)
 def test_graph_receipt_change_rejected(self):
  args=graph_fixture();result=p.graph(*args);result['edges'].pop()
  with self.assertRaises(ValueError):v.static_recompute(args[0],result,*args[1:])
class ImportTests(unittest.TestCase):
 def fixture(self,kind='SOURCE'):
  path='/usr/lib/a.py' if kind=='SOURCE' else '/usr/lib/a.pyc' if kind=='BYTECODE' else '/usr/lib/a.so';f=file_fixture(path);files={path:f,'/usr/bin/python3.12':file_fixture('/usr/bin/python3.12')}
  rows=[{'name':'sys','origin_class':'BUILTIN','origin':'built-in','sha256':None,'file_identity':None},{'name':'abc','origin_class':'FROZEN','origin':'frozen','sha256':None,'file_identity':None},{'name':'a','origin_class':kind,'origin':path,'sha256':f['sha256'],'file_identity':f['identity']}]
  value={'schema':'PYTHON_RUNTIME_IMPORT_EVIDENCE_V1','version':[3,12,3],'isolated':True,'no_site':True,'no_bytecode_write':True,'sys_path':['/usr/lib/python3.12'],'meta_path':['trusted'],'modules':rows,'actual_executable':'/usr/bin/python3.12','mapped_extensions':[path] if kind=='EXTENSION' else []}
  expected={'sys_path':value['sys_path'][:],'meta_path':['trusted'],'modules':{r['name']:{'origin':r['origin'],'origin_class':r['origin_class']} for r in rows},'actual_executable':'/usr/bin/python3.12'};return value,files,expected
 def test_builtin_frozen_source_validated_without_execution_claim(self):
  r=p.python_imports(*self.fixture());self.assertTrue(r['execution_bytes_unproven']);self.assertFalse(r['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED'])
 def test_extension_mapping_required(self):
  args=self.fixture('EXTENSION');self.assertEqual(p.python_imports(*args)['module_count'],3);args[0]['mapped_extensions']=[]
  with self.assertRaises(ValueError):p.python_imports(*args)
 def test_unreviewed_pyc_rejected_and_reviewed_distinguished(self):
  args=self.fixture('BYTECODE')
  with self.assertRaises(ValueError):p.python_imports(*args)
  args[2]['modules']['a']['bytecode_reviewed']=True;self.assertEqual(p.python_imports(*args)['module_count'],3)
 def test_unexpected_path_meta_import_and_version(self):
  for key,val in (('sys_path',['/mnt/c/project']),('meta_path',['evil']),('version',[3,12,4])):
   args=self.fixture();args[0][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):p.python_imports(*args)
 def test_missing_module_or_extra_import_rejected(self):
  args=self.fixture();args[0]['modules'].pop()
  with self.assertRaises(ValueError):p.python_imports(*args)
 def test_file_identity_and_hash_drift(self):
  for key,val in (('sha256','b'*64),('file_identity',{})):
   args=self.fixture();args[0]['modules'][-1][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):p.python_imports(*args)
 def test_mapping_snapshot_not_lifetime(self):
  f=file_fixture('/usr/lib/a.so');r=p.mapping(b'1000-2000 r-xp 00000000 00:01 2 /usr/lib/a.so\n',{'/usr/lib/a.so':f});self.assertFalse(r['lifetime_coverage']);self.assertFalse(r['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED'])
 def test_unlisted_mapping_inode_and_deleted_rejected(self):
  for line in (b'1000-2000 r-xp 00000000 00:01 3 /usr/lib/a.so',b'1000-2000 r-xp 00000000 00:01 2 /other',b'1000-2000 r-xp 00000000 00:01 2 /usr/lib/a.so (deleted)'):
   with self.subTest(line=line),self.assertRaises(ValueError):p.mapping(line,{'/usr/lib/a.so':file_fixture('/usr/lib/a.so')})
class AliasAndGateTests(unittest.TestCase):
 def test_versioned_runtime_manifest_is_pending_and_preserves_commands(self):
  from . import diagnostic_contract as original,manager_capsule_v2 as capsule
  value=c.pending_runtime_manifest('1'*40,{n:'0'*64 for n in c.CLOSURE});self.assertEqual(value['argvs'],original.argvs(1000));self.assertEqual(value['environment'],original.environment(1000));self.assertIsNone(value['validated_dependencies']);self.assertFalse(value['execution_authorized'])
  with self.assertRaisesRegex(ValueError,'BLOCKED_RAW_NATIVE'):capsule.manager_dispatch_gate(value)
 def test_reviewed_alias_hops_have_explicit_final_path(self):
  row=file_fixture('/lib/a.so');row['physical']='/usr/lib/a.so';row['aliases']=[{'path':'/lib','target':'usr/lib','identity':{'st_mode':stat.S_IFLNK|0o777,'st_uid':0}}];allow={'path':'/lib/a.so','sha256':None,'aliases':{'/lib':'usr/lib'}};v.file_proof(row,allow)
 def test_alias_substitution_wrong_owner_and_escape(self):
  with self.assertRaises(ValueError):c.alias_target('/lib','../../escape')
  row=file_fixture('/lib/a.so');row['aliases']=[{'path':'/lib','target':'bad','identity':{'st_mode':stat.S_IFLNK|0o777,'st_uid':1000}}]
  with self.assertRaises(ValueError):v.file_proof(row,{'path':'/lib/a.so','sha256':None,'aliases':{'/lib':'usr/lib'}})
 def test_hardlink_mode_owner_and_missing_identity(self):
  for key,val in (('st_nlink',2),('st_uid',1000),('st_mode',stat.S_IFREG|0o666),('st_size',2**64)):
   row=file_fixture();row['identity'][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):v.file_proof(row,{'path':row['requested'],'sha256':None,'aliases':{}})
 def test_static_and_maps_cannot_authorize_manager(self):
  evidence={'static_graph':{'status':'PASS_STATIC_ELF_GRAPH'},'python_imports':{'status':'PASS_PYTHON_OBSERVED_ORIGIN_CONTRACT'},'COMPLETE_DYNAMIC_RESOLUTION_ATTESTED':False}
  with self.assertRaisesRegex(ValueError,'LIFECYCLE'):p.manager_gate(evidence)
  evidence['COMPLETE_DYNAMIC_RESOLUTION_ATTESTED']=True
  with self.assertRaisesRegex(ValueError,'UNSUPPORTED'):p.manager_gate(evidence)
 def test_strict_json_duplicate_float_negative_and_huge(self):
  for raw in (b'{"a":1,"a":2}',b'{"x":-1}',b'{"x":1.0}',b'{"x":NaN}',b'{"x":18446744073709551616}'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):c.load(raw)
 def test_authorization_fixture_is_not_human_authorization(self):
  scope,sr,rr,now=fixture_approval()
  with self.assertRaisesRegex(ValueError,'PROVENANCE'):nc.approval(sr,rr,c.sha(sr),c.sha(rr),now=now)
  got,_=nc.approval(sr,rr,c.sha(sr),c.sha(rr),now=now,allow_fixture=True);self.assertFalse(got['execution_authorized'])
 def test_expired_replay_and_wrong_original_bytes(self):
  scope,sr,rr,now=fixture_approval()
  for args in ({'now':now+datetime.timedelta(hours=2)},{'now':now,'seen':(c.sha(rr),)}):
   with self.subTest(args=args),self.assertRaises(ValueError):nc.approval(sr,rr,c.sha(sr),c.sha(rr),allow_fixture=True,**args)
  with self.assertRaises(ValueError):nc.approval(sr+b' ',rr,c.sha(sr),c.sha(rr),now=now,allow_fixture=True)
 def test_version_approval_and_scope_operation_rejected(self):
  scope,sr,rr,now=fixture_approval()
  with self.assertRaises(ValueError):nc.approval(sr,rr,c.sha(sr),next(iter(c.CONSUMED)),now=now,allow_fixture=True)
  scope['operation']='MANAGER_QUERY'
  with self.assertRaises(ValueError):nc.check(scope)
