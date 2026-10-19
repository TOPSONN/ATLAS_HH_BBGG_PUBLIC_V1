#!/usr/bin/env python3
"""Fixed-original-N statistics and Phase8-preserving descriptive region primitives."""
from collections import Counter
import bisect
import math
import statistics

OBSERVABLES=('m_gamma_gamma','m_bb','m_HH','DeltaR_bb','DeltaR_gamma_gamma','diphoton_pT','dijet_pT','reconstructed_jet_multiplicity','native_btag_multiplicity')
STAGES=('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')

def demand(ok,reason):
    if not ok:raise ValueError(reason)

def fixed_n_variance(values,n):
    demand(isinstance(n,int) and n>1 and len(values)<=n,'INVALID_ORIGINAL_COHORT')
    demand(all(math.isfinite(x) for x in values),'NONFINITE_CONTRIBUTION')
    mean=math.fsum(values)/n
    return n/(n-1)*math.fsum([(x-mean)**2 for x in values]+[(n-len(values))*mean*mean])

def weight_summary(events,n,weight_key='source_weight_pb'):
    w=[float(e[weight_key]) for e in events];s=math.fsum(w);s2=math.fsum(x*x for x in w);a=math.fsum(abs(x) for x in w)
    order=sorted(events,key=lambda e:(-abs(float(e[weight_key])),e['source_event_ordinal']))
    conditioned=a>0 and abs(s)>64*math.ulp(1.)*a
    return {'N_original':n,'N_selected':len(events),'sumw':s,'sumw2':s2,'sum_absw':a,'fixed_N_variance':fixed_n_variance(w,n),'ESS':s*s/s2 if s2 else None,'largest_fraction':abs(float(order[0][weight_key]))/a if a else None,'top5_fraction':math.fsum(abs(float(e[weight_key])) for e in order[:5])/a if a else None,'top10_fraction':math.fsum(abs(float(e[weight_key])) for e in order[:10])/a if a else None,'negative_count':sum(x<0 for x in w),'cancellation_ratio':abs(s)/a if a else None,'relative_sampling_SE':math.sqrt(fixed_n_variance(w,n))/abs(s) if conditioned else None,'conditioned_denominator':conditioned,'dominant_sources':[{'source_event_ordinal':e['source_event_ordinal'],'source_event_sha256':e['source_event_sha256'],'abs_fraction':abs(float(e[weight_key]))/a} for e in order[:5]] if a else []}

def quality(n,ess,largest,cancellation):
    if n==0:return 'EMPTY_BIN'
    if cancellation is not None and cancellation<1e-3:return 'CANCELLATION_DOMINATED'
    if ess is None:return 'UNDEFINED_ESS'
    if ess<10:return 'LOW_ESS_LT10'
    if ess<20:return 'LOW_ESS_LT20'
    if largest is not None and largest>.2:return 'HIGH_SINGLE_EVENT_DOMINANCE'
    return 'VALID_DESCRIPTIVE_ONLY'

def weighted_mean(events,observable,n):
    defined=[]
    for e in events:
        value=e['observables'][observable]
        demand(value is None or math.isfinite(value),'NONFINITE_OBSERVABLE')
        if value is not None:defined.append((e,float(value)))
    ws=weight_summary([e for e,x in defined],n); result={'N_defined':len(defined),'missing':len(events)-len(defined),'invalid':0,'mean':None,'mean_variance':None,'mean_SE':None,'unweighted_median':None,'min':None,'max':None,'ESS':ws['ESS'],'largest_fraction':ws['largest_fraction']}
    if defined:
        values=[x for e,x in defined];result.update(unweighted_median=statistics.median(values),min=min(values),max=max(values))
    if not ws['conditioned_denominator']:result['status']='UNDEFINED_EMPTY_OR_CANCELLATION';return result
    mean=math.fsum(e['source_weight_pb']*x for e,x in defined)/ws['sumw']
    influence=[e['source_weight_pb']*(x-mean) for e,x in defined]
    variance=fixed_n_variance(influence,n)/(ws['sumw']**2)
    result.update(mean=mean,mean_variance=variance,mean_SE=math.sqrt(variance),status='DEFINED_DESCRIPTIVE_FIXED_N_DELTA');return result

