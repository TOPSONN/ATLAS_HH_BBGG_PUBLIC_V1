#!/usr/bin/env python3
"""Independent Decimal(70) verification of existing native event statistics.

This module never imports generator, shower, detector or integration runtimes.
Input events must be outputs of the native existing-data ROOT reader. Synthetic
unit fixtures, if used, stay separate from actual-data evidence.
"""
from __future__ import annotations
import argparse
import bisect
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path

BENCHMARKS = (Decimal('-1'), Decimal('0'), Decimal('1'), Decimal('2'), Decimal('2.5'), Decimal('5'))
STAGES = ('INPUT', 'PHOTONS', 'JETS', 'TWO_BTAGS', 'FINAL_MGG')
FROZEN_KAPPA_SHA = 'c76dd54b9236ee8110385fe746eb465125c70f1f30e0d580ac95acacc03a9e0f'
D = Decimal

def require(value, reason):
    if not value:
        raise ValueError(reason)

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_float=D)

def decimal(value):
    result = value if isinstance(value, D) else D(str(value))
    require(result.is_finite(), 'NONFINITE_DECIMAL_INPUT')
    return result

def moments(values):
    n = len(values)
    require(n >= 2, 'FULL_SOURCE_COHORT_REQUIRED')
    values = list(map(decimal, values))
    total = sum(values)
    square = sum(x*x for x in values)
    mean = total / n
    centered = sum((x-mean)**2 for x in values)
    absolute = sum(map(abs, values))
    return dict(N_original=n, sumw=total, sumw2=square, sum_absw=absolute,
                mean_weight=mean, weight_sample_variance=centered/(n-1),
                fixed_N_source_sampling_variance=centered*n/(n-1),
                ESS=total*total/square if square else None,
                cancellation_ratio=abs(total)/absolute if absolute else None,
                largest_absolute_fraction=max(map(abs, values))/absolute if absolute else None,
                N_positive=sum(x>0 for x in values), N_negative=sum(x<0 for x in values),
                N_zero=sum(x==0 for x in values))

def covariance(first, second):
    require(len(first) == len(second) and len(first) >= 2, 'PAIRED_COHORT_REQUIRED')
    a, b = list(map(decimal, first)), list(map(decimal, second))
    n = D(len(a))
    ma, mb = sum(a)/n, sum(b)/n
    return n/(n-1)*sum((x-ma)*(y-mb) for x,y in zip(a,b))

def compare(actual, expected, label, checks, relative=D('4e-10'), absolute=D('1e-27')):
    if expected is None:
        require(actual is None, 'UNDEFINED_NOT_NULL_'+label)
    elif isinstance(expected, int):
        require(actual == expected, 'INTEGER_MISMATCH_'+label)
    else:
        actual = decimal(actual)
        expected = decimal(expected)
        require(abs(actual-expected) <= absolute + relative*max(abs(actual),abs(expected)),
                'DECIMAL_MISMATCH_'+label)
    checks[0] += 1

def compare_summary(actual, expected, label, checks):
    for key, value in expected.items():
        compare(actual[key], value, label+'_'+key, checks)

def quality(summary, count):
    if not count: return 'EMPTY_BIN'
    if summary['cancellation_ratio'] is not None and summary['cancellation_ratio'] < D('1e-12'):
        return 'CANCELLATION_DOMINATED'
    if summary['ESS'] is None: return 'EMPTY_BIN'
    if summary['ESS'] < 10: return 'LOW_ESS_LT10'
    if summary['ESS'] < 20: return 'LOW_ESS_LT20'
    if summary['largest_absolute_fraction'] is not None and summary['largest_absolute_fraction'] > D('.1'):
        return 'HIGH_SINGLE_EVENT_DOMINANCE'
    return 'VALID_DESCRIPTIVE_ONLY'

def edge_map(config):
    data = config.get('edges', config.get('observables', config))
    return {key:list(map(decimal, value if isinstance(value,list) else value['edges']))
            for key,value in data.items() if isinstance(value,(list,dict))}

def event_cohorts(path):
    cohorts = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        event = json.loads(line, parse_float=D)
        cohorts.setdefault(event['dataset_id'], []).append(event)
    for name, events in cohorts.items():
        events.sort(key=lambda e:e['source_event_ordinal'])
        n = len(events)
        require([e['source_event_ordinal'] for e in events] == list(range(1,n+1)),
                'DUPLICATE_OR_MISSING_SOURCE_'+name)
        require(all(e['N_original']==n and len(e['stages'])==5 for e in events),
                'WRONG_N_OR_STAGE_VECTOR_'+name)
    return cohorts

def tag_probability(jet):
    pt, flavour = float(jet['pt']), jet['flavour']
    if flavour == 5: p=.8*math.tanh(.003*pt)*30/(1+.086*pt)
    elif flavour == 4: p=.2*math.tanh(.02*pt)/(1+.0034*pt)
    else:
        require(flavour in (0,1,2,3,21), 'UNSUPPORTED_TAG_FLAVOUR')
        p=.002+7.3e-6*pt
    return D(str(min(1.,max(0.,p))))

