#!/usr/bin/env python3
"""SYNTHETIC_METHOD_TEST: independent readback integrity gates, no ROOT input."""
import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import independent_validation as validation
from postprocess import groups


def cohort(dataset="METHOD_A", n=3):
    return [
        {
            "dataset_id": dataset,
            "source_event_ordinal": ordinal,
            "N_original": n,
            "source_event_sha256": f"{ordinal:064x}",
            "source_weight_pb": 1.0,
            "stages": [True] * 5,
            "observables": {"method_x": 0.25},
            "test_evidence_class": "SYNTHETIC_METHOD_TEST",
        }
        for ordinal in range(1, n + 1)
    ]


class FullSourceIntegrity(unittest.TestCase):
    def test_complete_cohort_retains_original_n(self):
        actual = groups(cohort())
        self.assertEqual([r["source_event_ordinal"] for r in actual["METHOD_A"]], [1, 2, 3])
        self.assertTrue(all(r["N_original"] == 3 for r in actual["METHOD_A"]))

    def test_full_cohort_order_is_restored_explicitly(self):
        rows = list(reversed(cohort()))
        self.assertEqual([r["source_event_ordinal"] for r in groups(rows)["METHOD_A"]], [1, 2, 3])

    def test_truncated_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_DUPLICATE_COHORT"):
            groups(cohort()[:-1])

    def test_duplicate_ordinal_replacing_source_is_rejected(self):
        rows = cohort()
        rows[-1] = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_DUPLICATE_COHORT"):
            groups(rows)

    def test_later_row_cannot_change_original_n(self):
        rows = cohort()
        rows[-1]["N_original"] = 1000
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_DUPLICATE_COHORT"):
            groups(rows)

    def test_boolean_source_ordinal_is_not_integer_identity(self):
        rows = cohort()
        rows[0]["source_event_ordinal"] = True
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_DUPLICATE_COHORT"):
            groups(rows)


class PrefixIntegrity(unittest.TestCase):
    def setUp(self):
        self.full = groups(cohort("METHOD_A") + cohort("METHOD_B"))
        self.prefix = copy.deepcopy(self.full["METHOD_A"] + self.full["METHOD_B"])

    def test_complete_prefix_adds_no_independent_sources(self):
        result = validation.check_prefix(self.full, self.prefix)
        self.assertEqual(result["actual_prefix_entries_read"], 6)
        self.assertEqual(result["additional_independent_sources"], 0)
        self.assertEqual(result["evidence_class"], "REFERENCE_PREFIX_TEST")

    def test_missing_dataset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "PREFIX_MISSING_DATASET"):
            validation.check_prefix(self.full, self.prefix[:3])

    def test_missing_last_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "PREFIX_TRUNCATED_COHORT"):
            validation.check_prefix(self.full, self.prefix[:-1])

    def test_duplicate_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PREFIX_SOURCE"):
            validation.check_prefix(self.full, self.prefix + [self.prefix[0]])

    def test_unknown_dataset_is_rejected(self):
        self.prefix[0]["dataset_id"] = "UNKNOWN_METHOD_SOURCE"
        with self.assertRaisesRegex(ValueError, "UNKNOWN_PREFIX_DATASET"):
            validation.check_prefix(self.full, self.prefix)

    def test_prefix_source_content_is_compared(self):
        self.prefix[0]["observables"]["method_x"] = 0.5
        with self.assertRaisesRegex(ValueError, "ACTUAL_PREFIX_FULL_EVENT_CONTENT_MISMATCH"):
            validation.check_prefix(self.full, self.prefix)

    def test_prefix_original_n_cannot_be_renormalized(self):
        self.prefix[0]["N_original"] = 100
        with self.assertRaisesRegex(ValueError, "ACTUAL_PREFIX_FULL_EVENT_CONTENT_MISMATCH"):
            validation.check_prefix(self.full, self.prefix)

    def test_first_100_is_bound_to_same_full_cohort(self):
        full = groups(cohort(n=103))
        result = validation.check_prefix(full, copy.deepcopy(full["METHOD_A"][:100]))
        self.assertEqual(result["actual_prefix_entries_read"], 100)
        self.assertEqual(full["METHOD_A"][0]["N_original"], 103)

    def test_ordinal_101_cannot_enter_first_100_prefix(self):
        full = groups(cohort(n=103))
        rows = copy.deepcopy(full["METHOD_A"][:100])
        rows[-1] = copy.deepcopy(full["METHOD_A"][100])
        with self.assertRaisesRegex(ValueError, "PREFIX_ORDINAL_OUT_OF_RANGE"):
            validation.check_prefix(full, rows)

    def test_boolean_prefix_ordinal_is_rejected(self):
        self.prefix[0]["source_event_ordinal"] = True
        with self.assertRaises(ValueError):
            validation.check_prefix(self.full, self.prefix)


