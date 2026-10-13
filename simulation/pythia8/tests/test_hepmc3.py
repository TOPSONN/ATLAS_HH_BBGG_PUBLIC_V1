"""Portable readback tests based on actual produced events.

Mutated copies test rejection or weight serialization APIs only. They are
never physics references. CI uses the published raw prefix; during staged
development a physically validated local ten-event run is an explicit fallback.
"""
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/pythia8/scripts"))
import validate_hepmc3 as validator


class HepMC3PortableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reference = REPO / "reference_samples/pythia8/pp_bbgg_sm_lo_ps_13tev"
        if (reference / "shower_100.hepmc3.gz").exists():
            cls.path = reference / "shower_100.hepmc3.gz"
            cls.ledger = reference / "event_ledger_100.jsonl"
            cls.count = 100
        else:
            local = Path("/home/btu/simulations/pythia8_runs/stage_a_bbgg_10_v2")
            if not (local / "shower.hepmc3").exists():
                raise unittest.SkipTest("actual published HepMC3 prefix has not been prepared")
            cls.path, cls.ledger, cls.count = local / "shower.hepmc3", local / "event_ledger.jsonl", 10
        cls.source = REPO / validator.SOURCE_SAMPLES["bbgg"][0]
        cls.source_hash = validator.SOURCE_SAMPLES["bbgg"][1]
        cls.data = gzip.decompress(cls.path.read_bytes()) if cls.path.suffix == ".gz" else cls.path.read_bytes()
        cls.parts = list(validator.iter_ascii(cls.path))
        cls.header = validator.parse_header(cls.parts[0][1])
        cls.first = next(raw for kind, raw in cls.parts if kind == "event")

    def check_copy(self, data, **options):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "API_ONLY.hepmc3"
            path.write_bytes(data)
            return validator.validate_file(path, expected_events=self.count, **options)

    def rejected(self, data, message):
        with self.assertRaisesRegex(validator.ValidationError, message):
            self.check_copy(data)

    def test_actual_source_ledger_and_all_event_graphs(self):
        result = validator.validate_file(self.path, self.count, ledger=self.ledger, source_file=self.source,
                                         source_sha256=self.source_hash, sample_id="bbgg")
        self.assertEqual(result["validation_status"], "PASS")
        self.assertEqual(result["N_readback"], self.count)
        self.assertEqual(result["physical_library_readback"], "NOT_EVALUATED_BY_PYTHON")
        self.assertEqual(result["decompressed_file_sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertLess(result["max_beam_to_stable_residual_gev"], 2.3e-5)

    def test_exact_raw_blocks_are_not_reserialized(self):
        self.assertEqual(b"".join(raw for _, raw in self.parts), self.data)
        events = [raw for kind, raw in self.parts if kind == "event"]
        self.assertEqual(len(events), self.count)
        self.assertEqual(validator.parse_event(events[0], self.header)["event_hash"], hashlib.sha256(events[0]).hexdigest())

    def test_wrong_units_rejected(self):
        self.rejected(self.data.replace(b"U GEV MM", b"U MEV MM", 1), "GeV/mm")

    def test_nonfinite_fourvector_rejected(self):
        data = re.sub(rb"(^P \d+ -?\d+ -?\d+) \S+", rb"\1 nan", self.data, count=1, flags=re.M)
        self.rejected(data, "non-finite")

    def test_missing_daughter_parent_rejected(self):
        # Change a real non-beam particle's production reference only.
        data = re.sub(rb"(^P \d+) (-?[1-9]\d*) ", rb"\1 -2147483000 ", self.data, count=1, flags=re.M)
        self.rejected(data, "dangling")

    def test_wrong_final_momentum_rejected(self):
        lines = self.data.splitlines(keepends=True)
        for i, line in enumerate(lines):
            row = line.split()
            if row and row[0] == b"P" and row[-1] == b"1":
                row[7] = str(float(row[7]) + 1.0).encode()
                lines[i] = b" ".join(row) + b"\n"
                break
        self.rejected(b"".join(lines), "four-momentum closure")

    def test_duplicate_event_index_rejected(self):
        data = re.sub(rb"^E 2 ", b"E 1 ", self.data, count=1, flags=re.M)
        self.rejected(data, "index|sequential")

    def test_extra_data_after_footer_rejected(self):
        self.rejected(self.data + b"E 999 1 2\n", "after HepMC footer")

    def test_missing_footer_rejected(self):
        self.rejected(self.data.replace(validator.END, b""), "missing/truncated")

    def test_empty_record_list_rejected(self):
        self.rejected(self.parts[0][1] + validator.END, "no events")

    def test_wrong_expected_count_rejected(self):
        with self.assertRaisesRegex(validator.ValidationError, "count"):
            validator.validate_file(self.path, expected_events=self.count + 1)

    def test_gzip_crc_failure_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "corrupt.hepmc3.gz"
            compressed = bytearray(gzip.compress(self.data, mtime=0))
            compressed[-8] ^= 1
            path.write_bytes(compressed)
            with self.assertRaisesRegex(validator.ValidationError, "gzip|integrity"):
                validator.validate_file(path, self.count)

    def test_ledger_original_source_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "API_ONLY_ledger.jsonl"
            rows = self.ledger.read_text().splitlines()
            row = json.loads(rows[0]); row["source_event_content_hash"] = "0" * 64
            rows[0] = json.dumps(row)
            path.write_text("\n".join(rows) + "\n")
            with self.assertRaisesRegex(validator.ValidationError, "source|identity|indexed LHE"):
                validator.validate_file(self.path, self.count, ledger=path, source_file=self.source)

    def test_signed_weight_serialization_api_preserves_signs(self):
        # Metadata serialization test without a source ledger: explicitly not a
        # generated signed physics sample or an independently normalized reference.
        def negative(match):
            return b"W " + b" ".join(str(-float(value)).encode() for value in match[1].split())
        data = b"".join(re.sub(rb"^W ([^\n]+)$", negative, raw, flags=re.M) if kind == "event" else raw
                        for kind, raw in self.parts)
        result = self.check_copy(data)
        moments = result["weight_moments_by_name"]["input_contribution_pb"]
        self.assertEqual(moments["negative"], self.count)
        self.assertLess(moments["sum"], 0)
        self.assertGreater(moments["sum_abs"], 0)
        self.assertEqual(result["event_identity"], "ATTRIBUTES_ONLY")

    def test_size_budget_is_enforced(self):
        with self.assertRaisesRegex(validator.ValidationError, "size limit"):
            validator.validate_file(self.path, self.count, max_decompressed_gb=1e-12)

    def test_reviewed_baseline_card_identity(self):
        path = REPO / "simulation/pythia8/config/baseline_shower.cmnd"
        self.assertEqual(validator.file_sha256(path), validator.BASELINE_SETTINGS_SHA256)
        diagnostic = REPO / "simulation/pythia8/config/diagnostic_collinear_disabled.cmnd"
        self.assertNotEqual(validator.file_sha256(diagnostic), validator.BASELINE_SETTINGS_SHA256)

    def test_actual_schema_weight_columns_are_independently_checked(self):
        original = json.loads(self.ledger.read_text().splitlines()[0])
        cases = [("pythia_weight_pb", original["pythia_weight_pb"] * 1.1),
                 ("lhe_weight_pb", original["lhe_weight_pb"] * 1.1),
                 ("converter_weights_pb", [original["converter_weights_pb"][0] * 1.1]),
                 ("input_contribution_pb", original["input_contribution_pb"] * 10),
                 ("source_total_events", 100)]
        for name, value in cases:
            row = dict(original); row[name] = value
            with self.subTest(column=name), self.assertRaises(validator.ValidationError):
                validator.ledger_weight_vector(row, expected_source_events=1000)

    def test_missing_actual_schema_weight_fields_rejected(self):
        row = json.loads(self.ledger.read_text().splitlines()[0])
        row.pop("converter_weights_pb")
        with self.assertRaisesRegex(validator.ValidationError, "required actual-schema"):
            validator.ledger_weight_vector(row, expected_source_events=1000)

    def test_converter_output_mutation_rejected_even_with_recomputed_ledger_hash(self):
        parts = list(self.parts)
        first_index = next(i for i, (kind, _) in enumerate(parts) if kind == "event")
        def alter(match):
            values = match[1].split(); values[3] = str(float(values[3]) * 2).encode()
            return b"W " + b" ".join(values)
        altered = re.sub(rb"^W ([^\n]+)$", alter, parts[first_index][1], flags=re.M)
        parts[first_index] = ("event", altered)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "API_ONLY_ledger.jsonl"
            rows = self.ledger.read_text().splitlines()
            row = json.loads(rows[0]); row["output_event_hash"] = hashlib.sha256(altered).hexdigest()
            rows[0] = json.dumps(row); path.write_text("\n".join(rows) + "\n")
            with self.assertRaisesRegex(validator.ValidationError, "stored weight vector"):
                self.check_copy(b"".join(raw for _, raw in parts), ledger=path, source_file=self.source)

    def test_published_repository_full_ledger_and_physics_evidence(self):
        if not (REPO / validator.REFERENCE_DIRS["jjgg"] / "sample_manifest.json").exists():
            raise unittest.SkipTest("actual published three-process prefixes have not been prepared")
        result = validator.validate_repository(REPO)
        self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
