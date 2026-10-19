"""Evidence-bound partial-recovery policy. No parser/production dispatcher exists."""
import hashlib,math
from pathlib import Path
COUNTERS=('NEW_ME_CALLS','NEW_INTEGRALS','NEW_HARD_EVENTS','NEW_PYTHIA_EVENTS','NEW_DELPHES_EVENTS')
PHYSICS={'PHYSICAL_TOTAL_BACKGROUND':'BLOCKED','PHYSICAL_SIGNIFICANCE':'NOT_EVALUATED','PHYSICAL_CLs':'NOT_EVALUATED','PHOTON_FAKE_RATE':'UNKNOWN','HEAVY_FLAVOUR_GENERATOR_EXCLUSIVITY':'UNVERIFIED','MATCHED_SIGNAL_NORMALIZATION':'BLOCKED_PHASE7I'}
def require(ok,reason):
 if not ok:raise ValueError(reason)
def raw_identity(path):
 path=Path(path);require(path.is_file(),'MISSING_ACTUAL_INPUT');before=path.stat();h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 after=path.stat();require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'INPUT_CHANGED_DURING_READ');return {'bytes':after.st_size,'sha256':h.hexdigest()}
def validate_contract(c):
 require(c['selected_pilot_component']=='NONE_READY' and c['new_baseline_approved'] is False,'SILENT_BASELINE_OR_COMPONENT_APPROVAL')
 require(c['old_phase11_raw_gate']=='BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT' and c['runtime_historical_writer']=='UNKNOWN','HISTORICAL_REBASELINE_OR_WRITER_CLAIM')
 require(c['MG5_PARSER_EXECUTED'] is False and c['MATCHING_VALIDATED'] is False and c['physical_authorization'] is False and c['dispatcher'] is None and c['approval_override_flag'] is None,'PRODUCTION_OR_PARSER_NOT_AUTHORIZED')
 for key in COUNTERS:require(type(c.get(key)) is int and c[key]==0,'NONZERO_OR_MISSING_PRODUCTION_COUNTER:'+key)
 for key,value in PHYSICS.items():require(c[key]==value,'FALSE_PHYSICAL_PROMOTION:'+key)
 require(c['PDF_member']==0 and type(c['PDF_member']) is int and c['PDF_LHAPDF_ID']==263400 and c['PDF_native_alpha_type']=='ipol','PDF_IDENTITY')
 require(c['PDF_ME_alpha_binding']=='UNVERIFIED' and c['reference_diagnostic_not_official_accuracy_bound'] is True,'FALSE_ALPHA_BINDING_OR_ACCURACY')
 require(set(c['unresolved_settings'])=={'runtime_baseline_approval','PDF_MG5_backend_binding','ME_ISR_FSR_alpha_threshold_conventions','photon_IR','generation_cuts','central_scale','shower_settings','matching','weights','approved_future_resources'},'MISSING_REQUIRED_UNRESOLVED_SETTING')
 require(c['PDF_declared_alpha_reference']['scale_GeV']==4.1799998 and c['PDF_declared_alpha_reference']['value']==0.2544023564420006 and c['PDF_declared_alpha_reference']['scale_source_key']=='MZ' and c['PDF_declared_alpha_reference']['value_source_key']=='AlphaS_MZ','WRONG_ALPHA_REFERENCE_INFERENCE')
 require(c['reference_field_vs_native_strict_diagnostic_pass'] is False and type(c['native_reference_relative_difference']) is float and math.isfinite(c['native_reference_relative_difference']) and math.isclose(c['native_reference_relative_difference'],2.626248635282933e-6,rel_tol=1e-12),'MEASURED_REFERENCE_DIAGNOSTIC_CHANGED')
 for key,row in c['unresolved_settings'].items():require(row.get('value') is None and row.get('status')=='BLOCKED' and bool(row.get('evidence_required')),'UNKNOWN_AS_ZERO_OR_DEFAULT:'+key)
 return True
def validate_runtime(snapshots,proposal,current):
 require(snapshots['evidence_class']=='ACTUAL_RAW_RUNTIME_OBSERVATION','RUNTIME_EVIDENCE_CLASS')
 for key in ('new_ME_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events'):require(type(snapshots.get(key)) is int and snapshots[key]==0,'RUNTIME_AGGREGATE_PRODUCTION_COUNTER')
 rows=snapshots['snapshots'];require(all(x.get('evidence_class')=='ACTUAL_RAW_RUNTIME_OBSERVATION' for x in rows),'RUNTIME_ROW_EVIDENCE_CLASS')
 for x in rows:
  for key in ('new_ME_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events'):require(type(x.get(key)) is int and x[key]==0,'RUNTIME_PRODUCTION_COUNTER')
 require(len(rows)==3 and len({x['pid'] for x in rows})==3 and all(type(x['pid']) is int and x['pid']>0 for x in rows),'THREE_DISTINCT_PROCESS_IDS_REQUIRED')
 require(snapshots['raw_bytes_stable'] is True and snapshots['file_identity_stable'] is True,'RUNTIME_CHANGED_DURING_SNAPSHOTS')
 require(all(x['raw_identity']==current and x['cold_cache_independence_claimed'] is False and x['installed_file_write_performed'] is False for x in rows),'STALE_RAW_HASH_OR_FALSE_INDEPENDENCE')
 require(proposal['new_observed_raw_identity']==current and proposal['new_baseline_approved'] is False and proposal['physical_execution_authorized'] is False,'NEW_BASELINE_NOT_APPROVED')
 require(proposal['old_phase11_raw_gate']=='BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT','OLD_PHASE11_GATE_MUST_STAY_BLOCKED');return True
