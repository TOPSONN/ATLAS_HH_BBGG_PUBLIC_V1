"""Bounded controller I/O; no process creation or kernel/service dispatch.

Private parent evidence stays in a finite RAM buffer. This is intentionally
volatile: it cannot certify durable receipts, allocated disk or controller-loss
recovery. The child pipe is private to the same service, never a host export.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import selectors
import subprocess
import time

PUBLIC_CAP = 65536
PRIVATE_CAP = 131072
RECORD_CAP = 32768
FAILURE_RESERVE = 2048
MAX_RECORDS = 128


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def contains_private(value, depth=0):
    require(depth <= 32, 'EVIDENCE_DEPTH_BOUND')
    if type(value) is dict:
        found = value.get('kind') in ('PRIVATE_MOUNTINFO_RAW', 'PRIVATE_CHILD_STDERR')
        found |= any(k in value for k in ('raw_mountinfo', 'mountinfo_bytes_base64'))
        for item in value.values():
            found |= contains_private(item, depth+1)
        return found
    if type(value) is list:
        found = False
        for item in value:
            found |= contains_private(item, depth+1)
        return found
    if type(value) is str:
        # Reuse the reviewed pure publication detector for serialized JSON,
        # Unicode escapes, Markdown wrappers and raw mount lines. No audit/Git
        # operation is called; uncertainty is conservatively private.
        from .recovery_publication import reject_private_mount_capture
        try:
            reject_private_mount_capture(value)
        except (ValueError, RecursionError):
            return True
    return False


def has_incomplete_capture(value, depth=0):
    """Propagate known partial capture claims; this is not a sequence verifier.

    Complete flag observations and RAM retention are separate. Unparseable
    serialized private evidence is conservatively unknown/incomplete.
    """
    if depth > 32:
        return True
    if type(value) is dict:
        if value.get('kind') in ('PRIVATE_MOUNTINFO_RAW', 'MOUNTINFO_CAPTURE_SAFE_METADATA'):
            if value.get('complete') is not True:
                return True
        if 'private_capture_complete' in value and value['private_capture_complete'] is not True:
            return True
        return any(has_incomplete_capture(item, depth+1) for item in value.values())
    if type(value) is list:
        return any(has_incomplete_capture(item, depth+1) for item in value)
    if type(value) is str and contains_private(value):
        try:
            nested = json.loads(value)
        except (ValueError, RecursionError):
            return True
        return has_incomplete_capture(nested, depth+1)
    return False


class EvidenceBuffer:
    """One run's logical byte budget, with a reserved terminal failure record.

    A write error consumes its reservation before writing: retry cannot reset
    the accounting or duplicate a partly written record. No file is opened.
    Private RAM may disappear on process loss; it is never durable retention.
    """
    def __init__(self, *, private_pipe=False):
        require(type(private_pipe) is bool, 'PRIVATE_PIPE_BOOLEAN_REQUIRED')
        self.private_pipe = private_pipe
        self.public_bytes = 0
        self.records = 0
        self.private_bytes = 0
        self.private_records = []
        self.incomplete = False
        self.capture_incomplete = False

    def _retain_private(self, raw):
        if self.private_bytes + len(raw) > PRIVATE_CAP:
            self.incomplete = True
            return False
        self.private_records.append(raw)
        self.private_bytes += len(raw)
        return True

    def emit(self, value, write=None):
        require(type(value) is dict, 'EVIDENCE_OBJECT_REQUIRED')
        private = contains_private(value)
        raw = canonical(value) + b'\n'
        require(len(raw) <= RECORD_CAP, 'BOUNDED_RECORD_REQUIRED')
        self.capture_incomplete |= has_incomplete_capture(value)
        terminal = value.get('kind') == 'BLOCKED'
        unsafe_claim = terminal and any(value.get(key, False) is not False for key in (
            'FULL_LAUNCH_ENVELOPE_VERIFIED', 'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'))
        if terminal and ((private and not self.private_pipe) or
                         len(raw) > FAILURE_RESERVE or unsafe_claim):
            original_hash = hashlib.sha256(raw).hexdigest()
            original_bytes = len(raw)
            retained = self._retain_private(raw)
            shown = {'kind': 'BLOCKED',
                     'reason': 'PRIVATE_OVERSIZED_OR_UNSAFE_FAILURE_RECORD',
                     'original_record_sha256': original_hash,
                     'original_record_bytes': original_bytes,
                     'original_record_retained_in_volatile_ram': retained,
                     'retention_scope': 'CURRENT_PROCESS_VOLATILE_RAM_ONLY',
                     'private_capture_complete': not (self.incomplete or self.capture_incomplete),
                     'FULL_LAUNCH_ENVELOPE_VERIFIED': False,
                     'FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED': False}
            cleanup = value.get('controller_pipe_cleanup_status')
            if cleanup in ('CLOSED', 'UNKNOWN', 'NOT_OBSERVED'):
                shown['controller_pipe_cleanup_status'] = cleanup
            raw = canonical(shown) + b'\n'
        elif private and not self.private_pipe:
            require(self._retain_private(raw), 'PRIVATE_VOLATILE_EVIDENCE_INCOMPLETE')
            shown = {'kind': 'LOCAL_PRIVATE_EVIDENCE_BUFFERED',
                     'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                     'storage': 'BOUNDED_VOLATILE_RAM_ONLY',
                     'durable_receipt_verified': False}
            raw = canonical(shown) + b'\n'
        elif value.get('kind') in ('MOUNT_INVENTORY_SAFE', 'CLASSIFIED_MOUNT_POLICY_SAFE',
                                   'NAMESPACE_READBACK', 'GUARD_DENIAL_READBACK'):
            # Keep the exact bounded data in volatile memory, publish only its
            # reference. Repeating whole proofs at three stages must not use
            # the output budget before the reserved terminal can be written.
            require(self._retain_private(raw), 'PRIVATE_VOLATILE_EVIDENCE_INCOMPLETE')
            shown = {'kind': value['kind'], 'evidence_sha256': hashlib.sha256(raw).hexdigest(),
                     'evidence_bytes': len(raw), 'storage': 'BOUNDED_VOLATILE_RAM_ONLY',
                     'durable_receipt_verified': False}
            if type(value.get('stage')) is str and len(value['stage']) <= 64:
                shown['stage'] = value['stage']
            raw = canonical(shown) + b'\n'
        if terminal:
            require(len(raw) <= FAILURE_RESERVE, 'FAILURE_RECEIPT_BOUND')
        cap = PUBLIC_CAP if terminal else PUBLIC_CAP - FAILURE_RESERVE
        require(self.records < MAX_RECORDS - (0 if terminal else 1), 'RUN_RECORD_BOUND')
        require(self.public_bytes + len(raw) <= cap, 'RUN_OUTPUT_BOUND')
        self.public_bytes += len(raw)
        self.records += 1
        write = os.write if write is None else write
        offset = 0
        while offset < len(raw):
            count = write(1, raw[offset:])
            require(type(count) is int and 0 < count <= len(raw)-offset,
                    'SHORT_RECEIPT_WRITE')
            offset += count


    def mount_capture(self, expected_sha256, stage):
        chunks = {}
        count = size = None
        for raw in self.private_records:
            row = json.loads(raw)
            if row.get('kind') != 'PRIVATE_MOUNTINFO_RAW' or row.get('stage') != stage:
                continue
            require(row.get('raw_sha256') == expected_sha256 and row.get('complete') is True,
                    'MOUNT_CAPTURE_IDENTITY_OR_COMPLETENESS')
            n, index, length = row.get('chunks'), row.get('chunk_index'), row.get('raw_bytes')
            require(type(n) is int and 1 <= n <= 16 and type(index) is int and 0 <= index < n and
                    type(length) is int and 0 <= length <= 16384, 'MOUNT_CAPTURE_FIELDS')
            require(count in (None, n) and size in (None, length), 'MOUNT_CAPTURE_AMBIGUOUS')
            count, size = n, length
            block = base64.b64decode(row['base64'], validate=True)
            require(len(block) <= 1024 and index not in chunks, 'MOUNT_CAPTURE_CHUNK_BOUND_OR_DUPLICATE')
            chunks[index] = block
        require(count is not None and set(chunks) == set(range(count)), 'MOUNT_CAPTURE_INCOMPLETE')
        raw = b''.join(chunks[i] for i in range(count))
        require(len(raw) == size and hashlib.sha256(raw).hexdigest() == expected_sha256,
                'MOUNT_CAPTURE_SHA256_MISMATCH')
        return raw


    def summary(self):
        return {'public_bytes': self.public_bytes, 'records': self.records,
                'private_bytes': self.private_bytes,
                'private_sha256': hashlib.sha256(b''.join(self.private_records)).hexdigest(),
                'private_buffer_complete': not self.incomplete,
                'private_capture_complete': not (self.incomplete or self.capture_incomplete),
                'scope': 'VOLATILE_LOGICAL_IO_ONLY',
                'persistent_allocated_capacity_verified': False,
                'controller_loss_receipt_retention_verified': False}


def collect_child(proc, timeout, *, selector_factory=selectors.DefaultSelector,
                  clock=time.monotonic, read=os.read, set_blocking=os.set_blocking):
    """Bound reads during execution, then close both pipes on every path.

    Caller owns process-group termination and wait on failure. Pipe-close
    failure remains UNKNOWN and does not replace the original read/timeout
    exception. No command, process or cgroup is created here.
    """
    require(type(timeout) in (int, float) and 0 < timeout <= 1, 'CHILD_TIMEOUT_BOUND')
    deadline = clock() + timeout
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    caps = {'stdout': 65536, 'stderr': 8192}
    streams = [getattr(proc, name) for name in buffers]
    original_error = None
    try:
        with selector_factory() as selector:
            for name, stream in zip(buffers, streams):
                fd = stream.fileno()
                set_blocking(fd, False)
                selector.register(fd, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = deadline - clock()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired('FIXED_INERT_CHILD', timeout)
                for key, _ in selector.select(min(remaining, .02)):
                    name = key.data
                    request = min(4096, caps[name] - len(buffers[name]) + 1)
                    try:
                        block = read(key.fd, request)
                    except BlockingIOError:
                        continue
                    require(type(block) is bytes and len(block) <= request, 'CHILD_READ_BOUND')
                    if not block:
                        selector.unregister(key.fd)
                        continue
                    buffers[name].extend(block)
                    require(len(buffers[name]) <= caps[name], 'INERT_CHILD_FAILED_OR_OUTPUT_BOUND')
            remaining = deadline - clock()
            if remaining <= 0:
                raise subprocess.TimeoutExpired('FIXED_INERT_CHILD', timeout)
            proc.wait(timeout=remaining)
        return bytes(buffers['stdout']), bytes(buffers['stderr'])
    except BaseException as error:
        original_error = error
        raise
    finally:
        close_failed = False
        for stream in streams:
            try:
                stream.close()
            except BaseException:
                close_failed = True
        status = 'UNKNOWN' if close_failed else 'CLOSED'
        proc.controller_pipe_cleanup_status = status
        if original_error is not None:
            original_error.controller_pipe_cleanup_status = status
        elif close_failed:
            error = ValueError('CHILD_PIPE_CLOSE_FAILED')
            error.controller_pipe_cleanup_status = status
            raise error


def decode_records(raw):
    require(type(raw) is bytes and len(raw) <= 65536, 'CHILD_STDOUT_BOUND')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'CHILD_DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('CHILD_NONFINITE_JSON')
    lines = raw.splitlines()
    require(lines and len(lines) <= 24 and all(lines), 'CHILD_PROTOCOL_RECORD_BOUND')
    require(all(len(line) + 1 <= RECORD_CAP for line in lines), 'CHILD_RECORD_BYTE_BOUND')
    result = [json.loads(line, object_pairs_hook=pairs, parse_constant=constant) for line in lines]
    require(all(type(x) is dict for x in result), 'CHILD_PROTOCOL_OBJECT_REQUIRED')
    for value in result:
        contains_private(value)
        canonical(value)  # Reject overflow-to-infinity values such as 1e9999.
    require(raw.endswith(b'\n'), 'CHILD_PROTOCOL_INCOMPLETE_FINAL_LF')
    return result


_current = EvidenceBuffer()


def reset(*, private_pipe=False):
    global _current
    _current = EvidenceBuffer(private_pipe=private_pipe)


def emit(value):
    _current.emit(value)


def summary():
    return _current.summary()


def mount_capture(expected_sha256, stage):
    return _current.mount_capture(expected_sha256, stage)
