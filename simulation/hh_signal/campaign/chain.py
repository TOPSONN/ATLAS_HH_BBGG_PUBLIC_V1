"""Sequential real shower, independent ReaderAscii, Delphes and ROOT stages."""
import gzip,json,shutil,csv,math
from pathlib import Path
from .common import *
from .decay import decay_source
from .lhe import load_lhe

def artifact(path):
    p=Path(path);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}

def audit_rows(folder,total,model):
    folder=Path(folder);rows=[json.loads(s) for s in (folder/'reco_events.jsonl').read_text().splitlines()]
    stages=[('00_input',lambda r:True),('01_photons',lambda r:r['cut_photons']),('02_jets',lambda r:r['cut_jets']),
       ('03_two_btags',lambda r:r['cut_two_btags']),('04_mgg_105_160',lambda r:r['cut_mgg'])]
    native={r['stage']:r for r in csv.DictReader((folder/'cutflow.csv').open())};result=[]
    factor=model['mixed_decay_factor'];full=len(rows)==total
    for stage,predicate in stages:
        selected=[r for r in rows if predicate(r)];weights=[r['source_contribution_pb'] for r in selected]
        n=len(selected);sw=math.fsum(weights);sw2=math.fsum(w*w for w in weights)
        require(n==int(native[stage]['raw_events']) and abs(sw-float(native[stage]['source_weight_sum_pb']))<1e-12 and
                abs(sw2-float(native[stage]['source_weight_sum_squared_pb2']))<1e-12,'INDEPENDENT_SIGNAL_CUTFLOW_MISMATCH')
        # Full source N includes all original events, selection zeros included.
        var=total/(total-1)*max(0.,sw2-sw*sw/total)
        z=1.959963984540054;p=n/total;den=1+z*z/total
        center=(p+z*z/(2*total))/den;half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
        result.append({'stage':stage,'raw_events':n,'original_source_events':total,'acceptance':p,
           'acceptance_wilson95':[max(0,center-half),min(1,center+half)] if full else None,
           'zero_count_one_sided95_upper':1-math.pow(.05,1/total) if n==0 and full else None,
           'RAW_PRODUCTION_WEIGHT_sum_pb':sw,'RAW_PRODUCTION_WEIGHT_sumw2_pb2':sw2,
           'MODEL_BR_ONLY_WEIGHT_sum_pb':factor*sw,'MODEL_BR_ONLY_WEIGHT_sumw2_pb2':factor*factor*sw2,
           'source_MC_sampling_variance_pb2':var if full else None,'MODEL_BR_ONLY_source_MC_standard_error_pb':factor*math.sqrt(var) if full else None,
           'REFERENCE_BR_WEIGHT':None,'ADOPTED_PHYSICAL_WEIGHT':None,
           'scope':'single_real_detector_tag_outcome; detector_tag_variance_not_independently_measured' if full else 'PREFIX_DIAGNOSTIC_ONLY_NOT_AN_INDEPENDENT_FULL_N_ACCEPTANCE'})
    diagnostics={'events':len(rows),'truth_H_gamma_geometric_matches':{str(k):sum(r['H_origin_reco_matches']==k for r in rows) for k in (0,1,2)},
       'truth_b_jet_geometric_matches':{str(k):sum(r['H_bottom_geometric_jet_matches']==k for r in rows) for k in (0,1,2)},
       'undefined_mass_counts':{k:sum(r[k] is None for r in rows) for k in ('m_gamma_gamma','m_bb','m_bb_gamma_gamma','m_jj')},
       'matching_scope':'geometric diagnostic only, not calibrated detector efficiency'}
    receipt={'status':'PASS_INDEPENDENT_ACTUAL_SIGNAL_CUTFLOW_WEIGHT_ALGEBRA','cutflow':result,'diagnostics':diagnostics,
       'model_BR_factor':factor,'BR_factor_applications':1,'BR_scope':'MODEL_BR_ONLY','source_denominator':total}
    save_json(folder/'independent_cutflow.json',receipt);return receipt

