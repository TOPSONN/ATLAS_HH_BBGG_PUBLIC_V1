"""Resource, request and recovery controls; no MG5 generation is launched here."""
import argparse
import hashlib
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
import generate_sample as generator
import generate_batches as batches


class GenerationControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = {"mg5_path": str(self.root / "installed/mg5"),
                       "toolchain_prefix": str(self.root / "installed/toolchain"),
                       "source_commit": "3ea6e242a6021cc909c1016dd1a4f0ab1c398ac7"}
        self.args = generator.parser().parse_args(["--installation", str(self.root / "config.json"),
                                                  "--output", str(self.root / "sample")])

    def tearDown(self):
        self.temporary.cleanup()

    def test_alias_and_request_fingerprint(self):
        path, profile, commands, output, request, fingerprint = generator.prepare_request(self.args, self.config)
        self.assertEqual(profile, "bbgg")
        self.assertEqual(path.name, "bbgg.mg5")
        self.assertEqual(request["process_card_sha256"], generator.digest_file(path))
        self.assertEqual(fingerprint, hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest())
        self.assertEqual(commands[-1], "generate p p > b b~ a a QCD=2 QED=2")

    def test_diphoton_alias_and_card_path(self):
        self.args.process = "pp_diphoton"
        path, profile, *_ = generator.prepare_request(self.args, self.config)
        self.assertEqual(profile, "diphoton")
        self.args.process = str(path)
        self.assertEqual(generator.prepare_request(self.args, self.config)[1], "diphoton")

    def test_arbitrary_process_commands_rejected(self):
        card = self.root / "process.mg5"
        card.write_text("# validation_profile: bbgg\nimport model sm\ngenerate p p > b b~ a a\n")
        with self.assertRaises(ValueError):
            generator.profile_from_card(card)

    def test_events_and_seed_boundaries(self):
        for name, value in (("events", 0), ("seed", 0), ("seed", 30081 ** 2 + 1)):
            with self.subTest(name=name, value=value):
                args = argparse.Namespace(**vars(self.args))
                setattr(args, name, value)
                with self.assertRaises(ValueError):
                    generator.prepare_request(args, self.config)
        self.args.seed = 30081 ** 2
        generator.prepare_request(self.args, self.config)

    def test_finite_positive_limits(self):
        for name in ("energy", "max_hours", "max_disk_gb"):
            for value in (0, -1, float("nan"), float("inf")):
                with self.subTest(name=name, value=value):
                    args = argparse.Namespace(**vars(self.args))
                    setattr(args, name, value)
                    with self.assertRaises(ValueError):
                        generator.prepare_request(args, self.config)

    def test_protect_repository_installation_and_ancestor(self):
        for output in (generator.REPO / "personal", self.root / "installed/mg5/sample", self.root):
            with self.subTest(output=output), self.assertRaises(ValueError):
                generator.check_output(output, self.config)

    def test_output_shell_metacharacters_rejected(self):
        for name in ("two words", "sample;rm", "sample\nline", "sample'quote"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                generator.check_output(self.root / name, self.config)

    def test_actual_massless_mg5_card_accepted(self):
        card = generator.REPO / "simulation/mg5/cards/reference_1000/param_card.dat"
        generator.validate_param_card(card)

    def test_nonzero_b_yukawa_and_nan_rejected(self):
        actual = (generator.REPO / "simulation/mg5/cards/reference_1000/param_card.dat").read_text()
        path = self.root / "param.dat"
        for extra in ("\nBLOCK YUKAWA\n 5 4.7\n", "\nBLOCK SMINPUTS\n 99 nan\n"):
            path.write_text(actual + extra)
            with self.assertRaises(ValueError):
                generator.validate_param_card(path)

    def test_resource_preflight_cpu_and_disk_reject(self):
        self.args.jobs = 999999
        with self.assertRaises(ValueError):
            generator.preflight(self.root / "sample", self.args)
        self.args.jobs = 1
        low_disk = argparse.Namespace(free=100, total=10000, used=9900)
        with patch.object(generator.shutil, "disk_usage", return_value=low_disk), self.assertRaises(ValueError):
            generator.preflight(self.root / "sample", self.args)

    def test_unknown_production_estimate_is_explicit(self):
        self.args.jobs = 1
        with patch.object(generator.shutil, "disk_usage", return_value=argparse.Namespace(free=10**12, total=10**12)):
            resources = generator.preflight(self.root / "sample", self.args)
        self.assertEqual(resources["output_size_estimate_bytes"], "UNKNOWN")
        self.assertEqual(resources["runtime_estimate_seconds"], "UNKNOWN")

    def controller(self, **overrides):
        directory = self.root / "control"
        directory.mkdir()
        args = argparse.Namespace(max_hours=1, max_disk_gb=1, **{})
        for key, value in overrides.items():
            setattr(args, key, value)
        manifest = {"execution": {}, "status": "RUNNING"}
        return generator.Controller(directory, args, manifest)

    def test_stop_marker_retains_partial_status(self):
        controller = self.controller()
        (controller.output / "STOP").touch()
        with self.assertRaises(generator.RunInterrupted) as caught:
            controller.check()
        self.assertEqual(caught.exception.status, "PARTIAL_STOPPED")

    def test_signal_requests_safe_stop(self):
        controller = self.controller()
        controller.signal_handler(signal.SIGTERM, None)
        with self.assertRaises(generator.RunInterrupted) as caught:
            controller.check()
        self.assertEqual(caught.exception.status, "PARTIAL_STOPPED")

    def test_output_budget_is_enforced(self):
        controller = self.controller(max_disk_gb=1 / 1024 ** 3)
        (controller.output / "data").write_bytes(b"12345")
        with self.assertRaises(generator.RunInterrupted) as caught:
            controller.check(force=True)
        self.assertEqual(caught.exception.status, "PARTIAL_DISK")

    @unittest.skipUnless(os.name == "posix", "process group control requires Linux/WSL")
    def test_real_process_is_terminated_on_timeout(self):
        controller = self.controller(max_hours=0.0001)
        started = time.monotonic()
        with self.assertRaises(generator.RunInterrupted) as caught:
            controller.run([sys.executable, "-c", "import time; time.sleep(30)"], controller.output,
                           controller.output / "non_generator.log", "control_test")
        self.assertEqual(caught.exception.status, "PARTIAL_TIMEOUT")
        self.assertLess(time.monotonic() - started, 5)

    def test_batch_plan_has_unique_seeds_and_exact_target(self):
        args = argparse.Namespace(**vars(self.args), batches=10, events_per_batch=100000)
        plan = batches.make_plan(args, self.config)
        self.assertEqual(plan["target_events"], 1000000)
        self.assertEqual([item["seed"] for item in plan["batches"]], list(range(12345, 12355)))
        self.assertFalse(plan["reference_samples_included"])
        self.assertFalse(args.output.exists())

    def test_batch_seed_overflow_rejected(self):
        args = argparse.Namespace(**vars(self.args), batches=10, events_per_batch=100000)
        args.seed = 30081 ** 2
        with self.assertRaises(ValueError):
            batches.make_plan(args, self.config)

    def test_batch_snapshot_never_counts_partial_events(self):
        root = self.root / "batch_collection"
        root.mkdir()
        args = argparse.Namespace(**vars(self.args), batches=1, events_per_batch=1000)
        args.output = root
        plan = batches.make_plan(args, self.config)
        generator.atomic_json(root / "batch_manifest.json", plan)
        (root / "batch_01").mkdir()
        generator.atomic_json(root / "batch_01/run_manifest.json",
                              {"status": "PARTIAL_STOPPED", "actual_events": 500,
                               "request": plan["batches"][0]["request"]})
        snapshot = batches.batch_snapshot(root)
        self.assertEqual(snapshot["complete_events"], 0)
        self.assertFalse(snapshot["counts_independently_validated"])

    def test_saved_batch_plan_integrity_and_path_safety(self):
        args = argparse.Namespace(**vars(self.args), batches=2, events_per_batch=1000)
        for change in ("path", "duplicate_seed", "target", "hash"):
            plan = batches.make_plan(args, self.config)
            if change == "path":
                plan["batches"][0]["directory"] = "../../outside"
            elif change == "duplicate_seed":
                plan["batches"][1]["seed"] = plan["batches"][0]["seed"]
            elif change == "target":
                plan["target_events"] += 1
            else:
                plan["plan_sha256"] = "0" * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                batches.validate_plan(plan)

    def existing_request(self, status):
        self.args.installation.write_text(json.dumps(self.config))
        _, _, _, output, request, fingerprint = generator.prepare_request(self.args, self.config)
        output.mkdir()
        manifest = {"status": status, "request": request, "request_sha256": fingerprint,
                    "attempt_number": 1}
        generator.atomic_json(output / "run_manifest.json", manifest)
        self.args.resume = True
        return output, manifest

    def test_resume_accepts_numeric_format_but_rejects_changed_seed(self):
        output, _ = self.existing_request("PASS")
        self.args.max_hours = float(self.args.max_hours)
        checked = []
        with patch.object(generator, "verify", return_value=(self.root / "installed/mg5", {"retained_file_sha256": {}})), \
                patch.object(generator, "validator", return_value=lambda *a, **kw: checked.append(a[0])):
            self.assertEqual(generator.execute(self.args), 0)
            self.assertEqual(checked, [output / "sample.lhe.gz"])
            self.args.seed += 1
            with self.assertRaises(ValueError):
                generator.execute(self.args)

    def test_partial_resume_preserves_previous_attempt(self):
        output, original = self.existing_request("PARTIAL_STOPPED")
        old = output / "attempts/attempt_001"
        old.mkdir(parents=True)
        (old / "partial.log").write_text("Control fixture: no Monte Carlo events")
        with patch.object(generator, "verify", return_value=(self.root / "installed/mg5", {"retained_file_sha256": {}})), \
                patch.object(generator.Controller, "run", side_effect=generator.RunInterrupted("PARTIAL_STOPPED", "CONTROL_TEST")):
            with self.assertRaises(generator.RunInterrupted):
                generator.execute(self.args)
        self.assertTrue((old / "partial.log").is_file())
        saved = json.loads((output / "attempts/attempt_002/previous_manifest.json").read_text())
        self.assertEqual(saved, original)
        actual = json.loads((output / "run_manifest.json").read_text())
        self.assertEqual(actual["attempt_number"], 2)
        self.assertEqual(actual["status"], "PARTIAL_STOPPED")

    def test_batch_validation_rejects_duplicate_event_content(self):
        args = argparse.Namespace(**vars(self.args), batches=2, events_per_batch=1000)
        root = args.output
        plan = batches.make_plan(args, self.config)
        root.mkdir()
        generator.atomic_json(root / "batch_manifest.json", plan)
        for row in plan["batches"]:
            (root / row["directory"]).mkdir()
            generator.atomic_json(root / row["directory"] / "run_manifest.json",
                                  {"status": "PASS", "request": row["request"], "random_seed": row["seed"],
                                   "events_requested": row["events"]})
        result = {"actual_events": 1000, "compressed_file_sha256": "same_fixture_hash",
                  "event_content_sha256": "duplicate_fixture_hash", "cross_section_pb": 1,
                  "cross_section_uncertainty_pb": 0.1}
        with patch("validate_sample.validate_run", return_value=result), self.assertRaises(ValueError):
            batches.batch_snapshot(root, verify_samples=True)


if __name__ == "__main__":
    unittest.main()
