"""Mock-only integration tests for mount/namespace recovery; no kernel calls."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from simulation.hh_signal.final_closure.resource_closure import full_controller as c
from simulation.hh_signal.final_closure.resource_closure.tests import test_full_controller as baseline_tests
from simulation.hh_signal.final_closure.resource_closure.tests.test_namespace_attestation import good_proof

AttestationFixture = baseline_tests.AttestationFixture


class ControllerRecoveryTests(unittest.TestCase):
    def run_attestation_main(self, view, action='stage-pre'):
        with view.installed():
            result = c.main([action])
        return result, view.emitted

    def test_malformed_mountinfo_preserved_before_safe_projection_and_rejection(self):
        view = AttestationFixture()
        view.lines = ['not mountinfo']
        result, records = self.run_attestation_main(view)
        self.assertEqual(result, 2)
        self.assertEqual([x['kind'] for x in records],
                         ['PRIVATE_MOUNTINFO_RAW', 'MOUNTINFO_CAPTURE_SAFE_METADATA',
                          'MOUNT_INVENTORY_SAFE', 'BLOCKED'])
        raw = base64.b64decode(records[0]['base64'])
        self.assertEqual(raw, b'not mountinfo\n')
        self.assertEqual(records[0]['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(records[2]['inventory']['status'], 'FAIL')
        self.assertIsNotNone(records[2]['inventory']['parse_error'])

    def test_persistent_rw_has_diagnostics_and_no_cgroup_or_namespace_reads(self):
        view = AttestationFixture()
        view.lines.append('4 1 8:1 / /persistent rw - ext4 /dev/synthetic rw')
        with view.installed(), mock.patch.object(c.namespace_attestation, 'collect') as collect:
            result = c.main(['stage-pre'])
        self.assertEqual(result, 2)
        collect.assert_not_called()
        inventory = next(x['inventory'] for x in view.emitted if x['kind'] == 'MOUNT_INVENTORY_SAFE')
        self.assertIn('UNACCOUNTED_WRITABLE_MOUNT_ID:4', inventory['violations'])
        self.assertFalse(view.emitted[-1]['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_invalid_utf8_preserves_original_bytes_before_rejecting(self):
        view = AttestationFixture()
        with view.installed(), mock.patch.object(c.mount_attestation, 'read_bounded', return_value=b'\xff'):
            self.assertEqual(c.main(['stage-pre']), 2)
        self.assertEqual(base64.b64decode(view.emitted[0]['base64']), b'\xff')
        self.assertEqual(view.emitted[2]['inventory']['parse_error'], 'MOUNTINFO_INVALID_UTF8')

    def test_missing_namespace_readback_remains_blocked_despite_manager_yes(self):
        view = AttestationFixture()
        unknown = {'status': 'UNKNOWN_OR_REJECTED', 'readback_complete': False,
                   'reason': 'INERT_IOCTL_DENIED'}
        with view.installed(), \
             mock.patch.dict(c.os.environ, {'PrivateNetwork': 'yes', 'PrivateIPC': 'yes',
                                           'PrivateUsers': 'yes'}), \
             mock.patch.object(c.namespace_attestation, 'collect', return_value=unknown):
            self.assertEqual(c.main(['stage-pre']), 2)
        self.assertEqual(view.emitted[-2]['kind'], 'NAMESPACE_READBACK')
        self.assertEqual(view.emitted[-2]['proof'], unknown)
        self.assertEqual(view.emitted[-1]['kind'], 'BLOCKED')

    def test_namespace_read_exception_does_not_report_a_pass(self):
        view = AttestationFixture()
        with view.installed(), mock.patch.object(c.namespace_attestation, 'collect',
                                                 side_effect=PermissionError('INERT_OWNER_QUERY_DENIED')):
            self.assertEqual(c.main(['stage-pre']), 2)
        self.assertIn('INERT_OWNER_QUERY_DENIED', view.emitted[-1]['reason'])
        self.assertFalse(any(x['kind'] == 'STAGE_PRE' for x in view.emitted))

    def test_namespace_inspection_cannot_claim_lifecycle_or_persistent_capacity(self):
        proof = {'namespace': good_proof()}
        with mock.patch.object(c, 'attestation', return_value=proof), \
             mock.patch.object(c, 'emit') as emit, \
             mock.patch.object(c, 'workflow') as workflow, \
             mock.patch.object(c.subprocess, 'Popen') as child:
            self.assertEqual(c.main(['namespace-inspection']), 0)
        record = emit.call_args.args[0]
        self.assertEqual(record['kind'], 'INSPECTION_ONLY_COMPLETE')
        self.assertFalse(record['EIGHT_PHASE_WORKFLOW_COMPLETED'])
        self.assertFalse(record['FULL_LAUNCH_ENVELOPE_VERIFIED'])
        self.assertEqual(record['persistent_capacity'], 'BLOCKED')
        child.assert_not_called()
        workflow.assert_not_called()

    def test_forged_environment_cannot_authorize_a_new_service(self):
        with mock.patch.dict(c.os.environ, {'KERNEL_APPROVED': 'yes', 'HUMAN_APPROVED': '1',
                                           'FULL_LAUNCH_ENVELOPE_VERIFIED': 'true',
                                           'REVIEWED_REVISION': 'a' * 40}, clear=True), \
             mock.patch.object(c.os, 'execv') as execute, \
             mock.patch.object(c.subprocess, 'Popen') as child, \
             mock.patch.object(c.subprocess, 'run') as process, \
             mock.patch.object(c, 'attestation') as attest, \
             mock.patch.object(c, 'emit') as emit:
            self.assertEqual(c.main(['launch-live-diagnostic']), 2)
        self.assertIn('NEW_KERNEL_ATTEMPT_REQUIRES_SEPARATE_EXPLICIT_AUTHORIZATION',
                      emit.call_args.args[0]['reason'])
        for action in (execute, child, process, attest):
            action.assert_not_called()

    def test_single_main_retains_all_namespace_and_privilege_restrictions(self):
        with mock.patch.object(c.os, 'sched_getaffinity', return_value={3}), \
             mock.patch.object(c.os, 'getuid', return_value=1000), \
             mock.patch.object(Path, 'home', return_value=Path('/home/inert')):
            properties = c.properties()
        expected = {'PrivateUsers=yes', 'PrivateNetwork=yes', 'PrivateIPC=yes',
                    'ProtectSystem=strict', 'ProtectHome=read-only',
                    'ProtectControlGroups=yes', 'NoNewPrivileges=yes',
                    'RestrictNamespaces=yes', 'CapabilityBoundingSet=',
                    'ReadOnlyPaths=/dev /proc /sys', 'KillMode=control-group',
                    'Restart=no', 'MemorySwapMax=0'}
        self.assertTrue(expected <= set(properties))
        self.assertFalse(any(x.startswith(('ExecStartPre=', 'ExecStopPost=',
                                          'ReadWritePaths=', 'BindPaths=')) for x in properties))

    def workflow_fixture(self, **kwargs):
        return baseline_tests.FullControllerMockWorkflow().workflow_fixture(**kwargs)

    def test_multi_record_child_preserves_diagnostics_and_validates_namespace(self):
        prefix = [{'kind': 'PRIVATE_MOUNTINFO_RAW', 'base64': 'aW5lcnQ=', 'complete': True},
                  {'kind': 'NAMESPACE_READBACK', 'proof': good_proof()}]
        with self.workflow_fixture(child_prefix_records=prefix) as fixture:
            self.assertEqual(c.main(['workflow']), 0)
            records = [x.args[0] for x in fixture.emit.call_args_list]
        self.assertTrue(all(x['kind'] == 'CHILD_DIAGNOSTIC_RECORD' for x in records[:2]))
        self.assertEqual([x['record'] for x in records[:2]], prefix)
        self.assertEqual(records[-1]['kind'], 'MAIN_LIFECYCLE_RECEIPT')
        self.assertFalse(records[-1]['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_forged_child_lifecycle_or_full_envelope_prefix_rejected(self):
        for forged in ({'kind': 'MAIN_LIFECYCLE_RECEIPT', 'FULL_LAUNCH_ENVELOPE_VERIFIED': True},
                       {'kind': 'NAMESPACE_READBACK', 'FULL_LAUNCH_ENVELOPE_VERIFIED': True},
                       {'kind': 'NAMESPACE_READBACK', 'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': True},
                       {'kind': 'NAMESPACE_READBACK', 'nested': [{'FULL_LAUNCH_ENVELOPE_VERIFIED': True}]},
                       {'kind': 'NAMESPACE_READBACK', 'FULL_LAUNCH_ENVELOPE_VERIFIED': 0},
                       {'kind': 'NAMESPACE_READBACK', 'FULL_LAUNCH_ENVELOPE_VERIFIED': None}):
            with self.subTest(forged=forged), self.workflow_fixture(child_prefix_records=[forged]) as fixture:
                self.assertEqual(c.main(['workflow']), 2)
                records = [x.args[0] for x in fixture.emit.call_args_list]
                self.assertFalse(any(x['kind'] == 'MAIN_LIFECYCLE_RECEIPT' for x in records))
                self.assertEqual(records[-1]['kind'], 'BLOCKED')
        explicit_false = {'kind': 'NAMESPACE_READBACK', 'FULL_LAUNCH_ENVELOPE_VERIFIED': False}
        with self.workflow_fixture(child_prefix_records=[explicit_false]) as fixture:
            self.assertEqual(c.main(['workflow']), 0)
            self.assertFalse(fixture.emit.call_args.args[0]['FULL_LAUNCH_ENVELOPE_VERIFIED'])
        for fields in ({'FULL_LAUNCH_ENVELOPE_VERIFIED': True},
                       {'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': True},
                       {'nested': [{'FULL_LAUNCH_ENVELOPE_VERIFIED': True}]}):
            with self.subTest(terminal_fields=fields), self.workflow_fixture(child_terminal_fields=fields) as fixture:
                self.assertEqual(c.main(['workflow']), 2)
                records = [x.args[0] for x in fixture.emit.call_args_list]
                self.assertFalse(any(x['kind'] == 'MAIN_LIFECYCLE_RECEIPT' for x in records))
                self.assertEqual(records[-1]['kind'], 'BLOCKED')

    def test_child_diagnostic_recursion_is_bounded(self):
        record = {'kind': 'NAMESPACE_READBACK', 'nested': {}}
        node = record['nested']
        for _ in range(33):
            node['nested'] = {}
            node = node['nested']
        with self.workflow_fixture(child_prefix_records=[record]) as fixture:
            self.assertEqual(c.main(['workflow']), 2)
            self.assertEqual(fixture.emit.call_args.args[0]['kind'], 'BLOCKED')

    def test_failed_child_terminal_and_stderr_preserved_as_private_rejected_evidence(self):
        with self.workflow_fixture(child_returncode=2, child_stderr=b'INERT_FAILURE') as fixture:
            self.assertEqual(c.main(['workflow']), 2)
            records = [x.args[0] for x in fixture.emit.call_args_list]
        stderr = next(x for x in records if x['kind'] == 'PRIVATE_CHILD_STDERR')
        self.assertEqual(base64.b64decode(stderr['base64']), b'INERT_FAILURE')
        self.assertEqual(stderr['sha256'], hashlib.sha256(b'INERT_FAILURE').hexdigest())
        rejected = next(x for x in records if x['kind'] == 'CHILD_TERMINAL_REJECTED')
        self.assertEqual(rejected['exit_status'], 2)
        self.assertEqual(rejected['terminal_record']['kind'], 'CHILD_RECEIPT')
        self.assertEqual(records[-1]['kind'], 'BLOCKED')

    def test_describe_diagnostic_returns_argv_without_authorizing_or_running_it(self):
        with mock.patch.object(c, 'launch_command', return_value=['FIXED', 'NAMESPACE_INSPECTION']), \
             mock.patch.object(c, 'emit') as emit, \
             mock.patch.object(c.os, 'execv') as execute, \
             mock.patch.object(c.subprocess, 'Popen') as child, \
             mock.patch.object(c.subprocess, 'run') as process, \
             mock.patch.object(c, 'attestation') as attest:
            self.assertEqual(c.main(['describe-diagnostic']), 0)
        record = emit.call_args.args[0]
        self.assertEqual(record['kind'], 'PROPOSED_ARGV_ONLY')
        self.assertEqual(record['argv'], ['FIXED', 'NAMESPACE_INSPECTION'])
        self.assertFalse(record['execution_authorized'])
        self.assertFalse(record['FULL_LAUNCH_ENVELOPE_VERIFIED'])
        for operation in (execute, child, process, attest):
            operation.assert_not_called()

    def test_missing_child_namespace_cannot_be_treated_as_inherited_proof(self):
        with self.workflow_fixture(child_changes={'namespace': {}}) as fixture:
            self.assertEqual(c.main(['workflow']), 2)
            self.assertEqual(fixture.emit.call_args.args[0]['kind'], 'BLOCKED')
            self.assertFalse(fixture.tree.exists())

    def test_each_child_namespace_drift_is_rejected(self):
        for name in c.namespace_attestation.TYPES:
            child = copy.deepcopy(good_proof())
            child['namespaces'][name]['inode'] += 50
            if name == 'user':
                for target in ('net', 'ipc'):
                    child['owner_userns'][target]['inode'] += 50
            with self.subTest(name=name), self.workflow_fixture(child_changes={'namespace': child}) as fixture:
                self.assertEqual(c.main(['workflow']), 2)
                self.assertEqual(fixture.emit.call_args.args[0]['kind'], 'BLOCKED')
                self.assertFalse(fixture.tree.exists())

    def test_child_terminal_receipt_is_required(self):
        with self.workflow_fixture(child_terminal_kind='NAMESPACE_READBACK') as fixture:
            self.assertEqual(c.main(['workflow']), 2)
            self.assertIn('CHILD_TERMINAL_RECEIPT_MISSING', fixture.emit.call_args.args[0]['reason'])

    def test_child_record_overflow_is_rejected(self):
        # 24 records fit the reviewed finite protocol (including terminal).
        prefix = [{'kind': 'NAMESPACE_READBACK', 'proof': good_proof()} for _ in range(23)]
        with self.workflow_fixture(child_prefix_records=prefix) as fixture:
            self.assertEqual(c.main(['workflow']), 0)
            self.assertFalse(fixture.emit.call_args.args[0]['FULL_LAUNCH_ENVELOPE_VERIFIED'])
        # One additional record must fail before any lifecycle success.
        prefix.append({'kind': 'NAMESPACE_READBACK', 'proof': good_proof()})
        with self.workflow_fixture(child_prefix_records=prefix) as fixture:
            self.assertEqual(c.main(['workflow']), 2)
            self.assertIn('CHILD_PROTOCOL_RECORD_BOUND', fixture.emit.call_args.args[0]['reason'])
            self.assertFalse(fixture.tree.exists())

    def test_child_json_malformed_or_empty_has_no_lifecycle_success(self):
        for raw in (b'', b'bad json\n'):
            with self.subTest(raw=raw), self.workflow_fixture(child_raw_override=raw) as fixture:
                self.assertEqual(c.main(['workflow']), 2)
                records = [x.args[0] for x in fixture.emit.call_args_list]
                self.assertFalse(any(x['kind'] == 'MAIN_LIFECYCLE_RECEIPT' for x in records))
                self.assertEqual(records[-1]['kind'], 'BLOCKED')

    def test_mocked_workflow_cannot_authorize_production_after_success(self):
        with self.workflow_fixture() as fixture:
            self.assertEqual(c.main(['workflow']), 0)
            with self.assertRaisesRegex(ValueError, 'FORMAL_BUILD_NOT_AUTHORIZED'):
                c.run_formal_build(fixture.emit.call_args.args[0])
            with self.assertRaisesRegex(ValueError, 'PERSISTENT_ALLOCATED_DISK_HARD_BOUND_NOT_IMPLEMENTED'):
                c.run_full_campaign(fixture.emit.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
