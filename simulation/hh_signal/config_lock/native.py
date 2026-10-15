"""Bounded PDF/RNG-file initialization and writer-boundary probes, no ME."""
import io,json,os,re,resource,shutil,subprocess,sys,time
from pathlib import Path
from .contract import *
from .writers import suppress_writers,suppress_permanent_writer,output_audit
from simulation.hh_signal.integration_audit.audit import save
from simulation.hh_signal.campaign.common import mg_environment

class ProbeBudget:
    """Aggregate preparation/probe budget. Integral monitoring remains gated."""
    def __init__(self,root):
        self.root=Path(root);self.start=time.monotonic();self.cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
        self.last_disk=0;self.check(force_disk=True)
    def check(self,force_disk=False):
        caps=lock()['administrative_ceilings'];now=time.monotonic();cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
        require(now-self.start<caps['aggregate_wall_seconds'] and
            cpu.ru_utime+cpu.ru_stime-self.cpu.ru_utime-self.cpu.ru_stime<caps['aggregate_CPU_seconds'],'AGGREGATE_PREPARATION_BUDGET')
        if force_disk or now-self.last_disk>2:
            require(sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())<caps['additional_disk_bytes'],'AGGREGATE_PREPARATION_DISK_CAP')
            self.last_disk=now

BUDGET=None

def child_limits():
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def run(command,cwd,env):
    if BUDGET:BUDGET.check()
    p=subprocess.run(list(map(str,command)),cwd=cwd,env=env,capture_output=True,text=True,timeout=60,preexec_fn=child_limits)
    if BUDGET:BUDGET.check()
    require(p.returncode==0,'NATIVE_NO_INTEGRAL_PROBE_FAILED:'+p.stdout+p.stderr)
    return p.stdout

def preview(card,mg):
    sys.path.insert(0,str(mg));from madgraph.various.banner import RunCardLO
    # The constructor has no file location and therefore no neighboring
    # default-card path. Every write gets a completely fresh object.
    obj=RunCardLO(io.StringIO(card));out=io.StringIO();obj.write_include_file(None,output_file=out)
    return out.getvalue()

def initialize_probe(folder,native,seed,compiled,cfg):
    folder=Path(folder);folder.mkdir(exist_ok=False);src=folder/'src';src.mkdir();work=folder/'work';work.mkdir()
    for rel in ['Source/PDF/pdfwrap.f','Source/PDF/pdf.inc','Source/alfas.inc','Source/alfas_functions.f','Source/ranmar.f']:
        target=src/Path(rel).relative_to('Source');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((native/rel).read_bytes())
    setrun=(native/'Source/setrun.f').read_text();start=re.search(r'(?im)^      subroutine get_pdfup\b',setrun)
    require(start is not None,'MISSING_NATIVE_METADATA_MAPPER');(src/'get_pdfup.f').write_text(setrun[start.start():])
    assignments='\n'.join('      '+line.strip() for line in compiled.splitlines() if re.match(r'\s*(pdlabel|pdsublabel\([12]\)|lhaid|iseed)\s*=',line,re.I))+'\n'
    (src/'probe_assignments.inc').write_text(assignments)
    (work/'randinit').write_text('r='+str(seed)+'\n');(work/'iproc.dat').write_text('0\n');(work/'moffset.dat').write_text('0\n')
    table=native/'lib/Pdfdata/cteq6l1.tbl';require(table.is_file(),'MISSING_ACTUAL_CTEQ6L1_TABLE')
    for parent in [work/'lib/Pdfdata',folder/'lib/Pdfdata']:
        parent.mkdir(parents=True);shutil.copyfile(table,parent/table.name)
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';env=mg_environment(cfg)
    exe=folder/'initialization_probe'
    command=[compiler,'-O0','-std=legacy','-ffixed-line-length-none','-I'+str(src/'PDF'),'-I'+str(src),
        HERE/'src/initialization_probe.f',src/'PDF/pdfwrap.f',src/'alfas_functions.f',src/'ranmar.f',src/'get_pdfup.f',
        native/'lib/libpdf.a',native/'lib/libgeneric.a','-o',exe]
    run(command,folder,env);stdout=run([exe,str(seed)],work,env);(folder/'probe_stdout.txt').write_text(stdout)
    def tokens(label):
        found=re.findall(r'(?m)^\s*HH_'+label+r'\s+(.*)$',stdout);require(len(found)==1,'MISSING_NATIVE_PROBE_FIELD:'+label);return found[0].split()
    pdf=tokens('PDF');alpha=tokens('ALPHA');offsets=tokens('OFFSETS')
    rows=[{'Q_GeV':float(q),'alpha_s':float(a)} for q,a in re.findall(r'(?m)^\s*HH_RUNNING\s+(\S+)\s+(\S+)\s*$',stdout)]
    runtime={'PDF':pdf[0],'PDSUBLABEL':pdf[1:],'alpha_s_MZ':float(alpha[0]),'running_loops':int(alpha[1]),
        'PDFSUP':list(map(int,tokens('PDFSUP'))),'requested_seed':seed,'compiled_seed':int(tokens('COMPILED_SEED')[0]),
        'native_base_seed':int(tokens('BASE_SEED')[0]),'stage_offsets':dict(zip(['iproc','moffset'],map(int,offsets))),
        'alpha_values':rows,'probe_sha256':sha(HERE/'src/initialization_probe.f'),
        'executable_sha256':sha(exe),'CTEQ6L1_table_sha256':sha(table),'new_ME_calls':0,'new_integrals':0,
        'scope':'actual native PDF initialization and get_base/offset reads; no density, RNG draw, kinematics, ME or integral'}
    output_audit(work)
    return runtime

