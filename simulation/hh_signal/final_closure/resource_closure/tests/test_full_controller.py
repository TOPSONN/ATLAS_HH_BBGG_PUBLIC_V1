"""Offline controller policies: no service, filter, approval, or native calls.

The kernel observations below are explicit mocks. Their success is not actual
resource-enforcement evidence and cannot unlock the full campaign or build.
"""
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from simulation.hh_signal.final_closure.resource_closure import full_controller as c


class AttestationFixture:
    """Exact reviewed artificial cgroup/mount view; never inspects the host."""

    def __init__(self):
        self.relative = '/user.slice/user-1000.slice/user@1000.service/app.slice/' + c.UNIT
        self.aggregate = '/sys/fs/cgroup' + self.relative
        self.reads = {'/proc/self/cgroup': '0::' + self.relative + '\n'}
        self.reads.update({self.aggregate + '/' + key: value for key, value in c.EFFECTIVE.items()})
        self.reads.update({self.aggregate + '/' + key: value for key, value in {
            'cpu.stat': 'usage_usec 15000\nuser_usec 10000\nsystem_usec 5000\n',
            'memory.current': '33554432', 'memory.peak': '37748736',
            'memory.swap.current': '0', 'cgroup.events': 'populated 1\nfrozen 0',
            'cgroup.procs': '222\n223\n'}.items()})
        self.lines = [
            '1 0 0:1 / / ro,relatime - ext4 /dev/sdd ro',
            '2 1 0:2 / ' + str(c.WORK) + ' rw,nosuid,nodev,noexec - tmpfs tmpfs rw',
            '3 1 0:3 / /tmp rw,nosuid,nodev,noexec - tmpfs tmpfs rw']
        self.vfs = {
            str(c.REPO): SimpleNamespace(f_flag=os.ST_RDONLY),
            self.aggregate: SimpleNamespace(f_flag=os.ST_RDONLY),
            str(c.WORK): SimpleNamespace(f_flag=0, f_blocks=2048, f_frsize=4096,
                                        f_files=1024, f_bfree=1024, f_ffree=1000),
            '/tmp': SimpleNamespace(f_flag=0, f_blocks=256, f_frsize=4096,
                                    f_files=256, f_bfree=128, f_ffree=250)}
        self.rlimits = {kind: (cap, cap) for kind, cap in c.LIMITS.values()}
        self.affinity = {3}

    def read_text(self, path, *args, **kwargs):
        key = str(path)
        if key == '/proc/self/mountinfo':
            return '\n'.join(self.lines) + '\n'
        if key not in self.reads:
            raise FileNotFoundError(key)
        return self.reads[key]

    @contextlib.contextmanager
    def installed(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(Path, 'read_text', autospec=True,
                                                  side_effect=self.read_text))
            stack.enter_context(mock.patch.object(c.resource, 'getrlimit',
                                                  side_effect=lambda kind: self.rlimits[kind]))
            stack.enter_context(mock.patch.object(c.os, 'statvfs',
                                                  side_effect=lambda p: self.vfs[str(p)]))
            stack.enter_context(mock.patch.object(c.os, 'stat',
                                                  return_value=SimpleNamespace(st_ino=987)))
            stack.enter_context(mock.patch.object(c.os, 'sched_getaffinity',
                                                  return_value=self.affinity))
            stack.enter_context(mock.patch.object(c.os, 'getpid', return_value=222))
            stack.enter_context(mock.patch.object(c.os, 'getuid', return_value=1000))
            stack.enter_context(mock.patch.dict(c.os.environ, {}, clear=True))
            yield


