"""Phase10 event-cluster stratification, independently implemented arithmetic.

Phase9 persisted annotations are input evidence, not a new full graph classifier.
No import of Phase9 classification or production statistics is permitted here.
"""
from collections import Counter
import csv
import bisect
import hashlib
import json
import math
from pathlib import Path

STAGES = ('00_INPUT','01_TWO_PHOTONS','02_TWO_JETS','03_TWO_BTAGS','04_MGG_105_160')
HF_DATASETS = ('B01','B02','B03')
EVIDENCE = 'ACTUAL_EXISTING_DATA_READBACK'

def demand(ok, reason):
    if not ok: raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def read_jsonl(path):
    with Path(path).open('rb') as f:
        for line in f:
            demand(len(line)<16*1024**2,'OVERSIZED_ROW')
            yield json.loads(line)

def write_json(path,data):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')

def write_csv(path,rows):
    demand(rows,'EMPTY_RESULT')
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)

def fixed_cov(x,y):
    demand(len(x)==len(y) and len(x)>1,'INVALID_FIXED_N_COHORT')
    n=len(x);mx=math.fsum(x)/n;my=math.fsum(y)/n
    return n/(n-1)*math.fsum((a-mx)*(b-my) for a,b in zip(x,y))

def wilson(k,n):
    if not n:return (None,None)
    z=1.959963984540054;p=k/n;d=1+z*z/n
    c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (0. if k==0 else max(0.,c-h)),(1. if k==n else min(1.,c+h))

def binomial_cdf(k,n,p):
    if k<0:return 0.
    if k>=n:return 1.
    if p<=0:return 1.
    if p>=1:return 0.
    terms=[math.lgamma(n+1)-math.lgamma(j+1)-math.lgamma(n-j+1)+j*math.log(p)+(n-j)*math.log1p(-p) for j in range(k+1)]
    m=max(terms)
    return min(1.,math.exp(m)*math.fsum(math.exp(t-m) for t in terms))

def rare_exact(k,n):
    """Two-sided 95% Clopper-Pearson only at rare boundaries; zero one-sided too."""
    if n==0:return (None,None,None)
    if k==0:return 0.,-math.expm1(math.log(.025)/n),-math.expm1(math.log(.05)/n)
    if k==n:return math.exp(math.log(.025)/n),1.,None
    if min(k,n-k)>10:return (None,None,None)
    def solve(j,target):
        a,b=0.,1.
        for _ in range(65):
            p=(a+b)/2
            if binomial_cdf(j,n,p)>target:a=p
            else:b=p
        return (a+b)/2
    return solve(k-1,.975),solve(k,.025),None

def summary(indicators,weights):
    n=len(weights);demand(n>1 and len(indicators)==n,'INVALID_FULL_COHORT')
    demand(all(math.isfinite(w) for w in weights),'NONFINITE_WEIGHT')
    xs=[w*int(bool(i)) for i,w in zip(indicators,weights)];s=math.fsum(xs);s2=math.fsum(x*x for x in xs);k=sum(map(bool,indicators))
    var=fixed_cov(xs,xs);lo,hi=wilson(k,n);el,eh,one=rare_exact(k,n)
    return dict(original_N=n,events=k,event_fraction=k/n,wilson95_low=lo,wilson95_high=hi,rare_exact95_low=el,rare_exact95_high=eh,zero_one_sided95_upper=one,sumw_pb=s,sumw2_pb2=s2,fixed_N_variance_pb2=var,source_sampling_SE_pb=math.sqrt(max(0.,var)),ESS=s*s/s2 if s2 else None,relative_source_sampling_SE=math.sqrt(max(0.,var))/abs(s) if s else None,interval_scope='UNWEIGHTED_IID_PROPOSAL_ACCEPTANCE_NOT_PHYSICAL_RATE',uncertainty_scope='FIXED_ORIGINAL_N_EVENT_CLUSTERS_RAW_SOURCE_PB')

def conditional(indicator,denominator,weights):
    numerator=[w*int(i) for w,i in zip(weights,indicator)];den=[w*int(i) for w,i in zip(weights,denominator)];s=math.fsum(den);k=sum(indicator);n=sum(denominator)
    ratio=math.fsum(numerator)/s if s else None
    residual=[a-ratio*b for a,b in zip(numerator,den)] if ratio is not None else None
    lo,hi=wilson(k,n);el,eh,one=rare_exact(k,n)
    return dict(denominator_events=n,acceptance=k/n if n else None,acceptance_wilson95_low=lo,acceptance_wilson95_high=hi,acceptance_rare_exact95_low=el,acceptance_rare_exact95_high=eh,acceptance_zero_one_sided95_upper=one,denominator_sumw_pb=s,weighted_acceptance=ratio,weighted_acceptance_variance=fixed_cov(residual,residual)/s**2 if s else None)

