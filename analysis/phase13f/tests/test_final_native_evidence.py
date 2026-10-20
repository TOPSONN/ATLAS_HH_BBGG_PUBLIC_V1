"""Independent data-only regression: never import the producing guard/assessor.
Native tests are NOT rerun by this file; it checks the published raw local data.
"""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'analysis/phase13f/evidence/final_suite'
PHASES=('preflight','child','receipt','postflight')
CASES=['normal']+[a+'_'+b for a in PHASES for b in ('cpu','ram','wall','disk','abnormal')]+['aggregate_cpu','orphan','controller_loss','pids','source_write','cgroup_write','namespace_escape','stdout_overflow','disk_inodes','legacy_missing_approval']
def read(p):return json.loads(p.read_text())
class NativeEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.summary=read(E/'suite_summary.json')
  cls.rows={c:read(E/c/'result.json') for c in CASES}
 def test_complete_required_cases(self):
  s=self.summary;self.assertIsNone(s['failure']);self.assertIs(s['FULL_LAUNCH_ENVELOPE_VERIFIED'],True)
  self.assertEqual([x['case'] for x in s['results']],CASES)
  self.assertTrue(all(x['status']=='PASS_EXPECTED_RESULT' for x in s['results']))
 def test_effective_kernel_limits_all_cases(self):
  expected={'cpu.max':'3000 10000','cpu.max.burst':'0','memory.max':'536870912','memory.swap.max':'0','memory.oom.group':'1','pids.max':'8','work_capacity_bytes':8388608,'repository_readonly':True,'cgroup_readonly':True,'AS':[536870912]*2,'CPU':[2]*2,'FSIZE':[65536]*2}
  for c,r in self.rows.items():
   with self.subTest(case=c):
    a=[x for x in r['stdout_records'] if x.get('kind')=='ATTESTED'];self.assertEqual(len(a),1)
    for k,v in expected.items():self.assertEqual(a[0][k],v)
    self.assertIs(a[0]['valid'],True)
 def test_measured_cpu_wall_ram_bound(self):
  for c,r in self.rows.items():
   with self.subTest(case=c):
    u=r['last_unit_properties'];cpu=max(r['max_observed_CPU_usec'],int(u['CPUUsageNSec'])/1000)
    self.assertGreater(cpu,0);self.assertLessEqual(cpu,4000000)
    self.assertLessEqual(r['elapsed_including_host_cleanup_seconds'],13)
    self.assertLessEqual((int(u['ExecMainExitTimestampMonotonic'])-int(u['ExecMainStartTimestampMonotonic']))/1e6,13)
    self.assertGreater(int(u['MemoryPeak']),0);self.assertLessEqual(int(u['MemoryPeak']),536870912)
 def test_no_residual_or_host_write(self):
  for c,r in self.rows.items():
   with self.subTest(case=c):
    self.assertEqual(r['residual_processes_after_cleanup'],[])
    self.assertIs(r['host_work_directory_empty'],True);self.assertIs(r['canary_preserved'],True)
 def test_real_four_phase_positive_and_original_guard(self):
  r=self.rows['normal'];logs=r['stdout_records']
  for kind in ('ENTER','EXIT'):self.assertEqual([x['phase'] for x in logs if x.get('kind')==kind],list(PHASES))
  self.assertIsNone(r['resource_stop']);self.assertEqual(r['last_unit_properties']['Result'],'success')
  child=next(x for x in logs if x.get('kind')=='CHILD_RESULT')['details'][0]
  self.assertEqual(child['bytes'],9302);self.assertEqual(child['sha256'],'e4567fd50d47a317407eb10cca76387053cdf06631949773296314702f77dca1')
  self.assertEqual(child['original_child_limits'],{'address_space_bytes':536870912,'cpu_seconds':2,'wall_seconds':3,'output_file_bytes':65536})
 def test_all_negative_phases_stop_before_following_work(self):
  for c,r in self.rows.items():
   if not any(c.startswith(p+'_') for p in PHASES):continue
   phase=c.split('_')[0];logs=r['stdout_records']
   self.assertEqual([x['phase'] for x in logs if x.get('kind')=='ENTER'][-1],phase)
   self.assertFalse(any(x.get('kind')=='COMPLETE' or (x.get('kind')=='EXIT' and x.get('phase')==phase) for x in logs))
 def test_group_oom_at_each_phase(self):
  for p in PHASES:self.assertEqual(self.rows[p+'_ram']['last_unit_properties']['Result'],'oom-kill')
 def test_disk_enospc_at_each_phase(self):
  for p in PHASES:
   r=self.rows[p+'_disk'];logs=r['stdout_records'];details=[d for x in logs for d in x.get('details',[])]
   self.assertTrue(any(x.get('errno')==28 for x in logs+details))
 def test_aggregate_cpu_and_controller_loss_are_actual_busy_tests(self):
  r=self.rows['aggregate_cpu'];self.assertEqual(r['resource_stop'],'AGGREGATE_CPU_EARLY_STOP');self.assertGreaterEqual(r['max_observed_CPU_usec'],2500000)
  r=self.rows['controller_loss'];self.assertEqual(r['last_unit_properties']['Result'],'timeout');self.assertIs(r['observer_is_separate_process'],True);self.assertIs(r['cgroup_empty_and_unpopulated_verified'],True)
  self.assertGreaterEqual(r['max_observed_CPU_usec'],2500000)
 def test_orphan_and_inode_and_log_negative(self):
  self.assertTrue(self.rows['orphan']['residual_pids_detected']);self.assertEqual(self.rows['orphan']['resource_stop'],'RESIDUAL_CGROUP_PROCESSES')
  self.assertTrue(any(x.get('errno')==28 and x.get('tmpfs_free_inodes')==0 for x in self.rows['disk_inodes']['stdout_records']))
  self.assertEqual(self.rows['stdout_overflow']['last_unit_properties']['ExecMainStatus'],'25')
 def test_no_physical_dispatch_or_approval(self):
  for r in self.rows.values():
   for k in ('MG5_invocations','new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events'):self.assertEqual(type(r[k]),int);self.assertEqual(r[k],0)
  self.assertIs(self.summary['parser_or_physics_authorized'],False)
 def test_exact_executed_sources_still_match(self):
  snap=self.summary['source_snapshot'];rows=[]
  for r in snap['paths']:
   relative=r['path'].split('/atlas_hh_phase13f_v1/',1)[1];raw=(ROOT/relative).read_bytes()
   self.assertEqual(len(raw),r['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256']);rows.append({'path':relative,'sha256':r['sha256']})
  ident=hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest();self.assertEqual(ident,snap['identity'])
  for r in self.rows.values():self.assertEqual(r['source_snapshot_identity'],ident)
 def test_host_export_actual_bounds(self):
  inv=read(E/'host_exports_inventory.json')
  self.assertEqual([r['case'] for r in inv['cases']],CASES)
  for r in inv['cases']:
   self.assertLessEqual(r['total_regular_bytes'],6*65536+64)
   self.assertLessEqual(r['metadata_files'],4)
   self.assertTrue(r['work_empty'])
   for f in r['files']:self.assertLessEqual(f['bytes'],65536)
