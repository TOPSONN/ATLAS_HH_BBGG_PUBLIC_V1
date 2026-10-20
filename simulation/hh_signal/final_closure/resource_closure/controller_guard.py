"""Reviewed-source proposal for a future S4 volatile diagnostic only.

No import installs a filter, reads proc or executes probes. Actual calls require
separate kernel/service authorization. This default-ALLOW x86_64 filter is not
a syscall allowlist, disk quota, compiler compatibility claim or physics gate.
The six probes use invalid FDs/flags and cannot target a host file/device.
Owner ioctls must occur BEFORE installation; ALL ioctl calls are then denied.
S4 has null stdin and pipes, needs no TTY or human approval input. Denying all
ioctl avoids treating driver-local request numbers as globally safe queries.

Primary ABI references: Linux v6.6 seccomp_filter documentation; x86
unistd_64.h; include/uapi/linux/{seccomp,sched,nsfs}.h. PR_SET_SECCOMP uses
classic BPF seccomp_data offsets: nr=0,arch=4,args[0]=16,args[1]=24.
"""
from __future__ import annotations
import copy
import ctypes
import errno
import hashlib
import json
import os
import platform
from . import allocation_guard as historical
from . import namespace_attestation as ns

SCOPE = 'VOLATILE_DIAGNOSTIC_ONLY'
AUDIT_ARCH_X86_64 = 0xC000003E
X32_SYSCALL_BIT = 0x40000000
KILL = 0x80000000
ALLOW = 0x7FFF0000
EPERM = 0x00050001
NEW_NAMESPACE_FLAGS = 0x7E020000
DENIED = {**historical.DENIED, 'socket': 41, 'connect': 42, 'accept': 43,
          'sendto': 44, 'recvfrom': 45, 'sendmsg': 46, 'recvmsg': 47,
          'shutdown': 48, 'bind': 49, 'listen': 50, 'getsockname': 51,
          'getpeername': 52, 'socketpair': 53, 'setsockopt': 54,
          'getsockopt': 55, 'unshare': 272, 'accept4': 288,
          'recvmmsg': 299, 'setns': 308, 'sendmmsg': 307, 'clone3': 435}
CASES = (
    ('setns_invalid_fd_denied', 'setns', 'INVALID_FD'),
    ('unshare_invalid_flags_denied', 'unshare', 'INVALID_FLAGS'),
    ('fallocate_invalid_fd_denied', 'fallocate', 'INVALID_FD'),
    ('fsetxattr_invalid_fd_denied', 'fsetxattr', 'INVALID_FD'),
    ('ioctl_clone_invalid_fd_denied', 'ioctl', 'INVALID_FD'),
    ('connect_invalid_fd_denied', 'connect', 'INVALID_FD'),
)
_ACTIVE = None


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= (2**63 - 1)


def program():
    """Pure rows. Deny clone3; ordinary clone allowed, namespace flags denied.

    Denying clone3 is deliberate and can break libc/compiler subprocess paths;
    no formal builder support is asserted. x32/wrong architecture are killed.
    """
    LD, JEQ, JSET, RET = 0x20, 0x15, 0x45, 0x06
    rows = [(LD, 0, 0, 4), (JEQ, 1, 0, AUDIT_ARCH_X86_64),
            (RET, 0, 0, KILL), (LD, 0, 0, 0),
            (JSET, 0, 1, X32_SYSCALL_BIT), (RET, 0, 0, KILL)]
    for number in sorted(set(DENIED.values())):
        rows.extend(((JEQ, 0, 1, number), (RET, 0, 0, EPERM)))
    # clone flags are unsigned long; reject high bits as well as NEW* flags.
    rows.extend(((JEQ, 0, 8, 56), (LD, 0, 0, 20), (JEQ, 1, 0, 0),
                 (RET, 0, 0, EPERM), (LD, 0, 0, 16),
                 (JSET, 0, 1, NEW_NAMESPACE_FLAGS), (RET, 0, 0, EPERM),
                 (RET, 0, 0, ALLOW), (RET, 0, 0, ALLOW)))
    # Restore syscall nr after clone comparison; all non-clone paths jump here.
    rows.append((LD, 0, 0, 0))
    rows.extend(((JEQ, 0, 1, 16), (RET, 0, 0, EPERM), (RET, 0, 0, ALLOW)))
    return rows


def program_identity():
    return hashlib.sha256(json.dumps(program(), separators=(',', ':')).encode()).hexdigest()


class _Filter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint32)]


class _Program(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(_Filter))]


