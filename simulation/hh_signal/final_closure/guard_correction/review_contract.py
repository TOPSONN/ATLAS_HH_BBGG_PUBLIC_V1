"""Pure review/receipt predicates. Data descriptors never grant human approval."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[3]
PHYSICS_SHA='a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb'
OLD_BUILD='98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281'
OLD_EXECUTABLES={'c70949e1538fc53e2725c126a1527edf2e268c85e82e4149d3d3a1f46ccd426c',
 '7dc0b4150a9f0a17973e23016b679a16bde5621ab46b48f11a0d9c30badff3ff',
 '1a458edc8320dfe03ef8af681c5d88099f171117b8dc8746def4f2c13f79f3f6',
 'ff465034a83e815be7db974e26f0ff6c88215fa15fb6a76cdd20b66dbbf4f6b3'}
CONSUMED_OR_UNCORRECTED={'58d39888a024028e32f3071db9215c0db6fe0a89','79f779ef6d96340681242f86afe06bc90975728d',
 '1f3c5fc4efa141a0e3e6831aa3b44c0e6bd32ee7','4b1635073b6b1cd3096ee268a3c7858dea3da3b1'}
SCHEMA='HH_ROUTE_A_GUARD_BUILD_REVIEW_V1'
def require(ok,message):
    if not ok:raise ValueError(message)
def identity(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_bindings():
    paths=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.f','.patch','.json']]
    paths +=[REPO/'metadata/phase7i_builder_review_contract.json',REPO/'metadata/phase7i_guard_correction_status.json']
    return [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(paths)]
def full_source_identity():
    from ..integration_runtime.contract import sources
    return sorted(sources()+source_bindings(),key=lambda r:r['path'])
def build_contract():return json.loads((REPO/'metadata/phase7i_builder_review_contract.json').read_text())
def verify_dependency_sources(process):
    contract=build_contract()
    for row in contract['frozen_process_dependencies']:
        p=Path(process)/row['path']
        require(p.is_file() and not p.is_symlink() and sha(p)==row['sha256'],'FINITE_LO_DEPENDENCY_DRIFT:'+row['path'])
    return {'status':'EXACT_FINITE_LO_MODEL_LOOP_AND_LIBRARY_CONTEXT'}
def verify_compiler(compiler):
    for row in build_contract()['compiler_linker_identity']:
        p=Path(compiler).parent/row['name']
        require(p.is_file() and sha(p)==row['sha256'],'COMPILER_LINKER_DRIFT:'+row['name'])

def validate_build_approval(approval,revision,bindings):
    # A trusted operator must first obtain the human's separate BUILD approval.
    # This function only checks its recorded scope/binding; it cannot issue it.
    require(isinstance(approval,dict),'SEPARATE_BUILD_APPROVAL_REQUIRED')
    require(re.fullmatch('[0-9a-f]{40}',revision or '') is not None and revision not in CONSUMED_OR_UNCORRECTED,'CONSUMED_OR_UNCORRECTED_REVISION')
    require(approval.get('action')=='BUILD_ONLY' and approval.get('revision')==revision and
        approval.get('physics_contract_sha256')==PHYSICS_SHA and approval.get('source_binding_identity')==identity(bindings),
        'EXACT_BUILD_SCOPE_AND_SOURCE_REVIEW_REQUIRED')
    require(approval.get('physical_restart_authorized') is False,'BUILD_APPROVAL_CANNOT_AUTHORIZE_RESTART')
    return {'status':'BUILD_REVIEW_BINDING_ONLY_NOT_RESTART_AUTHORIZATION','revision':revision}

def guard_descriptor():
    from .overlay import source,sha as textsha,ORIGINAL_SHA256
    return {'route':'A_FINITE_LO_NO_BORN_ONLY','native_guard_sha256':textsha(source()),'original_guard_sha256':ORIGINAL_SHA256,
        'physics_contract_sha256':PHYSICS_SHA,'model_reference_MU_R_GeV':91.188,
        'source_binding_identity':identity(full_source_identity()),'source_bindings':full_source_identity(),
        'physical_restart_authorized':False}

def validate_build_receipt(receipt,bindings,candidate_hash):
    require(identity(receipt)!=OLD_BUILD and receipt.get('schema')==SCHEMA,'STALE_BUILD_IDENTITY_OR_SCHEMA')
    require(receipt.get('source_identity')==bindings and receipt.get('physics_contract_sha256')==PHYSICS_SHA,'CORRECTED_SOURCE_BINDING_DRIFT')
    guard=receipt.get('guard_correction',{})
    require(guard.get('native_guard_sha256')==candidate_hash and guard.get('source_bindings')==bindings and
        guard.get('source_binding_identity')==identity(bindings) and guard.get('physical_restart_authorized') is False,'GUARD_BINDING_DRIFT')
    require(receipt.get('approved_build_source_revision') not in CONSUMED_OR_UNCORRECTED and
        re.fullmatch('[0-9a-f]{40}',receipt.get('approved_build_source_revision','')) is not None,'CONSUMED_AUTHORIZATION_CANNOT_MIGRATE')
    replicas=receipt.get('replicas',[])
    require([r.get('seed') for r in replicas]==[910001,910019,910037,910061],'FIXED_BUILD_SEED_SET')
    for row in replicas:
        require(re.fullmatch('[0-9a-f]{64}',row.get('executable_sha256','')) is not None and
            row['executable_sha256'] not in OLD_EXECUTABLES,'OLD_OR_MISSING_BINARY_IDENTITY')
        require(row.get('new_ME_calls')==0 and row.get('new_integrals')==0 and row.get('retained_physical_events')==0,'BUILD_MUST_RETAIN_ZERO_ME_SCOPE')
        require(row.get('immutable') and row.get('dynamic_dependencies') and row.get('preflights'),'ACTUAL_BUILD_EVIDENCE_REQUIRED')
    return {'status':'DESCRIPTOR_BINDING_PASS_ONLY_FILE_HASH_AND_NATIVE_PREFLIGHT_VERIFICATION_STILL_REQUIRED','restart_authorized':False}

def binary_identity(receipt):
    # Preparation timestamps/resource use remain evidence, but are not binary
    # identity. Neither identity may be substituted into an old complete receipt.
    return identity({'schema':receipt['schema'],'physics':receipt['physics_contract_sha256'],'sources':receipt['source_identity'],
        'guard':receipt['guard_correction'],'replicas':[{k:r[k] for k in ['seed','executable_sha256','immutable','dynamic_dependencies','fortran_compiler_sha256']} for r in receipt['replicas']]})