def conditional_distribution(jets):
    # Independent full Poisson-binomial PMF, unlike the native three-state DP.
    distribution = [D(1)]
    for jet in jets:
        p = tag_probability(jet)
        new = [D(0)]*(len(distribution)+1)
        for k,value in enumerate(distribution):
            new[k] += value*(1-p)
            new[k+1] += value*p
        distribution = new
    require(abs(sum(distribution)-1)<D('1e-60'), 'CONDITIONAL_PMF_NORMALIZATION')
    return distribution

def conditional_probability(jets):
    return sum(conditional_distribution(jets)[2:])

def check_statistics(events, result, edges, checks):
    factor = decimal(result['model_BR_factor'])
    require(result['factor_applications'] == (0 if factor==1 else 1), 'BR_APPLICATION_COUNT')
    weights = [decimal(e['source_weight_pb'])*factor for e in events]
    n = len(events)
    for stage, row in enumerate(result['stages']):
        require(row['stage'] == STAGES[stage], 'STAGE_ORDER_CHANGED')
        contributions = [w if e['stages'][stage] else D(0) for e,w in zip(events,weights)]
        compare_summary(row, moments(contributions), row['stage'], checks)
        passed = sum(e['stages'][stage] for e in events)
        compare(row['N_pass'],passed,'N_PASS',checks)
        if not passed:
            # Decimal transcendental is independent of native expm1/log1p.
            expected = 1-(D('.05').ln()/n).exp()
            compare(row['zero_count_one_sided95_proposal_upper'],expected,'ZERO_BOUND',checks)
            require(row['weighted_rate_upper_bound'] is None, 'ZERO_COUNT_NOT_WEIGHTED_RATE_BOUND')
    for row in result['bin_quality']:
        stage=STAGES.index(row['stage']); name=row['observable']; e=edges[name]
        values=[D(0)]*n; count=missing=0
        for i,(event,w) in enumerate(zip(events,weights)):
            if not event['stages'][stage]: continue
            value=event['observables'].get(name)
            if value is None: missing+=1; continue
            if bisect.bisect_right(e,decimal(value))==row['bin']:
                values[i]=w; count+=1
        summary=moments(values)
        compare_summary(row,summary,'BIN_'+name+'_'+str(row['bin']),checks)
        compare(row['N_original_sources_contributing'],count,'BIN_CONTRIBUTORS',checks)
        compare(row['missing_kinematics'],missing,'BIN_MISSING',checks)
        require(row['quality_flag']==quality(summary,count),'BIN_QUALITY_FLAG')
    for stage,row in zip((3,4),result['conditional_tags']):
        probabilities=[];zero_count=one_count=D(0);eligible_count=0
        for event in events:
            mgg=event['observables'].get('m_gamma_gamma')
            mass=stage!=4 or (mgg is not None and 105<=mgg<=160)
            if event['stages'][2] and mass:
                distribution=conditional_distribution(event['eligible_jets']);zero_count+=distribution[0];one_count+=distribution[1] if len(distribution)>1 else D(0);eligible_count+=1
                probabilities.append(sum(distribution[2:]))
            else:probabilities.append(D(0))
        expected=[w*p for w,p in zip(weights,probabilities)]
        compare(row['eligible_before_tag_count'],eligible_count,'TAG_ELIGIBLE',checks)
        compare(row['expected_tag0_count'],zero_count,'TAG_ZERO',checks)
        compare(row['expected_tag1_count'],one_count,'TAG_ONE',checks)
        compare(row['expected_count'],sum(probabilities),'CONDITIONAL_COUNT',checks)
        compare(row['conditional_count_variance'],sum(p*(1-p) for p in probabilities),'TAG_VARIANCE',checks)
        compare(row['conditional_weighted_variance_pb2'],sum(w*w*p*(1-p) for w,p in zip(weights,probabilities)),'WEIGHTED_TAG_VARIANCE',checks)
        compare_summary(row['analytic_expectation'],moments(expected),'ANALYTIC_MEAN',checks)
        require(row['variance_components_added'] is False,'TAG_VARIANCE_DOUBLE_COUNTED')

