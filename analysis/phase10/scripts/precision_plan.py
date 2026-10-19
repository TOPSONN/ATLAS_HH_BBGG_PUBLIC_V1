#!/usr/bin/env python3
"""Phase10F: plan acceptance/rate/bin support from frozen Phase9 measurements."""
import argparse,csv,hashlib,json,math,sys
from collections import defaultdict
from decimal import Decimal,localcontext
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from precision import TARGETS,demand,acceptance_plan,acceptance_n,acceptance_exact_counts,variance_n,ess_scaled_n,kappa_relative_variance,mixture_contract

def load(p):return json.loads(Path(p).read_text())
def rows(p):
    with Path(p).open() as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csvwrite(p,data):
    fields=list(dict.fromkeys(k for r in data for k in r))
    with Path(p).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(data)
def write(p,data):
    with Path(p).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def execute(p9,out):
    demand(not out.exists(),'OUTPUT_MUST_BE_FRESH');stats=p9/'statistics_02';rare=rows(stats/'phase9_rare_event_precision.csv');plots=load(stats/'phase9_plot_data.json');histograms=plots['histograms'];manifest=load(p9/'science_review_final/phase9a_independent_review.json')
    demand(len(rare)==40 and len(histograms)==144,'WRONG_FROZEN_PHASE9_STATISTICS');final=[x for x in rare if x['stage']=='04_MGG_105_160'];demand(len(final)==8,'INCOMPLETE_EIGHT_SOURCES')
    scenarios=[];crosschecks=[]
    for row in final:
        n=int(row['N']);k=int(row['k']);ds=row['dataset_id'];source=float(row['source_sumw_pb']);v=float(row['fixed_original_N_sampling_variance_pb2'])
        for r in TARGETS:
            plan=acceptance_plan(k,n,row['lower'],row['upper'],r);point=plan['N_total_acceptance_point'];decimalpoint=acceptance_n(Decimal(k)/n,r);demand(point==decimalpoint,'INDEPENDENT_EXACT_RATIONAL_PLAN_MISMATCH');crosschecks.append({'dataset_id':ds,'target':r,'rational_N':point,'Decimal80_N':decimalpoint})
            common={'dataset_id':ds,'stage':row['stage'],'pilot_N_original':n,'pilot_survivors':k,'evidence_class':'HISTORICAL_SOURCE_AUDIT','physical_normalization_uncertainty':'UNKNOWN_NOT_INCLUDED','same_proposal_required':True,'new_generation_performed':False,**plan}
            scenarios.append({**common,'precision_quantity':'ACCEPTANCE','pilot_source_sumw_pb':None,'pilot_source_variance_pb2':None,'N_total_weighted_moment_point':None,'interpretation':'Asymptotic Bernoulli plugin; CP95 pilot envelope; unchanged IID proposal and fixed selection; not guaranteed precision.'})
            scenarios.append({**common,'precision_quantity':'WEIGHTED_SELECTED_RAW_SOURCE_RATE','pilot_source_sumw_pb':row['source_sumw_pb'],'pilot_source_variance_pb2':row['fixed_original_N_sampling_variance_pb2'],'N_total_weighted_moment_point':variance_n(n,row['source_sumw_pb'],row['fixed_original_N_sampling_variance_pb2'],r),'interpretation':'N0*Var_pilot(R)/(R^2*r^2), fixed-original-N Bessel variance. Finite-sample moment extrapolation; rare/tail uncertainty unresolved. Own constant BR cancels relative SE; no integration or physical-normalization error combined.'})
        if k==0:
            upper=Decimal(row['one_sided95_upper_if_zero'])
            for divisor in (1,10,100):
                p=upper/divisor
                for r in TARGETS:scenarios.append({'dataset_id':ds,'stage':row['stage'],'pilot_N_original':n,'pilot_survivors':0,'precision_quantity':'ZERO_SURVIVOR_ACCEPTANCE_SCENARIO','target_relative_SE':r,'pilot_acceptance':None,'assumed_p':str(p),'scenario_definition':'one_sided95_p_upper/'+str(divisor),'N_total_acceptance_point':acceptance_n(p,r),'N_total_CP95_lower_p_conservative':None,'guaranteed_precision':False,'evidence_class':'FUTURE_UNEXECUTED_PROPOSAL','status':'ASSUMED_P_SCENARIO_NOT_MEASURED_REQUIREMENT','physical_normalization_uncertainty':'UNKNOWN_NOT_INCLUDED','same_proposal_required':True,'new_generation_performed':False})
    binplan=[]
    for h in histograms:
        if h['stage']!='04_MGG_105_160':continue
        bins=[h['underflow']]+h['bins']+[h['overflow']]
        for index,b in enumerate(bins):
            for r in TARGETS:
                n=h['N_original'];k=b['N'];p=Decimal(k)/n;shapeN=variance_n(n,b['value'],b['variance'],r) if b['value'] is not None and b['variance'] is not None and b['N']>=2 else None
                binplan.append({'dataset_id':h['dataset_id'],'observable':h['observable'],'bin':index,'flow':'UNDERFLOW' if index==0 else 'OVERFLOW' if index==len(bins)-1 else 'REGULAR','pilot_N_original':n,'bin_sources':k,'ESS':b['ESS'],'largest_fraction':b['largest_fraction'],'quality_flag':b['quality_flag'],'target_relative_SE':r,'N_total_bin_acceptance_plugin':acceptance_n(p,r),'N_total_raw_bin_rate_moment':variance_n(n,b['sumw'],b['source_variance'],r),'N_total_normalized_bin_delta_point':shapeN,'N_total_ESS_inverse_variance_proxy':ess_scaled_n(n,b['ESS'],r),'normalization':'Raw bin rate separated from normalized fraction/bin; flows in denominator','status':'NO_FINITE_MEASURED_PLAN_EMPTY_BIN' if k==0 else 'UNSUPPORTED_SINGLETON_SHAPE' if k==1 else 'DEGENERATE_OR_EMPTY_SHAPE_VARIANCE' if shapeN is None else 'CONDITIONAL_MOMENT_EXTRAPOLATION','physical_normalization_uncertainty':'UNKNOWN_NOT_INCLUDED','guaranteed_precision':False})
    kp=[];concentration=defaultdict(list)
    for row in plots['kappa_weight_concentration']:concentration[float(row['kappa_lambda'])].append(row)
    for row in plots['kappa_summary']:
        k=float(row['kappa_lambda'])
        if k not in (2.5,5.):continue
        sources=concentration[k];demand(len(sources)==1000 and len({s['source_event_sha256'] for s in sources})==1000,'KAPPA_SOURCE_IDENTITY_ERROR');selected=[s for s in sources if s['final_selected']];s=math.fsum(q['abs_weight_fraction'] for q in selected);q=math.fsum(q['abs_weight_fraction']**2 for q in selected);demand(math.isclose(s*s/q,row['final_ESS'],rel_tol=2e-11),'FROZEN_KAPPA_ESS_MISMATCH')
        for stage,ess in [('INPUT',row['source_ESS']),('FINAL_MGG',row['final_ESS'])]:
            rv=kappa_relative_variance(1000,ess)
            for r in TARGETS:kp.append({'kappa_lambda':k,'stage':stage,'pilot_original_N':1000,'pilot_ESS':ess,'pilot_relative_MC_SE':float(rv.sqrt()),'target_relative_SE':r,'N_total_old_proposal_moment_point':variance_n(1000,1,rv,r),'N_total_ESS_proxy':ess_scaled_n(1000,ess,r),'top1_input_abs_fraction':row['top1_abs_fraction'],'top1_final_abs_fraction':row['final_top1_abs_fraction'],'status':'INCONCLUSIVE_REWEIGHTING_CONDITIONAL_PLAN_ONLY','interpretation':'Old proposal empirical moments may miss tails; not a production requirement or confidence interval. No new ME weights/events.'})
    out.mkdir();csvwrite(out/'phase10_precision_scenarios.csv',scenarios);csvwrite(out/'phase10_bin_support_plan.csv',binplan);csvwrite(out/'phase10_kappa_support_plan.csv',kp)
    assumptions={'acceptance':'same fixed selection / IID source proposal; CP pilot envelope not future achieved-precision guarantee','weighted_rate':'unbiased raw source trial contributions, finite variance and stable higher moments; N0*pilot variance extrapolation; rare support can invalidate it','histogram':'separate raw bin rate and fraction/bin; normalized delta includes covariance already verified in Phase9; singleton/zero-variance empirical shape plans left undefined','proposal_uncertainty':'Historical proposal acceptance and weight moments do not transport to different matching/PDF/cuts; independent pilot and explicit densities required','physical_normalization':'UNKNOWN/BLOCKED; never folded into source MC precision','resampling':'No bootstrap/resample is counted as a new independent hard event','kappa':'2.5 and5 share old1000 sources; new independent-generation or known-density multiple proposals require separate authorization and full cross-kappa bookkeeping'}
    write(out/'phase10_precision_independent_checks.json',{'status':'PASS_DECIMAL80_VS_EXACT_RATIONAL_ACCEPTANCE_PLANNING','comparisons':len(crosschecks),'checks':crosschecks,'additional_frozen_kappa_ESS_checks':2,'evidence_class':'HISTORICAL_SOURCE_AUDIT'})
    write(out/'phase10_importance_sampling_contract.json',mixture_contract())
    write(out/'phase10_precision_summary.json',{'status':'PASS_ASSUMPTION_EXPLICIT_PRECISION_PLANNING','source_inputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [stats/'phase9_rare_event_precision.csv',stats/'phase9_plot_data.json',p9/'science_review_final/phase9a_independent_review.json']},'scenarios':len(scenarios),'bin_support_rows':len(binplan),'kappa_plan_rows':len(kp),'original_independent_events':7100,'additional_independent_events':0,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'assumptions':assumptions,'physical_total_background':'BLOCKED','physical_significance':'NOT_EVALUATED','B02_20percent_acceptance_N':24975,'B02_20percent_weighted_Bessel_moment_N':25000,'B02_difference_explanation':'Bernoulli plugin p(1-p) vs finite-pilot Bessel variance N0/(N0-1); both conditional estimates, neither guaranteed.'})
    return {'scenarios':len(scenarios),'bin_rows':len(binplan),'kappa_rows':len(kp)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase9',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(execute(a.phase9,a.output)))