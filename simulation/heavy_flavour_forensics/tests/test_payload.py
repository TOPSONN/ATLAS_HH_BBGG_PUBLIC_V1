"""Publication boundary API fixtures; no physics reference or production."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_payload


class PublicationControls(unittest.TestCase):
    def test_exact_new_card_exceptions_do_not_allow_historical_changes(self):
        for path in audit_payload.CARDS:
            audit_payload.inspect(path, b"# proposal\n")
        for path in ("simulation/mg5/scripts/generate_sample.py", "simulation/rare_backgrounds/README.md",
                     "reference_samples/delphes/example.json", "simulation/mg5/cards/other_candidate.mg5"):
            with self.assertRaisesRegex(ValueError, "historical/unrelated"):
                audit_payload.inspect(path, b"{}\n")

    def test_small_selected_graph_json_and_summary_allowed(self):
        audit_payload.inspect("simulation/heavy_flavour_forensics/evidence/source997.json", b"{}\n")
        with self.assertRaisesRegex(ValueError, "2MiB"):
            audit_payload.inspect("simulation/heavy_flavour_forensics/evidence/oversized.json", b"x" * (2 * 1024**2 + 1))

    def test_physical_event_files_figures_caches_and_full_tables_rejected(self):
        for suffix in (".ROOT", ".lhe.gz", ".hepmc3", ".PNG", ".pdf", ".JSONL", ".pkl", ".so"):
            with self.assertRaisesRegex(ValueError, "payload forbidden"):
                audit_payload.inspect("simulation/heavy_flavour_forensics/evidence/bad" + suffix, b"{}\n")
        with self.assertRaisesRegex(ValueError, "cache forbidden"):
            audit_payload.inspect("simulation/heavy_flavour_forensics/vendor/source.py", b"# upstream\n")

    def test_private_path_rejected_but_documented_repository_path_allowed(self):
        private = b"/home/" + b"example/private"
        with self.assertRaisesRegex(ValueError, "private path"):
            audit_payload.inspect("simulation/heavy_flavour_forensics/evidence/private.json", private)
        audit_payload.inspect("reports/phase6e_example.md", b"cd /mnt/" + b"c/HH\n")

    def test_total_payload_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "6MiB"):
            audit_payload.total(["simulation/heavy_flavour_forensics/evidence/one.json"], lambda _: b"x" * (6 * 1024**2 + 1))


if __name__ == "__main__":
    unittest.main()
