"""Synthetic API/failure guards only; these are not physical shower samples."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import audit_shower
import publish_shower_references as publisher


class PublicationApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.header = b"HepMC::Version 3.03.01\nHepMC::Asciiv3-START_EVENT_LISTING\n"
        self.footer = b"HepMC::Asciiv3-END_EVENT_LISTING\n"
        # No particles and no physics validation: exercise the block-copy API.
        self.blocks = [f"E {index} 0 0\nU GEV MM\nW 1.00000000000000000e-03\n".encode()
                       for index in range(1, 1001)]
        self.source = self.root / "synthetic_api_records.hepmc3"
        self.source.write_bytes(self.header + b"".join(self.blocks) + self.footer)

    def tearDown(self):
        self.directory.cleanup()

    def test_block_copy_preserves_all_selected_bytes_without_reserialization(self):
        output = self.root / "prefix.hepmc3"
        report = publisher.select_prefix(self.source, output)
        self.assertEqual(output.read_bytes(), self.header + b"".join(self.blocks[:100]) + self.footer)
        self.assertEqual(report["event_content_sha256"], hashlib.sha256(b"".join(self.blocks[:100])).hexdigest())
        self.assertEqual(report["event_numbers"], list(range(1, 101)))

    def test_truncated_full_stream_cannot_be_claimed_as1000(self):
        self.source.write_bytes(self.header + b"".join(self.blocks[:999]) + self.footer)
        with self.assertRaises(ValueError):
            publisher.select_prefix(self.source, self.root / "bad.hepmc3")

    def test_missing_footer_rejected(self):
        self.source.write_bytes(self.header + b"".join(self.blocks))
        with self.assertRaises(ValueError):
            publisher.select_prefix(self.source, self.root / "bad.hepmc3")

    def test_ledger_selection_preserves_original_lines_and_event_mapping(self):
        rows = [json.dumps({"output_event_index": i, "source_event_index": 1000-i,
                            "output_event_hash": str(i)}, separators=(",", ":")).encode() + b"\n"
                for i in range(1, 1001)]
        ledger = self.root / "ledger.jsonl"
        ledger.write_bytes(b"".join(rows))
        target = self.root / "selected.jsonl"
        publisher.select_ledger(ledger, target, [2, 1])
        self.assertEqual(target.read_bytes(), rows[1] + rows[0])

    def test_duplicate_ledger_output_index_rejected(self):
        ledger = self.root / "ledger.jsonl"
        ledger.write_text('{"output_event_index":1}\n{"output_event_index":1}\n')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            publisher.select_ledger(ledger, self.root / "bad.jsonl", [1])

    def test_deterministic_gzip_changes_container_only(self):
        first, second = self.root / "one.gz", self.root / "two.gz"
        publisher.deterministic_gzip(self.source, first)
        publisher.deterministic_gzip(self.source, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(gzip.decompress(first.read_bytes()), self.source.read_bytes())
        self.assertEqual(first.read_bytes()[4:8], b"\0\0\0\0")
        self.assertFalse(first.read_bytes()[3] & 8)

    def test_full_release_gzip_must_match_verified_ascii(self):
        target = self.root / "full.gz"
        publisher.deterministic_gzip(self.source, target)
        raw = self.source.read_bytes()
        publisher.verify_full_gzip(target, hashlib.sha256(raw).hexdigest(), len(raw))
        with self.assertRaisesRegex(ValueError, "differs"):
            publisher.verify_full_gzip(target, "0" * 64, len(raw))
        with self.assertRaisesRegex(ValueError, "beyond"):
            publisher.verify_full_gzip(target, hashlib.sha256(raw).hexdigest(), len(raw) - 1)

    def test_corrupt_full_release_gzip_crc_rejected(self):
        target = self.root / "full.gz"
        publisher.deterministic_gzip(self.source, target)
        damaged = bytearray(target.read_bytes())
        damaged[-8] ^= 1
        target.write_bytes(damaged)
        with self.assertRaises(gzip.BadGzipFile):
            publisher.verify_full_gzip(target, hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source.stat().st_size)

    def test_truncated_full_release_gzip_rejected(self):
        target = self.root / "full.gz"
        publisher.deterministic_gzip(self.source, target)
        target.write_bytes(target.read_bytes()[:-4])
        with self.assertRaises(EOFError):
            publisher.verify_full_gzip(target, hashlib.sha256(self.source.read_bytes()).hexdigest(), self.source.stat().st_size)

    def test_unselected_archive_and_unapproved_figure_rejected(self):
        for path in ("reference_samples/pythia8/unselected.hepmc3.gz", "reports/new.png"):
            with self.assertRaises(ValueError):
                audit_shower.inspect(path, b"synthetic API guard")

    def test_private_path_rejected_in_textual_payload(self):
        private = "/" + "home" + "/undocumented-user/private"
        with self.assertRaisesRegex(ValueError, "private"):
            audit_shower.inspect("simulation/pythia8/evidence/private.json", private.encode())


if __name__ == "__main__":
    unittest.main()
