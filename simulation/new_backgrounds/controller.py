#!/usr/bin/env python3
"""Independent bounded self-service controller for three physical LO backgrounds."""
from __future__ import annotations
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import argparse
import gzip
import json
import os
import shutil
import sys
import time
import uuid

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
sys.path.insert(0,str(REPO/'simulation/zh_pilot/scripts'))
sys.path.insert(0,str(REPO/'simulation/new_backgrounds/scripts'))
from simulation.new_backgrounds.common import (ACK,BASE,AUTHORIZATION_SOURCE_SHA256,PROCESSES,
    Monitor,availability,bridge_identity,request,require,reserve_campaign,save_json,sha_file,strict_json,tree_bytes,CAMPAIGN)
from prepare_pilot import safe_output,protected_paths,bound_bundle
from check_environment import verify_environment


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--process',required=True,choices=tuple(PROCESSES))
    p.add_argument('--events',required=True,type=int)
    p.add_argument('--seed',required=True,type=int)
    p.add_argument('--energy',required=True,type=float)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--max-hours',type=float,default=4)
    p.add_argument('--max-disk-gb',type=float,default=10)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--resume-source',type=Path,
                   help='Reuse a preserved source stopped only by the verified MG5 implicit-default comparison bug; never invoke MG5')
    p.add_argument('--resume-chain',type=Path,
                   help='Continue the one pinned B04 reader-context stop; reuse its genuine prefix10 without calling the shower again')
    p.add_argument('--resume-detector',type=Path,
                   help='Continue the pinned signed-jet validator stop; reuse all showers and detector10/100, run only remaining detector1000')
    return p


def preserved_source(run,requested,installed,*,allow_reserved_continuation=False):
    """Narrow, read-only recovery; no retries of a physically failed shower."""
    candidate=Path(run).expanduser()
    require(candidate.is_dir() and not candidate.is_symlink(),'missing/unsafe preserved source directory')
    run=candidate.resolve()
    require(not Path(requested['output']).is_relative_to(run) and not run.is_relative_to(Path(requested['output'])),
            'recovery output must be separate from the preserved source')
    manifest_path=run/'run_manifest.json';plan_path=run/'execution_plan.json'
    manifest=strict_json(manifest_path);plan=strict_json(plan_path)
    require(manifest['status']=='PARTIAL_PHYSICAL_CHAIN' and
            manifest.get('failure')=='Actual complete run card differs from reviewed request',
            'only the diagnosed implicit-default comparison stop permits source reuse')
    require(manifest['MG5_events_generated']==1000 and
            all(manifest.get(k)==0 for k in ('Pythia_events_attempted','Pythia_events_written','HepMC_validated_events','Delphes_ROOT_entries')),
            'source reuse requires1000 preserved source events and no downstream physical attempt')
    downstream={'shower_background_'+s for s in ('prefix10','prefix100','full1000')}
    downstream|={'background_reader_'+s for s in ('prefix10','prefix100','full1000')}
    require(not any(row['stage'] in downstream or row['stage'].startswith('delphes_')
                    for row in manifest['stages_attempted']), 'downstream stages were already attempted')
    original=manifest['request']
    require(all(original[k]==requested[k] for k in ('process','events','seed','energy_gev')) and
            Path(original['output']).resolve()==run and plan['request']==original,
            'preserved source request or location differs')
    require(plan['installed_identity']==installed,'installed environment changed since original source generation')
    result_path=run/'validation/mg5_execution.json';result=strict_json(result_path)
    source=Path(result['lhe_path']).resolve()
    require(source.is_relative_to(run) and source.is_file() and not source.is_symlink() and
            sha_file(source)==result['artifacts']['lhe_gz']['sha256'],'preserved source bytes changed')
    require(allow_reserved_continuation or not (CAMPAIGN/('downstream_recovery_'+sha_file(source)+'.json')).exists(),
            'preserved source already reserved for one downstream attempt; no physical retry')
    authority=Path(result['authorization_receipt']['path'])
    require(authority==run/'authorization.json' and sha_file(authority)==result['authorization_receipt']['sha256'],
            'preserved source authority changed')
    elapsed=manifest['resource_usage']['elapsed_seconds']
    require(type(elapsed) in (float,int) and 0<elapsed<requested['max_hours']*3600,
            'preserved source consumed the remaining elapsed budget')
    cfg=strict_json(REPO/'.local/mg5_installation.json')
    size=tree_bytes(run,(cfg['mg5_path'],cfg['toolchain_prefix']))
    require(size<requested['max_disk_gb']*1024**3,'preserved source consumed the disk budget')
    return {'run':str(run),'result':result,'manifest_path':str(manifest_path),'manifest_sha256':sha_file(manifest_path),
            'plan_path':str(plan_path),'plan_sha256':sha_file(plan_path),'result_path':str(result_path),
            'result_sha256':sha_file(result_path),'source_path':str(source),'source_sha256':sha_file(source),
            'original_authorization_path':str(authority),'original_authorization_sha256':sha_file(authority),
            'original_bridge_sha256':manifest['bridge_sha256'],'previous_elapsed_seconds':elapsed,
            'previous_output_bytes':size,'MG5_invocations_in_recovery':0,
            'previous_sampled_peak_rss_bytes':manifest['resource_usage']['peak_sampled_process_tree_rss_bytes'],
            'previous_peak_observed_output_bytes':manifest['resource_usage']['peak_observed_output_bytes'],
            'scope':'Same original source, read-only revalidation of a diagnosed representation stop; no replacement statistics'}


