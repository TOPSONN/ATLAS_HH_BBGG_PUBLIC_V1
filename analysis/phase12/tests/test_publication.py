import copy,hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('p12_pub',Path(__file__).resolve().parents[1]/'scripts/validate_publication.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Publication(unittest.TestCase):
 def send(self,name,raw):return m.payload(name,raw,{name})
 def gates(self):return {**m.PHYSICS,**{k:False for k in m.FALSE_GATES},**{k:0 for k in m.COUNTERS}}
 def test_source_extensions_allowed(self):
  for suffix in ('.py','.json','.md','.csv','.txt','.cxx','.h','.sh'):
   p='analysis/phase12/x'+suffix;self.send(p,b'{}' if suffix=='.json' else b'# source\n')
 def test_gitattributes_allowed(self):self.send('analysis/phase12/.gitattributes',b'evidence/** -text\n')
 def test_only_one_workflow_allowed(self):
  self.assertTrue(m.allowed(m.WORKFLOW));self.assertFalse(m.allowed('.github/workflows/other.yml'))
 def test_canonical_paths_only(self):
  for p in ('../analysis/phase12/x.py','/analysis/phase12/x.py','analysis/phase12/../x.py','analysis/phase12/x\\y.py','analysis//phase12/x.py','analysis/phase12/./x.py','metadata/phase120_bad.json'):
   with self.subTest(p=p):self.assertFalse(m.allowed(p))
 def test_historical_scopes_rejected(self):
  for phase in range(6,12):
   p=f'analysis/phase{phase}/x.py'
   with self.subTest(phase=phase),self.assertRaises(ValueError):self.send(p,b'# source')
 def test_unlisted_rejected(self):
  with self.assertRaises(ValueError):m.payload('analysis/phase12/x.py',b'x',set())
 def test_pdf_png_extensions_rejected(self):
  for ext in ('.pdf','.PDF','.png','.PNG'):
   p='analysis/phase12/evidence/figure'+ext
   with self.subTest(ext=ext),self.assertRaises(ValueError):self.send(p,b'text')
 def test_binary_grid_event_extensions_rejected(self):
  for ext in ('.root','.lhe.gz','.hepmc3','.jsonl','.exe','.so','.a','.dat','.info','.pyc','.tar.gz','.zip'):
   p='analysis/phase12/evidence/x'+ext
   with self.subTest(ext=ext),self.assertRaises(ValueError):self.send(p,b'abc')
 def test_raw_config_names_rejected(self):
  for base in ('mg5_configuration.txt','lhapdf.conf'):
   p='analysis/phase12/evidence/'+base
   with self.subTest(base=base),self.assertRaises(ValueError):self.send(p,b'text')
 def test_disguised_magic_rejected(self):
  for raw in (b'%PDF-1.0',b'\x89PNGabc',b'rootabc',b'MZabc',b'\x7fELFabc',b'\x1f\x8babc',b'PK\x03\x04abc'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):self.send('analysis/phase12/evidence/x.txt',raw)
 def test_disguised_lhapdf_grid_or_info_rejected(self):
  for raw in (b'PdfType: central\nFormat: lhagrid1\n---\n',b'SetDesc: candidate\nSetIndex: 1\n'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):self.send('analysis/phase12/evidence/x.txt',raw)
 def test_current_runtime_hash_rejected_without_publishing_raw_bytes(self):
  from unittest.mock import patch
  digest='e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1'
  self.assertIn(digest,m.PRIVATE_RUNTIME_HASHES)
  with patch.object(m,'sha',return_value=digest),self.assertRaisesRegex(ValueError,'PRIVATE_RUNTIME_RAW_IDENTITY'):
   self.send('analysis/phase12/evidence/inert.txt',b'inert method fixture')
 def test_raw_private_configuration_body_rejected(self):
  raw=b'# MG5 MAIN DIRECTORY\nfortran_compiler = x\ncpp_compiler = x\nauto_update = 0\nmg5_path = /private\n'
  with self.assertRaises(ValueError):self.send('analysis/phase12/evidence/renamed.txt',raw)
 def test_raw_private_config_embedded_in_json_rejected(self):
  raw='# MG5 MAIN DIRECTORY\nfortran_compiler = x\ncpp_compiler = x\nauto_update = 0\nmg5_path = /private\n'
  with self.assertRaises(ValueError):self.send('analysis/phase12/evidence/embed.json',json.dumps({'innocent_name':raw}).encode())
 def test_encoded_private_field_rejected(self):
  for value in ('YWJj',[1,2,3],{'a':'bytes'}):
   with self.subTest(value=value),self.assertRaises(ValueError):self.send('analysis/phase12/evidence/x.json',json.dumps({'raw_base64':value}).encode())
 def test_identity_counts_and_redaction_are_allowed(self):
  self.send('analysis/phase12/evidence/x.json',json.dumps({'raw_bytes':9266,'raw_hex':None,'raw_config':'REDACTED','sha256':'a'*64}).encode())
 def test_empty_unbounded_rejected(self):
  for raw in (b'',b'x'*(2*1024**2)):
   with self.assertRaises(ValueError):self.send('analysis/phase12/evidence/x.txt',raw)
 def test_crlf_exact_identity_preserved(self):
  m.exact_bytes(b'x\r\n',b'x\r\n','x.csv')
  with self.assertRaises(ValueError):m.exact_bytes(b'x\n',b'x\r\n','x.csv')
 def test_gates_current_boundary(self):self.assertTrue(m.validate_gates(self.gates()))
 def test_physics_promotions_rejected(self):
  for key in m.PHYSICS:
   g=self.gates();g[key]='PASS'
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_gates(g)
 def test_baseline_parser_matching_approval_promotions_rejected(self):
  for key in m.FALSE_GATES:
   for value in (True,0,None):
    g=self.gates();g[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.validate_gates(g)
 def test_production_counters_must_be_integer_zero(self):
  for key in m.COUNTERS:
   for value in (False,1,None,0.0):
    g=self.gates();g[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):m.validate_gates(g)
 def test_exact_evidence_class_allowlist(self):
  self.assertEqual(m.CLASSES,{'ACTUAL_RAW_RUNTIME_OBSERVATION','PUBLIC_SOURCE_AUDIT','ACTUAL_ISOLATED_PDF_READBACK','LOCAL_PAYLOAD_METADATA_AUDIT','SYNTHETIC_METHOD_ONLY','INDEPENDENT_ALGEBRA_METHOD_TEST','HISTORICAL_SOURCE_AUDIT','FUTURE_UNEXECUTED_PROPOSAL'})
 def test_delivery_exceptions_are_only_three(self):self.assertEqual(m.DELIVERY,{m.QUALITY,m.MANIFEST,'reports/phase12_final_report.md'})

class GitPayloadFixtures(unittest.TestCase):
 def setUp(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);self.repo=Path(td.name)
  self.git('init','-q');self.git('config','user.name','Inert fixture');self.git('config','user.email','fixture@example.invalid');self.git('config','core.autocrlf','false')
  (self.repo/'base.txt').write_bytes(b'base');self.git('add','base.txt');self.git('commit','-q','-m','fixture base');self.base=self.git('rev-parse','HEAD').decode().strip()
 def git(self,*args):return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.STDOUT,timeout=15)
 def write(self,name,raw):
  p=self.repo/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return p
 def commit(self,name):self.git('add','-A');self.git('commit','-q','-m',name)
 def test_every_intermediate_blob_is_checked(self):
  name='analysis/phase12/evidence/result.txt';self.write(name,b'%PDF-1.0 hidden intermediate');self.commit('bad intermediate');self.write(name,b'now harmless text');self.commit('harmless final')
  with self.assertRaisesRegex(ValueError,'BINARY_OR_FIGURE_MAGIC'):m.audit_git(self.repo,{name},self.base)
 def test_intermediate_private_config_is_not_erased_by_final(self):
  name='analysis/phase12/evidence/result.txt';self.write(name,b'# MG5 MAIN DIRECTORY\nfortran_compiler = x\ncpp_compiler = x\nauto_update = 0\n');self.commit('private intermediate');self.write(name,b'bounded final');self.commit('clean final')
  with self.assertRaisesRegex(ValueError,'RAW_PRIVATE_CONFIGURATION_DISGUISED'):m.audit_git(self.repo,{name},self.base)
 def test_index_raw_bytes_are_checked(self):
  name='analysis/phase12/evidence/result.csv';self.write(name,b'x\n');self.git('add',name);self.write(name,b'x\r\n')
  with self.assertRaisesRegex(ValueError,'INDEX_OR_REMOTE_NORMALIZATION'):m.audit_git(self.repo,{name},self.base)
 def test_git_symlink_payload_rejected(self):
  name='analysis/phase12/evidence/result.txt';p=self.repo/name;p.parent.mkdir(parents=True);p.symlink_to('missing');self.commit('symlink payload')
  with self.assertRaises(ValueError):m.audit_git(self.repo,{name},self.base)
 def test_ordinary_bounded_source_history_passes(self):
  name='analysis/phase12/source/helper.py';self.write(name,b'# first\n');self.commit('first source');self.write(name,b'# final\n');self.commit('final source')
  r=m.audit_git(self.repo,{name},self.base);self.assertEqual(r['outgoing_commits'],2);self.assertEqual(r['outgoing_payload_snapshots'],2);self.assertTrue(r['all_staged_and_intermediate_commit_payloads_inspected'])
 def test_deleted_intermediate_unlisted_path_cannot_disappear(self):
  name='analysis/phase12/evidence/temp.txt';p=self.write(name,b'not manifested');self.commit('unlisted intermediate');p.unlink();self.commit('delete intermediate')
  with self.assertRaises(ValueError):m.audit_git(self.repo,set(),self.base)
if __name__=='__main__':unittest.main()
