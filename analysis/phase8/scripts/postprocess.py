#!/usr/bin/env python3
"""Bounded existing-event region/shape summaries; never invokes a generator."""
import argparse,bisect,csv,hashlib,json,math,statistics,sys
from pathlib import Path
from collections import defaultdict
STAGES=['INPUT','PHOTONS','JETS','TWO_BTAGS','FINAL_MGG']
TAGS=['TAG_0','TAG_1','TAG_GE2']; MASSES=['LOW','HIGGS','HIGH','OUTSIDE_MGG','UNDEFINED_MGG']
def dump(p,j):
    with Path(p).open('x') as f: json.dump(j,f,indent=2,allow_nan=False);f.write('\n')
def table(p,rows):
    if not rows: raise ValueError('EMPTY_TABLE_NOT_EVIDENCE')
    with Path(p).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def mass_region(m):
    if m is None:return 'UNDEFINED_MGG'
    if not math.isfinite(m):raise ValueError('NONFINITE_MGG')
    if 105<=m<120:return 'LOW'
    if 120<=m<=130:return 'HIGGS'
    if 130<m<=160:return 'HIGH'
    return 'OUTSIDE_MGG'
def tag_region(n):
    if n<0 or int(n)!=n:raise ValueError('INVALID_TAG_MULTIPLICITY')
    return 'TAG_0' if n==0 else 'TAG_1' if n==1 else 'TAG_GE2'
def summary(x,n):
    if n<2 or len(x)>n or any(not math.isfinite(v) for v in x):raise ValueError('INVALID_WEIGHT_COHORT')
    y=list(x)+[0.]*(n-len(x));s=math.fsum(y);q=math.fsum(v*v for v in y);a=math.fsum(abs(v) for v in y)
    origin=y[0];mean=math.fsum(v-origin for v in y)/n
    v=math.fsum(((z-origin)-mean)**2 for z in y)*n/(n-1)
    return dict(sumw=s,sumw2=q,sum_absw=a,fixed_N_variance=v,ESS=s*s/q if q else None,largest_fraction=max(map(abs,y))/a if a else None,cancellation_ratio=abs(s)/a if a else None)
def groups(events):
    out=defaultdict(list)
    for e in events:out[e['dataset_id']].append(e)
    for k,ev in out.items():
        if any(e['N_original']!=len(ev) or type(e['source_event_ordinal']) is not int for e in ev) or {e['source_event_ordinal'] for e in ev}!=set(range(1,len(ev)+1)):raise ValueError('INCOMPLETE_OR_DUPLICATE_COHORT:'+k)
        ev.sort(key=lambda e:e['source_event_ordinal'])
    return out

def wilson(k,n):
    z=1.959963984540054;den=1+z*z/n;center=(k/n+z*z/(2*n))/den;half=z*math.sqrt((k/n)*(1-k/n)/n+z*z/(4*n*n))/den
    return max(0.,center-half),min(1.,center+half)
def moments(cohort,key):
    v=[e['observables'][key] for e in cohort if e['observables'][key] is not None]
    return (statistics.mean(v) if v else None,len(cohort)-len(v))
def regions(g,manifest):
    rows=[];closure=[]
    for ds,ev in g.items():
        eligible=[e for e in ev if e['stages'][2]];factor=manifest[ds]['model_br_factor']; buckets={(t,m):[] for t in TAGS for m in MASSES}
        for e in eligible:buckets[tag_region(e['native_btag_multiplicity']),mass_region(e['observables']['m_gamma_gamma'])].append(e)
        for (t,m),cohort in buckets.items():
            s=summary([e['source_weight_pb'] for e in cohort],len(ev));sm=summary([e['source_weight_pb']*factor for e in cohort],len(ev))
            mean_gg,missing_gg=moments(cohort,'m_gamma_gamma');mean_bb,missing_bb=moments(cohort,'m_bb');mean_hh,missing_hh=moments(cohort,'m_HH');lo,hi=wilson(len(cohort),len(ev));den=math.fsum(e['source_weight_pb'] for e in eligible)
            rows.append(dict(mean_mgg=mean_gg,mean_mbb_when_defined=mean_bb,mean_mHH_when_defined=mean_hh,mean_scope='UNWEIGHTED_DESCRIPTIVE_OF_DEFINED_ACTUAL_CANDIDATES',missing_mgg=missing_gg,missing_mbb=missing_bb,missing_mHH=missing_hh,weighted_efficiency_relative_to_photon_jet=s['sumw']/den if den else None,proposal_efficiency=len(cohort)/len(ev),proposal_Wilson95_low=lo,proposal_Wilson95_high=hi,dataset_id=ds,tag_region=t,mass_region=m,N_original=len(ev),N_photon_jet_eligible=len(eligible),N_region=len(cohort),**s,sumw_MODEL_BR_ONLY=sm['sumw'],model_BR_factor=factor,BR_applications=int(factor!=1),mbb_definition='LEADING_TWO_ACTUAL_TAGGED_JETS' if t=='TAG_GE2' else 'UNDEFINED_NO_TWO_TAG_PAIR',physical_scope='EXPLORATORY_NOT_OFFICIAL_ATLAS',zero_one_sided95_proposal_upper=-math.expm1(math.log(.05)/len(ev)) if not cohort else None))
        expected=math.fsum(e['source_weight_pb'] for e in eligible);actual=math.fsum(r['sumw'] for r in rows if r['dataset_id']==ds)
        abs_sum=math.fsum(abs(e['source_weight_pb']) for e in eligible);tolerance=32*sys.float_info.epsilon*max(1,len(eligible))*abs_sum
        count=sum(len(x) for x in buckets.values())
        if count!=len(eligible) or abs(actual-expected)>tolerance:raise ValueError('REGION_PARTITION_CLOSURE_FAILED:'+ds)
        closure.append(dict(dataset_id=ds,N_partition=count,N_eligible=len(eligible),sumw_partition=actual,sumw_eligible=expected,absolute_tolerance=tolerance,status='PASS_EXCLUSIVE_COUNT_AND_SUMW_CLOSURE'))
    return rows,closure

