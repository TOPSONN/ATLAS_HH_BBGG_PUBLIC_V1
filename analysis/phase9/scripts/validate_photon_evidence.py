#!/usr/bin/env python3
"""Independent Decimal70 photon-summary validation of existing event evidence.

No import of the photon classifier, graph driver, or production statistics.
Does not rerun ROOT, reclassify truth, generate events or infer a fake rate.
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

LABELS = ('PROMPT_HARD_PROCESS','SHOWER_RADIATION','HADRON_DECAY','ELECTRON_ASSOCIATED','UNCLASSIFIED')
STAGES = ('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')

def need(ok, why):
    if not ok: raise ValueError(why)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def close(actual, expected, name):
    if expected is None:
        need(actual in (None,''), 'undefined became number: '+name);return
    a=Decimal(str(actual));e=Decimal(expected)
    need(a.is_finite() and abs(a-e)<=max(Decimal('2e-24'),abs(e)*Decimal('3e-12')), 'independent Decimal mismatch: '+name)

def partition_rows(rows):
    event_rows=[r for r in rows if r['classification_unit']=='SOURCE_EVENT_INDICATOR_NONEXCLUSIVE_ORIGIN_FLAGS']
    object_rows=[r for r in rows if r['classification_unit']=='SOURCE_EVENT_HAS_MATCHING_PHOTON_ORIGIN_OBJECT']
    need(len(event_rows)==150 and len(object_rows)==600 and len(rows)==750,'unexpected photon evidence unit/cardinality')
    return event_rows,object_rows

def clustered_object_moments(counts, weights):
    need(len(counts)==len(weights) and len(counts)>1,'incomplete object cohort')
    need(all(isinstance(c,int) and not isinstance(c,bool) and c>=0 for c in counts),'invalid object counts')
    with localcontext() as context:
        context.prec=70
        n=Decimal(len(counts));y=[Decimal(c)*Decimal(str(w)) for c,w in zip(counts,weights)]
        need(all(v.is_finite() for v in y),'nonfinite object weight')
        sy=sum(y);vy=n/(n-1)*(sum(v*v for v in y)-sy*sy/n)
        return sy,vy

def validate(details, summary, csv_path):
    cohorts={}
    for line in Path(details).read_text().splitlines():
        event=json.loads(line);ds=event['dataset_id'];cohorts.setdefault(ds,[]).append(event)
        p=event['photon_origin'];need(p['source_event_sha256']==event['source_event_sha256'],'source hash mismatch')
        need(p['fake_rate_status']=='BLOCKED_CALIBRATION_UNAVAILABLE' and p['calibrated_fake_probability'] is None,'unapproved fake inference')
        selected=[q for q in p['reco_photons'] if q['selected']]
        for field,objects in [('native_reco_photon_counts',p['reco_photons']),('selected_reco_photon_counts',selected)]:
            counts={label:sum(q['origin']==label for q in objects) for label in LABELS}
            need(p[field]==counts and sum(counts.values())==len(objects),'photon count/category closure failed')
        assigned=[]
        for q in p['reco_photons']:
            need(q['origin'] in LABELS,'unknown label')
            if q['matched_truth_id'] is not None:
                need(q['delta_r'] is not None and 0<=q['delta_r']<.2,'invalid geometric cone')
                assigned.append(q['matched_truth_id'])
            if q['origin']=='PROMPT_HARD_PROCESS':
                t=q['truth_origin'];need(set(t['copy_chain_ids'])&set(p['verified_hard_photon_roots']),'prompt origin lacks verified root')
            if q['origin']=='SHOWER_RADIATION':
                need(any(41<=abs(s)<=59 for s in q['truth_origin']['birth_original_pythia_statuses']),'radiation lacks original status')
        need(len(assigned)==len(set(assigned)),'truth object assigned to multiple native photons')
    need(set(cohorts)=={'B01','B02','B03','B04','B05','B06'},'missing complete background cohort')
    s=json.loads(Path(summary).read_text())
    object_checks=0
    for ds,events in cohorts.items():
        need(len(events)==1000 and s['datasets'][ds]['original_N']==1000,'wrong original N')
        need([e['source_event_index'] for e in events]==list(range(1,1001)),'source ordinal gap')
        totals={}
        for prefix,field in [('STABLE_TRUTH','stable_truth_photon_counts'),('FIDUCIAL_TRUTH','fiducial_truth_photon_counts'),('NATIVE_RECO','native_reco_photon_counts'),('SELECTED_RECO','selected_reco_photon_counts')]:
            for label in LABELS:
                key=prefix+'_'+label;totals[key]=sum(e['photon_origin'][field][label] for e in events)
                need(totals[key]==s['datasets'][ds]['photon_object_totals'].get(key,0),'object aggregate mismatch')
                object_checks+=1
    rows=list(csv.DictReader(Path(csv_path).open()))
    event_rows,object_rows=partition_rows(rows)
    keys=set(); comparisons=0
    with localcontext() as context:
        context.prec=70
        for row in rows:
            key=(row['dataset_id'],row['stage'],row['category'],row['classification_unit']);need(key not in keys,'duplicate CSV aggregate key');keys.add(key)
            ds,stage,category,unit=key;index=STAGES.index(stage);events=cohorts[ds]
            if unit=='SOURCE_EVENT_INDICATOR_NONEXCLUSIVE_ORIGIN_FLAGS':
                label=category.removeprefix('HAS_SELECTED_RECO_');need(label in LABELS,'unexpected event category')
                counts=[int(any(q['selected'] and q['origin']==label for q in e['photon_origin']['reco_photons'])) for e in events]
            else:
                fields={'STABLE_TRUTH_':'stable_truth_photon_counts','FIDUCIAL_TRUTH_':'fiducial_truth_photon_counts','NATIVE_RECO_':'native_reco_photon_counts','SELECTED_RECO_':'selected_reco_photon_counts'}
                prefixes=[prefix for prefix in fields if category.startswith(prefix)];need(len(prefixes)==1,'unknown object category')
                prefix=prefixes[0];label=category[len(prefix):];need(label in LABELS,'unexpected object class')
                counts=[e['photon_origin'][fields[prefix]][label] for e in events]
                need(all(isinstance(c,int) and c>=0 for c in counts),'invalid object multiplicity')
                need(row['fake_rate_interpretation']=='NOT_A_CALIBRATED_FAKE_RATE','object multiplicity inferred as fake rate')
            counts=[c if e['stages'][index] else 0 for c,e in zip(counts,events)]
            flags=[c>0 for c in counts]
            n=Decimal(len(events));k=sum(flags);w=[Decimal(str(e['weight_pb'])) for e in events];x=[v if flag else Decimal(0) for v,flag in zip(w,flags)]
            total=sum(x);squares=sum(v*v for v in x);variance=n/(n-1)*(squares-total*total/n)
            need(int(row['events'])==k and int(row['original_N'])==int(n),'event indicator count mismatch')
            for field,value in [('event_fraction',Decimal(k)/n),('sumw_pb',total),('sumw2_pb2',squares),('source_sampling_variance_pb2',variance),('source_sampling_se_pb',variance.sqrt()),('ESS',total*total/squares if squares else None)]:
                close(row[field],value,key.__repr__()+':'+field);comparisons+=1
            if unit=='SOURCE_EVENT_HAS_MATCHING_PHOTON_ORIGIN_OBJECT':
                sy,vy=clustered_object_moments(counts,w)
                need(int(row['object_count'])==sum(counts),'object multiplicity count mismatch')
                close(row['weighted_object_multiplicity_pb'],sy,'object weighted sum');comparisons+=1
                close(row['object_multiplicity_event_correlated_variance_pb2'],vy,'event-correlated object variance');comparisons+=1
            else:
                stage_flags=[e['stages'][index] for e in events];sn=sum(stage_flags);sw=sum(weight for weight,flag in zip(w,stage_flags) if flag)
                need(int(row['stage_event_denominator'])==sn,'stage denominator count mismatch')
                close(row['stage_weight_denominator_pb'],sw,'stage denominator sumw');comparisons+=1
                close(row['within_stage_event_fraction'],Decimal(k)/sn if sn else None,'conditional unweighted fraction');comparisons+=1
                ratio=total/sw if sw else None
                close(row['weighted_within_stage_fraction'],ratio,'conditional weighted fraction');comparisons+=1
                if ratio is not None:
                    residuals=[weight*(Decimal(int(flag))-ratio*Decimal(int(st))) for weight,flag,st in zip(w,flags,stage_flags)]
                    mean=sum(residuals)/n
                    se=(n/(n-1)*sum((r-mean)**2 for r in residuals)/(sw*sw)).sqrt()
                else:se=None
                close(row['weighted_within_stage_fraction_event_cluster_se'],se,'shared-event conditional fraction SE');comparisons+=1
    return {'status':'PASS_INDEPENDENT_PHOTON_EVENT_AND_OBJECT_CLOSURE','test_scope':'ACTUAL_EXISTING_DATA_READBACK','independent_method':'Decimal70; independently built selected object indicators; fixed complete cohort N','events':sum(map(len,cohorts.values())),'aggregate_rows':len(rows),'event_indicator_rows':len(event_rows),'object_multiplicity_rows':len(object_rows),'numerical_comparisons':comparisons,'object_aggregate_checks':object_checks,'source_hashes':{'event_details':sha(details),'origins_summary':sha(summary),'photon_csv':sha(csv_path)},'fake_calibration_status':'BLOCKED_CALIBRATION_UNAVAILABLE','new_ME_calls':0,'new_integrals':0,'new_events':0}

def main():
    a=argparse.ArgumentParser();a.add_argument('--details',type=Path,required=True);a.add_argument('--summary',type=Path,required=True);a.add_argument('--csv',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    out=validate(args.details,args.summary,args.csv)
    with args.output.open('x') as stream:json.dump(out,stream,indent=2);stream.write('\n')
    print(json.dumps(out))
if __name__=='__main__':main()