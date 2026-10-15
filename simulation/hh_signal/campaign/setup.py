from __future__ import annotations
import os, shutil, shlex, subprocess, sys, json, re
from pathlib import Path
from .common import *

def build_native(folder,monitor):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    dc,pc,env=native_environment();root=Path(dc['root_prefix'])
    compiler='/usr/bin/g++'
    flags=shlex.split(subprocess.check_output([str(root/'bin/root-config'),'--cflags','--libs'],env=env,text=True))
    common=[compiler,'-std=c++20','-O2','-Wall','-Wextra',
       '-I'+str(CAMPAIGN/'include'),'-I'+str(REPO/'simulation/pythia8/include'),
       '-I'+str(REPO/'simulation/new_backgrounds/include'),'-I'+str(REPO/'simulation/delphes/include'),
       '-I'+str(Path(pc['pythia_prefix'])/'include'),'-I'+str(Path(pc['hepmc3_prefix'])/'include'),
       '-I'+str(Path(dc['delphes_prefix'])/'include')]
    libraries=['-L'+str(Path(pc['pythia_prefix'])/'lib'),'-lpythia8',
       '-L'+str(Path(pc['hepmc3_prefix'])/'lib'),'-lHepMC3',
       '-L'+str(Path(dc['delphes_prefix'])/'lib'),'-lDelphes',*flags]
    binaries={}
    for name in ('initialize_decay_model','shower_signal','validate_signal_hepmc','analyze_signal_root'):
        source=CAMPAIGN/'src'/(name+'.cxx')
        if name=='analyze_signal_root':
            command=[str(root/'bin/x86_64-conda-linux-gnu-c++'),'-std=c++20','-O2',
              '-I'+str(REPO/'simulation/delphes/include'),'-I'+str(REPO/'simulation/pythia8/include'),
              '-I'+str(Path(dc['delphes_prefix'])/'include'),str(source),
              '-L'+str(Path(dc['delphes_prefix'])/'lib'),'-lDelphes',*flags,'-o',str(folder/name)]
        else:
            command=[*common,str(source),'-L'+str(Path(pc['pythia_prefix'])/'lib'),'-lpythia8',
              '-L'+str(Path(pc['hepmc3_prefix'])/'lib'),'-lHepMC3','-ldl','-o',str(folder/name)]
        monitor.run_command(command,folder,'compile_'+name,env=env)
        binaries[name]={'path':str(folder/name),'sha256':sha(folder/name),'source_sha256':sha(source)}
    model=folder/'initialized_decay_model.json'
    monitor.run_command([binaries['initialize_decay_model']['path'],pc['xml_path'],
        str(REPO/'simulation/pythia8/config/baseline_shower.cmnd'),str(model)],folder,'initialize_decay_model_zero_events',env=env)
    table=read_json(model);require(table['events_generated']==0 and table['scope']=='MODEL_BR_ONLY','HIGGS_BR_MODEL_FAILURE')
    receipt={'status':'PASS_NATIVE_SIGNAL_BUILD_AND_INITIALIZED_MODEL_ONLY','binaries':binaries,
             'model_table':{'path':str(model),'sha256':sha(model)},'model_values':table}
    save_json(folder/'build_receipt.json',receipt)
    return receipt

def build_mg(folder,monitor,model_values):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    cfg=read_json(REPO/'.local/mg5_installation.json');original=Path(cfg['mg5_path']).resolve()
    shutil.copytree(original,folder/'mg5',symlinks=True,ignore=shutil.ignore_patterns('tests','__pycache__','*.pyc','*.pkl','*.pickle'))
    env=mg_environment(cfg);env['TMPDIR']=str(folder/'tmp');(folder/'tmp').mkdir()
    monitor.run_command([str(Path(cfg['toolchain_prefix'])/'bin/python3'),'-B','-O',
       str(CAMPAIGN/'mg5_adapter.py'),str(folder/'mg5'),str(folder/'production_template')],folder,'export_full_loop_madevent',env=env)
    process=folder/'production_template'
    from simulation.hh_signal.scripts.verify_loop_model import modify_card
    card=(process/'Cards/param_card.dat').read_text()
    card=modify_card(card,'sminputs',3,.130)
    card,n=re.subn(r'(?im)^(DECAY\s+25\s+)\S+',lambda m:m[1]+f"{model_values['H_total_width_gev']:.12e}",card)
    require(n==1,'actual Higgs width field missing')
    (folder/'param_card_frozen.dat').write_text(card)
    sys.path.insert(0,str(folder/'mg5'))
    import madgraph
    madgraph.ReadWrite=False
    from madgraph.various.banner import RunCardLO
    run=RunCardLO(str(process/'Cards/run_card.dat'))
    overrides={'nevents':100,'iseed':20261121,'ebeam1':6500.,'ebeam2':6500.,'lpp1':1,'lpp2':1,
       'pdlabel':'cteq6l1','lhaid':0,'fixed_ren_scale':False,'fixed_fac_scale':False,
       'dynamical_scale_choice':4,'scalefact':0.5,'req_acc':0.02,'nhel':0,
       'use_syst':False,'event_norm':'average','lhe_version':3.0,'ickkw':0,'cut_decays':False}
    for key,value in overrides.items():run[key]=value
    run.write(str(folder/'run_card_frozen.dat'))
    for ml in (process/'Cards/MadLoopParams.dat',folder/'matrix_element/Cards/MadLoopParams.dat'):
        text=ml.read_text()
        for key,value in [('MLReductionLib','1'),('MLStabThres','1.000000d-09'),('CTStabThres','1.000000d-09'),
                          ('HelicityFilterLevel','0'),('WriteOutFilters','.false.')]:
            text,n=re.subn(r'(#'+key+r'\s*\n)[^\n]+',lambda m:m[1]+value,text)
            require(n==1,'missing MadLoop numerical setting')
        ml.write_text(text)
    receipt={'status':'PASS_NATIVE_FULL_MASS_EXPORT_AND_FROZEN_PROPOSED_CARDS_ZERO_EVENTS',
       'process_template':str(process),'private_mg5':str(folder/'mg5'),'matrix_element':str(folder/'matrix_element'),
       'model_table_values':model_values,'overrides':overrides,
       'param_card_sha256':sha(folder/'param_card_frozen.dat'),'run_card_sha256':sha(folder/'run_card_frozen.dat'),
       'native_scale_source_sha256':sha(process/'SubProcesses/setscales.f'),
       'native_PDF_source_sha256':sha(process/'Source/PDF/pdfwrap.f')}
    save_json(folder/'build_receipt.json',receipt)
    return receipt

