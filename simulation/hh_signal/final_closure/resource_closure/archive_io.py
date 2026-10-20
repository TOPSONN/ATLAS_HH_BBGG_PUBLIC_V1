"""Fixed-profile, descriptor-only USTAR transport; never extracts or executes.

The service owns resource accounting. This module only reads its owned build
subtree and writes preopened fresh regular files. No host output path is opened.
Archives and their JSON index are local build artifacts, never public evidence.
"""
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat

BLOCK = 512
SCHEMA = "HH_RESOURCE_ARCHIVE_INDEX_V1"
EMPTY_SHA = hashlib.sha256(b"").hexdigest()


class ArchiveError(ValueError):
    """A bounded transport or identity predicate failed closed."""


def need(ok, code):
    if not ok:
        raise ArchiveError(code)


@dataclass(frozen=True)
class ArchiveLimits:
    profile: str
    chunk_count: int
    chunk_bytes: int
    member_bytes: int
    max_entries: int
    index_bytes: int
    selected_json_bytes: int


FIXTURE_LIMITS = ArchiveLimits("FIXTURE", 2, 65536, 65536, 256, 65536, 65536)
BUILD_ONLY_LIMITS = ArchiveLimits("BUILD_ONLY", 32, 67108864, 67108864, 32768,
                                67108864, 4194304)


def _limits(value):
    need(type(value) is ArchiveLimits and value in (FIXTURE_LIMITS, BUILD_ONLY_LIMITS),
         "UNREVIEWED_ARCHIVE_LIMITS")
    # Dataclass equality alone would accept bool values in integer fields.
    need(all(type(getattr(value, k)) is int for k in
             ("chunk_count", "chunk_bytes", "member_bytes", "max_entries",
              "index_bytes", "selected_json_bytes")), "ARCHIVE_LIMIT_TYPES")
    return value


def _int(value, low, high):
    return type(value) is int and low <= value <= high


def _sha(value):
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None


def _path(value):
    need(type(value) is str and value and "\\" not in value and
         not any(ord(c) < 32 or ord(c) == 127 for c in value), "MEMBER_PATH")
    rel = PurePosixPath(value)
    need(not rel.is_absolute() and value == rel.as_posix() and
         all(x not in ("", ".", "..") for x in value.split("/")), "MEMBER_PATH")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ArchiveError("MEMBER_PATH_ENCODING") from exc
    need(len(encoded) <= 240 and b"\0" not in encoded, "MEMBER_PATH_LENGTH")
    return encoded


def _octal(value, width):
    result = format(value, "o").encode()
    need(len(result) < width, "USTAR_NUMBER_RANGE")
    return b"0" * (width - 1 - len(result)) + result + b"\0"


def _header(name, size):
    raw = _path(name)
    prefix = b""
    leaf = raw
    if len(raw) > 100:
        positions = [i for i, b in enumerate(raw) if b == 47 and
                     i <= 155 and len(raw) - i - 1 <= 100]
        need(bool(positions), "USTAR_PATH_SPLIT")
        split = positions[-1]
        prefix, leaf = raw[:split], raw[split + 1:]
    data = bytearray(BLOCK)
    data[:len(leaf)] = leaf
    data[100:108] = _octal(0o600, 8)
    data[108:116] = _octal(0, 8)
    data[116:124] = _octal(0, 8)
    data[124:136] = _octal(size, 12)
    data[136:148] = _octal(0, 12)
    data[148:156] = b" " * 8
    data[156:157] = b"0"
    data[257:263] = b"ustar\0"
    data[263:265] = b"00"
    data[345:345 + len(prefix)] = prefix
    checksum = sum(data)
    data[148:156] = format(checksum, "06o").encode() + b"\0 "
    return bytes(data)


