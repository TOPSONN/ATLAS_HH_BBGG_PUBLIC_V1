"""Decimal/Lagrange regression independent of the production scan algebra."""
import csv,math
from decimal import Decimal,localcontext
from .common import require
from .lhe import load_lhe

def validate_scan(table,source_path,factor):
    rows=list(csv.DictReader(open(table)));source=load_lhe(source_path)
    require(len(rows)==6000 and len(source['records'])==1000,'INDEPENDENT_SCAN_COHORT_COUNT')
    byevent={};benchmarks=[Decimal('-1'),Decimal('0'),Decimal('1'),Decimal('2'),Decimal('2.5'),Decimal('5')]
    for row in rows:
        i=int(row['source_event_index']);k=Decimal(row['kappa_lambda'])
        require(1<=i<=1000 and k in benchmarks and k not in byevent.setdefault(i,{}),'INDEPENDENT_DUPLICATE_OR_INVALID_ROW')
        byevent[i][k]=row
    require(set(byevent)==set(range(1,1001)),'INDEPENDENT_SOURCE_EVENT_SET')
    worst=Decimal(0);condition_worst=Decimal(0);sensitive=[];cauchy=Decimal(0);columns={k:[] for k in benchmarks}
    with localcontext() as ctx:
        ctx.prec=60;N=Decimal(1000);F=Decimal(str(factor))
        for i,group in byevent.items():
            require(set(group)==set(benchmarks),'INDEPENDENT_BENCHMARK_SET');original=source['records'][i-1]
            y={k:Decimal(r['full_mass_squared_ME']) for k,r in group.items()}
            require(all(v.is_finite() and v>=0 for v in y.values()) and y[1]>0,'INDEPENDENT_ME_FINITE_POSITIVITY')
            for k,row in group.items():
                require(row['source_event_sha256']==original['hash'] and float(row['source_alpha_s'])==original['alpha_qcd'] and
                    float(row['source_scale_gev'])==original['scale'],'INDEPENDENT_ORIGINAL_POINT_BINDING')
                # Lagrange interpolation through0,1,2; held-out points directly
                # test the native curve without production.quadratic().
                terms=[y[0]*(k-1)*(k-2)/2,-y[1]*k*(k-2),y[2]*k*(k-1)/2]
                prediction=sum(terms)
                err=abs(prediction-y[k])/max(abs(prediction),y[k],Decimal('1e-300'));worst=max(worst,err)
                # Finite native errors are amplified near destructive
                # cancellation. Keep the strict result-relative flag and
                # apply the unchanged threshold to interpolation magnitudes.
                conditioned=abs(prediction-y[k])/max(sum(abs(t) for t in terms),y[k],Decimal('1e-300'))
                condition_worst=max(condition_worst,conditioned)
                require(conditioned<Decimal('1e-7'),'INDEPENDENT_LAGRANGE_HELD_OUT_FAILURE')
                if err>=Decimal('1e-7'):
                    sensitive.append({'source_event_index':i,'kappa_lambda':str(k),'result_relative_residual':float(err),
                        'interpolation_condition_scaled_residual':float(conditioned),'ratio':row['ratio']})
                ratio=y[k]/y[1];actual=Decimal(row['ratio'])
                require(abs(ratio-actual)<=Decimal('1e-12')*max(1,ratio),'INDEPENDENT_ACTUAL_ME_RATIO_FAILURE')
                weight=Decimal(str(original['weight']))/N*ratio
                require(abs(weight-Decimal(row['source_contribution_pb']))<Decimal('1e-13') and
                    abs(weight*F-Decimal(row['MODEL_BR_ONLY_weight_pb']))<Decimal('1e-15'),'INDEPENDENT_WEIGHT_BR_OR_DENOMINATOR_FAILURE')
                columns[k].append(weight)
            box=y[0];triangle=(y[2]-2*y[1]+box)/2;interference=y[1]-box-triangle
            excess=interference*interference-4*max(0,triangle)*box
            scale=max(y.values())**2
            cauchy=max(cauchy,max(0,excess)/max(scale,Decimal('1e-300')))
            require(triangle>=-Decimal('1e-8')*max(y.values()) and excess<=Decimal('1e-7')*max(scale,Decimal('1e-300')),
                'INDEPENDENT_BOX_TRIANGLE_INTERFERENCE_BOUND')
        sums={k:sum(v,Decimal(0)) for k,v in columns.items()};cov=[];summary={}
        for k,a in columns.items():
            q=sum((x*x for x in a),Decimal(0));v=N/(N-1)*(q-sums[k]*sums[k]/N)
            summary[str(k)]={'sum_pb':float(sums[k]),'sumw2_pb2':float(q),'ESS':float(sums[k]*sums[k]/q),'source_input_sampling_variance_pb2':float(max(0,v))}
            for l,b in columns.items():
                value=N/(N-1)*(sum((x*y for x,y in zip(a,b)),Decimal(0))-sums[k]*sums[l]/N)
                cov.append({'kappa_a':str(k),'kappa_b':str(l),'covariance_pb2':float(value)})
    return {'status':'PASS_INDEPENDENT_DECIMAL_LAGRANGE_WEIGHT_AND_INTERFERENCE_REGRESSION','source_events':1000,
        'benchmarks':6,'rows':6000,'new_independent_events':0,'max_held_out_relative_residual':float(worst),
        'max_held_out_interpolation_condition_scaled_residual':float(condition_worst),
        'condition_scaled_acceptance_threshold':1e-7,'result_relative_flags_at_same_threshold':sensitive,
        'max_positive_Cauchy_bound_excess_relative':float(cauchy),'summaries':summary,'source_input_covariance':cov,
        'scope':'source-input weighted estimator; selected detector-outcome covariance is separate'}
