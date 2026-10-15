"""Portable actual preparation/RNG evidence, never a native survey PASS."""
import json,re
from .contracts import *
from simulation.hh_signal.config_lock.contract import validate_source_inventory,lock

def validate():
    from simulation.hh_signal.config_lock.validate import validate as prior
    require(prior()['NATIVE_RUNTIME_GATE']=='NOT_EVALUATED','HISTORICAL_GATE_CHANGED')
    root=HERE/'evidence';manifest=read_json(root/'manifest.json')
    validate_source_inventory(manifest['files'],root)
    require({p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}==
        {r['path'] for r in manifest['files']}|{'manifest.json'},'UNDECLARED_MATCHED_EVIDENCE')
    plan=read_json(root/'plan.json');require(plan==plan_definition(),'FROZEN_PREPARATION_SOURCE_OR_SCOPE_DRIFT')
    require(read_json(root/'scope_identity.json')['scope_sha256']==scope_identity(plan),'SCOPE_SHA')
    rng=[(root/('rng_mode_'+str(i)+'.txt')).read_text() for i in [0,1]]
    trace=lambda t:re.findall(r'RANMAR_TRACE\s+\d+\s+(\S+)',t)
    require(len(trace(rng[0]))==16 and trace(rng[0])==trace(rng[1]),'NATIVE_RNG_REGRESSION')
    require(re.findall(r'AUXILIARY_NEXT\s+(.*)',rng[0])!=re.findall(r'AUXILIARY_NEXT\s+(.*)',rng[1]),'AUXILIARY_NOT_EXERCISED')
    s=read_json(root/'semantics.json')
    require(s['status']=='BLOCKED_INTEGRATION_SEMANTICS' and not s['native_survey_executed'] and
        s['new_ME_calls']==s['new_integrals']==s['new_physical_events']==0,'SEMANTICS_OVERCLAIM')
    frozen={r['path']:r['sha256'] for r in lock()['frozen_runtime_sources']}
    for row in s['source_audit']:require(row['sha256']==frozen[row['path']],'SOURCE_AUDIT_NOT_FROZEN')
    for row in s['probe_sources']:require(sha(REPO/row['path'])==row['sha256'],'NATIVE_PROBE_SOURCE_DRIFT')
    require('41.000000' in (root/'fixed_weight.txt').read_text(),'FIXED_WEIGHT_RECEIPT')
    cli=read_json(root/'cli_checks.json')
    require(cli['preparation_exit']==cli['validation_exit']==0 and cli['denied_exits']==[2,2,2] and
        cli['overwrite_exit']==2 and cli['no_denied_output_created'],'ACTUAL_CLI_FAILURE_PATHS')
    p=read_json(root/'preservation.json');require(p['unchanged_files']==8420 and p['changed_files']==0 and p['file_set_unchanged'],'HISTORICAL_PRESERVATION')
    return {'status':'PASS_PREPARATION_AND_NONINTEGRATING_METHOD_EVIDENCE','authorization_status':'NOT_GRANTED',
        'NATIVE_SURVEY_EXECUTED':False,'WRITER_SEMANTICS_VALIDATED':False,'scientific_gate':'BLOCKED_INTEGRATION_SEMANTICS',
        'new_ME_calls':0,'new_integrals':0,'new_physical_events':0,'replica_results':'ALL_NOT_EXECUTED',
        'native_runtime_ME_grid_tail_transient_tests':'NOT_EVALUATED_REQUIRES_AUTHORIZATION_AND_SEMANTICS'}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
