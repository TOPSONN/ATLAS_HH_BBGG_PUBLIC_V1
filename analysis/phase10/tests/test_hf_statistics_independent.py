"""Tiny covariance/mask fixtures only; full existing-data audit belongs to root ledger."""
import copy
import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "independent_hf_statistics", Path(__file__).resolve().parents[1]/"scripts/validate_hf_statistics.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class IndependentHFStatistics(unittest.TestCase):
    def event(self):
        origin = {"hard_outgoing_pdg_ids": [5, -5, 22, 22],
                  "heavy_flavour": {"shower_bottom_births": 0, "shower_charm_births": 1,
                                    "direct_gluon_splitting_count": 1,
                                    "jets": [{"heavy_hadron_flavour": 5}]}}
        native = {"eligible_jets": [{"flavour": 5, "native_btag_bits": 1},
                                    {"flavour": 5, "native_btag_bits": 1}]}
        return origin, native

    def test_native_two_jets_still_one_source_flag(self):
        a, b = self.event()
        flags = m.independent_masks(a, b)
        self.assertIs(flags["NATIVE_TAGS_GE2"], True)
        self.assertIs(flags["HAS_NATIVE_BOTTOM_JET"], True)

    def test_native_bit0_is_literal(self):
        a, b = self.event()
        for jet in b["eligible_jets"]:
            jet["native_btag_bits"] = 2
        self.assertTrue(m.independent_masks(a, b)["NATIVE_TAGS_0"])

    def test_ME_not_replaced_by_shower_origin(self):
        a, b = self.event()
        flags = m.independent_masks(a, b)
        self.assertTrue(flags["ME_BOTTOM"])
        self.assertTrue(flags["HAS_SHOWER_CHARM_BIRTH"])
        self.assertFalse(flags["ME_CHARM"])

    def test_origin_flags_are_nonexclusive(self):
        a, b = self.event()
        flags = m.independent_masks(a, b)
        self.assertTrue(flags["HAS_DIRECT_G_TO_HEAVY_PAIR"])
        self.assertTrue(flags["HAS_SHOWER_CHARM_BIRTH"])
        self.assertTrue(flags["HAS_HEAVY_HADRON_ELIGIBLE_JET"])

    def test_massless_light_ME_native_heavy_is_preserved(self):
        a, b = self.event()
        a["hard_outgoing_pdg_ids"] = [21, 2, 22, 22]
        flags = m.independent_masks(a, b)
        self.assertTrue(flags["ME_LIGHT_OR_GLUON"])
        self.assertTrue(flags["HAS_NATIVE_BOTTOM_JET"])

    def test_mutually_exclusive_masks_have_negative_covariance(self):
        self.assertEqual(m.covariance_from_moments(4, 2, 2, 0), Fraction(-4, 3))

    def test_diagonal_uses_all_original_trials(self):
        self.assertEqual(m.covariance_from_moments(4, 2, 2, 2), Fraction(4, 3))

    def test_constant_source_flag_has_zero_covariance(self):
        self.assertEqual(m.covariance_from_moments(4, 4, 2, 2), 0)

    def test_shared_source_ratio_covariance(self):
        self.assertEqual(m.ratio_variance(10, 2, 2, 5, 5), Fraction(4, 75))

    def test_empty_stratum_ratio_undefined(self):
        self.assertIsNone(m.ratio_variance(10, 0, 0, 0, 0))

    def test_zero_events_not_zero_original_N(self):
        self.assertEqual(m.covariance_from_moments(1000, 0, 0, 0), 0)
        with self.assertRaises(ValueError):
            m.covariance_from_moments(1, 0, 0, 0)

    def test_nonfinite_and_boolean_weights_rejected(self):
        for x in ("NaN", "Infinity", False):
            with self.assertRaises(ValueError):
                m.frac(x)


if __name__ == "__main__":
    unittest.main()
