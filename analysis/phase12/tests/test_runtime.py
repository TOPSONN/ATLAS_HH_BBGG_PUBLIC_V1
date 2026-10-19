import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
import runtime_provenance as runtime

class RuntimeMethods(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
  self.policy=json.loads((Path(__file__).resolve().parents[1]/"config/runtime_proposal.json").read_text())
  self.base=b"fortran_compiler = f77 # \ncpp_compiler = cxx # \nauto_update = 0 # \nmg5_path = /SYNTHETIC_METHOD_ONLY\n"
 def test_policy_no_baseline_approval(self):
  self.assertTrue(runtime.validate_policy(self.policy));self.policy["new_baseline_approved"]=True
  with self.assertRaisesRegex(ValueError,"APPROVAL"):runtime.validate_policy(self.policy)
 def test_dispatcher_rejected(self):
  self.policy["dispatcher"]="mg5"
  with self.assertRaisesRegex(ValueError,"DISPATCHER"):runtime.validate_policy(self.policy)
 def test_physical_permission_rejected(self):
  self.policy["physical_execution_authorized"]=True
  with self.assertRaisesRegex(ValueError,"AUTHORIZED"):runtime.validate_policy(self.policy)
 def test_snapshot_limit_not_unbounded(self):
  self.policy["max_config_bytes"]=0
  with self.assertRaisesRegex(ValueError,"BOUNDED"):runtime.validate_policy(self.policy)
 def test_installed_output_rejected(self):
  forbidden=self.root/"installed";forbidden.mkdir()
  with self.assertRaisesRegex(ValueError,"INSTALLED"):
   runtime.safe_output(forbidden/"new",self.root,[forbidden])
 def test_policy_cannot_authorize_installed_output(self):
  self.policy['allowed_output_root']='/home/btu/opt'
  with self.assertRaisesRegex(ValueError,'PATH_POLICY'):runtime.validate_policy(self.policy)
 def test_installed_write_guard_cannot_be_removed(self):
  self.policy['forbidden_write_roots']=[]
  with self.assertRaisesRegex(ValueError,'GUARD'):runtime.validate_policy(self.policy)
 def test_snapshot_worker_cannot_be_unbounded(self):
  self.policy['worker_timeout_seconds']=None
  with self.assertRaisesRegex(ValueError,'UNBOUNDED'):runtime.validate_policy(self.policy)
 def test_result_workspace_containment(self):
  with self.assertRaisesRegex(ValueError,"OUTSIDE"):
   runtime.safe_output(self.root.parent/"elsewhere",self.root,[])
 def test_no_existing_file_overwrite(self):
  path=self.root/"old";path.write_bytes(b"preserve")
  with self.assertRaises(FileExistsError):runtime.private_write(path,b"changed")
  self.assertEqual(path.read_bytes(),b"preserve")
 def test_semantics_not_raw_identity(self):
  changed=self.base.replace(b"auto_update = 0",b"auto_update = 0 ")
  self.assertEqual(runtime.semantic_settings(self.base),runtime.semantic_settings(changed))
  self.assertNotEqual(runtime.sha(self.base),runtime.sha(changed))
 def test_semantic_zero_is_string_not_missing(self):
  settings=runtime.semantic_settings(self.base);self.assertEqual(settings["auto_update"],"0")
  self.assertNotIn("alpha_s",settings)
 def test_duplicate_setting_rejected(self):
  with self.assertRaisesRegex(ValueError,"DUPLICATE"):
   runtime.semantic_settings(self.base+b"auto_update = 1\n")
 def test_serializer_inverse_roundtrip(self):
  text=self.base
  for _ in range(3):text=runtime.serializer_round(text)
  self.assertEqual(runtime.inverse_padding(text,3),self.base)
  self.assertEqual(runtime.semantic_settings(text),runtime.semantic_settings(self.base))
  self.assertEqual(len(text)-len(self.base),27)
 def test_wrong_padding_not_normalized(self):
  with self.assertRaises(ValueError):runtime.inverse_padding(self.base,64)
 def test_public_settings_do_not_expose_arbitrary_values(self):
  settings=runtime.semantic_settings(self.base);settings["private_token"]="PRIVATE_SENTINEL"
  published=runtime.public_settings(settings)
  self.assertNotIn("private_token",published);self.assertNotIn("mg5_path",published)
 def test_snapshot_reads_unchanged_synthetic_target(self):
  target=self.root/"fixture";target.write_bytes(self.base)
  before=target.stat()
  result=runtime.snapshot(target,target.resolve(),self.root/"private")
  self.assertEqual(result["raw_identity"],runtime.identity(self.base))
  self.assertEqual(target.read_bytes(),self.base)
  self.assertEqual(before.st_mtime_ns,target.stat().st_mtime_ns)
  self.assertFalse(result["installed_file_write_performed"])
  self.assertEqual((self.root/"private/runtime_config.raw.txt").read_bytes(),self.base)
 def test_snapshot_oversize_rejected(self):
  target=self.root/"fixture";target.write_bytes(b"x"*8)
  with self.assertRaisesRegex(ValueError,"SIZE"):runtime.snapshot(target,target.resolve(),self.root/"private",4)
  self.assertFalse((self.root/"private").exists())
 def test_snapshot_resolution_mismatch_rejected(self):
  target=self.root/"fixture";target.write_bytes(self.base)
  with self.assertRaisesRegex(ValueError,"RESOLUTION"):
   runtime.snapshot(target,self.root/"different",self.root/"private")
 def snapshots(self):
  rows=[]
  for index in (1,2,3):
   rows.append({"pid":index,"status":"PASS_BOUNDED_READ_ONLY_SNAPSHOT","raw_identity":runtime.identity(self.base),
                "file_metadata_after":dict(device=1,inode=1,bytes=len(self.base),mtime_ns=1,ctime_ns=1),
                "resolved_path":"/SYNTHETIC_METHOD_ONLY","semantic_sha256":runtime.json_hash(runtime.semantic_settings(self.base)),
                "effective_settings_allowlisted":runtime.public_settings(runtime.semantic_settings(self.base))})
  return rows
 def test_three_same_pids_are_not_separate_processes(self):
  rows=self.snapshots();rows[2]["pid"]=1
  with self.assertRaisesRegex(ValueError,"DISTINCT"):runtime.summarize_snapshots(rows)
 def test_three_fixture_observations_not_cold_cache_proof(self):
  result=runtime.summarize_snapshots(self.snapshots())
  self.assertTrue(result["raw_bytes_stable"]);self.assertIn("not independent cold-cache",result["observation_scope"])
  self.assertFalse(result["writer_identified"])
 def test_changed_inode_is_not_stable_binding(self):
  rows=self.snapshots();rows[2]["file_metadata_after"]["inode"]=2
  result=runtime.summarize_snapshots(rows);self.assertFalse(result["file_identity_stable"]);self.assertEqual(result["status"],"BLOCKED_PHASE12_RUNTIME_DRIFT")
 def test_changed_raw_bytes_are_blocked(self):
  rows=self.snapshots();rows[2]["raw_identity"]=runtime.identity(b"changed")
  self.assertEqual(runtime.summarize_snapshots(rows)["status"],"BLOCKED_PHASE12_RUNTIME_DRIFT")
 def test_baseline_stays_unapproved_old_gate_blocked(self):
  result=runtime.propose_baseline(runtime.summarize_snapshots(self.snapshots()),self.policy,self.root/"private-copy")
  self.assertFalse(result["new_baseline_approved"]);self.assertEqual(result["old_phase11_raw_gate"],"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT")
  self.assertEqual(result["historical_writer"],"UNKNOWN")
 def test_absent_historical_payload_is_not_invented(self):
  source={"path":"/SYNTHETIC_METHOD_ONLY","sha256":"0"*64}
  result=runtime.exact_diff_and_reproduction(self.base,source,self.root)
  self.assertEqual(result["historical_comparisons"],[]);self.assertFalse(result["actual_writer_identified"])
  self.assertNotEqual(result["serializer_behavior"],"SERIALIZER_BEHAVIOR_REPRODUCED")
 def test_task_records_do_not_publish_commands(self):
  path=self.root/"receipt.json";path.write_text(json.dumps({"label":"SYNTHETIC_METHOD_ONLY","exit_code":0,"command":["PRIVATE_SENTINEL"]}))
  result=runtime.task_record_summary([path])
  self.assertNotIn("PRIVATE_SENTINEL",json.dumps(result));self.assertEqual(result[0]["direct_writer_attribution_from_summary"],"NOT_ESTABLISHED")
if __name__=="__main__":unittest.main()
