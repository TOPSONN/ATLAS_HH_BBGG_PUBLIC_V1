"""Independent scalar-only audit of this stopped Stage A; cannot dispatch code.

No runtime imports, native execution, candidate data or fabricated final counters.
The absent ME-entry count is an instrumentation observation, not HI_COUNTS.
"""
import math

SOURCE='58d39888a024028e32f3071db9215c0db6fe0a89'

def audit(receipt):
    if receipt.get('reviewed_revision')!=SOURCE:raise ValueError('EXECUTED_SOURCE_MISMATCH')
    if receipt.get('status')!='PARTIAL_NO_REPLACEMENT' or receipt.get('final_verdict')!='BLOCKED_NATIVE_RUNTIME':
        raise ValueError('STOPPED_ATTEMPT_MUST_NOT_BE_PROMOTED')
    stages=receipt.get('stages',[])
    if len(stages)!=1 or stages[0].get('seed')!=910001 or stages[0].get('stage')!='adaptation':
        raise ValueError('FOLLOWUP_WORK_AFTER_STAGE_A_FAILURE')
    if receipt.get('replicas') or receipt.get('actual_integral_stages_completed')!=0:
        raise ValueError('UNSUPPORTED_COMPLETED_INTEGRAL')
    stage=stages[0];r=stage['receipt'];records=r['records']
    if r.get('execution_class')!='REAL_NATIVE_SUPERVISED':raise ValueError('METHOD_EVIDENCE_IS_NOT_NATIVE_DISPATCH')
    if stage.get('status')!='FAILED_PARTIAL_PRESERVED' or r.get('exit')!=92 or r.get('failure')!='NATIVE_EXIT:92':
        raise ValueError('FAILURE_IDENTITY_MISMATCH')
    if 'STOP 92' not in r.get('bounded_runtime_errors',[]):raise ValueError('MISSING_STOP92_DIAGNOSTIC')
    if not r.get('process_group_kill_cleanup') or r.get('raw_streams_retained'):
        raise ValueError('PROCESS_OR_RAW_STREAM_RETENTION_MISMATCH')
    def one(tag):
        rows=[line.split()[1:] for line in records if line.split()[0]==tag]
        if len(rows)!=1:raise ValueError('MISSING_OR_DUPLICATE:'+tag)
        return rows[0]
    if one('HH_PRE_SAMPLING_CONFIG_PASS')!=['910001','0','0']:raise ValueError('INITIAL_SEED_MISMATCH')
    if one('HI_INPUTS')!=['250','4','4','2','0','F']:raise ValueError('ENDPOINT_MISMATCH')
    if one('HI_PDF')!=['cteq6l1']*3:raise ValueError('INITIAL_PDF_MISMATCH')
    if float(one('HI_ALPHA')[0])!=.130 or one('HI_ALPHA')[1]!='1':raise ValueError('INITIAL_ALPHA_MISMATCH')
    seed=list(map(int,one('HI_SEED')))
    if seed[:4]!=[910001,0,0,1]:raise ValueError('RANMAR_CONFIGURATION_MISMATCH')
    expanded=910001*31300
    ij=(1802+1+expanded%30081-1)%31328+1
    kl=(9373+expanded//30081-1)%30081+1
    if seed[4:]!=[ij,kl]:raise ValueError('RANMAR_STATE_MISMATCH')
    tags={line.split()[0] for line in records}
    if tags&{'HI_COMPLETE','HI_RESULT','HI_COUNTS','HI_NATIVE_LOOP_COUNT','HI_ITERATION'}:
        raise ValueError('UNEXPECTED_COMPLETION_OR_FINAL_COUNTER')
    entries=[int(line.split()[1]) for line in records if line.split()[0]=='HI_ME_ENTRY']
    returns=[int(line.split()[1]) for line in records if line.split()[0]=='HI_ME_RETURN']
    if entries and (len(entries)!=1 or entries[0]<1):raise ValueError('INVALID_ENTRY_MARKER')
    if returns and (len(returns)!=1 or not entries or returns[0]>entries[0]):raise ValueError('INVALID_RETURN_MARKER')
    if receipt.get('new_hard_event_production') is not False or receipt.get('retained_physical_LHE_events')!=0:
        raise ValueError('EVENT_PRODUCTION_OR_RETENTION_OVERCLAIM')
    for key in ['aggregate_wall_seconds','aggregate_CPU_seconds']:
        value=receipt[key]
        if not math.isfinite(value) or value<0 or value>14400:raise ValueError('RESOURCE_ENVELOPE:'+key)
    return {'status':'PASS_INDEPENDENT_STOPPED_RECEIPT_AUDIT','real_native_dispatch':True,
        'native_pid':r['pid'],'native_exit':92,'failure':'NATIVE_EXIT:92',
        'observed_outer_ME_entries':entries[0] if entries else 0,
        'observed_outer_ME_returns':returns[0] if returns else 0,
        'final_ME_counter':None,'integrand_calls':None,'completed_integrals':0,
        'sigma_pb':None,'native_internal_error_pb':None,'completed_replicas':0,
        'effective_RANMAR_state':seed,'initial_PDF':'cteq6l1','initial_alpha_s_MZ':.130,'initial_running_loops':1,
        'writer_validation':'NOT_REACHED','full_loop_validation':'NOT_REACHED',
        'point_guard_predicate':'UNKNOWN_AMONG_FIVE_STOP92_BRANCHES',
        'counter_scope':'Flushed HI_ME_ENTRY/RETURN observation; no final HI_COUNTS was emitted. Integrand call count is unavailable.',
        'uncertainty_scope':'No integral/error/replica dispersion exists; missing values are not numeric zero.'}
