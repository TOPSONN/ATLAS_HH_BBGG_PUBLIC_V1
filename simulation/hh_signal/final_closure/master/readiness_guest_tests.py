import copy,hashlib,unittest
from unittest.mock import patch
from . import readiness_validation as v
from .guest_v2 import CG,Reader
from .contract import sha

def fixture():
 boot='11111111-1111-4111-8111-111111111111\n';cg='0::/one\n'
 a={'label':'before','boot_id':boot,'cgroup':cg,'mount_namespace':{'dev':4,'inode':40},'pid':2,'uid':1000,'gid':1000,'monotonic_ns':10}
 b=copy.deepcopy(a);b.update(label='after',monotonic_ns=20)
 rows=[]
 def row(path,text):
  rows.append({'path':path,'text':text,'status':'REPORTED_UNATTESTED','sha256':sha(text.encode()),
   'uid':1000 if path.startswith('/proc/self/') else 0,'mode':0o444,'dev':4,'inode':len(rows)+1,'bytes':len(text.encode())})
 row('/proc/sys/kernel/random/boot_id',boot);row('/proc/self/cgroup',cg)
 for root in ('/sys/fs/cgroup/one','/sys/fs/cgroup'):
  for field in CG:
   text={'cpu.stat':'usage_usec 5\nuser_usec 3\nsystem_usec 2\n','cpu.max':'100000 100000\n','memory.events':'oom 0\noom_kill 0\n',
    'cgroup.events':'populated 1\nfrozen 0\n','cgroup.controllers':'cpu memory pids\n','cgroup.subtree_control':'cpu memory\n','cgroup.type':'domain\n','cgroup.procs':'2\n'}.get(field,'0\n')
   row(root+'/'+field,text)
 return {'schema':'HH_G1_GUEST_READONLY_V2','source_sha256':'a'*64,'legacy_source_sha256':'b'*64,
  'trust':'REPORTED_UNATTESTED','host_mapping_complete':False,'started_monotonic_ns':1,'ended_monotonic_ns':30,
  'anchor_before':a,'anchor_after':b,'records':rows,'retained_payload_bytes':sum(x['bytes'] for x in rows),
  'cgroup_lineage':['/sys/fs/cgroup/one','/sys/fs/cgroup'],'block_graph':[]}

class GuestReaderTests(unittest.TestCase):
 def test_complete_input_is_unattested_not_actual_manager_or_enforcement(self):
  r=v.guest_review(fixture(),'a'*64,'b'*64,now_monotonic_ns=31)
  self.assertEqual(r['lineage_count'],2);self.assertFalse(r['complete_attestation']);self.assertFalse(r['runtime_enforcement'])
 def test_every_anchor_change_is_rejected(self):
  for name,value in [('boot_id','22222222-2222-4222-8222-222222222222\n'),('cgroup','0::/other\n'),('mount_namespace',{'dev':4,'inode':41}),('uid',0),('pid',3)]:
   x=fixture();x['anchor_after'][name]=value
   with self.assertRaises(ValueError):v.guest_review(x,'a'*64,'b'*64)
 def test_whole_lineage_no_leaf_only_or_missing_root(self):
  for paths in (['/sys/fs/cgroup/one'],['/sys/fs/cgroup'],['/sys/fs/cgroup','/sys/fs/cgroup/one']):
   x=fixture();x['cgroup_lineage']=paths
   with self.assertRaisesRegex(ValueError,'LINEAGE'):v.guest_review(x,'a'*64,'b'*64)
 def test_missing_counter_is_unknown_never_zero(self):
  x=fixture();x['records']=[r for r in x['records'] if not r['path'].endswith('/memory.peak')];x['retained_payload_bytes']=sum(r['bytes'] for r in x['records'])
  r=v.guest_review(x,'a'*64,'b'*64);self.assertIn('memory.peak',r['missing_counter_names'])
 def test_source_legacy_byte_digest_and_ownership(self):
  for field,value in [('sha256','c'*64),('uid',9),('bytes',False)]:
   x=fixture();x['records'][0][field]=value
   with self.assertRaises(ValueError):v.guest_review(x,'a'*64,'b'*64)
  for s,l in [('z'*64,'b'*64),('a'*64,'z'*64)]:
   with self.assertRaises(ValueError):v.guest_review(fixture(),s,l)
 def test_repeated_path_different_content_is_not_merged(self):
  x=fixture();r=copy.deepcopy(x['records'][0]);r.update(text='INERT',sha256=sha(b'INERT'),bytes=5);x['records'].append(r);x['retained_payload_bytes']+=5
  with self.assertRaises(ValueError):v.guest_review(x,'a'*64,'b'*64)
 def test_stale_and_clock_reversed(self):
  with self.assertRaisesRegex(ValueError,'STALE'):v.guest_review(fixture(),'a'*64,'b'*64,now_monotonic_ns=60_000_000_031)
  x=fixture();x['anchor_after']['monotonic_ns']=0
  with self.assertRaises(ValueError):v.guest_review(x,'a'*64,'b'*64)
 def test_truncated_block_relations_reject_whole_graph(self):
  x=fixture();x['block_graph']=[{'relation_complete':False}]
  with self.assertRaisesRegex(ValueError,'BLOCK_RELATIONS'):v.guest_review(x,'a'*64,'b'*64)
 def test_capture_cannot_self_attest_host_mapping(self):
  x=fixture();x['host_mapping_complete']=True
  with self.assertRaises(ValueError):v.guest_review(x,'a'*64,'b'*64)
 def test_reader_missing_file_retains_unknown(self):
  reader=Reader()
  with patch('os.open',side_effect=FileNotFoundError):self.assertIsNone(reader.read('INERT'))
  self.assertEqual(reader.rows[0]['status'],'UNKNOWN');self.assertEqual(reader.used,0)

if __name__=='__main__':unittest.main()
