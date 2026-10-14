"""Synthetic BR algebra and exact candidate-command controls only.

Values in these tests are invented probabilities, not SM BR predictions.
Tests do not install/import MG5, integrate, decay or generate physics events.
"""
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, REPO / "simulation/heavy_flavour_forensics/scripts" / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


higgs = module("phase6e_higgs_contract", "higgs_contract.py")
cards = module("phase6e_process_cards", "parse_process_cards.py")


def factor(name, br, multiplicity=1):
    return {"decay_id": name, "branching_ratio": br, "multiplicity": multiplicity}


class ExactlyOnceBranchingRatios(unittest.TestCase):
    def test_synthetic_stable_higgs_forced_decay_factor_once(self):
        self.assertEqual(higgs.normalization_factor([factor("H_to_gamma_gamma", ".002")]), Decimal(".002"))
        self.assertEqual(higgs.normalization_factor([factor("top_to_bW", ".9", 2), factor("H_to_gamma_gamma", ".002")]), Decimal(".00162"))

    def test_exclusive_matrix_element_channel_already_in_source(self):
        self.assertEqual(higgs.normalization_factor([], source_included_decays=["H_to_gamma_gamma"]), 1)
        with self.assertRaises(ValueError):
            higgs.normalization_factor([factor("H_to_gamma_gamma", ".002")], source_included_decays=["H_to_gamma_gamma"])

    def test_applied_or_duplicate_decay_rejected(self):
        for kwargs in ({"already_applied_decays": ["H_to_gamma_gamma"]},
                       {"source_included_decays": ["H_to_gamma_gamma"], "already_applied_decays": ["H_to_gamma_gamma"]}):
            with self.assertRaises(ValueError):
                higgs.normalization_factor([factor("H_to_gamma_gamma", ".002")], **kwargs)
        with self.assertRaises(ValueError):
            higgs.normalization_factor([factor("H_to_gamma_gamma", ".002"), factor("H_to_gamma_gamma", ".002")])

    def test_external_forcing_requires_explicit_closure_evidence_gate(self):
        with self.assertRaises(ValueError):
            higgs.normalization_factor([factor("H_to_gamma_gamma", ".002")], external_forced_decay=True)
        self.assertEqual(higgs.normalization_factor([factor("H_to_gamma_gamma", ".002")], external_forced_decay=True,
                                                  external_weight_closure_verified=True), Decimal(".002"))
        # True is API-only acknowledgement, never a physical closure receipt.

    def test_nonboolean_closure_and_union_flags_rejected(self):
        for invalid in ("UNKNOWN", "False", 1, None):
            for flag in ("external_forced_decay", "external_weight_closure_verified"):
                with self.subTest(flag=flag, invalid=invalid), self.assertRaises(ValueError):
                    higgs.normalization_factor([], **{flag: invalid})
            with self.assertRaises(ValueError):
                higgs.semileptonic_w_factor(".1", ".6", channel_scope="ONE_CHARGE_ASSIGNMENT", source_includes_charge_union=invalid)

    def test_unknown_nonfinite_or_invalid_probability_rejected(self):
        for invalid in ("UNKNOWN", "NaN", "Infinity", "-.01", "1.01", True, .002):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                higgs.normalization_factor([factor("H_to_gamma_gamma", invalid)])

    def test_endpoints_and_multiplicity(self):
        self.assertEqual(higgs.normalization_factor([factor("x", "0", 2)]), 0)
        self.assertEqual(higgs.normalization_factor([factor("x", "1", 3)]), 1)
        for invalid in (0, -1, True, 1.5, "2"):
            with self.assertRaises(ValueError):
                higgs.normalization_factor([factor("x", ".5", invalid)])

    def test_invalid_decay_ledgers_and_factor_shape_rejected(self):
        for invalid in ("H_to_gamma_gamma", [""], [" H_to_gamma_gamma"], ["x", "x"], [1]):
            for name in ("source_included_decays", "already_applied_decays"):
                with self.subTest(name=name, invalid=invalid), self.assertRaises(ValueError):
                    higgs.normalization_factor([], **{name: invalid})
        for invalid in ({"decay_id": "x", "branching_ratio": ".1"}, factor("", ".1"), {**factor("x", ".1"), "width": ".1"}):
            with self.assertRaises(ValueError):
                higgs.normalization_factor([invalid])

    def test_synthetic_semileptonic_charge_union_applied_once(self):
        self.assertEqual(higgs.semileptonic_w_factor(".1", ".6", channel_scope="ONE_CHARGE_ASSIGNMENT"), Decimal(".06"))
        self.assertEqual(higgs.semileptonic_w_factor(".1", ".6", channel_scope="BOTH_CHARGE_ASSIGNMENTS"), Decimal(".12"))
        with self.assertRaises(ValueError):
            higgs.semileptonic_w_factor(".1", ".6", channel_scope="BOTH_CHARGE_ASSIGNMENTS", source_includes_charge_union=True)
        for scope in ("UNKNOWN", "INCLUSIVE"):
            with self.assertRaises(ValueError):
                higgs.semileptonic_w_factor(".1", ".6", channel_scope=scope)

    def test_inconsistent_exclusive_w_branching_ratios_rejected(self):
        with self.assertRaises(ValueError):
            higgs.semileptonic_w_factor("1", "1", channel_scope="BOTH_CHARGE_ASSIGNMENTS")
        self.assertEqual(higgs.semileptonic_w_factor(".5", ".5", channel_scope="BOTH_CHARGE_ASSIGNMENTS"), Decimal(".5"))


