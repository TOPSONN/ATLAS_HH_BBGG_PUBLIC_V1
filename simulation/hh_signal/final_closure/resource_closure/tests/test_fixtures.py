"""Harmless offline fixture/assessor regressions; no service/native dispatch."""
import ast,copy,errno,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from .. import fixtures as f
from ..run_fixtures import assess,flattened,save_new,campaign_outcome
from .. import allocation_guard as guard

def record(kind,**fields):return {'kind':kind,**fields}
def allocation_facts():
 return {'schema':'HH_ALLOCATION_BYPASS_GUARD_V1','installed':True,'pid':123,
  'program_sha256':guard.program_identity(),'instruction_count':len(guard.program()),
  'seccomp_mode':2,'no_new_privs':1,'filter_count_before':1,'filter_count_after':2,
  'native_architecture':'x86_64','x32_action':'KILL_PROCESS','default_action':'ALLOW',
  'denied_action':'ERRNO_EPERM','denied_syscalls':dict(guard.DENIED),
  'safe_readonly_tty_requests':list(guard.SAFE_TTY_REQUESTS),
  'physical_or_build_authorization':False}
def evidence(case='normal'):
 p={'aggregate_CPU_seconds':4,'aggregate_wall_seconds':13,'aggregate_memory_bytes':536870912,
  'cpu_quota_percent':30,'cpu_quota_period_usec':10000,'max_tasks':16,
  'per_process_address_space_bytes':536870912,'per_process_CPU_seconds':2,
  'per_regular_file_bytes':65536,'work_tmpfs_bytes':8388608,'work_tmpfs_inodes':1024,
  'tmp_tmpfs_bytes':1048576,'tmp_tmpfs_inodes':256,'aggregate_disk_bytes':16777216,
  'host_metadata_files':4,'host_metadata_bytes':65536,'source_control_reserve_bytes':0,
  'host_allocation_granule_bytes':4096}
 selected=f.spec(case);phase=selected['phase']
 index=len(f.PHASES) if phase is None else f.PHASES.index(phase)
 import hashlib
 identity=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 logs=[record('ATTESTED',valid=True,mode='fixture',source_identity='a'*64,pid=123,
  allocation_guard=allocation_facts(),writable_mounts=['/owned/work','/tmp'],
  exclusive_job_lock={'acquired':True,'pid':123,'read_only':True,
   'path':str(Path.home()/'simulations/.resource_envelope.lock'),'dev':1234,'inode':5678},
  profile_identity=identity,repository_readonly=True,cgroup_readonly=True,affinity_count=1,
  effective={'cpu.max':'3000 10000','cpu.max.burst':'0','memory.max':'536870912',
   'memory.swap.max':'0','memory.oom.group':'1','pids.max':'16'},
  limits={'AS':[536870912]*2,'CPU':[2]*2,'FSIZE':[65536]*2,'CORE':[0,0]},
  mounts=[{'path':'/owned/work','bytes':8388608,'inodes':1024,'filesystem':'tmpfs'},
          {'path':'/tmp','bytes':1048576,'inodes':256,'filesystem':'tmpfs'}])]
 for prior in f.PHASES[:index]:logs += [record('ENTER',phase=prior),record('EXIT',phase=prior)]
 row={'case':case,'profile':p,'evidence_class':'SYNTHETIC_METHOD_ONLY',
  'stdout_records':logs,'last_unit_properties':{'Result':'success','ExecMainStatus':'0'},
  'max_observed_CPU_usec':2000000,'max_observed_memory_bytes':20000000,
  'payload_wall_seconds':1.0,'elapsed_including_host_cleanup_seconds':1.1,
  'resource_stop':None,'residual_pids_detected':[],'residual_processes_after_cleanup':[],
  'cgroup_empty_and_unpopulated_verified':True,'host_work_directory_empty':True,
  'canary_preserved':True,'source_snapshot_identity':'a'*64,
  'measured_host_payload_allocated_bytes':0,'host_canary_allocated_bytes':4096,
  'actual_data_disk_upper_bytes':8388608+1048576+4*65536+4096,
  'host_payload_files':[{'path':n,'bytes':0,'allocated_bytes':0,'sha256':'b'*64} for n in
   ('chunk_00.bin','chunk_01.bin','index.bin','stdout.log','stderr.log')],
  'formal_build_executed':False,'full_parser_or_physics_authorized':False,
  'MG5_invocations':0,'new_ME_calls':0,'new_integrals':0,'new_hard_events':0,
  'new_Pythia_events':0,'new_Delphes_events':0}
 if case=='normal':
  logs.append(record('COMPLETE',all_six_phases=True));return row
 logs.append(record('ENTER',phase=phase));mode=selected['mode']
 last=row['last_unit_properties']
 if mode in f.MODES:
  logs.append(record('INJECTED',phase=phase,mode=mode,
   execution_site='child' if phase in ('compile','loader') else 'supervisor'))
  if mode=='ram':last['Result']='oom-kill';row['max_observed_memory_bytes']=536870912
  elif mode=='disk':logs.append(record('LIMIT_ERROR',errno=28))
  elif mode=='abnormal':
   if phase in ('compile','loader'):
    last['ExecMainStatus']='2';logs.append(record('CHILD_MEASURED',exit=87))
   else:last['ExecMainStatus']='87'
  elif mode=='wall':last['Result']='timeout'
  else:last['ExecMainStatus']='9'
 elif case=='job_lock':
  logs.append(record('CONTAINED',check='JOB_LOCK',job_lock_probe={
   'owner_pid':123,'separate_open_description':True,'denied':True,'errno':11,
   'path':str(Path.home()/'simulations/.resource_envelope.lock')}))
 elif case=='allocation_bypass':
  logs.append(record('CONTAINED',check='ALLOCATION_BYPASS',allocation_probe={
   'installed':True,'all_denied':True,'program_sha256':guard.program_identity(),'pid':123,
   'allocated_bytes_before':0,'allocated_bytes_after':0,
   'logical_bytes_before':0,'logical_bytes_after':0,
   'checks':[{'operation':n,'errno':1,'return_code':-1,'syscall':s} for n,s in
    [('fallocate_keep_size','fallocate'),('ioctl_clone','ioctl'),('setxattr','fsetxattr')]]}))
 elif case=='aggregate_cpu':
  row['resource_stop']='AGGREGATE_CPU_EARLY_STOP';row['max_observed_CPU_usec']=2600000
 elif case=='controller_loss':
  last['Result']='timeout';row.update(controller_exited_verified=True,
   observer_is_separate_process=True,max_observed_CPU_usec=2900000)
 elif case=='orphan':
  row['resource_stop']='RESIDUAL_CGROUP_PROCESSES';row['residual_pids_detected']=[12345]
  logs.append(record('ORPHAN_CREATED',setsid=True,pid=12345))
 elif case in ('stdout_overflow','chunk_overflow'):last['ExecMainStatus']='25'
 elif case in ('tmp_disk','tmp_inodes','disk_inodes'):
  logs.append(record('LIMIT_ERROR',errno=28,tmpfs_free_inodes=0,
   root='/tmp' if case.startswith('tmp_') else '/private/work'))
 else:
  checks={'source_write':'READONLY_CANARY','cgroup_write':'CGROUP_READONLY',
   'namespace_escape':'NAMESPACE_ESCAPE_DENIED','pids':'TASKS_MAX',
   'legacy_missing_approval':'LEGACY_MISSING_APPROVAL','archive_bound':'ARCHIVE_BOUND'}
  logs.append(record('CONTAINED',check=checks[case]))
 return row

