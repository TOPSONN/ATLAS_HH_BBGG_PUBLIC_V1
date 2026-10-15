"""Event-level sampling estimates; independent unknowns stay separate."""
import math

def wilson(n,N,z=1.959963984540054):
    if N<=0 or not 0<=n<=N:raise ValueError('invalid binomial counts')
    p=n/N;d=1+z*z/N;c=(p+z*z/(2*N))/d;h=z*math.sqrt(p*(1-p)/N+z*z/(4*N*N))/d
    return max(0.,c-h),min(1.,c+h)

def precision_plan(n,N):
    lo,hi=wilson(n,N)
    return {'observed':n,'original_independent_events':N,'acceptance':n/N,'wilson95':[lo,hi],
        'zero_one_sided95_upper':1-.05**(1/N) if n==0 else None,
        'planning_status':'NO_FINITE_CONSERVATIVE_GUARANTEE_FROM_ZERO_PILOT' if n==0 else 'PILOT_BASED_NOT_A_GUARANTEE',
        'independent_events_for_relative_source_acceptance_precision':{
           str(t):{'plug_in':math.ceil((1-n/N)/((t*t)*(n/N))) if n else None,
                   'conservative_using_wilson_lower':math.ceil((1-lo)/(t*t*lo)) if lo>0 else None}
           for t in (.2,.1,.05)},'production_authorized_by_this_plan':False}

def covariance(a,b):
    if len(a)!=len(b) or len(a)<=1:raise ValueError('same independent source cohort required')
    N=len(a);return N/(N-1)*(math.fsum(x*y for x,y in zip(a,b))-math.fsum(a)*math.fsum(b)/N)

def histogram(values,weights,edges,N,active=None):
    """Flows included; no silent drop; undefined observables counted separately."""
    import bisect
    if len(values)!=len(weights) or len(values)!=N:raise ValueError('original N cohort required')
    bins=[[] for _ in range(len(edges)+1)];missing=[]
    active=[True]*N if active is None else active
    if len(active)!=N:raise ValueError('selection mask differs from original N')
    for v,w,yes in zip(values,weights,active):
        if not math.isfinite(w):raise ValueError('nonfinite weight')
        if not yes:continue
        if v is None:missing.append(w);continue
        if not math.isfinite(v):raise ValueError('nonfinite observable')
        # Convention [low,high); rightmost edge belongs to overflow.
        bins[bisect.bisect_right(edges,v)].append(w)
    total=math.fsum(w for b in bins for w in b);qall=math.fsum(w*w for b in bins for w in b)
    abs_sum=math.fsum(abs(w) for b in bins for w in b)
    safe=abs(total)>1e-12*max(abs_sum,1e-300);rows=[]
    for j,b in enumerate(bins):
        sw=math.fsum(b);q=math.fsum(w*w for w in b);p=sw/total if safe else None
        var=N/(N-1)*max(0.,q-sw*sw/N)
        shapevar=N/(N-1)*max(0.,q*(1-2*p)+p*p*qall)/(total*total) if safe else None
        lo,hi=wilson(len(b),N)
        rows.append({'bin':j,'low':edges[j-1] if j else None,'high':edges[j] if j<len(edges) else None,
            'flow':'underflow' if j==0 else 'overflow' if j==len(edges) else 'regular',
            'entries':len(b),'empty':not bool(b),'sumw':sw,'sumw2':q,'source_sampling_variance':var,
            'proposal_bin_acceptance_wilson95_low':lo,'proposal_bin_acceptance_wilson95_high':hi,
            'zero_proposal_count_one_sided95_upper':1-.05**(1/N) if not b else None,
            'interval_scope':'source_proposal_count_only; not a finite target-reweight-rate bound without a weight bound',
            'ESS':sw*sw/q if q else 0.,'UNIT_AREA_SHAPE_ONLY':p,
            'bin_precision_status':'EMPTY' if not b else 'LOW_ESS_LT10' if q and sw*sw/q<10 else 'BOUNDED_DIAGNOSTIC_GE10_ESS',
            'unit_area_source_sampling_variance':shapevar,
            'shape_status':'DEFINED' if safe else 'UNDEFINED_ZERO_OR_SIGNED_CANCELLATION',
            'missing_pair_events':len(missing),'missing_pair_weight':math.fsum(missing),'original_N':N})
    return rows
