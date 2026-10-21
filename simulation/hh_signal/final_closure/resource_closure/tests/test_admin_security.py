"""Complete graph/mount rejection fixtures; no real device or namespace reads."""
import copy
import unittest
from .. import device_policy as d
from .. import instance_binding as b


def node(identity='8:16', host='HOST_NEW'):
    return dict(id=identity, diskseq=10, devpath='/dev/review-new', kind='disk',
        parent=None, holders=[], slaves=[], by_ids=['/dev/disk/by-id/REVIEW_NEW'],
        serial='SERIAL_NEW', wwn='WWN_NEW', bytes=4194304, host_id=host,
        host_ancestors=['BUS_NEW'], thin=False, sparse=False, snapshot=False,
        expandable=False, mount_refs=[], raw_uid=0, raw_gid=0, raw_mode=0o600)


def device():
    root=node('8:0','HOST_ROOT')
    root.update(devpath='/dev/review-root',serial='SERIAL_ROOT',wwn='WWN_ROOT',
                by_ids=['/dev/disk/by-id/REVIEW_ROOT'],host_ancestors=['BUS_ROOT'])
    candidate=node()
    snapshot=dict(schema='DEVICE_GRAPH_REVIEW_V1',complete=True,host_mapping_complete=True,
                  all_mount_namespaces_complete=True,nodes=[root,candidate],
                  namespace=dict(dev=4,inode=40,boot_id='BOOT_REVIEW',collector_start_ns=1))
    contract=dict(candidate='8:16',protected_guest_ids=['8:0'],root_guest_id='8:0',
                  protected_inventory_complete=True,protected_host_ids=['HOST_ROOT','BUS_ROOT'],
                  protected_host_inventory_complete=True,
                  disposable_provisioning_receipt_sha256='a'*64,
                  expected={k:candidate[k] for k in ('diskseq','bytes','host_id','serial','wwn')})
    contract['expected']['by_id']=candidate['by_ids'][0]
    return snapshot,contract


def mount():
    ns=dict(dev=4,inode=40,boot_id='BOOT_REVIEW',collector_start_ns=1)
    target='/srv/atlas-hh/capacity-v2'
    parent=dict(id=1,dev='8:0',root='/',path='/',filesystem_type='ext4')
    paths=[]
    for i,p in enumerate(('/','/srv','/srv/atlas-hh',target)):
        paths.append(dict(path=p,uid=0,gid=0,mode=0o700 if p==target else 0o755,
            dev=2048,inode=i+1,is_directory=True,is_symlink=False,empty=True))
    snapshot=dict(schema='MOUNT_TARGET_REVIEW_V1',complete=True,other_jobs_complete=True,
        namespace_before=copy.deepcopy(ns),namespace_after=copy.deepcopy(ns),
        mountinfo='1 999 8:0 / / rw - ext4 /dev/review-root rw\n',
        findmnt_exact=[],findmnt_nested=[],findmnt_covering=copy.deepcopy(parent),
        path_before=copy.deepcopy(paths),path_after=copy.deepcopy(paths),other_job_mounts=[])
    return snapshot,dict(namespace=ns,mountpoint=target,parent_mount=parent)


def transaction():
    identity=dict(fd_number=9,st_dev=1,st_ino=100,st_rdev=2064,diskseq=10,size_bytes=4194304,
        host_instance='HOST_NEW',by_id_target='/dev/review-new',boot_id='BOOT_REVIEW',
        namespace_inode=40,helper_start_ns=5,lease_nonce='RUN_LEASE_REVIEW')
    records=[dict(phase=phase,identity=copy.deepcopy(identity),monotonic_ns=10+i,
        fd_held=True,exclusive_claim_held=True,hotplug_exclusion_held=True)
        for i,phase in enumerate(b.PHASES)]
    plan=dict(schema='PINNED_DEVICE_HELPER_PROPOSAL_V1',
        consumer='SAME_FD_IN_PROCESS_REVIEWED_HELPER',kernel_exclusive_claim_required=True,
        host_hotplug_exclusion_required=True,all_host_writers_excluded_required=True,
        exact_size_bytes=4194304,expected_host_instance='HOST_NEW',
        expected_identity=copy.deepcopy(identity))
    plan['device_snapshot'],plan['device_contract']=device()
    plan['device_policy_sha256']=d.review_device(plan['device_snapshot'],
                                               plan['device_contract'])['snapshot_sha256']
    plan['mount_snapshot'],plan['mount_contract']=mount()
    plan['mount_policy_sha256']=d.review_mount(plan['mount_snapshot'],
                                             plan['mount_contract'])['snapshot_sha256']
    return records,plan


