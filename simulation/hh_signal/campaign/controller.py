"""One source reservation per phase; resumptions never regenerate a source."""
import argparse,fcntl,traceback,uuid,resource,sys
from .common import *
from .production import generate_source,validate_source,resume_preintegration
from .chain import run_chain

STATE=REPO/'.local/phase7_campaign'

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',choices=['7b','7c','7d','all'],required=True)
    p.add_argument('--process',choices=['ggf_hh_sm'],default='ggf_hh_sm')
    p.add_argument('--events',type=int)
    p.add_argument('--seed',type=int)
    p.add_argument('--energy',type=float,default=13000.)
    p.add_argument('--output',required=True)
    p.add_argument('--max-hours',type=float)
    p.add_argument('--max-disk-gb',type=float)
    p.add_argument('--kappa-config',default=str(CAMPAIGN/'config/kappa_scan.json'))
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--resume',action='store_true',help='continue the same reserved source, never generate it again')
    return p

def request(args):
    require(args.energy==13000.,'ONLY_FROZEN_13000_GEV_VALIDATED; changing energy needs a separately reviewed campaign')
    require(args.events is None or (args.phase!='all' and args.events==LIMITS[args.phase][0]),'EXACT_AUTHORIZED_PHASE_EVENT_COUNT_REQUIRED')
    require(args.seed is None or 1<=args.seed<=900000000,'INVALID_MG_SEED')
    require(args.phase!='7d' or args.seed is None,'SEED_NOT_APPLICABLE_TO_DETERMINISTIC_SOURCE_REWEIGHT')
    require(args.phase!='all' or args.seed is None,'ALL_USES_DISTINCT_FROZEN_PHASE_SEEDS; select an individual source phase to set its seed')
    for x,ceiling in [(args.max_hours,22 if args.phase=='all' else LIMITS[args.phase][1]),
                      (args.max_disk_gb,20 if args.phase=='all' else LIMITS[args.phase][2])]:
        require(x is None or math.isfinite(x) and 0<x<=ceiling,'INVALID_RESOURCE_CEILING')
    require(Path(args.kappa_config).resolve()==(CAMPAIGN/'config/kappa_scan.json').resolve(),'ONLY_REVIEWED_KAPPA_CONFIG_ACCEPTED')
    scan=read_json(args.kappa_config);require(scan['benchmarks']==[-1,0,1,2,2.5,5],'KAPPA_GRID_DIFFERS')
    require(scan['kappa_top']==1 and scan['source_phase']=='7c' and scan['source_events']==1000 and
        scan['new_independent_events']==0 and scan['held_out_quadratic_benchmarks']==[-1,2.5,5], 'UNREVIEWED_COUPLING_OR_SOURCE_SCAN')
    return safe_output(args.output)

def cache():
    # Registered native cache from actual zero-event initialization, Ward and
    # fixed-point tests. No software download or implicit replacement build.
    if not any((STATE/n).exists() for n in ('model_build.json','native_build.json','loop_prerequisite.json')):
        from .prerequisites import prepare_cache
        prepare_cache(STATE)
    b=read_json(STATE/'model_build.json');n=read_json(STATE/'native_build.json')
    require(b['numerical']['status']=='PASS_ACTUAL_FROZEN_PRODUCTION_PARAMETER_LOOP_GATES','FULL_MASS_GATE')
    w=read_json(STATE/'loop_prerequisite.json')
    require(w['status'].startswith('PASS'),'WARD_GATE')
    for name,row in n['binaries'].items():
        require(sha(row['path'])==row['sha256'] and sha(CAMPAIGN/'src'/(name+'.cxx'))==row['source_sha256'], 'STALE_NATIVE_BINARY_'+name)
    require(sha(n['model_table']['path'])==n['model_table']['sha256'],'STALE_MODEL_BR_TABLE')
    folder=Path(b['build']['private_mg5']).parent
    for name in ('param','run'):
        require(sha(folder/(name+'_card_frozen.dat'))==b['build'][name+'_card_sha256'],'STALE_FROZEN_CARD')
    proc=Path(b['build']['process_template'])/'Cards/proc_card_mg5.dat'
    require('generate g g > h h [noborn=QCD]' in proc.read_text(),'MISSING_NATIVE_PROCESS_HISTORY')
    return b['build'],n