def me_class(outgoing):
    ids={abs(int(x)) for x in outgoing}
    return 'ME_BOTTOM' if 5 in ids else 'ME_CHARM' if 4 in ids else 'ME_LIGHT_OR_GLUON'

def flags(event):
    h=event['heavy_flavour'];jets=h['jets'];me=me_class(event['hard_outgoing_pdg_ids']);n=sum(bool(j['tagged']) for j in jets)
    demand(h['hard_process_flavour']==me,'PERSISTED_ME_FLAVOUR_MISMATCH')
    f={
        'ME_BOTTOM':me=='ME_BOTTOM','ME_CHARM':me=='ME_CHARM','ME_LIGHT_OR_GLUON':me=='ME_LIGHT_OR_GLUON',
        'HAS_ME_INITIAL_HEAVY_FLAVOUR_RECORD':h['heavy_quark_birth_counts'].get('ME_INITIAL_HEAVY_FLAVOUR_RECORD',0)>0,
        'HAS_SHOWER_BOTTOM_BIRTH':h['shower_bottom_births']>0,'HAS_SHOWER_CHARM_BIRTH':h['shower_charm_births']>0,
        'HAS_DIRECT_G_TO_HEAVY_PAIR':h['direct_gluon_splitting_count']>0,
        'HAS_TERMINAL_B_HADRON':h['terminal_b_hadrons']>0,'HAS_TERMINAL_C_HADRON':h['terminal_c_hadrons']>0,
        'HAS_UNCLASSIFIED_QUARK_BIRTH':h['unclassified_quark_births']>0,
        'HAS_AMBIGUOUS_HADRON_ASSIGNMENT':bool(h['ambiguous_hadron_assignment_ids']),
        'HAS_NATIVE_BOTTOM_JET':any(j['native_flavour']==5 for j in jets),
        'HAS_NATIVE_CHARM_JET':any(j['native_flavour']==4 for j in jets),
        'HAS_HEAVY_HADRON_ELIGIBLE_JET':any(j['heavy_hadron_flavour'] in (4,5) for j in jets),
        'HARD_LIGHT_NATIVE_HEAVY':me=='ME_LIGHT_OR_GLUON' and any(j['native_flavour'] in (4,5) for j in jets),
        'HAS_NATIVE_FLAVOUR_BOUNDARY_AMBIGUITY':any(len(j['native_attainable_labels'])>1 for j in jets),
        'HAS_NATIVE_FLAVOUR_MISMATCH':not h['native_reproduction_pass'],
        'NATIVE_TAGS_0':n==0,'NATIVE_TAGS_1':n==1,'NATIVE_TAGS_GE2':n>=2,
    }
    return f

def level_signature(event):
    h=event['heavy_flavour'];jets=h['jets'];tags=sum(bool(j['tagged']) for j in jets)
    def labels(key):return '+'.join(map(str,sorted({int(j[key]) for j in jets}))) if jets else 'NO_ELIGIBLE_JETS'
    return dict(ME_flavour=me_class(event['hard_outgoing_pdg_ids']),shower_flags=f"B{int(h['shower_bottom_births']>0)}_C{int(h['shower_charm_births']>0)}_GPAIR{int(h['direct_gluon_splitting_count']>0)}",hadron_flavour_set=labels('heavy_hadron_flavour'),native_flavour_set=labels('native_flavour'),native_tag_category='TAG_0' if tags==0 else 'TAG_1' if tags==1 else 'TAG_GE2')