def shape(x,edges,n):
    bins=[[] for _ in range(len(edges)+1)]
    for value,w in x:bins[bisect.bisect_right(edges,value)].append(w)
    sums=[math.fsum(b) for b in bins];total=math.fsum(sums);a=math.fsum(abs(w) for _,w in x)
    if not a or abs(total)<=64*sys.float_info.epsilon*a:return None,bins
    return [v/total for v in sums],bins

def shape_variance(bins,normalized,n):
    if normalized is None:return [None]*len(bins)
    total=math.fsum(v for cell in bins for v in cell);q=[math.fsum(v*v for v in cell) for cell in bins]
    return [n/(n-1)*((1-p)**2*q[k]+p*p*math.fsum(v for j,v in enumerate(q) if j!=k))/(total*total) for k,p in enumerate(normalized)]
def comparisons(g,edges):
    rows=[];signal=g.get('S01_C1000',[])
    for ds,ev in g.items():
        if not ds.startswith('B'):continue
        for stage_i,stage in enumerate(STAGES):
            for obs,definition in edges.items():
                e=definition['edges'];a=[(v['observables'][obs],v['source_weight_pb']) for v in signal if v['stages'][stage_i] and v['observables'][obs] is not None];b=[(v['observables'][obs],v['source_weight_pb']) for v in ev if v['stages'][stage_i] and v['observables'][obs] is not None]
                pa,ba=shape(a,e,len(signal));pb,bb=shape(b,e,len(ev));va=shape_variance(ba,pa,len(signal));vb=shape_variance(bb,pb,len(ev));status='VALID_DESCRIPTIVE_ONLY'
                tv=ks=overlap=None
                if pa is None or pb is None:status='UNDEFINED_EMPTY_OR_ILL_CONDITIONED_SHAPE'
                elif min(pa+pb)<0:status='SIGNED_SHAPE_METRICS_UNDEFINED'
                else:
                    tv=.5*math.fsum(abs(x-y) for x,y in zip(pa,pb));overlap=math.fsum(min(x,y) for x,y in zip(pa,pb));cs=cb=ks=0.
                    for x,y in zip(pa,pb):cs+=x;cb+=y;ks=max(ks,abs(cs-cb))
                for bin_i in range(len(e)+1):
                    qa=summary(ba[bin_i],len(signal));qb=summary(bb[bin_i],len(ev));ratio=None if pa is None or pb is None or pb[bin_i]==0 else pa[bin_i]/pb[bin_i]
                    flags=[]
                    for label,z in [('SIGNAL',qa),('BACKGROUND',qb)]:
                        if z['ESS'] is None:flags.append(label+'_EMPTY_BIN')
                        elif z['ESS']<10:flags.append(label+'_LOW_ESS_LT10')
                        elif z['ESS']<20:flags.append(label+'_LOW_ESS_LT20')
                        if z['largest_fraction'] is not None and z['largest_fraction']>.1:flags.append(label+'_HIGH_SINGLE_EVENT_DOMINANCE')
                    rows.append(dict(signal='S01_C1000',background=ds,stage=stage,observable=obs,bin=bin_i,flow='UNDERFLOW' if bin_i==0 else 'OVERFLOW' if bin_i==len(e) else 'REGULAR',signal_shape_variance_fixed_N=va[bin_i],background_shape_variance_fixed_N=vb[bin_i],shape_variance_method='DELTA_METHOD_BIN_TOTAL_COVARIANCE_COMMON_ORIGINAL_N',signal_shape=None if pa is None else pa[bin_i],background_shape=None if pb is None else pb[bin_i],signal_over_background_shape_ratio=ratio,signal_ESS=qa['ESS'],background_ESS=qb['ESS'],signal_contributing_sources=len(ba[bin_i]),background_contributing_sources=len(bb[bin_i]),total_variation=tv,binned_cumulative_distance=ks,overlap_coefficient=overlap,quality_flags='|'.join(flags),status=status,metric_scope='DESCRIPTIVE_FIXED_BINS_NO_PHYSICAL_SIGNIFICANCE_NO_PVALUE'))
    return rows

