#!/usr/bin/env python3
"""SYNTHETIC_METHOD_TEST: strict frozen-source and fail-closed provenance rules."""
import copy, importlib.util, json, math, tempfile, unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/audit_inputs.py"
spec = importlib.util.spec_from_file_location("phase8_audit_inputs", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def index(self, count=2, change=None):
        lines = ["ATLAS_DELPHES_INPUT_V1"]
        for i in range(1, count + 1):
            row = ["E", str(i), str(i), "a" * 64, str(i), "b" * 64, "1", "2", "2", "1", "1"]
            if change: change(i, row)
            lines.extend([" ".join(row), "W 1", "P 1 22 1 1 0 0 1 0 0 0 0 0 0"])
        path = self.root / "index.dat";path.write_text("\n".join(lines) + "\n");return path
    def test_valid_full_index(self):
        result, rows = audit.audit_index(self.index(), 2, 2)
        self.assertEqual(result["actual_index_events"], 2);self.assertEqual(len(rows), 2)
        self.assertIn("PENDING_NATIVE",result["status"])
    def test_duplicate_source_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "EVENT_IDENTITY"):
            audit.audit_index(self.index(change=lambda i,r:r.__setitem__(4,"1") if i==2 else None),2,2)
    def test_duplicate_native_number_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "duplicate"):
            audit.audit_index(self.index(change=lambda i,r:r.__setitem__(2,"1") if i==2 else None),2,2)
    def test_missing_source_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "truncated/prefix"):
            audit.audit_index(self.index(count=1),2,2)
    def test_original_denominator_preserved(self):
        with self.assertRaisesRegex(audit.AuditError, "denominator"):
            audit.audit_index(self.index(),2,10)
    def test_nonfinite_weight_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "nonfinite"):
            audit.audit_index(self.index(change=lambda i,r:r.__setitem__(6,"nan")),2,2)
    def test_bad_nominal_vector_rejected(self):
        path=self.index();path.write_text(path.read_text().replace("W 1", "W 2",1))
        with self.assertRaisesRegex(audit.AuditError, "nominal-vector"):
            audit.audit_index(path,2,2)
    def test_truncated_particle_rejected(self):
        path=self.index();path.write_text(path.read_text().rsplit("P ",1)[0])
        with self.assertRaisesRegex(audit.AuditError,"truncated P"):
            audit.audit_index(path,2,2)
    def test_hash_mismatch_rejected(self):
        path=self.root/"file";path.write_bytes(b"verified bytes")
        with self.assertRaisesRegex(audit.AuditError, "HASH_MISMATCH"):
            audit.check_file("root",path,"0"*64)
    def test_missing_file_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "MISSING_DATA"):
            audit.check_file("root",self.root/"absent","0"*64)
    def test_unknown_alias_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "unknown portable"):
            audit.resolve_path("/arbitrary/private/root",self.root,self.root)
    def test_traversal_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "unsafe"):
            audit.resolve_path("LOCAL_HOME/../escape",self.root,self.root)
    def test_wrong_sample_version_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "wrong sample version"):
            audit.audit_manifest({"sample_version":"WRONG"},self.root,self.root)
    def test_unknown_dataset_rejected(self):
        with self.assertRaisesRegex(audit.AuditError, "unknown"):
            audit.audit_manifest({"sample_version":audit.VERSION,"base_revision":audit.BASE,"datasets":[{"dataset_id":"UNKNOWN"}]},self.root,self.root)
    def test_snapshot_preservation_failure(self):
        path=self.root/"source";path.write_bytes(b"original")
        receipt={"files":[{"path":str(path),"sha256":audit.digest(path),"bytes":8,"dataset_id":"TEST","role":"SOURCE"}]}
        self.assertEqual(audit.verify_snapshot(receipt)["files_verified"],1)
        path.write_bytes(b"modified")
        with self.assertRaisesRegex(audit.AuditError,"preservation"):
            audit.verify_snapshot(receipt)
    def test_no_overwrite(self):
        path=self.root/"receipt.json";audit.write_new(path,{"test":True})
        with self.assertRaises(FileExistsError):audit.write_new(path,{"test":False})
    def test_lhe_index_weight_closure(self):
        _,rows=audit.audit_index(self.index(),2,2)
        path=self.root/"source.lhe";path.write_text('<LesHouchesEvents><event>\n1 1 2 1 1 1\n</event><event>\n1 1 2 1 1 1\n</event></LesHouchesEvents>')
        self.assertEqual(audit.audit_lhe(path,2,rows)["events"],2)
        path.write_text(path.read_text().replace("1 1 2", "1 1 3",1))
        with self.assertRaisesRegex(audit.AuditError,"raw weight"):
            audit.audit_lhe(path,2,rows)

class BackgroundContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=MODULE.with_name("background_contract.py")
        spec=importlib.util.spec_from_file_location("phase8_background_contract",path)
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
        config=MODULE.parents[1]/"config/datasets.json"
        cls.contract=cls.module.build_background_contract(json.loads(config.read_text()))
    def test_all_background_pairs_keep_physical_gate(self):
        self.assertEqual(len(self.contract["pairs"]),15)
        self.assertTrue(all(not p["safe_for_physical_addition"] for p in self.contract["pairs"]))
    def test_continuum_three_pairs_not_exclusive(self):
        pairs=[p for p in self.contract["pairs"] if p["status"]=="POTENTIAL_DOUBLE_COUNTING"]
        self.assertEqual(len(pairs),3);self.assertTrue(all(not p["validated_exclusive"] for p in pairs))
    def test_fake_rate_unknown_is_null(self):
        value=self.module.fake_photon_readiness()
        self.assertIsNone(value["numerical_fake_rate"])
        self.assertFalse(value["zero_selected_events_implies_zero_background"])
    def test_missing_background_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing"):
            self.module.build_background_contract({"datasets":[]})

if __name__ == "__main__":
    unittest.main(verbosity=2)
