"""Build and replay native kernels on fixed nonphysical streams, never survey."""
import argparse,difflib,json,os,re,resource,struct,subprocess,time,signal
from pathlib import Path
from .contract import *
from .overlay import sources,build_overlay
from .review import summarize,coverage
from simulation.hh_signal.config_lock.native import child_limits
from simulation.hh_signal.config_lock.contract import lock
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.integration_audit.audit import save
ACTIVE_OUTPUT=None

def trace(text):return [' '.join(t.split()) for t in text.splitlines() if t.lstrip().startswith('H_')]

def compare(a,b):
    a=trace(a);b=trace(b)
    require(a and b,'MISSING_NATIVE_TRACE')
    for i in range(max(len(a),len(b))):
        av=a[i] if i<len(a) else '<MISSING>';bv=b[i] if i<len(b) else '<MISSING>'
        if av!=bv:return {'equal':False,'first_record':i,'A':av,'B':bv}
    # Reject equal but invalid numeric results; never mistake two NaNs for PASS.
    for line in a:
        if line.startswith('H_R '):
            for token in line.split()[2:]:require(__import__('math').isfinite(struct.unpack('>d',bytes.fromhex(token))[0]),'NONFINITE_METHOD_ARITHMETIC')
    return {'equal':True,'records':len(a),'trace_sha256':identity(a)}

def command(argv,cwd,env,expected=0):
    start=time.monotonic();child=subprocess.Popen(list(map(str,argv)),cwd=cwd,env=env,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,text=True,preexec_fn=child_limits,start_new_session=True)
    try:stdout,stderr=child.communicate(timeout=60)
    except BaseException:
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait();raise
    r=subprocess.CompletedProcess(argv,child.returncode,stdout,stderr)
    require(len(stdout.encode())+len(stderr.encode())<=64*1024**2,'METHOD_LOG_CAP')
    if r.returncode!=expected:
        (Path(cwd)/'failed_child_stdout.txt').write_text(r.stdout)
        (Path(cwd)/'failed_child_stderr.txt').write_text(r.stderr)
    require(r.returncode==expected,'METHOD_CHILD_FAILED:'+r.stdout[-1500:]+r.stderr[-3500:])
    return r,time.monotonic()-start

