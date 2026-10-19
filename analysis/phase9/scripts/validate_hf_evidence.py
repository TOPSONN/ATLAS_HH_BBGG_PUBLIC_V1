#!/usr/bin/env python3
"""Independent Decimal70 HF event/CSV validation; no graph reclassification."""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import math
import re
from pathlib import Path

STAGES = ('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
EXPECTED = {'B01':[1000,446,266,91,28], 'B02':[1000,378,241,7,1], 'B03':[1000,445,277,0,0]}


def require(ok, message):
    if not ok: raise ValueError(message)


def read_rows(path):
    with Path(path).open() as stream:
        for line in stream:
            require(len(line) <= 16*1024**2, 'unbounded event evidence row')
            yield json.loads(line)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''): h.update(block)
    return h.hexdigest()


def jet_key(j):
    return 'HARD_{hard_cone_flavour}_SHOWER_{shower_record_cone_flavour}_HADRON_{heavy_hadron_flavour}_NATIVE_{native_flavour}_TAG_{tag}'.format(**j,tag=int(j['tagged']))


def indicator(h, category):
    jets=h['jets']; counts=h['heavy_quark_birth_counts']; n=sum(j['tagged'] for j in jets)
    direct={
      'ME_BOTTOM':h['hard_process_flavour']=='ME_BOTTOM', 'ME_CHARM':h['hard_process_flavour']=='ME_CHARM',
      'ME_LIGHT_OR_GLUON':h['hard_process_flavour']=='ME_LIGHT_OR_GLUON',
      'HAS_ME_INITIAL_HEAVY_FLAVOUR_RECORD':counts.get('ME_INITIAL_HEAVY_FLAVOUR_RECORD',0)>0,
      'HAS_SHOWER_BOTTOM_BIRTH':h['shower_bottom_births']>0,
      'HAS_SHOWER_CHARM_BIRTH':h['shower_charm_births']>0,
      'HAS_DIRECT_G_TO_HEAVY_PAIR':h['direct_gluon_splitting_count']>0,
      'HAS_TERMINAL_B_HADRON':h['terminal_b_hadrons']>0,
      'HAS_TERMINAL_C_HADRON':h['terminal_c_hadrons']>0,
      'HAS_UNCLASSIFIED_QUARK_BIRTH':h['unclassified_quark_births']>0,
      'HAS_AMBIGUOUS_HADRON_ASSIGNMENT':bool(h['ambiguous_hadron_assignment_ids']),
      'HAS_NATIVE_BOTTOM_JET':any(j['native_flavour']==5 for j in jets),
      'HAS_NATIVE_CHARM_JET':any(j['native_flavour']==4 for j in jets),
      'HAS_HEAVY_HADRON_ELIGIBLE_JET':any(j['heavy_hadron_flavour'] in (4,5) for j in jets),
      'HARD_LIGHT_NATIVE_HEAVY':h['hard_process_flavour']=='ME_LIGHT_OR_GLUON' and any(j['native_flavour'] in (4,5) for j in jets),
      'HAS_NATIVE_FLAVOUR_BOUNDARY_AMBIGUITY':any(len(j['native_attainable_labels'])>1 for j in jets),
      'HAS_NATIVE_FLAVOUR_MISMATCH':not h['native_reproduction_pass'],
      'NATIVE_TAGS_0':n==0, 'NATIVE_TAGS_1':n==1, 'NATIVE_TAGS_GE2':n>=2}
    require(category in direct, 'unknown HF category '+category)
    return direct[category]


def close(actual, expected, field):
    if expected is None:
        require(actual=='', 'undefined quantity was filled: '+field); return
    value=Decimal(actual)
    require(value.is_finite(), 'nonfinite CSV quantity '+field)
    tolerance=max(Decimal('1e-28'),abs(expected)*Decimal('3e-12'))
    require(abs(value-expected)<=tolerance, 'independent Decimal mismatch '+field+': '+actual+' vs '+str(expected))


def moments(xs):
    n=Decimal(len(xs)); total=sum(xs); sq=sum(x*x for x in xs)
    var=n/(n-1)*(sq-total*total/n)
    require(var>=0,'negative independent Decimal variance')
    return total,sq,var,(total*total/sq if sq else None)


