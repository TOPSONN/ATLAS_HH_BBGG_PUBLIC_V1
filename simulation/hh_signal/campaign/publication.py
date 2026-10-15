"""Copy selected verified reference assets; this module never pushes Git."""
import shutil,gzip
from .common import *
from .chain import artifact

REF=REPO/'reference_samples/hh_signal/S01_ggf_hh_sm'
EVIDENCE=PACKAGE/'evidence/campaign'

def copy_bytes(source,destination):
    destination=Path(destination);require(not destination.exists(),'REFERENCE_ALREADY_EXISTS')
    destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)

def pack_phase(run,phase):
    run=Path(run);p=read_json(run/'phase_receipt.json')
    require(p['status']=='PASS_REAL_HH_SOURCE_DECAY_SHOWER_HEPMC_DELPHES_ROOT_MODEL_SCOPE','NO_REFERENCE_FROM_UNVALIDATED_CHAIN')
    n=p['full_count'];require(n==LIMITS[phase][0],'WRONG_REFERENCE_SOURCE_COUNT')
    folder=REF/('phase7b_100' if phase=='7b' else 'phase7c_1000');require(not folder.exists(),'REFERENCE_ALREADY_EXISTS')
    full=p['stages']['full'+str(n)];selected=p['stages']['full100' if n==100 else 'prefix100']
    require(full['validated_events']==n and selected['validated_events']==100,'MISSING_GENUINE_NATIVE_REFERENCE_PROOF')
    src=run/'source';stage=run/'stages'/selected['stage'];folder.mkdir(parents=True)
    copy_bytes(p['source']['path'],folder/('reference_'+str(n)+'.lhe.gz'))
    for original,name in [('process/Cards/proc_card_mg5.dat','process_card.mg5'),('embedded_run_card.dat','run_card.dat'),
       ('embedded_param_card.dat','param_card.dat'),('reviewed_run_card.dat','reviewed_run_card.dat'),
       ('reviewed_param_card.dat','reviewed_param_card.dat'),('process/Cards/MadLoopParams.dat','MadLoopParams.dat')]:
        copy_bytes(src/original,folder/'cards'/name)
    copy_bytes(stage/'delphes/detector_card.tcl',folder/'cards/detector_card.tcl')
    copy_bytes(stage/'shower/effective_settings.cmnd',folder/'cards/effective_shower.cmnd')
    hepmc=stage/'shower/shower.hepmc3'
    (folder/'reference_100.hepmc3.gz').write_bytes(gzip.compress(hepmc.read_bytes(),mtime=0))
    copy_bytes(stage/'delphes/detector.root',folder/'detector_100.root')
    for original,name in [('root_validation/reco_events.jsonl','reco_events_100.jsonl'),('readback/hepmc_ancestry.jsonl','hepmc_ancestry_100.jsonl'),
        ('readback/input_event_index.dat','input_event_index_100.dat'),('readback/signal_truth.dat','signal_truth_100.dat'),
        ('shower/attempt_ledger.jsonl','shower_attempt_ledger_100.jsonl')]:copy_bytes(stage/original,folder/name)
    copy_bytes(run/'decay/decay_ledger.jsonl',folder/'decay_ledger.jsonl')
    save_json(folder/'full_source_and_chain_validation.json',project_public(p))
    save_json(folder/'validation.json',{'status':'SELECTED_GENUINE_REFERENCE_FROM_ACTUAL_VALIDATED_CHAIN',
        'source_events':n,'selected_HepMC_events':100,'selected_ROOT_entries':100,'original_weight_denominator':n,
        'reference_origin':selected['status'],'source_LHE_sha256':p['source']['sha256'],
        'source_native_HepMC_sha256':sha(hepmc),'selected_native_ROOT_sha256':sha(stage/'delphes/detector.root'),
        'source_HepMC_and_ROOT_are_same_exact_prefix':True,'additional_independent_events':0,
        'prefix_statistical_scope':'SUBSET_NOT_EXTRA_INDEPENDENT_STATISTICS','full1000_shower_ROOT_location':'LOCAL_ONLY' if n==1000 else 'SELECTED_FULL100',
        'normalization_scope':'MODEL_BR_ONLY','source_included_decay_factors':[],'model_BR_factor':p['decay']['missing_mixed_decay_factor'],
        'factor_applications':1,'adopted_physical_BR':None})
    entries=[{'path':p.relative_to(folder).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(folder.rglob('*')) if p.is_file()]
    save_json(folder/'manifest.json',{'schema_version':1,'files':entries,'source_events':n,'HepMC_events':100,'ROOT_entries':100})
    return {'phase':phase,'files':len(entries)+1,'source_events':n,'HepMC_events':100,'ROOT_entries':100,
        'manifest_sha256':sha(folder/'manifest.json')}

def pack_reweight(run):
    run=Path(run);result=read_json(run/'reweight_validation.json');folder=REF/'phase7d_klambda'
    require(result['source_events']==1000 and result['new_independent_events']==0,'REWEIGHT_SOURCE_SCOPE')
    require(not folder.exists(),'REFERENCE_ALREADY_EXISTS');folder.mkdir(parents=True)
    copy_bytes(run/'event_reweights.csv',folder/'event_reweights.csv')
    copy_bytes(run/'comparison/weighted_histograms.root',folder/'weighted_histograms.root')
    copy_bytes(CAMPAIGN/'config/kappa_scan.json',folder/'kappa_scan.json')
    save_json(folder/'validation.json',project_public(result))
    entries=[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(folder.iterdir())]
    save_json(folder/'manifest.json',{'schema_version':1,'files':entries,'source_events':1000,'new_independent_events':0})
    return {'phase':'7d','manifest_sha256':sha(folder/'manifest.json'),'events_reweighted':1000,'new_independent_events':0}