def preserved_chain(run,requested,installed):
    """One known false reader failure; completed physical prefix10 is immutable."""
    candidate=Path(run).expanduser();require(candidate.is_dir() and not candidate.is_symlink(),'unsafe stopped chain directory')
    run=candidate.resolve();manifest_path=run/'run_manifest.json'
    require(not Path(requested['output']).is_relative_to(run) and not run.is_relative_to(Path(requested['output'])),
            'continuation output must be separate from the preserved stopped chain')
    require(sha_file(manifest_path)=='18ecb5657ab7bdb20d9861c357fe3904f935e4d63f0dcca8e1b5260790ea45ce',
            'only the reviewed immutable B04 prefix10 reader stop may continue')
    manifest=strict_json(manifest_path);oldplan=strict_json(run/'execution_plan.json')
    require(manifest['status']=='PARTIAL_PHYSICAL_CHAIN' and manifest['failure']=='FAILED_STAGE: background_reader_prefix10; retained actual log' and
            manifest['bridge_sha256']=='112d4d208f3d046092aaf71c5c2263f1637ee1b96c19c612e59c63c9621ca199' and manifest['MG5_events_generated']==1000,
            'unexpected original chain failure or source identity')
    require(oldplan['installed_identity']==installed and manifest['request']['process']=='zh' and
            all(manifest['request'][k]==requested[k] for k in ('process','events','seed','energy_gev')),
            'chain continuation request or retained environment differs')
    attempted={row['stage'] for row in manifest['stages_attempted']}
    require('shower_background_prefix10' in attempted and 'background_reader_prefix10' in attempted and
            not any(stage in attempted for stage in ('shower_background_prefix100','shower_background_full1000')) and
            not any(stage.startswith('delphes_') for stage in attempted),'a later physical stage was already attempted')
    prefix=run/'pythia/prefix10';summary=strict_json(prefix/'run_summary.json')
    generic=strict_json(prefix/'generic_physics_validation.json');failed=strict_json(prefix/'background_hepmc_validation.json')
    require(summary['status']=='SHOWER_WRITTEN_REQUIRES_INDEPENDENT_READER' and
            all(summary[key]==10 for key in ('N_input','N_attempted','N_pythia_next_calls','N_shower_success','N_written','N_source_identity_verified')) and
            summary['N_shower_failed']==summary['N_source_identity_failed']==0 and summary['source_total_events']==1000,
            'reused prefix is not the complete genuine successful10-event shower')
    require(generic['validation_status']=='PASS' and generic['N_readback']==generic['N_passed_validation']==10 and generic['N_failed_validation']==0,
            'existing prefix failed real generic physics validation')
    require(failed['validation_status']=='FAIL_BACKGROUND_HEPMC_RECORDS' and
            failed['fatal_error']=='Retained original Pythia status inconsistent with actual HepMC status' and
            failed['N_readback']==failed['N_failed_validation']==1 and failed['N_passed_validation']==0,
            'existing ancestry failure is not the diagnosed null-Event context bug')
    require(sha_file(prefix/'shower.hepmc3')=='ad51a02e982ae83368768e84569f20093de304714c54e7496aadc12a438f9e00',
            'genuine retained prefix10 changed')
    source=preserved_source(manifest['preserved_source_recovery']['run'],requested,installed,allow_reserved_continuation=True)
    require(source['source_sha256']==summary['source_file_sha256'] and summary['pythia_seed']==610401,'reused prefix belongs to another source/seed')
    marker=CAMPAIGN/('reader_context_continuation_'+source['source_sha256']+'.json')
    require(not marker.exists(),'one reader-context continuation was already reserved; no repeated physical continuation')
    cfg=strict_json(REPO/'.local/mg5_installation.json')
    source['previous_elapsed_seconds']=manifest['resource_usage']['elapsed_seconds']
    source['previous_output_bytes']+=tree_bytes(run,(cfg['mg5_path'],cfg['toolchain_prefix']))
    source['previous_sampled_peak_rss_bytes']=max(source['previous_sampled_peak_rss_bytes'],manifest['resource_usage']['peak_sampled_process_tree_rss_bytes'])
    source['previous_peak_observed_output_bytes']=max(source['previous_peak_observed_output_bytes'],manifest['resource_usage']['combined_peak_observed_output_bytes'])
    source['previous_chain_run']=str(run)
    source['previous_chain_bindings']={str(path):sha_file(path) for path in
        (manifest_path,run/'execution_plan.json',run/'authorization.json',prefix/'execution_authorization.json',
         prefix/'run_summary.json',prefix/'generic_physics_validation.json',prefix/'background_hepmc_validation.json')}
    original_reservation=manifest['preserved_source_recovery']['downstream_global_reservation']
    require(sha_file(original_reservation['path'])==original_reservation['sha256'],'original one-attempt registry changed')
    source['previous_chain_bindings'][original_reservation['path']]=original_reservation['sha256']
    kept=('shower.hepmc3','run_summary.json','event_ledger.jsonl','particle_diagnostics.jsonl',
          'decay_tables_original_preinit.json','decay_tables_inclusive_initialized.json','decay_tables_initialized.json','decay_tables_before_init.json',
          'original_particle_data.xml','inclusive_initialized_particle_data.xml','effective_particle_data.xml',
          'effective_settings.cmnd','inclusive_initialized_settings.cmnd')
    source['reused_prefix10_files']={str(prefix/name):sha_file(prefix/name) for name in kept}
    source['chain_continuation_scope']='READ_ONLY_PREFIX10_REVALIDATION_THEN_PREVIOUSLY_UNEXECUTED_PREFIX100_FULL1000; ZERO_SOURCE_GENERATION_ZERO_PREFIX10_SHOWER_REPLAY'
    require(source['previous_elapsed_seconds']<requested['max_hours']*3600 and source['previous_output_bytes']<requested['max_disk_gb']*1024**3,
            'previous source and stopped chain consumed the remaining budget')
    return source


