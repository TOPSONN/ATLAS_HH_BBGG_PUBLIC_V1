"""Pure synthetic nsfs observations; never open proc namespace or issue ioctl."""
from __future__ import annotations
import copy
from contextlib import ExitStack
import errno
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

try:
    from simulation.hh_signal.final_closure.resource_closure import namespace_attestation as ns
except ImportError:
    spec = importlib.util.spec_from_file_location('namespace_attestation',
                                                Path(__file__).with_name('namespace_attestation.py'))
    ns = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ns)


def good_proof():
    rows = {name: {'dev': 4, 'inode': 100 + i, 'type': expected}
            for i, (name, expected) in enumerate(ns.TYPES.items())}
    owner = {k: rows['user'][k] for k in ('dev', 'inode')}
    return {'schema': 'PHASE7I_NSFS_READBACK_V1',
            'status': 'PASS_READONLY_NAMESPACE_IDENTITY', 'readback_complete': True,
            'namespaces': rows, 'owner_userns': {'net': owner.copy(), 'ipc': owner.copy()},
            'uid_map': '1000 1000 1\n', 'gid_map': '1000 1000 1\n',
            'CapEff': '0000000000000000', 'NoNewPrivs': '1', 'Seccomp': '2',
            'network_interfaces': ['lo']}


