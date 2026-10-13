"""Scientific reporting boundary tests; no generated detector/physics records."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import summarize_btags as statistics


class StatisticalBoundaries(unittest.TestCase):
    def test_no_denominator_is_unknown_and_zero_tags_have_positive_upper_bound(self):
        self.assertIsNone(statistics.interval(0, 0))
        lower, upper = statistics.interval(0, 793)
        self.assertEqual(lower, 0)
        self.assertAlmostEqual(upper, 0.004820857120536111, places=15)

    def test_small_expected_mistag_count_remains_insufficient_even_with_many_jets(self):
        group = {"eligible_reco_jets": 686, "tagged_bit0": 1, "probabilities": [0.002] * 686}
        result = statistics.finish(group, "light")
        self.assertEqual(result["statistics_status"], "INSUFFICIENT_STATISTICS")
        self.assertGreater(result["wilson95"][1], result["observed_fraction"])

    def test_boundary_goes_to_next_bin_and_eta_endpoint_is_outside(self):
        self.assertEqual(statistics.bin_number(50, statistics.PT_EDGES), 1)
        self.assertEqual(statistics.bin_number(200, statistics.PT_EDGES), 3)
        self.assertEqual(statistics.bin_number(0.8, statistics.ETA_EDGES), 1)
        with self.assertRaises(ValueError):
            statistics.bin_number(2.5, statistics.ETA_EDGES)


if __name__ == "__main__":
    unittest.main()
