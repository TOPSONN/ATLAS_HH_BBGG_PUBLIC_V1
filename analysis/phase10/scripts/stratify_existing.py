#!/usr/bin/env python3
"""Read existing persisted Phase9 annotations once; produce Phase10 event-unit strata."""
import argparse
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from hf_stratification import demand,read_jsonl,sha,stratify,validate_join,write_csv,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--origins',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    demand(not a.output.exists(),'PRESERVE_PRIOR_RESULTS_OUTPUT_MUST_BE_FRESH')
    origins=list(read_jsonl(a.origins));native=list(read_jsonl(a.native));demand(len(origins)==len(native)==6000,'FULL_BACKGROUND_6000_REQUIRED')
    for x,y in zip(origins,native):validate_join(x,y)
    demand(Counter(e['dataset_id'] for e in origins)==Counter({f'B{i:02}':1000 for i in range(1,7)}),'BACKGROUND_DATASET_COHORTS')
    for ds in sorted({e['dataset_id'] for e in origins}):
        cohort=[e for e in origins if e['dataset_id']==ds]
        demand([e['source_event_index'] for e in cohort]==list(range(1,1001)),'NONCONTIGUOUS_OR_DUPLICATE_SOURCE_EVENT')
        demand(len({e['source_event_sha256'] for e in cohort})==1000,'DUPLICATE_HARD_SOURCE_IDENTITY')
    edges_path=Path(__file__).resolve().parents[3]/'analysis/phase8/config/histogram_edges_v1.json'
    edge_config=__import__('json').loads(edges_path.read_text())['observables']
    shape_edges={name:edge_config[name]['edges'] for name in ('m_gamma_gamma','m_bb','m_HH')}
    rows,cov,overlap,summaries=stratify(origins,shape_edges);a.output.mkdir(parents=True)
    write_csv(a.output/'phase10_hf_strata.csv',rows);write_csv(a.output/'phase10_hf_covariance.csv',cov);write_csv(a.output/'phase10_process_overlap_diagnostics.csv',overlap)
    result=dict(schema_version=1,status='VALIDATED_WITH_LIMITS',evidence_class='ACTUAL_EXISTING_DATA_READBACK',source_events_joined=6000,source_events_stratified=3000,new_native_ROOT_loops=0,classification_scope='REUSE_FROZEN_PHASE9_EVENT_ANNOTATIONS_WITH_INDEPENDENT_ME_FLAGS_EVENT_JOIN_AND_STATISTICS',statistical_unit='ORIGINAL_SOURCE_EVENT_ALL_JETS_CLUSTERED',new_physical_events=0,heavy_flavour_generator_exclusivity='UNVERIFIED',physical_total_background='BLOCKED',input_hashes={str(a.origins):sha(a.origins),str(a.native):sha(a.native),str(edges_path):sha(edges_path)},strata_rows=len(rows),covariance_rows=len(cov),process_overlap_rows=len(overlap),datasets=summaries)
    write_json(a.output/'phase10_hf_summary.json',result);print(__import__('json').dumps({k:result[k] for k in ('status','source_events_joined','strata_rows','covariance_rows')}))
if __name__=='__main__':main()
