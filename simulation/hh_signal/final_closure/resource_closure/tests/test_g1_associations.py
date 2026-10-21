import contextlib,copy,hashlib,io,json,os,shutil,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from .test_g1_acquisition import fixture
from .. import g1_acquisition as g,g1_associations as a

def endpoint(cls,id):return {'class':cls,'namespace':'root/cimv2','server':'LOCAL_CHECKED','device_id':id}
def v2():
 v=fixture();v['schema']='PHASE7I_G1_HOST_CAPTURE_V2';rows={r['key']:r for r in v['observations']}
 def reported(key,data):rows[key].update(status='REPORTED_UNATTESTED',error_code=None,data=data)
 reported('disk_drives',[{'DeviceID':'DISK0','Index':0}]);reported('partitions',[{'DeviceID':'PART0','DiskIndex':0}])
 reported('logical_disks',[{'DeviceID':'V:','DriveType':3}])
 reported(a.KEYS[0],[{'association_class':'Win32_DiskDriveToDiskPartition','antecedent':endpoint('Win32_DiskDrive','DISK0'),'dependent':endpoint('Win32_DiskPartition','PART0')}])
 reported(a.KEYS[1],[{'association_class':'Win32_LogicalDiskToPartition','antecedent':endpoint('Win32_DiskPartition','PART0'),'dependent':endpoint('Win32_LogicalDisk','V:'),'starting_address':'0','ending_address':'18446744073709551615'}])
 for key in a.KEYS:rows[key].update(association_encoding=a.CONTRACT,provider_enumeration_complete=True,enumerated_edge_count=1)
 return v,rows