class FixedFixtureTests(unittest.TestCase):
 def context(self):
  logs=[];called=[]
  ctx={'emit':lambda kind,**kw:logs.append(record(kind,**kw)),
   'work':Path('/METHOD_ONLY_UNUSED'),'phase_callbacks':
   {p:(lambda c,p=p:called.append(p)) for p in f.PHASES}}
  return ctx,logs,called
 def test_exact_case_matrix_unique(self):
  self.assertEqual(len(f.CASES),47);self.assertEqual(len(set(f.CASES)),47)
  self.assertEqual(f.PHASES,('preflight','compile','loader','receipt','postflight','export'))
  for phase in f.PHASES:
   for mode in f.MODES:self.assertEqual(f.spec(phase+'_'+mode),{'phase':phase,'mode':mode})
 def test_unknown_case_and_action_rejected_before_work(self):
  for case in ('build','physical_restart','normal;true','../normal',None):
   with self.assertRaises(ValueError):f.spec(case)
  for mode in ('gfortran','ME','integral','generate_events',''):
   with self.assertRaises(ValueError):f.action(mode)
 def test_normal_all_six_callback_order(self):
  ctx,logs,called=self.context();result=f.run_fixture('normal',ctx)
  self.assertEqual(called,list(f.PHASES))
  self.assertEqual([r['phase'] for r in logs if r['kind']=='ENTER'],list(f.PHASES))
  self.assertEqual([r['phase'] for r in logs if r['kind']=='EXIT'],list(f.PHASES))
  self.assertEqual(logs[-1]['kind'],'COMPLETE');self.assertFalse(result['formal_build_executed'])
 def test_missing_callback_never_partial_success(self):
  ctx,logs,_=self.context();del ctx['phase_callbacks']['export']
  with self.assertRaisesRegex(ValueError,'EXACT_SIX'):f.run_fixture('normal',ctx)
  self.assertEqual(logs,[])
 def test_all_thirty_phase_injections_stop_before_callback(self):
  class DeliberateStop(Exception):pass
  for phase in f.PHASES:
   for mode in f.MODES:
    with self.subTest(phase=phase,mode=mode):
     ctx,logs,called=self.context()
     ctx['child_action']=lambda m,c:(_ for _ in ()).throw(DeliberateStop())
     with patch.object(f,'action',side_effect=DeliberateStop):
      with self.assertRaises(DeliberateStop):f.run_fixture(phase+'_'+mode,ctx)
     self.assertEqual(called,list(f.PHASES[:f.PHASES.index(phase)]))
     self.assertFalse(any(r['kind']=='COMPLETE' for r in logs))
 def test_compile_and_loader_require_actual_child_hook(self):
  for phase in ('compile','loader'):
   ctx,_,_=self.context()
   with self.assertRaisesRegex(ValueError,'FIXED_CHILD_ACTION'):f.run_fixture(phase+'_cpu',ctx)
 def test_orphan_is_created_after_real_fixed_loader_callback(self):
  class DeliberateStop(Exception):pass
  ctx,logs,called=self.context()
  with patch.object(f,'special',side_effect=DeliberateStop):
   with self.assertRaises(DeliberateStop):f.run_fixture('orphan',ctx)
  self.assertEqual(called,list(f.PHASES[:3]))
  self.assertFalse(any(r['kind']=='COMPLETE' for r in logs))
 def test_job_lock_probe_callback_required_and_no_business_callback(self):
  ctx,logs,called=self.context()
  with self.assertRaisesRegex(ValueError,'JOB_LOCK_PROBE_CALLBACK'):f.run_fixture('job_lock',ctx)
  ctx,logs,called=self.context();ctx['job_lock']=lambda c:{'fixture':'NO_LIVE_FLOCK'}
  f.run_fixture('job_lock',ctx)
  self.assertEqual(called,[])
  self.assertEqual(logs[-2]['check'],'JOB_LOCK')
  self.assertEqual(logs[-1]['kind'],'NEGATIVE_COMPLETE')
 def test_allocation_probe_callback_is_required_and_ends_flow(self):
  ctx,logs,called=self.context()
  with self.assertRaisesRegex(ValueError,'ALLOCATION_BYPASS_CALLBACK'):f.run_fixture('allocation_bypass',ctx)
  ctx,logs,called=self.context()
  ctx['allocation_bypass']=lambda c:{'fixture':'NO_REAL_SYSCALL'}
  f.run_fixture('allocation_bypass',ctx)
  self.assertEqual(called,[])
  self.assertEqual(logs[-2]['check'],'ALLOCATION_BYPASS')
  self.assertEqual(logs[-1]['kind'],'NEGATIVE_COMPLETE')
 def test_archive_rejection_is_exact_and_ends_flow(self):
  ctx,logs,called=self.context()
  ctx['archive_bound']=lambda c:(_ for _ in ()).throw(ValueError('ARCHIVE_CAPACITY'))
  f.run_fixture('archive_bound',ctx)
  self.assertEqual(called,list(f.PHASES[:-1]))
  self.assertEqual(logs[-1]['kind'],'NEGATIVE_COMPLETE')
  ctx,_,_=self.context();ctx['archive_bound']=lambda c:None
  with self.assertRaisesRegex(ValueError,'NOT_ENFORCED'):f.run_fixture('archive_bound',ctx)
 def test_legacy_approval_denial_has_no_creation_path(self):
  ctx,logs,_=self.context();ctx['legacy_missing_approval']=lambda c:True
  f.run_fixture('legacy_missing_approval',ctx)
  self.assertEqual(logs[-2]['check'],'LEGACY_MISSING_APPROVAL')
  ctx,_,_=self.context();ctx['legacy_missing_approval']=lambda c:False
  with self.assertRaises(ValueError):f.run_fixture('legacy_missing_approval',ctx)
 def test_direct_child_entry_rejects_before_any_stress_action(self):
  with patch.object(f,'require_child_envelope',side_effect=ValueError('NOT_ENCLOSED')), \
       patch.object(f,'action') as stress,patch('sys.argv',['fixed_fixture','--action','ram']):
   with self.assertRaisesRegex(ValueError,'NOT_ENCLOSED'):f.main()
   stress.assert_not_called()
 def test_child_envelope_checks_kernel_before_action_source(self):
  tree=ast.parse(Path(f.__file__).read_text())
  main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  calls=[n.func.id for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
  self.assertLess(calls.index('require_child_envelope'),calls.index('action'))
  child=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require_child_envelope')
  text=ast.get_source_segment(Path(f.__file__).read_text(),child)
  for token in ('owned_cgroup','cgroup_read','memory.max','cpu.max','RLIMIT_AS',
                'RLIMIT_CPU','RLIMIT_FSIZE','statvfs','ST_RDONLY'):
   self.assertIn(token,text)
 def test_fixture_source_has_fixed_python_actions_no_native_dispatch(self):
  text=Path(f.__file__).read_text();tree=ast.parse(text)
  calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
  self.assertFalse(calls & {'eval','exec','compile','__import__'})
  self.assertNotIn('gfortran',text);self.assertNotIn('ldd',text)
  self.assertIn('300*1024**2',text);self.assertIn('range(0,len(data),4096)',text)
  self.assertIn("os.setsid()",text);self.assertIn("os.fork()",text)

class CampaignScopeTests(unittest.TestCase):
 def successful_rows(self):
  return [{'case':case,'status':'PASS_EXPECTED_RESULT'} for case in f.CASES]
 def test_all47_payload_success_still_cannot_certify_full_controller(self):
  result=campaign_outcome(list(f.CASES),self.successful_rows(),None)
  self.assertTrue(result['PAYLOAD_BUSINESS_ENVELOPE_VERIFIED'])
  self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])
  self.assertFalse(result['FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'])
  self.assertFalse(result['FORMAL_BUILD_ENVELOPE_VERIFIED'])
  for term in ('Host provisioning','observer CPU/RAM','post-unit','result writing'):
   self.assertIn(term,result['remaining_scope_reason'])
 def test_missing_partial_failed_or_reordered_cases_cannot_certify_payload(self):
  complete=self.successful_rows()
  cases=[(list(f.CASES),complete[:-1],None),
   (list(f.CASES)[:-1],complete[:-1],None),
   (list(f.CASES),complete,{'case':f.CASES[-1],'reason':'failure'}),
   (list(f.CASES),list(reversed(complete)),None)]
  changed=copy.deepcopy(complete);changed[-1]['status']='FAIL'
  cases.append((list(f.CASES),changed,None))
  for chosen,rows,failure in cases:
   result=campaign_outcome(chosen,rows,failure)
   self.assertFalse(result['PAYLOAD_BUSINESS_ENVELOPE_VERIFIED'])
   self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])
 def test_environment_or_api_cannot_override_full_controller_flags(self):
  with patch.dict('os.environ',{'FULL_LAUNCH_ENVELOPE_VERIFIED':'true',
                               'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED':'true'}):
   result=campaign_outcome(list(f.CASES),self.successful_rows(),None)
   self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])
   self.assertFalse(result['FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'])
  with self.assertRaises(TypeError):
   campaign_outcome(list(f.CASES),self.successful_rows(),None,
                    FULL_LAUNCH_ENVELOPE_VERIFIED=True)

