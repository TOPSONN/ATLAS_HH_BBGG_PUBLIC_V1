import copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
import parser_contract as p
class ContractTests(unittest.TestCase):
 def test_current_source_cannot_dispatch(self):self.assertIs(p.FULL_LAUNCH_ENVELOPE_IMPLEMENTED,False)
 def test_exact_contract(self):self.assertEqual(p.validate_contract(copy.deepcopy(p.SCHEMA)),p.SCHEMA)
 def test_scope_and_caps_mutations(self):
  for key in p.SCHEMA:
   c=copy.deepcopy(p.SCHEMA);c[key]=None
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,"PARSER_SCOPE"):p.validate_contract(c)
 def test_unknown_field_rejected(self):
  c=copy.deepcopy(p.SCHEMA);c['yes']=True
  with self.assertRaises(ValueError):p.validate_contract(c)
 def test_symbolic_generate_explicit(self):
  self.assertTrue(p.SCHEMA['diagram_enumeration']);self.assertFalse(p.SCHEMA['code_generation'])
  self.assertEqual(p.COMMANDS[2],'generate p4 p4 > b b~ a a QCD=2 QED=2')
 def test_missing_approval_before_package_read(self):
  with self.assertRaisesRegex(ValueError,'MISSING_NEW_EXPLICIT'):p.authorization('/nonexistent/package',None)
 def test_missing_approval_path(self):
  with self.assertRaisesRegex(ValueError,'MISSING_NEW_EXPLICIT'):p.authorization('/nonexistent/package','/nonexistent/approve')
 def test_no_old_review_reuse(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=root/'approval';q=root/'package'
   a.write_text(json.dumps({'authorization_type':'BUILD_ONLY'}));q.write_text(json.dumps({'human_approval_status':'NOT_AUTHORIZED','execution_eligible':True,'package_status':'READY_FOR_SEPARATE_APPROVAL','configuration_proposal_identity':{'bytes':1,'sha256':'0'*64},'parser_executed':False,'contract':p.SCHEMA,'source_revision':'0'*40,'contract_sha256':p.canonical(p.SCHEMA),'future_output':str(root/'out')}))
   with patch.object(p,'FULL_LAUNCH_ENVELOPE_IMPLEMENTED',True),self.assertRaisesRegex(ValueError,'NEW_EXACT_SCOPE'):p.authorization(q,a,is_tty=True,terminal_input=lambda:'')
 def test_exact_approval_requires_tty_and_challenge(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=root/'approval';q=root/'package'
   package={'human_approval_status':'NOT_AUTHORIZED','execution_eligible':True,'package_status':'READY_FOR_SEPARATE_APPROVAL','configuration_proposal_identity':{'bytes':1,'sha256':'0'*64},'parser_executed':False,'contract':p.SCHEMA,'source_revision':'0'*40,'contract_sha256':p.canonical(p.SCHEMA),'future_output':str(root/'out')}
   q.write_text(json.dumps(package));a.write_text(json.dumps({'authorization_type':'EXPLICIT_USER_PARSER_APPROVAL','package_sha256':p.identity(q)['sha256'],'source_revision':package['source_revision'],'contract_sha256':package['contract_sha256'],'future_output':package['future_output'],'one_attempt':True}))
   with patch.object(p,'FULL_LAUNCH_ENVELOPE_IMPLEMENTED',True),self.assertRaisesRegex(ValueError,'HUMAN_TERMINAL'):p.authorization(q,a,is_tty=False)
   with patch.object(p,'FULL_LAUNCH_ENVELOPE_IMPLEMENTED',True),self.assertRaisesRegex(ValueError,'EXACT_HUMAN'):p.authorization(q,a,is_tty=True,terminal_input=lambda:'yes')
   with patch.object(p,'FULL_LAUNCH_ENVELOPE_IMPLEMENTED',True),self.assertRaisesRegex(ValueError,'EXACT_HUMAN'):p.authorization(q,a,is_tty=True,terminal_input=lambda:'AUTHORIZE SYMBOLIC_PARSER '+p.identity(q)['sha256']+' ')
   self.assertFalse((root/'out').exists())
 def test_output_fresh_and_contained(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.assertEqual(p.fresh_output(root/'new',root),root/'new')
   for path in (root,root/'../escape'):
    with self.assertRaises(ValueError):p.fresh_output(path,root)
   (root/'link').symlink_to(root,target_is_directory=True)
   with self.assertRaises(ValueError):p.fresh_output(root/'link/new',root)
 def test_unproven_complete_launch_is_rejected_before_challenge(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);q=root/'package';a=root/'approval';q.write_text(json.dumps({'execution_eligible':False,'package_status':'BLOCKED_PHASE13_RESOURCE_ENFORCEMENT'}));a.write_text('{}')
   with self.assertRaisesRegex(ValueError,'FULL_LAUNCH_ENVELOPE_NOT_PROVEN'):p.authorization(q,a,is_tty=True,terminal_input=lambda:self.fail('MUST_NOT_CHALLENGE'))
 def test_no_numerical_or_dispatch_authorization(self):
  for key in ('numerical_ME','integration','event_production','output_process_build','launch','Pythia','Delphes','StageA','check_process','parser_approved','parser_executed'):
   self.assertIs(p.SCHEMA[key],False)
if __name__=='__main__':unittest.main()
