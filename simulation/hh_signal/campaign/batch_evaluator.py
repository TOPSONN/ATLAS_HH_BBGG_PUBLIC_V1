"""Native same-point coupling batch, gated by actual fresh-process regression."""
import re
from .common import *

def verified_batch(out,source_sha):
    path=Path(out)/'batch_verification_fast.json'
    if not path.exists():path=Path(out)/'batch_verification.json'
    if not path.exists():return None
    proof=read_json(path)
    require(proof['status']=='PASS_ACTUAL_NATIVE_BATCH_VS_INDEPENDENT_FRESH_PROCESS_REGRESSION' and
       proof['source_sha256']==source_sha and len(proof['tested_points'])>=10 and proof['max_relative_difference']<1e-8,
       'UNVERIFIED_NATIVE_COUPLING_BATCH')
    driver=proof.get('driver_file','check_reweight_batch.f')
    require(driver in ['check_reweight_batch.f','check_reweight_batch_fast.f'],'UNREVIEWED_NATIVE_BATCH_DRIVER')
    require(sha(CAMPAIGN/'src'/driver)==proof['compiler_source_sha256'] and
        sha(proof['batch_executable'])==proof['batch_executable_sha256'],'STALE_NATIVE_BATCH_BINARY')
    proof['receipt_sha256']=sha(path)
    return proof

def evaluate_batch(record,source,proof,monitor,env,attempt):
    work=Path(proof['batch_executable']).parent;r=record
    p=[[q['p4'][3],*q['p4'][:3]] for q in r['particles']]
    (work/'PS.input').write_text(f"{r['alpha_qcd']:.17e} {r['scale']:.17e}\n"+
        '\n'.join(' '.join(f'{v:.17e}' for v in q) for q in p)+'\n')
    run=monitor.run_command([proof['batch_executable']],work,'attempt'+str(attempt)+'_batch_me_'+str(r['index']),env=env)
    log=Path(run['log_path']).read_text();model=re.search(r'HH_MODEL_FROZEN\s+([^\n]+)',log)
    results=re.findall(r'HH_BATCH_RESULT\s+([^\n]+)',log);inputs=re.findall(r'HH_ME_INPUT\s+([^\n]+)',log)
    require(model is not None and len(results)==len(inputs)==7,'NATIVE_BATCH_OUTPUT_COUNT')
    warm=re.search(r'HH_BATCH_WARMUP_RC\s+(\d+)',log)
    if proof.get('driver_file')=='check_reweight_batch_fast.f':
        require(warm is not None and int(warm[1])//100 in (2,3),'UNSTABLE_NATIVE_BATCH_CALIBRATION')
    frozen=list(map(float,model[1].split()))
    require(frozen[:3]==[125.,173.,4.7] and abs(frozen[3]-source['validation']['actual_model_parameters']['decay_25'])<1e-14,
        'NATIVE_BATCH_MODEL_DIFFERS_FROM_SOURCE')
    values={};details={}
    for j,(line,entry,k) in enumerate(zip(results,inputs,[-1,0,1,2,2.5,5,1])):
        f=line.split();q=list(map(float,entry.split()));v=float(f[1]);rc=int(f[5]);precision=float(f[4])
        require(float(f[0])==q[0]==k and math.isfinite(v) and v>=0 and rc//100 in (2,3),'UNSTABLE_NATIVE_BATCH_POINT_NO_DROP')
        require(abs(q[1]-r['scale'])<1e-10*max(1,r['scale']) and abs(q[2]-r['alpha_qcd'])<1e-12,'SOURCE_BATCH_SCALE_ALPHA_CHANGED')
        require(k!=0 or q[4]==0,'BATCH_KAPPA_ZERO_HHH_NOT_REMOVED')
        if j==6:repeat=v
        else:values[k]=v;details[k]=(rc,precision,run['log_sha256'])
    return values,details,repeat
