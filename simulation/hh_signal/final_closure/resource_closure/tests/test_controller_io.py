"""Pure/in-memory controller I/O regressions: no subprocess or kernel probe."""
import base64
import copy
import hashlib
import tempfile
from pathlib import Path
import json
import subprocess
from types import SimpleNamespace
import unittest
from unittest import mock
from simulation.hh_signal.final_closure.resource_closure import controller_io as io
from simulation.hh_signal.final_closure.resource_closure import full_controller as controller
from simulation.hh_signal.final_closure.resource_closure.tests import test_full_controller as baseline


class Selector:
    def __init__(self): self.items = {}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def register(self, fd, events, data): self.items[fd] = SimpleNamespace(fd=fd,data=data)
    def unregister(self, fd): self.items.pop(fd)
    def get_map(self): return self.items
    def select(self, timeout): return [(key, 1) for key in list(self.items.values())]


def collect(stdout=b'', stderr=b'', *, read_override=None, clock=lambda: 0):
    proc = SimpleNamespace(stdout=SimpleNamespace(fileno=lambda: 10,close=mock.Mock()),
                           stderr=SimpleNamespace(fileno=lambda: 11,close=mock.Mock()), wait=mock.Mock())
    data = {10: stdout, 11: stderr}
    requests = []
    def read(fd, count):
        requests.append((fd,count))
        raw, data[fd] = data[fd][:count], data[fd][count:]
        return raw
    result = io.collect_child(proc, 1, selector_factory=Selector, clock=clock,
                             read=read_override or read, set_blocking=lambda *args: None)
    return result, proc, requests


