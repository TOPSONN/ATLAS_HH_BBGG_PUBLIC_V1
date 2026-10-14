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

COMMAND = 'AUTHORIZE_PHASE6G_ZH_100_RUN'
BASE = '05cff9a5d991ba6782b339bc41932ae4da296d8c'
HASH = re.compile(r'[0-9a-f]{64}\Z')


def load_json(path):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=32*1024**2, 'Invalid bounded JSON file')
    def pairs(values):
        result={}
        for key,value in values:
            require(key not in result, 'Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def positive_budget(value, maximum):
    require(type(value) in (int,float) and math.isfinite(value) and 0<value<=maximum, 'Invalid resource ceiling')


def check_live_job(value,live,now=None):
    require(live.get('status')=='AUTHORIZED_EXECUTION_IN_PROGRESS' and live.get('ticket_id')==value['ticket_id'],
            'BLOCKED_PHYSICAL_AUTHORIZATION: root job closed or different ticket')
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
        uuid.UUID(value['ticket_id'])
    except (ValueError,TypeError,KeyError,AttributeError):
        raise ValueError('Missing exact authorization ticket UUID') from None
    request=value['source_request']
    require(request['process']=='zh' and type(request['events']) is int and request['events']==100 and
            type(request['energy_gev']) is int and request['energy_gev']==13000 and
            type(request['seed']) is int and 1<=request['seed']<=900000000, 'Unauthorized target/count/energy/seed')
    positive_budget(request['max_hours'],2);positive_budget(request['max_disk_gb'],5)
    require(stage in ('prefix10','full100') and value['child_stage']==stage and
            type(value['source_total_events']) is int and value['source_total_events']==100, 'Invalid stage or original denominator')
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
    for field,key in (('native_runner_sha256','zh_shower'),('native_validator_sha256','validate_zh_hepmc3')):
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
    return value


def source_index_bytes(report, *, method_only=False):
    """Render the exact numeric reader index; original LHE/ledger bytes remain untouched."""
    require(type(method_only) is bool, 'Method scope must be a literal Boolean')
    require(report['status']==('METHOD_ONLY' if method_only else 'PASS_LHE_RECORDS'), 'Missing independently validated source scope')
    events=report['source_events']
    require(len(events)==100 and report['actual_events']==100, 'Full original100-event source index required')
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


def run_stage(*, authorization_file, stage, build_receipt, source_validation, xml_path, run_id, run_command):
    """Only call from the root's claimed human-authorization/resource guard.

    run_command(argv,cwd,stage) must recheck root authorization and global2h/5GiB
    limits before starting a child. This API itself never calls subprocess.
    """
    require(callable(run_command), 'Root guarded run_command callback required')
    build=load_json(build_receipt)
    authorization=check_stage_receipt(authorization_file,stage,build)
    require(source_validation['status']=='PASS_LHE_RECORDS' and source_validation['actual_events']==100 and
            source_validation['idwtup']==-4, 'Actual full100-event LHE validation required')
    output=Path(authorization['child_output']).resolve()
    request=authorization['source_request'];count=10 if stage=='prefix10' else 100
    require(isinstance(run_id,str) and run_id and not any(c.isspace() for c in run_id), 'Missing unique Pythia run identity')
    common=['--authorization',str(Path(authorization_file).resolve()),'--authorization-sha256',digest(authorization_file),
            '--bridge-sha256',authorization['bridge_sha256'],'--source-index',authorization['source_index_path'],
            '--index-sha256',authorization['source_index_sha256'],'--source-sha256',authorization['source_original_sha256'],
            '--events',str(count),'--source-total','100','--seed',str(request['seed']),
            '--stage',stage,'--output',str(output),'--max-hours',str(request['max_hours']),
            '--max-disk-gb',str(request['max_disk_gb']),'--xml',str(xml_path),'--sample-id','zh']
    repo=Path(__file__).resolve().parents[4]
    argv=[build['binaries']['zh_shower']['path'],*common,'--input',authorization['source_lhe_path'],
          '--run-id',run_id,'--settings',str(repo/'simulation/pythia8/config/baseline_shower.cmnd'),
          '--overlay',str(repo/'simulation/zh_pilot/cards/preferred_higgs_decay.cmnd'),
          '--source-sigma-pb',str(source_validation['cross_section_pb']),
          '--source-error-pb',str(source_validation['cross_section_uncertainty_pb'])]
    shower=run_command(argv,output,'zh_shower_'+stage,env=build['runtime_environment'])
    if shower['exit_code']!=0:
        return {'status':'PARTIAL_SHOWER','execution':shower,'exclusive_physical_normalization':'BLOCKED'}
    summary=load_json(output/'run_summary.json')
    require(summary['status']=='SHOWER_WRITTEN_REQUIRES_INDEPENDENT_READER' and summary['N_written']==count and
            summary['N_input']==count and summary['N_shower_failed']==0 and summary['source_total_events']==100,
            'Native shower did not preserve the complete requested source mapping')
    check_stage_receipt(authorization_file,stage,build)
    reader_args=[build['binaries']['validate_zh_hepmc3']['path'],*common,'--source-lhe',authorization['source_lhe_path'],
                 '--input',str(output/'shower.hepmc3'),'--report',str(output/'zh_hepmc_validation.json')]
    reader=run_command(reader_args,output,'zh_reader_'+stage,env=build['runtime_environment'])
    if reader['exit_code']!=0:
        return {'status':'FAILED_HEPMC_VALIDATION','shower_execution':shower,'reader_execution':reader,
                'exclusive_physical_normalization':'BLOCKED'}
    report=load_json(output/'zh_hepmc_validation.json')
    require(report['validation_status']=='PASS_ZH_HEPMC_RECORDS' and report['N_readback']==count and
            report['N_failed_validation']==0 and report['source_total_events']==100, 'Actual ReaderAscii receipt incomplete')
    check_stage_receipt(authorization_file,stage,build)
    return {'status':'PASS_RAW_SHOWER_AND_HEPMC_RECORDS','events':count,'source_total_events':100,
            'shower_execution':shower,'reader_execution':reader,'reader_report':report,
            'physical_BR_adoption':'UNKNOWN_NOT_APPLIED','exclusive_physical_normalization':'BLOCKED'}
