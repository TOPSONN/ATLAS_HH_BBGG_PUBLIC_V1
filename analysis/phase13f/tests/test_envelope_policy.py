import ast,copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'analysis/phase13f/source'))
import envelope as e
spec=importlib.util.spec_from_file_location('fixture_assessment',ROOT/'analysis/phase13f/scripts/run_full_job_fixtures.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def normal():
 return {'case':'normal','stdout_records':[{'kind':'ATTESTED','valid':True}]+[{'kind':kind,'phase':phase} for phase in ('preflight','child','receipt','postflight') for kind in ('ENTER','EXIT')]+[{'kind':'COMPLETE'}],'last_unit_properties':{'Result':'success','ExecMainStatus':'0'},'resource_stop':None,'residual_processes_after_cleanup':[]}
class EnvelopePolicy(unittest.TestCase):
 def test_exact_profile(self):self.assertEqual(e.load_profile(),e.PROFILE)
 def test_every_profile_mutation_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'profile'
   for key in e.PROFILE:
    value=copy.deepcopy(e.PROFILE);value[key]=None;p.write_text(json.dumps(value))
    with self.subTest(key=key),self.assertRaisesRegex(ValueError,'PROFILE_DRIFT'):e.load_profile(p)
 def test_bool_cannot_replace_counter(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'profile';value=dict(e.PROFILE);value['MG5_invocations']=False;p.write_text(json.dumps(value))
   with self.assertRaises(ValueError):e.load_profile(p)
 def test_no_approval_or_physics(self):
  self.assertIs(e.PROFILE['full_parser_execution_authorized'],False)
  for key in ('MG5_invocations','new_ME_calls','new_integrals','new_events'):self.assertEqual(e.PROFILE[key],0)
 def test_original_child_limits_preserved(self):
  self.assertEqual((e.PROFILE['child_original_cpu_seconds'],e.PROFILE['child_original_wall_seconds'],e.PROFILE['child_original_AS_bytes']),(2,3,536870912))
 def test_resource_bounds_are_conservative(self):
  self.assertLess(.3*(2+10+.1)+.003,4);self.assertLess(8388608+6*65536+64,9437184)
 def test_foreign_unit_rejected_before_subprocess(self):
  for name in ('ssh.service','atlas-hh-phase13f-abc.service','../bad','atlas-hh-phase13f-'+'f'*32+'.service;true'):
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'FOREIGN_UNIT'):e.unit_properties(name)
 def test_foreign_cgroup_rejected(self):
  with self.assertRaisesRegex(ValueError,'FOREIGN_CGROUP'):e.owned_cgroup('atlas-hh-phase13f-'+'a'*32+'.service','/init.scope')
 def test_fresh_output_constraints(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.assertEqual(e.fresh(p/'new'),p/'new')
   (p/'link').symlink_to(p,target_is_directory=True)
   for bad in (p,p/'../escape',p/'link/new'):
    with self.subTest(path=str(bad)),self.assertRaises(ValueError):e.fresh(bad)
 def test_receipt_size_and_overwrite_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r';e.new_json(p,{'a':1})
   with self.assertRaises(FileExistsError):e.new_json(p,{'a':2})
   with self.assertRaisesRegex(ValueError,'RECEIPT_BOUND'):e.new_json(Path(d)/'large',{'x':'X'*65536})
 def test_arbitrary_command_or_mode_rejected_before_output(self):
  with self.assertRaisesRegex(ValueError,'UNREVIEWED_FIXTURE'):e.run_case('mg5','/nonexistent/output')
 def test_observer_completion_is_directly_reachable(self):
  tree=ast.parse((ROOT/'analysis/phase13f/source/envelope.py').read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_case')
  loops=[n for n in ast.walk(fn) if isinstance(n,ast.While) and n.body and isinstance(n.body[0],ast.Assign) and any(isinstance(t,ast.Name) and t.id=='last' for t in n.body[0].targets)]
  self.assertEqual(len(loops),1)
  exits=[n for n in loops[0].body if isinstance(n,ast.If) and 'SubState' in ast.unparse(n.test)]
  self.assertEqual(len(exits),1)
 def test_cleanup_waits_for_both_processes_and_populated_flag(self):
  fake=Path('/safe/atlas-hh-phase13f-'+'a'*32+'.service')
  with patch.object(e,'cgroup_read',side_effect=[{'cgroup.procs':'123','cgroup.events':'populated 1'}, {'cgroup.procs':'','cgroup.events':'populated 1'},{'cgroup.procs':'','cgroup.events':'populated 0'}]),patch.object(e,'kill_owned') as kill,patch.object(e.time,'sleep'):
   self.assertTrue(e.wait_empty(fake,e.time.monotonic()+1));self.assertEqual(kill.call_count,2)
 def test_cleanup_never_converts_timeout_to_success(self):
  with patch.object(e,'cgroup_read',return_value={'cgroup.procs':'123','cgroup.events':'populated 1'}),patch.object(e,'kill_owned'):
   self.assertFalse(e.wait_empty(Path('/safe/job'),e.time.monotonic()-1))
 def test_full_disk_diagnostics_are_preallocated_within_existing_caps(self):
  source=(ROOT/'analysis/phase13f/source/workflow.py').read_text()
  self.assertIn("stream.write(b'\\0'*65536);stream.flush();stream.seek(0)",source)
  self.assertLess(source.index("stream.write(b'\\0'*65536)"),source.index('p=subprocess.Popen'))
  self.assertEqual(e.PROFILE['per_regular_file_bytes'],65536)
 def test_true_normal(self):self.assertTrue(a.assess(normal()))
 def test_normal_rejects_observer_resource_stop(self):
  for reason in ('TOTAL_WALL_EARLY_STOP','AGGREGATE_CPU_EARLY_STOP','RESIDUAL_CGROUP_PROCESSES'):
   row=normal();row['resource_stop']=reason
   with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,'NORMAL_FOUR_PHASE'):a.assess(row)
 def test_normal_rejects_each_missing_phase(self):
  for phase in e.PHASES:
   row=normal();row['stdout_records']=[v for v in row['stdout_records'] if v.get('phase')!=phase]
   with self.subTest(phase=phase),self.assertRaises(ValueError):a.assess(row)
 def test_no_attestation_rejected(self):
  row=normal();row['stdout_records']=row['stdout_records'][1:]
  with self.assertRaisesRegex(ValueError,'KERNEL_PROOF'):a.assess(row)
 def test_attestation_false_rejected(self):
  row=normal();row['stdout_records'][0]['valid']=False
  with self.assertRaises(ValueError):a.assess(row)
 def test_residual_process_never_passes(self):
  row=normal();row['residual_processes_after_cleanup']=[123]
  with self.assertRaisesRegex(ValueError,'RESIDUAL_PROCESS'):a.assess(row)
 def test_cpu_stop_requires_actual_aggregate_usage(self):
  row=normal();row['case']='aggregate_cpu';row['resource_stop']='AGGREGATE_CPU_EARLY_STOP';row['max_observed_CPU_usec']=1
  with self.assertRaisesRegex(ValueError,'CPU_STOP'):a.assess(row)
 def test_all_31_required_cases(self):self.assertEqual(len(e.CASES),31);self.assertEqual(len(set(e.CASES)),31)
 def test_kernel_predicate_independently_fails_mutated_facts(self):
  tree=ast.parse((ROOT/'analysis/phase13f/source/workflow.py').read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='valid' for t in n.targets))
  allowed=(ast.Expression,ast.BoolOp,ast.And,ast.Compare,ast.Eq,ast.Name,ast.Load,ast.Subscript,ast.Constant,ast.List,ast.BinOp,ast.Mult)
  expression=ast.Expression(node.value)
  self.assertTrue(all(isinstance(n,allowed) for n in ast.walk(expression)))
  code=compile(ast.fix_missing_locations(expression),'<independent predicate test>','eval')
  facts={'cpu.max':'3000 10000','cpu.max.burst':'0','memory.max':'536870912','memory.swap.max':'0','memory.oom.group':'1','pids.max':'8','repository_readonly':True,'cgroup_readonly':True,'AS':[536870912]*2,'CPU':[2]*2,'FSIZE':[65536]*2}
  self.assertTrue(eval(code,{'__builtins__':{}},{'facts':facts,'capacity':8388608}))
  for key in facts:
   wrong=dict(facts);wrong[key]=None
   with self.subTest(key=key):self.assertFalse(eval(code,{'__builtins__':{}},{'facts':wrong,'capacity':8388608}))
  self.assertFalse(eval(code,{'__builtins__':{}},{'facts':facts,'capacity':1081101176832}))
if __name__=='__main__':unittest.main()

class ControllerLossEvidence(unittest.TestCase):
 def test_idle_or_incomplete_controller_loss_cannot_pass(self):
  row={'case':'controller_loss','stdout_records':[{'kind':'ATTESTED','valid':True}], 'last_unit_properties':{'Result':'timeout'},'observer_is_separate_process':True,'residual_processes_after_cleanup':[],'max_observed_CPU_usec':3000000,'elapsed_including_host_cleanup_seconds':10.2,'cgroup_empty_and_unpopulated_verified':True}
  self.assertTrue(a.assess(row))
  for k,v in [('max_observed_CPU_usec',1),('max_observed_CPU_usec',4000001),('elapsed_including_host_cleanup_seconds',13.1),('cgroup_empty_and_unpopulated_verified',False),('observer_is_separate_process',False)]:
   bad=copy.deepcopy(row);bad[k]=v
   with self.subTest(key=k,value=v),self.assertRaises(ValueError):a.assess(bad)
