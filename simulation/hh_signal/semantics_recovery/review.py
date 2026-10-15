"""Independent numerical review and bounded excerpts of nonphysical traces."""
import math,re,struct
from decimal import Decimal,localcontext
from .contract import require,policy

def numbers(line):return [struct.unpack('>d',bytes.fromhex(v))[0] for v in line.split()[2:]]

def summarize(text):
    lines=[' '.join(x.split()) for x in text.splitlines() if x.lstrip().startswith('H_')]
    sums=[numbers(x) for x in lines if x.startswith('H_R SUM ')]
    iterations=[numbers(x) for x in lines if x.startswith('H_R ITERATION ')]
    result=[numbers(x) for x in lines if x.startswith('H_R RESULT ')]
    integer_rows=lambda tag:[list(map(int,x.split()[1:])) for x in lines if x.startswith(tag+' ')]
    rng={tag:{'count':len(v),'first':v[:8],'last':v[-8:]} for tag in ['RANMAR','RAN1','XRAN1']
        for v in [[x.split()[1] for x in lines if x.startswith('H_RNG_'+tag+' ')]]}
    return {'first_16_sum_states':sums[:16],'iteration_values':iterations,'result':result,
        'iterations':integer_rows('H_ITERATION'),'tails':integer_rows('H_TAIL'),
        'completion':integer_rows('H_COMPLETE'),'capacity':integer_rows('H_CANDIDATE_LIMIT'),
        'IO':integer_rows('H_IO'),'RNG':rng,'chi_records':sum(x.startswith('H_R CHI_') for x in lines),
        'native_error_after_records':sum(x.startswith('H_R NATIVE_ERROR_AFTER ') for x in lines),
        'candidate_records':sum(x.startswith('H_CANDIDATE ') for x in lines),
        'acceptance_records':sum(x.startswith('H_ACCEPT ') for x in lines),
        'complete_buffer_trace_lines':sum(x.startswith('H_RAW_NONPHYSICAL ') for x in lines),
        'none_pass_1000':bool(re.search(r'1000\s+points passed the cut but all returned zero',text)),
        'native_grid_read':'Grid read from file' in text,
        'weight_units':'METHOD_ONLY; not pb or a physical cross section'}

def independent_check(s):
    require(len(s['first_16_sum_states'])==16 and len(s['iteration_values'])==4,'MISSING_NATIVE_NUMERICAL_DIAGNOSTICS')
    a=b=q=0.
    for i,row in enumerate(s['first_16_sum_states'],1):
        v=float(1+i%7)
        if i%11==0:v=-v
        if i%13==0:v=0.
        w=v/1000;a+=abs(w);b+=w;q+=w*w
        require(row[:3]==[a,b,q],'INDEPENDENT_FIRST_POINT_SUM_OR_SQUARE_DRIFT')
    with localcontext() as ctx:
        ctx.prec=60;weights=[];i=0
        while sum(v!=0 for v in weights)<250:
            i+=1;v=Decimal(1+i%7)
            if i%11==0:v=-v
            if i%13==0:v=Decimal(0)
            weights.append(v)
        n=Decimal(len(weights));nonzero=Decimal(250)
        mean=sum(abs(w) for w in weights)/n
        # Reproduce the actual native non_zero variance arithmetic without
        # claiming this is a calibrated coverage estimator.
        variance=abs((sum(w*w for w in weights)-nonzero*mean*mean)/(n-1)/n)
        target=[float(mean),float(variance.sqrt())]
    tol=policy()['independent_decimal_tolerance']
    for expected,actual in zip(target,s['iteration_values'][0][:2]):
        require(math.isclose(expected,actual,rel_tol=tol['relative'],abs_tol=tol['absolute']),'INDEPENDENT_NATIVE_ERROR_ARITHMETIC_DRIFT')
    means=[r[0] for r in s['iteration_values'][-3:]];errors=[r[1] for r in s['iteration_values'][-3:]]
    total=math.fsum(m*m/(e*e) for m,e in zip(means,errors))
    expected_mean=math.fsum(m*m*m/(e*e) for m,e in zip(means,errors))/total
    expected_error=expected_mean/math.sqrt(total)
    for expected,actual in zip([expected_mean,expected_error],[s['result'][0][0],s['result'][0][2]]):
        require(math.isclose(expected,actual,rel_tol=tol['relative'],abs_tol=tol['absolute']),'INDEPENDENT_LAST_THREE_ERROR_DRIFT')
    return {'status':'PASS_INDEPENDENT_FIXED_STREAM_DOUBLE_AND_DECIMAL_ARITHMETIC',
        'first_iteration_attempted_points':int(n),'first_iteration_nonzero_points':250,
        'first_iteration_native_abs_mean':target[0],'first_iteration_native_error':target[1],
        'last_three_mean':expected_mean,'last_three_error':expected_error,'tolerance':tol,
        'scope':'native arithmetic identity on nonphysical fixed stream; no coverage or HH convergence claim'}

def coverage(summaries):
    a=summaries['adaptation'];m=summaries['measurement'];forced=summaries['forced_secondary_store']
    require(a['iterations']==[[1,2,500],[2,3,1000],[3,4,2000],[4,5,4000]],'POINT_DOUBLING_OR_ADAPTATION_STOP_DRIFT')
    require(m['iterations']==[[1,2,500],[2,3,1000],[3,4,2000]] and m['native_grid_read'],'MEASUREMENT_GRID_OR_ENDPOINT_DRIFT')
    require(a['tails'] and a['chi_records'] and a['native_error_after_records'] and a['complete_buffer_trace_lines'],
        'INCOMPLETE_TAIL_ERROR_OR_BUFFER_DIAGNOSTICS')
    require(any(row[2]>0 for row in forced['tails']),'NONZERO_OVERWEIGHT_BRANCH_NOT_COVERED')
    require(summaries['none_pass']['none_pass_1000'] and not summaries['none_pass']['completion'],'EARLY_FAILURE_NOT_VERIFIED')
    require(summaries['candidate_limit']['capacity']==[[200000,200000]],'CANDIDATE_CAPACITY_NOT_VERIFIED')
    for case in ['negative_accuracy','positive_accuracy']:
        require(summaries[case]['completion'] and summaries[case]['iterations'][0][1]>4,'EARLY_ACCURACY_STOP_NOT_VERIFIED')
    return independent_check(a)
