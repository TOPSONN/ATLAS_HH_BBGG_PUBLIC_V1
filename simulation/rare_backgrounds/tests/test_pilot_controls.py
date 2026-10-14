"""Provenance/output controls on actual published pilot data; no physics runs."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/rare_backgrounds/scripts"))
import analyze_pilot as pilot
import extract_pilot as extraction


class PilotControls(unittest.TestCase):
    def setUp(self):
        self.scratch_root = REPO / ".local/phase6d/control-test-scratch"
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self.scratch = tempfile.TemporaryDirectory(dir=self.scratch_root)
        self.addCleanup(self.cleanup_scratch)
        self.directory = Path(self.scratch.name) / "evidence"
        shutil.copytree(REPO / "simulation/rare_backgrounds/evidence/pilot", self.directory / "pilot")
        shutil.copyfile(REPO / "simulation/rare_backgrounds/evidence/input_verification.json", self.directory / "input_verification.json")

    def cleanup_scratch(self):
        Path(self.scratch.name).resolve().relative_to(self.scratch_root.resolve())
        self.scratch.cleanup()

    def test_verified_actual_full_pilot_accepts(self):
        extraction, verified = pilot.validate_inputs(self.directory / "pilot")
        self.assertEqual(extraction["actual_ROOT_entries_read"], 3000)
        self.assertEqual(len(verified["samples"]), 3)

    def test_changed_pilot_fails_before_output_creation(self):
        source = self.directory / "pilot/bbgg.jsonl"
        with source.open("ab") as stream:
            stream.write(b"\n")
        output = Path(self.scratch.name) / "result"
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            pilot.run(self.directory / "pilot", output)
        self.assertFalse(output.exists())

    def test_forged_duplicate_extraction_process_fails(self):
        path = self.directory / "pilot/extraction.json"
        evidence = json.loads(path.read_text())
        evidence["samples"].append(evidence["samples"][0])
        path.write_text(json.dumps(evidence))
        with self.assertRaisesRegex(ValueError, "duplicate process"):
            pilot.validate_inputs(self.directory / "pilot")

    def test_changed_native_receipt_fails(self):
        with (self.directory / "input_verification.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "receipt hash mismatch"):
            pilot.validate_inputs(self.directory / "pilot")

    def test_existing_output_is_preserved(self):
        output = Path(self.scratch.name) / "result"
        output.mkdir()
        marker = output / "personal-output.txt"
        marker.write_text("preserve these bytes")
        with self.assertRaisesRegex(ValueError, "new directory"):
            pilot.run(self.directory / "pilot", output)
        self.assertEqual(marker.read_text(), "preserve these bytes")

    def test_receipt_mutation_during_analysis_cannot_receive_pass(self):
        original = pilot.tags.analyze_file
        def mutate_after_valid_analysis(*args):
            summary = original(*args)
            with (self.directory / "pilot/extraction.json").open("ab") as stream:
                stream.write(b" ")
            return summary
        output = Path(self.scratch.name) / "partial"
        with patch.object(pilot.tags, "analyze_file", side_effect=mutate_after_valid_analysis):
            with self.assertRaisesRegex(ValueError, "bytes changed during"):
                pilot.run(self.directory / "pilot", output)
        self.assertFalse((output / "analysis.json").exists())
        self.assertEqual(json.loads((output / "partial_status.json").read_text())["status"], "PARTIAL")

    def test_extraction_rejects_partial_process_receipt(self):
        path = self.directory / "input_verification.json"
        receipt = json.loads(path.read_text())
        receipt["samples"] = receipt["samples"][:1]
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "three unique"):
            extraction.validated_receipt(path)

    def test_extraction_rejects_duplicate_process_receipt(self):
        path = self.directory / "input_verification.json"
        receipt = json.loads(path.read_text())
        receipt["samples"][2] = receipt["samples"][0]
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "three unique"):
            extraction.validated_receipt(path)

    def test_exact_weight_change_below_binary64_resolution_fails_checksum(self):
        # Explicit API failure fixture, never a Monte Carlo/reference record.
        nominal = "0.000066246662"
        changed = "0.0000662466620000000000001"
        self.assertEqual(float(nominal), float(changed))
        path = Path(self.scratch.name) / "input_event_index.jsonl"
        path.write_text(nominal)
        receipt = {"source_files_sha256": {path.name: extraction.sha(path)}}
        extraction.check_source_index(path.parent, receipt)
        path.write_text(changed)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            extraction.check_source_index(path.parent, receipt)


if __name__ == "__main__":
    unittest.main()
