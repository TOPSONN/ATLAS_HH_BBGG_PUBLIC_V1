"""Independent tag enumeration and pilot algebra; no new physics samples.

Small invented records below are labelled mathematical/API fixtures. Actual
regressions read the unchanged Phase6D ROOT-derived pilot, retaining all1000
original events per process, including zero-probability events.
"""
import copy
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("phase6e_influence", Path(__file__).resolve().parents[1] / "scripts/influence.py")
influence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(influence)
D = Decimal
PAIRS = ("bb", "bc", "b-light", "cc", "c-light", "light-light")
ORIGINS = ("at_least_two_native_b_tags", "one_native_b_tag_and_nonb_tags", "zero_native_b_tags_and_nonb_tags")


def native_probability(jet):
    """Independent literal pinned formula, evaluated on persisted native PT."""
    pt, flavor = float(jet["pt"]), jet["flavor"]
    if flavor == 5:
        p = .8 * math.tanh(.003 * pt) * 30 / (1 + .086 * pt)
    elif flavor == 4:
        p = .2 * math.tanh(.02 * pt) / (1 + .0034 * pt)
    elif flavor in (0, 1, 2, 3, 21):
        p = .002 + 7.3e-6 * pt
    else:
        raise ValueError("unknown native flavor")
    return D(str(min(1, max(0, p))))


def independent_pair_type(first, second):
    labels = sorted("b" if j["flavor"] == 5 else "c" if j["flavor"] == 4 else "light" for j in (first, second))
    return {("b", "b"): "bb", ("b", "c"): "bc", ("b", "light"): "b-light",
            ("c", "c"): "cc", ("c", "light"): "c-light", ("light", "light"): "light-light"}[tuple(labels)]


def enumerate_tags(jets):
    """Enumerate complete configurations; do not use the production pair DP."""
    jets = sorted(jets, key=lambda j: (-float(j["pt"]), j["index"]))
    with localcontext() as context:
        context.prec = 70
        probabilities = [native_probability(j) for j in jets]
        pairs, origins = {c: D(0) for c in PAIRS}, {c: D(0) for c in ORIGINS}
        total = D(0)
        for bits in itertools.product((False, True), repeat=len(jets)):
            chance = math.prod(p if tagged else 1-p for p, tagged in zip(probabilities, bits))
            indices = [i for i, bit in enumerate(bits) if bit]
            if len(indices) < 2:
                continue
            total += chance
            pairs[independent_pair_type(jets[indices[0]], jets[indices[1]])] += chance
            n_b = sum(jets[i]["flavor"] == 5 for i in indices)
            origins[ORIGINS[0] if n_b >= 2 else ORIGINS[1] if n_b == 1 else ORIGINS[2]] += chance
        return total, pairs, origins


def fixture_records(q, weights=None, indices=None):
    """Synthetic scalar API fixture, never a generated or reference event."""
    weights = weights or ["1"] * len(q)
    indices = indices or list(range(1, len(q)+1))
    return [{"source_event_index": i, "source_event_hash": hashlib.sha256(str(i).encode()).hexdigest(),
             "source_contribution_pb": w, "two_tags": {"q": str(v),
             "leading_pair_types": {c: str(v) if c == "bb" else "0" for c in PAIRS},
             "event_tag_origin_types": {c: str(v) if c == ORIGINS[0] else "0" for c in ORIGINS}}}
            for i, v, w in zip(indices, q, weights)]


