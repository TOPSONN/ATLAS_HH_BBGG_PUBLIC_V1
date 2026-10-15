"""Portable verification of bounded actual native Phase7F evidence."""
import json,re
from .contract import *
from .controller import command_guard

def validate():
    evidence=HERE/'evidence';manifest=read_json(evidence/'manifest.json')
    validate_source_inventory(manifest['files'],evidence)
    require({p.relative_to(evidence).as_posix() for p in evidence.rglob('*') if p.is_file()}==
        {r['path'] for r in manifest['files']}|{'manifest.json'},'UNDECLARED_EVIDENCE_FILE')
    plan=read_json(evidence/'plan.json')
    require(plan['lock_sha256']==sha(HERE/'configuration_lock.json') and plan['authorization']=='NOT_AUTHORIZED' and
        plan['NATIVE_RUNTIME_GATE']=='NOT_EVALUATED' and plan['INTEGRATION_EXECUTED']=='NO','PLAN_SCOPE_CHANGED')
    for row in plan['replicas']:
        root=evidence/row['workspace'];seed=row['seed'];cards=root/'cards'
        verify_cards(*[(cards/p).read_text() for p in ['reviewed_run_card.dat','working_run_card.dat','embedded_run_card.dat','run_card.inc']],seed)
        runtime=read_json(root/'runtime_initialization.json');verify_runtime(runtime,seed)
        launch=read_json(root/'launch_command.json');command_guard(launch)
        require(int(launch[launch.index('--seed')+1])==seed,'LAUNCH_SEED_BINDING')
        banner=read_json(cards/'MG5_banner.json')
        require(int(card_values(banner['mgruncard'])['iseed'])==seed and
            'generate g g > h h [noborn=QCD]' in banner['mgproccard'],'BANNER_SEED_OR_PROCESS')
        require(sha(cards/'param_card.dat')==lock()['template_hashes']['param_card.dat'],'PARAM_CARD_IDENTITY')
        built=read_json(root/'native_build.json')
        require(built['executable_sha256']==row['compiled_bridge_sha256'] and built['new_integrals']==built['new_ME_calls']==0 and
            built['unauthorized_native_dispatch_exit']==80 and built['native_pre_sampling_gate_source_sha256']==sha(HERE/'src/pre_sampling_guard.f'),
            'NATIVE_BUILD_OR_DISPATCH_EVIDENCE')
        require('HH_NATIVE_PREFLIGHT_ONLY_ZERO_ME_CALLS' in built['preflight_stdout'] and
            re.search(r'HH_PRE_SAMPLING_CONFIG_PASS\s+'+str(seed)+r'\s+0\s+0',built['preflight_stdout']) is not None,'NATIVE_PREFLIGHT_SEED_EVIDENCE')
    drift=read_json(evidence/'stale_default_probe.json')
    require(drift['reused_working_card_passes'][1]['pdlabel']=='nn23lo1' and
        drift['fresh_frozen_template_passes']==['cteq6l1']*3,'WRITER_DRIFT_REGRESSION')
    gate=read_json(evidence/'gate_probe.json');require([r['exit'] for r in gate['cases']]==[0,71,72,73,74,76,77] and
        gate['source_sha256']==sha(HERE/'src/pre_sampling_guard.f'),'NATIVE_GATE_FAILURE_PATHS')
    writer=read_json(evidence/'writer_probe.json');require(writer['permanent_writer_exit']==86 and
        writer['suppressed_candidate_store_clear']==[1,1,1],'NATIVE_WRITER_BOUNDARIES')
    from simulation.hh_signal.integration_audit.validate import validate as validate_historical_audit
    require(validate_historical_audit()['C_effective_PDF_gate']=='FAIL','HISTORICAL_ERRATUM_LOST')
    return {'status':'PASS_PORTABLE_EFFECTIVE_LOCK_AND_ACTUAL_NATIVE_EVIDENCE','replicas':4,
        'historical_C_target_gate':'FAIL_PRESERVED','absolute_cross_sections':'INCONCLUSIVE',
        'kappa_lambda_2_5_and5':'INCONCLUSIVE_REWEIGHTING','NATIVE_RUNTIME_GATE':'NOT_EVALUATED',
        'INTEGRATION_EXECUTED':'NO','new_ME_calls':0,'new_physical_events':0}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
