import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from .. import g1_publication as p

class G1PublicationTests(unittest.TestCase):
 def test_only_exact_source_and_safe_reports_are_allowed(self):
  self.assertTrue(p.allowed(p.PREFIX+'g1_windows_inventory.ps1'))
  for n in ('device_policy.py','instance_binding.py','evidence_slots.py','offline_regression.py'):
   self.assertFalse(p.allowed(p.PREFIX+n))
  for n in ('a.png','a.pdf','data.lhe','input.root','private/x.json'):
   self.assertFalse(p.allowed(p.REPORTS+n))
 def test_private_capture_fields_and_sid_are_rejected(self):
  name=p.REPORTS+'evidence.json'
  for obj in ({'schema':'PHASE7I_G1_HOST_CAPTURE_V1'},{'SerialNumber':'INERT'},
              {'nested':{'stdout':'INERT'}},{'identity':'S-1-5-21-1-2-3-1001'}):
   with patch.object(p.original,'allowed_path',p.allowed):
    with self.assertRaises(ValueError):p.validate(name,json.dumps(obj).encode())
 def test_every_intermediate_is_inspected_even_if_head_removes_private_file(self):
  root=Path(__file__).resolve().parents[5]
  local=root/'.local';local.mkdir(exist_ok=True)
  if not local.resolve().is_relative_to(root):raise ValueError('FIXTURE_OUTSIDE_WORKSPACE')
  with tempfile.TemporaryDirectory(dir=local) as d:
   r=Path(d)
   def git(*args):return subprocess.check_output(['git',*args],cwd=r,stderr=subprocess.STDOUT).decode().strip()
   git('init');git('config','user.name','Inert');git('config','user.email','inert@example.invalid')
   (r/'base.txt').write_text('INERT');git('add','base.txt');git('commit','-m','base');base=git('rev-parse','HEAD')
   f=r/'reports/phase7i_g1_g2_feasibility/evidence.json';f.parent.mkdir(parents=True)
   f.write_text('{"SerialNumber":"INERT_PRIVATE"}');git('add','.');git('commit','-m','rejected intermediate')
   f.write_text('{"status":"INERT_SAFE"}');git('add','.');git('commit','-m','safe head')
   with patch.object(p,'BASE',base):
    with self.assertRaisesRegex(ValueError,'PRIVATE'):p.audit(r)
 def test_encoded_json_uppercase_suffix_and_markdown_cannot_hide_private_frames(self):
  bad={'serial':'INERT_PRIVATE'}
  for name,raw in [(p.REPORTS+'x.JSON',json.dumps(bad)),
                   (p.REPORTS+'x.json',json.dumps({'wrapped':json.dumps(bad)})),
                   (p.REPORTS+'x.md','```json\n'+json.dumps(bad)+'\n```'),
                   (p.REPORTS+'x.md',json.dumps(json.dumps(bad))),
                   (p.REPORTS+'x.md','"S-\\u0031-5-21-1-2-3-1001"'),
                   (p.REPORTS+'x.txt','serial=INERT_PRIVATE\n'),
                   (p.REPORTS+'x.md','{"schema":"PHASE7I_G1_GUEST_CAPTURE_V1"}')]:
   with patch.object(p.original,'allowed_path',p.allowed):
    with self.assertRaises(ValueError):p.validate(name,raw.encode())

if __name__=='__main__':unittest.main()