def preserved_detector(run,requested,installed):
    """Known numeric false positive only; never call MG5 or Pythia again."""
    from simulation.new_backgrounds.delphes_stage import REUSE_MANIFEST_SHA,REUSE_FULL_SHOWER_SHA,REUSE_ROOT_SHA,REUSE_NATIVE_SHA
    candidate=Path(run).expanduser()
    require(candidate.is_dir() and not candidate.is_symlink(),'unsafe stopped detector directory')
    run=candidate.resolve();output=Path(requested['output']);manifest_path=run/'run_manifest.json'
    require(not output.is_relative_to(run) and not run.is_relative_to(output),'detector continuation output must be separate')
    require(sha_file(manifest_path)==REUSE_MANIFEST_SHA,'only the immutable diagnosed B04 detector stop may continue')
    manifest=strict_json(manifest_path);oldplan=strict_json(run/'execution_plan.json')
    require(manifest['status']=='PARTIAL_PHYSICAL_CHAIN' and
            manifest['failure']=='FAILED_STAGE: independent_native_root_zh_100; retained actual log' and
            manifest['bridge_sha256']=='fd9bec3eb7ae1022ff31361f946769f528d41c0093a18aa29835824a91545b67' and
            requested['process']=='zh' and oldplan['installed_identity']==installed and
            all(manifest['request'][k]==requested[k] for k in ('process','events','seed','energy_gev')),
            'unexpected preserved detector failure, request or environment')
    require(all(manifest[k]==1000 for k in ('MG5_events_generated','Pythia_events_attempted','Pythia_events_written','HepMC_validated_events')) and
            manifest['Delphes_ROOT_entries']==0 and not any(row['stage']=='delphes_zh_1000' for row in manifest['stages_attempted']),
            'full detector was already attempted or genuine full shower missing')
    source=preserved_source(manifest['preserved_source_recovery']['run'],requested,installed,allow_reserved_continuation=True)
    require(not (CAMPAIGN/('root_numeric_continuation_'+source['source_sha256']+'.json')).exists(),
            'one detector continuation already reserved; no physical retry')
    # Exact immutable file bindings cover every reused physical record, authority,
    # weight table and readback receipt, without duplicating the large full shower.
    bindings={str(p):sha_file(p) for folder in (run/'pythia',run/'validation',run/'native_build',run/'delphes')
              for p in folder.rglob('*') if p.is_file()}
    for p in (manifest_path,run/'execution_plan.json',run/'authorization.json'):
        bindings[str(p)]=sha_file(p)
    prior=manifest['preserved_source_recovery']
    for key in ('previous_chain_bindings','reused_prefix10_files'):
        for path,digest in prior.get(key,{}).items():
            require(sha_file(path)==digest,'earlier immutable continuation authority/artifact changed')
            bindings[path]=digest
    reserved=prior['downstream_global_reservation']
    require(sha_file(reserved['path'])==reserved['sha256'],'earlier one-use continuation registry changed')
    bindings[reserved['path']]=reserved['sha256']
    for stage,count in (('prefix10',10),('prefix100',100),('full1000',1000)):
        receipt=manifest['stages'][stage];folder=run/'pythia'/stage
        require(receipt['status']=='PASS_RAW_SHOWER_AND_HEPMC_RECORDS' and
                all(receipt['run_summary'][k]==count for k in ('N_attempted','N_shower_success','N_written','N_source_identity_verified')) and
                receipt['run_summary']['N_shower_failed']==0 and receipt['reader_report']['N_readback']==count and
                receipt['reader_report']['N_passed_validation']==count and receipt['reader_report']['N_failed_validation']==0,
                'retained shower/reader did not pass every actual record')
        require(strict_json(folder/'run_summary.json')==receipt['run_summary'] and
                strict_json(folder/'background_hepmc_validation.json')==receipt['reader_report'],
                'stored physical receipts differ from original manifest')
        report=receipt['reader_report']
        require(all(sha_file(folder/name)==report[key] for name,key in
                    (('shower.hepmc3','decompressed_file_sha256'),('input_event_index.dat','input_index_sha256'),
                     ('background_truth_index.dat','truth_index_sha256'))),'retained Reader inspected different physical files')
    require(sha_file(run/'pythia/full1000/shower.hepmc3')==REUSE_FULL_SHOWER_SHA and
            strict_json(run/'validation/weight_and_BR_ledger.json')==manifest['weight_and_BR_ledger'] and
            manifest['weight_and_BR_ledger']['status']=='PASS_MODEL_BR_WEIGHT_CLOSURE','full shower or verified weight closure changed')
    detectors={}
    for count in (10,100):
        folder=run/'delphes'/f'prefix{count}'
        require(sha_file(folder/'detector.root')==REUSE_ROOT_SHA[count] and
                sha_file(folder/'native_validation.json')==REUSE_NATIVE_SHA[count],'original detector bytes/report changed')
        detectors[str(count)]={'status':'SOURCE_BOUND_READ_ONLY_DETECTOR_REUSE','original_directory':str(folder),
            'source_manifest_path':str(manifest_path),'source_manifest_sha256':REUSE_MANIFEST_SHA,
            'root_path':str(folder/'detector.root'),'root_sha256':REUSE_ROOT_SHA[count],
            'old_native_validation_path':str(folder/'native_validation.json'),'old_native_validation_sha256':REUSE_NATIVE_SHA[count],
            'source_full_shower_sha256':REUSE_FULL_SHOWER_SHA,
            'artifacts_sha256':{name:sha_file(folder/name) for name in ('detector_card.tcl','input.hepmc3','input_event_index.dat','background_truth_index.dat')}}
    cfg=strict_json(REPO/'.local/mg5_installation.json')
    source['previous_elapsed_seconds']=manifest['resource_usage']['elapsed_seconds']
    source['previous_output_bytes']=manifest['resource_usage']['preserved_source_output_bytes']+tree_bytes(run,(cfg['mg5_path'],cfg['toolchain_prefix']))
    source['previous_sampled_peak_rss_bytes']=manifest['resource_usage']['combined_peak_sampled_process_tree_rss_bytes']
    source['previous_peak_observed_output_bytes']=manifest['resource_usage']['combined_peak_observed_output_bytes']
    source['retained_shower']={'status':'SOURCE_BOUND_COMPLETED_SHOWER_REUSE_ZERO_PRODUCER_CALLS',
        'original_run':str(run),'manifest_path':str(manifest_path),'manifest_sha256':REUSE_MANIFEST_SHA,
        'files_sha256':bindings,'Pythia_invocations_in_continuation':0,'new_source_events':0,
        'full_shower_sha256':REUSE_FULL_SHOWER_SHA}
    source['reused_detectors']=detectors
    require(source['previous_elapsed_seconds']<requested['max_hours']*3600 and source['previous_output_bytes']<requested['max_disk_gb']*1024**3,
            'previous genuine stages consumed the continuation budget')
    return source


