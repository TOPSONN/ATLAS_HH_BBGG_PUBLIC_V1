"""Read-only namespace proof for a proposed diagnostic, never authorization.

No probes run on import. NS_GET_* ioctls query existing nsfs descriptors only;
no namespace creation, setns, network traffic or IPC allocation is performed.
Current task permits mock tests only: collect() is not dispatched in this task.
"""
from __future__ import annotations
import fcntl, os, platform
from pathlib import Path

NS_GET_USERNS = 0xB701
NS_GET_NSTYPE = 0xB703
TYPES = {'user': 0x10000000, 'mnt': 0x00020000, 'net': 0x40000000,
         'ipc': 0x08000000, 'pid': 0x20000000}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def bounded_read(path, cap=4096):
    with Path(path).open('rb') as stream:
        value = stream.read(cap + 1)
    require(len(value) <= cap, 'NAMESPACE_READBACK_BOUND')
    return value.decode('ascii', errors='strict')


def identity(fd):
    info = os.fstat(fd)
    return {'dev': info.st_dev, 'inode': info.st_ino}


def parse_id_map(text):
    rows = []
    for line in text.splitlines():
        fields = line.split()
        require(len(fields) == 3 and all(x.isdecimal() and x.isascii() for x in fields),
                'INVALID_ID_MAPPING')
        row = [int(x) for x in fields]
        require(row[2] > 0 and all(x <= 0xFFFFFFFF for x in row) and
                row[0] + row[2] <= 0xFFFFFFFF and row[1] + row[2] <= 0xFFFFFFFF,
                'INVALID_ID_MAPPING_RANGE')
        rows.append(row)
    require(1 <= len(rows) <= 8, 'ID_MAP_ROW_BOUND')
    for column in (0, 1):
        ranges = sorted((r[column], r[column] + r[2]) for r in rows)
        require(all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])), 'OVERLAPPING_ID_MAP')
    return rows


def _validate_fields(proof, parent=None):
    require(type(proof) is dict and proof.get('readback_complete') is True,
            'NAMESPACE_READBACK_UNKNOWN')
    ns = proof['namespaces']
    require(set(ns) == set(TYPES), 'EXACT_NAMESPACE_SET_REQUIRED')
    for name, expected in TYPES.items():
        row = ns[name]
        require(type(row.get('type')) is int and row.get('type') == expected and type(row.get('inode')) is int and
                row['inode'] > 0 and type(row.get('dev')) is int and row['dev'] > 0,
                'NSFS_TYPE_OR_IDENTITY_MISMATCH:' + name)
    for name in ('net', 'ipc'):
        require(proof['owner_userns'].get(name) == {k: ns['user'][k] for k in ('dev', 'inode')},
                'NAMESPACE_OWNED_BY_DIFFERENT_USERNS:' + name)
    for name in ('uid_map', 'gid_map'):
        rows = parse_id_map(proof[name])
        require(sum(r[2] for r in rows) < 0xFFFFFFFF, 'INITIAL_OR_FULL_ID_MAP_FORBIDDEN')
    require(proof['CapEff'] == '0000000000000000' and proof['NoNewPrivs'] == '1',
            'CAPABILITY_OR_NNP_MISMATCH')
    require(proof['Seccomp'] == '2', 'SYSTEMD_NAMESPACE_FILTER_NOT_OBSERVED')
    require(proof['network_interfaces'] == ['lo'], 'UNEXPECTED_NETWORK_INTERFACE')
    if parent is not None:
        validate(parent)
        require(ns == parent['namespaces'], 'CHILD_NAMESPACE_IDENTITY_CHANGED')
        require(proof['owner_userns'] == parent['owner_userns'], 'CHILD_NAMESPACE_OWNER_CHANGED')
    return True


def validate(proof, parent=None):
    require(type(proof) is dict and proof.get('schema') == 'PHASE7I_NSFS_READBACK_V1' and
            proof.get('status') == 'PASS_READONLY_NAMESPACE_IDENTITY' and
            not any(k in proof for k in ('reason', 'error', 'close_errors')),
            'NAMESPACE_READBACK_UNKNOWN_OR_REJECTED')
    return _validate_fields(proof, parent)


def collect():
    """Future authorized service only. Denied/missing readback stays UNKNOWN."""
    proof = {'schema': 'PHASE7I_NSFS_READBACK_V1', 'readback_complete': False,
             'status': 'UNKNOWN', 'namespaces': {}, 'owner_userns': {}}
    opened = []
    try:
        require(platform.machine() == 'x86_64', 'UNREVIEWED_NSFS_IOCTL_ARCHITECTURE')
        for name, expected in TYPES.items():
            fd = os.open('/proc/self/ns/' + name, os.O_RDONLY | os.O_CLOEXEC)
            opened.append(fd)
            proof['namespaces'][name] = {**identity(fd), 'type': fcntl.ioctl(fd, NS_GET_NSTYPE)}
            require(proof['namespaces'][name]['type'] == expected, 'NSFS_TYPE_MISMATCH')
            if name in ('net', 'ipc'):
                owner = fcntl.ioctl(fd, NS_GET_USERNS)
                require(type(owner) is int and owner >= 0 and owner not in opened,
                        'INVALID_NAMESPACE_OWNER_DESCRIPTOR')
                opened.append(owner)
                proof['owner_userns'][name] = identity(owner)
        proof['uid_map'] = bounded_read('/proc/self/uid_map', 512)
        proof['gid_map'] = bounded_read('/proc/self/gid_map', 512)
        fields = dict(x.split(':', 1) for x in bounded_read('/proc/self/status').splitlines() if ':' in x)
        for field in ('CapEff', 'NoNewPrivs', 'Seccomp'):
            proof[field] = fields[field].strip()
        interfaces = []
        for line in bounded_read('/proc/net/dev').splitlines()[2:]:
            require(':' in line, 'INVALID_NETWORK_INTERFACE_READBACK')
            interfaces.append(line.split(':', 1)[0].strip())
        proof['network_interfaces'] = sorted(interfaces)
        proof['readback_complete'] = True
        _validate_fields(proof)
        proof['status'] = 'PASS_READONLY_NAMESPACE_IDENTITY'
    except (OSError, ValueError, KeyError, UnicodeError) as error:
        proof['status'] = 'UNKNOWN_OR_REJECTED'
        proof['readback_complete'] = False
        proof['reason'] = str(error)[:512]
    finally:
        close_errors = []
        for fd in reversed(opened):
            try:
                os.close(fd)
            except OSError as error:
                close_errors.append({'fd': fd, 'errno': error.errno})
        if close_errors:
            proof.update(status='UNKNOWN_OR_REJECTED', readback_complete=False,
                         close_errors=close_errors)
    return proof
