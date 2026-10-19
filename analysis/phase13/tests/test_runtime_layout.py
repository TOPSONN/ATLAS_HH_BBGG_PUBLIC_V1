"""Portable source-layout tests; synthetic temp files only, never import MG5."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PHASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("phase13_runtime_layout",PHASE/"source/runtime_layout.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
POLICY=json.loads((PHASE/"config/runtime_layout.json").read_text())

class LayoutTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name);self.source=self.base/"source";self.source.mkdir()
  (self.source/"input").mkdir();(self.source/"input/config").write_bytes(b"raw \n")
  self.limits={"max_entries":100,"max_single_file_bytes":1024,"max_total_regular_bytes":4096}
 def inspect(self,path=None):return m.inspect_tree(path or self.source,self.limits)
 def copied(self):
  before=self.inspect();target=self.base/"copy";m.independent_copy(self.source,target,before)
  return before,target,self.inspect(target)
 def test_independent_bytes_and_inodes(self):
  before,target,after=self.copied()
  self.assertTrue(m.verify_copy(before,after)["no_shared_original_inodes"])
  self.assertEqual((target/"input/config").read_bytes(),b"raw \n")
  self.assertNotEqual((target/"input/config").stat().st_ino,(self.source/"input/config").stat().st_ino)
 def test_relative_file_and_directory_links_remain_inside_copy(self):
  (self.source/"alias").symlink_to("input/config");(self.source/"dir_alias").symlink_to("input")
  before,target,after=self.copied();m.verify_copy(before,after)
  self.assertEqual(os.readlink(target/"alias"),"input/config")
  self.assertEqual((target/"dir_alias/config").resolve(),target/"input/config")
 def test_broken_internal_symlink_is_preserved_and_explicit(self):
  (self.source/"broken").symlink_to("input/missing")
  before,target,after=self.copied();m.verify_copy(before,after)
  self.assertTrue((target/"broken").is_symlink());self.assertFalse((target/"broken").exists())
  self.assertEqual(after["broken_internal_symlink_count"],1)
  row=next(row for row in after["entries"] if row["relative_path"]=="broken")
  self.assertEqual(row["type"],"BROKEN_INTERNAL_SYMLINK");self.assertIsNone(row["sha256"])
 def test_absolute_symlink_is_rejected_even_when_target_is_inside(self):
  (self.source/"absolute").symlink_to(self.source/"input/config")
  with self.assertRaisesRegex(ValueError,"ABSOLUTE_SOURCE_SYMLINK"):self.inspect()
 def test_relative_symlink_escape_is_rejected(self):
  (self.source/"escape").symlink_to("../outside")
  with self.assertRaisesRegex(ValueError,"SOURCE_SYMLINK_ESCAPES_RUNTIME"):self.inspect()
 def test_symlink_loop_is_rejected(self):
  (self.source/"loop").symlink_to("loop")
  with self.assertRaisesRegex(ValueError,"SOURCE_SYMLINK_LOOP"):self.inspect()
 def test_special_fifo_is_rejected(self):
  os.mkfifo(self.source/"pipe")
  with self.assertRaisesRegex(ValueError,"SPECIAL_SOURCE_FILE"):self.inspect()
 def test_privileged_file_mode_is_rejected(self):
  (self.source/"input/config").chmod(0o4600)
  with self.assertRaisesRegex(ValueError,"PRIVILEGED_SOURCE_MODE"):self.inspect()
 def test_single_file_cap(self):
  self.limits["max_single_file_bytes"]=1
  with self.assertRaisesRegex(ValueError,"SINGLE_SOURCE_FILE_SIZE_LIMIT"):self.inspect()
 def test_total_byte_cap(self):
  self.limits["max_total_regular_bytes"]=1
  with self.assertRaisesRegex(ValueError,"SOURCE_TREE_LIMIT"):self.inspect()
 def test_entry_cap(self):
  self.limits["max_entries"]=1
  with self.assertRaisesRegex(ValueError,"SOURCE_TREE_LIMIT"):self.inspect()
 def test_root_must_be_directory(self):
  with self.assertRaisesRegex(ValueError,"SOURCE_ROOT_NOT_DIRECTORY"):self.inspect(self.source/"input/config")
 def test_existing_destination_is_rejected(self):
  target=self.base/"copy";target.mkdir()
  with self.assertRaisesRegex(ValueError,"COPY_DESTINATION_EXISTS"):m.independent_copy(self.source,target,self.inspect())
 def test_destination_inside_original_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"COPY_INSIDE_ORIGINAL"):m.independent_copy(self.source,self.source/"copy",self.inspect())
 def test_stale_manifest_raw_byte_change_is_rejected(self):
  before=self.inspect();(self.source/"input/config").write_bytes(b"raw  \n")
  with self.assertRaisesRegex(ValueError,"STALE_SOURCE_BYTES"):m.independent_copy(self.source,self.base/"copy",before)
 def test_same_bytes_replaced_source_inode_is_rejected(self):
  before=self.inspect();replacement=self.source/"input/replacement";replacement.write_bytes(b"raw \n")
  replacement.replace(self.source/"input/config")
  with self.assertRaisesRegex(ValueError,"SOURCE_INODE_CHANGED"):m.independent_copy(self.source,self.base/"copy",before)
 def test_changed_symlink_text_is_rejected(self):
  link=self.source/"alias";link.symlink_to("input/config");before=self.inspect()
  link.unlink();link.symlink_to("input/missing")
  with self.assertRaisesRegex(ValueError,"SOURCE_SYMLINK_CHANGED"):m.independent_copy(self.source,self.base/"copy",before)
 def test_shared_original_hardlink_cannot_pass_byte_equality(self):
  before=self.inspect();target=self.base/"copy";(target/"input").mkdir(parents=True)
  os.link(self.source/"input/config",target/"input/config")
  with self.assertRaisesRegex(ValueError,"SHARED_ORIGINAL_HARDLINK"):m.verify_copy(before,self.inspect(target))
 def test_duplicate_destination_hardlinks_cannot_pass(self):
  (self.source/"input/other").write_bytes(b"raw \n");before=self.inspect()
  target=self.base/"copy";(target/"input").mkdir(parents=True)
  (target/"input/config").write_bytes(b"raw \n");os.link(target/"input/config",target/"input/other")
  with self.assertRaisesRegex(ValueError,"COPIED_FILES_SHARE_HARDLINKS"):m.verify_copy(before,self.inspect(target))
 def test_original_hardlinks_become_independent_destination_files(self):
  os.link(self.source/"input/config",self.source/"input/other")
  before,target,after=self.copied()
  self.assertTrue(m.verify_copy(before,after)["no_copied_regular_file_hardlinks"])
 def test_manifest_path_traversal_is_rejected(self):
  for value in ("../escape","/absolute","input/../escape","input//alias",""):
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,"INVALID_MANIFEST"):m.relative_path(value)
 def test_fresh_output_rejects_existing_path(self):
  target=self.base/"result";target.mkdir()
  with self.assertRaisesRegex(ValueError,"FRESH_EXISTING_PARENT"):m.ensure_fresh_output(target,self.base)
 def test_fresh_output_rejects_symlink_ancestor(self):
  alias=self.base/"alias";alias.symlink_to(self.source)
  with self.assertRaisesRegex(ValueError,"OUTPUT_PARENT_SYMLINK"):m.ensure_fresh_output(alias/"result",self.base)
 def test_fresh_output_rejects_outside_reviewed_parent(self):
  with self.assertRaisesRegex(ValueError,"OUTPUT_OUTSIDE_REVIEW_WORKSPACE"):m.ensure_fresh_output(self.base/"result",self.source)
 def test_fresh_output_rejects_literal_parent_traversal(self):
  with self.assertRaisesRegex(ValueError,"OUTPUT_PATH_TRAVERSAL"):m.ensure_fresh_output(self.source/"../result",self.base)
 def test_new_output_must_have_existing_parent(self):
  with self.assertRaisesRegex(ValueError,"FRESH_EXISTING_PARENT"):m.ensure_fresh_output(self.base/"missing/result",self.base)
 def test_proposal_changes_only_mg5_path_in_separate_bytes(self):
  raw=b"# preserve exact padding  \nother = value \nmg5_path = /old\n"
  candidate,receipt=m.proposed_config(raw,"/old","/new")
  self.assertEqual(candidate,b"# preserve exact padding  \nother = value \nmg5_path = /new\n")
  self.assertFalse(receipt["activated"]);self.assertFalse(receipt["new_baseline_approved"])
  self.assertFalse(receipt["exact_copied_raw_config_modified"])
  self.assertEqual(receipt["historical_writer"],"UNKNOWN")
  self.assertEqual(receipt["changed_setting_keys"],["mg5_path"])
 def test_proposal_wrong_embedded_original_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"EMBEDDED_MG5_PATH"):m.proposed_config(b"mg5_path = /other\n","/old","/new")
 def test_proposal_duplicate_key_is_rejected(self):
  with self.assertRaisesRegex(ValueError,"DUPLICATE_CONFIG_KEY"):m.proposed_config(b"mg5_path = /old\nmg5_path = /old\n","/old","/new")
 def test_proposal_inline_comment_requires_review(self):
  with self.assertRaisesRegex(ValueError,"MG5_PATH_COMMENT"):m.proposed_config(b"mg5_path = /old # keep\n","/old","/new")
 def fixture_policy(self):
  raw=("mg5_path = "+str(self.source)+"\nother = unchanged  \n").encode()
  (self.source/"input/mg5_configuration.txt").write_bytes(raw)
  policy=copy.deepcopy(POLICY);policy.update(source_root=str(self.source),source_resolved_root=str(self.source),allowed_output_parent=str(self.base),
    expected_config={"bytes":len(raw),"sha256":m.digest(raw)},limits=self.limits)
  return raw,policy
 def test_complete_synthetic_prepare_preserves_source_and_raw_config(self):
  raw,policy=self.fixture_policy();before=self.inspect();output=self.base/"execution"
  with patch.object(m,"validate_policy",return_value=True):receipt=m.prepare(self.source,output,policy)
  self.assertEqual(self.inspect(),before)
  copied=Path(receipt["configuration_proposal"]["copied_raw_config_path"])
  self.assertEqual(copied.read_bytes(),raw)
  proposed=Path(receipt["configuration_proposal"]["path"]);self.assertNotEqual(proposed.read_bytes(),raw)
  self.assertTrue(proposed.is_relative_to(output));self.assertFalse(receipt["new_baseline_approved"])
  self.assertEqual(receipt["future_MG5_startup_success"],"UNVERIFIED_NOT_EXECUTED")
  self.assertEqual(receipt["OS_write_confinement_status"],"ROOT_SEPARATE_ENFORCEMENT_REVIEW_REQUIRED")
  self.assertTrue(all(type(receipt[key]) is int and receipt[key]==0 for key in m.COUNTERS))
  self.assertEqual((self.source/"input/mg5_configuration.txt").read_bytes(),raw)
 def test_complete_prepare_rejects_whitespace_drift_before_output_creation(self):
  raw,policy=self.fixture_policy();(self.source/"input/mg5_configuration.txt").write_bytes(raw+b" ")
  output=self.base/"execution"
  with patch.object(m,"validate_policy",return_value=True),self.assertRaisesRegex(ValueError,"STALE_RUNTIME_CONFIG_BASELINE"):
   m.prepare(self.source,output,policy)
  self.assertFalse(output.exists())
 def test_current_policy_has_no_execution_or_new_approval(self):
  self.assertTrue(m.validate_policy(POLICY))
  self.assertFalse(POLICY["parser_executed"]);self.assertIsNone(POLICY["dispatcher"])
 def test_policy_rejects_parser_or_physical_authorization(self):
  for key in ("parser_executed","physical_authorization","new_baseline_approved"):
   bad=copy.deepcopy(POLICY);bad[key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_policy(bad)
 def test_policy_does_not_accept_silently_rebased_raw_hash(self):
  bad=copy.deepcopy(POLICY);bad["expected_config"]["sha256"]="0"*64
  with self.assertRaisesRegex(ValueError,"UNREVIEWED_CONFIG_BASELINE"):m.validate_policy(bad)
 def test_write_new_never_overwrites_existing_file(self):
  target=self.base/"receipt";m.write_new(target,b"first")
  with self.assertRaises(FileExistsError):m.write_new(target,b"second")
  self.assertEqual(target.read_bytes(),b"first")
 def test_write_new_rejects_destination_symlink(self):
  target=self.base/"alias";target.symlink_to(self.source/"input/config")
  with self.assertRaises(FileExistsError):m.write_new(target,b"change")
  self.assertEqual((self.source/"input/config").read_bytes(),b"raw \n")

if __name__=="__main__":unittest.main()
