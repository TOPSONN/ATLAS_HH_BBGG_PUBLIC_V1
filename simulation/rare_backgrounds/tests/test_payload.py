"""Bounded publication failure controls, not native physics acceptance."""
from pathlib import Path
import importlib.util
import unittest
spec = importlib.util.spec_from_file_location('rare_payload', Path(__file__).resolve().parents[1]/'scripts/audit_payload.py')
payload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(payload)


class PayloadControls(unittest.TestCase):
    def test_historical_cards_and_data_are_not_editable_payloads(self):
        for path in ('simulation/delphes/cards/atlas_like_bbgg_baseline.tcl', 'reports/phase6c_decision.md', 'reference_samples/mg5/example.json'):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'historical'):
                payload.inspect(path, b'unchanged historical fixture')

    def test_only_three_bounded_compact_tables_are_allowed(self):
        path = next(iter(payload.PILOT))
        payload.inspect(path, b'{}\n')
        with self.assertRaisesRegex(ValueError, 'size cap'):
            payload.inspect(path, b'x'*(2*1024**2+1))
        for name in ('conditional_events.jsonl', 'conditional_events.JSONL'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'three compact'):
                payload.inspect('simulation/rare_backgrounds/evidence/results/'+name, b'{}\n')

    def test_native_binary_archive_and_figures_are_rejected(self):
        for ending in ('.root', '.lhe.gz', '.hepmc3', '.pdf', '.png', '.so'):
            with self.subTest(ending=ending), self.assertRaises(ValueError):
                payload.inspect('simulation/rare_backgrounds/evidence/new'+ending, b'fixture')

    def test_documented_repo_path_is_allowed_only_in_markdown(self):
        path = b'/mnt/' + b'c/HH'
        payload.inspect('simulation/rare_backgrounds/USER_GUIDE_ZH_TW.md', path)
        with self.assertRaisesRegex(ValueError, 'private'):
            payload.inspect('simulation/rare_backgrounds/evidence/binding.json', path)


if __name__ == '__main__':
    unittest.main()