def run_chain(phase_output,source,native,monitor,phase,seed,assignment_seed,detector_seed):
    out=Path(phase_output);total=source['events_observed'];dc,pc,env=native_environment()
    decay=decay_source(source['path'],out/'decay',assignment_seed,native['model_values'])
    stages={};binaries=native['binaries'];full_lhe=out/'decay/decayed_source.lhe'
    for count in ((10,100) if total==100 else (10,100,1000)):
        name='prefix'+str(count) if count<total else 'full'+str(count)
        stage=out/'stages'/name;stage.mkdir(parents=True,exist_ok=False)
        authorization={'task':ACK,'phase':phase,'events':count,'original_count':total,'source_sha256':source['sha256'],
           'input_sha256':sha(full_lhe),'index_sha256':sha(out/'decay/decayed_source_index.dat'),'roles_sha256':sha(out/'decay/roles.dat'),
           'executable_sha256':binaries['shower_signal']['sha256'],'pythia_seed':seed,'detector_seed':detector_seed,
           'source_event_budget':'already_reserved_no_additional_independent_events','normalization':'MODEL_BR_ONLY'}
        save_json(stage/'authorization.json',authorization)
        monitor.run_command([binaries['shower_signal']['path'],str(full_lhe),str(out/'decay/decayed_source_index.dat'),
            str(out/'decay/roles.dat'),pc['xml_path'],str(REPO/'simulation/pythia8/config/baseline_shower.cmnd'),
            str(stage/'shower'),str(count),str(total),str(seed),source['sha256'],str(stage/'authorization.json')],stage,
            phase+'_shower_'+name,env=env)
        # Existing generic validator separately checks graph endpoints, stable
        # mass shells, full proton four-momentum, PDG/status and finite weights.
        monitor.run_command([pc['validator_path'],'--input',str(stage/'shower/shower.hepmc3'),'--xml',pc['xml_path'],
            '--events',str(count),'--source-sha256',source['sha256'],'--sample-id','S01_PHASE7B100' if total==100 else 'S01_PHASE7C1000',
            '--seed',str(seed),'--report',str(stage/'generic_validation.json')],stage,phase+'_generic_reader_'+name,env=env)
        monitor.run_command([binaries['validate_signal_hepmc']['path'],str(stage/'shower/shower.hepmc3'),
            str(out/'decay/production_source_index.dat'),str(stage/'readback'),str(count),str(total),source['sha256'],
            str(stage/'authorization.json')],stage,phase+'_signal_reader_'+name,env=env)
        native_reader=read_json(stage/'readback/native_validation.json')
        require(native_reader['validated_events']==count,'ACTUAL_SIGNAL_READER_COUNT')
        detector=stage/'delphes';detector.mkdir();card=detector/'detector_card.tcl'
        frozen=REPO/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl';raw=frozen.read_bytes()
        require(sha(frozen)=='cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47','HISTORICAL_DETECTOR_CARD_CHANGED')
        require(raw.count(b'set RandomSeed 610301')==1,'wrong native card seed marker')
        card.write_bytes(raw.replace(b'set RandomSeed 610301',('set RandomSeed '+str(detector_seed)).encode()))
        monitor.run_command([dc['delphes_binary'],str(card),'detector.root',str(stage/'shower/shower.hepmc3')],detector,
            phase+'_delphes_'+name,env=env)
        monitor.run_command([binaries['analyze_signal_root']['path'],str(detector/'detector.root'),
           str(stage/'readback/input_event_index.dat'),str(stage/'readback/signal_truth.dat'),str(card),str(stage/'root_validation'),
           str(count),str(total),str(stage/'authorization.json')],stage,phase+'_native_root_'+name,env=env)
        root=read_json(stage/'root_validation/native_validation.json');require(root['validated']==root['entries']==count,'ACTUAL_NATIVE_SIGNAL_ROOT_COUNT')
        independent=audit_rows(stage/'root_validation',total,native['model_values'])
        receipt={'status':'PASS_ACTUAL_SIGNAL_PREFIX_CHAIN' if count<total else 'PASS_ACTUAL_FULL_SIGNAL_CHAIN',
           'source_events':total,'validated_events':count,'stage':name,'new_independent_events':0,
           'source_sha256':source['sha256'],'shower':read_json(stage/'shower/run_summary.json'),
           'generic_ReaderAscii':read_json(stage/'generic_validation.json'),'signal_ReaderAscii':native_reader,
           'native_ROOT':root,'independent_cutflow':independent,
           'artifacts':{k:artifact(stage/p) for k,p in {'HepMC':'shower/shower.hepmc3','ROOT':'delphes/detector.root',
              'reco':'root_validation/reco_events.jsonl','input_index':'readback/input_event_index.dat',
              'truth':'readback/signal_truth.dat','ancestry':'readback/hepmc_ancestry.jsonl'}.items()}}
        save_json(stage/'chain_receipt.json',receipt);stages[name]=receipt
        save_json(out/'completed_stages.json',stages)
    return {'status':'PASS_REAL_HH_SOURCE_DECAY_SHOWER_HEPMC_DELPHES_ROOT_MODEL_SCOPE','phase':phase,
       'source':source,'decay':decay,'stages':stages,'full_count':total,'full_stage':'full'+str(total),
       'model_BR_only':True,'new_independent_source_events':total}