def reserve_existing_source_once(existing_source,campaign,output):
    """Exclusive registry outside the preserved run; prevents fresh-output retries."""
    CAMPAIGN.mkdir(parents=True,exist_ok=True)
    kind='root_numeric_continuation_' if existing_source.get('retained_shower') else 'reader_context_continuation_' if existing_source.get('reused_prefix10_files') else 'downstream_recovery_'
    path=CAMPAIGN/(kind+existing_source['source_sha256']+'.json')
    receipt={'status':'RESERVED_ONE_EXISTING_SOURCE_DOWNSTREAM_ATTEMPT',
             'original_source_sha256':existing_source['source_sha256'],'campaign_id':campaign['campaign_id'],
             'bridge_sha256':campaign['bridge_sha256'],'output':str(output),
             'created_at_utc':datetime.now(timezone.utc).isoformat(),'new_source_events_authorized':0}
    with path.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    return {'path':str(path),'sha256':sha_file(path)}


def prepare(output,requested,identity,bindings,installed,resources):
    from simulation.new_backgrounds.mg5_stage import prepare_mg5_stage,PROFILES
    cfg=strict_json(REPO/'.local/mg5_installation.json')
    stage=prepare_mg5_stage(output/'mg5',repo=REPO,installation=cfg,process=requested['process'],
        events=1000,seed=requested['seed'],energy_gev=13000)
    plan={'schema_version':1,'task':ACK,'status':'PREPARED_TEXT_ONLY','request':requested,
        'profile':PROFILES[requested['process']],'bridge_sha256':identity,'bridge_sources':bindings,
        'reviewed_base_head':BASE,'installed_identity':installed,'resources':resources,'mg5_prepared':stage,
        'authorization_source_sha256':AUTHORIZATION_SOURCE_SHA256,'source_denominator':1000,
        'seeds':{'MG5':requested['seed'],'Pythia':PROCESSES[requested['process']]['pythia_seed'],
                 'Delphes':PROCESSES[requested['process']]['delphes_seed']},
        'subsets':'10/100 are original source prefixes; never extra independent hard statistics',
        'detector_label':'FAST_SIM_ATLAS_LIKE_NOT_OFFICIAL_ATLAS','interpretation_gates':{'O':'BLOCKED','P':'UNKNOWN','Q':'BLOCKED'},
        'new_events_generated':0,'Git_publication_automatic':False}
    save_json(output/'execution_plan.json',plan);return plan


def native_authority(output,stage,requested,campaign,auth_sha,source,build,started):
    child=output/'pythia'/stage;require(not child.exists(),'stage already exists; no hidden rerun');child.mkdir(parents=True)
    record={'schema_version':1,'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','authorization_command':ACK,
        'reviewed_base_head':BASE,'campaign_id':campaign['campaign_id'],'source_request':requested,
        'pythia_seed':PROCESSES[requested['process']]['pythia_seed'],'child_stage':stage,'child_output':str(child),
        'bridge_sha256':campaign['bridge_sha256'],'authorization_receipt_sha256':auth_sha,'source_total_events':1000,
        'source_original_sha256':source['original_sha256'],'source_lhe_path':str(source['plain_path']),
        'source_lhe_sha256':source['plain_sha256'],'source_index_path':str(source['index_path']),
        'source_index_sha256':source['index_sha256'],'native_runner_sha256':build['binaries']['shower_background']['sha256'],
        'native_validator_sha256':build['binaries']['validate_background_hepmc3']['sha256'],
        'deadline_epoch_seconds':time.time()+max(0,requested['max_hours']*3600-(time.monotonic()-started))}
    path=child/'execution_authorization.json';save_json(path,record);return path


