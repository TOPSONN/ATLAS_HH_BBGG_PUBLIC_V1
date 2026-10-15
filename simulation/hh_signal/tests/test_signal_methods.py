import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.hh_signal.contracts import PACKAGE, REPO, read_json, validate_model, validate_couplings, verify_bundle
from simulation.hh_signal.methods import assign_higgs_decays, validate_assignment, missing_decay_factor, contribution_pb, pair_mass_or_none
sys.path.insert(0,str(PACKAGE/'scripts'))
from verify_loop_model import fixed_point, check_numerical_results, modify_card
from generate_signal import safe_output
from audit_payload import scan

class ModelFailures(unittest.TestCase):
    def setUp(self):
        self.model=read_json(PACKAGE/'config/signal_model_contract.json')
        self.couplings=read_json(PACKAGE/'config/coupling_contract.json')
    def test_actual_frozen_SM_contract(self): validate_model(self.model);validate_couplings(self.couplings)
    def test_wrong_model(self):
        self.model['model']='heft'
        with self.assertRaisesRegex(ValueError,'WRONG_MODEL'): validate_model(self.model)
    def test_missing_box_triangle_or_rational(self):
        for term in ('box','triangle','R2'):
            bad=copy.deepcopy(self.model);bad['topologies'].remove(term)
            with self.subTest(term=term),self.assertRaisesRegex(ValueError,'TOPOLOGY'):validate_model(bad)
    def test_full_mt_required(self):
        self.model['finite_top_mass']=False
        with self.assertRaisesRegex(ValueError,'FULL_MT'):validate_model(self.model)
    def test_heft_not_full_loop(self):
        self.model['accuracy']='HEFT_APPROXIMATION_ONLY'
        with self.assertRaisesRegex(ValueError,'HEFT'):validate_model(self.model)
    def test_effective_contact_rejected_R2_separate(self):
        self.model['effective_contacts']=True
        with self.assertRaisesRegex(ValueError,'HEFT'):validate_model(self.model)
    def test_no_fabricated_cross_section(self):
        self.model['source_cross_section_pb']=0.03
        with self.assertRaisesRegex(ValueError,'CROSS_SECTION'):validate_model(self.model)
    def test_no_authorization_toggle(self):
        self.model['physical_events_authorized']=True
        with self.assertRaisesRegex(ValueError,'GENERATION'):validate_model(self.model)
    def test_changing_MH_is_not_kappa_lambda(self):
        self.couplings['lambda_mapping']['changes_Higgs_mass']=True
        with self.assertRaisesRegex(ValueError,'MASS_CHANGE'):validate_couplings(self.couplings)
    def test_top_yukawa_is_independent(self):
        self.couplings['top_mapping']['source']='MASS[6]'
        with self.assertRaisesRegex(ValueError,'YUKAWA'):validate_couplings(self.couplings)
    def test_bsm_production_not_supported(self):
        self.couplings['lambda_mapping']['production_scan_supported']=True
        with self.assertRaisesRegex(ValueError,'BSM'):validate_couplings(self.couplings)

