"""Offline executable contract tests against native-RVec synthetic fixtures."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

executable = Path(sys.argv.pop(1))
fixtures = Path(sys.argv.pop(1)) / 'local_events_fixtures'

class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'new_output'

    def run_driver(self, source=None, start='0', end='3', scale='1', status='PROVISIONAL'):
        return subprocess.run([str(executable), str(source or fixtures/'0.root'), str(self.output),
                               start, end, scale, status], capture_output=True, text=True)

    def test_unknown_units(self):
        self.assertNotEqual(self.run_driver(status='UNKNOWN').returncode, 0)
        self.assertFalse(self.output.exists())

    def test_remote_uri(self):
        self.assertNotEqual(self.run_driver(source='root://example.invalid/input.root').returncode, 0)
        self.assertFalse(self.output.exists())

    def test_entry_ceiling(self):
        self.assertNotEqual(self.run_driver(end='100001').returncode, 0)

    def test_negative_start(self):
        self.assertNotEqual(self.run_driver(start='-1').returncode, 0)

    def test_invalid_scale(self):
        for scale in ['0', '-1', 'nan', 'inf']:
            self.assertNotEqual(self.run_driver(scale=scale).returncode, 0)

    def test_output_preservation(self):
        self.output.mkdir(); sentinel = self.output/'sentinel'; sentinel.write_text('preserve')
        self.assertNotEqual(self.run_driver().returncode, 0)
        self.assertEqual(sentinel.read_text(), 'preserve')

    def test_native_fixture_and_histograms(self):
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        summary = json.loads((self.output/'summary.json').read_text())
        self.assertEqual(summary['unique_entries'], 3)
        self.assertEqual(summary['invalid_events'], 0)
        with (self.output/'events.csv').open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([int(r['entry']) for r in rows], [0,1,2])
        self.assertEqual(int(rows[0]['event']), 9007199254740993)
        self.assertEqual(len(list(self.output.glob('*.png'))), 7)
        self.assertGreater((self.output/'phase2_diagnostics.root').stat().st_size, 100)
        with (self.output/'histogram_inventory.csv').open() as f:
            inventory = {r['name']: r for r in csv.DictReader(f)}
        self.assertEqual(float(inventory['photon_pt']['filled_values']), 6)
        self.assertEqual(float(inventory['m_gg']['filled_values']), 3)
        self.assertEqual(float(inventory['m_jj']['filled_values']), 3)
        self.assertNotEqual(self.run_driver().returncode, 0)

    def test_structural_mismatch_no_plots(self):
        self.assertNotEqual(self.run_driver(source=fixtures/'3.root').returncode, 0)
        self.assertFalse(list(self.output.glob('*.png')))

    def test_friend_refused(self):
        self.assertNotEqual(self.run_driver(source=fixtures/'4.root').returncode, 0)
        self.assertFalse(self.output.exists())

    def test_subrange_unique_entries(self):
        result=self.run_driver(start='1')
        self.assertEqual(result.returncode,0,result.stderr)
        with (self.output/'events.csv').open() as f:
            rows=list(csv.DictReader(f))
        self.assertEqual([int(r['entry']) for r in rows],[1,2])

if __name__ == '__main__': unittest.main()
