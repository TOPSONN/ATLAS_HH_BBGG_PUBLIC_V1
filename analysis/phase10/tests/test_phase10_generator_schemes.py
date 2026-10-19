import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis/phase10/source"))
from generator_schemes import inactive_card_errors, validate_pilot_contract, validate_scheme_review


class GeneratorContractTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads((ROOT / "metadata/phase10_generator_scheme_review.json").read_text())
        self.contract = json.loads((ROOT / "analysis/phase10/config/generator_pilot_contract.json").read_text())

    def validate(self):
        return validate_pilot_contract(self.contract, self.review, ROOT)

    def test_complete_matrix_preserves_unvalidated_status(self):
        self.assertEqual([], validate_scheme_review(self.review))
        self.assertIsNone(self.review["recommended_matching_candidate"])

    def test_inactive_contract_is_structurally_valid_and_blocked(self):
        result = self.validate()
        self.assertTrue(result["valid_inactive_contract"], result)
        self.assertFalse(result["execution_authorized"])
        self.assertGreater(len(result["blocking_conditions"]), 5)

    def test_no_generic_matching_claim(self):
        self.review["matching_prescription_status"] = "VALIDATED"
        self.assertIn("UNSUPPORTED_MATCHING_PRESCRIPTION", self.validate()["errors"])

    def test_reject_false_exact_process_validation(self):
        self.review["schemes"][0]["exact_process_validated"] = True
        self.assertTrue(any("UNSUPPORTED_EXACT_PROCESS" in x for x in self.validate()["errors"]))

    def test_reject_premature_recommendation(self):
        self.review["recommended_matching_candidate"] = "B_5F_MLM"
        self.assertIn("UNSUPPORTED_MATCHING_RECOMMENDATION", self.validate()["errors"])

    def test_reject_numeric_merging_scale(self):
        for key in ("xqcut_gev", "qcut_gev", "merging_tms_gev", "fxfx_qcut_me_gev"):
            with self.subTest(key=key):
                trial = copy.deepcopy(self.contract)
                trial["matching"][key] = 20.0
                result = validate_pilot_contract(trial, self.review, ROOT)
                self.assertIn("UNVALIDATED_NUMERIC_MERGING_SCALE", result["errors"])

    def test_reject_production_activation(self):
        self.contract["instantiable"] = True
        self.contract["execution_authorized"] = True
        self.assertIn("PHYSICAL_PRODUCTION_FORBIDDEN", self.validate()["errors"])

    def test_reject_missing_blocker(self):
        self.contract["blockers"].remove("PDF_ALPHA_S_NOT_FROZEN")
        self.assertIn("MISSING_PHYSICAL_BLOCKERS", self.validate()["errors"])

    def test_reject_event_counter(self):
        self.contract["actual_new_production"]["new_hard_events"] = 1
        self.assertIn("NONZERO_OR_MISSING_PHYSICAL_COUNTERS", self.validate()["errors"])

    def test_reject_boolean_event_counter(self):
        self.contract["actual_new_production"]["new_hard_events"] = False
        self.assertIn("NONZERO_OR_MISSING_PHYSICAL_COUNTERS", self.validate()["errors"])

    def test_reject_infinite_resource_ceiling(self):
        self.contract["resource_planning"]["illustrative_ceiling"]["wall_seconds"] = float("inf")
        self.assertIn("NONFINITE_RESOURCE_WALL_SECONDS", self.validate()["errors"])

    def test_reject_fake_human_approval(self):
        self.contract["independent_human_review_receipt"] = "invented"
        self.assertIn("HUMAN_APPROVAL_NOT_OBSERVED", self.validate()["errors"])

    def test_reject_guaranteed_statistics(self):
        self.contract["precision_objectives"]["guaranteed_precision"] = True
        self.assertIn("UNSUPPORTED_PRECISION_GUARANTEE", self.validate()["errors"])

    def test_reject_active_card_lines(self):
        text = "# FUTURE_UNEXECUTED_PROPOSAL DO_NOT_EXECUTE\ngenerate p p > a a"
        self.assertIn("ACTIVE_CARD_CONTENT", inactive_card_errors(text, "x.inactive.txt"))

    def test_reject_active_card_extension(self):
        self.assertIn("ACTIVE_CARD_EXTENSION", inactive_card_errors("# DO_NOT_EXECUTE", "x.mg5"))

    def test_no_dispatcher(self):
        self.contract["dispatcher"] = "anything"
        self.assertIn("GENERATOR_DISPATCHER_FORBIDDEN", self.validate()["errors"])

    def test_existing_output_receipt_cannot_be_overwritten(self):
        import importlib.util
        import tempfile
        from unittest import mock
        spec = importlib.util.spec_from_file_location(
            "pilot_cli_fixture", ROOT / "analysis/phase10/scripts/validate_pilot_contract.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory(prefix="phase10_receipt_fixture_") as folder:
            output = Path(folder) / "existing_receipt.json"
            output.write_text("KEEP_EXACT_EXISTING_RECEIPT")
            with mock.patch.object(sys, "argv", ["validate_pilot_contract.py", "--output", str(output)]):
                with self.assertRaises(FileExistsError):
                    cli.main()
            self.assertEqual(output.read_text(), "KEEP_EXACT_EXISTING_RECEIPT")

    def test_source_identity(self):
        self.contract["base_revision"] = "0" * 40
        self.assertIn("BASE_REVISION_MISMATCH", self.validate()["errors"])

    def test_fxfx_born_bb_inapplicable(self):
        row = next(x for x in self.review["schemes"] if x["id"] == "B_FXFX_BB_CORE")
        self.assertEqual("INAPPLICABLE", row["scientific_verdict"])
        self.assertIn("MG_FXFX", row["source_evidence"])


if __name__ == "__main__":
    unittest.main()
