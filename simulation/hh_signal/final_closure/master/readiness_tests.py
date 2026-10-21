"""Real pure positive/negative calls; no deployment or kernel queries."""
import copy,json,os,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from . import readiness_validation as v,readiness_runner as r,ledger
from .contract import LIMITS,sha,load,canonical
from ..resource_closure.tests.test_admin_security import device,mount
from ..resource_closure import device_policy

def transaction():
 # Fixed recorded-model identity, no os.makedev emulation or kernel query.
 # Full legacy positive transaction is exercised unchanged in Linux612 CI.
 identity=dict(fd_number=9,st_dev=1,st_ino=100,st_rdev=2064,diskseq=10,size_bytes=4194304,
  host_instance='HOST_NEW',by_id_target='/dev/review-new',boot_id='BOOT_REVIEW',namespace_inode=40,helper_start_ns=5,lease_nonce='LEASE_REVIEW')
 records=[dict(phase=p,identity=copy.deepcopy(identity),monotonic_ns=10+i,fd_held=True,exclusive_claim_held=True,hotplug_exclusion_held=True) for i,p in enumerate(('acquire','before_operation','after_operation','before_release'))]
 return records,{'consumer':'SAME_FD_IN_PROCESS_REVIEWED_HELPER','expected_identity':identity,'all_host_writers_excluded_required':True}

def trace():
 rows=[]
 for i,(phase,state,cpu) in enumerate((('admission','NOT_STARTED',0),('worker','RUNNING',100),('postmortem','DEAD_OBSERVED',200),('collector_finalized','DEAD_OBSERVED',300))):
  rows.append(dict(monotonic_ns=1+i*100000000,CPU_usec=cpu,memory_peak_bytes=1000+i,swap_bytes=0,
   cgroup_dev=10,cgroup_inode=20,InvocationID='a'*32,boot_id='11111111-1111-4111-8111-111111111111',collector_identity='INERT_COLLECTOR',
   phase=phase,worker_state=state,cgroup_empty=i==3,owned_descendants=[] if i==3 else [99],postmortem_raw_sha256='b'*64 if i==3 else None,
   cpu_stat={'usage_usec':cpu,'user_usec':cpu,'system_usec':0},memory_events={'oom':0,'oom_kill':0},
   cgroup_events={'populated':0 if i==3 else 1},final_observer_identity='INERT_EXTERNAL_MANAGER_OBSERVER' if i==3 else None))
 return rows
def fs():
 profile=dict(device_bytes=4194304,block_size=1024,block_count=4096,inode_count=128,inode_size=256,journal_blocks=1024,
  source_instance_sha256='a'*64,expected_uuid='11111111-1111-4111-8111-111111111111',expected_label='INERT_S4',protected_uuids=[])
 data={k:profile[k] for k in ('device_bytes','block_size','block_count','inode_count','inode_size','journal_blocks','source_instance_sha256')}
 data.update(raw_sha256='b'*64,free_blocks=2000,free_inodes=100,filesystem='ext4',internal_journal=True,external_journal=False,
  features=['has_journal'],uuid=profile['expected_uuid'],label=profile['expected_label'])
 return data,profile

