"""Self-service audit/validation/report/preparation; physical modes remain closed."""
import argparse,json,sys
from .contracts import *
from simulation.hh_signal.integration_audit.audit import save

def audit():
    input_identity()
    from simulation.hh_signal.config_lock.validate import validate as f
    from simulation.hh_signal.matched_integration.validate import validate as g
    from simulation.hh_signal.campaign.validate_references import validate_all
    result={'source_integrity':'PASS_FROZEN_TRACKED_INPUTS','F':f(),'G':g(),'B_C_D':validate_all()}
    root=Path.home()/'simulations/hh_signal_runs/campaign_01'
    rows=list(csv.DictReader((HERE/'config/protected_campaign_inventory.csv').open()))
    result['local_8420']=inventory(root,rows) if root.exists() else {'status':'UNAVAILABLE_ON_THIS_HOST','files':None}
    return result

def validate_evidence():
    from .validate import validate
    return validate()

def execute(mode,out,resume=False,authorization=None):
    require(mode in MODES,'UNKNOWN_MODE');out=safe_output(out)
    binding=identity({'sources':source_identity(),'inputs':input_identity(),'core_evidence':core_evidence_identity(),'mode':mode})
    if resume:
        r=read_json(out/'receipt.json');require(r['scope_sha256']==binding and r['mode']==mode,'UNSAFE_RESUME_SOURCE_CONFIG_DRIFT')
        manifest=read_json(out/'output_manifest.json')
        require(not any(p.is_symlink() for p in out.rglob('*')),'RESUME_SYMLINK')
        require({p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}=={row['path'] for row in manifest}|{'output_manifest.json'},'UNSAFE_RESUME_FILE_SET')
        for row in manifest:require(sha(out/row['path'])==row['sha256'],'UNSAFE_RESUME_OUTPUT_DRIFT')
        require(r['status']!='DENIED','DENIED_RECEIPT_IS_NOT_EXECUTION_AUTHORIZATION')
        return {**r,'resume':'READ_ONLY_VERIFIED_IDENTICAL_SCOPE'}
    require(not out.exists(),'PRESERVE_EXISTING_CLOSURE_RUN');out.mkdir(parents=True)
    try:
        require(authorization is None,'CLI_TOKEN_CANNOT_GRANT_HUMAN_AUTHORIZATION');assert_closed(mode)
        validate_evidence()
        if mode=='audit':result=audit()
        elif mode=='validate':result=validate_evidence()
        elif mode=='report':
            from .existing_analysis import derive
            result=derive(out)
        else:
            from .plans import prepare
            result=prepare(out,corrected=mode=='prepare-corrected-signal')
        receipt={'status':'PASS_CURRENTLY_AUTHORIZED_MODE','mode':mode,'scope_sha256':binding,'result':result,
            'new_physical_ME_calls':0,'new_integrals':0,'new_independent_events':0}
    except Exception as exc:
        receipt={'status':'DENIED' if mode in ['integration','corrected-signal'] or authorization is not None else 'FAILED_PARTIAL_PRESERVED',
            'mode':mode,'scope_sha256':binding,'reason':str(exc),'new_physical_ME_calls':0,'new_integrals':0,'new_independent_events':0}
    save(out/'receipt.json',receipt)
    save(out/'output_manifest.json',[{'path':p.relative_to(out).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()])
    return receipt

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=MODES);p.add_argument('--output',required=True)
    p.add_argument('--resume',action='store_true');p.add_argument('--authorization',help='negative-test input only; never grants authorization')
    a=p.parse_args(argv)
    try:
        r=execute(a.mode,a.output,a.resume,a.authorization)
        print(json.dumps({k:r[k] for k in ['status','mode','scope_sha256','new_physical_ME_calls','new_integrals','new_independent_events']
            if k in r}|{'receipt':str(Path(a.output).expanduser()/'receipt.json'),'reason':r.get('reason')},indent=2))
        return 0 if r['status']=='PASS_CURRENTLY_AUTHORIZED_MODE' else 2
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','mode':a.mode,'reason':str(exc),'new_independent_events':0,'new_integrals':0}));return 2
if __name__=='__main__':raise SystemExit(main())
