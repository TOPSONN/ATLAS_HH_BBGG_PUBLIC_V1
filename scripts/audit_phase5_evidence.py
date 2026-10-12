#!/usr/bin/env python3
"""Assemble executed Phase 5 evidence without promoting unknown physics inputs."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

BASE='704045c6c18c313114e3ab41019e46c70beb086b'
EXPECTED_TESTS={
    'root_io','rdataframe','roofit_roostats','root_schema_suite','bounded_transfer',
    'kinematic_numerics','native_local_events','phase2_driver_contract','unit_evidence_gate',
    'selection_boundaries','phase3_driver_contract','native_mc_events','synthetic_matching_contract',
    'mc_matching_adapter','cartesian_stability_contract','phase4_driver_contract','phase4_transfer_budget',
    'phase4_unit_evidence','signed_normalization_contract','signed_shape_covariance',
    'control_region_contract','phase5_transfer_contract','phase5_region_driver'}


def sha(path,lf=False):
    raw=path.read_bytes()
    return hashlib.sha256(raw.replace(b'\r\n',b'\n') if lf else raw).hexdigest()


def main():
    if not __debug__:raise RuntimeError('Evidence validation requires Python assertion checks enabled')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',required=True,type=Path)
    parser.add_argument('--step1-build',required=True,type=Path)
    parser.add_argument('--region-root',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path('metadata/phase5_quality_gates.json'))
    args=parser.parse_args()
    occupancy_path=Path('metadata/phase5_region_occupancy.csv')
    assert not args.output.exists() and not occupancy_path.exists(),'Evidence outputs must be new files'
    subprocess.run(['python','-B','scripts/freeze_phase5_baseline.py','metadata/phase5_baseline_preservation.json','--verify'],check=True)
    xml=args.build_dir/'phase5_ctest.xml'
    cases=ET.parse(xml).getroot().findall('testcase')
    assert {case.attrib['name'] for case in cases}==EXPECTED_TESTS and len(cases)==23
    assert all(not any(case.find(tag) is not None for tag in ('failure','error','skipped')) for case in cases)
    last=args.step1_build/'Testing/Temporary/LastTest.log'
    text=last.read_text()
    assert set(re.findall(r'Testing: (\S+)',text))=={'root_io','rdataframe','roofit_roostats'}
    assert text.count('Test Passed.')==3 and 'Test Failed.' not in text
    tested=json.loads((args.build_dir/'phase5_test_source_hashes.json').read_text())
    for path,expected in tested.items():assert sha(Path(path),True)==expected,path
    environment={}
    for line in (args.build_dir/'step1_cmake_environment.txt').read_text().splitlines():
        key,value=line.split('=',1);environment[key]=value
    assert environment['ROOT_VERSION']=='6.40.04' and environment['ROOT_CXX_STANDARD']=='20'
    assert environment['PROJECT_CXX_STANDARD']=='20' and environment['CXX_STANDARD_REQUIRED']=='ON' and environment['CXX_EXTENSIONS']=='OFF'
    linkages=json.loads((args.build_dir/'phase5_linkage.json').read_text())
    assert environment['CXX_COMPILER']==linkages['compiler']
    for name,linkage in linkages['linked'].items():assert 'not found' not in linkage,name
    weights=json.loads(Path('metadata/phase5_weight_observations.json').read_text())
    assert weights['status']=='PASS' and weights['normalization']=='BLOCKED' and weights['bounded_event_rows']==29700
    for path,expected in weights['source_inputs_sha256'].items():assert sha(Path(path))==expected,path
    assert weights['script_sha256']==sha(Path('scripts/audit_phase5_weights.py'))
    with Path('metadata/phase5_dsid_manifest.csv').open(newline='') as handle:dsids=list(csv.DictReader(handle))
    assert {r['dsid'] for r in dsids}=={'302521','302520','364352','343981','346214','423103'}
    official_path=Path('.local/phase5_sources_20261012/record93922.json')
    official=json.loads(official_path.read_text())['metadata']
    assert str(official['recid'])=='93922' and official['doi']=='10.7483/OPENDATA.ATLAS.IMZO.7U52'
    official_files={r['key']:r for r in official['_files']}
    table_path=Path('.local/phase0_sources/framework_extras_metadata.csv.txt')
    with table_path.open(newline='') as handle:table={r['dataset_number']:r for r in csv.DictReader(handle)}
    for row in dsids:
        entry=official_files[row['filename']];candidate=table[row['dsid']]
        assert int(row['size_bytes'])==entry['size'] and row['published_checksum']==entry['checksum']
        for public_field,file_field in (('file_id','file_id'),('version_id','version_id'),('bucket_id','bucket'),('release_uri','uri')):
            assert row[public_field]==entry[file_field]
        assert row['record_response_sha256']==sha(official_path) and row['metadata_response_sha256']==sha(table_path)
        assert row['physics_short']==candidate['physics_short'] and row['table_e_tag']==candidate['e-tag']
        for manifest_field,table_field in (('table_crossSection_pb','crossSection_pb'),('table_genFiltEff','genFiltEff'),
            ('table_kFactor','kFactor'),('table_nEvents','nEvents'),('table_signed_sumW','sumOfWeights'),('table_sumW2','sumOfWeightsSquared')):
            assert float(row[manifest_field])==float(candidate[table_field])
    official_sources={}
    source_files={'converter':'framework_Root_PhysLiteToOpenData.cxx.txt','skim':'framework_scripts_skimOpenDataNtuples.py.txt',
                  'jet':'framework_Root_JetInfo.cxx.txt','photon':'framework_Root_PhotonInfo.cxx.txt','algorithm':'framework_algorithms.txt'}
    for key,name in source_files.items():
        path=Path('.local/phase0_sources')/name
        expected=weights['official_sources'][key]['local_snapshot_sha256']
        assert sha(path)==expected,path
        official_sources[key]={'path':path.as_posix(),'sha256':expected,**weights['official_sources'][key]}
    with Path('metadata/phase5_luminosity_evidence.csv').open(newline='') as handle:lumi=list(csv.DictReader(handle))
    assert len(lumi)==13
    transfer=json.loads(Path('.local/phase5_access_20261012/access.json').read_text())
    assert transfer['status']=='BLOCKED_ACCESS' and not transfer.get('files')
    assert transfer['selected_dsids']==[302521] and transfer['expected_size']==110755804
    assert transfer['expected_checksum']=='adler32:b43248ea'
    assert transfer['charged_bytes']==transfer['payload_bytes']+len(transfer['requests'])*65536
    assert transfer['phase5_charged_bytes']==transfer['phase5_documentation_charged_bytes']+transfer['charged_bytes']<=134217728
    assert transfer['cumulative_charged_bytes']==transfer['historical_charged_bytes']+transfer['phase5_charged_bytes']<=268435456
    assert transfer['remote_root_operations']==0
    regions={}
    occupancy=[]
    expected_c9={'DATA':1689}
    for sample in ('343981','346214','423103'):
        historical=Path('outputs/phase4_numerical_v2_20261012')/sample/'reconstruction/cutflow.csv'
        with historical.open(newline='') as handle:old_rows=list(csv.DictReader(handle))
        c9_rows=[r for r in old_rows if r['selection_name']=='C9_leading_two_jet_eta']
        assert len(c9_rows)==1
        expected_c9[sample]=int(c9_rows[0]['events_after'])
    for sample,c9 in expected_c9.items():
        folder=args.region_root/sample
        summary=json.loads((folder/'summary.json').read_text())
        assert summary['status']=='PASS_BOUNDED_DERIVED_CACHE_INVENTORY'
        assert summary['sample_id']==sample and summary['start']==100
        assert summary['end_exclusive']==(63195 if sample=='DATA' else 10000)
        assert summary['unit_status']=='PROVISIONAL' and summary['region_definition']=='study-regions-v1'
        assert summary['cache_schema']==('DATA_PHASE2_28' if sample=='DATA' else 'MC_PHASE4_24')
        assert summary['generator_weight_semantics']==('NOT_APPLICABLE' if sample=='DATA' else 'UNKNOWN')
        cache=Path('outputs/phase4_numerical_v2_20261012')/('DATA93915/phase2/events.csv' if sample=='DATA' else sample+'/reconstruction/events.csv')
        assert Path(summary['input_cache']).resolve()==cache.resolve()
        assert summary['C9']==c9 and summary['entries']==(63095 if sample=='DATA' else 9900)
        assert not summary['normalization_applied'] and not summary['scale_factors_applied'] and not summary['physical_transfer_factor_applied']
        with (folder/'region_counts.csv').open(newline='') as handle:rows=list(csv.DictReader(handle))
        disjoint=[r for r in rows if r['kind']=='DISJOINT_REGION']
        assert len(disjoint)==8 and sum(int(r['raw_entries']) for r in disjoint)==summary['entries']
        regions[sample]={'summary':summary,'summary_sha256':sha(folder/'summary.json'),
                        'event_ledger_sha256':sha(folder/'event_regions.csv'),
                        'region_counts_sha256':sha(folder/'region_counts.csv'),
                        'cache_sha256':sha(Path(summary['input_cache']))}
        for row in rows:occupancy.append({'sample_id':sample,**row})
    # Gate scopes are intentionally narrower than the blocked physical study.
    specifications={
      'A':('PASS','Preserved Phase4 source/selection/results/input identity and executed numerical baseline regression'),
      'B':('PASS','Current official MC release UUID/DSID/filename and documented process identity only; exact producer/tag application remains UNKNOWN'),
      'C':('UNKNOWN','Exact FEB2025 nominal generator-weight convention'),
      'D':('UNKNOWN','Complete signed pre-skim normalization denominator and sumabs applicability'),
      'E':('UNKNOWN','Exact e4045/FEB2025 generation filter/configuration; later documented100-160/pT20 is not exact-production proof'),
      'F':('UNKNOWN','Applicable DATA run/LB/GRL/trigger/skim/bounded exposure'),
      'G':('PASS','Compatibility assessed using unchanged selection and preserved caches; unresolved physical differences explicitly identified'),
      'H':('BLOCKED','Scientifically interpretable physical weighted DATA/MC shape comparison; synthetic code only'),
      'I':('BLOCKED','Physical CR/VR model, contamination, coverage and closure; descriptive partition and synthetic TF only'),
      'J':('PASS','Fresh23/23 CTest plus3/3 Step1, compiler/ROOT linkage, metadata joins and historical/source hashes')}
    receipts={name:{'path':name,'sha256':sha(Path(name))} for name in (
      '.local/phase5_sources_20261012/access.json','.local/phase5_access_20261012/access.json',
      '.local/phase5_baseline_ctest.log','.local/phase5_step1.log','.local/phase5_validation.log')}
    source_reports={p.as_posix():sha(p,True) for directory in ('reports','metadata')
                    for p in Path(directory).glob('phase5_*') if p!=args.output}
    buffer=io.StringIO(newline='')
    writer=csv.DictWriter(buffer,fieldnames=list(occupancy[0]),lineterminator='\n');writer.writeheader();writer.writerows(occupancy)
    occupancy_bytes=buffer.getvalue().encode('utf-8')
    source_reports[occupancy_path.as_posix()]=hashlib.sha256(occupancy_bytes).hexdigest()
    result={'project':'ATLAS_HH_BBGG_PUBLIC_V1','task':'PHASE5_MC_BACKGROUND_AND_NORMALIZATION_V1',
      'checked_utc':datetime.now(timezone.utc).isoformat(),'base_commit':BASE,
      'status':'PARTIAL','verdict':'ENGINEERING_PASS_PHYSICAL_MODEL_BLOCKED',
      'gates':{key:{'state':state,'scope':scope} for key,(state,scope) in specifications.items()},
      'environment':environment,'compiler_ROOT_linkage':linkages,
      'step1_regression':{'tests':3,'passed':3,'log_sha256':sha(last)},
      'integrated_ctest':{'tests':23,'passed':23,'xml_sha256':sha(xml),
        'cases':[{'name':c.attrib['name'],'status':'PASS','seconds':c.attrib.get('time')} for c in cases]},
      'tested_source_sha256_lf':tested,'source_and_report_sha256_lf':source_reports,
      'build_artifact_sha256':{p.name:sha(p) for p in (args.build_dir/'phase5_test_source_hashes.json',args.build_dir/'phase5_linkage.json',
        args.build_dir/'step1_cmake_environment.txt',args.build_dir/'test_normalization',args.build_dir/'test_shape_comparison',
        args.build_dir/'test_control_regions',args.build_dir/'phase5_region_inventory')},
      'transfer':transfer,'access_receipts':receipts,'descriptive_regions':regions,
      'verified_preserved_official_sources':official_sources,
      'physical_normalization_applied':False,'physical_shape_comparison_executed':False,
      'physical_closure_executed':False,'real_HH_fit_executed':False,
      'physical_release_ROOT_events_read_in_Phase5':0,'physical_study_figures_generated':0,
      'synthetic_fixture_outputs':'Existing ROOT/driver regressions read synthetic ROOT fixtures and can generate temporary synthetic figures; these are not physical study outputs or approved publication artifacts',
      'figure_policy':'Unapproved PDF/PNG excluded from staging and all outgoing commits; previous local drafts retain LOCAL_DRAFT status',
      'limitations':['302521 storage access failed; schema NOT_EVALUATED','All applicable DATA luminosity scopes UNKNOWN',
        'Exact nominal-weight, signed pre-skim aggregation/completeness, BR/SF/overlap conventions UNKNOWN',
        'Continuum filter applicability/edge migration and complete background mixture unresolved',
        'Region counts are descriptive; synthetic closure is not physical closure; existing DATA is not blinded'],
      'reproduction':['source /home/btu/miniforge3/etc/profile.d/conda.sh; conda activate atlas-hh-root',
        'bash scripts/validate_step1.sh NEW_EXTERNAL_STEP1_BUILD',
        'bash scripts/validate_phase5.sh NEW_EXTERNAL_PHASE5_BUILD',
        'python -B scripts/audit_phase5_weights.py --csv outputs/NEW_weights.csv --json outputs/NEW_weights.json',
        'See reports/phase5_decision.md for cache inventory commands and failed transfer attempt history']}
    with occupancy_path.open('xb') as handle:handle.write(occupancy_bytes)
    with args.output.open('x',encoding='utf-8',newline='\n') as handle:handle.write(json.dumps(result,indent=2)+'\n')
    print('PASS executed evidence: Step1 3/3, integrated23/23, preserved baseline; physics gates remain UNKNOWN/BLOCKED')


if __name__=='__main__':main()
