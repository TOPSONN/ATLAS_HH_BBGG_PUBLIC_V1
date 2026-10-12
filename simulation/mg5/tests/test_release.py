"""Release guard/transport tests from actual reference events; no network writes."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import publish_release as release
import validate_sample as validator

REFERENCE = SCRIPTS.parents[2] / "reference_samples/mg5/pp_bbgg_sm_lo_13tev/smoke_100.lhe.gz"
TARGET = "a" * 40


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "sample_one"
        self.run.mkdir()
        (self.run / "cards").mkdir()
        shutil.copyfile(REFERENCE, self.run / "sample.lhe.gz")
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self):
        result = validator.validate_file(self.run / "sample.lhe.gz", 100)
        hashes = {}
        for key, filename in (("process_card", "proc_card_mg5.dat"),
                              ("run_card", "run_card.dat"), ("param_card", "param_card.dat")):
            data = result["cards"][key].encode()
            (self.run / "cards" / filename).write_bytes(data)
            hashes[key + "_sha256"] = hashlib.sha256(data).hexdigest()
        self.manifest = {
            "schema_version": 1, "status": "PASS", "profile": "bbgg",
            "process": validator.PROCESS["bbgg"], "events_requested": 100,
            "random_seed": int(result["run_values"]["iseed"]),
            "sqrt_s_gev": float(result["run_values"]["ebeam1"]) * 2,
            "mg5_source_commit": validator.SOURCE_COMMIT,
            "source_identity": {"source_commit": validator.SOURCE_COMMIT,
                                "source_url": validator.SOURCE_URL, "source_tag": validator.SOURCE_TAG},
            "card_hashes": hashes, "lhe_gz": "sample.lhe.gz", "validation": result,
        }
        (self.run / "run_manifest.json").write_text(json.dumps(self.manifest))

    def plan(self):
        return release.build_plan([self.run], "mg5-test-v1", 100)

    def test_preflight_validates_real_events_and_leaves_input_unchanged(self):
        before = {p.relative_to(self.run): release.file_hash(p) for p in self.run.rglob("*") if p.is_file()}
        plan, assets = self.plan()
        self.assertEqual(plan["actual_events_total"], 100)
        self.assertEqual(len(assets), 5)
        self.assertEqual(assets[0]["sha256"], self.manifest["validation"]["compressed_file_sha256"])
        after = {p.relative_to(self.run): release.file_hash(p) for p in self.run.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_wrong_expected_total_rejected(self):
        with self.assertRaisesRegex(release.PublicationError, "expected-events"):
            release.build_plan([self.run], "test", 1000000)

    def test_duplicate_content_cannot_double_count(self):
        other = self.root / "sample_two"
        shutil.copytree(self.run, other)
        with self.assertRaisesRegex(release.PublicationError, "duplicate event"):
            release.build_plan([self.run, other], "test", 200)

    def test_partial_run_rejected(self):
        self.manifest["status"] = "PARTIAL_STOPPED"
        (self.run / "run_manifest.json").write_text(json.dumps(self.manifest))
        with self.assertRaises(ValueError):
            self.plan()

    def test_card_tampering_rejected(self):
        with (self.run / "cards/run_card.dat").open("a") as stream:
            stream.write("# tampering\n")
        with self.assertRaises(ValueError):
            self.plan()

    def test_asset_at_size_limit_rejected(self):
        with patch.object(release, "ASSET_LIMIT_BYTES", (self.run / "sample.lhe.gz").stat().st_size):
            with self.assertRaisesRegex(release.PublicationError, "strictly smaller"):
                self.plan()

    def test_private_banner_rejected_without_editing_event_content(self):
        with gzip.open(self.run / "sample.lhe.gz", "rb") as stream:
            private_path = b"/" + b"home" + b"/privateuser/secret"
            data = stream.read().replace(b"<header>", b"<header>\n<!-- " + private_path + b" -->", 1)
        with (self.run / "sample.lhe.gz").open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
                stream.write(data)
        self.write_manifest()
        with self.assertRaisesRegex(release.PublicationError, "private paths"):
            self.plan()

    def transport(self, assets, fail_upload=False, tamper_download=False, existing=False):
        calls = []

        def fake(arguments):
            calls.append(arguments)
            if arguments[:2] == ["auth", "status"]:
                return ""
            if arguments[0] == "api":
                if "/commits/" in arguments[-1]:
                    return json.dumps({"sha": TARGET})
                if "/git/matching-refs/" in arguments[-1]:
                    return "[]"
                return json.dumps([[{"tag_name": "mg5-test-v1"}]] if existing else [[]])
            if arguments[:2] == ["release", "create"]:
                if fail_upload:
                    raise release.PublicationError("simulated upload failure")
                self.assertIn("--draft", arguments)
                self.assertNotIn("--clobber", arguments)
                return ""
            if arguments[:2] == ["release", "view"]:
                return json.dumps({"isDraft": True, "tagName": "mg5-test-v1", "targetCommitish": TARGET,
                                   "url": "https://github.com/example/draft",
                                   "assets": [{"name": a["name"], "size": a["size_bytes"]} for a in assets]})
            if arguments[:2] == ["release", "download"]:
                name = arguments[arguments.index("--pattern") + 1]
                output = Path(arguments[arguments.index("--dir") + 1]) / name
                shutil.copyfile(output.parent.parent / name, output)
                if tamper_download:
                    output.write_bytes(b"tampered")
                return ""
            self.fail("unexpected network command")

        return fake, calls

    def test_draft_upload_verified_using_mock_transport_only(self):
        plan, assets = self.plan()
        fake, calls = self.transport(assets)
        stage = self.root / "release_stage"
        with patch.object(release, "run_gh", fake):
            receipt = release.publish_plan(plan, assets, stage, TARGET)
        self.assertEqual(receipt["status"], "DRAFT_UPLOADED_VERIFIED")
        self.assertTrue(receipt["publication_verified"])
        self.assertEqual(len(receipt["verified_assets"]), 5)
        self.assertFalse(any(call[:2] == ["release", "edit"] for call in calls))

    def test_upload_failure_retains_explicit_partial_receipt(self):
        plan, assets = self.plan()
        fake, calls = self.transport(assets, fail_upload=True)
        stage = self.root / "release_stage"
        with patch.object(release, "run_gh", fake):
            with self.assertRaisesRegex(release.PublicationError, "partial draft"):
                release.publish_plan(plan, assets, stage, TARGET)
        receipt = json.loads((stage / "release_receipt.json").read_text())
        self.assertEqual(receipt["status"], "PARTIAL_OR_FAILED_DRAFT_UPLOAD")
        self.assertFalse(receipt["publication_verified"])

    def test_download_hash_mismatch_is_failure(self):
        plan, assets = self.plan()
        fake, _ = self.transport(assets, tamper_download=True)
        with patch.object(release, "run_gh", fake):
            with self.assertRaises(release.PublicationError):
                release.publish_plan(plan, assets, self.root / "stage", TARGET)

    def test_existing_release_refused_before_staging_or_upload(self):
        plan, assets = self.plan()
        fake, calls = self.transport(assets, existing=True)
        stage = self.root / "stage"
        with patch.object(release, "run_gh", fake):
            with self.assertRaisesRegex(release.PublicationError, "already exists"):
                release.publish_plan(plan, assets, stage, TARGET)
        self.assertFalse(stage.exists())
        self.assertFalse(any(call[:2] == ["release", "create"] for call in calls))


if __name__ == "__main__":
    unittest.main()