def validate_pdf(n,a):
 require(n['evidence_class']=='ACTUAL_ISOLATED_PDF_READBACK' and n['status']=='PASS_ISOLATED_NATIVE_PDF_INTERFACE_WITH_LIMITS','ACTUAL_NATIVE_READBACK_REQUIRED')
 require(a['status']=='PASS_COMPLETE_SELECTED_MEMBER_ACQUISITION' and a['candidate']=='NNPDF30_lo_as_0130_nf_4' and type(a['member']) is int and a['member']==0 and a['maximum_selected_distributions']==1,'MISSING_COMPLETE_ACTUAL_MEMBER')
 require(a['aggregate_body_bytes']==sum(x['received_bytes'] for x in a['files'])<=134217728 and all(0<x['received_bytes']==x['bytes']==x['advertised_bytes']<=83886080 for x in a['files']),'BROKEN_OR_OVERSIZE_DOWNLOAD')
 require({x['role'] for x in a['files']}=={'member','info'} and len(a['files'])==2,'EXACT_TWO_PAYLOADS_REQUIRED')
 for row in a['files']:require(row['sha256']==n['metadata'][row['role']+'_identity']['sha256'],'PAYLOAD_SHA_BINDING')
 require(set(n['native_flavours'])=={-4,-3,-2,-1,1,2,3,4,21} and n['bottom_active'] is False and n['native_LHAPDF_ID']==263400,'WRONG_FOUR_FLAVOUR_SCOPE')
 require(n['finite_xfx_values']==36 and len(n['alpha_values'])==5 and n['nonfinite_errors']==0 and n['interpolation_errors']==0,'PARTIAL_OR_INVALID_NATIVE_READBACK')
 metadata=n['metadata'];require(metadata['PDF_maximum_flavours']==4 and metadata['alpha_maximum_flavours']==4 and metadata['PDF_order_QCD']==0 and metadata['alpha_order_QCD']==0 and metadata['alpha_type']=='ipol' and set(metadata['flavours'])==set(n['native_flavours']),'WRONG_NATIVE_METADATA_SCOPE')
 require(metadata['alpha_reference']['scale_GeV']==4.1799998 and metadata['alpha_reference']['value']==0.2544023564420006,'WRONG_NATIVE_ALPHA_REFERENCE')
 require([row['Q_GeV'] for row in n['alpha_values']]==[4.1799998,10.,91.1876,100.,1000.] and all(type(row['alpha_s']) is float and math.isfinite(row['alpha_s']) and row['alpha_s']>0 for row in n['alpha_values']),'NONFINITE_OR_UNREVIEWED_ALPHA_POINTS')
 require([[row['x'],row['Q_GeV']] for row in n['finite_pdf_points']]==[[.0001,10.],[.01,91.1876],[.1,1000.],[.5,100.]],'UNREVIEWED_PDF_POINTS')
 require(all(set(row['xfxQ'])=={str(v) for v in n['native_flavours']} and all(type(v) is float and math.isfinite(v) for v in row['xfxQ'].values()) for row in n['finite_pdf_points']),'NONFINITE_OR_MISSING_NATIVE_FLAVOUR_VALUES')
 diag=n['alpha_reference_diagnostic'];require(diag['declared_reference']==metadata['alpha_reference'] and diag['within_strict_diagnostic_tolerance'] is False and diag['strict_diagnostic_relative_tolerance']==1e-6 and diag['publisher_interpolation_accuracy_bound'] is None,'REFERENCE_DIAGNOSTIC_RECLASSIFIED')
 require(diag['native_alpha_at_declared_Q']==n['alpha_values'][0]['alpha_s'] and math.isclose(diag['relative_difference'],(diag['native_alpha_at_declared_Q']-metadata['alpha_reference']['value'])/metadata['alpha_reference']['value'],rel_tol=1e-12),'REFERENCE_NUMERIC_BINDING')
 require(len(n['out_of_domain_guard_rejections'])==5 and all(x['native_xfxQ_called'] is False for x in n['out_of_domain_guard_rejections']),'OUTSIDE_DOMAIN_NOT_GUARDED')
 require(n['raw_inputs_and_dependencies_before']==n['raw_inputs_and_dependencies_after'] and len(n['raw_inputs_and_dependencies_before'])==10,'RAW_NATIVE_DEPENDENCY_DRIFT')
 require(n['MG5_parser_executed'] is False and n['matching_validated'] is False and n['physical_component_validated'] is False and n['installed_directory_writes'] is False,'FALSE_PHYSICAL_PROMOTION')
 for key in ('new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events'):require(type(n.get(key)) is int and n[key]==0,'NATIVE_GENERATION_FORBIDDEN')
 require(n['alpha_reference_diagnostic']['comparison_role']=='DIAGNOSTIC_NOT_OFFICIAL_ACCURACY_TEST' and n['alpha_reference_diagnostic']['physical_ME_or_shower_alpha_binding']=='UNVERIFIED_NOT_EXECUTED','REFERENCE_DIAGNOSTIC_PROMOTION')
 return True
def recheck_native_inputs(n):
 for name,row in n['raw_inputs_and_dependencies_after'].items():require(raw_identity(name)=={k:row[k] for k in ('bytes','sha256')},'STALE_NATIVE_INPUT:'+name)
 for name,digest in n['source_sha256'].items():require(raw_identity(name)['sha256']==digest,'EXECUTED_READER_SOURCE_CHANGED:'+name)
 return True
def validate_inactive(text):require(text.strip() and all(line.lstrip().startswith('#') for line in text.splitlines() if line.strip()),'ACTIVE_PARSER_CARD');return True
