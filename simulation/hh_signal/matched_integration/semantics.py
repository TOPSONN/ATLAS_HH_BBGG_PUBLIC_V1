"""Non-integrating native RNG probes and a hash-bound, deliberately partial audit."""
import argparse,json,re,resource,time
from pathlib import Path
from .contracts import HERE,REPO,require,sha,read_json,safe_output
from simulation.hh_signal.config_lock.contract import lock
from simulation.hh_signal.config_lock.native import run
from simulation.hh_signal.config_lock.writers import output_audit
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.integration_audit.audit import save

SOURCES=['Source/dsample.f','Source/ran1.f','Source/ranmar.f','SubProcesses/unwgt.f',
    'SubProcesses/P0_gg_hh/configs.inc','SubProcesses/P0_gg_hh/auto_dsig1.f']
RANGES={'Source/dsample.f':[(947,971),(1682,1720),(1750,1760),(1945,1963),(2128,2150),(2180,2222),(2546,2576)],
    'SubProcesses/unwgt.f':[(233,257),(559,575),(810,823)],
    'Source/ranmar.f':[(34,70)],'Source/ran1.f':[(1,48)],
    'SubProcesses/P0_gg_hh/configs.inc':[(1,18)],'SubProcesses/P0_gg_hh/auto_dsig1.f':[(140,185)]}

def audit_sources(native):
    native=Path(native);frozen={r['path']:r for r in lock()['frozen_runtime_sources']}
    rows=[];texts={}
    for rel in SOURCES:
        p=native/rel;require(rel in frozen and sha(p)==frozen[rel]['sha256'],'NATIVE_SOURCE_DRIFT:'+rel)
        text=p.read_text();texts[rel]=text;lines=text.splitlines()
        rows.append({'path':rel,'sha256':sha(p),'excerpts':[{'first_line':a,'last_line':min(b,len(lines)),
            'text':'\n'.join(lines[a-1:b])} for a,b in RANGES[rel]]})
    ds=texts['Source/dsample.f'];un=texts['SubProcesses/unwgt.f']
    require(re.search(r'DATA\s+MAPCONFIG\(0\)/1/',texts['SubProcesses/P0_gg_hh/configs.inc'],re.I),'MULTICHANNEL_NOT_REVIEWED')
    require(re.search(r'zooming\s*=\s*\.false\.',ds,re.I),'ZOOM_MODE_CHANGED')
    compact=re.sub(r'\s+','',ds.lower());cu=re.sub(r'\s+','',un.lower())
    require('events=2*events' in compact and 'nun=neventswritten' in compact,'STOPPING_OR_POINT_GROWTH_CHANGED')
    require('nw=nw+1' in cu and 'swgt(nw)=wgt' in cu,'CANDIDATE_BOOKKEEPING_CHANGED')
    return rows,texts