def frozen_phase(prior):
    out=Path(prior['output']);path=out/'phase_receipt.json';p=read_json(path)
    require(p['status']=='PASS_REAL_HH_SOURCE_DECAY_SHOWER_HEPMC_DELPHES_ROOT_MODEL_SCOPE' and
        p['full_count']==prior['events'] and sha(p['source']['path'])==p['source']['sha256'],'FROZEN_PHASE_SOURCE_CHANGED')
    if prior.get('phase_receipt_sha256'):require(sha(path)==prior['phase_receipt_sha256'],'FROZEN_PHASE_RECEIPT_CHANGED')
    for stage in p['stages'].values():
        for row in stage['artifacts'].values():require(sha(row['path'])==row['sha256'],'FROZEN_NATIVE_ARTIFACT_CHANGED')
    return p

def run_phase(args,phase,out,registry,build,native):
    count,hours,disk=LIMITS[phase];hours=min(hours,args.max_hours or hours);disk=min(disk,args.max_disk_gb or disk)
    prior=registry['phases'].get(phase)
    seed=args.seed if args.seed is not None else (20261121 if phase=='7b' else 20261122)
    if phase=='7c':
        b=registry['phases'].get('7b',{})
        require(b.get('status')=='PASS_FULL_CHAIN','PHASE7C_REQUIRES_GENUINE_7B_FULL_CHAIN_PASS')
        frozen_phase(b)
        require(seed!=b['seed'],'INDEPENDENT_PHASES_REQUIRE_DIFFERENT_SEEDS')
    if prior:
        require(args.resume and prior['output']==str(out) and prior['seed']==seed,'SOURCE_ALREADY_RESERVED_NO_REGENERATION')
        if prior['status']=='PASS_FULL_CHAIN':return frozen_phase(prior)
    else:
        require(not args.resume and not out.exists(),'FRESH_OUTPUT_REQUIRED')
        require(sum(p['events'] for p in registry['phases'].values())+count<=1100,'1100_INDEPENDENT_SOURCE_EVENT_CEILING')
    before=resources(out,disk);out.mkdir(parents=True,exist_ok=bool(prior))
    bundle,files=identity()
    if prior:require(prior['source_request']=={'phase':phase,'events':count,'seed':seed},'RESUME_REQUEST_CHANGED')
    else:
        prior={'status':'RESERVED_ONE_ATTEMPT','output':str(out),'events':count,'seed':seed,
            'source_request':{'phase':phase,'events':count,'seed':seed},'source_attempt_id':str(uuid.uuid4()),
            'created_utc':datetime.now(timezone.utc).isoformat(),'controlled_seconds':0}
        registry['phases'][phase]=prior;save_json(STATE/'campaign_registry.json',registry)
    resume_index=len(list(out.glob('execution_*.json')))
    logroot=out/('control_'+str(resume_index));logroot.mkdir(exist_ok=False)
    remaining=hours*3600-prior['controlled_seconds']
    require(remaining>0 and sum(x['controlled_seconds'] for x in registry['phases'].values())<22*3600,'CAMPAIGN_WALLTIME_EXHAUSTED')
    # All current and earlier preparation scratch counts against the disk cap.
    from simulation.new_backgrounds.common import tree_bytes
    scratch=Path.home()/'.local/share/atlas-hh-phase7'
    scratch_bytes=tree_bytes(scratch,readonly_roots=(Path.home()/'opt',Path.home()/'.local/share/atlas-hh-phase6a/toolchain'))
    require(scratch_bytes<disk*GIB,'PREPARATION_SCRATCH_EXCEEDS_PHASE_DISK_CAP')
    m=Monitor(out,{'max_hours':remaining/3600,'max_disk_gb':disk-scratch_bytes/GIB},
        readonly_roots=(scratch,Path.home()/'opt',Path.home()/'.local/share/atlas-hh-phase6a/toolchain'))
    # Separate resumptions need separate log names, while preserving all partials.
    original=m.run_command
    def command(argv,cwd,stage,**kwargs):return original(argv,cwd,'attempt'+str(resume_index)+'_'+stage,**kwargs)
    m.run_command=command
    started=time.monotonic();cpu_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    save_json(logroot/'preflight.json',{'request':vars(args),'phase':phase,'source_request':prior['source_request'],
        'resources':before,'preparation_scratch_bytes_charged':scratch_bytes,'bridge_sha256':bundle,'bridge_files':files})
    try:
        m.install_signals()
        if (out/'source/source_present.json').exists():
            source=read_json(out/'source/source_present.json')
            source['validation']=validate_source(out/'source',phase,seed,build)
            source['requested_seed']=seed;source['effective_seed']=source['validation']['effective_seed'];source['seed']=source['effective_seed']
            source['status']='PASS_GENUINE_INDEPENDENT_FULL_MASS_SOURCE'
            save_json(out/'source/validated_source.json',source)
        else:
            if (out/'source').exists():
                require(args.resume,'PARTIAL_SOURCE_REQUIRES_MANUAL_INSPECTION; no automatic replacement')
                source=resume_preintegration(out/'source',phase,seed,build,m)
            else:source=generate_source(out/'source',phase,seed,build,m,prior['source_request'])
        prior['effective_seed']=source['validation']['effective_seed']
        if phase=='7c':require(prior['effective_seed']!=registry['phases']['7b']['effective_seed'],'ACTUAL_SOURCE_SEEDS_NOT_INDEPENDENT')
        save_json(STATE/'campaign_registry.json',registry)
        result=run_chain(out,source,native,m,phase,710101 if phase=='7b' else 710102,
                         710201 if phase=='7b' else 710202,710301 if phase=='7b' else 710302)
        save_json(out/'phase_receipt.json',result);prior['status']='PASS_FULL_CHAIN';prior['phase_receipt_sha256']=sha(out/'phase_receipt.json')
        if 'failure' in prior:
            prior.setdefault('historical_failures',[]).append(prior.pop('failure'))
            save_json(out/'recovery.json',{'status':'PASS_FULL_CHAIN_AFTER_PRESERVED_EARLIER_FAILURE',
                'historical_failure_receipt_sha256':sha(out/'failure.json'),'phase_receipt_sha256':prior['phase_receipt_sha256']})
        print(phase.upper()+' PASS genuine independent events='+str(count),flush=True)
        return result
    except BaseException as exc:
        prior['status']='PARTIAL_REQUIRES_INSPECTION';prior['failure']=str(exc)
        save_json(out/'failure.json',{'status':'PARTIAL_SIGNAL_PRODUCTION','error':str(exc),'traceback':traceback.format_exc(),
            'source_reservation':prior,'no_automatic_source_replacement':True})
        raise
    finally:
        m.restore_signals();elapsed=time.monotonic()-started;prior['controlled_seconds']+=elapsed
        cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
        save_json(out/('execution_'+str(resume_index)+'.json'),{'metrics':m.metrics(),'elapsed_seconds':elapsed,
           'children_user_cpu_seconds':cpu.ru_utime-cpu_before.ru_utime,'children_system_cpu_seconds':cpu.ru_stime-cpu_before.ru_stime,
           'preparation_scratch_bytes_charged':scratch_bytes,'phase_state':prior})
        save_json(STATE/'campaign_registry.json',registry)

