"""Review preparation and separately approved, exact-revision native execution.

The revision argument checks identity; it is not human authorization. Codex must
obtain separate approval of a changed executable revision before execute-reviewed.
"""
import argparse,fcntl,json,os,shutil,time,resource
from .contract import *
from .containment import Budget,supervise,capability,StageFailure
from .validate import validate_stage,summarize
from simulation.hh_signal.integration_audit.audit import save

def check_build(root):
    root=safe_root(root);review=read_json(root/'review_build.json')
    require(review['source_identity']==sources() and review['physics_contract_sha256']==PHYSICS_SHA,'REVIEWED_BUILD_SOURCE_DRIFT')
    require([r['seed'] for r in review['replicas']]==list(SEEDS),'PREPARED_SEEDS_DRIFT')
    for r in review['replicas']:
        folder=root/f'replica_{r["seed"]}'
        for row in r['immutable']:require(sha(folder/row['path'])==row['sha256'],'IMMUTABLE_BUILD_INPUT_DRIFT:'+row['path'])
        require(sha(folder/r['executable'])==r['executable_sha256'],'EXECUTABLE_DRIFT')
        for dep in r['dynamic_dependencies']:require(sha(dep['path'])==dep['sha256'],'SHARED_LIBRARY_DRIFT:'+dep['name'])
    return review

