"""Fixed-slot evidence protocol with real ordinary-file offline fixtures.

This is NOT a production device/writer adapter. No native results can be
encoded. Runtime UID separation, a bounded filesystem and collector placement
must be independently provisioned. fsync acknowledgement is not a proof of
power-loss behavior of an unattested storage stack.
"""
from __future__ import annotations
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import threading
from .device_policy import need, integer, canonical, text, path, same

SLOT_BYTES = 4096
LANES = {'checkpoint': (0, 1, 2, 3), 'postmortem': (4, 5), 'failure': (6, 7)}
NAMES = tuple('slot_%02d.evidence' % i for i in range(8))
MAGIC = b'HHEVID1\0'
HEADER = struct.Struct('>8sI32s')
COMMIT = b'HH_COMMIT_V1!'
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')


class EvidenceError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise EvidenceError(reason)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _write_all(fd, data, offset=0):
    while data:
        count = os.pwrite(fd, data, offset)
        require(type(count) is int and 0 < count <= len(data), 'WRITE_NO_PROGRESS')
        data, offset = data[count:], offset + count


def validate_event(event):
    require(type(event) is dict and set(event) == {
        'event_id', 'kind', 'monotonic_ns', 'observer', 'worker_state',
        'cause', 'resources', 'cgroup', 'raw_sha256', 'native_result'}, 'EVENT_FIELDS')
    require(type(event['event_id']) is str and UUID.fullmatch(event['event_id']),
            'EVENT_ID')
    require(type(event['kind']) is str and event['kind'] in LANES and integer(event['monotonic_ns'], 1),
            'EVENT_KIND_OR_CLOCK')
    require(event['observer'] == 'independent_collector', 'COLLECTOR_ATTRIBUTION')
    require(event['worker_state'] in ('RUNNING', 'DEAD_OBSERVED', 'UNKNOWN') and
            text(event['cause']), 'EVENT_STATE')
    require(event['native_result'] is None, 'NATIVE_RESULT_RECONSTRUCTION_FORBIDDEN')
    resources = event['resources']
    require(type(resources) is dict and set(resources) ==
            {'CPU_usec', 'wall_ns', 'memory_peak_bytes', 'swap_peak_bytes',
             'cgroup_dev', 'cgroup_inode', 'MainPID'}, 'RESOURCE_FIELDS')
    require(all(x is None or integer(x) for x in resources.values()), 'RESOURCE_VALUE')
    refs = event['raw_sha256']
    require(type(refs) is list and len(refs) <= 16 and
            all(type(x) is str and HEX.fullmatch(x) for x in refs) and
            len(set(refs)) == len(refs), 'RAW_REFERENCE')
    if event['kind'] == 'postmortem':
        require(event['worker_state'] == 'DEAD_OBSERVED' and refs and
                all(resources[k] is not None for k in
                    ('cgroup_dev', 'cgroup_inode', 'MainPID')), 'POSTMORTEM_RAW_BINDING')
        require(integer(resources['MainPID'], 1) and integer(resources['cgroup_inode'], 1),
                'POSTMORTEM_POSITIVE_PID_INODE')
        group = event['cgroup']
        require(type(group) is dict and set(group) ==
                {'unit', 'invocation_id', 'path', 'dev', 'inode', 'MainPID', 'boot_id'} and
                type(group['unit']) is str and
                re.fullmatch(r'atlas-hh-[a-z0-9-]{1,96}\.service', group['unit']) and
                type(group['invocation_id']) is str and
                re.fullmatch(r'[0-9a-f]{32}', group['invocation_id']) and
                path(group['path']) and group['path'].startswith('/sys/fs/cgroup/') and
                type(group['boot_id']) is str and UUID.fullmatch(group['boot_id']) and
                same([group['dev'], group['inode'], group['MainPID']],
                     [resources['cgroup_dev'], resources['cgroup_inode'], resources['MainPID']]),
                'POSTMORTEM_CGROUP_IDENTITY')
    else:
        require(event['cgroup'] is None, 'UNVERIFIED_CGROUP_CLAIM')
    if event['kind'] == 'checkpoint':
        require(event['worker_state'] == 'RUNNING', 'CHECKPOINT_REQUIRES_RUNNING_WORKER')
    if event['kind'] == 'failure':
        require(event['worker_state'] == 'UNKNOWN', 'FAILURE_MUST_NOT_INVENT_TERMINAL')


