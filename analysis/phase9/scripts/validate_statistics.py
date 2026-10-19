#!/usr/bin/env python3
"""Independent Decimal70 validation of persisted Phase9 statistics.

No production statistics module is imported. Existing Phase8 event summaries
supply source units; this is not a new ROOT dispatch or event generation.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
from decimal import Decimal,localcontext
import hashlib
import json
import math
from pathlib import Path

STAGES=('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
TAGS=('TAG_0','TAG_1','TAG_GE2')
MASSES=('LOW','HIGGS','HIGH','OUTSIDE_MGG','UNDEFINED_MGG')
OBS=('m_gamma_gamma','m_bb','m_HH','DeltaR_bb','DeltaR_gamma_gamma','diphoton_pT','dijet_pT','reconstructed_jet_multiplicity','native_btag_multiplicity')
EPS64=Decimal('0.0000000000000142108547152020037174224853515625')


def require(ok,reason):
    if not ok:raise ValueError(reason)


def number(x):
    require(not isinstance(x,bool),'boolean numerical quantity')
    value=Decimal(str(x));require(value.is_finite(),'nonfinite numerical quantity')
    return value


def compare(actual,expected,field):
    if expected is None:
        require(actual in (None,''),'undefined quantity was filled: '+field);return
    value=number(actual)
    tolerance=max(Decimal('2e-27'),abs(expected)*Decimal('4e-12'))
    require(abs(value-expected)<=tolerance,'independent Decimal70 mismatch '+field+': '+str(value)+' vs '+str(expected))


def variance(total,squared,n):
    require(isinstance(n,int) and not isinstance(n,bool) and n>1,'invalid original N')
    numerator=Decimal(n)*squared-total*total
    require(numerator>=0,'negative independent fixed-N variance')
    return numerator/Decimal(n-1)


def moments(weights,n):
    require(len(weights)<=n,'more contributions than original source events')
    ws=[number(x) for x in weights];s=sum(ws,Decimal(0));q=sum((x*x for x in ws),Decimal(0));a=sum((abs(x) for x in ws),Decimal(0))
    return s,q,a,variance(s,q,n),(s*s/q if q else None)


def conditioned(s,a):
    return a>0 and abs(s)>EPS64*a


def normalized_delta(s,q,a,b,qb,n):
    require(q>=0 and qb>=0 and qb<=q,'invalid squared-weight partition')
    if not conditioned(s,a):return None,None
    p=b/s
    # Disjoint bin/other squared sums give this independent closed form.
    v=Decimal(n)/Decimal(n-1)*((1-p)*(1-p)*qb+p*p*(q-qb))/(s*s)
    require(v>=0,'negative normalized closed-form variance')
    return p,v


def mass_region(mass):
    if mass is None:return 'UNDEFINED_MGG'
    m=number(mass)
    if Decimal(105)<=m<Decimal(120):return 'LOW'
    if Decimal(120)<=m<=Decimal(130):return 'HIGGS'
    if Decimal(130)<m<=Decimal(160):return 'HIGH'
    return 'OUTSIDE_MGG'


def derive_stages(event):
    obs=event['observables'];jets=event['eligible_jets']
    require(all(number(j['pt'])>25 and abs(number(j['eta']))<Decimal('2.5') for j in jets),'noneligible jet in persisted eligible list')
    for j in jets:
        require(isinstance(j['native_btag_bits'],int) and not isinstance(j['native_btag_bits'],bool),'invalid native tag bits')
        require(j['tagged']==bool(j['native_btag_bits']&1),'tagged is not native bit0')
    tags=sum(bool(j['native_btag_bits']&1) for j in jets)
    require(tags==event['native_btag_multiplicity'],'native tag multiplicity mismatch')
    if tags<2:require(obs['m_bb'] is None and obs['m_HH'] is None,'null tagged-pair candidate violated')
    pair=event['selected_photon_multiplicity']>=2
    if pair:
        for prefix in ('photon1','photon2'):
            eta=abs(number(obs[prefix+'_eta']))
            require(eta<Decimal('2.37') and not Decimal('1.37')<eta<Decimal('1.52'),'stored selected photon acceptance violated')
        require(number(obs['photon1_pT'])>25 and number(obs['photon2_pT'])>25,'stored selected photon pT violated')
        pair=number(obs['photon1_pT'])>35
    stage2=pair and len(jets)>=2
    stage3=stage2 and tags>=2
    mgg=obs['m_gamma_gamma']
    stage4=stage3 and mgg is not None and Decimal(105)<=number(mgg)<=Decimal(160)
    stages=[True,bool(pair),bool(stage2),bool(stage3),bool(stage4)]
    require(stages==event['stages'],'independent baseline stage reconstruction differs')
    return stages,tags


def region_for(event):
    stages,tags=derive_stages(event)
    if not stages[2]:return None
    tag=TAGS[min(tags,2)]
    return tag,mass_region(event['observables']['m_gamma_gamma'])


def bucket(value,edges):
    require(len(edges)>=2 and all(edges[i]<edges[i+1] for i in range(len(edges)-1)),'invalid histogram edges')
    x=number(value)
    if x<edges[0]:return 0
    if x>=edges[-1]:return len(edges)
    for j in range(len(edges)-1):
        if edges[j]<=x<edges[j+1]:return j+1
    raise ValueError('no independent bin assignment')


def csv_rows(path):
    with Path(path).open(newline='') as stream:return list(csv.DictReader(stream))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()


def validate(statistics,phase8):
    manifest_path=phase8/'phase8_local_manifest.json';event_path=phase8/'native/phase8_events.jsonl'
    manifest=json.loads(manifest_path.read_text());datasets={d['dataset_id']:d for d in manifest['datasets']};cohorts=defaultdict(list);groups=defaultdict(list)
    with event_path.open() as stream:
        for line in stream:
            require(len(line)<16*1024**2,'unbounded original summary row')
            e=json.loads(line);did=e['dataset_id'];require(did in datasets,'unknown dataset')
            require(e['source_event_ordinal']==len(cohorts[did])+1,'duplicate/skipped source ordinal')
            require(e['N_original']==datasets[did]['N_original'],'source denominator mismatch')
            derive_stages(e);cohorts[did].append(e)
            key=region_for(e)
            if key is not None:groups[(did,*key)].append(e)
    require(set(cohorts)==set(datasets) and sum(map(len,cohorts.values()))==7100,'not complete 7100 original cohort')
    for did,events in cohorts.items():
        require(len(events)==datasets[did]['N_original'],'cohort size mismatch')
        require(len({e['source_event_sha256'] for e in events})==len(events),'duplicate hard-source event identity')
        require([sum(e['stages'][i] for e in events) for i in range(5)]==datasets[did]['expected_cutflow'],'historical cutflow changed')
    checks=0;hist_bins=0
    with localcontext() as context:
        context.prec=70
        plots=json.loads((statistics/'phase9_plot_data.json').read_text());histograms=plots['histograms'];require(len(histograms)==144,'not all 144 plot histograms')
        seen=set()
        for hist in histograms:
            did,stage,obs=hist['dataset_id'],hist['stage'],hist['observable'];key=(did,stage,obs)
            require(key not in seen and obs in OBS,'duplicate/unknown plot histogram');seen.add(key)
            require(hist['tag_region']=='ALL' and hist['mass_region']=='ALL','unexpected plot region')
            require(hist['flow_policy']=='INCLUDE_UNDERFLOW_AND_OVERFLOW_IN_DENOMINATOR','wrong flow denominator contract')
            n=datasets[did]['N_original'];i=STAGES.index(stage);selected=[e for e in cohorts[did] if e['stages'][i]]
            edges=[number(x) for x in hist['edges']];bins=[[] for _ in range(len(edges)+1)];defined=[]
            for event in selected:
                x=event['observables'][obs]
                if x is not None:
                    where=bucket(x,edges);bins[where].append(event['source_weight_pb']);defined.append(event['source_weight_pb'])
            s,q,a,v,ess=moments(defined,n)
            require(hist['N_original']==n and hist['N_selected']==len(selected) and hist['N_defined']==len(defined),'histogram source count differs')
            require(hist['missing']==len(selected)-len(defined) and hist['invalid']==0,'histogram missing/invalid differs')
            for field,expected in [('sumw',s),('sumw2',q),('sum_absw',a),('ESS',ess)]:compare(hist[field],expected,'hist '+field);checks+=1
            require(hist['status']==('DEFINED_DESCRIPTIVE' if conditioned(s,a) else 'UNDEFINED_EMPTY_OR_CANCELLATION'),'wrong histogram defined status')
            records=[hist['underflow'],*hist['bins'],hist['overflow']];require(len(records)==len(bins),'missing flow/bin records')
            fractions=[]
            for record,weights in zip(records,bins):
                b,qb,ab,vb,eb=moments(weights,n);p,pv=normalized_delta(s,q,a,b,qb,n)
                require(record['N']==len(weights),'histogram bin source count differs')
                for field,expected in [('sumw',b),('sumw2',qb),('source_variance',vb),('ESS',eb),('value',p),('variance',pv)]:compare(record[field],expected,'bin '+field);checks+=1
                if p is not None:fractions.append(p)
                hist_bins+=1
            if conditioned(s,a):compare(sum(fractions),Decimal(1),'flow-inclusive normalized closure');checks+=1
        region_rows=csv_rows(statistics/'phase9_region_diagnostics.csv');require(len(region_rows)==120,'not all 120 regions');seen=set()
        for row in region_rows:
            did,tag,mass=row['dataset_id'],row['tag_region'],row['mass_region'];key=(did,tag,mass)
            require(key not in seen and tag in TAGS and mass in MASSES,'duplicate/unknown region');seen.add(key)
            events=groups[key];n=datasets[did]['N_original'];br=number(datasets[did]['model_br_factor']);eligible=sum(e['stages'][2] for e in cohorts[did])
            require(row['stage']==STAGES[2] and int(row['N_original'])==n and int(row['N_eligible'])==eligible and int(row['N_region'])==len(events),'region counts differ')
            s,q,a,v,ess=moments([e['source_weight_pb'] for e in events],n)
            for field,expected in [('source_sumw_pb',s),('source_sumw2_pb2',q),('fixed_N_variance_pb2',v),('MODEL_BR_ONLY_sumw_pb',s*br),('MODEL_BR_ONLY_variance_pb2',v*br*br),('ESS',ess)]:compare(row[field],expected,'region '+field);checks+=1
        require(seen=={(d,t,m) for d in datasets for t in TAGS for m in MASSES},'region Cartesian coverage differs')
        for did,events in cohorts.items():
            eligible=[e for e in events if e['stages'][2]];partition=[e for t in TAGS for m in MASSES for e in groups[(did,t,m)]]
            require(len(partition)==len(eligible) and {e['source_event_ordinal'] for e in partition}=={e['source_event_ordinal'] for e in eligible},'region event exclusivity/closure failed')
            require(sum((number(e['source_weight_pb']) for e in partition),Decimal(0))==sum((number(e['source_weight_pb']) for e in eligible),Decimal(0)),'region weight closure failed');checks+=2
        rare=csv_rows(statistics/'phase9_rare_event_precision.csv');require(len(rare)==40,'not all 40 stage-statistics rows');seen=set()
        for row in rare:
            did,stage=row['dataset_id'],row['stage'];key=(did,stage);require(key not in seen,'duplicate stage statistics');seen.add(key)
            n=datasets[did]['N_original'];i=STAGES.index(stage);events=[e for e in cohorts[did] if e['stages'][i]];k=len(events);ws=[number(e['source_weight_pb']) for e in events]
            s,q,a,v,ess=moments(ws,n);br=number(datasets[did]['model_br_factor']);se=v.sqrt();p=Decimal(k)/n
            require(int(row['N'])==n and int(row['k'])==k,'rare source count differs')
            require(int(row['BR_applications'])==datasets[did]['BR_factor_applications'],'BR application count differs')
            require(row['integration_error_combined']=='False' and row['zero_survivors_prove_zero_background']=='False','false physical uncertainty/zero interpretation')
            expected=[('acceptance',p),('raw_binomial_SE',(p*(1-p)/n).sqrt()),('source_sumw_pb',s),('source_sumw2_pb2',q),('fixed_original_N_sampling_variance_pb2',v),('weighted_source_MC_SE_pb',se),('weighted_source_relative_SE',se/abs(s) if conditioned(s,a) else None),('MODEL_BR_ONLY_sumw_pb',s*br),('MODEL_BR_ONLY_sampling_SE_pb',se*br),('model_BR_factor',br),('ESS',ess),('largest_source_abs_fraction',max((abs(x) for x in ws),default=Decimal(0))/a if a else None),('top5_source_abs_fraction',sum(sorted((abs(x) for x in ws),reverse=True)[:5],Decimal(0))/a if a else None)]
            if k==0:expected.append(('one_sided95_upper_if_zero',1-(Decimal('.05').ln()/n).exp()))
            else:require(row['one_sided95_upper_if_zero']=='','nonzero survivor upper-only field filled')
            for field,value in expected:compare(row[field],value,'stage '+field);checks+=1
        require(seen=={(d,s) for d in datasets for s in STAGES},'stage-statistics Cartesian coverage differs')
    inputs=[event_path,manifest_path,*[statistics/name for name in ('phase9_plot_data.json','phase9_region_diagnostics.csv','phase9_rare_event_precision.csv')]]
    return dict(status='PASS_INDEPENDENT_DECIMAL70_STATISTICS',evidence_class='INDEPENDENT_PERSISTED_EVENT_NUMERICAL_ANALYSIS',
                source_events=7100, fresh_ROOT_dispatches=0, histograms=144, flow_inclusive_bins=hist_bins, region_rows=120,
                region_event_exclusivity=True, region_raw_and_BR_weight_closure=True, stage_rows=40, numerical_comparisons=checks,
                formula='N/(N-1)*((1-p)^2 Qbin+p^2 Qother)/S^2; independent event-level Decimal70 reconstruction',
                CP_intervals='NOT_REIMPLEMENTED_HERE_SEPARATE_NATIVE_ROOT33_CASE_RECEIPT',
                physical_total_background='BLOCKED',physical_significance='NOT_EVALUATED',new_ME_calls=0,new_events=0,
                input_hashes={p.name:sha(p) for p in inputs})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--statistics',type=Path,required=True);p.add_argument('--phase8-results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(not a.output.exists(),'preserve prior validation receipt')
    result=validate(a.statistics,a.phase8_results);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))

if __name__=='__main__':main()