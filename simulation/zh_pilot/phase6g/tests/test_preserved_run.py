"""Bounded METHOD_ONLY integrity/algebra controls; never physical reference data.

No complete authorized-run PASS is mocked. Analytic records below exercise
arithmetic/failure methods only, in removed temporary directories. They are not
Monte Carlo events, native validation, or prepared physics references.
"""
from __future__ import annotations
import copy
import csv
from decimal import Decimal
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(REPO))
from simulation.zh_pilot.phase6g import validate_run as v
from simulation.zh_pilot.phase6g import prepare_references as p


def arithmetic_rows(*,selected=False,signed=False):
    """Repeated analytic rows ONLY; not independent physics sample fixtures."""
    rows=[];source={'source_events':[]};hepmc=[]
    for ordinal in range(1,101):
        event_hash=hashlib.sha256(f'METHOD_ONLY_SOURCE_{ordinal}'.encode()).hexdigest()
        output_hash=hashlib.sha256(f'METHOD_ONLY_OUTPUT_{ordinal}'.encode()).hexdigest()
        raw=Decimal(3 if ordinal%2 else -1) if signed else Decimal(1)
        source['source_events'].append({'source_event_content_hash':event_hash,'nominal_generator_weight':str(raw)})
        hepmc.append({'event_block_sha256':output_hash})
        passed=selected and ordinal<=2
        rows.append({'source_event_index':ordinal,'source_event_sha256':event_hash,'hepmc_event_sha256':output_hash,
            'source_contribution_pb':str(raw/100),'selected_photons':2 if passed else 0,'eligible_jets':2 if passed else 0,
            'tagged_bit0':2 if passed else 0,'H_origin_final_truth_photons':2,'H_origin_reco_matches':2 if passed else 0,
            'm_gamma_gamma':'125' if passed else None,'m_bb':'91.188' if passed else None,'m_bb_gamma_gamma':'216.188' if passed else None,
            'cut_photons':bool(passed),'cut_jets':bool(passed),'cut_two_btags':bool(passed),'cut_mgg':bool(passed)})
    return rows,source,hepmc


def write_cutflow(path,rows,source):
    out=io.StringIO();writer=csv.writer(out,lineterminator='\n');writer.writerow(['stage','raw_events','source_weight_sum_pb','source_weight_sum_squared_pb2'])
    for index,stage in enumerate(v.STAGES):
        selected=[(row,event) for row,event in zip(rows,source['source_events']) if index==0 or row[('cut_photons','cut_jets','cut_two_btags','cut_mgg')[index-1]]]
        weights=[Decimal(event['nominal_generator_weight'])/100 for row,event in selected]
        writer.writerow([stage,len(weights),str(sum(weights)),str(sum(w*w for w in weights))])
    path.write_text(out.getvalue(),encoding='utf-8')


def settings_fixture(folder):
    """Synthetic configuration algebra only, no initialization or event output."""
    values={key:True for key in ('ProcessLevel:all','PartonLevel:all','PartonLevel:ISR','PartonLevel:FSR','HadronLevel:all',
        'HadronLevel:Hadronize','HadronLevel:Decay','Beams:strictLHEFscale','Random:setSeed','BeamRemnants:primordialKT')}
    values.update({key:False for key in ('PartonLevel:MPI','SecondHard:generate','HardQCD:all','SoftQCD:all',
        'JetMatching:merge','Merging:doKTMerging','Merging:doMGMerging','Merging:doPTLundMerging','UncertaintyBands:doVariations')})
    values.update({'SLHA:readFrom':0,'Beams:frameType':4,'PartonShowers:model':1,'SpaceShower:pTmaxMatch':1,
        'TimeShower:pTmaxMatch':1,'Random:seed':20261104,'H_forcing':'25:onMode=off;25:onIfMatch=22 22','Z_forcing':'NONE',
        'BeamRemnants:primordialKTsoft':.9,'BeamRemnants:primordialKThard':1.8,'BeamRemnants:halfScaleForKT':1.5,
        'BeamRemnants:halfMassForKT':1,'BeamRemnants:reducedKTatHighY':.5,'BeamRemnants:primordialKTremnant':.4,
        'PDF:pSet':'8','SpaceShower:alphaSvalue':.1365,'TimeShower:alphaSvalue':.1365,'4:m0':1.5,'5:m0':4.8})
    text='# SYNTHETIC_METHOD_ONLY_CONFIG\n'+'\n'.join(key+' = '+('on' if value is True else 'off' if value is False else str(value))
        for key,value in values.items() if key not in ('H_forcing','Z_forcing','4:m0','5:m0'))+'\n'
    for name in ('effective_settings.cmnd','inclusive_initialized_settings.cmnd'):(folder/name).write_text(text,encoding='utf-8')
    return {'required_settings':values}