class FullControllerClosedGates(unittest.TestCase):
    def test_no_receipt_can_establish_persistent_capacity(self):
        for receipt in (None, {}, {'status': 'PASS'},
                        {'quota_verified': True, 'FULL_LAUNCH_ENVELOPE_VERIFIED': True},
                        {'allocated_bytes': 0, 'disk_bytes': 16777216, 'sha256': 'a' * 64}):
            with self.subTest(receipt=receipt):
                with self.assertRaisesRegex(ValueError, 'PERSISTENT_ALLOCATED_DISK_HARD_BOUND_NOT_IMPLEMENTED'):
                    c.persistent_storage_gate(receipt)

    def test_environment_cannot_unlock_campaign_or_formal_build(self):
        with mock.patch.dict(os.environ, {'FULL_LAUNCH_ENVELOPE_VERIFIED': 'true',
                                         'PERSISTENT_QUOTA_VERIFIED': 'true',
                                         'BUILD_AUTHORIZED': '1'}, clear=True), \
             mock.patch.object(c.subprocess, 'Popen') as child, \
             mock.patch.object(c.subprocess, 'run') as process, \
             mock.patch.object(c.os, 'execv') as activation:
            with self.assertRaisesRegex(ValueError, 'PERSISTENT_ALLOCATED_DISK_HARD_BOUND_NOT_IMPLEMENTED'):
                c.run_full_campaign({'status': 'PASS'}, authorized=True)
            with self.assertRaisesRegex(ValueError, 'FORMAL_BUILD_NOT_AUTHORIZED'):
                c.run_formal_build({'status': 'PASS'}, authorized=True)
            child.assert_not_called()
            process.assert_not_called()
            activation.assert_not_called()

    def test_full_campaign_calls_storage_gate_before_dispatch(self):
        with mock.patch.object(c, 'persistent_storage_gate',
                               side_effect=ValueError('REVIEWED_STORAGE_DENIAL')) as gate, \
             mock.patch.object(c, 'workflow') as workflow:
            with self.assertRaisesRegex(ValueError, 'REVIEWED_STORAGE_DENIAL'):
                c.run_full_campaign()
            gate.assert_called_once_with()
            workflow.assert_not_called()

    def test_cli_denials_preserve_false_verdict_and_zero_counters(self):
        for action in ('BUILD_ONLY', 'full-campaign'):
            with self.subTest(action=action), mock.patch.object(c, 'emit') as emit, \
                 mock.patch.object(c.os, 'execv') as activation:
                self.assertEqual(c.main([action]), 2)
                record = emit.call_args.args[0]
                self.assertEqual(record['kind'], 'BLOCKED')
                self.assertFalse(record['FULL_LAUNCH_ENVELOPE_VERIFIED'])
                for key in c.ZERO:
                    self.assertEqual(record[key], 0)
                activation.assert_not_called()

    def test_unknown_action_or_extra_options_do_not_activate(self):
        for argv in (['launch-live-diagnostic', '--output', '/tmp/escape'],
                     ['launch-live'], ['BUILD_ONLY', '--authorized'], ['model-import']):
            with self.subTest(argv=argv), mock.patch.object(c.os, 'execv') as activation, \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    c.main(argv)
                activation.assert_not_called()


