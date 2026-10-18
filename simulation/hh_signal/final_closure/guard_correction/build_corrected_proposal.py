"""Prepare real binaries, execute initialization only, retain original guards."""
import difflib,resource,time,re,subprocess
from .contract import *
from .overlay import apply
from ..guard_correction.overlay import source as corrected_guard_source
from ..guard_correction.review_contract import (validate_build_approval,
    full_source_identity,guard_descriptor,SCHEMA,binary_identity,
    verify_dependency_sources,verify_compiler)
from .containment import Budget,supervise
from simulation.hh_signal.config_lock.contract import lock,verify_cards
from simulation.hh_signal.semantics_recovery.runner import command
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.integration_audit.audit import save

CHANGED=['SubProcesses/P0_gg_hh/driver.f','Source/dsample.f','Source/ranmar.f','SubProcesses/unwgt.f',
    'Source/rw_events.f','SubProcesses/P0_gg_hh/matrix1.f','SubProcesses/P0_gg_hh/auto_dsig1.f']

def prepare(root, *, build_review=None):
    require(isinstance(build_review,dict),"SEPARATE_BUILD_APPROVAL_REQUIRED")
    validate_build_approval(build_review,build_review.get("revision"),full_source_identity())
    check_revision(build_review["revision"])
    root=safe_root(root);require(not root.exists(),'EXISTING_REVIEW_WORKSPACE_PRESERVED')
    require(sha(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')==PHYSICS_SHA,'PHYSICS_CONTRACT_DRIFT')
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    rows=lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary']
    require(cfg['source_commit']==read_json(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')['MG5_commit'],'MG5_COMMIT_DRIFT')
    for r in rows:require(sha(native/r['path'])==r['sha256'],'PINNED_NATIVE_SOURCE_DRIFT:'+r['path'])
    from simulation.hh_signal.final_closure.src.plans import verify_model_sources
    verify_model_sources(cfg['mg5_path'],read_json(REPO/'metadata/phase7a_model_manifest.json')['installed_model_files'])
    root.mkdir(parents=True);replicas=[];start=time.monotonic();cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'
    verify_compiler(compiler)
    for seed in SEEDS:
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
        flags=[compiler,'-O0','-w','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none','-I'+str(sub),
            '-I'+str(process/'Source'),'-I'+str(process/'Source/MODEL'),'-I'+str(process/'Source/PDF/gammaUPC'),'-J'+str(sub)]
        names=['driver','myamp','genps','unwgt','setcuts','get_color','cuts','cluster','reweight','initcluster','addmothers',
            'setscales','idenparts','dummy_fct','auto_dsig','auto_dsig1','matrix1','hh_pre_sampling_guard']
        files=[HERE/'observers.f90',corrected_guard,sub/'native_io_only.f90']+[sub/(n+'.f') for n in names]+[
            process/'Source'/(n+'.f') for n in ['setrun','rw_events','dsample','ranmar']]
        objects=[]
        for i,file in enumerate(files):
            obj=sub/f'hi_{i}.o';command([*flags,'-c',file,'-o',obj],sub,env);objects.append(obj)
        for i,file in enumerate([h/'anonymous_io.c',HERE/'control.c']):
            obj=sub/f'hi_c_{i}.o';command([str(compiler).replace('gfortran','gcc'),'-O0','-c',file,'-o',obj],sub,env);objects.append(obj)
        exe=folder/'hh_final_integral_reviewed'
        libs=['MadLoop','cts','iregi','dhelas','dsample','model','generic','pdf','gammaUPC','cernlib','bias']
        command([compiler,'-o',exe,*objects,'-L'+str(process/'lib'),*['-l'+n for n in libs],'-lstdc++'],sub,env)
        linked=subprocess.check_output(['ldd',str(exe)],text=True,timeout=30)
        dependency_paths=sorted(set(re.findall(r'(?:=>\s+|^\s*)(/[^\s()]+)',linked,re.M)))
        dependencies=[{'name':Path(path).name,'path':str(Path(path).resolve()),'sha256':sha(Path(path).resolve())} for path in dependency_paths]
        require(dependencies and not 'not found' in linked,'UNRESOLVED_SHARED_LIBRARY')
        preflights=[]
        for stage,mo in [('adaptation',0),('measurement',1)]:
            work=sub/(stage+'_preflight');work.mkdir();(work/'temporary').mkdir()
            for name,value in [('randinit',f'r={seed}'),('iproc.dat','0'),('moffset.dat',str(mo))]:(work/name).write_text(value+'\n')
            for name in NAMED:(work/name).touch()
            r=supervise([exe],work,{**env,'HH_PREFLIGHT_ONLY':'1'},stage_input(stage),Budget(root,wall=120,cpu=60))
            require(any('HI_PREFLIGHT_ZERO_ME' in s for s in r['records']) and not any(s.startswith('HI_COUNTS') for s in r['records']),
                'PREFLIGHT_ME_OR_COMPLETION_OVERCLAIM')
            r.update(stage=stage,scope='ACTUAL_NATIVE_INPUT_PARSE_EXIT_BEFORE_MAPPING_OR_ME',postcondition=no_events(work))
            preflights.append(r)
        denied=sub/'denied_preflight';denied.mkdir();(denied/'temporary').mkdir()
        for name,value in [('randinit',f'r={seed}'),('iproc.dat','0'),('moffset.dat','0')]: (denied/name).write_text(value+'\n')
        r,_=command([exe],denied,{**env,'TMPDIR':str(denied/'temporary'),'HH_PREFLIGHT_ONLY':'0'},expected=80)
        require('SUPERVISOR_REQUIRED' in r.stdout,'UNSUPERVISED_ENTRY_NOT_REJECTED')
        immutable=[{'path':p.relative_to(folder).as_posix(),'sha256':sha(p)} for p in sorted(folder.rglob('*'))
            if p.is_file() and not any(x.endswith('_preflight') for x in p.relative_to(folder).parts)]
        receipt={'seed':seed,'executable':'hh_final_integral_reviewed','executable_sha256':sha(exe),'immutable':immutable,
            'dynamic_dependencies':dependencies,'fortran_compiler_sha256':sha(compiler),
            'preflights':preflights,'unsupervised_exit':80,'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0}
        save(folder/'build.json',receipt);replicas.append(receipt)
    for r in rows:require(sha(native/r['path'])==r['sha256'],'ORIGINAL_SOURCE_CHANGED')
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    manifest={'status':'PREPARED_NEW_EXECUTABLE_REVISION_APPROVAL_REQUIRED','authorized_base_revision':BASE,
        'schema':SCHEMA,'approved_build_source_revision':build_review['revision'],
        'guard_correction':guard_descriptor(),
        'physics_contract_sha256':PHYSICS_SHA,'source_identity':full_source_identity(),'replicas':replicas,'ceilings':CAPS,
        'actual_physical_execution':False,'new_ME_calls':0,'new_integrals':0,'retained_physical_events':0,
        'resources_review_only':{'wall_seconds':time.monotonic()-start,'child_CPU_seconds':after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime}}
    manifest['immutable_binary_identity']=binary_identity(manifest)
    save(root/'review_build.json',manifest);return manifest