def main(argv=None):
    args=parser().parse_args(argv)
    try:
        out=request(args)
        if args.dry_run:
            print(json.dumps({'status':'DRY_RUN_NO_EVENTS','output':str(out),'phase':args.phase,
                'events':args.events or (1100 if args.phase=='all' else LIMITS[args.phase][0]),
                'energy_gev':args.energy,'software_reinstallation':False,'resume':args.resume},indent=2));return
        STATE.mkdir(parents=True,exist_ok=True)
        with (STATE/'physics.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('ANOTHER_CAMPAIGN_PHYSICS_JOB_IS_RUNNING')
            scientific_environment();build,native=cache()
            registry=read_json(STATE/'campaign_registry.json') if (STATE/'campaign_registry.json').exists() else {'task':ACK,'phases':{}}
            if args.phase in ('7b','7c'):run_phase(args,args.phase,out,registry,build,native)
            elif args.phase=='all':
                for phase in ('7b','7c'):run_phase(args,phase,out/phase,registry,build,native)
                from .reweight import run_reweight
                run_reweight(args,out/'7d',registry,build,native)
            else:
                from .reweight import run_reweight
                run_reweight(args,out,registry,build,native)
    except Exception as exc:
        print('CAMPAIGN_BLOCKED: '+str(exc),file=sys.stderr,flush=True);sys.exit(2)