class DevicePolicyTests(unittest.TestCase):
    def rejected(self,s,c,reason):
        with self.assertRaisesRegex(d.PolicyError,reason):d.review_device(s,c)

    def test_consistent_snapshot_is_not_operation_authority(self):
        s,c=device();r=d.review_device(s,c)
        self.assertFalse(r['operation_authorized']);self.assertFalse(r['runtime_verified'])

    def test_sibling_partition_and_same_parent_root_rejected(self):
        s,c=device();s['nodes'][0]['kind']='part';s['nodes'][1]['kind']='part'
        parent=node('8:32','HOST_PARENT')
        parent.update(devpath='/dev/review-parent',by_ids=['/dev/disk/by-id/REVIEW_PARENT'],
                      serial='SERIAL_PARENT',wwn='WWN_PARENT',host_ancestors=['BUS_PARENT'])
        s['nodes'].append(parent)
        for n in s['nodes'][:2]:n['parent']='8:32'
        self.rejected(s,c,'ROOT_OR_PROTECTED_TOPOLOGY')

    def test_candidate_whole_disk_with_root_descendant_rejected(self):
        s,c=device();s['nodes'][0].update(kind='part',parent='8:16')
        self.rejected(s,c,'ROOT_OR_PROTECTED_TOPOLOGY')

    def test_dm_holder_root_bridge_rejected(self):
        s,c=device();s['nodes'][0]['kind']='dm'
        s['nodes'][0]['slaves']=['8:16'];s['nodes'][1]['holders']=['8:0']
        self.rejected(s,c,'ROOT_OR_PROTECTED_TOPOLOGY')

    def test_independent_dm_and_loop_are_unsupported(self):
        for kind in ('dm','loop'):
            s,c=device();s['nodes'][1]['kind']=kind
            self.rejected(s,c,'DM_LOOP')

    def test_host_common_ancestor_rejected_even_separate_guest_disks(self):
        s,c=device();s['nodes'][1]['host_ancestors']=['BUS_ROOT']
        self.rejected(s,c,'HOST_BACKING_INTERSECTION')

    def test_host_serial_wwn_size_diskseq_and_by_id_mismatch(self):
        for key,value in [('host_id','OTHER'),('serial','OTHER'),('wwn','OTHER'),
                          ('bytes',4194305),('diskseq',11),('by_id','/dev/disk/by-id/OTHER')]:
            s,c=device();c['expected'][key]=value
            self.rejected(s,c,'MISMATCH')

    def test_unknown_or_thin_sparse_snapshot_expandable_refused(self):
        for key in ('thin','sparse','snapshot','expandable'):
            for value in (True,None):
                s,c=device();s['nodes'][1][key]=value
                self.rejected(s,c,'BACKING_PROPERTY|UNBOUNDED_BACKING')

    def test_incomplete_host_namespace_or_protected_history_refused(self):
        for key in ('complete','host_mapping_complete','all_mount_namespaces_complete'):
            s,c=device();s[key]=False;self.rejected(s,c,'INCOMPLETE')
        s,c=device();c['protected_guest_ids']=[];self.rejected(s,c,'INCOMPLETE')

    def test_signature_empty_is_not_disposable_provenance(self):
        s,c=device();c.pop('disposable_provisioning_receipt_sha256')
        self.rejected(s,c,'PROVENANCE')

    def test_mount_references_and_worker_raw_access_rejected(self):
        s,c=device();s['nodes'][1]['mount_refs']=['other_namespace:99']
        self.rejected(s,c,'REFERENCED_BY_MOUNT')
        s,c=device();s['nodes'][1]['raw_mode']=0o660
        self.rejected(s,c,'ACCESS_POLICY')

    def test_duplicate_aliases_cannot_claim_two_device_instances(self):
        for field in ('devpath','by_ids'):
            s,c=device();s['nodes'][0][field]=copy.deepcopy(s['nodes'][1][field])
            self.rejected(s,c,'ALIAS')

    def test_parent_cycles_missing_edges_and_nonreciprocal_holders(self):
        s,c=device();s['nodes'][0]['parent']='8:16';s['nodes'][1]['parent']='8:0'
        self.rejected(s,c,'CYCLE')
        s,c=device();s['nodes'][1]['parent']='8:99';self.rejected(s,c,'DANGLING')
        s,c=device();s['nodes'][1]['holders']=['8:0'];self.rejected(s,c,'RECIPROCAL')

    def test_boolean_expected_size_is_not_integer_identity(self):
        s,c=device();s['nodes'][1]['bytes']=1;c['expected']['bytes']=True
        self.rejected(s,c,'MISMATCH')

    def test_complete_partition_without_parent_is_not_complete_graph(self):
        s,c=device();s['nodes'][0]['kind']='part'
        self.rejected(s,c,'PARTITION_PARENT')


