"""Fixed reviewed scientific and resource envelope. No token grants approval."""
import json,os,subprocess
from pathlib import Path
from simulation.hh_signal.final_closure.src.contracts import REPO,require,sha,identity,read_json
HERE=Path(__file__).resolve().parent
BASE='1f3c5fc4efa141a0e3e6831aa3b44c0e6bd32ee7'
PHYSICS_SHA='a8a093e2ec47283dd9cb503b2c83fe95b89df4761df5fb7afc623fa291c937cb'
SEEDS=(910001,910019,910037,910061)
CAPS={'wall_seconds':14400,'CPU_seconds':14400,'disk_bytes':5*1024**3,'jobs':1,'workers':1}
NAMED=('results.dat','ftn26','grid_information')
FILE_CAP=64*1024**2
CONTROL_MAGIC='HH_FINAL_SUPERVISED_V1'
PREVIOUS_APPROVED_SOURCE='79f779ef6d96340681242f86afe06bc90975728d'
PREVIOUS_FROZEN_BUILD='98aa0054eff5ffd351928bb2adb88e336e5d9fc8372dae53831ca7472d9f4281'
RECOVERY_METADATA='metadata/phase7i_git_precheck_recovery.json'
RECOVERY_SOURCE_PATHS={
    'simulation/hh_signal/final_closure/integration_runtime/'+name for name in
    ['contract.py','git_precheck.py','test_git_precheck.py','run.py','published.py','test_runtime.py']}

def git(*args):
    from .git_precheck import GitGuard
    with GitGuard(REPO) as guard:return guard.git(*args).decode().strip()

def sources():
    return [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(HERE.rglob('*'))
        if p.is_file() and p.suffix in ['.py','.f','.f90','.c'] and 'evidence' not in p.parts]

def verify_source_binding(review,*,public=False,historical_audit=False):
    """Reuse only the exact old native build; never rewrite its stopped receipt.

    A separate committed engineering descriptor binds the changed Python-only
    precheck to the same native bytes. It is not restart authorization. The
    execution route still requires the exact new HEAD and external human review.
    """
    if historical_audit:
        # Frozen old receipts are independently readable; they are NEVER
        # rebound to changed Route-A native sources or accepted for execution.
        m=read_json(REPO/RECOVERY_METADATA)
        expected=m['previous_public_build_identity'] if public else PREVIOUS_FROZEN_BUILD
        require(identity(review)==expected and review['source_identity']==m['previous_execution_source_identity'],
            'HISTORICAL_RECEIPT_IDENTITY_DRIFT')
        return {'status':'HISTORICAL_FROZEN_BUILD_AUDIT_ONLY','restart_authorized':False}
    current=sources()
    if review['source_identity']==current:return {'status':'SOURCE_IDENTICAL_TO_BUILD'}
    m=read_json(REPO/RECOVERY_METADATA)
    require(m['previous_approved_source']==PREVIOUS_APPROVED_SOURCE and
        m['frozen_build_identity']==PREVIOUS_FROZEN_BUILD and m['restart_authorized'] is False,
        'RECOVERY_REVIEW_BINDING_DRIFT')
    expected=m['previous_public_build_identity'] if public else PREVIOUS_FROZEN_BUILD
    require(identity(review)==expected,'UNREVIEWED_NATIVE_BUILD_REBINDING')
    require(review['source_identity']==m['previous_execution_source_identity'] and
        current==m['current_execution_source_identity'],'RECOVERY_SOURCE_IDENTITY_DRIFT')
    old={r['path']:r['sha256'] for r in review['source_identity']};new={r['path']:r['sha256'] for r in current}
    delta={p for p in old.keys()|new.keys() if old.get(p)!=new.get(p)}
    require(delta<=RECOVERY_SOURCE_PATHS and delta==set(m['changed_execution_source_paths']),
        'RECOVERY_CHANGED_NATIVE_OR_UNDECLARED_SOURCE')
    return {'status':'UNCHANGED_NATIVE_BUILD_NEW_SOURCE_REAPPROVAL_REQUIRED',
        'previous_approved_source':PREVIOUS_APPROVED_SOURCE,'frozen_build_identity':PREVIOUS_FROZEN_BUILD,
        'new_source_binding_identity':identity({'previous_build':expected,'current_sources':current}),
        'restart_authorized':False}

def check_revision(revision,*,full=False):
    from .git_precheck import verify_checkout
    # Evaluate source enumeration/hashing inside the independent Git watchdog.
    def required():
        if full:
            from .route_a import full_sources
            return [r['path'] for r in full_sources()]+[RECOVERY_METADATA]
        return [r['path'] for r in sources()]+[RECOVERY_METADATA]
    checked=verify_checkout(REPO,revision,required,
        'simulation/hh_signal/final_closure/config/physics_contract.json',PHYSICS_SHA)
    # This checks identity only. The human's separate approval must be checked
    # in the trusted conversation before an operator invokes execute-reviewed.
    verified=[{'path':p,'sha256':h} for p,h in sorted(checked['critical_source_sha256'].items())
        if Path(p).suffix in ['.py','.f','.f90','.c']]
    return {'revision':revision,'physics_sha256':PHYSICS_SHA,'source_identity':verified,'git_preflight':checked}

def safe_root(value):
    p=Path(value).expanduser();parent=Path.home()/'simulations/hh_final_closure'
    require(p.is_absolute() and '..' not in p.parts and p.resolve().is_relative_to(parent.resolve()) and
        p.resolve()!=parent.resolve() and not any(q.is_symlink() for q in [p,*p.parents]),'UNSAFE_RUNTIME_ROOT')
    return p

def stage_input(stage):
    require(stage in ['adaptation','measurement'],'UNKNOWN_STAGE')
    # Native get_user_params: multichannel=0 means full coherent amplitude.
    # The historical preparation's value1 activates AMP2(SUBDIAG)/sum(AMP2).
    n=4 if stage=='adaptation' else 3
    return f'250 {n} {n}\n0.0\n{2 if stage=="adaptation" else 0}\n0\n0\n1\n'

def no_events(root):
    from simulation.hh_signal.config_lock.writers import output_audit
    return output_audit(root)
