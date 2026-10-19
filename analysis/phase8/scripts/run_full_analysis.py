#!/usr/bin/env python3
"""Execute only Phase8 existing-input analysis, one contained process group at a time."""
import argparse,fcntl,hashlib,json,os,re,resource,signal,subprocess,sys,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[3]
CONDA=Path.home()/'miniforge3/bin/conda'; ENV=Path.home()/'miniforge3/envs/atlas-hh-root'
CEILINGS={'wall_seconds':14400,'cpu_seconds':14400,'disk_bytes':2*1024**3,'jobs':1,'workers':1}
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()
def disk(paths):
    return sum(p.stat().st_size for r in paths if r.exists() for p in r.rglob('*') if p.is_file() and not p.is_symlink())
def group_usage(pgid):
    ticks=0;rss=0;hz=os.sysconf('SC_CLK_TCK');page=os.sysconf('SC_PAGE_SIZE')
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            raw=(p/'stat').read_text();v=raw[raw.rfind(')')+2:].split()
            if int(v[2])!=pgid:continue
            ticks+=sum(int(v[i]) for i in [11,12,13,14]);rss+=int(v[21])*page
        except (OSError,ValueError,IndexError):pass
    return ticks/hz,rss

def group_members(pgid):
    """Live members of this child session; zombies consume no runnable resources."""
    members=[]
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            raw=(entry/'stat').read_text();fields=raw[raw.rfind(')')+2:].split()
            if int(fields[2])==pgid and fields[0] not in ('Z','X'):members.append(int(entry.name))
        except (OSError,ValueError,IndexError):pass
    return members

def terminate_group(proc):
    """Terminate descendants even after the leader exited; always bound cleanup."""
    for sig in (signal.SIGTERM,signal.SIGKILL):
        if group_members(proc.pid):
            try:os.killpg(proc.pid,sig)
            except ProcessLookupError:pass
        deadline=time.monotonic()+5
        while group_members(proc.pid) and time.monotonic()<deadline:time.sleep(.05)
        if not group_members(proc.pid):
            if proc.poll() is None:proc.wait(timeout=5)
            return
    raise RuntimeError('PROCESS_GROUP_TERMINATION_FAILED')