class AssignmentAndWeightMethods(unittest.TestCase):
    def setUp(self):
        self.h=[{'pdg_id':25,'lineage_id':7,'is_original':True},{'pdg_id':25,'lineage_id':8,'is_original':True}]
    def test_distinct_original_higgs(self):
        p=assign_higgs_decays(self.h,127,0);validate_assignment(p,self.h)
        self.assertNotEqual(p['bb_lineage'],p['gammagamma_lineage'])
    def test_missing_or_three_higgs(self):
        for h in ([],self.h[:1],self.h+self.h[:1]):
            with self.assertRaisesRegex(ValueError,'TWO_ORIGINAL'):assign_higgs_decays(h,1,0)
    def test_duplicate_lineage(self):
        self.h[1]['lineage_id']=7
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):assign_higgs_decays(self.h,1,0)
    def test_no_invented_H1_H2_pdg(self):
        self.h[0]['pdg_id']=2501
        with self.assertRaisesRegex(ValueError,'PDG25'):assign_higgs_decays(self.h,1,0)
    def test_copy_not_original(self):
        self.h[0]['is_original']=False
        with self.assertRaisesRegex(ValueError,'ORIGINAL'):assign_higgs_decays(self.h,1,0)
    def test_same_decay_rejected(self):
        with self.assertRaisesRegex(ValueError,'SAME_DECAY'):
            validate_assignment({'bb_lineage':7,'gammagamma_lineage':7,'assignment_probability':0.5},self.h)
    def test_unbiased_independent_seed_and_order_invariance(self):
        assignments=[assign_higgs_decays(self.h,83,i)['gammagamma_lineage']==7 for i in range(10000)]
        self.assertLess(abs(sum(assignments)-5000),200)
        self.assertEqual(assign_higgs_decays(self.h,83,0),assign_higgs_decays(list(reversed(self.h)),83,0))
        self.assertNotEqual(assignments,[assign_higgs_decays(self.h,84,i)['gammagamma_lineage']==7 for i in range(10000)])
    def test_no_kinematic_ranking_or_momentum_mutation(self):
        h=copy.deepcopy(self.h);assign_higgs_decays(self.h,1,2);self.assertEqual(h,self.h)
    def test_exactly_once_BR_algebra_fixture(self):
        # Algebra-only arbitrary probabilities, not adopted Higgs BRs.
        self.assertAlmostEqual(missing_decay_factor(0.6,0.002,[],[]),0.0024)
    def test_duplicate_BR_rejected(self):
        with self.assertRaisesRegex(ValueError,'ALREADY'):missing_decay_factor(0.6,0.002,[],['H_bb'])
    def test_already_decayed_source_requires_review(self):
        with self.assertRaisesRegex(ValueError,'SEPARATE_REVIEW'):missing_decay_factor(0.6,0.002,['H_bb'],[])
    def test_missing_identical_factor(self):
        with self.assertRaisesRegex(ValueError,'IDENTICAL'):missing_decay_factor(0.6,0.002,[],[],1)
    def test_signed_pb_weight_preserved(self):
        kw={'original_count':1000,'weight_semantics':'cross_section_weight_pb','raw_unit':'pb','br_factor':0.0024}
        self.assertAlmostEqual(contribution_pb(raw_weight=-2,**kw),-4.8e-6)
        self.assertAlmostEqual(contribution_pb(raw_weight=2,**kw),4.8e-6)
    def test_selected_N_rejected(self):
        with self.assertRaisesRegex(ValueError,'SELECTED_N'):
            contribution_pb(raw_weight=1,original_count=1000,selected_count=10,weight_semantics='cross_section_weight_pb',raw_unit='pb')
    def test_double_sigma_rejected(self):
        with self.assertRaisesRegex(ValueError,'DOUBLE_SIGMA'):
            contribution_pb(raw_weight=1,original_count=1000,cross_section_pb=1,weight_semantics='cross_section_weight_pb',raw_unit='pb')
    def test_pb_mb_unit_error_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNITS'):
            contribution_pb(raw_weight=1,original_count=1000,weight_semantics='cross_section_weight_pb',raw_unit='mb')
    def test_no_inferring_unit_signed_NLO_convention(self):
        with self.assertRaisesRegex(ValueError,'UNCERTIFIED'):
            contribution_pb(raw_weight=-1,original_count=1000,cross_section_pb=1,weight_semantics='unit_positive_sigma_pb',raw_unit='dimensionless')
    def test_no_sigma_N_twice(self):
        with self.assertRaisesRegex(ValueError,'DOUBLE_SIGMA_OVER_N'):
            contribution_pb(raw_weight=1,original_count=1000,sigma_over_n_already_applied=True,weight_semantics='cross_section_weight_pb',raw_unit='pb')
    def test_wrong_original_count(self):
        for n in (0,-1,1.5):
            with self.assertRaisesRegex(ValueError,'ORIGINAL_N'):
                contribution_pb(raw_weight=1,original_count=n,weight_semantics='cross_section_weight_pb',raw_unit='pb')
    def test_missing_pair_null(self):self.assertIsNone(pair_mass_or_none([]));self.assertIsNone(pair_mass_or_none([[1,1,0,0]]))
    def test_cartesian_pair(self):self.assertEqual(pair_mass_or_none([[5,3,0,4],[5,-3,0,-4]]),10)

