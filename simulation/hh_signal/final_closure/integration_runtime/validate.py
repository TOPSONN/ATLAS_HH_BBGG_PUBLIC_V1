"""Validate genuine stage receipts; synthetic fixtures cannot certify physics."""
import math,re,statistics
from .contract import *

def one(records,name):
    rows=[s.split()[1:] for s in records if s.split()[0]==name]
    require(len(rows)==1,'MISSING_OR_DUPLICATE_PROTOCOL:'+name);return rows[0]

def number(s):
    x=float(s.replace('D','E'));require(math.isfinite(x),'NONFINITE_PROTOCOL');return x

def seed_pair(base,io,joffset,config):
    seed=base*31300;ij=1802+config+seed%30081;kl=9373+seed//30081+io+joffset
    while ij>31328:ij-=31328
    while kl>30081:kl-=30081
    return ij,kl

def validate_preflight(r,seed):
    require(r.get('execution_class')=='REAL_NATIVE_SUPERVISED' and r.get('exit')==0 and r.get('failure') is None and
        r.get('process_group_kill_cleanup') is True and r.get('raw_streams_retained') is False,'INVALID_ZERO_ME_PREFLIGHT')
    require(isinstance(r.get('pid'),int) and r['pid']>0 and math.isfinite(r.get('wall_seconds',math.nan)) and r['wall_seconds']>=0,
        'MISSING_ACTUAL_PREFLIGHT_MEASUREMENTS')
    require(set(r.get('raw_stream_SHA256',{}))=={'stdout','stderr'} and all(re.fullmatch('[0-9a-f]{64}',v)
        for v in r['raw_stream_SHA256'].values()),'MISSING_PREFLIGHT_STREAM_IDENTITIES')
    require(set(r.get('raw_stream_bytes',{}))=={'stdout','stderr'} and r['raw_stream_bytes']['stdout']>0 and
        all(isinstance(x,int) and 0<=x<16*1024**2 for x in r['raw_stream_bytes'].values()),'INVALID_PREFLIGHT_STREAM_COUNTS')
    records=r['records'];mo=0 if r['stage']=='adaptation' else 1;n=4 if mo==0 else 3
    require(one(records,'HI_PREFLIGHT_ZERO_ME')==[],'PREFLIGHT_ENDPOINT_MISSING')
    require(one(records,'HH_PRE_SAMPLING_CONFIG_PASS')==list(map(str,[seed,0,mo])),'PREFLIGHT_SEED_DRIFT')
    require(one(records,'HI_INPUTS')==['250',str(n),str(n),'2' if mo==0 else '0','0','F'],'PREFLIGHT_ENDPOINT_DRIFT')
    require(one(records,'HI_PDF')==['cteq6l1']*3,'PREFLIGHT_PDF_DRIFT')
    a=one(records,'HI_ALPHA');require(number(a[0])==.13 and a[1]=='1','PREFLIGHT_ALPHA_DRIFT')
    require(list(map(number,one(records,'HI_MASS')))==[125.,173.,4.7],'PREFLIGHT_MASS_DRIFT')
    s=one(records,'HI_SCALE');require(s[0]=='4' and number(s[1])==.5 and s[2:]==['F','F','F'],'PREFLIGHT_SCALE_DRIFT')
    b=one(records,'HI_BEAMS');require(list(map(number,b[:2]))==[6500.,6500.] and b[2:]==['1','1'],'PREFLIGHT_BEAM_DRIFT')
    allowed={'HH_PRE_SAMPLING_CONFIG_PASS','HI_INPUTS','HI_PDF','HI_ALPHA','HI_MASS','HI_SCALE','HI_BEAMS','HI_PREFLIGHT_ZERO_ME','H_IO'}
    require(all(s.split()[0] in allowed for s in records),'PREFLIGHT_ME_OR_EXTRA_PROTOCOL')
    # Initialization opens one verified anonymous sink; these are I/O-boundary
    # counters, not event-writer or ME counters. Preserve the actual protocol.
    io=one(records,'H_IO');require(list(map(int,io))==[1,1],'PREFLIGHT_ANONYMOUS_IO_DRIFT')
    require(r.get('scope')=='ACTUAL_NATIVE_INPUT_PARSE_EXIT_BEFORE_MAPPING_OR_ME' and
        r.get('postcondition',{}).get('retained_event_records')==0,'PREFLIGHT_ZERO_RETENTION_NOT_VERIFIED')
    return {'status':'PASS_INITIALIZATION_ONLY_NO_ME'}

