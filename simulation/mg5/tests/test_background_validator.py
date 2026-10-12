"""Adversarial copies of real MG5 events; no fabricated passing physics data."""
import gzip
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/mg5/scripts"))
import validate_lhe as v


def mutate_particle(data, predicate, change):
    match = re.search(rb"<event>.*?</event>", data, re.S)
    if not match:
        raise AssertionError("real event not found")
    lines = match[0].decode().splitlines(keepends=True)
    for index, line in enumerate(lines):
        row = line.split()
        if len(row) == 13 and re.fullmatch(r"[+-]?\d+", row[0]) and predicate(row):
            change(row)
            lines[index] = " ".join(row) + "\n"
            return data[:match.start()] + "".join(lines).encode() + data[match.end():]
    raise AssertionError("target particle not found in first real event")


class GenericProfileChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = gzip.decompress((REPO / v.SAMPLE_DIR / "smoke_100.lhe.gz").read_bytes())

    def test_old_sample_cannot_be_relabelled_charm_or_light_jets(self):
        for profile in ("ccgg", "jjgg"):
            with self.assertRaisesRegex(v.ValidationError, "process/orders"):
                v.validate_data(self.data, 100, profile=profile)

    def test_quark_and_gluon_color_assignments(self):
        for predicate, change, message in (
            (lambda r: r[0] == "5", lambda r: r.__setitem__(5, "501"), "quark/antiquark color"),
            (lambda r: r[0] == "-5", lambda r: r.__setitem__(4, "501"), "quark/antiquark color"),
        ):
            with self.assertRaisesRegex(v.ValidationError, message):
                v.validate_data(mutate_particle(self.data, predicate, change), 100)

    def test_color_flow_conservation(self):
        corrupt = mutate_particle(self.data, lambda r: r[0] == "5" and r[1] == "1",
                                  lambda r: r.__setitem__(4, "9999"))
        with self.assertRaisesRegex(v.ValidationError, "color-flow"):
            v.validate_data(corrupt, 100)

    def test_massless_charm_parameter_is_required(self):
        data = re.sub(rb"(\n\s+4\s+)0\.000000e\+00(\s+# c)", rb"\g<1>1.27\2", self.data, count=1)
        self.assertNotEqual(data, self.data)
        with self.assertRaisesRegex(v.ValidationError, "massless five-flavour"):
            v.validate_data(data, 100)

    def test_duplicate_generator_card_and_changed_pdf_rejected(self):
        card = re.search(rb"<slha>.*?</slha>", self.data, re.S)[0]
        for data, message in ((self.data.replace(card, card + card, 1), "duplicate"),
                              (self.data.replace(b"cteq6l1", b"different_pdf"), "PDF")):
            with self.assertRaisesRegex(v.ValidationError, message):
                v.validate_data(data, 100)


class RealBackgroundLibraryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = {profile: REPO / directory / "reference_1000.lhe.gz"
                     for profile, directory in v.BACKGROUND_DIRS.items()}
        cls.data = {profile: gzip.decompress(path.read_bytes()) for profile, path in cls.paths.items()}

    def test_actual_1000_each_and_total_3000_excludes_smoke(self):
        result = v.validate_background_library(REPO)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["actual_reference_events"], 3000)
        self.assertEqual(result["smoke_events_excluded"], 100)
        self.assertEqual([sample["actual_events"] for sample in result["samples"]], [1000] * 3)
        self.assertEqual({sample["physics_profile"] for sample in result["samples"]}, {"bbgg", "ccgg", "jjgg"})

    def test_actual_final_pdg_contents(self):
        charm = v.validate_file(self.paths["ccgg"], 1000, profile="ccgg")
        self.assertEqual(charm["outgoing_pdg_counts"], {-4: 1000, 4: 1000, 22: 2000})
        jets = v.validate_file(self.paths["jjgg"], 1000, profile="jjgg")
        self.assertEqual(jets["outgoing_pdg_counts"][22], 2000)
        self.assertEqual(sum(jets["outgoing_pdg_counts"].values()), 4000)
        self.assertTrue(set(jets["outgoing_pdg_counts"]) <= v.LIGHT_JETS | {22})

    def test_charm_cannot_be_relabelled_as_bottom(self):
        data = mutate_particle(self.data["ccgg"], lambda r: r[0] == "4" and r[1] == "1",
                               lambda r: r.__setitem__(0, "5"))
        with self.assertRaisesRegex(v.ValidationError, "final state"):
            v.validate_data(data, 1000, profile="ccgg")

    def test_heavy_flavour_contamination_of_light_jets_rejected(self):
        for flavour in (4, 5):
            def change(row):
                row[0] = str(flavour)
                row[4], row[5] = "501", "0"
            data = mutate_particle(self.data["jjgg"], lambda r: int(r[0]) in v.LIGHT_JETS and r[1] == "1", change)
            with self.assertRaisesRegex(v.ValidationError, "light-jet process"):
                v.validate_data(data, 1000, profile="jjgg")

    def test_nonzero_charge_light_jet_channels_are_validated(self):
        # qg -> qg gamma gamma carries the incoming quark's charge into the final state.
        charge = {21: 0, 22: 0, 1: -1, 2: 2, 3: -1, 4: 2, 5: -1}
        found = False
        for event in ET.fromstring(self.data["jjgg"]).findall("event"):
            rows = v.records(event.text)[1:]
            incoming = [int(row[0]) for row in rows if row[1] == "-1"]
            total = sum(charge[abs(pdg)] * (1 if pdg > 0 else -1) for pdg in incoming)
            if total:
                found = True
                break
        self.assertTrue(found, "actual sample must exercise charged light-jet channels")
        self.assertEqual(v.validate_data(self.data["jjgg"], 1000, profile="jjgg")["validation_status"], "PASS")

    def test_charged_final_flavour_mutation_rejected(self):
        # Find a real event with a final u or d/s, keeping its color and momentum.
        data = self.data["jjgg"]
        for match in re.finditer(rb"<event>.*?</event>", data, re.S):
            if any(len(row) == 13 and row[1] == "1" and abs(int(row[0])) in {1, 2, 3}
                   for row in v.records(ET.fromstring(match[0]).text)[1:]):
                chosen = match
                break
        else:
            self.fail("actual sample has no final quark")
        before = data[:chosen.start()]
        tail = data[chosen.start():]
        def change(row):
            old = int(row[0])
            row[0] = str((1 if abs(old) == 2 else 2) * (1 if old > 0 else -1))
        corrupt = before + mutate_particle(tail, lambda r: r[1] == "1" and abs(int(r[0])) in {1, 2, 3}, change)
        with self.assertRaisesRegex(v.ValidationError, "electric-charge"):
            v.validate_data(corrupt, 1000, profile="jjgg")

    def test_actual_jet_cut_and_light_definition_are_checked(self):
        # Raising a declared cut on unchanged real events must fail, never silently filter.
        for key in (b"ptj", b"drjj", b"draj"):
            data = re.sub(rb"(?m)^\s*[^=\n]+(?=\s*=\s*" + key + rb"\s*!?)",
                          b" 10000.0 ", self.data["jjgg"], count=1)
            self.assertNotEqual(data, self.data["jjgg"])
            with self.assertRaisesRegex(v.ValidationError, "cut failure"):
                v.validate_data(data, 1000, profile="jjgg")
        data = self.data["jjgg"].replace(b"define jl = g u u~ d d~ s s~", b"define jl = g u u~ d d~ s s~ c c~")
        with self.assertRaisesRegex(v.ValidationError, "light-jet definition"):
            v.validate_data(data, 1000, profile="jjgg")

    def test_same_charge_d_to_s_flavour_mutation_rejected(self):
        # d and s have identical charge, color representation and zero model
        # mass; changing only flavour must still violate these amplitudes.
        data = self.data["jjgg"]
        for match in re.finditer(rb"<event>.*?</event>", data, re.S):
            if any(len(row) == 13 and row[1] == "1" and abs(int(row[0])) in {1, 3}
                   for row in v.records(ET.fromstring(match[0]).text)[1:]):
                chosen = match
                break
        else:
            self.fail("actual sample has no final d/s quark")
        def change(row):
            old = int(row[0])
            row[0] = str((3 if abs(old) == 1 else 1) * (1 if old > 0 else -1))
        corrupt = data[:chosen.start()] + mutate_particle(
            data[chosen.start():], lambda r: r[1] == "1" and abs(int(r[0])) in {1, 3}, change)
        with self.assertRaisesRegex(v.ValidationError, "quark-flavour"):
            v.validate_data(corrupt, 1000, profile="jjgg")

    def test_missing_events_rejected_with_validation_error(self):
        for profile in v.BACKGROUND_DIRS:
            data = re.sub(rb"<event>.*?</event>", b"", self.data[profile], flags=re.S)
            with self.assertRaisesRegex(v.ValidationError, "contains no events"):
                v.validate_data(data, 1000, profile=profile)

    def test_manifest_card_hash_count_and_cut_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            for directory in (v.SAMPLE_DIR, *v.BACKGROUND_DIRS.values(), "simulation/mg5"):
                shutil.copytree(REPO / directory, destination / directory)
            path = destination / v.BACKGROUND_DIRS["ccgg"] / "sample_manifest.json"
            original = json.loads(path.read_text())
            for key, value, message in (("compressed_file_sha256", "0" * 64, "compressed_file_sha256"),
                                        ("actual_events", 999, "count"),
                                        ("random_seed", 1, "seed")):
                manifest = json.loads(json.dumps(original))
                manifest["samples"][0][key] = value
                path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(v.ValidationError, message):
                    v.validate_background_library(destination)
            manifest = json.loads(json.dumps(original))
            manifest["samples"][0]["generation_cuts"]["jet_pt_min_gev"] = 19
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(v.ValidationError, "generation cuts"):
                v.validate_background_library(destination)
            path.write_text(json.dumps(original))
            card = destination / original["samples"][0]["param_card_path"]
            card.write_text(card.read_text() + "\n# altered provenance\n")
            with self.assertRaisesRegex(v.ValidationError, "card hash"):
                v.validate_background_library(destination)

    def test_new_profiles_reject_truncation_nan_and_wrong_count(self):
        for profile in v.BACKGROUND_DIRS:
            data = self.data[profile]
            for corrupted, message in ((data[:-100], "XML"),
                                        (mutate_particle(data, lambda r: r[1] == "1",
                                                         lambda r: r.__setitem__(6, "nan")), "non-finite")):
                with self.assertRaisesRegex(v.ValidationError, message):
                    v.validate_data(corrupted, 1000, profile=profile)
            with self.assertRaisesRegex(v.ValidationError, "count"):
                v.validate_data(data, 999, profile=profile)


if __name__ == "__main__":
    unittest.main()