def probe(output,native):
    out=safe_output(output);require(not out.exists(),'PRESERVE_EXISTING_SEMANTICS_PROBE')
    start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
    rows,texts=audit_sources(native);cfg=read_json(REPO/'.local/mg5_installation.json')
    out.mkdir(parents=True);src=out/'src';src.mkdir();work=out/'work';work.mkdir()
    # Only RNG routines are linked. No matrix-element, PDF or integrator library.
    for name in ['ranmar.f','ran1.f']:(src/name).write_text(texts['Source/'+name])
    ds=texts['Source/dsample.f'];m=re.search(r'(?ims)^      function ran1\(idum\).*?^      end\s*$',ds)
    require(m is not None,'RAN1_EXTRACTION_FAILED');(src/'aux_ran1.f').write_text(m.group()+'\n')
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';env=mg_environment(cfg)
    flags=[compiler,'-O0','-std=legacy','-ffixed-line-length-none']
    commands=[[*flags,HERE/'src/rng_noninterference_probe.f90',src/'ranmar.f',src/'ran1.f',src/'aux_ran1.f','-o',out/'rng_probe'],
        [*flags,HERE/'src/fixed_weight_kernel_probe.f90','-o',out/'weight_probe']]
    for command in commands:run(command,out,env)
    stdout=[run([out/'rng_probe',str(mode)],work,env) for mode in [0,1]]
    for i,t in enumerate(stdout):(out/('rng_mode_'+str(i)+'.txt')).write_text(t)
    trace=lambda t:re.findall(r'RANMAR_TRACE\s+\d+\s+(\S+)',t)
    aux=lambda t:re.findall(r'AUXILIARY_NEXT\s+(\S+)\s+(\S+)',t)
    require(len(trace(stdout[0]))==16 and trace(stdout[0])==trace(stdout[1]),'RANMAR_INTERFERENCE')
    require(aux(stdout[0])!=aux(stdout[1]),'AUXILIARY_TEST_NOT_EXERCISED')
    weight=run([out/'weight_probe'],work,env);(out/'fixed_weight.txt').write_text(weight)
    require(re.search(r'FIXED_WEIGHT_SUMS\s+41\.0+\s+289\.0+',weight),'FIXED_WEIGHT_METHOD_FAILURE')
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt={'status':'BLOCKED_INTEGRATION_SEMANTICS','authorization_status':'NOT_GRANTED',
        'scope':'RNG-only actual native routines and fixed synthetic weights; no ME, phase space or integral',
        'RANMAR_trace_equal':True,'RANMAR_draws_per_mode':16,'interleaved_aux_calls_mode_1':{'ran1':32,'xran1':16},
        'auxiliary_next_draws_differ':True,'fixed_weight_sum':41,'fixed_weight_sum_squares':289,
        'fixed_weight_scope':'copied arithmetic shape only; not the native integrator or writer path',
        'conditional_invariants':['three separate RNG states; auxiliary draws do not advance RANMAR in tested sequence',
            'single HH channel bypasses ran1 channel selection; zooming explicitly false in pinned source',
            'same point/weight stream implies same sum, squared sum and weight-based grid increments'],
        'known_changes':['candidate nw/swgt and auxiliary RNG draws are removed',
            'th_nunwgt, th_maxwgt, neventswritten become zero; original candidate diagnostics lost',
            'negative accuracy luminosity stopping depends on neventswritten and is not equivalent'],
        'unproven':['same complete native point/weight/ME trace through all iterations',
            'same grids, adaptation, reported integral and error under real no-output execution',
            'native numerical tail/overweight counters with suppressed candidate storage',
            'complete transient output observation during a genuine survey'],
        'required_next':'review narrowly instrumented paired no-output native paths before enabling Stage A; no equivalence claim',
        'native_survey_executed':False,'new_ME_calls':0,'new_integrals':0,'new_physical_events':0,
        'postcondition':output_audit(work),'source_audit':rows,
        'resources_preparation_only':{'wall_seconds':time.monotonic()-start,
            'child_CPU_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
            'child_peak_RSS_KiB_process_lifetime_high_water':after.ru_maxrss,
            'disk_bytes_before_receipt':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),
            'limits':'one CPU affinity, each child 60 CPU/wall seconds, 64MiB file size; compiler and RNG probes only'},
        'compiler_version':run([compiler,'--version'],out,env).splitlines()[0],
        'probe_sources':[{'path':p.relative_to(REPO).as_posix(),'sha256':sha(p)} for p in sorted((HERE/'src').glob('*.f90'))],
        'linked_local_source_hashes':[{'name':p.name,'sha256':sha(p)} for p in sorted(src.iterdir())],
        'executables':[{'name':p.name,'sha256':sha(p)} for p in [out/'rng_probe',out/'weight_probe']]}
    save(out/'semantics.json',receipt);return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--native',required=True)
    a=p.parse_args();r=probe(a.output,a.native);print(json.dumps({k:v for k,v in r.items() if k!='source_audit'},indent=2))
if __name__=='__main__':main()
