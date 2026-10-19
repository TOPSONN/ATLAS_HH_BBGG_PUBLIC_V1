"""Synthetic-method-only two-dimensional photon sidebands.

A=tight isolated (target); B=tight nonisolated; C=anti-tight isolated;
D=anti-tight nonisolated. "Anti-tight" is an external validated disjoint
definition, never inferred from a local numerical shower-shape threshold.
For fake-only F=N-P, kappa=F_A F_D/(F_B F_C), prediction=kappa F_B F_C/F_D.
This library cannot measure or authorize a physical fake rate.
"""
from __future__ import annotations
import math

REGIONS = ("A", "B", "C", "D")
EVIDENCE_CLASS = "SYNTHETIC_METHOD_ONLY"
ORDER = tuple("observed_" + r for r in REGIONS) + tuple("prompt_" + r for r in REGIONS) + ("kappa",)

def region(tight: bool, isolated: bool) -> str:
    if type(tight) is not bool or type(isolated) is not bool:
        raise ValueError("validated exclusive boolean ID and isolation labels required")
    return { (True, True):"A", (True, False):"B", (False, True):"C", (False, False):"D"}[(tight, isolated)]

def _finite(values):
    return all(isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v) for v in values)

def validate_covariance(cov, n):
    if len(cov) != n or any(len(row) != n for row in cov):
        raise ValueError("complete joint covariance required")
    if not all(_finite(row) for row in cov):
        raise ValueError("nonfinite covariance")
    scale = max(1.0, max(abs(v) for row in cov for v in row))
    tol = 1e-10 * scale
    if any(abs(cov[i][j]-cov[j][i]) > tol for i in range(n) for j in range(n)):
        raise ValueError("covariance is not symmetric")
    # PSD Cholesky permits zero modes, but refuses nonzero coupling to a zero pivot.
    lower = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            residual = cov[i][j] - math.fsum(lower[i][k]*lower[j][k] for k in range(j))
            if i == j:
                if residual < -tol: raise ValueError("covariance is not positive semidefinite")
                lower[i][j] = math.sqrt(max(0.0, residual))
            elif lower[j][j] > math.sqrt(tol):
                lower[i][j] = residual/lower[j][j]
            elif abs(residual) > tol:
                raise ValueError("invalid covariance zero mode")
    return cov

def quadratic(g, cov):
    value = math.fsum(g[i]*cov[i][j]*g[j] for i in range(len(g)) for j in range(len(g)))
    if value < -1e-8*max(1.0, max(abs(v) for row in cov for v in row)):
        raise ValueError("negative propagated variance")
    return max(0.0, value)

def event_total_covariance(rows):
    """Fixed-independent-N covariance of a vector total, with full event clusters.

    Each row is one independent source event, with all candidates and subtraction
    contributions already summed by that event. The same event must appear once;
    separate sources must be handled as independent blocks before summation.
    Negative off-diagonals for exclusive categorical regions are retained.
    """
    if len(rows)<2 or not rows or not rows[0]:
        raise ValueError("at least two independent event clusters required")
    n, width = len(rows), len(rows[0])
    if any(len(row)!=width or not _finite(row) for row in rows):
        raise ValueError("invalid cluster vector")
    totals = [math.fsum(row[j] for row in rows) for j in range(width)]
    means = [v/n for v in totals]
    cov = [[n/(n-1)*math.fsum((row[i]-means[i])*(row[j]-means[j]) for row in rows)
            for j in range(width)] for i in range(width)]
    validate_covariance(cov, width)
    return totals, cov