class FixedSlotStore:
    """Single trusted collector API; fixture files are bounded to32KiB.

    Each occupied slot is never reused, including torn slots. Worker isolation
    is a DEPLOYMENT requirement, not furnished by advisory locking or this API.
    """
    def __init__(self, directory, identity, *, create=False, offline_fixture_only=False):
        require(offline_fixture_only is True, 'PRODUCTION_WRITER_NOT_APPROVED')
        require(type(identity) is dict and set(identity) ==
                {'source_revision', 'source_sha256', 'run_id', 'stage', 'collector_boot_id'},
                'IDENTITY_FIELDS')
        require(type(identity['source_revision']) is str and
                re.fullmatch(r'[0-9a-f]{40}', identity['source_revision']) and
                type(identity['source_sha256']) is str and HEX.fullmatch(identity['source_sha256'])
                and type(identity['run_id']) is str and UUID.fullmatch(identity['run_id'])
                and type(identity['collector_boot_id']) is str and UUID.fullmatch(identity['collector_boot_id'])
                and text(identity['stage'], 64), 'IDENTITY_ENCODING')
        self._identity_raw = canonical(identity)
        self._owner_thread = threading.get_ident()
        self._append_lock = threading.Lock()
        self.path = Path(directory)
        require(self.path.is_absolute() and self.path.resolve() == self.path,
                'NONCANONICAL_FIXTURE_PATH')
        self.fd = None
        if create:
            os.mkdir(self.path, 0o700)  # existing directory is never overwritten
        self.fd = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY |
                          os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            st = os.fstat(self.fd)
            require(stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid() and
                    stat.S_IMODE(st.st_mode) == 0o700, 'DIRECTORY_METADATA')
            self.directory_instance = (st.st_dev, st.st_ino)
            if create:
                for name in NAMES:
                    fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL |
                                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=self.fd)
                    try:
                        _write_all(fd, b'\0' * SLOT_BYTES)
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                os.fsync(self.fd)
                parent = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY |
                                 os.O_NOFOLLOW | os.O_CLOEXEC)
                try:
                    os.fsync(parent)
                finally:
                    os.close(parent)
            self._raw_slots()
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    @property
    def identity(self):
        return json.loads(self._identity_raw)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _open_slot(self, index, write=False):
        require(self.fd is not None, 'STORE_CLOSED')
        st = os.fstat(self.fd)
        require((st.st_dev, st.st_ino) == self.directory_instance, 'DIRECTORY_INSTANCE')
        fd = os.open(NAMES[index], (os.O_RDWR if write else os.O_RDONLY) |
                     os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.fd)
        try:
            st = os.fstat(fd)
            require(stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid() and
                    stat.S_IMODE(st.st_mode) == 0o600 and st.st_nlink == 1 and
                    st.st_size == SLOT_BYTES and st.st_blocks * 512 >= SLOT_BYTES,
                    'SLOT_METADATA')
        except BaseException:
            os.close(fd)
            raise
        return fd

    def _raw_slots(self):
        require(set(os.listdir(self.fd)) == set(NAMES), 'MISSING_OR_EXTRA_SLOT')
        raw = []
        for index in range(8):
            fd = self._open_slot(index)
            try:
                data = os.pread(fd, SLOT_BYTES + 1, 0)
            finally:
                os.close(fd)
            require(len(data) == SLOT_BYTES, 'SHORT_SLOT')
            raw.append(data)
        return raw

    def _decode(self, raw, index):
        require(len(raw) == SLOT_BYTES, 'FRAME_SIZE')
        magic, length, digest = HEADER.unpack(raw[:HEADER.size])
        require(magic == MAGIC and 0 < length <= SLOT_BYTES - HEADER.size - len(COMMIT),
                'FRAME_HEADER')
        require(raw[-len(COMMIT):] == COMMIT, 'TORN_OR_UNCOMMITTED_SLOT')
        payload = raw[HEADER.size:HEADER.size + length]
        require(_sha(payload) == digest.hex() and
                raw[HEADER.size + length:-len(COMMIT)] ==
                b'\0' * (SLOT_BYTES - HEADER.size - length - len(COMMIT)), 'FRAME_HASH_OR_PADDING')
        def pairs(items):
            result = {}
            for key, value in items:
                require(key not in result, 'DUPLICATE_JSON_KEY')
                result[key] = value
            return result
        try:
            def nonfinite(value):
                raise EvidenceError('NONFINITE_FRAME_JSON')
            record = json.loads(payload, object_pairs_hook=pairs, parse_constant=nonfinite)
        except (ValueError, UnicodeDecodeError) as error:
            raise EvidenceError('FRAME_JSON') from error
        require(type(record) is dict and set(record) ==
                {'identity', 'sequence', 'slot', 'event'}, 'RECORD_FIELDS')
        require(canonical(record['identity']) == self._identity_raw and
                type(record['slot']) is int and record['slot'] == index and
                integer(record['sequence'], 1) and record['sequence'] <= 8,
                'REPLAY_OR_FOREIGN_IDENTITY')
        validate_event(record['event'])
        if record['event']['cgroup'] is not None:
            require(record['event']['cgroup']['boot_id'] == self.identity['collector_boot_id'],
                    'FOREIGN_BOOT_CLOCK_DOMAIN')
        require(index in LANES[record['event']['kind']], 'LANE_MISMATCH')
        return record

    def scan(self):
        require(threading.get_ident() == self._owner_thread, 'COLLECTOR_THREAD_MISMATCH')
        raw = self._raw_slots()
        rows, damaged, seen_events, seen_sequences = [], [], set(), set()
        for index, data in enumerate(raw):
            if data == b'\0' * SLOT_BYTES:
                continue
            try:
                record = self._decode(data, index)
                require(record['sequence'] not in seen_sequences and
                        record['event']['event_id'] not in seen_events, 'REPLAYED_RECORD')
                seen_sequences.add(record['sequence'])
                seen_events.add(record['event']['event_id'])
                rows.append(record)
            except (EvidenceError, TypeError, KeyError, struct.error) as error:
                damaged.append({'slot': index, 'sha256': _sha(data),
                                'reason': str(error)[:128]})
        occupied = sum(data != b'\0' * SLOT_BYTES for data in raw)
        ordered, previous_time, dead, worker_binding = [], 0, False, None
        for row in sorted(rows, key=lambda x: x['sequence']):
            error = None
            if row['sequence'] > occupied:
                error = 'SEQUENCE_EXCEEDS_OCCUPIED_HISTORY'
            elif row['event']['monotonic_ns'] <= previous_time:
                error = 'NONMONOTONIC_STORED_HISTORY'
            elif dead and row['event']['kind'] == 'checkpoint':
                error = 'WORKER_RESURRECTION_REJECTED'
            elif row['event']['kind'] == 'postmortem' and worker_binding is not None and \
                    not same(row['event']['cgroup'], worker_binding):
                error = 'WORKER_CGROUP_INSTANCE_REBINDING'
            if error:
                damaged.append({'slot': row['slot'], 'sha256': _sha(raw[row['slot']]),
                                'reason': error})
                continue
            previous_time = row['event']['monotonic_ns']
            dead = dead or row['event']['kind'] == 'postmortem'
            if row['event']['kind'] == 'postmortem':
                worker_binding = row['event']['cgroup']
            ordered.append(row)
        return {'status': 'UNKNOWN' if damaged else 'INTEGRITY_VALID_DURABILITY_UNATTESTED',
                'records': ordered,
                'damaged': damaged, 'slot_sha256': [_sha(x) for x in raw],
                'FULL_LAUNCH_ENVELOPE_VERIFIED': False,
                'production_permissions_verified': False}

    def append(self, event):
        require(threading.get_ident() == self._owner_thread, 'COLLECTOR_THREAD_MISMATCH')
        require(self._append_lock.acquire(blocking=False), 'REENTRANT_OR_CONCURRENT_APPEND')
        try:
            return self._append_serialized(event)
        finally:
            self._append_lock.release()

    def _append_serialized(self, event):
        # Advisory locking serializes cooperating collectors only.
        validate_event(event)
        if event['cgroup'] is not None:
            require(event['cgroup']['boot_id'] == self.identity['collector_boot_id'],
                    'FOREIGN_BOOT_CLOCK_DOMAIN')
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            before = self.scan()
            require(not before['damaged'] or event['kind'] in ('failure', 'postmortem'),
                    'DAMAGED_STORE_ONLY_UNKNOWN_FAILURE_ALLOWED')
            require(not any(r['event']['event_id'] == event['event_id']
                            for r in before['records']), 'REPLAYED_EVENT')
            require(event['kind'] != 'checkpoint' or
                    not any(r['event']['kind'] == 'postmortem' for r in before['records']),
                    'WORKER_RESURRECTION_REJECTED')
            previous_groups = [r['event']['cgroup'] for r in before['records']
                               if r['event']['kind'] == 'postmortem']
            require(event['kind'] != 'postmortem' or not previous_groups or
                    same(event['cgroup'], previous_groups[0]),
                    'WORKER_CGROUP_INSTANCE_REBINDING')
            require(not before['records'] or event['monotonic_ns'] >
                    max(r['event']['monotonic_ns'] for r in before['records']),
                    'NONMONOTONIC_EVENT')
            raw = self._raw_slots()
            empty = [i for i in LANES[event['kind']] if raw[i] == b'\0' * SLOT_BYTES]
            require(empty, 'LANE_ENOSPC_FAILURE_RESERVE_UNTOUCHED')
            index = empty[0]
            sequence = sum(data != b'\0' * SLOT_BYTES for data in raw) + 1
            record = {'identity': self.identity, 'sequence': sequence,
                      'slot': index, 'event': event}
            payload = canonical(record)
            require(len(payload) <= SLOT_BYTES - HEADER.size - len(COMMIT), 'PAYLOAD_BOUND')
            body = HEADER.pack(MAGIC, len(payload), bytes.fromhex(_sha(payload))) + payload
            body += b'\0' * (SLOT_BYTES - len(body))
            fd = self._open_slot(index, write=True)
            try:
                require(os.pread(fd, SLOT_BYTES, 0) == b'\0' * SLOT_BYTES,
                        'OCCUPIED_SLOT_NEVER_OVERWRITTEN')
                _write_all(fd, body)
                os.fsync(fd)
                _write_all(fd, COMMIT, SLOT_BYTES - len(COMMIT))
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(self.fd)
            # Reopen rather than trusting the writer's buffer/descriptor.
            fd = self._open_slot(index)
            try:
                reread = os.pread(fd, SLOT_BYTES + 1, 0)
            finally:
                os.close(fd)
            require(self._decode(reread, index) == record, 'REOPEN_VERIFICATION')
            after = self.scan()
            require(after['damaged'] == before['damaged'] and
                    any(r == record for r in after['records']) and
                    all(after['slot_sha256'][i] == before['slot_sha256'][i]
                        for i in range(8) if i != index), 'WHOLE_STORE_REOPEN_VERIFICATION')
            return {'status': 'ACK_FILE_DIR_SYNC_REOPEN_FIXTURE_ONLY',
                    'slot': index, 'sha256': _sha(reread),
                    'platform_power_loss_verified': False,
                    'runtime_capacity_verified': False}
        finally:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
