"""Offline BPF interpreter and fully mocked runtime paths. No kernel calls."""
from __future__ import annotations
import copy
import ctypes
import errno
from contextlib import ExitStack
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from simulation.hh_signal.final_closure.resource_closure import controller_guard as g
from simulation.hh_signal.final_closure.resource_closure.tests.test_namespace_attestation import good_proof


def evaluate(nr, *, arch=g.AUDIT_ARCH_X86_64, arg0=0, arg1=0):
    """Independent tiny classic-BPF interpreter; no seccomp installation."""
    words = {0: nr & 0xFFFFFFFF, 4: arch, 16: arg0 & 0xFFFFFFFF,
             20: (arg0 >> 32) & 0xFFFFFFFF, 24: arg1 & 0xFFFFFFFF,
             28: (arg1 >> 32) & 0xFFFFFFFF}
    rows, pc, acc = g.program(), 0, 0
    for _ in range(len(rows) + 1):
        code, jt, jf, value = rows[pc]
        if code == 0x20:
            acc = words[value]
            pc += 1
        elif code in (0x15, 0x45):
            condition = acc == value if code == 0x15 else bool(acc & value)
            pc += 1 + (jt if condition else jf)
        elif code == 0x06:
            return value
        else:
            raise AssertionError('unreviewed opcode')
        if not 0 <= pc < len(rows):
            raise AssertionError('BPF jump out of bounds')
    raise AssertionError('BPF nontermination')


def guard(pid=600, before=2, after=3, origin='CURRENT_PROCESS_INSTALL'):
    return g._proof(pid, before, after, origin)


def facts():
    parent = good_proof()
    return {'schema': 'PHASE7I_CURRENT_NAMESPACE_FACTS_V1', 'pid': 601,
        'identities': {name: {k: row[k] for k in ('dev', 'inode')}
                       for name, row in parent['namespaces'].items()},
        **{key: copy.deepcopy(parent[key]) for key in
           ('uid_map', 'gid_map', 'CapEff', 'NoNewPrivs', 'Seccomp', 'network_interfaces')}}


class ProgramTests(unittest.TestCase):
    def test_all_historical_denials_preserved(self):
        self.assertTrue(g.historical.DENIED.items() <= g.DENIED.items())
        for name, number in g.historical.DENIED.items():
            with self.subTest(name=name):
                self.assertEqual(evaluate(number), g.EPERM)

    def test_fixed_new_native_syscall_numbers(self):
        self.assertEqual({name: g.DENIED[name] for name in
                          ('socket', 'connect', 'unshare', 'setns', 'clone3')},
                         {'socket': 41, 'connect': 42, 'unshare': 272, 'setns': 308, 'clone3': 435})
        self.assertEqual(g.NEW_NAMESPACE_FLAGS, 0x02000000 | 0x04000000 | 0x08000000 |
                         0x10000000 | 0x20000000 | 0x40000000 | 0x20000)

    def test_all_new_denied_syscalls_model_eperm(self):
        for name, number in g.DENIED.items():
            with self.subTest(name=name):
                self.assertEqual(evaluate(number), 0x00050001)

    def test_wrong_arch_and_x32_kill(self):
        for arch in (0x40000003, 0xC00000B7, 0):
            self.assertEqual(evaluate(0, arch=arch), g.KILL)
        for number in (0, 16, 56, 308):
            self.assertEqual(evaluate(number | 0x40000000), g.KILL)

    def test_all_ioctl_requests_denied_including_tty_and_nsfs(self):
        for request in (0x5401, 0x5413, 0x541B, 0xB701, 0xB703,
                        0x40049409, 0, 0x100005401, 0xFFFFFFFFFFFFFFFF):
            self.assertEqual(evaluate(16, arg1=request), g.EPERM)

    def test_clone_namespace_bits_and_high_word_denied(self):
        for bit in (0x20000, 0x02000000, 0x04000000, 0x08000000,
                    0x10000000, 0x20000000, 0x40000000, 0x100000000):
            with self.subTest(bit=bit):
                self.assertEqual(evaluate(56, arg0=bit | 17), g.EPERM)
        for flags in (0, 17, 0x100 | 0x200 | 0x10000 | 17, 0x4000 | 0x100 | 17):
            self.assertEqual(evaluate(56, arg0=flags), g.ALLOW)

    def test_default_allow_is_explicit_and_no_quota_claim(self):
        for number in (0, 1, 2, 3, 9, 57, 58, 59, 157, 317):
            self.assertEqual(evaluate(number), g.ALLOW)
        self.assertEqual(len(g.program_identity()), 64)
        self.assertEqual(g.program(), g.program())
        self.assertLess(len(g.program()), 4096)
        for code, jt, jf, value in g.program():
            self.assertTrue(0 <= jt <= 255 and 0 <= jf <= 255 and 0 <= value <= 0xFFFFFFFF)


