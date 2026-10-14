"""Portable bounded METHOD_ONLY fixtures; no native process or physics event call."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

REPO=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('test_phase6g_stage',REPO/'simulation/zh_pilot/phase6g/scripts/shower_stage.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


def fixture():
    rows=[['1','1','-1.23D-3','125','0.007','0.12'], ['25','1','1','2','0','0','0','0','0','125','125','0','9']]
    return {'status':'METHOD_ONLY','actual_events':100,'source_events':[
        {'source_event_index':i,'source_event_content_hash':format(i,'064x'),'rows':rows} for i in range(1,101)]}


def local_temp():
    parent=(REPO/'.local/phase6g/method-test-temp').resolve()
    if REPO.resolve() not in parent.parents:
        raise ValueError('Temporary test paths must stay in the workspace')
    parent.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(dir=parent)


class ShowerMethodTests(unittest.TestCase):
    def test_guarded_compile_callback_contract_without_native_execution(self):
        """Simulated callback exercises every build stage; never starts a process."""
        build=stage._build
        with local_temp() as temp:
            root=Path(temp);pythia=root/'METHOD_ONLY_pythia';hepmc=root/'METHOD_ONLY_hepmc'
            files=[pythia/'lib/libpythia8.so',hepmc/'lib/libHepMC3.so.4',
                   pythia/'include/Pythia8/Pythia.h',pythia/'share/Pythia8/xmldoc/METHOD_ONLY.xml',
                   root/'METHOD_ONLY_existing_runner',root/'METHOD_ONLY_existing_reader']
            for path in files:
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'SYNTHETIC_METHOD_ONLY_NOT_NATIVE')
            config={'pythia_prefix':str(pythia),'hepmc3_prefix':str(hepmc),'xml_path':str(files[3].parent),
                'pythia_version':'8.317','hepmc3_version':'3.3.1',
                'pythia_source_commit':'83a5c9986f30746cfb390435a9b10ac55a758fca',
                'hepmc3_source_commit':'beb66aa1a2ac263066becdee26d18ead83edec95',
                'runner_path':str(files[4]),'validator_path':str(files[5]),
                'library_sha256':{str(path):build.digest(path) for path in files[:2]},
                'header_sha256':{str(files[2]):build.digest(files[2])},'xml_sha256':{str(files[3]):build.digest(files[3])}}
            calls=[];labels=set()
            def callback(argv,cwd,label,env=None,expected_exit_code=0):
                self.assertRegex(label,r'^[a-z0-9_]+$');self.assertNotIn(label,labels);labels.add(label)
                calls.append((label,list(argv),expected_exit_code))
                self.assertIs(type(expected_exit_code),int)
                if expected_exit_code:
                    self.assertEqual(expected_exit_code,2);self.assertTrue(label.endswith('_missing_authorization'))
                    self.assertEqual(len(argv),1);self.assertIn(Path(argv[0]).name,('zh_shower','validate_zh_hepmc3'))
                    content='BLOCKED_PHYSICAL_AUTHORIZATION: SYNTHETIC_METHOD_ONLY\n'
                elif argv[0]=='METHOD_ONLY_COMPILER':
                    if '--version' in argv:content='METHOD_ONLY simulated compiler\n'
                    else:Path(argv[argv.index('-o')+1]).write_bytes(b'SYNTHETIC_METHOD_ONLY_NOT_NATIVE');content=''
                elif argv[0]=='ldd':
                    content='libpythia8.so => '+str(files[0])+' (METHOD_ONLY)\nlibHepMC3.so.4 => '+str(files[1])+' (METHOD_ONLY)\n'
                elif label=='zh_method_fixtures':
                    content=json.dumps({'status':'METHOD_ONLY','new_physics_events':0,'next_calls':0,'checks':21})
                elif label=='zh_settings_preflight':content=json.dumps({'status':'DRY_RUN','events_processed':0})
                else:
                    self.assertIn('--build-info',argv)
                    content=json.dumps({'pythia_version_integer':8317,'hepmc3_version':'3.03.01','cxx_standard':202002})
                log=Path(cwd)/(label+'.log');log.write_text(content,encoding='utf-8')
                return {'exit_code':expected_exit_code,'log_path':str(log)}
            with mock.patch.object(build.shutil,'which',return_value='METHOD_ONLY_COMPILER'),\
                 mock.patch.object(build.subprocess,'run',side_effect=AssertionError('No direct process in guarded path')):
                result=build.compile_bridge(root/'METHOD_ONLY_build',config,run_command=callback)
            self.assertEqual(result['next_calls'],0);self.assertEqual(len(calls),19)
            self.assertEqual({label for label,_,code in calls if code},
                {'zh_shower_missing_authorization','validate_zh_hepmc3_missing_authorization'})
            self.assertIn('existing_prebuild_runner_build_info',labels);self.assertIn('existing_postbuild_runner_build_info',labels)

    def test_expected_probe_unexpected_success_is_rejected(self):
        callback=mock.Mock(return_value={'exit_code':0,'log_path':'NOT_READ'})
        with self.assertRaises(ValueError):
            stage._build.invoke(['/METHOD_ONLY/zh_shower'],Path('.'),'zh_shower_missing_authorization',{},
                                run_command=callback,expected_exit_code=2)
        self.assertEqual(callback.call_args.kwargs['expected_exit_code'],2)

    def test_ordinary_callback_failure_remains_fatal(self):
        callback=mock.Mock(return_value={'exit_code':2,'log_path':'NOT_READ'})
        with self.assertRaises(ValueError):
            stage._build.invoke(['METHOD_ONLY_COMPILER'],Path('.'),'zh_shower_build',{},run_command=callback)
        self.assertEqual(callback.call_args.kwargs['expected_exit_code'],0)

    def test_invalid_stage_or_negative_policy_rejects_before_callback(self):
        callback=mock.Mock(side_effect=AssertionError('Invalid policy must reject before callback'))
        for argv,label,expected in ((['zh_shower'],'zh_shower.build',0),(['zh_shower'],'zh_shower_build',2),
                                    (['zh_shower','--input','FORBIDDEN'],'zh_shower_missing_authorization',2),
                                    (['OTHER'],'other_missing_authorization',2),(['zh_shower'],'zh_shower_missing_authorization',True)):
            with self.subTest(label=label,expected=expected),self.assertRaises(ValueError):
                stage._build.invoke(argv,Path('.'),label,{},run_command=callback,expected_exit_code=expected)
        callback.assert_not_called()

    def test_source_index_keeps_full_denominator(self):
        raw=stage.source_index_bytes(fixture(),method_only=True)
        self.assertEqual(sum(line.startswith(b'E ') for line in raw.splitlines()),100)
        self.assertEqual(sum(line.startswith(b'P ') for line in raw.splitlines()),100)

    def test_index_exponent_adaptation_does_not_modify_original_rows(self):
        value=fixture();before=json.dumps(value)
        raw=stage.source_index_bytes(value,method_only=True)
        self.assertIn(b'-1.23E-3',raw)
        self.assertEqual(json.dumps(value),before)

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

    def test_invalid_resource_budgets_rejected(self):
        for value in (True,'2',float('nan'),float('inf'),0,-1,2.01):
            with self.subTest(value=value),self.assertRaises(ValueError):stage.positive_budget(value,2)

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
        with self.assertRaises(ValueError):stage.check_live_job({'ticket_id':'METHOD_ONLY','deadline_epoch_seconds':200},
            {'status':'CLOSED','ticket_id':'METHOD_ONLY'},100)

    def test_different_ticket_reentry_rejected(self):
        with self.assertRaises(ValueError):stage.check_live_job({'ticket_id':'METHOD_ONLY','deadline_epoch_seconds':200},
            {'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','ticket_id':'OTHER_METHOD'},100)

    def test_expired_stage_reentry_rejected(self):
        with self.assertRaises(ValueError):stage.check_live_job({'ticket_id':'METHOD_ONLY','deadline_epoch_seconds':100},
            {'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','ticket_id':'METHOD_ONLY'},100)

    def test_nonfinite_or_boolean_deadline_rejected(self):
        for deadline in (True,float('inf'),float('nan'),'UNKNOWN'):
            with self.subTest(deadline=deadline),self.assertRaises(ValueError):
                stage.check_live_job({'ticket_id':'METHOD_ONLY','deadline_epoch_seconds':deadline},
                    {'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','ticket_id':'METHOD_ONLY'},100)

    def test_no_unguarded_subprocess_in_runtime_api(self):
        source=(REPO/'simulation/zh_pilot/phase6g/scripts/shower_stage.py').read_text()
        self.assertNotIn('import subprocess',source)
        self.assertNotIn('subprocess.run',source)


if __name__=='__main__':unittest.main()
