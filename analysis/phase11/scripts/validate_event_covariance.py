#!/usr/bin/env python3
"""Independent Fraction/integer-bitset audit of actual Phase11 covariance evidence.

No production arithmetic/classification imports. Uses frozen Phase9 annotations;
this is independent numerical analysis, not a fresh truth-origin classification.
"""
import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def same(actual,exact,name):
    target=float(exact);value=float(actual)
    require(math.isfinite(value) and abs(value-target)<=max(1e-24,abs(target)*2e-12),'INDEPENDENT_RATIONAL_MISMATCH_'+name)


def flag(e,name):
    h=e['heavy_flavour'];jets=h['jets'];pdgs={abs(int(v)) for v in e['hard_outgoing_pdg_ids']}
    values={
     'ME_BOTTOM':5 in pdgs,'ME_CHARM_WITHOUT_BOTTOM':4 in pdgs and 5 not in pdgs,'ME_LIGHT_OR_GLUON':not(pdgs & {4,5}),
     'INITIAL_HEAVY_RECORD':h['heavy_quark_birth_counts'].get('ME_INITIAL_HEAVY_FLAVOUR_RECORD',0)>0,
     'SHOWER_BOTTOM_BIRTH':h['shower_bottom_births']>0,'SHOWER_CHARM_BIRTH':h['shower_charm_births']>0,
     'DIRECT_G_TO_HEAVY_PAIR':h['direct_gluon_splitting_count']>0,
     'TERMINAL_B_HADRON':h['terminal_b_hadrons']>0,'TERMINAL_C_HADRON':h['terminal_c_hadrons']>0,
     'NATIVE_BOTTOM_JET':any(j['native_flavour']==5 for j in jets),'NATIVE_CHARM_JET':any(j['native_flavour']==4 for j in jets),
     'UNKNOWN_QUARK_BIRTH':h['unclassified_quark_births']>0,
     'UNKNOWN_HADRON_ENDPOINT':any(j['sole_hadron_endpoint'].startswith('UNKNOWN') for j in jets),
     'AMBIGUOUS_HADRON_ASSIGNMENT':len(h['ambiguous_hadron_assignment_ids'])>0,
     'AMBIGUOUS_PYTHIA_TUPLE':(e.get('pythia_mapping') or {}).get('ambiguous_or_missing',0)>0}
    require(name in values,'UNKNOWN_VECTOR_FLAG');return values[name]


