"""Pure BPF evaluation and readonly header audit; NEVER install/probe a filter."""
import ast
import errno
import hashlib
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
from .. import allocation_guard as g


def evaluate(nr, args=(0, 0, 0, 0, 0, 0), arch=g.AUDIT_ARCH_X86_64):
    """Independent tiny interpreter for the four emitted classic-BPF opcodes."""
    data = struct.pack("<iIQ6Q", nr, arch, 0, *args)
    rows = g.program()
    accumulator = 0
    position = 0
    for _ in range(len(rows) + 1):
        code, yes, no, value = rows[position]
        if code == 0x20:
            accumulator = struct.unpack_from("<I", data, value)[0]
            position += 1
        elif code == 0x15:
            position += 1 + (yes if accumulator == value else no)
        elif code == 0x45:
            position += 1 + (yes if accumulator & value else no)
        elif code == 0x06:
            return value
        else:
            raise AssertionError("Unexpected BPF instruction")
        if position >= len(rows):
            raise AssertionError("BPF jump out of program")
    raise AssertionError("BPF did not terminate")


class AllocationProgramTests(unittest.TestCase):
    def test_each_declared_bypass_syscall_is_eperm(self):
        self.assertEqual(len(g.DENIED), len(set(g.DENIED.values())))
        for name, number in g.DENIED.items():
            with self.subTest(syscall=name):
                self.assertEqual(evaluate(number), g.SECCOMP_RET_ERRNO_EPERM)
        self.assertEqual(g.SECCOMP_RET_ERRNO_EPERM & 65535, errno.EPERM)

    def test_fallocate_all_modes_including_keep_size_and_zero_range(self):
        for mode in (0, 1, 2 | 1, 8, 16, 16 | 1, 32, 64, 64 | 1, 0xFFFFFFFF):
            with self.subTest(mode=mode):
                self.assertEqual(evaluate(285, (3, mode, 0, 65536, 0, 0)),
                                 g.SECCOMP_RET_ERRNO_EPERM)

    def test_io_uring_and_native_aio_cannot_submit_allocations(self):
        for number in (206, 208, 209, 210, 333, 425, 426, 427):
            self.assertEqual(evaluate(number), g.SECCOMP_RET_ERRNO_EPERM)

    def test_mutating_xattrs_and_mount_filehandle_paths_denied(self):
        for name in ("setxattr", "lsetxattr", "fsetxattr", "removexattr", "lremovexattr",
                     "fremovexattr", "mount", "umount2", "open_tree", "move_mount",
                     "mount_setattr", "name_to_handle_at", "open_by_handle_at"):
            self.assertEqual(evaluate(g.DENIED[name]), g.SECCOMP_RET_ERRNO_EPERM)

    def test_only_three_safe_readonly_tty_ioctl_requests_allowed(self):
        for request in (0x5401, 0x5413, 0x541B):
            self.assertEqual(evaluate(16, (3, request, 0, 0, 0, 0)), g.SECCOMP_RET_ALLOW)
        # Clone, clone-range, dedupe, preallocation/reservation and setting tty
        # state are all outside the three explicitly reviewed read-only queries.
        for request in (0, 0x40049409, 0x4020940D, 0xC0189436, 0x40305828,
                        0x4030582A, 0x5402, 0x5414, 0xFFFFFFFF):
            self.assertEqual(evaluate(16, (3, request, 0, 0, 0, 0)),
                             g.SECCOMP_RET_ERRNO_EPERM)

    def test_ioctl_high_word_cannot_smuggle_safe_low_request(self):
        for request in g.SAFE_TTY_REQUESTS:
            self.assertEqual(evaluate(16, (3, request | (1 << 32), 0, 0, 0, 0)),
                             g.SECCOMP_RET_ERRNO_EPERM)

    def test_wrong_architecture_and_x32_are_kill_process(self):
        for arch in (0x40000003, 0xC00000B7, 0, 0xFFFFFFFF):
            self.assertEqual(evaluate(0, arch=arch), g.SECCOMP_RET_KILL_PROCESS)
        for nr in (0x40000000, 0x40000000 | 285, 0x40000000 | 16, -1):
            self.assertEqual(evaluate(nr), g.SECCOMP_RET_KILL_PROCESS)

    def test_other_native_compiler_and_archive_syscalls_remain_allowed(self):
        # Ordinary read/write/pwrite/open/stat/fsync/mmap/clone/exec/wait/prctl
        # remain subject to outer mounts, fixed inodes, RLIMIT and cgroup rules.
        for number in (0, 1, 2, 3, 5, 8, 9, 10, 11, 17, 18, 19, 20, 39, 57,
                       59, 60, 61, 72, 74, 75, 76, 77, 157, 202, 257, 262, 600):
            self.assertEqual(evaluate(number), g.SECCOMP_RET_ALLOW)

    def test_exhaustive_native_numbers_match_declared_policy(self):
        for number in range(512):
            if number == 16:
                expected = g.SECCOMP_RET_ERRNO_EPERM
            elif number in g.DENIED.values():
                expected = g.SECCOMP_RET_ERRNO_EPERM
            else:
                expected = g.SECCOMP_RET_ALLOW
            self.assertEqual(evaluate(number), expected, number)

    def test_program_rows_and_jumps_are_bounded_and_identity_stable(self):
        rows = g.program()
        self.assertLess(len(rows), 256)
        self.assertEqual(g.program_identity(), hashlib.sha256(
            json.dumps(rows, separators=(",", ":")).encode()).hexdigest())
        for i, (code, yes, no, value) in enumerate(rows):
            self.assertTrue(all(type(x) is int for x in (code, yes, no, value)))
            self.assertLessEqual(value, 0xFFFFFFFF)
            if code in (0x15, 0x45):
                self.assertLess(i + 1 + yes, len(rows))
                self.assertLess(i + 1 + no, len(rows))

    def test_syscall_numbers_match_installed_native_header_readonly(self):
        path = Path("/usr/include/x86_64-linux-gnu/asm/unistd_64.h")
        self.assertTrue(path.is_file(), "Native syscall header required for this readonly source audit")
        rows = {}
        for line in path.read_text().splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[0] == "#define" and fields[1].startswith("__NR_"):
                rows[fields[1][5:]] = int(fields[2])
        for name, number in g.DENIED.items():
            self.assertEqual(rows[name], number, name)
        self.assertEqual(rows["ioctl"], 16)

    def test_import_and_program_do_not_install_or_probe(self):
        self.assertIsNone(g._INSTALLED)
        text = Path(g.__file__).read_text()
        tree = ast.parse(text)
        forbidden = {"install", "probe", "prctl", "fallocate", "ioctl", "fsetxattr"}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                continue
            for call in (x for x in ast.walk(node) if isinstance(x, ast.Call)):
                name = call.func.id if isinstance(call.func, ast.Name) else getattr(call.func, "attr", "")
                self.assertNotIn(name, forbidden)
        for _ in range(3):
            g.program()
            g.program_identity()
        self.assertIsNone(g._INSTALLED)

    def test_live_probe_without_install_fails_before_file_creation(self):
        with patch.object(g.os, "open") as opened:
            with self.assertRaisesRegex(g.AllocationGuardError, "ACTUAL_ALLOCATION_GUARD_INSTALL_REQUIRED"):
                g.probe([3, 4], Path("/NEVER_CREATED"))
            opened.assert_not_called()
        self.assertIsNone(g._INSTALLED)


if __name__ == "__main__":
    unittest.main()
