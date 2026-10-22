"""Pure fixtures only: strict limits, counters, duplicates and contradictions."""
import copy,hashlib,json,unittest
from . import readiness_validation as v
from .readiness_guest_tests import fixture
from .guest_counter_review import review_bytes

def changed(x,field,text,level=0):
 path=x['cgroup_lineage'][level]+'/'+field
 row=next(r for r in x['records'] if r['path']==path)
 row.update(text=text,bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest())
 x['retained_payload_bytes']=sum(r.get('bytes',0) for r in x['records'])
 return x

def review(x):return v.guest_review(x,'a'*64,'b'*64)

class GuestCounterTests(unittest.TestCase):
 def test_max_only_explicit_limit_fields(self):
  for field in ('memory.max','memory.swap.max','pids.max'):
   with self.subTest(field=field):
    r=review(changed(fixture(),field,'max\n'))
    self.assertEqual(r['limit_observations'][0]['limits'][field],'UNLIMITED')
    self.assertIn({'lineage_index':0,'field':field,'meaning':'UNLIMITED'},r['unlimited_limits'])
    self.assertFalse(r['swap_disabled_verified']);self.assertFalse(r['runtime_enforcement'])
 def test_cpu_quota_max_but_period_must_be_numeric(self):
  r=review(changed(fixture(),'cpu.max','max 100000\n'))
  self.assertEqual(r['limit_observations'][0]['limits']['cpu.max']['quota_usec'],'UNLIMITED')
  for text in ('max max','1000 max','0 100000','1 0','1','1 2 3'):
   with self.subTest(text=text),self.assertRaises(ValueError):review(changed(fixture(),'cpu.max',text))
 def test_numeric_limits_preserve_zero_and_positive(self):
  for field in ('memory.max','memory.swap.max','pids.max'):
   for n in (0,1,536870912,2**64-1):
    with self.subTest(field=field,n=n):
     r=review(changed(fixture(),field,str(n)))
     self.assertEqual(r['limit_observations'][0]['limits'][field],n)
     self.assertEqual(r['unlimited_limits'],[])
 def test_max_rejected_in_all_usage_and_peak_fields(self):
  for field in ('memory.current','memory.peak','memory.swap.current'):
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'COUNTER_SYNTAX'):review(changed(fixture(),field,'max'))
 def test_invalid_numeric_tokens_in_limits_and_usage(self):
  for field in ('memory.max','memory.swap.max','pids.max','memory.current','memory.peak','memory.swap.current'):
   for token in ('MAX','unlimited','-1','+1','01','1.0','1e3','NaN','', '1 2','１２','0x10'):
    with self.subTest(field=field,token=token),self.assertRaises(ValueError):review(changed(fixture(),field,token))
 def test_full_u64_counter_boundary_and_oversize_rejection(self):
  for field in ('memory.current','memory.peak','memory.swap.current'):
   review(changed(fixture(),field,str(2**64-1)))
  for token in (str(2**64),'9'*21):
   for field in ('memory.max','memory.swap.max','memory.current','memory.peak','memory.swap.current','pids.max'):
    with self.subTest(field=field,token=token),self.assertRaises(ValueError):review(changed(fixture(),field,token))
 def test_stat_and_event_values_are_numeric_including_unknown_keys(self):
  for field,valid in (('cpu.stat','usage_usec 5\nuser_usec 3\nsystem_usec 2\n'),('memory.events','oom 0\noom_kill 0\n'),('cgroup.events','populated 1\nfrozen 0\n')):
   for token in ('max','-1','garbage',str(2**64)):
    with self.subTest(field=field,token=token),self.assertRaises(ValueError):review(changed(fixture(),field,valid+'future_counter '+token+'\n'))
 def test_flat_duplicate_and_malformed_fields_are_rejected(self):
  for field in ('cpu.stat','memory.events','cgroup.events'):
   for text in ('same 0\nsame 0\n','same 0\nsame 1\n','same','same 0 extra'):
    with self.subTest(field=field,text=text),self.assertRaises(ValueError):review(changed(fixture(),field,text))
 def test_duplicate_record_equal_conflicting_or_unknown_rejected(self):
  for status,text in (('REPORTED_UNATTESTED','0\n'),('REPORTED_UNATTESTED','max'),('UNKNOWN',None)):
   x=fixture();row=copy.deepcopy(next(r for r in x['records'] if r['path'].endswith('/memory.swap.max')))
   row['status']=status
   if text is not None:row.update(text=text,bytes=len(text),sha256=hashlib.sha256(text.encode()).hexdigest())
   x['records'].append(row);x['retained_payload_bytes']+=row['bytes'] if status=='REPORTED_UNATTESTED' else 0
   with self.subTest(status=status,text=text),self.assertRaisesRegex(ValueError,'DUPLICATE_RECORD'):review(x)
 def test_repeated_anchors_allow_exactly_the_two_collector_reads(self):
  x=fixture();row=copy.deepcopy(x['records'][0]);x['records'].append(row);x['retained_payload_bytes']+=row['bytes'];review(x)
  x['records'].append(row);x['retained_payload_bytes']+=row['bytes']
  with self.assertRaisesRegex(ValueError,'DUPLICATE_RECORD'):review(x)
 def test_missing_limit_or_usage_is_unknown_not_zero_or_unlimited(self):
  for field in ('memory.swap.max','memory.swap.current','memory.peak'):
   x=fixture();x['records']=[r for r in x['records'] if not r['path'].endswith('/'+field)]
   x['retained_payload_bytes']=sum(r['bytes'] for r in x['records']);r=review(x)
   self.assertIn(field,r['missing_counter_names']);self.assertEqual(r['counter_coverage'],'INCOMPLETE_OBSERVED')
   self.assertNotIn(field,r['limit_observations'][0]['limits']);self.assertEqual(r['unlimited_limits'],[])
 def test_missing_event_key_remains_explicit(self):
  r=review(changed(fixture(),'memory.events','oom 0\n'))
  self.assertIn('memory.events:oom_kill',r['missing_counter_names'])
 def test_binary_event_contradictions_are_rejected(self):
  for text in ('populated 2\nfrozen 0','populated 0\nfrozen 2'):
   with self.subTest(text=text),self.assertRaisesRegex(ValueError,'CGROUP_EVENT_CONTRADICTION'):review(changed(fixture(),'cgroup.events',text))
 def test_nonatomic_usage_can_exceed_limit_or_earlier_peak(self):
  x=changed(fixture(),'memory.current','100');changed(x,'memory.peak','50');changed(x,'memory.swap.current','100')
  r=review(x);self.assertFalse(r['runtime_enforcement']);self.assertFalse(r['swap_disabled_verified'])
 def test_unknown_max_field_is_rejected(self):
  for field in ('memory.current','memory.peak','memory.swap.current','memory.high','made_up.max'):
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'UNREVIEWED_LIMIT_FIELD'):v.cgroup_limit(field,'max')
 def test_every_lineage_is_parsed_not_only_leaf(self):
  r=review(changed(fixture(),'memory.swap.max','max',level=1))
  self.assertEqual(r['unlimited_limits'],[{'lineage_index':1,'field':'memory.swap.max','meaning':'UNLIMITED'}])
 def test_duplicate_json_keys_at_any_depth_rejected(self):
  for raw in (b'{"x":0,"x":0}',b'{"x":{"y":0,"y":1}}'):
   with self.subTest(raw=raw),self.assertRaisesRegex(ValueError,'DUPLICATE_JSON_FIELD'):review_bytes(raw,hashlib.sha256(raw).hexdigest(),'a'*64,'b'*64)
 def test_offline_input_bound_digest_and_collector_binding(self):
  raw=json.dumps(fixture()).encode();digest=hashlib.sha256(raw).hexdigest()
  self.assertEqual(review_bytes(raw,digest,'a'*64,'b'*64)['review']['status'],'PASS_READ_ONLY_OBSERVED')
  for b,h,s in ((raw,'0'*64,'a'*64),(raw,digest,'c'*64),(b' '*262145,hashlib.sha256(b' '*262145).hexdigest(),'a'*64)):
   with self.assertRaises(ValueError):review_bytes(b,h,s,'b'*64)
 def test_geometry_decimal_contract_unchanged(self):
  with self.assertRaisesRegex(ValueError,'COUNTER_SYNTAX'):v.decimal(str(2**64-1))
 def test_non_string_values_do_not_coerce_into_counters(self):
  for token in (None,0,True,1.0,[],{}):
   with self.subTest(token=token),self.assertRaisesRegex(ValueError,'COUNTER_SYNTAX'):v.cgroup_number(token)
 def test_root_absence_does_not_hide_nonroot_missing(self):
  x=fixture();x['records']=[r for r in x['records'] if r['path']!='/sys/fs/cgroup/memory.max']
  x['retained_payload_bytes']=sum(r['bytes'] for r in x['records']);r=review(x)
  self.assertEqual(r['nonroot_missing_counter_names'],[])
  self.assertEqual(r['missing_by_lineage'],[{'lineage_index':1,'root_cgroup':True,'fields':['memory.max']}])
  x['records']=[r for r in x['records'] if r['path']!='/sys/fs/cgroup/one/memory.swap.current']
  x['retained_payload_bytes']=sum(r['bytes'] for r in x['records']);r=review(x)
  self.assertEqual(r['nonroot_missing_counter_names'],['memory.swap.current'])

if __name__=='__main__':unittest.main()