class NamespaceValidationTests(unittest.TestCase):
    def test_constants_match_reviewed_linux_uapi(self):
        self.assertEqual(ns.NS_GET_USERNS, (0xB7 << 8) | 1)
        self.assertEqual(ns.NS_GET_NSTYPE, (0xB7 << 8) | 3)
        self.assertEqual(ns.TYPES,
                         {'user': 0x10000000, 'mnt': 0x20000, 'net': 0x40000000,
                          'ipc': 0x08000000, 'pid': 0x20000000})

    def test_synthetic_private_owner_pass(self):
        self.assertTrue(ns.validate(good_proof()))

    def test_status_unknown_rejected_even_complete_fields(self):
        for status in ('UNKNOWN', 'UNKNOWN_OR_REJECTED', None):
            proof = good_proof()
            proof['status'] = status
            with self.subTest(status=status), self.assertRaises((ValueError, KeyError, TypeError)):
                ns.validate(proof)

    def test_failure_reason_rejected_even_pass_status(self):
        proof = good_proof()
        proof['reason'] = 'Earlier readback failure'
        with self.assertRaises((ValueError, KeyError, TypeError)):
            ns.validate(proof)

    def test_schema_unknown_rejected(self):
        proof = good_proof()
        proof['schema'] = 'OTHER'
        with self.assertRaises((ValueError, KeyError, TypeError)):
            ns.validate(proof)

    def test_incomplete_rejected(self):
        proof = good_proof()
        proof['readback_complete'] = False
        with self.assertRaises(ValueError):
            ns.validate(proof)

    def test_exact_namespace_inventory_required(self):
        for kind in ('missing', 'extra'):
            proof = good_proof()
            if kind == 'missing':
                del proof['namespaces']['net']
            else:
                proof['namespaces']['other'] = copy.deepcopy(proof['namespaces']['net'])
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                ns.validate(proof)

    def test_type_and_identity_cannot_be_forged_by_bool_or_zero(self):
        for field, value in [('type', 0), ('type', True), ('inode', True),
                             ('inode', 0), ('dev', True), ('dev', 0)]:
            proof = good_proof()
            proof['namespaces']['net'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                ns.validate(proof)

    def test_net_or_ipc_owner_mismatch_rejected(self):
        for name in ('net', 'ipc'):
            proof = good_proof()
            proof['owner_userns'][name]['inode'] += 1
            with self.subTest(name=name), self.assertRaises(ValueError):
                ns.validate(proof)

    def test_initial_map_rejected(self):
        for name in ('uid_map', 'gid_map'):
            proof = good_proof()
            proof[name] = '0 0 4294967295\n'
            with self.subTest(name=name), self.assertRaises(ValueError):
                ns.validate(proof)

    def test_invalid_id_maps_rejected(self):
        cases = ['', '1000 1000 0', '-1 0 1', '0 0 4294967296',
                 '4294967295 0 1', '0 4294967295 1',
                 '4294967294 0 2', '0 4294967294 2',
                 '4294967295 0 2', '0 4294967295 2', '0 0 2\n1 3 1',
                 '0 0 2\n3 1 1', '0 0 1 extra', '０ 0 1',
                 '\n'.join('%d %d 1' % (i, i) for i in range(9))]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                ns.parse_id_map(text)

    def test_nonoverlapping_multiple_map_ranges_accepted(self):
        self.assertEqual(ns.parse_id_map('0 1 1\n1000 1000 1\n'),
                         [[0, 1, 1], [1000, 1000, 1]])

    def test_security_and_interfaces_rejected(self):
        for field, value in [('CapEff', '0000000000000001'), ('NoNewPrivs', '0'),
                             ('Seccomp', '0'), ('network_interfaces', ['lo', 'eth0']),
                             ('network_interfaces', [])]:
            proof = good_proof()
            proof[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                ns.validate(proof)

    def test_child_all_namespace_identities_match_parent(self):
        parent = good_proof()
        self.assertTrue(ns.validate(copy.deepcopy(parent), parent))
        for name in ns.TYPES:
            child = copy.deepcopy(parent)
            child['namespaces'][name]['inode'] += 100
            if name == 'user':
                for target in ('net', 'ipc'):
                    child['owner_userns'][target]['inode'] += 100
            with self.subTest(name=name), self.assertRaises(ValueError):
                ns.validate(child, parent)

    def test_invalid_parent_status_rejected(self):
        parent = good_proof()
        parent['status'] = 'UNKNOWN_OR_REJECTED'
        with self.assertRaises((ValueError, KeyError, TypeError)):
            ns.validate(good_proof(), parent)


class NamespaceCollectorMockTests(unittest.TestCase):
    """Every namespace FD/open/ioctl/read is patched with a finite fake."""

    def make_runtime(self, *, fail_open=None, fail_ioctl=None, invalid_owner=None,
                     fail_identity=None, fail_read=None, close_failure=None, arch='x86_64',
                     owner_mismatch=False, interfaces='lo: 0\n'):
        self.opened = []
        self.closed = []
        self.fd_kind = {}
        self.owner_fds = set()
        self.next_fd = 10

        def fake_open(path, flags):
            self.assertTrue(path.startswith('/proc/self/ns/'))
            self.assertEqual(flags, ns.os.O_RDONLY | ns.os.O_CLOEXEC)
            kind = path.rsplit('/', 1)[1]
            if kind == fail_open:
                raise PermissionError(errno.EACCES, 'inert open denied')
            fd = self.next_fd
            self.next_fd += 1
            self.opened.append(fd)
            self.fd_kind[fd] = kind
            return fd

        def fake_ioctl(fd, request):
            kind = self.fd_kind[fd]
            if (kind, request) == fail_ioctl:
                raise PermissionError(errno.EPERM, 'inert ioctl denied')
            if request == ns.NS_GET_NSTYPE:
                return ns.TYPES[kind]
            self.assertEqual(request, ns.NS_GET_USERNS)
            self.assertIn(kind, ('net', 'ipc'))
            if invalid_owner is not None:
                return invalid_owner
            owner = self.next_fd
            self.next_fd += 1
            self.fd_kind[owner] = 'user'
            self.owner_fds.add(owner)
            self.opened.append(owner)
            return owner

        def fake_stat(fd):
            if fd == fail_identity:
                raise OSError(errno.EIO, 'inert identity failure')
            kind = self.fd_kind[fd]
            inode = 100 + list(ns.TYPES).index(kind)
            if owner_mismatch and fd in self.owner_fds:
                inode += 1
            return SimpleNamespace(st_dev=4, st_ino=inode)

        def fake_read(path, cap=4096):
            if path == fail_read:
                raise PermissionError(errno.EACCES, 'inert read denied')
            values = {'/proc/self/uid_map': '1000 1000 1\n',
                      '/proc/self/gid_map': '1000 1000 1\n',
                      '/proc/self/status': 'CapEff:\t0000000000000000\nNoNewPrivs:\t1\nSeccomp:\t2\n',
                      '/proc/net/dev': 'header one\nheader two\n' + interfaces}
            self.assertIn(path, values)
            return values[path]

        def fake_close(fd):
            self.closed.append(fd)
            if fd == close_failure:
                raise OSError(errno.EIO, 'inert close failure')

        stack = ExitStack()
        for target, callback in [(ns.os, ('open', fake_open)), (ns.os, ('fstat', fake_stat)),
                                 (ns.os, ('close', fake_close)),
                                 (ns.fcntl, ('ioctl', fake_ioctl)),
                                 (ns, ('bounded_read', fake_read)),
                                 (ns.platform, ('machine', lambda: arch))]:
            stack.enter_context(patch.object(target, callback[0], side_effect=callback[1]))
        return stack

    def assert_all_closed(self):
        self.assertEqual(self.closed, list(reversed(self.opened)))

    def assert_rejected(self, proof):
        self.assertNotEqual(proof['status'], 'PASS_READONLY_NAMESPACE_IDENTITY')
        with self.assertRaises((ValueError, KeyError, TypeError)):
            ns.validate(proof)

    def test_mock_positive_closes_all_seven_fds(self):
        with self.make_runtime():
            proof = ns.collect()
        self.assertEqual(len(self.opened), 7)
        self.assert_all_closed()
        self.assertTrue(ns.validate(proof))

    def test_open_denied_rejects_and_closes_prior(self):
        for name in ns.TYPES:
            with self.subTest(name=name), self.make_runtime(fail_open=name):
                proof = ns.collect()
                self.assert_all_closed()
                self.assert_rejected(proof)

    def test_ioctl_denied_rejects_and_closes_all(self):
        calls = [(name, ns.NS_GET_NSTYPE) for name in ns.TYPES]
        calls += [(name, ns.NS_GET_USERNS) for name in ('net', 'ipc')]
        for call in calls:
            with self.subTest(call=call), self.make_runtime(fail_ioctl=call):
                proof = ns.collect()
                self.assert_all_closed()
                self.assert_rejected(proof)

    def test_owner_fstat_failure_closes_new_owner_fd(self):
        with self.make_runtime(fail_identity=13):
            proof = ns.collect()
        self.assertIn(13, self.owner_fds)
        self.assert_all_closed()
        self.assert_rejected(proof)

    def test_invalid_owner_descriptor_rejected_without_duplicate_close(self):
        for owner in (-1, True, 10):
            with self.subTest(owner=owner), self.make_runtime(invalid_owner=owner):
                proof = ns.collect()
                self.assert_all_closed()
                self.assert_rejected(proof)

    def test_read_failure_rejected_after_fd_readback(self):
        for path in ('/proc/self/uid_map', '/proc/self/gid_map', '/proc/self/status', '/proc/net/dev'):
            with self.subTest(path=path), self.make_runtime(fail_read=path):
                proof = ns.collect()
                self.assert_all_closed()
                self.assert_rejected(proof)

    def test_semantic_readback_failure_cannot_validate(self):
        with self.make_runtime(owner_mismatch=True):
            proof = ns.collect()
        self.assert_all_closed()
        self.assert_rejected(proof)

    def test_close_failure_returns_rejected_and_continues_closing(self):
        with self.make_runtime(close_failure=16):
            proof = ns.collect()
        self.assert_all_closed()
        self.assert_rejected(proof)

    def test_unknown_architecture_performs_no_open_or_ioctl(self):
        with self.make_runtime(arch='aarch64'):
            proof = ns.collect()
        self.assertEqual(self.opened, [])
        self.assert_all_closed()
        self.assert_rejected(proof)

    def test_extra_or_missing_network_interface_rejected(self):
        for text in ('lo: 0\neth0: 0\n', ''):
            with self.subTest(text=text), self.make_runtime(interfaces=text):
                proof = ns.collect()
                self.assert_all_closed()
                self.assert_rejected(proof)


if __name__ == '__main__':
    unittest.main()
