"""Build four real native drivers; execute only the retained pre-ME exit/STOP80."""
import re,time,resource
from .contracts import *
from simulation.hh_signal.config_lock.contract import lock,verify_cards
from simulation.hh_signal.config_lock.controller import patch_driver
from simulation.hh_signal.config_lock.writers import output_audit
from simulation.hh_signal.semantics_recovery.overlay import replace_once
from simulation.hh_signal.semantics_recovery.runner import command
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.integration_audit.audit import save,card_values

def prepare_native(replica):
    replica=Path(replica);native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    target=replica/'native_build';target.mkdir();process=target/'process';process.mkdir()
    f=lock();rows=f['frozen_runtime_sources']+f['runtime_build_auxiliary'];before=time.monotonic()
    cpu=resource.getrusage(resource.RUSAGE_CHILDREN)
    for row in rows:
        require(sha(native/row['path'])==row['sha256'],'NATIVE_PREPARATION_SOURCE_DRIFT')
        p=process/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((native/row['path']).read_bytes())
    require(not any(p.is_symlink() for p in process.rglob('*')),'NATIVE_PREPARATION_SYMLINK')
    sub=process/'SubProcesses/P0_gg_hh';cards=process/'Cards';cards.mkdir()
    text=(replica/'cards/reviewed_run_card.dat').read_text();seed=int(card_values(text)['iseed'])
    include=(replica/'cards/run_card.inc').read_text();verify_cards(text,text,text,include,seed)
    (cards/'run_card.dat').write_text(text)
    (cards/'param_card.dat').write_bytes((replica/'cards/param_card.dat').read_bytes())
    (process/'Source/run_card.inc').write_text('\n'.join('      '+s.strip() for s in include.splitlines() if s.strip())+'\n')
    # Native arithmetic, candidate updates, RNG, grid/error/stopping unchanged.
    driver=patch_driver((native/'SubProcesses/P0_gg_hh/driver.f').read_text(),seed)
    driver=replace_once(driver,"      open(unit=lun,status='scratch')",'      call hh_open_sink(lun)')
    driver=replace_once(driver,'      call hh_guard_report','      call hh_io_report')
    (sub/'driver.f').write_text(driver)
    unwgt=replace_once((native/'SubProcesses/unwgt.f').read_text(),
        "      open(unit = lunw, file='events.lhe', status='unknown')",'      call hh_open_sink(lunw)')
    dsample=replace_once((native/'Source/dsample.f').read_text(),
        "      open(unit=67,file='events.lhe',status='unknown')",'      call hh_open_sink(67)')
    rw=replace_once((native/'Source/rw_events.f').read_text(),
        "         open (unit=lun_ban, status='scratch')",'         call hh_open_sink(lun_ban)')
    start=rw.index('      subroutine write_event(lun,');at=rw.index("      write(lun,'(a)') '<event>'",start)
    rw=rw[:at]+'      call hh_require_transient(lun)\n'+rw[at:]
    (sub/'unwgt.f').write_text(unwgt);(process/'Source/dsample.f').write_text(dsample);(process/'Source/rw_events.f').write_text(rw)
    h=REPO/'simulation/hh_signal/semantics_recovery/src'
    io=(h/'io_and_rng.f90').read_text().split('\nsubroutine hh_trace_stream')[0]
    (sub/'native_io_only.f90').write_text(io+'\n')
    (sub/'hh_pre_sampling_guard.f').write_bytes((REPO/'simulation/hh_signal/config_lock/src/pre_sampling_guard.f').read_bytes())
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran'
    flags=[compiler,'-O0','-w','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none',
        '-I'+str(sub),'-I'+str(process/'Source'),'-I'+str(process/'Source/MODEL'),'-I'+str(process/'Source/PDF/gammaUPC'),'-J'+str(sub)]
    names=['driver','myamp','genps','unwgt','setcuts','get_color','cuts','cluster','reweight','initcluster','addmothers','setscales',
        'idenparts','dummy_fct','auto_dsig','auto_dsig1','matrix1','hh_pre_sampling_guard'];objects=[]
    files=[sub/(n+'.f') for n in names]+[process/'Source'/(n+'.f') for n in ['setrun','rw_events','dsample']]+[sub/'native_io_only.f90']
    for file in files:
        obj=file.with_suffix('.o');command([*flags,'-c',file,'-o',obj],sub,env);objects.append(obj)
    obj=sub/'anonymous_io.o';command([str(compiler).replace('gfortran','gcc'),'-O0','-c',h/'anonymous_io.c','-o',obj],sub,env);objects.append(obj)
    exe=target/'hh_integral_guarded'
    libs=['MadLoop','cts','iregi','dhelas','dsample','model','generic','pdf','gammaUPC','cernlib','bias']
    command([compiler,'-o',exe,*objects,'-L'+str(process/'lib'),*['-l'+n for n in libs],'-lstdc++'],sub,env)
    work=sub/'preflight_only';work.mkdir();(work/'temporary').mkdir()
    for name,value in [('randinit','r='+str(seed)),('iproc.dat','0'),('moffset.dat','0')]:(work/name).write_text(value+'\n')
    run_env={**env,'TMPDIR':str(work/'temporary')}
    r,_=command([exe],work,{**run_env,'HH_PREFLIGHT_ONLY':'1'})
    require('HH_NATIVE_PREFLIGHT_ONLY_ZERO_ME_CALLS' in r.stdout and
        re.search(r'HH_PRE_SAMPLING_CONFIG_PASS\s+'+str(seed)+r'\s+0\s+0',r.stdout),'NATIVE_PRE_ME_CONFIG_EXIT')
    denied,_=command([exe],work,{**run_env,'HH_PREFLIGHT_ONLY':'0'},expected=80)
    require('HH_INTEGRATION_NOT_AUTHORIZED' in denied.stdout and 'about to integrate' not in denied.stdout,'NATIVE_STOP80_MISSING')
    require(not list((work/'temporary').iterdir()),'NAMED_TRANSIENT_FROM_PREFLIGHT')
    audit=output_audit(work)
    for row in rows:require(sha(native/row['path'])==row['sha256'],'ORIGINAL_SOURCE_CHANGED_DURING_BUILD')
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt={'status':'PASS_REAL_NATIVE_BUILD_AND_PRE_ME_EXIT_ONLY','seed':seed,'native_runtime_gate':'NOT_EVALUATED_REAL_SURVEY',
        'STOP80_exit':80,'new_physical_ME_calls':0,'new_integrals':0,'new_independent_events':0,
        'runtime_source_files':len(rows),'new_objects':len(objects),'executable_sha256':sha(exe),
        'actual_initialization_stdout':r.stdout,'output_audit':audit,
        'native_IO_boundary':'original bookkeeping/serializer retained; approved anonymous regular scratch only',
        'patched_files':[{'path':p.relative_to(process).as_posix(),'sha256':sha(p)} for p in [sub/'driver.f',sub/'unwgt.f',
            process/'Source/dsample.f',process/'Source/rw_events.f',sub/'native_io_only.f90',sub/'hh_pre_sampling_guard.f']],
        'resources_preparation_only':{'wall_seconds':time.monotonic()-before,
            'child_CPU_seconds':after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime,
            'child_peak_RSS_KiB_process_lifetime_high_water':after.ru_maxrss,
            'logical_disk_bytes':sum(p.stat().st_size for p in target.rglob('*') if p.is_file())}}
    save(target/'native_preparation.json',receipt);return receipt
