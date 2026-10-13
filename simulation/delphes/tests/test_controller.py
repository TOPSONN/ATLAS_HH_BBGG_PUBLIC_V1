"""Control/API tests only; never invokes Delphes or generates MG5/Pythia events."""
import argparse
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
import run_delphes as runner
import validate_references as portable


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.monitor = None

    def tearDown(self):
        if self.monitor:
            self.monitor.restore()
        self.temporary.cleanup()

    def monitor_for(self, hours=1, disk=1):
        args = argparse.Namespace(max_hours=hours, max_disk_gb=disk)
        self.monitor = runner.Monitor(self.directory, args, {"status": "CONTROL_TEST", "execution": {}})
        return self.monitor

    def test_exact_reviewed_card_and_only_seed_changes(self):
        target = self.directory / "runtime.tcl"
        for seed in runner.SEEDS.values():
            runner.runtime_card(runner.CARD, target, seed)
            expected = runner.CARD.read_bytes().replace(b"set RandomSeed 610301", f"set RandomSeed {seed}".encode(), 1)
            self.assertEqual(target.read_bytes(), expected)
        self.assertEqual(runner.file_sha256(runner.CARD), runner.CARD_SHA256)

    def test_native_output_argument_is_relative_without_root_reserialization(self):
        config = {"delphes_binary": "/verified/delphes/bin/DelphesHepMC3"}
        command = runner.delphes_command(config, self.directory)
        self.assertEqual(command[2], "detector.root")
        self.assertFalse(Path(command[2]).is_absolute())
        self.assertEqual(command[1], str(self.directory / "detector_card.tcl"))
        self.assertEqual(command[3], str(self.directory / "input.hepmc3"))

    def test_changed_card_rejected_before_execution(self):
        changed = self.directory / "changed.tcl"
        changed.write_bytes(runner.CARD.read_bytes() + b"\nset SomethingElse 1\n")
        with self.assertRaisesRegex(ValueError, "immutable reviewed"):
            runner.runtime_card(changed, self.directory / "output.tcl", 610301)

    def test_output_overwrite_repository_install_and_metacharacters_rejected(self):
        config = {"delphes_prefix": str(self.directory / "installed/delphes"), "root_prefix": str(self.directory / "installed/root")}
        for path in (self.directory, runner.REPO / "run", self.directory / "installed/delphes/run", self.directory / "two words"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runner.safe_output(path, config)

    def test_path_escape_in_source_evidence_rejected(self):
        with self.assertRaises(ValueError):
            runner.bound_file(self.directory, "../escaped")

    def test_source_json_memory_bound(self):
        file = self.directory / "too-large.json"
        file.write_bytes(b"12345")
        with self.assertRaisesRegex(ValueError, "oversized"):
            runner.read_json(file, max_bytes=4)

    def test_jsonl_record_bound(self):
        file = self.directory / "oversized.jsonl"
        file.write_bytes(b'{"record":123}\n')
        with self.assertRaisesRegex(ValueError, "oversized"):
            list(runner.jsonl_rows(file, maximum=4))

    def test_source_vertex_positions_and_implicit_zero_contract(self):
        raw = (b"E 1 1 3\nV -1 0 [1] @ 1.5 2.5 3.5 4.5\n"
               b"P 1 0 2212 0 0 1 2 1 4\nP 2 -1 22 1 0 0 1 0 1\nP 3 2 22 1 0 0 1 0 1\n")
        rows = list(runner.indexed_particles(raw))
        self.assertEqual(rows[0][-4:], ["0", "0", "0", "0"])
        self.assertEqual(rows[1][-4:], ["1.5", "2.5", "3.5", "4.5"])
        self.assertEqual(rows[2][-4:], ["0", "0", "0", "0"])

    @unittest.skipUnless((runner.REPO / ".local/pythia8_installation.json").is_file(), "existing verified local Pythia fixture")
    def test_actual_reader_verification_scopes_inherited_wrong_pythia_environment(self):
        with patch.dict(os.environ, {"PYTHIA8DATA": "/wrong/pythia8312/xmldoc", "LD_LIBRARY_PATH": "/wrong/library"}):
            config, env, verified = runner.verify_pythia_reader(runner.REPO / ".local/pythia8_installation.json",
                                                               Path.home() / "miniforge3/envs/atlas-hh-root")
            self.assertEqual(env["PYTHIA8DATA"], config["xml_path"])
            self.assertEqual(verified["binary_build_info"]["pythia_version_integer"], 8317)
            self.assertEqual(os.environ["PYTHIA8DATA"], "/wrong/pythia8312/xmldoc")
            self.assertNotIn("/wrong/library", env["LD_LIBRARY_PATH"])

    def test_stop_signal_and_disk_preserve_partial_files(self):
        monitor = self.monitor_for()
        retained = self.directory / "partial.control"
        retained.write_bytes(b"CONTROL_TEST")
        monitor.signal_handler(signal.SIGTERM)
        with self.assertRaises(runner.StopRun):
            monitor.check()
        self.assertTrue(retained.exists())
        monitor.stopped = False
        (self.directory / "STOP").touch()
        with self.assertRaises(runner.StopRun):
            monitor.check()
        (self.directory / "STOP").unlink()
        monitor.args.max_disk_gb = 1 / 1024**3
        with self.assertRaises(runner.StopRun):
            monitor.check(force=True)
        self.assertTrue(retained.exists())

    def test_actual_nonphysics_child_timeout(self):
        monitor = self.monitor_for(hours=0.00005)
        began = time.monotonic()
        with self.assertRaises(runner.StopRun):
            monitor.run([sys.executable, "-c", "import time; time.sleep(30)"], "CONTROL_TEST")
        self.assertLess(time.monotonic() - began, 5)
        self.assertTrue((self.directory / "CONTROL_TEST.log").exists())

    def test_low_storage_rejected(self):
        with patch.object(runner.shutil, "disk_usage", return_value=argparse.Namespace(free=100)), self.assertRaises(ValueError):
            runner.resource_preflight(self.directory)

    def test_predictions_remain_unknown(self):
        result = runner.resource_preflight(self.directory)
        self.assertEqual(result["predicted_root_output_bytes"], "UNKNOWN")
        self.assertEqual(result["predicted_runtime_seconds"], "UNKNOWN")
        self.assertEqual(result["jobs"], 1)

    def test_native_failure_counts_are_retained_without_fabrication(self):
        path = self.directory / "native.json"
        observed = {"validation_status": "FAIL", "N_input": 100, "N_read": 100,
                    "N_processed": 99, "N_output": 99, "N_invalid": 1, "N_skipped": 1}
        path.write_text(json.dumps(observed))
        manifest = {}
        self.assertEqual(runner.record_native_validation(manifest, path, 1), observed)
        self.assertEqual(manifest["N_output"], 99)
        self.assertEqual(manifest["N_invalid"], 1)
        self.assertEqual(manifest["native_validator_exit_code"], 1)
        self.assertIsNone(runner.record_native_validation(manifest, self.directory / "missing.json", 1))
        self.assertEqual(manifest["N_output"], "UNKNOWN")

    @unittest.skipUnless(Path.home().joinpath("simulations/pythia8_runs/bbgg_1k/run_manifest.json").is_file(), "existing local Phase6B fixture")
    def test_actual_existing_source_raw_prefix_and_truth_api(self):
        monitor = self.monitor_for()
        published = runner.REPO / "reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev/shower_100.hepmc3.gz"
        config = {"phase6b_runs": {"bbgg": str(Path.home() / "simulations/pythia8_runs/bbgg_1k")}}
        context = runner.source_context(published, "bbgg", config)
        source_plain = self.directory / "source.hepmc3"
        with source_plain.open("wb") as target:
            for _, raw in runner.hepmc.iter_ascii(published):
                target.write(raw)
        runner.native_index_and_prefix(source_plain, self.directory, 2, context, monitor)
        runner.truth_index(self.directory, 2, context, monitor)
        original = list(runner.hepmc.iter_ascii(published))
        selected = list(runner.hepmc.iter_ascii(self.directory / "input.hepmc3"))
        self.assertEqual(selected, [original[0], original[1], original[2], original[-1]])
        index = (self.directory / "input_event_index.dat").read_text().splitlines()
        truth = (self.directory / "truth_analysis_index.dat").read_text().splitlines()
        self.assertEqual(sum(line.startswith("E ") for line in index), 2)
        self.assertEqual(sum(line.startswith("G ") for line in truth), 4)
        self.assertEqual(sum(line.startswith("L ") for line in truth), 4)
        self.assertEqual(sum(line.startswith("Q ") for line in truth), 4)
        self.assertEqual(sum(line.startswith("R ") for line in truth), 4)
        runner.copy_ledger_prefix(context, self.directory, 2, monitor)
        portable.validate_input_index(self.directory / "input_event_index.dat", self.directory / "input.hepmc3",
                                      self.directory / "source_event_ledger.jsonl", 2)
        portable.validate_truth_envelope(self.directory / "truth_analysis_index.dat", 2,
                                        self.directory / "source_event_ledger.jsonl", context["manifest"]["pythia_run_id"],
                                        context["manifest"]["pythia_seed"])


if __name__ == "__main__":
    unittest.main()