def synthetic_transfer(observed, prompt, kappa, covariance, *, diagnostic_negative=False, denominator_z=3.0):
    if len(observed)!=4 or len(prompt)!=4 or not _finite(observed+prompt+[kappa,denominator_z]):
        raise ValueError("four finite region observations and prompt subtractions required")
    if kappa <= 0 or denominator_z <= 0:
        raise ValueError("positive kappa and stability criterion required")
    if any(v<0 for v in observed+prompt):
        raise ValueError("nonnegative region inputs required")
    validate_covariance(covariance, 9)
    f = [n-p for n,p in zip(observed,prompt)]
    result = {"evidence_class":EVIDENCE_CLASS, "physical_usable":False,
        "input_order":ORDER, "observed":observed, "prompt_subtraction":prompt,
        "fake_only_subtracted":f, "kappa":kappa,
        "definition":"kappa=F_A*F_D/(F_B*F_C); A_prediction=kappa*F_B*F_C/F_D",
        "transfer_semantics":"C/D isolated-to-nonisolated anti-tight yield ratio; not a per-jet fake probability",
        "uncertainty_method":"joint-Jacobian delta covariance; shared-event and subtraction cross-covariance retained",
        "status":"VALID_SYNTHETIC_ESTIMATE", "valid":True}
    if any(v<0 for v in f):
        result.update(status="INVALID_NEGATIVE_SUBTRACTION",valid=False)
        if not diagnostic_negative: return result
    if f[3]<=0:
        result.update(status="INVALID_ZERO_OR_NEGATIVE_DENOMINATOR",valid=False)
        return result
    if f[1]==0 or f[2]==0:
        result.update(status="ZERO_CONTROL_SUPPORT",valid=False)
        return result
    a,b,c,d=f
    prediction=kappa*b*c/d
    transfer=c/d
    # Full 9-vector derivatives, including the prompt estimate as a random variable.
    g=[0,kappa*c/d,kappa*b/d,-kappa*b*c/(d*d),0,-kappa*c/d,-kappa*b/d,kappa*b*c/(d*d),b*c/d]
    gt=[0,0,1/d,-c/(d*d),0,0,-1/d,c/(d*d),0]
    gd=[0,0,0,1,0,0,0,-1,0]
    gr=[1-g[0],-g[1],-g[2],-g[3],-1-g[4],-g[5],-g[6],-g[7],-g[8]]
    var=quadratic(g,covariance)
    residual_var=quadratic(gr,covariance)
    sd=math.sqrt(quadratic(gd,covariance))
    if result["valid"] and (d<=denominator_z*sd):
        result.update(status="ILL_CONDITIONED_DENOMINATOR",valid=False)
    if diagnostic_negative and any(v<0 for v in f):
        result["diagnostic_only"]=True
    result.update(predicted_target=prediction, transfer_factor=transfer,
        prediction_gradient=g, transfer_gradient=gt, closure_gradient=gr,
        prediction_variance=var, prediction_se=math.sqrt(var),
        transfer_variance=quadratic(gt,covariance),
        denominator_se=sd, denominator_stability_z=denominator_z,
        target_closure_residual=a-prediction, target_closure_variance=residual_var,
        target_closure_pull=(a-prediction)/math.sqrt(residual_var) if residual_var>0 else None,
        relative_precision=math.sqrt(var)/abs(prediction) if prediction!=0 else None)
    return result

def validate_physical_fake_source(source):
    """Compatibility contract; a synthetic success never satisfies it."""
    requirements=("validated_tight_antitight", "validated_isolated_nonisolated",
        "conversion_categories", "electron_denominator", "prompt_leakage",
        "background_subtraction", "jet_flavour_composition", "target_closure",
        "full_correlations", "public_license")
    if source.get("evidence_class")=="SYNTHETIC_METHOD_ONLY":
        raise ValueError("synthetic inputs forbidden in physical fake calibration")
    if source.get("semantics")!="JET_TO_PHOTON_TRANSFER_WITH_MATCHED_DENOMINATOR":
        raise ValueError("prompt efficiency or electron transfer is not a jet fake transfer")
    if source.get("status")!="VALIDATED" or not all(source.get(k) is True for k in requirements):
        raise ValueError("BLOCKED_MISSING_COMPATIBLE_OBSERVABLES")
    return True