def _fd(fd, *, writing):
    need(type(fd) is int and fd >= 3, "DESCRIPTOR_TYPE_OR_RESERVED")
    try:
        info = os.fstat(fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        descriptor_flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    except OSError as exc:
        raise ArchiveError("INVALID_DESCRIPTOR") from exc
    need(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
         info.st_nlink == 1, "DESCRIPTOR_REGULAR_OWNED_SINGLE_LINK_REQUIRED")
    need(descriptor_flags & fcntl.FD_CLOEXEC, "DESCRIPTOR_CLOEXEC_REQUIRED")
    access = flags & os.O_ACCMODE
    need(access in ((os.O_WRONLY, os.O_RDWR) if writing else
                    (os.O_RDONLY, os.O_RDWR)), "DESCRIPTOR_ACCESS")
    if writing:
        need(info.st_size == 0 and os.lseek(fd, 0, os.SEEK_CUR) == 0,
             "FRESH_EMPTY_DESCRIPTOR_REQUIRED")
        need(not flags & os.O_APPEND, "APPEND_DESCRIPTOR_FORBIDDEN")
    return info


def _descriptors(fds, limits, *, writing, index_fd=None):
    need(type(fds) in (tuple, list) and len(fds) == limits.chunk_count,
         "FIXED_CHUNK_DESCRIPTOR_COUNT")
    all_fds = list(fds) + ([] if index_fd is None else [index_fd])
    infos = [_fd(fd, writing=writing) for fd in all_fds]
    need(len({(x.st_dev, x.st_ino) for x in infos}) == len(infos),
         "DUPLICATE_DESCRIPTOR_INODE")
    if not writing:
        need(all(x.st_size <= limits.chunk_bytes for x in infos[:len(fds)]),
             "CHUNK_SIZE_CAP")
    return infos


def _write_all(fd, data, offset):
    view = memoryview(data)
    while view:
        count = os.pwrite(fd, view, offset)
        need(count > 0, "SHORT_DESCRIPTOR_WRITE")
        view = view[count:]
        offset += count


class _ChunkWriter:
    def __init__(self, fds, limits):
        self.fds, self.limits = fds, limits
        self.sizes = [0] * len(fds)
        self.hashes = [hashlib.sha256() for _ in fds]
        self.total = 0

    def write(self, data):
        need(self.total + len(data) <= len(self.fds) * self.limits.chunk_bytes,
             "ARCHIVE_CAPACITY")
        view = memoryview(data)
        while view:
            index = self.total // self.limits.chunk_bytes
            offset = self.sizes[index]
            part = view[:self.limits.chunk_bytes - offset]
            _write_all(self.fds[index], part, offset)
            self.hashes[index].update(part)
            self.sizes[index] += len(part)
            self.total += len(part)
            view = view[len(part):]

    def rows(self):
        return [{"index": i, "bytes": size, "sha256": digest.hexdigest()}
                for i, (size, digest) in enumerate(zip(self.sizes, self.hashes))]


def _signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _tree(root, limits):
    root = Path(root)
    need(root.is_absolute() and not any(p.is_symlink() for p in (root, *root.parents)),
         "OWNED_TREE_ROOT")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    root_fd = os.open(root, flags)
    info = os.fstat(root_fd)
    need(info.st_uid == os.geteuid(), "OWNED_TREE_ROOT")
    result = []
    directories = [("", _signature(info))]
    visited = 0

    def walk(parent_fd, prefix):
        nonlocal visited
        children = []
        with os.scandir(parent_fd) as entries:
            for entry in entries:
                visited += 1
                need(visited <= limits.max_entries, "TREE_ENTRY_CAP")
                children.append(entry)
        children.sort(key=lambda x: x.name.encode("utf-8"))
        for entry in children:
            name = prefix + entry.name
            _path(name)
            st = entry.stat(follow_symlinks=False)
            need(st.st_dev == info.st_dev and st.st_uid == os.geteuid(),
                 "FOREIGN_TREE_INODE")
            if stat.S_ISDIR(st.st_mode):
                child_fd = os.open(entry.name, flags, dir_fd=parent_fd)
                try:
                    need(_signature(os.fstat(child_fd)) == _signature(st), "TREE_RACE")
                    directories.append((name, _signature(st)))
                    walk(child_fd, name + "/")
                finally:
                    os.close(child_fd)
            else:
                need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1,
                     "TREE_REGULAR_SINGLE_LINK_ONLY")
                need(st.st_size <= limits.member_bytes, "MEMBER_SIZE_CAP")
                result.append((name, st))
    try:
        walk(root_fd, "")
        return (root_fd, sorted(result, key=lambda x: x[0].encode("utf-8")),
                sorted(directories))
    except BaseException:
        os.close(root_fd)
        raise


