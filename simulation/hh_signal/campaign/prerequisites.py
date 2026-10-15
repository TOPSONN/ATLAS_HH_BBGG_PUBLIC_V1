"""Bounded native Ward test on a copied generated finite-mass amplitude."""
import re,shutil
from .common import *

def ward(build,numerical,output,monitor):
    from simulation.hh_signal.scripts.verify_loop_model import fixed_point,modify_card
    out=Path(output);shutil.copytree(build['matrix_element'],out,symlinks=False)
    work=out/'SubProcesses/P0_gg_hh'
    ml=out/'Cards/MadLoopParams.dat';t=ml.read_text()
    t,n=re.subn(r'(#CTModeRun\s*\n)[^\n]+',r'\g<1>4',t);require(n==1,'MISSING_NATIVE_QP_MODE');ml.write_text(t)
    for name in ('helas_calls_ampb_1.f','mp_helas_calls_ampb_1.f'):
        p=work/name;t=p.read_text();needle=next(s for s in t.splitlines() if 'VXXXXX(P(0,1)' in s)
        require(t.count(needle)==1,'AMBIGUOUS_WARD_POLARIZATION_SOURCE')
        replacement='\n'.join('      W('+str(5+j)+',1)=P('+str(j)+',1)/P(0,1)' for j in range(4))
        p.write_text(t.replace(needle,needle+'\n'+replacement))
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    monitor.run_command(['make','-j1','check'],work,'compile_native_ward',env=env)
    card=(out/'Cards/param_card.dat').read_text();rows=[]
    for j,e in enumerate((250.001,300.,400.,800.)):
        p=fixed_point(e);(work/'PS.input').write_text('\n'.join(' '.join(f'{v:.17e}' for v in q) for q in p)+'\n')
        (out/'Cards/param_card.dat').write_text(modify_card(card,'loop',1,e/2))
        result=monitor.run_command([str(work/'check'),'1'],work,'native_ward_'+str(j),env=env)
        value=float(re.search(r'PHASE7A_RESULT\s+(\S+)',Path(result['log_path']).read_text())[1])
        nominal=next(r['finite_squared_me'] for r in numerical['evaluations'] if r['mHH_gev']==e and r['kappa_lambda']==1 and r['label'].startswith('e'))
        require(0<=value/nominal<1e-12,'FAILED_ACTUAL_NATIVE_WARD')
        rows.append({'mHH_gev':e,'ward_squared_me':value,'nominal_squared_me':nominal,'ratio':value/nominal,
            'precision_mode':'native_CutTools_QP','external_gluon1_polarization':'p/E','log_sha256':result['log_sha256']})
    return {'status':'PASS_ACTUAL_FULL_MASS_WARD_ZERO_SOURCE_EVENTS','physical_events':0,'ward_points':rows}

def prepare_cache(state):
    from .setup import build_native,build_mg,check_numerical
    import uuid
    state=Path(state);scratch=Path.home()/'.local/share/atlas-hh-phase7'/('prepared_'+uuid.uuid4().hex)
    resources(scratch,10);scratch.mkdir(parents=True)
    m=Monitor(scratch,{'max_hours':2,'max_disk_gb':5},readonly_roots=(Path.home()/'opt',Path.home()/'.local/share/atlas-hh-phase6a/toolchain'))
    try:
        m.install_signals();scientific_environment()
        native=build_native(scratch/'native',m)
        build=build_mg(scratch/'generator',m,native['model_values']);numerical=check_numerical(build,m)
        w=ward(build,numerical,scratch/'ward',m)
        save_json(state/'native_build.json',native)
        save_json(state/'model_build.json',{'build':build,'numerical':numerical,'metrics':m.metrics()})
        save_json(state/'loop_prerequisite.json',w)
        save_json(state/'cache_preparation.json',{'physical_source_events':0,'metrics':m.metrics(),'scratch':str(scratch)})
    finally:m.restore_signals()
