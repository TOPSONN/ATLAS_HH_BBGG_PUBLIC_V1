"""Assumption-explicit precision plans; no event generation or physical normalization."""
from decimal import Decimal, localcontext, ROUND_CEILING
from fractions import Fraction
import math

TARGETS=('0.10','0.20','0.30','0.50')
def demand(ok,why):
    if not ok:raise ValueError(why)
def dec(v):
    d=Decimal(str(v));demand(d.is_finite(),'NONFINITE_INPUT');return d
def ceil_count(value):
    demand(value>=0,'NEGATIVE_REQUIREMENT')
    return max(2,int(value.to_integral_value(rounding=ROUND_CEILING)))
def target(v):
    d=dec(v);demand(0<d<1,'INVALID_RELATIVE_SE_TARGET');return d
def acceptance_n(p,r):
    with localcontext() as c:
        c.prec=80;p=dec(p);r=target(r);demand(0<=p<=1,'INVALID_ACCEPTANCE')
        if p==0:return None
        return ceil_count((1-p)/(p*r*r))
def acceptance_exact_counts(k,n,r):
    demand(isinstance(k,int) and isinstance(n,int) and not isinstance(k,bool) and not isinstance(n,bool) and 0<=k<=n and n>0,'INVALID_SOURCE_COUNTS')
    if k==0:return None
    rr=Fraction(str(r));demand(0<rr<1,'INVALID_RELATIVE_SE_TARGET');q=Fraction(n-k,k)/(rr*rr)
    return max(2,(q.numerator+q.denominator-1)//q.denominator)
def variance_n(n,estimate,variance,r):
    with localcontext() as c:
        c.prec=80;demand(n>1,'INVALID_ORIGINAL_N');s=dec(estimate);v=dec(variance);r=target(r);demand(v>=0,'NEGATIVE_VARIANCE')
        if s==0 or v==0:return None
        return ceil_count(Decimal(n)*v/(s*s*r*r))
def acceptance_plan(k,n,lower,upper,r):
    with localcontext() as c:
        c.prec=80;lo=dec(lower);hi=dec(upper);demand(0<=lo<=hi<=1,'INVALID_ACCEPTANCE_INTERVAL');point=acceptance_exact_counts(k,n,r)
        return {'target_relative_SE':str(target(r)),'pilot_acceptance':str(Decimal(k)/n),'N_total_acceptance_point':point,'N_total_CP95_upper_p_optimistic':acceptance_n(hi,r),'N_total_CP95_lower_p_conservative':acceptance_n(lo,r),'pilot_interval_envelope':'CP95_ACCEPTANCE_UNCERTAINTY_ENVELOPE_NOT_FUTURE_PRECISION_COVERAGE','status':'NO_FINITE_MEASURED_GUARANTEE_ZERO_SURVIVORS' if k==0 else 'CONDITIONAL_SAME_IID_PROPOSAL_PLANNING','guaranteed_precision':False}
def ess_scaled_n(n,ess,r):
    with localcontext() as c:
        c.prec=80;r=target(r)
        if ess is None:return None
        e=dec(ess);demand(0<e<=n*(1+Decimal('1e-12')),'INVALID_POSITIVE_WEIGHT_ESS')
        return ceil_count(Decimal(n)/(r*r*e))
def kappa_relative_variance(n,ess):
    with localcontext() as c:
        c.prec=80;e=dec(ess);demand(n>1 and 0<e<=n,'INVALID_ESS')
        return (Decimal(n)/e-1)/(n-1)
def mixture_contract():
    return {'evidence_class':'FUTURE_UNEXECUTED_PROPOSAL','pilot_executed':False,'new_independent_sources':0,'proposal_densities_known':False,'support_validated':False,'normalizing_constants_known':False,'physical_execution_authorized':False,'estimator_if_requirements_met':'q_mix=sum_k a_k g_k; a_k=N_k/N; Rhat=(1/N) sum_{k,i} f(x_ki)/q_mix(x_ki)','fixed_allocation_variance':'sum_k a_k^2 Var_gk[f/q_mix]/N_k; retain within-proposal and cross-kappa source-event covariance','requirements':['Normalized evaluable proposal densities in common phase space','Absolute normalization of every proposal and consistent perturbative scheme','Support wherever target integrand and selection are nonzero','Independent hard sources and immutable event identities','Known unbiased weights including generation filters and decay factors','Independent pilot/closure and influence-tail checks before rate inference'],'forbidden_shortcuts':['Resampled events counted as independent hard statistics','Pooling B100/C1000 with different PDF/alpha identities','Reusing historical acceptance after changing matching, cuts or proposal','Assuming proposal density from observed histogram frequencies','Using unknown nuisance values as zero']}