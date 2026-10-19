"""Source-only pilot decision and non-executable contracts; no dispatch API."""
import math
COMPONENTS=('MASSIVE_4F_BB_COMPONENT','COMMON_5F_AA_JETS_COMPONENT')
REQUIREMENT_KEYS={'model_masses_flavours','installed_PDF_member','alpha_s_threshold_binding','photon_IR_target','generation_cut_definition','hard_scale_definition','ME_PS_interface','shower_and_weight_identity'}
PAYLOAD_KEYS={'aggregate_future_CPU_seconds','exact_future_execution_source_revision','MG5_version','model_review_proposal','Pythia_version','process_review_proposal','PDF_member_flavour_scheme','alpha_s_and_thresholds','photon_IR_definition','generation_cuts','shower_settings','scale_definition','source_requirements','weight_contract','integration_reporting','independent_validation_protocol','stop_conditions'}
PHYSICAL_GATES={'HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY':'UNVERIFIED','PHOTON_FAKE_RATE':'UNKNOWN','MATCHED_SIGNAL_NORMALIZATION':'BLOCKED_PHASE7I','PHYSICAL_TOTAL_BACKGROUND':'BLOCKED','PHYSICAL_SIGNIFICANCE':'NOT_EVALUATED','PHYSICAL_CLs':'NOT_EVALUATED','PHYSICAL_KAPPA_INTERVAL':'NOT_EVALUATED'}
COUNTERS=('NEW_ME_CALLS','NEW_INTEGRALS','NEW_HARD_EVENTS','NEW_PYTHIA_EVENTS','NEW_DELPHES_EVENTS')

def demand(ok,reason):
 if not ok:raise ValueError(reason)

def select_component(requirements):
 demand(set(requirements)==set(COMPONENTS),'MISSING_CANDIDATE')
 eligible=[]
 for name,rows in requirements.items():
  demand(isinstance(rows,dict) and set(rows)==REQUIREMENT_KEYS,'MISSING_MANDATORY_REQUIREMENTS')
  for key,row in rows.items():
   demand(row.get('status') in ('SOURCE_SUPPORTED','BLOCKED','UNVERIFIED','PROPOSED_NOT_PHYSICALLY_VALIDATED'),'INVALID_REQUIREMENT_STATUS:'+key)
   demand(bool(row.get('evidence')) and bool(row.get('reason')),'UNEXPLAINED_FIELD:'+key)
  if all(row['status']=='SOURCE_SUPPORTED' for row in rows.values()):eligible.append(name)
 # A is the smaller isolated component; never claim inclusive coverage from this preference.
 return eligible[0] if eligible else 'NONE_READY'

