"""One immutable independent source reservation per authorized phase."""
from pathlib import Path
import json,shutil,re,sys,time,gzip
from .common import *
from .lhe import load_lhe,validate_production

def patch_request(text,events,seed):
    for key,value in [('nevents',events),('iseed',seed)]:
        text,n=re.subn(r'(?m)^([^\n=!]+)(\s*=\s*'+key+r'\b[^\n]*)$',lambda m:str(value)+m[2],text)
        require(n==1,'RUN_REQUEST_FIELD_NOT_UNIQUE')
    return text

def serial_configuration(process):
    p=Path(process)/'Cards/me5_configuration.txt'
    original=p.read_text()
    # The child MadEvent interface reloads its own options. MasterCmd's
    # --no_save options do not configure that child, and -m requests multicore.
    for key,value in [('nb_core','1'),('run_mode','0'),('automatic_html_opening','False'),
         ('auto_update','0'),('fortran_compiler','x86_64-conda-linux-gnu-gfortran'),
         ('cpp_compiler','x86_64-conda-linux-gnu-g++')]:
        original=re.sub(r'(?m)^\s*'+key+r'\s*=.*$','',original)
        original+='\n'+key+' = '+value+'\n'
    p.write_text(original)

def launch_text(name,process='process'):
    return '\n'.join(['set auto_update 0 --no_save','set automatic_html_opening False --no_save',
       'set nb_core 1 --no_save','set run_mode 0 --no_save',
       'launch '+process+' --name='+name,'shower=OFF','detector=OFF','analysis=OFF',
       'madspin=OFF','reweight=OFF','done','done','quit',''])

def generate_source(output,phase,seed,build,monitor,reservation):
    events=LIMITS[phase][0];out=Path(output)
    require(reservation['phase']==phase and reservation['events']==events and reservation['seed']==seed,
            'PHYSICAL_SOURCE_RESERVATION_MISMATCH')
    require(not out.exists(),'PRESERVE_EXISTING_SOURCE_NO_AUTOMATIC_REGENERATION')
    out.mkdir(parents=True);process=out/'process'
    shutil.copytree(build['process_template'],process,symlinks=True)
    serial_configuration(process)
    root=Path(build['private_mg5']);parent=root.parent
    cards=process/'Cards'
    (cards/'param_card.dat').write_bytes((parent/'param_card_frozen.dat').read_bytes())
    run=patch_request((parent/'run_card_frozen.dat').read_text(),events,seed)
    (cards/'run_card.dat').write_text(run)
    (out/'reviewed_run_card.dat').write_text(run)
    (out/'reviewed_param_card.dat').write_bytes((cards/'param_card.dat').read_bytes())
    name='hh_'+phase
    text=launch_text(name)
    (out/'launch.mg5').write_text(text)
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    env['TMPDIR']=str(out/'tmp');(out/'tmp').mkdir()
    protected=[cfg['mg5_path'],cfg['toolchain_prefix'],read_json(REPO/'.local/delphes_installation.json')['root_prefix']]
    save_json(out/'source_attempt.json',{'status':'AUTHORIZED_ONE_SOURCE_ATTEMPT_STARTED','reservation':reservation,
       'run_card_sha256':sha(cards/'run_card.dat'),'param_card_sha256':sha(cards/'param_card.dat'),
       'launch_driver_sha256':sha(out/'launch.mg5'),'adapter_sha256':sha(CAMPAIGN/'launch_adapter.py'),
       'native_MadLoop_params_sha256':sha(cards/'MadLoopParams.dat'),'physical_model':read_json(CAMPAIGN/'config/production.json')})
    result=monitor.run_command([str(Path(cfg['toolchain_prefix'])/'bin/python3'),'-B','-O',
       str(CAMPAIGN/'launch_adapter.py'),str(root),str(out/'launch.mg5'),*protected],out,'mg5_'+phase+'_independent_source',env=env)
    return collect_source(out,phase,seed,build,result)

def collect_source(out,phase,seed,build,result):
    out=Path(out);process=out/'process';name='hh_'+phase
    path=process/'Events'/name/'unweighted_events.lhe.gz'
    require(path.is_file(),'ACTUAL_SOURCE_LHE_MISSING')
    generated=load_lhe(path)
    # Preserve the real source before any downstream validation can fail.
    evidence={'status':'SOURCE_PRESENT_PENDING_INDEPENDENT_VALIDATION','phase':phase,'events_observed':len(generated['records']),
       'seed':seed,'path':str(path),'sha256':sha(path),'sigma_pb':generated['sigma_pb'],'error_pb':generated['error_pb'],
       'generator_execution':result,'source_attempt_sha256':sha(out/'source_attempt.json')}
    save_json(out/'source_present.json',evidence)
    validation=validate_source(out,phase,seed,build)
    evidence['status']='PASS_GENUINE_INDEPENDENT_FULL_MASS_SOURCE';evidence['validation']=validation
    evidence['requested_seed']=seed;evidence['effective_seed']=validation['effective_seed'];evidence['seed']=validation['effective_seed']
    save_json(out/'validated_source.json',evidence);return evidence

