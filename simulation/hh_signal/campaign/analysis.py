"""Read-only independent ROOT regression and per-process numerical comparison."""
import csv,shlex,subprocess,gzip,re
from .common import *
from .statistics import histogram,precision_plan,covariance
from .lhe import load_lhe,mass2
from simulation.rare_backgrounds.scripts.conditional_tags import tag_probability,probability_at_least_two

BINS={
 'mHH_truth':[250,300,350,400,450,500,600,700,800,1000,1500,2500],
 'm_bb':[0,25,50,75,100,125,150,175,200,250,350,500],
 'm_gamma_gamma':[0,80,100,105,110,115,120,122.5,125,127.5,130,135,140,150,160,180,250],
 'm_bb_gamma_gamma':[0,200,250,300,350,400,450,500,600,750,1000,1500,2500],
 'pT_HH_truth':[0,1e-6,10,25,50,100,200,400,800],
 'pT_H_truth_lead':[0,25,50,75,100,150,200,300,450,650,1000],
 'pT_H_truth_sublead':[0,25,50,75,100,150,200,300,450,650,1000],
 'pT_gamma_gamma':[0,25,50,75,100,150,200,300,450,650,1000],
 'pT_bb':[0,25,50,75,100,150,200,300,450,650,1000],
 'DeltaR_bb':[0,.4,.8,1.2,1.6,2.,2.4,2.8,3.2,4.,5.,7.],
 'DeltaR_gamma_gamma':[0,.4,.8,1.2,1.6,2.,2.4,2.8,3.2,4.,5.,7.],
 'N_jets':[-.5,.5,1.5,2.5,3.5,4.5,5.5,6.5,8.5,12.5],
 'N_btags':[-.5,.5,1.5,2.5,3.5,4.5,6.5]}
STAGES=[('00_input',None),('01_photons','cut_photons'),('02_jets','cut_jets'),('03_two_btags','cut_two_btags'),('04_mgg_105_160','cut_mgg')]

