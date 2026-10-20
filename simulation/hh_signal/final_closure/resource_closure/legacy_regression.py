"""Portable exact81 safe legacy regression; no native or approval positives.

Only reviewed Git, fixed Python fixtures and exact /bin/sleep20 are permitted.
This runner never installs a resource filter or starts a systemd service.
"""
from __future__ import annotations
import argparse,ast,contextlib,hashlib,importlib,io,json,os,resource,shutil,sys,time,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[4]
BASE='simulation.hh_signal.final_closure.'
SELECTED_TESTS=('simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_assume_unchanged_cannot_hide_outside_change', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_batch_parser_rejects_missing_truncated_wrong_hash_and_extra_data', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_bounded_blob_batches_preserve_exact_full_preflight', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_changed_mode_when_git_tracks_modes', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_clean_original_and_new', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_cpu_budget', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_deleted_tracked_file', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_edit_between_status_and_hash', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_git_environment_override', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_git_subprocess_failure', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_gitlink_requires_separate_review', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_inaccessible_tracked_path', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_index_race', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_invalid_git_index', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_missing_required_tracked_path', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_modified_physics_contract', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_modified_reviewed_source', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_observed_diff_refresh_side_effect_in_fixture', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_outside_path_edit_after_status', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_overall_watchdog_covers_python_work', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_plumbing_is_not_accepted_as_status_equivalence', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_repository_identity', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_same_size_same_mtime_race', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_skip_worktree_cannot_hide_outside_change', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_staged_modification', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_staged_rename', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_staged_replacement', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_subprocess_timeout_kills_descendant_group', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_symlink_parent', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_timeout_preserves_bounded_diagnostic', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_unexpected_symlink', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_unreviewed_fsmonitor_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_unstaged_modification', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_untracked_is_same_scope_as_original', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_wrong_head', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.GitPrecheckTests.test_wrong_reviewed_physics_hash', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_changed_recovery_source_identity_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_clean_method_only_build', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_historical_public_native_build_binding', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_missing_immutable_source_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_modified_card_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_modified_executable_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_stopped_attempt_is_not_reused_or_overwritten', 'simulation.hh_signal.final_closure.integration_runtime.test_git_precheck.FrozenInputGuards.test_wrong_dynamic_library_hash_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_full_coherent_amplitude_and_fixed_endpoints', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_exact_revision_not_an_authorization_flag', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_unknown_stage_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_source_fixture_cannot_be_genuine_stage', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_four_replicas_do_not_automatically_pass_convergence', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_replica_replacement_or_duplicate_is_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_eight_RANMAR_stream_pairs_are_distinct', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_scalar_nan_rejected', 'simulation.hh_signal.final_closure.integration_runtime.test_runtime.RuntimeMethods.test_approval_token_not_a_CLI_option', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_build_source_uses_fresh_local_copies_and_zero_me_only', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_builder_cannot_create_or_compile_without_human_review', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_compile_and_link_plan_no_old_or_duplicate_guard', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_exact_proposal_and_reversal_with_bounded_activation_delta', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_fake_human_pipe_is_not_a_review', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_lossless_toolchain_inventory_fits_unchanged_git_cap', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_physical_default_denies_before_native_or_output', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.ActivationSourceTests.test_source_binding_has_canonical_posix_order', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.BuildProcessMethods.test_actual_nonphysical_child_measurements_and_failure_retention', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.BuildProcessMethods.test_aggregate_budget_terminates_child', 'simulation.hh_signal.final_closure.integration_runtime.test_route_a.BuildProcessMethods.test_live_descendant_cpu_uses_conservative_one_core_bound', 'simulation.hh_signal.final_closure.guard_correction.test_correction.ScientificSourceTests.test_exact_reversible_intentional_changes', 'simulation.hh_signal.final_closure.guard_correction.test_correction.ScientificSourceTests.test_frozen_loop_context_and_theory_scope_in_contract', 'simulation.hh_signal.final_closure.guard_correction.test_correction.ScientificSourceTests.test_no_rng_sampler_weight_grid_or_estimator_calls_in_guard', 'simulation.hh_signal.final_closure.guard_correction.test_correction.ScientificSourceTests.test_versioned_diagnostic_schema_and_no_vector_payload', 'simulation.hh_signal.final_closure.guard_correction.test_correction.ScientificSourceTests.test_weakened_or_unreviewed_changes_cannot_reverse', 'simulation.hh_signal.final_closure.guard_correction.test_correction.BuilderReviewTests.test_binary_identity_does_not_conflate_timestamps_with_full_receipt', 'simulation.hh_signal.final_closure.guard_correction.test_correction.BuilderReviewTests.test_builder_exact_diff_and_unchanged_active_builder', 'simulation.hh_signal.final_closure.guard_correction.test_correction.BuilderReviewTests.test_model_dependency_drift_rejected_with_no_compiler', 'simulation.hh_signal.final_closure.guard_correction.test_correction.BuilderReviewTests.test_only_two_declared_new_metadata_paths', 'simulation.hh_signal.final_closure.guard_correction.test_correction.BuilderReviewTests.test_stale_binary_receipt_and_consumed_authorization_cannot_migrate', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_additive_metadata_scope_is_exact', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_drift_and_weakened_predicates_rejected', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_exact_overlay_projection_and_frozen_files', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_failure_only_exact_statements_flush_and_scalar_schema', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_nonfinite_scalars_are_explicit_not_json_nan', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_parser_is_stateless_under_concurrent_receipt_readers', 'simulation.hh_signal.final_closure.stop92_diagnostic.test_diagnostic.OverlayTests.test_strict_parser_bounds_extra_fields_split_records')

