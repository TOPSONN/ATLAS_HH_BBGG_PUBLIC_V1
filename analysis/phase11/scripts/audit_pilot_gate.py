#!/usr/bin/env python3
"""Bind actual static/existing-data evidence to an inactive pilot decision. No dispatch."""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from pilot_policy import validate_contract,validate_inactive_card,select_component,PHYSICAL_GATES,COUNTERS,demand

def load(p):return json.loads(p.read_text())
def binding(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def current_source_integrity(a,b,d,i):
 """Recheck exact receipt bytes now; never normalize, repair or overwrite inputs."""
 records=[];mismatches=[];cache={}
 def append_rows(role,rows):
  if not isinstance(rows,list) or not rows:
   mismatches.append({'origin':role,'reason':'MISSING_IDENTITY_COLLECTION'});return
  for row in rows:
   if not isinstance(row,dict) or not isinstance(row.get('path'),str):
    mismatches.append({'origin':role,'reason':'MALFORMED_IDENTITY_RECORD'});continue
   records.append((role,row))
 def append_hashes(role,rows):
  if not isinstance(rows,dict) or not rows:
   mismatches.append({'origin':role,'reason':'MISSING_IDENTITY_COLLECTION'});return
  append_rows(role,[{'path':name,'sha256':digest} for name,digest in rows.items()])
 append_rows('A.source_identity',a.get('source_identity'))
 append_rows('A.dependency_identity',a.get('dependency_identity'))
 files=b.get('files')
 append_rows('B.files',list(files.values()) if isinstance(files,dict) else None)
 append_hashes('B.configuration_and_executed_source_sha256',b.get('configuration_and_executed_source_sha256'))
 append_hashes('D.input_hashes_before',d.get('input_hashes_before'))
 append_hashes('independent.input_hashes',i.get('input_hashes'))
 def observe(name):
  if name in cache:return cache[name]
  path=Path(name);row={'resolved_path':None,'is_symlink':None,'sha256':None,'bytes':None}
  try:
   row.update(resolved_path=str(path.resolve()),is_symlink=path.is_symlink())
   if path.is_symlink():row['link_target']=os.readlink(path)
   if not path.exists():row['status']='BROKEN_SYMLINK' if path.is_symlink() else 'MISSING_FILE'
   elif not path.is_file():row['status']='NOT_REGULAR_FILE'
   else:
    before=path.stat();digest=hashlib.sha256()
    with path.open('rb') as stream:
     for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    after=path.stat();row.update(status='FILE',sha256=digest.hexdigest(),bytes=after.st_size)
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):row['status']='FILE_CHANGED_DURING_READ'
  except (OSError,RuntimeError) as error:row.update(status='READ_ERROR',error_type=type(error).__name__)
  cache[name]=row;return row
 for origin,expected in records:
  name=expected['path'];actual=observe(name);reasons=[]
  if expected.get('status')=='BROKEN_SYMLINK':
   if actual['status']!='BROKEN_SYMLINK':reasons.append('EXPECTED_BROKEN_SYMLINK_CHANGED')
   if expected.get('link_target')!=actual.get('link_target'):reasons.append('SYMLINK_TARGET_CHANGED')
   if expected.get('sha256') is not None or expected.get('bytes') is not None:reasons.append('BROKEN_SYMLINK_RECEIPT_HAS_PAYLOAD')
  else:
   digest=expected.get('sha256')
   if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):reasons.append('MISSING_OR_INVALID_EXPECTED_SHA256')
   if actual['status']!='FILE':reasons.append(actual['status'])
   elif actual['sha256']!=digest:reasons.append('RAW_SHA256_MISMATCH')
   if expected.get('bytes') is not None and expected['bytes']!=actual['bytes']:reasons.append('BYTE_COUNT_MISMATCH')
  if expected.get('resolved_path') is not None and expected['resolved_path']!=actual['resolved_path']:reasons.append('RESOLVED_PATH_CHANGED')
  if reasons:mismatches.append({'origin':origin,'path':name,'reasons':reasons,'expected':{key:expected[key] for key in ('status','sha256','bytes','resolved_path','link_target') if key in expected},'actual':actual})
 return {'status':'BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT' if mismatches else 'PASS_CURRENT_RAW_SOURCE_IDENTITIES',
         'checked_records':len(records),'unique_paths_checked':len(cache),'mismatch_count':len(mismatches),'mismatches':mismatches,
         'comparison':'EXACT_RAW_SHA256_NO_NORMALIZATION','inputs_modified':False}

