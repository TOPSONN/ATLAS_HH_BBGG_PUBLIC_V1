"""Harmless ordinary-byte archive fixtures; no compiler/native/physics route."""
import copy
import contextlib
import io
from unittest.mock import patch
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from simulation.hh_signal.final_closure.resource_closure import archive_io as a


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hh-inert-archive-")
        self.base = Path(self.temp.name)
        self.tree = self.base / "owned"
        self.tree.mkdir()
        self.fds = [os.open(self.base / f"chunk_{i}", os.O_RDWR | os.O_CREAT |
                    os.O_EXCL | os.O_CLOEXEC, 0o600) for i in range(2)]
        self.index_fd = os.open(self.base / "index", os.O_RDWR | os.O_CREAT |
                               os.O_EXCL | os.O_CLOEXEC, 0o600)

    def tearDown(self):
        for fd in [*self.fds, self.index_fd]:
            os.close(fd)
        self.temp.cleanup()

    def write(self):
        return a.write_archive(self.tree, self.fds, index_fd=self.index_fd)

    def index(self, summary=None):
        return a.read_archive_index(self.index_fd, expected_sha256=
                                    None if summary is None else summary["index_sha256"])

    def verify(self, index=None, names=()):
        return a.verify_archive(self.fds, self.index() if index is None else index,
                                receipt_names=names)

    def assertError(self, code, function, *args, **kwargs):
        with self.assertRaisesRegex(a.ArchiveError, code):
            function(*args, **kwargs)

    def test_empty_archive_has_two_zero_blocks_and_zero_unused_chunk(self):
        summary = self.write()
        self.assertEqual(summary["archive_bytes"], 1024)
        self.assertEqual(os.fstat(self.fds[1]).st_size, 0)
        self.assertEqual(self.verify(self.index(summary))["entry_count"], 0)

    def test_roundtrip_member_hashes_and_bounded_json_without_extraction(self):
        (self.tree / "nested").mkdir()
        (self.tree / "nested/receipt.json").write_text('{"inert":true,"count":3}')
        (self.tree / "empty").write_bytes(b"")
        summary = self.write()
        before = sorted(x.relative_to(self.base).as_posix() for x in self.base.rglob("*"))
        result = self.verify(self.index(summary), ("nested/receipt.json",))
        self.assertEqual(result["receipts"], {"nested/receipt.json": {"inert": True, "count": 3}})
        self.assertEqual(before, sorted(x.relative_to(self.base).as_posix()
                                      for x in self.base.rglob("*")))
        self.assertEqual(result["status"], "VERIFIED_NO_EXTRACTION_NO_EXECUTION")

    def test_cross_chunk_streaming_hashes(self):
        for i in range(3):
            (self.tree / str(i)).write_bytes(bytes([65 + i]) * 30000)
        summary = self.write()
        self.assertEqual(summary["chunks"][0]["bytes"], 65536)
        self.assertGreater(summary["chunks"][1]["bytes"], 0)
        self.assertEqual(self.verify(self.index(summary))["entry_count"], 3)

    def test_ustar_prefix_for_long_utf8_path(self):
        parent = self.tree / ("a" * 90)
        parent.mkdir()
        leaf = "b" * 60 + "_資料.txt"
        (parent / leaf).write_bytes(b"inert")
        self.write()
        self.assertEqual(self.verify()["members"][0]["path"], parent.name + "/" + leaf)

    def test_archive_is_deterministic_despite_mtime(self):
        p = self.tree / "inert"
        p.write_bytes(b"ordinary inert fixture")
        self.write()
        raw = [os.pread(fd, os.fstat(fd).st_size, 0) for fd in self.fds]
        for fd in [*self.fds, self.index_fd]:
            os.ftruncate(fd, 0)
        os.utime(p, (1, 1))
        self.write()
        self.assertEqual(raw, [os.pread(fd, os.fstat(fd).st_size, 0) for fd in self.fds])

    def test_file_size_cap(self):
        (self.tree / "inert").write_bytes(b"x" * 65537)
        self.assertError("MEMBER_SIZE_CAP", self.write)
        self.assertEqual(os.fstat(self.index_fd).st_size, 0)

    def test_aggregate_archive_cap_without_individual_file_violation(self):
        for i in range(3):
            (self.tree / str(i)).write_bytes(b"x" * 65536)
        self.assertError("ARCHIVE_CAPACITY", self.write)
        self.assertTrue(all(os.fstat(fd).st_size == 0 for fd in self.fds))

    def test_entry_count_cap_includes_empty_directories(self):
        for i in range(257):
            (self.tree / str(i)).mkdir()
        self.assertError("TREE_ENTRY_CAP", self.write)

    def test_source_symlink_rejected(self):
        (self.tree / "link").symlink_to("../index")
        self.assertError("TREE_REGULAR_SINGLE_LINK_ONLY", self.write)

    def test_source_hardlink_rejected(self):
        (self.tree / "one").write_bytes(b"inert")
        os.link(self.tree / "one", self.tree / "two")
        self.assertError("TREE_REGULAR_SINGLE_LINK_ONLY", self.write)

    def test_source_fifo_rejected(self):
        os.mkfifo(self.tree / "fifo")
        self.assertError("TREE_REGULAR_SINGLE_LINK_ONLY", self.write)

    def test_symlink_tree_root_rejected(self):
        link = self.base / "alias"
        link.symlink_to(self.tree, target_is_directory=True)
        self.assertError("OWNED_TREE_ROOT", a.write_archive, link, self.fds,
                         index_fd=self.index_fd)

    def test_no_overwrite_or_reuse(self):
        self.write()
        before = os.pread(self.fds[0], 1024, 0)
        self.assertError("FRESH_EMPTY_DESCRIPTOR_REQUIRED", self.write)
        self.assertEqual(before, os.pread(self.fds[0], 1024, 0))

    def test_fixed_descriptor_count_and_unique_inode(self):
        self.assertError("FIXED_CHUNK_DESCRIPTOR_COUNT", a.write_archive,
                         self.tree, self.fds[:1], index_fd=self.index_fd)
        self.assertError("DUPLICATE_DESCRIPTOR_INODE", a.write_archive,
                         self.tree, [self.fds[0], self.fds[0]], index_fd=self.index_fd)
        self.assertError("DUPLICATE_DESCRIPTOR_INODE", a.write_archive,
                         self.tree, self.fds, index_fd=self.fds[0])

    def test_cloexec_required(self):
        fcntl.fcntl(self.fds[0], fcntl.F_SETFD, 0)
        self.assertError("DESCRIPTOR_CLOEXEC_REQUIRED", self.write)

    def test_socket_device_directory_descriptors_rejected(self):
        with socket.socket() as sock:
            self.assertError("DESCRIPTOR_REGULAR", a.write_archive, self.tree,
                             [sock.fileno(), self.fds[1]], index_fd=self.index_fd)
        fd = os.open(os.devnull, os.O_RDWR | os.O_CLOEXEC)
        directory = os.open(self.tree, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            for special in [fd, directory]:
                self.assertError("DESCRIPTOR_REGULAR", a.write_archive,
                                 self.tree, [special, self.fds[1]], index_fd=self.index_fd)
        finally:
            os.close(fd)
            os.close(directory)

    def test_append_or_nonempty_descriptor_rejected(self):
        fcntl.fcntl(self.fds[0], fcntl.F_SETFL, os.O_APPEND)
        self.assertError("APPEND_DESCRIPTOR_FORBIDDEN", self.write)
        fcntl.fcntl(self.fds[0], fcntl.F_SETFL, 0)
        os.pwrite(self.fds[0], b"x", 0)
        self.assertError("FRESH_EMPTY_DESCRIPTOR_REQUIRED", self.write)

    def test_profile_cannot_be_expanded_or_bool_substituted(self):
        for lim in [a.ArchiveLimits("FIXTURE", 3, 65536, 65536, 256, 65536, 65536),
                    a.ArchiveLimits("FIXTURE", 2, 65536, 65536, True, 65536, 65536), {}]:
            self.assertError("UNREVIEWED_ARCHIVE_LIMITS", a.write_archive,
                             self.tree, self.fds, limits=lim, index_fd=self.index_fd)
        self.assertEqual(a.BUILD_ONLY_LIMITS.chunk_count, 32)
        self.assertEqual(a.BUILD_ONLY_LIMITS.chunk_bytes, 64 * 1024 * 1024)
        self.assertEqual(a.BUILD_ONLY_LIMITS.max_entries, 32768)

    def test_truncated_chunk_rejected(self):
        self.write()
        os.ftruncate(self.fds[0], 1000)
        self.assertError("CHUNK_LENGTH_MISMATCH", self.verify)

    def test_tampered_member_rejected_even_before_chunk_hash(self):
        (self.tree / "a").write_bytes(b"inert")
        self.write()
        os.pwrite(self.fds[0], b"X", 512)
        self.assertError("MEMBER_HASH_MISMATCH", self.verify)

    def test_chunk_hash_mismatch_rejected(self):
        self.write()
        index = self.index()
        index["chunks"][0]["sha256"] = "1" * 64
        self.assertError("CHUNK_HASH_MISMATCH", self.verify, index)

    def test_trailing_data_rejected(self):
        self.write()
        os.pwrite(self.fds[0], b"x", 1024)
        self.assertError("CHUNK_LENGTH_MISMATCH", self.verify)

    def test_nonzero_padding_rejected(self):
        (self.tree / "a").write_bytes(b"x")
        self.write()
        os.pwrite(self.fds[0], b"Y", 513)
        self.assertError("USTAR_NONZERO_PADDING", self.verify)

    def test_end_markers_rejected(self):
        self.write()
        os.pwrite(self.fds[0], b"x", 512)
        self.assertError("USTAR_END_MARKERS", self.verify)

    def test_tar_symlink_hardlink_pax_and_device_types_rejected(self):
        (self.tree / "a").write_bytes(b"x")
        self.write()
        original = bytearray(os.pread(self.fds[0], 512, 0))
        for kind in b"12xg3456":
            header = bytearray(original)
            header[156] = kind
            header[148:156] = b" " * 8
            header[148:156] = format(sum(header), "06o").encode() + b"\0 "
            os.pwrite(self.fds[0], header, 0)
            self.assertError("USTAR_HEADER_OR_RECORD_TYPE", self.verify)

    def test_tar_traversal_header_rejected(self):
        (self.tree / "a").write_bytes(b"x")
        self.write()
        header = bytearray(os.pread(self.fds[0], 512, 0))
        header[:100] = b"../outside" + b"\0" * 90
        header[148:156] = b" " * 8
        header[148:156] = format(sum(header), "06o").encode() + b"\0 "
        os.pwrite(self.fds[0], header, 0)
        self.assertError("USTAR_HEADER_OR_RECORD_TYPE", self.verify)

    def test_duplicate_tar_record_header_rejected(self):
        (self.tree / "a").write_bytes(b"x")
        (self.tree / "b").write_bytes(b"y")
        self.write()
        os.pwrite(self.fds[0], a._header("a", 1), 1024)
        self.assertError("USTAR_HEADER_OR_RECORD_TYPE", self.verify)

    def test_index_unknown_field_bool_range_and_size_rejected(self):
        self.write()
        index = self.index()
        mutations = [("entry_count", True), ("archive_bytes", 131584),
                     ("unknown", 0), ("total_member_bytes", -1)]
        for key, value in mutations:
            changed = copy.deepcopy(index)
            changed[key] = value
            self.assertError("INDEX_", self.verify, changed)
        os.ftruncate(self.index_fd, 65537)
        self.assertError("INDEX_SIZE_CAP", self.index)

    def test_index_traversal_duplicates_member_cap_and_order_rejected(self):
        (self.tree / "a").write_bytes(b"x")
        (self.tree / "b").write_bytes(b"y")
        self.write()
        original = self.index()
        for name in ["../x", "/absolute", "a/../x", "a//x", "a\\x"]:
            index = copy.deepcopy(original)
            index["members"][0]["path"] = name
            self.assertError("MEMBER_PATH", self.verify, index)
        index = copy.deepcopy(original)
        index["members"][1]["path"] = "a"
        self.assertError("INDEX_DUPLICATE_OR_ORDER", self.verify, index)
        index = copy.deepcopy(original)
        index["members"].reverse()
        self.assertError("INDEX_DUPLICATE_OR_ORDER", self.verify, index)
        index = copy.deepcopy(original)
        index["members"][0]["bytes"] = 65537
        self.assertError("INDEX_MEMBER_RANGE", self.verify, index)

    def test_index_hash_binding_and_duplicate_json_keys(self):
        self.write()
        self.assertError("INDEX_HASH_MISMATCH", a.read_archive_index, self.index_fd,
                         expected_sha256="1" * 64)
        raw = b'{"schema":"x","schema":"y"}'
        os.ftruncate(self.index_fd, 0)
        os.pwrite(self.index_fd, raw, 0)
        self.assertError("DUPLICATE_JSON_KEY", self.index)

    def test_selected_receipt_json_failures(self):
        (self.tree / "a.json").write_text('{"x":1,"x":2}')
        self.write()
        self.assertError("DUPLICATE_JSON_KEY", self.verify, names=("a.json",))
        self.assertError("SELECTED_RECEIPT_NAMES", self.verify, names=("missing",))
        self.assertError("SELECTED_RECEIPT_NAMES", self.verify, names=("a.json", "a.json"))
        self.assertError("SELECTED_RECEIPT_COUNT", self.verify, names=("a",) * 6)

    def test_export_descriptors_cannot_be_members_of_source(self):
        fd = os.open(self.tree / "chunk_inside", os.O_RDWR | os.O_CREAT |
                     os.O_EXCL | os.O_CLOEXEC, 0o600)
        try:
            self.assertError("EXPORT_DESCRIPTOR_INSIDE_SOURCE_TREE", a.write_archive,
                             self.tree, [fd, self.fds[1]], index_fd=self.index_fd)
        finally:
            os.close(fd)

    def test_directory_race_after_export_rejected_before_index_completion(self):
        (self.tree / "a").write_bytes(b"inert")
        original = a._ChunkWriter.write
        changed = False
        def write_then_mutate(instance, data):
            nonlocal changed
            original(instance, data)
            if not changed:
                (self.tree / "added_during_export").mkdir()
                changed = True
        with patch.object(a._ChunkWriter, "write", write_then_mutate):
            self.assertError("TREE_RACE", self.write)
        self.assertEqual(os.fstat(self.index_fd).st_size, 0)

    def test_member_race_before_open_rejected(self):
        path = self.tree / "a"
        path.write_bytes(b"inert")
        original = a._open_member
        def changed_open(root_fd, name):
            path.write_bytes(b"changed")
            return original(root_fd, name)
        with patch.object(a, "_open_member", changed_open):
            self.assertError("TREE_RACE", self.write)
        self.assertEqual(os.fstat(self.index_fd).st_size, 0)

    def test_cli_reads_and_returns_only_bounded_scalar_summary(self):
        (self.tree / "a.json").write_text('{"private_fixture":"not_printed"}')
        summary = self.write()
        argv = ["--index", str(self.base / "index"), "--chunk", str(self.base / "chunk_0"),
                "--chunk", str(self.base / "chunk_1"), "--expected-index-sha256",
                summary["index_sha256"], "--receipt", "a.json"]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = a.main(argv)
        self.assertEqual(status, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["selected_receipt_count"], 1)
        self.assertFalse(result["physical_execution_authorized"])
        self.assertNotIn("private_fixture", output.getvalue())
        self.assertNotIn("not_printed", output.getvalue())

    def test_cli_tamper_fails_without_extracting_or_disclosing_contents(self):
        summary = self.write()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = a.main(["--index", str(self.base / "index"), "--chunk",
                             str(self.base / "chunk_0"), "--chunk",
                             str(self.base / "chunk_1"), "--expected-index-sha256", "1" * 64])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["reason"], "INDEX_HASH_MISMATCH")

    def test_json_overflow_and_named_nonfinite_values_rejected(self):
        for raw in (b'{"x":1e999}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'):
            self.assertError("NONFINITE_JSON", a._json, raw)

    def test_excessive_integer_json_fails_as_bounded_archive_error(self):
        raw = b'{"x":' + b'9' * 5000 + b'}'
        self.assertError("INDEX_OR_RECEIPT_JSON", a._json, raw)

    def test_no_host_path_open_or_extract_or_physics_entry(self):
        source = Path(a.__file__).read_text()
        self.assertNotIn("extractall", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("mg5", source.lower())
        self.assertNotIn("HumanReview", source)


if __name__ == "__main__":
    unittest.main()