def pure_cases():
 cases=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,PermissionError,KeyError,TypeError):cases.append({'case':name,'passed':True,'expected':'REJECT'})
  else:cases.append({'case':name,'passed':False,'expected':'REJECT'})
 v.resource_trace(trace(),LIMITS['S4']);cases.append({'case':'normal_complete_trace','passed':True,'expected':'INPUT_CONSISTENCY_ONLY'})
 for name,change in (
  ('CPU_overrun',lambda x:x[-1].update(CPU_usec=4000001,cpu_stat={'usage_usec':4000001,'user_usec':4000001,'system_usec':0})),
  ('wall_overrun',lambda x:x[-1].update(monotonic_ns=13000000002)),
  ('OOM',lambda x:x[-1].update(cause='OOM')),
  ('timeout',lambda x:x[-1].update(cause='timeout')),
  ('controller_dies',lambda x:x[-1].update(cause='controller_loss')),
  ('collector_crash',lambda x:x[-1].update(cause='collector_crash')),
  ('block_ENOSPC',lambda x:x[-1].update(cause='ENOSPC')),
  ('missing_cpu_counter',lambda x:x[-1].pop('CPU_usec')),
  ('missing_raw_cpu_stat',lambda x:x[-1].pop('cpu_stat')),
  ('raw_OOM',lambda x:x[-1]['memory_events'].update(oom_kill=1)),
  ('collector_self_post_exit_claim',lambda x:x[-1].update(final_observer_identity=x[-1]['collector_identity'])),
  ('raw_cgroup_not_empty',lambda x:x[-1]['cgroup_events'].update(populated=1)),
  ('fake_cpu_stat',lambda x:x[-1]['cpu_stat'].update(user_usec=0)),
  ('missing_peak',lambda x:x[-1].pop('memory_peak_bytes')),
  ('RAM_overrun',lambda x:x[-1].update(memory_peak_bytes=LIMITS['S4']['RAM_bytes']+1)),
  ('swap',lambda x:x[-1].update(swap_bytes=1)),
  ('counter_reset',lambda x:x[-1].update(CPU_usec=1,cpu_stat={'usage_usec':1,'user_usec':1,'system_usec':0})),
  ('wrong_InvocationID',lambda x:x[-1].update(InvocationID='c'*32)),
  ('orphan',lambda x:x[-1].update(owned_descendants=[99])),
  ('missing_cleanup',lambda x:x[-1].pop('cgroup_empty')),
  ('missing_postmortem',lambda x:x[-1].pop('postmortem_raw_sha256')),
  ('cgroup_unload',lambda x:x[-1].pop('cgroup_inode')),
  ('resurrection',lambda x:x[-1].update(worker_state='RUNNING')),
  ('unknown_worker',lambda x:x[-1].update(worker_state='UNKNOWN')),
  ('replay_clock',lambda x:x[-1].update(monotonic_ns=x[-2]['monotonic_ns'])),
  ('collector_impersonation',lambda x:x[-1].update(collector_identity='INERT_OTHER')),
  ('missing_admission',lambda x:x[0].update(phase='main')),
  ('no_final_collector',lambda x:x[-1].update(phase='worker_dead'))):
  x=trace();change(x);reject(name,lambda x=x:v.resource_trace(x,LIMITS['S4']))
 for name,change in (
  ('inode_ENOSPC',lambda x:x.update(free_inodes=7)),('evidence_block_reserve',lambda x:x.update(free_blocks=1)),
  ('journal_removed',lambda x:x.update(internal_journal=False)),('external_journal',lambda x:x.update(external_journal=True)),
  ('capacity_expanded',lambda x:x.update(device_bytes=8388608)),('wrong_inode_count',lambda x:x.update(inode_count=256)),
  ('missing_geometry',lambda x:x.pop('block_size')),('wrong_instance',lambda x:x.update(source_instance_sha256='c'*64))):
  x,p=fs();change(x);reject(name,lambda x=x,p=p:v.geometry(x,p))
 for name,change in (
  ('protected_root_substitution',lambda s,c:c.update(candidate='8:0')),
  ('parent_graph_omission',lambda s,c:s['nodes'][1].update(parent='8:99')),
  ('alias_duplication',lambda s,c:s['nodes'][1].update(by_ids=s['nodes'][0]['by_ids'])),
  ('diskseq_change',lambda s,c:s['nodes'][1].update(diskseq=11)),
  ('host_backing_mismatch',lambda s,c:s['nodes'][1].update(host_id='OTHER')),
  ('thin',lambda s,c:s['nodes'][1].update(thin=True)),
  ('loop',lambda s,c:s['nodes'][1].update(kind='loop'))):
  s,c=device();change(s,c);reject(name,lambda s=s,c=c:device_policy.review_device(s,c))
 for name,change in (
  ('already_mounted',lambda s,c:s.update(findmnt_exact=[{}])),
  ('symlink_traversal',lambda s,c:s['path_before'][-1].update(is_symlink=True)),
  ('nested_mount',lambda s,c:s.update(mountinfo=s['mountinfo']+'2 1 8:16 / /srv/atlas-hh/capacity-v2/x rw - ext4 /dev/INERT rw\n')),
  ('missing_namespace',lambda s,c:s.pop('namespace_after'))):
  s,c=mount();change(s,c);reject(name,lambda s=s,c=c:device_policy.review_mount(s,c))
 for name,change in (
  ('FD_substitution',lambda x,p:x[-1]['identity'].update(fd_number=10)),
  ('helper_restart',lambda x,p:x[-1]['identity'].update(helper_start_ns=9)),
  ('lease_changed',lambda x,p:x[-1]['identity'].update(lease_nonce='OTHER')),
  ('path_reopening_consumer',lambda x,p:p.update(consumer='EXTERNAL_MKFS'))):
  x,p=transaction();change(x,p);reject(name,lambda x=x,p=p:v.review_same_instance(x,p))
 reject('privileged_dispatch_absent',lambda:v.live_operation('format'))
 return cases

