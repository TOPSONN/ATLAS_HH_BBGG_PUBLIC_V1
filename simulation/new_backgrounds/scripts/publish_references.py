#!/usr/bin/env python3
"""Prepare selected genuine references locally; never generate, stage or push.

All actual full1000 gates, source identities, selected-prefix correspondence,
privacy and byte budgets must pass before creating a reference directory.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO))
from simulation.new_backgrounds.scripts.validate_references import (ASSETS,DATA_SIDECARS,HASH,MAX_FILE,MAX_PACKAGE,MAX_TEXT,
    PREFIX,PROCESSES,hepmc_blocks,load_json_bytes,path_key,require,scan_private,sha,validate_files)

RETAINED_MANIFEST_SHA='494a1cc13ee5f0c6a271946b61ce8c1ab5e414a098c73aa1f5e4f5c7f7734dd7'
RETAINED_BRIDGE_SHA='fd9bec3eb7ae1022ff31361f946769f528d41c0093a18aa29835824a91545b67'
RETAINED_FULL_HEPMC_SHA='ae2055e5738ea228b38927c4b4008b6cd2e3ba7acecb28276dd0acd4c38cd0f5'


def encoded(value):return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')


def file_sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()


def inside_file(path,run,cap=None):
    path=Path(path)
    require(path.is_absolute() and path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(run),'Selected original artifact missing/unsafe/escapes actual run')
    for parent in path.parents:
        if parent==run:break
        require(not parent.is_symlink(),'Original artifact symlink ancestor forbidden')
    if cap is not None:require(path.stat().st_size<cap,'Selected original exceeds publication size budget')
    return path


def load_local(path,run):return load_json_bytes(inside_file(path,run,64*1024**2).read_bytes(),max_bytes=64*1024**2)


def public_projection(value,run,repo,labels):
    """Preserve numbers/hashes; replace known exact private paths with roles."""
    def text(original):
        if original in labels:return labels[original]
        if original.startswith(str(run).replace('\\','/')+'/'):return 'run:'+original[len(str(run))+1:]
        if original.startswith(str(repo).replace('\\','/')+'/'):return 'repo:'+original[len(str(repo))+1:]
        # Paths in scalar settings or diagnostics must be known artifacts.
        result=original
        for old,label in sorted(labels.items(),key=lambda item:len(item[0]),reverse=True):result=result.replace(old,label)
        scan_private(result.encode('utf-8'),'projected original receipt string')
        require(not result.startswith('/') and not (len(result)>2 and result[1]==':' and result[2] in '/\\'),
                'Unknown absolute private artifact string in receipt')
        return result
    if isinstance(value,dict):return {text(key):public_projection(child,run,repo,labels) for key,child in value.items()}
    if isinstance(value,list):return [public_projection(child,run,repo,labels) for child in value]
    if isinstance(value,str):return text(value)
    return value


def full_prefix(full,count):
    """Read all1000 original blocks and retain exact requested block bytes."""
    header=[];selected=[];blocks=[];block=[];ended=False
    with full.open('rb') as stream:
        for line in stream:
            require(len(line)<=8*1024**2 and line.endswith(b'\n') and b'\r' not in line,'Invalid bounded native full-shower ASCII line')
            if line.startswith(b'E '):
                require(not ended,'Full-shower event after trailer')
                if block:
                    content=b''.join(block);blocks.append(sha(content))
                    if len(blocks)<=count:selected.append(content)
                block=[line]
            elif line==b'HepMC::Asciiv3-END_EVENT_LISTING\n':
                require(not ended and block,'Missing/duplicate full-shower trailer')
                content=b''.join(block);blocks.append(sha(content))
                if len(blocks)<=count:selected.append(content)
                block=[];ended=True
            elif ended:require(not line.strip(),'Data after full-shower trailer')
            elif block:block.append(line)
            else:header.append(line)
            require(len(blocks)<=1000,'Excessive full-shower original records')
    require(ended and len(blocks)==1000 and len(selected)==count,'Actual complete full1000 shower required')
    return b''.join(header+selected)+b'HepMC::Asciiv3-END_EVENT_LISTING\n',blocks


def first_rows(path,count):
    selected=[];total=0
    with path.open('rb') as stream:
        for line in stream:
            require(line.endswith(b'\n') and len(line)<=MAX_TEXT and line.strip(),'Invalid bounded original event-ledger line')
            total+=1;require(total<=1000,'Excessive original ledger rows')
            if total<=count:selected.append(line)
    require(total==1000,'Complete original1000 event ledger required')
    return b''.join(selected)


def retained_shower_inputs(descriptor,run,request):
    """Allow only individually bound files of the known completed B04 shower."""
    require(isinstance(descriptor,dict) and
        descriptor.get('status')=='SOURCE_BOUND_COMPLETED_SHOWER_REUSE_ZERO_PRODUCER_CALLS' and
        descriptor.get('Pythia_invocations_in_continuation')==0 and descriptor.get('new_source_events')==0,
        'Invalid completed-shower non-generating reuse scope')
    candidate=Path(descriptor['original_run'])
    require(candidate.is_absolute() and candidate.is_dir() and not candidate.is_symlink(),'Unsafe retained shower root')
    original=candidate.resolve()
    require(original!=run and not original.is_relative_to(run) and not run.is_relative_to(original),
        'Retained shower and fresh detector output overlap')
    manifest_path=inside_file(descriptor['manifest_path'],original)
    require(manifest_path==original/'run_manifest.json' and descriptor['manifest_sha256']==RETAINED_MANIFEST_SHA and
        file_sha(manifest_path)==RETAINED_MANIFEST_SHA and descriptor['full_shower_sha256']==RETAINED_FULL_HEPMC_SHA,
        'Only the exact known B04 detector stop permits retained shower publication')
    old=load_local(manifest_path,original)
    require(old['status']=='PARTIAL_PHYSICAL_CHAIN' and old['failure']=='FAILED_STAGE: independent_native_root_zh_100; retained actual log' and
        old['bridge_sha256']==RETAINED_BRIDGE_SHA and old['request']['process']==request['process']=='zh' and
        all(old['request'][key]==request[key] for key in ('events','seed','energy_gev')) and
        Path(old['request']['output']).resolve()==original and
        all(old[key]==1000 for key in ('MG5_events_generated','Pythia_events_attempted','Pythia_events_written','HepMC_validated_events')) and
        old['Delphes_ROOT_entries']==0,'Retained shower origin is a different physical attempt or failure')
    require(not any(row['stage']=='delphes_zh_1000' for row in old['stages_attempted']),
        'Original full detector was already attempted')
    bindings=descriptor['files_sha256'];allowed={};earlier_checked={}
    require(isinstance(bindings,dict) and 0<len(bindings)<=512,'Unbounded or absent retained artifact hashes')
    prior=old['preserved_source_recovery'];earlier={}
    for key in ('previous_chain_bindings','reused_prefix10_files'):earlier.update(prior.get(key,{}))
    reservation=prior['downstream_global_reservation'];earlier[reservation['path']]=reservation['sha256']
    for name,digest in bindings.items():
        require(isinstance(digest,str) and HASH.fullmatch(digest),'Invalid retained artifact SHA256')
        if name in earlier:
            require(digest==earlier[name],'Earlier provenance differs from immutable closed manifest')
            path=Path(name)
            require(path.is_absolute() and path.is_file() and not path.is_symlink() and
                path.stat().st_size<64*1024**2 and file_sha(path)==digest,'Earlier immutable authority or prefix changed')
            require(not any(parent.is_symlink() for parent in path.parents),'Earlier provenance has symlink ancestor')
            earlier_checked[path]=(digest,path.stat().st_size)
            continue
        path=inside_file(name,original);relative=path.relative_to(original)
        require(relative.parts[0] in ('pythia','validation','native_build','delphes') or
            relative.as_posix() in ('run_manifest.json','execution_plan.json','authorization.json'),
            'Unrelated external file in retained shower allowlist')
        require(path.resolve() not in allowed and file_sha(path)==digest,'Retained measured artifact changed')
        allowed[path.resolve()]=digest
    require(set(earlier).issubset(bindings),'Earlier source/chain one-attempt provenance omitted')
    for name in ('run_manifest.json','execution_plan.json','authorization.json','validation/weight_and_BR_ledger.json'):
        require((original/name).resolve() in allowed,'Missing retained immutable receipt binding')
    oldplan=load_local(original/'execution_plan.json',original)
    require(oldplan['request']==old['request'] and oldplan['bridge_sha256']==RETAINED_BRIDGE_SHA,
        'Retained execution plan differs from closed manifest')
    source_sha=old['preserved_source_recovery']['source_sha256']
    for stage,count in (('prefix10',10),('prefix100',100),('full1000',1000)):
        folder=original/'pythia'/stage;receipt=old['stages'][stage]
        summary=load_local(folder/'run_summary.json',original);reader=load_local(folder/'background_hepmc_validation.json',original)
        require(receipt['status']=='PASS_RAW_SHOWER_AND_HEPMC_RECORDS' and summary==receipt['run_summary'] and
            reader==receipt['reader_report'] and reader['validation_status']=='PASS_BACKGROUND_HEPMC_RECORDS' and
            reader['N_readback']==reader['N_passed_validation']==count and reader['N_failed_validation']==0 and
            reader['source_total_events']==1000 and reader['source_file_sha256']==source_sha and
            all(summary[key]==count for key in ('N_input','N_attempted','N_source_identity_verified','N_shower_success','N_written')) and
            summary['N_shower_failed']==summary['N_source_identity_failed']==0,
            'Retained actual shower/ReaderAscii receipt incomplete')
        for name,key in (('shower.hepmc3','decompressed_file_sha256'),('input_event_index.dat','input_index_sha256'),
            ('background_truth_index.dat','truth_index_sha256'),('generic_physics_validation.json','generic_physics_report_sha256'),
            ('decay_tables_initialized.json','actual_initialized_decay_table_sha256')):
            require(allowed.get((folder/name).resolve())==reader[key],'Retained native QA binds different measured bytes')
        for name in ('run_summary.json','background_hepmc_validation.json','hepmc_ancestry.jsonl','event_ledger.jsonl',
            'decay_tables_original_preinit.json','decay_tables_inclusive_initialized.json','effective_settings.cmnd',
            'inclusive_initialized_settings.cmnd'):
            require((folder/name).resolve() in allowed,'Missing retained required source/decay evidence')
    require(allowed[(original/'pythia/full1000/shower.hepmc3').resolve()]==RETAINED_FULL_HEPMC_SHA,
        'Retained full1000 is not the reviewed genuine shower')
    ledger=load_local(original/'validation/weight_and_BR_ledger.json',original)
    require(ledger==old['weight_and_BR_ledger'] and ledger['status']=='PASS_MODEL_BR_WEIGHT_CLOSURE' and
        ledger['weight_closure']=='PASS' and ledger['factor_applications']==1 and not ledger['Z_BR_reapplied'],
        'Retained complete weight/decay closure differs')
    provenance={key:descriptor[key] for key in ('status','manifest_sha256','full_shower_sha256',
        'Pythia_invocations_in_continuation','new_source_events')}
    provenance['original_bridge_sha256']=RETAINED_BRIDGE_SHA
    provenance['original_measured_files_sha256']={path.relative_to(original).as_posix():digest for path,digest in allowed.items()}
    previous=Path(prior['previous_chain_run'])
    provenance['earlier_provenance_files_sha256']={
        ('prior-chain:'+path.relative_to(previous).as_posix() if path.is_relative_to(previous) else
         'prior-one-attempt-registry:'+path.name):digest for path,(digest,_) in earlier_checked.items()}
    return original,allowed,provenance,earlier_checked


def installed_xml_labels(build):
    """Project only the verified installed XML directory into a public role."""
    require(build.get('status')=='PASS_BUILD_AND_METHODS_ONLY' and
        build.get('weight_source_commit')=='83a5c9986f30746cfb390435a9b10ac55a758fca',
        'Actual retained Pythia build/source identity required for XML projection')
    fingerprints=build.get('installation_file_sha256',{})
    require(isinstance(fingerprints,dict) and fingerprints,'Missing bound installed XML fingerprints')
    roots={Path(name).parent for name in fingerprints if Path(name).name=='ParticleData.xml'}
    require(len(roots)==1,'Missing or ambiguous bound installed ParticleData XML directory')
    root=roots.pop();require(root.is_absolute() and root.is_dir() and not root.is_symlink(),'Unsafe bound installed XML directory')
    checked={}
    for name,digest in fingerprints.items():
        path=Path(name)
        if path.parent!=root:continue
        require(path.is_file() and not path.is_symlink() and path.resolve().parent==root.resolve() and
            isinstance(digest,str) and HASH.fullmatch(digest) and file_sha(path)==digest,
            'Bound installed XML bytes changed before public path projection')
        checked[path]=(digest,path.stat().st_size)
    require(checked,'No actual installed XML files verified')
    logical='installed:Pythia8.317_XML'
    return {str(root):logical,str(root).rstrip('/')+'/':logical+'/'},checked


def prepare_plan(run_dir,repo=REPO):
    run=Path(run_dir).expanduser().resolve();repo=Path(repo).resolve()
    require(run.is_dir() and not run.is_symlink(),'Actual preserved run directory required')
    state=load_local(run/'run_manifest.json',run)
    require(state.get('physical_generation_completed') is True and state.get('status') in
            ('PASS_FULL_CHAIN_MODEL_SCOPE','PASS_RAW_FULL_CHAIN_EXCLUSIVE_NORMALIZATION_BLOCKED'),
            'Only actual completed full1000 physical chains may publish selected references')
    require(all(type(state.get(key)) is int and state[key]==1000 for key in
        ('MG5_events_generated','Pythia_events_attempted','Pythia_events_written','HepMC_validated_events','Delphes_ROOT_entries')),
        'Actual local target1000 counters not all met')
    process=state['request']['process'];require(process in PROCESSES,'Unsupported physical source profile')
    recovery=state.get('preserved_source_recovery');recovery_allowed={};recovery_provenance=None
    recovery_run=None;retained_run=None;retained_allowed={};retained_provenance=None;earlier_checked={}
    if recovery:
        original=Path(recovery['run']).resolve();require(original!=run and not original.is_relative_to(run) and not run.is_relative_to(original),'Recovery source/output must remain distinct')
        for name,digest in (('manifest_path','manifest_sha256'),('plan_path','plan_sha256'),('result_path','result_sha256'),
                ('source_path','source_sha256'),('original_authorization_path','original_authorization_sha256')):
            path=inside_file(recovery[name],original);require(file_sha(path)==recovery[digest],'Original recovery provenance changed');recovery_allowed[path.resolve()]=recovery[digest]
        old=load_local(recovery['manifest_path'],original);oldplan=load_local(recovery['plan_path'],original)
        oldresult=load_local(recovery['result_path'],original);oldauth=load_local(recovery['original_authorization_path'],original)
        require(old['status']=='PARTIAL_PHYSICAL_CHAIN' and old['failure']=='Actual complete run card differs from reviewed request' and old['MG5_events_generated']==1000 and all(old.get(key)==0 for key in ('Pythia_events_attempted','Pythia_events_written','HepMC_validated_events','Delphes_ROOT_entries')),'Recovery did not originate from diagnosed pre-shower representation stop')
        require(oldplan['request']==old['request'] and all(old['request'][key]==state['request'][key] for key in ('process','events','seed','energy_gev')) and recovery['MG5_invocations_in_recovery']==0 and state['MG5_events_generated_in_this_attempt']==0 and state['MG5_events_reused']==1000,'Recovery introduces source replacement/double counting')
        require(oldauth['status']=='AUTHORIZED_TASK_ATTACHMENT' and oldauth['authorization_command']=='PHASE6G_THREE_NEW_BACKGROUNDS_FULL_CHAIN_1K_V1' and oldauth['attachment_sha256']=='65b25230b2c50c1c4c7bb253887a8934268732dfca8be9b05eb8aed18fd22d91','Preserved source lacked actual task authority')
        for group in (oldresult['artifacts'],oldresult['prepared_cards'],oldresult['cards']):
            for row in group.values():
                path=inside_file(row['path'],original);require(file_sha(path)==row['sha256'],'Original recovered MG artifact changed');recovery_allowed[path.resolve()]=row['sha256']
        require(oldresult['artifacts']['lhe_gz']['sha256']==recovery['source_sha256'],'Original recovery LHE identity mismatch')
        recovery_provenance={key:recovery[key] for key in ('manifest_sha256','plan_sha256','result_sha256','source_sha256','original_authorization_sha256','original_bridge_sha256','MG5_invocations_in_recovery')}
        recovery_run=original
        if recovery.get('retained_shower'):
            retained_run,retained_allowed,retained_provenance,earlier_checked=retained_shower_inputs(recovery['retained_shower'],run,state['request'])
            require(state['Pythia_events_attempted_in_this_attempt']==0 and state['Pythia_events_reused']==1000,
                'Detector-only continuation introduces shower generation/double counting')
    shower_dir=(retained_run if retained_run is not None else run)/'pythia/full1000'
    plan=load_local(run/'execution_plan.json',run);mg=load_local(run/'validation/mg5_execution.json',run)
    source=load_local(run/'validation/lhe_validation.json',run);hmc=load_local(shower_dir/'background_hepmc_validation.json',retained_run or run)
    full=load_local(run/'delphes/full1000/delphes_execution.json',run);prefix=load_local(run/'delphes/prefix100/delphes_execution.json',run)
    ledger=load_local(run/'validation/weight_and_BR_ledger.json',run);stats=load_local(run/'validation/cutflow_statistics.json',run)
    require(source['status']=='PASS_LHE_RECORDS' and source['actual_events']==source['events_valid']==source['events_assessed']==1000 and source['events_invalid']==source['events_not_assessed']==0,'Actual independent complete LHE PASS required')
    require(hmc['validation_status']=='PASS_BACKGROUND_HEPMC_RECORDS' and hmc['N_readback']==hmc['N_passed_validation']==1000 and hmc['N_failed_validation']==0,'Actual full1000 native ReaderAscii PASS required')
    for report,count in ((full,1000),(prefix,100)):
        require(report['status']=='PASS_NATIVE_BACKGROUND_RECORD_READBACK' and report['ROOT_entries']==report['processed']==count and report['source_events']==1000 and report['invalid']==report['skipped']==0,'Actual full1000 and prefix100 native ROOT PASS required')
    require(stats['status']=='PASS_INDEPENDENT_FULL1000_NUMERICAL_READBACK' and stats['source_events']==1000,'Actual full1000 numerical/statistical PASS required')
    require(ledger['weight_closure']=='PASS','Actual complete source/decay weight closure required for selected full-chain publication')
    require(source['profile']==mg['profile']==PROCESSES[process][1] and mg['request']['events']==1000 and mg['retry_or_event_replacement_performed'] is False,'Physical original source/profile/replacement convention mismatch')
    targets={};checked=dict(earlier_checked);labels={}
    if recovery:
        labels[str(recovery_run)]='run:ORIGINAL_PRESERVED_SOURCE_RUN'
        for path,digest in recovery_allowed.items():
            labels[str(path)]='original-MG-artifact:'+path.relative_to(recovery_run).as_posix();checked[path]=(digest,path.stat().st_size)
    if retained_run is not None:
        labels[str(retained_run)]='run:ORIGINAL_COMPLETED_SHOWER_RUN'
        for path,digest in retained_allowed.items():
            labels[str(path)]='retained-shower-artifact:'+path.relative_to(retained_run).as_posix();checked[path]=(digest,path.stat().st_size)
    def verify(path,expected=None,cap=None):
        path=Path(path)
        if path.resolve() in recovery_allowed:
            path=inside_file(path,recovery_run,cap);require(file_sha(path)==recovery_allowed[path.resolve()],'Bound recovered MG source artifact changed')
        elif path.resolve() in retained_allowed:
            path=inside_file(path,retained_run,cap);require(file_sha(path)==retained_allowed[path.resolve()],'Bound retained shower artifact changed')
        else:path=inside_file(path,run,cap)
        digest=file_sha(path)
        require(expected is None or digest==expected,'Preserved original artifact changed since actual QA: '+path.name)
        checked[path]=(digest,path.stat().st_size);return path
    def add_bytes(name,data,role,category='TEXT',events=None,provenance='DERIVED_BOUNDED_PUBLIC_RECEIPT'):
        path_key(name);require(name not in targets and type(data) is bytes,'Duplicate/invalid selected reference target')
        require(0<len(data)<(MAX_FILE if category=='ASSET' or name in DATA_SIDECARS else MAX_TEXT),'Selected reference file exceeds size policy: '+name)
        if category=='TEXT':scan_private(data,name)
        targets[name]={'data':data,'role':role,'category':category,'events':events,'full_source_events':1000,
            'provenance':provenance,'sha256':sha(data),'bytes':len(data)}
    def exact(path,name,role,category='TEXT',events=None,expected=None):
        path=verify(path,expected,MAX_FILE if category=='ASSET' or name in DATA_SIDECARS else MAX_TEXT);labels[str(path)]='artifact:'+role
        data=path.read_bytes();scan_private(data,name) if not name.endswith('.gz') else None
        add_bytes(name,data,role,category,events,'EXACT_ORIGINAL_ASSET_BYTES' if category=='ASSET' else 'EXACT_ORIGINAL_TEXT_BYTES')
    lhs=verify(mg['lhe_path'],source['source_file_sha256'],MAX_FILE)
    full_hepmc=verify(shower_dir/'shower.hepmc3',hmc['decompressed_file_sha256'])
    verify(full['root_path'],full['root_sha256']);verify(full['reco_events_path'],full['derived_files_sha256']['reco_events.jsonl'])
    verify(full['cutflow_path'],full['derived_files_sha256']['cutflow.csv'])
    verify(shower_dir/'input_event_index.dat',hmc['input_index_sha256'])
    verify(shower_dir/'background_truth_index.dat',hmc['truth_index_sha256'])
    require(stats['native_root_sha256']==full['root_sha256'] and stats['reco_events_sha256']==full['derived_files_sha256']['reco_events.jsonl'] and stats['cutflow_sha256']==full['derived_files_sha256']['cutflow.csv'],'Actual numerical receipt binds different full1000 detector bytes')
    raw,block_hashes=full_prefix(full_hepmc,100)
    prefix_input=verify(prefix['inputs']['hepmc_path'])
    require(prefix_input.read_bytes()==raw and prefix['source_full_shower_sha256']==hmc['decompressed_file_sha256'] and prefix['subset_origin']=='FIRST_N_EXACT_RECORDS_OF_VALIDATED_FULL1000_SHOWER','Selected100 HMC is not exact validated full1000 prefix')
    exact(lhs,'mg5/reference_1000.lhe.gz','MG5_FULL1000','ASSET',1000,source['source_file_sha256'])
    add_bytes('pythia8/reference_100.hepmc3.gz',gzip.compress(raw,mtime=0),'HEPMC_PREFIX100_FROM_FULL1000','ASSET',100,'GZIP_CONTAINER_OF_EXACT_VALIDATED_FULL1000_FIRST100_ASCII_RECORDS')
    exact(prefix['root_path'],'delphes/detector_100.root','DELPHES_PREFIX100','ASSET',100,prefix['root_sha256'])
    exact(prefix['inputs']['input_index_path'],'pythia8/input_event_index.dat','NATIVE_SOURCE_AND_PARTICLE_INDEX100',expected=prefix['input_index_sha256'])
    exact(prefix['inputs']['truth_index_path'],'pythia8/background_truth_index.dat','NATIVE_ACTUAL_ANCESTRY_TRUTH100',expected=prefix['truth_index_sha256'])
    exact(run/'delphes/prefix100/detector_card.tcl','delphes/detector_card.tcl','ACTUAL_DETECTOR_CARD',expected=prefix['card_sha256'])
    exact(prefix['reco_events_path'],'delphes/reco_events_100.jsonl','ACTUAL_RECONSTRUCTED_ROWS100',expected=prefix['derived_files_sha256']['reco_events.jsonl'])
    exact(prefix['cutflow_path'],'delphes/cutflow_100.csv','ACTUAL_NATIVE_PREFIX100_CUTFLOW',expected=prefix['derived_files_sha256']['cutflow.csv'])
    for key,name in {'process_card':'process_card.mg5','run_card':'run_card.dat','param_card':'param_card.dat'}.items():
        actual=source['actual_cards'][key].encode();require(sha(actual)==source['card_hashes'][key],'Actual header card hash mismatch');add_bytes('mg5/'+name,actual,'ACTUAL_LHE_HEADER_'+key.upper(),provenance='EXACT_VALIDATED_ORIGINAL_LHE_HEADER_CARD_TEXT')
    banner=verify(mg['banner_path'],mg['artifacts']['banner']['sha256'],MAX_TEXT)
    # The full MG banner is selected only when its original bytes are public-safe.
    exact(banner,'mg5/banner.txt','ACTUAL_GENERATOR_BANNER',expected=mg['artifacts']['banner']['sha256'])
    for name,role in [('hepmc_ancestry.jsonl','ACTUAL_HEPMC_ANCESTRY100'),('event_ledger.jsonl','ACTUAL_INPUT_ATTEMPT_LEDGER100')]:
        path=verify(shower_dir/name);add_bytes('pythia8/'+name.replace('.jsonl','_100.jsonl'),first_rows(path,100),role,provenance='EXACT_FIRST100_LINES_OF_ACTUAL_FULL1000_LEDGER')
    for name in ('decay_tables_original_preinit.json','decay_tables_inclusive_initialized.json','decay_tables_initialized.json'):
        exact(shower_dir/name,'pythia8/'+name,'ACTUAL_'+name.upper())
    labels[str(run)]='run:ACTUAL_PRESERVED_RUN';labels[str(repo)]='repo:ATLAS_HH_BBGG_PUBLIC_V1'
    for label,path in (('ORIGINAL_FULL1000_PLAIN_LHE',run/'validation/original_full1000.lhe'),('ORIGINAL_SOURCE_INDEX',run/'validation/source_events.dat')):labels[str(path)]='artifact:'+label
    for key,path in state['stages']['native_build']['weight_source_sha256'].items():labels[key]='retained-weight-source:'+Path(key).name
    xml_labels,xml_checked=installed_xml_labels(state['stages']['native_build'])
    labels.update(xml_labels);checked.update(xml_checked)
    def receipt(value,name,original_path=None):
        projection=public_projection(value,run,repo,labels)
        if original_path is not None:
            original_path=verify(original_path);projection={**projection,'original_receipt_sha256':checked[original_path][0],
                'public_projection_scope':'Numbers/hashes unchanged; known private artifact locations replaced by logical roles; native QA not reexecuted'}
        add_bytes('validation/'+name+'.json',encoded(projection),'ACTUAL_'+name.upper())
    fields=('schema_version','status','profile','source_total_events','actual_events','events_assessed','events_valid','events_invalid','events_not_assessed',
        'cross_section_pb','cross_section_uncertainty_pb','source_file_sha256','decompressed_file_sha256','idwtup','beam_energies_gev','seed','card_hashes',
        'maximum_closure_residual_gev','maximum_mass_shell_residual_gev2','weights','source_included_decay_ids','missing_decay_ids')
    compact={key:source[key] for key in fields if key in source}
    compact['source_events']=[{key:event[key] for key in ('source_event_index','source_event_content_hash','nominal_generator_weight','original_resonance_and_bottom_ids')} for event in source['source_events']]
    receipt(compact,'lhe_full1000',run/'validation/lhe_validation.json')
    receipt(hmc,'hepmc_full1000',shower_dir/'background_hepmc_validation.json')
    receipt(full,'root_full1000',run/'delphes/full1000/delphes_execution.json');receipt(prefix,'root_prefix100',run/'delphes/prefix100/delphes_execution.json')
    receipt(ledger,'weight_and_BR_ledger',run/'validation/weight_and_BR_ledger.json');receipt(stats,'cutflow_statistics',run/'validation/cutflow_statistics.json')
    fullfields=('schema_version','task','status','physical_generation_completed','campaign_id','request','bridge_sha256','MG5_events_generated',
        'MG5_events_generated_in_this_attempt','MG5_events_reused','Pythia_events_attempted','Pythia_events_attempted_in_this_attempt','Pythia_events_reused','Pythia_events_written','HepMC_validated_events','Delphes_ROOT_entries','source_cross_section_pb','source_integration_uncertainty_pb','interpretation_gates')
    compact_chain={key:state[key] for key in fullfields if key in state}
    if recovery_provenance is not None:compact_chain['preserved_source_recovery']=recovery_provenance
    if retained_provenance is not None:compact_chain['retained_completed_shower']=retained_provenance
    receipt(compact_chain,'full_chain',run/'run_manifest.json')
    provenance={'schema_version':1,'status':'BOUND_ACTUAL_GENERATOR_AND_SOURCE_PROVENANCE',
        'source_identity':{key:mg['source_identity'][key] for key in ('version','source_commit','source_tag','source_url')},
        'source_original_sha256':source['source_file_sha256'],'original_source_denominator':1000,
        'original_MG_authorization_sha256':mg['authorization_receipt']['sha256'],
        'actual_MG_generation_log_sha256':mg['artifacts']['run_log']['sha256'],
        'actual_tree_amplitude_receipt_sha256':mg['amplitude_validation']['sha256'],
        'actual_cards_sha256':source['card_hashes'],'retry_or_replacement_events':False,
        'new_MG_events_in_this_attempt':state.get('MG5_events_generated_in_this_attempt',1000),
        'original_MG_events_reused':state.get('MG5_events_reused',0),'source_recovery':recovery_provenance,
        'new_Pythia_events_in_this_attempt':state.get('Pythia_events_attempted_in_this_attempt'),
        'original_Pythia_events_reused':state.get('Pythia_events_reused',0),'retained_completed_shower':retained_provenance}
    receipt(provenance,'source_provenance')
    generator=repo/'simulation/new_backgrounds/config/generator_contract.json';require(generator.is_file() and file_sha(generator)==mg['background_generator_contract_sha256'],'Actual generator physics contract changed')
    add_bytes('validation/generator_contract.json',generator.read_bytes(),'ACTUAL_BOUND_GENERATOR_PHYSICS_CONTRACT',provenance='EXACT_SOURCE_CONTRACT_BYTES')
    summary=load_local(shower_dir/'run_summary.json',retained_run or run);receipt(summary,'pythia_full1000_summary',shower_dir/'run_summary.json')
    for filename in ('effective_settings.cmnd','inclusive_initialized_settings.cmnd'):
        path=verify(shower_dir/filename,cap=MAX_TEXT);text=path.read_text(encoding='utf-8')
        for old,label in sorted(labels.items(),key=lambda item:len(item[0]),reverse=True):text=text.replace(old,label)
        scan_private(text.encode(),filename);add_bytes('pythia8/'+filename,text.encode(),'ACTUAL_SETTINGS_LOGICAL_PATH_PROJECTION',provenance='PUBLIC_PATH_PROJECTION_OF_ACTUAL_SETTINGS; ORIGINAL_SHA256='+checked[path][0])
    total=sum(item['bytes'] for item in targets.values());require(total<MAX_PACKAGE,'Selected references exceed combined60MiB process budget; large assets remain local')
    listed=[{key:item[key] for key in ('role','category','events','full_source_events','provenance','sha256','bytes')}|{'path':name} for name,item in sorted(targets.items())]
    manifest={'schema_version':1,'status':'PASS_VALIDATED_REFERENCE_BUNDLE','process':process,'profile':PROCESSES[process][1],
        'actual_full_source_events':1000,'selected_HepMC_events':100,'selected_ROOT_entries':100,'seeds':plan['seeds'],
        'cross_section_pb':source['cross_section_pb'],'integration_uncertainty_pb':source['cross_section_uncertainty_pb'],
        'full_source_identities':{'lhe_gz_sha256':source['source_file_sha256'],'lhe_plain_sha256':source['decompressed_file_sha256'],
            'hepmc_plain_sha256':hmc['decompressed_file_sha256'],'root_sha256':full['root_sha256']},
        'reference_hepmc_plain_sha256':sha(raw),'reference_hepmc_block_sha256':block_hashes[:100],
        'physics_scope':'REAL_SELECTED_LO_FULL1000_STREAM; references100 are a subset, not independent new statistics',
        'normalization_scope':ledger['scope'],'detector_label':'FAST_SIM_ATLAS_LIKE_NOT_OFFICIAL_ATLAS','full1000_local_native_gates':'PASS',
        'calibrated_photon_fake_rate':'BLOCKED','overlap_matching_scheme':'BLOCKED','official_detector_BR_calibration':'BLOCKED',
        'physical_assets_rewritten':False,'HepMC_container_compression_only':True,'new_events_generated_by_publisher':0,
        'native_QA_reexecution_during_publication':False,'Git_staged':False,'Git_pushed':False,
        'limits':{'per_file_strictly_less_than_bytes':MAX_FILE,'per_process_strictly_less_than_bytes':MAX_PACKAGE},'files':listed}
    bundle=PREFIX+PROCESSES[process][0]+'/'
    blobs={bundle+name:item['data'] for name,item in targets.items()};blobs[bundle+'manifest.json']=encoded(manifest)
    report=validate_files(blobs)
    # Recheck original measured inputs after the complete portable preflight.
    for path,(digest,size) in checked.items():require(path.stat().st_size==size and file_sha(path)==digest,'Original preserved input changed during selection')
    return {'manifest':manifest,'blobs':blobs,'validation':report,'checked_originals':checked,'destination':repo/bundle}


def publish_references(run_dir,repo=REPO):
    plan=prepare_plan(run_dir,repo);target=plan['destination'];repo=Path(repo).resolve()
    require(not target.exists() and not target.is_symlink(),'Selected process reference directory already exists; preserve it')
    for parent in target.parents:require(not parent.is_symlink(),'Symlink publication ancestor forbidden')
    require(target.is_relative_to(repo/PREFIX),'Publication target must remain in selected reference tree')
    target.mkdir(parents=True,exist_ok=False)
    written=[]
    try:
        for relative,data in plan['blobs'].items():
            path=repo/relative;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(data)
            require(sha(path.read_bytes())==sha(data),'Selected bytes changed while copying');written.append(relative)
        for path,(digest,size) in plan['checked_originals'].items():require(path.stat().st_size==size and file_sha(path)==digest,'Original source changed during selected copying')
        readback={relative:(repo/relative).read_bytes() for relative in plan['blobs']};validate_files(readback)
        return {'schema_version':1,'status':'PASS_SELECTED_REFERENCES_PREPARED_NO_GIT_ACTION','process':plan['manifest']['process'],
            'destination':str(target),'manifest_sha256':sha(readback[target.relative_to(repo).as_posix()+'/manifest.json']),
            'files':len(readback),'bytes':sum(map(len,readback.values())),'portable_validation':plan['validation'],
            'new_events_generated':0,'Git_staged':False,'Git_pushed':False}
    except BaseException:
        failure=encoded({'status':'PARTIAL_REFERENCE_PREPARATION_NOT_PUBLISHABLE','written_repository_relative_paths':written,'new_events_generated':0})
        with (target/'PREPARATION_FAILED.json').open('xb') as stream:stream.write(failure)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--repo',type=Path,default=REPO);args=parser.parse_args()
    print(json.dumps(publish_references(args.run,args.repo),indent=2,allow_nan=False));return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,StopIteration) as error:
        print('BLOCKED_SELECTED_REFERENCE_PUBLICATION: '+str(error),file=sys.stderr);raise SystemExit(2)
