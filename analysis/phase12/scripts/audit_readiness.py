#!/usr/bin/env python3
"""Compose measured Phase12 partial recovery; never dispatches MG5 or production."""
import argparse,hashlib,json,sys,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from readiness_policy import validate_contract,validate_runtime,validate_pdf,recheck_native_inputs,validate_inactive,raw_identity,require,PHYSICS,COUNTERS

def load(p):return json.loads(Path(p).read_text())
def run(repo,root,output,matrix_output):
 cfg=repo/'analysis/phase12/config';c=load(cfg/'scientific_contract.json');validate_contract(c);validate_inactive((cfg/'parser_only.inactive.txt').read_text());request=load(cfg/'parser_only_review_request.json');require(request['execution_authorized'] is False and request['physical_execution_authorized'] is False and request['runtime_baseline_approved'] is False and request['dispatcher'] is None and request['approved_limits'] is None,'FUTURE_REQUEST_NOT_INACTIVE')
 snapshots=load(root/'runtime_01/runtime_raw_snapshots.json');proposal=load(root/'runtime_01/runtime_baseline_proposal.json');writer=load(root/'runtime_01/runtime_writer_attribution.json');native=load(root/'pdf_readback_04/pdf_member_readback.json');acquisition=load(root/'public_pdf_01/acquisition_receipt.json');dependency=load(root/'phase7i_dependency_impact.json')
 validate_pdf(native,acquisition);recheck_native_inputs(native);require(writer['actual_writer']=='UNKNOWN' and writer['actual_writer_identified'] is False and writer['serializer_behavior']=='SERIALIZER_BEHAVIOR_REPRODUCED','WRITER_ATTRIBUTION_PROMOTION');require(dependency['status']=='NOT_BOUND_BY_REVIEWED_CONTRACT','UNEXPECTED_PHASE7I_IMPACT_STATUS')
 current=raw_identity('/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt');runtime_error=None
 try:validate_runtime(snapshots,proposal,current)
 except ValueError as error:runtime_error=str(error)
 require(raw_identity(proposal['versioned_private_byte_copy'])==proposal['new_observed_raw_identity'],'PRIVATE_PROPOSED_COPY_RAW_MISMATCH')
 inherited_model_audit=load(repo/'analysis/phase11/evidence/phase11_model_pdf_audit_02.json');inherited_models={row['path']:row for row in inherited_model_audit['source_identity']}
 witnesses=[]
 for name in ('restrict_default.dat','restrict_no_b_mass.dat','parameters.py','particles.py'):
  p=Path('/home/btu/opt/mg5amcnlo/models/sm')/name;current_model=raw_identity(p);require(str(p) in inherited_models and current_model=={key:inherited_models[str(p)][key] for key in ('bytes','sha256')},'MODEL_WITNESS_CHANGED_SINCE_PHASE11');witnesses.append({'path':str(p),'resolved_path':str(p.resolve()),**current_model,'exact_Phase11_source_identity_match':True})
 fields=['Model','Restriction','PDF_member','AlphaS','Threshold','Photon_IR','Cuts','Scale','Shower','Matching','Weights','Runtime_identity','Exact_process_parser'];rows=[]
 for candidate in ('MASSIVE_4F_BB_COMPONENT','COMMON_5F_AA_JETS_COMPONENT'):
  A=candidate.startswith('MASSIVE')
  for field in fields:
   status='BLOCKED';detail='No numerical setting or physical execution approved.'
   if field in ('Model','Restriction'):status='VALIDATED_EXACT_SOURCE';detail='P11 static source semantics retained; current raw model witnesses bound. '+('sm/default MB4.7 MC0; incoming p4 excludes b and includes c.' if A else 'sm-no_b_mass MB=MC=0; proposed p5/j5 includes b/c.')
   elif field=='PDF_member':status='PROPOSED_WITH_EVIDENCE' if A else 'BLOCKED';detail='Actual external member0/263400 DataVersion2, nine native flavours/max4/no bottom, standalone LHAPDF6.5.6 validated; NOT MG5 binding.' if A else 'New nf4 evidence does not select a compatible common5F PDF member.'
   elif field=='AlphaS':status='PROPOSED_WITH_EVIDENCE' if A else 'UNVERIFIED';detail='ipol; declared referenceQ4.1799998/value.2544023564420006; native .254403024565842, strict1e-6 diagnosticfalse; nativeat91.1876=.12470053368074485. ME/shower binding UNVERIFIED.' if A else 'No new 5F ME/PDF/ISR/FSR alpha binding.'
   elif field=='Threshold':status='PROPOSED_WITH_EVIDENCE' if A else 'UNVERIFIED';detail='PDFmax4 variable; charm1.275/bottom4.1799998 evolution metadata, bottomnotactivated. Metadata thresholds are not ME pole masses or proof of ipol breakpoint behavior.' if A else '5F thresholds and matching flavour boundary remain unreviewed.'
   elif field=='Photon_IR':detail='P11 LO smoothcone is_a_j bottomcoverage/physicaltarget closure remains blocked; no new threshold.'
   elif field=='Cuts':detail='Null generation cuts; no sensitivity measurements authorized.'
   elif field=='Scale':detail='Null central scale; no historical default substituted.'
   elif field=='Shower':status='UNVERIFIED';detail='No Pythia execution; QCD/QED/g->bb/cc effective settings unbound.'
   elif field=='Matching':status='NOT_APPLICABLE' if A else 'BLOCKED';detail='No merged multiplicity is introduced for isolated LO review target; generator exclusivity and shower overlap remain UNVERIFIED.' if A else 'Generic MLM/CKKW-L source is not exact 0/1/2 family validation; merging scale null.'
   elif field=='Weights':status='UNVERIFIED';detail='No hard events; generator/merging signed weight and acceptance normalization unvalidated.'
   elif field=='Runtime_identity':detail='Three sequential current raw observations and proposed copy only; baseline NOT_APPROVED, writer UNKNOWN, old P11 raw gate BLOCKED.'
   elif field=='Exact_process_parser':detail='NOT_VALIDATED; future request is comment-only and NOT_AUTHORIZED.'
   rows.append({'candidate':candidate,'field':field,'status':status,'detail':detail})
 matrix={'schema_version':1,'evidence_class':'HISTORICAL_SOURCE_AUDIT','selected_pilot_component':'NONE_READY','rows':rows,'model_current_raw_witnesses':witnesses,'new_evidence_scope':'Only exact runtime/PDF dependencies changed; no full event analysis repeated.','physical_authorization':False}
 result={'schema_version':1,'evidence_class':'HISTORICAL_SOURCE_AUDIT','status':'BLOCKED_PHASE12_RUNTIME_DRIFT' if runtime_error else 'PASS_PHASE12_PARTIAL_RECOVERY','observed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime_current_identity':current,'runtime_recheck_error':runtime_error,'runtime_snapshot_status':snapshots['status'],'new_baseline_approved':False,'old_phase11_gate':'BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT','actual_writer_identified':False,'phase7i_dependency_impact':dependency['status'],'PDF_interface_status':native['status'],'PDF_MG5_alpha_binding':'UNVERIFIED','reference_diagnostic':native['alpha_reference_diagnostic'],'selected_pilot_component':'NONE_READY','MG5_PARSER_EXECUTED':False,'MATCHING_VALIDATED':False,'physical_execution_authorized':False,'dispatcher':None,'independent_human_review':False,**PHYSICS,**{k:0 for k in COUNTERS},'receipt_identities':{str(p):raw_identity(p) for p in [root/'runtime_01/runtime_raw_snapshots.json',root/'runtime_01/runtime_baseline_proposal.json',root/'runtime_01/runtime_writer_attribution.json',root/'pdf_readback_04/pdf_member_readback.json',root/'pdf_readback_04/pdf_alpha_reference_checks.json',root/'public_pdf_01/acquisition_receipt.json',root/'phase7i_dependency_impact.json']},'contract_identity':raw_identity(cfg/'scientific_contract.json')}
 for path,obj in ((output,result),(matrix_output,matrix)):
  with path.open('x') as stream:json.dump(obj,stream,indent=2);stream.write('\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument('--result-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--matrix-output',type=Path,required=True);a=p.parse_args();r=run(a.repo,a.result_root,a.output,a.matrix_output);print(json.dumps({'status':r['status'],'new_baseline_approved':False,'selected':r['selected_pilot_component']}))
