import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import publication as p
from .contract import REPO
class PublicationTests(unittest.TestCase):
 def validate(self,name,raw):
  with patch.object(p.original,'allowed_path',p.allowed):return p.validate(name,raw)
 def test_explicit_scope_denies_private_trace_figures_and_events(self):
  self.assertTrue(p.allowed(p.PREFIX+'runner.py'))
  for name in ('local_failure_trace.txt','a.pdf','a.png','events.root','context.json','EXPORT_MANIFEST.json'):
   self.assertFalse(p.allowed(p.REPORTS+name))
 def test_private_raw_and_encoded_payload_rejected(self):
  for value in ({'observations':[]},{'serial':'INERT_PRIVATE'},{'a':json.dumps({'wwn':'INERT_PRIVATE'})}):
   with self.assertRaises(ValueError):self.validate(p.REPORTS+'validation.json',json.dumps(value).encode())
  with self.assertRaises(ValueError):self.validate(p.REPORTS+'MASTER_REPORT_ZH_TW.md',json.dumps(json.dumps({'serial':'INERT'})).encode())
 def test_null_unexecuted_measurements_and_sanitized_summary_allowed(self):
  self.validate(p.REPORTS+'validation.json',b'{"GENUINE_ME_CALLS":null,"kernel_CPU":null,"FULL_LAUNCH_ENVELOPE_VERIFIED":false}')
 def test_unsafe_intermediate_not_hidden_by_safe_head(self):
  local=REPO/'.local/master_publication_fixtures';local.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=local) as d:
   r=Path(d)
   def git(*args):return subprocess.check_output(['git','-C',str(r),*args],stderr=subprocess.STDOUT).decode().strip()
   git('init');git('config','user.name','Inert');git('config','user.email','inert@example.invalid')
   (r/'base.txt').write_text('INERT');git('add','base.txt');git('commit','-m','base');base=git('rev-parse','HEAD')
   f=r/(p.REPORTS+'validation.json');f.parent.mkdir(parents=True);f.write_text('{"serial":"INERT_PRIVATE"}');git('add','.');git('commit','-m','bad intermediate')
   f.write_text('{"scope":"SOURCE_ONLY"}');git('add','.');git('commit','-m','safe head')
   with patch.object(p,'BASE',base):
    with self.assertRaisesRegex(ValueError,'PRIVATE'):p.audit(r)
if __name__=='__main__':unittest.main()