def _libc():
    library = ctypes.CDLL(None, use_errno=True)
    library.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                             ctypes.c_ulong, ctypes.c_ulong]
    library.prctl.restype = ctypes.c_int
    return library


def _checked(value, label):
    need(type(value) is int and value >= 0, label)
    return value


def _status_fields():
    text = ns.bounded_read('/proc/self/status')
    rows = {}
    for line in text.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            need(key not in rows, 'DUPLICATE_PROC_STATUS_FIELD')
            rows[key] = value.strip()
    return rows


def _security(library):
    rows = _status_fields()
    count = rows.get('Seccomp_filters', '')
    need(count.isascii() and count.isdecimal(), 'FILTER_COUNT_READBACK_UNAVAILABLE')
    count = int(count)
    need(integer(count, 1), 'FILTER_COUNT_READBACK_RANGE')
    mode = _checked(library.prctl(21, 0, 0, 0, 0), 'PR_GET_SECCOMP_FAILED')
    nnp = _checked(library.prctl(39, 0, 0, 0, 0), 'PR_GET_NO_NEW_PRIVS_FAILED')
    need(mode == 2 and nnp == 1 and rows.get('Seccomp') == '2' and
         rows.get('NoNewPrivs') == '1' and rows.get('CapEff') == '0000000000000000',
         'CURRENT_FILTER_SECURITY_READBACK_FAILED')
    return count


def _proof(pid, before, after, origin):
    return {'schema': 'PHASE7I_CONTROLLER_GUARD_V1', 'status': 'PASS_CURRENT_FILTER_READBACK',
            'scope': SCOPE, 'pid': pid, 'program_sha256': program_identity(),
            'instruction_count': len(program()), 'seccomp_mode': 2, 'no_new_privs': 1,
            'filter_count_before': before, 'filter_count_after': after,
            'origin': origin, 'program_identity_evidence':
            'REVIEWED_SOURCE_AND_INHERITANCE_NOT_KERNEL_PROGRAM_DUMP',
            'FULL_LAUNCH_ENVELOPE_VERIFIED': False}


def validate_guard(proof):
    need(type(proof) is dict and proof.get('schema') == 'PHASE7I_CONTROLLER_GUARD_V1' and
         proof.get('status') == 'PASS_CURRENT_FILTER_READBACK' and proof.get('scope') == SCOPE,
         'GUARD_PROOF_SCHEMA_OR_STATUS')
    need(proof.get('program_sha256') == program_identity() and
         type(proof.get('instruction_count')) is int and proof['instruction_count'] == len(program()) and
         type(proof.get('seccomp_mode')) is int and proof['seccomp_mode'] == 2 and
         type(proof.get('no_new_privs')) is int and proof['no_new_privs'] == 1 and
         integer(proof.get('pid'), 1) and integer(proof.get('filter_count_before'), 1) and
         integer(proof.get('filter_count_after'), 2) and
         proof['filter_count_after'] >= proof['filter_count_before'] and
         proof.get('origin') in ('CURRENT_PROCESS_INSTALL', 'CURRENT_PROCESS_INHERITED_READBACK') and
         proof.get('program_identity_evidence') ==
         'REVIEWED_SOURCE_AND_INHERITANCE_NOT_KERNEL_PROGRAM_DUMP' and
         proof.get('FULL_LAUNCH_ENVELOPE_VERIFIED') is False and
         not any(key in proof for key in ('reason', 'error')),
         'GUARD_PROOF_FIELD_MISMATCH')
    if proof['origin'] == 'CURRENT_PROCESS_INSTALL':
        need(proof['filter_count_after'] == proof['filter_count_before'] + 1,
             'INSTALL_FILTER_COUNT_NOT_INCREMENTED')
    return True


def install():
    """Future explicitly authorized service only; offline tests mock all calls."""
    global _ACTIVE
    need(_ACTIVE is None, 'CONTROLLER_GUARD_ALREADY_ACTIVE')
    need(platform.system() == 'Linux' and platform.machine() == 'x86_64',
         'CONTROLLER_GUARD_NATIVE_X86_64_ONLY')
    library = _libc()
    before = _security(library)
    _checked(library.prctl(38, 1, 0, 0, 0), 'PR_SET_NO_NEW_PRIVS_FAILED')
    rows = program()
    array = (_Filter * len(rows))(*(_Filter(*row) for row in rows))
    descriptor = _Program(len(rows), array)
    address = ctypes.cast(ctypes.pointer(descriptor), ctypes.c_void_p).value
    _checked(library.prctl(22, 2, address, 0, 0), 'CONTROLLER_FILTER_INSTALL_FAILED')
    after = _security(library)
    proof = _proof(os.getpid(), before, after, 'CURRENT_PROCESS_INSTALL')
    validate_guard(proof)
    _ACTIVE = proof
    return copy.deepcopy(proof)


