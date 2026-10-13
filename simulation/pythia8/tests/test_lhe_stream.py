"""Read-only source tests; signed variants are weight API fixtures only.

No mutated fixture is a generated physics reference or enters publication.
All particle four-vectors are copied from the genuine MG5 reference.
"""
import gzip
from pathlib import Path
import re
import sys
import tempfile
import tracemalloc
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/pythia8/scripts"))
import validate_lhe_stream as stream
from validate_lhe import validate_file as legacy_validate


class LHEStreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = REPO / "reference_samples/mg5/pp_bbgg_sm_lo_13tev/reference_1000.lhe.gz"
        cls.data = gzip.decompress(cls.path.read_bytes())

    def test_all_real_input_results_match_existing_validator(self):
        directories = {"bbgg": "pp_bbgg_sm_lo_13tev", "ccgg": "pp_ccgg_sm_lo_13tev", "jjgg": "pp_jjgg_light_sm_lo_13tev"}
        for profile, directory in directories.items():
            path = REPO / "reference_samples/mg5" / directory / "reference_1000.lhe.gz"
            old, new = legacy_validate(path, 1000, profile=profile), stream.validate_lhe_stream(path, profile, stream.REFERENCE_HASHES[profile])
            for key in ("actual_events", "cross_section_pb", "cross_section_uncertainty_pb", "nominal_event_weight",
                        "compressed_file_sha256", "decompressed_file_sha256", "event_content_sha256", "cards", "run_values"):
                self.assertEqual(old[key], new[key], key)
            self.assertTrue(new["known_positive_reference"])

    def test_source_iterator_exact_hashes_and_row_counts(self):
        rows = list(stream.iter_lhe_events(self.path))
        self.assertEqual(len(rows), 1000)
        self.assertEqual([row["source_event_index"] for row in rows], list(range(1, 1001)))
        import hashlib
        joined = hashlib.sha256(b"".join(row["raw"] for row in rows)).hexdigest()
        self.assertEqual(joined, stream.validate_lhe_stream(self.path, "bbgg")["event_content_sha256"])
        self.assertTrue(all(len(row["rows"]) == 7 for row in rows))

    def weight_api_fixture(self, factors):
        cursor = 0
        pattern = rb"(<event>\s*6\s+\d+\s+)(\S+)"
        def replace(match):
            nonlocal cursor
            value = float(match[2]) * factors[cursor % len(factors)]
            cursor += 1
            return match[1] + f"{value:.15e}".encode()
        data = re.sub(pattern, replace, self.data)
        self.assertEqual(cursor, 1000)
        return data

    def test_signed_weight_metadata_api_preserves_moments(self):
        # Alternating -w, +3w retains the original mean. This is an API test,
        # not a claim that this weight assignment was produced by MadGraph.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "API_ONLY_signed_weight_metadata.lhe"
            path.write_bytes(self.weight_api_fixture([-1, 3]))
            result = stream.validate_lhe_stream(path, "bbgg")
            self.assertFalse(result["known_positive_reference"])
            self.assertEqual(result["negative_weight_count"], 500)
            self.assertEqual(result["positive_weight_count"], 500)
            self.assertIsNone(result["nominal_event_weight"])
            self.assertLess(abs(result["weight_normalization_residual_pb"]), result["weight_normalization_tolerance_pb"])
            self.assertGreater(result["weight_moments"]["sum_abs"], result["weight_moments"]["sum"])

    def test_zero_weight_metadata_api_is_preserved_and_counted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "API_ONLY_zero_weight_metadata.lhe"
            path.write_bytes(self.weight_api_fixture([0, 2]))
            result = stream.validate_lhe_stream(path, "bbgg")
            self.assertEqual(result["zero_weight_count"], 500)
            self.assertEqual(result["positive_weight_count"], 500)

    def test_inconsistent_signed_normalization_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "API_ONLY_wrong_normalization.lhe"
            path.write_bytes(self.weight_api_fixture([2]))
            with self.assertRaisesRegex(stream.ValidationError, "mean weight/init"):
                stream.validate_lhe_stream(path, "bbgg")

    def test_known_reference_hash_cannot_be_relabelled(self):
        with self.assertRaisesRegex(stream.ValidationError, "SHA256"):
            stream.validate_lhe_stream(self.path, "bbgg", "0" * 64)

    def test_truncated_and_nonfinite_source_rejected(self):
        for data, message in ((self.data[:-100], "XML"),
                              (self.weight_api_fixture([float("nan")]), "non-finite")):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "invalid_source.lhe"
                path.write_bytes(data)
                with self.assertRaisesRegex(stream.ValidationError, message):
                    stream.validate_lhe_stream(path, "bbgg")

    def test_memory_is_bounded_for_real_source(self):
        tracemalloc.start()
        try:
            stream.validate_lhe_stream(self.path, "bbgg")
            self.assertLess(tracemalloc.get_traced_memory()[1], 4 * 1024**2)
        finally:
            tracemalloc.stop()

    def test_source_files_remain_unchanged(self):
        self.assertEqual(stream.file_sha256(self.path), stream.REFERENCE_HASHES["bbgg"])


if __name__ == "__main__":
    unittest.main()