class FullControllerKernelView(unittest.TestCase):
    def setUp(self):
        self.view = AttestationFixture()

    def assert_rejected(self, reason):
        with self.view.installed(), self.assertRaisesRegex(ValueError, reason):
            c.attestation('OFFLINE_MOCK')

    def test_exact_artificial_view_reports_observations_only(self):
        with self.view.installed():
            proof = c.attestation('OFFLINE_MOCK')
        self.assertEqual(proof['stage'], 'OFFLINE_MOCK')
        self.assertEqual(proof['CPU_usage_usec'], 15000)
        self.assertEqual(proof['memory_peak_bytes'], 37748736)
        self.assertEqual(proof['aggregate_cgroup'], self.view.aggregate)
        self.assertEqual(proof['effective'], c.EFFECTIVE)
        self.assertIsNone(proof['LISTEN_FDS'])
        self.assertNotIn('FULL_LAUNCH_ENVELOPE_VERIFIED', proof)

    def test_exec_control_leaf_still_reads_aggregate_limits(self):
        self.view.reads['/proc/self/cgroup'] = '0::' + self.view.relative + '/control\n'
        with self.view.installed():
            proof = c.attestation('OFFLINE_MOCK_CONTROL')
        self.assertEqual(proof['aggregate_cgroup'], self.view.aggregate)
        self.assertEqual(proof['leaf_cgroup'], self.view.aggregate + '/control')

    def test_empty_v1_or_multiple_memberships_rejected(self):
        for row in ('', '2:memory:/user.slice\n',
                    '0::' + self.view.relative + '\n0::' + self.view.relative + '\n'):
            with self.subTest(row=row):
                self.view.reads['/proc/self/cgroup'] = row
                self.assert_rejected('CGROUP_V2_REQUIRED')

    def test_foreign_or_repeated_service_membership_rejected(self):
        for row in ('0::' + self.view.relative.replace(c.UNIT, 'foreign.service'),
                    '0::' + self.view.relative + '/' + c.UNIT,
                    '0::' + self.view.relative + '/worker'):
            with self.subTest(row=row):
                self.view.reads['/proc/self/cgroup'] = row
                self.assert_rejected('OWN_SERVICE_CGROUP_REQUIRED')

    def test_foreign_user_slice_rejected(self):
        self.view.reads['/proc/self/cgroup'] = '0::' + self.view.relative.replace('1000', '1001')
        self.assert_rejected('OWN_USER_SERVICE_SLICE_REQUIRED')

    def test_nested_worker_control_cgroup_rejected(self):
        self.view.reads['/proc/self/cgroup'] = '0::' + self.view.relative + '/worker/control\n'
        self.assert_rejected('UNREVIEWED_CGROUP_DESCENDANT')

    def test_each_effective_limit_requires_exact_kernel_value(self):
        for key in c.EFFECTIVE:
            with self.subTest(key=key):
                original = self.view.reads[self.view.aggregate + '/' + key]
                self.view.reads[self.view.aggregate + '/' + key] = 'max'
                self.assert_rejected('KERNEL_EFFECTIVE_LIMIT_MISMATCH')
                self.view.reads[self.view.aggregate + '/' + key] = original

    def test_missing_effective_file_is_not_infinity_or_pass(self):
        del self.view.reads[self.view.aggregate + '/memory.max']
        with self.view.installed(), self.assertRaises(FileNotFoundError):
            c.attestation('OFFLINE_MOCK')

    def test_soft_or_hard_rlimit_mismatch_rejected(self):
        for name, (kind, cap) in c.LIMITS.items():
            for pair in ((cap + 1, cap + 1), (cap, cap + 1)):
                with self.subTest(name=name, pair=pair):
                    self.view.rlimits[kind] = pair
                    self.assert_rejected('HARD_RLIMIT_MISMATCH:' + name)
            self.view.rlimits[kind] = (cap, cap)

    def test_multi_cpu_affinity_rejected(self):
        self.view.affinity = {2, 3}
        self.assert_rejected('ONE_CPU_REQUIRED')

    def test_writable_source_or_cgroup_rejected(self):
        for path, reason in ((str(c.REPO), 'SOURCE_READONLY_REQUIRED'),
                             (self.view.aggregate, 'CGROUP_READONLY_REQUIRED')):
            with self.subTest(path=path):
                self.view.vfs[path].f_flag = 0
                self.assert_rejected(reason)
                self.view.vfs[path].f_flag = os.ST_RDONLY

    def test_tmpfs_capacity_and_inode_increase_rejected(self):
        for path, field in ((str(c.WORK), 'f_blocks'), (str(c.WORK), 'f_files'),
                            ('/tmp', 'f_blocks'), ('/tmp', 'f_files')):
            with self.subTest(path=path, field=field):
                value = getattr(self.view.vfs[path], field)
                setattr(self.view.vfs[path], field, value + 1)
                self.assert_rejected('TMPFS_CAP_MISMATCH')
                setattr(self.view.vfs[path], field, value)

    def test_additional_writable_host_mount_rejected(self):
        self.view.lines.append('4 1 0:1 / /persistent rw,relatime - ext4 /dev/sdd rw')
        self.assert_rejected('UNACCOUNTED_WRITABLE_MOUNT')

    def test_missing_memory_peak_remains_unknown(self):
        del self.view.reads[self.view.aggregate + '/memory.peak']
        with self.view.installed():
            proof = c.attestation('OFFLINE_MOCK')
        self.assertIsNone(proof['memory_peak_bytes'])
        self.assertIsNone(proof['raw']['memory.peak'])

    def test_missing_cpu_stat_cannot_report_success(self):
        del self.view.reads[self.view.aggregate + '/cpu.stat']
        with self.view.installed(), self.assertRaises((ValueError, TypeError, AttributeError)):
            c.attestation('OFFLINE_MOCK')

    def test_malformed_cpu_measurement_rejected(self):
        self.view.reads[self.view.aggregate + '/cpu.stat'] = 'usage_usec UNKNOWN'
        with self.view.installed(), self.assertRaises(ValueError):
            c.attestation('OFFLINE_MOCK')

    def test_missing_kernel_proof_cli_stays_blocked(self):
        with mock.patch.object(c, 'attestation', side_effect=FileNotFoundError('memory.max')), \
             mock.patch.object(c, 'emit') as emit:
            self.assertEqual(c.main(['stage-pre']), 2)
            self.assertEqual(emit.call_args.args[0]['kind'], 'BLOCKED')
            self.assertFalse(emit.call_args.args[0]['FULL_LAUNCH_ENVELOPE_VERIFIED'])


