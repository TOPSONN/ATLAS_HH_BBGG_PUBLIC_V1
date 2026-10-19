#!/usr/bin/env python3
"""Bounded Phase9D/E diagnostics from unchanged Phase8 persisted cohorts; no production."""
import argparse
from collections import Counter,defaultdict
import csv
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import math
from pathlib import Path
import statistics
from phase9_regions import OBSERVABLES,STAGES,demand,fixed_n_variance,weight_summary,weighted_mean,histogram,region_key,shape_metrics

CONFIDENCE=.95
TARGET_RELATIVE_SE=(.20,.30,.50)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def load(path):return json.loads(Path(path).read_text())
def csvrows(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))
def write_csv(path,records):
    fields=list(dict.fromkeys(k for r in records for k in r))
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in records:writer.writerow({k:json.dumps(v,separators=(',',':'),allow_nan=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})

def beta_cf(a,b,x):
    tiny=1e-300;qab=a+b;qap=a+1;qam=a-1;c=1.;d=1-qab*x/qap
    if abs(d)<tiny:d=tiny
    d=1/d;h=d
    for m in range(1,2001):
        m2=2*m;aa=m*(b-m)*x/((qam+m2)*(a+m2));d=1+aa*d
        if abs(d)<tiny:d=tiny
        c=1+aa/c
        if abs(c)<tiny:c=tiny
        d=1/d;h*=d*c;aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));d=1+aa*d
        if abs(d)<tiny:d=tiny
        c=1+aa/c
        if abs(c)<tiny:c=tiny
        d=1/d;change=d*c;h*=change
        if abs(change-1)<3e-14:return h
    raise ValueError('INCOMPLETE_BETA_DID_NOT_CONVERGE')

def beta_cdf(x,a,b):
    if x<=0:return 0.
    if x>=1:return 1.
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return bt*beta_cf(a,b,x)/a if x<(a+1)/(a+b+2) else 1-bt*beta_cf(b,a,1-x)/b

def beta_quantile(probability,a,b):
    demand(0<probability<1 and a>0 and b>0,'INVALID_BETA_QUANTILE')
    lo=0.;hi=1.
    for _ in range(180):
        mid=(lo+hi)/2
        if beta_cdf(mid,a,b)<probability:lo=mid
        else:hi=mid
        if hi-lo<2e-15*max(mid,1e-12):break
    return (lo+hi)/2

def binomial_intervals(k,n,confidence=CONFIDENCE):
    demand(isinstance(k,int) and isinstance(n,int) and not isinstance(k,bool) and not isinstance(n,bool) and n>0 and 0<=k<=n and 0<confidence<1,'INVALID_BINOMIAL_COHORT')
    alpha=1-confidence;p=k/n;z=statistics.NormalDist().inv_cdf((1+confidence)/2);den=1+z*z/n;center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    lower=0. if k==0 else beta_quantile(alpha/2,k,n-k+1)
    upper=1. if k==n else beta_quantile(1-alpha/2,k+1,n-k)
    return {'N':n,'k':k,'confidence':confidence,'acceptance':p,'raw_binomial_SE':math.sqrt(p*(1-p)/n),'wilson_lower':0. if k==0 else max(0.,center-half),'wilson_upper':1. if k==n else min(1.,center+half),'lower':lower,'upper':upper,'one_sided95_upper_if_zero':-math.expm1(math.log(.05)/n) if k==0 else None,'interpretation':'IID_PROPOSAL_ACCEPTANCE; not physical cross-section/fake calibration interval'}

def required_campaign(probability,target):
    if probability<=0:return None
    q=Decimal(str(probability));r=Decimal(str(target))
    return max(2,int(((1-q)/(q*r*r)).to_integral_value(rounding=ROUND_CEILING)))

