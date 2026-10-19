import ast,copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[1]/'source/phase7i_dependency.py'
spec=importlib.util.spec_from_file_location('phase12_dep_tests',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Phase7IDependencyTests(unittest.TestCase):
 def rows(self):return [{'path':'Source/file.f','sha256':'a'*64}]
 def test_valid_explicit_inventory(self):self.assertEqual(m.validate_inventory(self.rows()),self.rows())
 def test_abs_path_rejected(self):
  rows=self.rows();rows[0]['path']='/input/mg5_configuration.txt'
  with self.assertRaisesRegex(ValueError,'UNSAFE'):m.validate_inventory(rows)
 def test_parent_escape_rejected(self):
  rows=self.rows();rows[0]['path']='../input/mg5_configuration.txt'
  with self.assertRaisesRegex(ValueError,'UNSAFE'):m.validate_inventory(rows)
 def test_noncanonical_path_rejected(self):
  rows=self.rows();rows[0]['path']='Source//file.f'
  with self.assertRaisesRegex(ValueError,'UNSAFE'):m.validate_inventory(rows)
 def test_duplicate_inventory_rejected(self):
  rows=self.rows()*2
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):m.validate_inventory(rows)
 def test_missing_sha_rejected(self):
  rows=self.rows();del rows[0]['sha256']
  with self.assertRaisesRegex(ValueError,'HASH'):m.validate_inventory(rows)
 def test_malformed_sha_rejected(self):
  for value in [None,False,'0'*63,'x'*64]:
   rows=self.rows();rows[0]['sha256']=value
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'HASH'):m.validate_inventory(rows)
 def test_missing_or_empty_inventory_not_absence_proof(self):
  for rows in [None,[],{}]:
   with self.subTest(rows=rows),self.assertRaises(ValueError):m.validate_inventory(rows)
 def test_exact_target_is_direct_dependency(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);target=root/'Source/file.f';target.parent.mkdir();target.write_bytes(b'source')
   s=m.inventory_scope('fixture',self.rows(),root,target)
   self.assertEqual(s['classification'],'DIRECT_DEPENDENCY');self.assertEqual(m.classify_dependency([s],positive_callchain_review=False),'DIRECT_DEPENDENCY')
 def test_target_symlink_alias_is_still_direct(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);target=root/'actual';target.write_bytes(b'source');(root/'Source').mkdir();(root/'Source/file.f').symlink_to(target)
   self.assertEqual(m.inventory_scope('fixture',self.rows(),root,target)['classification'],'DIRECT_DEPENDENCY')
 def test_absence_without_positive_callchain_is_unknown(self):
  s={'target_matches':[]};self.assertEqual(m.classify_dependency([s],positive_callchain_review=False),'UNKNOWN')
 def test_explicit_indirect_call_remains_indirect(self):
  s={'target_matches':[]};self.assertEqual(m.classify_dependency([s],positive_callchain_review=True,explicit_indirect_read=True),'INDIRECT_DEPENDENCY')
 def test_reviewed_contract_absence_is_scope_limited(self):
  s={'target_matches':[]};self.assertEqual(m.classify_dependency([s],positive_callchain_review=True),'NOT_BOUND_BY_REVIEWED_CONTRACT')
 def test_no_scopes_cannot_pass(self):
  with self.assertRaises(ValueError):m.classify_dependency([],positive_callchain_review=True)
 def test_ast_function_call_sites_are_not_executed(self):
  raw=b'def prepare():\n    forbidden_native_build()\n    return "something"\n'
  r=m.function_record(raw,'prepare');self.assertEqual(r['calls'],['forbidden_native_build']);self.assertFalse(r['literal_mg5_configuration_target_present'])
 def test_ast_explicit_target_read_detected(self):
  r=m.function_record(b'def reader():\n return open("mg5_configuration.txt")\n','reader');self.assertTrue(r['literal_mg5_configuration_target_present'])
 def test_ast_missing_function_rejected(self):
  with self.assertRaises(ValueError):m.function_record(b'def x(): pass','prepare')
 def test_exact_revision_rejects_new_or_stale_head(self):
  for h in [b'0'*40,b'b80e1677']:
   with patch.object(m,'git_read',return_value=h):
    with self.assertRaisesRegex(ValueError,'EXACT_PHASE7I'):m.require_revision(Path('/inert'))
 def test_revision_query_is_readonly_git(self):
  with patch.object(m,'git_read',return_value=m.REVISION.encode()) as q:
   self.assertEqual(m.require_revision(Path('/inert')),m.REVISION);self.assertEqual(q.call_args.args[1:],('rev-parse','HEAD'))
 def test_source_raw_hash_not_semantically_normalized(self):self.assertNotEqual(m.digest_bytes(b'x=1\n'),m.digest_bytes(b'x=1 \n'))
 def test_no_old_runtime_or_generator_import(self):
  tree=ast.parse(SOURCE.read_text());names=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):names +=[x.name for x in n.names]
   elif isinstance(n,ast.ImportFrom):names.append(n.module or '')
  self.assertFalse(any(n.startswith(('simulation.','madgraph','ROOT','pythia')) for n in names))
 def test_cli_refuses_existing_output_before_audit(self):
  path=SOURCE.parents[1]/'scripts/audit_phase7i_dependency.py'
  spec=importlib.util.spec_from_file_location('dep_cli_tests',path);cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'receipt.json';out.write_bytes(b'KEEP')
   with patch('sys.argv',[str(path),'--phase7i-checkout','/inert','--output',str(out)]):
    with self.assertRaisesRegex(SystemExit,'FRESH_OUTPUT_REQUIRED'):cli.main()
   self.assertEqual(out.read_bytes(),b'KEEP')
if __name__=='__main__':unittest.main()