def run(output):
 output=Path(output).absolute()
 if output.suffix!='.json' or not output.parent.is_dir() or '..' in output.parts:
  raise ValueError('EXPLICIT_EXISTING_PARENT_JSON_OUTPUT_REQUIRED')
 text_output=output.with_suffix('.txt')
 if any(p.exists() or p.is_symlink() for p in (output,text_output)):
  raise ValueError('EXISTING_REGRESSION_EVIDENCE_PRESERVED')
 sys.path.insert(0,str(REPO));os.chdir(REPO)
 selected=list(SELECTED_TESTS);source_rows=[]
 if len(selected)!=len(set(selected)) or len(selected)!=81:
  raise ValueError('EXACT81_SELECTION_REQUIRED')
 for name in selected:
  module,klass,method=name.rsplit('.',2)
  path=REPO/Path(*module.split('.')).with_suffix('.py')
  data=path.read_bytes();tree=ast.parse(data)
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==klass)
  node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
  text=ast.get_source_segment(data.decode(),node)
  if 'HumanReview(' in text or 'execute(' in text:
   raise ValueError('UNSAFE_METHOD_SELECTION:'+name)
  source_rows.append({'path':path.relative_to(REPO).as_posix(),
                      'sha256':hashlib.sha256(data).hexdigest()})
 from . import backend
 implementation_before=backend.source_snapshot()
 json_output=output
 template=json_output.parent/(output.stem+'_git_templates')
 template.mkdir(mode=0o700)
 os.environ.update(PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',
  GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_TEMPLATE_DIR=str(template))
 audit={'counts':{},'rejected':[],'python_fixture_code_sha256':[],'human_review_attempts':0,'forbidden_imports':[]}
 allowed_codes={'print("METHOD_ONLY")','raise SystemExit(7)','import time;time.sleep(30)',
  'import subprocess,sys;subprocess.run([sys.executable,"-c","while True:pass"])'}
 def classify(argv):
  if not isinstance(argv,(list,tuple)) or not argv:return None
  args=list(map(os.fspath,argv));exe=Path(args[0]).name
  if args[0] in ('git',shutil.which('git')):return 'git'
  if args==['/bin/sleep','20']:return 'fixed_sleep20'
  if Path(args[0]).resolve()==Path(sys.executable).resolve() and len(args)>=3 and args[1:3] in (['-B','-c'],['-c']):
   code=args[-1]
   dynamic=(code.startswith('import subprocess,time;from pathlib import Path;p=subprocess.Popen(["/bin/sleep","20"]);Path(')
     and code.endswith(').write_text(str(p.pid));time.sleep(20)')
     and 'method_child_pid' in code and '/tmp/' in code)
   if code in allowed_codes or dynamic:
    h=hashlib.sha256(code.encode()).hexdigest()
    if h not in audit['python_fixture_code_sha256']:audit['python_fixture_code_sha256'].append(h)
    return 'fixed_python_fixture'
  return None
 def hook(event,args):
  if event=='subprocess.Popen':
   name=classify(args[1])
   if name is None:
    audit['rejected'].append({'event':event,'executable':str(args[0])[:128],
                              'argv_identity':hashlib.sha256(repr(args[1]).encode()).hexdigest()})
    raise RuntimeError('UNREVIEWED_SUBPROCESS_FORBIDDEN')
   audit['counts'][name]=audit['counts'].get(name,0)+1
  elif event in ('os.system','os.exec','os.posix_spawn'):
   audit['rejected'].append({'event':event});raise RuntimeError('EXECUTION_ESCAPE_FORBIDDEN')
  elif event=='import' and str(args[0]).split('.')[0] in ('madgraph','aloha','models','pythia8','ROOT','Delphes'):
   audit['forbidden_imports'].append(str(args[0]));raise RuntimeError('MODEL_OR_PHYSICS_IMPORT_FORBIDDEN')
 sys.addaudithook(hook)
 approval=importlib.import_module(BASE+'integration_runtime.approval')
 def forbid_human_review(*args,**kwargs):
  audit['human_review_attempts']+=1
  raise RuntimeError('HUMAN_AUTHORIZATION_CREATION_FORBIDDEN')
 original_human_constructor=approval.HumanReview.__init__
 approval.HumanReview.__init__=forbid_human_review
 class Result(unittest.TextTestResult):
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs);self.rows=[]
  def addSuccess(self,test):
   self.rows.append({'test':test.id(),'status':'PASS'});super().addSuccess(test)
  def addFailure(self,test,err):
   self.rows.append({'test':test.id(),'status':'FAIL'});super().addFailure(test,err)
  def addError(self,test,err):
   self.rows.append({'test':test.id(),'status':'ERROR'});super().addError(test,err)
 suite=unittest.TestSuite()
 for name in selected:
  loaded=unittest.defaultTestLoader.loadTestsFromName(name)
  assert loaded.countTestCases()==1,name
  suite.addTest(loaded)
 before=resource.getrusage(resource.RUSAGE_CHILDREN);parent0=time.process_time();started=time.monotonic()
 stream=io.StringIO();captured=io.StringIO()
 with contextlib.redirect_stdout(captured),contextlib.redirect_stderr(captured):
  result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
 after=resource.getrusage(resource.RUSAGE_CHILDREN)
 unique_sources={r['path']:r for r in source_rows}
 source_after=[{'path':name,'sha256':hashlib.sha256((REPO/name).read_bytes()).hexdigest()} for name in unique_sources]
 unchanged=all(unique_sources[r['path']]['sha256']==r['sha256'] for r in source_after)
 output={'status':'PASS_SELECTED_SAFE_LEGACY' if result.wasSuccessful() and unchanged and not audit['rejected'] else 'FAIL_SELECTED_SAFE_LEGACY',
  'scope':'Exact81 selected source/method tests. Excludes Native/Kernel/SyntheticReceipt/PTY authorization positives; no human capability constructed.',
  'tests_run':result.testsRun,'passes':len([r for r in result.rows if r['status']=='PASS']),
  'failure_count':len(result.failures),'error_count':len(result.errors),'skipped':len(result.skipped),
  'selected':selected,'results':result.rows,
  'failures':[{'test':t.id(),'traceback':s[:10000]} for t,s in result.failures],
  'errors':[{'test':t.id(),'traceback':s[:10000]} for t,s in result.errors],
  'excluded_scope':'Native/Kernel/SyntheticReceipt/PTY authorization positives; no HumanReview constructor','source_files_before':list(unique_sources.values()),
  'source_files_after':source_after,'selected_test_sources_unchanged':unchanged,
  'implementation_snapshot_before':implementation_before['identity'],
  'implementation_snapshot_after':backend.source_snapshot()['identity'],
  'implementation_snapshot_file_count':len(implementation_before['paths']),
  'subprocess_audit':audit,'wall_seconds':time.monotonic()-started,
  'parent_CPU_seconds':time.process_time()-parent0,
  'child_CPU_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
  'new_builds':0,'native_executions':0,'REAL_ME_CALLS':0,'REAL_INTEGRALS':0,
  'INDEPENDENT_EVENTS':0,'HUMAN_AUTHORIZATION_CREATED':False,
  'full_resource_service_executed':False}
 approval.HumanReview.__init__=original_human_constructor
 output['implementation_sources_unchanged']=(output['implementation_snapshot_before']==output['implementation_snapshot_after'])
 if not output['implementation_sources_unchanged']:output['status']='FAIL_IMPLEMENTATION_SOURCE_DRIFT'
 raw=(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
 assert len(raw)<=65536,('REGRESSION_METADATA_BOUND',len(raw))
 with json_output.open('xb') as f:f.write(raw)
 text=stream.getvalue()+'\nCAPTURED CLI OUTPUT (denial-only):\n'+captured.getvalue()
 with text_output.open('x') as f:f.write(text)
 print(json.dumps({k:output[k] for k in ['status','tests_run','passes','failure_count','error_count',
  'skipped','selected_test_sources_unchanged','wall_seconds']}))
 print(json.dumps(audit,sort_keys=True))
 return output


def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args(argv)
 result=run(args.output)
 return 0 if result['status']=='PASS_SELECTED_SAFE_LEGACY' else 2

if __name__=='__main__':raise SystemExit(main())
