"""Small method fixtures; does not execute the full precision audit."""
import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "independent_precision", Path(__file__).resolve().parents[1] / "scripts/validate_precision.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class IndependentPrecisionFixtures(unittest.TestCase):
    def test_b02_plugin_is_exact(self):
        self.assertEqual(m.acceptance_requirement(Fraction(1, 1000), ".2"), 24975)

    def test_b02_bessel_rate_is_distinct(self):
        self.assertEqual(m.rate_requirement(1000, 1, 1, ".2"), 25000)

    def test_zero_survivor_has_no_finite_measured_plan(self):
        self.assertIsNone(m.acceptance_requirement(0, ".2"))
        self.assertIsNone(m.rate_requirement(1000, 0, 0, ".2"))

    def test_zero_variance_is_undefined_plan(self):
        self.assertIsNone(m.rate_requirement(1000, 1, 0, ".2"))

    def test_ESS_proxy_does_not_create_new_sources(self):
        self.assertEqual(m.ess_requirement(1000, 1, ".2"), 25000)
        self.assertIsNone(m.ess_requirement(1000, None, ".2"))

    def test_Bessel_covariance_cancellation(self):
        self.assertEqual(m.moment_variance(1000, 1, 1), Fraction(1))

    def test_bin_total_delta_covariance(self):
        self.assertEqual(m.normalized_variance(10, 2, 2, 5, 5), Fraction(4, 75))

    def test_full_fraction_has_zero_empirical_variance(self):
        self.assertEqual(m.normalized_variance(10, 5, 5, 5, 5), 0)

    def test_undefined_total_has_no_shape(self):
        self.assertIsNone(m.normalized_variance(10, 0, 0, 0, 0))

    def test_negative_weights_preserve_squared_rate(self):
        self.assertEqual(m.rate_requirement(1000, -1, 1, ".2"), 25000)

    def test_nonfinite_and_boolean_rejected(self):
        for x in ("NaN", "Infinity", True):
            with self.assertRaises(ValueError):
                m.rational(x)

    def test_bad_target_and_ESS_rejected(self):
        for x in (0, 1, -1):
            with self.assertRaises(ValueError):
                m.acceptance_requirement(".1", x)
        with self.assertRaises(ValueError):
            m.ess_requirement(1000, 1001, ".2")


if __name__ == "__main__":
    unittest.main()