class AssociationTests(unittest.TestCase):
 def test_compact_graph_preserves_extents_without_trust_upgrade(self):
  v,rows=v2();g.validate_host(v);p=g.public_projection(v)
  self.assertEqual(p['association_validation'],'V2_COMPACT_CONTRACT')
  self.assertNotIn('DISK0',json.dumps(p));self.assertFalse(p['execution_authorized']);self.assertFalse(p['host_guest_mapping_complete'])
 def test_v1_history_remains_readable_but_not_compact_validated(self):
  self.assertEqual(g.public_projection(fixture())['association_validation'],'LEGACY_V1_NOT_COMPACT_VALIDATED')
 def test_each_missing_endpoint_field_rejected(self):
  for key in ('class','namespace','server','device_id'):
   v,r=v2();r[a.KEYS[0]]['data'][0]['antecedent'].pop(key)
   with self.assertRaises(ValueError):g.validate_host(v)
 def test_wrong_class_namespace_remote_empty_unicode_and_control_rejected(self):
  for field,value in [('class','Win32_LogicalDisk'),('namespace','root/other'),('server','REMOTE'),('device_id',''),('device_id','x\n'),('device_id','\u03b1'),('device_id','x'*1025)]:
   v,r=v2();r[a.KEYS[0]]['data'][0]['antecedent'][field]=value
   with self.assertRaises(ValueError):g.validate_host(v)
 def test_unknown_nested_instance_and_extra_property_rejected(self):
  for change in ('nested','extra','wrong_association'):
   v,r=v2();e=r[a.KEYS[0]]['data'][0]
   if change=='nested':e['antecedent']={'CimInstanceProperties':[]}
   elif change=='extra':e['serial']='INERT'
   else:e['association_class']='Win32_LogicalDiskToPartition'
   with self.assertRaises(ValueError):g.validate_host(v)
 def test_duplicate_and_conflicting_duplicate_rejected(self):
  for conflict in (False,True):
   v,r=v2();row=r[a.KEYS[1]];e=copy.deepcopy(row['data'][0])
   if conflict:e['ending_address']='1'
   row['data'].append(e);row['enumerated_edge_count']=2
   with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_CONFLICT'):g.validate_host(v)
 def test_missing_entire_edge_and_dangling_endpoint_rejected(self):
  for key in a.KEYS:
   v,r=v2();r[key]['data']=[];r[key]['enumerated_edge_count']=0
   with self.assertRaisesRegex(ValueError,'COVERAGE_INCOMPLETE'):g.validate_host(v)
  v,r=v2();r[a.KEYS[0]]['data'][0]['dependent']['device_id']='MISSING'
  with self.assertRaisesRegex(ValueError,'DANGLING'):g.validate_host(v)
 def test_disk_index_boolean_mismatch_and_multiple_parents_rejected(self):
  for value in (1,False,None,-1,2**32):
   v,r=v2();r['partitions']['data'][0]['DiskIndex']=value
   with self.assertRaisesRegex(ValueError,'DISK_PARENT'):g.validate_host(v)
  v,r=v2();r['disk_drives']['data'].append({'DeviceID':'DISK1','Index':0});row=r[a.KEYS[0]]
  e=copy.deepcopy(row['data'][0]);e['antecedent']['device_id']='DISK1';row['data'].append(e);row['enumerated_edge_count']=2
  with self.assertRaisesRegex(ValueError,'DISK_PARENT'):g.validate_host(v)
 def test_duplicate_inventory_case_alias_rejected(self):
  v,r=v2();r['disk_drives']['data'].append({'DeviceID':'disk0','Index':1})
  with self.assertRaisesRegex(ValueError,'INVENTORY_DUPLICATE'):g.validate_host(v)
 def test_extents_lossy_numeric_missing_overflow_reversed_rejected(self):
  for field,value in [('starting_address',False),('ending_address',2**64),('ending_address',str(2**64)),('ending_address','-1'),('starting_address','01'),('ending_address',None)]:
   v,r=v2();r[a.KEYS[1]]['data'][0][field]=value
   with self.assertRaises(ValueError):g.validate_host(v)
  v,r=v2();r[a.KEYS[1]]['data'][0].update(starting_address='2',ending_address='1')
  with self.assertRaisesRegex(ValueError,'EXTENT_ORDER'):g.validate_host(v)
 def test_unknown_prerequisite_cannot_report_edges(self):
  for key in ('disk_drives','partitions','logical_disks',a.KEYS[0]):
   v,r=v2();r[key].update(status='UNKNOWN',error_code='ASSOCIATION_INVALID');r[key].pop('data')
   r[key].pop('provider_enumeration_complete',None)
   with self.assertRaisesRegex(ValueError,'PREREQUISITE'):g.validate_host(v)
 def test_failed_query_cannot_keep_partial_edges(self):
  for key in a.KEYS:
   v,r=v2();r[key].update(status='UNKNOWN',error_code='ASSOCIATION_INVALID')
   with self.assertRaisesRegex(ValueError,'FAILED_PARTIAL'):g.validate_host(v)
 def test_enumeration_flag_count_and_contract_fail_closed(self):
  for field,value in [('provider_enumeration_complete',False),('enumerated_edge_count',False),('enumerated_edge_count',2),('association_encoding','OLD')]:
   v,r=v2();r[a.KEYS[0]][field]=value
   with self.assertRaises(ValueError):g.validate_host(v)
 def test_case_aliases_match_but_not_duplicate(self):
  v,r=v2();r[a.KEYS[0]]['data'][0]['antecedent']['device_id']='disk0';g.validate_host(v)
 def test_many_to_many_volume_relationships_preserved(self):
  v,r=v2();r['partitions']['data'].append({'DeviceID':'PART1','DiskIndex':0})
  e=copy.deepcopy(r[a.KEYS[0]]['data'][0]);e['dependent']['device_id']='PART1';r[a.KEYS[0]]['data'].append(e);r[a.KEYS[0]]['enumerated_edge_count']=2
  e=copy.deepcopy(r[a.KEYS[1]]['data'][0]);e['antecedent']['device_id']='PART1';r[a.KEYS[1]]['data'].append(e);r[a.KEYS[1]]['enumerated_edge_count']=2
  g.validate_host(v);self.assertEqual(len(r[a.KEYS[1]]['data']),2)
 def test_row_byte_and_aggregate_original_limits(self):
  for data in ([{}]*129,[{'x':'x'*65537}]):
   v,r=v2();r[a.KEYS[0]]['data']=data
   with self.assertRaises(ValueError):g.validate_host(v)
  v,r=v2()
  for key in ('features','runtime','os_memory','hypervisor'):r[key]['data']=[{'x':'x'*50000}]
  with self.assertRaisesRegex(ValueError,'AGGREGATE'):g.validate_host(v)
 def test_all_unknown_is_valid_unattested_not_complete(self):
  v=fixture();v['schema']='PHASE7I_G1_HOST_CAPTURE_V2';g.validate_host(v)
  self.assertFalse(g.public_projection(v)['FULL_LAUNCH_ENVELOPE_VERIFIED'])
 def test_source_has_exact13_queries_and_no_silent_serialization_warning(self):
  text=Path(g.__file__).with_name('g1_windows_inventory.ps1').read_text(encoding='utf-8')
  import re
  self.assertEqual(set(re.findall(r"^Add-Observation '([^']+)'",text,re.M)),g.HOST_KEYS)
  for line in text.splitlines():
   if 'ConvertTo-Json -InputObject' in line:self.assertIn('-WarningAction Stop',line)
  self.assertIn('if($Items.Count -gt 128)',text);self.assertIn('if($count -gt 65536)',text)
  self.assertIn('RemainingPayloadBytes=196608',text);self.assertIn('bytes.Length -gt 262144',text)
 def test_new_schema_banned_by_new_publication_gate(self):
  from .. import g1_association_publication as p
  self.assertEqual(p.validate(p.REPORTS+'validation.json',b'{"status":"PENDING"}')['bytes'],20)
  for raw in (json.dumps(v2()[0]),json.dumps({'embedded':json.dumps(v2()[0])})):
   with self.assertRaises(ValueError):p.validate(p.REPORTS+'validation.json',raw.encode())
 def test_publication_rejects_figures_private_paths_bad_modes_and_topology(self):
  from .. import g1_association_publication as p
  for name,raw,mode in [(p.REPORTS+'figure.png',b'PNG','100644'),(p.REPORTS+'validation.json',b'{"device_id":"INERT"}','100644'),
   (p.REPORTS+'private/raw.json',b'{}','100644'),(p.REPORTS+'validation.json',b'{}','100755'),(p.REPORTS+'validation.json',b'%PDF-1.0','100644')]:
   with self.assertRaises(ValueError):p.validate(name,raw,mode)
 def test_cli_v2_fresh_output_and_legacy_cannot_rebind_current_source(self):
  root=Path(__file__).resolve().parents[5]/'.local';root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as d:
   capture=Path(d)/'fixture.json';out=Path(d)/'projection.json';v,r=v2()
   v['collector_sha256']=hashlib.sha256(Path(g.__file__).with_name('g1_windows_inventory.ps1').read_bytes()).hexdigest()
   capture.write_text(json.dumps(v),encoding='utf-8')
   with patch.object(sys,'argv',['g1','--capture',str(capture),'--output',str(out)]),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(g.main(),0)
   projected=json.loads(out.read_bytes());self.assertEqual(projected['raw_capture_sha256'],hashlib.sha256(capture.read_bytes()).hexdigest());self.assertFalse(projected['execution_authorized'])
   v['schema']='PHASE7I_G1_HOST_CAPTURE_V1';capture.write_text(json.dumps(v),encoding='utf-8')
   with patch.object(sys,'argv',['g1','--capture',str(capture),'--output',str(Path(d)/'legacy.json')]),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(g.main(),2)
   self.assertFalse((Path(d)/'legacy.json').exists())
 def test_fixed_workflow_exception_rejects_nonrouting_changes(self):
  from ...master import history
  repo=Path(__file__).resolve().parents[5];raw=(repo/history.CAMPAIGN).read_bytes()
  history.reviewed_workflow_delta(history.CAMPAIGN,raw,history.FROZEN)
  for changed in (raw.replace(b'actions/checkout@v4',b'actions/checkout@v5'),raw+history.REPAIR_SUFFIX.encode(),raw.replace(history.SUFFIX.encode(),b'')):
   with self.assertRaises(ValueError):history.reviewed_workflow_delta(history.CAMPAIGN,changed,history.FROZEN)
 @unittest.skipUnless(os.name=='nt' and shutil.which('pwsh'),'Windows in-memory CIM fixture only')
 def test_actual_powershell_synthetic_cim_and_independent_python_reader(self):
  root=Path(__file__).resolve().parents[5]/'.local';root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as d:
   out=Path(d)/'receipt.json';script=Path(__file__).with_name('g1_association_offline.ps1')
   done=subprocess.run(['pwsh','-NoLogo','-NoProfile','-File',str(script),'-Output',str(out)],capture_output=True,timeout=45)
   self.assertEqual(done.returncode,0,done.stderr.decode(errors='replace'));result=json.loads(out.read_bytes())
   self.assertEqual(result['new_host_queries'],0);self.assertGreaterEqual(len(result['cases']),23)
   v,r=v2();r[a.KEYS[0]]['data']=result['synthetic_edges'];r[a.KEYS[1]]['data']=result['synthetic_volume_edges'];g.validate_host(v)

if __name__=='__main__':unittest.main()
