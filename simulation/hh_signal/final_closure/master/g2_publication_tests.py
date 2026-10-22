import json,unittest
from . import g2_publication as p,history
class PublicationTests(unittest.TestCase):
 def test_sanitized_decision_is_accepted_but_raw_identity_is_not(self):
  p.validate(p.REPORTS+'FINAL_STATUS.json',b'{"G2_USER_ACCEPTED":false,"actual_CPU":null}')
  for raw in (b'{"boot_id":"INERT"}',b'{"records":[]}',json.dumps({'x':json.dumps({'cgroup_lineage':[]})}).encode(),b'{"path":"C:/HH/.local/private/host.json"}'):
   with self.subTest(raw=raw),self.assertRaises(ValueError):p.validate(p.REPORTS+'FINAL_STATUS.json',raw)
 def test_exact_source_scope_and_figures(self):
  for name,raw in ((p.REPORTS+'figure.png',b'INERT'),(p.REPORTS+'FINAL_STATUS.json',b'MZ'),(p.PREFIX+'guest_v2.py',b'INERT'),('private/raw.json',b'{}')):
   with self.subTest(name=name),self.assertRaises(ValueError):p.validate(name,raw)
 def test_exact_new_routing_cannot_modify_frozen_science_or_accept_other_suffix(self):
  raw=(p.original.REPO/history.CAMPAIGN).read_bytes();history.reviewed_workflow_delta(history.CAMPAIGN,raw,history.FROZEN)
  for data in (raw+b'\n# unreviewed',raw.replace(history.G2_SUFFIX.encode(),history.G2_SUFFIX.encode()*2),raw.replace(history.COUNTER_SUFFIX.encode(),b'')):
   with self.assertRaises(ValueError):history.reviewed_workflow_delta(history.CAMPAIGN,data,history.FROZEN)
 def test_proposal_hashes_and_decisions_stay_unaccepted(self):
  from .g2_catalogue import TERMS,VM,OBSERVER,clause_rows
  self.assertTrue(all(len(h)==64 for h in (TERMS,VM,OBSERVER)))
  rows=clause_rows();self.assertEqual(len(rows),8);self.assertTrue(all(r['decision']=='NOT_ACCEPTED' and not r['execution_authorized'] for r in rows))
if __name__=='__main__':unittest.main()
