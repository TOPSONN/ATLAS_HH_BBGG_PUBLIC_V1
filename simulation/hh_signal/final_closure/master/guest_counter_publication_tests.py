"""Bounded publication and the one exact CI routing exception."""
import json,unittest
from . import guest_counter_publication as p,history
class PublicationTests(unittest.TestCase):
 def test_public_sanitized_status_allowed(self):
  p.validate(p.REPORTS+'G1_GUEST_VALIDATION.json',b'{"status":"PASS_READ_ONLY_OBSERVED","unlimited_limits":[]}')
 def test_private_identity_and_raw_capture_rejected(self):
  for raw in (b'{"records":[]}',b'{"boot_id":"INERT"}',b'{"cgroup_lineage":[]}',b'{"schema":"HH_G1_GUEST_READONLY_V2"}',b'{"serial":"INERT"}'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):p.validate(p.REPORTS+'G1_GUEST_VALIDATION.json',raw)
 def test_unapproved_figures_binary_or_outside_scope_rejected(self):
  for name,raw in ((p.REPORTS+'figure.png',b'INERT'),(p.REPORTS+'G1_GUEST_VALIDATION.json',b'MZ'),('private/raw.json',b'{}'),(p.PREFIX+'guest_v2.py',b'INERT')):
   with self.subTest(name=name),self.assertRaises(ValueError):p.validate(name,raw)
 def test_exact_ci_suffix_required_and_no_other_changes(self):
  raw=(p.original.REPO/history.CAMPAIGN).read_bytes()
  history.reviewed_workflow_delta(history.CAMPAIGN,raw,history.FROZEN)
  for changed in (raw+b'\n# extra',raw.replace(history.COUNTER_SUFFIX.encode(),history.COUNTER_SUFFIX.encode()*2),raw.replace(history.ENGINEERING_SUFFIX.encode(),b'')):
   with self.assertRaises(ValueError):history.reviewed_workflow_delta(history.CAMPAIGN,changed,history.FROZEN)
 def test_nested_serialized_and_escaped_raw_identity_rejected(self):
  for text in (json.dumps({'wrapper':json.dumps({'cgroup_lineage':[]})}),'{"\\u0062oot_id":"INERT"}'):
   with self.subTest(text=text),self.assertRaises(ValueError):p.validate(p.REPORTS+'G1_GUEST_VALIDATION.json',text.encode())
if __name__=='__main__':unittest.main()
