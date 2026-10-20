"""Synthetic-only independent mount-policy regression; no host mount reads."""
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

_HERE = Path(__file__).resolve().parent
_MODULE = _HERE.parent / 'mount_attestation.py'
if not _MODULE.is_file():
    _MODULE = _HERE / 'mount_attestation.py'
_SPEC = importlib.util.spec_from_file_location('mount_attestation_under_test', _MODULE)
m = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(m)


def line(i=1, parent=1, path='/', flags='ro', filesystem='ext4',
         superflags='rw', root='/', source='/dev/synthetic', dev='8:1', optional=''):
    return ('%s %s %s %s %s %s%s - %s %s %s\n' %
            (i, parent, dev, root, path, flags,
             (' ' + optional) if optional else '', filesystem, source, superflags)).encode()


def private_rows():
    return (line(2, path='/tmp', flags='rw,nosuid,nodev,noexec', filesystem='tmpfs',
                 source='tmpfs', dev='0:2') +
            line(3, path='/var/tmp', flags='rw,nosuid,nodev,noexec', filesystem='tmpfs',
                 source='tmpfs', dev='0:3'))


def valid():
    return line() + private_rows()


class MountAttestationTests(unittest.TestCase):
    def assert_bad(self, raw, code):
        with self.assertRaisesRegex(m.MountInfoError, code):
            m.parse_mountinfo(raw)
        receipt = m.inventory(raw, '/review/repo')
        self.assertEqual(receipt['status'], 'FAIL')
        self.assertIn(code, receipt['parse_error'])

    def test_faithful_fields_and_optional_tags(self):
        row = m.parse_mountinfo(line(optional='shared:10 master:3'))[0]
        self.assertEqual(row, {'id': 1, 'parent': 1, 'dev': '8:1', 'root': '/',
                              'path': '/', 'mount_options': ['ro'],
                              'optional': ['shared:10', 'master:3'],
                              'filesystem_type': 'ext4', 'source': '/dev/synthetic',
                              'superblock_options': ['rw']})

    def test_documented_escapes_decode_exactly_once(self):
        row = m.parse_mountinfo(line(path=r'/a\040b\011c\012d\134040',
                                    root=r'/root\040x', source=r'/source\134x'))[0]
        self.assertEqual(row['path'], '/a b\tc\nd\\040')
        self.assertEqual(row['root'], '/root x')
        self.assertEqual(row['source'], '/source\\x')

    def test_undocumented_and_incomplete_escapes_rejected(self):
        for value in (r'/a\000', r'/a\123', r'/a\04', '/a\\', r'/a\xyz'):
            with self.subTest(value=value):
                self.assert_bad(line(path=value), 'MOUNTINFO_MALFORMED_ESCAPE')

    def test_separators_and_field_counts(self):
        for raw in (b'1 1 0:1 / / ro ext4 none rw\n',
                    b'1 1 0:1 / / ro - ext4 none rw excess\n',
                    b'1  1 0:1 / / ro - ext4 none rw\n',
                    b'1 1 0:1 / / ro - ext4 none rw -\n'):
            with self.subTest(raw=raw):
                self.assert_bad(raw, 'MOUNTINFO_FIELD_')

    def test_literal_dash_source_is_not_a_second_separator(self):
        self.assertEqual(m.parse_mountinfo(line(source='-'))[0]['source'], '-')

    def test_invalid_raw_encoding_and_controls(self):
        self.assert_bad(b'', 'MOUNTINFO_INVALID_CONTROL_OR_EMPTY')
        self.assert_bad(line(path='/x\t'), 'MOUNTINFO_INVALID_CONTROL_OR_EMPTY')
        self.assert_bad(line(path='/x\r'), 'MOUNTINFO_INVALID_CONTROL_OR_EMPTY')
        self.assert_bad(line().replace(b'/dev/synthetic', b'\xff'), 'MOUNTINFO_INVALID_UTF8')

    def test_nonbytes_inventory_fails_closed_without_raising(self):
        self.assertEqual(m.inventory('not bytes', '/review/repo')['parse_error'], 'MOUNTINFO_BYTES_REQUIRED')

    def test_duplicate_ids_and_stacked_mountpoint_ambiguity(self):
        self.assert_bad(line() + line(path='/other'), 'MOUNTINFO_DUPLICATE_ID')
        self.assert_bad(line() + line(2), 'MOUNTINFO_AMBIGUOUS_MOUNTPOINT')

    def test_noncanonical_paths(self):
        for value in ('relative', '//root', '/a/../b', '/a/.', '/a//b', '/a/'):
            with self.subTest(value=value):
                self.assert_bad(line(path=value), 'MOUNTINFO_NONCANONICAL_PATH')

    def test_ids_devices_and_filesystem_type(self):
        for value in ('0', '-1', '01', '4294967296', 'a'):
            with self.subTest(value=value):
                self.assert_bad(line(i=value), 'MOUNTINFO_INVALID_ID')
        for value in ('-1:1', '01:1', '0:a', '0:4294967296'):
            with self.subTest(value=value):
                self.assert_bad(line(dev=value), 'MOUNTINFO_INVALID_DEVICE')
        self.assert_bad(line(filesystem='bad/type'), 'MOUNTINFO_INVALID_FILESYSTEM_TYPE')

    def test_ro_rw_conflicts_duplicate_option_keys(self):
        for value in ('rw,ro', 'ro,ro', 'ro,size=1,size=2', 'nosuid', 'ro,'):
            with self.subTest(value=value):
                self.assert_bad(line(flags=value), 'MOUNTINFO_')
                self.assert_bad(line(superflags=value), 'MOUNTINFO_')

    def test_readonly_bind_with_rw_backing_superblock_is_valid(self):
        result = m.inventory(valid(), '/review/repo')
        self.assertEqual(result['status'], 'PASS_POLICY_PREREQUISITES_ONLY')
        self.assertEqual(result['rows'][0]['mount_options'], ['ro'])
        self.assertEqual(result['rows'][0]['superblock_options'], ['rw'])
        self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_pseudo_roots_are_classification_never_rw_permission(self):
        for path, filesystem in m.PSEUDO_ROOTS.items():
            with self.subTest(path=path):
                raw = valid() + line(4, path=path, filesystem=filesystem, source=filesystem, dev='0:4')
                result = m.inventory(raw, '/review/repo')
                self.assertEqual(result['status'], 'PASS_POLICY_PREREQUISITES_ONLY')
                self.assertEqual(result['rows'][-1]['class'], 'kernel_pseudo_filesystem')
                result = m.inventory(raw.replace((path + ' ro').encode(), (path + ' rw').encode()), '/review/repo')
                self.assertEqual(result['status'], 'FAIL')
                self.assertIn('UNACCOUNTED_WRITABLE_MOUNT_ID:4', result['violations'])

    def test_pseudo_descendants_have_no_broad_allowlist(self):
        for path in ('/dev/anything', '/proc/other', '/sys/other'):
            with self.subTest(path=path):
                receipt = m.inventory(valid() + line(4, path=path, flags='rw',
                                                     filesystem='tmpfs', source='tmpfs', dev='0:4'), '/review/repo')
                self.assertEqual(receipt['rows'][-1]['class'], 'unknown_mount')
                self.assertIn('UNACCOUNTED_WRITABLE_MOUNT_ID:4', receipt['violations'])

    def test_pseudo_type_spoof_is_not_pseudo_root(self):
        receipt = m.inventory(valid() + line(4, path='/proc', flags='rw', filesystem='ext4'), '/review/repo')
        self.assertEqual(receipt['rows'][-1]['class'], 'persistent_mount')
        self.assertEqual(receipt['status'], 'FAIL')

    def test_persistent_and_source_writable_are_rejected(self):
        for path, kind in (('/output', 'persistent_mount'), ('/review/repo', 'source_mount'),
                           ('/review/repo/data', 'source_mount')):
            with self.subTest(path=path):
                result = m.inventory(valid() + line(4, path=path, flags='rw'), '/review/repo')
                self.assertEqual(result['rows'][-1]['class'], kind)
                self.assertEqual(result['status'], 'FAIL')

    def test_missing_private_mounts_and_custom_private_allowlist(self):
        self.assertIn('EXACT_PRIVATE_TMPFS_REQUIRED:/tmp', m.inventory(line(), '/review/repo')['violations'])
        result = m.inventory(valid(), '/review/repo', private_paths=('/tmp', '/var/tmp', '/output'))
        self.assertEqual(result['violations'], ['MOUNT_POLICY_FIXED_PRIVATE_PATHS_REQUIRED'])

    def test_private_mount_identity_and_flags_are_not_trusted_by_name(self):
        mutations = ({'filesystem': 'ext4'}, {'source': 'not_tmpfs'}, {'root': '/subdir'},
                     {'dev': '8:5'}, {'flags': 'rw,nodev,nosuid'}, {'superflags': 'ro'})
        for change in mutations:
            with self.subTest(change=change):
                kwargs = dict(i=2, path='/tmp', flags='rw,nosuid,nodev,noexec',
                              filesystem='tmpfs', source='tmpfs', dev='0:2')
                kwargs.update(change)
                raw = line() + line(**kwargs) + private_rows().splitlines(keepends=True)[1]
                self.assertIn('PRIVATE_TMPFS_IDENTITY_OR_FLAGS:/tmp', m.inventory(raw, '/review/repo')['violations'])

    def test_source_and_path_valued_options_redacted_in_safe_projection(self):
        secret = '/home/private/example'
        raw = valid() + line(4, path=secret, source=secret,
                             filesystem='overlay', superflags='rw,lowerdir=' + secret)
        result = m.inventory(raw, '/review/repo')
        self.assertNotIn(secret, json.dumps(result))
        self.assertIn(secret, m.parse_mountinfo(raw)[-1]['source'])

    def test_raw_bounds_and_row_bounds_reject_without_truncation_success(self):
        self.assert_bad(b'x' * (m.MAX_RAW_BYTES + 1), 'MOUNTINFO_READ_BOUND_EXCEEDED')
        rows = b''.join(line(i=i + 1, path='/p' + str(i)) for i in range(m.MAX_ROWS + 1))
        self.assertLessEqual(len(rows), m.MAX_RAW_BYTES)
        self.assert_bad(rows, 'MOUNTINFO_ROW_BOUND_EXCEEDED')

    def test_projection_overflow_is_explicit_fail_closed(self):
        raw = valid() + b''.join(line(i=4 + i, path='/p' + str(i)) for i in range(100))
        self.assertLessEqual(len(raw), m.MAX_RAW_BYTES)
        result = m.inventory(raw, '/review/repo')
        self.assertEqual(result['violations'], ['MOUNTINFO_PROJECTION_BOUND_EXCEEDED'])
        self.assertEqual(result['rows'], [])
        self.assertLessEqual(len(json.dumps(result).encode()), m.MAX_PROJECTION_BYTES)

    def test_bounded_reader_uses_single_bounded_read_no_host_file(self):
        stream = io.BytesIO(b'a' * (m.MAX_RAW_BYTES + 10))
        with mock.patch.object(Path, 'open', return_value=stream) as opened:
            result = m.read_bounded(Path('/synthetic/mountinfo'))
        opened.assert_called_once_with('rb')
        self.assertEqual(result, b'a' * m.MAX_RAW_BYTES + m.OVERFLOW_MARKER)
        self.assertEqual(m.inventory(result, '/review/repo')['parse_error'], 'MOUNTINFO_READ_BOUND_EXCEEDED')

    def test_raw_emission_precedes_parse_even_for_malformed_input(self):
        raw = b'bad mount data\n'
        records = []
        with mock.patch.object(m, 'parse_mountinfo', side_effect=AssertionError('NO_PARSE_BEFORE_RAW')):
            metadata = m.emit_evidence(raw, 'stage-pre', records.append)
        self.assertEqual(records[0]['kind'], 'PRIVATE_MOUNTINFO_RAW')
        self.assertEqual(base64.b64decode(records[0]['base64']), raw)
        self.assertEqual(metadata['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(records[-1]['kind'], 'MOUNTINFO_CAPTURE_SAFE_METADATA')
        self.assertTrue(metadata['complete'])
        self.assertEqual(m.inventory(raw, '/review/repo')['status'], 'FAIL')

    def test_chunked_raw_roundtrip_hash_and_record_bounds(self):
        raw = b'x' * m.MAX_RAW_BYTES
        records = []
        metadata = m.emit_evidence(raw, 'stage-post', records.append)
        chunks = records[:-1]
        self.assertEqual(len(chunks), 16)
        self.assertEqual(b''.join(base64.b64decode(x['base64']) for x in chunks), raw)
        self.assertEqual(metadata['raw_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertTrue(all(len(json.dumps(x).encode()) < 2048 for x in records))

    def test_overflow_raw_receipt_marks_incomplete(self):
        records = []
        raw = b'x' * m.MAX_RAW_BYTES + m.OVERFLOW_MARKER
        metadata = m.emit_evidence(raw, 'stage-pre', records.append)
        self.assertFalse(metadata['complete'])
        self.assertTrue(all(not x['complete'] for x in records))
        self.assertEqual(m.inventory(raw, '/review/repo')['status'], 'FAIL')

    def test_stage_label_and_repo_cannot_change_policy_or_inject_records(self):
        for value in ('bad\nstage', '', 'x' * 65):
            with self.subTest(value=value), self.assertRaises(m.MountInfoError):
                m.emit_evidence(valid(), value, lambda value: self.fail('unexpected emission'))
        self.assertEqual(m.inventory(valid(), '../repo')['violations'], ['MOUNT_POLICY_CANONICAL_REPO_REQUIRED'])


if __name__ == '__main__':
    unittest.main()