def check_numerical(build,monitor):
    from simulation.hh_signal.scripts.verify_loop_model import fixed_point,modify_card,check_numerical_results
    folder=Path(build['matrix_element']);work=folder/'SubProcesses/P0_gg_hh'
    shutil.copyfile(PACKAGE/'src/check_fixed_point.f',work/'check_sa.f')
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    monitor.run_command(['make','-j1','check'],work,'compile_campaign_me',env=env)
    frozen='Block loop\n  1 9.118800000000e+01 # standalone MU_R\n'+(Path(build['private_mg5']).parent/'param_card_frozen.dat').read_text()
    cases=[(f'e{e:g}_kl{k:g}'.replace('.','p').replace('-','m'),e,k,173.,173.,False)
           for e in (250.001,300.,400.,800.) for k in (-1.,0.,1.,2.)]
    cases += [('repeat',400.,1.,173.,173.,False),('exchange',400.,1.,173.,173.,True),
       ('mt180_fixed_yukawa',400.,1.,180.,173.,False),('yt_zero',400.,1.,173.,0.,False),('yt_double',400.,1.,173.,346.,False)]
    rows=[]
    for label,e,k,mt,ymt,exchange in cases:
        p=fixed_point(e)
        if exchange:p[2],p[3]=p[3],p[2]
        card=modify_card(frozen,'loop',1,e/2);card=modify_card(card,'mass',6,mt);card=modify_card(card,'yukawa',6,ymt)
        (folder/'Cards/param_card.dat').write_text(card)
        (work/'PS.input').write_text('\n'.join(' '.join(f'{x:.17e}' for x in v) for v in p)+'\n')
        r=monitor.run_command([str(work/'check'),str(k)],work,'campaign_me_'+label,env=env)
        log=Path(r['log_path']).read_text();match=re.search(r'PHASE7A_RESULT\s+([^\n]+)',log)
        require(match is not None,'missing actual ME');fields=match[1].split();me=float(fields[0]);rc=int(fields[4])
        require(math.isfinite(me) and me>=0 and rc//100 in (2,3),'invalid actual campaign loop ME')
        rows.append({'label':label,'mHH_gev':e,'kappa_lambda':k,'MT_gev':mt,'YUKAWA6_gev':ymt,
           'momenta_E_px_py_pz_gev':p,'finite_squared_me':me,'return_code':rc,'precision':float(fields[3]),
           'alpha_s_fixed':.130,'mu_R_gev':e/2,'card_sha256':sha(folder/'Cards/param_card.dat'),'log_sha256':r['log_sha256']})
    # Restore the exact reviewed SM card for later reweighting builds.
    (folder/'Cards/param_card.dat').write_text(frozen)
    result={'status':'PASS_ACTUAL_FROZEN_PRODUCTION_PARAMETER_LOOP_GATES',
       'physical_events':0,'evaluations':rows,**check_numerical_results(rows),
       'source_couplings_sha256':{p.name:sha(p) for p in (folder/'Source/MODEL').glob('couplings*.f')},
       'executable_sha256':sha(work/'check'),'H_total_width_gev':build['model_table_values']['H_total_width_gev'],
       'Ward_scope':'separate_actual_normalized_gluon1_Ward_test_in_prerequisite_receipt'}
    save_json(Path(build['private_mg5']).parent/'numerical_validation.json',result)
    return result