def synthetic_suite():
    diag=lambda x:[[float(v) if i==j else 0.0 for j,v in enumerate(x)] for i in range(len(x))]
    zero=diag([0]*9)
    f=[120.,80.,60.,40.]; p=[30.,10.,20.,5.]; n=[a+b for a,b in zip(f,p)]
    clean=synthetic_transfer(f,[0.]*4,1.,diag(f+[0.]*5))
    contaminated=synthetic_transfer(n,p,1.,diag(n+p+[0.]))
    correlated=synthetic_transfer([180.,80.,60.,40.],[0.]*4,1.5,zero)
    naive=synthetic_transfer([180.,80.,60.,40.],[0.]*4,1.,zero)
    # Exact same-event prompt fractions: the total covariance has observed-prompt
    # terms, so Var(N-P) differs from the false independent-source approximation.
    rows=[]
    for category,count in enumerate([120,80,60,40]):
        for _ in range(count):
            row=[0.]*8;row[category]=1.;row[category+4]=.25;rows.append(row)
    totals,cov8=event_total_covariance(rows)
    cov9=[r+[0.] for r in cov8]+[[0.]*9]
    shared=synthetic_transfer(totals[:4],totals[4:],1.,cov9)
    independent=[r[:] for r in cov9]
    for i in range(4):
        for j in range(4):independent[i][j+4]=independent[j+4][i]=0.
    false_independence=synthetic_transfer(totals[:4],totals[4:],1.,independent)
    # Independent eventwise influence-function variance, not the matrix contraction.
    g=shared["prediction_gradient"][:8]
    influence=[math.fsum(a*b for a,b in zip(row,g)) for row in rows]
    center=math.fsum(influence)/len(influence)
    independent_variance=len(rows)/(len(rows)-1)*math.fsum((x-center)**2 for x in influence)
    checks={
        "region_exclusivity":len({region(t,i) for t in (True,False) for i in (True,False)})==4,
        "target_closure":abs(clean["target_closure_residual"])<1e-12,
        "prompt_contamination_subtracted":abs(contaminated["predicted_target"]-120)<1e-12,
        "correlation_kappa_corrects_closure":abs(correlated["target_closure_residual"])<1e-12 and abs(naive["target_closure_residual"]-60)<1e-12,
        "zero_D_rejected":synthetic_transfer([1.,1.,1.,0.],[0.]*4,1.,zero)["valid"] is False,
        "zero_C_no_rate_claim":synthetic_transfer([1.,1.,0.,1.],[0.]*4,1.,zero)["status"]=="ZERO_CONTROL_SUPPORT",
        "negative_subtraction_rejected":synthetic_transfer([1.,1.,1.,1.],[0.,2.,0.,0.],1.,zero)["status"]=="INVALID_NEGATIVE_SUBTRACTION",
        "negative_diagnostic_never_valid":synthetic_transfer([1.,1.,1.,1.],[0.,2.,0.,0.],1.,zero,diagnostic_negative=True)["valid"] is False,
        "shared_subtraction_covariance_matters":abs(shared["prediction_variance"]-false_independence["prediction_variance"])>1e-8,
        "independent_influence_variance":math.isclose(shared["prediction_variance"],independent_variance,rel_tol=1e-11,abs_tol=1e-11),
        "ill_conditioned_rejected":synthetic_transfer([1.,2.,1.,1.],[0.]*4,1.,diag([1.]*9))["status"]=="ILL_CONDITIONED_DENOMINATOR",
        "physical_result_never_enabled":all(x["physical_usable"] is False for x in [clean,contaminated,correlated,shared])
    }
    return {"schema_version":1,"evidence_class":EVIDENCE_CLASS,
        "status":"PASS_SYNTHETIC_METHOD_ONLY" if all(checks.values()) else "FAIL_SYNTHETIC_METHOD",
        "checks":checks,"cases":{"independent_closure":clean,"prompt_subtraction":contaminated,
        "correlated_kappa":correlated,"shared_event_subtraction":shared,
        "incorrect_independence_variance":false_independence["prediction_variance"],
        "independent_influence_variance":independent_variance},
        "physical_fake_rate":"UNKNOWN","actual_transfer_measurement":"BLOCKED_MISSING_COMPATIBLE_OBSERVABLES",
        "import_into_physical_results":False,"new_physical_events":0}