def weight_ledger(source,folder,process,build):
    from simulation.new_backgrounds.validate_lhe import validate_downstream_binding
    path=Path(folder)/'hepmc_ancestry.jsonl';require(path.stat().st_size<=64*1024**2,'oversized ancestry/weight ledger')
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    records=[{'source_file_sha256':source['source_file_sha256'],'source_event_index':row['source_event_index'],
        'source_event_sha256':row['source_event_content_hash'],'source_total_events':1000,
        'weight_names':row['weight_names'],'weight_values':row['weights_pb']} for row in rows]
    binding=validate_downstream_binding(source,records,expected_output_count=1000)
    summary=strict_json(Path(folder)/'run_summary.json');model=summary['initialized_higgs_decay']
    from build_stage import weight_source_bindings
    proof_files=weight_source_bindings(strict_json(REPO/'.local/pythia8_installation.json'))
    require(proof_files==build['weight_source_sha256'],
            'retained external-LHE weight implementation changed')
    source_proof_path=REPO/'simulation/new_backgrounds/evidence/pythia_weight_source_inspection.json'
    ratios=[Decimal(str(row['weight_values'][2]))/Decimal(str(row['weight_values'][1])) for row in records if Decimal(str(row['weight_values'][1]))]
    applicable=process!='bbgj';br=Decimal(str(model['inclusive_model_BR_gamma_gamma'])) if applicable else Decimal(1)
    if applicable:
        require(model['applicable'] is True and 0<br<1 and Decimal(str(model['conditional_forced_probability']))==1,'invalid actual forced/inclusive H model')
        for key,name in {'inclusive_table_sha256':'decay_tables_inclusive_initialized.json','effective_table_sha256':'decay_tables_initialized.json',
            'original_preinit_table_sha256':'decay_tables_original_preinit.json','original_particle_data_sha256':'original_particle_data.xml',
            'inclusive_particle_data_sha256':'inclusive_initialized_particle_data.xml','effective_particle_data_sha256':'effective_particle_data.xml'}.items():
            require(sha_file(Path(folder)/name)==model[key],'actual initialized decay snapshot changed')
    identity=bool(ratios) and all(abs(r-1)<=Decimal('2e-10') for r in ratios)
    matched=bool(ratios) and all(abs(r-br)<=Decimal('2e-10')*max(abs(br),Decimal('1e-8')) for r in ratios)
    # Hash-bound retained external-LHE -4 code transfers the source nominal
    # without a forced-decay BR multiplier. A numerical BR match alone is not
    # proof of inclusion and cannot satisfy the reviewed convention.
    closure=identity
    transfer='IDENTITY' if identity else 'MATCHES_INITIALIZED_H_MODEL_BR' if matched else 'UNRESOLVED'
    raw=[Decimal(str(row['weight_values'][0])) for row in records]
    result={'schema_version':1,'status':'PASS_MODEL_BR_WEIGHT_CLOSURE' if applicable and closure else 'PASS_RAW_WEIGHT_CLOSURE' if closure else 'BLOCKED_DECAY_WEIGHT_CLOSURE',
        'scope':'MODEL_BR_ONLY' if applicable else 'NO_HIGGS_BR','factor':str(br) if applicable and closure else None,
        'factor_applications':1 if applicable and closure else 0,'weight_closure':'PASS' if closure else 'BLOCKED',
        'binding':binding,'full_original_source_denominator':1000,'observed_Info_to_LHE_ratio_min':str(min(ratios)) if ratios else None,
        'observed_Info_to_LHE_ratio_max':str(max(ratios)) if ratios else None,'nominal_transfer_class':transfer,
        'source_included_decay_factors':['Z_to_b_bbar'] if process=='zh' else [],'Z_BR_reapplied':False,'HH_factor_two_applied':False,
        'top_W_scope':'INCLUSIVE_SUPPORTED_PYTHIA_MODEL_NO_VALIDATED_PRODUCTION_DECAY_SPIN_CORRELATION' if process=='tth' else 'NOT_APPLICABLE',
        'actual_initialized_higgs_decay':model,'actual_summary_sha256':sha_file(Path(folder)/'run_summary.json'),
        'weight_source_proof_sha256':sha_file(source_proof_path),'weight_implementation_source_sha256':build['weight_source_sha256'],
        'weight_implementation_source_commit':build['weight_source_commit'],
        'phase6f_H_BR_reference_only':'0.0022965313147512443','YR4_H_BR_reference_only':'0.002270',
        'raw_source_weight_sum_pb':str(sum(raw)),'raw_source_weight_squared_sum_pb2':str(sum(w*w for w in raw)),
        'model_BR_weight_sum_pb':str(sum(raw)*br) if applicable and closure else None,
        'model_BR_weight_squared_sum_pb2':str(sum(w*w for w in raw)*br*br) if applicable and closure else None,
        'model_contribution_rule':'ORIGINAL_RAW_SOURCE_CONTRIBUTION_TIMES_ACTUAL_MODEL_BR_ONCE; never multiply already-corrected Info again',
        'normalization_scope':'EXPLORATORY_MODEL_ONLY_NO_OFFICIAL_ATLAS_NO_LUMINOSITY',
        'factor_inclusion_inference':'Observed named-column closure plus actual initialized model/forced table; not a precision physical BR adoption'}
    return result


def observed_counts(output,state,executions):
    """Retain genuine failed-stage counters; never invent0 or replacement events."""
    stages={row['stage'] for row in executions};observations={}
    process=state['request']['process'];lhe=output/'mg5/process/Events'/(process+'1000')/'unweighted_events.lhe.gz'
    if state.get('preserved_source_recovery'):lhe=Path(state['preserved_source_recovery']['source_path'])
    if 'mg5_1000_event_generation' in stages:state['MG5_events_generated']='UNKNOWN_UNTIL_COMPLETE_RECORD_COUNT'
    if lhe.is_file():
        try:
            from simulation.new_backgrounds.validate_lhe import bounded_bytes,parse_xml
            raw,digest=bounded_bytes(lhe);count=len(parse_xml(raw).findall('event'))
            state['MG5_events_generated']=count;observations['complete_LHE_XML_count']={'events':count,'sha256':digest,'physics_validation_separate':True}
        except (OSError,ValueError) as error:observations['LHE_count_error']=str(error)
    for stage in ('prefix10','prefix100','full1000'):
        for name in ('run_summary.json','background_hepmc_validation.json'):
            path=output/'pythia'/stage/name
            if path.is_file():
                try:
                    value=strict_json(path);observations[stage+'/'+name]=value
                    if stage=='full1000' and name=='run_summary.json':
                        state['Pythia_events_attempted']=value.get('N_attempted','UNKNOWN');state['Pythia_events_written']=value.get('N_written','UNKNOWN')
                    elif stage=='full1000':state['HepMC_validated_events']=value.get('N_passed_validation','UNKNOWN')
                except (OSError,ValueError) as error:observations[stage+'/'+name]={'error':str(error)}
    path=output/'delphes/full1000/native_validation.json'
    if path.is_file():
        try:
            value=strict_json(path);observations['full1000/native_ROOT']=value;state['Delphes_ROOT_entries']=value.get('ROOT_entries','UNKNOWN')
        except (OSError,ValueError) as error:observations['native_ROOT_error']=str(error)
    for prefix,key in (('shower_background_full1000','Pythia_events_written'),('background_reader_full1000','HepMC_validated_events'),
                       (f'delphes_{process}_1000','Delphes_ROOT_entries')):
        if prefix in stages and state[key]==0:state[key]='UNKNOWN_UNTIL_ACTUAL_NATIVE_RECEIPT'
    state['actual_partial_observations']=observations


