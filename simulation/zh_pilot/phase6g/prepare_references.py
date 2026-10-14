#!/usr/bin/env python3
"""Prepare a bounded local review copy of one actual authorized ZH100 raw run.

No Git staging, pushing, event processing, BR adoption, or receipt overwriting.
All source validation and byte-budget checks precede destination creation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO))
from simulation.zh_pilot.phase6g.common import require,sha_file
from simulation.zh_pilot.phase6g.validate_run import validate_run,strict_json,bounded_file

MAX_ASSET=30*1024**2
MAX_COMBINED_ASSETS=30*1024**2
MAX_TEXT=2*1024**2
MAX_COMBINED_TEXT=16*1024**2


def protected_roots():
    """Reuse the immutable readiness protection contract for sources/builds/data."""
    sys.path.insert(0,str(REPO/'simulation/zh_pilot/scripts'))
    from prepare_pilot import configured_protected_paths
    roots=[]
    for name in ('mg5_installation.json','pythia8_installation.json','delphes_installation.json'):
        config=strict_json(REPO/'.local'/name)
        roots.extend(Path(path).expanduser().resolve() for path in configured_protected_paths(config))
        if config.get('xml_path'):roots.append(Path(config['xml_path']).expanduser().resolve())
        for value in config.get('phase6b_runs',{}).values():
            source_run=Path(value).expanduser().resolve()
            roots.append(source_run.parent.parent/'delphes_runs')
    return roots


def encoded(value):
    return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')


def safe_destination(destination,run):
    raw=Path(destination).expanduser()
    require(not raw.exists() and not raw.is_symlink(),'reference destination exists; choose a fresh local review directory')
    for parent in raw.parents:require(not parent.is_symlink(),'symlink reference destination ancestor forbidden')
    resolved=raw.resolve();run=Path(run).resolve()
    require(resolved!=run and not resolved.is_relative_to(run) and not run.is_relative_to(resolved),
            'reference destination overlaps original preserved run')
    require(resolved!=REPO and not REPO.is_relative_to(resolved),'reference destination is repository root/ancestor')
    for protected in protected_roots():
        require(resolved!=protected and not resolved.is_relative_to(protected) and not protected.is_relative_to(resolved),
                'reference destination overlaps retained scientific source/build/installation/data tree')
    return resolved


def inspect_plan(items):
    """Size/hash preflight of exact inputs or explicitly derived receipt bytes."""
    assets=0;text=0;seen=set();result=[]
    for item in items:
        relative=Path(item['path']);require(not relative.is_absolute() and '..' not in relative.parts and relative.as_posix() not in seen,
            'invalid/duplicate selected package path');seen.add(relative.as_posix())
        category=item['category'];require(category in ('ASSET','TEXT'),'unknown reference category')
        if 'source' in item:
            source=bounded_file(item['source'],MAX_ASSET if category=='ASSET' else MAX_TEXT)
            count=source.stat().st_size;digest=sha_file(source)
            require(digest==item['expected_sha256'],'selected original bytes changed since validation')
        else:
            require(category=='TEXT' and type(item.get('data')) is bytes,'derived data must be bounded text receipt bytes')
            count=len(item['data']);digest=hashlib.sha256(item['data']).hexdigest()
        require(count<=(MAX_ASSET if category=='ASSET' else MAX_TEXT),'selected file exceeds byte limit: '+relative.as_posix())
        if category=='ASSET':assets+=count
        else:text+=count
        result.append({**item,'bytes':count,'sha256':digest})
    require(sum(i['category']=='ASSET' for i in result)==3 and assets<=MAX_COMBINED_ASSETS,'three selected assets exceed combined30MiB budget')
    require(text<=MAX_COMBINED_TEXT,'selected bounded text exceeds combined16MiB budget')
    return result,{'asset_files':3,'asset_bytes':assets,'text_bytes':text,'per_asset_bytes':MAX_ASSET,
        'combined_asset_bytes':MAX_COMBINED_ASSETS,'per_text_file_bytes':MAX_TEXT,'combined_text_bytes':MAX_COMBINED_TEXT}


def selection_plan(run,validation):
    require(validation.get('status')=='PASS_PRESERVED_RAW_RUN_ONLY' and validation.get('source_total_events')==100 and
        validation.get('physical_BR_adoption') is None and validation.get('exclusive_physical_normalization')=='BLOCKED_BR_WEIGHT_CLOSURE' and
        validation.get('fresh_native_ReaderAscii_executed') is False and validation.get('fresh_native_ROOT_executed') is False,
        'only complete actual authorized raw runs can prepare references; METHOD_ONLY is rejected')
    run=Path(run).resolve();checked=validation['checked_artifacts'];items=[]
    def exact(original,target,category='TEXT'):
        original=Path(original);require(not original.is_symlink() and original.resolve().is_relative_to(run),'selected original escapes actual run')
        relative=original.relative_to(run).as_posix();require(relative in checked,'selected file was not part of preserved validation')
        items.append({'source':original,'path':target,'category':category,'expected_sha256':checked[relative]['sha256'],
            'provenance':'EXACT_ORIGINAL_BYTES','original_run_relative_path':relative})
    def derived(value,target,receipt=None):
        if receipt is not None:
            value={**value,'original_receipt_sha256':checked[receipt]['sha256'],'projection_scope':'DERIVED_BOUNDED_FIELDS; original receipt kept in local preserved run'}
        items.append({'data':encoded(value),'path':target,'category':'TEXT','provenance':'DERIVED_RECEIPT_PROJECTION'})
    mg=strict_json(run/'validation/mg5_execution.json');plan=strict_json(run/'execution_plan.json')
    exact(Path(mg['lhe_path']),'mg5/reference_100.lhe.gz','ASSET')
    exact(run/'pythia/full100/shower.hepmc3.gz','pythia8/reference_100.hepmc3.gz','ASSET')
    exact(run/'delphes/detector.root','delphes/detector_100.root','ASSET')
    for key,name in (('process_card','process_card.mg5'),('run_card','run_card.dat'),('param_card','param_card.dat')):
        exact(Path(plan['mg5_prepared']['cards'][key]['path']),'mg5/'+name)
    exact(Path(mg['artifacts']['banner']['path']),'mg5/banner.txt')
    original_lhe=strict_json(run/'validation/lhe_validation.json')
    fields=('schema_version','status','physical_pilot_acceptance','exclusive_physical_normalization','physical_BR_adoption',
        'source_file_sha256','compressed_file_sha256','decompressed_file_sha256','event_content_sha256','header_sha256',
        'actual_events','source_total_events','events_assessed','events_valid','events_invalid','events_not_assessed',
        'cross_section_pb','cross_section_uncertainty_pb','banner_cross_section_pb','idwtup','beam_energies_gev','seed','card_hashes',
        'weights','source_included_decay_ids','missing_decay_ids','maximum_closure_residual_gev','maximum_mass_shell_residual_gev2',
        'distinct_source_event_hashes','independence_scope')
    projection={key:original_lhe[key] for key in fields}
    projection['source_events']=[{key:event[key] for key in ('source_event_index','source_event_content_hash','nominal_generator_weight',
        'scale_gev','aqed','aqcd','original_resonance_and_bottom_ids')} for event in original_lhe['source_events']]
    derived(projection,'validation/lhe_validation.json','validation/lhe_validation.json')
    identity=mg['source_identity']
    derived({'schema_version':1,'status':'BOUND_ACTUAL_GENERATOR_OUTPUT; physical records validated separately',
        'source_identity':{key:identity[key] for key in ('source_url','source_commit','source_tag','version')},
        'request':mg['request'],'generation':mg['generation'],'source_included_decay_ids':['Z_to_b_bbar'],
        'original_authorization_receipt_sha256':validation['authorization_receipt_sha256'],'original_ticket_id':validation['ticket_id'],
        'actual_cards_sha256':original_lhe['card_hashes'],'physical_BR_adoption':None,
        'exclusive_physical_normalization':'BLOCKED_BR_WEIGHT_CLOSURE'},'validation/generator_provenance.json','validation/mg5_execution.json')
    for filename in ('run_summary.json','event_ledger.jsonl','hepmc_ancestry.jsonl','zh_truth_index.dat',
        'zh_hepmc_validation.json','generic_physics_validation.json','effective_settings.cmnd','inclusive_initialized_settings.cmnd',
        'decay_tables_original_preinit.json','decay_tables_inclusive_initialized.json','decay_tables_initialized.json',
        'original_particle_data.xml','inclusive_initialized_particle_data.xml','effective_particle_data.xml'):
        exact(run/'pythia/full100'/filename,'pythia8/'+filename)
    for filename in ('native_validation.json','reco_events.jsonl','cutflow.csv','detector_card.tcl'):
        exact(run/'delphes'/filename,'delphes/'+filename)
    exact(run/'validation/weight_and_BR_ledger.json','validation/weight_and_BR_ledger.json')
    derived(validation,'validation/preserved_run_verification.json')
    return items


def prepare_references(run_dir,destination=None):
    raw_run=Path(run_dir).expanduser();validation=validate_run(raw_run);run=raw_run.resolve()
    destination=safe_destination(destination if destination is not None else run.parent/(run.name+'_reference_review')/'reference_samples/zh',run)
    items,limits=inspect_plan(selection_plan(run,validation))
    # All actual-source, authorization, CRC, native receipt and size gates passed.
    # Existence is checked again before the first write; no overwrite is allowed.
    require(not destination.exists(),'reference destination appeared during preflight')
    listed=[{key:item[key] for key in ('path','category','bytes','sha256','provenance')} for item in items]
    report={'schema_version':1,'status':'PREPARED_LOCAL_REFERENCE_REVIEW_ONLY','source_count':100,'files':listed,'limits':limits,
        'physical_BR_adoption':None,'exclusive_physical_normalization':'BLOCKED_BR_WEIGHT_CLOSURE','Git_staged':False,'Git_pushed':False,
        'native_QA_scope':'Exact original native receipts; no fresh native validation during copying',
        'no_graph_reserialization':True,'new_physics_events_generated':0,
        'publication_status':'LOCAL_REVIEW; exact embedded generator cards/banner may retain original output paths; no automatic Git action'}
    report_bytes=encoded(report);require(len(report_bytes)<=MAX_TEXT,'reference manifest exceeds text budget')
    destination.mkdir(parents=True,exist_ok=False)
    copied=[]
    try:
        for item in items:
            target=destination/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
            digest=hashlib.sha256();total=0
            with target.open('xb') as output:
                if 'source' in item:
                    with item['source'].open('rb') as source:
                        for block in iter(lambda:source.read(65536),b''):
                            total+=len(block);require(total<=item['bytes'],'selected source grew during copy');output.write(block);digest.update(block)
                else:output.write(item['data']);digest.update(item['data']);total=len(item['data'])
            require(total==item['bytes'] and digest.hexdigest()==item['sha256'],'selected source bytes changed during copy')
            copied.append({key:item[key] for key in ('path','category','bytes','sha256','provenance')})
        # Recheck the original inputs copied after the final write, without rerunning physics.
        for item in items:
            if 'source' in item:require(sha_file(item['source'])==item['sha256'],'selected original changed during reference preparation')
        for relative,identity in validation['checked_artifacts'].items():
            original=run/relative;require(original.is_file() and not original.is_symlink() and original.stat().st_size==identity['bytes'] and
                sha_file(original)==identity['sha256'],'actual source/receipt changed during reference preparation')
        with (destination/'reference_manifest.json').open('xb') as stream:stream.write(report_bytes)
        return report
    except BaseException:
        # Preserve partial copy evidence instead of deleting or mislabelling it.
        failure={'schema_version':1,'status':'PARTIAL_REFERENCE_PREPARATION_NOT_PUBLISHABLE','copied_files':copied,'new_physics_events_generated':0}
        with (destination/'PREPARATION_FAILED.json').open('xb') as stream:stream.write(encoded(failure))
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output','--destination',dest='output',type=Path)
    args=parser.parse_args();print(json.dumps(prepare_references(args.run,args.output),indent=2,allow_nan=False));return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
        print('BLOCKED_REFERENCE_PREPARATION: '+str(error),file=sys.stderr);raise SystemExit(2)