def readback(parent_guard):
    """Read THIS process, not a copied parent observation or kernel BPF dump.

    The private parent-to-child handoff and unchanged executable/source chain
    are external prerequisites. Mode/count alone cannot identify kernel BPF.
    """
    global _ACTIVE
    validate_guard(parent_guard)
    need(platform.system() == 'Linux' and platform.machine() == 'x86_64',
         'CONTROLLER_GUARD_NATIVE_X86_64_ONLY')
    after = _security(_libc())
    need(after >= parent_guard['filter_count_after'], 'INHERITED_FILTER_COUNT_DECREASED')
    proof = _proof(os.getpid(), parent_guard['filter_count_after'], after,
                   'CURRENT_PROCESS_INHERITED_READBACK')
    proof['parent_pid'] = parent_guard['pid']
    validate_guard(proof)
    _ACTIVE = proof
    return copy.deepcopy(proof)


def probe():
    """Six no-host-target calls, separately authorized future service only.

    Unsupported unshare flag 0x80000000 creates no namespace without seccomp.
    All other targets are fd=-1. Stop immediately on any unexpected result.
    This proves syscall refusal, not host proc-write/device access behavior.
    """
    need(_ACTIVE is not None, 'CURRENT_GUARD_REQUIRED_BEFORE_FIXED_PROBES')
    validate_guard(_ACTIVE)
    need(_ACTIVE['pid'] == os.getpid(), 'CURRENT_PID_GUARD_READBACK_REQUIRED')
    library = _libc()
    need(_security(library) >= _ACTIVE['filter_count_after'], 'FILTER_COUNT_DECREASED')
    signatures = {'setns': [ctypes.c_int, ctypes.c_int], 'unshare': [ctypes.c_int],
        'fallocate': [ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_longlong],
        'fsetxattr': [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int],
        'ioctl': [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong],
        'connect': [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]}
    for name, types in signatures.items():
        getattr(library, name).argtypes = types
        getattr(library, name).restype = ctypes.c_int
    requests = (lambda: library.setns(-1, 0), lambda: library.unshare(-2147483648),
        lambda: library.fallocate(-1, 1, 0, 1),
        lambda: library.fsetxattr(-1, b'user.hh_inert_guard', b'I', 1, 0),
        lambda: library.ioctl(-1, 0x40049409, ctypes.c_ulong(-1).value),
        lambda: library.connect(-1, None, 0))
    checks = []
    for (case_id, name, target), call in zip(CASES, requests):
        ctypes.set_errno(0)
        code = call()
        observed = ctypes.get_errno() if code < 0 else 0
        checks.append({'case_id': case_id, 'syscall': name, 'target': target,
                       'return_code': code, 'errno': observed})
        if code != -1 or observed != errno.EPERM:
            break
    passed = len(checks) == len(CASES) and all(x['return_code'] == -1 and
                                             x['errno'] == errno.EPERM for x in checks)
    return {'schema': 'PHASE7I_CONTROLLER_GUARD_DENIAL_V1', 'scope': SCOPE,
            'status': 'PASS_FIXED_INVALID_TARGET_DENIALS' if passed else 'REJECTED',
            'pid': os.getpid(), 'program_sha256': program_identity(),
            'checks': checks, 'all_denied': passed,
            'host_write_or_device_access_tested': False,
            'FULL_LAUNCH_ENVELOPE_VERIFIED': False}


