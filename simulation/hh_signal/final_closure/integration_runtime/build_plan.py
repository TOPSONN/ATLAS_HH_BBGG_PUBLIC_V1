"""Pure compile/link construction; no compiler invocation at import or planning."""
from .contract import *

LIBS=['MadLoop','cts','iregi','dhelas','dsample','model','generic','pdf','gammaUPC','cernlib','bias']
def plan(process,folder,compiler):
    process=Path(process);folder=Path(folder);compiler=Path(compiler)
    sub=process/'SubProcesses/P0_gg_hh';h=REPO/'simulation/hh_signal/semantics_recovery/src'
    flags=[compiler,'-O0','-w','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none','-I'+str(sub),
        '-I'+str(process/'Source'),'-I'+str(process/'Source/MODEL'),'-I'+str(process/'Source/PDF/gammaUPC'),'-J'+str(sub)]
    names=['driver','myamp','genps','unwgt','setcuts','get_color','cuts','cluster','reweight','initcluster','addmothers',
        'setscales','idenparts','dummy_fct','auto_dsig','auto_dsig1','matrix1','hh_pre_sampling_guard']
    files=[HERE/'observers.f90',sub/'native_checks_corrected.f',sub/'native_io_only.f90']+[sub/(n+'.f') for n in names]+[
        process/'Source'/(n+'.f') for n in ['setrun','rw_events','dsample','ranmar']]
    jobs=[];objects=[]
    for i,p in enumerate(files):
        obj=sub/f'hi_{i}.o';jobs.append([*flags,'-c',p,'-o',obj]);objects.append(obj)
    for i,p in enumerate([h/'anonymous_io.c',HERE/'control.c']):
        obj=sub/f'hi_c_{i}.o';jobs.append([str(compiler).replace('gfortran','gcc'),'-O0','-c',p,'-o',obj]);objects.append(obj)
    jobs.append([compiler,'-o',folder/'hh_final_integral_reviewed',*objects,'-L'+str(process/'lib'),*['-l'+n for n in LIBS],'-lstdc++'])
    return [[str(arg) for arg in job] for job in jobs]