def histogram(events,observable,edges,n):
    demand(len(edges)>=2 and all(math.isfinite(x) for x in edges) and all(a<b for a,b in zip(edges,edges[1:])),'INVALID_EDGES')
    buckets=[[] for _ in range(len(edges)+1)];defined=[];missing=0
    for event in events:
        x=event['observables'][observable]
        if x is None:missing+=1;continue
        demand(math.isfinite(x),'NONFINITE_OBSERVABLE')
        index=bisect.bisect_right(edges,x);buckets[index].append(event);defined.append((event,index))
    ws=weight_summary([e for e,b in defined],n)
    result={'observable':observable,'edges':edges,'N_original':n,'N_defined':len(defined),'N_selected':len(events),'missing':missing,'invalid':0,'normalization':'UNIT_AREA_FIXED_N_DELTA','flow_policy':'INCLUDE_UNDERFLOW_AND_OVERFLOW_IN_DENOMINATOR','weight_scope':'RAW_SOURCE_SHAPE; constant per-dataset MODEL_BR factor cancels','sumw':ws['sumw'],'sumw2':ws['sumw2'],'sum_absw':ws['sum_absw'],'ESS':ws['ESS'],'largest_fraction':ws['largest_fraction'],'status':'DEFINED_DESCRIPTIVE' if ws['conditioned_denominator'] else 'UNDEFINED_EMPTY_OR_CANCELLATION','error_interpretation':'Fixed original-N delta variance including bin-total covariance; zero empirical empty-bin variance is not a physical zero-background statement.','bins':[],'underflow':None,'overflow':None}
    def one(index):
        events_in_bin=buckets[index];b=weight_summary(events_in_bin,n);fraction=b['sumw']/ws['sumw'] if ws['conditioned_denominator'] else None
        variance=None
        if fraction is not None:
            influence=[e['source_weight_pb']*((1 if where==index else 0)-fraction) for e,where in defined]
            variance=fixed_n_variance(influence,n)/(ws['sumw']**2)
        return {'low':edges[index-1] if index else None,'high':edges[index] if index<len(edges) else None,'value':fraction,'variance':variance,'N':len(events_in_bin),'ESS':b['ESS'],'largest_fraction':b['largest_fraction'],'sumw':b['sumw'],'sumw2':b['sumw2'],'source_variance':b['fixed_N_variance'],'quality_flag':quality(len(events_in_bin),b['ESS'],b['largest_fraction'],b['cancellation_ratio'])}
    result['underflow']=one(0);result['overflow']=one(len(edges));result['bins']=[one(i) for i in range(1,len(edges))]
    return result

def region_key(event):
    demand(event['stages'][2],'REGION_NOT_PHOTON_JET_ELIGIBLE')
    tags=event['native_btag_multiplicity'];tag='TAG_0' if tags==0 else 'TAG_1' if tags==1 else 'TAG_GE2'
    mass=event['observables']['m_gamma_gamma']
    region='UNDEFINED_MGG' if mass is None else 'LOW' if 105<=mass<120 else 'HIGGS' if 120<=mass<=130 else 'HIGH' if 130<mass<=160 else 'OUTSIDE_MGG'
    if tags<2:
        demand(event['observables']['m_bb'] is None and event['observables']['m_HH'] is None,'NULL_TAG_PAIR_CANDIDATE_VIOLATION')
    return tag,region

def shape_metrics(signal,background):
    bins=lambda h:[h['underflow']]+h['bins']+[h['overflow']]
    result={'status':'UNDEFINED_EMPTY_OR_CANCELLATION','JS_natural_log':None,'CDF_sup_distance':None,'inference':'DESCRIPTIVE_BINNED_METRIC_NOT_A_TEST_P_VALUE_OR_PHYSICAL_SENSITIVITY','ratio_bins':[]}
    if not signal['status'].startswith('DEFINED') or not background['status'].startswith('DEFINED'):return result
    a,b=bins(signal),bins(background);demand(signal['edges']==background['edges'],'SHAPE_EDGE_MISMATCH')
    if any(x['value']<0 for x in a+b):result['status']='UNSUPPORTED_SIGNED_PROBABILITY_SHAPE';return result
    terms=[];cdfa=0;cdfb=0;ks=0
    for i,(sa,ba) in enumerate(zip(a,b)):
        p,q=sa['value'],ba['value'];mid=.5*(p+q)
        if p>0:terms.append(.5*p*math.log(p/mid))
        if q>0:terms.append(.5*q*math.log(q/mid))
        cdfa+=p;cdfb+=q;ks=max(ks,abs(cdfa-cdfb))
        ratio=p/q if q>0 else None
        variance=(sa['variance']/q**2+p*p*ba['variance']/q**4) if q>0 else None
        result['ratio_bins'].append({'bin':i,'ratio':ratio,'variance_independent_dataset_delta':variance,'status':'UNDEFINED_ZERO_BACKGROUND_BIN' if q==0 else 'DESCRIPTIVE_INDEPENDENT_SOURCE_DATASETS_ONLY','signal_quality':sa['quality_flag'],'background_quality':ba['quality_flag']})
    result.update(status='DEFINED_DESCRIPTIVE_ONLY',JS_natural_log=math.fsum(terms),CDF_sup_distance=ks);return result