def execute(output,requested,plan,installed_before,started,existing_source=None):
    from simulation.new_backgrounds.mg5_stage import execute_mg5_stage
    from simulation.new_backgrounds.validate_lhe import validate_file,prepared_contract,ValidationError
    from simulation.new_backgrounds.delphes_stage import native_environment,build_root_analyzer,execute_delphes
    from simulation.new_backgrounds.analyze_results import summarize_detector
    from build_stage import compile_bridge
    from shower_stage import source_index_bytes,run_stage
    mgcfg=strict_json(REPO/'.local/mg5_installation.json');pycfg=strict_json(REPO/'.local/pythia8_installation.json');dcfg=strict_json(REPO/'.local/delphes_installation.json')
    env=native_environment(dcfg,pycfg,mgcfg,output)
    monitor_request=dict(requested)
    if existing_source:
        started-=existing_source['previous_elapsed_seconds']
        monitor_request['max_disk_gb']-=existing_source['previous_output_bytes']/1024**3
    monitor=Monitor(output,monitor_request,env,started,readonly_roots=(mgcfg['mg5_path'],mgcfg['toolchain_prefix']))
    monitor.install_signals()
    if existing_source:
        campaign={'campaign_id':str(uuid.uuid4()),'bridge_sha256':plan['bridge_sha256'],
                  'status':'RESERVED_EXISTING_SOURCE_DOWNSTREAM_ONLY','source_event_ceiling':0,
                  'original_source_sha256':existing_source['source_sha256'],'original_manifest_sha256':existing_source['manifest_sha256']}
        save_json(output/'downstream_attempt_reservation.json',campaign)
    else:campaign=reserve_campaign(output,requested,plan['bridge_sha256'])
    authority={'schema_version':1,'status':'AUTHORIZED_TASK_ATTACHMENT','authorization_command':ACK,
        'attachment_sha256':AUTHORIZATION_SOURCE_SHA256,'reviewed_base_head':BASE,'request':requested,'profile':plan['profile'],
        'bridge_sha256':plan['bridge_sha256'],'campaign_id':campaign['campaign_id'],'authorized_at_utc':datetime.now(timezone.utc).isoformat()}
    authority_path=output/'authorization.json';save_json(authority_path,authority);auth_sha=sha_file(authority_path)
    state={'schema_version':1,'task':ACK,'status':'AUTHORIZED_EXECUTION_IN_PROGRESS','campaign_id':campaign['campaign_id'],
        'request':requested,'bridge_sha256':plan['bridge_sha256'],'controller_started_at_utc':datetime.now(timezone.utc).isoformat(),
        'authorization_receipt':{'path':str(authority_path),'sha256':auth_sha,'id':campaign['campaign_id']},'source_attempt_reservation':campaign,
        'MG5_events_generated':0,'Pythia_events_attempted':0,'Pythia_events_written':0,'HepMC_validated_events':0,'Delphes_ROOT_entries':0,
        'MG5_events_generated_in_this_attempt':0,'MG5_events_reused':1000 if existing_source else 0,
        'Pythia_events_attempted_in_this_attempt':0 if existing_source and existing_source.get('retained_shower') else None,
        'Pythia_events_reused':1000 if existing_source and existing_source.get('retained_shower') else 0,
        'stages':{},'interpretation_gates':{'O':'BLOCKED_PHOTON_FAKE','P':'UNKNOWN_OVERLAP','Q':'BLOCKED_OFFICIAL_CALIBRATION'}}
    if existing_source:state['preserved_source_recovery']=existing_source
    def guard(argv,cwd,stage,env=None,expected_exit_code=0):
        require(bridge_identity()[0]==plan['bridge_sha256'] and sha_file(authority_path)==auth_sha,'frozen source or task authority changed')
        if existing_source:
            if existing_source.get('retained_shower'):
                require(not stage.startswith(('mg5_','shower_background_','background_reader_')) and
                        not any(Path(str(arg)).name in ('mg5_aMC','shower_background') for arg in argv),
                        'detector-only continuation forbids every source/shower producer')
            require(all(sha_file(existing_source[key])==existing_source[digest] for key,digest in
                        (('manifest_path','manifest_sha256'),('plan_path','plan_sha256'),('result_path','result_sha256'),('source_path','source_sha256'),
                         ('original_authorization_path','original_authorization_sha256'))),
                    'preserved source provenance changed during recovery')
            if existing_source.get('downstream_global_reservation'):
                reserved=existing_source['downstream_global_reservation']
                require(sha_file(reserved['path'])==reserved['sha256'],'existing-source one-attempt registry changed')
            for key in ('previous_chain_bindings','reused_prefix10_files'):
                require(all(sha_file(path)==digest for path,digest in existing_source.get(key,{}).items()),
                        'preserved stopped chain or genuine prefix10 changed')
            require(all(sha_file(path)==digest for path,digest in existing_source.get('retained_shower',{}).get('files_sha256',{}).items()),
                    'immutable completed shower or detector-prefix artifact changed')
        return monitor.run_command(argv,cwd,stage,env=env,expected_exit_code=expected_exit_code)
    save_json(output/'run_manifest.json',state)
    try:
        validation=output/'validation';validation.mkdir()
        if not existing_source:
            build=compile_bridge(output/'native_build',pycfg,run_command=guard)
            root=build_root_analyzer(output/'root_build',dcfg,run_command=guard)
            state['stages']['native_build']=build;state['stages']['root_build']=root;save_json(output/'run_manifest.json',state)
            result=execute_mg5_stage(plan['mg5_prepared'],run_command=guard);result['authorization_receipt']=state['authorization_receipt']
        else:result=existing_source['result']
        save_json(validation/'mg5_execution.json',result)
        try:
            source=validate_file(result['lhe_path'],expected_seed=requested['seed'],process=requested['process'],
                card_contract=prepared_contract(requested['seed'],requested['process']),provenance=result)
        except ValidationError as error:
            save_json(validation/'lhe_validation.json',error.report);raise
        save_json(validation/'lhe_validation.json',source);state['stages']['MG5']=result;state['MG5_events_generated']=source['actual_events']
        state['source_cross_section_pb']=source['cross_section_pb'];state['source_integration_uncertainty_pb']=source['cross_section_uncertainty_pb']
        save_json(output/'run_manifest.json',state)
        if existing_source:
            retained=existing_source.get('retained_shower')
            build=strict_json(Path(retained['original_run'])/'native_build/build_receipt.json') if retained else compile_bridge(output/'native_build',pycfg,run_command=guard)
            root=build_root_analyzer(output/'root_build',dcfg,run_command=guard)
            state['stages']['native_build']=build;state['stages']['root_build']=root;save_json(output/'run_manifest.json',state)
        plain=validation/'original_full1000.lhe'
        with gzip.open(result['lhe_path'],'rb') as src,plain.open('xb') as dst:
            while block:=src.read(1024**2):monitor.check();dst.write(block)
        require(sha_file(plain)==source['decompressed_file_sha256'],'plain LHE differs from validated CRC/original')
        index=validation/'source_events.dat';index.write_bytes(source_index_bytes(source))
        descriptor={'original_sha256':source['source_file_sha256'],'plain_path':plain,'plain_sha256':sha_file(plain),'index_path':index,'index_sha256':sha_file(index)}
        if existing_source:
            existing_source['downstream_global_reservation']=reserve_existing_source_once(existing_source,campaign,output)
            save_json(output/'run_manifest.json',state)
        for stage in ('prefix10','prefix100','full1000'):
            if existing_source and existing_source.get('retained_shower'):
                original=Path(existing_source['retained_shower']['original_run'])
                observed=strict_json(original/'run_manifest.json')['stages'][stage]
                state['stages'][stage]=observed;save_json(validation/(stage+'_validation.json'),observed)
                save_json(output/'run_manifest.json',state)
                continue
            auth=native_authority(output,stage,requested,campaign,auth_sha,descriptor,build,started)
            reused=None
            if stage=='prefix10' and existing_source and existing_source.get('reused_prefix10_files'):
                child=output/'pythia/prefix10'
                for path,digest in existing_source['reused_prefix10_files'].items():
                    require(sha_file(path)==digest,'preserved prefix artifact changed before exact copy')
                    target=child/Path(path).name;shutil.copyfile(path,target)
                    require(sha_file(target)==digest,'reused prefix copy differs from genuine original bytes')
                original_prefix=Path(existing_source['previous_chain_run'])/'pythia/prefix10'
                reused={'status':'SOURCE_BOUND_NON_GENERATING_PREFIX10_REUSE',
                        'original_prefix_directory':str(original_prefix),
                        'original_manifest_path':str(Path(existing_source['previous_chain_run'])/'run_manifest.json'),
                        'original_manifest_sha256':existing_source['previous_chain_bindings'][str(Path(existing_source['previous_chain_run'])/'run_manifest.json')],
                        'original_failed_reader_report_sha256':existing_source['previous_chain_bindings'][str(original_prefix/'background_hepmc_validation.json')],
                        'original_stage_authorization_sha256':existing_source['previous_chain_bindings'][str(original_prefix/'execution_authorization.json')],
                        'artifacts':{Path(path).name:digest for path,digest in existing_source['reused_prefix10_files'].items()}}
            run_id=strict_json(output/'pythia/prefix10/run_summary.json')['pythia_run_id'] if reused else str(uuid.uuid4())
            observed=run_stage(authorization_file=auth,stage=stage,build_receipt=output/'native_build/build_receipt.json',
                source_validation=source,xml_path=pycfg['xml_path'],run_id=run_id,run_command=guard,
                **({'reused_shower':reused} if reused else {}))
            require(observed['status']=='PASS_RAW_SHOWER_AND_HEPMC_RECORDS','physical shower/reader failed '+stage)
            state['stages'][stage]=observed;save_json(validation/(stage+'_validation.json'),observed)
            save_json(output/'run_manifest.json',state)
        full=(Path(existing_source['retained_shower']['original_run']) if existing_source and existing_source.get('retained_shower') else output)/'pythia/full1000'
        reader=state['stages']['full1000']['reader_report']
        state['Pythia_events_attempted']=state['stages']['full1000']['run_summary']['N_attempted']
        state['Pythia_events_written']=1000;state['HepMC_validated_events']=reader['N_readback']
        ledger=weight_ledger(source,full,requested['process'],build);ledger_path=validation/'weight_and_BR_ledger.json';save_json(ledger_path,ledger)
        if existing_source and existing_source.get('retained_shower'):
            require(ledger==strict_json(Path(existing_source['retained_shower']['original_run'])/'validation/weight_and_BR_ledger.json'),
                    'read-only recomputed weight/BR ledger differs from preserved full1000 closure')
        state['weight_and_BR_ledger']=ledger
        save_json(output/'run_manifest.json',state)
        shower={'status':'PASS_READER_ASCII_RECORDS','validated_events':1000,'source_events':1000,
            'hepmc_path':str(full/'shower.hepmc3'),'hepmc_path_sha256':reader['decompressed_file_sha256'],
            'input_index_path':str(full/'input_event_index.dat'),'input_index_path_sha256':reader['input_index_sha256'],
            'truth_index_path':str(full/'background_truth_index.dat'),'truth_index_path_sha256':reader['truth_index_sha256']}
        for count in (10,100,1000):
            target=output/'delphes'/('prefix'+str(count) if count!=1000 else 'full1000')
            reused=existing_source.get('reused_detectors',{}).get(str(count)) if existing_source else None
            det=execute_delphes(target,shower,dcfg,root,PROCESSES[requested['process']]['delphes_seed'],guard,requested['process'],events=count,
                                **({'reused_detector':reused} if reused else {}))
            state['stages']['Delphes'+str(count)]=det;save_json(validation/('detector_'+str(count)+'_validation.json'),det)
            save_json(output/'run_manifest.json',state)
        state['Delphes_ROOT_entries']=state['stages']['Delphes1000']['ROOT_entries']
        model={key:ledger[key] for key in ('status','scope','factor','factor_applications','weight_closure')}
        model['ledger_sha256']=sha_file(ledger_path)
        if model['factor'] is not None:model['factor']=float(model['factor'])
        stats=summarize_detector(state['stages']['Delphes1000'],model_br=model if requested['process']!='bbgj' and ledger['weight_closure']=='PASS' else None,
            generator_integration_uncertainty_pb=float(source['cross_section_uncertainty_pb']))
        save_json(validation/'cutflow_statistics.json',stats);state['statistics']=stats
        if not (existing_source and existing_source.get('retained_shower')):
            with (full/'shower.hepmc3').open('rb') as src,(full/'shower.hepmc3.gz').open('xb') as dst:
                with gzip.GzipFile(fileobj=dst,mode='wb',mtime=0,filename='') as compressed:
                    while block:=src.read(1024**2):monitor.check();compressed.write(block)
        require(verify_environment()==installed_before and bridge_identity()[0]==plan['bridge_sha256'],'installed tools or frozen source changed during production')
        require(sha_file(result['lhe_path'])==source['source_file_sha256'],'original source file changed');monitor.check()
        state['status']='PASS_FULL_CHAIN_MODEL_SCOPE' if ledger['weight_closure']=='PASS' else 'PASS_RAW_FULL_CHAIN_EXCLUSIVE_NORMALIZATION_BLOCKED'
        state['physical_generation_completed']=True
    except BaseException as error:
        state['status']='PARTIAL_PHYSICAL_CHAIN' if existing_source or any('mg5_' in row['stage'] for row in monitor.executions) else 'FAILED_PREFLIGHT_OR_BUILD'
        state['failure']=str(error);state['physical_generation_completed']=False
    finally:
        observed_counts(output,state,monitor.executions)
        if not (existing_source and existing_source.get('retained_shower')):
            state['Pythia_events_attempted_in_this_attempt']=state['Pythia_events_attempted']
        if not existing_source:state['MG5_events_generated_in_this_attempt']=state['MG5_events_generated']
        try:state['resource_usage']=monitor.metrics()
        except (OSError,ValueError,RuntimeError) as error:state['resource_usage']={'accounting_error':str(error),'executions':monitor.executions}
        if existing_source and 'elapsed_seconds' in state['resource_usage']:
            metrics=state['resource_usage'];metrics['includes_preserved_source_elapsed']=True
            metrics['recovery_elapsed_seconds']=metrics['elapsed_seconds']-existing_source['previous_elapsed_seconds']
            metrics['preserved_source_output_bytes']=existing_source['previous_output_bytes']
            metrics['combined_source_and_recovery_output_bytes']=metrics['observed_output_bytes']+existing_source['previous_output_bytes']
            metrics['combined_peak_sampled_process_tree_rss_bytes']=max(metrics['peak_sampled_process_tree_rss_bytes'],existing_source['previous_sampled_peak_rss_bytes'])
            metrics['combined_peak_observed_output_bytes']=max(existing_source['previous_peak_observed_output_bytes'],
                                                              metrics['peak_observed_output_bytes']+existing_source['previous_output_bytes'])
        state['stages_attempted']=monitor.executions;save_json(output/'run_manifest.json',state);monitor.restore_signals()
    return state


