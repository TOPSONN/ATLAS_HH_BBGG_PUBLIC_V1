"""Scientific/safety regression. All receipt numbers here are METHOD_ONLY."""
import contextlib,copy,io,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import contracts as c,controller as ctl,runtime_contract as r
from simulation.hh_signal.config_lock import writers

def receipt():
    return dict(scope_sha256='METHOD_ONLY',status='PASS',semantics='VALIDATED',ME_calls=10,
        seed=910001,effective_seed=910001,zero_retained_LHE=True,output_audit='PASS',
        transient_monitoring_coverage='METHOD_ONLY_WITH_DECLARED_GAPS',actual_counters={'points':10},
        grid_history=['METHOD_ONLY'],termination='FIXED_ENDPOINT',aggregate_resources=dict(wall=1,cpu=1,disk=1))

class Matched(unittest.TestCase):
    def test_phrase_env_file_cli_never_grant(self):
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            token=Path(tmp)/'authorization.txt';token.write_text(c.AUTHORIZATION_PHRASE)
            with patch.dict(os.environ,{'PHASE7G_AUTHORIZATION':c.AUTHORIZATION_PHRASE,'AUTHORIZATION_FILE':str(token)}):
                self.assertEqual(c.authorization_status()['status'],'NOT_GRANTED')
                for args in [['--execute'],['--authorization',c.AUTHORIZATION_PHRASE],['--authorization',str(token)]]:
                    with patch.object(ctl,'safe_output',side_effect=AssertionError('I/O before authorization')),contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(ctl.main(['--output','invalid',*args]),2)

    def test_semantics_separate_gate_even_if_future_grant(self):
        with patch.object(c,'authorization_status',return_value={'status':'GRANTED'}):
            with self.assertRaisesRegex(ValueError,'BLOCKED_INTEGRATION_SEMANTICS'):c.execution_gate(authorization='METHOD_ONLY',semantics={'status':'UNKNOWN'})

    def test_stage_a_positive_receipt_method_only(self):r.accept_stage_a(receipt(),'METHOD_ONLY')

    def test_stage_a_blocks_other_replicas_without_evidence(self):
        for key,value,reason in [('ME_calls',0,'NO_ACTUAL_ME'),('semantics','UNKNOWN','STAGE_A'),
            ('effective_seed',21,'SEED_IDENTITY'),('zero_retained_LHE',False,'ZERO_LHE'),
            ('actual_counters',{},'MISSING_NATIVE'),('grid_history',[],'MISSING_NATIVE'),
            ('transient_monitoring_coverage',None,'MISSING_NATIVE'),('termination','TIME_LIMIT','PARTIAL'),
            ('scope_sha256','OTHER','SCOPE_MISMATCH')]:
            row=receipt();row[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,reason):r.accept_stage_a(row,'METHOD_ONLY')

    def test_fixed_endpoint_excludes_luminosity_and_accuracy_stop(self):
        p=c.plan_definition()
        for stage in ['adaptation','measurement']:
            e=p['endpoints'][stage];r.endpoint(e,stage)
            for key,value in [('accuracy',-10.),('accuracy',.01),('minimum_iterations',1),('initial_points',1000)]:
                bad={**e,key:value}
                with self.assertRaisesRegex(ValueError,'UNFROZEN_ENDPOINT'):r.endpoint(bad,stage)

    def test_resources_stop_preserves_partial(self):
        r.resource_gate(1,1,1)
        for args in [(14400,1,1),(1,14400,1),(1,1,5*1024**3),(1,1,1,2,1),(1,1,1,1,2)]:
            with self.assertRaisesRegex(ValueError,'RESOURCE_CEILING'):r.resource_gate(*args)
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            p=Path(tmp)/'partial.txt';p.write_text('METHOD_ONLY_PARTIAL_LOG')
            with self.assertRaises(ValueError):r.resource_gate(14400,1,1)
            self.assertEqual(p.read_text(),'METHOD_ONLY_PARTIAL_LOG')

    def test_cross_replica_and_stale_grid_rejected(self):
        rows=[dict(seed=s,workspace=str(s),initial_grid='FRESH_EMPTY',imported_grid=False) for s in c.SEEDS]
        r.grid_identity(rows)
        for key,value in [('workspace',rows[1]['workspace']),('initial_grid','B_GRID'),('imported_grid',True),('seed',21)]:
            bad=copy.deepcopy(rows);bad[0][key]=value
            with self.assertRaises(ValueError):r.grid_identity(bad)

    def test_independent_replica_statistics_known_answer(self):
        rows=[dict(seed=s,workspace=str(s),initial_grid='FRESH_EMPTY',imported_grid=False,status='COMPLETE',
            integrand_sha256='METHOD_ONLY',sigma_pb=x,internal_error_pb=.1) for s,x in zip(c.SEEDS,[1.,2.,3.,4.])]
        out=r.summary(rows)
        self.assertEqual(out['mean_pb'],2.5);self.assertAlmostEqual(out['between_replica_SE_pb'],(5/12)**.5)
        self.assertAlmostEqual(out['within_run_propagated_SE_pb'],.05);self.assertFalse(out['errors_combined'])
        self.assertLess(out['t3_95_interval_pb'][0],.5)
        rows[0]['status']='PARTIAL'
        with self.assertRaisesRegex(ValueError,'PARTIAL_REPLICAS'):r.summary(rows)

    def test_no_event_or_disguised_output(self):
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp:
            root=Path(tmp);p=root/'bad.lhe';p.write_text('METHOD_ONLY_EXTENSION')
            with self.assertRaises(ValueError):writers.output_audit(root)
            p.unlink();p=root/'trace.txt';p.write_text('<event>METHOD_ONLY_BOUNDARY_FIXTURE</event>')
            with self.assertRaises(ValueError):writers.output_audit(root)

    def test_no_existing_plan_overwrite(self):
        with tempfile.TemporaryDirectory(dir=c.REPO) as tmp,patch.object(ctl,'safe_output',return_value=Path(tmp)):
            with self.assertRaisesRegex(ValueError,'PRESERVE_EXISTING'):ctl.prepare(tmp)

    def test_scope_hash_changes_with_endpoint_or_source(self):
        p=c.plan_definition();q=copy.deepcopy(p);q['endpoints']['adaptation']['initial_points']+=1
        self.assertNotEqual(c.scope_identity(p),c.scope_identity(q))
        q=copy.deepcopy(p);q['sources'][0]['sha256']='0'*64
        self.assertNotEqual(c.scope_identity(p),c.scope_identity(q))

if __name__=='__main__':unittest.main()