def build(out,native,original,side,env,compiler,mutation=None):
    out.mkdir();inc=out/'include';inc.mkdir()
    # Headers/modules are isolated copies, each checked against frozen inputs.
    frozen={r['path']:r['sha256'] for r in lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary']}
    copied=[]
    for directory in ['Source','Source/MODEL','SubProcesses/P0_gg_hh']:
        for p in sorted((native/directory).glob('*')):
            if p.suffix.lower() not in ['.inc','.mod']:continue
            rel=p.relative_to(native).as_posix();require(rel in frozen and sha(p)==frozen[rel],'BUILD_INPUT_DRIFT:'+rel)
            (inc/p.name).write_bytes(p.read_bytes());copied.append({'path':rel,'sha256':sha(p)})
    (inc/'PDF').mkdir();pdf=native/'Source/PDF/pdf.inc';(inc/'PDF/pdf.inc').write_bytes(pdf.read_bytes())
    copied.append({'path':'Source/PDF/pdf.inc','sha256':sha(pdf)})
    transformed=build_overlay(original,reference=side=='A',mutation=mutation)
    patches=[]
    for rel,text in transformed.items():
        p=out/Path(rel).name;p.write_text(text)
        patches.append({'path':rel,'original_sha256':__import__('hashlib').sha256(original[rel].encode()).hexdigest(),'overlay_file_sha256':sha(p)})
    helper=(HERE/'src/io_and_rng.f90').read_text()
    if mutation=='aux_rng':helper=helper.replace('  xran1=hh_original_xran1(seed)',
        '  xran1=hh_original_xran1(seed)\n  xran1=hh_original_xran1(seed)')
    (out/'io_and_rng.f90').write_text(helper)
    # Only these native utility units are needed; do not link a loop-ME library.
    for name,signature in [('aloha_functions.f','      subroutine boostx('),('cluster.f','      integer function combid(')]:
        text=(out/name).read_text();match=re.search(re.escape(signature)+r'.*?^      end\s*$',text,re.M|re.S|re.I)
        require(match is not None,'NATIVE_UTILITY_NOT_FOUND:'+signature)
        (out/('selected_'+name)).write_text(match.group()+'\n')
    flags=[compiler,'-O0','-g','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none',
        '-ffunction-sections','-fdata-sections','-I'+str(inc),'-J'+str(inc)]
    objects=[]
    for file in [HERE/'src/anonymous_io.c',out/'io_and_rng.f90',out/'dsample.f',out/'ranmar.f',out/'ran1.f',
        out/'unwgt.f',out/'rw_events.f',out/'addmothers.f',out/'get_color.f',out/'selected_aloha_functions.f',
        out/'selected_cluster.f',HERE/'src/method_driver.f']:
        obj=out/(file.stem+'.o');cmd=[*flags,'-c',file,'-o',obj]
        if file.suffix=='.c':cmd=[str(compiler).replace('gfortran','gcc'),'-O0','-c',file,'-o',obj]
        command(cmd,out,env);objects.append(obj)
    for member in ['DiscreteSampler.o','StringCast.o']:
        archive=native/'lib/libdsample.a';require(sha(archive)==frozen['lib/libdsample.a'],'NATIVE_MODULE_ARCHIVE_DRIFT')
        result=subprocess.check_output(['ar','p',str(archive),member],timeout=30);p=out/member;p.write_bytes(result);objects.append(p)
    library=native/'lib/libgeneric.a';require(sha(library)==frozen['lib/libgeneric.a'],'NATIVE_GENERIC_ARCHIVE_DRIFT')
    exe=out/'method_replay'
    command([compiler,'-Wl,--gc-sections',*objects,library,'-o',exe],out,env)
    # Discarded physical drivers/phase-space sampling must not be linked.
    symbols=subprocess.check_output(['nm','--defined-only',str(exe)],text=True,timeout=30)
    for symbol in ['sample_full_','sample_get_point_','sample_get_config_','smatrix_','smatrix1_','ml5_0_sloopmatrix_']:
        require(not re.search(r'\b'+symbol+r'$',symbols,re.M),'FORBIDDEN_PHYSICAL_ENTRY_LINKED:'+symbol)
    (out/'symbols.txt').write_text(symbols)
    return exe,{'side':side,'mutation':mutation,'input_headers':copied,'overlays':patches,
        'compiled_local_sources':[{'name':p.name,'sha256':sha(p)} for p in sorted(out.glob('*')) if p.suffix in ['.f','.f90']],
        'native_lib_hashes':{rel:frozen[rel] for rel in ['lib/libdsample.a','lib/libgeneric.a']},
        'executable_sha256':sha(exe),'symbols_sha256':sha(out/'symbols.txt'),
        'linked_libraries':'pinned generic arithmetic/kinematics and DiscreteSampler/StringCast only; no MadLoop/model/matrix library',
        'forbidden_sampling_and_physical_ME_symbols_absent':True}

def replay(exe,root,case,side,env,grid=None,expected=0):
    root.mkdir();temp=root/'temporary';temp.mkdir()
    if grid:(root/'ftn25').write_bytes(grid.read_bytes())
    r,wall=command([exe,case,side],root,{**env,'TMPDIR':str(temp)},expected=expected)
    (root/'stdout.txt').write_text(r.stdout);(root/'stderr.txt').write_text(r.stderr)
    require(not list(temp.iterdir()),'NAMED_TRANSIENT_REMAINS')
    for p in root.rglob('*'):
        if p.is_file() and p.name not in ['stdout.txt','stderr.txt']:
            require(b'<event>' not in p.read_bytes(),'PERMANENT_EVENT_RECORD')
    return r.stdout,{'case':case,'side':side,'exit':r.returncode,'wall_seconds':wall,
        'trace_records':len(trace(r.stdout)),'trace_sha256':identity(trace(r.stdout)),
        'retained_event_records':0,'empty_TMPDIR_after':True,
        'named_files':[{'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.iterdir()) if p.is_file()]}

def run(output,native):
    global ACTIVE_OUTPUT
    out=safe_output(output);require(not out.exists(),'PRESERVE_PRIOR_ATTEMPT');native=Path(native)
    original=sources(native);out.mkdir(parents=True)
    ACTIVE_OUTPUT=out
    p=policy();p['method_source_identity']=source_identity();save(out/'predeclared_policy.json',p)
    started=time.monotonic();usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'
    builds=[];executables={};pairs=[];receipts=[];raw={};summaries={}
    normalized=lambda t:{k:v.replace('hh_open_reference','hh_open_sink') for k,v in t.items()}
    require(normalized(build_overlay(original,True))==build_overlay(original,False),'UNREVIEWED_COMPUTATIONAL_SOURCE_DIFFERENCE')
    for side in ['A','B']:
        executables[side],b=build(out/('build_'+side),native,original,side,env,compiler);builds.append(b)
    for case in p['cases']:
        for side in ['A','B']:
            grid=out/('adaptation_'+side)/'ftn26' if case=='measurement' else None
            text,r=replay(executables[side],out/(case+'_'+side),case,side,env,grid);raw[case,side]=text;receipts.append(r)
        equal=compare(raw[case,'A'],raw[case,'B']);require(equal['equal'],'BASELINE_FIRST_DIVERGENCE:'+json.dumps(equal))
        summaries[case]=summarize(raw[case,'A'])
        pairs.append({'case':case,**equal})
    independent=coverage(summaries)
    negatives=[]
    for mutation in p['negative_mutations']:
        exe,b=build(out/('mutation_'+mutation),native,original,'B',env,compiler,mutation);builds.append(b)
        text,r=replay(exe,out/('negative_'+mutation),'adaptation','B',env);receipts.append(r)
        diff=compare(raw['adaptation','A'],text);require(not diff['equal'],'MUTATION_NOT_DETECTED:'+mutation)
        origins={'candidate':('SubProcesses/unwgt.f','nw = nw+1','candidate multiplicity and stopping/tail inputs'),
            'aux_rng':('Source/ran1.f','xran1=r(j)','auxiliary acceptance decisions'),
            'stopping':('Source/dsample.f','if (cur_it .gt. itm) then','premature finalization and changed candidate clearing'),
            'grid':('Source/dsample.f','grid(1, i, j) = grid(1, i, j) + abs(wgt)','grid adaptation increments'),
            'arithmetic':('Source/dsample.f','sigma=sigma+twgt1**2','squared sum and native error estimator'),
            'tail':('SubProcesses/unwgt.f','th_nunwgt = th_nunwgt +1','incomplete unweighting/tail diagnostics')}
        path,anchor,impact=origins[mutation];matching=[i for i,t in enumerate(original[path].splitlines(),1) if anchor.lower() in t.lower()]
        require(matching,'MISSING_CAUSAL_SOURCE_LOCATION:'+mutation)
        negatives.append({'mutation':mutation,'expected_rejection':True,'first_divergence':diff,
            'FIRST_DIVERGENCE_LOCATION':diff['first_record'],'EXPECTED_VALUE':diff['A'],'OBSERVED_VALUE':diff['B'],
            'CAUSAL_NATIVE_SOURCE_LINE':path+':'+str(matching[-1] if mutation=='stopping' else matching[0]),'SCIENTIFIC_IMPACT':impact})
    for case in p['negative_io_cases']:
        text,r=replay(executables['B'],out/case,case,'B',env,expected=87);receipts.append(r)
        require('<event>' not in text,'SERIALIZER_GUARD_TOO_LATE')
        negatives.append({'mutation':case,'exit':87,'physical_serialization_prevented':True})
    require(sources(native)==original,'HISTORICAL_SOURCE_CHANGED_DURING_METHODS')
    used=resource.getrusage(resource.RUSAGE_CHILDREN);disk=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    require(time.monotonic()-started<14400 and disk<5*1024**3,'RESOURCE_CEILING_PRESERVE_PARTIAL')
    result={'status':'READY_FOR_AUTHORIZED_NATIVE_VALIDATION','method_result':'PASS_METHOD_LEVEL_SEMANTICS_WITH_LIMITS',
        'policy_sha256':sha(out/'predeclared_policy.json'),'policy':p,'paired_cases':pairs,'negative_cases':negatives,
        'builds':builds,'runs':receipts,'new_physical_ME_calls':0,'new_integrals':0,'new_physical_events':0,
        'bounded_native_summaries':summaries,'independent_numerical_check':independent,
        'computational_source_correspondence':'A/B identical after the declared connection-name substitution; arithmetic and candidate bodies retained',
        'REAL_SURVEY_EXECUTED':False,'historical_STOP80_STOP86':'UNCHANGED','native_runtime_gate':'NOT_AUTHORIZED',
        'limitations':['fixed nonphysical streams, no phase-space sampling or genuine HH ME',
            'mock exact-helicity grid hooks and process multiplicity=1; real MadLoop/helicity/stability not tested',
            'A preserves native computations with only anonymous reference connection and identical read-only traces',
            'B scratch verified unlinked immediately and before each native write_event; scope excludes unknown external writers',
            'ordinary files contain grids/results and nonphysical trace only; anonymous formatted candidate records can consume disk/page cache until close; not a memory-only or no-transient-record claim',
            'native stopping/error equivalence here does not establish HH convergence'],
        'resources_method_only':{'wall_seconds':time.monotonic()-started,
            'child_CPU_seconds':used.ru_utime+used.ru_stime-usage.ru_utime-usage.ru_stime,
            'child_peak_RSS_KiB_process_lifetime_high_water':used.ru_maxrss,'logical_disk_bytes':disk}}
    save(out/'result.json',result);return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--native')
    p.add_argument('--execute',action='store_true');p.add_argument('--authorization')
    a=p.parse_args(argv)
    try:
        if a.execute or a.authorization is not None:deny_real_execution()
        require(a.native,'MISSING_PINNED_NATIVE_SOURCE')
        r=run(a.output,a.native);print(json.dumps({k:r[k] for k in ['status','method_result','new_physical_ME_calls','new_integrals',
            'new_physical_events','REAL_SURVEY_EXECUTED','resources_method_only']},indent=2));return 0
    except Exception as exc:
        if ACTIVE_OUTPUT:
            save(ACTIVE_OUTPUT/'failure_receipt.json',{'status':'PARTIAL_PRESERVED','error':str(exc),'policy_changed_to_force_PASS':False,
                'new_physical_ME_calls':0,'new_integrals':0,'new_physical_events':0})
        print('SEMANTICS_RECOVERY_BLOCKED:'+str(exc),file=__import__('sys').stderr);return 2
if __name__=='__main__':raise SystemExit(main())