def main(argv=None):
    started=time.monotonic();args=parser().parse_args(argv)
    try:
        requested=request(args);identity,bindings=bridge_identity();bound_bundle();installed=verify_environment()
        require(sum(bool(value) for value in (args.resume_source,args.resume_chain,args.resume_detector))<=1,'choose one source/chain/detector continuation mode')
        output=safe_output(args.output,protected_paths());resources=availability(output,requested)
        existing_source=preserved_detector(args.resume_detector,requested,installed) if args.resume_detector else preserved_chain(args.resume_chain,requested,installed) if args.resume_chain else preserved_source(args.resume_source,requested,installed) if args.resume_source else None
        require(time.monotonic()-started<requested['max_hours']*3600,'BLOCKED_RESOURCES: preflight exceeded wall cap')
        output.mkdir(parents=True,exist_ok=False)
        plan=prepare(output,requested,identity,bindings,installed,resources)
        if existing_source:
            plan['preserved_source_recovery']=existing_source;plan['MG5_execution_mode']='NEVER_INVOKE_MG5_REUSE_ORIGINAL_SOURCE'
            save_json(output/'execution_plan.json',plan)
        if args.dry_run:
            plan['status']='PASS_TEXT_ONLY_DRY_RUN';save_json(output/'execution_plan.json',plan)
            print(json.dumps({'status':plan['status'],'output':str(output),'new_events_generated':0},indent=2));return 0
        state=execute(output,requested,plan,installed,started,existing_source)
        print(json.dumps({'status':state['status'],'output':str(output),'MG5_events_generated':state['MG5_events_generated'],
            'HepMC_validated_events':state['HepMC_validated_events'],'Delphes_ROOT_entries':state['Delphes_ROOT_entries']},indent=2))
        return 0 if state['status'].startswith('PASS_') else 2
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
        print('BLOCKED_OR_FAILED: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
