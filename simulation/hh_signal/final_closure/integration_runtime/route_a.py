"""Actual Route-A build identities and strict, non-executing file reader.

HH_ROUTE_A_GUARD_BUILD_REVIEW_V1 is the reviewed proposal schema. These predicates
complete its file/protocol checks; they do not certify a build without separate
human binary review, nor grant a physical restart.
"""
import math,re,subprocess
from pathlib import Path,PurePosixPath
from .contract import *
from .approval import CONSUMED
from ..guard_correction.review_contract import OLD_EXECUTABLES,SCHEMA,build_contract,verify_dependency_sources,verify_compiler

GUARD_SHA='404dfd1fb81a3fa9ad7cf18d511caf063674a325c2622785e7fca1d5f4fba123'
ROUTE='A_FINITE_LO_NO_BORN_ONLY'

def full_sources():
    # Bind all Python/native implementation dependencies, frozen cards, physics
    # and historical model/source manifests, not merely this runtime package.
    paths=set()
    for root in [REPO/'simulation/hh_signal',REPO/'simulation/mg5/scripts']:
        paths.update(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and
            p.suffix in ['.py','.f','.f90','.c','.sh','.inc','.dat','.patch'])
    paths.update(p for p in (REPO/'simulation/hh_signal').rglob('*.json') if 'evidence' not in p.parts)
    paths.update(REPO/r['path'] for r in build_contract()['frozen_card_identities'])
    paths.update([REPO/'metadata/phase7a_model_manifest.json',REPO/'metadata/phase7i_builder_review_contract.json',
        REPO/'metadata/phase7i_guard_correction_status.json',REPO/'metadata/phase7_final_route_a_build_contract.json',
        REPO/'metadata/phase7_final_route_a_toolchain.json'])
    return [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in
        sorted(paths,key=lambda p:p.relative_to(REPO).as_posix())]

def descriptor():
    rows=full_sources()
    require(sha(HERE.parent/'guard_correction/native_checks_corrected.f')==GUARD_SHA,'CORRECTED_GUARD_SOURCE_DRIFT')
    return {'route':ROUTE,'native_guard_sha256':GUARD_SHA,'physics_contract_sha256':PHYSICS_SHA,
        'source_binding_identity':identity(rows),'source_bindings':rows,'model_reference_MU_R_GeV':91.188,
        'physical_restart_authorized':False}

def binary_identity(r):
    return identity({k:r[k] for k in ['schema','approved_build_source_revision','physics_contract_sha256',
        'source_identity','guard_correction','frozen_source_cards','toolchain_identity','compile_plans']} | {
        'replicas':[{k:x[k] for k in ['seed','executable','executable_sha256','immutable','dynamic_dependencies',
            'fortran_compiler_sha256']} for x in r['replicas']]})

def identities(r):
    return {'FULL_BUILD_RECEIPT_IDENTITY':identity(r),'IMMUTABLE_BINARY_SOURCE_IDENTITY':binary_identity(r)}

def regular(root,name):
    rel=PurePosixPath(name)
    require(name==rel.as_posix() and not rel.is_absolute() and '..' not in rel.parts and rel.parts,'UNSAFE_RECEIPT_PATH')
    p=Path(root).joinpath(*rel.parts)
    require(not any(q.is_symlink() for q in [p,*p.parents]) and p.is_file(),'MISSING_OR_SYMLINK_BUILD_INPUT:'+name)
    return p

def dependencies(exe):
    # ldd is restricted to locally built, independently reviewed executables.
    text=subprocess.check_output(['ldd',str(exe)],text=True,timeout=30)
    require('not found' not in text,'UNRESOLVED_SHARED_LIBRARY')
    paths=sorted(set(re.findall(r'(?:=>\s+|^\s*)(/[^\s()]+)',text,re.M)))
    require(paths,'MISSING_DYNAMIC_DEPENDENCIES')
    return [{'name':Path(p).name,'path':str(Path(p).resolve()),'sha256':sha(Path(p).resolve())} for p in paths]