def validate_join(origin,native):
    demand(origin['dataset_id']==native['dataset_id'],'DATASET_JOIN')
    demand(origin['source_event_index']==native['source_event_ordinal'],'SOURCE_ORDINAL_JOIN')
    for name in ('source_event_sha256','hepmc_event_sha256','stages'):
        demand(origin[name]==native[name],'PERSISTED_IDENTITY_JOIN_'+name)
    demand(math.isclose(origin['weight_pb'],native['source_weight_pb'],rel_tol=1e-14,abs_tol=1e-18),'SOURCE_WEIGHT_JOIN')
    if origin['heavy_flavour']:
        a={j['index']:j for j in native['eligible_jets']};b={j['index']:j for j in origin['heavy_flavour']['jets']}
        demand(set(a)==set(b),'ELIGIBLE_JET_JOIN')
        for i in a:
            demand(a[i]['flavour']==b[i]['native_flavour'] and a[i]['tagged']==b[i]['tagged'],'JET_NATIVE_FIELDS')
            demand(b[i]['sole_hadron_endpoint']=='UNKNOWN_MULTI_MOTHER_STRING_NOT_RESOLVED','UNKNOWN_HADRON_ENDPOINT_LOST')

def shape_population_pair(events_a,events_b,stage_index,observable,edges):
    demand(len(edges)>=2 and all(a<b for a,b in zip(edges,edges[1:])),'INVALID_FROZEN_SHAPE_EDGES')
    def one(events):
        selected=[e for e in events if e['stages'][stage_index]]
        defined=[e for e in selected if e['observables'][observable] is not None]
        bins=[0.]*(len(edges)+1);counts=[0]*(len(edges)+1)
        for e in defined:
            x=e['observables'][observable];demand(math.isfinite(x),'NONFINITE_SHAPE_VALUE');i=bisect.bisect_right(edges,x);bins[i]+=e['weight_pb'];counts[i]+=1
        total=math.fsum(bins);squares=math.fsum(e['weight_pb']**2 for e in defined)
        unsupported=any(x<0 for x in bins)
        fractions=[x/total for x in bins] if total>0 and not unsupported else None
        return dict(selected_events=len(selected),defined_events=len(defined),missing_events=len(selected)-len(defined),source_sumw_pb=total,ESS=total*total/squares if squares else None,nonempty_bins=sum(n>0 for n in counts),fractions=fractions,counts=counts,unsupported_signed_shape=unsupported)
    a,b=one(events_a),one(events_b);shared=sum(x>0 and y>0 for x,y in zip(a['counts'],b['counts']));js=cdf=None
    if a['fractions'] is not None and b['fractions'] is not None:
        terms=[];ca=cb=0.;cdf=0.
        for p,q in zip(a['fractions'],b['fractions']):
            mid=(p+q)/2
            if p:terms.append(.5*p*math.log(p/mid))
            if q:terms.append(.5*q*math.log(q/mid))
            ca+=p;cb+=q;cdf=max(cdf,abs(ca-cb))
        js=math.fsum(terms)
    return dict(observable=observable,shape_status='DEFINED_DESCRIPTIVE_ONLY' if js is not None else 'UNSUPPORTED_SIGNED_SHAPE' if a['unsupported_signed_shape'] or b['unsupported_signed_shape'] else 'UNDEFINED_EMPTY_OR_ZERO_WEIGHT_SUPPORT',defined_events_a=a['defined_events'],defined_events_b=b['defined_events'],missing_events_a=a['missing_events'],missing_events_b=b['missing_events'],source_sumw_a_pb=a['source_sumw_pb'],source_sumw_b_pb=b['source_sumw_pb'],ESS_a=a['ESS'],ESS_b=b['ESS'],nonempty_bins_a=a['nonempty_bins'],nonempty_bins_b=b['nonempty_bins'],shared_nonempty_bins=shared,JS_natural_log=js,CDF_sup_distance=cdf,flow_policy='UNDERFLOW_AND_OVERFLOW_INCLUDED_IN_EACH_OWN_SOURCE_SHAPE_DENOMINATOR',weight_scope='SEPARATE_RAW_SOURCE_NORMALIZED_SHAPES_NO_PHYSICAL_PROCESS_SUM',inference='DESCRIPTIVE_SHAPE_POPULATION_NOT_PERTURBATIVE_DOUBLE_COUNT_PROOF_NOT_PVALUE',physical_sum_allowed=False)


