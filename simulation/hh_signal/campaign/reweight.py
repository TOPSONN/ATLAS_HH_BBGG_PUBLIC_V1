"""Full-mass native ME ratios on the exact validated independent C1000."""
import csv,re,shutil,resource
from .common import *
from .lhe import load_lhe,validate_production

def quadratic(values):
    b=values[0];a=(values[2]+b-2*values[1])/2;i=values[1]-b-a
    # |box + k triangle|² = b + k interference + k² triangle.
    residual=max(abs(values[k]-(b+k*i+k*k*a))/max(values[k],abs(b)+abs(k*i)+abs(k*k*a),1e-300)
                 for k in (-1,2.5,5))
    return b,i,a,residual

def weighted_summary(weights):
    n=len(weights);s=math.fsum(weights);q=math.fsum(x*x for x in weights)
    return {'sum':s,'sumw2':q,'ESS':s*s/q if q else 0.,
       'max_single_fraction':max(map(abs,weights),default=0)/abs(s) if s else None,
       'source_sampling_variance':n/(n-1)*max(0,q-s*s/n) if n>1 else None}

def completed_reweight(out,source_sha,benchmarks):
    """Read-only idempotent resume of a genuinely completed numerical chain."""
    out=Path(out);path=out/'reweight_validation.json'
    if not path.exists():return None
    result=read_json(path);comparison=result.get('comparison',{})
    if comparison.get('status')!='PASS_SEPARATE_PROCESS_EXPLORATORY_COMPARISON_WITH_LIMITS':return None
    require(result['source_sha256']==source_sha and result['benchmarks']==benchmarks and
        result['source_events']==1000 and result['new_independent_events']==0,'COMPLETED_REWEIGHT_SCOPE_CHANGED')
    require(sha(out/'event_reweights.csv')==result['event_reweights_sha256'],'COMPLETED_REWEIGHT_TABLE_CHANGED')
    for name,key in [('weighted_histograms.csv','histogram_sha256'),('weighted_histograms.root','native_numerical_ROOT_sha256'),
                     ('signal_background_cutflow.csv','cutflow_sha256')]:
        require(sha(out/'comparison'/name)==comparison[key],'COMPLETED_REWEIGHT_COMPARISON_CHANGED')
    for row in comparison['inputs']:
        # Original absolute source bindings are local audit data, not inferred
        # from the newly derived comparison.
        require(row['input_source_unchanged'],'COMPLETED_REWEIGHT_INPUT_NOT_PRESERVED')
    return result

