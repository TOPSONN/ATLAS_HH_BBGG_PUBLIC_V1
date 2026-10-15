"""Guarded integration-only preparation and future stage controller."""
import argparse,io,json,math,re,shutil,statistics,sys,time
from pathlib import Path
from .contract import *
from .writers import output_audit,publication_guard,suppress_writers,suppress_permanent_writer
from simulation.hh_signal.integration_audit.audit import save

FORBIDDEN=('generate_events','store_events','combine_events','unweight','pythia','shower','delphes','detector','launch','refine')

def safe_output(raw):
    p=Path(raw).expanduser();allowed=Path.home()/'simulations/hh_config_lock'
    require(p.is_absolute() and '..' not in p.parts and p.resolve().is_relative_to(allowed.resolve()) and
        p.resolve()!=allowed.resolve() and not any(x.is_symlink() for x in [p,*p.parents]),'UNSAFE_ISOLATED_OUTPUT')
    return p

def patch_driver(text,seed):
    require(digest_bytes(text.encode())==lock()['native_sources']['driver.f'],'UNREVIEWED_NATIVE_DRIVER')
    pattern=r'(?im)^(      call init_good_hel\(\))$'
    text,n=re.subn(pattern,'      call hh_before_sampling('+str(seed)+'_8)\n'+
        "      hh_probe_mode='0'\n      call get_environment_variable('HH_PREFLIGHT_ONLY',\n     $ hh_probe_mode)\n"+
        "      if(hh_probe_mode.eq.'1') then\n      call hh_guard_report\n"+
        "      write(*,*) 'HH_NATIVE_PREFLIGHT_ONLY_ZERO_ME_CALLS'\n      stop\n      endif\n"+
        "      write(*,*) 'HH_INTEGRATION_NOT_AUTHORIZED'\n      stop 80\n"+r'\1',text)
    require(n==1,'MISSING_PRE_SAMPLING_NATIVE_BOUNDARY')
    text,n=re.subn(r'(?m)^(      call cpu_time\(t_before\))$',r'      character*1 hh_probe_mode\n\1',text)
    require(n==1,'NATIVE_PROBE_DECLARATION_BOUNDARY');return text

def grid_start(root,stage,own_survey=None):
    root=Path(root);require(stage in ['survey','measurement'],'UNREVIEWED_INTEGRATION_STAGE')
    grids=[p for p in root.rglob('*') if p.is_file() and (p.name.startswith(('ftn','grid_')) or p.name=='results.dat')]
    if stage=='survey':require(not grids,'STALE_GRID_REUSE')
    else:
        require(own_survey and own_survey['workspace']==str(root.resolve()),'CROSS_REPLICA_GRID_REUSE')
        require({p.relative_to(root).as_posix():sha(p) for p in grids}==own_survey['grid_hashes'],'UNVERIFIED_MEASUREMENT_GRID')
    return True

def command_guard(argv):
    require(isinstance(argv,list) and all(isinstance(t,str) for t in argv),'INVALID_COMMAND_VECTOR')
    require(argv and Path(argv[0]).name=='hh_integral_guarded','ONLY_PINNED_NATIVE_BRIDGE_PERMITTED')
    require(not any(re.search(r'\b'+name+r'\b',' '.join(argv),re.I) for name in FORBIDDEN),'FORBIDDEN_INTEGRATION_ONLY_COMMAND')
    return True

def exercise_stage(root,executor,*,elapsed_seconds=0,cpu_seconds=0,disk_bytes=0):
    """Exercise controller mechanics with a supplied METHOD_ONLY executor.

    No native executor can be obtained by this API; real execution stays behind
    deny_execution. Synthetic boundary tests never produce physics evidence.
    """
    require(getattr(executor,'METHOD_ONLY',False) is True,'NATIVE_EXECUTOR_NOT_AUTHORIZED')
    caps=lock()['administrative_ceilings']
    require(0<=elapsed_seconds<caps['aggregate_wall_seconds'] and 0<=cpu_seconds<caps['aggregate_CPU_seconds'] and
        0<=disk_bytes<caps['additional_disk_bytes'],'AGGREGATE_RESOURCE_CEILING')
    before=output_audit(root);executor();after=output_audit(root)
    require(sum(r['bytes'] for r in after['files'])<caps['additional_disk_bytes'],'ADDITIONAL_DISK_CEILING')
    return {'status':'PASS_METHOD_ONLY_CONTROLLER_EXERCISE','before':before,'after':after,'new_integrals':0}

def convergence_method(replicas):
    require(len(replicas)==4 and len({r['seed'] for r in replicas})==4,'FOUR_INDEPENDENT_REPLICA_ENDPOINTS_REQUIRED')
    require(all(r['integrand_lock']==replicas[0]['integrand_lock'] and r['independent_grid'] is True and
        math.isfinite(r['sigma']) and math.isfinite(r['error']) and r['error']>0 for r in replicas),'INVALID_MATCHED_INTEGRAND_ENDPOINTS')
    values=[r['sigma'] for r in replicas];mean=statistics.mean(values);se=statistics.stdev(values)/2
    return {'mean':mean,'between_replica_standard_error':se,'t3_95_interval':[mean-3.182446305284263*se,mean+3.182446305284263*se],
        'within_run_propagated_error_of_mean':math.sqrt(sum(r['error']**2 for r in replicas))/4,
        'scope':'fixed-budget independent replica endpoint method; within/between not blindly added; no convergence claim from four replicas alone'}