def vector(name,origins,native):
    stage_names=('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
    selected=[]
    for e,n in zip(origins,native):
        if name in stage_names:passed=n['stages'][stage_names.index(name)]
        elif name.startswith('ORIGIN:'):passed=flag(e,name.split(':',1)[1])
        elif name.startswith('FINAL_ORIGIN:'):passed=n['stages'][4] and flag(e,name.split(':',1)[1])
        elif name.startswith('REGION:'):
            tag,mass=name.split(':')[1:]
            t=sum(bool(j['native_btag_bits']&1) for j in n['eligible_jets'])
            actual_tag=('TAG_0' if t==0 else 'TAG_1' if t==1 else 'TAG_GE2')
            m=n['observables']['m_gamma_gamma']
            actual_mass='UNDEFINED_MGG' if m is None else 'LOW_SIDEBAND' if 105<=m<120 else 'HIGGS_LIKE' if 120<=m<=130 else 'HIGH_SIDEBAND' if 130<m<=160 else 'OUTSIDE_MGG'
            passed=n['stages'][2] and actual_tag==tag and actual_mass==mass
        else:raise ValueError('UNKNOWN_VECTOR')
        selected.append(bool(passed))
    return sum(1<<i for i,p in enumerate(selected) if p)


def validate(phase9,diagnostics,phase10_summary):
    source=phase9/'origins_03/phase9_origins_event_details.jsonl';native_path=phase9/'native/phase9_native_events.jsonl'
    data={};native={}
    for path,target,key in [(source,data,'source_event_index'),(native_path,native,'source_event_ordinal')]:
        with path.open() as stream:
            for line in stream:
                e=json.loads(line)
                if e['dataset_id'] not in ('B01','B02','B03'):continue
                k=(e['dataset_id'],e[key]);require(k not in target,'DUPLICATE_SOURCE_EVENT');target[k]=e
    require(set(data)==set(native) and len(data)==3000,'FULL_ORIGINAL_SOURCE_COHORTS')
    for k in data:
        require(data[k]['source_event_sha256']==native[k]['source_event_sha256'] and data[k]['hepmc_event_sha256']==native[k]['hepmc_event_sha256'],'SOURCE_ID_JOIN')
    csv_path=diagnostics/'phase11_event_source_covariance.csv'
    rows=list(csv.DictReader(csv_path.open(newline='')));require(len(rows)==3825,'FULL_COVARIANCE_ROW_COVERAGE')
    summary=json.loads((diagnostics/'phase11_existing_hf_event_crosscheck.json').read_text())
    previous=json.loads(phase10_summary.read_text())
    checks=0;states={};seen=set();negative_disjoint=0
    for ds in ('B01','B02','B03'):
        oo=[data[(ds,i)] for i in range(1,1001)];nn=[native[(ds,i)] for i in range(1,1001)]
        weights={Fraction(str(e['source_weight_pb'])) for e in nn};require(len(weights)==1,'THIS_ACTUAL_DATA_AUDIT_REQUIRES_VERIFIED_EQUAL_WEIGHTS')
        w=next(iter(weights));dsrows=[r for r in rows if r['dataset_id']==ds];names=sorted({r['vector_a'] for r in dsrows}|{r['vector_b'] for r in dsrows});require(len(names)==50 and len(dsrows)==1275,'COMPLETE_UPPER_TRIANGLE')
        masks={name:vector(name,oo,nn) for name in names};n=1000
        for row in dsrows:
            a,b=row['vector_a'],row['vector_b'];key=(ds,a,b);require(key not in seen and a<=b,'DUPLICATE_OR_UNORDERED_COVARIANCE');seen.add(key)
            ma,mb=masks[a],masks[b];ka,kb=ma.bit_count(),mb.bit_count();overlap=(ma&mb).bit_count()
            exact=w*w*Fraction(n,n-1)*(Fraction(overlap)-Fraction(ka*kb,n))
            same(row['fixed_N_covariance_pb2'],exact,'COVARIANCE');checks+=1
            require(int(row['original_N'])==1000,'SELECTED_N_SUBSTITUTED')
            if a.startswith('REGION:') and b.startswith('REGION:') and a!=b and ka and kb:
                require(overlap==0 and exact<0,'REGION_MULTINOMIAL_CORRELATION_LOST');negative_disjoint+=1
        stages={}
        for stage in ('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160'):
            k=masks[stage].bit_count();value=summary['datasets'][ds]['stages'][stage];old=previous['datasets'][ds]['stages'][stage]
            require(k==value['events']==old['events'],'HISTORICAL_PHASE10_COUNT_CHANGED')
            total=w*k;variance=w*w*Fraction(k*(n-k),n-1)
            same(value['sumw_pb'],total,'STAGE_RATE');same(value['fixed_N_variance_pb2'],variance,'STAGE_VARIANCE')
            same(old['sumw_pb'],total,'PHASE10_STAGE_RATE');same(old['fixed_N_variance_pb2'],variance,'PHASE10_STAGE_VARIANCE');checks+=4
            stages[stage]={'events':k,'sumw_pb':float(total),'variance_pb2':float(variance)}
        states[ds]={'original_N':n,'equal_source_weight_pb':float(w),'covariance_vectors':len(names),'upper_triangle_rows':len(dsrows),'stage_checks':stages}
    inputs=[source,native_path,csv_path,diagnostics/'phase11_existing_hf_event_crosscheck.json',phase10_summary]
    return {'schema_version':1,'status':'PASS_INDEPENDENT_RATIONAL_BITSET_EXISTING_DATA','evidence_class':'ACTUAL_EXISTING_DATA_READBACK','independent_arithmetic':'Fraction + integer event bitsets, exact overlap counts and rational moments; no production imports','source_events':3000,'covariance_pairs_checked':len(rows),'negative_disjoint_region_covariances_checked':negative_disjoint,'numeric_comparisons':checks,'Phase10_stage_counts_rates_variances_match':True,'scope_limit':'Specialized to verified equal-weight historical cohorts. Signed-weight readiness tested separately with fixtures; no fresh origin classification or ROOT loop.','datasets':states,'input_hashes':{str(p):sha(p) for p in inputs},'new_ME_calls':0,'new_integrals':0,'new_events':0,'physical_total_background':'BLOCKED'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase9',type=Path,required=True);p.add_argument('--diagnostics',type=Path,required=True);p.add_argument('--phase10-summary',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(not a.output.exists(),'PRESERVE_EXISTING_RECEIPT')
    result=validate(a.phase9,a.diagnostics,a.phase10_summary)
    with a.output.open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','covariance_pairs_checked','numeric_comparisons')}))

if __name__=='__main__':main()