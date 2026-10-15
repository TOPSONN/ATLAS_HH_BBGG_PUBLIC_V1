#!/usr/bin/env python3
"""Guarded future stage API. Actual execution requires the root authorization callback.

Importing this module, validating receipts or rendering DAT bytes never processes
events. No standalone physical-execution CLI is provided.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import time
import uuid

_spec=importlib.util.spec_from_file_location('phase6g_build_helpers',Path(__file__).with_name('build_stage.py'))
_build=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_build)
digest,require,source_bindings=_build.digest,_build.require,_build.source_bindings

COMMAND = 'PHASE6G_THREE_NEW_BACKGROUNDS_FULL_CHAIN_1K_V1'
BASE = '05cff9a5d991ba6782b339bc41932ae4da296d8c'
HASH = re.compile(r'[0-9a-f]{64}\Z')
REUSED_PREFIX10_HEPMC_SHA256 = 'ad51a02e982ae83368768e84569f20093de304714c54e7496aadc12a438f9e00'
REUSED_SHOWER_FILES = (
    'shower.hepmc3','run_summary.json','event_ledger.jsonl','particle_diagnostics.jsonl',
    'decay_tables_original_preinit.json','decay_tables_before_init.json',
    'decay_tables_inclusive_initialized.json','decay_tables_initialized.json',
    'original_particle_data.xml','inclusive_initialized_particle_data.xml','effective_particle_data.xml',
    'inclusive_initialized_settings.cmnd','effective_settings.cmnd',
)


def load_json(path):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=32*1024**2, 'Invalid bounded JSON file')
    def pairs(values):
        result={}
        for key,value in values:
            require(key not in result, 'Duplicate JSON key')
            result[key]=value
        return result
    def number(value):
        parsed=float(value)
        require(math.isfinite(parsed),'Nonfinite JSON number')
        return parsed
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_float=number,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def positive_budget(value, maximum):
    require(type(value) in (int,float) and math.isfinite(value) and 0<value<=maximum, 'Invalid resource ceiling')


def check_live_job(value,live,now=None):
    require(live.get('status')=='AUTHORIZED_EXECUTION_IN_PROGRESS' and live.get('campaign_id')==value['campaign_id'],
            'BLOCKED_PHYSICAL_AUTHORIZATION: root job closed or different campaign')
    deadline=value.get('deadline_epoch_seconds')
    require(type(deadline) in (int,float) and math.isfinite(deadline) and deadline>(time.time() if now is None else now),
            'BLOCKED_PHYSICAL_AUTHORIZATION: stage deadline expired')


def check_stage_receipt(path, stage, build):
    path=Path(path).resolve()
    value=load_json(path)
    require(type(value.get('schema_version')) is int and value['schema_version']==1 and
            value.get('status')=='AUTHORIZED_EXECUTION_IN_PROGRESS' and value.get('authorization_command')==COMMAND,
            'BLOCKED_PHYSICAL_AUTHORIZATION: absent or invalid stage authorization')
    require(value.get('reviewed_base_head')==BASE, 'Unreviewed bridge baseline')
    try:
        uuid.UUID(value['campaign_id'])
    except (ValueError,TypeError,KeyError,AttributeError):
        raise ValueError('Missing exact authorization campaign UUID') from None
    request=value['source_request']
    require(request['process'] in ('zh','tth','bbgj') and type(request['events']) is int and request['events']==1000 and
            type(request['energy_gev']) is int and request['energy_gev']==13000 and
            type(request['seed']) is int and 1<=request['seed']<=900000000, 'Unauthorized target/count/energy/seed')
    positive_budget(request['max_hours'],4);positive_budget(request['max_disk_gb'],10)
    require(type(value.get('pythia_seed')) is int and 1<=value['pythia_seed']<=900000000, 'Missing separate validated Pythia seed')
    require(stage in ('prefix10','prefix100','full1000') and value['child_stage']==stage and
            type(value['source_total_events']) is int and value['source_total_events']==1000, 'Invalid stage or original denominator')
    output=Path(value['child_output'])
    root=Path(request['output'])
    require(output.is_absolute() and root.is_absolute() and output.resolve()!=root.resolve() and
            root.resolve() in output.resolve().parents and path==output.resolve()/'execution_authorization.json',
            'Authorization receipt/output path mismatch')
    live=load_json(root/'run_manifest.json')
    check_live_job(value,live)
    for field in ('bridge_sha256','authorization_receipt_sha256','source_original_sha256','source_lhe_sha256',
                  'source_index_sha256','native_runner_sha256','native_validator_sha256'):
        require(isinstance(value.get(field),str) and HASH.fullmatch(value[field]), 'Missing exact authorization hash: '+field)
    for field,key in (('native_runner_sha256','shower_background'),('native_validator_sha256','validate_background_hepmc3')):
        require(build['binaries'][key]['sha256']==value[field] and digest(build['binaries'][key]['path'])==value[field],
                'Native binary changed or not authorized')
    for field,hash_field in (('source_lhe_path','source_lhe_sha256'),('source_index_path','source_index_sha256')):
        source=Path(value[field])
        require(source.is_absolute() and source.is_file() and not source.is_symlink() and digest(source)==value[hash_field],
                'Trusted full source/DAT bytes changed')
    if 'expires_at_utc' in value:
        expiry=datetime.fromisoformat(value['expires_at_utc'].replace('Z','+00:00'))
        require(expiry.tzinfo is not None and datetime.now(timezone.utc)<expiry, 'Authorization receipt expired')
    require(build['status']=='PASS_BUILD_AND_METHODS_ONLY' and source_bindings()==build['source_sha256'], 'Reviewed executable source changed since build')
    require(build.get('installation_file_sha256'), 'Runtime installation fingerprints absent')
    for name,sha in build['installation_file_sha256'].items():
        require(digest(name)==sha,'Retained installation changed since build')
    require(build.get('weight_source_sha256') and build.get('weight_source_commit')=='83a5c9986f30746cfb390435a9b10ac55a758fca',
            'Pinned external-LHE weight source proof absent')
    for name,sha in build['weight_source_sha256'].items():
        require(digest(name)==sha,'Pinned external-LHE weight implementation changed')
    return value


def source_index_bytes(report, *, method_only=False):
    """Render the exact numeric reader index; original LHE/ledger bytes remain untouched."""
    require(type(method_only) is bool, 'Method scope must be a literal Boolean')
    require(report['status']==('METHOD_ONLY' if method_only else 'PASS_LHE_RECORDS'), 'Missing independently validated source scope')
    events=report['source_events']
    require(len(events)==1000 and report['actual_events']==1000, 'Full original1000-event source index required')
    lines=[]
    for ordinal,event in enumerate(events,1):
        require(event['source_event_index']==ordinal and isinstance(event['source_event_content_hash'],str) and
                HASH.fullmatch(event['source_event_content_hash']), 'Duplicate/unmapped source event identity')
        rows=event['rows']
        require(len(rows[0])==6 and int(rows[0][0])+1==len(rows), 'Source NUP/header mismatch')
        lines.append('E '+str(ordinal)+' '+event['source_event_content_hash']+' '+' '.join(str(x).replace('D','E').replace('d','e') for x in rows[0]))
        for row in rows[1:]:
            require(len(row)==13, 'Source particle row does not contain13fields')
            lines.append('P '+' '.join(str(x).replace('D','E').replace('d','e') for x in row))
    return ('\n'.join(lines)+'\n').encode('ascii')


def check_reused_prefix10(descriptor, *, authorization, output, run_id):
    """Verify the one preserved context-failure prefix; never invoke a producer.

    The root copies only immutable shower assets into a fresh authorized output.
    The failed original reader report and its closed root manifest stay intact.
    """
    require(isinstance(descriptor,dict) and descriptor.get('status')=='SOURCE_BOUND_NON_GENERATING_PREFIX10_REUSE',
            'Missing strict non-generating prefix reuse descriptor')
    require(authorization['child_stage']=='prefix10' and authorization['source_request']['process']=='zh',
            'Only the actual preserved B04 prefix10 context failure may be reused')
    original=Path(descriptor['original_prefix_directory']).resolve()
    original_root=original.parent.parent
    require(original.is_dir() and not original.is_symlink() and original.name=='prefix10' and
            original.parent.name=='pythia' and original!=output and original_root not in output.parents,
            'Invalid or overlapping original prefix reuse directory')
    manifest_path=Path(descriptor['original_manifest_path']).resolve()
    require(manifest_path==original_root/'run_manifest.json' and
            digest(manifest_path)==descriptor['original_manifest_sha256'], 'Original closed manifest changed')
    old=load_json(manifest_path)
    require(old.get('status')=='PARTIAL_PHYSICAL_CHAIN' and
            old.get('failure')=='FAILED_STAGE: background_reader_prefix10; retained actual log' and
            old.get('Delphes_ROOT_entries')==0 and old.get('HepMC_validated_events')==0,
            'Original failure is not the isolated non-generating reader context bug')
    for key in ('process','events','seed','energy_gev'):
        require(old['request'][key]==authorization['source_request'][key], 'Reused source request changed')
    attempts=old['stages_attempted']
    producers=[x for x in attempts if x['stage'] in ('shower_background_prefix10','shower_background_prefix100','shower_background_full1000')]
    readers=[x for x in attempts if x['stage'].startswith('background_reader_')]
    require(len(producers)==1 and producers[0]['stage']=='shower_background_prefix10' and producers[0]['exit_code']==0 and
            len(readers)==1 and readers[0]['stage']=='background_reader_prefix10' and readers[0]['exit_code']!=0,
            'Preserved attempt contains another shower or reader stage')
    old_report_path=original/'background_hepmc_validation.json'
    require(digest(old_report_path)==descriptor['original_failed_reader_report_sha256'], 'Original failed reader receipt changed')
    failed=load_json(old_report_path)
    require(failed.get('validation_status')=='FAIL_BACKGROUND_HEPMC_RECORDS' and
            failed.get('fatal_error')=='Retained original Pythia status inconsistent with actual HepMC status' and
            failed.get('decompressed_file_sha256')==REUSED_PREFIX10_HEPMC_SHA256 and failed.get('source_total_events')==1000,
            'Reused raw HepMC does not match the diagnosed actual context failure')
    old_auth_path=original/'execution_authorization.json'
    require(digest(old_auth_path)==descriptor['original_stage_authorization_sha256'], 'Original stage authority changed')
    old_auth=load_json(old_auth_path)
    require(old_auth['bridge_sha256']==old['bridge_sha256'] and old_auth['campaign_id']==old['campaign_id'] and
            old_auth['child_stage']=='prefix10' and old_auth['source_request']==old['request'] and
            old_auth['source_original_sha256']==authorization['source_original_sha256'] and
            old_auth['source_lhe_sha256']==authorization['source_lhe_sha256'] and
            old_auth['source_index_sha256']==authorization['source_index_sha256'] and
            old_auth['pythia_seed']==authorization['pythia_seed'], 'Original source-bound authority differs from continuation')
    files=descriptor['artifacts']
    require(isinstance(files,dict) and set(files)==set(REUSED_SHOWER_FILES) and
            files['shower.hepmc3']==REUSED_PREFIX10_HEPMC_SHA256, 'Incomplete or different immutable prefix asset set')
    for name,sha in files.items():
        require(isinstance(sha,str) and HASH.fullmatch(sha), 'Invalid preserved asset SHA256')
        for folder in (original,output):
            path=folder/name
            require(path.is_file() and not path.is_symlink() and digest(path)==sha, 'Preserved prefix asset changed: '+name)
    summary=load_json(output/'run_summary.json')
    require(summary['process_alias']=='zh' and summary['source_sample_id']=='B04_ZH_BBGG' and
            summary['source_file_sha256']==authorization['source_original_sha256'] and summary['source_total_events']==1000 and
            summary['pythia_seed']==authorization['pythia_seed'] and summary['source_generation_seed']==authorization['source_request']['seed'] and
            summary['pythia_run_id']==run_id and summary['events_requested']==10 and
            all(summary[key]==10 for key in ('N_input','N_attempted','N_pythia_next_calls','N_source_identity_verified','N_shower_success','N_written')) and
            all(summary[key]==0 for key in ('N_source_identity_failed','N_shower_failed','N_internal_rejected','N_refused_internal_source_read_attempts')),
            'Saved genuine prefix was not the complete source-verified ten-event shower')
    return {'exit_code':0,'execution_mode':'REUSED_EXISTING_SHOWER_NO_PROCESS_INVOCATION',
            'new_pythia_next_calls':0,'original_pythia_next_calls':10,
            'original_run_summary_sha256':files['run_summary.json'],
            'original_hepmc_sha256':files['shower.hepmc3'],'original_manifest_sha256':descriptor['original_manifest_sha256']}


def run_stage(*, authorization_file, stage, build_receipt, source_validation, xml_path, run_id, run_command, reused_shower=None):
    """Only call from the root's source-bound task-authorization/resource guard.

    run_command(argv,cwd,stage) must recheck root authorization and global4h/10GiB
    limits before starting a child. This API itself never calls subprocess.
    """
    require(callable(run_command), 'Root guarded run_command callback required')
    build=load_json(build_receipt)
    authorization=check_stage_receipt(authorization_file,stage,build)
    require(source_validation['status']=='PASS_LHE_RECORDS' and source_validation['actual_events']==1000 and
            source_validation['idwtup']==-4, 'Actual full1000-event LHE validation required')
    output=Path(authorization['child_output']).resolve()
    request=authorization['source_request'];count={'prefix10':10,'prefix100':100,'full1000':1000}[stage]
    require(isinstance(run_id,str) and run_id and not any(c.isspace() for c in run_id), 'Missing unique Pythia run identity')
    common=['--authorization',str(Path(authorization_file).resolve()),'--authorization-sha256',digest(authorization_file),
            '--bridge-sha256',authorization['bridge_sha256'],'--source-index',authorization['source_index_path'],
            '--index-sha256',authorization['source_index_sha256'],'--source-sha256',authorization['source_original_sha256'],
            '--events',str(count),'--source-total','1000','--seed',str(authorization['pythia_seed']),
            '--stage',stage,'--output',str(output),'--max-hours',str(request['max_hours']),
            '--max-disk-gb',str(request['max_disk_gb']),'--xml',str(xml_path),'--process',request['process'],'--sample-id',{'zh':'B04_ZH_BBGG','tth':'B05_TTH_HGG','bbgj':'B06_BBGJ'}[request['process']]]
    repo=Path(__file__).resolve().parents[3]
    argv=[build['binaries']['shower_background']['path'],*common,'--input',authorization['source_lhe_path'],
          '--run-id',run_id,'--settings',str(repo/'simulation/pythia8/config/baseline_shower.cmnd'),
          '--overlay',str(repo/'simulation/new_backgrounds/cards'/('shower_'+request['process']+'.cmnd')),
          '--source-sigma-pb',str(source_validation['cross_section_pb']),
          '--source-error-pb',str(source_validation['cross_section_uncertainty_pb'])]
    if reused_shower is None:
        shower=run_command(argv,output,'shower_background_'+stage,env=build['runtime_environment'])
    else:
        shower=check_reused_prefix10(reused_shower,authorization=authorization,output=output,run_id=run_id)
    if shower['exit_code']!=0:
        return {'status':'PARTIAL_SHOWER','execution':shower,'exclusive_physical_normalization':'BLOCKED'}
    summary=load_json(output/'run_summary.json')
    require(summary['status']=='SHOWER_WRITTEN_REQUIRES_INDEPENDENT_READER' and summary['N_written']==count and
            summary['N_input']==count and summary['N_shower_failed']==0 and summary['source_total_events']==1000,
            'Native shower did not preserve the complete requested source mapping')
    check_stage_receipt(authorization_file,stage,build)
    reader_args=[build['binaries']['validate_background_hepmc3']['path'],*common,'--source-lhe',authorization['source_lhe_path'],
                 '--input',str(output/'shower.hepmc3'),'--report',str(output/'background_hepmc_validation.json')]
    reader=run_command(reader_args,output,'background_reader_'+stage,env=build['runtime_environment'])
    if reader['exit_code']!=0:
        return {'status':'FAILED_HEPMC_VALIDATION','shower_execution':shower,'reader_execution':reader,
                'exclusive_physical_normalization':'BLOCKED'}
    report=load_json(output/'background_hepmc_validation.json')
    require(report['validation_status']=='PASS_BACKGROUND_HEPMC_RECORDS' and report['N_readback']==count and
            report['N_failed_validation']==0 and report['source_total_events']==1000, 'Actual ReaderAscii receipt incomplete')
    if reused_shower is not None:
        check_reused_prefix10(reused_shower,authorization=authorization,output=output,run_id=run_id)
    check_stage_receipt(authorization_file,stage,build)
    return {'status':'PASS_RAW_SHOWER_AND_HEPMC_RECORDS','events':count,'source_total_events':1000,
            'shower_execution':shower,'reader_execution':reader,'reader_report':report,'run_summary':summary,
            'physical_BR_adoption':'PENDING_ACTUAL_CLOSURE','exclusive_physical_normalization':'BLOCKED'}