def prepare(out):
    from . import native as native_tools
    from .native import preview,initialize_probe,writer_probe,gate_probe
    out=safe_output(out);require(not out.exists(),'EXISTING_OUTPUT_OVERWRITE_FORBIDDEN')
    cfg=read_json(REPO/'.local/mg5_installation.json');native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    target=lock();require(cfg['source_commit']==target['MG5_commit'],'WRONG_MG5_VERSION')
    # Fail before constructing any workspace if installed or historical inputs
    # differ. No historic directory is used as a writable working directory.
    for row in target['frozen_runtime_sources']+target['runtime_build_auxiliary']:require(sha(native/row['path'])==row['sha256'],'FROZEN_SOURCE_CHANGED:'+row['path'])
    for name,value in target['native_support_cards'].items():require(sha(native/'Cards'/name)==value,'FROZEN_PROCESS_OR_MADLOOP_CARD_CHANGED')
    for name,value in target['template_hashes'].items():require(sha(HERE/'templates'/name)==value,'FROZEN_TEMPLATE_CHANGED')
    mg=Path(cfg['mg5_path']);expected=read_json(REPO/'simulation/hh_signal/integration_audit/evidence/native_source_identity.json')
    require(sha(mg/'madgraph/various/banner.py')==expected['files']['madgraph/various/banner.py'],'NATIVE_WRITER_CHANGED')
    for name,value in expected['files'].items():require(sha(mg/name)==value,'PINNED_MG5_SOURCE_CHANGED:'+name)
    native_tools.BUDGET=native_tools.ProbeBudget(out.parent)
    out.mkdir(parents=True);replicas=[]
    for seed in SEEDS:
        replica=out/f'seed_{seed}';replica.mkdir();cards=replica/'cards';cards.mkdir();work=replica/'runtime';work.mkdir()
        text=(HERE/'templates/run_card.dat').read_text()
        for key,value in [('nevents',0),('iseed',seed)]:
            text,n=re.subn(r'(?m)^([^\n=!]+)(\s*=\s*'+key+r'\b[^\n]*)$',lambda m:str(value)+m[2],text)
            require(n==1,'AMBIGUOUS_FROZEN_TEMPLATE')
        for name in ['reviewed_run_card.dat','working_run_card.dat','embedded_run_card.dat']:(cards/name).write_text(text)
        (cards/'param_card.dat').write_bytes((HERE/'templates/param_card.dat').read_bytes())
        previews=[preview(text,mg) for _ in range(3)];require(len(set(previews))==1,'NATIVE_WRITER_DRIFT')
        (cards/'run_card.inc').write_text(previews[0]);verify_cards(text,text,text,previews[0],seed)
        # Real MG5 Banner object, prepared before any integral/event. A later
        # runtime banner must be independently checked again after compilation.
        from madgraph.various.banner import Banner
        banner=Banner();banner.add_text('MGRunCard',text);banner.add_text('slha',(cards/'param_card.dat').read_text())
        banner.add_text('MGProcCard','import model loop_sm\ngenerate g g > h h [noborn=QCD]\n')
        save(cards/'MG5_banner.json',dict(banner))
        launch=['hh_integral_guarded','--seed',str(seed),'--stage','survey'];command_guard(launch)
        save(replica/'launch_command.json',launch)
        runtime=initialize_probe(replica/'native_probe',native,seed,previews[0],cfg)
        runtime.update({'launch_seed':int(launch[launch.index('--seed')+1]),'banner_seed':int(card_values(banner['mgruncard'])['iseed']),
            'run_identity_seed':seed,'source_manifest_sha256':sha(HERE/'configuration_lock.json')})
        verify_runtime(runtime,seed);save(replica/'runtime_initialization.json',runtime)
        bridge=replica/'bridge_source';bridge.mkdir()
        for name,data in [('unwgt.f',suppress_writers((native/'SubProcesses/unwgt.f').read_text())),
            ('rw_events.f',suppress_permanent_writer((native/'Source/rw_events.f').read_text())),
            ('driver.f',patch_driver((native/'SubProcesses/P0_gg_hh/driver.f').read_text(),seed)),
            ('hh_pre_sampling_guard.f',(HERE/'src/pre_sampling_guard.f').read_text())]:(bridge/name).write_text(data)
        grid_start(work,'survey');publication_guard(work)
        replicas.append({'seed':seed,'workspace':replica.name,'native_initialization':'PASS_NO_INTEGRAL_PROBE',
            'compiled_bridge_executable':None,'independent_grid':'FRESH_EMPTY_DIRECTORY','future_measurement_moffset':1})
    writer=writer_probe(out/'writer_probe',native,cfg);save(out/'writer_probe.json',writer)
    gate=gate_probe(out/'gate_probe',native,cfg,out/f'seed_{SEEDS[0]}/native_probe/src/get_pdfup.f')
    save(out/'gate_probe.json',gate)
    from .build_bridge import build
    for replica in replicas:
        root=out/replica['workspace'];receipt=build(root,native,cfg);save(root/'native_build.json',receipt)
        replica['compiled_bridge_executable']='native_build/hh_integral_guarded'
        replica['compiled_bridge_sha256']=receipt['executable_sha256']
    # No trust in a one-time snapshot: verify source/template bytes again.
    for row in target['frozen_runtime_sources']+target['runtime_build_auxiliary']:require(sha(native/row['path'])==row['sha256'],'SOURCE_CHANGED_DURING_PREPARATION')
    for name,value in target['template_hashes'].items():require(sha(HERE/'templates'/name)==value,'TEMPLATE_CHANGED_DURING_PREPARATION')
    for name,value in target['native_support_cards'].items():require(sha(native/'Cards'/name)==value,'SUPPORT_CARD_CHANGED_DURING_PREPARATION')
    for name,value in expected['files'].items():require(sha(mg/name)==value,'MG5_SOURCE_CHANGED_DURING_PREPARATION')
    native_tools.BUDGET.check(force_disk=True)
    plan={'schema_version':1,'base_head':BASE,'lock_sha256':sha(HERE/'configuration_lock.json'),
        'status':'PREPARED_PROBES_EXECUTED_NO_INTEGRATION','replicas':replicas,'new_integrals':0,'new_physical_events':0,
        'INTEGRATION_EXECUTED':'NO','authorization':'NOT_AUTHORIZED','NATIVE_RUNTIME_GATE':'NOT_EVALUATED',
        'ceilings':target['administrative_ceilings'],'source_hashes_checked_before_after':True,
        'bridge_design':'direct isolated native driver; pre-sampling PDF/alpha/seed/scale/mass gate, suppressed candidate/store bodies and fatal permanent writer; no MG survey command dispatcher',
        'native_pre_sampling_gate_execution':'PASS_INITIALIZATION_ONLY_MODE; exit before first helicity/ME call',
        'native_integral_execution':'NOT_EXECUTED; both Python and native integral dispatch unconditionally denied',
        'eventual_physical_LHE_embedded_source_card':'NOT_EVALUATED_NO_PHYSICAL_EVENTS_ALLOWED; prepared Banner is not a generated-source banner',
        'stages':[{'name':'survey','grid':'independent fresh adaptation','moffset':0},
            {'name':'measurement','grid':'own survey grid, hash-bound; fixed grid input=0','moffset':1}],
        'future_acceptance':'separate reviewed authorization, full patched native build/hash and native zero-retention runtime validation required; preserve all iteration estimates/ME counters/grids; no automatic budget expansion'}
    save(out/'plan.json',plan)
    save(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]})
    return validate_plan(out)