def resume_preintegration(out,phase,seed,build,monitor):
    """Only an explicitly certified zero-record compile failure can continue."""
    out=Path(out);proof=read_json(out/'preintegration_continuation.json')
    require(proof['status']=='VERIFIED_ZERO_SOURCE_RECORDS_PREINTEGRATION_COMPILE_FAILURE' and
        proof['source_records_observed']==proof['integration_result_files_observed']==0,'UNPROVED_PREINTEGRATION_CONTINUATION')
    require(not (out/'continuation_started.json').exists(),'PREINTEGRATION_CONTINUATION_ALREADY_ATTEMPTED')
    require(sha(out/'ME5_debug')==proof['debug_sha256'] and sha(out/'launch.mg5')==proof['original_launch_sha256'] and
        sha(out/'reviewed_run_card.dat')==proof['original_run_card_sha256'] and
        sha(out/'reviewed_param_card.dat')==proof['original_param_card_sha256'],'STALE_ZERO_RECORD_PROOF')
    for p in (out/'process').rglob('*'):
        require(not (p.is_file() and (p.name in ['events.lhe','unweighted_events.lhe','unweighted_events.lhe.gz','results.dat','ftn21'] or p.suffix=='.lhe')),
            'POSSIBLE_PREEXISTING_EVENTS_NO_AUTOMATIC_CONTINUATION')
    shutil.copyfile(out/'ME5_debug',out/'preintegration_failure_debug.txt')
    # MG clears iseed in the working card before compiling. A zero-record
    # continuation must restore the exact reviewed physics/run request first.
    (out/'process/Cards/run_card.dat').write_bytes((out/'reviewed_run_card.dat').read_bytes())
    (out/'process/Cards/param_card.dat').write_bytes((out/'reviewed_param_card.dat').read_bytes())
    serial_configuration(out/'process')
    (out/'continuation_launch.mg5').write_text(launch_text('hh_'+phase))
    save_json(out/'continuation_started.json',{'same_source_reservation':True,'additional_independent_source_budget':0,
       'prior_source_records':0,'proof_sha256':sha(out/'preintegration_continuation.json'),
       'driver_sha256':sha(out/'continuation_launch.mg5'),'native_child_config_sha256':sha(out/'process/Cards/me5_configuration.txt')})
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg);env['TMPDIR']=str(out/'tmp')
    protected=[cfg['mg5_path'],cfg['toolchain_prefix'],read_json(REPO/'.local/delphes_installation.json')['root_prefix']]
    result=monitor.run_command([str(Path(cfg['toolchain_prefix'])/'bin/python3'),'-B','-O',str(CAMPAIGN/'launch_adapter.py'),
        str(build['private_mg5']),str(out/'continuation_launch.mg5'),*protected],out,'mg5_'+phase+'_same_zero_record_continuation',env=env)
    return collect_source(out,phase,seed,build,result)

