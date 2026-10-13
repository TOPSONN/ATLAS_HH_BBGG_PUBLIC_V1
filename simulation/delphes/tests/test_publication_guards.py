"""Synthetic publication/API failure fixtures; never physical ROOT references."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish_references as publication
import audit_payload as audit


class PublicationGuards(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_non_root_signature_is_rejected(self):
        path = self.directory / "api_fixture.root"
        path.write_bytes(b"not a ROOT file")
        with self.assertRaisesRegex(ValueError, "magic"):
            publication.inspect_root(path)

    def test_oversized_api_fixture_cannot_be_repository_reference(self):
        path = self.directory / "api_fixture.root"
        with path.open("wb") as stream:
            stream.write(b"root")
            stream.truncate(publication.CAP + 1)
        with self.assertRaisesRegex(ValueError, "10MiB"):
            publication.inspect_root(path)

    def test_visible_private_data_rejected_across_chunk_boundary(self):
        path = self.directory / "api_fixture.root"
        private = b"/" + b"home" + b"/undocumented-user/private"
        raw = b"root" + b"x" * (1024**2-7) + private
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "private"):
            publication.inspect_root(path)

    def test_partial_run_rejected_before_any_reference_files(self):
        path = self.directory / "run_manifest.json"
        path.write_text('{"status":"PARTIAL","process":"bbgg","events_requested":100}')
        with self.assertRaisesRegex(ValueError, "genuine"):
            publication.prepare("bbgg", self.directory)

    def test_later_invalid_process_prevents_all_public_writes(self):
        source = self.directory / "api_source.txt"
        source.write_text("synthetic API control payload")
        first = ("reference_samples/delphes/api/sample_manifest.json", {"root_file": {"bytes": 4}},
                 {"reference_samples/delphes/api/detector_100.root": source})
        with patch.object(publication, "REPO", self.directory), patch.object(publication, "prepare", side_effect=[first, ValueError("invalid second process")]), \
             patch.object(sys, "argv", ["publish_references.py", "--bbgg-run", "one", "--ccgg-run", "two", "--jjgg-run", "three"]):
            self.assertEqual(publication.main(), 1)
        self.assertFalse((self.directory / "reference_samples").exists())
        self.assertFalse((self.directory / "simulation").exists())

    def test_oversized_verified_plan_writes_only_concrete_release_proposal(self):
        plans = [(f"reference_samples/delphes/{profile}/sample_manifest.json",
                  {"root_file": {"bytes": publication.CAP + 1, "sha256": "a" * 64}}, {})
                 for profile in publication.PROFILES]
        with patch.object(publication, "REPO", self.directory), patch.object(publication, "prepare", side_effect=plans), \
             patch.object(sys, "argv", ["publish_references.py", "--bbgg-run", "one", "--ccgg-run", "two", "--jjgg-run", "three"]):
            self.assertEqual(publication.main(), 2)
        import json
        proposal = json.loads((self.directory / "simulation/delphes/evidence/large_root_release_proposal.json").read_text())
        self.assertEqual(len(proposal["proposed_assets"]), 3)
        self.assertFalse(proposal["release_created"])
        self.assertFalse(proposal["assets_uploaded"])
        self.assertFalse((self.directory / "reference_samples").exists())

    def test_documented_user_path_is_allowed_only_in_markdown(self):
        documented = b"/" + b"home" + b"/btu/simulations/delphes_runs/example"
        audit.inspect("simulation/delphes/USER_GUIDE_ZH_TW.md", documented)
        with self.assertRaisesRegex(ValueError, "private"):
            audit.inspect("reference_samples/delphes/example/sample_manifest.json", documented)
        with self.assertRaisesRegex(ValueError, "private"):
            audit.inspect(next(iter(audit.ROOT_REFERENCES)), b"root" + documented)

    def test_unselected_root_and_figures_are_rejected(self):
        for path in ("reference_samples/delphes/example/unselected.root", "reports/unapproved.pdf", "reports/unapproved.png"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                audit.inspect(path, b"root")

    def test_ten_mib_plaintext_index_budget_is_limited_to_selected_paths(self):
        raw = b"x" * (7 * 1024**2)
        audit.inspect(next(iter(audit.INPUT_INDICES)), raw)
        with self.assertRaisesRegex(ValueError, "size cap"):
            audit.inspect("reference_samples/delphes/other/input_event_index.dat", raw)
        with self.assertRaisesRegex(ValueError, "size cap"):
            audit.inspect(next(iter(audit.INPUT_INDICES)), raw + b"x" * (4 * 1024**2))


if __name__ == "__main__":
    unittest.main()
