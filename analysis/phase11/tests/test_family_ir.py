import copy
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('family_ir_tests',ROOT/'analysis/phase11/source/family_ir.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FamilyIRTests(unittest.TestCase):
    def setUp(self):
        self.b=json.loads((ROOT/'analysis/phase11/config/candidate_b.json').read_text())
        self.ir=json.loads((ROOT/'analysis/phase11/config/photon_ir.json').read_text())
    def test_candidate_valid_inactive(self):self.assertEqual(m.validate_candidate_b(self.b),[])
    def test_photon_valid_inactive(self):self.assertEqual(m.validate_photon_ir(self.ir),[])
    def test_equal_is_max_amplitude(self):
        self.assertEqual(m.classify_order_token('QCD=2')['relation'],'<=')
        self.assertEqual(m.classify_order_token('QCD=2')['target'],'AMPLITUDE')
    def test_double_equal_is_exact_amplitude(self):self.assertEqual(m.classify_order_token('QED==2')['relation'],'==')
    def test_squared_order_is_not_amplitude(self):
        a=m.classify_order_token('QCD^2==2');self.assertEqual(a['target'],'SQUARED_MATRIX_ELEMENT');self.assertFalse(a['parser_execution'])
    def test_bad_order_rejected(self):
        for t in ['QCD=2; launch','QED==nan','QCD==2 [QCD]','QCD=-1']:
            with self.assertRaises(ValueError):m.classify_order_token(t)
    def test_missing_incoming_bottom_rejected(self):
        self.b['incoming_pdg_ids'].remove(5);self.assertTrue(m.validate_candidate_b(self.b))
    def test_massive_bottom_not_5f_massless_proposal(self):
        self.b['model_masses_GeV']['bottom']=4.7;self.assertTrue(m.validate_candidate_b(self.b))
    def test_boolean_not_numeric_zero_mass(self):
        self.b['model_masses_GeV']['bottom']=False;self.assertIn('MASS_TYPE',m.validate_candidate_b(self.b))
    def test_mlm_four_not_five(self):
        self.b['matching']['mlm_required_nQmatch']=4;self.assertTrue(m.validate_candidate_b(self.b))
    def test_ckkwl_four_not_five(self):
        self.b['matching']['ckkwl_required_nQuarksMerge']=4;self.assertTrue(m.validate_candidate_b(self.b))
    def test_maxjetflavor_four_not_five(self):
        self.b['matching']['required_maxjetflavor']=4;self.assertTrue(m.validate_candidate_b(self.b))
    def test_unreviewed_scale_numeric_rejected(self):
        for v in [0,30,-1,False]:
            b=copy.deepcopy(self.b);b['matching']['numerical_scale_GeV']=v;self.assertTrue(m.validate_candidate_b(b))
    def test_pdf_not_inherited(self):
        self.b['pdf']['set']='cteq6l1';self.assertIn('UNREVIEWED_PDF',m.validate_candidate_b(self.b))
    def test_alpha_not_inherited(self):
        self.b['alpha_s']['value_MZ']=.13;self.assertIn('UNREVIEWED_ALPHA_S',m.validate_candidate_b(self.b))
    def test_tree_false_loop_promotion_rejected(self):
        self.b['loop_induced_gg_aa_included']=True;self.assertTrue(m.validate_candidate_b(self.b))
    def test_fragmentation_false_promotion_rejected(self):
        self.b['fragmentation_contribution_included']=True;self.assertTrue(m.validate_candidate_b(self.b))
    def test_mixed_component_sum_rejected(self):
        self.b['separate_explicit_HF_addition_allowed']=True;self.assertTrue(m.validate_candidate_b(self.b))
    def test_old_order_syntax_not_exact_proposal(self):
        self.b['process_definitions'][2]['exact_order_text']=self.b['process_definitions'][2]['phase10_text'];self.assertTrue(m.validate_candidate_b(self.b))
    def test_missing_multiplicity(self):
        self.b['process_definitions'].pop();self.assertTrue(m.validate_candidate_b(self.b))
    def test_fxfixed_historical_LO_rejected(self):
        self.b['matching']['FxFx_for_historical_LO']='SUPPORTED';self.assertTrue(m.validate_candidate_b(self.b))
    def test_execute_flag_rejected(self):
        self.b['execution_authorized']=True;self.assertIn('EXECUTION_NOT_INACTIVE',m.validate_candidate_b(self.b))
    def test_parser_zero_not_false_rejected(self):
        self.b['parser_validated']=0;self.assertTrue(m.validate_candidate_b(self.b))
    def test_unresolved_zero_is_not_null(self):
        self.ir['unresolved_fields']['fragmentation']['value']=0;self.assertTrue(m.validate_photon_ir(self.ir))
    def test_unselected_photon_default_not_adopted(self):
        self.ir['selected_parameters']['r0gamma']=.4;self.assertIn('UNREVIEWED_PHOTON_PARAMETER',m.validate_photon_ir(self.ir))
    def test_bottom_in_isolation_four_vs_five(self):
        self.assertEqual(m.jet_cut_class(5,4),'is_a_b');self.assertEqual(m.jet_cut_class(-5,5),'is_a_j');self.assertEqual(m.jet_cut_class(4,4),'is_a_j');self.assertEqual(m.jet_cut_class(21,4),'is_a_j')
    def test_false_bottom_coverage_rejected(self):
        self.ir['source_semantics']['QCD_energy_sum']='all QCD';self.assertTrue(m.validate_photon_ir(self.ir))
    def test_drab_is_not_disabled(self):
        self.ir['source_semantics']['disabled_by_positive_ptgmin'].append('drab');self.assertTrue(m.validate_photon_ir(self.ir))
    def test_fixedcone_not_equivalent(self):
        self.ir['source_semantics']['fixed_cone_equivalence_established']=True;self.assertTrue(m.validate_photon_ir(self.ir))
    def test_smoothcone_soft_limit(self):self.assertAlmostEqual(m.frixione_bound(0,.4,.5,30,1),0)
    def test_smoothcone_outer_boundary(self):self.assertAlmostEqual(m.frixione_bound(.4,.4,.5,30,1),15)
    def test_smoothcone_monotone(self):
        v=[m.frixione_bound(r,.4,.5,30,1) for r in [.0,.05,.1,.2,.4]];self.assertEqual(v,sorted(v))
    def test_xn_abs_and_zero_semantics(self):
        self.assertEqual(m.frixione_bound(.1,.4,.5,30,-1),m.frixione_bound(.1,.4,.5,30,1));self.assertEqual(m.frixione_bound(0,.4,.5,30,0),15)
    def test_fixed_cone_can_pass_when_smooth_fails(self):
        # Synthetic method counterexample only: 1 GeV parton near photon.
        self.assertLess(1,.5*30);self.assertGreater(1,m.frixione_bound(.01,.4,.5,30,1))
    def test_bad_frixione_domain_rejected(self):
        for v in [(0,0,.5,30,1),(.5,.4,.5,30,1),(0,.4,.5,0,1),(0,.4,float('nan'),30,1)]:
            with self.assertRaises(ValueError):m.frixione_bound(*v)
    def test_signed_and_zero_weights_preserved(self):
        self.assertEqual(m.signed_merging_product(-2,.3),-.6);self.assertEqual(m.signed_merging_product(0,.3),0)
    def test_nonfinite_weight_rejected(self):
        with self.assertRaises(ValueError):m.signed_merging_product(float('nan'),1)
    def test_inactive_card_all_comments(self):self.assertEqual(m.inactive_card_errors((ROOT/'analysis/phase11/config/cards/candidate_b.inactive.txt').read_text()),[])
    def test_active_generator_line_rejected(self):
        for s in ['generate p p > a a','launch','output /tmp/new','import model sm']:
            self.assertTrue(m.inactive_card_errors('# inactive\n'+s))
    def test_missing_static_source_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'VERSION').write_text('3.5.15')
            with self.assertRaisesRegex(ValueError,'SOURCE_WITNESS_MISSING'):
                m.audit_sources(root,root)

    def test_escaped_coupling_witness_is_exact_and_wrong_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'parser.py').write_text(r'logger.info("    \"==\" request exactly that number of coupling while \"=\" is interpreted as \"<=\".")')
            old=m.WITNESSES
            try:
                m.WITNESSES=[('COUPLING','mg5','parser.py',['"==" request exactly'])]
                with self.assertRaisesRegex(ValueError,'SOURCE_WITNESS_MISSING:COUPLING'):
                    m.audit_sources(root,root)
                m.WITNESSES=[('COUPLING','mg5','parser.py',['request exactly that number of coupling while'])]
                self.assertEqual(len(m.audit_sources(root,root)['source_witnesses']),1)
            finally:m.WITNESSES=old

    def test_matching_unvalidated_flags_cannot_be_promoted(self):
        for k in ['highest_multiplicity_validated','ckkwl_core_string_parser_validated','weight_writer_closure_validated']:
            for v in [True,0,None]:
                b=copy.deepcopy(self.b);b['matching'][k]=v
                self.assertIn('UNVALIDATED_MATCHING_FLAG_PROMOTION:'+k,m.validate_candidate_b(b))
    def test_photon_status_cannot_be_promoted(self):
        self.ir['status']='PHYSICALLY_VALIDATED'
        self.assertIn('PHOTON_STATUS_FALSE_PROMOTION',m.validate_photon_ir(self.ir))
    def test_photon_nulls_cannot_be_false_zero_or_default(self):
        for k in ['ptgmin_GeV','r0gamma','isoEM']:
            for v in [False,0,.4]:
                ir=copy.deepcopy(self.ir);ir['selected_parameters'][k]=v
                self.assertIn('UNREVIEWED_PHOTON_PARAMETER',m.validate_photon_ir(ir))

if __name__=='__main__':unittest.main()
