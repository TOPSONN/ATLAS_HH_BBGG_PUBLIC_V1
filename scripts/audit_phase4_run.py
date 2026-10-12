#!/usr/bin/env python3
"""Audit cached MC outputs without rereading events; retain failed physics gates."""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess


def digest(path, text=False):
    raw=path.read_bytes()
    return hashlib.sha256(raw.replace(b'\r\n',b'\n') if text else raw).hexdigest()


def read_csv(path):
    with path.open() as f: return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def write_json(path, data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def selection(row, c):
    number=lambda name:float(row[name]) if row[name] else math.nan
    p,j=int(row['photon_n']),int(row['jet_n'])
    pp=[number('photon1_pt'),number('photon2_pt')]; pe=[number('photon1_eta'),number('photon2_eta')]
    jp=[number('jet1_pt'),number('jet2_pt')]; je=[number('jet1_eta'),number('jet2_eta')]
    mgg,mjj=number('m_gg'),number('m_jj')
    valid=row['valid']=='1'
    for n,pts,etas,mass in [(p,pp,pe,mgg),(j,jp,je,mjj)]:
        valid=valid and n>=0 and all(math.isfinite(pts[i]) and pts[i]>=0 and math.isfinite(etas[i]) for i in range(min(n,2)))
        if n>=2: valid=valid and math.isfinite(mass) and mass>=0
    accept=lambda eta: abs(eta)<c['photon_abs_eta_max'] and not(c['photon_crack_low']<abs(eta)<c['photon_crack_high'])
    stages=[True,valid,p>=2,pp[0]>c['photon_leading_pt_min_gev'],pp[1]>c['photon_subleading_pt_min_gev'],
            all(accept(eta) for eta in pe),c['diphoton_mass_low_gev']<=mgg<=c['diphoton_mass_high_gev'],j>=2,
            all(pt>c['jet_pt_min_gev'] for pt in jp),all(abs(eta)<c['jet_abs_eta_max'] for eta in je)]
    for i in range(1,len(stages)):stages[i]=stages[i] and stages[i-1]
    return stages


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--access-dir',required=True,type=Path)
    parser.add_argument('--run-dir',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--regression-log',required=True,type=Path)
    parser.add_argument('--physical-log',required=True,type=Path)
    parser.add_argument('--remaining-log',required=True,type=Path)
    parser.add_argument('--execution-source-manifest',required=True,type=Path,
                        help='Preserved manifest hashing source used for physical execution')
    args=parser.parse_args(); root=Path.cwd(); out=args.output_dir;out.mkdir(exist_ok=False)
    ledger=json.loads((args.access_dir/'access.json').read_text())
    assert ledger['charged_bytes']<=128*1024*1024 and ledger['cumulative_charged_bytes']<=256*1024*1024
    assert ledger['cumulative_charged_bytes']==ledger['historical_charged_bytes']+ledger['charged_bytes']
    regression=args.regression_log.read_text(encoding='utf-8-sig')
    assert '100% tests passed out of 17' in regression
    first_log=args.physical_log.read_text(encoding='utf-8-sig')
    remaining_log=args.remaining_log.read_text(encoding='utf-8-sig')
    assert 'returned non-zero exit status 1' in first_log and '343981' in first_log
    assert 'Independent Cartesian MC pair-mass closure failed' in first_log
    actual_exits={343981:1}
    for dsid in (346214,423103):
        found=re.findall(r'ACTUAL_EXIT\s+'+str(dsid)+r'\s+(\d+)',remaining_log)
        assert len(found)==1
        actual_exits[dsid]=int(found[0]);assert actual_exits[dsid]==0
    execution_source=json.loads(args.execution_source_manifest.read_text())['source_sha256_lf']
    config={}
    for line in (root/'metadata/phase3_selection_config.ini').read_text().splitlines():
        if line and not line.startswith('#'):
            key,value=line.split('=',1)
            if key!='definition_version':config[key]=float(value)
    sample_metadata={int(r['dsid']):r for r in read_csv(root/'metadata/phase4_mc_sample_manifest.csv')}
    data_types={r['actual_branch']:r['root_type'] for r in read_csv(root/'metadata/root_schema_manifest.csv') if r['present']=='yes'}
    branches=[];cutflows=[];matches=[];run_summaries=[];weights={};unit_evidence={};checksums=[];keys=set();compatibility={}
    required=['runNumber','eventNumber','photon_n','jet_n','jet_btag_quantile']+[kind+'_'+field for kind in ('photon','jet') for field in ('pt','eta','phi','e')]
    for sample in ledger['files']:
        dsid=sample['dsid'];directory=args.run_dir/str(dsid); run=directory/'reconstruction'
        summary=json.loads((run/'summary.json').read_text()); assert summary['dsid']==dsid
        assert summary['entries_read']==9900 and summary['start_entry']==100 and summary['end_exclusive']==10000
        assert not summary['normalization_applied'] and not summary['scale_factors_applied'] and not summary['truth_energy_inferred']
        events=read_csv(run/'events.csv');assert [int(r['entry']) for r in events]==list(range(100,10000))
        counts=[0]*10;failing=[]
        for row in events:
            key=(int(row['dsid']),int(row['run']),int(row['event']))
            assert key[0]==dsid and key not in keys;keys.add(key)
            stages=selection(row,config)
            assert stages[-1]==(row['C9_selected']=='1')
            counts=[a+b for a,b in zip(counts,stages)]
            if row['cartesian_mass_closure_pass']=='0':failing.append({k:row[k] for k in ('dsid','entry','run','event','m_gg','m_jj','C9_selected')})
        flow=read_csv(run/'cutflow.csv');assert [int(r['events_after']) for r in flow]==counts
        assert len(failing)==summary['mass_closure_failures']
        # Preserve every recorded failure; auditing consistency is not a waiver.
        summary['cached_cutflow_audit']='PASS';summary['failing_event_rows']=failing
        summary['expected_driver_exit_from_closure']=0 if summary['mass_closure_status']=='PASS' else 1
        summary['actual_driver_exit_recorded']=actual_exits[dsid]
        assert summary['actual_driver_exit_recorded']==summary['expected_driver_exit_from_closure']
        run_summaries.append(summary);cutflows.extend(flow)
        match=read_csv(run/'matching_threshold_summary.csv');assert len(match)==12
        for row in match:
            matched=int(row['matched_pairs']);nr=int(row['eligible_reco']);nt=int(row['eligible_truth'])
            assert matched+int(row['unmatched_reco'])==nr and matched+int(row['unmatched_truth'])==nt
            assert int(row['events'])==(counts[1] if row['scope']=='ALL_VALID' else counts[-1])
            for denominator,column in [(nr,'geometric_reco_match_fraction'),(nt,'geometric_truth_match_fraction')]:
                assert math.isclose(float(row[column]),matched/denominator,rel_tol=1e-12) if denominator else row[column]==''
        matches.extend(match)
        fields={}
        with (run/'normalization_sf_diagnostics.csv').open() as f:
            for row in csv.DictReader(f):
                assert row['usage']=='NOT_APPLIED'
                value=float(row['value']); name=row['branch']
                stats=fields.setdefault(name,{'type':row['native_type'],'count':0,'finite':0,'negative':0,'minimum':None,'maximum':None})
                stats['count']+=1
                if math.isfinite(value):
                    stats['finite']+=1;stats['negative']+=value<0
                    stats['minimum']=value if stats['minimum'] is None else min(stats['minimum'],value)
                    stats['maximum']=value if stats['maximum'] is None else max(stats['maximum'],value)
        diagnostic=json.loads((run/'weight_diagnostics.json').read_text())
        assert diagnostic['positive']+diagnostic['negative']+diagnostic['zero']==9900
        assert math.isclose(math.fsum(float(r['mc_weight']) for r in events),diagnostic['sumw'],rel_tol=1e-12)
        weights[str(dsid)]={'generator_diagnostic':diagnostic,'native_scalar_ranges':fields,
            'later_v1_metadata':{k:sample_metadata[dsid][k] for k in ('crossSection_pb','genFiltEff','kFactor','nEvents','sumOfWeights','sumOfWeightsSquared','e_tag')},
            'normalization':'BLOCKED','generator_convention':'UNKNOWN_EXACT_RELEASE','usage':'NO_EVENT_WEIGHT_SF_OR_LUMINOSITY_APPLIED'}
        rows=read_csv(directory/'branches.csv')
        types={r['actual_branch']:r['root_type'] for r in rows if r['present']=='yes'}
        assert len(types)==118
        for row in rows:branches.append({'dsid':dsid,**row})
        compatibility[str(dsid)]={'native_required_types':{name:{'data':data_types.get(name),'mc':types.get(name),'matches':data_types.get(name)==types.get(name)} for name in required},
            'schema_type_assessment':'PASS' if all(data_types.get(n)==types.get(n) for n in required) else 'FAIL',
            'physical_unit_and_calibration_equivalence':'UNKNOWN_PROVISIONAL','data_period_luminosity':'UNKNOWN',
            'rate_comparison':'BLOCKED','distribution_comparison':'NOT_EXECUTED'}
        unit_evidence[str(dsid)]={'reco':json.loads((directory/'reco_units_v2.json').read_text()),'physical_first100':json.loads((directory/'physical_probe.json').read_text())}
        for path in sorted(directory.rglob('*')):
            if path.is_file():checksums.append({'path':str(path),'bytes':path.stat().st_size,'sha256':digest(path),'kind':'LOCAL_DIAGNOSTIC_NOT_FIGURE_APPROVAL'})
        input_path=args.access_dir/sample['filename']
        assert input_path.stat().st_size==sample['size']
        assert digest(input_path)==sample['sha256']
        checksums.append({'path':str(input_path),'bytes':sample['size'],'sha256':sample['sha256'],'kind':'OFFICIAL_ADLER32_CHECKED_MC_INPUT'})
    assert len(keys)==29700
    preserved=[]
    base='830af3031da80c1c5f3c01ccec22e3619e95f41f'
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'metadata','note','reports'],text=True).splitlines()
    for name in names:
        original=subprocess.check_output(['git','show',base+':'+name])
        assert digest(root/name,True)==hashlib.sha256(original.replace(b'\r\n',b'\n')).hexdigest(),name
        preserved.append(name)
    gates={
        'A':{'status':'PASS','scope':'published sample identity/checksums and processed-entry DSIDs'},
        'B':{'status':'UNKNOWN','schema':'PASS','numerical_unit_consistency':'PASS','units':'PROVISIONAL','exact_producer_calibration':'UNKNOWN'},
        'C':{'status':'FAIL','scope':'fixed-tolerance physical pair-mass closure','by_dsid':{str(s['dsid']):s['mass_closure_status'] for s in run_summaries}},
        'D':{'status':'PASS','scope':'independent cached raw cutflow reproduction; does not waive C'},
        'E':{'status':'BLOCKED','scope':'exact generator convention/generated sums/filter/SFs/BR/completeness unresolved'},
        'F':{'status':'UNKNOWN','geometric_algorithm_and_same_event_association':'PASS_PROVISIONAL','official_truth_origin_and_flavour':'BLOCKED'},
        'G':{'status':'BLOCKED','scope':'exact quantile tagger/WP/calibration/flavour unavailable'},
        'H':{'status':'UNKNOWN','native_common_types':'PASS','unit_calibration_equivalence':'UNKNOWN','coverage_and_normalized_comparison':'BLOCKED'},
        'I':{'status':'PASS','scope':'no HH fit/significance/rate/limit/coupling or unsupported official efficiency claims'},
        'J':{'status':'PASS','ctest':'17/17','historical_artifact_files_preserved':len(preserved)}}
    manifest={'project':'ATLAS_HH_BBGG_PUBLIC_V1','task':'PHASE4_MC_RECONSTRUCTION_AND_TRUTH_VALIDATION_V1',
        'status':'PARTIAL_WITH_FAILED_NUMERICAL_GATE','base_commit':base,'record':93922,'selected_dsids':[f['dsid'] for f in ledger['files']],
        'reconstructed_entries':29700,'distinct_file_entries_inspected':30000,'main_ranges':[[100,10000]],
        'prefix_stages':[[0,10],[10,100]],'truth_prefix_same_entry_revisits':'first100 for separate truth/normalization probes; not added to raw cutflow',
        'extra_numeric_diagnostic_repeat_reads':[{'dsid':343981,'entry':5888,'count':1}],
        'duplicate_check_scope':'processed entry ranges across all3 files; first100 separately; not full releases or cross-prefix event-ID scan',
        'transport_charged_bytes':ledger['charged_bytes'],'cumulative_charged_bytes':ledger['cumulative_charged_bytes'],
        'transport_accounting':'application-consumed HTTP bodies plus64KiB per attempted request; not measured wire bytes',
        'root_version':'6.40.04','cpp_standard':20,'compiler':'GNU15.3.0 conda x86_64-conda-linux-gnu-c++','cmake_version':'4.4.4',
        'regression':'17/17 PASS','regression_log':str(args.regression_log),'regression_log_sha256':digest(args.regression_log),
        'process_exit_evidence':'actual process exits are recorded separately in the reconstruction report; expected_driver_exit_from_closure is an inference, not an execution record',
        'physical_process_logs':{str(p):digest(p) for p in (args.physical_log,args.remaining_log)},
        'physical_execution_source_sha256_lf':execution_source,
        'physical_execution_note':'original physical outputs preserved; final reader adds an exact-TTree safety guard, satisfying the already measured TTree classes without event rereads',
        'sample_runs':run_summaries,'data_mc_compatibility':compatibility,'historical_preserved_paths':preserved,
        'phase4_pdf_png_generated':0,'source_sha256_lf':{str(p.relative_to(root)):digest(p,True) for p in sorted(list((root/'include').glob('*.h'))+list((root/'src').glob('*.cxx'))+[root/'apps/phase4_mc_reconstruction.cxx',root/'CMakeLists.txt'])}}
    write_json(out/'phase4_run_manifest.json',manifest);write_json(out/'phase4_quality_gates.json',gates)
    write_json(out/'phase4_weight_normalization_evidence.json',weights);write_json(out/'phase4_unit_evidence.json',unit_evidence)
    write_json(out/'phase4_transfer_ledger.json',ledger)
    write_csv(out/'phase4_branch_inventory.csv',branches);write_csv(out/'phase4_cutflow.csv',cutflows)
    write_csv(out/'phase4_matching_validation.csv',matches);write_csv(out/'phase4_checksum_manifest.csv',checksums)
    print('PASS_REPORT_CONSISTENCY; SCIENTIFIC_GATE_C=FAIL; STATUS=PARTIAL_WITH_FAILED_NUMERICAL_GATE')


if __name__=='__main__': main()