class ControllerIOTests(unittest.TestCase):
    def test_stream_collects_exact_caps_in_bounded_chunks(self):
        result, proc, calls = collect(b'x'*65536, b'e'*8192)
        self.assertEqual(tuple(map(len,result)), (65536,8192))
        self.assertTrue(all(1 <= count <= 4096 for _,count in calls))
        proc.wait.assert_called_once_with(timeout=1)

    def test_stream_rejects_one_byte_over_each_cap_during_read(self):
        for out,err in ((b'x'*65537,b''),(b'',b'e'*8193)):
            with self.subTest(out=len(out),err=len(err)), self.assertRaisesRegex(ValueError,'OUTPUT_BOUND'):
                collect(out,err)

    def test_invalid_or_oversized_stream_reads_rejected(self):
        for value in (None,True,'text',b'x'*4097):
            with self.subTest(value=type(value).__name__),self.assertRaisesRegex(ValueError,'CHILD_READ_BOUND'):
                collect(read_override=lambda *args: value)

    def test_deadline_is_checked_when_pipe_never_finishes(self):
        ticks=iter((0,0,.5,1.1))
        with self.assertRaises(subprocess.TimeoutExpired):
            collect(read_override=lambda *args: b'x',clock=lambda: next(ticks))

    def test_eagain_does_not_discard_data_or_remove_stream(self):
        calls=[]
        def read(fd,n):
            calls.append(fd)
            if calls.count(fd)==1: raise BlockingIOError()
            return b''
        result,_,_=collect(read_override=read)
        self.assertEqual(result,(b'',b''))
        self.assertEqual(calls,[10,11,10,11])

    def test_eof_does_not_grant_more_time_for_process_exit(self):
        ticks=iter((0,0,1.1))
        with self.assertRaises(subprocess.TimeoutExpired): collect(clock=lambda:next(ticks))

    def test_child_protocol_rejects_duplicates_nonfinite_nonobjects_and_blanks(self):
        for raw in (b'{"kind":"A","kind":"B"}\n',b'{"x":NaN}\n',
                    b'{"x":Infinity}\n',b'[]\n',b'{}\n\n',b''):
            with self.subTest(raw=raw),self.assertRaises(ValueError): io.decode_records(raw)
        self.assertEqual(io.decode_records(b'{"kind":"INERT"}\n'),[{'kind':'INERT'}])

    def test_child_protocol_bounds_records_and_nested_values(self):
        self.assertEqual(len(io.decode_records(b'{}\n'*24)),24)
        with self.assertRaisesRegex(ValueError,'RECORD_BOUND'): io.decode_records(b'{}\n'*25)
        value={}; at=value
        for _ in range(34): at['nested']={};at=at['nested']
        with self.assertRaisesRegex(ValueError,'DEPTH_BOUND'):
            io.decode_records(json.dumps(value).encode())

    def test_private_and_nested_frames_never_reach_parent_public_stream(self):
        raw={'kind':'CHILD_DIAGNOSTIC_RECORD','record':{'kind':'PRIVATE_MOUNTINFO_RAW','base64':'SECRET'}}
        c=io.EvidenceBuffer();out=[]
        c.emit(raw,write=lambda fd,b:(out.append(b),len(b))[1])
        shown=b''.join(out)
        self.assertNotIn(b'SECRET',shown)
        self.assertNotIn(b'PRIVATE_MOUNTINFO_RAW',shown)
        self.assertIn(b'BOUNDED_VOLATILE_RAM_ONLY',shown)
        self.assertIn(b'SECRET',b''.join(c.private_records))
        self.assertFalse(c.summary()['controller_loss_receipt_retention_verified'])

    def test_internal_child_pipe_can_transfer_private_evidence_only_under_same_cap(self):
        c=io.EvidenceBuffer(private_pipe=True);out=[]
        c.emit({'kind':'PRIVATE_CHILD_STDERR','base64':'INERT'},write=lambda fd,b:(out.append(b),len(b))[1])
        self.assertIn(b'PRIVATE_CHILD_STDERR',b''.join(out))
        self.assertEqual(c.private_bytes,0)

    def test_aggregate_output_bound_preserves_room_for_terminal_failure(self):
        c=io.EvidenceBuffer();write=lambda fd,b:len(b)
        with self.assertRaisesRegex(ValueError,'RUN_OUTPUT_BOUND'):
            while True:c.emit({'kind':'INERT','text':'x'*2000},write=write)
        c.emit({'kind':'BLOCKED','reason':'RUN_OUTPUT_BOUND'},write=write)
        self.assertLessEqual(c.public_bytes,io.PUBLIC_CAP)

    def test_private_capacity_exhaustion_is_explicitly_incomplete(self):
        c=io.EvidenceBuffer();write=lambda fd,b:len(b)
        with self.assertRaisesRegex(ValueError,'PRIVATE_VOLATILE_EVIDENCE_INCOMPLETE'):
            while True:c.emit({'kind':'PRIVATE_CHILD_STDERR','base64':'x'*20000},write=write)
        self.assertFalse(c.summary()['private_capture_complete'])
        self.assertLessEqual(c.private_bytes,io.PRIVATE_CAP)

    def test_no_progress_oversized_or_boolean_write_fails_without_resetting_budget(self):
        for count in (0,-1,True,999999):
            with self.subTest(count=count):
                c=io.EvidenceBuffer()
                with self.assertRaisesRegex(ValueError,'SHORT_RECEIPT_WRITE'):
                    c.emit({'kind':'INERT'},write=lambda fd,b:count)
                self.assertGreater(c.public_bytes,0)

    def test_short_writes_preserve_exact_record(self):
        out=[];c=io.EvidenceBuffer()
        def write(fd,b):out.append(b[:1]);return 1
        c.emit({'kind':'INERT'},write=write)
        self.assertEqual(b''.join(out),b'{"kind":"INERT"}\n')

    def test_failed_child_cannot_embed_forged_full_claim_in_rejected_terminal(self):
        fixture=baseline.FullControllerMockWorkflow().workflow_fixture
        with fixture(child_returncode=2,child_terminal_fields={'FULL_LAUNCH_ENVELOPE_VERIFIED':True}) as f:
            self.assertEqual(controller.main(['workflow']),2)
            records=[x.args[0] for x in f.emit.call_args_list]
        self.assertEqual(records[-1]['kind'],'BLOCKED')
        self.assertIn('FULL_CLAIM_FORBIDDEN',records[-1]['reason'])
        self.assertFalse(any(x['kind']=='CHILD_TERMINAL_REJECTED' for x in records))


    def test_serialized_private_frames_and_raw_mount_strings_are_masked(self):
        private = {'kind': 'PRIVATE_MOUNTINFO_RAW', 'base64': 'SYNTHETIC_SECRET'}
        values = [json.dumps(private),
                  chr(96)*3 + 'json {"ki\\u006ed":"PRIVATE_MOUNTINFO_R\\u0041W","base64":"SYNTHETIC_SECRET"} ' + chr(96)*3,
                  json.dumps({'raw_mountinfo': 'SYNTHETIC_SECRET'}),
                  '31 1 0:1 / /SYNTHETIC_SECRET rw - ext4 /dev/synthetic rw\n']
        for value in values:
            with self.subTest(value=value):
                c=io.EvidenceBuffer();out=[]
                c.emit({'kind':'NAMESPACE_READBACK','proof':{'text':value}},
                       write=lambda fd,b:(out.append(b),len(b))[1])
                self.assertNotIn(b'SYNTHETIC_SECRET',b''.join(out))
                self.assertGreater(c.private_bytes,0)

    def test_unicode_and_control_failure_uses_reserved_sanitized_terminal(self):
        for reason in ('中'*1024,'\x00'*1024):
            with self.subTest(reason=repr(reason[:1])):
                c=io.EvidenceBuffer();out=[]
                original={'kind':'BLOCKED','reason':reason,'FULL_LAUNCH_ENVELOPE_VERIFIED':False}
                c.emit(original,write=lambda fd,b:(out.append(b),len(b))[1])
                record=json.loads(b''.join(out))
                self.assertEqual(record['kind'],'BLOCKED')
                self.assertIs(record['FULL_LAUNCH_ENVELOPE_VERIFIED'],False)
                self.assertLessEqual(len(b''.join(out)),io.FAILURE_RESERVE)
                self.assertTrue(record['original_record_retained_in_volatile_ram'])
                self.assertIn(io.canonical(original)+b'\n',c.private_records)

    def test_private_failure_preserves_blocked_shape_and_full_false(self):
        c=io.EvidenceBuffer();out=[]
        c.emit({'kind':'BLOCKED','nested':{'kind':'PRIVATE_CHILD_STDERR',
                                          'base64':'SYNTHETIC_SECRET'}},
               write=lambda fd,b:(out.append(b),len(b))[1])
        record=json.loads(b''.join(out))
        self.assertEqual(record['kind'],'BLOCKED')
        self.assertIs(record['FULL_LAUNCH_ENVELOPE_VERIFIED'],False)
        self.assertNotIn(b'SYNTHETIC_SECRET',b''.join(out))

    def test_failure_reserve_survives_full_private_ram_without_false_completeness(self):
        c=io.EvidenceBuffer();write=lambda fd,b:len(b)
        prefix={'kind':'PRIVATE_CHILD_STDERR','base64':''}
        size=io.RECORD_CAP-len(io.canonical(prefix)+b'\n')
        for _ in range(4):
            c.emit({'kind':'PRIVATE_CHILD_STDERR','base64':'x'*size},write=write)
        self.assertEqual(c.private_bytes,io.PRIVATE_CAP)
        out=[]
        c.emit({'kind':'BLOCKED','reason':'中'*1024},
               write=lambda fd,b:(out.append(b),len(b))[1])
        record=json.loads(b''.join(out))
        self.assertEqual(record['kind'],'BLOCKED')
        self.assertFalse(record['original_record_retained_in_volatile_ram'])
        self.assertFalse(record['private_capture_complete'])
        self.assertFalse(c.summary()['private_capture_complete'])

    def test_child_decoder_rejects_overflow_float_incomplete_lf_and_record_size(self):
        for raw in (b'{"kind":"INERT","x":1e9999}\n',
                    b'{"kind":"INERT"}',
                    b'{"kind":"INERT","text":"' + b'x'*io.RECORD_CAP + b'"}\n'):
            with self.subTest(raw_prefix=raw[:40]),self.assertRaises(ValueError):
                io.decode_records(raw)

    def test_collect_child_closes_both_pipes_on_success(self):
        result,proc,_=collect()
        self.assertEqual(result,(b'',b''))
        proc.stdout.close.assert_called_once_with()
        proc.stderr.close.assert_called_once_with()
        self.assertEqual(proc.controller_pipe_cleanup_status,'CLOSED')

    def test_pipe_close_failure_does_not_replace_original_timeout(self):
        proc=SimpleNamespace(stdout=SimpleNamespace(fileno=lambda:10,close=mock.Mock(side_effect=OSError('SYNTHETIC_CLOSE'))),
                             stderr=SimpleNamespace(fileno=lambda:11,close=mock.Mock()),wait=mock.Mock())
        ticks=iter((0,2))
        with self.assertRaises(subprocess.TimeoutExpired) as caught:
            io.collect_child(proc,1,selector_factory=Selector,clock=lambda:next(ticks),
                             read=lambda *args:b'',set_blocking=lambda *args:None)
        self.assertEqual(caught.exception.controller_pipe_cleanup_status,'UNKNOWN')
        self.assertEqual(proc.controller_pipe_cleanup_status,'UNKNOWN')
        proc.stderr.close.assert_called_once_with()
        proc.wait.assert_not_called()

    def test_pipe_close_failure_after_normal_eof_rejects_success(self):
        proc=SimpleNamespace(stdout=SimpleNamespace(fileno=lambda:10,close=mock.Mock(side_effect=OSError('SYNTHETIC_CLOSE'))),
                             stderr=SimpleNamespace(fileno=lambda:11,close=mock.Mock()),wait=mock.Mock())
        with self.assertRaisesRegex(ValueError,'CHILD_PIPE_CLOSE_FAILED') as caught:
            io.collect_child(proc,1,selector_factory=Selector,clock=lambda:0,
                             read=lambda *args:b'',set_blocking=lambda *args:None)
        self.assertEqual(caught.exception.controller_pipe_cleanup_status,'UNKNOWN')
        proc.stderr.close.assert_called_once_with()

