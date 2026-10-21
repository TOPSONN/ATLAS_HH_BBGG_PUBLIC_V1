import contextlib,copy,datetime,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from .. import g1_acquisition as g

def fixture():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 rows=[{'key':key,'interface':'INERT_SOURCE_FIXTURE','time':now,'status':'UNKNOWN','error_code':'ACCESS_DENIED'} for key in sorted(g.HOST_KEYS)]
 return {'schema':'PHASE7I_G1_HOST_CAPTURE_V1','capture_id':'11111111-1111-4111-8111-111111111111',
 'collector_sha256':'a'*64,'administrator':False,'distro_launches':0,'privileged_actions':0,
 'trust':'REPORTED_UNATTESTED','host_guest_mapping_complete':False,'protected_storage_complete':False,
 'started_utc':now,'ended_utc':now,'observations':rows}

class G1AcquisitionTests(unittest.TestCase):
 def test_real_missing_state_is_unknown_not_stopped(self):
  p=g.public_projection(fixture());self.assertEqual(p['running_distro_state'],'UNKNOWN')
  self.assertIsNone(p['running_distro_count']);self.assertFalse(p['execution_authorized'])
 def test_three_existing_policies_reject_incomplete_capture(self):
  rows=g.existing_policy_decisions(fixture())
  self.assertEqual([x['policy'] for x in rows],['device','mount','transaction'])
  self.assertTrue(all(x['status']=='REJECTED_INCOMPLETE_REAL_ACQUISITION' for x in rows))
 def test_duplicate_top_level_and_nested_json_rejected(self):
  for raw in (b'{"x":1,"x":2}',b'{"a":{"k":1,"k":2}}'):
   with self.assertRaisesRegex(ValueError,'DUPLICATE'):g.load(raw)
 def test_nonfinite_json_and_oversized_capture_rejected(self):
  for raw in (b'{"a":NaN}',b'{"a":Infinity}',b' '* (g.MAX_BYTES+1)):
   with self.assertRaises(ValueError):g.load(raw)
 def test_each_scope_boolean_cannot_authorize_collection(self):
  for key,value in [('administrator',True),('distro_launches',1),('privileged_actions',1),('distro_launches',False)]:
   v=fixture();v[key]=value
   with self.assertRaisesRegex(ValueError,'UNAUTHORIZED_SCOPE'):g.validate_host(v)
 def test_self_attestation_and_completeness_are_rejected(self):
  for key,value in [('trust','OBSERVED_TRUSTED_SOURCE'),('host_guest_mapping_complete',True),('protected_storage_complete',True)]:
   v=fixture();v[key]=value
   with self.assertRaisesRegex(ValueError,'SELF_ATTESTATION'):g.validate_host(v)
 def test_missing_and_duplicated_observation_is_rejected(self):
  for op in (lambda x:x.pop(),lambda x:x.__setitem__(0,copy.deepcopy(x[1]))):
   v=fixture();op(v['observations'])
   with self.assertRaises(ValueError):g.validate_host(v)
 def test_negative_exit_cannot_report_running_success(self):
  v=fixture();r=next(x for x in v['observations'] if x['key']=='running_distros')
  r.update(status='REPORTED_UNATTESTED',error_code=None,data=[{'exit_code':2,'stdout':'','stderr':'INERT'}])
  with self.assertRaisesRegex(ValueError,'NONZERO_NATIVE'):g.validate_host(v)
 def test_running_none_and_positive_list_remain_unattested(self):
  for text,count,expected in [('',0,'NONE_RUNNING_REPORTED_UNATTESTED'),('INERT\n',1,'RUNNING_REPORTED_UNATTESTED')]:
   v=fixture();r=next(x for x in v['observations'] if x['key']=='running_distros')
   r.update(status='REPORTED_UNATTESTED',error_code=None,data=[{'exit_code':0,'stdout':text,'stderr':''}])
   p=g.public_projection(v);self.assertEqual(p['running_distro_count'],count)
   self.assertEqual(p['running_distro_state'],expected);self.assertFalse(p['execution_authorized'])
 def test_raw_serial_paths_and_error_text_never_echo_to_public(self):
  v=fixture();r=v['observations'][0]
  secret='INERT_PRIVATE_SERIAL_PATH_AND_CREDENTIAL_SENTINEL'
  r['data']=[{'SerialNumber':secret,'Path':secret,'stdout':secret}];r['error_message']=secret
  self.assertNotIn(secret,json.dumps(g.public_projection(v)))
 def test_unknown_error_code_cannot_inject_private_text(self):
  v=fixture();v['observations'][0]['error_code']='INERT_PRIVATE_TEXT'
  with self.assertRaisesRegex(ValueError,'ERROR_CODE'):g.public_projection(v)
 def test_rows_and_data_bytes_are_bounded(self):
  for data in ([None]*129,[{'x':'z'*65537}]):
   v=fixture();v['observations'][0]['data']=data
   with self.assertRaises(ValueError):g.public_projection(v)
 def test_bad_clock_uuid_and_hash_rejected(self):
  for key,value in [('ended_utc','2000-01-01T00:00:00+00:00'),('capture_id','INERT'),('collector_sha256','z'*64)]:
   v=fixture();v[key]=value
   with self.assertRaises(ValueError):g.public_projection(v)
 def test_schema_and_missing_data_rejected(self):
  v=fixture();v['schema']='INERT'
  with self.assertRaises(ValueError):g.validate_host(v)
  v=fixture();v['observations'][0]['status']='REPORTED_UNATTESTED'
  with self.assertRaises(ValueError):g.validate_host(v)
 def test_native_boolean_exit_cannot_alias_zero(self):
  v=fixture();r=next(x for x in v['observations'] if x['key']=='running_distros')
  r['data']=[{'exit_code':False,'stdout':''}]
  with self.assertRaisesRegex(ValueError,'NATIVE_EXIT'):g.validate_host(v)
 def test_failed_observation_cannot_claim_success_or_none_running(self):
  v=fixture();r=next(x for x in v['observations'] if x['key']=='running_distros')
  r.update(status='REPORTED_UNATTESTED',data=[{'exit_code':0,'stdout':''}])
  with self.assertRaisesRegex(ValueError,'CANNOT_CONTAIN_ERROR'):g.public_projection(v)
 def test_clock_error_does_not_echo_private_value(self):
  v=fixture();v['started_utc']='INERT_PRIVATE_CLOCK_SENTINEL'
  with self.assertRaisesRegex(ValueError,'^INVALID_CAPTURE_TIME$'):g.public_projection(v)
 def test_cli_rejects_private_invalid_capture_without_traceback_or_output(self):
  root=Path(__file__).resolve().parents[5]/'.local';root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as d:
   capture=Path(d)/'capture.json';out=Path(d)/'out.json';v=fixture()
   v['started_utc']='INERT_PRIVATE_CLOCK_SENTINEL';capture.write_text(json.dumps(v),encoding='utf-8')
   output=io.StringIO()
   with patch.object(sys,'argv',['g1','--capture',str(capture),'--output',str(out)]),contextlib.redirect_stdout(output):
    self.assertEqual(g.main(),2)
   self.assertNotIn('SENTINEL',output.getvalue());self.assertNotIn('Traceback',output.getvalue())
   self.assertFalse(out.exists())
 def test_cli_preserves_existing_output_and_never_accepts_wrong_collector(self):
  root=Path(__file__).resolve().parents[5]/'.local';root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as d:
   capture=Path(d)/'capture.json';out=Path(d)/'out.json';v=fixture()
   out.write_text('INERT_EXISTING_EVIDENCE',encoding='utf-8')
   v['collector_sha256']=hashlib.sha256(Path(g.__file__).with_name('g1_windows_inventory.ps1').read_bytes()).hexdigest()
   capture.write_text(json.dumps(v),encoding='utf-8')
   with patch.object(sys,'argv',['g1','--capture',str(capture),'--output',str(out)]),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(g.main(),2)
   self.assertEqual(out.read_text(encoding='utf-8'),'INERT_EXISTING_EVIDENCE')
   v['collector_sha256']='0'*64;capture.write_text(json.dumps(v),encoding='utf-8')
   with patch.object(sys,'argv',['g1','--capture',str(capture),'--output',str(Path(d)/'new.json')]),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(g.main(),2)
   self.assertFalse((Path(d)/'new.json').exists())

if __name__=='__main__':unittest.main()
