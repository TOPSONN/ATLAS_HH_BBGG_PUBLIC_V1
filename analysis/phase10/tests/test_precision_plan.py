import importlib.util
from decimal import Decimal
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('precision',Path(__file__).resolve().parents[1]/'source/precision.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PrecisionGuards(unittest.TestCase):
    """SYNTHETIC_METHOD_ONLY: exact planning arithmetic and missing-support guards."""
    def test_b02_preserves_historical_totalN_assumption(self):
        for r,n in [('0.10',99900),('0.20',24975),('0.30',11100),('0.50',3996)]:self.assertEqual(m.acceptance_exact_counts(1,1000,r),n)
    def test_total_not_additional_events(self):self.assertEqual(m.acceptance_exact_counts(143,1000,'.10'),600)
    def test_rate_Bessel_distinct_from_Bernoulli_plugin(self):self.assertEqual(m.variance_n(1000,1,1,'.20'),25000)
    def test_constant_BR_factor_cancels_relative_plan(self):self.assertEqual(m.variance_n(1000,2,4,'.2'),m.variance_n(1000,1,1,'.2'))
    def test_zero_survivor_no_finite_measured_requirement(self):
        p=m.acceptance_plan(0,1000,0,'.0036820838968657545','.2');self.assertIsNone(p['N_total_acceptance_point']);self.assertIsNone(p['N_total_CP95_lower_p_conservative']);self.assertFalse(p['guaranteed_precision'])
    def test_CP_envelope_wide_for_singleton(self):
        p=m.acceptance_plan(1,1000,'.000025317487491291883','.005558924279825132','.2');self.assertLess(p['N_total_CP95_upper_p_optimistic'],24975);self.assertGreater(p['N_total_CP95_lower_p_conservative'],24975)
    def test_weight_zero_estimate_undefined(self):self.assertIsNone(m.variance_n(1000,0,1,'.2'))
    def test_degenerate_empirical_variance_not_zero_true_error(self):self.assertIsNone(m.variance_n(1000,1,0,'.2'))
    def test_empty_ESS_does_not_become_zero_rate(self):self.assertIsNone(m.ess_scaled_n(1000,None,'.2'))
    def test_ESS_scaling_is_only_conditional_proxy(self):self.assertEqual(m.ess_scaled_n(1000,1,'.2'),25000)
    def test_originalN_is_used_for_kappa_final(self):
        self.assertAlmostEqual(float(m.kappa_relative_variance(1000,10)),99/999,places=14)
    def test_no_density_inferred_from_histogram(self):
        p=m.mixture_contract();self.assertFalse(p['proposal_densities_known']);self.assertFalse(p['support_validated']);self.assertFalse(p['physical_execution_authorized'])
    def test_nonfinite_rejected(self):
        for x in ['NaN','Infinity','-Infinity']:
            with self.assertRaises(ValueError):m.acceptance_n(x,'.2')
    def test_targets_strict_between_zero_and_one(self):
        for x in [0,1,-1,2]:
            with self.assertRaises(ValueError):m.acceptance_n('.1',x)
    def test_negative_acceptance_rejected(self):
        with self.assertRaises(ValueError):m.acceptance_n('-.1','.2')
    def test_inverted_interval_rejected(self):
        with self.assertRaises(ValueError):m.acceptance_plan(1,1000,'.1','.01','.2')
    def test_boolean_counts_rejected(self):
        for args in [(True,1000),(1,True)]:
            with self.assertRaises(ValueError):m.acceptance_exact_counts(*args,'.2')
    def test_negative_variance_rejected(self):
        with self.assertRaises(ValueError):m.variance_n(1000,1,-1,'.2')
    def test_invalid_ESS_rejected(self):
        for x in [0,-1,1001]:
            with self.assertRaises(ValueError):m.kappa_relative_variance(1000,x)
    def test_precision_is_not_physical_normalization(self):
        p=m.mixture_contract();self.assertIn('Using unknown nuisance values as zero',p['forbidden_shortcuts'])
if __name__=='__main__':unittest.main()