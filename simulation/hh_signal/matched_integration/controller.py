"""Prepare frozen two-stage scope; every physical execute request is denied."""
import argparse,json,sys
from pathlib import Path
from .contracts import *
from simulation.hh_signal.integration_audit.audit import save
from simulation.hh_signal.config_lock.contract import validate_source_inventory

def prepare(out):
    out=safe_output(out);require(not out.exists(),'PRESERVE_EXISTING_MATCHED_PLAN')
    from simulation.hh_signal.config_lock.validate import validate
    require(validate()['NATIVE_RUNTIME_GATE']=='NOT_EVALUATED','HISTORICAL_GUARD_STATE_CHANGED')
    plan=plan_definition();out.mkdir(parents=True)
    for replica in plan['replicas']:
        root=out/replica['workspace'];root.mkdir();(root/'adaptation').mkdir();(root/'measurement').mkdir()
        source=REPO/'simulation/hh_signal/config_lock/evidence'/('seed_'+str(replica['seed']))/'cards'
        cards=root/'cards';cards.mkdir()
        for name in ['reviewed_run_card.dat','param_card.dat','run_card.inc','MG5_banner.json']:
            (cards/name).write_bytes((source/name).read_bytes())
        for stage,endpoint in plan['endpoints'].items():
            if stage not in ['adaptation','measurement']:continue
            e=endpoint
            text=f"{e['initial_points']} {e['iterations']} {e['minimum_iterations']}\n0.0\n{e['grid_mode']}\n1\n0\n1\n"
            (root/stage/'input_app.txt').write_text(text)
            (root/stage/'iproc.dat').write_text('0\n');(root/stage/'moffset.dat').write_text(str(e['moffset'])+'\n')
            (root/stage/'randinit').write_text('r='+str(replica['seed'])+'\n')
    save(out/'plan.json',plan);save(out/'scope_identity.json',{'scope_sha256':scope_identity(plan),'authorization':'NOT_GRANTED'})
    save(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
        for p in sorted(out.rglob('*')) if p.is_file()]})
    return validate_plan(out)

def validate_plan(out):
    out=safe_output(out);plan=read_json(out/'plan.json');manifest=read_json(out/'manifest.json')
    require(plan==plan_definition(),'FROZEN_SCOPE_OR_SOURCE_CHANGED')
    require(read_json(out/'scope_identity.json')['scope_sha256']==scope_identity(plan),'SCOPE_HASH_MISMATCH')
    validate_source_inventory(manifest['files'],out)
    require({p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}==
        {r['path'] for r in manifest['files']}|{'manifest.json'},'UNDECLARED_PREPARED_OUTPUT')
    for replica in plan['replicas']:
        cards=out/replica['workspace']/'cards'
        frozen=REPO/'simulation/hh_signal/config_lock/evidence'/('seed_'+str(replica['seed']))/'cards'
        for name in ['reviewed_run_card.dat','param_card.dat','run_card.inc','MG5_banner.json']:
            require((cards/name).read_bytes()==(frozen/name).read_bytes(),'PREPARED_CARD_DRIFT:'+name)
        for stage in ['adaptation','measurement']:
            root=out/replica['workspace']/stage
            e=plan['endpoints'][stage]
            require((root/'input_app.txt').read_text()==f"{e['initial_points']} {e['iterations']} {e['minimum_iterations']}\n0.0\n{e['grid_mode']}\n1\n0\n1\n",'NATIVE_INPUT_DRIFT')
            require((root/'randinit').read_text()=='r='+str(replica['seed'])+'\n' and
                (root/'iproc.dat').read_text()=='0\n' and (root/'moffset.dat').read_text()==str(e['moffset'])+'\n','SEED_OFFSET_DRIFT')
            require(not any(p.name.startswith('ftn') or p.name=='results.dat' for p in root.rglob('*')),'STALE_GRID_OR_RESULT')
    require(not any(p.is_symlink() for p in out.rglob('*')),'PREPARATION_SYMLINK')
    return {'status':'PASS_FROZEN_PREPARATION_ONLY','authorization_status':'NOT_GRANTED',
        'semantics_gate':'BLOCKED_INTEGRATION_SEMANTICS','new_integrals':0,'new_physical_events':0,'native_survey_executed':False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True)
    p.add_argument('--validate',action='store_true');p.add_argument('--execute',action='store_true')
    p.add_argument('--authorization',help='accepted only to demonstrate it cannot grant authorization')
    a=p.parse_args(argv)
    try:
        if a.execute or a.authorization is not None:execution_gate(authorization=a.authorization)
        print(json.dumps(validate_plan(a.output) if a.validate else prepare(a.output),indent=2));return 0
    except Exception as exc:print('MATCHED_INTEGRATION_BLOCKED: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