def jsonl(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def dump_csv(path,rows):
    with Path(path).open('x',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def integration(path):
    p=Path(path);data=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
    body=re.search(rb'<init>\s*\n(.*?)</init>',data,re.S)[1]
    lines=[s.split(b'#')[0].strip() for s in body.splitlines() if s.split(b'#')[0].strip()]
    sigma,error=map(float,lines[1].split()[:2]);require(sigma>0 and error>=0,'INTEGRATION_INIT_ERROR')
    return {'source_integrated_cross_section_pb':sigma,'source_integration_error_pb':error,'relative_error':error/sigma}

def compile_extractor(out,monitor):
    dc,pc,env=native_environment();root=Path(dc['root_prefix']);source=CAMPAIGN/'src/extract_root_features.cxx'
    flags=shlex.split(subprocess.check_output([str(root/'bin/root-config'),'--cflags','--libs'],env=env,text=True))
    exe=out/'extract_root_features'
    monitor.run_command([str(root/'bin/x86_64-conda-linux-gnu-c++'),'-std=c++20','-O2',
        '-I'+str(REPO/'simulation/delphes/include'),'-I'+str(REPO/'simulation/pythia8/include'),
        '-I'+str(Path(dc['delphes_prefix'])/'include'),str(source),'-L'+str(Path(dc['delphes_prefix'])/'lib'),'-lDelphes',
        *flags,'-o',str(exe)],out,'compile_independent_feature_extractor',env=env)
    return exe,env

def background_weight_factor(ledger):
    if ledger['scope']=='NO_HIGGS_BR':
        require(ledger['status']=='PASS_RAW_WEIGHT_CLOSURE' and ledger['factor'] is None and
            ledger['factor_applications']==0,'INVALID_NO_HIGGS_RAW_WEIGHT_CONVENTION')
        return 1.  # Identity of raw-source weights, not a physical BR=1.
    require(ledger['scope']=='MODEL_BR_ONLY' and ledger['status']=='PASS_MODEL_BR_WEIGHT_CLOSURE' and
        ledger['factor'] is not None and ledger['factor_applications']==1,'UNKNOWN_OR_DOUBLE_BACKGROUND_BR_FACTOR')
    factor=float(ledger['factor']);require(math.isfinite(factor) and 0<factor<=1,'INVALID_MODEL_BR_FACTOR')
    return factor

def backgrounds():
    result=[]
    for code,alias,reference in [('B01','bbgg','pp_bbgg_sm_lo_13tev'),('B02','ccgg','pp_ccgg_sm_lo_13tev'),('B03','jjgg','pp_jjgg_light_sm_lo_13tev')]:
        folder=Path.home()/'simulations/delphes_runs'/('stage_c_'+alias+'_1000');manifest=read_json(folder/'run_manifest.json')
        for name,d in manifest['files'].items():require(sha(folder/name)==d['sha256'],'EXISTING_BACKGROUND_FILE_CHANGED_'+code+'_'+name)
        source=REPO/'reference_samples/mg5'/reference/'reference_1000.lhe.gz'
        require(sha(source)==manifest['source_mg5_sha256'],'EXISTING_BACKGROUND_SOURCE_CHANGED')
        result.append({'code':code,'root':folder/'detector.root','index':folder/'input_event_index.dat',
           'reco':folder/'reco_events.jsonl','source':source,'factor':1.,'scope':'RAW_SOURCE_EXPLORATORY_UNCALIBRATED_OVERLAP_UNKNOWN'})
    for code,alias,run,ref in [('B04','zh','zh_1k_detector_v3','B04_ZH'),('B05','tth','tth_1k','B05_TTH'),('B06','bbgj','bbgj_1k','B06_BBGJ')]:
        folder=Path.home()/'simulations/phase6g_runs'/run;manifest=read_json(folder/'run_manifest.json')
        bindings={}
        def verify_declared(item):
            if isinstance(item,dict):
                if isinstance(item.get('path'),str) and isinstance(item.get('sha256'),str) and Path(item['path']).is_absolute():
                    path=Path(item['path']);require(path.is_file() and sha(path)==item['sha256'],'EXISTING_DECLARED_BACKGROUND_ARTIFACT_CHANGED')
                    bindings[str(path)]=item['sha256']
                for value in item.values():verify_declared(value)
            elif isinstance(item,list):
                for value in item:verify_declared(value)
        verify_declared(manifest)
        root=folder/'delphes/full1000/detector.root';receipt=read_json(folder/'delphes/full1000/delphes_execution.json')
        require(sha(root)==receipt['root_sha256'],'EXISTING_BACKGROUND_ROOT_CHANGED')
        index=Path(receipt['inputs']['input_index_path']);require(sha(index)==receipt['input_index_sha256'],'EXISTING_BACKGROUND_INDEX_CHANGED')
        reco=Path(receipt['reco_events_path']);require(sha(reco)==receipt['derived_files_sha256']['reco_events.jsonl'],'EXISTING_RECO_CHANGED')
        source=Path(manifest['stages']['MG5']['artifacts']['lhe_gz']['path'])
        require(sha(source)==manifest['stages']['MG5']['artifacts']['lhe_gz']['sha256']==sha(REPO/'reference_samples/new_backgrounds'/ref/'mg5/reference_1000.lhe.gz'),'EXISTING_BACKGROUND_SOURCE_CHANGED')
        ledger=manifest['weight_and_BR_ledger'];factor=background_weight_factor(ledger)
        result.append({'code':code,'root':root,'index':index,'reco':reco,'source':source,'factor':factor,
            'BR_ledger_scope':ledger['scope'],'BR_factor_applications':ledger['factor_applications'],
            'declared_artifact_bindings_reverified':len(bindings),
            'scope':'MODEL_BR_ONLY_EXPLORATORY_TTH_SPIN_UNVALIDATED' if alias=='tth' else
                'MODEL_BR_ONLY_EXPLORATORY' if alias=='zh' else 'ONE_BORN_PHOTON_NO_CALIBRATED_FAKE_MODEL'})
    return result

def conditional_tag(rows,weights):
    expected=[];variances=[]
    for r,w in zip(rows,weights):
        ps=[tag_probability(int(j['flavor']),j['pt']) for j in r['eligible_jets']]
        p=float(probability_at_least_two(ps)) if r['cut_jets'] and r['m_gamma_gamma'] is not None and 105<=r['m_gamma_gamma']<=160 else 0.
        expected.append(w*p);variances.append(w*w*p*(1-p))
    return {'conditional_expected_final_weight_pb':math.fsum(expected),'conditional_tag_sampling_variance_pb2':math.fsum(variances),
       'conditional_mean_source_sampling_variance_pb2':covariance(expected,expected),
       'assumptions':'verified pinned independent per-jet bit0 Bernoulli, fixed reconstructed jets/photons; persisted Float_t PT approximation',
       'full_detector_sampling_variance':None,'official_ATLAS_systematic':None,
       'combination_warning':'do not add tag variance to a sampling estimate from observed tagged outcomes; those outcomes already fluctuate',
       'mass_distribution_scope':'actual tagged-pair realization only; conditional counts do not substitute an expected m_bb histogram'}

def analyze(out,phase,native,reweights,monitor):
    out=Path(out);out.mkdir();exe,env=compile_extractor(out,monitor)
    source=load_lhe(phase['source']['path']);factor=native['model_values']['mixed_decay_factor'];full=phase['stages']['full1000']
    signal={'code':'S01','root':Path(full['artifacts']['ROOT']['path']),'index':Path(full['artifacts']['input_index']['path']),
       'reco':Path(full['artifacts']['reco']['path']),'source':Path(phase['source']['path']),'factor':factor,'scope':'MODEL_BR_ONLY_LO_FULL_MASS_UNCALIBRATED'}
    streams=[signal,*backgrounds()];features={};preserved=[];hists=[];cuts=[];tag={};plans={}
    lookup={(r['source_event_index'],r['kappa_lambda']):r for r in reweights}
    for stream in streams:
        code=stream['code'];path=out/(code+'_features.jsonl');old=jsonl(stream['reco'])
        root_before=sha(stream['root']);source_before=sha(stream['source']);require(len(old)==1000,'EXISTING_RECO_COUNT')
        monitor.run_command([str(exe),str(stream['root']),str(stream['index']),str(path),'1000'],out,'independent_root_'+code.lower(),env=env)
        rows=jsonl(path);require(len(rows)==1000,'INDEPENDENT_ROOT_FEATURE_COUNT');integ=integration(stream['source'])
        for a,b in zip(rows,old):
            require(a['source_event_index']==b['source_event_index'] and a['source_event_sha256']==b.get('source_event_sha256',b.get('source_event_hash')),'RECO_SOURCE_IDENTITY_CHANGED')
            for key in ('cut_photons','cut_jets','cut_two_btags','cut_mgg'):require(a[key]==b[key],'INDEPENDENT_SELECTION_REGRESSION')
            require(abs(a['source_contribution_pb']-b['source_contribution_pb'])<1e-12,'INDEPENDENT_SOURCE_WEIGHT_REGRESSION')
        if code=='S01':
            for r,s in zip(rows,source['records']):
                a,b=s['particles'][2]['p4'],s['particles'][3]['p4'];hh=[a[j]+b[j] for j in range(4)]
                r['mHH_truth']=math.sqrt(mass2(hh));r['pT_HH_truth']=math.hypot(*hh[:2])
                pts=sorted([math.hypot(*p[:2]) for p in (a,b)],reverse=True)
                r['pT_H_truth_lead'],r['pT_H_truth_sublead']=pts
        require(sha(stream['root'])==root_before and sha(stream['source'])==source_before,'INPUT_MUTATED_BY_READ_ONLY_ANALYSIS')
        preserved.append({'process':code,'events_reread':1000,'ROOT_sha256':root_before,'source_LHE_sha256':source_before,
           'input_index_sha256':sha(stream['index']),'retained_reco_sha256':sha(stream['reco']),'new_features_sha256':sha(path),
           'native_all_named_weight_vectors_verified':True,'input_source_unchanged':True,'integration':integ,
           'weight_transfer_multiplier':stream['factor'],'BR_ledger_scope':stream.get('BR_ledger_scope',stream['scope']),
           'BR_factor_applications':stream.get('BR_factor_applications',1 if code=='S01' else 0),
           'declared_artifact_bindings_reverified':stream.get('declared_artifact_bindings_reverified')})
        features[code]=rows;plans[code]=precision_plan(sum(r['cut_mgg'] for r in rows),1000)
        variants=[(k,[lookup[(i,k)]['source_contribution_pb']*factor for i in range(1,1001)],'MODEL_BR_ONLY_REWEIGHTED_INCONCLUSIVE_ABSOLUTE_RATE') for k in (-1,0,1,2,2.5,5)] if code=='S01' else [(None,[r['source_contribution_pb']*stream['factor'] for r in rows],stream['scope'])]
        for k,weights,scope in variants:
            name=code+('_kl'+str(k) if k is not None else '')
            tag[name]=conditional_tag(rows,weights)
            for stage,key in STAGES:
                accepted=[True if key is None else r[key] for r in rows];a=[w if yes else 0. for w,yes in zip(weights,accepted)];s=math.fsum(a);q=math.fsum(w*w for w in a)
                cuts.append({'process':code,'kappa_lambda':k,'stage':stage,'observed_events':sum(accepted),'original_N':1000,
                   'weight_scope':scope,'sum_weight_pb':s,'sumw2_pb2':q,
                   'sum_abs_w_pb':math.fsum(abs(w) for w,yes in zip(weights,accepted) if yes),
                   'N_positive':sum(w>0 and yes for w,yes in zip(weights,accepted)),
                   'N_negative':sum(w<0 and yes for w,yes in zip(weights,accepted)),
                   'N_zero':sum(w==0 and yes for w,yes in zip(weights,accepted)),
                   'source_sampling_variance_pb2':covariance(a,a),
                   'correlated_SM_source_normalization_integration_error_pb':abs(s)*integ['relative_error'],
                   'target_benchmark_independent_integration_error_pb':None if code=='S01' and k!=1 else abs(s)*integ['relative_error'],
                   'COMMON_LUMINOSITY_EXPLORATORY_fb_inverse':100,'expected_weighted_count_at_100fb_inverse':s*100*1000,
                   'physical_background_combination':'BLOCKED_OVERLAP_AND_CALIBRATION'})
            for stage,key in [('00_input',None),('04_mgg_105_160','cut_mgg')]:
                selectedweights=[w if key is None or r[key] else 0. for r,w in zip(rows,weights)]
                for observable,edges in BINS.items():
                    values=[r.get(observable) for r in rows]
                    active=[key is None or r[key] for r in rows]
                    for row in histogram(values,selectedweights,edges,1000,active):
                        row.update(process=code,kappa_lambda=k,observable=observable,stage=stage,weight_scope=scope,
                           COMMON_LUMINOSITY_EXPLORATORY_fb_inverse=100,
                           expected_weighted_count_at_100fb_inverse=row['sumw']*100*1000,
                           observable_scope='NOT_APPLICABLE_BACKGROUND_TRUTH_HH' if code!='S01' and 'truth' in observable else 'DEFINED_OR_MISSING_PAIR')
                        hists.append(row)
    # Separate B100 readback closes every named ROOT weight value as well;
    # its events are not pooled into the C1000 comparison/statistics.
    registry=read_json(REPO/'.local/phase7_campaign/campaign_registry.json')
    bphase=read_json(Path(registry['phases']['7b']['output'])/'phase_receipt.json');bfull=bphase['stages']['full100']
    bfeatures=out/'B100_independent_named_weights.jsonl'
    monitor.run_command([str(exe),bfull['artifacts']['ROOT']['path'],bfull['artifacts']['input_index']['path'],str(bfeatures),'100'],
        out,'independent_root_b100_all_named_weights',env=env)
    brow=jsonl(bfeatures);bprevious=jsonl(bfull['artifacts']['reco']['path']);require(len(brow)==len(bprevious)==100,'B100_INDEPENDENT_COUNT')
    for a,b in zip(brow,bprevious):
        require(a['source_event_index']==b['source_event_index'] and a['source_event_sha256']==b['source_event_sha256'] and
            all(a[k]==b[k] for k in ['cut_photons','cut_jets','cut_two_btags','cut_mgg']),'B100_INDEPENDENT_WEIGHT_SELECTION_REGRESSION')
    dump_csv(out/'weighted_histograms.csv',hists);dump_csv(out/'signal_background_cutflow.csv',cuts)
    dc,pc,env=native_environment()
    monitor.run_command([str(Path(dc['root_prefix'])/'bin/python'),'-B',str(CAMPAIGN/'write_root_histograms.py'),
        str(out/'weighted_histograms.csv'),'weighted_histograms.root'],out,'native_numerical_root_histograms',env=env)
    signal_covariance=[]
    for stage,key in STAGES:
        wk={k:[lookup[(i,k)]['MODEL_BR_ONLY_weight_pb'] if key is None or features['S01'][i-1][key] else 0.
            for i in range(1,1001)] for k in (-1,0,1,2,2.5,5)}
        for k,a in wk.items():
            for l,b in wk.items():
                v=covariance(a,b);va=covariance(a,a);vb=covariance(b,b)
                signal_covariance.append({'stage':stage,'kappa_a':k,'kappa_b':l,'common_source_sampling_covariance_pb2':v,
                   'correlation':v/math.sqrt(va*vb) if va>0 and vb>0 else None})
    result={'status':'PASS_SEPARATE_PROCESS_EXPLORATORY_COMPARISON_WITH_LIMITS','inputs':preserved,
       'original_background_events_preserved':6000,'signal_events_reread':1000,'independent_B100_named_weight_entries':100,
       'independent_ROOT_records_reread':7100,'B100_independent_readback_sha256':sha(bfeatures),'new_independent_events':0,
       'fixed_common_bins':BINS,'histogram_sha256':sha(out/'weighted_histograms.csv'),'native_numerical_ROOT_sha256':sha(out/'weighted_histograms.root'),
       'cutflow_sha256':sha(out/'signal_background_cutflow.csv'),
       'conditional_tag_statistics':tag,'independent_event_precision_plans':plans,'signal_common_event_selected_covariance':signal_covariance,
       'shape_scope':'UNIT_AREA_SHAPE_ONLY guarded zero/cancellation; flows included; observed tagged pairs',
       'luminosity_scope':'COMMON_LUMINOSITY_EXPLORATORY 100 fb^-1; pb * fb^-1 *1000',
       'combined_physical_background':'BLOCKED_OVERLAP_AND_CALIBRATION','B01_B02_B03_ME_PS_overlap':'UNKNOWN',
       'B04_B05_Higgs_BR':'MODEL_BR_ONLY','ttH_spin':'UNVALIDATED','B06_photon_fake':'NO_CALIBRATED_FAKE_MODEL',
       'official_ATLAS_systematics':None,'discovery_or_exclusion':None,'PDF_scale_variation':None,'BR_uncertainty':None,
       'full_detector_sampling_variance':None,'total_uncertainty_band':None}
    result['sampling_interpretation']='event-level sample covariance includes the realized hard-point, decay, shower, detector and tag randomness; it is not an isolated generator-only contribution'
    result['isolated_generator_only_acceptance_variance']=None
    result['conditional_tag_variance_interpretation']='conditional on reconstructed jets/photons under the pinned independent Bernoulli model; not additive to the already fluctuating observed-outcome covariance'
    save_json(out/'analysis_validation.json',result)
    return result
