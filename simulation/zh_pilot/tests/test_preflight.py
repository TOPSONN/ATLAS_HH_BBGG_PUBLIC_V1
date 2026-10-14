"""Independent planning guards; synthetic paths/configs are not physics samples."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[3]
TEMP=REPO/'.local/phase6f-test-tmp'
TEMP.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(REPO/'simulation/zh_pilot/scripts'))
import prepare_pilot as cli


def request(**changes):
    obj=dict(process='zh',events=100,seed=20261104,energy=13000,dry_run=True,max_hours=2,max_disk_gb=5)
    obj.update(changes)
    return argparse.Namespace(**obj)


class RequestTests(unittest.TestCase):
    def test_reviewed_request(self):
        cli.validate_request(request())

    def test_typed_api_cannot_accept_truthy_flags_or_boolean_numbers(self):
        for key,value in (('seed',True),('events',True),('energy',True),('dry_run','false'),
                          ('max_hours',True),('max_disk_gb',True)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                cli.validate_request(request(**{key:value}))

    def test_non_dry_rejects_before_environment_or_output(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            target=Path(directory)/'must_not_exist'
            with patch.object(cli,'verify_environment',side_effect=AssertionError('environment reached')):
                rc=cli.main(['--process','zh','--events','100','--seed','1','--energy','13000','--output',str(target)])
            self.assertEqual(rc,2);self.assertFalse(target.exists())

    def test_large_other_energy_and_seed(self):
        for changes in ({'events':1000},{'events':0},{'process':'tth'},{'energy':14000},
                        {'seed':0},{'seed':900000001},{'energy':float('nan')}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                cli.validate_request(request(**changes))

    def test_nonfinite_and_overflow_limits(self):
        for key in ('max_hours','max_disk_gb'):
            for value in (0,-1,float('nan'),float('inf'),1e308):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    cli.validate_request(request(**{key:value}))

    def test_real_cli_no_production_subprocess(self):
        result=subprocess.run([sys.executable,'-B',str(REPO/'simulation/zh_pilot/scripts/prepare_pilot.py'),
           '--process','zh','--events','100','--seed','1','--energy','13000'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('NOT_AUTHORIZED',result.stderr)


class BundleTests(unittest.TestCase):
    def make_bundle(self,root):
        module=root/'simulation/zh_pilot'; (module/'cards').mkdir(parents=True)
        config=module/'config';config.mkdir()
        policy={'schema_version':1,'physical_production_authorized':False,'physical_execution_gate':'NOT_AUTHORIZED',
                'process':'zh','events':100,'energy_gev':13000,'workers':1,
                'required_decay_ids':['Z_to_b_bbar','H_to_gamma_gamma']}
        for name in ('preflight_policy','generator_contract','decay_contract','input_profiles'):
            (config/(name+'.json')).write_text(json.dumps(policy if name=='preflight_policy' else {'schema_version':1}))
        (module/'cards/production.mg5').write_text('SYNTHETIC_TEST_ONLY\n')
        files=[{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(module.rglob('*')) if p.is_file()]
        bundle={'schema_version':1,'physical_production_authorized':False,'files':files}
        (config/'bundle.json').write_text(json.dumps(bundle))
        return module,config,bundle

    def test_bound_snapshots_and_mutations(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            root=Path(directory);module,_,_=self.make_bundle(root)
            _,snapshots=cli.bound_bundle(root)
            self.assertEqual(len(snapshots),5)
            (module/'cards/production.mg5').write_text('changed')
            with self.assertRaises(ValueError):cli.bound_bundle(root)

    def test_additional_card_unbound(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            root=Path(directory);module,_,_=self.make_bundle(root)
            (module/'cards/new.mg5').write_text('generate invalid')
            with self.assertRaises(ValueError):cli.bound_bundle(root)

    def test_bad_scope_duplicate_and_hash(self):
        for mode in ('duplicate','outside','hash','authorization'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory(dir=TEMP) as directory:
                root=Path(directory);_,config,bundle=self.make_bundle(root)
                if mode=='duplicate':bundle['files'].append(bundle['files'][0])
                if mode=='outside':bundle['files'][0]['path']='simulation/zh_pilot/../private.json'
                if mode=='hash':bundle['files'][0]['sha256']='0'*64
                if mode=='authorization':bundle['physical_production_authorized']=True
                (config/'bundle.json').write_text(json.dumps(bundle))
                with self.assertRaises(ValueError):cli.bound_bundle(root)

    def test_nonfinite_schema_bool_and_json(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            path=Path(directory)/'config.json'
            for raw in ('{"schema_version":true}','{"schema_version":1,"number":NaN}',
                        '{"schema_version":1,"schema_version":1}'):
                path.write_text(raw)
                with self.assertRaises(ValueError):cli.load_json(path)


class ResourceTests(unittest.TestCase):
    def test_contradictory_named_weights_cannot_pass_cross_contract(self):
        generator=json.loads((REPO/'simulation/zh_pilot/config/generator_contract.json').read_text())
        decay=json.loads((REPO/'simulation/zh_pilot/config/decay_contract.json').read_text())
        profiles=json.loads((REPO/'simulation/zh_pilot/config/input_profiles.json').read_text())
        policy=json.loads((REPO/'simulation/zh_pilot/config/preflight_policy.json').read_text())
        names=['input_contribution_pb','LHE_XWGTUP_pb','Pythia_Info_weight_pb','converter_weight_0_pb']
        decay['nominal_weight_columns']=names
        self.assertEqual(cli.cross_contract_check(generator,decay,profiles,policy)['physical_validation'],'NOT_EXECUTED')
        decay['nominal_weight_columns']=names[:-1]+['invented_column']
        with self.assertRaises(ValueError):cli.cross_contract_check(generator,decay,profiles,policy)

    def test_registered_source_and_build_roots_are_protected(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            root=Path(directory)
            source=root/'state/atlas-hh-phase6c/src/delphes'
            build=root/'state/atlas-hh-phase6c/build/analyzer'
            cfg={'analyzer_path':str(build/'analyze_delphes'),
                 'source_sha256':{str(source/'modules/a.cc'):'0'*64,str(source/'classes/b.cc'):'0'*64}}
            protected=cli.configured_protected_paths(cfg)
            for path in (source/'new',build/'new',root/'state/atlas-hh-phase6c/new'):
                with self.subTest(path=path),self.assertRaises(ValueError):
                    cli.safe_output(path,protected,repo=root/'repo')

    def test_successful_main_retains_semantic_checks_and_seed_card(self):
        import validate_profiles,check_decay_tables
        run_path='simulation/zh_pilot/cards/run_card.dat'
        snapshots={run_path:(REPO/run_path).read_bytes()}
        policy={'expected_outputs':{'production_lhe':'NOT_CREATED_IN_TEST'}}
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            output=Path(directory)/'plan'
            with patch.object(cli,'bound_bundle',return_value=(policy,snapshots)), \
                 patch.object(validate_profiles,'validate_card_contract',return_value={'status':'TEST_METHOD_ONLY'}), \
                 patch.object(validate_profiles,'validate_profile_config',return_value={'status':'TEST_METHOD_ONLY'}), \
                 patch.object(check_decay_tables,'validate_decay_contract',return_value={'status':'TEST_METHOD_ONLY'}), \
                 patch.object(cli,'cross_contract_check',return_value={'status':'TEST_METHOD_ONLY'}), \
                 patch.object(cli,'load_json',return_value={}), \
                 patch.object(cli,'verify_environment',return_value={'status':'TEST_ENVIRONMENT_STUB'}), \
                 patch.object(cli,'protected_paths',return_value=[]), \
                 patch.object(cli,'safe_output',return_value=output), \
                 patch.object(cli,'resources',return_value={'administrative_disk_budget_bytes':6*1024**3}):
                result=cli.main(['--process','zh','--events','100','--seed','42','--energy','13000','--dry-run','--output',str(output)])
            self.assertEqual(result,0)
            plan=json.loads((output/'readiness_plan.json').read_text())
            self.assertEqual(set(plan['semantic_contract_checks']),{'generator','input_profiles','decay','cross_contracts'})
            self.assertTrue(all(x['status']=='TEST_METHOD_ONLY' for x in plan['semantic_contract_checks'].values()))
            self.assertIn('42= iseed',(output/'prepared/run_card.dat').read_text())
            self.assertEqual(plan['physical_execution_gate'],'NOT_AUTHORIZED')
            self.assertFalse((output/'mg5').exists())

    def test_request_seed_changes_only_declared_card_fields(self):
        raw=b'100 = nevents\n620101 = iseed\n6500 = ebeam1\n6500 = ebeam2\n216.188 = scale\n'
        prepared,overrides=cli.requested_run_card(raw,request(seed=42))
        self.assertIn(b'42= iseed',prepared)
        self.assertIn(b'216.188 = scale',prepared)
        self.assertEqual(set(overrides),{'nevents','iseed','ebeam1','ebeam2'})
        with self.assertRaises(ValueError):cli.requested_run_card(raw+b'1 = iseed\n',request())

    def test_preserve_existing_and_protected_paths(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            root=Path(directory);protected=root/'installed';protected.mkdir()
            with self.assertRaises(ValueError):cli.safe_output(protected/'new',[protected],repo=root/'repo')
            with self.assertRaises(ValueError):cli.safe_output(root,[],repo=root/'repo')
            with self.assertRaises(ValueError):cli.safe_output(root/'has space',[],repo=root/'repo')
            self.assertEqual(cli.safe_output(root/'new',[],repo=root/'repo'),root/'new')

    def test_budget_and_unknown_projection(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            with patch.object(cli.shutil,'disk_usage',return_value=argparse.Namespace(free=1024**3)):
                with self.assertRaises(ValueError):cli.resources(Path(directory)/'out',2)
                result=cli.resources(Path(directory)/'out',.5)
            for key in ('projected_wall_seconds','projected_peak_ram_bytes','projected_storage_bytes'):
                self.assertEqual(result[key],'UNKNOWN')
            self.assertEqual(result['requested_workers'],1)


if __name__=='__main__':unittest.main()