def validate_contract(c):
 demand(c.get('schema_version')==1,'CONTRACT_SCHEMA')
 demand(PAYLOAD_KEYS<=set(c),'MISSING_SCIENTIFIC_CONTRACT_FIELDS')
 demand(c['selected_component']==select_component(c['source_requirements']),'FABRICATED_COMPONENT_SELECTION')
 demand(c['exact_future_execution_source_revision'] is None,'UNREVIEWED_FUTURE_EXECUTABLE_REVISION')
 demand(c['aggregate_future_CPU_seconds'] is None,'UNREVIEWED_FUTURE_CPU_CEILING')
 demand(c['MG5_version']=='3.5.16' and c['Pythia_version']=='8.317','VERSION_BINDING')
 demand(bool(c['independent_validation_protocol']) and bool(c['stop_conditions']),'MISSING_VALIDATION_OR_STOP_PROTOCOL')
 demand(c['weight_contract'].get('physical_signed_interface_validated') is False,'SIGNED_INTERFACE_NOT_VALIDATED')
 demand(c['integration_reporting'].get('new_integral_executed') is False,'INTEGRAL_NOT_AUTHORIZED')
 demand(c.get('status')=='INACTIVE_REVIEW_ONLY','NOT_INACTIVE')
 demand(c.get('selected_component')=='NONE_READY','NO_VALIDATED_COMPONENT_THIS_REVIEW')
 for key in ('PDF_member_flavour_scheme','alpha_s_and_thresholds','photon_IR_definition','generation_cuts','shower_settings','scale_definition'):
  demand(c[key] is None,'UNVALIDATED_SCIENTIFIC_PAYLOAD:'+key)
 demand(c.get('execution_authorized') is False and c.get('instantiable') is False and c.get('physical_pilot_executed') is False,'UNAUTHORIZED_PILOT')
 demand(c.get('dispatcher') is None and c.get('approval_override_flag') is None,'UNREVIEWED_DISPATCHER_OR_FLAG')
 demand(c.get('physical_approval',{}).get('status')=='NOT_AUTHORIZED','APPROVAL_MISSING')
 demand(c['physical_approval'].get('receipt') is None,'UNREVIEWED_APPROVAL_RECEIPT')
 for key in COUNTERS:demand(type(c.get(key)) is int and c[key]==0,'PRODUCTION_FORBIDDEN:'+key)
 for key,value in PHYSICAL_GATES.items():demand(c.get(key)==value,'PHYSICAL_GATE_PROMOTED:'+key)
 demand(c.get('inclusive_background_total') is False,'MIXED_COMPONENT_TOTAL_FORBIDDEN')
 demand(c.get('calibrated_fake_probability') is None,'UNVALIDATED_FAKE_RATE')
 demand(c.get('unknown_nuisances',{}).get('values') is None and c['unknown_nuisances'].get('covariance') is None and c['unknown_nuisances'].get('status')=='UNKNOWN_NOT_ZERO','UNKNOWN_AS_ZERO')
 demand(c.get('external_human_review_approval') is False,'NO_HUMAN_SIGNOFF')
 demand(c.get('fresh_output_required') is True and c.get('existing_output_reuse_allowed') is False,'HISTORICAL_OVERWRITE_RISK')
 demand(type(c.get('retained_new_physical_events')) is int and c['retained_new_physical_events']==0,'CURRENT_RETAINED_EVENTS_FORBIDDEN')
 limits=c.get('resource_review',{})
 for key in ('threads','wall_seconds','RAM_bytes','disk_bytes','new_hard_events','scan_points','ME_evaluations','integration_cycles','event_trials'):
  row=limits.get(key,{})
  demand(type(row.get('illustrative_unapproved_limit')) is int and row['illustrative_unapproved_limit']>0,'FINITE_PROPOSAL_REQUIRED:'+key)
  demand(row.get('approved_limit') is None and row.get('enforcement_status') in ('UNVERIFIED','UNIMPLEMENTED'),'RESOURCE_APPROVAL_OR_ENFORCEMENT_FABRICATED:'+key)
 demand(c.get('unresolved_fields'),'MISSING_EXPLICIT_BLOCKERS')
 for key,row in c['unresolved_fields'].items():
  demand(row.get('value') is None and row.get('status')=='BLOCKED' and bool(row.get('evidence_required')) and bool(row.get('reason')),'NULL_BLOCKER_POLICY:'+key)
 return True

def validate_inactive_card(text):
 lines=[x.strip() for x in text.splitlines() if x.strip()]
 demand(lines and all(x.startswith('#') for x in lines),'ACTIVE_CARD_TEXT_FORBIDDEN')
 demand('INACTIVE' in text.upper(),'INACTIVE_MARKER_REQUIRED')
 return True

def signed_source_statistics(weights,mask):
 demand(len(weights)==len(mask) and len(weights)>1,'ORIGINAL_SOURCE_COHORT_REQUIRED')
 demand(all(isinstance(w,(float,int)) and not isinstance(w,bool) and math.isfinite(w) for w in weights),'NONFINITE_OR_INVALID_WEIGHT')
 demand(all(type(v) is bool for v in mask),'INVALID_EVENT_MASK')
 n=len(weights);x=[float(w) if selected else 0. for w,selected in zip(weights,mask)];s=math.fsum(x);q=math.fsum(v*v for v in x);variance=n/(n-1)*(q-s*s/n)
 demand(variance>=-1e-12*max(q,1),'NEGATIVE_SOURCE_VARIANCE')
 return {'original_N':n,'sumw':s,'sumw2':q,'fixed_N_variance':max(variance,0.),'relative_SE':math.sqrt(max(variance,0.))/abs(s) if s else None,'ESS':s*s/q if q else None,'new_independent_events':0,'scope':'SIGNED_ALGEBRA_METHOD_ONLY_NOT_GENERATOR_WEIGHT_INTERFACE_VALIDATION'}