class ReviewedCandidateCommands(unittest.TestCase):
    def test_exact_original_candidates_and_coupling_bounds(self):
        expected = {"bb_gamma_j": "generate p p > b b~ a j4 QCD=3 QED=1",
                    "tth": "generate p p > t t~ h QCD=2 QED=1", "zh": "generate p p > z h QCD=0 QED=2"}
        for name, command in expected.items():
            path = REPO / "simulation/mg5/cards" / (name + "_candidate.mg5")
            parsed = cards.commands(path, name)
            self.assertEqual(parsed[-1], command)
            self.assertEqual(parsed[0], "import model sm-no_b_mass")
            self.assertEqual(parsed[1], "define p = g u c d s b u~ c~ d~ s~ b~")

    def test_no_generation_or_unreviewed_physics_commands(self):
        base = cards.reviewed_commands("bb_gamma_j")
        for lines in ([*base, "launch"], [*base, "output generated"], [*base, "compute_widths h"],
                      [*base, "import command injected.mg5"], [*base, "! echo injected"],
                      [base[0].replace("sm-no_b_mass", "heft"), *base[1:]],
                      [*base[:-1], base[-1].replace("QCD=3", "QCD=4")],
                      [base[0], base[1], base[2].replace("d~ s~", "d~ s~ b b~"), base[3]]):
            with tempfile.TemporaryDirectory(prefix="phase6e_api_only_", dir=REPO) as directory:
                path = Path(directory) / "API_ONLY.mg5"
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    cards.commands(path, "bb_gamma_j")

    def test_stable_higgs_and_explicit_one_charge_decay_scope(self):
        self.assertNotIn("h >", cards.reviewed_commands("tth")[-1])
        self.assertNotIn("h >", cards.reviewed_commands("zh")[-1])
        chain = cards.reviewed_commands("tth_semileptonic_e_one_charge")[-1]
        self.assertIn("w+ > e+ ve", chain)
        self.assertIn("w- > j4 j4", chain)
        self.assertNotIn("e-", chain)
        self.assertEqual(cards.reviewed_commands("ordinary_sm_higgs_diphoton_negative")[-1], "generate h > a a")

    def test_actual_parse_receipt_commands_card_hashes_and_amplitude_orders(self):
        receipt = json.loads((REPO / "simulation/heavy_flavour_forensics/evidence/process_parse.json").read_text())
        expected = {"bb_gamma_j": {"QCD": 3, "QED": 1}, "tth": {"QCD": 2, "QED": 1}, "zh": {"QCD": 0, "QED": 2}}
        for descriptor in receipt["cards"]:
            self.assertEqual(hashlib.sha256((REPO / descriptor["path"]).read_bytes()).hexdigest(), descriptor["sha256"])
        for check in receipt["checks"]:
            self.assertEqual(check["commands"], cards.reviewed_commands(check["id"]))
            self.assertEqual(check["physical_events"], 0)
            if check["id"] in expected:
                self.assertGreater(check["record_count"], 0)
                for amplitude in check["amplitude_records"]:
                    self.assertGreater(amplitude["diagram_count"], 0)
                    self.assertEqual(amplitude["actual_amplitude_orders"], [expected[check["id"]]])

    def test_actual_parse_receipt_does_not_claim_higgs_physics(self):
        receipt = json.loads((REPO / "simulation/heavy_flavour_forensics/evidence/process_parse.json").read_text())
        self.assertEqual(receipt["status"], "PASS_PARSE_ONLY")
        self.assertEqual(receipt["events_generated"], 0)
        self.assertFalse(receipt["output_or_launch_executed"])
        self.assertEqual(receipt["physical_cross_sections_branching_ratios_and_decay_closure"], "NOT_EVALUATED")
        negative = next(c for c in receipt["checks"] if c["id"] == "ordinary_sm_higgs_diphoton_negative")
        self.assertEqual(negative["status"], "PASS_EXPECTED_NO_TREE_DIAGRAMS")


if __name__ == "__main__":
    unittest.main()
