#!/usr/bin/env python3
"""Independent Python checks of actual native event, histogram and historical readback."""
import argparse,bisect,csv,hashlib,json,math,sys
from collections import defaultdict
from pathlib import Path
from postprocess import groups,mass_region,tag_region,summary
STAGES=['INPUT','PHOTONS','JETS','TWO_BTAGS','FINAL_MGG']
PAIRS={'mgg_vs_mbb':('m_gamma_gamma','m_bb'),'mgg_vs_mHH':('m_gamma_gamma','m_HH'),'mbb_vs_mHH':('m_bb','m_HH'),'pT_Hgg_vs_pT_Hbb':('diphoton_pT','dijet_pT')}
def near(a,b,scale=1e-30,n=1):
    return abs(a-b)<=128*sys.float_info.epsilon*max(n,1)*max(abs(a),abs(b),scale)
def require(condition,reason):
    if not condition:raise ValueError(reason)
def validate_histogram_cells(records,seen):
    for key,m in records.items():
        if m['status']!='DEFINED':
            require(not seen.get(key),'UNDEFINED_HISTOGRAM_HAS_CELLS');continue
        nx=len(m['x_edges'])+1;ny=len(m['y_edges'])+1 if m['dimension']==2 else 1
        expected={(x,) if m['dimension']==1 else (x,y) for x in range(nx) for y in range(ny)}
        require(seen.get(key,set())==expected,'INCOMPLETE_OR_OUT_OF_RANGE_HISTOGRAM_CELLS:'+str(key))
def check_prefix(g,pe):
    seen=set();counts=defaultdict(int)
    for e in pe:
        ds=e['dataset_id'];ordinal=e['source_event_ordinal'];require(type(ordinal)is int,'NONINTEGER_PREFIX_ORDINAL');require(ds in g,'UNKNOWN_PREFIX_DATASET');require(1<=ordinal<=min(100,len(g[ds])),'PREFIX_ORDINAL_OUT_OF_RANGE');key=(ds,ordinal)
        require(key not in seen,'DUPLICATE_PREFIX_SOURCE');seen.add(key);counts[ds]+=1
        require(e==g[ds][ordinal-1],'ACTUAL_PREFIX_FULL_EVENT_CONTENT_MISMATCH')
    require(set(counts)==set(g),'PREFIX_MISSING_DATASET')
    require(all(counts[ds]==min(100,len(g[ds])) for ds in g),'PREFIX_TRUNCATED_COHORT')
    return {'status':'PASS_EXACT_PREFIX_FULL_EVENT_SUMMARY_IDENTITY','actual_prefix_entries_read':len(pe),'additional_independent_sources':0,'evidence_class':'REFERENCE_PREFIX_TEST'}
def check_histograms(events,manifest,csvpath,edge_input):
    by=groups(events);edge=edge_input['observables'];hist={};counts=0;missing=0
    for ds,ev in by.items():
        for si,stage in enumerate(STAGES):
            for observable in list(edge)+list(PAIRS):
                dims=PAIRS.get(observable,(observable,));bins=defaultdict(list);miss=0
                for e in ev:
                    if not e['stages'][si]:continue
                    values=[e['observables'][d] for d in dims]
                    if any(v is None for v in values):miss+=1;continue
                    cell=tuple(bisect.bisect_right(edge[d]['edges'],v) for d,v in zip(dims,values));bins[cell].append(e['source_weight_pb'])
                hist[ds,stage,observable]=(bins,miss)
    hmanifest=json.loads((csvpath.parent/'phase8_histogram_manifest.json').read_text())
    records={}
    for m in hmanifest['histograms']:
        key=(m['dataset_id'],m['stage'],m['observable'],m['normalization_mode']);require(key not in records,'DUPLICATE_HISTOGRAM_MANIFEST_ID');records[key]=m
        bins,miss=hist[key[:3]];require(m['missing_count']==miss,'HISTOGRAM_MISSING_COUNT:'+str(key));require(m['invalid_count']==0,'HISTOGRAM_INVALID_COUNT')
    expected={(ds,stage,obs,mode) for ds in by for stage in STAGES for obs in list(edge)+list(PAIRS) for mode in ['RAW_EVENT_COUNTS','SOURCE_WEIGHTED','UNIT_AREA_SHAPE','EXPLORATORY_LUMINOSITY_YIELD']}
    require(set(records)==expected,'INCOMPLETE_HISTOGRAM_MANIFEST');seen=defaultdict(set)
    row_count=0
    with csvpath.open() as f:
        for r in csv.DictReader(f):
            row_count+=1;key=(r['dataset_id'],r['stage'],r['observable'],r['normalization_mode']);m=records[key];bins,miss=hist[key[:3]];dim=int(r['dimension']);cell=(int(r['bin_x']),) if dim==1 else (int(r['bin_x']),int(r['bin_y']));weights=bins.get(cell,[])
            require(m['status']=='DEFINED','UNDEFINED_HISTOGRAM_CSV_ROW');require(dim==m['dimension'],'HISTOGRAM_CSV_DIMENSION_MISMATCH');require(cell not in seen[key],'DUPLICATE_HISTOGRAM_CSV_CELL');seen[key].add(cell)
            n=manifest[key[0]]['N_original'];s=math.fsum(weights);sq=math.fsum(x*x for x in weights)
            mode=key[3]
            if mode=='RAW_EVENT_COUNTS':s=sq=len(weights);factor=1.
            elif mode=='UNIT_AREA_SHAPE':
                denom=math.fsum(v for w in bins.values() for v in w);require(denom!=0,'UNEXPECTED_EMPTY_SHAPE');factor=1/denom
            elif mode=='EXPLORATORY_LUMINOSITY_YIELD':factor=manifest[key[0]]['model_br_factor']*100000
            else:factor=1.
            expected=s*factor;expected_sq=sq*factor*factor
            require(near(float(r['content']),expected,n=n),'HISTOGRAM_CONTENT:'+str(key)+':'+str(cell));require(near(float(r['sumw2']),expected_sq,n=n),'HISTOGRAM_SUMW2:'+str(key)+':'+str(cell));counts+=1
    validate_histogram_cells(records,seen)
    return {'status':'PASS_INDEPENDENT_ALL_NATIVE_HISTOGRAM_CELLS','csv_rows_checked':row_count,'content_and_sumw2_pairs_checked':counts,'histogram_manifest_entries':len(records),'tolerance':'128*double_epsilon*N_original*max(abs(observed),abs(expected),1e-30); independent math.fsum versus ROOT serial double accumulation'}
