"""Analytic/API fixtures only; no generated physics events or calibrations."""
import importlib.util
import math
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "rare_background_statistics",
    Path(__file__).resolve().parents[1] / "scripts/statistics.py",
)
stats = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stats)


class StatisticalMethods(unittest.TestCase):
    def test_fixed_heterogeneous_tag_moments(self):
        result = stats.analyze_values(["0.1", "0.2", "0"], ["2", "2", "2"], 0)
        self.assertAlmostEqual(result["conditional_tag"]["expected_count"], .3)
        self.assertAlmostEqual(result["conditional_tag"]["count_variance"], .25)
        self.assertAlmostEqual(result["conditional_tag"]["weighted_variance_pb2"], 1)

    def test_signed_weights_change_mean_not_positive_variance(self):
        result = stats.analyze_values(["0.2", "0.8"], ["1", "-1"], 0)
        self.assertAlmostEqual(result["conditional_tag"]["expected_weighted_cross_section_pb"], -.6)
        self.assertAlmostEqual(result["conditional_tag"]["weighted_variance_pb2"], .32)
        self.assertEqual(result["exact_observed_interval"]["status"], "NOT_APPLICABLE")

    def test_unequal_positive_weights_do_not_receive_binomial_yield_interval(self):
        result = stats.analyze_values([.2, .3], [1, 2], 1)
        self.assertEqual(result["exact_observed_interval"]["status"], "NOT_APPLICABLE")

    def test_all_source_denominator_includes_ineligible_zeros(self):
        result = stats.analyze_values([0, 0, 0, 1], [.25] * 4, 1)
        self.assertEqual(result["source_event_pilot"]["probability_mean"], .25)
        self.assertAlmostEqual(result["source_event_pilot"]["unbiased_event_sample_variance_q"], .25)
        self.assertAlmostEqual(result["source_event_pilot"]["probability_mean_standard_error"], .25)
        self.assertAlmostEqual(result["source_event_pilot"]["cross_section_mean_standard_error_pb"], .25)

    def test_conditional_prediction_and_mean_standard_error_differ(self):
        result = stats.analyze_values([.2] * 10, [.1] * 10, 2)
        self.assertEqual(result["source_event_pilot"]["probability_mean_standard_error"], 0)
        self.assertAlmostEqual(result["conditional_tag"]["count_variance"], 1.6)

    def test_total_variance_identity(self):
        result = stats.analyze_values([0, .2, .8, 1], [.25] * 4, 2)
        law = result["law_total_variance"]
        self.assertAlmostEqual(law["sum_components"], law["marginal_bernoulli_mean_one_minus_mean"])
        self.assertAlmostEqual(law["empirical_population_variance_q"], .17)
        self.assertAlmostEqual(law["mean_q_one_minus_q"], .08)

    def test_direct_poisson_binomial_known_distribution(self):
        result = stats.poisson_binomial([.2, .7], 1)
        for actual, expected in zip(result["pmf"], [.24, .62, .14]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(result["probability_zero"], .24)
        self.assertAlmostEqual(result["probability_observed_count"], .62)
        self.assertAlmostEqual(result["probability_at_most_observed"], .86)

    def test_poisson_binomial_deterministic_endpoints(self):
        result = stats.poisson_binomial([0, 1, 1], 2)
        self.assertEqual(result["pmf"], [0, 0, 1, 0])
        self.assertEqual(result["predictive_interval"]["equal_tail_discrete_bounds"], [2, 2])
        self.assertIsNone(result["log_probability_zero"])

    def test_zero_probability_uses_log_product(self):
        result = stats.poisson_binomial([1e-6] * 1000, 0)
        self.assertAlmostEqual(result["probability_zero"], math.exp(1000 * math.log1p(-1e-6)), places=14)
        self.assertAlmostEqual(result["pmf"][0], result["probability_zero"], places=12)
        self.assertGreaterEqual(result["predictive_interval"]["actual_coverage"], .95)

    def test_clopper_pearson_zero_exact_closed_forms(self):
        result = stats.clopper_pearson(0, 1000)
        self.assertEqual(result["two_sided_equal_tail"][0], 0)
        self.assertAlmostEqual(result["two_sided_equal_tail"][1], -math.expm1(math.log(.025) / 1000), places=15)
        self.assertAlmostEqual(result["one_sided_upper"], -math.expm1(math.log(.05) / 1000), places=15)
        self.assertLess(result["one_sided_upper"], result["two_sided_equal_tail"][1])

    def test_clopper_pearson_two_trial_one_success_identity(self):
        result = stats.clopper_pearson(1, 2)
        self.assertAlmostEqual(result["two_sided_equal_tail"][0], 1 - math.sqrt(.975), places=13)
        self.assertAlmostEqual(result["two_sided_equal_tail"][1], math.sqrt(.975), places=13)

    def test_clopper_pearson_nist_example(self):
        # NIST primary-source 4/20, 90% example: 0.071354 and 0.401029.
        result = stats.clopper_pearson(4, 20, .90)
        self.assertAlmostEqual(result["two_sided_equal_tail"][0], .071354, delta=1e-6)
        self.assertAlmostEqual(result["two_sided_equal_tail"][1], .401029, delta=1e-6)
        # Independent factorial enumeration verifies the inversion more tightly
        # than the rounded handbook example.
        lower, upper = result["two_sided_equal_tail"]
        sf = sum(math.comb(20, k) * lower ** k * (1 - lower) ** (20-k)
                 for k in range(4, 21))
        cdf = sum(math.comb(20, k) * upper ** k * (1 - upper) ** (20-k)
                  for k in range(5))
        self.assertAlmostEqual(sf, .05, places=13)
        self.assertAlmostEqual(cdf, .05, places=13)

    def test_clopper_pearson_all_success_endpoint(self):
        result = stats.clopper_pearson(5, 5)
        self.assertAlmostEqual(result["two_sided_equal_tail"][0], .025 ** .2, places=13)
        self.assertEqual(result["two_sided_equal_tail"][1], 1)

    def test_zero_observed_forecast_unbounded_and_upper_not_guarantee(self):
        result = stats.analyze_values([.001] * 1000, [.01] * 1000, 0)
        conservative = result["forecasts"]["conservative_observed_lower_bound"]
        self.assertTrue(all(row["events"] is None for row in conservative))
        detection = result["forecasts"]["zero_detection"]
        self.assertIsNone(detection["conditional_sufficient_events_at_lower_rate"])
        self.assertEqual(detection["optimistic_minimum_at_upper_rate_events"], 1000)

    def test_precision_z_and_relative_targets_are_distinct(self):
        one = stats.relative_precision_forecast(.01, .20)
        ci = stats.relative_precision_forecast(.01, .20, stats.Z95)
        ten = stats.relative_precision_forecast(.01, .10)
        self.assertEqual(one["events"], 2475)
        self.assertGreater(ci["events"], one["events"] * 3.8)
        self.assertEqual(ten["events"], one["events"] * 4)

    def test_analytic_mean_forecast_is_not_tag_count_forecast(self):
        result = stats.analyze_values([.01] * 10, [.1] * 10, 0)
        self.assertEqual(result["forecasts"]["model_assisted_analytic_q_mean"][0]["events"], 1)
        self.assertEqual(result["forecasts"]["model_assisted_mean_rate"][0]["events"], 2475)

    def test_nested_stages_same_event_covariance(self):
        result = stats.nested_stage_covariance([.2, .8], [0, .8], [1, -1])
        self.assertAlmostEqual(result["conditional_count_covariance"], .16)
        self.assertAlmostEqual(result["conditional_weighted_covariance_pb2"], .16)
        self.assertAlmostEqual(result["pilot_event_sample_covariance"], .24)
        self.assertAlmostEqual(result["empirical_total_per_event_covariance"], .2)
        self.assertAlmostEqual(result["marginal_nested_identity"], .2)

    def test_invalid_inputs_rejected(self):
        for values in ([-.01, .2], [.2, 1.01], [.2, "NaN"], [True, .2]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                stats.analyze_values(values, [1, 1], 0)
        with self.assertRaises(ValueError):
            stats.analyze_values([0, .1], [1, 1], 0, source_count=1000)
        with self.assertRaises(ValueError):
            stats.nested_stage_covariance([.2, .3], [.3, .3], [1, 1])

    def test_schema_retains_all_events_and_blocks_duplicate_source(self):
        rows = [{
            "ordinal": i, "source_count": 4, "source_event_index": i,
            "source_contribution_pb": ".25", "cut_jets": i == 4,
            "observed_two_tags": i == 4,
            "scenarios": {"baseline": {"stage_two_tags_probability": "1" if i == 4 else "0"}},
        } for i in range(1, 5)]
        result = stats.analyze_stage(rows, "stage_two_tags_probability", "observed_two_tags",
                                     expected_events=4, source_count=4)
        self.assertEqual(result["events_all_source"], 4)
        self.assertEqual(result["conditional_tag"]["expected_count"], 1)
        rows[2]["source_event_index"] = 1
        with self.assertRaises(ValueError):
            stats.analyze_stage(rows, "stage_two_tags_probability", "observed_two_tags",
                                expected_events=4, source_count=4)


if __name__ == "__main__":
    unittest.main()
