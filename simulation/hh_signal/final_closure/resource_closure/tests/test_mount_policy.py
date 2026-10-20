"""Independently constructed synthetic policy cases; no proc/ns/ioctl calls."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import unittest
from unittest import mock

from .. import mount_policy as p
from .test_namespace_attestation import good_proof


def row(i=1, parent=999, path='/', flags='ro,relatime', filesystem='ext4',
        source='/dev/synthetic', root='/', dev='8:1', optional=''):
    return ('%d %d %s %s %s %s%s - %s %s rw\n' %
            (i, parent, dev, root, path, flags, ' ' + optional if optional else '',
             filesystem, source)).encode()


def capture(extra=b''):
    return (row() + row(2, 1, '/var/tmp', 'rw,nosuid,nodev,noexec', 'tmpfs', 'tmpfs', dev='0:2') +
            row(3, 1, '/tmp', 'rw,nosuid,nodev,noexec', 'tmpfs', 'tmpfs', dev='0:3') + extra)


def private_facts(raw, namespace=None):
    ns = (namespace or good_proof())['namespaces']['mnt']
    nsid = {key: ns[key] for key in ('dev', 'inode')}
    return {path: {'schema': 'PHASE7I_PRIVATE_TMPFS_FACTS_V1',
                   'raw_sha256': hashlib.sha256(raw).hexdigest(), 'mount_id': mount_id,
                   'mount_namespace': nsid.copy(),
                   'statvfs': {'f_blocks': size // 4096, 'f_frsize': 4096,
                               'f_files': inodes, 'f_bfree': 16, 'f_ffree': 16, 'f_flag': 14}}
            for path, size, inodes, mount_id in
            [('/tmp', 1048576, 256, 3), ('/var/tmp', 8388608, 1024, 2)]}


def transcript(raw, namespace, mount_ids):
    nsid = {key: namespace['namespaces']['mnt'][key] for key in ('dev', 'inode')}
    contract = MountPolicyTests.policy['denial_transcript']
    rows = [('setns_invalid_fd_denied', 'setns', 'INVALID_FD'),
            ('unshare_invalid_flags_denied', 'unshare', 'INVALID_FLAGS'),
            ('fallocate_invalid_fd_denied', 'fallocate', 'INVALID_FD'),
            ('fsetxattr_invalid_fd_denied', 'fsetxattr', 'INVALID_FD'),
            ('ioctl_clone_invalid_fd_denied', 'ioctl', 'INVALID_FD'),
            ('connect_invalid_fd_denied', 'connect', 'INVALID_FD')]
    return {'schema': 'PHASE7I_KERNEL_API_DENIAL_TRANSCRIPT_V1',
            'raw_sha256': hashlib.sha256(raw).hexdigest(), 'source_revision': 'a' * 40,
            'mount_namespace': nsid,
            'namespace_proof_sha256': hashlib.sha256(p.canonical(namespace)).hexdigest(),
            'mount_ids': mount_ids, 'collector_source_sha256': contract['producer_source_sha256'],
            'probe': {'schema': 'PHASE7I_CONTROLLER_GUARD_DENIAL_V1',
                      'scope': 'VOLATILE_DIAGNOSTIC_ONLY', 'status': 'PASS_FIXED_INVALID_TARGET_DENIALS',
                      'pid': 777, 'program_sha256': contract['program_sha256'],
                      'checks': [{'case_id': name, 'syscall': syscall, 'target': target,
                                  'return_code': -1, 'errno': 1} for name, syscall, target in rows],
                      'all_denied': True, 'host_write_or_device_access_tested': False,
                      'FULL_LAUNCH_ENVELOPE_VERIFIED': False}}


class MountPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy_raw = p.DEFAULT_POLICY_PATH.read_bytes()
        cls.policy = p.load_policy(raw=cls.policy_raw)

    def check(self, raw=None, **changes):
        raw = raw if raw is not None else capture()
        kwargs = {'policy': self.policy, 'namespace_proof': good_proof(),
                  'private_facts': private_facts(raw), 'source_revision': 'a' * 40, 'controller_pid': 777}
        kwargs.update(changes)
        return p.verify(raw, '/review/repo', **kwargs)

    def codes(self, result):
        return [item['code'] for item in result['violations']]

    def assert_fail(self, result, code):
        self.assertEqual(result['status'], 'FAIL_POLICY')
        self.assertTrue(any(code in value for value in self.codes(result)), self.codes(result))

    def test_import_and_verify_do_not_load_policy_or_read_host(self):
        with mock.patch.object(Path, 'open', side_effect=AssertionError('NO_IMPLICIT_FILE_READ')):
            importlib.reload(p)
            result = self.check()
        self.assertEqual(result['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')

    def test_exact_policy_byte_and_semantic_pins(self):
        self.assertEqual(hashlib.sha256(self.policy_raw).hexdigest(), p.POLICY_SHA256)
        self.assertEqual(hashlib.sha256(p.canonical(self.policy)).hexdigest(), p.POLICY_SEMANTIC_SHA256)
        from .. import controller_guard
        producer = Path(controller_guard.__file__)
        self.assertEqual(hashlib.sha256(producer.read_bytes()).hexdigest(),
                         self.policy['denial_transcript']['producer_source_sha256'])
        self.assertEqual(controller_guard.program_identity(), self.policy['denial_transcript']['program_sha256'])
        for raw in (self.policy_raw + b' ', self.policy_raw[:-1], b'{}', b'x' * 16385):
            with self.subTest(raw_length=len(raw)), self.assertRaises(p.PolicyError):
                p.load_policy(raw=raw)

    def test_explicit_loader_is_bounded_binary_source_read(self):
        with mock.patch.object(Path, 'read_text', side_effect=AssertionError('NO_READ_TEXT')):
            self.assertEqual(p.load_policy(), self.policy)

    def test_mutating_profile_or_inserting_verified_flag_is_denied(self):
        for mutate in (lambda x: x['private_tmpfs']['/tmp'].update(bytes=2097152),
                       lambda x: x.update(verified=True),
                       lambda x: x['private_tmpfs']['/tmp'].update(inodes=True)):
            changed = copy.deepcopy(self.policy)
            mutate(changed)
            self.assert_fail(self.check(policy=changed), 'UNREVIEWED_OR_MUTATED_POLICY')

    def test_each_policy_rule_has_machine_resolvable_source(self):
        self.assertEqual(set(self.policy['rules']), {'P%02d' % i for i in range(11)})
        for rule in self.policy['rules'].values():
            self.assertTrue(rule['rule'])
            self.assertTrue(rule['sources'])
            self.assertTrue(all(name in self.policy['sources'] for name in rule['sources']))

    def test_limited_private_tmpfs_positive_is_source_only(self):
        result = self.check()
        self.assertEqual(result['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')
        self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])
        self.assertFalse(result['FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'])
        self.assertFalse(result['persistent_hard_capacity_verified'])
        self.assertTrue(result['collector_implemented'])
        self.assertFalse(result['collector_live_validated'])
        self.assertEqual(result['runtime_status'], 'NOT_EXECUTED_OR_UNVERIFIED')

    def test_source_under_readonly_ancestor_needs_no_exact_mount(self):
        result = self.check()
        self.assertEqual(result['source_covering_mount_id'], 1)
        self.assertEqual(result['class_counts']['source'], 0)
        self.assertEqual(result['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')

    def test_readonly_bind_with_rw_superblock_and_source_exact_mount(self):
        raw = capture(row(4, 1, '/review/repo', root='/frozen/repository'))
        self.assertEqual(self.check(raw)['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')
        self.assertEqual(self.check(raw)['source_covering_mount_id'], 4)

    def test_extra_persistent_rw_and_nested_writable_bind_fail(self):
        for extra in (row(4, 1, '/output', flags='rw'),
                      row(4, 1, '/readonly') + row(5, 4, '/readonly/sub', flags='rw', root='/outside')):
            with self.subTest(extra=extra):
                self.assert_fail(self.check(capture(extra)), 'NONPRIVATE_WRITABLE_MOUNT')

    def test_source_and_private_subtree_overmounts_fail_even_ro(self):
        for path, parent, code in (('/review/repo/sub', 1, 'SOURCE_SUBTREE_OVERMOUNT'),
                                   ('/tmp/sub', 3, 'PRIVATE_TMPFS_SUBTREE_OVERMOUNT'),
                                   ('/var/tmp/sub', 2, 'PRIVATE_TMPFS_SUBTREE_OVERMOUNT')):
            with self.subTest(path=path):
                self.assert_fail(self.check(capture(row(4, parent, path))), code)

    def test_source_cannot_be_covered_by_private_writable_ancestor(self):
        raw = capture()
        for repo in ('/tmp/source', '/', '/var'):
            with self.subTest(repo=repo):
                result = p.verify(raw, repo, policy=self.policy,
                                  namespace_proof=good_proof(), private_facts=private_facts(raw))
                self.assert_fail(result, 'SOURCE_AND_PRIVATE_TMPFS_OVERLAP')
                if repo == '/tmp/source':
                    self.assertIn('SOURCE_COVERED_BY_WRITABLE_MOUNT', self.codes(result))

    def test_root_parent_outside_namespace_is_legal(self):
        self.assertEqual(self.check()['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')

    def test_nonroot_outside_parent_cycle_and_hidden_coverage_fail(self):
        cases = [(row(4, 888, '/outside'), 'NONROOT_PARENT_OUTSIDE_CAPTURE'),
                 (row(4, 5, '/cycle') + row(5, 4, '/cycle/sub'), 'MOUNT_GRAPH_CYCLE'),
                 (row(4, 1, '/outer') + row(5, 1, '/outer/sub'), 'HIDDEN_OR_OVERRIDDEN_MOUNT_GRAPH')]
        for extra, code in cases:
            with self.subTest(code=code):
                self.assert_fail(self.check(capture(extra)), code)

    def test_legal_readonly_nested_tree_is_not_flattened(self):
        raw = capture(row(4, 1, '/outer') + row(5, 4, '/outer/sub'))
        self.assertEqual(self.check(raw)['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')

    def test_duplicate_mountpoint_or_id_malformed_and_escaped_path(self):
        for raw, code in [(capture(row(4, 1, '/tmp')), 'AMBIGUOUS_MOUNTPOINT'),
                          (capture(row(3, 1, '/other')), 'DUPLICATE_ID'),
                          (capture() + b'bad row\n', 'MOUNTINFO_'),
                          (capture(row(4, 1, r'/tmp\040escape', flags='rw')), 'NONPRIVATE_WRITABLE_MOUNT'),
                          (capture(row(4, 1, '/a/../tmp')), 'NONCANONICAL_PATH')]:
            with self.subTest(code=code):
                self.assert_fail(self.check(raw), code)

    def test_final_lf_explicit_incomplete_and_truncation_fail_closed(self):
        self.assert_fail(self.check(capture()[:-1]), 'INCOMPLETE_OR_NON_LF_CAPTURE')
        self.assert_fail(self.check(capture_complete=False), 'INCOMPLETE_OR_NON_LF_CAPTURE')
        self.assert_fail(self.check(capture_complete=1), 'INCOMPLETE_OR_NON_LF_CAPTURE')
        self.assert_fail(self.check(b'x' * 16384 + b'\n'), 'READ_BOUND_EXCEEDED')
        self.assertFalse(self.check(capture()[:-1])['capture_complete'])
        self.assertFalse(self.check(b'x' * 16384 + b'\n')['capture_complete'])

    def test_shared_slave_unknown_and_conflicting_propagation_fail(self):
        for optional in ('shared:1', 'master:1', 'shared:1 master:2',
                         'master:1 propagate_from:2', 'unknown:1',
                         'shared:1 shared:2', 'propagate_from:1', 'unbindable master:1'):
            with self.subTest(optional=optional):
                self.assert_fail(self.check(capture(row(4, 1, '/propagation', optional=optional))),
                                 'UNCONTAINED_OR_UNKNOWN_PROPAGATION')

    def test_private_and_unbindable_propagation_are_distinct(self):
        result = self.check(capture(row(4, 1, '/unbindable', optional='unbindable')))
        self.assertEqual(result['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')
        self.assertEqual(result['mounts'][-1]['propagation'], 'UNBINDABLE')

    def test_readback_missing_is_blocked_and_booleans_do_not_prove_capacity(self):
        result = self.check(private_facts={})
        self.assertEqual(result['status'], 'BLOCKED_REQUIRED_EVIDENCE')
        facts = private_facts(capture())
        facts['/tmp'] = {'verified': True, 'bytes': 1048576, 'inodes': 256}
        self.assert_fail(self.check(private_facts=facts), 'PRIVATE_TMPFS_BOUND_READBACK_INVALID')

    def test_private_readback_snapshot_mountid_namespace_and_limits_bound(self):
        for key, value in [('raw_sha256', 'c' * 64), ('mount_id', 99), ('mount_id', True),
                           ('mount_namespace', {'dev': 4, 'inode': 999})]:
            facts = private_facts(capture())
            facts['/tmp'][key] = value
            with self.subTest(key=key):
                self.assert_fail(self.check(private_facts=facts), 'PRIVATE_TMPFS_BOUND_READBACK_INVALID')
        for key, value in [('f_blocks', 512), ('f_files', 257), ('f_flag', 0), ('f_flag', 15),
                           ('f_frsize', True), ('f_bfree', 999999), ('f_ffree', 999999)]:
            facts = private_facts(capture())
            facts['/tmp']['statvfs'][key] = value
            with self.subTest(field=key):
                self.assert_fail(self.check(private_facts=facts), 'PRIVATE_TMPFS_BOUND_READBACK_INVALID')
        facts = private_facts(capture())
        facts['/tmp']['statvfs']['f_blocks'] = 2**80
        self.assert_fail(self.check(private_facts=facts), 'UNBOUNDED_OR_EXCESS_PRIVATE_READBACK')
        facts = private_facts(capture())
        facts['/unexpected'] = copy.deepcopy(facts['/tmp'])
        self.assert_fail(self.check(private_facts=facts), 'UNBOUNDED_OR_EXCESS_PRIVATE_READBACK')

    def test_foreign_namespace_and_unknown_namespace_do_not_pass(self):
        changed = good_proof()
        changed['namespaces']['mnt']['inode'] += 1
        self.assert_fail(self.check(namespace_proof=changed), 'PRIVATE_TMPFS_BOUND_READBACK_INVALID')
        unknown = {'status': 'UNKNOWN', 'readback_complete': False}
        self.assertEqual(self.check(namespace_proof=unknown)['status'], 'BLOCKED_REQUIRED_EVIDENCE')
        invalid = good_proof()
        invalid['CapEff'] = '0000000000000001'
        self.assert_fail(self.check(namespace_proof=invalid), 'NAMESPACE_EVIDENCE_INVALID')
        invalid = good_proof()
        invalid['owner_userns'] = None
        self.assert_fail(self.check(namespace_proof=invalid), 'NAMESPACE_EVIDENCE_INVALID')

    def test_kernel_api_rw_never_granted_by_path_or_transcript(self):
        raw = capture(row(4, 1, '/proc', flags='rw', filesystem='proc', source='proc', dev='0:4'))
        datum = transcript(raw, good_proof(), [4])
        self.assert_fail(self.check(raw, kernel_api_transcript=datum), 'NONPRIVATE_WRITABLE_MOUNT')

    def test_unexpected_proc_dev_submounts_fail(self):
        for path in ('/proc/unreviewed', '/dev/unreviewed', '/sys/unreviewed'):
            raw = capture(row(4, 1, path, flags='rw', filesystem='tmpfs', source='tmpfs', dev='0:4'))
            with self.subTest(path=path):
                result = self.check(raw)
                self.assert_fail(result, 'UNREVIEWED_KERNEL_API_MOUNT_IDENTITY')

    def test_ro_kernel_api_needs_denial_data_and_never_authenticates_collector(self):
        raw = capture(row(4, 1, '/proc', filesystem='proc', source='proc', dev='0:4'))
        self.assertEqual(self.check(raw)['status'], 'BLOCKED_REQUIRED_EVIDENCE')
        result = self.check(raw, kernel_api_transcript=transcript(raw, good_proof(), [4]))
        self.assertEqual(result['status'], 'PASS_SOURCE_POLICY_PREREQUISITES')
        self.assertEqual(result['kernel_api_runtime'], 'UNKNOWN_PRODUCER_NOT_LIVE_VALIDATED')
        self.assertTrue(result['collector_implemented'])
        self.assertFalse(result['collector_live_validated'])
        self.assertFalse(result['persistent_hard_capacity_verified'])
        self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_denial_transcript_exact_schema_bindings_and_numerics(self):
        raw = capture(row(4, 1, '/proc', filesystem='proc', source='proc', dev='0:4'))
        original = transcript(raw, good_proof(), [4])
        for key, value in [('raw_sha256', 'c' * 64), ('source_revision', 'd' * 40),
                           ('mount_ids', [True]), ('collector_source_sha256', 1),
                           ('namespace_proof_sha256', 'c' * 64),
                           ('mount_namespace', {'dev': 4, 'inode': 999}), ('verified', True)]:
            changed = copy.deepcopy(original)
            changed[key] = value
            with self.subTest(key=key):
                self.assert_fail(self.check(raw, kernel_api_transcript=changed), 'KERNEL_API_DENIAL_TRANSCRIPT_INVALID')
        for key, value in [('errno', 0), ('errno', True), ('return_code', 0),
                           ('return_code', -1.0), ('syscall', 'unreviewed'),
                           ('target', 'HOST_PATH')]:
            changed = copy.deepcopy(original)
            changed['probe']['checks'][0][key] = value
            with self.subTest(case_key=key):
                self.assert_fail(self.check(raw, kernel_api_transcript=changed), 'KERNEL_API_DENIAL_TRANSCRIPT_INVALID')
        for key, value in [('pid', 778), ('pid', True), ('program_sha256', 'c' * 64),
                           ('all_denied', False), ('host_write_or_device_access_tested', True),
                           ('FULL_LAUNCH_ENVELOPE_VERIFIED', True)]:
            changed = copy.deepcopy(original)
            changed['probe'][key] = value
            with self.subTest(probe_key=key):
                self.assert_fail(self.check(raw, kernel_api_transcript=changed), 'KERNEL_API_DENIAL_TRANSCRIPT_INVALID')

    def test_public_probe_validator_is_strict_and_never_authenticates_runtime(self):
        raw = capture(row(4, 1, '/proc', filesystem='proc', source='proc', dev='0:4'))
        probe = transcript(raw, good_proof(), [4])['probe']
        self.assertTrue(p.validate_guard_probe(probe, policy=self.policy, controller_pid=777))
        for pid in (True, 0, 778, 777.0):
            with self.subTest(expected_pid=pid):
                self.assertFalse(p.validate_guard_probe(probe, policy=self.policy, controller_pid=pid))
        for key, value in [('pid', True), ('pid', 778), ('all_denied', 1),
                           ('FULL_LAUNCH_ENVELOPE_VERIFIED', True), ('host_write_or_device_access_tested', True)]:
            changed = copy.deepcopy(probe)
            changed[key] = value
            with self.subTest(field=key):
                self.assertFalse(p.validate_guard_probe(changed, policy=self.policy, controller_pid=777))
        changed_policy = copy.deepcopy(self.policy)
        changed_policy['denial_transcript']['producer_source_sha256'] = True
        self.assertFalse(p.validate_guard_probe(probe, policy=changed_policy, controller_pid=777))
        datum = transcript(raw, good_proof(), [4])
        datum['collector_source_sha256'] = True
        self.assert_fail(self.check(raw, kernel_api_transcript=datum), 'KERNEL_API_DENIAL_TRANSCRIPT_INVALID')

    def test_denial_missing_duplicate_unknown_cases_reject(self):
        raw = capture(row(4, 1, '/proc', filesystem='proc', source='proc', dev='0:4'))
        for kind in ('missing', 'duplicate', 'unknown'):
            datum = transcript(raw, good_proof(), [4])
            if kind == 'missing':
                datum['probe']['checks'].pop()
            elif kind == 'duplicate':
                datum['probe']['checks'][1] = copy.deepcopy(datum['probe']['checks'][0])
            else:
                datum['probe']['checks'][0]['case_id'] = 'unreviewed_case'
            with self.subTest(kind=kind):
                self.assert_fail(self.check(raw, kernel_api_transcript=datum), 'KERNEL_API_DENIAL_TRANSCRIPT_INVALID')

    def test_runtime_wsl_and_unknown_classification_never_allow_rw(self):
        for path, filesystem, expected in [('/run/user/1000', 'tmpfs', 'user_runtime_wsl'),
                                           ('/mnt/wsl/unknown', 'tmpfs', 'user_runtime_wsl'),
                                           ('/private', 'overlay', 'unknown')]:
            raw = capture(row(4, 1, path, flags='rw', filesystem=filesystem))
            with self.subTest(path=path):
                result = self.check(raw)
                self.assertEqual(result['mounts'][-1]['class'], expected)
                self.assert_fail(result, 'NONPRIVATE_WRITABLE_MOUNT')

    def test_safe_projection_hashes_sensitive_paths_and_bounds_overflow(self):
        secret = '/home/private/fixture'
        self.assertNotIn(secret, json.dumps(self.check(capture(row(4, 1, secret)))))
        extra = b''.join(row(4 + i, 1, '/private' + str(i)) for i in range(100))
        result = self.check(capture(extra))
        self.assert_fail(result, 'SAFE_PROJECTION_BOUND_EXCEEDED')
        self.assertFalse(result['projection_complete'])
        self.assertLessEqual(len(p.canonical(result)), 16384)


if __name__ == '__main__':
    unittest.main()