class StrictAssessorTests(unittest.TestCase):
 def test_all_47_synthetic_expected_data_shapes(self):
  for case in f.CASES:
   with self.subTest(case=case):self.assertTrue(assess(evidence(case)))
 def test_no_attestation_no_pass(self):
  for mutation in ('missing','false','duplicate'):
   row=evidence()
   if mutation=='missing':row['stdout_records'].pop(0)
   elif mutation=='false':row['stdout_records'][0]['valid']=False
   else:row['stdout_records'].insert(0,record('ATTESTED',valid=True))
   with self.assertRaises(ValueError):assess(row)
 def test_valid_flag_cannot_hide_changed_kernel_facts(self):
  mutations=[lambda p:p['effective'].update({'cpu.max':'max 10000'}),
   lambda p:p['effective'].update({'memory.max':'max'}),
   lambda p:p['effective'].update({'cpu.max.burst':'1000'}),
   lambda p:p['limits'].update(CPU=[60,60]),
   lambda p:p['mounts'][0].update(bytes=1073741824),
   lambda p:p.update(repository_readonly=False),lambda p:p.update(affinity_count=2),
   lambda p:p.update(profile_identity='0'*64)]
  for mutation in mutations:
   row=evidence();mutation(row['stdout_records'][0])
   with self.assertRaises(ValueError):assess(row)
 def test_valid_flag_cannot_hide_missing_or_tampered_allocation_filter(self):
  for mutation in (lambda p:p.pop('allocation_guard'),
   lambda p:p['allocation_guard'].update(program_sha256='0'*64),
   lambda p:p['allocation_guard'].update(pid=124),
   lambda p:p['allocation_guard'].update(seccomp_mode=0),
   lambda p:p['allocation_guard'].update(filter_count_after=1),
   lambda p:p['allocation_guard'].update(denied_syscalls={}),
   lambda p:p.update(writable_mounts=['/owned/work','/tmp','/var/tmp'])):
   row=evidence();mutation(row['stdout_records'][0])
   with self.assertRaises(ValueError):assess(row)
 def test_single_job_lock_must_be_actual_readonly_same_pid_canonical_inode(self):
  for mutation in (lambda p:p.pop('exclusive_job_lock'),
   lambda p:p['exclusive_job_lock'].update(acquired=False),
   lambda p:p['exclusive_job_lock'].update(read_only=False),
   lambda p:p['exclusive_job_lock'].update(pid=124),
   lambda p:p['exclusive_job_lock'].update(path='/tmp/fake_lock'),
   lambda p:p['exclusive_job_lock'].update(dev=0),
   lambda p:p['exclusive_job_lock'].update(inode=0),
   lambda p:p['exclusive_job_lock'].update(dev=True)):
   row=evidence();mutation(row['stdout_records'][0])
   with self.assertRaises(ValueError):assess(row)
 def test_probe_requires_same_worker_and_exact_filter_identity(self):
  for mutation in (lambda p:p.update(pid=124),
                   lambda p:p.update(program_sha256='d'*64)):
   row=evidence('allocation_bypass');mutation(row['stdout_records'][-1]['allocation_probe'])
   with self.assertRaises(ValueError):assess(row)
 def test_transport_complete_and_file_caps_independent(self):
  for mutate in (lambda r:r['host_payload_files'].pop(),
   lambda r:r['host_payload_files'][0].update(bytes=65537),
   lambda r:r['host_payload_files'][0].update(allocated_bytes=65537),
   lambda r:r.update(measured_host_payload_allocated_bytes=65536),
   lambda r:r.update(host_canary_allocated_bytes=8192),
   lambda r:r.update(actual_data_disk_upper_bytes=0),
   lambda r:r['host_payload_files'][0].update(sha256='missing')):
   row=evidence();mutate(row)
   with self.assertRaises(ValueError):assess(row)
 def test_normal_cannot_hide_resource_stop_or_failed_phase(self):
  for change in (lambda r:r.update(resource_stop='TOTAL_WALL_EARLY_STOP'),
   lambda r:r['stdout_records'].append(record('FAILED',reason='broken')),
   lambda r:r['stdout_records'].pop(2),
   lambda r:r['last_unit_properties'].update(Result='oom-kill')):
   row=evidence();change(row)
   with self.assertRaises(ValueError):assess(row)
 def test_every_phase_failure_blocks_downstream_and_completion(self):
  for phase in f.PHASES:
   row=evidence(phase+'_cpu');row['stdout_records'].append(record('EXIT',phase=phase))
   with self.assertRaises(ValueError):assess(row)
   row=evidence(phase+'_cpu');row['stdout_records'].append(record('COMPLETE',all_six_phases=True))
   with self.assertRaises(ValueError):assess(row)
 def test_metrics_must_be_actual_finite_and_within_caps(self):
  values={'max_observed_CPU_usec':[0,4000001,False],
   'max_observed_memory_bytes':[0,536870913,False],
   'payload_wall_seconds':[0,13.001,float('nan')],
   'elapsed_including_host_cleanup_seconds':[13.501,float('inf')]}
  for key,bad in values.items():
   for value in bad:
    row=evidence();row[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):assess(row)
 def test_each_physical_counter_missing_nonzero_or_boolean_rejected(self):
  for key in ('MG5_invocations','new_ME_calls','new_integrals','new_hard_events',
              'new_Pythia_events','new_Delphes_events'):
   for bad in (None,1,False):
    row=evidence();row[key]=bad
    with self.assertRaises(ValueError):assess(row)
 def test_residual_populated_or_unproven_cleanup_never_passes(self):
  for key,value in [('residual_processes_after_cleanup',[123]),
   ('cgroup_empty_and_unpopulated_verified',False),('canary_preserved',False),
   ('host_work_directory_empty',False),('formal_build_executed',True)]:
   row=evidence();row[key]=value
   with self.assertRaises(ValueError):assess(row)
 def test_job_lock_probe_requires_same_owner_separate_description_and_eagain(self):
  for mutation in (lambda p:p.update(owner_pid=124),
   lambda p:p.update(separate_open_description=False),lambda p:p.update(denied=False),
   lambda p:p.update(errno=1),lambda p:p.update(errno=0),
   lambda p:p.update(path='/tmp/not_the_global_lock')):
   row=evidence('job_lock');mutation(row['stdout_records'][-1]['job_lock_probe'])
   with self.assertRaises(ValueError):assess(row)
 def test_allocation_probe_requires_real_mutator_denials_and_no_disk_growth(self):
  for mutation in (lambda p:p.update(installed=False),
   lambda p:p.update(all_denied=False),lambda p:p.update(checks=[]),
   lambda p:p.update(pid=0),lambda p:p.update(program_sha256='missing'),
   lambda p:p['checks'][0].update(return_code=0),
   lambda p:p['checks'][2].update(syscall='wrong_syscall'),
   lambda p:p.update(logical_bytes_after=4096),
   lambda p:p['checks'][0].update(errno=0),lambda p:p['checks'][1].update(errno=95),
   lambda p:p['checks'][2].update(operation='not_setxattr'),
   lambda p:p.update(allocated_bytes_after=4096),
   lambda p:p.update(allocated_bytes_before=None)):
   row=evidence('allocation_bypass');mutation(row['stdout_records'][-1]['allocation_probe'])
   with self.assertRaises(ValueError):assess(row)
 def test_cpu_flag_without_cumulative_measurement_is_rejected(self):
  row=evidence('aggregate_cpu');row['max_observed_CPU_usec']=1000
  with self.assertRaisesRegex(ValueError,'CUMULATIVE'):assess(row)
 def test_ram_failure_requires_kernel_oom_not_status_flag(self):
  row=evidence('receipt_ram');row['last_unit_properties']['Result']='success'
  with self.assertRaisesRegex(ValueError,'OOM'):assess(row)
 def test_controller_loss_requires_dead_distinct_controller_and_kernel_timeout(self):
  for key in ('controller_exited_verified','observer_is_separate_process'):
   row=evidence('controller_loss');row[key]=False
   with self.assertRaises(ValueError):assess(row)
  row=evidence('controller_loss');row['last_unit_properties']['Result']='signal'
  with self.assertRaises(ValueError):assess(row)
 def test_inode_and_tmp_disk_require_specific_observed_errno(self):
  for case in ('disk_inodes','tmp_inodes','tmp_disk'):
   row=evidence(case);row['stdout_records'][-1]['errno']=5
   with self.assertRaises(ValueError):assess(row)
  row=evidence('tmp_inodes');row['stdout_records'][-1]['tmpfs_free_inodes']=4
  with self.assertRaises(ValueError):assess(row)
 def test_child_injection_cannot_be_labelled_supervisor(self):
  row=evidence('compile_disk');row['stdout_records'][-2]['execution_site']='supervisor'
  with self.assertRaises(ValueError):assess(row)
 def test_protocol_child_details_bounded(self):
  with self.assertRaises(ValueError):flattened([{'details':[{}]*17}])
  with self.assertRaises(ValueError):flattened([{'details':['not-a-record']}])
 def test_bounded_new_receipt_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'new.json';save_new(path,{'fixture':'SYNTHETIC_METHOD_ONLY'})
   with self.assertRaises(FileExistsError):save_new(path,{})
   with self.assertRaises(ValueError):save_new(Path(td)/'large.json',{'x':'a'*65536})