def planning(interval,target):
    demand(0<target<1,'INVALID_PRECISION_TARGET')
    p=interval['acceptance'];lo=interval['lower'];hi=interval['upper'];required=lambda q:required_campaign(q,target)
    return {'target_relative_SE':target,'point_acceptance':p if interval['k'] else None,'required_new_independent_campaign_N_at_point':required(p) if interval['k'] else None,'optimistic_N_at_CP95_upper_acceptance':required(hi),'conservative_N_at_CP95_lower_acceptance':required(lo),'planning_status':'NO_FINITE_MEASURED_PLANNING_GUARANTEE_ZERO_SURVIVORS' if not interval['k'] else 'ASSUMPTION_DEPENDENT_PLANNING_ESTIMATE','assumptions':'Future IID source proposal and fixed selection identical; unweighted Bernoulli acceptance; asymptotic relative-SE target, not guaranteed precision or a physical fake-yield estimate. CP95 envelope describes pilot acceptance uncertainty, not a coverage claim for future achieved precision.'}

def execute(source,previous,output):
    source=Path(source).resolve();previous=Path(previous).resolve();output=Path(output).resolve();demand(not output.exists(),'DIAGNOSTICS_OUTPUT_MUST_BE_FRESH');demand(previous not in output.parents,'NO_WRITES_INSIDE_HISTORICAL_OUTPUT')
    datasets={d['dataset_id']:d for d in load(previous/'phase8_local_manifest.json')['datasets']};edges=load(source/'analysis/phase8/config/histogram_edges_v1.json')['observables'];cohorts=defaultdict(list)
    eventfile=previous/'native/phase8_events.jsonl'
    for line in eventfile.open():
        e=json.loads(line);demand(e['dataset_id'] in datasets,'UNKNOWN_DATASET');cohorts[e['dataset_id']].append(e)
    demand(set(cohorts)==set(datasets),'MISSING_COHORT');demand(sum(len(v) for v in cohorts.values())==7100,'NOT_7100_INDEPENDENT_ORIGINAL_SOURCES')
    for did,events in cohorts.items():
        ds=datasets[did];demand(len(events)==ds['N_original'],'ORIGINAL_N_MISMATCH');demand(len({(e['source_event_ordinal'],e['source_event_sha256']) for e in events})==len(events),'DUPLICATE_SOURCE_IDENTITY')
        demand([sum(e['stages'][i] for e in events) for i in range(5)]==ds['expected_cutflow'],'BASELINE_CUTFLOW_CHANGED')
    rare=[];plans=[];tails=[];binquality=[];cutflows=[];allh=[];histcache={};cases={};regionrows=[];regionobs=[];regiongroups={};closures=[];tag_comp=[]
    for did,events in cohorts.items():
        ds=datasets[did];n=ds['N_original'];br=ds['model_br_factor']
        for i,stage in enumerate(STAGES):
            selected=[e for e in events if e['stages'][i]];summary=weight_summary(selected,n);inter=binomial_intervals(len(selected),n);cases[n,len(selected)]=inter
            rare.append({'dataset_id':did,'stage':stage,**inter,'source_sumw_pb':summary['sumw'],'source_sumw2_pb2':summary['sumw2'],'fixed_original_N_sampling_variance_pb2':summary['fixed_N_variance'],'weighted_source_MC_SE_pb':math.sqrt(summary['fixed_N_variance']),'weighted_source_relative_SE':summary['relative_sampling_SE'],'MODEL_BR_ONLY_sumw_pb':summary['sumw']*br,'MODEL_BR_ONLY_sampling_SE_pb':math.sqrt(summary['fixed_N_variance'])*br,'model_BR_factor':br,'BR_applications':ds['BR_factor_applications'],'ESS':summary['ESS'],'largest_source_abs_fraction':summary['largest_fraction'],'top5_source_abs_fraction':summary['top5_fraction'],'weight_scope':'XWGTUP_pb/original_N once; MODEL_BR_ONLY own factor once','integration_error_combined':False,'zero_survivors_prove_zero_background':False})
            cutflows.append({'dataset_id':did,'stage':stage,'N':len(selected),'N_original':n,'efficiency':len(selected)/n,'wilson_lower':inter['wilson_lower'],'wilson_upper':inter['wilson_upper'],'exact_lower':inter['lower'],'exact_upper':inter['upper']})
            tails.append({'dataset_id':did,'stage':stage,**summary,'interpretation':'Observed source proposal plus realized shower/detector; pure generator and detector components not independently identifiable from one realization.'})
            for observable in OBSERVABLES:
                h=histogram(selected,observable,edges[observable]['edges'],n);h.update(dataset_id=did,stage=stage,tag_region='ALL',mass_region='ALL',unit=edges[observable]['unit']);histcache[did,stage,observable]=h
                for ib,b in enumerate([h['underflow']]+h['bins']+[h['overflow']]):
                    binquality.append({'dataset_id':did,'stage':stage,'observable':observable,'bin':ib,'flow':'UNDERFLOW' if ib==0 else 'OVERFLOW' if ib==len(h['bins'])+1 else 'REGULAR','N_original':n,'N_sources':b['N'],'ESS':b['ESS'],'largest_source_abs_fraction':b['largest_fraction'],'quality_flag':b['quality_flag'],'sumw':b['sumw'],'sumw2':b['sumw2'],'source_fixed_N_variance':b['source_variance'],'normalized_value':b['value'],'normalized_fixed_N_delta_variance':b['variance'],'missing_observable':h['missing']})
                if i in (0,4):allh.append(h)
            if i==4:
                for target in TARGET_RELATIVE_SE:
                    plans.append({'dataset_id':did,'stage':stage,**planning(inter,target)})
                    if len(selected)==0:
                        for divisor in (1,10,100):
                            assumed=inter['one_sided95_upper_if_zero']/divisor
                            plans.append({'dataset_id':did,'stage':stage,'target_relative_SE':target,'point_acceptance':None,'assumed_acceptance':assumed,'required_new_independent_campaign_N_at_assumed_acceptance':required_campaign(assumed,target),'planning_status':'EXPLICIT_HYPOTHETICAL_ACCEPTANCE_SCENARIO_ONLY','assumptions':'Assume p equals one-sided95 zero-survivor upper bound divided by '+str(divisor)+'; this is not measured p or guaranteed N, and does not calibrate photon fake rates.'})
        eligible=[e for e in events if e['stages'][2]];parts=defaultdict(list)
        for event in eligible:parts[region_key(event)].append(event)
        for tag in ('TAG_0','TAG_1','TAG_GE2'):
            tagged=[e for e in eligible if ('TAG_0' if e['native_btag_multiplicity']==0 else 'TAG_1' if e['native_btag_multiplicity']==1 else 'TAG_GE2')==tag]
            ts=weight_summary(tagged,n);tag_comp.append({'dataset_id':did,'stage':STAGES[2],'tag_region':tag,'N':len(tagged),'N_eligible':len(eligible),'source_sumw_pb':ts['sumw'],'fixed_N_variance_pb2':ts['fixed_N_variance'],'ESS':ts['ESS']})
            for mass in ('LOW','HIGGS','HIGH','OUTSIDE_MGG','UNDEFINED_MGG'):
                part=parts[tag,mass];ws=weight_summary(part,n);regiongroups[did,tag,mass]=part
                regionrows.append({'dataset_id':did,'stage':STAGES[2],'tag_region':tag,'mass_region':mass,'N_original':n,'N_eligible':len(eligible),'N_region':len(part),'source_sumw_pb':ws['sumw'],'source_sumw2_pb2':ws['sumw2'],'fixed_N_variance_pb2':ws['fixed_N_variance'],'MODEL_BR_ONLY_sumw_pb':ws['sumw']*br,'MODEL_BR_ONLY_variance_pb2':ws['fixed_N_variance']*br*br,'ESS':ws['ESS'],'largest_source_abs_fraction':ws['largest_fraction'],'top5_source_abs_fraction':ws['top5_fraction'],'mbb_definition':'OBSERVED_LEADING_TWO_NATIVE_TAGGED_ELIGIBLE_JETS' if tag=='TAG_GE2' else 'UNDEFINED_NO_TWO_TAG_PAIR','weight_scope':'RAW_SOURCE_AND_OWN_MODEL_BR_ONLY; no physical combined background'})
                for observable in OBSERVABLES:regionobs.append({'dataset_id':did,'stage':STAGES[2],'tag_region':tag,'mass_region':mass,'observable':observable,'unit':edges[observable]['unit'],**weighted_mean(part,observable,n)})
        partition_n=sum(len(v) for v in parts.values());partition_w=math.fsum(e['source_weight_pb'] for part in parts.values() for e in part);eligible_w=math.fsum(e['source_weight_pb'] for e in eligible)
        demand(partition_n==len(eligible) and math.isclose(partition_w,eligible_w,rel_tol=1e-14,abs_tol=1e-28),'REGION_COUNT_OR_SUMW_CLOSURE_FAILURE')
        closures.append({'dataset_id':did,'N_eligible':len(eligible),'N_partition':partition_n,'sumw_eligible':eligible_w,'sumw_partition':partition_w,'status':'PASS_EXCLUSIVE_EVENT_COUNT_AND_SOURCE_SUMW'})
    # Independent exact reference cases include pilot and small edge cases for ROOT cross-check.
    for n,k in ((1000,0),(1000,1),(1000,143),(1000,1000),(1,0),(1,1),(10,0),(10,1),(10,5),(10,10)):
        cases[n,k]=binomial_intervals(k,n)
    shapes=[];ratios=[]
    signal='S01_C1000'
    def compare(did,observable,stage,tag,mass,a,b):
        metrics=shape_metrics(a,b);shapes.append({'signal_dataset':signal,'background_dataset':did,'stage':stage,'tag_region':tag,'mass_region':mass,'observable':observable,'signal_N_defined':a['N_defined'],'background_N_defined':b['N_defined'],'signal_ESS':a['ESS'],'background_ESS':b['ESS'],'signal_largest_fraction':a['largest_fraction'],'background_largest_fraction':b['largest_fraction'],**{k:v for k,v in metrics.items() if k!='ratio_bins'}})
        for item in metrics['ratio_bins']:ratios.append({'signal_dataset':signal,'background_dataset':did,'stage':stage,'tag_region':tag,'mass_region':mass,'observable':observable,**item})
    for did in ('B01','B02','B03','B04','B05','B06'):
        for observable in OBSERVABLES:
            compare(did,observable,STAGES[4],'ALL','ALL',histcache[signal,STAGES[4],observable],histcache[did,STAGES[4],observable])
            for tag in ('TAG_0','TAG_1','TAG_GE2'):
                for mass in ('LOW','HIGGS','HIGH','OUTSIDE_MGG','UNDEFINED_MGG'):
                    a=histogram(regiongroups[signal,tag,mass],observable,edges[observable]['edges'],datasets[signal]['N_original']);b=histogram(regiongroups[did,tag,mass],observable,edges[observable]['edges'],datasets[did]['N_original'])
                    compare(did,observable,STAGES[2],tag,mass,a,b)
    # Kappa is frozen reweighting of C1000, not new matrix-element work or new sources.
    kpath=source/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv';kw=defaultdict(list);original={e['source_event_ordinal']:e for e in cohorts[signal]}
    for row in csvrows(kpath):
        ordinal=int(row['source_event_index']);demand(original[ordinal]['source_event_sha256']==row['source_event_sha256'],'KAPPA_SOURCE_HASH_MISMATCH')
        kw[row['kappa_lambda']].append({'source_event_ordinal':ordinal,'source_event_sha256':row['source_event_sha256'],'source_weight_pb':float(row['MODEL_BR_ONLY_weight_pb']),'final_selected':original[ordinal]['stages'][4]})
    kappas=[];concentration=[]
    for k in ('-1','0','1','2','2.5','5'):
        events=kw[k];demand(len(events)==1000,'KAPPA_ROWS_ARE_NOT_1000_SHARED_SOURCES');initial=weight_summary(events,1000);final=weight_summary([e for e in events if e['final_selected']],1000);kappas.append({'kappa_lambda':float(k),'source_ESS':initial['ESS'],'final_ESS':final['ESS'],'top1_abs_fraction':initial['largest_fraction'],'top5_abs_fraction':initial['top5_fraction'],'top10_abs_fraction':initial['top10_fraction'],'final_top1_abs_fraction':final['largest_fraction'],'status':'INCONCLUSIVE_REWEIGHTING' if k in ('2.5','5') else 'VALID_DESCRIPTIVE_ONLY'})
        ordered=sorted(events,key=lambda e:(-abs(e['source_weight_pb']),e['source_event_ordinal']));cumulative=0.
        for rank,event in enumerate(ordered,1):
            fraction=abs(event['source_weight_pb'])/initial['sum_absw'];cumulative+=fraction;concentration.append({'kappa_lambda':float(k),'rank':rank,'source_event_ordinal':event['source_event_ordinal'],'source_event_sha256':event['source_event_sha256'],'abs_weight_fraction':fraction,'cumulative_abs_fraction':cumulative,'final_selected':event['final_selected']})
    output.mkdir(parents=True)
    for name,data in [('phase9_rare_event_precision.csv',rare),('phase9_mc_planning.csv',plans),('phase9_source_tail_support.csv',tails),('phase9_bin_quality.csv',binquality),('phase9_region_diagnostics.csv',regionrows),('phase9_region_observables.csv',regionobs),('phase9_shape_metrics.csv',shapes),('phase9_shape_ratios.csv',ratios),('phase9_kappa_support.csv',kappas)]:write_csv(output/name,data)
    plot={'schema_version':1,'stage_map':dict(zip(('INPUT','PHOTONS','JETS','TWO_BTAGS','FINAL_MGG'),STAGES)),'histograms':allh,'cutflows':cutflows,'tag_composition':tag_comp,'regions':regionrows,'kappa_summary':kappas,'kappa_weight_concentration':concentration,'physical_total_background':'BLOCKED','physical_significance':'NOT_EVALUATED','physical_CLs':'NOT_EVALUATED','normalization':'UNIT_AREA_FIXED_N_DELTA; no luminosity assumption','uncertainty':'Fixed original-N empirical source sampling; normalized shape includes bin-total covariance; empty zero estimator is not zero true rate.'}
    (output/'phase9_plot_data.json').write_text(json.dumps(plot,indent=2,allow_nan=False)+'\n')
    (output/'phase9_binomial_reference.json').write_text(json.dumps({'schema_version':1,'method':'Independent incomplete-beta continued fraction and bisection; central Clopper-Pearson95 plus Wilson95','cases':[cases[key] for key in sorted(cases)]},indent=2,allow_nan=False)+'\n')
    (output/'phase9_region_closure.json').write_text(json.dumps(closures,indent=2,allow_nan=False)+'\n')
    manifest={'status':'PASS_EXISTING_SOURCE_DIAGNOSTICS_WITH_PHYSICAL_BLOCKERS','evidence_class':'HISTORICAL_EVIDENCE_AUDIT_AND_INDEPENDENT_PERSISTED_EVENT_NUMERICAL_ANALYSIS','independent_source_events':7100,'additional_independent_sources':0,'actual_fresh_ROOT_dispatches_in_this_script':0,'cohorts':{d:len(e) for d,e in cohorts.items()},'baseline_selection_changed':False,'ROOT_reference_check':'SEPARATE_NATIVE_ORCHESTRATOR_RECEIPT_REQUIRED','histograms':len(allh),'region_rows':len(regionrows),'region_observable_rows':len(regionobs),'shape_rows':len(shapes),'bin_quality_rows':len(binquality),'rare_event_rows':len(rare),'planning_rows':len(plans),'binomial_reference_cases':len(cases),'source_inputs':{'Phase8_event_summary':sha(eventfile),'Phase8_local_manifest':sha(previous/'phase8_local_manifest.json'),'histogram_edges_v1':sha(source/'analysis/phase8/config/histogram_edges_v1.json'),'regions_v1':sha(source/'analysis/phase8/config/regions_v1.json'),'frozen_kappa_csv':sha(kpath)},'outputs':{p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()},'new_ME_calls':0,'new_integrals':0,'new_events':0,'physical_total_background':'BLOCKED','physical_significance':'NOT_EVALUATED','physical_CLs':'NOT_EVALUATED'}
    (output/'phase9_statistics_manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n');return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--phase8-results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=execute(a.source,a.phase8_results,a.output);print(json.dumps(result,indent=2));return 0

if __name__=='__main__':raise SystemExit(main())