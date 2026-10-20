import unittest
from simulation.hh_signal.final_closure.resource_closure import full_publication as p


class FullPublicationTests(unittest.TestCase):
    def test_exact_stacked_base(self):
        self.assertEqual(p.BASE, '66663557984fcc069de600e2af07e778a4ac30ff')

    def test_additive_sources_and_reports(self):
        self.assertTrue(p.allowed(p.ROOT + 'full_controller.py'))
        self.assertTrue(p.allowed('reports/phase7i_resource_closure/full_controller_result_01.json'))

    def test_historical_and_physics_changes_rejected(self):
        for name in (p.ROOT + 'backend.py', p.ROOT + 'worker.py',
                     p.ROOT + 'config/fixture_profile.json',
                     'simulation/hh_signal/final_closure/config/physics_contract.json',
                     'reports/phase7i_resource_closure/ram_followup_status.json'):
            self.assertFalse(p.allowed(name), name)

    def test_figures_private_events_rejected(self):
        for name in ('reports/phase7i_resource_closure/full_controller_plot.png',
                     'reports/phase7i_resource_closure/full_controller_plot.pdf',
                     p.ROOT + '.local/private.json', p.ROOT + 'sample.lhe'):
            self.assertFalse(p.allowed(name), name)

    def test_magic_cannot_hide_as_report(self):
        for raw in (b'%PDF-1.7', b'\x89PNG\r\n\x1a\n', b'root', b'\x7fELF'):
            with self.assertRaises(ValueError):
                p.old.validate_payload('reports/phase7i_resource_closure/full_controller_bad.txt', raw)

    def test_old_allowlist_restored_after_failure(self):
        old = p.old.allowed_path
        with self.assertRaises(ValueError):
            p.audit('/no/such/repo')
        self.assertIs(p.old.allowed_path, old)


if __name__ == '__main__':
    unittest.main()