class ControllerFinalizationTests(unittest.TestCase):
    def test_child_action_cannot_enable_unverified_raw_output(self):
        with mock.patch.object(controller, 'child', side_effect=ValueError('INERT_BOUNDARY_FAILURE')), \
             mock.patch.object(controller.controller_io, 'reset') as reset, \
             mock.patch.object(controller, 'emit'):
            self.assertEqual(controller.main(['inert-child']),2)
        reset.assert_called_once_with(private_pipe=False)

    def test_group_kill_failure_does_not_replace_original_child_timeout(self):
        failure=subprocess.TimeoutExpired('FIXED_CHILD',1)
        fixture=baseline.FullControllerMockWorkflow().workflow_fixture
        with fixture(child_error=failure) as f:
            f.killed.side_effect=PermissionError('INERT_GROUP_KILL_DENIED')
            self.assertEqual(controller.main(['workflow']),2)
            record=f.emit.call_args.args[0]
            f.proc.wait.assert_called_once_with(timeout=.2)
        self.assertIn('timed out',record['reason'])
        self.assertEqual(record['process_cleanup']['status'],'UNKNOWN')
        self.assertFalse(record['FULL_LAUNCH_ENVELOPE_VERIFIED'])


class ControllerIntegrationHardeningTests(unittest.TestCase):
    def blocked(self, changes, reason):
        with baseline.FullControllerMockWorkflow().workflow_fixture(child_changes=changes) as f:
            self.assertEqual(controller.main(['workflow']),2)
            self.assertIn(reason,f.emit.call_args.args[0]['reason'])
            self.assertFalse(f.emit.call_args.args[0]['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_child_actual_pid_is_bound_to_popen(self):
        self.blocked({'pid':111},'CHILD_ACTUAL_PID_REQUIRED')

    def test_child_guard_copy_or_wrong_parent_or_program_rejected(self):
        with baseline.FullControllerMockWorkflow().workflow_fixture() as f:
            valid=copy.deepcopy(json.loads(f.proc.communicate.return_value[0])['proof']['guard'])
        for key,value in (('pid',222),('parent_pid',333),('program_sha256','0'*64),
                          ('origin','CURRENT_PROCESS_INSTALL'),('filter_count_after',2)):
            bad=copy.deepcopy(valid);bad[key]=value
            if key == 'origin':
                # Make the forged install proof internally valid, so this
                # case reaches the distinct child-inheritance origin gate.
                bad['filter_count_before']=2
            with self.subTest(key=key):
                self.blocked({'guard':bad},'GUARD')

    def test_parent_namespace_copy_is_not_child_readback(self):
        self.blocked({'namespace':baseline.good_proof()},'CHILD_CURRENT_NAMESPACE_FACTS_REQUIRED')

    def test_child_current_namespace_facts_cannot_be_empty_or_contradict_top_level(self):
        with baseline.FullControllerMockWorkflow().workflow_fixture() as f:
            valid=copy.deepcopy(json.loads(f.proc.communicate.return_value[0])['proof']['namespace'])
        missing=copy.deepcopy(valid);missing['current_identity_facts']['identities']={}
        self.blocked({'namespace':missing},'CURRENT_EXACT_NAMESPACE_IDENTITIES')
        inconsistent=copy.deepcopy(valid)
        mapping=inconsistent['current_identity_facts']['uid_map'].split()
        mapping[1]=str(int(mapping[1])+1)
        inconsistent['current_identity_facts']['uid_map']=' '.join(mapping)+chr(10)
        self.blocked({'namespace':inconsistent},'UNCHANGED_NAMESPACE_ID_MAP_CHANGED:uid_map')

    def test_child_wrong_source_or_policy_cannot_pass(self):
        self.blocked({'source_revision':'b'*40},'CHILD_SOURCE_REVISION_MISMATCH')
        self.blocked({'classified_mount_policy':{'status':'PASS_SOURCE_POLICY_PREREQUISITES',
                      'policy_sha256':'0'*64}},'CHILD_CLASSIFIED_MOUNT_POLICY_REQUIRED')

    def test_child_probe_wrong_pid_or_missing_checks_rejected(self):
        with baseline.FullControllerMockWorkflow().workflow_fixture() as f:
            valid=copy.deepcopy(json.loads(f.proc.communicate.return_value[0])['proof']['guard_probe'])
        for key,value in (('pid',222),('checks',[]),('all_denied',False)):
            bad=copy.deepcopy(valid);bad[key]=value
            with self.subTest(key=key):
                self.blocked({'guard_probe':bad},'CHILD_CURRENT_GUARD_PROBES_REQUIRED')

    def test_rejected_probe_details_emitted_before_gate(self):
        view=baseline.AttestationFixture()
        with view.installed(),mock.patch.object(controller.controller_guard,'probe',
                return_value={'status':'REJECTED','all_denied':False,'pid':222,'checks':[
                    {'case_id':'setns_invalid_fd_denied','return_code':-1,'errno':9}]}):
            self.assertEqual(controller.main(['stage-pre']),2)
        readback=next(x for x in view.emitted if x['kind']=='GUARD_DENIAL_READBACK')
        self.assertEqual(readback['probe']['checks'][0]['errno'],9)
        self.assertEqual(view.emitted[-1]['kind'],'BLOCKED')

    def test_foreign_cgroup_never_installs_or_probes(self):
        view=baseline.AttestationFixture();view.reads['/proc/self/cgroup']='0::/FOREIGN\n'
        with view.installed(),mock.patch.object(controller.controller_guard,'install') as install, \
             mock.patch.object(controller.controller_guard,'probe') as probe:
            self.assertEqual(controller.main(['stage-pre']),2)
        install.assert_not_called();probe.assert_not_called()

    def test_output_exhaustion_and_scratch_error_keep_original_terminal(self):
        with baseline.FullControllerMockWorkflow().workflow_fixture(
                child_error=ValueError('RUN_OUTPUT_BOUND'),cleanup_failure=True) as f:
            self.assertEqual(controller.main(['workflow']),2)
            rows=[x.args[0] for x in f.emit.call_args_list]
        self.assertEqual(rows[-1]['kind'],'BLOCKED')
        self.assertEqual(rows[-1]['reason'],'RUN_OUTPUT_BOUND')
        self.assertEqual(rows[-1]['scratch_cleanup']['status'],'UNKNOWN')
        self.assertFalse(any(x['kind']=='CLEANUP_FAILED' for x in rows))

    def test_mock_complete_has_contiguous_phases_and_independent_transport(self):
        with baseline.FullControllerMockWorkflow().workflow_fixture() as f:
            self.assertEqual(controller.main(['workflow']),0)
            record=f.emit.call_args.args[0]
        phases=record['records']
        self.assertEqual([x['name'] for x in phases],list(controller.PHASES))
        self.assertTrue(all(x['completed'] and x['end_ns']>=x['start_ns'] for x in phases))
        self.assertTrue(all(a['end_ns']==b['start_ns'] for a,b in zip(phases,phases[1:])))
        self.assertEqual(phases[5]['logical_transport']['status'],'PASS_LOGICAL_ARTIFACT_TRANSPORT_ONLY')
        self.assertFalse(record['manager_cleanup_verified'])
        self.assertTrue(record['controller_still_alive'])

    def test_private_handoff_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            work=Path(name);tree=work/'controller';tree.mkdir()
            (tree/'target').write_text('{}\n')
            (tree/'namespace_handoff.json').symlink_to(tree/'target')
            with mock.patch.object(controller,'WORK',work), \
                 mock.patch.object(controller.Path,'cwd',return_value=tree):
                with self.assertRaises(OSError):controller.load_child_context('/INERT_CGROUP')

    def test_volatile_raw_capture_and_large_safe_projection_stay_bounded(self):
        c=io.EvidenceBuffer();out=[];write=lambda fd,b:(out.append(b),len(b))[1]
        data=b'INERT_ONLY\n';sha=hashlib.sha256(data).hexdigest()
        c.emit({'kind':'PRIVATE_MOUNTINFO_RAW','stage':'INERT','raw_sha256':sha,
                'raw_bytes':len(data),'complete':True,'chunks':1,'chunk_index':0,
                'base64':base64.b64encode(data).decode()},write=write)
        self.assertEqual(c.mount_capture(sha,'INERT'),data)
        c.emit({'kind':'MOUNT_INVENTORY_SAFE','inventory':{'fixture':'x'*16000}},write=write)
        self.assertLess(len(b''.join(out)),1500)
        self.assertGreater(c.private_bytes,16000)
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):c.mount_capture(sha,'ABSENT')


    @staticmethod
    def capture_fixture():
        data = b'INERT_CAPTURE_ONLY_' * 120
        sha = hashlib.sha256(data).hexdigest()
        blocks = [data[i:i+1024] for i in range(0, len(data), 1024)]
        rows = [{'kind':'PRIVATE_MOUNTINFO_RAW','stage':'INERT',
                 'raw_sha256':sha,'raw_bytes':len(data),'complete':True,
                 'chunks':len(blocks),'chunk_index':i,
                 'base64':base64.b64encode(block).decode()}
                for i,block in enumerate(blocks)]
        return data, sha, rows

    @staticmethod
    def capture_buffer(rows):
        buffer = io.EvidenceBuffer()
        # Synthetic canonical private frames only; never read a live mount.
        for row in rows:
            buffer.emit(row, write=lambda fd,raw:len(raw))
        return buffer

    def test_mount_capture_duplicate_or_missing_chunks_rejected(self):
        data, sha, rows = self.capture_fixture()
        self.assertEqual(self.capture_buffer(rows).mount_capture(sha,'INERT'),data)
        for frames,reason in ((rows+[copy.deepcopy(rows[0])],'DUPLICATE'),
                              (rows[:-1],'INCOMPLETE')):
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError,reason):
                self.capture_buffer(frames).mount_capture(sha,'INERT')

    def test_mount_capture_inconsistent_metadata_is_rejected(self):
        _, sha, rows = self.capture_fixture()
        variations = (
            (0,'raw_sha256','0'*64,'IDENTITY'),
            (0,'complete',False,'COMPLETENESS'),
            (0,'chunks',True,'FIELDS'),(0,'chunks',17,'FIELDS'),
            (0,'chunk_index',-1,'FIELDS'),(0,'chunk_index',True,'FIELDS'),
            (0,'raw_bytes',False,'FIELDS'),(0,'raw_bytes',16385,'FIELDS'),
            (1,'chunks',4,'AMBIGUOUS'),(1,'raw_bytes',len(b'INERT_CAPTURE_ONLY_'*120)+1,'AMBIGUOUS'))
        for index,key,value,reason in variations:
            frames = copy.deepcopy(rows); frames[index][key] = value
            with self.subTest(field=key,value=value), self.assertRaisesRegex(ValueError,reason):
                self.capture_buffer(frames).mount_capture(sha,'INERT')

    def test_mount_capture_payload_corruption_and_block_overflow_rejected(self):
        _, sha, rows = self.capture_fixture()
        frames = copy.deepcopy(rows); frames[0]['base64'] = '@@'
        with self.assertRaises(ValueError):
            self.capture_buffer(frames).mount_capture(sha,'INERT')
        frames = copy.deepcopy(rows)
        frames[0]['base64'] = base64.b64encode(b'x'*1025).decode()
        with self.assertRaisesRegex(ValueError,'CHUNK_BOUND'):
            self.capture_buffer(frames).mount_capture(sha,'INERT')
        for replacement in (b'x'*1024,b''):
            frames = copy.deepcopy(rows)
            frames[0]['base64'] = base64.b64encode(replacement).decode()
            with self.subTest(length=len(replacement)), self.assertRaisesRegex(ValueError,'SHA256'):
                self.capture_buffer(frames).mount_capture(sha,'INERT')


    def test_capture_completeness_distinguishes_partial_input_from_ram(self):
        _, _, rows = self.capture_fixture()
        for complete in (False,None,1,'true'):
            row = copy.deepcopy(rows[0]); row['complete'] = complete
            with self.subTest(complete=complete):
                buffer = self.capture_buffer([row])
                self.assertGreater(buffer.private_bytes,0)
                self.assertFalse(buffer.summary()['private_capture_complete'])
                self.assertTrue(buffer.summary()['private_buffer_complete'])
        buffer = self.capture_buffer(rows)
        self.assertTrue(buffer.summary()['private_capture_complete'])
        self.assertTrue(buffer.summary()['private_buffer_complete'])

    def test_nested_partial_capture_never_becomes_complete(self):
        _, _, rows = self.capture_fixture()
        row = copy.deepcopy(rows[0]); row['complete'] = False
        wrappers = ({'kind':'CHILD_DIAGNOSTIC_RECORD','record':row},
                    {'kind':'BLOCKED','details':[{'nested':row}]},
                    {'kind':'BLOCKED','reason':json.dumps({'nested':row})},
                    {'kind':'BLOCKED','reason':'prefix '+json.dumps(row)})
        for wrapper in wrappers:
            with self.subTest(kind=wrapper['kind'],serialized='reason' in wrapper):
                buffer = self.capture_buffer([wrapper])
                self.assertFalse(buffer.summary()['private_capture_complete'])
                self.assertTrue(buffer.summary()['private_buffer_complete'])
                self.assertGreater(buffer.private_bytes,0)
        metadata={'kind':'MOUNTINFO_CAPTURE_SAFE_METADATA','complete':False,
                  'raw_sha256':row['raw_sha256'],'raw_bytes':row['raw_bytes']}
        buffer=self.capture_buffer([metadata])
        self.assertFalse(buffer.summary()['private_capture_complete'])
        self.assertEqual(buffer.private_bytes,0)



if __name__=='__main__':unittest.main()