def validate_profiles(a,b,d,i):
 roles=[(a,'HISTORICAL_SOURCE_AUDIT'),(b,'HISTORICAL_SOURCE_AUDIT'),(d,'ACTUAL_EXISTING_DATA_READBACK'),(i,'ACTUAL_EXISTING_DATA_READBACK')]
 for obj,role in roles:demand(obj.get('evidence_class')==role,'EVIDENCE_ROLE_CLASS')
 profiles=[(a,('new_ME_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events')),(b,('new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events')),(d,('new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events')),(i,('new_ME_calls','new_integrals','new_events'))]
 for obj,keys in profiles:
  for key in keys:demand(type(obj.get(key)) is int and obj[key]==0,'MISSING_OR_NONZERO_PRODUCTION_COUNTER:'+key)
 demand(a.get('physical_pilot_executed') is False and b.get('physical_pilot_executed') is False,'PILOT_EXECUTED_OR_MISSING')
 demand(type(a.get('new_MG5_parser_calls')) is int and a['new_MG5_parser_calls']==0 and b.get('generator_parser_executed') is False,'PARSER_NOT_AUTHORIZED')
 demand(d.get('status')=='VALIDATED_WITH_LIMITS' and d.get('persisted_events_joined')==6000 and d.get('HF_original_events_analysed')==3000 and type(d.get('new_ROOT_loops')) is int and d['new_ROOT_loops']==0,'EXISTING_DATA_SCOPE')
 demand(i.get('status')=='PASS_INDEPENDENT_RATIONAL_BITSET_EXISTING_DATA' and i.get('source_events')==3000 and i.get('covariance_pairs_checked')==3825 and i.get('Phase10_stage_counts_rates_variances_match') is True,'INDEPENDENT_COVARIANCE_FAILED')
 return True

