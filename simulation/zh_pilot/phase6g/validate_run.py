#!/usr/bin/env python3
"""Read-only verification of a preserved authorized ZH100 raw diagnostic run.

All100 original LHE records are revalidated. Downstream ASCII/CRC/source/weight
bindings and actual native receipts are checked without rerunning Pythia,
Delphes, ReaderAscii, or ROOT. This never supplies exclusive BR normalization.
"""
from __future__ import annotations
import argparse
from contextvars import ContextVar
import csv
from decimal import Decimal
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import sys

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO))
from simulation.zh_pilot.phase6g import validate_lhe as lhe_validator
from simulation.zh_pilot.phase6g.common import require, strict_json as _strict_json, sha_file, bridge_identity, ACK, BASE

MAX_TEXT=2*1024**2
MAX_RECORD_FILE=128*1024**2
BASELINE=REPO/'simulation/pythia8/config/baseline_shower.cmnd'
OVERLAY=REPO/'simulation/zh_pilot/cards/preferred_higgs_decay.cmnd'
CARD=REPO/'simulation/delphes/cards/atlas_like_bbgg_baseline.tcl'
STAGES=('00_input','01_photons','02_jets','03_two_btags','04_mgg_105_160')
_GUARD=ContextVar('preserved_run_files',default=None)
BASELINE_SHA='53ab239a091b179abce8db5d6905a279884c47a0286a422c059265460ec33389'
OVERLAY_SHA='f2315b863cf39bf6a8b5e87da29397d1e3a773b703ec429a0b78666656d8d2f6'
CARD_SHA='cd91fc7982365af23e4002c6295418fbbc0077ffe381e992e7e6070052eb1f47'


def bounded_file(path,limit=MAX_TEXT):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=limit,'missing/unsafe/oversized preserved file: '+path.name)
    guard=_GUARD.get()
    if guard is not None:
        resolved=path.resolve();identity=(sha_file(path),path.stat().st_size)
        require(resolved not in guard or guard[resolved]==identity,'preserved input changed during verification: '+path.name)
        guard[resolved]=identity
    return path


def strict_json(path):
    return _strict_json(bounded_file(path))


def verify_unchanged(guard):
    for path,(digest,size) in guard.items():
        require(path.is_file() and not path.is_symlink() and path.stat().st_size==size and sha_file(path)==digest,
                'preserved input changed during verification: '+path.name)


def scoped_path(run,path):
    raw=Path(path);resolved=raw.resolve()
    require(not raw.is_symlink() and resolved.is_relative_to(run.resolve()),'preserved artifact escapes original run')
    return resolved


def jsonl(path,count):
    raw=bounded_file(path,MAX_RECORD_FILE).read_bytes()
    require(raw.endswith(b'\n') and len(raw.splitlines())==count,'incomplete/extra preserved JSONL rows')
    rows=[]
    for line in raw.splitlines():
        require(len(line)<=MAX_TEXT,'oversized preserved JSONL row')
        def unique(pairs):
            value={}
            for key,item in pairs:require(key not in value,'duplicate JSONL key');value[key]=item
            return value
        row=json.loads(line,object_pairs_hook=unique,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSONL')))
        require(type(row) is dict and 'fixture_scope' not in row,'synthetic or malformed preserved record')
        def finite(item):
            if type(item) is float:require(math.isfinite(item),'nonfinite JSONL numeric overflow')
            if isinstance(item,dict):
                for child in item.values():finite(child)
            elif isinstance(item,list):
                for child in item:finite(child)
        finite(row)
        rows.append(row)
    return rows


def literal_counts(record,expected):
    for key,count in expected.items():require(type(record.get(key)) is int and record[key]==count,'missing/contradictory actual count: '+key)


def validate_derived_files(folder,detector):
    """Bind ROOT-derived rows/decisions, including H-match pairs, to execution."""
    hashes=detector['derived_files_sha256']
    require(type(hashes) is dict and set(hashes)=={'reco_events.jsonl','cutflow.csv'},'derived native output hash fields missing/changed')
    for name,digest in hashes.items():
        require(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest) is not None and
                sha_file(bounded_file(Path(folder)/name,MAX_RECORD_FILE))==digest,'ROOT-derived native output changed: '+name)
    return dict(hashes)


def close(a,b):
    return lhe_validator.FROZEN.close(lhe_validator.decimal(a),lhe_validator.decimal(b),1e-14,1e-11)


def gzip_identity(path,plain_sha,limit=MAX_RECORD_FILE):
    path=bounded_file(path,limit);before=sha_file(path);digest=hashlib.sha256();total=0
    try:
        with gzip.open(path,'rb') as stream:
            while block:=stream.read(65536):
                total+=len(block);require(total<=limit,'gzip decompressed limit exceeded');digest.update(block)
    except (OSError,EOFError) as error:raise ValueError('preserved gzip CRC/truncation failure') from error
    require(digest.hexdigest()==plain_sha and sha_file(path)==before,'compressed/plain record identity changed')
    return {'compressed_sha256':before,'decompressed_sha256':digest.hexdigest(),'decompressed_bytes':total}