def execute(command,label,result,build):
    receipt=result/f'{label}_execution.json';log=result/f'{label}.log'
    if receipt.exists() or log.exists():raise ValueError('REFUSE_EXECUTION_RECEIPT_OVERWRITE:'+label)
    previous=[json.loads(p.read_text()) for p in result.glob('*_execution.json')]
    spent_wall=sum(p.get('wall_seconds',0) for p in previous);spent_cpu=sum(p.get('cpu_seconds',0) for p in previous)
    for rpath in result.glob('*_execution.json'):
        row=json.loads(rpath.read_text())
        if 'cpu_seconds' not in row:
            timepath=rpath.with_name(rpath.name.replace('_execution.json','_resources.txt'))
            if timepath.exists():spent_cpu+=sum(float(v) for v in re.findall(r'(?:User time|System time) \(seconds\): ([0-9.]+)',timepath.read_text()))
    if spent_wall>=CEILINGS['wall_seconds'] or spent_cpu>=CEILINGS['cpu_seconds'] or disk([result,build])>=CEILINGS['disk_bytes']:raise RuntimeError('BLOCKED_PHASE8_RESOURCE_LIMITS')
    start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);peak=0;reason=None
    with log.open('x') as f:
        childenv=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',ROOT_MAX_THREADS='1')
        proc=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=childenv)
        try:
            while proc.poll() is None:
                cpu,rss=group_usage(proc.pid);peak=max(peak,rss)
                if time.monotonic()-start+spent_wall>CEILINGS['wall_seconds']:reason='AGGREGATE_WALL_LIMIT'
                elif cpu+spent_cpu>CEILINGS['cpu_seconds']:reason='AGGREGATE_CPU_LIMIT'
                elif disk([result,build])>CEILINGS['disk_bytes']:reason='ADDITIONAL_OUTPUT_DISK_LIMIT'
                if reason:raise TimeoutError(reason)
                time.sleep(.25)
            if group_members(proc.pid):
                reason='ORPHAN_PROCESS_GROUP_REMAINS'
                raise RuntimeError(reason)
        except BaseException:
            try:terminate_group(proc)
            except RuntimeError:
                reason='PROCESS_GROUP_TERMINATION_FAILED'
                raise
            raise
        finally:
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            r={'label':label,'command':command,'exit_code':proc.poll(),'wall_seconds':time.monotonic()-start,'cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'peak_observed_process_group_RSS_bytes':peak,'aggregate_observed_disk_bytes':disk([result,build]),'resource_failure':reason,'ceilings':CEILINGS,'new_ME_calls':0,'new_integrals':0,'new_physical_events':0}
            with receipt.open('x') as q:json.dump(r,q,indent=2);q.write('\n')
    if proc.returncode:raise RuntimeError('PHASE8_COMMAND_FAILED:'+label+':'+str(proc.returncode)+':'+str(log))
    print(label,'PASS',round(r['wall_seconds'],3),'seconds',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--result',type=Path,required=True);p.add_argument('--action',choices=['all','audit','full','methods','statistics','kappa','postprocess','validate','repeat','prefix'],default='all');p.add_argument('--label',default='01');a=p.parse_args()
    if not a.result.is_dir() or a.result.is_symlink():raise ValueError('REAL_EXISTING_RESULT_PARENT_REQUIRED')
    if not a.manifest.is_file() or not a.build.is_dir():raise ValueError('MISSING_MANIFEST_OR_COMPILED_BUILD')
    if a.action in ('all','prefix') and not (a.result/'phase8_prefix_local_manifest.json').is_file():raise ValueError('MISSING_VERIFIED_PREFIX_MANIFEST_PREPARE_BEFORE_EXECUTION')
    if not a.label.replace('_','').isalnum():raise ValueError('INVALID_RECEIPT_LABEL')
    with (a.result/'.phase8_analysis.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        envcmd=[str(CONDA),'run','--no-capture-output','-p',str(ENV)];app=a.build/'analysis/phase8/phase8_analyze';methods=a.build/'analysis/phase8/phase8_methods';cfg=REPO/'analysis/phase8/config';scripts=REPO/'analysis/phase8/scripts';datasets=json.loads(a.manifest.read_text())['datasets']
        def native(mode,folder):return [*envcmd,str(app),mode,'--manifest',str(a.manifest),'--config',str(cfg/'selection_v1.json'),'--edges',str(cfg/'histogram_edges_v1.json'),'--output',str(a.result/folder)]
        def run(cmd,label):execute(cmd,label+'_'+a.label,a.result,a.build)
        if a.action in ['all','audit']:run(native('audit','native_audit'),'native_audit')
        if a.action in ['all','full']:run(native('analyze','native'),'native_full')
        if a.action in ['all','prefix']:
            prefix=a.result/'phase8_prefix_local_manifest.json'
            run([*envcmd,str(app),'analyze','--manifest',str(prefix),'--config',str(cfg/'selection_v1.json'),'--edges',str(cfg/'histogram_edges_v1.json'),'--output',str(a.result/'native_prefix')],'native_prefix')
        if a.action in ['all','methods']:run([*envcmd,str(methods),'methods-test','--output',str(a.result/'methods')],'synthetic_methods')
        if a.action in ['all','statistics']:
            stats=a.result/'statistics';stats.mkdir(exist_ok=False);index={}
            for d in datasets:
                ds=d['dataset_id'];out=stats/ds
                run([*envcmd,str(methods),'analyze-statistics','--events',str(a.result/'native/phase8_events.jsonl'),'--dataset',ds,'--factor',str(d['model_br_factor']),'--factor-applications','0','--edges',str(cfg/'histogram_edges_v1.json'),'--output',str(out)],'statistics_'+ds)
                index[ds]=str(out/'phase8_statistical_uncertainty.json')
            with (a.result/'statistics_index.json').open('x') as f:json.dump(index,f,indent=2);f.write('\n')
        if a.action in ['all','kappa']:
            d=next(d for d in datasets if d['dataset_id']=='S01_C1000')
            run([*envcmd,str(methods),'kappa','--events',str(a.result/'native/phase8_events.jsonl'),'--weights',str(REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv'),'--source-sha256',d['lhe_sha256'],'--model-br',str(d['model_br_factor']),'--edges',str(cfg/'histogram_edges_v1.json'),'--output',str(a.result/'kappa')],'kappa')
        if a.action in ['all','postprocess']:
            run([sys.executable,'-B',str(scripts/'postprocess.py'),'--events',str(a.result/'native/phase8_events.jsonl'),'--manifest',str(a.manifest),'--edges',str(cfg/'histogram_edges_v1.json'),'--output',str(a.result/'postprocess')],'postprocess')
            run([sys.executable,'-B',str(scripts/'background_contract.py'),'--manifest',str(a.manifest),'--output',str(a.result/'background')],'background_contract')
        if a.action in ['all','validate']:
            run([sys.executable,'-B',str(scripts/'independent_validation.py'),'--manifest',str(a.manifest),'--native',str(a.result/'native'),'--prefix',str(a.result/'native_prefix'),'--edges',str(cfg/'histogram_edges_v1.json'),'--output',str(a.result/'independent_native_validation.json')],'independent_native')
            run([*envcmd,str(app),'validate','--output',str(a.result/'native')],'root_readback')
            run([sys.executable,'-B',str(scripts/'independent_statistics.py'),'--events',str(a.result/'native/phase8_events.jsonl'),'--edges',str(cfg/'histogram_edges_v1.json'),'--statistics-index',str(a.result/'statistics_index.json'),'--kappa-weights',str(REPO/'reference_samples/hh_signal/S01_ggf_hh_sm/phase7d_klambda/event_reweights.csv'),'--kappa-directory',str(a.result/'kappa'),'--output',str(a.result/'independent_statistics_validation.json')],'independent_numerical')
        if a.action in ['repeat']:
            run(native('analyze','native_repeat'),'native_repeat')
            first=json.loads((a.result/'native/phase8_native_summary.json').read_text());second=json.loads((a.result/'native_repeat/phase8_native_summary.json').read_text())
            if first['numerical_histogram_content_sha256']!=second['numerical_histogram_content_sha256']:raise ValueError('REPEATED_NUMERICAL_DIGEST_MISMATCH')
            stable=['phase8_events.jsonl','phase8_cutflow_raw.csv','phase8_cutflow_weighted.csv','phase8_reconstruction_statistics.csv','phase8_histograms.csv','phase8_truth_matching.json']
            closure={n:digest(a.result/'native'/n)==digest(a.result/'native_repeat'/n) for n in stable}
            if not all(closure.values()):raise ValueError('REPEAT_CSV_OR_EVENT_SUMMARY_MISMATCH')
            with (a.result/'repeatability_validation.json').open('x') as f:json.dump({'status':'PASS_REPEAT_ACTUAL_EXISTING_EVENT_ANALYSIS','numerical_histogram_content_sha256':first['numerical_histogram_content_sha256'],'exact_repeated_content':closure,'ROOT_file_UUID_compared':False,'additional_independent_sources':0},f,indent=2);f.write('\n')
if __name__=='__main__':main()