"""Separate human authorization, scientific semantics and runtime gates."""
import json,hashlib,math,re
from pathlib import Path
from simulation.hh_signal.contracts import require,sha,read_json

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE='081d29a8499a714faeb9e1296d41ac93d48c82d2'
BASE_BRANCH='codex/phase7f-hh-effective-config-lock'
REQUESTED_BRANCH_ALIAS='codex/phase7f-hh-config-lock'
SEEDS=(910001,910019,910037,910061)
AUTHORIZATION_PHRASE='AUTHORIZE_PHASE7G_HH_INTEGRATION_ONLY_4_REPLICAS'

def authorization_status():
    # No CLI flag, file content, environment variable, plan or test fixture is
    # interpreted as a separate trusted human conversation instruction.
    return {'status':'NOT_GRANTED','physical_integration_enabled':False}

def execution_gate(*,authorization=None,semantics=None,stage_a=None):
    # This preparation revision has no grant issuer or enabled native path.
    require(authorization_status()['status']=='GRANTED','NOT_AUTHORIZED_PHASE7G; separate explicit human instruction absent')
    require(authorization and semantics and semantics['status']=='VALIDATED','BLOCKED_INTEGRATION_SEMANTICS')
    return True

def scope_identity(plan):
    return hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def source_identity():
    paths=[p for p in HERE.rglob('*') if p.is_file() and p.suffix in ['.py','.f','.f90','.sh'] and 'evidence' not in p.parts]
    paths += [REPO/'simulation/hh_signal/config_lock/configuration_lock.json',
        REPO/'simulation/hh_signal/config_lock/contract.py',REPO/'simulation/hh_signal/config_lock/controller.py',
        REPO/'simulation/hh_signal/config_lock/writers.py',REPO/'simulation/hh_signal/config_lock/runtime_bridge.py']
    return [{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted(paths)]

def safe_output(value):
    p=Path(value).expanduser();allowed=Path.home()/'simulations/hh_matched_integration'
    require(p.is_absolute() and '..' not in p.parts and p.resolve().is_relative_to(allowed.resolve()) and
        p.resolve()!=allowed.resolve() and not any(x.is_symlink() for x in [p,*p.parents]),'UNSAFE_MATCHED_PREPARATION_OUTPUT')
    return p

def plan_definition():
    return {'schema_version':1,'task':'PHASE7G_HH_MATCHED_INTEGRATION_ONLY_V1','base_head':BASE,'base_branch':BASE_BRANCH,
        'branch_alias_from_request':REQUESTED_BRANCH_ALIAS,'base_resolution':'verified PR22 exact head; existing branch names preserved',
        'authorization_status':'NOT_GRANTED','native_STOP80':'PRESERVED','permanent_writer_STOP86':'PRESERVED',
        'semantics_gate':'BLOCKED_INTEGRATION_SEMANTICS','stage_A_status':'NOT_EXECUTED','stage_B_status':'NOT_EXECUTED',
        'configuration_lock_sha256':sha(REPO/'simulation/hh_signal/config_lock/configuration_lock.json'),
        'replicas':[{'seed':s,'workspace':'replica_'+str(s),'grid_origin':'FRESH_INDEPENDENT_EMPTY',
            'status':'NOT_EXECUTED','sigma_pb':None,'internal_error_pb':None,'ME_calls':None} for s in SEEDS],
        'stage_A':{'seed':SEEDS[0],'purpose':'first real adaptation survey only, after authorization and semantics review',
            'blocks_other_replicas_until_pass':True,'reuse_policy':'only exact same adaptation endpoint/config; not a final measurement estimate'},
        'endpoints':{'adaptation':{'initial_points':250,'iterations':4,'minimum_iterations':4,'accuracy':0.,'grid_mode':2,'moffset':0},
            'measurement':{'initial_points':250,'iterations':3,'minimum_iterations':3,'accuracy':0.,'grid_mode':0,'moffset':1},
            'native_point_growth':'2x per iteration, not250 constant; initial ME setup calls are separate',
            'stopping':'fixed predeclared endpoint; no accuracy/luminosity early stop; resource/zero-pass/native failure means PARTIAL, never silently accepted'},
        'ceilings':{'concurrent_jobs':1,'workers':1,'aggregate_wall_seconds':14400,'aggregate_CPU_seconds':14400,
            'additional_disk_bytes':5*1024**3,'automatic_expansion':False},
        'cost_planning_only':{'nominal_phase_space_calls_per_replica':250*(15+7),'assumed_exact_helicities':4,
            'nominal_ME_calls_four_replicas':4*4*250*(15+7),'pilot_seconds_per_ME':.0625797962206441,
            'nominal_seconds_excluding_setup':4*4*250*(15+7)*.0625797962206441,
            'scope':'planning extrapolation from old B timing, not a new measurement, guarantee or spending authorization'},
        'required_runtime_evidence':['actual ME counters, distinct from integrand calls','per-iteration estimates and native errors',
            'effective config and original seed plus offsets','all grid snapshots/geometry and provenance',
            'candidate/write/store/overweight counters','loop stability diagnostics','CPU/wall/peak RAM/disk/termination',
            'transient monitoring method, coverage gaps and final zero-event postcondition','hash-bound immutable input envelope'],
        'new_integrals':0,'new_physical_events':0,'convergence':'NOT_EVALUATED','sources':source_identity()}
