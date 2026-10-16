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

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'},timeout=30).decode().strip()

def sources():
    return [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(HERE.rglob('*'))
        if p.is_file() and p.suffix in ['.py','.f','.f90','.c'] and 'evidence' not in p.parts]

def check_revision(revision):
    import re
    require(re.fullmatch('[0-9a-f]{40}',revision or '') is not None,'EXACT_REVIEWED_REVISION_REQUIRED')
    require(git('rev-parse','HEAD')==revision,'REVIEWED_REVISION_MISMATCH')
    require(not git('status','--porcelain','--untracked-files=no'),'DIRTY_TRACKED_CHECKOUT')
    git('ls-files','--error-unmatch',*[r['path'] for r in sources()])
    require(sha(REPO/'simulation/hh_signal/final_closure/config/physics_contract.json')==PHYSICS_SHA,'PHYSICS_CONTRACT_DRIFT')
    # This checks identity only. The human's separate approval must be checked
    # in the trusted conversation before an operator invokes execute-reviewed.
    return {'revision':revision,'physics_sha256':PHYSICS_SHA,'source_identity':sources()}

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
