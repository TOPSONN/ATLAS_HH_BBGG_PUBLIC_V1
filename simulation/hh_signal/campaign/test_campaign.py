"""Mathematical/guard tests; no manufactured physical reference events."""
import unittest,math,tempfile,json
from unittest.mock import patch
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
    def test_completed_resume_rejects_modified_numerical_table(self):
        from .reweight import completed_reweight
        from .common import save_json
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'event_reweights.csv').write_text('METHOD_ONLY_TAMPERED_TABLE\n')
            save_json(path/'reweight_validation.json',{'source_sha256':'reviewed_source',
                'benchmarks':[-1,0,1,2,2.5,5],'source_events':1000,'new_independent_events':0,
                'event_reweights_sha256':'0'*64,
                'comparison':{'status':'PASS_SEPARATE_PROCESS_EXPLORATORY_COMPARISON_WITH_LIMITS'}})
            with self.assertRaisesRegex(ValueError,'COMPLETED_REWEIGHT_TABLE_CHANGED'):
                completed_reweight(path,'reviewed_source',[-1,0,1,2,2.5,5])
    def test_manifest_rejects_ignored_unstaged_physics_asset(self):
        from . import audit_payload
        manifest={'files':[{'path':'selected.bin','bytes':3,'sha256':'0'*64}]}
        tree={'reference_samples/hh_signal/S01_ggf_hh_sm/method_only_manifest_test/manifest.json':'method_fixture'}
        with patch.object(audit_payload,'git',return_value=json.dumps(manifest).encode()):
            with self.assertRaisesRegex(ValueError,'REFERENCE_MANIFEST_ASSET_NOT_STAGED'):audit_payload.reference_manifests(tree)
    def test_zero_record_continuation_restores_seed_before_any_launch(self):
        from . import production
        from .common import sha,save_json
        class BeforeAnyGenerator(Exception):pass
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);cards=out/'process/Cards';cards.mkdir(parents=True)
            reviewed=b'20261121 = iseed\n100 = nevents\n'
            (out/'reviewed_run_card.dat').write_bytes(reviewed)
            (out/'reviewed_param_card.dat').write_bytes(b'REVIEWED_PARAMETER_TEXT_ONLY\n')
            (cards/'run_card.dat').write_bytes(b'0 = iseed\n100 = nevents\n')
            (cards/'param_card.dat').write_bytes(b'NATIVE_MUTATED_PARAMETER_TEXT_ONLY\n')
            (cards/'me5_configuration.txt').write_text('run_mode=2\nnb_core=8\n')
            (out/'ME5_debug').write_text('METHOD_ONLY_PREINTEGRATION_DEBUG_FIXTURE\n')
            (out/'launch.mg5').write_text('METHOD_ONLY_LAUNCH_FIXTURE\n')
            save_json(out/'preintegration_continuation.json',{'status':'VERIFIED_ZERO_SOURCE_RECORDS_PREINTEGRATION_COMPILE_FAILURE',
                'source_records_observed':0,'integration_result_files_observed':0,'debug_sha256':sha(out/'ME5_debug'),
                'original_launch_sha256':sha(out/'launch.mg5'),'original_run_card_sha256':sha(out/'reviewed_run_card.dat'),
                'original_param_card_sha256':sha(out/'reviewed_param_card.dat')})
            read=production.read_json
            def config(path):
                if Path(path).name=='mg5_installation.json':return {'toolchain_prefix':'/portable/toolchain','mg5_path':'/portable/mg5'}
                if Path(path).name=='delphes_installation.json':return {'root_prefix':'/portable/root'}
                return read(path)
            case=self
            class Monitor:
                def run_command(self,*a,**kw):
                    case.assertEqual((cards/'run_card.dat').read_bytes(),reviewed)
                    case.assertEqual((cards/'param_card.dat').read_bytes(),(out/'reviewed_param_card.dat').read_bytes())
                    case.assertIn('nb_core = 1',(cards/'me5_configuration.txt').read_text())
                    case.assertNotIn(' -m ',(out/'continuation_launch.mg5').read_text())
                    raise BeforeAnyGenerator()
            with patch.object(production,'read_json',side_effect=config):
                with self.assertRaises(BeforeAnyGenerator):production.resume_preintegration(out,'7b',20261121,{'private_mg5':'/portable/mg5'},Monitor())
    def test_native_scalar_printing_intervals(self):
        from .lhe import printed_half_unit
        self.assertAlmostEqual(printed_half_unit('0.3876131E+03'),5e-5)
        self.assertAlmostEqual(printed_half_unit('4.075980e-03'),5e-10)
        from .lhe import native_scale_half_unit
        self.assertAlmostEqual(native_scale_half_unit(297.4079,5e-7),5e-5)
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
    def test_no_higgs_identity_is_not_an_unknown_BR_replacement(self):
        from .analysis import background_weight_factor
        ledger={'scope':'NO_HIGGS_BR','status':'PASS_RAW_WEIGHT_CLOSURE','factor':None,'factor_applications':0}
        self.assertEqual(background_weight_factor(ledger),1.)
        for update in [{'scope':'MODEL_BR_ONLY'},{'factor_applications':1},{'status':'UNKNOWN'}]:
            with self.assertRaises(ValueError):background_weight_factor({**ledger,**update})
    def test_constant_nominal_sampling_variance_is_exact_zero(self):
        from .statistics import covariance
        # A zero source-sampling variance must not acquire a negative or tiny
        # artificial variance from second-moment cancellation.
        for scale in [1e-100,1.9069e-5,1e100]:
            self.assertEqual(covariance([scale]*1000,[scale]*1000),0.)
            self.assertEqual(covariance([scale]*3,[1.,2.,4.]),0.)
    def test_zero_and_correlated_sampling(self):
        from .statistics import precision_plan,covariance
        p=precision_plan(0,1000)
        self.assertGreater(p['zero_one_sided95_upper'],0)
        self.assertEqual(p['wilson95'][0],0.)
        self.assertIsNone(p['independent_events_for_relative_source_acceptance_precision']['0.1']['plug_in'])
        self.assertIsNone(p['independent_events_for_relative_source_acceptance_precision']['0.1']['conservative_using_wilson_lower'])
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