def inherit_namespace(parent_proof, current_facts):
    """Pure identity-based owner inheritance, explicitly not child nsfs ioctl.

    Parent/caller must retain the original namespace references and be alive.
    Identity equality does not authenticate an untrusted JSON producer.
    """
    _validate_namespace_parent(parent_proof)
    need(type(current_facts) is dict and set(current_facts) == {
        'schema', 'pid', 'identities', 'uid_map', 'gid_map', 'CapEff', 'NoNewPrivs',
        'Seccomp', 'network_interfaces'} and
        current_facts['schema'] == 'PHASE7I_CURRENT_NAMESPACE_FACTS_V1' and
        integer(current_facts['pid'], 1), 'CURRENT_NAMESPACE_FACTS_SCHEMA')
    for key in ('uid_map', 'gid_map', 'CapEff', 'NoNewPrivs', 'Seccomp'):
        need(type(current_facts[key]) is str and current_facts[key].isascii() and
             len(current_facts[key]) <= 512, 'CURRENT_NAMESPACE_TEXT_TYPE:' + key)
    need(type(current_facts['network_interfaces']) is list and
         current_facts['network_interfaces'] == ['lo'], 'CURRENT_NAMESPACE_NETWORK_FACTS')
    for key in ('uid_map', 'gid_map'):
        need(ns.parse_id_map(current_facts[key]) == ns.parse_id_map(parent_proof[key]),
             'UNCHANGED_NAMESPACE_ID_MAP_CHANGED:' + key)
    identities = current_facts['identities']
    need(type(identities) is dict and set(identities) == set(ns.TYPES),
         'CURRENT_EXACT_NAMESPACE_IDENTITIES')
    for name in ns.TYPES:
        row = identities[name]
        need(type(row) is dict and set(row) == {'dev', 'inode'} and
             integer(row['dev'], 1) and integer(row['inode'], 1),
             'CURRENT_NAMESPACE_IDENTITY_TYPE:' + name)
        need(row == {key: parent_proof['namespaces'][name][key] for key in ('dev', 'inode')},
             'CURRENT_NAMESPACE_IDENTITY_CHANGED:' + name)
    proof = {key: copy.deepcopy(value) for key, value in parent_proof.items()
             if key not in ('current_identity_facts', 'initial_owner_proof_sha256',
                            'owner_evidence', 'type_evidence')}
    for key in ('uid_map', 'gid_map', 'CapEff', 'NoNewPrivs', 'Seccomp', 'network_interfaces'):
        proof[key] = copy.deepcopy(current_facts[key])
    proof['owner_evidence'] = 'OWNER_INHERITED_BY_SAME_NAMESPACE_IDENTITY'
    proof['type_evidence'] = 'CACHED_FROM_INITIAL_NSFS_TYPE_READBACK'
    proof['current_identity_facts'] = copy.deepcopy(current_facts)
    proof['initial_owner_proof_sha256'] = parent_proof.get('initial_owner_proof_sha256') or \
        hashlib.sha256(json.dumps(parent_proof, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    ns.validate(proof, parent_proof)
    return proof


def _validate_namespace_parent(proof):
    try:
        ns.validate(proof)
        need(type(proof['owner_userns']) is dict and
             set(proof['owner_userns']) == {'net', 'ipc'}, 'PARENT_EXACT_OWNER_SET')
        for row in proof['owner_userns'].values():
            need(type(row) is dict and set(row) == {'dev', 'inode'} and
                 integer(row['dev'], 1) and integer(row['inode'], 1),
                 'PARENT_OWNER_IDENTITY_TYPE')
        if any(key in proof for key in ('owner_evidence', 'type_evidence',
                                       'initial_owner_proof_sha256', 'current_identity_facts')):
            need(proof.get('owner_evidence') == 'OWNER_INHERITED_BY_SAME_NAMESPACE_IDENTITY' and
                 proof.get('type_evidence') == 'CACHED_FROM_INITIAL_NSFS_TYPE_READBACK',
                 'PARENT_INHERITED_EVIDENCE_LABEL')
            digest = proof.get('initial_owner_proof_sha256')
            need(type(digest) is str and len(digest) == 64 and
                 all(char in '0123456789abcdef' for char in digest), 'PARENT_INITIAL_PROOF_HASH')
    except (AttributeError, KeyError, TypeError) as error:
        raise ValueError('PARENT_NAMESPACE_PROOF_MALFORMED') from error


def collect_inherited_namespace(parent_proof):
    """Future readonly stat/proc producer; no open namespace FD or ioctl."""
    _validate_namespace_parent(parent_proof)
    facts = {'schema': 'PHASE7I_CURRENT_NAMESPACE_FACTS_V1', 'pid': os.getpid(),
             'identities': {}}
    for name in ns.TYPES:
        info = os.stat('/proc/self/ns/' + name)
        facts['identities'][name] = {'dev': info.st_dev, 'inode': info.st_ino}
    for key in ('uid_map', 'gid_map'):
        facts[key] = ns.bounded_read('/proc/self/' + key, 512)
    fields = _status_fields()
    for key in ('CapEff', 'NoNewPrivs', 'Seccomp'):
        need(key in fields, 'CURRENT_NAMESPACE_SECURITY_MISSING:' + key)
        facts[key] = fields[key]
    interfaces = []
    for line in ns.bounded_read('/proc/net/dev').splitlines()[2:]:
        need(':' in line, 'CURRENT_NETWORK_READBACK_MALFORMED')
        interfaces.append(line.split(':', 1)[0].strip())
    facts['network_interfaces'] = sorted(interfaces)
    return inherit_namespace(parent_proof, facts)