def variants(g):
    rows=[]
    rules={'BASELINE':lambda o:True,'MBB_100_150':lambda o:o['m_bb'] is not None and 100<=o['m_bb']<=150,'DIPHOTON_PT_GT100':lambda o:o['diphoton_pT'] is not None and o['diphoton_pT']>100,'DR_BB_LT1_5':lambda o:o['DeltaR_bb'] is not None and o['DeltaR_bb']<1.5,'MHH_LT350':lambda o:o['m_HH'] is not None and o['m_HH']<350,'MHH_350_500':lambda o:o['m_HH'] is not None and 350<=o['m_HH']<500,'MHH_GE500':lambda o:o['m_HH'] is not None and o['m_HH']>=500}
    for ds,ev in g.items():
        final=[e for e in ev if e['stages'][4]]
        for label,rule in rules.items():
            accepted=[e for e in final if rule(e['observables'])];s=summary([e['source_weight_pb'] for e in accepted],len(ev))
            rows.append(dict(dataset_id=ds,variant=label,N_original=len(ev),N_baseline=len(final),N_variant=len(accepted),**s,scope='PREDECLARED_IN_SAMPLE_DESCRIPTIVE_NOT_OPTIMIZATION',physical_objective=None))
    return rows
SYSTEMATICS=[('luminosity','LOGNORMAL','ALL_PHYSICAL_YIELDS'),('photon_ID','LOGNORMAL','PHOTON_OBJECTS'),('photon_trigger','LOGNORMAL','PHOTON_OBJECTS'),('photon_energy_scale','SHAPE','M_GAMMA_GAMMA'),('photon_energy_resolution','SHAPE','M_GAMMA_GAMMA'),('JES','SHAPE','JETS'),('JER','SHAPE','JETS'),('b_tag_efficiency','SHAPE_AND_RATE','HF_JETS'),('light_mistag','SHAPE_AND_RATE','LIGHT_JETS'),('charm_mistag','SHAPE_AND_RATE','CHARM_JETS'),('pileup','SHAPE_AND_RATE','EVENT'),('PDF','CORRELATED_VARIATION','GENERATOR'),('muR','SCALE_VARIATION','GENERATOR'),('muF','SCALE_VARIATION','GENERATOR'),('generator_model','ALTERNATIVE_MODEL','SOURCE'),('parton_shower','ALTERNATIVE_MODEL','SHOWER'),('Higgs_BR','CORRELATED_RATE','MODEL_BR_ONLY'),('background_normalization','CONSTRAINED_RATE','BACKGROUND'),('heavy_flavour_overlap','DEFINITION_GATE','B01_B02_B03'),('photon_fake','CALIBRATED_TRANSFER_MODEL','B06'),('finite_MC_statistics','EVENT_COVARIANCE','PER_BIN'),('kappa_support','SOURCE_SUPPORT_GATE','SHARED_C1000')]
def systematics():
    return [dict(nuisance_name=k,future_data_requirement='Independent calibrated sources and reviewed correlations before physical inference',nuisance=k,implementation_type=t,scope=s,affected_processes='ALL_OR_DECLARED_SCOPE',affected_observables='OBJECT_AND_RATE_DEPENDENT',rate_or_shape=t,actual_source='ACTUAL_EVENT_MC_DIAGNOSTICS' if k=='finite_MC_statistics' else 'NONE_APPROVED_FOR_PHYSICAL_USE',numerical_value=None,uncertainty_unit=None,correlation_scope=None,availability='METHOD_ONLY' if k in ['finite_MC_statistics','kappa_support'] else 'UNKNOWN',validation_level='DESCRIPTIVE_METHOD_ONLY',blocking_reason='No official calibration, physical overlap/fake model or sufficient common-source support',future_requirement='Independent calibrated sources and reviewed nuisance correlations before physical inference',physical_value=None,physical_constraint=None,correlation_model=None,readiness='COMPUTED_EVENT_DIAGNOSTICS_NOT_OFFICIAL_NUISANCE' if k=='finite_MC_statistics' else 'BLOCKED_LOW_SUPPORT_2_5_5' if k=='kappa_support' else 'BLOCKED_OVERLAP_DEFINITION' if k=='heavy_flavour_overlap' else 'BLOCKED_MISSING_FAKE_CALIBRATION' if k=='photon_fake' else 'UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED',toy_value_used_for_physical_data=False,official_ATLAS_calibration=False) for k,t,s in SYSTEMATICS]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--events',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--edges',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('REFUSE_EXISTING_OUTPUT_DIRECTORY')
    ev=[json.loads(x) for x in a.events.read_text().splitlines()];g=groups(ev);m={d['dataset_id']:d for d in json.loads(a.manifest.read_text())['datasets']};ed=json.loads(a.edges.read_text())['observables']
    rows,closure=regions(g,m);sh=comparisons(g,ed);vr=variants(g);a.output.mkdir();table(a.output/'phase8_control_regions.csv',rows);dump(a.output/'phase8_region_closure.json',closure);table(a.output/'phase8_shape_comparisons.csv',sh);table(a.output/'phase8_shape_variants.csv',vr);table(a.output/'phase8_systematics_readiness.csv',systematics())
    templ={'schema_version':1,'evidence_scope':'EXISTING_FAST_SIM_DESCRIPTIVE_TEMPLATES_ONLY','physical_likelihood':'BLOCKED_OVERLAP_FAKE_CALIBRATION_AND_SYSTEMATICS','physical_significance':'NOT_EVALUATED','physical_CLs':'NOT_EVALUATED','physical_kappa_limit':'NOT_EVALUATED','official_ATLAS_calibration':False,'rebinning_policy':'Predeclared frozen edges; no post-hoc improvement claim; future fit binning must satisfy common-source support, positivity and calibration before use.','datasets':[]}
    for ds,evs in g.items():templ['datasets'].append({'dataset_id':ds,'N_original':len(evs),'weight_scope':m[ds]['branching_ratio_scope'],'physical_normalization_ready':False,'source_root_sha256':m[ds]['root_sha256']})
    templ['templates']=[]
    for ds,evs in g.items():
        for obs,definition in ed.items():
            values=[(e['observables'][obs],e['source_weight_pb']*m[ds]['model_br_factor']*100000) for e in evs if e['stages'][4] and e['observables'][obs] is not None];_,cells=shape(values,definition['edges'],len(evs))
            templ['templates'].append(dict(process=ds,region='TAG_GE2_BROAD_MGG_105_160',observable=obs,bin_edges=definition['edges'],bin_content_including_flows=[math.fsum(c) for c in cells],sumw2_including_flows=[math.fsum(v*v for v in c) for c in cells],signed_weight_handling='PRESERVE_NO_CLIP',normalization_scope='ILLUSTRATIVE_MODEL_YIELD_100fb_NOT_PHYSICAL_TEMPLATE',nuisance_definitions='UNKNOWN_EXTERNAL_CALIBRATION_REQUIRED',covariance_information='fixed original N event diagnostics; kappa source covariance recorded separately',dataset_id=ds,source_identity=m[ds]['root_sha256'],overlap_scope='UNRESOLVED_FOR_PHYSICAL_COMBINATION',systematics_availability='UNKNOWN_PHYSICAL_NUISANCES',validation_state='DESCRIPTIVE_ONLY',signed_weight_status='PRESERVED_ZERO_NEGATIVE_NONFINITE_POLICY_EXPLICIT',provenance={'root_sha256':m[ds]['root_sha256']},validation_status='DESCRIPTIVE_ONLY_PHYSICAL_FIT_BLOCKED'))
    dump(a.output/'phase8_template_manifest.json',templ);dump(a.output/'phase8_postprocess_summary.json',{'status':'PASS_EXISTING_EVENT_REGIONS_AND_DESCRIPTIVE_SHAPES','region_rows':len(rows),'partition_closure':closure,'shape_rows':len(sh),'variant_rows':len(vr),'systematics_categories':len(SYSTEMATICS),'new_events':0,'physical_inference':'NOT_EVALUATED'});print('PASS_EXISTING_EVENT_REGIONS_AND_DESCRIPTIVE_SHAPES',len(rows),len(sh),len(vr))
if __name__=='__main__':main()