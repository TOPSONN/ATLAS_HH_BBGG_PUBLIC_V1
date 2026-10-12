"""Publication guards using copies of the two actual 1000-event references."""
from __future__ import annotations

import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import publish_background_references as publisher
from validate_lhe import sha256, validate_file

REPO = SCRIPTS.parents[2]


class BackgroundPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.target = self.base / "publication"
        self.runs = {}
        for profile, definition in publisher.PROFILES.items():
            run = self.base / profile
            run.mkdir()
            (run / "cards").mkdir()
            (run / "process/Events/sample").mkdir(parents=True)
            directory = REPO / "reference_samples/mg5" / definition["directory"]
            published = json.loads((directory / "sample_manifest.json").read_text())["samples"][0]
            compressed = (directory / "reference_1000.lhe.gz").read_bytes()
            data = gzip.decompress(compressed)
            (run / "sample.lhe.gz").write_bytes(compressed)
            (run / "sample.lhe").write_bytes(data)
            (run / "process/Events/sample/unweighted_events.lhe.gz").write_bytes(compressed)
            validation = validate_file(run / "sample.lhe.gz", 1000, profile=profile, beam_energy=6500)
            cards = {}
            for key, name in (("process_card", "proc_card_mg5.dat"), ("run_card", "run_card.dat"), ("param_card", "param_card.dat")):
                shutil.copyfile(REPO / published[key + "_path"], run / "cards" / name)
                cards[key + "_sha256"] = sha256((run / "cards" / name).read_bytes())
            label = profile + "_reference_1000"
            evidence = REPO / "simulation/mg5/evidence" / label
            for source, destination in (("generator_banner.txt", "generator_banner.txt"),
                                        ("process_generation.txt", "process_generation.log"),
                                        ("event_generation.txt", "event_generation.log"),
                                        ("generate.mg5", "generate.mg5"), ("launch.mg5", "launch.mg5")):
                shutil.copyfile(evidence / source, run / destination)
            shutil.copyfile(REPO / "simulation/mg5/cards" / label / "me5_configuration.txt", run / "cards/me5_configuration.txt")
            local = {"status": "PASS", "profile": profile, "events_requested": 1000,
                     "random_seed": definition["seed"], "sqrt_s_gev": 13000,
                     "process": "generate " + definition["process"], "mg5_source_commit": publisher.SOURCE_COMMIT,
                     "source_identity": {"source_commit": publisher.SOURCE_COMMIT, "source_tag": "v3.5.16",
                                         "source_url": publisher.SOURCE_URL, "mg5_path": "/fixture/mg5",
                                         "toolchain_prefix": "/fixture/toolchain", "conda_sh": "/fixture/conda"},
                     "validation": validation, "card_hashes": cards, "execution": published["execution"]}
            (run / "run_manifest.json").write_text(json.dumps(local))
            self.runs[profile] = run

    def tearDown(self):
        self.temporary.cleanup()

    def test_plan_preserves_actual_generator_bytes_and_is_read_only(self):
        original = (self.runs["ccgg"] / "sample.lhe").read_bytes()
        sample, writes = publisher.prepare_run("ccgg", self.runs["ccgg"], self.target)
        self.assertEqual(sample["actual_events"], 1000)
        self.assertEqual(gzip.decompress(writes[sample["file"]]), original)
        self.assertEqual(sample["decompressed_file_sha256"], sha256(original))
        self.assertFalse(self.target.exists())
        self.assertFalse(any("pp_bbgg" in path for path in writes))

    def test_actual_alpha_s_is_derived_from_banner_card(self):
        for profile, run in self.runs.items():
            sample, _ = publisher.prepare_run(profile, run, self.target)
            blocks = publisher.param_blocks((run / "cards/param_card.dat").read_text())
            self.assertEqual(sample["alpha_s_settings"]["param_card_as"], blocks["SMINPUTS"][3])
            self.assertEqual(sample["alpha_s_settings"]["event_aqcd"], sample["alpha_s_settings"]["event_aqcd_values"][0])

    def test_existing_publication_file_is_never_overwritten(self):
        sample, _ = publisher.prepare_run("ccgg", self.runs["ccgg"], self.target)
        existing = self.target / sample["file"]
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b"preserved historical payload")
        with self.assertRaisesRegex(ValueError, "no overwrite"):
            publisher.prepare_run("ccgg", self.runs["ccgg"], self.target)
        self.assertEqual(existing.read_bytes(), b"preserved historical payload")

    def test_wrong_seed_rejected_before_any_publication(self):
        path = self.runs["jjgg"] / "run_manifest.json"
        manifest = json.loads(path.read_text())
        manifest["random_seed"] += 1
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "seed"):
            publisher.prepare_run("jjgg", self.runs["jjgg"], self.target)
        self.assertFalse(self.target.exists())

    def test_failure_of_second_run_writes_neither_sample(self):
        manifest = self.runs["jjgg"] / "run_manifest.json"
        value = json.loads(manifest.read_text())
        value["status"] = "FAIL"
        manifest.write_text(json.dumps(value))
        argv = ["publisher", "--ccgg-run", str(self.runs["ccgg"]), "--jjgg-run", str(self.runs["jjgg"])]
        with patch.object(publisher, "REPO", self.target), patch.object(sys, "argv", argv):
            # Default arguments bind the source repository; explicitly redirect
            # only the target used by the invocation to an empty temporary tree.
            original_prepare = publisher.prepare_run
            with patch.object(publisher, "prepare_run", side_effect=lambda profile, run: original_prepare(profile, run, self.target)):
                self.assertEqual(publisher.main(), 1)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
