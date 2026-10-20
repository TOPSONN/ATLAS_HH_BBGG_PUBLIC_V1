"""Fixed-slot local diagnostic transport; no filesystem or execution APIs.

S3 proves only logical bytes, names, schema and integrity. It does not establish
allocated blocks, inodes, metadata, journal, durability or a persistent quota.
A committed artifact is not proof that its controller or kernel workflow passed.
S4 live execution and every formal build remain separately gated by the caller.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import struct

MAGIC = b"HH7I_DIAGNOSTIC_TRANSPORT_V1\n"
COMMIT = b"\nHH7I_ARTIFACT_COMMIT_V1\n"
SCHEMA = "PHASE7I_DIAGNOSTIC_TRANSPORT_V1"
SCOPE = "VOLATILE_DIAGNOSTIC_ONLY"
MANIFEST_LIMIT = 4096
TRANSPORT_LIMIT = 131072
JSON_DEPTH_LIMIT = 16
SLOTS = (("controller.json", 32768, "json_object"),
         ("failure.json", 8192, "json_object"),
         ("mountinfo.bin", 16384, "bytes"),
         ("namespace.json", 16384, "json_object"))


class TransportError(ValueError):
    """Invalid, incomplete or excessive logical transport; never authorizes I/O."""


def _need(value, reason):
    if not value:
        raise TransportError(reason)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=True).encode("ascii")


def contract_document():
    """Return an independent fresh source contract, not a mutable approval flag."""
    return {
        "schema": "PHASE7I_STORAGE_TRANSPORT_CONTRACT_V1",
        "scope": SCOPE,
        "route": "S3_FIXED_SLOT_LOGICAL_TRANSPORT_WITH_S4_ONLY_PROPOSAL",
        "slots": [{"name": n, "maximum_bytes": cap, "encoding": enc}
                  for n, cap, enc in SLOTS],
        "maximum_artifacts": 4,
        "maximum_payload_bytes": 73728,
        "maximum_manifest_bytes": MANIFEST_LIMIT,
        "maximum_transport_bytes": TRANSPORT_LIMIT,
        "json_depth_limit": JSON_DEPTH_LIMIT,
        "source_revision": "EXACT_LOWERCASE_40_HEX_REQUIRED_FROM_CALLER",
        "completion": "TRAILER_DIGEST_AND_EOF_REQUIRED_ARTIFACT_ONLY",
        "path_opening_or_extraction": False,
        "persistent_allocated_capacity_verified": False,
        "persistent_inode_capacity_verified": False,
        "metadata_journal_extents_control_plane_bound": "UNVERIFIED",
        "durability_and_controller_success": "NOT_ASSERTED_BY_TRANSPORT",
        "formal_build_authorized": False,
        "FULL_LAUNCH_ENVELOPE_VERIFIED": False,
    }


CONTRACT_SHA256 = hashlib.sha256(_canonical(contract_document())).hexdigest()


def _revision(value):
    _need(type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None,
          "EXACT_SOURCE_REVISION_REQUIRED")


def _duplicates(pairs):
    value = {}
    for key, item in pairs:
        _need(key not in value, "DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def _constant(value):
    raise TransportError("NONFINITE_JSON_CONSTANT")


def _depth(value, depth=0):
    _need(depth <= JSON_DEPTH_LIMIT, "JSON_DEPTH_BOUND")
    if isinstance(value, dict):
        _need(all(type(key) is str for key in value), "JSON_STRING_KEYS_REQUIRED")
        for item in value.values():
            _depth(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, depth + 1)


def _json_object(raw):
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_duplicates,
                           parse_constant=_constant)
        _need(type(value) is dict, "JSON_OBJECT_REQUIRED")
        _depth(value)
        _need(_canonical(value) == raw, "CANONICAL_JSON_REQUIRED")
        return value
    except TransportError:
        raise
    except (UnicodeError, ValueError, TypeError, OverflowError, RecursionError) as error:
        raise TransportError("INVALID_JSON_OBJECT") from error


def artifact_json(value):
    """Canonicalize a bounded JSON object; no runtime/physics claims are checked."""
    _need(type(value) is dict, "JSON_OBJECT_REQUIRED")
    try:
        _depth(value)
        raw = _canonical(value)
        _need(len(raw) <= 32768, "JSON_ARTIFACT_BOUND")
        _json_object(raw)
        return raw
    except TransportError:
        raise
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise TransportError("INVALID_JSON_OBJECT") from error


def _prepare(artifacts, source_revision):
    _revision(source_revision)
    _need(type(artifacts) is dict and 1 <= len(artifacts) <= len(SLOTS),
          "FIXED_ARTIFACT_COUNT")
    allowed = {name: (cap, encoding) for name, cap, encoding in SLOTS}
    _need(all(type(name) is str and name in allowed for name in artifacts),
          "FIXED_SLOT_NAME_REQUIRED")
    rows, payloads = [], []
    for name in sorted(artifacts):
        raw = artifacts[name]
        cap, encoding = allowed[name]
        _need(type(raw) is bytes, "IMMUTABLE_BYTES_REQUIRED")
        _need(len(raw) <= cap, "ARTIFACT_SIZE_BOUND")
        if encoding == "json_object":
            _json_object(raw)
        rows.append({"name": name, "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest()})
        payloads.append(raw)
    document = {"schema": SCHEMA, "scope": SCOPE,
                "source_revision": source_revision,
                "storage_contract_sha256": CONTRACT_SHA256, "artifacts": rows}
    manifest = _canonical(document)
    _need(len(manifest) <= MANIFEST_LIMIT, "MANIFEST_SIZE_BOUND")
    prefix = MAGIC + struct.pack(">I", len(manifest)) + manifest
    digest = hashlib.sha256()
    digest.update(prefix)
    for raw in payloads:
        digest.update(raw)
    trailer = COMMIT + digest.digest() + b"\n"
    total = len(prefix) + sum(map(len, payloads)) + len(trailer)
    _need(total <= TRANSPORT_LIMIT, "TRANSPORT_SIZE_BOUND")
    return (prefix, *payloads, trailer), document, total


def write_transport(stream, artifacts, *, source_revision):
    """Write to the caller's stream; partial failure has no completed return.

    This function opens no path, flushes no host file and grants no persistence.
    A sink must obey write semantics; this API cannot constrain an arbitrary
    sink's hidden allocations or other side effects.
    """
    _need(callable(getattr(stream, "write", None)), "WRITE_STREAM_REQUIRED")
    pieces, manifest, total = _prepare(artifacts, source_revision)
    written, digest = 0, hashlib.sha256()
    for piece in pieces:
        offset = 0
        while offset < len(piece):
            part = piece[offset:offset + 4096]
            count = stream.write(part)
            _need(type(count) is int and 0 < count <= len(part),
                  "INVALID_OR_NO_PROGRESS_WRITE")
            digest.update(part[:count])
            written += count
            _need(written <= TRANSPORT_LIMIT, "TRANSPORT_SIZE_BOUND")
            offset += count
    _need(written == total, "TRANSPORT_WRITE_SIZE_MISMATCH")
    return _summary(manifest, total, digest.hexdigest())


def encode_transport(artifacts, *, source_revision):
    stream = io.BytesIO()
    write_transport(stream, artifacts, source_revision=source_revision)
    return stream.getvalue()


def _read_exact(stream, count):
    parts = []
    remaining = count
    while remaining:
        raw = stream.read(remaining)
        _need(type(raw) is bytes and 0 < len(raw) <= remaining,
              "INCOMPLETE_OR_INVALID_READ")
        parts.append(raw)
        remaining -= len(raw)
    return b"".join(parts)


def _summary(manifest, total, digest):
    return {"status": "PASS_LOGICAL_ARTIFACT_TRANSPORT_ONLY",
            "scope": SCOPE, "source_revision": manifest["source_revision"],
            "storage_contract_sha256": CONTRACT_SHA256,
            "artifacts": manifest["artifacts"],
            "artifact_count": len(manifest["artifacts"]),
            "payload_bytes": sum(row["bytes"] for row in manifest["artifacts"]),
            "transport_bytes": total, "transport_sha256": digest,
            "persistent_allocated_capacity_verified": False,
            "persistent_inode_capacity_verified": False,
            "durability_or_controller_success_asserted": False,
            "FULL_LAUNCH_ENVELOPE_VERIFIED": False}


def verify_transport(stream, *, expected_revision):
    """Independently consume a strict fixed-slot stream; return (summary, bytes).

    No writer preparation/encoding routine is used for acceptance. The returned
    payload dictionary is PRIVATE local evidence. The summary is logical-only;
    it still requires publication review and independently bound source/kernel
    evidence before any stronger interpretation.
    """
    _revision(expected_revision)
    if type(stream) is bytes:
        stream = io.BytesIO(stream)
    _need(callable(getattr(stream, "read", None)), "READ_STREAM_REQUIRED")
    prefix = _read_exact(stream, len(MAGIC) + 4)
    _need(prefix[:len(MAGIC)] == MAGIC, "TRANSPORT_MAGIC")
    manifest_size = struct.unpack(">I", prefix[-4:])[0]
    _need(1 <= manifest_size <= MANIFEST_LIMIT, "MANIFEST_SIZE_BOUND")
    manifest_raw = _read_exact(stream, manifest_size)
    manifest = _json_object(manifest_raw)
    _need(set(manifest) == {"schema", "scope", "source_revision",
                          "storage_contract_sha256", "artifacts"},
          "MANIFEST_SCHEMA")
    _need(manifest["schema"] == SCHEMA and manifest["scope"] == SCOPE,
          "MANIFEST_SCOPE")
    _need(manifest["source_revision"] == expected_revision, "SOURCE_REVISION_MISMATCH")
    _need(manifest["storage_contract_sha256"] == CONTRACT_SHA256,
          "STORAGE_CONTRACT_MISMATCH")
    rows = manifest["artifacts"]
    _need(type(rows) is list and 1 <= len(rows) <= 4, "FIXED_ARTIFACT_COUNT")
    slot_caps = {name: cap for name, cap, _ in SLOTS}
    slot_encodings = {name: enc for name, _, enc in SLOTS}
    prior, total_payload = "", 0
    for row in rows:
        _need(type(row) is dict and set(row) == {"name", "bytes", "sha256"},
              "ARTIFACT_MANIFEST_SCHEMA")
        name, size, sha = row["name"], row["bytes"], row["sha256"]
        _need(type(name) is str and name in slot_caps and name > prior,
              "FIXED_SLOT_ORDER_OR_DUPLICATE")
        _need(type(size) is int and 0 <= size <= slot_caps[name], "ARTIFACT_SIZE_BOUND")
        _need(type(sha) is str and re.fullmatch(r"[0-9a-f]{64}", sha) is not None,
              "ARTIFACT_SHA256_SCHEMA")
        prior = name
        total_payload += size
    total = len(prefix) + manifest_size + total_payload + len(COMMIT) + 33
    _need(total <= TRANSPORT_LIMIT, "TRANSPORT_SIZE_BOUND")
    body_digest = hashlib.sha256(prefix + manifest_raw)
    transport_digest = hashlib.sha256(prefix + manifest_raw)
    artifacts = {}
    for row in rows:
        raw = _read_exact(stream, row["bytes"])
        _need(hashlib.sha256(raw).hexdigest() == row["sha256"], "ARTIFACT_SHA256_MISMATCH")
        if slot_encodings[row["name"]] == "json_object":
            _json_object(raw)
        body_digest.update(raw)
        transport_digest.update(raw)
        artifacts[row["name"]] = raw
    trailer = _read_exact(stream, len(COMMIT) + 33)
    _need(trailer == COMMIT + body_digest.digest() + b"\n", "COMMIT_TRAILER_MISMATCH")
    transport_digest.update(trailer)
    extra = stream.read(1)
    _need(type(extra) is bytes and extra == b"", "TRAILING_OR_INVALID_DATA")
    return _summary(manifest, total, transport_digest.hexdigest()), artifacts

