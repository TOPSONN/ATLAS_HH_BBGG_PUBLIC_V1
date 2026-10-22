import ast,copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from . import diagnostic_plan as plan,diagnostic_publication as pub,diagnostic_docs as docs
from .contract import REPO,sha
class PreparationTests(unittest.TestCase):
 def test_new_profile_does_not_reuse_old_progress(self):
  self.assertNotEqual(plan.PROGRESS,plan.prior.PROGRESS);self.assertEqual(len(plan.STAGES),12);self.assertNotIn('diagnostic_capture',plan.BOOTSTRAP)
 def test_source_binding_includes_adapter_not_live_data(self):
  context={'scope_identity':'old','scope':'old','base':'old','source_rows':[]}
  with patch.object(plan,'PRIOR_BINDING',return_value=context):c=plan.binding('unused',guest='unused')
  names={x['path'] for x in c['source_rows']};self.assertIn(pub.PREFIX+'diagnostic_capture.py',names);self.assertIn(pub.PREFIX+'diagnostic_validate.py',names);self.assertEqual(c['scope'],'G2_EFFECTIVE_DIAGNOSTIC_PREPARATION_NO_ACQUISITION')
 def test_safe_stages_have_no_acquisition_call(self):
  tree=ast.parse((REPO/pub.PREFIX/'diagnostic_stages.py').read_text(encoding='utf-8'))
  for node in ast.walk(tree):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):self.assertNotIn(node.func.attr,('capture','snapshot','Popen','child','socket_ready','probe'))
 def test_publication_rejects_raw_and_unapproved_artifacts(self):
  name=pub.REPORTS+'FINAL_STATUS.json'
  for data in (b'{"boot_id":"private"}',b'{"stdout_b64":"private"}',b'{"schema":"HH_G2_EFFECTIVE_DIAGNOSTIC_V1"}'):
   with self.assertRaises(ValueError):pub.validate(name,data)
  for path in ('private/receipt.json',pub.REPORTS+'plot.png',pub.REPORTS+'plot.pdf'):
   with self.assertRaises(ValueError):pub.validate(path,b'{}')
 def test_pending_tool_scope_is_publishable_but_never_approved(self):
  self.assertTrue(pub.validate(pub.REPORTS+'G2_DIAGNOSTIC_TOOL_MANIFEST.json',b'{"tool_sha256":{"/usr/bin/systemctl":null},"execution_ready":false}'))
 def test_eight_decisions_explicit_and_old_documents_not_rewritten(self):
  rows=docs.clause_review();self.assertEqual(len(rows),8);self.assertTrue(all(r['accepted'] is False and len(r)==10 for r in rows))
if __name__=='__main__':unittest.main()
