"""Self-service guards and streaming provenance tests; no Pythia events generated."""
import argparse
from contextlib import redirect_stdout
import gzip
import io
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import shower_sample as shower
from validate_lhe_stream import validate_lhe_stream


class ShowerControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.monitor = None
        self.config = {"pythia_prefix": str(self.root / "installed/pythia"),
                       "hepmc3_prefix": str(self.root / "installed/hepmc")}

    def tearDown(self):
        if self.monitor:
            self.monitor.restore()
        self.temporary.cleanup()

    def controller(self, hours=1, disk_gb=1):
        output = self.root / "output"
        output.mkdir()
        args = argparse.Namespace(max_hours=hours, max_disk_gb=disk_gb)
        self.monitor = shower.Monitor(output, args, {"status": "RUNNING", "execution": {}})
        return self.monitor

    def test_existing_output_and_protected_directories_rejected(self):
        for path in (self.root, shower.REPO / "personal_run", self.root / "installed/pythia/run"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                shower.safe_output(path, self.config)

    def test_unsupported_output_characters_rejected(self):
        for name in ("two words", "semicolon;path", "newline\npath", "quoted'path"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                shower.safe_output(self.root / name, self.config)

    def test_low_free_disk_rejected_before_processing(self):
        usage = argparse.Namespace(free=100)
        with patch.object(shower.shutil, "disk_usage", return_value=usage), self.assertRaises(ValueError):
            shower.resources(self.root / "sample")

    def test_resource_predictions_are_explicitly_unknown(self):
        result = shower.resources(self.root / "sample")
        self.assertEqual(result["predicted_hepmc_bytes"], "UNKNOWN")
        self.assertEqual(result["predicted_runtime_seconds"], "UNKNOWN")
        self.assertEqual(result["jobs"], 1)

    def test_stop_file_preserves_partial_evidence(self):
        monitor = self.controller()
        (monitor.output / "partial.control").write_text("Non-physics control data")
        (monitor.output / "STOP").touch()
        with self.assertRaises(shower.StopRun):
            monitor.check()
        self.assertTrue((monitor.output / "partial.control").exists())

    def test_signal_requests_stop(self):
        monitor = self.controller()
        monitor.signal_handler(signal.SIGTERM, None)
        with self.assertRaises(shower.StopRun):
            monitor.check()

    def test_disk_budget_is_enforced(self):
        monitor = self.controller(disk_gb=1 / 1024**3)
        (monitor.output / "control.data").write_bytes(b"12345")
        with self.assertRaises(shower.StopRun):
            monitor.check(force=True)

    @unittest.skipUnless(os.name == "posix", "Linux/WSL process-group guard")
    def test_real_nonphysics_process_terminated_on_timeout(self):
        monitor = self.controller(hours=0.0001)
        started = time.monotonic()
        with self.assertRaises(shower.StopRun):
            monitor.run([sys.executable, "-c", "import time; time.sleep(30)"], "control_only")
        self.assertLess(time.monotonic() - started, 5)
        self.assertTrue((monitor.output / "control_only.log").exists())

    def test_streaming_gzip_preserves_exact_bytes_and_crc(self):
        monitor = self.controller()
        source = monitor.output / "control.txt"
        source.write_bytes(bytes(range(256)) * 1024)
        output = monitor.output / "control.txt.gz"
        shower.gzip_output(source, output, monitor)
        self.assertEqual(gzip.decompress(output.read_bytes()), source.read_bytes())
        self.assertEqual(output.read_bytes()[4:8], b"\0" * 4)
        self.assertFalse(output.read_bytes()[3] & 8)

    def test_real_lhe_identity_sidecar_and_scratch_are_exact(self):
        original = shower.REPO / shower.REFERENCE_INPUTS["bbgg"][0]
        validation = validate_lhe_stream(original, "bbgg", shower.REFERENCE_INPUTS["bbgg"][1])
        monitor = self.controller()
        plain = shower.prepare_source(original, monitor.output, validation, monitor)
        self.assertEqual(shower.file_sha256(plain), validation["decompressed_file_sha256"])
        rows = [json.loads(row) for row in (monitor.output / "source_events.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 1000)
        first = next(shower.iter_lhe_events(original))
        self.assertEqual(rows[0]["source_event_content_hash"], first["source_event_content_hash"])
        self.assertEqual(rows[0]["nominal_generator_weight"], first["nominal_generator_weight"])
        index = (monitor.output / "source_index.dat").read_text().splitlines()
        self.assertEqual(sum(line.startswith("E ") for line in index), 1000)
        self.assertEqual(sum(line.startswith("P ") for line in index), 6000)

    def test_jobs_greater_than_one_rejected_honestly(self):
        original = shower.REPO / shower.REFERENCE_INPUTS["bbgg"][0]
        argv = ["shower_sample", "--installation", str(self.root / "missing-config.json"),
                "--input", str(original), "--process", "bbgg", "--seed", "610201", "--jobs", "2"]
        with patch.object(sys, "argv", argv), self.assertRaisesRegex(ValueError, "supports --jobs 1 only"):
            shower.main()

    def test_invalid_seed_or_resource_limit_rejected(self):
        original = shower.REPO / shower.REFERENCE_INPUTS["bbgg"][0]
        common = ["shower_sample", "--installation", str(self.root / "missing-config.json"),
                  "--input", str(original), "--process", "bbgg"]
        for extra in (["--seed", "0"], ["--seed", "900000001"], ["--seed", "610201", "--max-hours", "nan"],
                      ["--seed", "610201", "--max-disk-gb", "-1"]):
            with self.subTest(extra=extra), patch.object(sys, "argv", common + extra), self.assertRaises(ValueError):
                shower.main()

    def test_editing_the_canonical_card_cannot_bypass_immutable_hash(self):
        original = shower.REPO / shower.REFERENCE_INPUTS["bbgg"][0]
        edited = self.root / "edited_baseline.cmnd"
        edited.write_bytes(shower.BASELINE.read_bytes() + b"\nTimeShower:alphaSvalue = 0.2\n")
        argv = ["shower_sample", "--installation", str(self.root / "missing-config.json"), "--input", str(original),
                "--process", "bbgg", "--seed", "610201", "--settings", str(edited), "--dry-run"]
        with patch.object(sys, "argv", argv), patch.object(shower, "BASELINE", edited), \
                self.assertRaisesRegex(ValueError, "repository baseline card differs"):
            shower.main()

    def test_reviewed_v2_card_is_pinned_and_old_diagnostic_card_rejected(self):
        self.assertEqual(shower.file_sha256(shower.BASELINE), shower.BASELINE_SHA256)
        old_card = shower.BASELINE.parent / "diagnostic_collinear_disabled.cmnd"
        self.assertNotEqual(shower.file_sha256(old_card), shower.BASELINE_SHA256)
        original = shower.REPO / shower.REFERENCE_INPUTS["bbgg"][0]
        argv = ["shower_sample", "--installation", str(self.root / "missing-config.json"),
                "--input", str(original), "--process", "bbgg", "--seed", "610201",
                "--settings", str(old_card), "--dry-run"]
        with patch.object(sys, "argv", argv), self.assertRaisesRegex(ValueError, "immutable reviewed baseline"):
            shower.main()

    def test_actual_reader_failure_counters_are_retained(self):
        report_path = self.root / "physical_validation.json"
        report = {"validation_status": "FAIL", "N_readback": 100, "N_passed_validation": 99,
                  "N_failed_validation": 1, "N_not_assessed": 0, "mass_shell_failed_particle_count": 3}
        report_path.write_text(json.dumps(report))
        manifest = {"status": "RUNNING"}
        self.assertEqual(shower.record_physical_validation(manifest, report_path, 1), report)
        self.assertEqual(manifest["N_failed_validation"], 1)
        self.assertEqual(manifest["N_readback"], 100)
        self.assertEqual(manifest["mass_shell_failed_particle_count"], 3)

    def test_missing_reader_evidence_remains_unknown(self):
        manifest = {}
        result = shower.record_physical_validation(manifest, self.root / "missing.json", 1)
        self.assertIsNone(result)
        self.assertEqual(manifest["N_failed_validation"], "UNKNOWN")
        self.assertEqual(manifest["N_readback"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
