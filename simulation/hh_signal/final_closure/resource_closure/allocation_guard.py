"""Inherited x86_64 allocation-bypass filter; source proposal until tested.

RLIMIT_FSIZE bounds logical EOF, not fallocate KEEP_SIZE allocated extents.
This filter complements fixed FDs, readonly mounts, tmpfs quotas and cgroups.
It is NOT a complete syscall allowlist, filesystem quota or authorization.
No import or offline unit test installs a filter or executes the live probe.

Primary source: microsoft/WSL2-Linux-Kernel linux-msft-wsl-6.6.87.2,
fs/open.c:vfs_fallocate; fs/ext4/extents.c:ext4_fallocate (KEEP_SIZE skips
inode_newsize_ok); fs/ioctl.c:do_vfs_ioctl. Kernel seccomp documentation:
https://www.kernel.org/doc/html/v6.6/userspace-api/seccomp_filter.html
"""
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import stat

AUDIT_ARCH_X86_64 = 0xC000003E
X32_SYSCALL_BIT = 0x40000000
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ALLOW = 0x7FFF0000
SECCOMP_RET_ERRNO_EPERM = 0x00050000 | errno.EPERM
SAFE_TTY_REQUESTS = (0x5401, 0x5413, 0x541B)
# Fixed native x86_64 syscall numbers, independently checked against installed
# /usr/include/x86_64-linux-gnu/asm/unistd_64.h. Compatibility ABIs are killed.
DENIED = {
    "ptrace": 101, "mknod": 133, "pivot_root": 155, "chroot": 161,
    "mount": 165, "umount2": 166, "swapon": 167, "swapoff": 168,
    "quotactl": 179, "setxattr": 188, "lsetxattr": 189, "fsetxattr": 190,
    "removexattr": 197, "lremovexattr": 198, "fremovexattr": 199,
    "io_setup": 206, "io_getevents": 208, "io_submit": 209,
    "io_cancel": 210, "mknodat": 259, "fallocate": 285,
    "name_to_handle_at": 303, "open_by_handle_at": 304,
    "process_vm_writev": 311, "bpf": 321, "userfaultfd": 323,
    "io_pgetevents": 333, "io_uring_setup": 425, "io_uring_enter": 426,
    "io_uring_register": 427, "open_tree": 428, "move_mount": 429,
    "fsopen": 430, "fsconfig": 431, "fsmount": 432, "fspick": 433,
    "pidfd_getfd": 438, "mount_setattr": 442, "quotactl_fd": 443,
}
_INSTALLED = None


class AllocationGuardError(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise AllocationGuardError(code)


def program():
    """Return classic-BPF rows only; no kernel syscall or installation."""
    LD, JEQ, JSET, RET = 0x20, 0x15, 0x45, 0x06
    deny, allow, kill = SECCOMP_RET_ERRNO_EPERM, SECCOMP_RET_ALLOW, SECCOMP_RET_KILL_PROCESS
    rows = [(LD, 0, 0, 4), (JEQ, 1, 0, AUDIT_ARCH_X86_64),
            (RET, 0, 0, kill), (LD, 0, 0, 0),
            (JSET, 0, 1, X32_SYSCALL_BIT), (RET, 0, 0, kill)]
    for number in sorted(DENIED.values()):
        rows.extend(((JEQ, 0, 1, number), (RET, 0, 0, deny)))
    # ioctl arg1 is an unsigned-int request in the native kernel ABI. Reject
    # nonzero upper bits too, then allow only three read-only terminal queries.
    rows.extend(((JEQ, 0, 9, 16), (LD, 0, 0, 28), (JEQ, 1, 0, 0),
                 (RET, 0, 0, deny), (LD, 0, 0, 24),
                 (JEQ, 3, 0, SAFE_TTY_REQUESTS[0]),
                 (JEQ, 2, 0, SAFE_TTY_REQUESTS[1]),
                 (JEQ, 1, 0, SAFE_TTY_REQUESTS[2]),
                 (RET, 0, 0, deny), (RET, 0, 0, allow), (RET, 0, 0, allow)))
    return rows


def program_identity():
    return hashlib.sha256(json.dumps(program(), separators=(",", ":")).encode()).hexdigest()


class _Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]


class _Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filters", ctypes.POINTER(_Filter))]


def _libc():
    library = ctypes.CDLL(None, use_errno=True)
    library.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                             ctypes.c_ulong, ctypes.c_ulong]
    library.prctl.restype = ctypes.c_int
    return library


def _checked(value, name):
    if value < 0:
        raise OSError(ctypes.get_errno(), name)
    return value


def _filter_count():
    rows = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines()
                if ":" in line)
    value = rows.get("Seccomp_filters", "").strip()
    need(value.isdigit(), "SECCOMP_FILTER_COUNT_UNAVAILABLE")
    return int(value)


