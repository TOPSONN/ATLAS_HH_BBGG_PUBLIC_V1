"""Scientific guard and future-build review regression; no physical dispatch."""
import ast,copy,hashlib,json,os,re,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import builder_proposal as builder
from .overlay import source,restore,sha,ORIGINAL_SHA256,PREDICATES,diff
from .diagnostics import parse_record
from .methods import execute,HERE
from . import review_contract as review
from ..stop92_diagnostic.overlay import exact_point

class ScientificSourceTests(unittest.TestCase):
    def test_exact_reversible_intentional_changes(self):
        text=source();old=restore(text)
        self.assertEqual(sha(old),ORIGINAL_SHA256)
        self.assertNotEqual(sha(text),ORIGINAL_SHA256)
        self.assertEqual((HERE/'native_checks_corrected.f').read_text(),text)
        self.assertEqual((HERE/'native_checks_corrected.patch').read_text(),diff(old,text))
        self.assertIn('abs(scale/q-1d0).gt.1d-10',text)
        self.assertNotIn('abs(MU_R/q-1d0)',text)
        for i in [1,2]:self.assertLess(text.index('call finite(q2fact('+str(i)+'))'),text.index('abs(scale/q-1d0)'))
        self.assertEqual(len(PREDICATES),5)
    def test_weakened_or_unreviewed_changes_cannot_reverse(self):
        for text in [source().replace('1d-10','1d-5'),source().replace('call finite(q2fact(1))','continue'),
            source().replace('stop 92','continue'),source().replace('points=points+1','points=points+2')]:
            with self.assertRaises(ValueError):restore(text)
    def test_no_rng_sampler_weight_grid_or_estimator_calls_in_guard(self):
        point=exact_point(source())
        self.assertEqual(set(re.findall(r'(?im)^\s*call\s+(\w+)',point)),{'finite'})
        for name in ['ranmar','ran1','xran1','sample_full','SMATRIX','grid','sumw','candidate']:
            self.assertNotIn(name.lower(),point.lower())
        self.assertEqual(point.count('flush(6)'),5);self.assertEqual(point.count('stop 92'),5)
    def test_versioned_diagnostic_schema_and_no_vector_payload(self):
        fields=PREDICATES[1][2]
        record='HI_FAILURE POINT92 POINT92_RENORMALIZATION_SCALE'+''.join(' '+key+'= 1.0000000000000000E+000' for key,_ in fields)
        result=parse_record(record)
        self.assertEqual(tuple(result['scalars']),tuple(k for k,_ in fields));self.assertLess(len(record),768)
        for bad in [record+' p4= 1.0',record+'\n',record.replace('native_scale_over_q','MU_R_over_q'),
            record+' '*768,record.replace('POINT92_RENORMALIZATION_SCALE','UNKNOWN')]:
            with self.assertRaises(ValueError):parse_record(bad)
    def test_frozen_loop_context_and_theory_scope_in_contract(self):
        contract=review.build_contract()
        self.assertEqual(contract['native_guard_sha256'],sha(source()))
        self.assertEqual(contract['builder_candidate_sha256'],sha(builder.source()))
        self.assertEqual(len(contract['frozen_process_dependencies']),71)
        self.assertEqual(contract['route'],'A_FINITE_LO_NO_BORN_ONLY')
        self.assertFalse(contract['build_approval']);self.assertFalse(contract['physical_restart_approval'])
        evidence=(review.REPO/'reports/phase7i_guard_correction_evidence/dependency_excerpts.txt').read_text()
        self.assertIn('PARAMETER (NBORNAMPS=0)',evidence)
        self.assertIn('R2_GGHHT,AMPL(1,3)',evidence)
        self.assertIn('R2_GGHT,AMPL(1,4)',evidence)
        self.assertIn('CTSXCUT(CTMODE,LSCALE,MU_R',evidence)