def portable_hepmc(path):
    """Reuse immutable portable graph/parser methods; never execute native QA."""
    path=bounded_file(path,MAX_RECORD_FILE)
    sys.path.insert(0,str(REPO/'simulation/pythia8/scripts'))
    spec=importlib.util.spec_from_file_location('phase6g_preserved_ascii',REPO/'simulation/pythia8/scripts/validate_hepmc3.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    header=None;events=[];attrs=[];digest=hashlib.sha256()
    for kind,raw in module.iter_ascii(path,max_decompressed_gb=MAX_RECORD_FILE/1024**3):
        digest.update(raw)
        if kind=='header':header=module.parse_header(raw)
        elif kind=='event':
            require(header is not None and len(events)<100,'extra/misordered preserved HepMC events')
            events.append(module.parse_event(raw,header));attributes={}
            for line in raw.decode().splitlines():
                if line.startswith('A 0 '):
                    _,_,key,value=line.split(' ',3);require(key not in attributes,'duplicate event attribute')
                    attributes[key]=module.unescape(value)
            attrs.append(attributes)
    require(header is not None and len(events) in (10,100),'wrong preserved prefix/full event count')
    return header,events,attrs,digest.hexdigest()


def validate_settings(folder,summary,seed):
    """Check recorded initialized Settings values; particle channels use tables."""
    required=summary['required_settings'];require(type(required) is dict,'actual settings object missing')
    expected={key:True for key in ('ProcessLevel:all','PartonLevel:all','PartonLevel:ISR','PartonLevel:FSR',
        'HadronLevel:all','HadronLevel:Hadronize','HadronLevel:Decay','Beams:strictLHEFscale','Random:setSeed','BeamRemnants:primordialKT')}
    expected.update({key:False for key in ('PartonLevel:MPI','SecondHard:generate','HardQCD:all','SoftQCD:all',
        'JetMatching:merge','Merging:doKTMerging','Merging:doMGMerging','Merging:doPTLundMerging','UncertaintyBands:doVariations')})
    expected.update({'SLHA:readFrom':0,'Beams:frameType':4,'PartonShowers:model':1,'SpaceShower:pTmaxMatch':1,
        'TimeShower:pTmaxMatch':1,'Random:seed':seed,'H_forcing':'25:onMode=off;25:onIfMatch=22 22','Z_forcing':'NONE',
        'BeamRemnants:primordialKTsoft':0.9,'BeamRemnants:primordialKThard':1.8,'BeamRemnants:halfScaleForKT':1.5,
        'BeamRemnants:halfMassForKT':1.0,'BeamRemnants:reducedKTatHighY':0.5,'BeamRemnants:primordialKTremnant':0.4,'PDF:pSet':'8'})
    for key,value in expected.items():
        require(key in required,'missing initialized setting: '+key)
        if type(value) in (bool,str):require(type(required[key]) is type(value) and required[key]==value,'reviewed initialized setting differs: '+key)
        else:require(type(required[key]) in (int,float) and close(required[key],value),'reviewed initialized setting differs: '+key)
    require(set(required)==set(expected)|{'SpaceShower:alphaSvalue','TimeShower:alphaSvalue','4:m0','5:m0'},'missing/unknown initialized settings fields')
    for key in ('SpaceShower:alphaSvalue','TimeShower:alphaSvalue'):require(0<lhe_validator.decimal(required[key])<1,'invalid shower alphaS')
    for key in ('4:m0','5:m0'):require(lhe_validator.decimal(required[key])>=0,'invalid actual shower heavy-quark mass')
    hashes={}
    for name in ('effective_settings.cmnd','inclusive_initialized_settings.cmnd'):
        path=bounded_file(folder/name,MAX_RECORD_FILE);values={}
        for line in path.read_text(encoding='utf-8').splitlines():
            text=line.strip()
            if not text or text.startswith(('#','!')):continue
            require('=' in text,'malformed initialized settings line');key,value=text.split('=',1);key=key.strip();value=value.strip()
            require(key not in values,'duplicate initialized settings entry');values[key]=value
        for key,value in required.items():
            if key in ('H_forcing','Z_forcing','4:m0','5:m0'):continue
            require(key in values,'initialized settings record missing: '+key)
            if type(value) is bool:require(values[key].lower()==('on' if value else 'off'),'recorded settings Boolean differs: '+key)
            elif isinstance(value,str):require(values[key]==value,'recorded settings word differs: '+key)
            else:require(close(values[key],value),'recorded settings number differs: '+key)
        hashes[name]=sha_file(path)
    return hashes


def validate_tables(folder,summary):
    values=summary['initialized_higgs_decay']
    names={'inclusive_table_sha256':'decay_tables_inclusive_initialized.json','effective_table_sha256':'decay_tables_initialized.json',
           'original_preinit_table_sha256':'decay_tables_original_preinit.json','original_particle_data_sha256':'original_particle_data.xml',
           'inclusive_particle_data_sha256':'inclusive_initialized_particle_data.xml','effective_particle_data_sha256':'effective_particle_data.xml'}
    hashes={}
    for key,name in names.items():
        path=bounded_file(folder/name,MAX_RECORD_FILE);require(sha_file(path)==values[key],'actual initialized table/XML changed: '+name);hashes[name]=values[key]
    inclusive=strict_json(folder/names['inclusive_table_sha256']);effective=strict_json(folder/names['effective_table_sha256'])
    for table in (inclusive,effective):
        require(table['initialized_external_lhe'] is True and table['source_Z_decay_already_included'] is True and
                table['physical_BR_adoption']=='UNKNOWN_NOT_APPLIED','table scope/BR adoption contradiction')
        require(close(table['tables']['25']['mass_gev'],125) and close(table['tables']['23']['mass_gev'],91.188),'initialized mass scheme changed')
    require(inclusive['tables']['23']==effective['tables']['23'],'preferred H-only forcing altered Z table')
    a,b=inclusive['tables']['25'],effective['tables']['25']
    require(a['total_width_gev']==b['total_width_gev'] and len(a['channels'])==len(b['channels']),'H inclusive/forced table identity differs')
    target=[];enabled=[]
    for left,right in zip(a['channels'],b['channels']):
        require(all(left[key]==right[key] for key in ('index','products','stored_inclusive_BR','partial_width_gev')),'forcing altered inclusive H model values')
        if sorted(right['products'])==[22,22]:target.append(right)
        if right['on_mode'] in (1,2):enabled.append(right)
    require(len(target)==len(enabled)==1 and target[0]==enabled[0],'effective H table is not only gamma gamma')
    width=lhe_validator.decimal(b['total_width_gev']);partial=lhe_validator.decimal(target[0]['partial_width_gev']);br=lhe_validator.decimal(target[0]['stored_inclusive_BR'])
    require(0<partial<=width and 0<br<=1 and abs(partial/width-br)<=Decimal('2e-12'),'invalid initialized H width/BR')
    require(close(values['inclusive_model_BR_gamma_gamma'],br) and close(values['total_width_GeV'],width) and
            close(values['partial_width_gamma_gamma_GeV'],partial) and close(values['conditional_forced_probability'],1),'summary differs from bound actual H table')
    return hashes


def check_stage(folder,count,source,seed,manifest_stage):
    summary=strict_json(folder/'run_summary.json');reader=strict_json(folder/'zh_hepmc_validation.json');generic=strict_json(folder/'generic_physics_validation.json')
    require(summary['status']=='SHOWER_WRITTEN_REQUIRES_INDEPENDENT_READER' and manifest_stage['status']=='PASS_RAW_SHOWER_AND_HEPMC_RECORDS','incomplete actual shower stage')
    literal_counts(summary,{'source_total_events':100,'events_requested':count,'N_input':count,'N_written':count,'N_shower_success':count,
                            'N_attempted':count,'N_pythia_next_calls':count,'N_shower_failed':0,'N_internal_rejected':0,
                            'N_refused_internal_source_read_attempts':0,'N_source_identity_verified':count,'N_source_identity_failed':0})
    require(summary['source_file_sha256']==source['source_file_sha256'] and summary['pythia_seed']==seed and summary['event_identity']=='PASS','shower source/seed identity changed')
    require(summary['source_sample_id']=='zh' and summary['pythia_version']=='8.317' and summary['hepmc3_version']=='3.03.01' and
            close(summary['input_cross_section_pb'],source['cross_section_pb']) and
            close(summary['input_cross_section_uncertainty_pb'],source['cross_section_uncertainty_pb']),'actual shower model/source normalization differs')
    require(reader['validation_status']=='PASS_ZH_HEPMC_RECORDS' and generic['validation_status']=='PASS','actual native ReaderAscii validation incomplete')
    literal_counts(reader,{'N_readback':count,'N_passed_validation':count,'N_failed_validation':0,'source_total_events':100})
    literal_counts(generic,{'N_requested_validation':count,'N_readback':count,'N_passed_validation':count,'N_failed_validation':0,'N_not_assessed':0})
    require(generic.get('fatal_error') is None and generic['validator']=='actual_HepMC3_ReaderAscii_and_Pythia_ParticleData','untracked smoke cannot substitute for actual physics readback')
    require(reader['Higgs_BR_adoption']=='UNKNOWN_NOT_APPLIED' and reader['exclusive_physical_normalization']=='BLOCKED' and
            reader['source_Z_BR_reapplied'] is False and reader['pythia_version']=='8.317' and reader['hepmc3_reported_version']=='3.03.01',
            'native physics version/normalization contradiction')
    require(reader['source_file_sha256']==generic['source_file_sha256']==source['source_file_sha256'] and
            reader['generic_physics_report_sha256']==sha_file(folder/'generic_physics_validation.json'),'actual generic/ancestry receipt binding differs')
    require(manifest_stage['reader_report']==reader,'manifest/native ReaderAscii report differs')
    for field,name in (('decompressed_file_sha256','shower.hepmc3'),('input_index_sha256','input_event_index.dat'),('truth_index_sha256','zh_truth_index.dat')):
        require(sha_file(bounded_file(folder/name,MAX_RECORD_FILE))==reader[field],'preserved reader artifact changed: '+name)
    require(generic['decompressed_file_sha256']==reader['decompressed_file_sha256'],'generic native reader inspected another HepMC file')
    header,events,attrs,ascii_sha=portable_hepmc(folder/'shower.hepmc3')
    require(len(events)==count and ascii_sha==reader['decompressed_file_sha256'],'portable ASCII identity/count differs')
    ledger=jsonl(folder/'event_ledger.jsonl',count);ancestry=jsonl(folder/'hepmc_ancestry.jsonl',count)
    records=[]
    for ordinal,(event,attribute,row,origin) in enumerate(zip(events,attrs,ledger,ancestry),1):
        original=source['source_events'][ordinal-1]
        require(event['event_number']==ordinal and event['source_total_events']==100 and row['processing_status']=='WRITTEN' and
                type(row['source_event_index']) is int and row['source_event_index']==ordinal and row['output_event_index']==ordinal,
                'missing/replaced/failed source attempt in successful stage')
        literal_counts(row,{'source_total_events':100,'pythia_seed':seed,'processing_attempt':ordinal,'output_event_index':ordinal})
        identity=event['identity']
        require(identity['source_file_sha256']==row['source_file_sha256']==source['source_file_sha256'] and
                identity['source_event_content_hash']==row['source_event_content_hash']==origin['source_event_content_hash']==original['source_event_content_hash'] and
                identity['pythia_run_id']==row['pythia_run_id']==summary['pythia_run_id'] and int(identity['pythia_seed'])==seed and
                identity['source_sample_id']==row['source_sample_id']=='zh',
                'source/run/event ledger mapping changed')
        require(event['event_hash']==row['output_event_hash']==origin['event_block_sha256'] and
                origin['source_event_index']==ordinal and origin['source_total_events']==100,'original output block/ancestry identity differs')
        require(attribute['source_lhe_profile']=='ZH_ZBB_STABLE_H' and attribute['source_included_decay_ids']=='Z_to_b_bbar' and
                attribute['physical_BR_adoption']=='UNKNOWN_NOT_APPLIED' and attribute['exclusive_physical_normalization']=='BLOCKED',
                'source/decay/BR metadata contradiction')
        require(json.loads(attribute['zh_decay_lineage'])==origin['lineage'],'native ancestry receipt differs from preserved event attribute')
        vector=[row['input_contribution_pb'],row['lhe_weight_pb'],row['pythia_weight_pb'],*row['converter_weights_pb']]
        require(close(row['nominal_generator_weight'],original['nominal_generator_weight']),'original nominal generator weight differs')
        require(len(vector)==len(event['weights']) and all(close(a,b) for a,b in zip(vector,event['weights'])) and
                origin['weight_names']==header['weight_names'] and all(close(a,b) for a,b in zip(origin['weights_pb'],event['weights'])),'preserved named weight vectors differ')
        require(len(origin['weights_pb'])==len(event['weights']),'ancestry weights truncated')
        records.append({'source_file_sha256':source['source_file_sha256'],'source_event_index':ordinal,'source_event_sha256':original['source_event_content_hash'],
                        'source_total_events':100,'weight_names':header['weight_names'],'weight_values':event['weights']})
    binding=lhe_validator.validate_downstream_binding(source,records,expected_output_count=count)
    for field,index in (('raw_LHE_weight_sum_pb',1),('Info_weight_sum_pb',2),('converter_nominal_weight_sum_pb',3)):
        require(close(reader[field],sum((lhe_validator.decimal(row['weight_values'][index]) for row in records),Decimal(0))),
                'native named-column sums differ: '+field)
    weights=[lhe_validator.decimal(row['weight_values'][0]) for row in records]
    for field,value in (('weight_sum_contribution_pb',sum(weights)),('weight_sum_abs_contribution_pb',sum(map(abs,weights))),
                       ('weight_sum_squared_contribution_pb2',sum(w*w for w in weights))):require(close(summary[field],value),'actual signed contribution moments differ')
    table_hashes=validate_tables(folder,summary)
    settings_hashes=validate_settings(folder,summary,seed)
    return {'events':count,'reader_report_sha256':sha_file(folder/'zh_hepmc_validation.json'),'generic_report_sha256':sha_file(folder/'generic_physics_validation.json'),
            'decompressed_sha256':ascii_sha,'records':records,'table_hashes':table_hashes,'settings_hashes':settings_hashes,
            'summary':summary,'binding':binding,'reader':reader}


def validate_cutflow(csv_path,rows,source,hepmc_rows):
    """Event-level arithmetic/source identities only, not a fresh ROOT analysis."""
    require(len(rows)==len(hepmc_rows)==len(source['source_events'])==100,'full100 reco/source rows required')
    totals={stage:{'raw':0,'sum':Decimal(0),'sum2':Decimal(0)} for stage in STAGES}
    for ordinal,(row,event,hepmc) in enumerate(zip(rows,source['source_events'],hepmc_rows),1):
        require(type(row['source_event_index']) is int and row['source_event_index']==ordinal and
                row['source_event_sha256']==event['source_event_content_hash'] and row['hepmc_event_sha256']==hepmc['event_block_sha256'],'reco original source mapping differs')
        weight=lhe_validator.decimal(event['nominal_generator_weight'])/100
        require(close(row['source_contribution_pb'],weight),'reco source contribution normalized differently')
        flags=[True,*[row[k] for k in ('cut_photons','cut_jets','cut_two_btags','cut_mgg')]]
        require(all(type(x) is bool for x in flags) and all(not flags[i] or flags[i-1] for i in range(1,5)),'cutflow is not nested literal event decisions')
        for key in ('selected_photons','eligible_jets','tagged_bit0'):require(type(row[key]) is int and row[key]>=0,'invalid native multiplicity')
        for key in ('H_origin_final_truth_photons','H_origin_reco_matches'):require(type(row[key]) is int and 0<=row[key]<=2,'invalid H-origin diagnostic count')
        require(row['H_origin_reco_matches']<=row['H_origin_final_truth_photons'],'H-origin reconstructed match count exceeds available truth photons')
        require(row['tagged_bit0']<=row['eligible_jets'] and (not flags[1] or row['selected_photons']>=2) and
                (not flags[2] or row['eligible_jets']>=2) and (not flags[3] or row['tagged_bit0']>=2),'multiplicity/cut decision contradiction')
        for key,available in (('m_gamma_gamma',row['selected_photons']>=2),('m_bb',row['tagged_bit0']>=2),
                              ('m_bb_gamma_gamma',row['selected_photons']>=2 and row['tagged_bit0']>=2)):
            require((row[key] is not None) is available,'native pair availability/null contradiction')
            if available:require(lhe_validator.decimal(row[key])>=0,'nonfinite/negative reconstructed mass')
        require(flags[4]==(flags[3] and 105<=lhe_validator.decimal(row['m_gamma_gamma'])<=160),'mgg window decision differs from original Phase6C definition')
        for stage,flag in zip(STAGES,flags):
            if flag:totals[stage]['raw']+=1;totals[stage]['sum']+=weight;totals[stage]['sum2']+=weight*weight
    table=list(csv.DictReader(bounded_file(csv_path).read_text().splitlines()))
    require([r['stage'] for r in table]==list(STAGES),'cutflow stages missing/changed')
    for row in table:
        total=totals[row['stage']]
        require(lhe_validator.integer(row['raw_events'])==total['raw'] and close(row['source_weight_sum_pb'],total['sum']) and
                close(row['source_weight_sum_squared_pb2'],total['sum2']),'raw counts/signed source sums differ from all100 reco rows')
    return {k:{'raw_events':v['raw'],'source_weight_sum_pb':str(v['sum']),'source_weight_sum_squared_pb2':str(v['sum2'])} for k,v in totals.items()}


def _validate_run(run_dir):
    raw_run=Path(run_dir).expanduser();require(not raw_run.is_symlink(),'symlink run directory forbidden')
    run=raw_run.resolve();require(run.is_dir(),'no preserved physical run directory')
    state=strict_json(run/'run_manifest.json');plan=strict_json(run/'execution_plan.json')
    require(state['status']=='BLOCKED_BR_WEIGHT_CLOSURE' and state['gates']['C']=='PASS_EXPLICIT_ONE_USE_AUTHORIZATION' and
            plan['status']=='PREPARED_FOR_CLAIMED_EXECUTION' and plan['physical_execution_authorized'] is True,
            'no complete actual authorized raw run; METHOD_ONLY/readiness cannot be published')
    require('fixture_scope' not in state and 'fixture_scope' not in plan and state['physical_BR_adoption'] is None and
            state['exclusive_physical_normalization']=='BLOCKED_BR_WEIGHT_CLOSURE','synthetic or unapproved physical normalization')
    literal_counts(state,{'MG5_events_generated':100,'Pythia_events_written':100,'HepMC_validated_events':100,'Delphes_ROOT_entries':100})
    request=state['request'];require(request==plan['requested'] and request['process']=='zh' and type(request['events']) is int and request['events']==100 and
                                  type(request['energy_gev']) is int and request['energy_gev']==13000 and Path(request['output']).resolve()==run,'request/source original100 mismatch')
    require(set(request)=={'process','events','seed','energy_gev','output','max_hours','max_disk_gb'} and type(request['seed']) is int and
            1<=request['seed']<=900000000,'missing/unknown preserved request fields')
    for field,ceiling in (('max_hours',2),('max_disk_gb',5)):
        value=request[field];require(type(value) in (int,float) and math.isfinite(value) and 0<value<=ceiling,'preserved resource bound differs')
    bridge_sha,_=bridge_identity();require(state['bridge_sha256']==plan['bridge_sha256']==bridge_sha and plan['reviewed_base_head']==BASE,'reviewed bridge source changed')
    for path,digest in ((BASELINE,BASELINE_SHA),(OVERLAY,OVERLAY_SHA),(CARD,CARD_SHA)):
        require(sha_file(bounded_file(path))==digest,'historical baseline/H-only overlay changed')
    auth=state['authorization_receipt'];require(plan['claimed_authorization']==auth,'claimed source authorization differs')
    ticket=strict_json(bounded_file(auth['path']));require(sha_file(auth['path'])==auth['sha256'] and ticket['ticket_id']==auth['id']==state['ticket_id'] and
        ticket['authorization_command']==ACK and ticket['status']=='EXPLICIT_USER_AUTHORIZATION' and ticket['request']==request,'actual consumed human receipt absent/contradictory')
    require(Path(auth['path']).name.endswith('.consumed-'+auth['id']),'authorization was not consumed')
    campaign=state['campaign_reservation'];reservation=strict_json(campaign['path'])
    require(sha_file(campaign['path'])==campaign['sha256'] and campaign['ticket_id']==auth['id'] and
            reservation['status']=='RESERVED_SINGLE_100_EVENT_ATTEMPT_NOT_GENERATION_PROOF' and reservation['request']==request and
            reservation['ticket_id']==auth['id'] and reservation['bridge_sha256']==bridge_sha,'single-source campaign reservation differs')
    literal_counts(reservation,{'reserved_events_ceiling':100})
    mg=strict_json(run/'validation/mg5_execution.json');require(mg['authorization_receipt']==auth,'MG source authorization differs')
    require(state['stages']['MG5']==mg and mg['retry_or_event_replacement_performed'] is False,'actual MG stage altered/retried')
    for binding in [*mg['artifacts'].values(),*mg['cards'].values()]:
        path=bounded_file(scoped_path(run,binding['path']),MAX_RECORD_FILE)
        require(sha_file(path)==binding['sha256'] and path.stat().st_size==binding['bytes'],'bound actual MG artifact changed')
    prepared=plan['mg5_prepared'];cards={'profile':'ZH_ZBB_STABLE_H'}
    for key,binding in prepared['cards'].items():
        path=bounded_file(scoped_path(run,binding['path']));require(sha_file(path)==binding['sha256'],'original prepared card changed');cards[key]=path.read_text(encoding='utf-8')
    source_path=scoped_path(run,mg['lhe_path'])
    source=lhe_validator.validate_file(source_path,expected_seed=request['seed'],card_contract=cards,provenance=mg)
    preserved=strict_json(run/'validation/lhe_validation.json')
    for key in ('status','source_file_sha256','decompressed_file_sha256','event_content_sha256','actual_events','events_valid','events_invalid','card_hashes'):
        require(preserved[key]==source[key],'preserved LHE receipt differs from complete fresh record check: '+key)
    plain=bounded_file(run/'validation/original_full100.lhe',MAX_RECORD_FILE)
    require(sha_file(plain)==source['decompressed_file_sha256'],'preserved plain LHE changed')
    from simulation.zh_pilot.phase6g.scripts.shower_stage import source_index_bytes
    index=bounded_file(run/'validation/source_events.dat',MAX_RECORD_FILE)
    require(index.read_bytes()==source_index_bytes(source),'trusted original source DAT differs from exact validated100 source rows')
    build=strict_json(run/'native_build/build_receipt.json');root_build=strict_json(run/'root_build/build_receipt.json')
    require(state['stages']['native_build']==build and state['stages']['root_build']==root_build and build['status']=='PASS_BUILD_AND_METHODS_ONLY' and
            root_build['status']=='PASS_COMPILE_AND_BUILD_INFO_ONLY','original native build receipts differ')
    from simulation.zh_pilot.phase6g.scripts.build_stage import source_bindings
    require(build['source_sha256']==source_bindings() and root_build['source_sha256']==sha_file(REPO/'simulation/zh_pilot/phase6g/src/analyze_zh_root.cxx'),
            'native receipt built different reviewed source')
    stages={}
    for stage,count in (('prefix10',10),('full100',100)):
        stage_auth=strict_json(run/'pythia'/stage/'execution_authorization.json')
        require(stage_auth['authorization_command']==ACK and stage_auth['status']=='AUTHORIZED_EXECUTION_IN_PROGRESS' and stage_auth['reviewed_base_head']==BASE and
                stage_auth['ticket_id']==auth['id'] and stage_auth['bridge_sha256']==bridge_sha and stage_auth['authorization_receipt_sha256']==auth['sha256'] and
                stage_auth['source_request']==request and stage_auth['child_stage']==stage and
                Path(stage_auth['child_output']).resolve()==run/'pythia'/stage,'historical stage authorization binding differs')
        literal_counts(stage_auth,{'source_total_events':100})
        require(stage_auth['source_original_sha256']==source['source_file_sha256'] and stage_auth['source_lhe_sha256']==sha_file(plain) and
                stage_auth['source_index_sha256']==sha_file(index) and Path(stage_auth['source_lhe_path']).resolve()==plain.resolve() and
                Path(stage_auth['source_index_path']).resolve()==index.resolve() and
                stage_auth['native_runner_sha256']==build['binaries']['zh_shower']['sha256'] and
                stage_auth['native_validator_sha256']==build['binaries']['validate_zh_hepmc3']['sha256'],'stage actual source/build hashes differ')
        require(strict_json(run/'validation'/(stage+'_validation.json'))==state['stages'][stage],'preserved stage receipt differs from run manifest')
        stages[stage]=check_stage(run/'pythia'/stage,count,source,request['seed'],state['stages'][stage])
    full=run/'pythia/full100';compressed=gzip_identity(full/'shower.hepmc3.gz',stages['full100']['decompressed_sha256'])
    native=strict_json(run/'delphes/native_validation.json')
    require(native['status']=='PASS_NATIVE_ZH_RECORD_READBACK' and native['root_version']=='6.40.04','actual native ROOT receipt absent')
    literal_counts(native,{'ROOT_entries':100,'source_events':100,'events_assessed':100,'read':100,'processed':100,'invalid':0,'skipped':0,'events_not_assessed':0})
    require(native['profile']=='H_DECAY_PHOTONS_Z_DECAY_BOTTOMS' and native['exclusive_physical_normalization']=='BLOCKED_NO_ADOPTED_PHYSICAL_BR' and
            native['btag_model']=='FAST_SIM_ATLAS_LIKE_BIT0_NOT_OFFICIAL_ATLAS','native profile/normalization contradicts reviewed scope')
    detector=strict_json(run/'validation/detector_validation.json')
    require(detector==state['stages']['Delphes'] and all(detector.get(key)==value for key,value in native.items()),'actual native ROOT receipt differs from saved stage')
    validate_derived_files(run/'delphes',detector)
    for field,path in (('root_sha256',run/'delphes/detector.root'),('input_index_sha256',full/'input_event_index.dat'),
                       ('truth_index_sha256',full/'zh_truth_index.dat'),('card_sha256',run/'delphes/detector_card.tcl')):
        require(sha_file(bounded_file(path,MAX_RECORD_FILE))==native[field],'preserved native ROOT/source/card artifact changed')
    require(native['input_index_sha256']==stages['full100']['reader']['input_index_sha256'] and
            native['truth_index_sha256']==stages['full100']['reader']['truth_index_sha256'] and
            sha_file(bounded_file(run/'delphes/input.hepmc3',MAX_RECORD_FILE))==stages['full100']['decompressed_sha256'],
            'ROOT native adapter is not bound to the actual Reader-verified indices/record')
    with (run/'delphes/detector.root').open('rb') as stream:require(stream.read(4)==b'root','not an actual ROOT file envelope')
    canonical=(run/'delphes/detector_card.tcl').read_bytes();seed_line=f'set RandomSeed {request["seed"]}'.encode()
    require(canonical.count(seed_line)==1 and hashlib.sha256(canonical.replace(seed_line,b'set RandomSeed 610301',1)).hexdigest()==sha_file(CARD),
            'native detector card differs beyond requested seed')
    reco=jsonl(run/'delphes/reco_events.jsonl',100);origins=jsonl(full/'hepmc_ancestry.jsonl',100)
    cutflow=validate_cutflow(run/'delphes/cutflow.csv',reco,source,origins)
    ledger=strict_json(run/'validation/weight_and_BR_ledger.json')
    require(ledger['status']=='OBSERVED_RAW_WEIGHT_TRANSFER_ONLY' and ledger['source_included_decay_ids']==['Z_to_b_bbar'] and
            ledger['source_Z_BR_reapplied'] is False and ledger['physical_BR_adoption'] is None and ledger['external_BR_factors_applied']==[] and
            ledger['physical_BR_factor'] is None and ledger['exclusive_cross_section_pb'] is None and
            ledger['full_original_source_denominator']==100 and ledger['exclusive_physical_normalization']=='BLOCKED_BR_WEIGHT_CLOSURE','unapproved/missing/repeated BR ledger')
    require(ledger==state['weight_and_BR_ledger'] and ledger['binding']==stages['full100']['binding'],'preserved signed-weight binding differs from fresh source/vector check')
    ratios=[lhe_validator.decimal(row['weight_values'][2])/lhe_validator.decimal(row['weight_values'][1]) for row in stages['full100']['records'] if lhe_validator.decimal(row['weight_values'][1])]
    zero=100-len(ratios);literal_counts(ledger,{'full_original_source_denominator':100,'zero_weight_events_ratio_unidentifiable':zero})
    for field,value in (('Info_to_LHE_ratio_min',min(ratios) if ratios else None),('Info_to_LHE_ratio_max',max(ratios) if ratios else None)):
        require(ledger[field] is None if value is None else close(ledger[field],value),'observed raw Info/LHE transfer ratio changed')
    model_reference=Decimal('0.0022965313147512443');actual_model=stages['full100']['summary']['initialized_higgs_decay']
    actual_br=lhe_validator.decimal(actual_model['inclusive_model_BR_gamma_gamma'])
    identity=bool(ratios) and all(abs(r-1)<=Decimal('1e-10') for r in ratios)
    model_match=bool(ratios) and all(abs(r-model_reference)<=Decimal('1e-10')*max(1,abs(r)) for r in ratios)
    actual_match=bool(ratios) and all(abs(r-actual_br)<=Decimal('1e-10')*max(1,abs(r)) for r in ratios)
    classification='IDENTITY' if identity else 'MATCHES_PHASE6F_MODEL_BR_REFERENCE_ONLY' if model_match else 'UNRESOLVED'
    require(ledger['nominal_transfer_class']==classification and ledger['actual_initialized_higgs_decay']==actual_model and
            ledger['actual_model_summary_sha256']==sha_file(full/'run_summary.json') and
            ledger['ratio_matches_actual_initialized_model_BR_numeric_only'] is actual_match and
            ledger['ratio_match_establishes_factor_inclusion'] is False and ledger['planning_missing_decay_ids']==['H_to_gamma_gamma'] and
            lhe_validator.decimal(ledger['Pythia_model_BR_reference_only'])==model_reference and
            lhe_validator.decimal(ledger['CERN_YR4_BR_reference_only'])==Decimal('0.002270'),'model/observed ratio or physical factor-inclusion scope differs')
    paths=[run/'run_manifest.json',run/'execution_plan.json',source_path,*[run/'validation'/name for name in ('mg5_execution.json','lhe_validation.json','weight_and_BR_ledger.json')],
           full/'shower.hepmc3',full/'shower.hepmc3.gz',run/'delphes/detector.root',run/'delphes/native_validation.json',run/'delphes/cutflow.csv',run/'delphes/reco_events.jsonl']
    files={p.relative_to(run).as_posix():{'sha256':sha_file(p),'bytes':p.stat().st_size} for p in paths}
    return {'schema_version':1,'status':'PASS_PRESERVED_RAW_RUN_ONLY','source_total_events':100,'source_cross_section_pb':source['cross_section_pb'],
            'source_integration_uncertainty_pb':source['cross_section_uncertainty_pb'],'source_lhe_sha256':source['source_file_sha256'],
            'source_included_decay_ids':['Z_to_b_bbar'],'physical_BR_adoption':None,'exclusive_physical_normalization':'BLOCKED_BR_WEIGHT_CLOSURE',
            'actual_counts':{'LHE':100,'full_Pythia':100,'full_HepMC_ReaderAscii':100,'ROOT':100},'cutflow':cutflow,'gzip':compressed,
            'files':files,'stages':{name:{k:info[k] for k in ('events','reader_report_sha256','generic_report_sha256','decompressed_sha256','table_hashes','settings_hashes')} for name,info in stages.items()},
            'validation_scope':'Fresh all100 LHE and portable ASCII/CRC/source/weight bindings; native graph/ROOT QA inherited from exact preserved actual receipts',
            'fresh_native_ReaderAscii_executed':False,'fresh_native_ROOT_executed':False,'new_physics_events_generated':0,
            'authorization_receipt_sha256':auth['sha256'],'ticket_id':auth['id']}


def validate_run(run_dir):
    """Never mutates original records, receipts, authorization, or native files."""
    guard={};token=_GUARD.set(guard)
    try:
        result=_validate_run(run_dir);verify_unchanged(guard)
        bridge_sha,_=bridge_identity();require(bridge_sha==strict_json(Path(run_dir)/'run_manifest.json')['bridge_sha256'],'bridge changed during preserved verification')
        run=Path(run_dir).expanduser().resolve()
        result['checked_artifacts']={path.relative_to(run).as_posix():{'sha256':digest,'bytes':size}
            for path,(digest,size) in guard.items() if path.is_relative_to(run)}
        result['preserved_files_checked']=len(guard)
        return result
    finally:_GUARD.reset(token)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--report',type=Path)
    args=parser.parse_args();result=validate_run(args.run)
    if args.report:
        with args.report.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,allow_nan=False));return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
        print('BLOCKED_PRESERVED_RUN: '+str(error),file=sys.stderr);raise SystemExit(2)