def stratify(events,shape_edges=None):
    rows=[];covrows=[];summaries={};signatures={}
    for dataset in HF_DATASETS:
        ev=[e for e in events if e['dataset_id']==dataset];demand(len(ev)==1000,'FULL_HF_COHORT_REQUIRED')
        weights=[e['weight_pb'] for e in ev];ff=[flags(e) for e in ev];names=sorted(ff[0]);ss=[level_signature(e) for e in ev];keys=sorted({tuple(sorted(s.items())) for s in ss});signatures[dataset]=(ev,ss)
        ambiguities=dict(unknown_hadron_endpoint_jets=sum(j['sole_hadron_endpoint'].startswith('UNKNOWN') for e in ev for j in e['heavy_flavour']['jets']),ambiguous_hadron_assignment_events=sum(bool(e['heavy_flavour']['ambiguous_hadron_assignment_ids']) for e in ev),native_boundary_events=sum(f['HAS_NATIVE_FLAVOUR_BOUNDARY_AMBIGUITY'] for f in ff),pythia_tuple_ambiguous_or_missing=sum((e.get('pythia_mapping') or {}).get('ambiguous_or_missing',0) for e in ev))
        summaries[dataset]=dict(original_N=len(ev),stages={},ambiguities=ambiguities)
        for k,stage in enumerate(STAGES):
            passed=[e['stages'][k] for e in ev];summaries[dataset]['stages'][stage]=summary(passed,weights)
            for name in names:
                base=[f[name] for f in ff];indicator=[a and b for a,b in zip(base,passed)]
                rows.append(dict(dataset_id=dataset,stage=stage,row_type='NONEXCLUSIVE_ORIGIN_FLAG',category=name,evidence_class=EVIDENCE,**summary(indicator,weights),**{'stratum_'+a:b for a,b in conditional(indicator,base,weights).items()}))
            for key in keys:
                base=[tuple(sorted(s.items()))==key for s in ss];indicator=[a and b for a,b in zip(base,passed)]
                rows.append(dict(dataset_id=dataset,stage=stage,row_type='EXCLUSIVE_OBSERVED_CROSS_TAB',category=json.dumps(dict(key),sort_keys=True,separators=(',',':')),evidence_class=EVIDENCE,**dict(key),**summary(indicator,weights),**{'stratum_'+a:b for a,b in conditional(indicator,base,weights).items()}))
            vectors={name:[w*int(p and f[name]) for p,f,w in zip(passed,ff,weights)] for name in names}
            for a in names:
                for b in names:
                    xa,xb=vectors[a],vectors[b];cov=fixed_cov(xa,xb);va=fixed_cov(xa,xa);vb=fixed_cov(xb,xb)
                    covrows.append(dict(dataset_id=dataset,stage=stage,flag_a=a,flag_b=b,overlap_events=sum(p and f[a] and f[b] for p,f in zip(passed,ff)),fixed_N_covariance_pb2=cov,correlation=cov/math.sqrt(va*vb) if va>0 and vb>0 else None,statistical_unit='ORIGINAL_SOURCE_EVENT_ALL_JETS_CLUSTERED',nonexclusive_flags=True))
    overlap=[]
    for ai,a in enumerate(HF_DATASETS):
        for b in HF_DATASETS[ai+1:]:
            for k,stage in enumerate(STAGES):
                def population(dataset):
                    ev,ss=signatures[dataset];selected=[s for e,s in zip(ev,ss) if e['stages'][k]]
                    # Exclude ME definition deliberately: compares reconstructed/shower feature support.
                    c=Counter(tuple(sorted((x,y) for x,y in s.items() if x!='ME_flavour')) for s in selected)
                    return c,len(selected)
                ca,na=population(a);cb,nb=population(b);common=set(ca)&set(cb);union=set(ca)|set(cb)
                overlap.append(dict(dataset_a=a,dataset_b=b,stage=stage,row_type='CATEGORICAL_FEATURE_POPULATION',events_a=na,events_b=nb,observed_feature_cells_a=len(ca),observed_feature_cells_b=len(cb),shared_feature_cells=len(common),support_jaccard=len(common)/len(union) if union else None,events_a_in_shared_cells=sum(ca[x] for x in common),events_b_in_shared_cells=sum(cb[x] for x in common),fraction_a_in_shared_cells=sum(ca[x] for x in common)/na if na else None,fraction_b_in_shared_cells=sum(cb[x] for x in common)/nb if nb else None,inference='OBSERVED_RECONSTRUCTED_FEATURE_POPULATION_OVERLAP_NOT_PERTURBATIVE_DOUBLE_COUNT_PROOF',physical_sum_allowed=False))
                if shape_edges is not None:
                    for observable,edges in shape_edges.items():
                        overlap.append(dict(dataset_a=a,dataset_b=b,stage=stage,row_type='KINEMATIC_SHAPE_POPULATION',**shape_population_pair(signatures[a][0],signatures[b][0],k,observable,edges)))
    return rows,covrows,overlap,summaries
