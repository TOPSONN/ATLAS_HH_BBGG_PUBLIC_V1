"""Process-selection and bounded execution tests; no MG5 generation is launched."""
from contextlib import redirect_stdout
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
import generate_sample as generator
from resource_limits import LimitStopped, RunLimits


class BackgroundGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cards = SCRIPTS.parent / "cards"

    def tearDown(self):
        self.temporary.cleanup()

    def test_reviewed_process_cards_are_accepted(self):
        expected = {"ccgg.mg5": ("ccgg", "generate p p > c c~ a a QCD=2 QED=2"),
                    "jjgg_light.mg5": ("jjgg", "generate p p > a a jl jl QCD=2 QED=2")}
        for name, (profile, command) in expected.items():
            actual, commands = generator.profile_from_card(self.cards / name)
            self.assertEqual(actual, profile)
            self.assertEqual(commands[-1], command)
            self.assertIn("define p = g u c d s b u~ c~ d~ s~ b~", commands)

    def test_charm_or_bottom_in_light_jet_definition_rejected(self):
        text = (self.cards / "jjgg_light.mg5").read_text()
        for extra in ("c c~", "b b~"):
            path = self.root / "unsafe.mg5"
            path.write_text(text.replace("define jl = g u u~ d d~ s s~", "define jl = g u u~ d d~ s s~ " + extra))
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                generator.profile_from_card(path)

    def test_relabelled_old_process_rejected(self):
        text = (self.cards / "bbgg.mg5").read_text().replace("validation_profile: bbgg", "validation_profile: ccgg")
        path = self.root / "relabelled.mg5"
        path.write_text(text)
        with self.assertRaises(ValueError):
            generator.profile_from_card(path)

    def test_hidden_launch_or_shell_command_rejected(self):
        text = (self.cards / "ccgg.mg5").read_text()
        for command in ("launch", "shell touch unexpected", "set nevents 1000000"):
            path = self.root / "unsafe.mg5"
            path.write_text(text + command + "\n")
            with self.subTest(command=command), self.assertRaises(ValueError):
                generator.profile_from_card(path)

    def test_b_specific_cuts_do_not_substitute_for_charm_or_light_jets(self):
        bbgg = {key: str(value) for key, value in generator.BASE_SETTINGS.items()}
        generator.check_profile_cuts(bbgg, "bbgg")
        for profile in ("ccgg", "jjgg"):
            with self.subTest(profile=profile), self.assertRaises(KeyError):
                generator.check_profile_cuts(bbgg, profile)

    def test_ordinary_jet_soft_collinear_regulators_required(self):
        for profile in ("ccgg", "jjgg"):
            values = {key: str(value) for key, value in generator.settings_for_profile(profile).items()}
            generator.check_profile_cuts(values, profile)
            for key in ("ptj", "etaj", "drjj", "draj", "pta", "etaa", "draa"):
                unsafe = dict(values, **{key: "0"})
                with self.subTest(profile=profile, key=key), self.assertRaises(ValueError):
                    generator.check_profile_cuts(unsafe, profile)

    def test_charm_cut_classification_cannot_be_changed_silently(self):
        for profile in ("ccgg", "jjgg"):
            values = {key: str(value) for key, value in generator.settings_for_profile(profile).items()}
            for flavor in (3, 5):
                values["maxjetflavor"] = str(flavor)
                with self.subTest(profile=profile, flavor=flavor), self.assertRaises(ValueError):
                    generator.check_profile_cuts(values, profile)

    def test_old_profile_settings_remain_independent(self):
        bbgg, diphoton = generator.settings_for_profile("bbgg"), generator.settings_for_profile("diphoton")
        self.assertEqual(bbgg, generator.BASE_SETTINGS)
        self.assertEqual(diphoton, generator.BASE_SETTINGS)
        ccgg = generator.settings_for_profile("ccgg")
        ccgg["ptj"] = 1
        self.assertNotIn("ptj", generator.BASE_SETTINGS)
        self.assertEqual(generator.settings_for_profile("jjgg")["ptj"], 20)

    def test_dry_run_never_starts_generator_or_creates_output(self):
        installation = self.root / "config.json"
        installation.write_text(json.dumps({"toolchain_prefix": str(self.root / "toolchain")}))
        output = self.root / "sample"
        argv = ["generate_sample", "--installation", str(installation), "--process", str(self.cards / "ccgg.mg5"),
                "--events", "1000", "--seed", "20261021", "--output", str(output), "--dry-run"]
        with patch.object(sys, "argv", argv), \
                patch.object(generator, "verify", return_value=(self.root / "mg5", {"source_commit": generator.SOURCE_COMMIT})), \
                patch.object(generator, "run") as run, redirect_stdout(io.StringIO()) as capture:
            self.assertEqual(generator.main(), 0)
        result = json.loads(capture.getvalue())
        self.assertEqual(result["events_generated"], 0)
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertFalse(output.exists())
        run.assert_not_called()


class ExecutionLimitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.controller = None

    def tearDown(self):
        if self.controller:
            self.controller.close()
        self.temporary.cleanup()

    def limits(self, hours=1, disk_gb=1):
        self.controller = RunLimits(self.root, hours, disk_gb, {"jobs": 2})
        return self.controller

    def test_cpu_bound_and_low_disk_preflight(self):
        with self.assertRaises(ValueError):
            RunLimits.preflight(self.root, 999999)
        with patch("resource_limits.shutil.disk_usage", return_value=type("Usage", (), {"free": 100})()):
            with self.assertRaises(ValueError):
                RunLimits.preflight(self.root, 1)

    def test_production_estimates_are_unknown(self):
        resources = RunLimits.preflight(self.root, 1)
        self.assertEqual(resources["runtime_estimate_seconds"], "UNKNOWN")
        self.assertEqual(resources["output_size_estimate_bytes"], "UNKNOWN")

    def test_stop_marker_preserves_partial_file_and_status(self):
        controller = self.limits()
        (self.root / "partial.control").write_text("Non-Monte-Carlo control data")
        (self.root / "STOP").touch()
        with self.assertRaises(LimitStopped) as caught:
            controller.check()
        self.assertEqual(caught.exception.status, "PARTIAL_STOPPED")
        self.assertTrue((self.root / "partial.control").exists())
        status = json.loads((self.root / "run_status.json").read_text())
        self.assertFalse(status["partial_events_are_accepted"])

    def test_signal_requests_safe_stop(self):
        controller = self.limits()
        controller.request_stop(signal.SIGTERM, None)
        with self.assertRaises(LimitStopped) as caught:
            controller.check()
        self.assertEqual(caught.exception.status, "PARTIAL_STOPPED")

    def test_output_budget_preserves_failure(self):
        controller = self.limits(disk_gb=1 / 1024 ** 3)
        with self.assertRaises(LimitStopped) as caught:
            controller.check(force=True)
        self.assertEqual(caught.exception.status, "PARTIAL_DISK")
        controller.close()
        status = json.loads((self.root / "run_status.json").read_text())
        self.assertEqual(status["status"], "PARTIAL_DISK")

    @unittest.skipUnless(os.name == "posix", "requires Linux/WSL process groups")
    def test_real_control_process_terminated_on_timeout(self):
        controller = self.limits(hours=0.0001)
        started = time.monotonic()
        with self.assertRaises(LimitStopped) as caught:
            controller.run([sys.executable, "-c", "import time; time.sleep(30)"], self.root,
                           self.root / "control_only.log")
        self.assertEqual(caught.exception.status, "PARTIAL_TIMEOUT")
        self.assertLess(time.monotonic() - started, 5)

    @unittest.skipUnless(os.name == "posix", "requires Linux/WSL process groups")
    def test_generator_failure_status_and_log_are_retained(self):
        controller = self.limits()
        with self.assertRaises(RuntimeError):
            controller.run([sys.executable, "-c", "print('CONTROL_FAILURE'); raise SystemExit(7)"],
                           self.root, self.root / "control_only.log")
        self.assertIn("CONTROL_FAILURE", (self.root / "control_only.log").read_text())
        controller.close()
        status = json.loads((self.root / "run_status.json").read_text())
        self.assertEqual(status["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