def historical(g,manifest):
    report=[]
    for ds,ev in g.items():
        p=Path(manifest[ds]['historical_reco_path']);old=[json.loads(line) for line in p.read_text().splitlines()];require(len(old)==len(ev),'HISTORICAL_COHORT_SIZE:'+ds);pairs=0;maxdiff=0.
        for new,prior in zip(ev,old):
            require(new['source_event_sha256']==prior.get('source_event_sha256',prior.get('source_event_hash')),'HISTORICAL_SOURCE_HASH:'+ds)
            require(new['source_event_ordinal']==prior['source_event_index'],'HISTORICAL_SOURCE_ORDINAL:'+ds)
            require(near(new['source_weight_pb'],prior['source_contribution_pb']),'HISTORICAL_SOURCE_WEIGHT:'+ds)
            for si,k in enumerate(['cut_photons','cut_jets','cut_two_btags','cut_mgg'],1):require(new['stages'][si]==prior[k],'HISTORICAL_EVENT_STAGE:'+ds+':'+str(new['source_event_ordinal']))
            for now,was in [('m_gamma_gamma','m_gamma_gamma'),('m_bb','m_bb'),('m_HH','m_bb_gamma_gamma'),('DeltaR_gamma_gamma','DeltaR_gamma_gamma'),('DeltaR_bb','DeltaR_bb')]:
                if was not in prior:continue
                a=new['observables'][now];b=prior[was];require((a is None)==(b is None),'HISTORICAL_DEFINED_STATE:'+ds+':'+now)
                if a is not None:
                    require(abs(a-b)<=1e-8+1e-10*max(abs(a),abs(b)),'HISTORICAL_RECO_VALUE:'+ds+':'+now);maxdiff=max(maxdiff,abs(a-b));pairs+=1
        report.append({'dataset_id':ds,'events_checked':len(ev),'source_hash_and_four_event_stage_checks':'PASS','historical_mass_and_angular_pairs_checked':pairs,'largest_absolute_value_difference':maxdiff,'comparison_tolerance':'1e-8 absolute + 1e-10 relative (historical Cartesian precision)','evidence_class':'ACTUAL_FULL_DATA_READBACK'})
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--native',type=Path,required=True);p.add_argument('--edges',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--prefix',type=Path);a=p.parse_args();require(not a.output.exists(),'REFUSE_VALIDATION_OVERWRITE')
    manifest={d['dataset_id']:d for d in json.loads(a.manifest.read_text())['datasets']};events=[json.loads(line) for line in (a.native/'phase8_events.jsonl').read_text().splitlines()];g=groups(events);require(set(g)==set(manifest),'DATASET_COHORT_MISMATCH')
    cut=[]
    for ds,ev in g.items():
        actual=[sum(e['stages'][k] for e in ev) for k in range(5)];require(actual==manifest[ds]['expected_cutflow'],'INDEPENDENT_CUTFLOW_CLOSURE:'+ds);require(len(ev)==manifest[ds]['expected_entries'],'ACTUAL_ENTRIES_MISMATCH:'+ds)
        for e in ev:
            require(e['model_factor_applied']==0,'BR_ALREADY_APPLIED_IN_NATIVE_SOURCE');require(near(e['source_weight_pb']*len(ev),e['raw_LHE_XWGTUP_pb']),'ORIGINAL_N_NORMALIZATION')
            for k,v in e['observables'].items():require(v is None or math.isfinite(v),'NONFINITE_NATIVE_OBSERVABLE:'+k)
            for name,candidate in e['reconstruction'].items():
                if candidate is not None:require(all(v is None or math.isfinite(v) for v in candidate.values()),'NONFINITE_CANDIDATE')
        cut.append({'dataset_id':ds,'actual':actual,'status':'FULL_CUTFLOW_PASS'})
    h=check_histograms(events,manifest,a.native/'phase8_histograms.csv',json.loads(a.edges.read_text()));old=historical(g,manifest);prefix=None
    if a.prefix:
        pe=[json.loads(line) for line in (a.prefix/'phase8_events.jsonl').read_text().splitlines()];prefix=check_prefix(g,pe)
    truth=json.loads((a.native/'phase8_truth_matching.json').read_text());require(truth['S01_C1000']['Hgg_matches']==[60,299,641],'SIGNAL_PHOTON_TRUTH_MATCH_CLOSURE');require(truth['S01_C1000']['Hbb_matches']==[43,402,555],'SIGNAL_BOTTOM_TRUTH_MATCH_CLOSURE')
    result={'status':'PASS_INDEPENDENT_ACTUAL_NATIVE_READBACK','evidence_class':'ACTUAL_FULL_DATA_READBACK','independent_source_events':len(events),'cutflow':cut,'histograms':h,'historical_regression':old,'reference_prefix':prefix,'new_ME_calls':0,'new_integrals':0,'new_independent_events':0}
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'full_entries':len(events),'histogram_cells':h['csv_rows_checked'],'prefix':prefix}))
if __name__=='__main__':main()