def validate_plan(out):
    out=safe_output(out);plan=read_json(out/'plan.json');manifest=read_json(out/'manifest.json')
    require(plan['authorization']=='NOT_AUTHORIZED' and plan['NATIVE_RUNTIME_GATE']=='NOT_EVALUATED' and
        plan['INTEGRATION_EXECUTED']=='NO' and plan['lock_sha256']==sha(HERE/'configuration_lock.json'),'PLAN_AUTHORIZATION_OR_LOCK_CHANGED')
    require({r['seed'] for r in plan['replicas']}==set(SEEDS),'REPLICA_SEEDS_CHANGED')
    validate_source_inventory(manifest['files'],out)
    require({p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}=={r['path'] for r in manifest['files']}|{'manifest.json'},'UNEXPECTED_WORKSPACE_FILE')
    for replica in plan['replicas']:
        root=out/replica['workspace'];seed=replica['seed'];cards=root/'cards'
        verify_cards(*[(cards/n).read_text() for n in ['reviewed_run_card.dat','working_run_card.dat','embedded_run_card.dat','run_card.inc']],seed)
        verify_runtime(read_json(root/'runtime_initialization.json'),seed);grid_start(root/'runtime','survey');publication_guard(root/'runtime')
    return {'status':'PASS_PREPARATION_NATIVE_NO_INTEGRAL_PROBES_AND_MANIFEST','replicas':4,
        'NATIVE_RUNTIME_GATE':'NOT_EVALUATED','INTEGRATION_EXECUTED':'NO','new_physical_events':0,'new_integrals':0}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--validate',action='store_true');p.add_argument('--execute',action='store_true')
    args=p.parse_args(argv)
    try:
        if args.execute:deny_execution('independent integral')
        print(json.dumps(validate_plan(args.output) if args.validate else prepare(args.output),indent=2));return 0
    except Exception as exc:print('CONFIG_LOCK_BLOCKED: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
