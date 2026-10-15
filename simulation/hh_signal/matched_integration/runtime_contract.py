"""Future receipt acceptance methods. No execution, authorization or mock physics."""
import math,statistics
from .contracts import require,SEEDS

def endpoint(e,stage):
    require(stage in ['adaptation','measurement'],'UNREVIEWED_STAGE')
    require(e=={'initial_points':250,'iterations':4 if stage=='adaptation' else 3,
        'minimum_iterations':4 if stage=='adaptation' else 3,'accuracy':0.,
        'grid_mode':2 if stage=='adaptation' else 0,'moffset':0 if stage=='adaptation' else 1},'UNFROZEN_ENDPOINT')

def resource_gate(wall,cpu,disk,jobs=1,workers=1):
    require(all(math.isfinite(v) and v>=0 for v in [wall,cpu,disk]),'INVALID_RESOURCE_COUNTER')
    require(wall<14400 and cpu<14400 and disk<5*1024**3 and jobs==workers==1,'RESOURCE_CEILING_STOP_PRESERVE_PARTIAL')

def accept_stage_a(receipt,scope):
    require(receipt.get('scope_sha256')==scope,'SCOPE_MISMATCH')
    require(receipt.get('status')=='PASS' and receipt.get('semantics')=='VALIDATED','STAGE_A_NOT_VALIDATED')
    require(type(receipt.get('ME_calls')) is int and receipt['ME_calls']>0,'NO_ACTUAL_ME_EVIDENCE')
    require(receipt.get('seed')==SEEDS[0] and receipt.get('effective_seed')==SEEDS[0],'SEED_IDENTITY')
    require(receipt.get('zero_retained_LHE') is True and receipt.get('output_audit')=='PASS','ZERO_LHE_NOT_PROVEN')
    require(receipt.get('transient_monitoring_coverage') and receipt.get('actual_counters') and receipt.get('grid_history'),
        'MISSING_NATIVE_RUNTIME_COUNTERS_OR_COVERAGE')
    require(receipt.get('termination')=='FIXED_ENDPOINT','PARTIAL_OR_UNKNOWN_STOP')
    resource_gate(**receipt['aggregate_resources']);return True

def grid_identity(rows):
    require([r['seed'] for r in rows]==list(SEEDS),'REPLICA_SEEDS')
    require(len({r['workspace'] for r in rows})==4,'SHARED_REPLICA_WORKSPACE')
    for r in rows:require(r.get('initial_grid')=='FRESH_EMPTY' and not r.get('imported_grid'),'STALE_OR_IMPORTED_GRID')
    return True

def summary(rows):
    """Student t(3) interval across four completed independent matched replicas."""
    grid_identity(rows);require(len({r['integrand_sha256'] for r in rows})==1,'MIXED_INTEGRANDS')
    require(all(r.get('status')=='COMPLETE' for r in rows),'PARTIAL_REPLICAS_NO_FINAL_MEAN')
    values=[r['sigma_pb'] for r in rows];errors=[r['internal_error_pb'] for r in rows]
    require(all(math.isfinite(v) and v>0 for v in values) and all(math.isfinite(v) and v>=0 for v in errors),'INVALID_ESTIMATE')
    mean=statistics.mean(values);sd=statistics.stdev(values);se=sd/2
    return {'mean_pb':mean,'between_replica_sd_pb':sd,'between_replica_SE_pb':se,
        't3_95_interval_pb':[mean-3.182446305284263*se,mean+3.182446305284263*se],
        'internal_errors_pb':errors,'within_run_propagated_SE_pb':math.sqrt(sum(v*v for v in errors))/4,
        'errors_combined':False,'convergence':'NOT_ESTABLISHED_BY_FOUR_REPLICAS_ALONE'}
