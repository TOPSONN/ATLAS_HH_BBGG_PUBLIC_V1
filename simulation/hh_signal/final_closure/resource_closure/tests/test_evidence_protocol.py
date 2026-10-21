"""Ordinary32KiB temp-file fixtures and fault injection; no live kill/OOM/stress."""
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from .. import evidence_slots as e


def identity():
    return dict(source_revision='a'*40,source_sha256='b'*64,
                run_id='12345678-1234-1234-1234-123456789abc',stage='offline_fixture',
                collector_boot_id='cccccccc-1234-1234-1234-123456789abc')


def event(kind='checkpoint',number=1,cause='NORMAL'):
    resources={k:None for k in ('CPU_usec','wall_ns','memory_peak_bytes',
                               'swap_peak_bytes','cgroup_dev','cgroup_inode','MainPID')}
    if kind=='postmortem':resources.update(cgroup_dev=8,cgroup_inode=99,MainPID=123)
    group=dict(unit='atlas-hh-offline.service',invocation_id='e'*32,
        path='/sys/fs/cgroup/offline_fixture',dev=8,inode=99,MainPID=123,
        boot_id=identity()['collector_boot_id']) if kind=='postmortem' else None
    return dict(event_id='12345678-1234-1234-1234-%012x'%number,kind=kind,
        monotonic_ns=number,observer='independent_collector',
        worker_state={'checkpoint':'RUNNING','postmortem':'DEAD_OBSERVED','failure':'UNKNOWN'}[kind],
        cause=cause,resources=resources,cgroup=group,raw_sha256=['c'*64] if kind=='postmortem' else [],
        native_result=None)


class EvidenceProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'evidence'
        self.store=e.FixedSlotStore(self.path,identity(),create=True,offline_fixture_only=True)

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def test_normal_ack_sync_and_reopen_preserves_identity(self):
        ack=self.store.append(event())
        self.assertIn('SYNC_REOPEN',ack['status'])
        self.store.close()
        with e.FixedSlotStore(self.path,identity(),offline_fixture_only=True) as reopened:
            result=reopened.scan()
            self.assertEqual(len(result['records']),1)
            self.assertEqual(result['records'][0]['identity'],identity())
            self.assertEqual(result['status'],'INTEGRITY_VALID_DURABILITY_UNATTESTED')

    def test_source_constructor_is_not_production_writer_authorization(self):
        with self.assertRaisesRegex(e.EvidenceError,'NOT_APPROVED'):
            e.FixedSlotStore(self.path,identity())

    def test_all_slots_reserved_before_worker_admission(self):
        self.assertEqual(len(list(self.path.iterdir())),8)
        self.assertEqual(sum(p.stat().st_size for p in self.path.iterdir()),32768)
        self.assertTrue(all(p.stat().st_nlink==1 for p in self.path.iterdir()))

    def test_checkpoint_capacity_does_not_consume_failure_reserve(self):
        for i in range(1,5):self.store.append(event(number=i))
        before={p.name:p.read_bytes() for p in self.path.iterdir()}
        with self.assertRaisesRegex(e.EvidenceError,'LANE_ENOSPC'):self.store.append(event(number=5))
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.path.iterdir()})
        self.store.append(event('failure',6,'DISK_ENOSPC_MODEL'))
        self.assertEqual(len(self.store.scan()['records']),5)

    def test_sigkill_oom_and_wall_timeout_are_distinct_postmortem_models(self):
        self.store.append(event())
        for cause in ('SIGKILL_MODEL','OOM_MODEL','WALL_TIMEOUT_MODEL'):
            with self.subTest(cause=cause):
                # Each is a separate run/lane fixture; no process is killed.
                target=Path(self.temp.name)/cause
                with e.FixedSlotStore(target,identity(),create=True,offline_fixture_only=True) as s:
                    s.append(event())
                    s.append(event('postmortem',2,cause))
                    self.assertEqual(s.scan()['records'][-1]['event']['cause'],cause)
                    self.assertIsNone(s.scan()['records'][-1]['event']['native_result'])

    def test_partial_write_never_reuses_torn_slot_or_invents_terminal(self):
        real=e.os.pwrite
        def partial(fd,data,offset):
            if offset==0:real(fd,data[:100],0)
            raise OSError(errno.ENOSPC,'injected ENOSPC')
        with patch.object(e.os,'pwrite',side_effect=partial):
            with self.assertRaises(OSError):self.store.append(event())
        damaged=self.store.scan();self.assertEqual(damaged['status'],'UNKNOWN')
        preserved=(self.path/e.NAMES[0]).read_bytes()
        with self.assertRaisesRegex(e.EvidenceError,'DAMAGED_STORE'):
            self.store.append(event(number=2))
        self.store.append(event('failure',3,'PARTIAL_WRITE_MODEL'))
        self.assertEqual((self.path/e.NAMES[0]).read_bytes(),preserved)
        self.assertEqual(self.store.scan()['status'],'UNKNOWN')

    def test_fsync_failure_has_no_ack_and_no_native_reconstruction(self):
        with patch.object(e.os,'fsync',side_effect=OSError(errno.EIO,'sync failed')):
            with self.assertRaises(OSError):self.store.append(event())
        self.assertEqual(self.store.scan()['status'],'UNKNOWN')
        bad=event();bad['native_result']={'integral':123}
        with self.assertRaisesRegex(e.EvidenceError,'RECONSTRUCTION'):self.store.append(bad)

    def test_collector_crash_before_commit_is_unknown_after_reopen(self):
        real=e.os.pwrite
        def crash(fd,data,offset):
            if offset==e.SLOT_BYTES-len(e.COMMIT):raise OSError(errno.EIO,'collector crash model')
            return real(fd,data,offset)
        with patch.object(e.os,'pwrite',side_effect=crash):
            with self.assertRaises(OSError):self.store.append(event())
        self.store.close()
        with e.FixedSlotStore(self.path,identity(),offline_fixture_only=True) as s:
            self.assertEqual(s.scan()['status'],'UNKNOWN')

    def test_event_replay_foreign_run_and_clock_reset_rejected(self):
        self.store.append(event())
        with self.assertRaisesRegex(e.EvidenceError,'REPLAY'):self.store.append(event())
        bad=event(number=2);bad['monotonic_ns']=1
        with self.assertRaisesRegex(e.EvidenceError,'NONMONOTONIC'):self.store.append(bad)
        other=identity();other['run_id']='aaaaaaaa-1234-1234-1234-123456789abc'
        with e.FixedSlotStore(self.path,other,offline_fixture_only=True) as s:
            self.assertEqual(s.scan()['status'],'UNKNOWN')

    def test_tampering_missing_slot_and_link_alias_rejected(self):
        self.store.append(event())
        path=self.path/e.NAMES[0];raw=bytearray(path.read_bytes());raw[200]^=1;path.write_bytes(raw)
        self.assertEqual(self.store.scan()['status'],'UNKNOWN')
        path=self.path/e.NAMES[7];path.unlink()
        with self.assertRaisesRegex(e.EvidenceError,'MISSING'):self.store.scan()

    def test_no_progress_oversize_and_worker_terminal_claim_rejected(self):
        with patch.object(e.os,'pwrite',return_value=0):
            with self.assertRaisesRegex(e.EvidenceError,'NO_PROGRESS'):self.store.append(event())
        bad=event();bad['observer']='worker'
        with self.assertRaisesRegex(e.EvidenceError,'ATTRIBUTION'):self.store.append(bad)
        bad=event('postmortem');bad['raw_sha256']=[]
        with self.assertRaisesRegex(e.EvidenceError,'RAW_BINDING'):self.store.append(bad)

    def rewrite_frame(self,slot,change):
        path=self.path/e.NAMES[slot];raw=path.read_bytes()
        _,length,_=e.HEADER.unpack(raw[:e.HEADER.size])
        record=json.loads(raw[e.HEADER.size:e.HEADER.size+length])
        change(record);payload=e.canonical(record)
        body=e.HEADER.pack(e.MAGIC,len(payload),hashlib.sha256(payload).digest())+payload
        body+=b'\0'*(e.SLOT_BYTES-len(body)-len(e.COMMIT))+e.COMMIT
        path.write_bytes(body)

    def test_resealed_sequence_jump_and_bool_slot_are_unknown(self):
        self.store.append(event())
        for key,value in [('sequence',2),('sequence',100),('slot',False),('slot',0.0)]:
            original=(self.path/e.NAMES[0]).read_bytes()
            self.rewrite_frame(0,lambda r:r.update({key:value}))
            self.assertEqual(self.store.scan()['status'],'UNKNOWN')
            (self.path/e.NAMES[0]).write_bytes(original)

    def test_resealed_clock_reversal_and_worker_resurrection_rejected(self):
        self.store.append(event())
        self.store.append(event('postmortem',2))
        with self.assertRaisesRegex(e.EvidenceError,'RESURRECTION'):
            self.store.append(event(number=3))
        self.rewrite_frame(4,lambda r:r['event'].update(monotonic_ns=1))
        self.assertEqual(self.store.scan()['status'],'UNKNOWN')

    def test_identity_property_cannot_rebind_existing_run(self):
        self.store.append(event())
        altered=self.store.identity;altered['run_id']='aaaaaaaa-1234-1234-1234-123456789abc'
        self.assertEqual(self.store.identity,identity())
        self.assertEqual(len(self.store.scan()['records']),1)

    def test_same_instance_reentrancy_and_foreign_thread_denied_before_write(self):
        before=self.store._raw_slots()
        self.store._append_lock.acquire()
        try:
            with self.assertRaisesRegex(e.EvidenceError,'CONCURRENT'):self.store.append(event())
        finally:self.store._append_lock.release()
        with patch.object(e.threading,'get_ident',return_value=self.store._owner_thread+1):
            with self.assertRaisesRegex(e.EvidenceError,'THREAD_MISMATCH'):self.store.append(event())
        self.assertEqual(before,self.store._raw_slots())

    def test_second_sync_and_directory_sync_failure_never_ack(self):
        for fail_at in (2,3):
            target=Path(self.temp.name)/('sync_%s'%fail_at)
            with e.FixedSlotStore(target,identity(),create=True,offline_fixture_only=True) as s:
                real=e.os.fsync;calls=[]
                def fail(fd):
                    calls.append(fd)
                    if len(calls)==fail_at:raise OSError(errno.EIO,'injected sync failure')
                    return real(fd)
                with patch.object(e.os,'fsync',side_effect=fail):
                    with self.assertRaises(OSError):s.append(event())
                # Bytes may be committed but no durable ACK was delivered.
                self.assertEqual(s.scan()['status'],'INTEGRITY_VALID_DURABILITY_UNATTESTED')
                with self.assertRaisesRegex(e.EvidenceError,'REPLAY'):s.append(event())

    def test_postmortem_zero_pid_and_checkpoint_dead_claim_rejected(self):
        for key in ('MainPID','cgroup_inode'):
            bad=event('postmortem');bad['resources'][key]=0
            with self.assertRaisesRegex(e.EvidenceError,'POSITIVE'):self.store.append(bad)
        bad=event();bad['worker_state']='DEAD_OBSERVED'
        with self.assertRaisesRegex(e.EvidenceError,'RUNNING'):self.store.append(bad)

    def test_foreign_boot_or_cgroup_binding_cannot_create_postmortem(self):
        bad=event('postmortem');bad['cgroup']['boot_id']='dddddddd-1234-1234-1234-123456789abc'
        with self.assertRaisesRegex(e.EvidenceError,'FOREIGN_BOOT'):self.store.append(bad)
        bad=event('postmortem');bad['cgroup']['MainPID']=124
        with self.assertRaisesRegex(e.EvidenceError,'CGROUP_IDENTITY'):self.store.append(bad)

    def test_postmortems_cannot_switch_unit_or_invocation_for_same_worker(self):
        self.store.append(event('postmortem'))
        bad=event('postmortem',2);bad['cgroup']['invocation_id']='f'*32
        with self.assertRaisesRegex(e.EvidenceError,'INSTANCE_REBINDING'):self.store.append(bad)
        self.store.append(event('postmortem',3))
        self.rewrite_frame(5,lambda r:r['event']['cgroup'].update(invocation_id='f'*32))
        self.assertEqual(self.store.scan()['status'],'UNKNOWN')
