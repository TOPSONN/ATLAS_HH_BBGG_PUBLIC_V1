"""Predeclared identity, reproducibility and execution boundaries."""
import hashlib,json
from pathlib import Path
from simulation.hh_signal.contracts import require,sha,read_json
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE='a5582e508e452a515670d1edc1d39041e88a8638'
BRANCH='codex/phase7-final-closure'
BASE_BRANCH='codex/phase7g-hh-matched-integration'

def deny_real_execution():
    raise ValueError('NOT_AUTHORIZED_PHASE7H_REAL_ME_OR_INTEGRATION; CLI/environment/files cannot grant human authorization')

def policy():
    return {'schema_version':1,'base_head':BASE,'method_only':True,'new_integrals':0,'new_physical_ME_calls':0,
        'comparison':{'discrete':'EXACT','floating':'BITWISE_EXACT_HEX','absolute_tolerance':0.,'relative_tolerance':0.,
            'justification':'same compiler flags, native computational source and deterministic stream; only regular-file connection differs; native text rounding is retained in both paths',
            'failure_policy':'preserve first divergence; no post-failure tolerance relaxation'},
        'independent_decimal_tolerance':{'relative':1e-12,'absolute':1e-14,
            'justification':'independent high precision sum versus <=270 first-iteration double additions and native variance cancellation; fixed before the independent check'},
        'cases':['adaptation','measurement','negative_accuracy','positive_accuracy','none_pass','forced_secondary_store','candidate_limit'],
        'negative_mutations':['candidate','aux_rng','stopping','grid','arithmetic','tail'],
        'negative_io_cases':['deny_permanent','deny_transient','deny_rebound','deny_rebound_scratch'],
        'adaptation':{'initial_points':250,'iterations':4,'minimum_iterations':4,'accuracy':0.,'grid_mode':2},
        'measurement':{'initial_points':250,'iterations':3,'minimum_iterations':3,'accuracy':0.,'grid_mode':0},
        'scope':'native sample_init/put_point/result, unwgt/write_leshouche/addmothers/store/clear and native text serialization/readback; no sample_full/get_point/phase-space or physical ME call',
        'limits':{'concurrent_jobs':1,'workers':1,'child_CPU_seconds':60,'child_wall_seconds':60,
            'child_file_size_bytes':64*1024**2,'aggregate_wall_seconds':14400,'additional_disk_bytes':5*1024**3}}

def source_identity():
    return [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(HERE.rglob('*'))
        if p.is_file() and p.suffix in ['.py','.f','.f90','.c','.sh'] and 'evidence' not in p.parts]

def identity(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def safe_output(value):
    p=Path(value).expanduser();allowed=Path.home()/'simulations/hh_semantics_recovery'
    require(p.is_absolute() and '..' not in p.parts and p.resolve().is_relative_to(allowed.resolve()) and p.resolve()!=allowed.resolve()
        and not any(x.is_symlink() for x in [p,*p.parents]),'UNSAFE_METHOD_OUTPUT')
    return p
