"""Bounded mountinfo evidence and conservative, non-authorizing mount policy.

This module performs no namespace operation, service activation or write probe.
``emit_evidence`` emits the private captured bytes before parsing.  Callers must
then emit ``inventory`` and only afterwards enforce its violations.  Read-only
bind mounts may have ``rw`` superblocks; permission is per mount, not inferred
from the backing superblock.  No writable pseudo-filesystem exception exists.
"""
from __future__ import annotations

import base64
import hashlib
import json
import posixpath
import re
from pathlib import Path

MAX_RAW_BYTES = 16384
MAX_ROWS = 256
MAX_PROJECTION_BYTES = 16384
RAW_CHUNK_BYTES = 1024
OVERFLOW_MARKER = b'\nPHASE7I_MOUNTINFO_READ_OVERFLOW\n'
ESCAPES = {'040': ' ', '011': '\t', '012': '\n', '134': '\\'}
PSEUDO_ROOTS = {
    '/proc': 'proc', '/proc/sys': 'proc', '/proc/sysrq-trigger': 'proc',
    '/sys': 'sysfs', '/sys/fs/cgroup': 'cgroup2', '/dev': 'devtmpfs',
    '/dev/pts': 'devpts', '/dev/shm': 'tmpfs', '/dev/mqueue': 'mqueue',
}


class MountInfoError(ValueError):
    """A bounded evidence/format failure; never permission to continue."""


def _fail(code):
    raise MountInfoError(code)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def read_bounded(path=Path('/proc/self/mountinfo')):
    """Read at most cap+1 bytes; over-cap returns cap bytes plus a sentinel.

    A sentinel is an explicit *incomplete* capture, never a valid mount table.
    No stat or second read races with the single bounded stream read.
    """
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_RAW_BYTES + 1)
    if len(raw) > MAX_RAW_BYTES:
        return raw[:MAX_RAW_BYTES] + OVERFLOW_MARKER
    return raw


def _capture(raw):
    if not isinstance(raw, bytes):
        _fail('MOUNTINFO_BYTES_REQUIRED')
    complete = len(raw) <= MAX_RAW_BYTES and OVERFLOW_MARKER not in raw
    retained = raw[:MAX_RAW_BYTES]
    return retained, complete


def _decode_field(value):
    result = []
    index = 0
    while index < len(value):
        if value[index] != '\\':
            result.append(value[index])
            index += 1
            continue
        code = value[index + 1:index + 4]
        if len(code) != 3 or code not in ESCAPES:
            _fail('MOUNTINFO_MALFORMED_ESCAPE')
        result.append(ESCAPES[code])
        index += 4
    return ''.join(result)


def _path(value):
    decoded = _decode_field(value)
    if not decoded.startswith('/') or decoded.startswith('//') or posixpath.normpath(decoded) != decoded:
        _fail('MOUNTINFO_NONCANONICAL_PATH')
    return decoded


def _integer(value):
    if not re.fullmatch(r'[1-9][0-9]{0,9}', value) or int(value) > 2**32 - 1:
        _fail('MOUNTINFO_INVALID_ID')
    return int(value)


def _options(value):
    values = value.split(',')
    if not values or any(not x or len(x) > 1024 for x in values):
        _fail('MOUNTINFO_INVALID_OPTIONS')
    names = [x.split('=', 1)[0] for x in values]
    if len(set(names)) != len(names) or ('ro' in values) == ('rw' in values):
        _fail('MOUNTINFO_AMBIGUOUS_OPTIONS')
    return values