def run(repo,model,family,detector,independent,output):
 a,b,d,i=map(load,(model,family,detector,independent));cfg=repo/'analysis/phase11/config'
 validate_profiles(a,b,d,i)
 demand(a.get('evidence_class')=='HISTORICAL_SOURCE_AUDIT' and b.get('evidence_class')=='HISTORICAL_SOURCE_AUDIT' and d.get('evidence_class')=='ACTUAL_EXISTING_DATA_READBACK' and i.get('evidence_class')=='ACTUAL_EXISTING_DATA_READBACK','EVIDENCE_ROLE_CLASS')
 ca,cb,ir,c=[load(cfg/name) for name in ('candidate_a.json','candidate_b.json','photon_ir.json','bounded_pilot_contract.json')]
 demand(a['candidate']==ca and a['source_hashes_unchanged'] is True,'MODEL_CONFIG_OR_SOURCE_BINDING')
 demand(b['candidate_b']==cb and b['photon_ir']==ir,'FAMILY_IR_CONFIG_BINDING')
 demand(a['status']=='BLOCKED_PHASE11_PDF_OR_ALPHA_S' and b['status']=='PASS_STATIC_SOURCE_REVIEW_WITH_BLOCKERS','UNEXPECTED_SOURCE_STATUS')
 demand(a['compatible_installed_4f_pdf'] is None,'UNREVIEWED_PDF_PROMOTION')
 demand(a['new_MG5_parser_calls']==0 and b['generator_parser_executed'] is False,'PARSER_NOT_AUTHORIZED')
 for obj in (a,b,d,i):
  for key,value in obj.items():
   if key.lower() in ('new_me_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events','new_events'):
    demand(type(value) is int and value==0,'NONZERO_PRODUCTION_IN_EVIDENCE:'+key)
 demand(d['persisted_events_joined']==6000 and d['HF_original_events_analysed']==3000 and d['new_ROOT_loops']==0,'EXISTING_DATA_SCOPE')
 demand(d['input_hashes_before']==d['input_hashes_after'],'EXISTING_DATA_CHANGED')
 demand(i['status']=='PASS_INDEPENDENT_RATIONAL_BITSET_EXISTING_DATA' and i['source_events']==3000 and i['covariance_pairs_checked']==3825 and i['Phase10_stage_counts_rates_variances_match'] is True,'INDEPENDENT_COVARIANCE_FAILED')
 demand(str(detector) in i['input_hashes'],'INDEPENDENT_DETECTOR_SUMMARY_IDENTITY_MISSING')
 shared=set(d['input_hashes_before'])&set(i['input_hashes']);demand(len(shared)>=2 and all(d['input_hashes_before'][key]==i['input_hashes'][key] for key in shared),'INDEPENDENT_SHARED_INPUT_BINDING')
 source_integrity=current_source_integrity(a,b,d,i)
 validate_contract(c)
 cards=sorted((cfg/'cards').glob('*.inactive.txt'))+[cfg/'inactive_detector_diff.txt']
 for p in cards:validate_inactive_card(p.read_text())
 parser=load(cfg/'parser_process_review_request.json');demand(parser['execution_authorized'] is False and parser['dispatcher'] is None and parser['approved_limits'] is None,'PARSER_REQUEST_NOT_INACTIVE')
 selected=select_component(c['source_requirements']);demand(selected==c['selected_component'],'SELECTION_BINDING')
 kernel={}
 for name in ('/proc/self/cgroup','/sys/fs/cgroup/cgroup.controllers','/sys/fs/cgroup/memory.max'):
  p=Path(name)
  if p.is_file():kernel[name]={'text':p.read_text().strip(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 result={'schema_version':1,'status':'BLOCKED_PHASE11_NO_VALIDATED_COMPONENT','evidence_class':'HISTORICAL_SOURCE_AUDIT','selected_pilot_component':selected,'source_integrity':source_integrity,'source_integrity_status':source_integrity['status'],'source_supported':['effective model restrictions and flavours','coupling order and generic interface semantics','exact LO isolation field interactions','detector isolation mutation/collection sequence'],'exact_process_validation':'PARSER_NOT_VALIDATED','physical_pilot_status':'PHYSICAL_PILOT_NOT_EXECUTED','matching_status':'MATCHING_NOT_VALIDATED','source_requirements':c['source_requirements'],'evidence':{k:binding(p) for k,p in [('model_pdf',model),('family_IR',family),('existing_HF',detector),('independent_covariance',independent)]},'inactive_cards':[binding(p) for p in cards],'contract':binding(cfg/'bounded_pilot_contract.json'),'current_kernel_resource_observations':kernel,'resource_interpretation':'Kernel controller presence is not delegated per-job enforcement. Existing P8 monitor bounds process-group CPU/wall/disk but native ME/trial/cycle counters and hard job RAM containment remain unreviewed. All illustrative pilot caps unapproved.','physical_pilot_executed':False,'physical_approval':'NOT_AUTHORIZED','external_human_review_approval':False,'new_ROOT_loops':0,'parser_process_generation_executed':False,'figure_publication_authorized':False,**PHYSICAL_GATES,**{key:0 for key in COUNTERS}}
 with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument('--model-audit',type=Path,required=True);p.add_argument('--family-audit',type=Path,required=True);p.add_argument('--detector-summary',type=Path,required=True);p.add_argument('--independent-covariance',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.repo,a.model_audit,a.family_audit,a.detector_summary,a.independent_covariance,a.output);print(json.dumps({'status':r['status'],'selected':r['selected_pilot_component'],'pilot_executed':False}))
if __name__=='__main__':main()
