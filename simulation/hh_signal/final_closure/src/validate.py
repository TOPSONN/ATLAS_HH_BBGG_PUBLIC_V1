"""Portable closure evidence verification; never claims a real survey PASS."""
from .contracts import *
from simulation.hh_signal.semantics_recovery.contract import policy,source_identity as h_sources
from simulation.hh_signal.semantics_recovery.review import coverage

def validate():
    input_identity();e=HERE/'evidence';manifest=read_json(e/'manifest.json')
    require({p.relative_to(e).as_posix() for p in e.rglob('*') if p.is_file()}==
        {r['path'] for r in manifest['files']}|{'manifest.json'},'UNDECLARED_CLOSURE_EVIDENCE')
    for r in manifest['files']:require(sha(e/r['path'])==r['sha256'],'CLOSURE_EVIDENCE_DRIFT:'+r['path'])
    h=read_json(e/'native_method_result.json')
    require(h['policy']['method_source_identity']==h_sources() and h['policy']=={**policy(),'method_source_identity':h_sources()},'NATIVE_METHOD_SOURCE_OR_FROZEN_POLICY_DRIFT')
    require(h['status']=='READY_FOR_AUTHORIZED_NATIVE_VALIDATION' and not h['REAL_SURVEY_EXECUTED'],'NATIVE_RUNTIME_OVERCLAIM')
    require(all(h[k]==0 for k in ['new_physical_ME_calls','new_integrals','new_physical_events']),'UNAUTHORIZED_PHYSICAL_EXECUTION')
    require(len(h['paired_cases'])==7 and all(r['equal'] and r['records']>0 for r in h['paired_cases']),'MISSING_PAIRED_CASE')
    require(len(h['negative_cases'])==10,'MISSING_NATIVE_NEGATIVES')
    for r in h['negative_cases']:
        require(r.get('expected_rejection') or r.get('exit')==87,'NATIVE_NEGATIVE_NOT_REJECTED')
    independent=coverage(h['bounded_native_summaries'])
    require(independent==h['independent_numerical_check'],'INDEPENDENT_NUMERICAL_REGRESSION')
    require(read_json(e/'inode_reuse_failure.json')['status']=='PARTIAL_PRESERVED','FAILURE_EVIDENCE_LOST')
    data=read_json(e/'analysis/existing_source_analysis.json')
    require(data['ME_rows']==6000 and data['new_ME_calls']==data['new_integrals']==data['new_events']==0,'HISTORICAL_ANALYSIS_SCOPE')
    require(data['corrected_target']['status']=='NOT_EXECUTED','CORRECTED_TARGET_OVERCLAIM')
    for k in [2.5,5.]:require(next(r for r in data['benchmarks'] if r['kappa_lambda']==k)['relative_shape_status']=='INCONCLUSIVE_REWEIGHTING','KAPPA_SUPPORT_OVERCLAIM')
    root=read_json(e/'root_object_readback.json')
    require(root['status']=='PASS_READ_ONLY_EXISTING_7000_ROOT_ENTRIES' and root['all_input_sources_unchanged'],'MISSING_NATIVE_ROOT_READBACK')
    p=read_json(e/'preservation.json');require(p['files']==8420 and p['status']=='PASS_FULL_LOCAL_SHA256_INVENTORY','MISSING_HISTORICAL_PRESERVATION')
    native=read_json(e/'native_preparations.json')
    require([r['seed'] for r in native]==[910001,910019,910037,910061],'MISSING_NATIVE_PREPARATION_SEEDS')
    for r in native:
        require(r['STOP80_exit']==80 and r['new_physical_ME_calls']==r['new_integrals']==r['new_independent_events']==0 and
            r['native_runtime_gate']=='NOT_EVALUATED_REAL_SURVEY','NATIVE_PRE_ME_BUILD_OVERCLAIM')
    return {'status':'PASS_AUTHORIZED_ENGINEERING_AND_EXISTING_INPUT_EVIDENCE','Phase7H':'READY_FOR_AUTHORIZED_NATIVE_VALIDATION',
        'Phase7I':'NOT_AUTHORIZED_NOT_EXECUTED','Phase7J_corrected_signal':'NOT_AUTHORIZED_NOT_EXECUTED',
        'native_runtime_gate':'NOT_EVALUATED_REAL_SURVEY','real_ME_calls':0,'new_integrals':0,'new_independent_events':0,
        'final_verdict':'PHASE7_BLOCKED_AUTHORIZATION','independent_method_arithmetic':independent['status']}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
