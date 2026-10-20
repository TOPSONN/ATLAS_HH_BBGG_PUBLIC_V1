"""Active Route-A builder. Separate human BUILD_ONLY approval is mandatory."""
import difflib,resource,time,re,subprocess,os,datetime
from .contract import *
from .overlay import apply
from ..guard_correction.overlay import source as corrected_guard_source
from .route_a import (full_sources as full_source_identity,descriptor as guard_descriptor,
    SCHEMA,binary_identity,verify_dependency_sources,verify_compiler,dependencies,
    immutable,frozen_inputs)
from .approval import verify as verify_human_review,scope as review_scope
from .build_plan import plan
from .build_process import invoke as bounded_invoke
from .validate import validate_preflight
from .containment import Budget,supervise
from simulation.hh_signal.config_lock.contract import lock,verify_cards
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.integration_audit.audit import save

CHANGED=['SubProcesses/P0_gg_hh/driver.f','Source/dsample.f','Source/ranmar.f','SubProcesses/unwgt.f',
    'Source/rw_events.f','SubProcesses/P0_gg_hh/matrix1.f','SubProcesses/P0_gg_hh/auto_dsig1.f']

def prepare(root, *, build_review=None, revision=None):
    # No work, clone, compiler or native executable before both gates.
    root=safe_root(root)
    approval=verify_human_review(build_review,review_scope('BUILD_ONLY',revision,root,full_source_identity()))
    from ..resource_closure.worker import require_build_enclosure
    enclosure=require_build_enclosure(root)
    binding_sources=full_source_identity()
    binding=check_revision(revision,full=True)
    from ..resource_closure.worker import emit as resource_emit,journal
    resource_emit('BUILD_SOURCE_PREFLIGHT_VERIFIED',revision=revision,binding_sha256=identity(binding))
    require(not root.exists(),'EXISTING_REVIEW_WORKSPACE_PRESERVED')
    require(sha(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')==PHYSICS_SHA,'PHYSICS_CONTRACT_DRIFT')
    overrides={'LD_PRELOAD','LD_AUDIT','GCC_EXEC_PREFIX','COMPILER_PATH','LIBRARY_PATH','CPATH','C_INCLUDE_PATH','CPLUS_INCLUDE_PATH','GFORTRAN_CONVERT_UNIT','GFORTRAN_OPTIONAL_PLUS'}
    require(not overrides.intersection(os.environ),'UNREVIEWED_COMPILER_OR_RUNTIME_ENVIRONMENT')
    cfg=read_json(REPO/'.local/mg5_installation.json');env={k:v for k,v in mg_environment(cfg).items() if not k.startswith('HH_')}
    env.update(OMP_NUM_THREADS='1',OMP_THREAD_LIMIT='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        TMPDIR='/tmp',TMP='/tmp',TEMP='/tmp')
    native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    rows=lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary']
    require(cfg['source_commit']==read_json(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')['MG5_commit'],'MG5_COMMIT_DRIFT')
    for r in rows:require(sha(native/r['path'])==r['sha256'],'PINNED_NATIVE_SOURCE_DRIFT:'+r['path'])
    from simulation.hh_signal.final_closure.src.plans import verify_model_sources
    verify_model_sources(cfg['mg5_path'],read_json(REPO/'metadata/phase7a_model_manifest.json')['installed_model_files'])
    root.mkdir(parents=True);replicas=[];plans=[];command_receipts=[];loader_receipts=[];initializations=[];start=time.monotonic();cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
    budget=Budget(root)
    prepared_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    def checkpoint():
        resource_emit('BUILD_CHECKPOINT',commands=len(command_receipts),completed_replicas=len(replicas),
            initializations=len(initializations),loader_commands=len(loader_receipts),
            aggregate_wall_seconds=time.monotonic()-start,aggregate_CPU_seconds=budget.used_cpu())
        if command_receipts:journal('BUILD_LAST_COMMAND',command_receipts[-1])
        if loader_receipts:journal('BUILD_LAST_LOADER',loader_receipts[-1])
        if initializations:journal('BUILD_LAST_INITIALIZATION',initializations[-1])
        save(root/'partial_build.json',{'status':'BUILD_ONLY_BOOKKEEPING_NO_RETRY','preparation_pid':os.getpid(),
            'prepared_at_UTC':prepared_at,'commands':command_receipts,'completed_replicas':replicas,
            'initializations':initializations,'loader_commands':loader_receipts,
            'aggregate_wall_seconds':time.monotonic()-start,'aggregate_CPU_seconds':budget.used_cpu(),
            'peak_disk_bytes':budget.peak_disk,'new_ME_calls':0,'new_integrals':0})
    def invoke(argv,cwd,env,expected=0):
        resource_emit('BUILD_CHILD_ENTER',argv=list(map(str,argv)),expected_exit=expected)
        try:result,measurement=bounded_invoke(argv,cwd,env,budget,expected)
        except BaseException as exc:
            if hasattr(exc,'build_measurement'):command_receipts.append(exc.build_measurement)
            checkpoint();raise
        command_receipts.append(measurement)
        checkpoint()
        return result,measurement['wall_seconds']
    def enclosed_loader(argv):
        resource_emit('BUILD_LOADER_ENTER',argv=list(map(str,argv)))
        try:result,measurement=bounded_invoke(argv,root,env,budget)
        except BaseException as exc:
            if hasattr(exc,'build_measurement'):loader_receipts.append(exc.build_measurement)
            checkpoint();raise
        loader_receipts.append(measurement);checkpoint()
        return result
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'
    verify_compiler(compiler)
    from .route_a import toolchain
    tools=toolchain(compiler)
    for seed in SEEDS:
        budget.check()
        folder=root/f'replica_{seed}';process=folder/'process';process.mkdir(parents=True)
        for r in rows:
            target=process/r['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((native/r['path']).read_bytes())
        require(not any(p.is_symlink() for p in process.rglob('*')),'BUILD_SYMLINK')
        sub=process/'SubProcesses/P0_gg_hh';cards=process/'Cards';cards.mkdir()
        original={rel:(native/rel).read_text() for rel in CHANGED};transformed=apply(original,seed)
        patches=folder/'overlays';patches.mkdir()
        for rel,text in transformed.items():
            (process/rel).write_text(text)
            (patches/(Path(rel).name+'.patch')).write_text(''.join(difflib.unified_diff(original[rel].splitlines(True),
                text.splitlines(True),fromfile='frozen/'+rel,tofile='isolated/'+rel)))
        verify_dependency_sources(process)
        for item in frozen_inputs()['cards']:
            require(sha(REPO/item['path'])==item['sha256'],'FROZEN_CARD_DRIFT')
        old=REPO/f'simulation/hh_signal/config_lock/evidence/seed_{seed}/cards'
        card=(old/'reviewed_run_card.dat').read_text();include=(old/'run_card.inc').read_text()
        verify_cards(card,card,card,include,seed)
        (cards/'run_card.dat').write_text(card);(cards/'param_card.dat').write_bytes((old/'param_card.dat').read_bytes())
        (process/'Source/run_card.inc').write_text('\n'.join('      '+s.strip() for s in include.splitlines() if s.strip())+'\n')
        h=REPO/'simulation/hh_signal/semantics_recovery/src'
        (sub/'native_io_only.f90').write_text((h/'io_and_rng.f90').read_text().split('\nsubroutine hh_trace_stream')[0]+'\n')
        (sub/'hh_pre_sampling_guard.f').write_bytes((REPO/'simulation/hh_signal/config_lock/src/pre_sampling_guard.f').read_bytes())
        corrected_guard=sub/'native_checks_corrected.f'
        corrected_guard.write_text(corrected_guard_source())
        require(sha(corrected_guard)==guard_descriptor()['native_guard_sha256'],'CORRECTED_GUARD_BYTES_DRIFT')
        jobs=plan(process,folder,compiler);plans.append({'seed':seed,'commands':jobs})
        for argv in jobs:
            require(not Path(argv[argv.index('-o')+1]).exists(),'STALE_BUILD_OBJECT_OR_EXECUTABLE')
            invoke(argv,sub,env)
        exe=folder/'hh_final_integral_reviewed'
        linked_dependencies=dependencies(exe,runner=enclosed_loader)
        preflights=[]
        for stage,mo in [('adaptation',0),('measurement',1)]:
            work=sub/(stage+'_preflight');work.mkdir();(work/'temporary').mkdir()
            for name,value in [('randinit',f'r={seed}'),('iproc.dat','0'),('moffset.dat',str(mo))]:(work/name).write_text(value+'\n')
            for name in NAMED:(work/name).touch()
            resource_emit('BUILD_NATIVE_ZERO_ME_ENTER',seed=seed,stage=stage)
            try:r=supervise([exe],work,{**env,'HH_PREFLIGHT_ONLY':'1'},stage_input(stage),budget)
            except BaseException as exc:
                if hasattr(exc,'receipt'):initializations.append({'seed':seed,'stage':stage,'failed_receipt':exc.receipt})
                checkpoint();raise
            initializations.append({'seed':seed,'stage':stage,'receipt':r});checkpoint()
            require(any('HI_PREFLIGHT_ZERO_ME' in s for s in r['records']) and not any(s.startswith('HI_COUNTS') for s in r['records']),
                'PREFLIGHT_ME_OR_COMPLETION_OVERCLAIM')
            r.update(stage=stage,scope='ACTUAL_NATIVE_INPUT_PARSE_EXIT_BEFORE_MAPPING_OR_ME',postcondition=no_events(work))
            validate_preflight(r,seed);preflights.append(r)
        denied=sub/'denied_preflight';denied.mkdir();(denied/'temporary').mkdir()
        for name,value in [('randinit',f'r={seed}'),('iproc.dat','0'),('moffset.dat','0')]: (denied/name).write_text(value+'\n')
        r,denial_wall=invoke([exe],denied,{**env,'TMPDIR':str(denied/'temporary'),'HH_PREFLIGHT_ONLY':'0'},expected=80)
        require('SUPERVISOR_REQUIRED' in r.stdout,'UNSUPERVISED_ENTRY_NOT_REJECTED')
        receipt={'seed':seed,'executable':'hh_final_integral_reviewed','executable_sha256':sha(exe),'immutable':immutable(folder),
            'dynamic_dependencies':linked_dependencies,'fortran_compiler_sha256':sha(compiler),
            'preflights':preflights,'unsupervised_exit':80,
            'unsupervised_denial':{'exit':r.returncode,'record':'HI_FAILURE SUPERVISOR_REQUIRED',
                'pid':command_receipts[-1].get('pid'),'wall_seconds':denial_wall},'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0}
        save(folder/'build.json',receipt);replicas.append(receipt);checkpoint()
    for r in rows:require(sha(native/r['path'])==r['sha256'],'ORIGINAL_SOURCE_CHANGED')
    require(full_source_identity()==binding_sources,'SOURCE_CHANGED_DURING_BUILD')
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    manifest={'status':'PREPARED_NEW_EXECUTABLE_REVISION_APPROVAL_REQUIRED','authorized_base_revision':BASE,
        'schema':SCHEMA,'approved_build_source_revision':revision,
        'build_review':approval,'git_preflight':binding,'frozen_source_cards':frozen_inputs(),
        'toolchain_identity':tools,'compile_plans':plans,'build_commands':command_receipts,
        'resource_envelope':enclosure,'loader_commands':loader_receipts,
        'preparation':{'pid':os.getpid(),'prepared_at_UTC':prepared_at},
        'guard_correction':guard_descriptor(),
        'physics_contract_sha256':PHYSICS_SHA,'source_identity':full_source_identity(),'replicas':replicas,'ceilings':CAPS,
        'actual_physical_execution':False,'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0,
        'resources_review_only':{'wall_seconds':time.monotonic()-start,'child_CPU_seconds':after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime,
            'peak_disk_bytes':budget.peak_disk,'peak_anonymous_files':budget.peak_anonymous}}
    manifest['immutable_binary_identity']=binary_identity(manifest)
    save(root/'review_build.json',manifest)
    from .route_a import validate_receipt
    validate_receipt(manifest,root,revision,full_source_identity(),check_linkage=True,linkage_runner=enclosed_loader)
    save(root/'review_build.json',manifest)
    return manifest