def validate_stage(receipt,seed,stage,work):
    require(receipt.get('execution_class')=='REAL_NATIVE_SUPERVISED','METHOD_FIXTURE_IS_NOT_PHYSICAL_EVIDENCE')
    require(receipt['exit']==0 and not receipt['failure'] and not receipt['raw_streams_retained'],'FAILED_NATIVE_STAGE')
    records=receipt['records'];one(records,'HI_COMPLETE');n=4 if stage=='adaptation' else 3;mo=0 if n==4 else 1
    inp=one(records,'HI_INPUTS');require(inp==['250',str(n),str(n),'2' if mo==0 else '0','0','F'],'WRONG_NATIVE_ENDPOINT_OR_AMPLITUDE')
    require(one(records,'HI_PDF')==['cteq6l1']*3,'ACTUAL_NATIVE_PDF_MISMATCH')
    a=one(records,'HI_ALPHA');require(number(a[0])==.13 and a[1]=='1','ACTUAL_NATIVE_ALPHA_MISMATCH')
    require(list(map(number,one(records,'HI_MASS')))==[125.,173.,4.7],'NATIVE_MASS_MISMATCH')
    scale=one(records,'HI_SCALE');require(scale[0]=='4' and number(scale[1])==.5 and scale[2:]==['F','F','F'],'NATIVE_SCALE_MISMATCH')
    beams=one(records,'HI_BEAMS');require(list(map(number,beams[:2]))==[6500.,6500.] and beams[2:]==['1','1'],'NATIVE_BEAM_MISMATCH')
    initial=list(map(int,one(records,'HH_PRE_SAMPLING_CONFIG_PASS')))
    require(initial==[seed,0,mo],'INITIAL_NATIVE_SEED_OFFSET_MISMATCH')
    ss=list(map(int,one(records,'HI_SEED')));require(len(ss)==6 and ss[:3]==[seed,0,mo*3157],'ACTUAL_RANMAR_BASE_RESET')
    require(tuple(ss[4:])==seed_pair(*ss[:4]),'ACTUAL_RANMAR_INITIALIZATION_MISMATCH')
    its=[list(map(number,s.split()[1:])) for s in records if s.startswith('HI_ITERATION ')]
    require(len(its)==n and all(r[0]==i and r[1]==250*2**(i-1) and r[2]>=r[1] and r[3]>0 and r[4]>0 for i,r in enumerate(its,1)),
        'ITERATION_COMPLETENESS_OR_POINT_GROWTH')
    counts=one(records,'HI_COUNTS');calls,loops,writes,points=map(int,counts[:4]);maxprec=number(counts[4])
    require(calls>0 and loops>0 and writes>0 and points>0,'MISSING_GENUINE_RUNTIME_COUNTERS')
    require(int(one(records,'HI_NATIVE_LOOP_COUNT')[0])==loops,'NATIVE_ME_COUNTER_DISAGREEMENT')
    require(int(one(records,'HI_ME_ENTRY')[0])==loops and int(one(records,'HI_ME_RETURN')[0])==loops,'INCOMPLETE_ME_ENTRY_RETURN_PAIR')
    codes=[list(map(int,s.split()[1:])) for s in records if s.startswith('HI_LOOP_CODE ')]
    require(sum(r[1] for r in codes)==loops and all(r[0]//100!=4 for r in codes),'LOOP_DIAGNOSTIC_FAILURE')
    result=list(map(number,one(records,'HI_RESULT')))
    require(result[0]>0 and result[1]>0 and int(result[3])==n,'INVALID_NATIVE_RESULT')
    io=list(map(int,one(records,'H_IO')));require(io[0]>0 and io[1]>=writes,'SCRATCH_WRITER_NOT_VALIDATED')
    tails=[list(map(number,s.split()[1:])) for s in records if s.startswith('HI_TAIL ')]
    require(tails and all(r[0]>=r[1]>=0 and r[2]>=0 for r in tails),'MISSING_CANDIDATE_TAIL_DIAGNOSTICS')
    audit=no_events(work)
    require(set(p.name for p in Path(work).iterdir())<=set(NAMED)|{'ftn25','randinit','iproc.dat','moffset.dat','input_app.txt','temporary'},'UNEXPECTED_RUNTIME_OUTPUT')
    return {'status':'PASS_GENUINE_STAGE_WITH_LIMITS','seed':seed,'stage':stage,
        'sigma_pb':result[0],'native_internal_error_pb':result[1],'native_last3_chi2':result[2],
        'iterations':its,'loop_return_codes':codes,'ME_outer_entries':loops,'integrand_calls':calls,
        'PDF_and_scale_checked_points':points,'maximum_reported_precision':maxprec,
        'RANMAR_base_and_offsets':ss,'native_candidates_and_tails':tails,
        'native_unweight_count_in_anonymous_scratch':int(result[6]),'retained_physical_LHE_events':0,
        'candidate_record_writes_to_anonymous_scratch':writes,'zero_retention_postcondition':audit,
        'ME_counter_scope':'actual outer SLOOPMATRIX results; internal reduction/rescue subcalls are not counted as independent ME entries',
        'uncertainty_scope':'original native last-three-iteration estimator; coverage not independently established'}

def summarize(replicas):
    require(len(replicas)==4 and [r['seed'] for r in replicas]==list(SEEDS),'FOUR_APPROVED_REPLICAS_REQUIRED')
    vals=[r['measurement']['sigma_pb'] for r in replicas];mean=statistics.mean(vals);sd=statistics.stdev(vals);se=sd/2
    return {'final_verdict':'INCONCLUSIVE_CONVERGENCE','matched_integral_execution':'PASS_COMPLETED_WITH_LIMITS',
        'mean_pb':mean,'between_replica_sample_SD_pb':sd,'between_replica_SE_pb':se,
        'student_t3_95_interval_pb':[mean-3.182446305284263*se,mean+3.182446305284263*se],
        'internal_errors_pb':[r['measurement']['native_internal_error_pb'] for r in replicas],
        'assumptions':'independent matched proposals and approximately normal replica estimates for Student interval; four replicas do not establish coverage',
        'reason':'report actual dispersion and drift; no calibrated precision/coverage criterion was approved; no automatic extra replicas',
        'within_and_between_errors_combined':False}