def writer_probe(folder,native,cfg):
    folder=Path(folder);folder.mkdir(exist_ok=False);work=folder/'work';work.mkdir()
    original=(native/'SubProcesses/unwgt.f').read_text();patched=suppress_writers(original)
    source=folder/'unwgt_guarded.f';source.write_text(patched)
    permanent=folder/'rw_events_guarded.f';permanent.write_text(suppress_permanent_writer((native/'Source/rw_events.f').read_text()))
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';env=mg_environment(cfg)
    flags=[compiler,'-O0','-std=legacy','-ffixed-line-length-none','-ffunction-sections','-fdata-sections',
        '-I'+str(native/'SubProcesses/P0_gg_hh'),'-I'+str(native/'Source'),'-I'+str(native/'Source/MODEL')]
    # Compile all native patched routines; link only the exercised boundaries.
    run([*flags,'-c',source,'-o',folder/'unwgt_guarded.o'],folder,env)
    run([*flags,'-c',permanent,'-o',folder/'rw_events_guarded.o'],folder,env)
    exe=folder/'writer_boundary_probe'
    run([*flags,HERE/'src/writer_probe.f',folder/'unwgt_guarded.o','-Wl,--gc-sections','-o',exe],folder,env)
    stdout=run([exe],work,env);require(re.search(r'HH_GUARD_SUPPRESSED_CALLS\s+1\s+1\s+1',stdout),'WRITER_BOUNDARY_COUNTERS')
    # Direct permanent serialization must terminate, even if an unexpected
    # caller bypasses the suppressed candidate/storage paths.
    deny=folder/'deny_probe.f';deny.write_text('      program denied_writer\n      call write_event\n      end\n')
    run([*flags,deny,folder/'rw_events_guarded.o','-Wl,--gc-sections','-o',folder/'deny_probe'],folder,env)
    p=subprocess.run([str(folder/'deny_probe')],cwd=work,env=env,capture_output=True,text=True,timeout=10)
    require(p.returncode==86 and 'HH_GUARD_PERMANENT_EVENT_WRITE_FORBIDDEN' in p.stdout,'NATIVE_PERMANENT_WRITER_NOT_DENIED')
    return {'status':'PASS_NATIVE_SYNTHETIC_WRITER_BOUNDARIES_ONLY','suppressed_candidate_store_clear':[1,1,1],
        'permanent_writer_exit':p.returncode,'stdout':stdout,'patched_unwgt_sha256':sha(source),
        'patched_permanent_writer_sha256':sha(permanent),'executable_sha256':sha(exe),
        'postcondition':output_audit(work),'NATIVE_RUNTIME_GATE':'NOT_EVALUATED','new_integrals':0,'new_ME_calls':0}

def gate_probe(folder,native,cfg,metadata_mapper):
    folder=Path(folder);folder.mkdir(exist_ok=False);work=folder/'work';work.mkdir()
    (work/'iproc.dat').write_text('0\n');(work/'moffset.dat').write_text('0\n')
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';env=mg_environment(cfg)
    flags=[compiler,'-O0','-std=legacy','-ffixed-line-length-none','-I'+str(native/'SubProcesses/P0_gg_hh'),
        '-I'+str(native/'Source'),'-I'+str(native/'Source/MODEL')]
    exe=folder/'pre_sampling_gate_probe'
    run([*flags,HERE/'src/gate_probe.f',HERE/'src/pre_sampling_guard.f',metadata_mapper,
        native/'Source/alfas_functions.f',native/'Source/ranmar.f','-o',exe],folder,env)
    cases=[]
    for mode,expected in [('valid',0),('pdf',71),('labels',72),('alpha',73),('seed',74),('mass',76),('header',77)]:
        result=subprocess.run([str(exe),mode],cwd=work,env=env,capture_output=True,text=True,timeout=10)
        require(result.returncode==expected,'NATIVE_PRE_SAMPLING_GATE_CASE:'+mode)
        cases.append({'case':mode,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    return {'status':'PASS_ACTUAL_NATIVE_GATE_SYNTHETIC_CONTEXT_TESTS','cases':cases,'source_sha256':sha(HERE/'src/pre_sampling_guard.f'),
        'executable_sha256':sha(exe),'postcondition':output_audit(work),'NATIVE_RUNTIME_GATE':'NOT_EVALUATED',
        'scope':'native guard in synthetic common-block contexts; full driver not executed','new_integrals':0,'new_ME_calls':0}