def immutable(folder):
    return [{'path':p.relative_to(folder).as_posix(),'sha256':sha(p)} for p in sorted(folder.rglob('*'))
        if p.is_file() and p.relative_to(folder).as_posix()!='build.json' and not any(
            p.is_relative_to(Path(folder)/'process/SubProcesses/P0_gg_hh'/name) for name in
            ['adaptation_preflight','measurement_preflight','denied_preflight','adaptation','measurement'])]

def frozen_inputs():
    from simulation.hh_signal.config_lock.contract import lock
    return {'native':lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary'],
        'cards':build_contract()['frozen_card_identities']}

def toolchain_rows():
    m=read_json(REPO/'metadata/phase7_final_route_a_toolchain.json')
    require(m.get('encoding')=='LOSSLESS_PARENT_DIRECTORY_GROUPS_V1','WRONG_TOOLCHAIN_INVENTORY_ENCODING')
    rows=sorted([{'path':(PurePosixPath(parent)/name).as_posix(),'sha256':h}
        for parent,items in m['groups'].items() for name,h in items],key=lambda row:row['path'])
    require(len(rows)==m['file_count']==8166 and len({r['path'] for r in rows})==len(rows) and
        identity(rows)==m['complete_file_list_sha256'],'LOSSLESS_TOOLCHAIN_INVENTORY_DRIFT')
    require(all(not PurePosixPath(r['path']).is_absolute() and '..' not in PurePosixPath(r['path']).parts and
        re.fullmatch('[0-9a-f]{64}',r['sha256']) for r in rows),'UNSAFE_TOOLCHAIN_INVENTORY')
    return rows

def toolchain(compiler):
    verify_compiler(compiler);root=Path(compiler).parent.parent
    rows=toolchain_rows()
    for item in rows:require(sha(root/item['path'])==item['sha256'],'TOOLCHAIN_INPUT_DRIFT:'+item['path'])
    return rows

def verify_copies(folder,seed):
    from .build import CHANGED
    from .overlay import apply
    native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    frozen=frozen_inputs();process=folder/'process'
    original={p:(native/p).read_text() for p in CHANGED};changed=apply(original,seed)
    for item in frozen['native']:
        rel=item['path'];require(sha(native/rel)==item['sha256'],'HISTORICAL_INPUT_DRIFT')
        if rel in changed:expected=changed[rel].encode()
        elif rel=='Source/run_card.inc':continue
        else:expected=(native/rel).read_bytes()
        require(regular(process,rel).read_bytes()==expected,'FROZEN_COPY_OR_OVERLAY_DRIFT:'+rel)
    for item in frozen['cards']:require(sha(REPO/item['path'])==item['sha256'],'FROZEN_CARD_SOURCE_DRIFT')
    old=REPO/f'simulation/hh_signal/config_lock/evidence/seed_{seed}/cards'
    for src,dst in [('reviewed_run_card.dat','Cards/run_card.dat'),('param_card.dat','Cards/param_card.dat')]:
        require(regular(process,dst).read_bytes()==(old/src).read_bytes(),'COPIED_CARD_DRIFT')
    inc='\n'.join('      '+s.strip() for s in (old/'run_card.inc').read_text().splitlines() if s.strip())+'\n'
    require(regular(process,'Source/run_card.inc').read_bytes()==inc.encode(),'RUN_CARD_INCLUDE_DRIFT')
    verify_dependency_sources(process)
    extra={'process/SubProcesses/P0_gg_hh/native_checks_corrected.f':(HERE.parent/'guard_correction/native_checks_corrected.f').read_bytes(),
        'process/SubProcesses/P0_gg_hh/hh_pre_sampling_guard.f':(REPO/'simulation/hh_signal/config_lock/src/pre_sampling_guard.f').read_bytes(),
        'process/SubProcesses/P0_gg_hh/native_io_only.f90':((REPO/'simulation/hh_signal/semantics_recovery/src/io_and_rng.f90').read_text().split('\nsubroutine hh_trace_stream')[0]+'\n').encode()}
    for name,data in extra.items():require(regular(folder,name).read_bytes()==data,'GENERATED_HELPER_SOURCE_DRIFT')