def check_kappa(events, weights_path, directory, edges, checks):
    require(hashlib.sha256(Path(weights_path).read_bytes()).hexdigest()==FROZEN_KAPPA_SHA,
            'WRONG_FROZEN_KAPPA_CSV')
    records=list(csv.DictReader(Path(weights_path).open(encoding='utf-8',newline='')))
    n=len(events);require(n==1000 and len(records)==6000,'KAPPA_COHORT_COUNT')
    by={};hashes={i+1:e['source_event_sha256'] for i,e in enumerate(events)}
    for row in records:
        i,k=int(row['source_event_index']),decimal(row['kappa_lambda'])
        require(k in BENCHMARKS and (i,k) not in by,'DUPLICATE_OR_UNKNOWN_KAPPA')
        require(row['source_event_sha256']==hashes[i],'KAPPA_SOURCE_HASH')
        by[(i,k)]=row
    require(len(by)==6000,'MISSING_KAPPA_BENCHMARK')
    result=read(Path(directory)/'phase8_kappa_summary.json')
    for k,row in zip(BENCHMARKS,result['summaries']):
        raw=[decimal(by[(i,k)]['source_contribution_pb']) for i in range(1,n+1)]
        final=[decimal(by[(i,k)]['MODEL_BR_ONLY_weight_pb']) if events[i-1]['stages'][4] else D(0) for i in range(1,n+1)]
        compare_summary(row['input'],moments(raw),'KAPPA_INPUT_'+str(k),checks)
        compare_summary(row['final'],moments(final),'KAPPA_FINAL_'+str(k),checks)
        ranked=sorted(map(abs,raw),reverse=True);absolute=sum(ranked)
        for top in (1,5,10):
            compare(row['top'+str(top)+'_contribution_fraction'],sum(ranked[:top])/absolute,'KAPPA_TOP'+str(top),checks)
        if k in (D('2.5'),D('5')):
            require(row['status']=='INCONCLUSIVE_REWEIGHTING','LOW_SUPPORT_NOT_INCONCLUSIVE')
    for stage,matrix in enumerate(result['covariance_by_stage']):
        columns={k:[decimal(by[(i,k)]['MODEL_BR_ONLY_weight_pb']) if events[i-1]['stages'][stage] else D(0) for i in range(1,n+1)] for k in BENCHMARKS}
        for a,k in enumerate(BENCHMARKS):
            for b,l in enumerate(BENCHMARKS):
                c=covariance(columns[k],columns[l])
                compare(matrix['covariance'][a][b],c,'KAPPA_COV_'+str(stage)+'_'+str(a)+'_'+str(b),checks)
                va,vb=covariance(columns[k],columns[k]),covariance(columns[l],columns[l])
                expected=c/(va*vb).sqrt() if va>0 and vb>0 else None
                compare(matrix['correlation'][a][b],expected,'KAPPA_CORR',checks)
                require(matrix['covariance'][a][b]==matrix['covariance'][b][a],'NONSYMMETRIC_PUBLISHED_MATRIX')
        require(matrix['eigenvalues_modified'] is False,'COVARIANCE_EIGENVALUE_CLIPPING')
        require(decimal(matrix['minimum_eigenvalue'])>=-decimal(matrix['PSD_absolute_tolerance']),'NATIVE_PSD_GATE')
    rows=read(Path(directory)/'phase8_kappa_bin_quality.json')
    for row in rows:
        stage=STAGES.index(row['stage']); k=decimal(row['kappa_lambda']); e=edges[row['observable']]
        weights=[D(0)]*n; count=missing=0
        for i,event in enumerate(events):
            if not event['stages'][stage]:continue
            value=event['observables'].get(row['observable'])
            if value is None:missing+=1;continue
            if bisect.bisect_right(e,decimal(value))==row['bin']:
                weights[i]=decimal(by[(i+1,k)]['MODEL_BR_ONLY_weight_pb']);count+=1
        summary=moments(weights);compare_summary(row,summary,'KAPPA_BIN',checks)
        compare(row['N_original_sources_contributing'],count,'KAPPA_BIN_COUNT',checks)
        compare(row['missing_kinematics'],missing,'KAPPA_BIN_MISSING',checks)
        require(row['quality_flag']==quality(summary,count),'KAPPA_BIN_QUALITY')
    return dict(source_events=n,ME_rows=len(records),covariance_entries_verified=5*36,
                bin_quality_rows_verified=len(rows),new_ME_calls=0)

def run(args):
    with localcontext() as context:
        context.prec=70
        cohorts=event_cohorts(args.events);edges=edge_map(read(args.edges));checks=[0]
        mapping=read(args.statistics_index)
        if 'datasets' in mapping:mapping=mapping['datasets']
        require(isinstance(mapping,dict),'STATISTICS_INDEX_MUST_MAP_DATASET_TO_RESULT_JSON')
        checked=[]
        for name,path in mapping.items():
            require(name in cohorts,'UNKNOWN_STATISTICS_DATASET')
            result=read(path)
            check_statistics(cohorts[name],result,edges,checks)
            checked.append(dict(dataset_id=name,N_original=len(cohorts[name]),evidence_class='ACTUAL_FULL_DATA_READBACK'))
        kappa=check_kappa(cohorts['S01_C1000'],args.kappa_weights,args.kappa_directory,edges,checks)
        result=dict(status='PASS_INDEPENDENT_DECIMAL70_STATISTICS',evidence_class='ACTUAL_FULL_DATA_READBACK',
                    method='Independent Decimal70 centered moments and full Poisson-binomial PMF; no imported production code',
                    comparisons=checks[0],datasets=checked,kappa=kappa,new_ME_calls=0,new_integrals=0,new_events=0,
                    conditional_variance_added_to_observed=False,physical_inference='NOT_EVALUATED')
        output=Path(args.output)
        require(not output.exists(),'REFUSE_EXISTING_INDEPENDENT_RECEIPT')
        with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events',required=True)
    parser.add_argument('--edges',required=True)
    parser.add_argument('--statistics-index',required=True)
    parser.add_argument('--kappa-weights',required=True)
    parser.add_argument('--kappa-directory',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(run(args),indent=2))

if __name__=='__main__':main()
