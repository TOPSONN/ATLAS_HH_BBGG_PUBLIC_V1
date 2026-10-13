#!/usr/bin/env python3
"""Native adversarial readback tests derived only from an actual detector run.

Set DELPHES_NATIVE_TEST_RUN, DELPHES_ANALYZER, DELPHES_LIBRARY and optionally
DELPHES_NATIVE_TEST_EVIDENCE. No detector execution or accepted fake physics
reference is created. Derived corruptions are explicitly failure fixtures.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid


@unittest.skipUnless(
    all(os.environ.get(k) for k in (
        "DELPHES_NATIVE_TEST_RUN", "DELPHES_ANALYZER", "DELPHES_LIBRARY")),
    "requires real native ROOT environment and an actual detector run",
)
class NativeReadbackFailures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ROOT
        cls.ROOT = ROOT
        if ROOT.gSystem.Load(os.environ["DELPHES_LIBRARY"]) < 0:
            raise RuntimeError("verified Delphes dictionary could not load")
        cls.source_run = Path(os.environ["DELPHES_NATIVE_TEST_RUN"])
        cls.analyzer = os.environ["DELPHES_ANALYZER"]
        cls.evidence = Path(os.environ.get(
            "DELPHES_NATIVE_TEST_EVIDENCE", tempfile.gettempdir()
        )) / ("native-failure-fixtures-" + uuid.uuid4().hex)
        cls.evidence.mkdir(parents=True, exist_ok=False)
        source = ROOT.TFile.Open(str(cls.source_run / "detector.root"), "READ")
        if not source or source.IsZombie():
            raise RuntimeError("actual detector source ROOT is unavailable")
        cls.count = int(source.Get("Delphes").GetEntries())
        if cls.count < 2:
            raise RuntimeError("at least two actual detector records required")
        source.Close()

    def directory(self):
        path = self.evidence / self._testMethodName
        path.mkdir()
        return path

    def analyze(self, directory, *, root=None, index=None, truth=None):
        command = [
            self.analyzer, "--input", str(root or self.source_run / "detector.root"),
            "--input-index", str(index or self.source_run / "input_event_index.dat"),
            "--truth-index", str(truth or self.source_run / "truth_analysis_index.dat"),
            "--card", str(self.source_run / "detector_card.tcl"), "--process", "bbgg",
            "--events", str(self.count),
            "--summary", str(directory / "native_validation.json"),
            "--events-jsonl", str(directory / "reco_events.jsonl"),
            "--cutflow", str(directory / "cutflow.csv"),
            "--efficiencies", str(directory / "efficiencies.csv"),
        ]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=60)
        (directory / "stdout.txt").write_text(completed.stdout)
        (directory / "stderr.txt").write_text(completed.stderr)
        report = json.loads((directory / "native_validation.json").read_text())
        self.assertEqual(completed.returncode == 0, report["validation_status"] == "PASS")
        return report

    def corrupted_index(self, directory, marker, field, value):
        lines = (self.source_run / "input_event_index.dat").read_text().splitlines()
        for i, line in enumerate(lines):
            parts = line.split()
            if parts and parts[0] == marker:
                parts[field] = value
                lines[i] = " ".join(parts)
                break
        else:
            raise RuntimeError("actual source index lacks required record")
        path = directory / "corrupted_input_index.dat"
        path.write_text("\n".join(lines) + "\n")
        return path

    def root_copy(self, directory, *, entries=None, missing=None, nan=False):
        source = self.ROOT.TFile.Open(str(self.source_run / "detector.root"), "READ")
        tree = source.Get("Delphes")
        if missing:
            tree.SetBranchStatus(missing + "*", 0)
        path = directory / "derived_failure_fixture.root"
        target = self.ROOT.TFile.Open(str(path), "RECREATE")
        clone = tree.CloneTree(0)
        corrupted = False
        for i in range(self.count if entries is None else entries):
            tree.GetEntry(i)
            if nan and not corrupted and tree.Photon.GetEntriesFast():
                tree.Photon.At(0).PT = float("nan")
                corrupted = True
            clone.Fill()
        if nan and not corrupted:
            raise RuntimeError("actual source had no photon for NaN failure fixture")
        clone.Write()
        target.Close()
        source.Close()
        return path

    def assert_failure(self, report, text):
        self.assertEqual(report["validation_status"], "FAIL")
        self.assertIn(text, report["error"])
        self.assertEqual(report["N_output"], self.count)
        self.assertEqual(report["N_processed"], 0)

    def test_actual_unmodified_readback(self):
        report = self.analyze(self.directory())
        self.assertEqual(report["validation_status"], "PASS")
        for key in ("N_input", "N_read", "N_processed", "N_output"):
            self.assertEqual(report[key], self.count)
        self.assertEqual(report["N_invalid"], 0)

    def test_event_identity_corruption(self):
        directory = self.directory()
        index = self.corrupted_index(directory, "E", 2, "987654321")
        report = self.analyze(directory, index=index)
        self.assert_failure(report, "identity")
        self.assertEqual(report["N_invalid"], 1)

    def test_particle_momentum_corruption(self):
        directory = self.directory()
        index = self.corrupted_index(directory, "P", 4, "123.125")
        report = self.analyze(directory, index=index)
        self.assert_failure(report, "multiset")
        self.assertEqual(report["N_read"], 1)

    def test_particle_position_corruption(self):
        directory = self.directory()
        index = self.corrupted_index(directory, "P", 10, "1.125")
        report = self.analyze(directory, index=index)
        self.assert_failure(report, "multiset")

    def test_secondary_weight_corruption(self):
        directory = self.directory()
        index = self.corrupted_index(directory, "W", 2, "123.125")
        report = self.analyze(directory, index=index)
        self.assert_failure(report, "Weight vector")

    def test_nonfinite_actual_branch_corruption(self):
        directory = self.directory()
        root = self.root_copy(directory, nan=True)
        report = self.analyze(directory, root=root)
        self.assert_failure(report, "non-finite")
        self.assertEqual(report["N_invalid"], 1)

    def test_missing_required_branch(self):
        directory = self.directory()
        root = self.root_copy(directory, missing="Photon")
        report = self.analyze(directory, root=root)
        self.assert_failure(report, "required Delphes branch")
        self.assertEqual(report["N_read"], 0)

    def test_short_tree_preserves_actual_output_and_assessment_counts(self):
        directory = self.directory()
        root = self.root_copy(directory, entries=self.count - 1)
        report = self.analyze(directory, root=root)
        self.assertEqual(report["validation_status"], "FAIL")
        self.assertIn("tree entries", report["error"])
        self.assertEqual(report["N_output"], self.count - 1)
        self.assertEqual(report["N_read"], self.count - 1)
        self.assertEqual(report["N_processed"], self.count - 1)
        self.assertEqual(report["N_invalid"], 0)
        self.assertEqual(report["N_skipped"], 1)
        self.assertEqual(report["N_unassessed_output_entries"], 0)


if __name__ == "__main__":
    unittest.main()