def parse_mountinfo(raw):
    """Return faithful parsed rows, rejecting incomplete or ambiguous input.

    Row keys: id, parent, dev, root, path, mount_options, optional,
    filesystem_type, source, superblock_options.  Unknown optional tags remain
    data.  Root/path/source escapes are decoded exactly once.
    """
    retained, complete = _capture(raw)
    if not complete:
        _fail('MOUNTINFO_READ_BOUND_EXCEEDED')
    try:
        text = retained.decode('utf-8', 'strict')
    except UnicodeDecodeError:
        _fail('MOUNTINFO_INVALID_UTF8')
    if not text or any(ord(x) < 32 and x != '\n' for x in text) or '\x7f' in text:
        _fail('MOUNTINFO_INVALID_CONTROL_OR_EMPTY')
    lines = text.split('\n')
    if lines[-1] == '':
        lines.pop()
    if not lines or len(lines) > MAX_ROWS:
        _fail('MOUNTINFO_ROW_BOUND_EXCEEDED')
    rows = []
    ids, paths = set(), set()
    for line in lines:
        fields = line.split(' ')
        if any(not x for x in fields) or '-' not in fields[6:]:
            _fail('MOUNTINFO_FIELD_SEPARATOR')
        # The grammar separator follows the six fixed fields. A later '-'
        # may legitimately be the mount-source token, not another separator.
        separator = fields.index('-', 6)
        if separator < 6 or len(fields) != separator + 4:
            _fail('MOUNTINFO_FIELD_COUNT')
        mount_id, parent = _integer(fields[0]), _integer(fields[1])
        if not re.fullmatch(r'(0|[1-9][0-9]{0,9}):(0|[1-9][0-9]{0,9})', fields[2]):
            _fail('MOUNTINFO_INVALID_DEVICE')
        if any(int(x) > 2**32 - 1 for x in fields[2].split(':')):
            _fail('MOUNTINFO_INVALID_DEVICE')
        root, path = _path(fields[3]), _path(fields[4])
        if mount_id in ids:
            _fail('MOUNTINFO_DUPLICATE_ID')
        if path in paths:
            _fail('MOUNTINFO_AMBIGUOUS_MOUNTPOINT')
        ids.add(mount_id)
        paths.add(path)
        filesystem = fields[separator + 1]
        if not re.fullmatch(r'[A-Za-z0-9_.+-]{1,64}', filesystem):
            _fail('MOUNTINFO_INVALID_FILESYSTEM_TYPE')
        optional = fields[6:separator]
        if len(optional) != len(set(optional)) or any(len(x) > 128 for x in optional):
            _fail('MOUNTINFO_INVALID_OPTIONAL_FIELDS')
        rows.append({'id': mount_id, 'parent': parent, 'dev': fields[2],
                     'root': root, 'path': path, 'mount_options': _options(fields[5]),
                     'optional': optional, 'filesystem_type': filesystem,
                     'source': _decode_field(fields[separator + 2]),
                     'superblock_options': _options(fields[separator + 3])})
    return rows


def _classification(row, repo, private_paths):
    if row['path'] in private_paths:
        return 'private_tmpfs'
    if row['path'] == repo or row['path'].startswith(repo.rstrip('/') + '/'):
        return 'source_mount'
    if PSEUDO_ROOTS.get(row['path']) == row['filesystem_type']:
        return 'kernel_pseudo_filesystem'
    if row['filesystem_type'] in ('ext2', 'ext3', 'ext4', 'xfs', 'btrfs', 'fuseblk', '9p', 'drvfs', 'ntfs', 'ntfs3'):
        return 'persistent_mount'
    return 'unknown_mount'


def _safe_options(values):
    # Path-valued overlay/volume options belong only in PRIVATE raw evidence.
    flags = {'ro', 'rw', 'nosuid', 'nodev', 'noexec', 'relatime', 'noatime',
             'strictatime', 'sync', 'dirsync', 'lazytime', 'seclabel',
             'nosymfollow', 'remount', 'mand', 'nomand', 'iversion'}
    return [value if value in flags or re.fullmatch(
        r'(size|nr_inodes|mode|uid|gid|fmask|dmask|inode64|errors|data)=[0-9A-Za-z._-]{1,32}', value)
        else 'sha256:' + _sha(value.encode()) for value in values]