class RuntimeMockTests(unittest.TestCase):
    def setUp(self):
        self.old = g._ACTIVE
        g._ACTIVE = None
        self.library = Mock()
        self.calls = []

        def prctl(code, *args):
            self.calls.append((code, args))
            return 2 if code == 21 else 1 if code == 39 else 0
        self.library.prctl.side_effect = prctl

    def tearDown(self):
        g._ACTIVE = self.old

    def context(self, counts=(2, 3), status_extra=None):
        stack = ExitStack()
        count_values = iter(counts)

        def status():
            return {'Seccomp_filters': str(next(count_values)), 'Seccomp': '2', 'NoNewPrivs': '1',
                    'CapEff': '0000000000000000', **(status_extra or {})}
        stack.enter_context(patch.object(g, '_libc', return_value=self.library))
        stack.enter_context(patch.object(g, '_status_fields', side_effect=status))
        stack.enter_context(patch.object(g.os, 'getpid', return_value=600))
        stack.enter_context(patch.object(g.platform, 'system', return_value='Linux'))
        stack.enter_context(patch.object(g.platform, 'machine', return_value='x86_64'))
        return stack

    def test_mock_install_exact_count_increment_and_current_pid(self):
        with self.context():
            proof = g.install()
        self.assertTrue(g.validate_guard(proof))
        self.assertEqual(proof['pid'], 600)
        self.assertEqual((proof['filter_count_before'], proof['filter_count_after']), (2, 3))
        self.assertEqual([row[0] for row in self.calls], [21, 39, 38, 22, 21, 39])
        self.assertIs(proof['FULL_LAUNCH_ENVELOPE_VERIFIED'], False)
        proof['pid'] = 1
        self.assertEqual(g._ACTIVE['pid'], 600)

    def test_failed_install_readback_does_not_activate(self):
        for counts in ((2, 2), (2, 4), (3, 2)):
            with self.subTest(counts=counts), self.context(counts), self.assertRaises(ValueError):
                g.install()
            self.assertIsNone(g._ACTIVE)

    def test_install_syscall_failure_stops_without_active_flag(self):
        original = self.library.prctl.side_effect
        for failed in (38, 22):
            self.library.prctl.side_effect = lambda code, *args: -1 if code == failed else original(code, *args)
            with self.subTest(failed=failed), self.context(), self.assertRaises(ValueError):
                g.install()
            self.assertIsNone(g._ACTIVE)
        self.library.prctl.side_effect = original

    def test_current_security_fields_missing_or_bad_rejected(self):
        for key, value in (('Seccomp_filters', ''), ('Seccomp_filters', '３'), ('Seccomp_filters', '0'),
                           ('Seccomp', '0'), ('NoNewPrivs', '0'), ('CapEff', '0000000000000001')):
            with self.subTest(key=key), self.context(status_extra={key: value}), self.assertRaises(ValueError):
                g.install()
            self.assertIsNone(g._ACTIVE)

    def test_install_wrong_arch_or_repeated_install_rejected(self):
        with patch.object(g.platform, 'machine', return_value='aarch64'), \
             patch.object(g, '_libc') as library, self.assertRaises(ValueError):
            g.install()
        library.assert_not_called()
        g._ACTIVE = guard()
        with patch.object(g, '_libc') as library, self.assertRaises(ValueError):
            g.install()
        library.assert_not_called()

    def test_child_readback_is_current_process_observation(self):
        with self.context((4,)):
            proof = g.readback(guard(pid=599))
        self.assertEqual(proof['pid'], 600)
        self.assertEqual(proof['parent_pid'], 599)
        self.assertEqual(proof['origin'], 'CURRENT_PROCESS_INHERITED_READBACK')
        self.assertEqual((proof['filter_count_before'], proof['filter_count_after']), (3, 4))
        self.assertIn('NOT_KERNEL_PROGRAM_DUMP', proof['program_identity_evidence'])
        self.assertEqual([x[0] for x in self.calls], [21, 39])

    def test_child_count_decrease_and_parent_corruption_fail(self):
        with self.context((2,)), self.assertRaises(ValueError):
            g.readback(guard())
        self.assertIsNone(g._ACTIVE)
        for key, value in (('program_sha256', '0' * 64), ('pid', True),
                           ('seccomp_mode', True), ('no_new_privs', True),
                           ('filter_count_after', True), ('FULL_LAUNCH_ENVELOPE_VERIFIED', True),
                           ('status', 'UNKNOWN')):
            bad = guard()
            bad[key] = value
            with self.subTest(key=key), patch.object(g, '_libc') as library, self.assertRaises(ValueError):
                g.readback(bad)
            library.assert_not_called()

    def configure_probe(self, fail_at=None, error=errno.EBADF, code=-1):
        recorded = []
        for i, (_, name, _) in enumerate(g.CASES):
            def call(*args, i=i, name=name):
                recorded.append((name, args))
                ctypes.set_errno(error if i == fail_at else errno.EPERM)
                return code if i == fail_at else -1
            getattr(self.library, name).side_effect = call
        return recorded

    def test_six_mock_probes_exact_invalid_targets(self):
        g._ACTIVE = guard()
        recorded = self.configure_probe()
        with self.context((3,)):
            proof = g.probe()
        self.assertTrue(proof['all_denied'])
        self.assertEqual(proof['status'], 'PASS_FIXED_INVALID_TARGET_DENIALS')
        self.assertEqual([x['case_id'] for x in proof['checks']], [x[0] for x in g.CASES])
        self.assertEqual(recorded, [('setns', (-1, 0)), ('unshare', (-2147483648,)),
            ('fallocate', (-1, 1, 0, 1)), ('fsetxattr', (-1, b'user.hh_inert_guard', b'I', 1, 0)),
            ('ioctl', (-1, 0x40049409, ctypes.c_ulong(-1).value)), ('connect', (-1, None, 0))])
        self.assertIs(proof['host_write_or_device_access_tested'], False)

    def test_probe_stops_first_unexpected_errno_or_success(self):
        for at in range(6):
            for code, error in ((-1, errno.EBADF), (0, 0)):
                g._ACTIVE = guard()
                recorded = self.configure_probe(at, error, code)
                with self.subTest(at=at, code=code), self.context((3,)):
                    proof = g.probe()
                self.assertFalse(proof['all_denied'])
                self.assertEqual(proof['status'], 'REJECTED')
                self.assertEqual(len(recorded), at + 1)

    def test_probe_missing_or_other_pid_guard_never_calls_libc(self):
        for active in (None, guard(pid=999)):
            g._ACTIVE = active
            with patch.object(g.os, 'getpid', return_value=600), \
                 patch.object(g, '_libc') as library, self.assertRaises(ValueError):
                g.probe()
            library.assert_not_called()

    def test_probe_security_readback_failure_never_issues_probe(self):
        g._ACTIVE = guard()
        recorded = self.configure_probe()
        with self.context((2,)), self.assertRaises(ValueError):
            g.probe()
        self.assertEqual(recorded, [])

    def test_status_parser_rejects_duplicate_fields(self):
        with patch.object(g.ns, 'bounded_read', return_value='Seccomp: 2\nSeccomp: 2\n'), \
             self.assertRaises(ValueError):
            g._status_fields()


