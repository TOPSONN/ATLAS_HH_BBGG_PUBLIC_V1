import copy,hashlib,importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('gate_evidence',Path(__file__).resolve().parents[1]/'scripts/audit_pilot_gate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class EvidenceProfiles(unittest.TestCase):
 def fixtures(self):
  a={'evidence_class':'HISTORICAL_SOURCE_AUDIT','new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_pythia_events':0,'new_delphes_events':0,'physical_pilot_executed':False,'new_MG5_parser_calls':0}
  b={'evidence_class':'HISTORICAL_SOURCE_AUDIT','new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'physical_pilot_executed':False,'generator_parser_executed':False}
  d={'evidence_class':'ACTUAL_EXISTING_DATA_READBACK','status':'VALIDATED_WITH_LIMITS','new_ME_calls':0,'new_integrals':0,'new_hard_events':0,'new_Pythia_events':0,'new_Delphes_events':0,'persisted_events_joined':6000,'HF_original_events_analysed':3000,'new_ROOT_loops':0}
  i={'evidence_class':'ACTUAL_EXISTING_DATA_READBACK','status':'PASS_INDEPENDENT_RATIONAL_BITSET_EXISTING_DATA','new_ME_calls':0,'new_integrals':0,'new_events':0,'source_events':3000,'covariance_pairs_checked':3825,'Phase10_stage_counts_rates_variances_match':True}
  return a,b,d,i
 def test_complete_fixture_profile(self):self.assertTrue(m.validate_profiles(*self.fixtures()))
 def test_deleted_counter_cannot_silently_pass(self):
  for role in range(4):
   a=list(self.fixtures());del a[role]['new_ME_calls']
   with self.subTest(role=role),self.assertRaises(ValueError):m.validate_profiles(*a)
 def test_nonzero_counter_not_masked(self):
  a=self.fixtures();a[0]['new_ME_calls']=1
  with self.assertRaises(ValueError):m.validate_profiles(*a)
 def test_false_does_not_equal_integer_zero(self):
  a=self.fixtures();a[0]['new_ME_calls']=False
  with self.assertRaises(ValueError):m.validate_profiles(*a)
 def test_synthetic_cannot_impersonate_data(self):
  a=self.fixtures();a[2]['evidence_class']='SYNTHETIC_METHOD_ONLY'
  with self.assertRaises(ValueError):m.validate_profiles(*a)
 def test_partial_covariance_not_full_pass(self):
  a=self.fixtures();a[3]['covariance_pairs_checked']=1
  with self.assertRaises(ValueError):m.validate_profiles(*a)
 def test_generic_status_not_exact_review(self):
  a=self.fixtures();a[3]['status']='PASS'
  with self.assertRaises(ValueError):m.validate_profiles(*a)
 def test_parser_flag_missing_or_true_rejected(self):
  for v in (None,True,0):
   a=self.fixtures();a[1]['generator_parser_executed']=v
   with self.subTest(v=v),self.assertRaises(ValueError):m.validate_profiles(*a)

class CurrentRawSourceIdentity(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
  self.paths={name:self.root/(name+'.txt') for name in ('model','dependency','family','executed','detector','independent')}
  for path in self.paths.values():path.write_bytes(b'known = 1\n')
  def row(name):
   path=self.paths[name];return {'path':str(path),'resolved_path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  self.a={'source_identity':[row('model')],'dependency_identity':[row('dependency')]}
  self.b={'files':{'family':row('family')},'configuration_and_executed_source_sha256':{str(self.paths['executed']):row('executed')['sha256']}}
  self.d={'input_hashes_before':{str(self.paths['detector']):row('detector')['sha256']}}
  self.i={'input_hashes':{str(self.paths['independent']):row('independent')['sha256']}}
 def check(self):return m.current_source_integrity(self.a,self.b,self.d,self.i)
 def test_unchanged_raw_sources_pass(self):
  result=self.check();self.assertEqual(result['status'],'PASS_CURRENT_RAW_SOURCE_IDENTITIES');self.assertEqual(result['checked_records'],6);self.assertEqual(result['mismatches'],[])
 def test_whitespace_only_drift_is_blocked_without_normalization(self):
  original=copy.deepcopy(self.a);self.paths['model'].write_bytes(b'known = 1 \n')
  result=self.check();self.assertEqual(result['status'],'BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT');self.assertIn('RAW_SHA256_MISMATCH',result['mismatches'][0]['reasons']);self.assertEqual(self.a,original)
 def test_missing_regular_source_is_recorded_not_raised(self):
  self.paths['dependency'].unlink();result=self.check();self.assertEqual(result['status'],'BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT');self.assertIn('MISSING_FILE',result['mismatches'][0]['reasons']);self.assertIsNone(result['mismatches'][0]['actual']['sha256'])
 def test_each_receipt_scope_is_rehashed(self):
  for name in self.paths:
   path=self.paths[name];original=path.read_bytes();path.write_bytes(b'changed\n')
   with self.subTest(name=name):self.assertEqual(self.check()['status'],'BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT')
   path.write_bytes(original)
 def test_stale_receipt_hash_blocks_unchanged_current_file(self):
  self.i['input_hashes'][str(self.paths['independent'])]='0'*64
  self.assertEqual(self.check()['mismatches'][0]['origin'],'independent.input_hashes')
 def test_missing_identity_collection_cannot_pass(self):
  del self.a['dependency_identity'];self.assertEqual(self.check()['status'],'BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT')
 def test_broken_symlink_retains_explicit_missing_payload_semantics(self):
  path=self.root/'broken';path.symlink_to('missing-grid.dat')
  self.a['source_identity']=[{'path':str(path),'resolved_path':str(path.resolve()),'status':'BROKEN_SYMLINK','link_target':'missing-grid.dat','sha256':None,'bytes':None}]
  self.assertEqual(self.check()['status'],'PASS_CURRENT_RAW_SOURCE_IDENTITIES')
 def test_previously_broken_symlink_now_resolving_is_drift(self):
  path=self.root/'broken';path.symlink_to('missing-grid.dat')
  self.a['source_identity']=[{'path':str(path),'status':'BROKEN_SYMLINK','link_target':'missing-grid.dat','sha256':None,'bytes':None}]
  (self.root/'missing-grid.dat').write_bytes(b'new payload')
  self.assertIn('EXPECTED_BROKEN_SYMLINK_CHANGED',self.check()['mismatches'][0]['reasons'])
 def test_regular_receipt_does_not_accept_new_broken_symlink(self):
  path=self.paths['model'];path.unlink();path.symlink_to('missing.dat')
  self.assertIn('BROKEN_SYMLINK',self.check()['mismatches'][0]['reasons'])
 def test_symlink_loop_is_recorded_as_read_error(self):
  path=self.paths['model'];path.unlink();path.symlink_to(path.name)
  result=self.check();self.assertIn('READ_ERROR',result['mismatches'][0]['reasons'])
 def test_resolved_path_identity_is_not_just_content_identity(self):
  path=self.paths['model'];same=self.root/'same';same.write_bytes(path.read_bytes());path.unlink();path.symlink_to(same)
  result=self.check();self.assertIn('RESOLVED_PATH_CHANGED',result['mismatches'][0]['reasons'])

if __name__=='__main__':unittest.main()
