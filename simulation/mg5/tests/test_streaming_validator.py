"""Streaming checks use actual MG5 references; mutations are test copies only."""
import gc
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import tracemalloc
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "simulation/mg5/scripts"))
import validate_lhe as legacy
import validate_sample as streaming

REFERENCE_DIR = REPO / legacy.SAMPLE_DIR


class StreamingValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = REFERENCE_DIR / "smoke_100.lhe.gz"
        cls.original = cls.path.read_bytes()
        cls.data = gzip.decompress(cls.original)

    def check_mutation(self, data, pattern):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.lhe"
            path.write_bytes(data)
            with self.assertRaisesRegex(streaming.ValidationError, pattern):
                streaming.validate_file(path, 100)

    def test_real_references_match_legacy_every_field(self):
        for sample, count in (("smoke_100", 100), ("reference_1000", 1000)):
            path = REFERENCE_DIR / (sample + ".lhe.gz")
            old = legacy.validate_file(path, count)
            current = streaming.validate_file(path, count)
            for key in old:
                self.assertEqual(current[key], old[key], key)

    def test_plain_and_gzip_have_identical_decompressed_event_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "sample.lhe"
            path.write_bytes(self.data)
            result = streaming.validate_file(path, 100)
            compressed = streaming.validate_file(self.path, 100)
            self.assertEqual(result["file_format"], "lhe")
            self.assertEqual(result["event_content_sha256"], compressed["event_content_sha256"])
            self.assertEqual(result["decompressed_file_sha256"], compressed["decompressed_file_sha256"])

    def test_input_and_decompressed_limits_enforced(self):
        for limits, message in (({"max_file_gb": 1e-8}, "input size"),
                                ({"max_decompressed_gb": 1e-8}, "decompressed size")):
            with self.assertRaisesRegex(streaming.ValidationError, message):
                streaming.validate_file(self.path, **limits)

    def test_no_fixed_40_mib_decompressed_limit(self):
        # Add XML comments BETWEEN real events, never invented/duplicated events.
        # This tests streaming size policy; it is not a generated physics sample.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "comment_size_test.lhe"
            position = self.data.index(b"</event>") + len(b"</event>")
            with path.open("wb") as stream:
                stream.write(self.data[:position])
                comment = b"\n<!--" + b"x" * (64 * 1024) + b"-->\n"
                for _ in range(650):
                    stream.write(comment)
                stream.write(self.data[position:])
            result = streaming.validate_file(path, 100)
            self.assertGreater(result["decompressed_bytes"], 40 * 1024 * 1024)
            original = streaming.validate_file(self.path, 100)
            self.assertEqual(result["event_content_sha256"], original["event_content_sha256"])

    def test_peak_memory_does_not_retain_all_1000_events(self):
        peaks = []
        for name, count in (("smoke_100", 100), ("reference_1000", 1000)):
            gc.collect()
            tracemalloc.start()
            try:
                streaming.validate_file(REFERENCE_DIR / (name + ".lhe.gz"), count)
                peaks.append(tracemalloc.get_traced_memory()[1])
            finally:
                tracemalloc.stop()
        self.assertLess(peaks[1], peaks[0] + 512 * 1024)
        self.assertLess(peaks[1], 4 * 1024 * 1024)

    def test_truncated_xml_rejected(self):
        self.check_mutation(self.data[:-100], "XML")

    def test_wrong_count_and_seed_rejected(self):
        with self.assertRaisesRegex(streaming.ValidationError, "count"):
            streaming.validate_file(self.path, 99)
        actual = int(streaming.validate_file(self.path)["run_values"]["iseed"])
        with self.assertRaisesRegex(streaming.ValidationError, "seed"):
            streaming.validate_file(self.path, expected_seed=actual + 1)

    def test_gzip_crc_and_truncation_rejected(self):
        for corrupt in (self.original[:-10], self.original[:-8] + b"\0" * 8):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "sample.lhe.gz"
                path.write_bytes(corrupt)
                with self.assertRaisesRegex(streaming.ValidationError, "gzip integrity"):
                    streaming.validate_file(path)

    def test_wrong_model_or_added_process_rejected(self):
        self.check_mutation(self.data.replace(b"import model sm-no_b_mass", b"import model sm"), "model")
        self.check_mutation(self.data.replace(b"generate p p > b b~ a a QCD=2 QED=2",
                                            b"generate p p > b b~ a a QCD=2 QED=2\nadd process p p > a a"), "process")

    def test_massive_b_parameter_rejected(self):
        data = re.sub(rb"(\n\s+5\s+)0\.000000e\+00(\s+# b)", rb"\g<1>4.7\2", self.data, count=1)
        self.assertNotEqual(data, self.data)
        self.check_mutation(data, "massless five-flavour")
        self.check_mutation(self.data.replace(b"BLOCK YUKAWA # ", b"BLOCK YUKAWA # \n      5 4.7"),
                            "zero b Yukawa")

    def test_pdf_mismatch_rejected(self):
        self.check_mutation(self.data.replace(b"cteq6l1", b"different_pdf"), "PDF")

    def test_nonfinite_and_bad_kinematics_rejected(self):
        position = self.data.index(b"<event>")
        prefix, tail = self.data[:position], self.data[position:].decode()
        for column, value, message in ((6, "nan", "non-finite"), (0, "4", "final state"),
                                       (9, None, "mass-shell")):
            lines = tail.splitlines(keepends=True)
            row = lines[4].split()
            row[column] = value if value is not None else str(float(row[column]) + 1)
            lines[4] = " ".join(row) + "\n"
            self.check_mutation(prefix + "".join(lines).encode(), message)

    def test_duplicate_header_and_unsafe_entities_rejected(self):
        header = re.search(rb"<header>.*?</header>", self.data, re.S)[0]
        self.check_mutation(self.data.replace(header, header + header, 1), "duplicate")
        version = re.search(rb"<MGVersion>.*?</MGVersion>", self.data, re.S)[0]
        self.check_mutation(self.data.replace(version, version + version, 1), "duplicate")
        self.check_mutation(b'<!DOCTYPE LesHouchesEvents [<!ENTITY x "unsafe">]>\n' + self.data, "DTD")

    def test_event_hash_ignores_comment_and_cdata_event_lookalikes(self):
        digest = streaming.EventDigest()
        real = b"<event id='1>0'>\nhello\n</event>"
        data = b"<!-- <event>comment</event> --><![CDATA[<event>cdata</event>]]>" + real
        for start in range(0, len(data), 3):
            digest.feed(data[start:start + 3])
        digest.finish()
        self.assertEqual(digest.count, 1)
        self.assertEqual(digest.digest.hexdigest(), hashlib.sha256(real).hexdigest())

    def test_large_xml_event_rejected_without_unbounded_memory(self):
        digest = streaming.EventDigest()
        digest.feed(b"<event>")
        with self.assertRaisesRegex(streaming.ValidationError, "16 MiB"):
            for _ in range(257):
                digest.feed(b"x" * (64 * 1024))

    def test_manifest_and_exact_cards_independently_rechecked(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sample = directory / "sample.lhe.gz"
            sample.write_bytes(self.original)
            result = streaming.validate_file(sample, 100)
            (directory / "cards").mkdir()
            hashes = {}
            for key, filename in (("process_card", "proc_card_mg5.dat"),
                                  ("run_card", "run_card.dat"), ("param_card", "param_card.dat")):
                path = directory / "cards" / filename
                path.write_text(result["cards"][key], encoding="utf-8")
                hashes[key + "_sha256"] = streaming.file_hash(path)
            rv = result["run_values"]
            manifest = {"schema_version": 1, "status": "PASS", "profile": "bbgg",
                        "process": streaming.PROCESS["bbgg"], "events_requested": 100,
                        "random_seed": int(rv["iseed"]), "sqrt_s_gev": 2 * float(rv["ebeam1"]),
                        "mg5_source_commit": streaming.SOURCE_COMMIT,
                        "source_identity": {"source_commit": streaming.SOURCE_COMMIT,
                                            "source_url": streaming.SOURCE_URL, "source_tag": streaming.SOURCE_TAG},
                        "card_hashes": hashes, "lhe_gz": "sample.lhe.gz",
                        "validation": {k: value for k, value in result.items() if k not in {"cards", "run_values"}}}
            path = directory / "run_manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(streaming.validate_run(directory)["run_manifest_validation"], "PASS")
            manifest["source_identity"]["source_commit"] = "0" * 40
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(streaming.ValidationError, "source identity"):
                streaming.validate_run(directory)
            manifest["source_identity"]["source_commit"] = streaming.SOURCE_COMMIT
            manifest["status"] = "PARTIAL_STOPPED"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(streaming.ValidationError, "complete PASS"):
                streaming.validate_run(directory)
            manifest["status"] = "PASS"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            manifest["validation"]["compressed_file_sha256"] = "0" * 64
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(streaming.ValidationError, "compressed_file_sha256"):
                streaming.validate_run(directory)
            manifest["validation"]["compressed_file_sha256"] = result["compressed_file_sha256"]
            path.write_text(json.dumps(manifest), encoding="utf-8")
            (directory / "cards/run_card.dat").write_text("altered card", encoding="utf-8")
            with self.assertRaisesRegex(streaming.ValidationError, "card hash"):
                streaming.validate_run(directory)

    def test_schema2_request_hash_and_requested_cards_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            sample = directory / "sample.lhe.gz"
            sample.write_bytes(self.original)
            result = streaming.validate_file(sample, 100)
            (directory / "cards").mkdir()
            hashes = {}
            for key, filename in (("process_card", "proc_card_mg5.dat"),
                                  ("run_card", "run_card.dat"), ("param_card", "param_card.dat")):
                path = directory / "cards" / filename
                path.write_text(result["cards"][key], encoding="utf-8")
                hashes[key + "_sha256"] = streaming.file_hash(path)
            rv = result["run_values"]
            request = {"profile": "bbgg", "process": streaming.PROCESS["bbgg"], "events_requested": 100,
                       "random_seed": int(rv["iseed"]), "sqrt_s_gev": 2 * float(rv["ebeam1"]),
                       "mg5_source_commit": streaming.SOURCE_COMMIT}
            attempt = directory / "attempts/attempt_001"
            attempt.mkdir(parents=True)
            supplied = attempt / "requested_process.mg5"
            supplied.write_text(result["cards"]["process_card"], encoding="utf-8")
            request["process_card_sha256"] = streaming.file_hash(supplied)
            manifest = {"schema_version": 2, "status": "PASS", **request, "request": request,
                        "request_sha256": streaming.sha256(json.dumps(request, sort_keys=True).encode()),
                        "attempt_directory": "attempts/attempt_001",
                        "source_identity": {"source_commit": streaming.SOURCE_COMMIT,
                                            "source_url": streaming.SOURCE_URL, "source_tag": streaming.SOURCE_TAG},
                        "card_hashes": hashes, "lhe_gz": "sample.lhe.gz",
                        "validation": {k: value for k, value in result.items() if k not in {"cards", "run_values"}}}
            path = directory / "run_manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(streaming.validate_run(directory)["run_manifest_validation"], "PASS")
            manifest["request_sha256"] = "0" * 64
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(streaming.ValidationError, "request hash"):
                streaming.validate_run(directory)
            manifest["request_sha256"] = streaming.sha256(json.dumps(request, sort_keys=True).encode())
            path.write_text(json.dumps(manifest), encoding="utf-8")
            supplied.write_text("altered process", encoding="utf-8")
            with self.assertRaisesRegex(streaming.ValidationError, "requested input card hash"):
                streaming.validate_run(directory)

    def test_partial_run_and_escaping_path_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = {"lhe_gz": "../outside.lhe.gz"}
            (directory / "run_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(streaming.ValidationError, "escapes"):
                streaming.validate_run(directory)

    def test_original_reference_unchanged(self):
        self.assertEqual(self.path.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