class InheritedNamespaceMockTests(unittest.TestCase):
    def test_pure_owner_inheritance_is_explicit_not_child_ioctl(self):
        parent, current = good_proof(), facts()
        child = g.inherit_namespace(parent, current)
        self.assertTrue(g.ns.validate(child, parent))
        self.assertEqual(child['owner_evidence'], 'OWNER_INHERITED_BY_SAME_NAMESPACE_IDENTITY')
        self.assertEqual(child['type_evidence'], 'CACHED_FROM_INITIAL_NSFS_TYPE_READBACK')
        self.assertEqual(child['current_identity_facts'], current)
        self.assertEqual(len(child['initial_owner_proof_sha256']), 64)
        self.assertNotIn('owner_evidence', parent)
        parent_post = g.inherit_namespace(child, current)
        self.assertEqual(parent_post['initial_owner_proof_sha256'], child['initial_owner_proof_sha256'])

    def test_every_namespace_identity_must_match(self):
        for name in g.ns.TYPES:
            current = facts()
            current['identities'][name]['inode'] += 1
            with self.subTest(name=name), self.assertRaises(ValueError):
                g.inherit_namespace(good_proof(), current)

    def test_missing_extra_bool_zero_and_wrong_shape_fail(self):
        for kind in ('missing', 'extra', 'bool', 'zero', 'extra_row', 'non_dict', 'pid_bool', 'overflow'):
            current = facts()
            if kind == 'missing':
                del current['identities']['net']
            elif kind == 'extra':
                current['identities']['other'] = {'dev': 4, 'inode': 10}
            elif kind in ('bool', 'zero', 'overflow'):
                current['identities']['net']['inode'] = {'bool': True, 'zero': 0, 'overflow': 2**64}[kind]
            elif kind == 'extra_row':
                current['identities']['net']['type'] = 1
            elif kind == 'non_dict':
                current['identities']['net'] = None
            else:
                current['pid'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                g.inherit_namespace(good_proof(), current)

    def test_rejected_parent_or_current_security_never_passes(self):
        parent = good_proof()
        parent['status'] = 'UNKNOWN'
        with self.assertRaises(ValueError):
            g.inherit_namespace(parent, facts())
        for key, value in (('NoNewPrivs', '0'), ('Seccomp', '0'), ('CapEff', '1'),
                           ('network_interfaces', ['lo', 'eth0']), ('uid_map', '0 0 4294967295')):
            current = facts()
            current[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                g.inherit_namespace(good_proof(), current)

    def test_malformed_parent_metadata_and_changed_id_map_rejected(self):
        for key, value in (('uid_map', None), ('gid_map', True), ('Seccomp', 2),
                           ('uid_map', '2000 2000 1'), ('network_interfaces', ('lo',))):
            current = facts()
            current[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                g.inherit_namespace(good_proof(), current)
        for kind in ('none_owner', 'bool_owner', 'extra_owner', 'bad_initial_hash', 'bad_label'):
            parent = good_proof()
            if kind == 'none_owner':
                parent['owner_userns'] = None
            elif kind == 'bool_owner':
                parent['namespaces']['user']['dev'] = 1
                parent['owner_userns']['net']['dev'] = True
                parent['owner_userns']['ipc']['dev'] = True
            elif kind == 'extra_owner':
                parent['owner_userns']['other'] = parent['owner_userns']['net'].copy()
            else:
                parent = g.inherit_namespace(parent, facts())
                parent['initial_owner_proof_sha256' if kind == 'bad_initial_hash' else 'owner_evidence'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                g.inherit_namespace(parent, facts())

    def test_mock_stat_text_producer_never_opens_namespace_or_ioctl(self):
        parent = good_proof()
        calls = []
        def stat(path):
            calls.append(path)
            row = parent['namespaces'][path.rsplit('/', 1)[1]]
            return SimpleNamespace(st_dev=row['dev'], st_ino=row['inode'])
        def read(path, cap=4096):
            return {'/proc/self/uid_map': parent['uid_map'], '/proc/self/gid_map': parent['gid_map'],
                    '/proc/net/dev': 'header\nheader\nlo: 0\n'}[path]
        with patch.object(g.os, 'stat', side_effect=stat), patch.object(g.os, 'getpid', return_value=601), \
             patch.object(g.ns, 'bounded_read', side_effect=read), \
             patch.object(g, '_status_fields', return_value={k: parent[k] for k in ('CapEff','NoNewPrivs','Seccomp')}), \
             patch.object(g.ns.fcntl, 'ioctl', side_effect=AssertionError('no child ioctl')), \
             patch.object(g.os, 'open', side_effect=AssertionError('no child namespace FD')):
            child = g.collect_inherited_namespace(parent)
        self.assertTrue(g.ns.validate(child))
        self.assertEqual(calls, ['/proc/self/ns/' + name for name in g.ns.TYPES])

    def test_readback_failure_raises_before_proof(self):
        with patch.object(g.os, 'stat', side_effect=PermissionError('inert denied')), \
             self.assertRaises(PermissionError):
            g.collect_inherited_namespace(good_proof())


if __name__ == '__main__':
    unittest.main()
