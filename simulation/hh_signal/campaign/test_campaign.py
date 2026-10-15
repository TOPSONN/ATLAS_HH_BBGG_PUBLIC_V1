"""Mathematical/guard tests; no manufactured physical reference events."""
import unittest,math,tempfile,json
from pathlib import Path
from .decay import two_body,direction,assignment
from .lhe import mass2
from .controller import parser,request

class DecayMath(unittest.TestCase):
    def test_physical_two_body_all_boosts(self):
        # These are four-vector identities, not source-event fixtures.
        for xyz in ([0,0,0],[10,-30,200],[1000,30,-4000]):
            parent=[*xyz,math.sqrt(125**2+sum(x*x for x in xyz))]
            for mass in (0,4.8):
                for c in (-1,-.6,0,.7,1):
                    pair,m=two_body(parent,mass,c,.721)
                    self.assertAlmostEqual(m,125,places=7)
                    for j in range(4):self.assertAlmostEqual(sum(p[j] for p in pair),parent[j],places=7)
                    for p in pair:self.assertAlmostEqual(mass2(p),mass**2,places=6)
    def test_independent_symmetric_roles_and_angles(self):
        vals=[assignment(710201,i)[0] for i in range(1,10001)]
        self.assertLess(abs(vals.count(3)/len(vals)-.5),.02)
        angles=[direction(710201,i,3)[0] for i in range(1,10001)]
        self.assertLess(abs(sum(angles)/len(angles)),.02)
        self.assertLess(abs(sum(x*x for x in angles)/len(angles)-1/3),.02)
        self.assertNotEqual(direction(1,1,3),direction(1,1,4))
        self.assertEqual(assignment(1,1),assignment(1,1))
    def test_reject_unphysical_decay(self):
        for parent,m,c in [([0,0,0,1],1,0),([0,0,2,1],0,0),([0,0,0,125],0,2)]:
            with self.assertRaises(ValueError):two_body(parent,m,c,0)

class Guards(unittest.TestCase):
    def test_cli_real_values_and_rejections(self):
        output=str(Path.home()/'simulations/hh_signal_runs/test_no_creation')
        for phase,n in [('7b',100),('7c',1000),('7d',1000)]:
            a=parser().parse_args(['--phase',phase,'--events',str(n),*(['--seed','12'] if phase!='7d' else []),'--energy','13000',
                '--output',output,'--max-hours','.1','--max-disk-gb','2','--dry-run'])
            self.assertEqual(request(a),Path(output))
        for extra in [['--events','101'],['--energy','14000'],['--seed','0'],['--max-hours','7'],['--max-disk-gb','11']]:
            a=parser().parse_args(['--phase','7b','--output',output,*extra])
            with self.assertRaises(ValueError):request(a)
    def test_unsafe_outputs(self):
        from .common import safe_output
        for value in ['relative','/tmp/unsafe',str(Path.home()/'simulations/hh_signal_runs')]:
            with self.assertRaises(ValueError):safe_output(value)

class Statistics(unittest.TestCase):
    def test_zero_and_correlated_sampling(self):
        from .statistics import precision_plan,covariance
        p=precision_plan(0,1000)
        self.assertGreater(p['zero_one_sided95_upper'],0)
        self.assertIsNone(p['independent_events_for_relative_source_acceptance_precision']['0.1']['plug_in'])
        self.assertAlmostEqual(covariance([1,2,3],[2,4,6]),6.)
    def test_flows_missing_and_unit_area_correlations(self):
        from .statistics import histogram
        r=histogram([-1,.5,1.5,2,None],[1,1,1,1,1],[0,1,2],5)
        self.assertEqual([v['entries'] for v in r],[1,1,1,1])
        self.assertAlmostEqual(sum(v['UNIT_AREA_SHAPE_ONLY'] for v in r),1)
        self.assertEqual(r[0]['missing_pair_events'],1)
        z=histogram([.5,.5],[1,-1],[0,1],2)
        self.assertTrue(all(v['UNIT_AREA_SHAPE_ONLY'] is None for v in z))

if __name__=='__main__':unittest.main()
