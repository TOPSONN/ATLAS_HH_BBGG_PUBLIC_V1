"""Independent exhaustive numerical fixtures; no MC or detector execution."""
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/conditional_tags.py"
spec = importlib.util.spec_from_file_location("conditional_tags", SCRIPT)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def enumeration(probabilities):
    with localcontext() as context:
        context.prec = 80
        tail, pairs = Decimal(0), {}
        for tags in itertools.product((False, True), repeat=len(probabilities)):
            probability = Decimal(1)
            selected = []
            for index, (tagged, p) in enumerate(zip(tags, probabilities)):
                probability *= p if tagged else 1 - p
                if tagged:
                    selected.append(index)
            if len(selected) >= 2:
                tail += probability
                pair = tuple(selected[:2])
                pairs[pair] = pairs.get(pair, Decimal(0)) + probability
        return tail, pairs


def jet(index=0, pt=60, eta=0.2, phi=0, flavor=5, tag=0, mass=5):
    return {"index": index, "pt": pt, "eta": eta, "phi": phi, "mass": mass,
            "flavor": flavor, "btag": tag}


def photon(index=0, pt=60, eta=.1, phi=0):
    return {"index": index, "pt": pt, "eta": eta, "phi": phi, "mass": 0}


def event(ordinal=1, weight="0.001", pass_cuts=True):
    return {"ordinal": ordinal, "native_event_number": ordinal, "source_event_index": ordinal,
            "source_event_hash": hashlib.sha256(f"LHE{ordinal}".encode()).hexdigest(),
            "input_hepmc_event_hash": hashlib.sha256(f"HepMC{ordinal}".encode()).hexdigest(),
            "source_contribution_pb": weight,
            "photons": [photon(0), photon(1, 55, -.1, 3)] if pass_cuts else [],
            "jets": [jet(0, tag=1), jet(1, 55, -.2, 3, tag=1)],
            "N_jets": 2, "N_btags": 2,
            "m_gamma_gamma": 125 if pass_cuts else None,
            "cut_photons": pass_cuts, "cut_jets": pass_cuts,
            "cut_two_btags": pass_cuts, "cut_mgg": pass_cuts}


class ProbabilityTests(unittest.TestCase):
    def test_dp_exhaustive_heterogeneous_cases(self):
        for inputs in ([], [".5"], ["0", "1", ".3"], [".1", ".2", ".8", ".005"], ["1", "1", "1"]):
            p = list(map(Decimal, inputs))
            expected, _ = enumeration(p)
            self.assertLessEqual(abs(model.probability_at_least_two(p) - expected), Decimal("1e-48"))

    def test_rare_tail_does_not_cancel(self):
        self.assertEqual(model.probability_at_least_two(["1e-100", "1e-100"]), Decimal("1e-200"))
        self.assertEqual(1.0 - (1.0 - 1e-30)**2 - 2e-30*(1.0 - 1e-30), -2e-30)

    def test_deterministic_tags(self):
        self.assertEqual(model.probability_at_least_two([0, 1, 0, 1]), 1)
        self.assertEqual(model.leading_pair_probabilities([0, 1, 0, 1]), [(1, 3, Decimal(1))])

    def test_invalid_probability_rejected(self):
        for bad in (-.1, 1.1, "NaN", "Infinity", True):
            with self.assertRaises(ValueError):
                model.probability_at_least_two([bad])

    def test_leading_pairs_independent_enumeration(self):
        p = list(map(Decimal, (".1", ".8", ".03", ".2", "1")))
        expected_tail, expected_pairs = enumeration(p)
        actual = {(a, b): value for a, b, value in model.leading_pair_probabilities(p)}
        for pair, value in expected_pairs.items():
            self.assertLessEqual(abs(actual.get(pair, Decimal(0)) - value), Decimal("1e-48"))
        self.assertLessEqual(abs(sum(actual.values()) - expected_tail), Decimal("1e-48"))

    def test_formulas_and_toy_clipping(self):
        import math
        self.assertEqual(model.tag_probability(5, 60), Decimal(str(.80*math.tanh(.003*60)*(30/(1+.086*60)))))
        self.assertEqual(model.tag_probability(4, 60), Decimal(str(.20*math.tanh(.02*60)*(1/(1+.0034*60)))))
        self.assertEqual(model.tag_probability(21, 60), Decimal(str(.002+7.3e-06*60)))
        p = model.tag_probability_details(0, 200000, model.SCENARIOS["light_up20"])
        self.assertEqual(p["probability"], 1)
        self.assertTrue(p["clipped"])
        for invalid in (-4, 6, 22, True, 5.0):
            with self.assertRaises(ValueError):
                model.tag_probability(invalid, 60)

    def test_empty_pair_moments_nullable(self):
        result = model.leading_pair_moments([jet(), jet(1)], [], [0, 0])
        self.assertEqual(result["probability"], 0)
        self.assertIsNone(result["conditional_mean_mbb"])
        self.assertIsNone(result["conditional_mean_mbbgg"])

    def test_pair_moments_include_unobserved_combinations(self):
        jets = [jet(0, 90, .1, 0), jet(1, 70, .4, 1), jet(2, 50, -.7, 3)]
        probabilities = list(map(Decimal, (".4", ".7", ".2")))
        tail, pairs = enumeration(probabilities)
        result = model.leading_pair_moments(jets, [photon(), photon(1, 55, -.1, 3)], probabilities)
        expected = sum(value * Decimal(str(model.combined_mass([model.p4(jets[a]), model.p4(jets[b])])))
                       for (a, b), value in pairs.items())
        self.assertLessEqual(abs(result["mbb_first"] - expected), Decimal("1e-24"))
        self.assertLessEqual(abs(result["conditional_mean_mbb"] - expected / tail), Decimal("1e-24"))
        observed_only = model.combined_mass([model.p4(jets[0]), model.p4(jets[1])])
        self.assertNotAlmostEqual(float(result["conditional_mean_mbb"]), observed_only)


