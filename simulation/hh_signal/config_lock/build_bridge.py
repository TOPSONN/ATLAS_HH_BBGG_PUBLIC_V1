"""Compile a real isolated guarded native driver; never execute that driver."""
import re,shutil,subprocess
from pathlib import Path
from .contract import *
from .native import run
from simulation.hh_signal.campaign.common import mg_environment

def build(replica,native,cfg):
    replica=Path(replica);native=Path(native);target=replica/'native_build';target.mkdir(exist_ok=False)
    process=target/'process';process.mkdir()
    rows=lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary']
    for r in rows:
        require(sha(native/r['path'])==r['sha256'],'NATIVE_BUILD_INPUT_CHANGED')
        dest=process/r['path'];dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((native/r['path']).read_bytes())
    # Symlink inputs are dereferenced into ordinary isolated files. No archive,
    # object, card or source in the historic process can be modified by build.
    require(not any(p.is_symlink() for p in process.rglob('*')),'BUILD_SYMLINK_FORBIDDEN')
    sub=process/'SubProcesses/P0_gg_hh';cards=process/'Cards';cards.mkdir()
    for src,dest in [('working_run_card.dat','run_card.dat'),('param_card.dat','param_card.dat')]:
        (cards/dest).write_bytes((replica/'cards'/src).read_bytes())
    preview=(replica/'cards/run_card.inc').read_text()
    (process/'Source/run_card.inc').write_text('\n'.join('      '+line.strip() for line in preview.splitlines() if line.strip())+'\n')
    text=(cards/'run_card.dat').read_text();seed=int(card_values(text)['iseed'])
    verify_cards(text,text,text,(process/'Source/run_card.inc').read_text(),seed)
    for src,dest in [('driver.f',sub/'driver.f'),('unwgt.f',sub/'unwgt.f'),
        ('rw_events.f',process/'Source/rw_events.f'),('hh_pre_sampling_guard.f',sub/'hh_pre_sampling_guard.f')]:
        dest.write_bytes((replica/'bridge_source'/src).read_bytes())
    sources=['driver','myamp','genps','unwgt','setcuts','get_color','cuts','cluster','reweight','initcluster',
        'addmothers','setscales','idenparts','dummy_fct','auto_dsig','auto_dsig1','matrix1','hh_pre_sampling_guard']
    compiler=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';env=mg_environment(cfg)
    flags=[compiler,'-O0','-w','-std=legacy','-ffixed-line-length-none','-I'+str(sub),'-I'+str(process/'Source'),
        '-I'+str(process/'Source/MODEL'),'-I'+str(process/'Source/PDF/gammaUPC')]
    objects=[]
    for name in sources:
        obj=sub/(name+'.o');run([*flags,'-c',sub/(name+'.f'),'-o',obj],sub,env);objects.append(obj)
    # Override the old library versions of seed/PDF initialization and event
    # serialization with freshly compiled, hash-bound objects.
    for name in ['setrun','rw_events']:
        obj=process/'Source'/(name+'.o');run([*flags,'-c',process/'Source'/(name+'.f'),'-o',obj],sub,env);objects.append(obj)
    exe=target/'hh_integral_guarded'
    libraries=['MadLoop','cts','iregi','dhelas','dsample','model','generic','pdf','gammaUPC','cernlib','bias']
    run([compiler,'-o',exe,*objects,'-L'+str(process/'lib'),*['-l'+n for n in libraries],'-lstdc++'],sub,env)
    # Execute ONLY the explicit preflight exit branch inserted before the
    # first helicity initialization / ME boundary. No survey/measurement.
    probe_work=sub/'preflight_only';probe_work.mkdir()
    (probe_work/'iproc.dat').write_text('0\n');(probe_work/'moffset.dat').write_text('0\n')
    seed=int(card_values((cards/'run_card.dat').read_text())['iseed'])
    (probe_work/'randinit').write_text('r='+str(seed)+'\n')
    stdout=run([exe],probe_work,{**env,'HH_PREFLIGHT_ONLY':'1'})
    require('HH_NATIVE_PREFLIGHT_ONLY_ZERO_ME_CALLS' in stdout and 'HH_PRE_SAMPLING_CONFIG_PASS' in stdout and
        'about to integrate' not in stdout and re.search(r'HH_GUARD_SUPPRESSED_CALLS\s+0\s+0\s+0',stdout),
        'NATIVE_DRIVER_PREFLIGHT_DID_NOT_EXIT_BEFORE_SAMPLING')
    (target/'driver_preflight_stdout.txt').write_text(stdout)
    from .writers import output_audit
    audit=output_audit(probe_work)
    denied=subprocess.run([str(exe)],cwd=probe_work,env={**env,'HH_PREFLIGHT_ONLY':'0'},capture_output=True,text=True,timeout=30)
    require(denied.returncode==80 and 'HH_INTEGRATION_NOT_AUTHORIZED' in denied.stdout and
        'about to integrate' not in denied.stdout,'NATIVE_INTEGRAL_DISPATCH_NOT_DENIED')
    return {'status':'PASS_ACTUAL_ISOLATED_DRIVER_BUILD_AND_INITIALIZATION_ONLY_GATES','executable_sha256':sha(exe),
        'runtime_source_files':len(rows),'new_objects':len(objects),'binary_executed':'PREFLIGHT_EXIT_ONLY',
        'full_driver_initialization_probe':'PASS_EXIT_BEFORE_HELICITY_OR_ME_INITIALIZATION','new_integrals':0,'new_ME_calls':0,
        'preflight_stdout':stdout,'preflight_output_audit':audit,
        'unauthorized_native_dispatch_exit':denied.returncode,
        'fresh_compiled_run_include_sha256':sha(process/'Source/run_card.inc'),
        'native_pre_sampling_gate_source_sha256':sha(sub/'hh_pre_sampling_guard.f'),
        'source_snapshot_no_symlinks':True,'NATIVE_RUNTIME_GATE':'NOT_EVALUATED'}