class MountTargetTests(unittest.TestCase):
    def reject(self,s,c,reason):
        with self.assertRaisesRegex(d.PolicyError,reason):d.review_mount(s,c)

    def test_empty_unmounted_target_policy_only(self):
        s,c=mount();r=d.review_mount(s,c)
        self.assertFalse(r['privileged_mount_authorized']);self.assertFalse(r['path_race_closed'])

    def test_empty_already_mounted_target_is_refused(self):
        s,c=mount();s['mountinfo']+='2 1 8:16 / '+c['mountpoint']+' rw - ext4 /dev/new rw\n'
        self.reject(s,c,'EXISTING_LEAF')

    def test_nested_mount_and_bind_mount_are_refused(self):
        for suffix,root in [('/nested','/'),('','/bind-subtree')]:
            s,c=mount();s['mountinfo']+='2 1 8:16 '+root+' '+c['mountpoint']+suffix+' rw - ext4 /dev/new rw\n'
            self.reject(s,c,'EXISTING_LEAF')

    def test_bind_ancestor_refused(self):
        s,c=mount();s['mountinfo']+='2 1 8:16 /subtree /srv rw - ext4 /dev/new rw\n'
        self.reject(s,c,'BIND_ANCESTOR')

    def test_namespace_before_after_and_bool_alias_must_match_exactly(self):
        s,c=mount();s['namespace_after']['inode']=41;self.reject(s,c,'NAMESPACE')
        s,c=mount();c['namespace']['dev']=1
        for name in ('namespace_before','namespace_after'):s[name]['dev']=True
        self.reject(s,c,'NAMESPACE')

    def test_findmnt_disagrees_or_has_unknown_result(self):
        for key in ('findmnt_exact','findmnt_nested','findmnt_covering'):
            s,c=mount();s[key]=None;self.reject(s,c,'FINDMNT')

    def test_symlink_traversal_owner_mode_and_nonempty_refused(self):
        for key,value in [('is_symlink',True),('uid',1000),('gid',1000),
                          ('mode',0o777),('empty',False)]:
            s,c=mount();s['path_before'][-1][key]=value;s['path_after']=copy.deepcopy(s['path_before'])
            self.reject(s,c,'METADATA|OWNERSHIP|LEAF')
        s,c=mount();c['mountpoint']+='/../elsewhere';self.reject(s,c,'NONCANONICAL')

    def test_changed_path_inode_and_other_job_lease_refused(self):
        s,c=mount();s['path_after'][-1]['inode']+=1;self.reject(s,c,'PATH_CHANGED')
        s,c=mount();s['other_job_mounts']=[dict(path='/srv/atlas-hh',job='another')]
        self.reject(s,c,'OTHER_JOB_PATH')

    def test_parent_filesystem_rebinding_refused(self):
        s,c=mount();c['parent_mount']['dev']='8:99';self.reject(s,c,'PARENT_FILESYSTEM')

    def test_path_device_must_match_covering_mount_and_after_types(self):
        s,c=mount();s['path_before'][-1]['dev']=999
        s['path_after']=copy.deepcopy(s['path_before'])
        self.reject(s,c,'PATH_DEVICE')
        s,c=mount();s['path_after'][-1]['uid']=False
        self.reject(s,c,'PATH_CHANGED')

    def test_incomplete_or_oversize_raw_mount_capture_refused(self):
        s,c=mount();s['complete']=False;self.reject(s,c,'INCOMPLETE')
        s,c=mount();s['mountinfo']='x'*16385;self.reject(s,c,'MOUNTINFO_REJECTED')