def validate_source(out,phase,seed,build):
    out=Path(out);present=read_json(out/'source_present.json');path=Path(present['path'])
    sys.path.insert(0,str(Path(build['private_mg5'])))
    require(path.resolve().is_relative_to(out.resolve()) and sha(path)==present['sha256'],'SOURCE_CHANGED_BEFORE_QA')
    source=load_lhe(path)
    observed=re.findall(r'^\s*([0-9]+)\s*=\s*iseed\b',source['header'].decode(),re.M)
    require(len(observed)==1,'AMBIGUOUS_ACTUAL_SOURCE_SEED');effective_seed=int(observed[0])
    seed_observation=None
    if effective_seed!=seed:
        # The first genuine pilot is preserved after a diagnosed pre-source
        # compile continuation. This is a bounded documented deviation, not a
        # generic seed override or a successful test of the old launch code.
        observation=out/'recovery_seed_observation.json'
        require(phase=='7b' and observation.exists(),'SOURCE_SEED_MISMATCH')
        seed_observation=read_json(observation)
        require(seed_observation['status']=='DOCUMENTED_RECOVERED_PILOT_SEED_DEVIATION' and
            seed_observation['source_sha256']==sha(path) and seed_observation['requested_seed']==seed and
            seed_observation['effective_seed']==effective_seed and
            seed_observation['reviewed_run_card_sha256']==sha(out/'reviewed_run_card.dat') and
            seed_observation['preintegration_proof_sha256']==sha(out/'preintegration_continuation.json'),'STALE_RECOVERY_SEED_OBSERVATION')
        print('DOCUMENTED_PILOT_SEED_DEVIATION requested='+str(seed)+' effective='+str(effective_seed)+'; no replacement generation',flush=True)
    validation=validate_production(source,LIMITS[phase][0],effective_seed)
    validation['requested_seed']=seed;validation['effective_seed']=effective_seed
    validation['seed_status']='EXACT_REQUEST_HONORED' if effective_seed==seed else 'DOCUMENTED_RECOVERED_PILOT_DEVIATION'
    validation['seed_deviation']=seed_observation
    header=source['header'].decode()
    for name in ('param','run'):
        tag='slha' if name=='param' else 'MGRunCard'
        matched=re.search(r'<'+tag+r'>\s*\n(.*?)</'+tag+r'>',header,re.S|re.I)
        require(matched is not None,'MISSING_EXACT_EMBEDDED_'+tag)
        actual=matched[1]
        reviewed=(out/('reviewed_'+name+'_card.dat')).read_text()
        if name=='param':
            # Native MG serialization may reorder card comments. Independent
            # official readers compare every physical block/value below.
            pass
        else:
            sys.path.insert(0,str(Path(build['private_mg5'])))
            from madgraph.various.banner import RunCardLO
            embedded=out/'embedded_run_card.dat'
            if not embedded.exists():embedded.write_text(actual)
            a,b=RunCardLO(str(embedded)),RunCardLO(str(out/'reviewed_run_card.dat'))
            keys=('nevents','lpp1','lpp2','ebeam1','ebeam2','pdlabel','fixed_ren_scale','fixed_fac_scale',
                  'dynamical_scale_choice','scalefact','nhel','event_norm','ickkw','cut_decays')
            require(all(a[k]==b[k] for k in keys),'ACTUAL_NATIVE_RUN_CARD_DIFFERS')
            require(a['iseed']==effective_seed and b['iseed']==seed,'ACTUAL_NATIVE_SEED_PROVENANCE_DIFFERS')
            validation['actual_run_parameters']={k:a[k] for k in keys}
            validation['actual_run_parameters']['iseed']=a['iseed']
        if name=='param':
            from models.check_param_card import ParamCard
            embedded=out/'embedded_param_card.dat'
            if not embedded.exists():embedded.write_text(actual)
            a,b=ParamCard(str(embedded)),ParamCard(str(out/'reviewed_param_card.dat'))
            physical={('mass',6):173.,('mass',25):125.,('mass',5):4.7,('yukawa',6):173.,('yukawa',5):4.7,
                ('decay',25):build['model_table_values']['H_total_width_gev']}
            for (block,code),expected in physical.items():
                value=float(a[block].get((code,)).value)
                tolerance=1e-12*max(1,abs(expected))
                if (block,code)==('decay',25):
                    from decimal import Decimal
                    token=re.search(r'(?im)^DECAY\s+25\s+(\S+)',actual)[1]
                    tolerance=max(tolerance,.5*10.**Decimal(token).as_tuple().exponent)
                    validation['H_width_native_card_serialization']={'initialized_model_width_gev':expected,
                        'actual_source_card_width_gev':value,'printed_half_unit_tolerance_gev':tolerance,
                        'relative_rounding_delta':(value-expected)/expected}
                require(abs(value-expected)<=tolerance,'ACTUAL_PARAM_'+block+'_'+str(code)+'_DIFFERS')
            require(float(a['sminputs'].get((3,)).value)==.129783,'NATIVE_PDF_ALPHA_S_MZ_DIFFERS')
            validation['actual_model_parameters']={block+'_'+str(code):float(a[block].get((code,)).value) for block,code in physical}
    validation['exact_cards_sha256']={n:sha(out/n) for n in ('reviewed_run_card.dat','reviewed_param_card.dat','embedded_run_card.dat','embedded_param_card.dat')}
    validation['MadLoop_params_sha256']=sha(out/'process/Cards/MadLoopParams.dat')
    validation['native_first_event_writer_sha256']=sha(out/'process/Source/rw_events.f')
    validation['native_first_header_format']="(i2,i5,e16.7e3,3e15.7)"
    save_json(out/'lhe_validation.json',validation)
    return validation