class PreservedMethods(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='phase6g_integrity_METHOD_ONLY_',dir=REPO/'.local')
        self.folder=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def test_no_run_rejects_before_reference_directory_creation(self):
        destination=self.folder/'reference_samples/zh'
        with self.assertRaises((ValueError,OSError,KeyError)):p.prepare_references(self.folder/'absent',destination)
        self.assertFalse(destination.exists())

    def test_method_and_dryrun_receipts_never_become_preserved_pass(self):
        for status in ('METHOD_ONLY','PASS_PHASE6G_DRY_RUN_NOT_AUTHORIZED','PARTIAL_PHYSICAL_PILOT'):
            (self.folder/'run_manifest.json').write_text(json.dumps({'status':status,'gates':{'C':'NOT_AUTHORIZED'}}))
            (self.folder/'execution_plan.json').write_text(json.dumps({'status':'METHOD_ONLY','physical_execution_authorized':False}))
            before={name:p.sha_file(self.folder/name) for name in ('run_manifest.json','execution_plan.json')}
            with self.assertRaises(ValueError):v.validate_run(self.folder)
            self.assertEqual(before,{name:p.sha_file(self.folder/name) for name in before})

    def test_selection_plan_rejects_method_result(self):
        with self.assertRaises(ValueError):p.selection_plan(self.folder,{'status':'METHOD_ONLY','source_total_events':100})

    def test_cli_missing_authorization_leaves_no_report_or_references(self):
        report=self.folder/'report.json';destination=self.folder/'prepared'
        env=None
        for script,args in ((v.__file__,['--run',str(self.folder),'--report',str(report)]),(p.__file__,['--run',str(self.folder),'--output',str(destination)])):
            result=subprocess.run([sys.executable,'-B',script,*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30,env=env)
            self.assertEqual(result.returncode,2);self.assertIn('BLOCKED_',result.stderr)
        self.assertFalse(report.exists());self.assertFalse(destination.exists())

    def test_jsonl_duplicate_overflow_fixture_and_incomplete_rejected(self):
        path=self.folder/'control.jsonl'
        for raw in (b'{"a":1,"a":2}\n',b'{"a":1e999}\n',b'{"fixture_scope":"METHOD_ONLY"}\n',b'{}',b'{}\n{}\n'):
            path.write_bytes(raw)
            with self.assertRaises(ValueError):v.jsonl(path,1)

    def test_crc_and_plain_identity_methods_preserve_exact_bytes(self):
        path=self.folder/'METHOD_ONLY_CONTROL.gz';raw=b'METHOD_ONLY_NOT_EVENT_DATA\n'*20
        path.write_bytes(gzip.compress(raw,mtime=0));before=path.read_bytes()
        result=v.gzip_identity(path,hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['decompressed_bytes'],len(raw));self.assertEqual(path.read_bytes(),before)

    def test_crc_corruption_truncation_wrong_sha_and_expansion_limit_rejected(self):
        path=self.folder/'METHOD_ONLY_CONTROL.gz';raw=b'METHOD_ONLY'*200;gz=gzip.compress(raw,mtime=0)
        for data,sha,limit in ((gz[:-3],hashlib.sha256(raw).hexdigest(),3000),(gz[:-8]+b'\0'*8,hashlib.sha256(raw).hexdigest(),3000),
            (gz,'0'*64,3000),(gz,hashlib.sha256(raw).hexdigest(),100)):
            path.write_bytes(data)
            with self.assertRaises(ValueError):v.gzip_identity(path,sha,limit)

    def test_snapshot_detects_in_place_mutation_and_resets(self):
        path=self.folder/'receipt.json';path.write_bytes(b'{}\n');guard={};token=v._GUARD.set(guard)
        try:
            v.bounded_file(path);path.write_bytes(b'{"changed":1}\n')
            with self.assertRaises(ValueError):v.bounded_file(path)
            with self.assertRaises(ValueError):v.verify_unchanged(guard)
        finally:v._GUARD.reset(token)
        self.assertIsNone(v._GUARD.get())

    def test_literal_counts_reject_boolean_and_missing(self):
        for data in ({'n':True},{'n':99},{}):
            with self.assertRaises(ValueError):v.literal_counts(data,{'n':100})

    def test_native_derived_outputs_hash_bound_and_mutation_rejected(self):
        # Plain analytic bytes only; no ROOT or simulated records are created.
        names=('reco_events.jsonl','cutflow.csv')
        for name in names:(self.folder/name).write_bytes(b'SYNTHETIC_METHOD_ONLY_BYTE_BINDING\n')
        detector={'derived_files_sha256':{name:p.sha_file(self.folder/name) for name in names}}
        self.assertEqual(v.validate_derived_files(self.folder,detector),detector['derived_files_sha256'])
        (self.folder/'reco_events.jsonl').write_bytes(b'CHANGED_METHOD_ONLY_BINDING\n')
        with self.assertRaises(ValueError):v.validate_derived_files(self.folder,detector)
        detector['derived_files_sha256'].pop('cutflow.csv')
        with self.assertRaises(ValueError):v.validate_derived_files(self.folder,detector)

    def test_settings_integer_serialization_and_exact_seed_methods(self):
        summary=settings_fixture(self.folder);hashes=v.validate_settings(self.folder,summary,20261104)
        self.assertEqual(len(hashes),2)
        with self.assertRaises(ValueError):v.validate_settings(self.folder,summary,20261105)

    def test_settings_MPI_scope_and_record_disagreement_rejected(self):
        summary=settings_fixture(self.folder);summary['required_settings']['PartonLevel:MPI']=True
        with self.assertRaises(ValueError):v.validate_settings(self.folder,summary,20261104)
        summary=settings_fixture(self.folder);path=self.folder/'effective_settings.cmnd'
        path.write_text(path.read_text().replace('PartonLevel:MPI = off','PartonLevel:MPI = on'))
        with self.assertRaises(ValueError):v.validate_settings(self.folder,summary,20261104)

    def test_settings_duplicate_unknown_and_boolean_mode_rejected(self):
        summary=settings_fixture(self.folder);path=self.folder/'effective_settings.cmnd'
        path.write_text(path.read_text()+'Random:seed = 20261104\n')
        with self.assertRaises(ValueError):v.validate_settings(self.folder,summary,20261104)
        summary=settings_fixture(self.folder);summary['required_settings']['invented_physics_switch']=False
        with self.assertRaises(ValueError):v.validate_settings(self.folder,summary,20261104)
        summary=settings_fixture(self.folder);summary['required_settings']['Beams:frameType']=True
        with self.assertRaises(ValueError):v.validate_settings(self.folder,summary,20261104)

    def test_zero_survivors_valid_arithmetic_and_nullable_pairs(self):
        rows,source,hepmc=arithmetic_rows();path=self.folder/'METHOD_ONLY_cutflow.csv';write_cutflow(path,rows,source)
        result=v.validate_cutflow(path,rows,source,hepmc)
        self.assertEqual(result['00_input']['raw_events'],100);self.assertEqual(result['04_mgg_105_160']['raw_events'],0)
        self.assertEqual(Decimal(result['00_input']['source_weight_sum_pb']),1)

    def test_signed_source_weight_moments_no_output_normalization(self):
        rows,source,hepmc=arithmetic_rows(selected=True,signed=True);path=self.folder/'METHOD_ONLY_cutflow.csv';write_cutflow(path,rows,source)
        result=v.validate_cutflow(path,rows,source,hepmc)
        self.assertEqual(Decimal(result['04_mgg_105_160']['source_weight_sum_pb']),Decimal('.02'))
        self.assertEqual(Decimal(result['04_mgg_105_160']['source_weight_sum_squared_pb2']),Decimal('.001'))
        self.assertEqual(Decimal(result['00_input']['source_weight_sum_squared_pb2']),Decimal('.05'))

    def test_pair_nullability_and_nonfinite_mass_reject(self):
        for key,value in (('m_gamma_gamma',0),('m_bb','Infinity'),('m_bb_gamma_gamma',0)):
            rows,source,hepmc=arithmetic_rows();rows[0][key]=value;path=self.folder/'METHOD_ONLY_cutflow.csv';write_cutflow(path,rows,source)
            with self.assertRaises(ValueError):v.validate_cutflow(path,rows,source,hepmc)

    def test_nested_count_identity_denominator_and_H_matching_reject(self):
        changes=({'source_event_index':2},{'source_contribution_pb':'.1'},{'cut_jets':True},{'cut_photons':1},
            {'H_origin_reco_matches':3},{'H_origin_final_truth_photons':0,'H_origin_reco_matches':1})
        for change in changes:
            rows,source,hepmc=arithmetic_rows();rows[0].update(change);path=self.folder/'METHOD_ONLY_cutflow.csv';write_cutflow(path,rows,source)
            with self.assertRaises(ValueError):v.validate_cutflow(path,rows,source,hepmc)

    def test_mgg_closed_window_exact_endpoints(self):
        for mass,passed in (('105',True),('160',True),('104.999999999',False),('160.000000001',False)):
            rows,source,hepmc=arithmetic_rows(selected=True);rows[0]['m_gamma_gamma']=mass;rows[0]['cut_mgg']=passed
            path=self.folder/'METHOD_ONLY_cutflow.csv';write_cutflow(path,rows,source);v.validate_cutflow(path,rows,source,hepmc)
            rows[0]['cut_mgg']=not passed;write_cutflow(path,rows,source)
            with self.assertRaises(ValueError):v.validate_cutflow(path,rows,source,hepmc)

    def test_wrong_cutflow_stage_or_sum_rejected(self):
        rows,source,hepmc=arithmetic_rows();path=self.folder/'METHOD_ONLY_cutflow.csv';write_cutflow(path,rows,source)
        original=path.read_text()
        for raw in (original.replace('00_input','00_fake'),original.replace('00_input,100,1.00','00_input,100,2.00'),original+original.splitlines()[1]+'\n'):
            path.write_text(raw)
            with self.assertRaises(ValueError):v.validate_cutflow(path,rows,source,hepmc)

    def items(self):
        # Byte-budget controls only: these are plain labels, never simulated data.
        values=[]
        for index in range(3):
            path=self.folder/f'METHOD_ONLY_byte_control_{index}.bin';path.write_bytes(b'METHOD_ONLY_BYTE_BUDGET')
            values.append({'path':f'asset{index}','category':'ASSET','source':path,'expected_sha256':p.sha_file(path)})
        return values

    def test_inspect_plan_hash_paths_and_categories(self):
        items=self.items();prepared,limits=p.inspect_plan(items)
        self.assertEqual(limits['asset_files'],3);self.assertEqual(limits['asset_bytes'],69)
        for change in ({'path':'../escape'},{'expected_sha256':'0'*64},{'category':'BINARY_EXECUTABLE'}):
            bad=copy.deepcopy(items);bad[0].update(change)
            with self.assertRaises(ValueError):p.inspect_plan(bad)
        with self.assertRaises(ValueError):p.inspect_plan(items+[items[0]])

    def test_combined_asset_budget_is_checked_before_directory_creation(self):
        destination=self.folder/'not_created';items=self.items()
        with patch.object(p,'MAX_COMBINED_ASSETS',60):
            with self.assertRaises(ValueError):p.inspect_plan(items)
        self.assertFalse(destination.exists())

    def test_text_perfile_and_total_byte_budgets(self):
        items=self.items()+[{'path':'METHOD_ONLY_receipt.json','category':'TEXT','data':b'{}\n'*10}]
        with patch.object(p,'MAX_TEXT',20):
            with self.assertRaises(ValueError):p.inspect_plan(items)
        with patch.object(p,'MAX_COMBINED_TEXT',20):
            with self.assertRaises(ValueError):p.inspect_plan(items)

    def test_destination_rejects_existing_source_overlap_and_repository_ancestor(self):
        for destination in (self.folder,self.folder/'child',self.folder.parent,REPO):
            with self.assertRaises(ValueError):p.safe_destination(destination,self.folder)

    def test_destination_protects_configured_sources_builds_and_historical_runs(self):
        repo=self.folder/'METHOD_ONLY_REPOSITORY';(repo/'.local').mkdir(parents=True)
        source=self.folder/'retained_source';build=self.folder/'retained_build';environment=self.folder/'retained_environment'
        native_binary=self.folder/'retained_native_bin'/'reader';old_py=self.folder/'simulations/pythia8_runs/historical_1000'
        config={'source_dir':str(source),'build_dir':str(build),'root_prefix':str(environment),'validator_path':str(native_binary),
            'phase6b_runs':{'bbgg':str(old_py)}}
        for name in ('mg5_installation','pythia8_installation','delphes_installation'):(repo/'.local'/f'{name}.json').write_text(json.dumps(config))
        # Only import the unchanged helper from the real repository; config roots
        # below are synthetic path-protection controls, never installed tools.
        sys.path.insert(0,str(REPO/'simulation/zh_pilot/scripts'))
        with patch.object(p,'REPO',repo):
            for root in (source,build,environment,native_binary.parent,old_py,old_py.parent,self.folder/'simulations/delphes_runs'):
                with self.assertRaises(ValueError):p.safe_destination(root/'new_reference_package',self.folder/'original_run')
            good=self.folder/'local_review'
            self.assertEqual(p.safe_destination(good,self.folder/'original_run'),good.resolve())

if __name__=='__main__':unittest.main()
