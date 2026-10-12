"""Adversarial tests mutate copies of real MG5 outputs; no invented samples."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/mg5/scripts"))
import validate_lhe as v
from generate_sample import gzip_deterministic, profile_from_card


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = REPO / v.SAMPLE_DIR / "smoke_100.lhe.gz"
        cls.original = cls.path.read_bytes()
        cls.data = gzip.decompress(cls.original)

    def reject(self, data, pattern=None):
        with self.assertRaisesRegex(v.ValidationError, pattern or ".*"):
            v.validate_data(data, 100)

    def mutate_first_particle(self, column, replacement):
        text = self.data.decode()
        start = text.index("<event>")
        before, event = text[:start], text[start:]
        lines = event.splitlines(keepends=True)
        row = lines[4].split()  # first outgoing b (two initial particles precede it)
        row[column] = replacement(row[column]) if callable(replacement) else replacement
        lines[4] = " ".join(row) + "\n"
        return (before + "".join(lines)).encode()

    def test_real_references(self):
        self.assertEqual(v.validate_repository(REPO)["status"], "PASS")

    def test_truncated_xml(self):
        self.reject(self.data[:-100], "XML")

    def test_wrong_event_count(self):
        with self.assertRaisesRegex(v.ValidationError, "count"):
            v.validate_data(self.data, 99)

    def test_nan(self):
        self.reject(self.mutate_first_particle(6, "nan"), "non-finite")

    def test_wrong_final_pdg(self):
        self.reject(self.mutate_first_particle(0, "4"), "final state")

    def test_bad_mass_shell(self):
        self.reject(self.mutate_first_particle(9, lambda value: str(float(value) + 1)), "mass-shell")

    def test_momentum_closure_preserving_shell(self):
        self.reject(self.mutate_first_particle(6, lambda value: str(-float(value))), "closure")

    def test_bad_mothers(self):
        self.reject(self.mutate_first_particle(2, "3"), "mother")

    def test_negative_weight(self):
        data = re.sub(rb"(<event>\s*6\s+1\s+)\+", rb"\1-", self.data, count=1)
        self.reject(data, "non-positive")

    def test_zero_weight(self):
        data = re.sub(rb"(<event>\s*6\s+1\s+)\S+", rb"\g<1>0.0", self.data, count=1)
        self.reject(data, "non-positive")

    def test_missing_card(self):
        self.reject(re.sub(rb"<slha>.*?</slha>", b"", self.data, flags=re.S), "cards missing")

    def test_wrong_generator(self):
        self.reject(self.data.replace(b"<MGVersion>\n3.5.16", b"<MGVersion>\n3.5.15"), "version")

    def test_gzip_truncation_and_crc(self):
        for data in (self.original[:-10], self.original[:-8] + b"\0" * 8):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "sample.lhe.gz"
                path.write_bytes(data)
                with self.assertRaisesRegex(v.ValidationError, "gzip integrity"):
                    v.validate_file(path)

    def test_deterministic_gzip(self):
        self.assertEqual(gzip_deterministic(self.data), self.original)
        self.assertEqual(gzip_deterministic(self.data), gzip_deterministic(self.data))

    def test_manifest_hash_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            import shutil
            shutil.copytree(REPO / v.SAMPLE_DIR, destination / v.SAMPLE_DIR)
            shutil.copytree(REPO / "simulation/mg5", destination / "simulation/mg5")
            path = destination / v.SAMPLE_DIR / "sample_manifest.json"
            manifest = json.loads(path.read_text())
            manifest["samples"][0]["compressed_file_sha256"] = "0" * 64
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(v.ValidationError, "compressed_file_sha256"):
                v.validate_repository(destination)

    def test_unknown_process_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            card = Path(directory) / "process.mg5"
            card.write_text("# validation_profile: bbgg\nimport model sm\ngenerate p p > a a\n")
            with self.assertRaisesRegex(ValueError, "reviewed physics profile"):
                profile_from_card(card)

    def test_both_registered_process_cards(self):
        for profile in ("bbgg", "diphoton"):
            self.assertEqual(profile_from_card(REPO / f"simulation/mg5/cards/{profile}.mg5")[0], profile)

    def test_original_files_unchanged(self):
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_nonfinite_weight(self):
        data = re.sub(rb"(<event>\s*6\s+1\s+)\S+", rb"\g<1>inf", self.data, count=1)
        self.reject(data, "non-finite")

    def test_dtd_rejected(self):
        self.reject(b'<!DOCTYPE LesHouchesEvents [<!ENTITY x "unsafe">]>\n' + self.data, "DTD")

    def test_card_provenance_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            import shutil
            shutil.copytree(REPO / v.SAMPLE_DIR, destination / v.SAMPLE_DIR)
            shutil.copytree(REPO / "simulation/mg5", destination / "simulation/mg5")
            path = destination / "simulation/mg5/cards/smoke_100/param_card.dat"
            path.write_text(path.read_text() + "\n# altered provenance\n")
            with self.assertRaisesRegex(v.ValidationError, "card hash"):
                v.validate_repository(destination)

    def test_manifest_cut_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            import shutil
            shutil.copytree(REPO / v.SAMPLE_DIR, destination / v.SAMPLE_DIR)
            shutil.copytree(REPO / "simulation/mg5", destination / "simulation/mg5")
            path = destination / v.SAMPLE_DIR / "sample_manifest.json"
            manifest = json.loads(path.read_text())
            manifest["samples"][0]["generation_cuts"]["photon_pt_min_gev"] = 24
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(v.ValidationError, "manifest generation cuts"):
                v.validate_repository(destination)


if __name__ == "__main__":
    unittest.main()
