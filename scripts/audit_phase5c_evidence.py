#!/usr/bin/env python3
"""Offline Phase5C artifact/accounting audit; --local adds retained receipt checks."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local',action='store_true')
    args=parser.parse_args()
    checks=[]
    def check(ok,name):
        if not ok: raise ValueError(name)
        checks.append(name)
    quality=json.loads(Path('metadata/phase5c_quality_gates.json').read_text(encoding='utf-8'))
    check(quality['baseline_commit']=='1c7da77fe4c852c929be39b10544220033de9fec','Baseline identity')
    expected={'A':'PASS','B':'PASS','C':'BLOCKED','D':'BLOCKED','E':'UNKNOWN',
              'F':'PASS','G':'PASS','H':'PASS','I':'PASS','J':'PASS'}
    check({k:v['state'] for k,v in quality['gates'].items()}==expected,'Conservative exact gate states')
    for item in quality['sealed_artifacts']:
        raw=Path(item['path']).read_bytes()
        actual=sha(raw.replace(b'\r\n',b'\n')) if item['hash_convention']=='LF_TEXT_ONLY' else sha(raw)
        check(actual==item['sha256'],'Sealed artifact: '+item['path'])
        check(Path(item['path']).suffix.lower() not in {'.png','.pdf','.root'},'Text/source only: '+item['path'])
    baseline=json.loads(Path('metadata/phase5c_baseline_manifest.json').read_text())
    check(baseline['base_commit']==quality['baseline_commit'] and len(baseline['tracked'])==190 and len(baseline['immutable_local'])==407,'190 tracked +407 local preservation inventory')
    network=json.loads(Path('metadata/phase5c_sanitized_network_evidence.json').read_text())
    original=network['original_access_receipt'];receipts=network['new_and_prior_metadata_receipts']
    check(len(receipts)==5 and len({x['raw_sha256'] for x in receipts})==5,'Five distinct post-Phase5 metadata receipts')
    check(original['phase5_charged_bytes']==original['documentation_charge_bytes']+original['request_count']*65536+original['response_body_bytes'],'Original Phase5 arithmetic')
    check(original['cumulative_charged_bytes']==original['historical_charged_bytes']+original['phase5_charged_bytes'],'Original cumulative arithmetic')
    delta=0
    allowed_keys={'kind','status','reserve_bytes','body_cap_bytes','received_body_bytes','target',
                  'http_status','port','family','tls_version','tls_verification','error'}
    for receipt in receipts:
        own=0
        for op in receipt['operations']:
            check(set(op)<=allowed_keys,'Sanitized operation keys')
            check(type(op['reserve_bytes']) is int and op['reserve_bytes']==65536 and
                  type(op['received_body_bytes']) is int and 0<=op['received_body_bytes']<=op['body_cap_bytes']+1,'Operation reserve/body accounting')
            check('?' not in op['target'] and '#' not in op['target'] and '@' not in op['target'],'No query/fragment/credentials in target')
            if 'error' in op: check(bool(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*(?: \(errno -?[0-9]+\))?|HTTP_[0-9]+',op['error'])),'Error class only')
            own+=op['reserve_bytes']+op['received_body_bytes']
        check(own==receipt['incremental_charged_bytes'],'Receipt incremental arithmetic')
        delta+=own
    account=network['accounting']
    check(account['phase5_charged_bytes']==original['phase5_charged_bytes']+delta==5695475,'Phase5 total including Phase5C')
    check(account['cumulative_charged_bytes']==original['cumulative_charged_bytes']+delta==83829497,'Cumulative total including Phase5C')
    check(account['phase5_limit_bytes']==134217728 and account['cumulative_limit_bytes']==268435456,'Unchanged budgets')
    check(account['phase5_charged_bytes']<account['phase5_limit_bytes'] and account['cumulative_charged_bytes']<account['cumulative_limit_bytes'],'Accounting within ceilings')
    check(account['phase5c_incremental_charged_bytes']==393216 and account['phase5c_received_body_bytes']==0,'Six failed documentation charges retained')
    check(network['object']['ROOT_payload_bytes']==0 and network['object']['local_checksum']=='NOT_VERIFIED' and network['object']['native_schema']=='NOT_EVALUATED','No acquired-MC claim')
    check(network['support_delivery']=='UNSENT_DRAFT','Support remains unsent')
    sidebands=quality['sidebands']
    check((sidebands['entries'],sidebands['C9'],sidebands['sideband_entries'],sidebands['A'],sidebands['B'])==(63095,1689,1374,443,931),'Preserved DATA counts')
    check(sidebands['fold0']==724 and sidebands['fold1']==650 and sidebands['fold_identity_intersection']==0,'Disjoint deterministic folds')
    check(sidebands['historical_DATA_already_viewed'] and not sidebands['blinded_analysis'] and not sidebands['untouched_validation'],'Retrospective evidence classification')
    protocol=json.loads(Path('metadata/phase5c_sideband_protocol.json').read_text())
    check(sha(Path('metadata/phase5c_sideband_protocol.json').read_bytes())=='e9916da8772902c5464ea141397340a5230cb1733bb05e7c86800d9681295f66','Pre-read frozen protocol')
    check(protocol['central_excluded_from_all_diagnostics']=='[120,130)' and protocol['unit_status']=='PROVISIONAL','Central exclusion and unchanged units')
    with Path('metadata/phase5c_sideband_audit.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    check(len(rows)==1962 and all(r['scope']=='RETROSPECTIVE_DATA_ONLY_DESCRIPTIVE' for r in rows),'1962 descriptive audit rows')
    check(all(r['population']!='FIXED_OUTER_TRIM' for r in rows),'Trim endpoints explicit')
    occupancy=[r for r in rows if r['diagnostic']=='occupancy' and r['population']=='POOLED_SIDEBANDS' and float(r['split_abs_delta_eta'])==1]
    check({r['partition']:int(r['n']) for r in occupancy}=={'A':443,'B':931},'Audit baseline A/B counts')
    check(not quality['physics']['physical_closure_executed'] and not quality['physics']['physical_transfer_factor_applied']
          and not quality['physics']['background_prediction_performed'] and not quality['physics']['normalization_applied'], 'No unsupported physical model')
    regression=quality['regression']
    check((regression['ctest_total'],regression['ctest_passed'],regression['ctest_failed'],regression['ctest_skipped'])==(28,28,0,0),'Executed regression result')
    check(regression['environment']['ROOT_VERSION']=='6.40.04' and regression['environment']['PROJECT_CXX_STANDARD']=='20' and regression['compiled_translation_units']==38,'ROOT/C++20 compile identity')
    if args.local:
        for item in [original]+receipts:
            check(sha(Path(item['receipt']).read_bytes())==item['raw_sha256'],'Immutable raw receipt: '+item['receipt'])
        for item in baseline['immutable_local']:
            p=Path(item['path']);check(p.stat().st_size==item['bytes'] and sha(p.read_bytes())==item['sha256'],'Historical local: '+item['path'])
        for item in baseline['tracked']:
            raw=Path(item['path']).read_bytes()
            if item['hash_convention']=='LF_TEXT_ONLY':raw=raw.replace(b'\r\n',b'\n')
            if item['check']=='unchanged_prefix':raw=raw[:16148]
            check(sha(raw)==item.get('sha256_lf',item.get('sha256')),'Historical tracked: '+item['path'])
        for item in quality['local_artifacts']:
            p=Path(item['path']);check(p.stat().st_size==item['bytes'] and sha(p.read_bytes())==item['sha256'],'Actual evidence: '+item['path'])
        suite=ET.parse(regression['ctest_xml']).getroot()
        cases=list(suite.iter('testcase'))
        check(len(cases)==28 and all(c.get('status')=='run' and c.find('failure') is None and c.find('skipped') is None for c in cases),'Actual final CTest XML without failure/skip')
        for name in ('root_io','rdataframe','roofit_roostats','phase5c_sideband_contract','phase5c_documentation_contract'):
            check(any(c.get('name')==name for c in cases),'Required executed test: '+name)
        for directory in (Path('.local'),Path('outputs')):
            check(not any(directory.rglob('*302521*.root*')),'No final/partial 302521 ROOT in '+str(directory))
    print(json.dumps({'status':'PASS_OFFLINE_EVIDENCE_AUDIT','checks':len(checks),'local':args.local,
                      'physical_input_status':'BLOCKED','physical_normalization':'DISABLED'}))


if __name__=='__main__': main()