def execute_reviewed(root,revision):
    # Human approval is a prerequisite verified outside files/flags/env. This
    # function is not called by review preparation or any positive native test.
    binding=check_revision(revision);root=safe_root(root);review=check_build(root)
    published=read_json(HERE/'evidence/executable_review.json')
    require(identity(review)==published['local_review_build_identity'],'EDITABLE_LOCAL_BUILD_CANNOT_REPLACE_REVIEWED_EXECUTABLE')
    require(not (root/'execution_receipt.json').exists(),'FAILED_OR_COMPLETED_CAMPAIGN_MUST_NOT_RESTART')
    lock_path=Path.home()/'simulations/hh_final_closure/.physical_integral_campaign.lock'
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    lockfile=lock_path.open('a')
    try:fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:lockfile.close();raise ValueError('ANOTHER_PHYSICAL_CAMPAIGN_ACTIVE')
    budget=Budget(root);stages=[];replicas=[];reason=None;verdict='BLOCKED_NATIVE_RUNTIME'
    receipt={'status':'STARTED','reviewed_revision':revision,'binding':binding,'ceilings':CAPS,
        'human_authorization_scope':'external explicit approval of this exact revision required; no flag/file/env grant',
        'stages':stages,'replicas':replicas,'retained_physical_LHE_events':0}
    save(root/'execution_receipt.json',receipt)
    try:
        available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
        require(available>=1024**3 and shutil.disk_usage(root).free>=CAPS['disk_bytes'],'RESOURCE_FREE_RAM_OR_DISK')
        active=[]
        for task in Path('/proc').glob('[0-9]*'):
            if int(task.name)==os.getpid():continue
            try:name=(task/'exe').resolve().name
            except (FileNotFoundError,PermissionError):continue
            if name in ['madevent','mg5_aMC','hh_integral_guarded','hh_final_integral_reviewed']:active.append(int(task.name))
        require(not active,'ANOTHER_NATIVE_GENERATOR_ACTIVE')
        cfg=read_json(REPO/'.local/mg5_installation.json')
        from simulation.hh_signal.campaign.common import mg_environment
        env={k:v for k,v in mg_environment(cfg).items() if not k.startswith('HH_')}
        env['HH_PREFLIGHT_ONLY']='0'
        pairs=set()
        for seed in SEEDS:
            row=next(r for r in review['replicas'] if r['seed']==seed);folder=root/f'replica_{seed}'
            sub=folder/'process/SubProcesses/P0_gg_hh';per={'seed':seed}
            own_grid=None
            for stage,mo in [('adaptation',0),('measurement',1)]:
                budget.check();check_build(root);work=sub/stage;require(not work.exists(),'STALE_STAGE_OR_GRID_REUSE');work.mkdir()
                (work/'temporary').mkdir()
                for name,value in [('randinit',f'r={seed}'),('iproc.dat','0'),('moffset.dat',str(mo))]:(work/name).write_text(value+'\n')
                text=stage_input(stage);(work/'input_app.txt').write_text(text)
                for name in NAMED:(work/name).touch()
                if mo:
                    require(own_grid and sha(own_grid['path'])==own_grid['sha256'],'OWN_ADAPTATION_GRID_REQUIRED')
                    shutil.copyfile(own_grid['path'],work/'ftn25')
                    require(sha(work/'ftn25')==own_grid['sha256'],'GRID_COPY_DRIFT')
                else:require(not (work/'ftn25').exists(),'ADAPTATION_GRID_MUST_BE_FRESH')
                control=capability(seed,revision)
                try:r=supervise([folder/row['executable']],work,env,text,budget,control_fd=control)
                except StageFailure as exc:
                    stages.append({'seed':seed,'stage':stage,'status':'FAILED_PARTIAL_PRESERVED','receipt':exc.receipt});raise
                finally:os.close(control)
                stages.append({'seed':seed,'stage':stage,'status':'PENDING_SCIENTIFIC_VALIDATION','receipt':r})
                facts=validate_stage(r,seed,stage,work)
                check_build(root)
                pair=tuple(facts['RANMAR_base_and_offsets'][-2:]);require(pair not in pairs,'REPLICA_RNG_PAIR_COLLISION');pairs.add(pair)
                facts['receipt']=r;facts['measurement_grid_input_sha256']=None if not mo else own_grid['sha256']
                if not mo:
                    grid=work/'ftn26';require(grid.is_file() and grid.stat().st_size>0,'MISSING_FRESH_ADAPTATION_GRID')
                    own_grid={'path':str(grid),'sha256':sha(grid),'seed':seed};facts['adaptation_grid_sha256']=own_grid['sha256']
                stages[-1]=facts;per[stage]=facts
                save(root/'execution_receipt.json',receipt)
                if seed==SEEDS[0] and stage=='adaptation':receipt['Stage_A']='PASS_GENUINE_NATIVE_SURVEY_WITH_LIMITS'
                # No replacement, restart or alternative backend on any failure.
            replicas.append(per)
            if seed==SEEDS[0]:
                elapsed=time.monotonic()-budget.start;used=budget.used_cpu();leftwall,leftcpu=budget.remaining()
                require(1.5*elapsed*3<leftwall and 1.5*used*3<leftcpu,'RESOURCE_PROJECTED_REMAINING_COST')
        receipt['statistics']=summarize(replicas);verdict=receipt['statistics']['final_verdict']
    except Exception as exc:
        reason=str(exc)
        if 'RESOURCE' in reason or any(x in reason for x in ['NATIVE_EXIT:-24','NATIVE_EXIT:-25','NATIVE_EXIT:-9']):verdict='BLOCKED_RESOURCES'
    finally:
        receipt.update(status='COMPLETE_FIXED_ENDPOINTS' if len(replicas)==4 and reason is None else 'PARTIAL_NO_REPLACEMENT',
            final_verdict=verdict,reason=reason,aggregate_wall_seconds=time.monotonic()-budget.start,
            aggregate_CPU_seconds=budget.used_cpu(),peak_logical_disk_including_observed_unlinked_bytes=budget.peak_disk,
            peak_observed_unlinked_regular_files=budget.peak_anonymous,
            new_hard_event_production=False,retained_physical_LHE_events=0,
            actual_integral_stages_completed=sum(s.get('status')=='PASS_GENUINE_STAGE_WITH_LIMITS' for s in stages))
        save(root/'execution_receipt.json',receipt);fcntl.flock(lockfile,fcntl.LOCK_UN);lockfile.close()
    return receipt

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare-review','verify-build','execute-reviewed'])
    p.add_argument('--output',required=True);p.add_argument('--reviewed-revision');a=p.parse_args(argv)
    try:
        if a.mode=='prepare-review':
            from .build import prepare
            r=prepare(a.output)
        elif a.mode=='verify-build':r=check_build(a.output)
        else:r=execute_reviewed(a.output,a.reviewed_revision)
        print(json.dumps({k:r.get(k) for k in ['status','final_verdict','reason','new_ME_calls','new_integrals','retained_physical_events']}))
        return 0 if r.get('status') not in ['PARTIAL_NO_REPLACEMENT'] else 2
    except Exception as exc:
        out=safe_root(a.output)
        if out.exists() and not (out/'execution_receipt.json').exists():
            save(out/'review_failure.json',{'status':'FAILED_REVIEW_NO_PHYSICAL_DISPATCH','reason':str(exc),'new_ME_calls':0,'new_integrals':0})
        zero=None if (out/'execution_receipt.json').exists() else 0
        print(json.dumps({'status':'BLOCKED_NATIVE_RUNTIME','reason':str(exc),'new_ME_calls':zero,'new_integrals':zero}));return 2

if __name__=='__main__':raise SystemExit(main())