class FullControllerMountPolicy(unittest.TestCase):
    def test_duplicate_or_absent_exact_tmpfs_mount_rejected(self):
        row = '2 1 0:2 / /tmp rw,nosuid,nodev,noexec - tmpfs tmpfs rw'
        for rows in ([], [row, row]):
            with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, 'EXACT_MOUNT_REQUIRED'):
                c.mount_row(Path('/tmp'), rows)

    def test_filesystem_type_and_each_mount_safety_flag_required(self):
        for filesystem, flags, reason in (
                ('ext4', 'rw,nosuid,nodev,noexec', 'TMPFS_REQUIRED'),
                ('tmpfs', 'rw,nodev,noexec', 'TMPFS_FLAGS'),
                ('tmpfs', 'rw,nosuid,noexec', 'TMPFS_FLAGS'),
                ('tmpfs', 'rw,nosuid,nodev', 'TMPFS_FLAGS')):
            row = '2 1 0:2 / /tmp ' + flags + ' - ' + filesystem + ' tmpfs rw'
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, reason):
                c.mount_row(Path('/tmp'), [row])


class FullControllerCommandAndLifecycle(unittest.TestCase):
    def properties(self):
        with mock.patch.object(c.os, 'sched_getaffinity', return_value={3}), \
             mock.patch.object(c.os, 'getuid', return_value=1000), \
             mock.patch.object(Path, 'home', return_value=Path('/home/inert')):
            return c.properties()

    def test_conservative_timer_and_quota_bounds_leave_margin(self):
        bounds = c.lifecycle_bounds()
        self.assertEqual(sum(bounds['stage_budgets_seconds'].values()), bounds['timer_budget_seconds'])
        self.assertLess(bounds['timer_budget_seconds'], 13)
        self.assertLess(bounds['quota_duration_CPU_upper_seconds'], 4)
        self.assertGreaterEqual(bounds['quota_duration_CPU_upper_seconds'],
                                .3 * bounds['timer_budget_seconds'] + .003)
        self.assertTrue(bounds['timer_scheduling_overrun_not_a_realtime_guarantee'])

    def test_fixed_command_has_no_host_output_or_privileged_transport(self):
        with mock.patch.object(c, 'properties', return_value=self.properties()):
            command = c.launch_command()
        self.assertEqual(command[:7], ['/usr/bin/systemd-run', '--user', '--quiet', '--wait',
                                      '--pipe', '--unit', c.UNIT])
        self.assertEqual(command[-5:], ['/usr/bin/python3', '-I', '-B',
                                       str(c.HERE / 'full_controller.py'), 'workflow'])
        for forbidden in ('sudo', '--system', '--scope', '--uid', '--collect', 'OpenFile=',
                          'ReadWritePaths=', 'BindPaths=', 'RootImage=', 'StandardOutput=file:'):
            self.assertFalse(any(forbidden in item for item in command), forbidden)

    def test_fixed_limits_same_cgroup_kill_and_no_restart(self):
        props = self.properties()
        expected = {'MemoryMax=536870912', 'MemorySwapMax=0', 'CPUQuota=30%',
                    'CPUQuotaPeriodSec=10000us', 'LimitCPU=2', 'LimitAS=536870912',
                    'LimitFSIZE=65536', 'TasksMax=16', 'RuntimeMaxSec=8s',
                    'TimeoutStartSec=1s', 'TimeoutStopSec=0.5s',
                    'KillMode=control-group', 'SendSIGKILL=yes', 'Restart=no',
                    'RuntimeRandomizedExtraSec=0', 'NotifyAccess=none',
                    'TimeoutStartFailureMode=kill', 'TimeoutStopFailureMode=kill'}
        self.assertTrue(expected <= set(props))
        self.assertEqual(sum(p.startswith('ExecStartPre=') for p in props), 1)
        self.assertEqual(sum(p.startswith('ExecStopPost=') for p in props), 1)
        self.assertFalse(any(p.startswith('ExecStart=') for p in props))

    def test_only_finite_tmpfs_mounts_and_no_persistent_writable_allowlist(self):
        props = self.properties()
        mounts = [p for p in props if p.startswith('TemporaryFileSystem=')]
        self.assertEqual(set(mounts), {
            'TemporaryFileSystem=' + str(c.WORK) + ':rw,size=8388608,nr_inodes=1024,nodev,nosuid,noexec',
            'TemporaryFileSystem=/tmp:rw,size=1048576,nr_inodes=256,nodev,nosuid,noexec'})
        self.assertIn('ProtectSystem=strict', props)
        self.assertIn('ProtectHome=read-only', props)
        self.assertIn('ReadOnlyPaths=/dev /proc /sys', props)
        self.assertFalse(any(p.startswith(('ReadWritePaths=', 'BindPaths=', 'OpenFile=')) for p in props))

    def test_activation_performs_only_fixed_exec_without_business_work(self):
        with mock.patch.object(c, 'launch_command', return_value=['FIXED']) as command, \
             mock.patch.object(c.os, 'execv', side_effect=RuntimeError('INERT_EXEC_REPLACEMENT')) as execute, \
             mock.patch.object(c, 'workflow') as workflow, \
             mock.patch.object(c, 'sha') as hashing:
            with self.assertRaisesRegex(RuntimeError, 'INERT_EXEC_REPLACEMENT'):
                c.main(['launch-live-diagnostic'])
            execute.assert_called_once_with('/usr/bin/systemd-run', ['FIXED'])
            command.assert_called_once_with()
            workflow.assert_not_called()
            hashing.assert_not_called()

    def test_source_contains_all_eight_ordered_lifecycle_phases(self):
        self.assertEqual(c.PHASES, ('pre_provisioning', 'source_git_preflight', 'dependency_hashing',
                                  'worker_creation_monitoring', 'inert_build_preparation',
                                  'receipt_writing', 'postflight_validation', 'failure_cleanup'))
        tree = ast.parse(Path(c.__file__).read_text())
        workflow = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'workflow')
        indices = [n.slice.value for n in ast.walk(workflow)
                   if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                   and n.value.id == 'PHASES' and isinstance(n.slice, ast.Constant)]
        self.assertEqual(sorted(indices), list(range(8)))
        self.assertTrue(any(isinstance(n, ast.Try) and n.finalbody for n in ast.walk(workflow)))
        calls = [n for n in ast.walk(workflow) if isinstance(n, ast.Call)]
        self.assertTrue(any(isinstance(n.func, ast.Attribute) and n.func.attr == 'killpg' for n in calls))
        self.assertFalse(any(isinstance(n.func, ast.Name) and n.func.id in
                             ('run_formal_build', 'run_full_campaign', 'HumanReview') for n in calls))

    def test_success_record_source_never_sets_full_envelope_true(self):
        tree = ast.parse(Path(c.__file__).read_text())
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value in (
                            'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED',
                            'FULL_LAUNCH_ENVELOPE_VERIFIED'):
                        found.append(key.value)
                        self.assertIsInstance(value, ast.Constant)
                        self.assertIs(value.value, False)
        self.assertIn('FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED', found)
        self.assertIn('FULL_LAUNCH_ENVELOPE_VERIFIED', found)

    def test_record_bound_rejects_before_any_descriptor_write(self):
        with mock.patch.object(c.os, 'write') as write:
            with self.assertRaisesRegex(ValueError, 'BOUNDED_RECORD_REQUIRED'):
                c.emit({'oversized': 'x' * 32768})
            write.assert_not_called()

    def test_nonfinite_measurements_not_serialized_as_json_nan(self):
        with self.assertRaises(ValueError):
            c.canonical({'CPU_seconds': float('nan')})

    def test_short_descriptor_writes_are_retried_without_losing_bytes(self):
        chunks = []
        def partial(fd, data):
            self.assertEqual(fd, 1)
            n = min(3, len(data))
            chunks.append(data[:n])
            return n
        with mock.patch.object(c.os, 'write', side_effect=partial):
            c.emit({'bounded': 1})
        self.assertEqual(b''.join(chunks), c.canonical({'bounded': 1}) + b'\n')

    def test_zero_byte_write_is_denied(self):
        with mock.patch.object(c.os, 'write', return_value=0), \
             self.assertRaisesRegex(ValueError, 'SHORT_RECEIPT_WRITE'):
            c.emit({'bounded': 1})


