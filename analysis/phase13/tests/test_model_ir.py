"""Offline source-engineering tests; no actual MG5 import/parser/ME."""
import copy
import json
import pathlib
import sys
import tempfile
import unittest
BASE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'source'))
import model_ir as m

class ModelIRTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((BASE/'config/model_process_ir.json').read_text())
    def rejected(self,c=None,text=None):
        with self.assertRaises((ValueError,KeyError)):
            m.validate_plan(self.c if c is None else c,m.INACTIVE_PROCESS_TEXT if text is None else text)
    def test_current_exact_plan(self):self.assertTrue(m.validate_plan(self.c,m.INACTIVE_PROCESS_TEXT))
    def test_process_remains_all_comments(self):
        self.assertTrue(all(line.startswith('#') for line in m.INACTIVE_PROCESS_TEXT.splitlines()))
    def test_active_command_rejected(self):self.rejected(text=m.INACTIVE_PROCESS_TEXT+'launch\n')
    def test_output_codegen_command_rejected(self):
        self.c['process_commands'].append('output unsafe');self.rejected()
    def test_numeric_process_check_rejected(self):
        self.c['process_commands'].append('check p4 p4 > b b~ a a');self.rejected()
    def test_alias_cannot_include_bottom(self):
        self.c['process_commands'][1]+=' b b~';self.rejected()
    def test_exact_not_equal_order_claim_rejected(self):
        self.c['process_commands'][2]=self.c['process_commands'][2].replace('QCD=2','QCD==2');self.rejected()
    def test_order_semantics_must_be_bounds(self):
        self.c['amplitude_order_interpretation']='EXACT_QCD2_QED2';self.rejected()
    def test_symbolic_enumeration_scope_must_be_explicit(self):
        self.c['future_symbolic_diagram_enumeration_in_scope']=False;self.rejected()
    def test_massless_bottom_rejected(self):
        self.c['restricted_masses_GeV']['MB']=0.;self.rejected()
    def test_default_charm_mass_not_raw_UFO_default(self):
        self.c['restricted_masses_GeV']['MC']=1.27;self.rejected()
    def test_wrong_restriction_rejected(self):
        self.c['restriction']='models/sm/restrict_no_b_mass.dat';self.rejected()
    def test_stale_source_manifest_rejected(self):
        self.c['source_identities']['models/sm/restrict_default.dat']['sha256']='0'*64;self.rejected()
    def test_missing_source_manifest_member_rejected(self):
        self.c['source_identities'].pop('Template/LO/SubProcesses/cuts.f');self.rejected()
    def test_physical_approval_cannot_be_inferred(self):
        for key in ['parser_authorized','code_generation_authorized','numerical_ME_authorized','physical_configuration_validated','ATLAS_detector_isolation_equivalence_claimed','MG5_parser_executed']:
            c=copy.deepcopy(self.c);c[key]=True;self.rejected(c)
    def test_unlabeled_numeric_cut_rejected(self):
        self.c['candidate_generation_cuts']['drab']['evidence_level']='VALIDATED';self.rejected()
    def test_silent_drab_zero_rejected(self):
        self.c['candidate_generation_cuts']['drab']['value']=0.;self.rejected()
    def test_five_flavour_cut_classification_not_substituted(self):
        self.c['candidate_generation_cuts']['maxjetflavor']['value']=5;self.rejected()
    def test_bool_not_accepted_as_numeric_cut(self):
        self.c['candidate_generation_cuts']['xn']['value']=True;self.rejected()
    def test_missing_cut_rationale_rejected(self):
        self.c['candidate_generation_cuts']['ptgmin']['rationale']='';self.rejected()
    def test_unknown_mmaa_not_filled_with_default(self):
        self.c['candidate_generation_cuts']['mmaa']['value']=0.;self.rejected()
    def test_unknown_matching_not_filled_with_default(self):
        self.c['unresolved_generator_conventions']['ickkw']['value']=0;self.rejected()
    def test_unknown_scale_not_filled_with_default(self):
        self.c['unresolved_generator_conventions']['dynamical_scale_choice']['value']=3;self.rejected()
    def test_missing_convention_rejected(self):
        self.c['unresolved_generator_conventions'].pop('xqcut');self.rejected()
    def test_restriction_parser_ignores_yukawa(self):
        text='Block MASS\n4 0d0 # MC\n5 4.7d0 # MB\nBlock YUKAWA\n4 9\n5 9\n'
        self.assertEqual(m.restriction_masses(text),{'MC':0.,'MB':4.7})
    def test_duplicate_mass_rejected(self):
        with self.assertRaises(ValueError):m.restriction_masses('Block MASS\n4 0\n5 4.7\n5 0\n')
    def test_missing_mass_rejected(self):
        with self.assertRaises(ValueError):m.restriction_masses('Block MASS\n5 4.7\n')
    def test_nonfinite_mass_rejected(self):
        with self.assertRaises(ValueError):m.restriction_masses('Block MASS\n4 0\n5 nan\n')
    def test_ast_read_does_not_execute_model(self):
        text="raise RuntimeError('must never execute')\nMC=Parameter(value=1.27)\nMB=Parameter(value=4.7)\n"
        self.assertEqual(m.ast_parameter_defaults(text),{'MC':1.27,'MB':4.7})
    def test_ast_symbolic_mass_reference(self):
        self.assertEqual(m.ast_particle_mass_refs('c=Particle(mass=Param.MC)\nb=Particle(mass=Param.MB)'),{'c':'MC','b':'MB'})
    def test_four_flavour_bottom_is_separate_category(self):
        for pdg in [5,-5]:self.assertEqual(m.cut_flavour_category(pdg,4),'is_a_b')
    def test_charm_and_gluon_in_light_sum(self):
        for pdg in [4,-4,21]:self.assertEqual(m.cut_flavour_category(pdg,4),'is_a_j')
    def test_source_counterexample_five_not_four(self):
        self.assertEqual(m.cut_flavour_category(5,5),'is_a_j')
    def test_read_source_exact_bytes_and_reject_drift(self):
        with tempfile.TemporaryDirectory() as d:
            r=pathlib.Path(d);(r/'x').write_bytes(b'original\n');manifest={'x':m.raw_identity(b'original\n')}
            self.assertEqual(m.read_exact_sources(r,manifest)[0]['x'],'original\n')
            (r/'x').write_bytes(b'original \n')
            with self.assertRaises(ValueError):m.read_exact_sources(r,manifest)
    def test_read_source_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            r=pathlib.Path(d);(r/'real').write_bytes(b'x');(r/'link').symlink_to(r/'real')
            with self.assertRaises(ValueError):m.read_exact_sources(r,{'link':m.raw_identity(b'x')})
    def test_read_source_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):m.read_exact_sources(pathlib.Path(d),{'../x':m.raw_identity(b'x')})
    def test_no_generator_import_or_subprocess_in_auditor(self):
        import ast
        for rel in ['source/model_ir.py','scripts/audit_model_ir.py']:
            tree=ast.parse((BASE/rel).read_text())
            imported={alias.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for alias in n.names}
            imported|={n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module}
            self.assertFalse(imported & {'madgraph','models','subprocess','ctypes','lhapdf'})
            self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'exec','eval','__import__'} for n in ast.walk(tree)))

if __name__=='__main__':unittest.main()