def run_reweight(args,out,registry,build,native):
    c=registry['phases'].get('7c',{});require(c.get('status')=='PASS_FULL_CHAIN','PHASE7D_REQUIRES_GENUINE_7C1000_PASS')
    out=Path(out);existed=out.exists();require(not existed or args.resume,'PRESERVE_EXISTING_REWEIGHT_OUTPUT_USE_EXPLICIT_RESUME')
    hours=min(args.max_hours or 4,4);disk=min(args.max_disk_gb or 10,10)
    avail=resources(out,disk);out.mkdir(parents=True,exist_ok=existed)
    phase_path=Path(c['output'])/'phase_receipt.json'
    require(sha(phase_path)==c['phase_receipt_sha256'],'C1000_FROZEN_PHASE_RECEIPT_CHANGED')
    phase=read_json(phase_path);s=phase['source']
    require(sha(s['path'])==s['sha256'],'C1000_SOURCE_CHANGED')
    source=load_lhe(s['path']);validate_production(source,1000,c['seed'])
    scan=read_json(args.kappa_config);benchmarks=scan['benchmarks']
    scratch=out/'standalone'
    if not existed:shutil.copytree(build['matrix_element'],scratch,symlinks=False)
    work=scratch/'SubProcesses/P0_gg_hh'
    if not existed:shutil.copyfile(CAMPAIGN/'src/check_reweight.f',work/'check_sa.f')
    # Match every actual physical parameter after native MG's PDF alpha_s
    # initialization, then override only source-event alpha_s/mu and GC_30.
    card='Block loop\n 1 9.118800000000e+01\n'+(Path(c['output'])/'source/embedded_param_card.dat').read_text()
    if not existed:(scratch/'Cards/param_card.dat').write_text(card)
    else:require((scratch/'Cards/param_card.dat').read_text()==card,'RESUME_FROZEN_REWEIGHT_CARD_CHANGED')
    complete=completed_reweight(out,s['sha256'],benchmarks) if args.resume else None
    if complete is not None:
        from .analysis import backgrounds
        backgrounds()  # Reverify the original six immutable background bindings.
        for artifact in phase['stages']['full1000']['artifacts'].values():
            require(sha(artifact['path'])==artifact['sha256'],'COMPLETED_REWEIGHT_SIGNAL_INPUT_CHANGED')
        print('7D PASS existing complete numerical chain reverified; new source events=0',flush=True)
        return complete
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    from .batch_evaluator import verified_batch,evaluate_batch
    proof=verified_batch(out,s['sha256']);rows=[]
    if existed:
        require((out/'event_reweights.csv').exists(),'NO_COMPLETE_REWEIGHT_ROWS_TO_RESUME')
        for row in csv.DictReader((out/'event_reweights.csv').open()):
            rows.append({k:v if k=='source_event_sha256' else int(v) if k in ['source_event_index','return_code'] else float(v) for k,v in row.items()})
        require(len(rows)%6==0,'PARTIAL_REWEIGHT_EVENT_ROW_GROUP')
        for j,row in enumerate(rows):
            index=j//6+1;original=source['records'][index-1]
            require(row['source_event_index']==index and row['kappa_lambda']==benchmarks[j%6] and row['source_event_sha256']==original['hash'],
                'RESUME_REWEIGHT_SOURCE_IDENTITY_CHANGED')
            require(abs(row['ratio']-row['full_mass_squared_ME']/row['SM_denominator'])<1e-10*max(1,row['ratio']) and
                row['source_alpha_s']==original['alpha_qcd'] and row['source_scale_gev']==original['scale'],'RESUME_REWEIGHT_VALUE_CHANGED')
    completed=len(rows)//6;fresh_complete=proof['preserved_fresh_complete_source_events'] if proof else 1000
    old=out/'execution.json';history=sorted(out.glob('execution_attempt_*.json'))
    if old.exists() and not any(sha(old)==sha(p) for p in history):
        shutil.copyfile(old,out/('execution_attempt_'+str(len(history))+'.json'));history=sorted(out.glob('execution_attempt_*.json'))
    previous=[read_json(p) for p in history];attempt=len(history)
    prior_seconds=math.fsum(p['elapsed_seconds']+p.get('external_verification_seconds',0) for p in previous)
    proof_seconds=proof.get('cumulative_verification_elapsed_seconds',proof['elapsed_seconds']) if proof and not any(p.get('batch_proof_sha256')==proof['receipt_sha256'] for p in previous) else 0.
    remaining=hours*3600-prior_seconds-proof_seconds;require(remaining>0,'REWEIGHT_FOUR_HOUR_CUMULATIVE_CEILING')
    stop=out/'STOP'
    if stop.exists():
        require(args.resume and proof and stop.read_text()=='CONTROLLED_CHECKPOINT_FOR_INDEPENDENT_NATIVE_BATCH_VERIFICATION\n','UNAPPROVED_STOP_CLEARING_FORBIDDEN')
        stop.rename(out/('STOP_preserved_attempt_'+str(attempt)+'.txt'))
    m=Monitor(out,{'max_hours':remaining/3600,'max_disk_gb':disk})
    cpu0=resource.getrusage(resource.RUSAGE_CHILDREN);started=time.monotonic()
    try:
        m.install_signals()
        if not existed:m.run_command(['make','-j1','check'],work,'compile_event_reweight',env=env)
        with (out/'event_reweights.csv').open('a' if existed else 'x',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['source_event_index','source_event_sha256','source_alpha_s','source_scale_gev',
                'kappa_lambda','full_mass_squared_ME','SM_denominator','ratio','source_contribution_pb','MODEL_BR_ONLY_weight_pb',
                'return_code','precision','quadratic_residual','SM_repeat_relative_residual'],lineterminator='\n')
            if not existed:writer.writeheader()
            for r in source['records'][completed:]:
                p=[[q['p4'][3],*q['p4'][:3]] for q in r['particles']]
                (work/'PS.input').write_text(f"{r['alpha_qcd']:.17e} {r['scale']:.17e}\n"+
                    '\n'.join(' '.join(f'{v:.17e}' for v in q) for q in p)+'\n')
                values={};details={}
                # Repeat SM at the identical point; the verified batch repeats
                # within one process, the original path uses a fresh process.
                if proof:values,details,repeat=evaluate_batch(r,s,proof,m,env,attempt)
                for j,k in enumerate([] if proof else [*benchmarks,1]):
                    result=m.run_command([str(work/'check'),str(k)],work,'attempt'+str(attempt)+'_me_'+str(r['index'])+'_'+str(j),env=env)
                    log=Path(result['log_path']).read_text();match=re.search(r'HH_ME_RESULT\s+([^\n]+)',log)
                    inputs=re.search(r'HH_ME_INPUT\s+([^\n]+)',log)
                    model=re.search(r'HH_MODEL_FROZEN\s+([^\n]+)',log)
                    require(match is not None and inputs is not None and model is not None,'MISSING_ACTUAL_NATIVE_REWEIGHT_ME')
                    f=match[1].split();v=float(f[0]);rc=int(f[4]);prec=float(f[3]);q=list(map(float,inputs[1].split()))
                    require(math.isfinite(v) and v>=0 and rc//100 in (2,3),'UNSTABLE_NATIVE_REWEIGHT_POINT_NO_DROPPING')
                    require(abs(q[1]-r['scale'])<1e-10*max(1,r['scale']) and abs(q[2]-r['alpha_qcd'])<1e-12,
                        'SOURCE_EVENT_SCALE_OR_ALPHA_S_CHANGED')
                    frozen=list(map(float,model[1].split()))
                    require(frozen[:3]==[125.,173.,4.7] and abs(frozen[3]-s['validation']['actual_model_parameters']['decay_25'])<1e-14,
                        'NATIVE_REWEIGHT_MODEL_DIFFERS_FROM_ACTUAL_SOURCE_CARD')
                    require(k!=0 or q[4]==0,'KAPPA_ZERO_DID_NOT_REMOVE_HHH_VERTEX')
                    if j==len(benchmarks):repeat=v
                    else:values[k]=v;details[k]=(rc,prec,result['log_sha256'])
                b,i,a,residual=quadratic(values);den=values[1]
                require(den>scan['denominator_relative_floor']*max(values.values()),'UNRELIABLE_SM_DENOMINATOR_INCONCLUSIVE_NO_DROP')
                closure=abs(repeat-den)/den
                require(closure<1e-10 and residual<1e-7,'REWEIGHT_CLOSURE_OR_HELD_OUT_QUADRATIC_FAILURE')
                require(b>0 and a>=-1e-8*max(values.values()),'BOX_TRIANGLE_PROBABILITY_FAILURE')
                for k in benchmarks:
                    ratio=values[k]/den;w=r['weight']/1000*ratio
                    row={'source_event_index':r['index'],'source_event_sha256':r['hash'],'source_alpha_s':r['alpha_qcd'],
                        'source_scale_gev':r['scale'],'kappa_lambda':k,'full_mass_squared_ME':values[k],'SM_denominator':den,'ratio':ratio,
                        'source_contribution_pb':w,'MODEL_BR_ONLY_weight_pb':w*native['model_values']['mixed_decay_factor'],
                        'return_code':details[k][0],'precision':details[k][1],'quadratic_residual':residual,'SM_repeat_relative_residual':closure}
                    writer.writerow(row);rows.append(row)
                stream.flush()
                save_json(out/'progress.json',{'validated_real_source_events':r['index'],'ME_calls':r['index']*7,
                    'original_source_events':1000,'additional_independent_events':0})
                if r['index']%10==0:print('7D actual reweighted source events='+str(r['index']),flush=True)
        summaries={str(k):weighted_summary([r['source_contribution_pb'] for r in rows if r['kappa_lambda']==k]) for k in benchmarks}
        for summary in summaries.values():
            summary['status']='PASS_BOUNDED_SUPPORT_DIAGNOSTIC' if summary['ESS']>=100 and summary['max_single_fraction']<=.1 else 'INCONCLUSIVE_REWEIGHTING'
            summary['absolute_rate_status']='INCONCLUSIVE_ABSOLUTE_RATE'
        byk={k:[r['source_contribution_pb'] for r in rows if r['kappa_lambda']==k] for k in benchmarks}
        cov=[]
        for k in benchmarks:
            for l in benchmarks:
                cov.append({'kappa_a':k,'kappa_b':l,'source_sampling_covariance_pb2':1000/999*(math.fsum(x*y for x,y in zip(byk[k],byk[l]))-math.fsum(byk[k])*math.fsum(byk[l])/1000)})
        result={'status':'PASS_ACTUAL_EVENT_LEVEL_FULL_MASS_REWEIGHT_WITH_ABSOLUTE_RATE_LIMIT',
            'source_sha256':s['sha256'],'source_events':1000,'new_independent_events':0,'benchmarks':benchmarks,
            'fresh_native_matrix_element_processes_complete_points':fresh_complete*7,
            'batch_native_processes_complete_points':1000-fresh_complete,
            'native_loop_matrix_function_calls_complete_points':fresh_complete*42+(1000-fresh_complete)*(proof.get('native_loop_calls_per_complete_point',42) if proof else 42),
            'independent_batch_regression':proof,
            'partial_attempt_logs_preserved':True,'aborted_partial_native_function_call_count':'UNKNOWN_NOT_FABRICATED',
            'finite_matrix_element_results':7000,'summaries':summaries,'cross_benchmark_covariance':cov,
            'max_quadratic_relative_residual':max(r['quadratic_residual'] for r in rows),
            'max_SM_repeat_relative_residual':max(r['SM_repeat_relative_residual'] for r in rows),
            'ratios_above10':{str(k):sum(r['ratio']>10 for r in rows if r['kappa_lambda']==k) for k in benchmarks},
            'event_reweights_sha256':sha(out/'event_reweights.csv'),'independent_benchmark_integration':None,
            'absolute_rate_status':'INCONCLUSIVE_ABSOLUTE_RATE','reference_BR':None,'adopted_physical_BR':None,
            'model_BR_factor':native['model_values']['mixed_decay_factor'],'resources_before':avail}
        save_json(out/'reweight_validation.json',result)
        from .analysis import analyze
        result['comparison']=analyze(out/'comparison',phase,native,rows,m)
        save_json(out/'reweight_validation.json',result)
        registry['reweight']={'output':str(out),'status':result['status'],'controlled_seconds':prior_seconds+proof_seconds+time.monotonic()-started}
        save_json(REPO/'.local/phase7_campaign/campaign_registry.json',registry)
        return result
    finally:
        m.restore_signals();cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
        execution={'metrics':m.metrics(),'children_user_cpu_seconds':cpu.ru_utime-cpu0.ru_utime,
           'children_system_cpu_seconds':cpu.ru_stime-cpu0.ru_stime,'elapsed_seconds':time.monotonic()-started,
           'external_verification_seconds':proof_seconds,'batch_proof_sha256':proof['receipt_sha256'] if proof else None,
           'cumulative_controlled_seconds':prior_seconds+proof_seconds+time.monotonic()-started,'resumed_complete_source_points':completed}
        save_json(out/'execution.json',execution);save_json(out/('execution_attempt_'+str(attempt)+'.json'),execution)