class BuilderReviewTests(unittest.TestCase):
    def test_builder_exact_diff_and_unchanged_active_builder(self):
        candidate=builder.source();original=builder.restore(candidate)
        self.assertEqual(sha(original),builder.BUILDER_ORIGINAL_SHA256)
        self.assertEqual((HERE/'build_corrected_proposal.py').read_text(),candidate)
        self.assertEqual((HERE/'build_corrected_proposal.patch').read_text(),diff(original,candidate,'build.py'))
        self.assertIn("files=[HERE/'observers.f90',corrected_guard",candidate)
        self.assertIn('verify_dependency_sources(process)',candidate)
        with self.assertRaises(ValueError):builder.restore(candidate.replace("'-O0'","'-O2'"))
        self.assertIn("'source_identity':full_source_identity()",candidate)
    def test_proposed_builder_denies_missing_consumed_and_unbound_approval_before_work(self):
        tree=ast.parse(builder.source());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
        # Extract only the function for an inert, tripwired method fixture.
        # Never import/execute the production builder module or its compiler.
        namespace={'require':review.require,'validate_build_approval':review.validate_build_approval,
            'full_source_identity':lambda:[], 'check_revision':lambda _:(_ for _ in ()).throw(ValueError('METHOD_TRIPWIRE_BEFORE_BUILD'))}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<METHOD_ONLY_BUILDER_GATE>','exec'),namespace)
        with self.assertRaisesRegex(ValueError,'SEPARATE_BUILD_APPROVAL_REQUIRED'):namespace['prepare']('UNUSED')
        with self.assertRaisesRegex(ValueError,'CONSUMED_OR_UNCORRECTED_REVISION'):
            namespace['prepare']('UNUSED',build_review={'revision':'58d39888a024028e32f3071db9215c0db6fe0a89'})
        method_only={'action':'BUILD_ONLY','revision':'e'*40,'source_binding_identity':review.identity([]),
            'physics_contract_sha256':review.PHYSICS_SHA,'physical_restart_authorized':False}
        with self.assertRaisesRegex(ValueError,'METHOD_TRIPWIRE_BEFORE_BUILD'):namespace['prepare']('UNUSED',build_review=method_only)
        method_only['physical_restart_authorized']=True
        with self.assertRaisesRegex(ValueError,'BUILD_APPROVAL_CANNOT_AUTHORIZE_RESTART'):namespace['prepare']('UNUSED',build_review=method_only)
    def receipt(self):
        bindings=[{'path':'METHOD_ONLY','sha256':'a'*64}]
        r={'schema':review.SCHEMA,'source_identity':bindings,'physics_contract_sha256':review.PHYSICS_SHA,
            'approved_build_source_revision':'e'*40,
            'guard_correction':{'native_guard_sha256':sha(source()),'source_bindings':bindings,'source_binding_identity':review.identity(bindings),'physical_restart_authorized':False},
            'replicas':[{'seed':seed,'executable_sha256':str(i)*64,'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0,
              'immutable':[{'path':'METHOD_ONLY','sha256':'b'*64}],'dynamic_dependencies':[{'name':'METHOD_ONLY','sha256':'c'*64}],
              'preflights':[{'class':'METHOD_ONLY'}],'fortran_compiler_sha256':'d'*64} for i,seed in enumerate([910001,910019,910037,910061],1)]}
        return r,bindings
    def test_stale_binary_receipt_and_consumed_authorization_cannot_migrate(self):
        receipt,bindings=self.receipt();review.validate_build_receipt(receipt,bindings,sha(source()))
        for key,val in [('schema','OLD'),('source_identity',[]),('approved_build_source_revision','58d39888a024028e32f3071db9215c0db6fe0a89')]:
            bad=copy.deepcopy(receipt);bad[key]=val
            with self.assertRaises(ValueError):review.validate_build_receipt(bad,bindings,sha(source()))
        for old_binary in review.OLD_EXECUTABLES:
            bad=copy.deepcopy(receipt);bad['replicas'][0]['executable_sha256']=old_binary
            with self.assertRaisesRegex(ValueError,'OLD_OR_MISSING_BINARY'):review.validate_build_receipt(bad,bindings,sha(source()))
    def test_binary_identity_does_not_conflate_timestamps_with_full_receipt(self):
        r,_=self.receipt();other=copy.deepcopy(r)
        other['prepared_at']='METHOD_DIFFERENT_TIME';other['resources_review_only']={'wall_seconds':123}
        self.assertEqual(review.binary_identity(r),review.binary_identity(other));self.assertNotEqual(review.identity(r),review.identity(other))
    def test_model_dependency_drift_rejected_with_no_compiler(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'model.f';p.write_text('METHOD_ONLY')
            contract={'frozen_process_dependencies':[{'path':'model.f','sha256':review.sha(p)}]}
            with patch.object(review,'build_contract',return_value=contract):
                review.verify_dependency_sources(td);p.write_text('CHANGED_MODEL')
                with self.assertRaisesRegex(ValueError,'FINITE_LO_DEPENDENCY_DRIFT'):review.verify_dependency_sources(td)
    def test_only_two_declared_new_metadata_paths(self):
        from ..src.audit_payload import PREFIXES,compatibility,PATCHES
        from ...campaign.audit_payload import ALLOWED
        for name in ['guard_correction_status','builder_review_contract']:
            p='metadata/phase7i_'+name+'.json';self.assertIn(p,PREFIXES);self.assertIn(p,ALLOWED)
        path='simulation/hh_signal/campaign/audit_payload.py';old,new=PATCHES[path]
        before=old.encode();after=(review.REPO/path).read_bytes()
        # Use a real frozen base to exercise the declared compatibility diff.
        from ...campaign.audit_payload import git
        base=git('show','a5582e508e452a515670d1edc1d39041e88a8638:'+path)
        compatibility(path,base,after)
        with self.assertRaises(ValueError):compatibility(path,base,after.replace(b'phase7i_builder_review_contract',b'phase7i_unrelated'))

class NativeCorrectionMethods(unittest.TestCase):
    def test_three_versions_O0_and_O2_with_exact_rng_and_scalar_probes(self):
        for opt in ['-O0','-O2']:
            with self.subTest(optimization=opt),tempfile.TemporaryDirectory() as td:
                result=execute(Path(td)/'fresh',os.environ.get('FC','gfortran'),opt)
                self.assertEqual(len(result['matrix']),47)
                self.assertEqual(len(result['partial_receipts']),7)
                self.assertEqual(result['new_genuine_ME_calls'],0)
                rows={r['case']:r for r in result['matrix']}
                for i in [4,14]:self.assertEqual((rows[i]['original_exit'],rows[i]['corrected_exit']),(92,0))
                for i in [10,11,12,18,19,20]:self.assertEqual(rows[i]['corrected_exit'],90)
                self.assertEqual(rows[13]['corrected_exit'],0)
                self.assertEqual({r['corrected_parsed']['identifier'] for r in rows.values() if r['corrected_parsed']},{p[1] for p in PREDICATES})

if __name__=='__main__':unittest.main()