def _open_member(root_fd, name):
    parts = name.split("/")
    parent = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW |
                            os.O_CLOEXEC, dir_fd=parent)
            os.close(parent)
            parent = child
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                       dir_fd=parent)
    finally:
        os.close(parent)


def write_archive(root, chunk_fds, *, limits=FIXTURE_LIMITS, index_fd):
    """Export owned regular files to fixed fresh FDs; return scalar index binding.

    An error preserves partial chunks and an empty/uncompleted index. Callers
    must stop and preserve that workspace, never retry or edit the index.
    """
    limits = _limits(limits)
    output_infos = _descriptors(chunk_fds, limits, writing=True, index_fd=index_fd)
    root_fd, entries, directories = _tree(root, limits)
    try:
        output_inodes = {(st.st_dev, st.st_ino) for st in output_infos}
        need(not any((st.st_dev, st.st_ino) in output_inodes for _, st in entries),
             "EXPORT_DESCRIPTOR_INSIDE_SOURCE_TREE")
        archive_bytes = sum(BLOCK + ((st.st_size + BLOCK - 1) // BLOCK) * BLOCK
                            for _, st in entries) + 2 * BLOCK
        need(archive_bytes <= limits.chunk_count * limits.chunk_bytes, "ARCHIVE_CAPACITY")
        output = _ChunkWriter(chunk_fds, limits)
        members = []
        for name, before in entries:
            fd = _open_member(root_fd, name)
            digest = hashlib.sha256()
            try:
                need(_signature(os.fstat(fd)) == _signature(before), "TREE_RACE")
                output.write(_header(name, before.st_size))
                remaining = before.st_size
                while remaining:
                    data = os.read(fd, min(65536, remaining))
                    need(bool(data), "MEMBER_TRUNCATED")
                    output.write(data)
                    digest.update(data)
                    remaining -= len(data)
                need(not os.read(fd, 1) and _signature(os.fstat(fd)) == _signature(before),
                     "TREE_RACE")
            finally:
                os.close(fd)
            output.write(b"\0" * ((-before.st_size) % BLOCK))
            members.append({"path": name, "bytes": before.st_size,
                            "sha256": digest.hexdigest()})
        output.write(b"\0" * (2 * BLOCK))
        check_fd, check_entries, check_directories = _tree(root, limits)
        try:
            need([(name, _signature(st)) for name, st in entries] ==
                 [(name, _signature(st)) for name, st in check_entries] and
                 directories == check_directories, "TREE_RACE")
        finally:
            os.close(check_fd)
        index = {"schema": SCHEMA, "limits": asdict(limits),
                 "status": "ARCHIVE_COMPLETE", "archive_bytes": output.total,
                 "entry_count": len(members),
                 "total_member_bytes": sum(x["bytes"] for x in members),
                 "chunks": output.rows(), "members": members}
        raw = json.dumps(index, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
        need(len(raw) <= limits.index_bytes, "INDEX_SIZE_CAP")
        _write_all(index_fd, raw, 0)
        for fd in (*chunk_fds, index_fd):
            os.fsync(fd)
        return {"schema": SCHEMA, "status": "ARCHIVE_COMPLETE",
                "index_bytes": len(raw), "index_sha256": hashlib.sha256(raw).hexdigest(),
                "archive_bytes": output.total, "entry_count": len(members),
                "chunks": output.rows()}
    finally:
        os.close(root_fd)


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def constant(_):
        raise ArchiveError("NONFINITE_JSON")
    def real(value):
        result = float(value)
        need(math.isfinite(result), "NONFINITE_JSON")
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant,
                          parse_float=real)
    except ArchiveError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ArchiveError("INDEX_OR_RECEIPT_JSON") from exc


def validate_index(index, *, limits=FIXTURE_LIMITS):
    limits = _limits(limits)
    need(type(index) is dict and set(index) == {"schema", "limits", "status",
         "archive_bytes", "entry_count", "total_member_bytes", "chunks", "members"},
         "INDEX_SCHEMA")
    need(index["schema"] == SCHEMA and index["status"] == "ARCHIVE_COMPLETE" and
         type(index["limits"]) is dict and index["limits"] == asdict(limits) and
         all(type(index["limits"].get(k)) is type(v) for k, v in asdict(limits).items()),
         "INDEX_PROFILE")
    capacity = limits.chunk_count * limits.chunk_bytes
    need(_int(index["archive_bytes"], 2 * BLOCK, capacity) and
         index["archive_bytes"] % BLOCK == 0 and
         _int(index["entry_count"], 0, limits.max_entries) and
         _int(index["total_member_bytes"], 0, capacity), "INDEX_RANGES")
    chunks = index["chunks"]
    need(type(chunks) is list and len(chunks) == limits.chunk_count, "INDEX_CHUNKS")
    remaining = index["archive_bytes"]
    for i, row in enumerate(chunks):
        expected = min(remaining, limits.chunk_bytes)
        need(type(row) is dict and set(row) == {"index", "bytes", "sha256"} and
             type(row["index"]) is int and row["index"] == i and
             type(row["bytes"]) is int and row["bytes"] == expected and _sha(row["sha256"]),
             "INDEX_CHUNK_RANGE_OR_ORDER")
        if expected == 0:
            need(row["sha256"] == EMPTY_SHA, "EMPTY_CHUNK_HASH")
        remaining -= expected
    need(remaining == 0, "INDEX_ARCHIVE_LENGTH")
    members = index["members"]
    need(type(members) is list and len(members) == index["entry_count"], "INDEX_MEMBERS")
    names = []
    total = 0
    archive_bytes = 2 * BLOCK
    for row in members:
        need(type(row) is dict and set(row) == {"path", "bytes", "sha256"}, "INDEX_MEMBER_SCHEMA")
        names.append(_path(row["path"]))
        need(_int(row["bytes"], 0, limits.member_bytes) and _sha(row["sha256"]),
             "INDEX_MEMBER_RANGE")
        total += row["bytes"]
        archive_bytes += BLOCK + ((row["bytes"] + BLOCK - 1) // BLOCK) * BLOCK
    need(names == sorted(set(names)), "INDEX_DUPLICATE_OR_ORDER")
    need(total == index["total_member_bytes"] and archive_bytes == index["archive_bytes"],
         "INDEX_MEMBER_LENGTH_SUM")
    return index


def read_archive_index(index_fd, *, limits=FIXTURE_LIMITS, expected_sha256=None):
    limits = _limits(limits)
    info = _fd(index_fd, writing=False)
    need(0 < info.st_size <= limits.index_bytes, "INDEX_SIZE_CAP")
    raw = bytearray()
    while len(raw) < info.st_size:
        part = os.pread(index_fd, min(65536, info.st_size - len(raw)), len(raw))
        need(bool(part), "INDEX_TRUNCATED")
        raw.extend(part)
    need(_signature(os.fstat(index_fd)) == _signature(info), "INDEX_RACE")
    if expected_sha256 is not None:
        need(_sha(expected_sha256) and hashlib.sha256(raw).hexdigest() == expected_sha256,
             "INDEX_HASH_MISMATCH")
    return validate_index(_json(raw), limits=limits)


class _ChunkReader:
    def __init__(self, fds, index, infos, limits):
        self.fds, self.index, self.infos, self.limits = fds, index, infos, limits
        self.total = 0
        self.hashes = [hashlib.sha256() for _ in fds]

    def read(self, size):
        need(_int(size, 0, 65536) and self.total + size <= self.index["archive_bytes"],
             "ARCHIVE_TRUNCATED_OR_READ_BOUND")
        out = bytearray()
        while len(out) < size:
            i = self.total // self.limits.chunk_bytes
            offset = self.total % self.limits.chunk_bytes
            count = min(size - len(out), self.index["chunks"][i]["bytes"] - offset)
            need(count > 0, "ARCHIVE_TRUNCATED")
            data = os.pread(self.fds[i], count, offset)
            need(bool(data), "ARCHIVE_TRUNCATED")
            self.hashes[i].update(data)
            out.extend(data)
            self.total += len(data)
        return bytes(out)

    def finish(self):
        need(self.total == self.index["archive_bytes"], "ARCHIVE_TRAILING_DATA")
        for i, fd in enumerate(self.fds):
            need(_signature(os.fstat(fd)) == _signature(self.infos[i]), "CHUNK_RACE")
            need(self.hashes[i].hexdigest() == self.index["chunks"][i]["sha256"],
                 "CHUNK_HASH_MISMATCH")


def verify_archive(chunk_fds, archive_index, *, limits=FIXTURE_LIMITS, receipt_names=()):
    """Read and hash every member; return bounded selected JSON, never extract.

    The index must be read via read_archive_index with its scalar receipt hash
    when transport identity is required. Verification alone grants no approval.
    """
    limits = _limits(limits)
    index = validate_index(archive_index, limits=limits)
    infos = _descriptors(chunk_fds, limits, writing=False)
    need(all(st.st_size == row["bytes"] for st, row in zip(infos, index["chunks"])),
         "CHUNK_LENGTH_MISMATCH")
    need(type(receipt_names) in (list, tuple) and len(receipt_names) <= 5,
         "SELECTED_RECEIPT_COUNT")
    selected = {_path(name).decode("utf-8") for name in receipt_names}
    need(len(selected) == len(receipt_names) and
         selected <= {r["path"] for r in index["members"]}, "SELECTED_RECEIPT_NAMES")
    stream = _ChunkReader(chunk_fds, index, infos, limits)
    receipts = {}
    for row in index["members"]:
        need(stream.read(BLOCK) == _header(row["path"], row["bytes"]),
             "USTAR_HEADER_OR_RECORD_TYPE")
        keep = row["path"] in selected
        if keep:
            need(row["bytes"] <= limits.selected_json_bytes, "SELECTED_RECEIPT_SIZE_CAP")
        raw = bytearray() if keep else None
        digest = hashlib.sha256()
        remaining = row["bytes"]
        while remaining:
            data = stream.read(min(65536, remaining))
            digest.update(data)
            if keep:
                raw.extend(data)
            remaining -= len(data)
        need(digest.hexdigest() == row["sha256"], "MEMBER_HASH_MISMATCH")
        need(stream.read((-row["bytes"]) % BLOCK) == b"\0" * ((-row["bytes"]) % BLOCK),
             "USTAR_NONZERO_PADDING")
        if keep:
            receipts[row["path"]] = _json(raw)
            need(type(receipts[row["path"]]) is dict, "SELECTED_RECEIPT_OBJECT")
    need(stream.read(2 * BLOCK) == b"\0" * (2 * BLOCK), "USTAR_END_MARKERS")
    stream.finish()
    return {"schema": SCHEMA, "status": "VERIFIED_NO_EXTRACTION_NO_EXECUTION",
            "entry_count": index["entry_count"], "archive_bytes": index["archive_bytes"],
            "members": index["members"], "receipts": receipts}


def main(argv=None):
    """Read-only local artifact verification; no extraction or approval action."""
    import argparse
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--index", required=True)
    parser.add_argument("--chunk", required=True, action="append")
    parser.add_argument("--profile", choices=("FIXTURE", "BUILD_ONLY"), default="FIXTURE")
    parser.add_argument("--expected-index-sha256", required=True)
    parser.add_argument("--receipt", action="append", default=[])
    args = parser.parse_args(argv)
    limits = FIXTURE_LIMITS if args.profile == "FIXTURE" else BUILD_ONLY_LIMITS
    fds = []
    try:
        need(len(args.chunk) == limits.chunk_count, "FIXED_CHUNK_DESCRIPTOR_COUNT")
        # Read-only path opens for previously exported artifacts; O_NOFOLLOW
        # rejects a leaf symlink. No archive member becomes a filesystem path.
        index_fd = os.open(args.index, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        fds.append(index_fd)
        for path in args.chunk:
            fds.append(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC))
        index = read_archive_index(index_fd, limits=limits,
                                   expected_sha256=args.expected_index_sha256)
        result = verify_archive(fds[1:], index, limits=limits, receipt_names=args.receipt)
        # Never print member contents, binary bytes or a private build receipt.
        print(json.dumps({"status": result["status"], "profile": limits.profile,
                          "entry_count": result["entry_count"],
                          "archive_bytes": result["archive_bytes"],
                          "selected_receipt_count": len(result["receipts"]),
                          "source_or_binary_approved": False,
                          "physical_execution_authorized": False}, sort_keys=True))
        return 0
    except (ArchiveError, OSError) as exc:
        reason = str(exc) if isinstance(exc, ArchiveError) else "ARTIFACT_READ_ERROR"
        print(json.dumps({"status": "ARCHIVE_VALIDATION_FAILED", "reason": reason},
                         sort_keys=True))
        return 2
    finally:
        for fd in reversed(fds):
            os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
