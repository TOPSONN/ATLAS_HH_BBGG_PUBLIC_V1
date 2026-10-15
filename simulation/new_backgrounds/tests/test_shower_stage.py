"""Portable bounded METHOD_ONLY fixtures; no native process or physics event call."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

REPO=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('test_phase6g_stage',REPO/'simulation/new_backgrounds/scripts/shower_stage.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


def fixture():
    rows=[['1','1','-1.23D-3','125','0.007','0.12'], ['25','1','1','2','0','0','0','0','0','125','125','0','9']]
    return {'status':'METHOD_ONLY','actual_events':1000,'source_events':[
        {'source_event_index':i,'source_event_content_hash':format(i,'064x'),'rows':rows} for i in range(1,1001)]}


def local_temp():
    parent=(REPO/'.local/phase6g_backgrounds/method-test-temp').resolve()
    if REPO.resolve() not in parent.parents:
        raise ValueError('Temporary test paths must stay in the workspace')
    parent.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(dir=parent)


class ShowerMethodTests(unittest.TestCase):
    def test_expected_probe_unexpected_success_is_rejected(self):
        callback=mock.Mock(return_value={'exit_code':0,'log_path':'NOT_READ'})
        with self.assertRaises(ValueError):
            stage._build.invoke(['/METHOD_ONLY/shower_background'],Path('.'),'shower_background_missing_authorization',{},
                                run_command=callback,expected_exit_code=2)
        self.assertEqual(callback.call_args.kwargs['expected_exit_code'],2)

    def test_ordinary_callback_failure_remains_fatal(self):
        callback=mock.Mock(return_value={'exit_code':2,'log_path':'NOT_READ'})
        with self.assertRaises(ValueError):
            stage._build.invoke(['METHOD_ONLY_COMPILER'],Path('.'),'shower_background_build',{},run_command=callback)
        self.assertEqual(callback.call_args.kwargs['expected_exit_code'],0)

    def test_invalid_stage_or_negative_policy_rejects_before_callback(self):
        callback=mock.Mock(side_effect=AssertionError('Invalid policy must reject before callback'))
        for argv,label,expected in ((['shower_background'],'shower_background.build',0),(['shower_background'],'shower_background_build',2),
                                    (['shower_background','--input','FORBIDDEN'],'shower_background_missing_authorization',2),
                                    (['OTHER'],'other_missing_authorization',2),(['shower_background'],'shower_background_missing_authorization',True)):
            with self.subTest(label=label,expected=expected),self.assertRaises(ValueError):
                stage._build.invoke(argv,Path('.'),label,{},run_command=callback,expected_exit_code=expected)
        callback.assert_not_called()



    def test_method_fixture_cannot_be_claimed_physical(self):
        with self.assertRaises(ValueError):stage.source_index_bytes(fixture())

    def test_scope_flag_literal_bool_required(self):
        with self.assertRaises(ValueError):stage.source_index_bytes(fixture(),method_only='UNKNOWN')

    def test_prefix_is_not_new_source_denominator(self):
        value=fixture();value['source_events']=value['source_events'][:10]
        with self.assertRaises(ValueError):stage.source_index_bytes(value,method_only=True)

    def test_duplicate_or_unmapped_source_index_rejected(self):
        value=fixture();value['source_events'][1]['source_event_index']=1
        with self.assertRaises(ValueError):stage.source_index_bytes(value,method_only=True)

    def test_invalid_raw_hash_rejected(self):
        value=fixture();value['source_events'][0]['source_event_content_hash']='UNKNOWN'
        with self.assertRaises(ValueError):stage.source_index_bytes(value,method_only=True)

    def test_nup_or_particle_fields_rejected(self):
        value=fixture();value['source_events'][0]['rows']=[['2','1','1','125','0','0'],value['source_events'][0]['rows'][1]]
        with self.assertRaises(ValueError):stage.source_index_bytes(value,method_only=True)

    def test_duplicate_json_keys_rejected(self):
        with local_temp() as temp:
            path=Path(temp)/'fixture.json';path.write_text('{"status":1,"status":2}')
            with self.assertRaises(ValueError):stage.load_json(path)

    def test_nonfinite_json_rejected(self):
        with local_temp() as temp:
            path=Path(temp)/'fixture.json';path.write_text('{"value":NaN}')
            with self.assertRaises(ValueError):stage.load_json(path)

    def test_overflow_json_number_rejected(self):
        with local_temp() as temp:
            path=Path(temp)/'fixture.json';path.write_text('{"value":1e309}')
            with self.assertRaises(ValueError):stage.load_json(path)

    def test_invalid_resource_budgets_rejected(self):
        for maximum in (4,10):
            for value in (True,'2',float('nan'),float('inf'),0,-1,maximum+0.01):
                with self.subTest(value=value,maximum=maximum),self.assertRaises(ValueError):stage.positive_budget(value,maximum)

    def test_supported_caps_are_bounds(self):
        stage.positive_budget(4,4);stage.positive_budget(10,10)

    def test_missing_stage_authorization_never_calls_callback(self):
        callback=mock.Mock(side_effect=AssertionError('No physical callback allowed'))
        with local_temp() as temp:
            build=Path(temp)/'build.json';build.write_text('{}')
            with self.assertRaises(ValueError):
                stage.run_stage(authorization_file=Path(temp)/'absent.json',stage='prefix10',build_receipt=build,
                    source_validation={},xml_path='NOT_USED',run_id='METHOD_ONLY',run_command=callback)
        callback.assert_not_called()

    def test_truthy_unknown_authorization_rejected(self):
        with local_temp() as temp:
            path=Path(temp)/'authorization.json';path.write_text(json.dumps({'schema_version':1,'status':'UNKNOWN','authorization_command':stage.COMMAND}))
            with self.assertRaises(ValueError):stage.check_stage_receipt(path,'prefix10',{})

    def test_closed_job_reentry_rejected(self):
        with self.assertRaises(ValueError):stage.check_live_job({'campaign_id':'METHOD_ONLY','deadline_epoch_seconds':200},
            {'status':'CLOSED','campaign_id':'METHOD_ONLY'},100)

    def test_different_ticket_reentry_rejected(self):
        with self.assertRaises(ValueError):stage.check_live_job({'campaign_id':'METHOD_ONLY','deadline_epoch_seconds':200},
            {'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','campaign_id':'OTHER_METHOD'},100)

    def test_expired_stage_reentry_rejected(self):
        with self.assertRaises(ValueError):stage.check_live_job({'campaign_id':'METHOD_ONLY','deadline_epoch_seconds':100},
            {'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','campaign_id':'METHOD_ONLY'},100)

    def test_nonfinite_or_boolean_deadline_rejected(self):
        for deadline in (True,float('inf'),float('nan'),'UNKNOWN'):
            with self.subTest(deadline=deadline),self.assertRaises(ValueError):
                stage.check_live_job({'campaign_id':'METHOD_ONLY','deadline_epoch_seconds':deadline},
                    {'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','campaign_id':'METHOD_ONLY'},100)

    def test_no_unguarded_subprocess_in_runtime_api(self):
        source=(REPO/'simulation/new_backgrounds/scripts/shower_stage.py').read_text()
        self.assertNotIn('import subprocess',source)
        self.assertNotIn('subprocess.run',source)


if __name__=='__main__':unittest.main()