class FullControllerMockWorkflow(unittest.TestCase):
    """Lifecycle control flow with mocked programs/kernel and inert temp files."""

    @contextlib.contextmanager
    def workflow_fixture(self, *, child_changes=None, child_error=None,
                         child_returncode=0, source_changed=False, receipt_changed=False,
                         child_stderr=b'', extra_maps='', cleanup_failure=False):
        proof = {'aggregate_cgroup': '/INERT_CGROUP', 'mount_namespace_inode': 123}
        body = {'kind': 'CHILD_RECEIPT', 'proof': copy.deepcopy(proof), **c.ZERO}
        if child_changes:
            body['proof'].update(child_changes)
        proc = mock.Mock()
        proc.pid = 9876
        proc.returncode = child_returncode
        proc.poll.return_value = None if child_error else child_returncode
        if child_error:
            proc.communicate.side_effect = child_error
        else:
            proc.communicate.return_value = (json.dumps(body).encode(), child_stderr)
        checked = {'git_preflight': {
            'status': 'PASS', 'index_sha256': 'a' * 64, 'wall_seconds': .01,
            'CPU_seconds': .005, 'tracked_files': 1444,
            'critical_source_sha256': {'INERT': 'b' * 64}},
            'physics_sha256': 'c' * 64, 'source_identity': 'd' * 64}
        after = copy.deepcopy(checked)
        if source_changed:
            after['source_identity'] = 'e' * 64
        original_read = Path.read_text
        original_sha = c.sha
        original_rmdir = Path.rmdir
        with tempfile.TemporaryDirectory() as name, contextlib.ExitStack() as stack:
            work = Path(name)
            tree = work / 'controller'
            def read(path, *args, **kwargs):
                if str(path) == '/proc/self/maps':
                    return extra_maps
                return original_read(path, *args, **kwargs)
            def sha(path):
                if Path(path) == tree / 'receipt.json':
                    return 'f' * 64 if receipt_changed else original_sha(path)
                return '1' * 64
            def rmdir(path, *args, **kwargs):
                if cleanup_failure and path == tree:
                    raise OSError('INERT_CLEANUP_DENIED')
                return original_rmdir(path, *args, **kwargs)
            stack.enter_context(mock.patch.object(c, 'WORK', work))
            stack.enter_context(mock.patch.object(c, 'attestation', return_value=proof))
            stack.enter_context(mock.patch.object(c, 'sha', side_effect=sha))
            stack.enter_context(mock.patch.object(Path, 'read_text', autospec=True, side_effect=read))
            stack.enter_context(mock.patch.object(Path, 'rmdir', autospec=True, side_effect=rmdir))
            stack.enter_context(mock.patch.object(c.subprocess, 'run',
                return_value=SimpleNamespace(stdout='a' * 40 + '\n')))
            spawned = stack.enter_context(mock.patch.object(c.subprocess, 'Popen', return_value=proc))
            killed = stack.enter_context(mock.patch.object(c.os, 'killpg'))
            emit = stack.enter_context(mock.patch.object(c, 'emit'))
            stack.enter_context(mock.patch.object(c.sys, 'path', list(c.sys.path)))
            check = stack.enter_context(mock.patch(
                'simulation.hh_signal.final_closure.integration_runtime.contract.check_revision',
                side_effect=[checked, after]))
            yield SimpleNamespace(work=work, tree=tree, proc=proc, spawned=spawned,
                                  killed=killed, emit=emit, check=check)

    def test_mocked_complete_lifecycle_records_all_phases_and_cleans_fixed_files(self):
        with self.workflow_fixture() as fixture:
            self.assertEqual(c.main(['workflow']), 0)
            record = fixture.emit.call_args.args[0]
            self.assertEqual(record['status'], 'PASS_VOLATILE_DIAGNOSTIC')
            self.assertEqual([row['phase'] for row in record['records']], list(c.PHASES))
            self.assertFalse(record['FULL_LAUNCH_ENVELOPE_VERIFIED'])
            self.assertFalse(record['FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'])
            self.assertEqual(record['persistent_output_hard_bound'], 'BLOCKED')
            self.assertEqual(record['resource_matrix_cases_executed'], 0)
            self.assertEqual(fixture.check.call_count, 2)
            self.assertFalse(fixture.tree.exists())
            fixture.killed.assert_not_called()
            args, kwargs = fixture.spawned.call_args
            self.assertEqual(args[0][-1], 'inert-child')
            self.assertTrue(kwargs['start_new_session'])
            for key in c.ZERO:
                self.assertEqual(record[key], 0)

    def assert_blocked(self, reason, **kwargs):
        with self.workflow_fixture(**kwargs) as fixture:
            self.assertEqual(c.main(['workflow']), 2)
            records = [call.args[0] for call in fixture.emit.call_args_list]
            self.assertEqual(records[-1]['kind'], 'BLOCKED')
            self.assertIn(reason, records[-1]['reason'])
            self.assertFalse(records[-1]['FULL_LAUNCH_ENVELOPE_VERIFIED'])
            self.assertFalse(any(row.get('kind') == 'MAIN_LIFECYCLE_RECEIPT' for row in records))
            if not kwargs.get('cleanup_failure'):
                self.assertFalse(fixture.tree.exists())
            return fixture

    def test_child_failure_rejects_and_removes_partial_scratch(self):
        self.assert_blocked('INERT_CHILD_FAILED_OR_OUTPUT_BOUND', child_returncode=2)

    def test_child_stderr_rejects_even_if_exit_zero(self):
        self.assert_blocked('INERT_CHILD_FAILED_OR_OUTPUT_BOUND', child_stderr=b'failure')

    def test_child_in_sibling_cgroup_rejected(self):
        self.assert_blocked('SIBLING_CHILD_CGROUP_FORBIDDEN',
                            child_changes={'aggregate_cgroup': '/SIBLING_CGROUP'})

    def test_child_mount_namespace_change_rejected(self):
        self.assert_blocked('CHILD_MOUNT_NAMESPACE_CHANGED',
                            child_changes={'mount_namespace_inode': 999})

    def test_child_timeout_kills_process_group_and_waits(self):
        fixture = self.assert_blocked('timed out', child_error=subprocess.TimeoutExpired('INERT', 1))
        fixture.killed.assert_called_once_with(9876, c.signal.SIGKILL)
        fixture.proc.wait.assert_called_once_with(timeout=.2)

    def test_postflight_source_drift_rejects_after_receipt_written(self):
        self.assert_blocked('SOURCE_CHANGED', source_changed=True)

    def test_postflight_receipt_tamper_rejects(self):
        self.assert_blocked('RECEIPT_CHANGED', receipt_changed=True)

    def test_dependency_inventory_overflow_rejects_before_child(self):
        maps = '\n'.join('0000-1111 r-xp 0000 00:00 1 /INERT_LIBRARY_%d' % i for i in range(65))
        fixture = self.assert_blocked('DEPENDENCY_INVENTORY_BOUND', extra_maps=maps)
        fixture.spawned.assert_not_called()

    def test_cleanup_failure_preserves_original_child_error(self):
        fixture = self.assert_blocked('INERT_CHILD_FAILED_OR_OUTPUT_BOUND',
                                     child_returncode=2, cleanup_failure=True)
        records = [call.args[0] for call in fixture.emit.call_args_list]
        self.assertEqual(records[0]['kind'], 'CLEANUP_FAILED')
        self.assertIn('INERT_CHILD_FAILED_OR_OUTPUT_BOUND', records[0]['original_reason'])
        self.assertIn('INERT_CLEANUP_DENIED', records[0]['cleanup_reason'])


if __name__ == '__main__':
    unittest.main()
