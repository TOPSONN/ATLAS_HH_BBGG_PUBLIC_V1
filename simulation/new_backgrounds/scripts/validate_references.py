#!/usr/bin/env python3
"""Portable byte/count/CRC audit of selected genuine background references.

This does not rerun native ReaderAscii, ROOT or any generator. Bound original
native receipts retain that separate scope. No installation is needed by CI.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
import gzip
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[3]
PREFIX='reference_samples/new_backgrounds/'
PROCESSES={'zh':('B04_ZH','B04_ZH_BBGG'),'tth':('B05_TTH','B05_TTH_HGG'),'bbgj':('B06_BBGJ','B06_BBGJ')}
MAX_FILE=20*1024**2
MAX_PACKAGE=60*1024**2
MAX_TEXT=2*1024**2
MAX_JSON=2*1024**2
DATA_SIDECARS=('pythia8/input_event_index.dat','pythia8/background_truth_index.dat')
MAX_INFLATED=128*1024**2
HASH=re.compile(r'[0-9a-f]{64}\Z')
FORBIDDEN=(b'/'+b'home/',b'/'+b'mnt/'+b'c/'+b'HH',b'C:'+b'\\'+b'HH',b'C:'+b'/'+b'HH',
    b'C:'+b'\\'+b'Users'+b'\\',b'C:'+b'/'+b'Users'+b'/',b'METHOD_ONLY',b'SYNTHETIC')
ASSETS={'mg5/reference_1000.lhe.gz':('MG5_FULL1000',1000),'pythia8/reference_100.hepmc3.gz':('HEPMC_PREFIX100_FROM_FULL1000',100),'delphes/detector_100.root':('DELPHES_PREFIX100',100)}
REQUIRED_TEXT=('mg5/process_card.mg5','mg5/run_card.dat','mg5/param_card.dat',
 'pythia8/input_event_index.dat','pythia8/background_truth_index.dat','pythia8/hepmc_ancestry_100.jsonl',
 'pythia8/event_ledger_100.jsonl','delphes/reco_events_100.jsonl','delphes/detector_card.tcl',
 'validation/lhe_full1000.json','validation/hepmc_full1000.json','validation/root_full1000.json',
 'validation/root_prefix100.json','validation/full_chain.json','validation/weight_and_BR_ledger.json',
 'validation/cutflow_statistics.json','validation/generator_contract.json')


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(data):return hashlib.sha256(data).hexdigest()


def load_json_bytes(data,max_bytes=MAX_JSON):
    require(type(data) is bytes and len(data)<=max_bytes,'Oversized/invalid JSON receipt')
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out,'Duplicate JSON evidence key');out[key]=value
        return out
    def invalid(value):raise ValueError('Nonfinite JSON evidence: '+value)
    value=json.loads(data.decode('utf-8'),object_pairs_hook=pairs,parse_constant=invalid)
    def finite(item):
        if isinstance(item,dict):
            for child in item.values():finite(child)
        elif isinstance(item,list):
            for child in item:finite(child)
        elif isinstance(item,float):require(math.isfinite(item),'Overflowed JSON evidence number')
    finite(value);return value


def path_key(value):
    require(type(value) is str and value and '\\' not in value and ':' not in value,'Invalid repository-relative reference path')
    path=PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and '.' not in path.parts,'Unsafe reference path')
    require(path.as_posix()==value,'Noncanonical reference path')
    return value


def scan_private(data,label):
    lower=data.lower()
    for token in FORBIDDEN:require(token.lower() not in lower,'Private path or synthetic marker in selected reference: '+label)
    require(re.search(rb'[A-Za-z]:[\\/](?:Users|HH)(?:[\\/]|\b)',data,re.I) is None,'Private Windows path in '+label)


def inflate(data,label):
    require(type(data) is bytes and len(data)<MAX_FILE,'Selected file exceeds ordinary-Git size policy')
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
        raw=stream.read(MAX_INFLATED+1)
        require(len(raw)<=MAX_INFLATED,'Oversized gzip inflation')
        require(not stream.read(1),'Trailing inflated data')
    scan_private(raw,label);return raw


def number(value):
    require(type(value) is not bool,'Boolean physics number')
    result=Decimal(str(value).replace('D','E').replace('d','e'))
    require(result.is_finite(),'Nonfinite physics number');return result


def close(a,b):return abs(number(a)-number(b))<=Decimal('1e-12')+Decimal('2e-12')*max(abs(number(a)),abs(number(b)))


def json_rows(data,count):
    lines=data.splitlines();require(len(lines)==count and all(lines),'Wrong actual reference ledger row count')
    return [load_json_bytes(line) for line in lines]


def lhe_check(raw,receipt,manifest,contract):
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(),'Unsafe LHE XML declaration')
    root=ET.fromstring(raw)
    require(root.tag=='LesHouchesEvents' and root.attrib=={'version':'3.0'},'Wrong physical LHE version')
    require(len(root.findall('header'))==len(root.findall('init'))==1,'LHE schema/header duplication')
    header=root.find('header');require('3.5.16' in ET.tostring(header,encoding='unicode'),'Missing actual MG5 version')
    for key,tag in {'process_card':'MG5ProcCard','run_card':'MGRunCard','param_card':'slha'}.items():
        section=header.find(tag);require(section is not None and sha((section.text or '').encode('utf-8'))==receipt['card_hashes'][key],
            'Original LHE actual header card identity mismatch')
    init=[line.split() for line in (root.find('init').text or '').splitlines() if line.strip() and not line.lstrip().startswith('#')]
    require(len(init)==2 and len(init[0])==10 and len(init[1])==4,'LHE init schema mismatch')
    require([int(x) for x in init[0][:2]]==[2212,2212] and [number(x) for x in init[0][2:4]]==[6500,6500] and int(init[0][8])==-4 and int(init[0][9])==1,'LHE beam/strategy convention mismatch')
    require(number(init[1][0])==number(manifest['cross_section_pb'])==number(receipt['cross_section_pb']) and number(init[1][1])==number(manifest['integration_uncertainty_pb'])==number(receipt['cross_section_uncertainty_pb']),'LHE actual sigma/error binding mismatch')
    elements=root.findall('event');blocks=re.findall(rb'<event>.*?</event>',raw,re.S)
    require(len(elements)==len(blocks)==1000 and all(child.tag in ('header','init','event') for child in root),'Full original1000 LHE records required')
    identities=receipt['source_events'];require(len(identities)==1000,'Missing actual full source identity ledger')
    # Independent source math/cut checks reuse the same reviewed process-specific
    # stdlib parser. This does not invoke its live-provenance/installation API.
    sys.path.insert(0,str(REPO))
    from simulation.new_backgrounds.validate_lhe import event_particles
    process=manifest['process'];physics=dict(contract['physics'])
    physics['scales']=contract['profiles'][process]['scale_configuration'];physics['generation_cuts']=contract['profiles'][process]['generation_cuts']
    if process=='zh':physics=contract['frozen_phase6f_reference_physics']
    seen=set()
    for index,(event,block,identity) in enumerate(zip(elements,blocks,identities),1):
        require(identity['source_event_index']==index and identity['source_event_content_hash']==sha(block) and sha(block) not in seen,'Original source identity mismatch/duplicate')
        seen.add(sha(block));parsed=event_particles(event,process,physics)
        require(parsed['process_id']==int(init[1][3]) and number(parsed['weight'])==number(identity['nominal_generator_weight']),'Original source weight/process mismatch')
    require(receipt['decompressed_file_sha256']==sha(raw),'Exact original uncompressed LHE identity changed')
    require(receipt['status']=='PASS_LHE_RECORDS' and receipt['actual_events']==receipt['events_valid']==receipt['events_assessed']==1000 and receipt['events_invalid']==receipt['events_not_assessed']==0 and receipt['idwtup']==-4,'Original actual LHE receipt did not PASS all1000')
    return identities


def hepmc_blocks(raw):
    require(raw.startswith(b'HepMC::Version 3.03.01\nHepMC::Asciiv3-START_EVENT_LISTING\n') and raw.endswith(b'HepMC::Asciiv3-END_EVENT_LISTING\n') and b'\r' not in raw,'Invalid native HepMC3 envelope')
    lines=raw.splitlines(keepends=True);header=[];blocks=[];block=[];ended=False
    for line in lines:
        require(len(line)<=8*1024**2,'Oversized HepMC ASCII line')
        if line.startswith(b'E '):
            require(not ended,'HepMC event after trailer')
            if block:blocks.append(b''.join(block))
            block=[line]
        elif line==b'HepMC::Asciiv3-END_EVENT_LISTING\n':
            require(not ended and block,'Duplicate/missing native HepMC trailer');blocks.append(b''.join(block));block=[];ended=True
        elif block:block.append(line)
        elif not ended:header.append(line)
        else:require(not line.strip(),'HepMC data after trailer')
    require(ended and len(blocks)==100,'Exactly100 actual full-shower prefix events required')
    return header,blocks


def dat_events(data,magic):
    lines=data.decode('ascii').splitlines();require(lines and lines[0]==magic,'Native reference sidecar magic mismatch')
    records=[];row=[]
    for line in lines[1:]:
        if line.startswith('E '):
            if row:records.append(row)
            row=[line.split()]
        else:require(row,'Sidecar row precedes event');row.append(line.split())
    if row:records.append(row)
    require(len(records)==100,'Reference sidecar must contain100 actual events');return records


def truth_shape(record,ordinal):
    require(len(record)==8 and len(record[0])==9 and record[0][0]=='E' and
        int(record[0][1])==int(record[0][2])==ordinal,'Native truth prefix source/order/cardinality mismatch')
    for marker,group in zip('HGBOSDX',record[1:]):
        require(len(group)>=2 and group[0]==marker and int(group[1])==len(group)-2,'Native truth category/count mismatch')


def hepmc_check(raw,files,identities,manifest):
    header,blocks=hepmc_blocks(raw)
    names_line=next((line[2:].decode().strip() for line in header if line.startswith(b'W ')),None)
    require(names_line is not None,'HepMC named provenance weights missing');names=names_line.split('\\|')
    require(names[:3]==['input_contribution_pb','LHE_XWGTUP_pb','Pythia_Info_weight_pb'] and len(names)>=4,'HepMC named weight convention changed')
    index=dat_events(files['pythia8/input_event_index.dat'],'ATLAS_DELPHES_INPUT_V1')
    truth=dat_events(files['pythia8/background_truth_index.dat'],'ATLAS_NEW_BACKGROUND_TRUTH_V1')
    ancestry=json_rows(files['pythia8/hepmc_ancestry_100.jsonl'],100)
    attempts=json_rows(files['pythia8/event_ledger_100.jsonl'],100)
    reco=json_rows(files['delphes/reco_events_100.jsonl'],100)
    hashes=[]
    for ordinal,(block,expected,idx,truth_row,row,attempt,detector) in enumerate(zip(blocks,identities,index,truth,ancestry,attempts,reco),1):
        lines=block.decode().splitlines();event=lines[0].split();require(len(event)==4 and int(event[1])==ordinal,'HepMC event order/schema mismatch')
        require(lines.count('U GEV MM')==1,'HepMC units changed')
        attributes={}
        for line in lines:
            if line.startswith('A 0 '):
                parts=line.split(' ',3);require(len(parts)==4 and parts[2] not in attributes,'Duplicate/truncated event attribute');attributes[parts[2]]=parts[3]
        expected_attrs={'source_sample_id':manifest['profile'],'source_lhe_profile':manifest['profile'],'process_alias':manifest['process'],
            'source_file_sha256':manifest['full_source_identities']['lhe_gz_sha256'],'source_event_index':str(ordinal),
            'source_event_content_hash':expected['source_event_content_hash'],'source_total_events':'1000','output_event_index':str(ordinal),
            'pythia_seed':str(manifest['seeds']['Pythia'])}
        require(all(attributes.get(key)==value for key,value in expected_attrs.items()),'HepMC actual original source/provenance mismatch')
        values=[number(v) for v in next(line[2:] for line in lines if line.startswith('W ')).split()]
        require(len(values)==len(names) and close(values[0],number(expected['nominal_generator_weight'])/1000) and close(values[1],expected['nominal_generator_weight']) and close(values[2],values[3]),'HepMC raw/fullN/Info-converter weight closure mismatch')
        particles=[line.split() for line in lines if line.startswith('P ')]
        require(len(particles)==int(event[3]) and all(len(p)==10 for p in particles),'HepMC particle record count/schema mismatch')
        native={int(p[1]):p for p in particles};require(len(native)==len(particles),'Duplicate native particle ID')
        for p in particles:
            require(int(p[1])>0 and int(p[9])>0,'Invalid native particle identity/status')
            for value in p[4:9]:number(value)
        digest=sha(block);hashes.append(digest);fields=idx[0]
        require(len(fields)==11 and int(fields[1])==int(fields[2])==int(fields[4])==ordinal and fields[3]==digest and fields[5]==expected['source_event_content_hash'] and int(fields[8])==1000 and int(fields[9])==len(particles) and int(fields[10])==len(values),'Exact native prefix index source mapping changed')
        require(idx[1][0]=='W' and len(idx[1])-1==len(values) and all(close(a,b) for a,b in zip(idx[1][1:],values)) and len(idx)==len(particles)+2,'Native index weight/cardinality mismatch')
        for p in idx[2:]:
            require(len(p)==14 and p[0]=='P' and int(p[1]) in native,'Native index particle schema mismatch');other=native[int(p[1])]
            require(int(p[2])==int(other[3]) and int(p[3])==int(other[9]) and all(close(a,b) for a,b in zip(p[4:9],other[4:9])),'Native index/HepMC actual particle tuple mismatch')
        truth_shape(truth_row,ordinal)
        for marker,group in zip('HGBOSDX',truth_row[1:]):require(group[0]==marker and int(group[1])==len(group)-2 and all(int(i) in native for i in group[2:]),'Native truth category/count/ID mismatch')
        require(row['source_event_index']==attempt['source_event_index']==detector['source_event_index']==ordinal and row['source_event_content_hash']==attempt['source_event_content_hash']==detector['source_event_sha256']==expected['source_event_content_hash'],'Reference event ledgers not matched to original source')
        require(row['event_block_sha256']==attempt['output_event_hash']==detector['hepmc_event_sha256']==digest and row['source_total_events']==attempt['source_total_events']==detector['original_source_events']==1000,'Reference event/block identity or denominator changed')
        require(attempt['processing_status']=='WRITTEN' and row['weight_names']==names and all(close(a,b) for a,b in zip(row['weights_pb'],values)),'Native actual write ledger/weight mismatch')
    return hashes


def bundle_check(base,manifest,allfiles):
    require(manifest.get('schema_version')==1 and manifest.get('status')=='PASS_VALIDATED_REFERENCE_BUNDLE','Unverified selected physical reference manifest')
    process=manifest['process'];require(process in PROCESSES and base==PREFIX+PROCESSES[process][0]+'/' and manifest['profile']==PROCESSES[process][1],'Process reference directory/profile mismatch')
    listed={};total=0
    for row in manifest['files']:
        relative=path_key(row['path']);require(relative not in listed and HASH.fullmatch(row['sha256']) and type(row['bytes']) is int and 0<row['bytes']<MAX_FILE,'Invalid/duplicate/large selected manifest file')
        key=base+relative;require(key in allfiles,'Selected physical reference file missing: '+key);data=allfiles[key]
        require(type(data) is bytes and len(data)==row['bytes'] and sha(data)==row['sha256'],'Selected reference exact bytes/SHA changed: '+key)
        require(Path(relative).suffix.lower() not in ('.pdf','.png','.exe','.so','.dll'),'Unapproved figure/build payload forbidden')
        if row['category']=='TEXT':require(relative not in ASSETS and len(data)<(MAX_FILE if relative in DATA_SIDECARS else MAX_TEXT),'Reference text/physical asset category exceeds bound');scan_private(data,key)
        elif row['category']=='ASSET':require(relative in ASSETS and row['role']==ASSETS[relative][0] and row['events']==ASSETS[relative][1] and row['full_source_events']==1000,'Wrong selected physical asset/count scope')
        else:raise ValueError('Unknown selected file category')
        listed[relative]=data;total+=len(data)
    require(total<MAX_PACKAGE and set(ASSETS).issubset(listed) and all(name in listed for name in REQUIRED_TEXT),'Incomplete or oversized verified reference bundle')
    expected_keys={base+name for name in listed}|{base+'manifest.json'}
    require({key for key in allfiles if key.startswith(base)}==expected_keys,'Unlisted file in selected reference directory')
    receipts={name:load_json_bytes(listed['validation/'+name+'.json']) for name in ('lhe_full1000','hepmc_full1000','root_full1000','root_prefix100','full_chain','weight_and_BR_ledger','cutflow_statistics','generator_contract')}
    source_ids=manifest['full_source_identities'];require(all(HASH.fullmatch(source_ids[key]) for key in ('lhe_gz_sha256','lhe_plain_sha256','hepmc_plain_sha256','root_sha256')),'Missing exact local full1000 identities')
    require(source_ids['lhe_gz_sha256']==sha(listed['mg5/reference_1000.lhe.gz']),'Selected MG source is not original full1000')
    lhe_raw=inflate(listed['mg5/reference_1000.lhe.gz'],'original genuine LHE');require(sha(lhe_raw)==source_ids['lhe_plain_sha256'],'Original LHE decompressed SHA changed')
    identities=lhe_check(lhe_raw,receipts['lhe_full1000'],manifest,receipts['generator_contract'])
    hmc=receipts['hepmc_full1000'];require(hmc['validation_status']=='PASS_BACKGROUND_HEPMC_RECORDS' and hmc['N_readback']==hmc['N_passed_validation']==hmc['source_total_events']==1000 and hmc['N_failed_validation']==0 and hmc['source_file_sha256']==source_ids['lhe_gz_sha256'] and hmc['decompressed_file_sha256']==source_ids['hepmc_plain_sha256'],'Local full1000 native ReaderAscii gate/identity mismatch')
    for name,count in (('root_full1000',1000),('root_prefix100',100)):
        report=receipts[name];require(report['status']=='PASS_NATIVE_BACKGROUND_RECORD_READBACK' and report['ROOT_entries']==report['processed']==report['subset_events']==count and report['source_events']==1000 and report['invalid']==report['skipped']==0 and report['root_version']=='6.40.04' and report['process']==process,'Original native ROOT count/schema gate mismatch')
        require(report['schema'] and all(type(row['present']) is bool for row in report['schema']),'Missing actual compatible dictionary/schema evidence')
    require(receipts['root_full1000']['root_sha256']==source_ids['root_sha256'],'Full local ROOT identity changed')
    root_data=listed['delphes/detector_100.root'];scan_private(root_data,'original100 ROOT');require(root_data.startswith(b'root') and receipts['root_prefix100']['root_sha256']==sha(root_data),'ROOT magic/exact bound actual100-entry QA changed')
    require(receipts['root_prefix100']['input_index_sha256']==sha(listed['pythia8/input_event_index.dat']) and receipts['root_prefix100']['truth_index_sha256']==sha(listed['pythia8/background_truth_index.dat']) and receipts['root_prefix100']['card_sha256']==sha(listed['delphes/detector_card.tcl']),'Selected actual ROOT inputs/sidecars/card mismatch')
    summary=receipts['full_chain'];require(summary['physical_generation_completed'] is True and summary['MG5_events_generated']==summary['Pythia_events_attempted']==summary['Pythia_events_written']==summary['HepMC_validated_events']==summary['Delphes_ROOT_entries']==1000,'Actual local full chain target counts not all met')
    stats=receipts['cutflow_statistics'];require(stats['status']=='PASS_INDEPENDENT_FULL1000_NUMERICAL_READBACK' and stats['source_events']==1000 and stats['native_root_sha256']==source_ids['root_sha256'],'Actual full1000 numerical/statistical gate not met')
    raw=inflate(listed['pythia8/reference_100.hepmc3.gz'],'genuine full-source HepMC prefix');blocks=hepmc_check(raw,listed,identities[:100],manifest)
    require(blocks==manifest['reference_hepmc_block_sha256'] and sha(raw)==manifest['reference_hepmc_plain_sha256'],'Selected100 event blocks changed after native/full1000 validation')
    ledger=receipts['weight_and_BR_ledger'];require(ledger['full_original_source_denominator']==1000 and ledger['Z_BR_reapplied'] is False and ledger['HH_factor_two_applied'] is False,'Source decay/normalization factors changed')
    require(ledger['weight_closure']=='PASS' and ledger['nominal_transfer_class']=='IDENTITY' and
        close(ledger['observed_Info_to_LHE_ratio_min'],1) and close(ledger['observed_Info_to_LHE_ratio_max'],1),
        'Actual full1000 raw/Info/converter and missing-factor closure not PASS')
    if process!='bbgj':
        require(ledger['status']=='PASS_MODEL_BR_WEIGHT_CLOSURE' and ledger['scope']=='MODEL_BR_ONLY' and ledger['factor_applications']==1,'Unverified or repeated model H BR')
        model=ledger['actual_initialized_higgs_decay'];br=number(model['inclusive_model_BR_gamma_gamma'])
        require(model['applicable'] is True and 0<br<1 and close(ledger['factor'],br) and number(model['conditional_forced_probability'])==1 and
            close(number(model['partial_width_gamma_gamma_GeV'])/number(model['total_width_GeV']),br),'Actual initialized model/forced H BR width convention mismatch')
        for key,filename in (('inclusive_table_sha256','decay_tables_inclusive_initialized.json'),('effective_table_sha256','decay_tables_initialized.json'),('original_preinit_table_sha256','decay_tables_original_preinit.json')):
            require('pythia8/'+filename in listed and sha(listed['pythia8/'+filename])==model[key],'Actual initialized decay snapshot changed')
        require(hmc['higgs_two_photon_birth_events']==1000,'Actual all1000 H-to-gamma-gamma birth gate incomplete')
    else:require(ledger['status']=='PASS_RAW_WEIGHT_CLOSURE' and ledger['scope']=='NO_HIGGS_BR' and ledger['factor_applications']==0 and hmc['one_Born_photon_identity_events']==1000,'B06 raw one-Born/no-H-BR scope mismatch')
    return {'process':process,'profile':manifest['profile'],'status':'PASS_PORTABLE_REFERENCE_BYTE_COUNTS_CRC_AND_BOUND_NATIVE_RECEIPTS',
            'full_local_source_events':1000,'selected_LHE_events':1000,'selected_HepMC_events':100,'selected_ROOT_entries_bound_native_QA':100,
            'fresh_native_ReaderAscii_executed':False,'fresh_native_ROOT_executed':False,'files':len(listed),'bytes':total,
            'validated_physical_paths':[{ 'path':base+name,'sha256':sha(listed[name]),'events':ASSETS[name][1],
                'local_full1000_native_QA':'BOUND_ORIGINAL_PASS_NOT_REEXECUTED'} for name in ASSETS]}


def validate_files(files):
    """Validate exact Git blobs supplied by the auditor, never the working tree."""
    require(type(files) is dict and files,'No selected physical reference bundle provided')
    selected={}
    for key,data in files.items():
        path_key(key)
        if key.startswith(PREFIX):require(type(data) is bytes and len(data)<MAX_FILE,'Oversized/invalid reference blob');selected[key]=data
    manifests=sorted(key for key in selected if key.endswith('/manifest.json'))
    require(manifests and len(manifests)<=3,'Missing or excessive process reference manifests')
    allowed=set();results=[]
    for key in manifests:
        base=key[:-len('manifest.json')];manifest=load_json_bytes(selected[key]);scan_private(selected[key],key)
        result=bundle_check(base,manifest,selected);results.append(result);allowed.update(k for k in selected if k.startswith(base))
    require(allowed==set(selected),'Unmanifested selected reference process payload')
    return {'schema_version':1,'status':'PASS_PORTABLE_SELECTED_REFERENCE_BUNDLES','processes':results,
        'validated_physical_paths':[item for result in results for item in result['validated_physical_paths']],
        'new_events_generated':0,'fresh_native_ReaderAscii_executed':False,'fresh_native_ROOT_executed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=REPO);args=parser.parse_args()
    root=args.repo.resolve();folder=root/PREFIX;require(folder.is_dir(),'No selected published references')
    files={}
    for path in folder.rglob('*'):
        require(not path.is_symlink(),'Symlink in selected references')
        if path.is_file():require(path.stat().st_size<MAX_FILE,'Oversized selected reference file');files[path.relative_to(root).as_posix()]=path.read_bytes()
    print(json.dumps(validate_files(files),indent=2,allow_nan=False));return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,StopIteration,ET.ParseError) as error:
        print('BLOCKED_REFERENCE_READBACK: '+str(error),file=sys.stderr);raise SystemExit(2)
