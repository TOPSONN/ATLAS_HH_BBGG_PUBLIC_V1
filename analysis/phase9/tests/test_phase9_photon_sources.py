"""SYNTHETIC_METHOD_TEST and PUBLIC_CALIBRATION_SOURCE_AUDIT contract guards."""
import json
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from audit_photon_sources import card_values
from phase9_photon import require_fake_calibration

class SourceAuditTests(unittest.TestCase):
    def test_frixione_disabled_at_zero(self):
        x=card_values('0 = ptgmin\n0.4 = R0gamma\n1.0 = xn\n1.0 = epsgamma\nTrue = isoEM\n25 = pta')
        self.assertFalse(x['frixione_active']);self.assertTrue(x['isoem']);self.assertEqual(x['pta'],25)
    def test_frixione_enabled(self):
        self.assertTrue(card_values('25 = ptgmin')['frixione_active'])
    def test_comments_case_and_D(self):
        x=card_values(' # 90 = pta\n2.5D1 \t= pta ! photon cut\n-1 = eTaA')
        self.assertEqual(x['pta'],25);self.assertEqual(x['etaa'],-1)
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):card_values('1 = pta\n2 = pta')
    def test_public_inputs_not_compatible(self):
        a=json.loads((pathlib.Path(__file__).resolve().parents[1]/'config/photon_calibration_audit.json').read_text())
        self.assertEqual(a['test_scope'],'PUBLIC_CALIBRATION_SOURCE_AUDIT')
        self.assertFalse(a['compatible_calibration_imported'])
        self.assertFalse(a['restricted_material_imported'])
        self.assertIsNone(a['calibrated_jet_to_photon_probability'])
        self.assertEqual(a['PHOTON_FAKE'],'BLOCKED_CALIBRATION_UNAVAILABLE')
        self.assertEqual(len(a['sources']),2)
        for source in a['sources']:
            self.assertFalse(source['compatible'])
            self.assertEqual(source['energy_tev'],13)
            self.assertIn('CC BY 4.0',source['license'])
            for key in ('official_source','version','data_period','object_definition','transfer_factor_semantics','applicability','uncertainties'):
                self.assertTrue(source[key])
            with self.assertRaisesRegex(ValueError,'BLOCKED_CALIBRATION_UNAVAILABLE'):require_fake_calibration(source)
    def test_purity_not_fake_probability(self):
        a=json.loads((pathlib.Path(__file__).resolve().parents[1]/'config/photon_calibration_audit.json').read_text())
        source=a['sources'][0]
        self.assertEqual(source['published_summary']['genuine_diphoton_sideband_fraction'],.85)
        self.assertIn('not per-jet',source['transfer_factor_semantics'])
        self.assertFalse(source['compatible'])
if __name__=='__main__':unittest.main()