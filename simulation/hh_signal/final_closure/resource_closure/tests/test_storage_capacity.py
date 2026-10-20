"""Pure synthetic storage receipt tests; no OS or quota operation."""
import copy
import errno
import hashlib
import json
import unittest
from simulation.hh_signal.final_closure.resource_closure import storage_capacity as c

def raw(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def fixture():
    headers={name:hashlib.sha256(name.encode()).hexdigest() for name in c.HEADERS}
    ids=dict(zip(c.QTYPE,(1000,1000,0)))
    rows=[]
    for kind in c.QTYPE:
        for op,code in c.OPS.items():
            error=errno.EPERM if (kind,op)==('PRJQUOTA','Q_GETQUOTA') else errno.ESRCH
            rows.append({'API':'quotactl_fd','operation':op,'qtype':kind,'id':ids[kind],
                         'QCMD_hex':hex((code<<8)|c.QTYPE.index(kind)),'return':-1,
                         'errno':error,'errno_name':errno.errorcode[error],
                         'result_interpretation':'NO_BUFFER_FIELDS_INTERPRETED_ON_FAILURE'})
    doc={'schema':'READ_ONLY_QUOTACTL_FD_GET_V1','timestamp_UTC':'2026-10-20T10:07:08Z',
         'kernel_release':'6.6.87.2-microsoft-standard-WSL2','architecture':'x86_64',
         'syscall_number':443,**headers,'O_PATH_filesystem_major_minor':'8:48',
         'opened_path':'/INERT_SOURCE','project_id_source':'INERT_FIXTURE_ONLY',
         'rows':rows,'GET_calls':9,'SET_ON_OFF_SYNC_calls':0,
         'actual_service_mount_or_resource_tests':0,'retained_physical_events':0}
    args={'expected_device':'8:48','expected_kernel':doc['kernel_release'],
          'expected_headers':headers,'expected_ids':ids}
    return doc,args

def project(doc,args=None):
    if args is None:_,args=fixture()
    data=raw(doc)
    return c.quota_projection(data,expected_sha256=hashlib.sha256(data).hexdigest(),**args)

def geometry(profile):
    p=c.PROFILES[profile]
    hashes={key:hashlib.sha256(key.encode()).hexdigest() for key in
            ('device_geometry','filesystem_superblock','inode_readback','writer_restrictions')}
    journal=1024 if profile=='S4' else 8192
    doc={'schema':'PHASE7I_DEDICATED_GEOMETRY_CLAIM_V1',
         'source_kind':'ADMIN_PROVISIONED_FIXED_BLOCK_DEVICE','device':'/dev/INERT_FIXED_ONLY',
         'device_bytes':p['device_bytes'],'block_bytes':p['block_bytes'],
         'filesystem_blocks':p['device_bytes']//p['block_bytes'],
         'total_inodes':p['inodes'],'inode_bytes':256,'journal_blocks':journal,
         'overhead_blocks_including_journal':journal+p['inodes']*256//p['block_bytes']+32,
         'external_journal':False,'thin_or_sparse':False,'readback_sha256':hashes}
    return doc,{'profile':profile,'expected_device':doc['device'],'expected_readbacks':hashes}

def review_geometry(doc,args):
    data=raw(doc)
    return c.geometry_prerequisites(data,expected_sha256=hashlib.sha256(data).hexdigest(),**args)

class StorageCapacityTests(unittest.TestCase):
    def test_inactive_accounting_is_observed_separately_from_permission(self):
        doc,args=fixture();result=project(doc,args)
        self.assertTrue(all(s['accounting']=='NO_ACTIVE_ACCOUNTING_OBSERVED' for s in result['states'].values()))
        self.assertEqual(result['states']['PRJQUOTA']['individual_limits'],'UNKNOWN_PERMISSION')
        self.assertEqual(result['nonwrite_class_GETFMT_GETINFO_calls'],6)
        self.assertEqual(result['potential_write_class_GETQUOTA_calls'],3)
        self.assertTrue(result['GETQUOTA_all_failed'])
        self.assertEqual(result['GETQUOTA_success_count'],0)
        self.assertFalse(result['persistent_allocated_capacity_verified'])
        self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_successful_accounting_is_never_actual_capacity_acceptance(self):
        doc,args=fixture()
        for row in doc['rows']:
            if row['operation'] in ('Q_GETFMT','Q_GETINFO'):
                row.pop('result_interpretation')
                row.update({'return':0,'errno':0,'errno_name':None,
                    'result':{'format':2} if row['operation']=='Q_GETFMT' else
                    {'dqi_bgrace':0,'dqi_igrace':0,'dqi_flags':0,'dqi_valid':7}})
        result=project(doc,args)
        self.assertTrue(all(x['accounting']=='ACTIVE_ACCOUNTING_OBSERVED_LIMITS_NOT_VALIDATED' for x in result['states'].values()))
        self.assertFalse(result['formal_build_authorized'])

    def test_permission_and_unsupported_or_mixed_state_remain_unknown(self):
        for error,wanted in ((errno.EPERM,'UNKNOWN_PERMISSION'),(errno.ENOSYS,'UNKNOWN_MIXED_OR_UNSUPPORTED_READBACK')):
            doc,args=fixture();row=doc['rows'][0]
            row.update(errno=error,errno_name=errno.errorcode[error])
            self.assertEqual(project(doc,args)['states']['USRQUOTA']['accounting'],wanted)

    def test_duplicate_missing_extra_and_failed_zero_buffers_rejected(self):
        changes=[lambda d:d['rows'].__setitem__(1,copy.deepcopy(d['rows'][0])),
                 lambda d:d['rows'].pop(),
                 lambda d:d.__setitem__('extra',1),
                 lambda d:d['rows'][0].__setitem__('result',{'format':0})]
        for change in changes:
            doc,args=fixture();change(doc)
            with self.subTest(change=changes.index(change)),self.assertRaises(ValueError):project(doc,args)

    def test_source_device_header_id_and_blob_bindings(self):
        changes=[lambda d:d.__setitem__('O_PATH_filesystem_major_minor','8:49'),
                 lambda d:d.__setitem__('kernel_release','OTHER'),
                 lambda d:d.__setitem__(c.HEADERS[0],'0'*64),
                 lambda d:d['rows'][0].__setitem__('id',0),
                 lambda d:d.__setitem__('architecture','aarch64')]
        for change in changes:
            doc,args=fixture();change(doc)
            with self.subTest(change=changes.index(change)),self.assertRaises(ValueError):project(doc,args)
        doc,args=fixture()
        with self.assertRaisesRegex(ValueError,'SHA256'):
            c.quota_projection(raw(doc),expected_sha256='0'*64,**args)

    def test_only_exact_GET_commands_and_zero_mutation_counts(self):
        changes=[lambda d:d['rows'][0].__setitem__('operation','Q_SETQUOTA'),
                 lambda d:d['rows'][0].__setitem__('API','OTHER'),
                 lambda d:d['rows'][0].__setitem__('QCMD_hex','0x80000800'),
                 lambda d:d.__setitem__('SET_ON_OFF_SYNC_calls',1)]
        for change in changes:
            doc,args=fixture();change(doc)
            with self.subTest(change=changes.index(change)),self.assertRaises(ValueError):project(doc,args)

    def test_bool_float_bad_return_and_unhashable_values_rejected(self):
        changes=[lambda d:d.__setitem__('GET_calls',True),
                 lambda d:d['rows'][0].__setitem__('errno',True),
                 lambda d:d['rows'][0].__setitem__('return',False),
                 lambda d:d['rows'][0].__setitem__('operation',[]),
                 lambda d:d['rows'][0].__setitem__('errno',float('nan'))]
        for change in changes:
            doc,args=fixture();change(doc)
            with self.subTest(change=changes.index(change)),self.assertRaises(ValueError):project(doc,args)

    def test_duplicate_json_nonfinite_depth_and_size_rejected(self):
        for data in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":1e999}',
                     b'{"a":'+b'['*30+b'0'+b']'*30+b'}',b'x'*32769):
            with self.subTest(length=len(data)),self.assertRaises(ValueError):
                c.decode(data,hashlib.sha256(data).hexdigest())

    def test_both_geometry_profiles_fit_but_never_verify_actual_capacity(self):
        for profile,wanted,reserve in [('S4',13631488,3145728),
                                       ('FUTURE_BUILD_PROPOSAL_ONLY',4563402752,805306368)]:
            doc,args=geometry(profile);result=review_geometry(doc,args)
            self.assertEqual(result['known_geometry_and_tmpfs_bytes'],wanted)
            self.assertEqual(result['unproven_controlplane_outer_reserve_bytes'],reserve)
            self.assertFalse(result['actual_capacity_verified'])
            self.assertFalse(result['persistent_inode_capacity_verified'])
            self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_geometry_bool_mismatch_zero_inodes_and_unsafe_device_rejected(self):
        changes=[lambda d:d.__setitem__('device_bytes',True),
                 lambda d:d.__setitem__('device_bytes',4194305),
                 lambda d:d.__setitem__('filesystem_blocks',4097),
                 lambda d:d.__setitem__('total_inodes',0),
                 lambda d:d.__setitem__('block_bytes',4096)]
        for change in changes:
            doc,args=geometry('S4');change(doc)
            with self.subTest(change=changes.index(change)),self.assertRaises(ValueError):
                review_geometry(doc,args)
        doc,args=geometry('S4');doc['device']=args['expected_device']='/dev/../root'
        with self.assertRaises(ValueError):review_geometry(doc,args)

    def test_geometry_thin_external_and_substituted_readback_rejected(self):
        for field,value in [('thin_or_sparse',True),('external_journal',True),
                            ('thin_or_sparse',0)]:
            doc,args=geometry('S4');doc[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):review_geometry(doc,args)
        doc,args=geometry('S4')
        doc['readback_sha256']=dict(doc['readback_sha256'],device_geometry='0'*64)
        with self.assertRaises(ValueError):review_geometry(doc,args)

    def test_journal_inode_overhead_and_cap_expansion_rejected(self):
        changes=[lambda d:d.__setitem__('journal_blocks',0),
                 lambda d:d.__setitem__('overhead_blocks_including_journal',1024),
                 lambda d:d.__setitem__('overhead_blocks_including_journal',4096),
                 lambda d:d.__setitem__('total_inodes',129)]
        for change in changes:
            doc,args=geometry('S4');change(doc)
            with self.subTest(change=changes.index(change)),self.assertRaises(ValueError):review_geometry(doc,args)

if __name__ == '__main__':
    unittest.main()