def inventory(raw, repo, private_paths=('/tmp', '/var/tmp')):
    """Return a safe bounded projection and violations; never policy-raise.

    This is classification plus a conservative prerequisite check.  A PASS
    does not prove capacity, network, IPC, cleanup or the full launch envelope.
    Exact private tmpfs capacities/inodes still require caller statvfs checks.
    Unknown/persistent rw and every rw pseudo-filesystem fail closed.
    """
    if not isinstance(raw, bytes):
        return {'schema': 'PHASE7I_MOUNT_SAFE_PROJECTION_V1', 'status': 'FAIL',
                'complete': False, 'parse_error': 'MOUNTINFO_BYTES_REQUIRED',
                'rows': [], 'violations': ['MOUNTINFO_BYTES_REQUIRED'],
                'FULL_LAUNCH_ENVELOPE_VERIFIED': False}
    retained, complete = _capture(raw)
    result = {'schema': 'PHASE7I_MOUNT_SAFE_PROJECTION_V1',
              'raw_sha256': _sha(retained), 'raw_bytes': len(retained),
              'complete': complete, 'status': 'FAIL', 'parse_error': None,
              'rows': [], 'violations': [],
              'private_capacity_readback': 'REQUIRED_SEPARATE_STATVFS',
              'FULL_LAUNCH_ENVELOPE_VERIFIED': False}
    try:
        rows = parse_mountinfo(raw)
    except MountInfoError as error:
        result['parse_error'] = str(error)
        result['violations'] = [str(error)]
        return result
    repo = str(repo)
    if not repo.startswith('/') or posixpath.normpath(repo) != repo or repo.startswith('//'):
        result['violations'] = ['MOUNT_POLICY_CANONICAL_REPO_REQUIRED']
        return result
    if tuple(private_paths) != ('/tmp', '/var/tmp'):
        result['violations'] = ['MOUNT_POLICY_FIXED_PRIVATE_PATHS_REQUIRED']
        return result
    seen_private = set()
    violations = []
    for row in rows:
        kind = _classification(row, repo, private_paths)
        writable = 'rw' in row['mount_options']
        if kind == 'private_tmpfs':
            seen_private.add(row['path'])
            if (row['filesystem_type'] != 'tmpfs' or row['root'] != '/' or row['source'] != 'tmpfs'
                    or not row['dev'].startswith('0:')
                    or not {'rw', 'nodev', 'nosuid', 'noexec'} <= set(row['mount_options'])
                    or 'rw' not in row['superblock_options']):
                violations.append('PRIVATE_TMPFS_IDENTITY_OR_FLAGS:' + row['path'])
        elif writable:
            violations.append('UNACCOUNTED_WRITABLE_MOUNT_ID:' + str(row['id']))
        shown_path = row['path'] if row['path'] in PSEUDO_ROOTS or row['path'] in private_paths else 'sha256:' + _sha(row['path'].encode())
        result['rows'].append({'id': row['id'], 'parent': row['parent'], 'dev': row['dev'],
                               'mountpoint': shown_path, 'filesystem_type': row['filesystem_type'],
                               'mount_options': _safe_options(row['mount_options']),
                               'superblock_options': _safe_options(row['superblock_options']), 'class': kind})
    for path in private_paths:
        if path not in seen_private:
            violations.append('EXACT_PRIVATE_TMPFS_REQUIRED:' + path)
    result['violations'] = violations
    result['status'] = 'PASS_POLICY_PREREQUISITES_ONLY' if not violations else 'FAIL'
    if len(_canonical(result)) > MAX_PROJECTION_BYTES:
        result['status'] = 'FAIL'
        result['rows_total'] = len(rows)
        result['rows'] = []
        result['violations'] = ['MOUNTINFO_PROJECTION_BOUND_EXCEEDED']
    return result


def emit_evidence(raw, stage, emit):
    """Emit private captured bytes first; return/emit non-parsing metadata.

    Each chunk includes SHA256 and capture completeness.  The caller must keep
    PRIVATE_MOUNTINFO_RAW records local and publish only reviewed inventory
    projection and hashes.  This function deliberately does not parse/guard.
    """
    retained, complete = _capture(raw)
    if not isinstance(stage, str) or len(stage) > 64 or not re.fullmatch(r'[A-Za-z0-9_-]+', stage):
        _fail('MOUNTINFO_STAGE_LABEL_REQUIRED')
    count = max(1, (len(retained) + RAW_CHUNK_BYTES - 1) // RAW_CHUNK_BYTES)
    metadata = {'kind': 'MOUNTINFO_CAPTURE_SAFE_METADATA', 'stage': stage,
                'raw_sha256': _sha(retained), 'raw_bytes': len(retained),
                'complete': complete, 'chunks': count}
    for index in range(count):
        chunk = retained[index * RAW_CHUNK_BYTES:(index + 1) * RAW_CHUNK_BYTES]
        emit({'kind': 'PRIVATE_MOUNTINFO_RAW', 'stage': stage,
              'raw_sha256': metadata['raw_sha256'], 'raw_bytes': len(retained),
              'complete': complete, 'chunk_index': index, 'chunks': count,
              'base64': base64.b64encode(chunk).decode('ascii')})
    emit(metadata)
    return metadata