def validate(origins_dir,native_jsonl):
    events=defaultdict(list); native={}
    for row in read_rows(native_jsonl):
        if row['dataset_id'] not in EXPECTED: continue
        key=(row['dataset_id'],row['source_event_ordinal']);require(key not in native,'duplicate native source');native[key]=row
    for row in read_rows(origins_dir/'phase9_origins_event_details.jsonl'):
        ds=row['dataset_id']
        if ds not in EXPECTED: continue
        index=row['source_event_index'];require(index==len(events[ds])+1,'duplicate/skipped HF ordinal')
        original=native[(ds,index)]
        require(row['source_event_sha256']==original['source_event_sha256'] and row['hepmc_event_sha256']==original['hepmc_event_sha256'],'HF/native identity mismatch')
        require(row['stages']==original['stages'] and row['weight_pb']==original['source_weight_pb'],'HF/native stages or weights differ')
        h=row['heavy_flavour'];require(h['no_physical_background_sum'] is True,'unapproved physical sum')
        require(len(h['jets'])==len(original['eligible_jets']),'eligible jet count differs')
        for j,ref in zip(h['jets'],original['eligible_jets']):
            require(all(j[k]==ref[k] for k in ('index','pt','eta','phi','tagged')) and j['native_flavour']==ref['flavour'],'observed native jet fields changed')
            require(j['native_reproduction_pass']==(j['native_flavour'] in j['native_attainable_labels']),'native reconstruction evidence inconsistent')
        require(h['native_reproduction_pass']==all(j['native_reproduction_pass'] for j in h['jets']),'event native-reproduction flag inconsistent')
        events[ds].append(row)
    require(set(events)==set(EXPECTED),'missing HF cohort')
    for ds,rows in events.items():
        require([sum(e['stages'][i] for e in rows) for i in range(5)]==EXPECTED[ds],'historical stage closure failed')
    csv_rows=list(csv.DictReader((origins_dir/'phase9_heavy_flavour_origins.csv').open()))
    checks=0; seen=set(); partition_counts=defaultdict(int);partition_weight=defaultdict(Decimal)
    with localcontext() as context:
        context.prec=70
        for row in csv_rows:
            ds,stage,cat=row['dataset_id'],row['stage'],row['category'];key=(ds,stage,cat)
            require(key not in seen,'duplicate category evidence');seen.add(key)
            i=STAGES.index(stage); cohort=events[ds]; weights=[Decimal(str(e['weight_pb'])) for e in cohort]
            composition=bool(re.fullmatch(r'HARD_[0-9]+_SHOWER_[0-9]+_HADRON_[0-9]+_NATIVE_[0-9]+_TAG_[01]',cat))
            require(row.get('weight_scope','') in ('','RAW_SOURCE_PB_NO_NEW_NORMALIZATION'),'unknown weight scope')
            require(bool(row.get('weight_scope')) or composition,'missing indicator weight scope')
            if composition: require(row['classification_unit']=='SOURCE_EVENT_HAS_MATCHING_ELIGIBLE_JET','unknown object row unit')
            counts=[sum(jet_key(j)==cat for j in e['heavy_flavour']['jets']) if e['stages'][i] else 0 for e in cohort] if composition else [int(e['stages'][i] and indicator(e['heavy_flavour'],cat)) for e in cohort]
            flags=[int(c>0) for c in counts];xs=[w*f for w,f in zip(weights,flags)]
            total,sq,var,ess=moments(xs)
            require(int(row['events'])==sum(flags) and int(row['original_N'])==len(cohort),'event count mismatch')
            for name,expected in [('sumw_pb',total),('sumw2_pb2',sq),('source_sampling_variance_pb2',var),('source_sampling_se_pb',var.sqrt()),('ESS',ess)]:close(row[name],expected,name);checks+=1
            if composition:
                require(int(row['eligible_jet_count'])==sum(counts),'jet count mismatch')
                mtotal,_,mvar,_=moments([w*Decimal(c) for w,c in zip(weights,counts)])
                close(row['weighted_jet_multiplicity_pb'],mtotal,'weighted jet count');close(row['jet_multiplicity_event_correlated_variance_pb2'],mvar,'cluster jet variance');checks+=2
                partition_counts[(ds,stage)]+=sum(counts);partition_weight[(ds,stage)]+=mtotal
            else:
                denominator=sum(w for w,e in zip(weights,cohort) if e['stages'][i]); dcount=sum(e['stages'][i] for e in cohort)
                close(row['stage_weight_denominator_pb'],denominator,'stage denominator');checks+=1
                require(int(row['stage_event_denominator'])==dcount,'stage event denominator mismatch')
                ratio=total/denominator if denominator else None
                close(row['weighted_within_stage_fraction'],ratio,'within-stage ratio');checks+=1
                rvar=None
                if denominator:
                    residuals=[w*(Decimal(f)-ratio*Decimal(int(e['stages'][i]))) for w,f,e in zip(weights,flags,cohort)]
                    rvar=moments(residuals)[2]/(denominator*denominator)
                close(row['weighted_within_stage_fraction_event_cluster_se'],rvar.sqrt() if rvar is not None else None,'ratio cluster SE');checks+=1
        for ds,cohort in events.items():
            for i,stage in enumerate(STAGES):
                expected_counts=sum(len(e['heavy_flavour']['jets']) for e in cohort if e['stages'][i])
                expected_weight=sum(Decimal(str(e['weight_pb']))*len(e['heavy_flavour']['jets']) for e in cohort if e['stages'][i])
                require(partition_counts[(ds,stage)]==expected_counts,'jet-composition partition count failed')
                require(partition_weight[(ds,stage)]==expected_weight,'jet-composition weighted closure failed');checks+=2
    return dict(status='PASS_INDEPENDENT_DECIMAL70_HF_EVENT_CSV_CLOSURE',evidence_class='ACTUAL_EXISTING_DATA_READBACK',
                note='Numerical and native-object identity validation; not an independent full-graph reclassification',
                source_events=3000, csv_rows=len(csv_rows), numerical_checks=checks,
                jet_partition_closure=True, native_fields_preserved=True,
                input_hashes={p.name:digest(p) for p in (origins_dir/'phase9_origins_event_details.jsonl',origins_dir/'phase9_heavy_flavour_origins.csv',native_jsonl)})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--origins',type=Path,required=True);p.add_argument('--native-jsonl',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(not a.output.exists(),'preserve existing validation receipt')
    result=validate(a.origins,a.native_jsonl);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))

if __name__=='__main__':main()