def validate_receipt(r,root,revision,bindings,*,check_linkage=False):
    require(not any(p.is_symlink() for p in Path(root).rglob('*')),'BUILD_TREE_SYMLINK')
    require(r.get('schema')==SCHEMA,'WRONG_ROUTE_A_RECEIPT_SCHEMA')
    require(re.fullmatch('[0-9a-f]{40}',revision or '') and revision not in CONSUMED and
        r.get('approved_build_source_revision')==revision,'STALE_BUILD_SOURCE_REVISION')
    require(r.get('physics_contract_sha256')==PHYSICS_SHA and r.get('ceilings')==CAPS,'SCIENTIFIC_OR_RESOURCE_CONTRACT_DRIFT')
    require(r.get('source_identity')==bindings and r.get('guard_correction')==descriptor(),'FULL_SOURCE_OR_GUARD_BINDING_DRIFT')
    from .approval import scope
    expected_scope=scope('BUILD_ONLY',revision,Path(root),bindings)
    require(r.get('build_review')=={'status':'EXTERNAL_OPERATOR_REVIEW_SCOPE_BOUND','scope':expected_scope,
        'scope_sha256':identity(expected_scope)},'BUILD_REVIEW_SCOPE_PROVENANCE_DRIFT')
    git_binding=r.get('git_preflight',{});preflight=git_binding.get('git_preflight',{})
    critical={x['path']:x['sha256'] for x in bindings}
    critical[RECOVERY_METADATA]=sha(REPO/RECOVERY_METADATA)
    critical['simulation/hh_signal/final_closure/config/physics_contract.json']=PHYSICS_SHA
    require(git_binding.get('revision')==revision and git_binding.get('physics_sha256')==PHYSICS_SHA and
        preflight.get('status')=='PASS_FULL_TRACKED_PREFLIGHT' and preflight.get('critical_source_sha256')==critical,
        'FULL_TRACKED_GIT_PREFLIGHT_BINDING_REQUIRED')
    require(r.get('frozen_source_cards')==frozen_inputs(),'FROZEN_SOURCE_CARD_BINDING_DRIFT')
    cfg=read_json(REPO/'.local/mg5_installation.json');compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'
    require(r.get('toolchain_identity')==toolchain(compiler),'TOOLCHAIN_RECEIPT_DRIFT')
    from .build_plan import plan
    expected_plans=[{'seed':s,'commands':plan(Path(root)/f'replica_{s}/process',Path(root)/f'replica_{s}',compiler)} for s in SEEDS]
    require(r.get('compile_plans')==expected_plans,'COMPILE_LINK_PLAN_DRIFT')
    require(r.get('actual_physical_execution') is False and
        r.get('new_ME_calls')==r.get('new_integrals')==r.get('retained_physical_events')==0,'BUILD_SCOPE_OVERCLAIM')
    require([x.get('seed') for x in r.get('replicas',[])]==list(SEEDS),'FIXED_BUILD_SEED_SET')
    from .validate import validate_preflight
    for row in r['replicas']:
        folder=Path(root)/f'replica_{row["seed"]}'
        require(not folder.is_symlink(),'BUILD_SYMLINK')
        require(row.get('executable')=='hh_final_integral_reviewed' and row.get('executable_sha256') not in OLD_EXECUTABLES,'HISTORICAL_BINARY_AUDIT_ONLY')
        exe=regular(folder,row['executable']);require(sha(exe)==row['executable_sha256'],'EXECUTABLE_DRIFT')
        require(row.get('immutable')==immutable(folder) and row['immutable'],'INCOMPLETE_OR_EDITED_IMMUTABLE_INVENTORY')
        for item in row['immutable']:require(sha(regular(folder,item['path']))==item['sha256'],'IMMUTABLE_INPUT_DRIFT')
        require(read_json(folder/'build.json')==row,'PER_REPLICA_RECEIPT_DRIFT')
        require(row.get('fortran_compiler_sha256')==sha(compiler),'COMPILER_RECEIPT_DRIFT')
        verify_copies(folder,row['seed'])
        dep=row.get('dynamic_dependencies',[])
        require(dep and len({d['path'] for d in dep})==len(dep),'MISSING_OR_DUPLICATE_DEPENDENCY')
        for d in dep:
            # Loader SONAME may be a symlink name (libgfortran.so.5) while the
            # pinned resolved file ends in .5.0.0. Check both identities without
            # confusing the SONAME with the resolved filename.
            p=Path(d['path']);require(p.is_absolute() and re.fullmatch(r'[A-Za-z0-9_.+\-]+',d['name']) and
                sha(p)==d['sha256'],'SHARED_LIBRARY_DRIFT')
        if check_linkage:require(dependencies(exe)==dep,'ACTUAL_DYNAMIC_LINKAGE_DRIFT')
        require(row.get('new_ME_calls')==row.get('new_integrals')==row.get('retained_physical_events')==0,'REPLICA_SCOPE_OVERCLAIM')
        require([p.get('stage') for p in row.get('preflights',[])]==['adaptation','measurement'],'MISSING_ZERO_ME_PREFLIGHT')
        for p in row['preflights']:
            validate_preflight(p,row['seed'])
            require(p['postcondition']==no_events(folder/'process/SubProcesses/P0_gg_hh'/(p['stage']+'_preflight')),
                'PREFLIGHT_FILES_CHANGED_OR_FABRICATED')
        denial=row.get('unsupervised_denial',{})
        require(row.get('unsupervised_exit')==denial.get('exit')==80 and denial.get('record')=='HI_FAILURE SUPERVISOR_REQUIRED' and
            isinstance(denial.get('wall_seconds'),(int,float)) and denial['wall_seconds']>=0 and denial.get('pid',0)>0,
            'UNSUPERVISED_ENTRY_DENIAL_NOT_MEASURED')
        no_events(folder/'process/SubProcesses/P0_gg_hh/denied_preflight')
    measured=r.get('build_commands',[])
    expected=[]
    for p in expected_plans:expected.extend(p['commands']+[[str(Path(root)/f'replica_{p["seed"]}/hh_final_integral_reviewed')]])
    require([x.get('argv') for x in measured]==expected,'ACTUAL_COMPILE_COMMAND_HISTORY_MISSING')
    expected_exits=[]
    for p in expected_plans:expected_exits.extend([0]*len(p['commands'])+[80])
    for i,x in enumerate(measured):
        require(isinstance(x.get('pid'),int) and x['pid']>0 and math.isfinite(x.get('wall_seconds',math.nan)) and x['wall_seconds']>=0
            and x.get('process_group_kill_cleanup') is True and x.get('exit')==expected_exits[i],'BUILD_COMMAND_MEASUREMENTS_MISSING')
    require(r.get('preparation',{}).get('prepared_at_UTC') and r['preparation'].get('pid',0)>0 and r.get('resources_review_only'),
        'PREPARATION_MEASUREMENTS_MUST_REMAIN_INTACT')
    require(r.get('immutable_binary_identity')==binary_identity(r),'IMMUTABLE_BINARY_SOURCE_IDENTITY_DRIFT')
    return {'status':'PASS_ROUTE_A_FILE_AND_PROTOCOL_CHECKS_BINARY_REVIEW_REQUIRED',**identities(r),
        'physical_restart_authorized':False}