class NumericalAndPublication(unittest.TestCase):
    def test_physical_threshold_rejection(self):
        for energy in (0,249.99,250):
            with self.assertRaisesRegex(ValueError,'THRESHOLD'):fixed_point(energy)
    def test_common_point_conservation(self):
        p=fixed_point(400)
        self.assertEqual([p[0][i]+p[1][i] for i in range(4)],[p[2][i]+p[3][i] for i in range(4)])
    def test_actual_numerical_evidence_independent_regression(self):
        data=read_json(REPO/'metadata/phase7a_loop_validation.json')
        self.assertEqual(data['physical_signal_events'],0)
        self.assertTrue(data['status'].startswith('PASS_BOUNDED_FULL_MT_MB'))
        for row in data['triangle_box_interference']:
            self.assertGreater(row['box_squared'],0);self.assertGreater(row['triangle_squared'],0)
            self.assertLess(row['interference_kl1'],0)
            self.assertLess(row['relative_closure'],1e-7)
            # Independent finite-difference regression directly on retained
            # actual matrix elements, not on the producer's decomposition.
            q={r['kappa_lambda']:r['finite_squared_me'] for r in data['evaluations']
               if r['mHH_gev']==row['mHH_gev'] and r['label'].startswith('e')}
            self.assertLess(abs(q[2]-3*q[1]+3*q[0]-q[-1])/max(q.values()),1e-7)
        check_numerical_results(data['evaluations'])
    def test_frozen_bundle_and_stale_hash(self):
        verify_bundle()
        with tempfile.TemporaryDirectory() as td:
            temp=Path(td);(temp/'metadata').mkdir()
            (temp/'bad.dat').write_text('changed')
            (temp/'metadata/phase7a_model_manifest.json').write_text(json.dumps({'project_bindings':[{'path':'bad.dat','sha256':'0'*64}]}))
            with self.assertRaisesRegex(ValueError,'STALE_SOURCE'):verify_bundle(temp)
    def test_duplicate_nonfinite_JSON(self):
        for text in ('{"a":1,"a":2}','{"a":NaN}','{"a":1e999}'):
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)/'x.json';p.write_text(text)
                with self.assertRaises(ValueError):read_json(p)
    def test_unsafe_paths(self):
        for p in ('relative','/','/tmp/x',str(REPO/'x')):
            with self.assertRaises(ValueError):safe_output(p)
    def test_generation_mode_physically_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'must_not_exist'
            result=subprocess.run([sys.executable,'-B',str(PACKAGE/'scripts/generate_signal.py'),
                '--process','ggf_hh_sm','--events','100','--seed','20261120','--energy','13000',
                '--output',str(out),'--max-hours','4','--max-disk-gb','10'],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('PHYSICAL_SIGNAL_GENERATION_NOT_AUTHORIZED',result.stderr)
            self.assertFalse(out.exists())
    def test_unapproved_figure_or_fake_payload_rejected(self):
        for p,data in [('reports/phase7a_plot.png',b'PNG'),('simulation/hh_signal/data.lhe',b'none'),
                       ('simulation/hh_signal/fake.txt',b'<Les'+b'HouchesEvents>')]:
            with self.assertRaises(ValueError):scan(p,data)
    def test_out_of_scope_payload(self):
        with self.assertRaisesRegex(ValueError,'OUT_OF_SCOPE'):scan('simulation/delphes/changed.py',b'x')
    def test_nonunique_parameter_mapping(self):
        with self.assertRaisesRegex(ValueError,'NOT_UNIQUE'):modify_card('Block mass\n 6 173\n 6 180\n','mass',6,173)

if __name__=='__main__':unittest.main()