class ReadinessPureTests(unittest.TestCase):
 def test_all_exact_negative_cases(self):
  cases=pure_cases();self.assertGreaterEqual(len(cases),49);self.assertTrue(all(x['passed'] for x in cases),[x for x in cases if not x['passed']])
 def test_geometry_is_consistency_not_actual_or_durable(self):
  x,p=fs();a=v.geometry(x,p);self.assertFalse(a['live_readback_authenticated']);self.assertFalse(a['power_loss_verified'])
 def test_fixed_device_geometry_and_uuid(self):
  for field,value in [('uuid','invalid'),('label','WRONG'),('journal_blocks',512),('block_count',4097),('inode_size',False)]:
   x,p=fs();x[field]=value
   with self.assertRaises(ValueError):v.geometry(x,p)
 def test_dumpe2fs_raw_parser_and_independent_geometry(self):
  raw=b'Filesystem volume name: INERT_S4\nFilesystem UUID: 11111111-1111-4111-8111-111111111111\nFilesystem features: has_journal extent\nBlock size: 1024\nBlock count: 4096\nInode count: 128\nInode size: 256\nTotal journal blocks: 1024\nJournal inode: 8\nFree blocks: 2000\nFree inodes: 100\n'
  _,profile=fs();self.assertFalse(v.geometry(v.parse_geometry_header(raw,4194304,'a'*64),profile)['live_readback_authenticated'])
  for bad in (raw+b'Block size: 2048\n',raw.replace(b'Total journal blocks:',b'UNREVIEWED journal spelling:'),raw.replace(b'Free blocks: 2000',b'Free blocks: NaN')):
   with self.assertRaises(ValueError):v.parse_geometry_header(bad,4194304,'a'*64)
 def test_postmount_consistency_and_substitution(self):
  c={'namespace':{'inode':40},'mountpoint':'/srv/atlas-hh/test','major_minor':'8:16','filesystem_uuid':'11111111-1111-4111-8111-111111111111','mount_root_uid':1001}
  x={'namespace_before':c['namespace'],'namespace_after':c['namespace'],'mountinfo':'1 999 8:16 / /srv/atlas-hh/test rw,nosuid,nodev,noexec - ext4 /dev/INERT rw\n',
   'filesystem_uuid':c['filesystem_uuid'],'mount_root_uid':1001,'mount_root_mode':0o700,'worker_raw_device_access':False,'unexpected_writable_sources':[],
   'independent_findmnt':{'target':c['mountpoint'],'major_minor':c['major_minor'],'uuid':c['filesystem_uuid']}}
  self.assertFalse(v.postmount(x,c)['runtime_acceptance'])
  for field,value in [('mount_root_uid',0),('worker_raw_device_access',True),('independent_findmnt',{}),('namespace_after',{'inode':41})]:
   bad=copy.deepcopy(x);bad[field]=value
   with self.assertRaises(ValueError):v.postmount(bad,c)
 def test_resource_numeric_bool_and_no_terminal_claim(self):
  x=trace();x[-1]['CPU_usec']=False
  with self.assertRaises(ValueError):v.resource_trace(x,LIMITS['S4'])
  self.assertFalse(v.resource_trace(trace(),LIMITS['S4'])['runtime_acceptance'])
 def test_parse_counter_duplicate_noninteger(self):
  for text in ('x 1\nx 2','x NaN','x -1','x 1 2'):
   with self.assertRaises(ValueError):v.pairs(text)
 def test_bounded_directory_never_returns_first128_of129(self):
  from .guest_v2 import bounded_names
  with patch('os.scandir') as s:
   s.return_value.__enter__.return_value=iter([type('Entry',(),{'name':str(i)})() for i in range(129)])
   with self.assertRaisesRegex(ValueError,'ENUMERATION_BOUND'):bounded_names('INERT',128)
 def test_legacy_sources_are_not_replaced(self):
  from .contract import REPO
  manifest=load(REPO/'reports/phase7i_g1_association_repair/source_manifest.json');old={x['path']:x['sha256'] for x in manifest['files']}
  for path in ('simulation/hh_signal/final_closure/resource_closure/device_policy.py','simulation/hh_signal/final_closure/resource_closure/instance_binding.py','simulation/hh_signal/final_closure/resource_closure/evidence_slots.py','simulation/hh_signal/final_closure/resource_closure/g1_guest_inventory.py','simulation/hh_signal/final_closure/master/same_instance.py'):
   self.assertEqual(sha((REPO/path).read_bytes()),old[path])
 def test_plan_has_no_live_or_approval_dispatch(self):
  import contextlib,io
  out=io.StringIO()
  with contextlib.redirect_stdout(out):self.assertEqual(r.main(['plan']),0)
  self.assertFalse(json.loads(out.getvalue())['live_dispatcher'])
 def test_invalid_duplicate_json_is_not_readback(self):
  root=Path(__file__).parents[4]/'.local';root.mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as d:
   p=Path(d)/'torn.json'
   for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{"torn":'):
    p.write_bytes(raw)
    with self.assertRaises(ValueError):load(p)
 def test_guest_adapter_is_unexecuted_on_windows(self):
  if sys.platform!='linux':
   from .guest_v2 import acquire
   with self.assertRaisesRegex(ValueError,'LINUX_SESSION'):acquire()
 def test_no_authorization_via_live_argument(self):
  with self.assertRaises(SystemExit):r.main(['format'])

if __name__=='__main__':unittest.main()
