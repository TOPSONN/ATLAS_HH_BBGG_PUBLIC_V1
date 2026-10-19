import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/audit_initial_flavours.py'
spec=importlib.util.spec_from_file_location('phase11_incoming_audit',SCRIPT)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def rows(ids):
    return [[str(len(ids)+2),'1','1','100','0.01','0.1'],*[[str(p),'-1'] for p in ids],['22','1'],['22','1']]

class ExactInitialFlavourTests(unittest.TestCase):
    def test_charm_is_allowed_by_p4_domain(self):
        ids=audit.incoming(rows((4,-4)));self.assertEqual(ids,(4,-4))
        flags=audit.classes(ids);self.assertTrue(flags['ANY_INCOMING_CHARM']);self.assertTrue(flags['CHARM_WITHOUT_BOTTOM']);self.assertFalse(flags['ANY_INCOMING_BOTTOM']);self.assertTrue(flags['SOURCE_INITIAL_PDG_ALLOWED_BY_P4_ONLY'])
    def test_bottom_excluded_by_p4_domain(self):
        flags=audit.classes(audit.incoming(rows((5,-5))))
        self.assertTrue(flags['ANY_INCOMING_BOTTOM']);self.assertFalse(flags['SOURCE_INITIAL_PDG_ALLOWED_BY_P4_ONLY'])
    def test_mixed_bottom_charm_not_charm_only(self):
        flags=audit.classes((5,-4));self.assertTrue(flags['ANY_INCOMING_BOTTOM']);self.assertTrue(flags['ANY_INCOMING_CHARM']);self.assertFalse(flags['CHARM_WITHOUT_BOTTOM'])
    def test_gluon_light_has_no_heavy(self):
        flags=audit.classes((21,2));self.assertTrue(flags['NO_INCOMING_B_OR_C']);self.assertTrue(flags['SOURCE_INITIAL_PDG_ALLOWED_BY_P4_ONLY'])
    def test_beam_order_preserved(self):
        self.assertEqual(audit.incoming(rows((-4,4))),(-4,4))
    def test_three_incoming_partons_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACTLY_TWO'):
            audit.incoming(rows((21,4,-4)))
    def test_missing_incoming_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACTLY_TWO'):
            audit.incoming(rows((21,)))
    def test_unsupported_initial_pdg_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED'):
            audit.incoming(rows((22,21)))
    def test_truncated_particle_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,'PARTICLE_ROWS'):
            audit.incoming([['4','1','1','100','0.1','0.1'],['21','-1']])
    def test_signed_fullN_covariance(self):
        self.assertEqual(audit.covariance([.1,-.1,0],[0,.2,0]),float(Fraction(-3,100)))
    def test_zero_preserves_acceptance_limit(self):
        m=audit.metrics([False]*1000,[1.]*1000)
        self.assertEqual(m['events'],0);self.assertAlmostEqual(m['zero_one_sided95_acceptance_upper'],.002991249545095296)
    def test_no_generator_or_root_dispatch(self):
        text=SCRIPT.read_text()
        for forbidden in ('subprocess','import ROOT','os.system','generate_events','import madgraph'):
            self.assertNotIn(forbidden,text)
        self.assertIn('from validate_lhe_stream import iter_lhe_events',text)

if __name__=='__main__':unittest.main()