class InstanceBindingTests(unittest.TestCase):
    def reject(self,r,p,reason):
        with self.assertRaisesRegex(d.PolicyError,reason):b.review_transaction(r,p)

    def test_model_pass_never_means_toctou_runtime_closed(self):
        r,p=transaction();out=b.review_transaction(r,p)
        self.assertFalse(out['TOCTOU_RUNTIME_CLOSED']);self.assertFalse(out['operation_authorized'])
        with self.assertRaises(PermissionError):b.privileged_operation('format')

    def test_legacy_path_reopening_consumer_categorically_denied(self):
        r,p=transaction();p['consumer']='MKFS_REOPENS_DEV_PATH'
        self.reject(r,p,'PATH_REOPENING')

    def test_same_major_minor_but_new_diskseq_host_inode_or_nonce_rejected(self):
        for key,value in [('diskseq',11),('host_instance','OTHER'),('st_ino',101),
                          ('lease_nonce','NEW_LEASE'),('namespace_inode',41)]:
            r,p=transaction();r[1]['identity'][key]=value
            self.reject(r,p,'INSTANCE|PLAN|REVIEWED_IDENTITY')

    def test_consistent_wrong_device_or_namespace_not_plan_bound(self):
        for key,value in [('diskseq',99),('st_rdev',999),('by_id_target','/dev/other'),
                          ('namespace_inode',999),('helper_start_ns',999)]:
            r,p=transaction()
            for row in r:row['identity'][key]=value
            self.reject(r,p,'REVIEWED_IDENTITY')

    def test_boolean_plan_size_rejected(self):
        r,p=transaction();p['exact_size_bytes']=True
        for row in r:row['identity']['size_bytes']=1
        self.reject(r,p,'PLAN_SIZE')

    def test_fd_release_exclusivity_or_hotplug_gap_denied(self):
        for key in ('fd_held','exclusive_claim_held','hotplug_exclusion_held'):
            r,p=transaction();r[2][key]=False;self.reject(r,p,'LEASE_GAP')

    def test_missing_postoperation_replay_and_phase_shuffle_refused(self):
        r,p=transaction();r.pop();self.reject(r,p,'SHAPE')
        r,p=transaction();r[2]['monotonic_ns']=r[1]['monotonic_ns'];self.reject(r,p,'REPLAY')
        r,p=transaction();r[1],r[2]=r[2],r[1];self.reject(r,p,'ORDER')

    def test_missing_required_host_writer_exclusion_refused(self):
        r,p=transaction();p['all_host_writers_excluded_required']=False
        self.reject(r,p,'EXCLUSIVITY')

    def test_helper_cannot_start_after_acquisition_or_rebind_policy_digest(self):
        r,p=transaction()
        for row in r:row['identity']['helper_start_ns']=100
        p['expected_identity']['helper_start_ns']=100
        self.reject(r,p,'HELPER_START')
        r,p=transaction();p['device_policy_sha256']='f'*64
        self.reject(r,p,'POLICY_BINDING')

    def test_root_candidate_mount_and_namespace_cannot_contradict_device_graph(self):
        r,p=transaction();s=p['mount_snapshot'];c=p['mount_contract']
        s['mountinfo']=s['mountinfo'].replace('8:0','8:16')
        c['parent_mount']['dev']='8:16';s['findmnt_covering']['dev']='8:16'
        for key in ('path_before','path_after'):
            for row in s[key]:row['dev']=2064
        p['mount_policy_sha256']=d.review_mount(s,c)['snapshot_sha256']
        self.reject(r,p,'ROOT_MOUNT_CONTRADICTION')
        r,p=transaction();p['mount_snapshot']['mountinfo']+='2 1 8:16 / /elsewhere rw - ext4 /dev/review-new rw\n'
        p['mount_policy_sha256']=d.review_mount(p['mount_snapshot'],p['mount_contract'])['snapshot_sha256']
        self.reject(r,p,'MOUNT_REFERENCE_CONTRADICTION')
        r,p=transaction();p['device_snapshot']['namespace']['inode']=41
        p['device_policy_sha256']=d.review_device(p['device_snapshot'],p['device_contract'])['snapshot_sha256']
        self.reject(r,p,'NAMESPACE_CONTRADICTION')