class HistogramCellIntegrity(unittest.TestCase):
    def setUp(self):
        self.key = ("METHOD_A", "INPUT", "method_x", "SOURCE_WEIGHTED")
        self.records = {self.key: {"status": "DEFINED", "dimension": 1,
                                   "x_edges": [0.0, 1.0, 2.0], "y_edges": []}}
        self.seen = {self.key: {(0,), (1,), (2,), (3,)}}

    def test_1d_regular_and_both_flows_are_required(self):
        validation.validate_histogram_cells(self.records, self.seen)

    def test_entire_histogram_missing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS"):
            validation.validate_histogram_cells(self.records, {})

    def test_missing_overflow_is_rejected(self):
        self.seen[self.key].remove((3,))
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS"):
            validation.validate_histogram_cells(self.records, self.seen)

    def test_extra_out_of_range_cell_is_rejected(self):
        self.seen[self.key].add((4,))
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS"):
            validation.validate_histogram_cells(self.records, self.seen)

    def test_2d_all_flow_corners_are_required(self):
        self.records[self.key] = {"status": "DEFINED", "dimension": 2,
                                  "x_edges": [0.0, 1.0], "y_edges": [-1.0, 0.0, 1.0]}
        self.seen[self.key] = {(x, y) for x in range(3) for y in range(4)}
        validation.validate_histogram_cells(self.records, self.seen)
        self.seen[self.key].remove((0, 3))
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS"):
            validation.validate_histogram_cells(self.records, self.seen)

    def test_undefined_shape_has_no_invented_cells(self):
        self.records[self.key]["status"] = "UNDEFINED_ILL_CONDITIONED_OR_EMPTY_SHAPE"
        validation.validate_histogram_cells(self.records, {})
        with self.assertRaisesRegex(ValueError, "UNDEFINED_HISTOGRAM_HAS_CELLS"):
            validation.validate_histogram_cells(self.records, self.seen)


class HistogramCSVIntegrity(unittest.TestCase):
    """Exercise the real CSV parser using a tiny generic synthetic observable."""
    modes = ["RAW_EVENT_COUNTS", "SOURCE_WEIGHTED", "UNIT_AREA_SHAPE",
             "EXPLORATORY_LUMINOSITY_YIELD"]
    fields = ["dataset_id", "stage", "observable", "normalization_mode", "dimension",
              "bin_x", "bin_y", "content", "sumw2"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="phase8_method_readback_")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "phase8_histograms.csv"
        self.events = cohort(n=2)
        self.manifest = {"METHOD_A": {"N_original": 2, "model_br_factor": 0.001}}
        self.edges = {"observables": {"method_x": {"edges": [0.0, 1.0]}}}
        self.hmanifest = []
        self.rows = []
        for stage in validation.STAGES:
            for mode in self.modes:
                self.hmanifest.append({"dataset_id": "METHOD_A", "stage": stage,
                    "observable": "method_x", "normalization_mode": mode,
                    "status": "DEFINED", "dimension": 1, "x_edges": [0.0, 1.0],
                    "y_edges": [], "missing_count": 0, "invalid_count": 0})
                factor = 0.5 if mode == "UNIT_AREA_SHAPE" else 100.0 if mode == "EXPLORATORY_LUMINOSITY_YIELD" else 1.0
                for cell in range(3):
                    self.rows.append({"dataset_id": "METHOD_A", "stage": stage,
                        "observable": "method_x", "normalization_mode": mode,
                        "dimension": 1, "bin_x": cell, "bin_y": 0,
                        "content": 2.0 * factor if cell == 1 else 0.0,
                        "sumw2": 2.0 * factor * factor if cell == 1 else 0.0})

    def write(self):
        with self.path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, self.fields)
            writer.writeheader()
            writer.writerows(self.rows)
        (self.path.parent / "phase8_histogram_manifest.json").write_text(
            json.dumps({"histograms": self.hmanifest}), encoding="utf-8")

    def check(self):
        with mock.patch.object(validation, "PAIRS", {}):
            return validation.check_histograms(self.events, self.manifest, self.path, self.edges)

    def test_complete_csv_validates_all_60_cells(self):
        self.write()
        self.assertEqual(self.check()["csv_rows_checked"], 60)

    def test_absent_csv_file_is_rejected(self):
        self.write()
        self.path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.check()

    def test_header_only_csv_is_rejected(self):
        self.rows = []
        self.write()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS"):
            self.check()

    def test_truncated_csv_is_rejected(self):
        self.rows.pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS"):
            self.check()

    def test_duplicate_csv_cell_is_rejected_before_set_deduplication(self):
        self.rows.append(copy.deepcopy(self.rows[0]))
        self.write()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_HISTOGRAM_CSV_CELL"):
            self.check()

    def test_missing_histogram_manifest_entry_is_rejected(self):
        self.hmanifest.pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_HISTOGRAM_MANIFEST"):
            self.check()

    def test_duplicate_histogram_manifest_entry_is_rejected(self):
        self.hmanifest.append(copy.deepcopy(self.hmanifest[0]))
        self.write()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_HISTOGRAM_MANIFEST_ID"):
            self.check()

    def test_wrong_histogram_content_is_rejected(self):
        self.rows[1]["content"] = 100.0
        self.write()
        with self.assertRaisesRegex(ValueError, "HISTOGRAM_CONTENT"):
            self.check()

    def test_wrong_sumw2_is_rejected(self):
        self.rows[1]["sumw2"] = 100.0
        self.write()
        with self.assertRaisesRegex(ValueError, "HISTOGRAM_SUMW2"):
            self.check()


if __name__ == "__main__":
    print("Evidence class: SYNTHETIC_METHOD_TEST; physical ROOT events read: 0", flush=True)
    unittest.main(verbosity=2)