class IndependentInfluenceAlgebra(unittest.TestCase):
    def test_six_pair_categories_and_event_origins_by_complete_enumeration(self):
        jets = [{"index": i, "pt": 130-10*i, "flavor": flavor} for i, flavor in enumerate((5, 4, 21, 5, 4, 0))]
        expected, pairs, origins = enumerate_tags(jets)
        result = influence.event_decomposition(list(reversed(jets)))
        self.assertAlmostEqual(float(result["q"]), float(expected), places=14)
        for field, values in (("leading_pair_types", pairs), ("event_tag_origin_types", origins)):
            for category, value in values.items():
                self.assertAlmostEqual(float(result[field][category]), float(value), places=14)
        self.assertTrue(all(value > 0 for value in pairs.values()))

    def test_ineligible_event_has_zero_probability_in_both_partitions(self):
        result = influence.event_decomposition([{"index": 0, "pt": 90, "flavor": 5}, {"index": 1, "pt": 80, "flavor": 5}], False)
        self.assertEqual(result["q"], 0)
        self.assertTrue(all(value == 0 for field in ("leading_pair_types", "event_tag_origin_types") for value in result[field].values()))

    def test_all_source_zeros_and_signed_weight_variance(self):
        rows = fixture_records(["0", ".25", ".75", "1"], ["1", "-1", ".5", "0"], [1, 2, 3, 997])
        result = influence.stage_statistics(rows, "two_tags")
        self.assertEqual(D(result["expected_count"]), D(2))
        self.assertEqual(D(result["expected_cross_section_pb"]), D(".125"))
        self.assertEqual(D(result["conditional_tag_count_variance"]), D(".375"))
        self.assertEqual(D(result["conditional_tag_weighted_variance_pb2"]), D(".234375"))
        # q sample mean=.5, centered squares=.625, N=4; not two eligible jets/events.
        self.assertAlmostEqual(float(result["pilot_probability_mean_variance"]), .625 / 12)
        integrands = [0, -1, 1.5, 0]
        expected = sum((x-.125)**2 for x in integrands) / 12
        self.assertAlmostEqual(float(result["pilot_cross_section_mean_variance_pb2"]), expected)
        for key, summary in (("pilot_probability_mean_variance_contribution", "pilot_probability_mean_variance"),
                             ("pilot_expected_count_variance_contribution", "pilot_expected_count_variance"),
                             ("pilot_cross_section_mean_variance_contribution_pb2", "pilot_cross_section_mean_variance_pb2")):
            self.assertAlmostEqual(sum(float(row["two_tags"][key]) for row in rows), float(result[summary]))

    def test_leave_one_out_preserves_original_weight_denominator(self):
        result = influence.stage_statistics(fixture_records(["0", ".25", ".75", "1"], [".1"]*4, [1, 2, 3, 997]), "two_tags")
        diagnostic = result["leave_one_out_diagnostic"]
        self.assertEqual(D(diagnostic["remaining_fixed_pilot_expected_count"]), D(1))
        self.assertEqual(D(diagnostic["remaining_cross_section_original_N_denominator_pb"]), D(".1"))
        self.assertAlmostEqual(float(diagnostic["remaining_raw_integrand_mean_pb"]), .1*4/3)
        self.assertEqual(result["events_original_independent_sources"], 4)
        self.assertIn("DIAGNOSTIC_ONLY", diagnostic["interpretation"])

    def test_concentration_is_not_independent_source_information(self):
        result = influence.stage_statistics(fixture_records([".001"]*8), "two_tags")
        self.assertEqual(result["events_original_independent_sources"], 8)
        self.assertEqual(result["concentration_ratio"], 8)
        self.assertIsNone(result["pilot_inverse_squared_relative_SE"])
        self.assertLess(result["conditional_tag_inverse_squared_relative_SD"], .01)
        self.assertIn("not a count of independent events", result["concentration_scope"])

    def test_zero_result_has_nullable_concentration_and_retained_N(self):
        result = influence.stage_statistics(fixture_records(["0"]*4), "two_tags")
        self.assertEqual(result["events_original_independent_sources"], 4)
        self.assertIsNone(result["concentration_ratio"])
        self.assertIsNone(result["top5_fraction"])

    def test_unknown_flavor_and_duplicate_native_indices_rejected(self):
        for jets in ([{"index": 0, "pt": 80, "flavor": 6}],
                     [{"index": 0, "pt": 80, "flavor": 5}, {"index": 0, "pt": 60, "flavor": 5}]):
            with self.assertRaises(ValueError):
                influence.event_decomposition(jets)

    def test_invalid_direct_statistical_probabilities_rejected(self):
        for bad in ("-.1", "1.1", "NaN", "Infinity"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                influence.stage_statistics(fixture_records([bad, "0"]), "two_tags")

    def test_nonexclusive_partition_and_duplicate_source_rejected(self):
        rows = fixture_records([".2", ".3"])
        rows[0]["two_tags"]["leading_pair_types"]["bc"] = ".1"
        with self.assertRaises(ValueError):
            influence.stage_statistics(rows, "two_tags")
        rows = fixture_records([".2", ".3"], indices=[997, 997])
        with self.assertRaises(ValueError):
            influence.stage_statistics(rows, "two_tags")

    def test_exclusive_category_covariance_includes_negative_cross_terms(self):
        rows = fixture_records([".5", "1"], ["1", "-2"])
        for row, bb, bc in zip(rows, (".3", ".6"), (".2", ".4")):
            row["two_tags"]["leading_pair_types"].update(bb=bb, bc=bc)
        result = influence.stage_statistics(rows, "two_tags")
        matrices = result["exclusive_category_correlations"]["leading_pair_decomposition"]["matrices"]
        covariance = matrices["conditional_count_covariance"]
        weighted = matrices["conditional_weighted_covariance_pb2"]
        self.assertEqual(D(covariance["bb"]["bb"]), D(".45"))
        self.assertEqual(D(covariance["bc"]["bc"]), D(".4"))
        self.assertEqual(D(covariance["bb"]["bc"]), D("-.3"))
        self.assertEqual(D(weighted["bb"]["bc"]), D("-1.02"))
        self.assertEqual(sum(D(v) for row in covariance.values() for v in row.values()), D(".25"))
        self.assertNotEqual(sum(D(covariance[c][c]) for c in PAIRS), D(result["conditional_tag_count_variance"]))
        pilot = matrices["pilot_probability_mean_covariance"]
        self.assertEqual(D(pilot["bb"]["bc"]), D(".015"))
        self.assertEqual(sum(D(v) for row in pilot.values() for v in row.values()), D(".0625"))


class ActualUnchangedPilotRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.results = {}, {}
        for profile in ("bbgg", "ccgg", "jjgg"):
            path = REPO / "simulation/rare_backgrounds/evidence/pilot" / (profile + ".jsonl")
            cls.rows[profile] = [json.loads(raw, parse_float=D) for raw in path.read_text(encoding="utf-8").splitlines()]
            cls.results[profile] = influence.analyze_profile(cls.rows[profile])

    def test_actual_997_identity_native_labels_and_probability(self):
        row = self.rows["jjgg"][996]
        self.assertEqual(row["source_event_index"], 997)
        self.assertEqual(row["source_event_hash"], "322457dfbd206b7cbd2c243f7b437970b82bb03c38fafe7721e40709f77127b8")
        self.assertEqual(row["input_hepmc_event_hash"], "157928b854ffa4be208b4460338afea8d857446a595a56016c7e8cb994fec31f")
        self.assertEqual(row["source_contribution_pb"], "0.0094365561")
        self.assertEqual([jet["flavor"] for jet in row["jets"]], [5, 2, 21, 21, 5])
        self.assertEqual([jet["btag"] for jet in row["jets"]], [1, 0, 0, 0, 0])
        q, pairs, origins = enumerate_tags(row["jets"])
        actual = self.results["jjgg"]["records"][996]["mgg"]
        self.assertAlmostEqual(float(actual["q"]), .4939102757862776, places=14)
        self.assertAlmostEqual(float(actual["q"]), float(q), places=14)
        for field, expected in (("leading_pair_types", pairs), ("event_tag_origin_types", origins)):
            for category, value in expected.items():
                self.assertAlmostEqual(float(actual[field][category]), float(value), places=14)
        self.assertAlmostEqual(float(pairs["bb"]), .4871049586190675, places=14)
        self.assertEqual(pairs["bc"], 0)

    def test_all3000_exclusive_partitions_against_independent_configurations(self):
        for profile, rows in self.rows.items():
            for row, actual in zip(rows, self.results[profile]["records"]):
                jets = [jet for jet in row["jets"] if float(jet["pt"]) > 25 and abs(float(jet["eta"])) < 2.5]
                q, pairs, origins = enumerate_tags(jets) if row["cut_jets"] else (D(0), {c: D(0) for c in PAIRS}, {c: D(0) for c in ORIGINS})
                for stage, passed in (("two_tags", True), ("mgg", row["m_gamma_gamma"] is not None and 105 <= row["m_gamma_gamma"] <= 160)):
                    self.assertAlmostEqual(float(actual[stage]["q"]), float(q if passed else 0), places=13)
                    for field, expected in (("leading_pair_types", pairs), ("event_tag_origin_types", origins)):
                        for category, value in expected.items():
                            self.assertAlmostEqual(float(actual[stage][field][category]), float(value if passed else 0), places=13)

    def test_authoritative_counts_crosssections_and_variance_sums(self):
        reference = json.loads((REPO / "simulation/rare_backgrounds/evidence/results/analysis.json").read_text())
        for profile, result in self.results.items():
            for stage, summary in result["statistics"].items():
                prior = reference["samples"][profile]["scenarios"]["baseline"][stage]
                self.assertEqual(summary["events_original_independent_sources"], 1000)
                self.assertAlmostEqual(float(summary["expected_count"]), prior["conditional_tag"]["expected_count"], places=11)
                self.assertAlmostEqual(float(summary["expected_cross_section_pb"]), prior["conditional_tag"]["expected_weighted_cross_section_pb"], places=14)
                for partition in ("leading_pair_decomposition", "event_tag_origin_decomposition"):
                    self.assertAlmostEqual(sum(float(v["expected_count"]) for v in summary[partition].values()), float(summary["expected_count"]), places=11)
                    self.assertAlmostEqual(sum(float(v["expected_cross_section_pb"]) for v in summary[partition].values()), float(summary["expected_cross_section_pb"]), places=14)
                self.assertEqual(summary["weight_only_effective_sample_size"], 1000)
        jj = self.results["jjgg"]["statistics"]["mgg"]
        self.assertAlmostEqual(jj["leave_one_out_diagnostic"]["fraction_of_total_expected_count"], .9852106957028898, places=14)
        self.assertEqual(jj["top10_events"][0]["source_event_index"], 997)

    def test_missing_or_repeated_actual_source_is_blocked(self):
        with self.assertRaises(ValueError):
            influence.analyze_profile(self.rows["jjgg"][:-1])
        changed = copy.deepcopy(self.rows["jjgg"])
        changed[996]["source_event_hash"] = changed[995]["source_event_hash"]
        with self.assertRaises(ValueError):
            influence.analyze_profile(changed)

    def test_all3000_partition_covariance_sums_recover_aggregate_uncertainties(self):
        expected_fields = {"conditional_count_covariance": "conditional_tag_count_variance",
                           "conditional_weighted_covariance_pb2": "conditional_tag_weighted_variance_pb2",
                           "pilot_probability_mean_covariance": "pilot_probability_mean_variance",
                           "pilot_cross_section_mean_covariance_pb2": "pilot_cross_section_mean_variance_pb2"}
        for profile, result in self.results.items():
            for stage, summary in result["statistics"].items():
                for partition in summary["exclusive_category_correlations"].values():
                    for field, matrix in partition["matrices"].items():
                        total = sum(float(value) for row in matrix.values() for value in row.values())
                        self.assertAlmostEqual(total, float(summary[expected_fields[field]]), places=11)
                        for a, values in matrix.items():
                            for b, value in values.items():
                                self.assertEqual(value, matrix[b][a])
                        if field == "conditional_count_covariance":
                            self.assertGreater(sum(float(matrix[c][c]) for c in matrix), total)


if __name__ == "__main__":
    unittest.main()
