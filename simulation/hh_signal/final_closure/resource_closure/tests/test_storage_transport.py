"""Pure offline stream tests; no service, namespace, quota, stress or physics."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
MODULE = HERE.parent / "storage_transport.py"
if not MODULE.is_file():
    MODULE = HERE / "storage_transport.py"
SPEC = importlib.util.spec_from_file_location("storage_transport_under_test", MODULE)
s = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(s)
REV = "a" * 40
MAGIC = b"HH7I_DIAGNOSTIC_TRANSPORT_V1\n"
COMMIT = b"\nHH7I_ARTIFACT_COMMIT_V1\n"


def fixture():
    return {"controller.json": b'{"state":"OFFLINE_FIXTURE_ONLY"}',
            "mountinfo.bin": b"synthetic mount bytes\n",
            "namespace.json": b'{"evidence":"SYNTHETIC_NOT_KERNEL"}'}


def independent_parts(raw):
    assert raw.startswith(MAGIC)
    length = int.from_bytes(raw[len(MAGIC):len(MAGIC)+4], "big")
    document = json.loads(raw[len(MAGIC)+4:len(MAGIC)+4+length])
    payload = raw[len(MAGIC)+4+length:-(len(COMMIT)+33)]
    return document, payload


def independent_pack(document, payload, manifest_raw=None):
    if manifest_raw is None:
        manifest_raw = json.dumps(document, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=True, allow_nan=False).encode("ascii")
    body = MAGIC + len(manifest_raw).to_bytes(4, "big") + manifest_raw + payload
    return body + COMMIT + hashlib.sha256(body).digest() + b"\n"


class ShortWrite:
    def __init__(self, maximum):
        self.maximum = maximum
        self.raw = bytearray()

    def write(self, raw):
        part = raw[:self.maximum]
        self.raw.extend(part)
        return len(part)


class ShortRead(io.BytesIO):
    def read(self, count=-1):
        return super().read(min(count, 3))


class StorageTransportTests(unittest.TestCase):
    def encode(self, data=None):
        return s.encode_transport(fixture() if data is None else data, source_revision=REV)

    def reject(self, raw, reason=""):
        with self.assertRaisesRegex(s.TransportError, reason):
            s.verify_transport(raw, expected_revision=REV)

    def test_roundtrip_and_independent_wire_readback(self):
        data = fixture()
        raw = self.encode(data)
        report, decoded = s.verify_transport(raw, expected_revision=REV)
        self.assertEqual(decoded, data)
        self.assertEqual(report["payload_bytes"], sum(map(len, data.values())))
        self.assertEqual(report["transport_bytes"], len(raw))
        self.assertEqual(report["transport_sha256"], hashlib.sha256(raw).hexdigest())
        document, payload = independent_parts(raw)
        cursor = 0
        for row in document["artifacts"]:
            part = payload[cursor:cursor + row["bytes"]]
            self.assertEqual(part, data[row["name"]])
            self.assertEqual(hashlib.sha256(part).hexdigest(), row["sha256"])
            cursor += row["bytes"]
        self.assertEqual(cursor, len(payload))
        self.assertEqual(independent_pack(document, payload), raw)
        for key in ("persistent_allocated_capacity_verified", "persistent_inode_capacity_verified",
                    "durability_or_controller_success_asserted", "FULL_LAUNCH_ENVELOPE_VERIFIED"):
            self.assertIs(report[key], False)

    def test_short_writes_and_short_reads_preserve_exact_bytes(self):
        expected = self.encode()
        for maximum in (1, 7, 4095):
            sink = ShortWrite(maximum)
            with self.subTest(maximum=maximum):
                report = s.write_transport(sink, fixture(), source_revision=REV)
                self.assertEqual(bytes(sink.raw), expected)
                self.assertEqual(report["transport_bytes"], len(expected))
                self.assertEqual(s.verify_transport(ShortRead(expected), expected_revision=REV)[1], fixture())

    def test_ordinary_temporary_stream_fixture_is_not_capacity_evidence(self):
        with tempfile.TemporaryFile() as stream:
            report = s.write_transport(stream, fixture(), source_revision=REV)
            stream.seek(0)
            checked, data = s.verify_transport(stream, expected_revision=REV)
        self.assertEqual(report, checked)
        self.assertEqual(data, fixture())
        self.assertFalse(checked["persistent_allocated_capacity_verified"])

    def test_machine_readable_contract_matches_source_and_binding(self):
        config = HERE.parent / "config" / "storage_contract.json"
        if not config.is_file():
            config = HERE / "storage_contract.json"
        document = json.loads(config.read_text(encoding="utf-8-sig"))
        self.assertEqual(document, s.contract_document())
        canonical = json.dumps(document, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False).encode("ascii")
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), s.CONTRACT_SHA256)
        self.assertLess(sum(row["maximum_bytes"] for row in document["slots"]), 131072)

    def test_unknown_traversal_link_like_names_fail_before_first_write(self):
        for name in ("../mountinfo.bin", "/mountinfo.bin", "a/b", "mountinfo.bin/",
                     r"a\mountinfo.bin", "a\x00b", "symlink", "controller.JSON"):
            sink = io.BytesIO()
            with self.subTest(name=name), self.assertRaises(s.TransportError):
                s.write_transport(sink, {name: b"x"}, source_revision=REV)
            self.assertEqual(sink.getvalue(), b"")

    def test_wrong_count_container_and_payload_types_reject(self):
        for data in ({}, [], False, None, {"controller.json": b"{}",
                                         "failure.json": b"{}", "mountinfo.bin": b"",
                                         "namespace.json": b"{}", "extra": b""}):
            with self.subTest(data=data), self.assertRaises(s.TransportError):
                s.encode_transport(data, source_revision=REV)
        for raw in (False, None, "{}", bytearray(b"{}"), memoryview(b"{}")):
            with self.subTest(raw=repr(raw)), self.assertRaises(s.TransportError):
                self.encode({"controller.json": raw})

    def test_all_fixed_slot_caps_and_total_payload_are_enforced(self):
        at_cap = {}
        for name, cap, kind in s.SLOTS:
            at_cap[name] = b'{"v":"' + b"a"*(cap-8) + b'"}' if kind == "json_object" else b"x"*cap
        report, recovered = s.verify_transport(self.encode(at_cap), expected_revision=REV)
        self.assertEqual(report["payload_bytes"], 73728)
        self.assertEqual(recovered, at_cap)
        for name, cap, kind in s.SLOTS:
            over = b'{"v":"' + b"a"*(cap-7) + b'"}' if kind == "json_object" else b"x"*(cap+1)
            with self.subTest(name=name), self.assertRaisesRegex(s.TransportError, "SIZE_BOUND"):
                self.encode({name: over})

    def test_revision_and_stream_interfaces_fail_closed(self):
        for revision in (False, None, 1, "A"*40, "a"*39, "a"*41):
            with self.subTest(revision=revision):
                with self.assertRaisesRegex(s.TransportError, "EXACT_SOURCE"):
                    s.encode_transport(fixture(), source_revision=revision)
                with self.assertRaisesRegex(s.TransportError, "EXACT_SOURCE"):
                    s.verify_transport(self.encode(), expected_revision=revision)
        for stream in (False, None, [], b""):
            with self.subTest(stream=stream), self.assertRaises(s.TransportError):
                s.write_transport(stream, fixture(), source_revision=REV)
        for stream in (False, None, [], "not bytes"):
            with self.subTest(stream=stream), self.assertRaises(s.TransportError):
                s.verify_transport(stream, expected_revision=REV)

    def test_strict_payload_json_rejects_duplicates_nan_depth_and_noncanonical(self):
        for raw in (b'{"v":1,"v":2}', b'{"v":NaN}', b'{"v":Infinity}',
                    b'{"v":1e9999}', b'[]', b'{"x":"\xff"}', b'{ "v":1}',
                    b'{"v":' + b"["*20 + b"0" + b"]"*20 + b"}"):
            with self.subTest(raw=raw), self.assertRaises(s.TransportError):
                self.encode({"controller.json": raw})
        for value in ({1: "coercion"}, {"x": float("nan")}, {"x": float("inf")}, [], False):
            with self.subTest(value=value), self.assertRaises(s.TransportError):
                s.artifact_json(value)
        self.assertEqual(s.artifact_json({"v": True}), b'{"v":true}')

    def test_invalid_write_returns_reject_including_bool_and_no_progress(self):
        for value in (0, -1, None, True, "1", 1000000):
            class BadWrite:
                def write(self, raw):
                    return value
            with self.subTest(value=value), self.assertRaisesRegex(s.TransportError, "WRITE"):
                s.write_transport(BadWrite(), fixture(), source_revision=REV)

    def test_invalid_read_returns_reject_without_unbounded_read(self):
        for value in (b"", None, True, "text", bytearray(b"x"), b"x"*1000):
            class BadRead:
                def read(self, count):
                    return value
            with self.subTest(value=repr(value)), self.assertRaisesRegex(s.TransportError, "READ"):
                s.verify_transport(BadRead(), expected_revision=REV)

    def test_truncation_at_header_manifest_payload_and_commit_is_incomplete(self):
        raw = self.encode()
        header = len(MAGIC)+4
        manifest_size = int.from_bytes(raw[len(MAGIC):header], "big")
        for cut in (0, 1, len(MAGIC), header, header+1, header+manifest_size-1,
                    header+manifest_size+1, len(raw)-len(COMMIT)-33, len(raw)-1):
            with self.subTest(cut=cut):
                self.reject(raw[:cut], "INCOMPLETE")

    def test_extra_bytes_and_second_container_are_rejected(self):
        raw = self.encode()
        for extra in (b"x", b"\0", raw):
            with self.subTest(extra_bytes=len(extra)):
                self.reject(raw+extra, "TRAILING")

    def test_wrong_magic_and_unbounded_or_zero_manifest_length_reject_early(self):
        raw = self.encode()
        self.reject(b"X"+raw[1:], "MAGIC")
        for value in (0, 4097, 2**32-1):
            with self.subTest(value=value):
                self.reject(MAGIC+struct.pack(">I", value), "MANIFEST_SIZE_BOUND")

    def test_manifest_schema_scope_source_and_contract_are_not_receipt_flags(self):
        document, payload = independent_parts(self.encode())
        for key, value in (("schema", "other"), ("scope", "BUILD_ONLY"),
                           ("source_revision", "b"*40), ("storage_contract_sha256", "0"*64)):
            changed = copy.deepcopy(document)
            changed[key] = value
            with self.subTest(key=key):
                self.reject(independent_pack(changed, payload))
        for mutation in ("extra", "missing"):
            changed = copy.deepcopy(document)
            if mutation == "extra":
                changed["FULL_LAUNCH_ENVELOPE_VERIFIED"] = True
            else:
                del changed["scope"]
            with self.subTest(mutation=mutation):
                self.reject(independent_pack(changed, payload), "SCHEMA")

    def test_manifest_duplicate_json_keys_noncanonical_and_nonfinite_reject(self):
        document, payload = independent_parts(self.encode())
        canonical = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        candidates = (b'{"schema":"unused",' + canonical[1:],
                      canonical.replace(b'{"artifacts":', b'{ "artifacts":', 1),
                      canonical.replace(b'"bytes":', b'"bytes":NaN,"unused":', 1))
        for manifest_raw in candidates:
            with self.subTest(manifest_raw=manifest_raw[:50]):
                self.reject(independent_pack(document, payload, manifest_raw))

    def test_manifest_rows_count_order_duplicates_links_and_unsafe_entries_reject(self):
        document, payload = independent_parts(self.encode())
        changes = [[], document["artifacts"]*2, list(reversed(document["artifacts"])),
                   [document["artifacts"][0], document["artifacts"][0]]]
        for rows in changes:
            changed = copy.deepcopy(document)
            changed["artifacts"] = rows
            with self.subTest(rows=rows):
                self.reject(independent_pack(changed, payload))
        for name in ("../escape", "/tmp/escape", r"a\b", "unknown", "mountinfo.bin/"):
            changed = copy.deepcopy(document)
            changed["artifacts"][0]["name"] = name
            with self.subTest(name=name):
                self.reject(independent_pack(changed, payload), "FIXED_SLOT")
        changed = copy.deepcopy(document)
        changed["artifacts"][0]["linkname"] = "/escape"
        self.reject(independent_pack(changed, payload), "MANIFEST_SCHEMA")

    def test_manifest_length_bool_negative_oversize_and_bad_digest_types_reject(self):
        document, payload = independent_parts(self.encode())
        for key, values in (("bytes", (True, -1, 32769, "1", None)),
                            ("sha256", (False, None, "A"*64, "a"*63, "x"*64))):
            for value in values:
                changed = copy.deepcopy(document)
                changed["artifacts"][0][key] = value
                with self.subTest(key=key, value=value):
                    self.reject(independent_pack(changed, payload))

    def test_payload_hash_is_checked_before_global_commit(self):
        document, payload = independent_parts(self.encode())
        mutated = bytes([payload[0] ^ 1]) + payload[1:]
        self.reject(independent_pack(document, mutated), "ARTIFACT_SHA256_MISMATCH")

    def test_json_reader_checks_payload_schema_even_with_correct_hash_and_commit(self):
        document, payload = independent_parts(self.encode({"controller.json": b"{}"}))
        for body in (b"[]", b'{"v":NaN}', b'{"v":1,"v":2}', b"{ }"):
            changed = copy.deepcopy(document)
            changed["artifacts"][0]["bytes"] = len(body)
            changed["artifacts"][0]["sha256"] = hashlib.sha256(body).hexdigest()
            with self.subTest(body=body):
                self.reject(independent_pack(changed, body))

    def test_commit_digest_marker_and_final_newline_are_required(self):
        raw = self.encode()
        for offset in (-1, -2, -(len(COMMIT)+33)):
            changed = bytearray(raw)
            changed[offset] ^= 1
            with self.subTest(offset=offset):
                self.reject(bytes(changed), "COMMIT_TRAILER")

    def test_controller_loss_preserves_prefix_but_never_completed_receipt(self):
        class LostController(ShortWrite):
            def write(self, raw):
                if len(self.raw) > 100:
                    raise OSError("SYNTHETIC_CONTROLLER_LOSS")
                return super().write(raw)
        sink = LostController(100)
        with self.assertRaisesRegex(OSError, "CONTROLLER_LOSS"):
            s.write_transport(sink, fixture(), source_revision=REV)
        self.assertGreater(len(sink.raw), 0)
        self.reject(bytes(sink.raw), "INCOMPLETE")
        self.assertNotIn(COMMIT, sink.raw)

    def test_empty_binary_slot_is_transport_not_mount_validity(self):
        report, artifacts = s.verify_transport(self.encode({"mountinfo.bin": b""}), expected_revision=REV)
        self.assertEqual(artifacts, {"mountinfo.bin": b""})
        self.assertEqual(report["status"], "PASS_LOGICAL_ARTIFACT_TRANSPORT_ONLY")
        self.assertFalse(report["FULL_LAUNCH_ENVELOPE_VERIFIED"])


if __name__ == "__main__":
    unittest.main()

