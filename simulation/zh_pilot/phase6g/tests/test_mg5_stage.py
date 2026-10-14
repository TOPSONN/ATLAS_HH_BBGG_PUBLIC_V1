"""METHOD_ONLY driver/guard tests: no MG5 import, integration, or real events."""
from copy import deepcopy
import gzip
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("phase6g_mg5_stage", REPO / "simulation/zh_pilot/phase6g/mg5_stage.py")
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class MG5StageTests(unittest.TestCase):
    def setUp(self):
        scratch = REPO / ".local/phase6g/tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="phase6g_mg5_method_", dir=scratch)
        self.assertTrue(Path(self.temp.name).resolve().is_relative_to(scratch.resolve()))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # The isolated METHOD_ONLY checkout lets tests create output alongside a
        # protected repo while keeping every temporary write inside the workspace.
        self.fake_repo = self.root / "method_only_repo"
        for relative in ("simulation/zh_pilot/config/generator_contract.json",
                         "simulation/zh_pilot/scripts/check_generator.py",
                         "simulation/zh_pilot/cards/zh_stable.mg5",
                         "simulation/zh_pilot/cards/zh_zbb_stable_h.mg5",
                         "simulation/zh_pilot/cards/run_card.dat",
                         "simulation/zh_pilot/cards/param_card.dat"):
            destination = self.fake_repo / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((REPO / relative).read_bytes())
        self.install = {"mg5_path": str(self.root / "installed/mg5"),
                        "toolchain_prefix": str(self.root / "installed/toolchain"),
                        "source_commit": stage.MG5_COMMIT, "source_tag": "v3.5.16",
                        "source_url": "https://github.com/mg5amcnlo/mg5amcnlo.git"}
        self.work = self.root / "run/mg5"

    def plan(self, **kwargs):
        return stage.prepare_mg5_stage(self.work, repo=self.fake_repo, installation=self.install, **kwargs)

    def rewrite_plan(self, plan):
        (self.work / "prepared_stage.json").write_text(json.dumps(plan), encoding="utf-8")

    def fake_callback(self, calls, *, count=100, fail=None):
        """Recording-only callback with conspicuously invalid synthetic LHE."""
        def run(argv, cwd, label):
            calls.append((argv, cwd, label))
            log = cwd / ("process_generation.log" if label == "mg5_process_export" else "event_generation.log")
            if fail == label:
                log.write_text("METHOD_ONLY simulated guarded failure\n")
                return {"exit_code": 7, "log_path": str(log)}
            if label == "mg5_process_export":
                cards = cwd / "process/Cards"
                cards.mkdir(parents=True)
                for name in ("run_card.dat", "param_card.dat", "proc_card_mg5.dat", "me5_configuration.txt"):
                    (cards / name).write_text("METHOD_ONLY export placeholder\n")
                log.write_text("METHOD_ONLY recording callback; no MG5 executed\n")
            else:
                cards = cwd / "process/Cards"
                self.assertEqual((cards / "run_card.dat").read_bytes(), (cwd / "inputs/run_card.dat").read_bytes())
                self.assertEqual((cards / "param_card.dat").read_bytes(), (cwd / "inputs/param_card.dat").read_bytes())
                run = cwd / "process/Events/zh100"
                run.mkdir(parents=True)
                (run / "unweighted_events.lhe.gz").write_bytes(gzip.compress(b"METHOD_ONLY_INVALID_NOT_A_PHYSICS_REFERENCE\n"))
                (run / "zh100_method_banner.txt").write_text("METHOD_ONLY invalid banner\n")
                log.write_text("METHOD_ONLY recording callback\n"
                               "  === Results Summary for run: zh100 tag: method ===\n"
                               "     Cross-section :   0.1234 +- 0.001234 pb\n"
                               "     Nb of events :  " + str(count) + "\n")
            return {"exit_code": 0, "log_path": str(log), "method_only": True}
        return run

    def test_preparation_only_creates_bound_text_without_physics_outputs(self):
        plan = self.plan()
        self.assertEqual(plan["status"], "PREPARED_TEXT_ONLY")
        self.assertEqual(plan["new_physics_events_generated"], 0)
        self.assertFalse((self.work / "process").exists())
        self.assertTrue(all(p.suffix not in {".gz", ".root", ".lhe"} for p in self.work.rglob("*") if p.is_file()))
        self.assertEqual(plan["generator_contract_sha256"], stage.GENERATOR_CONTRACT_SHA256)
        values = stage._checker(REPO).parse_run((self.work / "inputs/run_card.dat").read_text())
        self.assertEqual((values["nevents"], values["iseed"], values["ebeam1"], values["ebeam2"]),
                         (100, 20261104, 6500, 6500))
        self.assertEqual(values["scale"], 216.188)
        self.assertEqual(values["pdlabel"], "cteq6l1")

    def test_single_worker_fixed_process_and_only_one_launch_are_prepared(self):
        self.plan(seed=42)
        generate = (self.work / "generate.mg5").read_text()
        launch = (self.work / "launch.mg5").read_text()
        self.assertIn("set nb_core 1\n", generate)
        self.assertIn("set nb_core 1\n", launch)
        self.assertIn(stage.PROCESS_COMMANDS[-1] + "\n", generate)
        self.assertEqual(launch.count("launch "), 1)
        for command in ("shower=OFF", "detector=OFF", "madspin=OFF", "reweight=OFF"):
            self.assertIn(command + "\n", launch)
        self.assertNotIn("install ", generate + launch)
        self.assertNotIn("calculate_width", generate + launch)

    def test_only_seed_and_request_fields_change_the_frozen_card(self):
        self.plan(seed=1)
        checker = stage._checker(REPO)
        template = checker.parse_run((REPO / "simulation/zh_pilot/cards/run_card.dat").read_text())
        prepared = checker.parse_run((self.work / "inputs/run_card.dat").read_text())
        self.assertEqual({k for k in template if template[k] != prepared[k]}, {"iseed"})
        self.assertEqual((self.work / "inputs/param_card.dat").read_bytes(),
                         (REPO / "simulation/zh_pilot/cards/param_card.dat").read_bytes())

    def test_unreviewed_count_energy_seed_and_bool_are_rejected_before_text_creation(self):
        for kwargs in ({"events": 10}, {"events": 1000}, {"events": True},
                       {"energy_gev": 14000}, {"energy_gev": float("nan")},
                       {"seed": 0}, {"seed": True}, {"seed": 900000001}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.plan(**kwargs)
            self.assertFalse(self.work.exists())

    def test_existing_and_protected_output_are_preserved(self):
        self.work.mkdir(parents=True)
        marker = self.work / "preserve.txt"
        marker.write_text("preserve")
        with self.assertRaises(ValueError):
            self.plan()
        self.assertEqual(marker.read_text(), "preserve")
        with self.assertRaisesRegex(ValueError, "protected"):
            stage.prepare_mg5_stage(REPO / ".local/new_forbidden_stage", installation=self.install)

    def test_changed_card_or_driver_never_reaches_capability(self):
        plan = self.plan()
        calls = []
        for path in (self.work / "inputs/run_card.dat", self.work / "generate.mg5"):
            raw = path.read_bytes()
            path.write_bytes(raw + b"launch forbidden\n")
            with self.assertRaisesRegex(ValueError, "changed"):
                stage.execute_mg5_stage(plan, run_command=self.fake_callback(calls))
            path.write_bytes(raw)
        self.assertEqual(calls, [])

    def test_execution_needs_callback_and_plan_cannot_grant_authority(self):
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "capability"):
            stage.execute_mg5_stage(plan, run_command=None)
        plan["execution_authority"] = "AUTHORIZED"
        self.rewrite_plan(plan)
        calls = []
        with self.assertRaises(ValueError):
            stage.execute_mg5_stage(plan, run_command=self.fake_callback(calls))
        self.assertEqual(calls, [])

    def test_recording_callback_calls_two_stages_once_without_claiming_physics_pass(self):
        plan = self.plan()
        calls = []
        report = stage.execute_mg5_stage(plan, run_command=self.fake_callback(calls))
        self.assertEqual([c[2] for c in calls], ["mg5_process_export", "mg5_100_event_generation"])
        self.assertEqual(report["status"], "MG5_OUTPUT_PRESENT_PENDING_INDEPENDENT_LHE_PHYSICS_VALIDATION")
        self.assertEqual(report["generation"]["precision"], "MG5_4_SIGNIFICANT_DIGIT_DISPLAY_ONLY")
        self.assertEqual(report["source_included_decay_ids"], ["Z_to_b_bbar"])
        self.assertEqual(report["missing_decay_ids_pending_weight_closure"], ["H_to_gamma_gamma"])
        self.assertFalse(report["retry_or_event_replacement_performed"])
        self.assertEqual(calls[0][0][1:4], ["-O", "-B", "-c"])
        with self.assertRaisesRegex(ValueError, "rerun"):
            stage.execute_mg5_stage(plan, run_command=self.fake_callback(calls))
        self.assertEqual(len(calls), 2)

    def test_callback_failure_cannot_trigger_automatic_retry_or_next_stage(self):
        plan = self.plan()
        calls = []
        with self.assertRaisesRegex(ValueError, "successfully"):
            stage.execute_mg5_stage(plan, run_command=self.fake_callback(calls, fail="mg5_process_export"))
        self.assertEqual(len(calls), 1)

    def test_wrong_actual_summary_count_is_not_replaced_or_accepted(self):
        plan = self.plan()
        calls = []
        with self.assertRaisesRegex(ValueError, "count other than 100"):
            stage.execute_mg5_stage(plan, run_command=self.fake_callback(calls, count=99))
        self.assertEqual(len(calls), 2)
        self.assertTrue((self.work / "process/Events/zh100/unweighted_events.lhe.gz").is_file())

    def test_log_parser_rejects_duplicate_run_missing_or_invalid_uncertainty(self):
        good = "=== Results Summary for run: zh100 tag: phase6f_zh_pilot ===\nCross-section : 1.234e-1 +- 1.2e-3 pb\nNb of events : 100\n"
        self.assertEqual(stage.parse_generation_summary(good)["cross_section_pb"], "0.1234")
        for text in (good + good, good.replace("zh100", "other_run"),
                     good.replace("1.2e-3", "-0.001"), good.replace("1.234e-1", "0"),
                     good.replace("1.2e-3", "NaN"), good.replace("100\n", "101\n")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                stage.parse_generation_summary(text)

    def test_alternate_interpreter_and_rehashed_metadata_are_rejected_before_callback(self):
        plan = self.plan()
        calls = []
        for key, value in (("python_executable", str(self.root / "unexpected_python")),
                           ("readonly_runtime_adapter_sha256", "0" * 64), ("schema_version", True)):
            changed = deepcopy(plan)
            changed[key] = value
            self.rewrite_plan(changed)
            with self.assertRaises(ValueError):
                stage.execute_mg5_stage(changed, run_command=self.fake_callback(calls))
        self.assertEqual(calls, [])

    def test_readonly_adapter_disables_cache_flags_before_actual_entrypoint_imports(self):
        fake_mg5 = ModuleType("madgraph")
        fake_mg5.MG5DIR = self.install["mg5_path"]
        fake_mg5.ReadWrite = True
        root = Path(self.install["mg5_path"])
        opts = root / "Template/LO/Source/make_opts"
        opts.parent.mkdir(parents=True)
        opts.write_text("METHOD_ONLY template\n")
        original_argv, original_path = sys.argv[:], sys.path[:]
        self.addCleanup(lambda: setattr(sys, "argv", original_argv))
        self.addCleanup(lambda: setattr(sys, "path", original_path))
        sys.argv = ["-c", str(root), str(self.work / "generate.mg5"), self.install["toolchain_prefix"]]
        observed = []
        with patch.dict(sys.modules, {"madgraph": fake_mg5}), patch.object(sys, "addaudithook"), patch.object(runpy, "run_path", side_effect=lambda *a, **k: observed.append(fake_mg5.ReadWrite)):
            exec(stage.READONLY_MG5_ADAPTER, {})
        self.assertEqual(observed, [False])
        self.assertFalse(fake_mg5.ReadWrite)
        self.assertEqual(sys.argv, [str(root / "bin/mg5_aMC"), str(self.work / "generate.mg5")])
        self.assertEqual(opts.read_text(), "METHOD_ONLY template\n")

    def test_ancient_template_repair_is_blocked_before_entrypoint_or_import(self):
        root = Path(self.install["mg5_path"])
        opts = root / "Template/LO/Source/make_opts"
        opts.parent.mkdir(parents=True)
        opts.write_text("METHOD_ONLY preserve old template\n")
        os.utime(opts, (1400000000, 1400000000))
        original_argv = sys.argv[:]
        self.addCleanup(lambda: setattr(sys, "argv", original_argv))
        sys.argv = ["-c", str(root), str(self.work / "generate.mg5"), self.install["toolchain_prefix"]]
        with patch.object(sys, "addaudithook"), patch.object(runpy, "run_path") as entry:
            with self.assertRaisesRegex(RuntimeError, "ancient template repair"):
                exec(stage.READONLY_MG5_ADAPTER, {})
            entry.assert_not_called()
        self.assertEqual(opts.read_text(), "METHOD_ONLY preserve old template\n")

    def test_installation_write_audit_guards_templates_cache_and_updates(self):
        fake_mg5 = ModuleType("madgraph")
        fake_mg5.MG5DIR = self.install["mg5_path"]
        fake_mg5.ReadWrite = True
        original_argv, original_path = sys.argv[:], sys.path[:]
        self.addCleanup(lambda: setattr(sys, "argv", original_argv))
        self.addCleanup(lambda: setattr(sys, "path", original_path))
        sys.argv = ["-c", self.install["mg5_path"], str(self.work / "generate.mg5"), self.install["toolchain_prefix"]]
        hooks = []
        with patch.dict(sys.modules, {"madgraph": fake_mg5}), patch.object(sys, "addaudithook", side_effect=hooks.append), patch.object(runpy, "run_path"):
            exec(stage.READONLY_MG5_ADAPTER, {})
        self.assertEqual(len(hooks), 1)
        hook = hooks[0]
        installed = Path(self.install["mg5_path"])
        toolchain = Path(self.install["toolchain_prefix"])
        for event, args in (
            ("open", (str(installed / "models/sm/py3_model.pkl"), "wb", os.O_WRONLY | os.O_CREAT)),
            ("open", (str(installed / "Template/LO/Source/make_opts"), "w", 0)),
            ("open", (str(installed / "input/mg5_configuration.txt"), "a", os.O_APPEND)),
            ("os.remove", (str(installed / "retained.py"), -1)),
            ("os.rename", (str(installed / "retained.py"), str(self.work / "moved.py"), -1, -1)),
            ("os.mkdir", (str(toolchain / "new_installation"), 0o777, -1)),
        ):
            with self.subTest(event=event, args=args), self.assertRaisesRegex(PermissionError, "BLOCKED_INSTALLATION_WRITE"):
                hook(event, args)
        # Output compilation and links reading retained software remain allowed.
        hook("open", (str(self.work / "process/Source/make_opts"), "w", os.O_WRONLY | os.O_CREAT))
        hook("open", (str(installed / "Template/LO/Source/make_opts"), "r", os.O_RDONLY))
        hook("os.symlink", (str(installed / "lib/libdummy.a"), str(self.work / "process/lib/libdummy.a"), -1))


if __name__ == "__main__":
    unittest.main()
