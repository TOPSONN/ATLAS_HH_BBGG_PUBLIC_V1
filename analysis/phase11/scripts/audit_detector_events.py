#!/usr/bin/env python3
"""Offline source + frozen existing-record readback; never imports ROOT/generators."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from detector_events import demand, diagnose_events, joined_records, read_jsonl, sha, static_detector_trace, write_csv, write_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--phase9',type=Path,required=True)
    p.add_argument('--phase8-manifest',type=Path,required=True)
    p.add_argument('--delphes-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    demand(not a.output.exists(),'FRESH_OUTPUT_DIRECTORY_REQUIRED')
    origins=a.phase9/'origins_03/phase9_origins_event_details.jsonl'
    native=a.phase9/'native/phase9_native_events.jsonl'
    regions=a.repo/'analysis/phase8/config/regions_v1.json'
    selection=a.repo/'analysis/phase8/config/selection_v1.json'
    inactive=a.repo/'analysis/phase11/config/inactive_detector_diff.txt'
    inputs=[origins,native,regions,selection,inactive,a.phase8_manifest]
    before={str(f):sha(f) for f in inputs}
    demand(all(not line.strip() or line.lstrip().startswith('#') for line in inactive.read_text().splitlines()),'INACTIVE_DIFF_MUST_BE_ALL_COMMENTED')
    manifest=json.loads(a.phase8_manifest.read_text())
    cards=[]
    for ds in manifest['datasets']:
        if ds['dataset_id'] in ('B01','B02','B03'):
            path=Path(ds['card_path']);demand(sha(path)==ds['card_sha256'],'FROZEN_RUNTIME_CARD_HASH')
            trace=static_detector_trace(path,a.delphes_source)
            cards.append({'dataset_id':ds['dataset_id'],'card_path':str(path),'card_sha256':sha(path),'trace':trace})
            inputs.append(path);before[str(path)]=sha(path)
    demand(len(cards)==3,'THREE_FROZEN_RUNTIME_CARDS_REQUIRED')
    for card in cards:
        for identity in card['trace']['source_identities'].values():
            path=Path(identity['path']);inputs.append(path);before[str(path)]=identity['sha256']
    origin_rows=list(read_jsonl(origins));native_rows=list(read_jsonl(native))
    demand(len(origin_rows)==len(native_rows)==6000,'FULL_PERSISTED_6000_JOIN_REQUIRED')
    expected=Counter({f'B{i:02}':1000 for i in range(1,7)})
    demand(Counter(e['dataset_id'] for e in origin_rows)==expected,'PERSISTED_DATASET_COHORTS')
    pairs=joined_records(origin_rows,native_rows,json.loads(selection.read_text()))
    counts,migration,covariance,summaries=diagnose_events(pairs,json.loads(regions.read_text()))
    after={str(f):sha(f) for f in inputs}
    demand(before==after,'SOURCE_OR_EXISTING_DATA_MUTATED_DURING_READBACK')
    a.output.mkdir(parents=True)
    write_csv(a.output/'phase11_hf_origin_stage_counts.csv',counts)
    write_csv(a.output/'phase11_hf_region_migration.csv',migration)
    write_csv(a.output/'phase11_event_source_covariance.csv',covariance)
    result={'schema_version':1,'status':'VALIDATED_WITH_LIMITS','evidence_class':'ACTUAL_EXISTING_DATA_READBACK',
            'persisted_events_joined':6000,'HF_original_events_analysed':3000,'new_ROOT_loops':0,
            'ancestry_scope':'REUSE_FROZEN_PHASE9_ANNOTATIONS; INDEPENDENT_ME_FLAVOUR_NATIVE_BIT0_JOIN_REGION_AND_EVENT_COVARIANCE',
            'statistical_unit':'ORIGINAL_SOURCE_EVENT_ALL_JETS_CLUSTERED','original_N_per_HF_source':1000,
            'input_hashes_before':before,'input_hashes_after':after,
            'origin_stage_rows':len(counts),'region_migration_rows':len(migration),'covariance_rows':len(covariance),
            'covariance_triangle':'UPPER_SYMMETRIC; absent cross-dataset covariance UNKNOWN_NOT_ZERO',
            'physical_total_background':'BLOCKED','generator_exclusivity':'UNVERIFIED','no_physical_process_sum':True,
            'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'datasets':summaries}
    write_json(a.output/'phase11_existing_hf_event_crosscheck.json',result)
    trace_result={'schema_version':1,'evidence_class':'HISTORICAL_SOURCE_AUDIT','status':'INACTIVE_SOURCE_SUPPORTED_WITH_LIMITS',
                  'historical_runtime_cards':cards,'inactive_future_diff_sha256':sha(inactive),
                  'detector_card_parser_executed':False,'Delphes_executed':False,
                  'future_saved_denominator':'EFFICIENCY_PASSING_PRE_ISOLATION_CANDIDATES; NOT_PRE_EFFICIENCY_RAW_PARTICLE_DENOMINATOR',
                  'exact_candidate_overlap_map':'BLOCKED_REQUIRES_REVIEWED_WRITER','calibrated_fake_rate':None,'PHOTON_FAKE_RATE':'UNKNOWN'}
    write_json(a.output/'phase11_detector_source_trace.json',trace_result)
    print(json.dumps({k:result[k] for k in ('status','persisted_events_joined','HF_original_events_analysed','covariance_rows')}))

if __name__=='__main__':
    main()