class EventTests(unittest.TestCase):
    def test_all_source_rows_retained_signed_weight_and_zero_probability(self):
        result = model.analyze_event(event(weight="-0.000000000123456789012345678901", pass_cuts=False))
        self.assertEqual(result["source_contribution_pb"], "-1.23456789012345678901E-10")
        self.assertEqual(result["source_count"], 1000)
        self.assertFalse(result["observed_two_tags"])
        self.assertTrue(all(Decimal(row["stage_two_tags_probability"]) == 0 for row in result["scenarios"].values()))

    def test_frozen_selection_boundaries(self):
        self.assertFalse(model.jet_eligible(jet(pt=25)))
        self.assertFalse(model.jet_eligible(jet(eta=2.5)))
        self.assertFalse(model.photon_eligible(photon(pt=25)))
        self.assertFalse(model.photon_eligible(photon(eta=2.37)))
        self.assertTrue(model.photon_eligible(photon(eta=1.37)))
        self.assertFalse(model.photon_eligible(photon(eta=1.4)))
        self.assertTrue(model.photon_eligible(photon(eta=1.52)))
        row = event()
        row["photons"][0]["pt"] = row["photons"][1]["pt"] = 35
        with self.assertRaisesRegex(ValueError, "cut_photons"):
            model.analyze_event(row)

    def test_tag_independent_mgg_inclusive_limits(self):
        for mass in (105, 160):
            row = event()
            row["m_gamma_gamma"] = mass
            self.assertTrue(model.analyze_event(row)["tag_independent_mgg"])
        row = event()
        row["m_gamma_gamma"] = "160.00000001"
        row["cut_mgg"] = False
        result = model.analyze_event(row)
        self.assertGreater(Decimal(result["scenarios"]["baseline"]["stage_two_tags_probability"]), 0)
        self.assertEqual(Decimal(result["scenarios"]["baseline"]["stage_mgg_probability"]), 0)

    def test_persisted_flavor_and_observed_bit0_used(self):
        row = event()
        row["jets"][0]["flavor"] = 4
        row["jets"][1]["flavor"] = 21
        result = model.analyze_event(row)
        expected = model.tag_probability(4, 60)*model.tag_probability(21, 55)
        self.assertLessEqual(abs(Decimal(result["scenarios"]["baseline"]["stage_two_tags_probability"]) - expected), Decimal("1e-28"))
        self.assertTrue(result["observed_two_tags"])
        row["jets"][1]["btag"] = 2
        with self.assertRaisesRegex(ValueError, "tagging bits"):
            model.analyze_event(row)

    def test_source_identity_duplicate_and_missing_rows_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"rows.jsonl"
            rows = [event(1), event(2)]
            path.write_text("".join(json.dumps(row)+"\n" for row in rows))
            self.assertEqual(len(list(model.iter_analysis_events(path, source_count=2))), 2)
            rows[1]["source_event_hash"] = rows[0]["source_event_hash"]
            path.write_text("".join(json.dumps(row)+"\n" for row in rows))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                list(model.iter_analysis_events(path, source_count=2))
            path.write_text(json.dumps(rows[0])+"\n")
            with self.assertRaisesRegex(ValueError, "every original"):
                list(model.iter_analysis_events(path, source_count=2))

    def test_overwrite_and_binding_hash_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            path, binding_path, output = (Path(temp)/name for name in ("rows.jsonl", "binding.json", "result"))
            path.write_text(json.dumps(event())+"\n")
            binding = {"schema_version":1, "process":"bbgg", "events":1000, "normalization_denominator":1000,
                       "verification_status":"PASS", "verification_scope":"actual_ROOT_native_source_card_full_file_hash",
                       "canonical_card_sha256":model.CARD_SHA256, "runtime_card_sha256":model.CARD_SHA256,
                       "reco_sha256":"0"*64, "root_sha256":"0"*64, "native_report_sha256":"0"*64,
                       "native_scientific_content_sha256":"0"*64, "source_mg5_sha256":"0"*64,
                       "source_pythia_run_id":"NUMERICAL_FIXTURE_ONLY"}
            binding_path.write_text(json.dumps(binding))
            with self.assertRaisesRegex(ValueError, "input SHA256"):
                model.analyze_file(path, binding_path, output)
            self.assertFalse(output.exists())
            binding["reco_sha256"] = model.file_sha256(path)
            binding_path.write_text(json.dumps(binding))
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "already exists"):
                model.analyze_file(path, binding_path, output)

    def test_full_file_signed_contributions_without_selected_renormalization(self):
        # Numerical fixtures only: these invented binding hashes do not claim a
        # physical ROOT verification, and this test executes no detector run.
        with tempfile.TemporaryDirectory() as temp:
            path, binding_path, output = (Path(temp)/name for name in ("rows.jsonl", "binding.json", "result"))
            rows = [event(index, weight=(".003" if index == 1 else "-.004" if index == 2 else ".001"),
                          pass_cuts=index <= 2) for index in range(1, 1001)]
            path.write_text("".join(json.dumps(row)+"\n" for row in rows))
            binding = {"schema_version":1, "process":"bbgg", "events":1000, "normalization_denominator":1000,
                       "verification_status":"PASS", "verification_scope":"actual_ROOT_native_source_card_full_file_hash",
                       "canonical_card_sha256":model.CARD_SHA256, "runtime_card_sha256":model.CARD_SHA256,
                       "reco_sha256":model.file_sha256(path), "root_sha256":"0"*64, "native_report_sha256":"0"*64,
                       "native_scientific_content_sha256":"0"*64, "source_mg5_sha256":"0"*64,
                       "source_pythia_run_id":"NUMERICAL_FIXTURE_ONLY"}
            binding_path.write_text(json.dumps(binding))
            summary = model.analyze_file(path, binding_path, output)
            self.assertEqual(summary["counts"]["events"], 1000)
            self.assertEqual(summary["counts"]["observed_two_tags"], 2)
            self.assertEqual(Decimal(summary["weight_sum_pb"]), Decimal(".997"))
            self.assertEqual(summary["negative_source_weights"], 1)
            with localcontext() as context:
                context.prec = model.PRECISION
                q = model.probability_at_least_two([model.tag_probability(5, 60), model.tag_probability(5, 55)])
                weighted = Decimal(summary["results"]["baseline"]["two_tags"]["weighted_cross_section_pb"])
                self.assertLessEqual(abs(weighted - Decimal("-.001")*q), Decimal("1e-49"))
            records = (output/"conditional_events.jsonl").read_text().splitlines()
            self.assertEqual(len(records), 1000)
            self.assertEqual(json.loads(records[-1])["scenarios"]["baseline"]["stage_two_tags_probability"], "0")
            self.assertLess((output/"conditional_events.jsonl").stat().st_size, 5*1024**2)
            self.assertEqual(model.file_sha256(path), binding["reco_sha256"])


if __name__ == "__main__":
    unittest.main()