def install():
    """Irreversibly install in this worker before business attest/imports.

    Requires a separately approved future execution scope. The function itself
    grants no build or physical permission. Children inherit this kernel filter.
    """
    global _INSTALLED
    need(_INSTALLED is None, "ALLOCATION_GUARD_ALREADY_INSTALLED")
    need(platform.system() == "Linux" and platform.machine() == "x86_64",
         "ALLOCATION_GUARD_NATIVE_X86_64_ONLY")
    library = _libc()
    before = _filter_count()
    _checked(library.prctl(38, 1, 0, 0, 0), "PR_SET_NO_NEW_PRIVS")
    rows = program()
    array = (_Filter * len(rows))(*(_Filter(*row) for row in rows))
    descriptor = _Program(len(rows), array)
    address = ctypes.cast(ctypes.pointer(descriptor), ctypes.c_void_p).value
    _checked(library.prctl(22, 2, address, 0, 0), "SECCOMP_ALLOCATION_FILTER_INSTALL")
    after = _filter_count()
    need(_checked(library.prctl(21, 0, 0, 0, 0), "PR_GET_SECCOMP") == 2 and
         _checked(library.prctl(39, 0, 0, 0, 0), "PR_GET_NO_NEW_PRIVS") == 1 and
         after == before + 1, "ALLOCATION_FILTER_KERNEL_READBACK")
    _INSTALLED = {"schema": "HH_ALLOCATION_BYPASS_GUARD_V1", "installed": True,
        "pid": os.getpid(), "program_sha256": program_identity(),
        "instruction_count": len(rows), "seccomp_mode": 2, "no_new_privs": 1,
        "filter_count_before": before, "filter_count_after": after,
        "native_architecture": "x86_64", "x32_action": "KILL_PROCESS",
        "default_action": "ALLOW", "denied_action": "ERRNO_EPERM",
        "denied_syscalls": dict(DENIED), "safe_readonly_tty_requests": list(SAFE_TTY_REQUESTS),
        "physical_or_build_authorization": False}
    return dict(_INSTALLED)


def probe(fds, work):
    """Future tiny live negative: 64KiB request maximum, no real build data.

    Never called in offline tests. A failure stops this fixed probe sequence.
    A missing guard fails BEFORE any file creation or allocation request.
    """
    need(_INSTALLED is not None and _INSTALLED["pid"] == os.getpid(),
         "ACTUAL_ALLOCATION_GUARD_INSTALL_REQUIRED")
    library = _libc()
    need(library.prctl(21, 0, 0, 0, 0) == 2, "LIVE_SECCOMP_MODE_REQUIRED")
    need(type(fds) in (list, tuple) and len(fds) == 2 and
         all(type(fd) is int and fd >= 3 for fd in fds), "FIXED_FIXTURE_CHUNK_FDS_REQUIRED")
    before = [os.fstat(fd) for fd in fds]
    need(all(stat.S_ISREG(st.st_mode) and st.st_uid == os.geteuid() and
             st.st_nlink == 1 and st.st_size == 0 for st in before),
         "FRESH_OWNED_PROBE_CHUNKS_REQUIRED")
    need(len({(st.st_dev, st.st_ino) for st in before}) == len(before), "DISTINCT_PROBE_CHUNKS_REQUIRED")
    work = Path(work)
    need(work.is_absolute() and work.is_dir() and not any(p.is_symlink() for p in (work, *work.parents)),
         "OWNED_PROBE_WORK_REQUIRED")
    path = work / "inert_allocation_guard_source.dat"
    source_fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    checks = []
    try:
        os.write(source_fd, b"INERT_ALLOCATION_GUARD_SOURCE\n")
        library.fallocate.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_longlong]
        library.fallocate.restype = ctypes.c_int
        library.ioctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong]
        library.ioctl.restype = ctypes.c_int
        library.fsetxattr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p,
                                      ctypes.c_size_t, ctypes.c_int]
        library.fsetxattr.restype = ctypes.c_int
        requests = (
            ("fallocate_keep_size", "fallocate", lambda: library.fallocate(fds[0], 1, 0, 65536)),
            ("ioctl_clone", "ioctl", lambda: library.ioctl(fds[0], 0x40049409, source_fd)),
            ("setxattr", "fsetxattr", lambda: library.fsetxattr(fds[0], b"user.hh_inert_guard", b"I", 1, 0)),
        )
        for operation, syscall, call in requests:
            ctypes.set_errno(0)
            code = call()
            observed = ctypes.get_errno() if code < 0 else 0
            checks.append({"operation": operation, "syscall": syscall,
                           "return_code": code, "errno": observed})
            if code != -1 or observed != errno.EPERM:
                break
    finally:
        os.close(source_fd)
    after = [os.fstat(fd) for fd in fds]
    return {"installed": True, "pid": os.getpid(), "program_sha256": program_identity(),
            "checks": checks, "request_max_bytes": 65536,
            "allocation_measurement_scope": "TWO_PREOPENED_HOST_CHUNK_INODES_ONLY",
            "allocated_bytes_before": sum(st.st_blocks * 512 for st in before),
            "allocated_bytes_after": sum(st.st_blocks * 512 for st in after),
            "logical_bytes_before": sum(st.st_size for st in before),
            "logical_bytes_after": sum(st.st_size for st in after),
            "all_denied": len(checks) == 3 and all(x["return_code"] == -1 and
                                                   x["errno"] == errno.EPERM for x in checks)}
