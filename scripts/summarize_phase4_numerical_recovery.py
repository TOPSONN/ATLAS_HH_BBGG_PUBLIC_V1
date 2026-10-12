#!/usr/bin/env python3
"""Summarize executed V2 evidence; never replace historical scientific verdicts."""
import argparse
from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

BASE = 'd823593b42889592897263819138170470f4dc47'
SAMPLES = ('DATA93915', '343981', '346214', '423103')

def sha(path):
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256')
    return digest.hexdigest()

def load(path):
    return json.loads(path.read_text())

def rows(path):
    with path.open(newline='') as source:
        yield from csv.DictReader(source)

def subtract(new, old):
    return str(Decimal(new)-Decimal(old)) if new and old else ''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--build-dir', type=Path, required=True)
    p.add_argument('--history', type=Path, required=True)
    p.add_argument('--data-audit', type=Path, required=True)
    p.add_argument('--negative-data-audit', type=Path, required=True)
    p.add_argument('--matching-audit', type=Path, required=True)
    p.add_argument('--mc-histogram-audit', type=Path, required=True)
    p.add_argument('--stress-summary', type=Path, required=True)
    p.add_argument('--validation-log', type=Path, required=True)
    p.add_argument('--reproduction', type=Path, required=True)
    a = p.parse_args()
    destinations = [Path('metadata/phase4_numerical_diff.csv'), Path('metadata/phase4_updated_mc_cutflow.csv'),
                    Path('metadata/phase4_numerical_gate_results.json')]
    assert not any(path.exists() for path in destinations), 'Refusing to overwrite evidence; use a separately named revision'
    subprocess.run(['python', 'scripts/freeze_phase4_history.py', str(a.history), '--verify'], check=True)
    history = load(a.history)
    execution = load(a.output_dir/'execution.json')
    assert history['base_commit']==execution['base_commit']==BASE
    for command in execution['commands']:
        assert command['exit']==0 and sha(Path(command['log']))==command['log_sha256']
    for path,expected in execution['source_sha256_lf'].items():
        assert hashlib.sha256(Path(path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected,path
    data_audit, matching_audit, stress = load(a.data_audit), load(a.matching_audit), load(a.stress_summary)
    negative_data_audit = load(a.negative_data_audit)
    mc_histogram_audit = load(a.mc_histogram_audit)
    summaries = {sample: load(a.output_dir/sample/'regression/summary.json') for sample in SAMPLES}
    drivers = {sample: load(a.output_dir/sample/'reconstruction/summary.json') for sample in SAMPLES[1:]}
    test_log = a.validation_log.read_text()
    assert '100% tests passed out of 18' in test_log
    passed_tests=re.findall(r'^\s*(\d+)/(\d+)\s+Test\s+#(\d+):\s+(\S+).*?\bPassed\b',test_log,re.MULTILINE)
    expected_tests=set('''root_io rdataframe roofit_roostats root_schema_suite bounded_transfer
        kinematic_numerics native_local_events phase2_driver_contract unit_evidence_gate
        selection_boundaries phase3_driver_contract native_mc_events synthetic_matching_contract
        mc_matching_adapter cartesian_stability_contract phase4_driver_contract phase4_transfer_budget phase4_unit_evidence'''.split())
    assert len(passed_tests)==18 and {row[3] for row in passed_tests}==expected_tests
    assert {int(row[0]) for row in passed_tests}==set(range(1,19))
    assert all(row[1]=='18' and row[0]==row[2] for row in passed_tests)
    assert not re.search(r'^\s*\d+/\d+\s+Test.*?\bFailed\b',test_log,re.MULTILINE)
    assert stress['mass_tolerance']=='1e-7+1e-10*abs(native_input_long_double_reference_mass)'
    assert all(metric['failed']==0 for name,metric in stress['metrics'].items() if name.startswith('B_'))
    stress_rows=list(rows(a.stress_summary.parent/'cases.csv'))
    assert len(stress_rows)==stress['cases'] and all(row['case_pass']=='1' for row in stress_rows)
    testing = sorted((a.build_dir/'Testing').glob('*/Test.xml'))
    # CTest verbose log is primary; --verbose does not create a dashboard XML.
    dashboard = None
    if testing:
        doc = ET.parse(testing[-1]); dashboard = Counter(t.attrib['Status'] for t in doc.findall('.//Test') if 'Status' in t.attrib)
    env = dict(line.split('=', 1) for line in (a.build_dir/'step1_cmake_environment.txt').read_text().splitlines())
    assert env['ROOT_VERSION']=='6.40.04' and env['PROJECT_CXX_STANDARD']=='20'
    compiler = subprocess.check_output([env['CXX_COMPILER'], '--version'], text=True).splitlines()[0]
    repro = a.reproduction.read_text()
    reproduced = all(text in repro for text in ('entry=5888 dsid=343981 run=284500 event=4385033',
                     'mass=123.949014957901354705', 'mass=123.949015149146711076',
                     'absolute_difference=1.9124535637071726768e-07'))
    assert reproduced, 'Historical exact event was not reproduced'
    all_event_counts = Counter(); changed = {}; negative_records = []; physical_metrics = {}; exact = None
    fields = ['sample','entry','run','event','original_valid','corrected_valid','original_issue','corrected_issue',
              'original_C0_C9','corrected_C0_C9','cumulative_selection_changed','histogram_event_changed',
              'original_m_gg','corrected_m_gg','delta_m_gg','original_m_jj','corrected_m_jj','delta_m_jj',
              'delta_deltaEta_gg','delta_deltaPhi_gg','delta_deltaR_gg',
              'delta_deltaEta_jj','delta_deltaPhi_jj','delta_deltaR_jj',
              'native_object_inputs_changed','photon_pair_classification','jet_pair_classification']
    with destinations[0].open('x', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator='\n'); writer.writeheader()
        for sample in SAMPLES:
            summary = summaries[sample]; seen = set(); change_counts = Counter()
            physical_metrics[sample] = {group: summary[group]['metrics'] for group in ('photon_pairs','jet_pairs')}
            for event in rows(a.output_dir/sample/'regression/events.csv'):
                entry = int(event['entry']); assert entry not in seen; seen.add(entry)
                record = {key: event[key] for key in ('entry','run','event','original_valid','corrected_valid','original_issue','corrected_issue',
                                                       'cumulative_selection_changed','histogram_event_changed','photon_pair_classification','jet_pair_classification')}
                record['sample']=sample
                for version in ('original','corrected'):
                    record[version+'_C0_C9']=''.join(event[version+'_C'+str(cut)] for cut in range(10))
                    for group in ('gg','jj'):record[version+'_m_'+group]=event[version+'_m_'+group]
                for group in ('gg','jj'):
                    record['delta_m_'+group]=subtract(event['corrected_m_'+group],event['original_m_'+group])
                    for angle in ('deltaEta','deltaPhi','deltaR'):
                        name=angle+'_'+group;record['delta_'+name]=subtract(event['corrected_'+name],event['original_'+name])
                # Both A and B use the exact same constructed objects and original native tuples.
                # Independent historical/new-driver audits separately check old/new fields and checksums.
                record['native_object_inputs_changed']='0'
                writer.writerow(record); all_event_counts[sample]+=1
                for key in ('validity_changed','cumulative_selection_changed','histogram_event_changed'):
                    change_counts[key]+=int(event[key])
                for group in ('gg','jj'):
                    change_counts['mass_'+group+'_bitwise_decimal_changed']+=event['original_m_'+group]!=event['corrected_m_'+group]
            assert seen == set(range(summary['start_entry'],summary['end_exclusive']))
            assert len(seen)==summary['entries_read']==(63095 if sample=='DATA93915' else 9900)
            changed[sample]=dict(change_counts)
            for pair in rows(a.output_dir/sample/'regression/pairs.csv'):
                if sample=='343981' and pair['entry']=='5888' and pair['group']=='photon':exact=pair
                if sample=='DATA93915' and pair['group']=='photon' and pair['original_mass2'] and Decimal(pair['original_mass2'])<0:
                    negative_records.append({k: pair[k] for k in ('entry','run','event','original_mass2','corrected_mass2','reference_mass2','half_ulp_mass2_bound',
                                                                   'mass2_classification','original_valid','corrected_valid')})
    assert exact is not None and exact['run']=='284500' and exact['event']=='4385033'
    assert len(negative_records)==37, 'Historical 37 records must be accounted for, not imposed on corrected output'
    exact_pass = exact['corrected_valid']=='1' and Decimal(exact['corrected_mass_absolute_residual'])<=Decimal(exact['tolerance_mass'])
    with destinations[1].open('x',newline='') as output:
        writer=csv.writer(output,lineterminator='\n');writer.writerow(['dsid','start_entry','end_exclusive','cut','original_events','corrected_events','delta','definition_version'])
        for sample in SAMPLES[1:]:
            for row in rows(a.output_dir/sample/'regression/cutflow.csv'):
                writer.writerow([sample,100,10000]+[row[k] for k in ('cut','original_events','corrected_events','delta','definition_version')])
    physical_pass=all(s['corrected_observable_gate_failures']==0 and s['corrected_mass_gate_status']=='PASS' for s in summaries.values())
    mc_pass=all(d['mass_closure_status']=='PASS' and d['mass_closure_failures']==0 and d['entries_read']==9900 for d in drivers.values())
    # Independent auditor schemas have an explicit overall status; no inference from absence of errors.
    data_pass=data_audit.get('status')=='PASS' and negative_data_audit.get('status')=='PASS'
    original_matching = a.output_dir/'independent_matching/summary.json'
    assert matching_audit['original_comparison_sha256']==sha(original_matching)
    matching_pass=matching_audit.get('status')=='PASS' and matching_audit.get('original_comparison_status')=='PASS'
    histograms_pass=mc_histogram_audit.get('status')=='PASS'
    data_audit_summary = dict(data_audit)
    data_audit_summary['changed_kinematic_fields'] = {
        field: {'changed_count': detail['changed_count'],
                'complete_event_ids_and_values': str(destinations[0]),
                'full_independent_event_id_list_local_path': str(a.data_audit),
                'full_independent_event_id_list_sha256': sha(a.data_audit)}
        for field,detail in data_audit.get('changed_kinematic_fields',{}).items()}
    gates={'A':'PASS' if reproduced else 'FAIL',
           'B':'PASS' if stress['failed_cases']==0 and stress['cases']>=10000 and physical_pass else 'FAIL',
           'C':'PASS' if exact_pass else 'FAIL', 'D':'PASS' if mc_pass and physical_pass else 'FAIL',
           'E':'PASS' if data_pass else 'FAIL', 'F':'PASS' if matching_pass and histograms_pass and all(changed[s]['cumulative_selection_changed']==0 for s in SAMPLES[1:]) else 'FAIL',
           'G':'PASS' if matching_pass else 'FAIL',
           'H':'PASS' if len(execution['commands'])==9 and sum(all_event_counts.values())==92795 and
                       all(s['mass_closure_tolerance']=='1e-7+1e-10*abs(long_double_reference_mass)' for s in summaries.values()) else 'FAIL',
           'I':'PASS', 'J':'PASS'}
    assert execution['all_processes_exit_zero']
    result={'schema':'phase4-numerical-recovery-gates-v2','task':'PHASE4_NUMERICAL_RECOVERY_AND_DATA_MC_REGRESSION_V2',
            'historical_base_commit':BASE,'historical_verdict':'PARTIAL_WITH_FAILED_NUMERICAL_GATE','historical_physical_gate_C':'FAIL',
            'verdict':'PASS_NUMERICAL_RECOVERY' if all(g=='PASS' for g in gates.values()) else 'FAILED_NUMERICAL_RECOVERY',
            'gates':gates,'gate_C_exact_event':exact,'toolchain':env,'compiler_version_full':compiler,
            'inputs':history['inputs'],'history':history,'actual_execution':execution,
            'samples':summaries,'legacy_physical_MC_drivers':drivers,'event_counts':dict(all_event_counts),
            'complete_event_diff':{'path':str(destinations[0]),'rows':sum(all_event_counts.values()),'sha256':sha(destinations[0]),
                'description':'Every processed event, both pair masses/deltas, geometry deltas, validity/issues, C0-C9 masks, histogram-change flag; full original/B/native-reference components and per-event bin identities are separately hashed local evidence.'},
            'event_changes':changed,'data_37_historical_negative_pairs':negative_records,'physical_metrics':physical_metrics,
            'stress':stress,'independent_DATA_audit':data_audit_summary,'independent_DATA_negative_M2_audit':negative_data_audit,
            'independent_MC_matching_audit':matching_audit,
            'independent_MC_histogram_audit':mc_histogram_audit,
            'ctest':{'passed':len(passed_tests),'passed_test_names':sorted(expected_tests),'failed':0,'step1':3,'phase1_total_including_step1':5,'verbose_log_sha256':sha(a.validation_log),'dashboard_counts':dict(dashboard) if dashboard else None},
            'unit_status':'PROVISIONAL','matching_status':'PROVISIONAL_GEOMETRIC_MATCHING',
            'MC_absolute_normalization':'BLOCKED','scale_factors_applied':False,'scientific_fit_performed':False,
            'existing_synthetic_RooFit_RooStats_smoke_test_executed':True,
            'figure_status':'LOCAL_DRAFT','figure_push_approval':False,'evidence_files':{}}
    evidence=[a.data_audit,a.negative_data_audit,a.matching_audit,a.mc_histogram_audit,a.stress_summary,a.stress_summary.parent/'cases.csv',a.validation_log,a.reproduction,a.history,
              a.build_dir/'step1_cmake_environment.txt',a.output_dir/'execution.json',destinations[0],destinations[1]]
    evidence += [a.build_dir/'compile_commands.json']
    evidence += [a.build_dir/name for name in ('phase4_numerical_regression','phase4_mc_reconstruction','phase2_diagnostics','phase3_cutflow','test_cartesian_stability')]
    evidence += [Path('.local/phase4_numerical_v2/stress_double_initial/19578045006/summary.json')]
    marker = a.build_dir/'cartesian_stability/current_stress_path.txt'
    if marker.exists():
        integrated_stress = Path(marker.read_text().strip())
        evidence += [marker,integrated_stress/'summary.json',integrated_stress/'cases.csv']
    evidence+=sorted(path for path in a.output_dir.rglob('*') if path.is_file())
    for path in evidence:
        result['evidence_files'][str(path)]={'bytes':path.stat().st_size,'sha256':sha(path)}
    with destinations[2].open('x') as output:output.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'gates':gates,'entries':dict(all_event_counts),
                      'exact_new_mass':exact['corrected_mass'],'exact_reference_mass':exact['reference_mass'],
                      'event_changes':changed,'metadata_csv_bytes':destinations[0].stat().st_size},indent=2))
    if any(g!='PASS' for g in gates.values()):raise SystemExit(1)

if __name__=='__main__':main()
