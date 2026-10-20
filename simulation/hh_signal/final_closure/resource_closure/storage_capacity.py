"""Pure receipt consistency review, never a quota or volume executor.

No OS/kernel API is imported or called. Exact caller-provided blob/source/device
bindings prevent accidental substitution; they cannot authenticate a claim.
Actual allocated capacity, control-plane and FULL acceptance stay false.
"""
from __future__ import annotations
import errno
import hashlib
import json
import re

MAX_RECEIPT_BYTES = 32768
QTYPE = ('USRQUOTA', 'GRPQUOTA', 'PRJQUOTA')
OPS = {'Q_GETFMT': 0x800004, 'Q_GETINFO': 0x800005, 'Q_GETQUOTA': 0x800007}
HEADERS = ('local_syscall_header_sha256', 'local_quota_header_sha256')
PROFILES = {
    'S4': {'device_bytes': 4194304, 'block_bytes': 1024, 'inodes': 128,
           'work_bytes': 8388608, 'tmp_bytes': 1048576, 'aggregate_bytes': 16777216},
    'FUTURE_BUILD_PROPOSAL_ONLY': {
        'device_bytes': 2147483648, 'block_bytes': 4096, 'inodes': 32768,
        'work_bytes': 2147483648, 'tmp_bytes': 268435456, 'aggregate_bytes': 5368709120}}

def require(value, reason):
    if not value:
        raise ValueError(reason)

def uint(value, reason, maximum=(1 << 64)-1):
    require(type(value) is int and 0 <= value <= maximum, reason)
    return value

def digest(value):
    require(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
            'SHA256_REQUIRED')
    return value

def decode(raw, expected_sha256):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_RECEIPT_BYTES, 'BOUNDED_RECEIPT_BYTES')
    require(hashlib.sha256(raw).hexdigest() == digest(expected_sha256), 'EXACT_RECEIPT_SHA256')
    def pairs(items):
        result = {}
        for key,value in items:
            require(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('NONFINITE_JSON')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('BOUNDED_UTF8_JSON') from error
    def walk(item, depth=0):
        require(depth <= 24, 'RECEIPT_DEPTH')
        if type(item) is dict:
            for child in item.values():
                walk(child, depth+1)
        elif type(item) is list:
            for child in item:
                walk(child, depth+1)
        elif type(item) is float:
            raise ValueError('FLOAT_NOT_IN_READBACK_SCHEMA')
    walk(value)
    require(type(value) is dict, 'RECEIPT_OBJECT')
    return value

def quota_projection(raw, *, expected_sha256, expected_device, expected_kernel,
                     expected_headers, expected_ids):
    doc = decode(raw, expected_sha256)
    fields = {'schema','timestamp_UTC','kernel_release','architecture','syscall_number',
              *HEADERS,'O_PATH_filesystem_major_minor','opened_path','project_id_source',
              'rows','GET_calls','SET_ON_OFF_SYNC_calls','actual_service_mount_or_resource_tests',
              'retained_physical_events'}
    require(set(doc) == fields and doc['schema'] == 'READ_ONLY_QUOTACTL_FD_GET_V1',
            'EXACT_GET_RECEIPT_SCHEMA')
    require(type(expected_device) is str and
            re.fullmatch(r'[0-9]+:[0-9]+', expected_device) is not None, 'EXPECTED_DEVICE')
    require(type(expected_kernel) is str and 0 < len(expected_kernel) <= 128, 'EXPECTED_KERNEL')
    require(type(expected_headers) is dict and set(expected_headers) == set(HEADERS),
            'EXPECTED_HEADER_BINDING')
    require(type(expected_ids) is dict and set(expected_ids) == set(QTYPE), 'EXPECTED_ID_BINDING')
    for value in expected_ids.values():
        uint(value, 'EXPECTED_ID', (1 << 31)-1)
    require(doc['O_PATH_filesystem_major_minor'] == expected_device and
            doc['kernel_release'] == expected_kernel and doc['architecture'] == 'x86_64' and
            type(doc['syscall_number']) is int and doc['syscall_number'] == 443,
            'GET_DEVICE_KERNEL_ARCH_BINDING')
    for name in HEADERS:
        require(doc[name] == digest(expected_headers[name]), 'GET_HEADER_BINDING')
    require(type(doc['timestamp_UTC']) is str and
            re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z',
                         doc['timestamp_UTC']) is not None, 'UTC_CAPTURE_TIME')
    for name in ('opened_path','project_id_source'):
        require(type(doc[name]) is str and 0 < len(doc[name]) <= 256, 'LOCAL_SOURCE_LABEL')
    for name, expected in [('GET_calls',9),('SET_ON_OFF_SYNC_calls',0),
                          ('actual_service_mount_or_resource_tests',0),('retained_physical_events',0)]:
        require(type(doc[name]) is int and doc[name] == expected, 'GET_ONLY_EXACT_COUNTS')
    require(type(doc['rows']) is list and len(doc['rows']) == 9, 'EXACT_NINE_GET_ROWS')
    rows = {}
    base = {'API','operation','qtype','id','QCMD_hex','return','errno','errno_name'}
    info_fields = {'dqi_bgrace','dqi_igrace','dqi_flags','dqi_valid'}
    quota_fields = {'dqb_bhardlimit','dqb_bsoftlimit','dqb_curspace','dqb_ihardlimit',
                    'dqb_isoftlimit','dqb_curinodes','dqb_btime','dqb_itime','dqb_valid'}
    for row in doc['rows']:
        require(type(row) is dict and base <= set(row), 'GET_ROW_SCHEMA')
        kind,op = row['qtype'],row['operation']
        require(type(kind) is str and type(op) is str and kind in QTYPE and op in OPS and
                row['API'] == 'quotactl_fd', 'GET_ONLY_API')
        key = (kind,op)
        require(key not in rows, 'DUPLICATE_GET_ROW')
        require(type(row['id']) is int and row['id'] == expected_ids[kind], 'GET_ID_BINDING')
        require(row['QCMD_hex'] == hex((OPS[op] << 8) | QTYPE.index(kind)), 'GET_COMMAND_ABI')
        require(type(row['return']) is int and row['return'] in (-1,0), 'GET_RETURN')
        error = uint(row['errno'], 'GET_ERRNO',4095)
        if row['return'] == -1:
            require(error > 0 and row['errno_name'] == errno.errorcode.get(error) and
                    row.get('result_interpretation') == 'NO_BUFFER_FIELDS_INTERPRETED_ON_FAILURE' and
                    set(row) == base | {'result_interpretation'}, 'FAILED_GET_BUFFER_UNTRUSTED')
        else:
            require(error == 0 and row['errno_name'] is None and set(row) == base | {'result'},
                    'SUCCESS_GET_SCHEMA')
            result = row['result']
            names = {'format'} if op == 'Q_GETFMT' else info_fields if op == 'Q_GETINFO' else quota_fields
            require(type(result) is dict and set(result) == names, 'GET_RESULT_FIELDS')
            for name,value in result.items():
                uint(value, 'GET_RESULT_UNSIGNED',
                     (1 << 32)-1 if name in ('format','dqi_flags','dqi_valid','dqb_valid') else (1 << 64)-1)
            if op == 'Q_GETFMT':
                require(1 <= result['format'] <= 5, 'KNOWN_QUOTA_FORMAT')
        rows[key] = row
    require(set(rows) == {(kind,op) for kind in QTYPE for op in OPS}, 'COMPLETE_GET_MATRIX')
    states = {}
    for kind in QTYPE:
        fmt,info = rows[kind,'Q_GETFMT'],rows[kind,'Q_GETINFO']
        if all(r['return'] == -1 and r['errno'] == errno.ESRCH for r in (fmt,info)):
            state = 'NO_ACTIVE_ACCOUNTING_OBSERVED'
        elif all(r['return'] == 0 for r in (fmt,info)):
            state = 'ACTIVE_ACCOUNTING_OBSERVED_LIMITS_NOT_VALIDATED'
        elif any(r['errno'] in (errno.EPERM,errno.EACCES) for r in (fmt,info)):
            state = 'UNKNOWN_PERMISSION'
        else:
            state = 'UNKNOWN_MIXED_OR_UNSUPPORTED_READBACK'
        limits = rows[kind,'Q_GETQUOTA']
        states[kind] = {'accounting':state,'individual_limits':
            'UNKNOWN_PERMISSION' if limits['errno'] in (errno.EPERM,errno.EACCES) else
            'NOT_AVAILABLE_INACTIVE' if limits['return'] == -1 and limits['errno'] == errno.ESRCH else
            'READBACK_PRESENT_NOT_ENFORCEMENT_PROOF' if limits['return'] == 0 else 'UNKNOWN'}
    return {'schema':'PHASE7I_QUOTA_PUBLIC_PROJECTION_V1','receipt_sha256':expected_sha256,
            'filesystem_major_minor':expected_device,'kernel_release':expected_kernel,'states':states,
            'GET_calls':9,'nonwrite_class_GETFMT_GETINFO_calls':6,
            'potential_write_class_GETQUOTA_calls':3,
            'GETQUOTA_all_failed':all(rows[kind,'Q_GETQUOTA']['return'] == -1 for kind in QTYPE),
            'GETQUOTA_success_count':sum(rows[kind,'Q_GETQUOTA']['return'] == 0 for kind in QTYPE),
            'quota_SET_ON_OFF_SYNC_calls':0,
            'GETQUOTA_caveat':'Generic GETQUOTA can allocate dquot storage; no future query is authorized by this parser.',
            'scope':'GET_RECEIPT_CONSISTENCY_ONLY',
            'persistent_allocated_capacity_verified':False,'superblock_quota_feature':'UNKNOWN',
            'formal_build_authorized':False,'FULL_LAUNCH_ENVELOPE_VERIFIED':False}

def geometry_prerequisites(raw, *, expected_sha256, profile, expected_device, expected_readbacks):
    """Positive geometry consistency only; never authenticates actual enforcement."""
    require(type(profile) is str and profile in PROFILES, 'KNOWN_PROFILE')
    p = PROFILES[profile]
    doc = decode(raw, expected_sha256)
    require(set(doc) == {'schema','source_kind','device','device_bytes','block_bytes',
                        'filesystem_blocks','total_inodes','inode_bytes','journal_blocks',
                        'overhead_blocks_including_journal','external_journal','thin_or_sparse',
                        'readback_sha256'} and doc['schema'] == 'PHASE7I_DEDICATED_GEOMETRY_CLAIM_V1',
            'GEOMETRY_SCHEMA')
    require(type(expected_device) is str and
            re.fullmatch(r'/dev/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', expected_device) is not None and
            not any(part in ('.','..') for part in expected_device.split('/')[1:]) and
            doc['device'] == expected_device and
            doc['source_kind'] == 'ADMIN_PROVISIONED_FIXED_BLOCK_DEVICE', 'DEDICATED_DEVICE_BINDING')
    require(doc['external_journal'] is False and doc['thin_or_sparse'] is False,
            'NO_EXTERNAL_JOURNAL_OR_THIN_BACKING')
    require(type(expected_readbacks) is dict and set(expected_readbacks) ==
            {'device_geometry','filesystem_superblock','inode_readback','writer_restrictions'},
            'EXACT_GEOMETRY_READBACKS')
    require(type(doc['readback_sha256']) is dict and
            doc['readback_sha256'] == {k:digest(v) for k,v in expected_readbacks.items()},
            'GEOMETRY_READBACK_BINDING')
    for key in ('device_bytes','block_bytes','filesystem_blocks','total_inodes','inode_bytes',
                'journal_blocks','overhead_blocks_including_journal'):
        uint(doc[key], 'GEOMETRY_UNSIGNED')
    require(doc['device_bytes'] == p['device_bytes'] and doc['block_bytes'] == p['block_bytes'] and
            doc['filesystem_blocks'] * doc['block_bytes'] == doc['device_bytes'] and
            0 < doc['total_inodes'] <= p['inodes'] and doc['inode_bytes'] == 256,
            'FIXED_GEOMETRY_PROFILE')
    inode_blocks = (doc['total_inodes'] * doc['inode_bytes'] + doc['block_bytes']-1) // doc['block_bytes']
    require(1024 <= doc['journal_blocks'] <= doc['filesystem_blocks']//2 and
            doc['journal_blocks'] + inode_blocks <= doc['overhead_blocks_including_journal'] <
            doc['filesystem_blocks'], 'JOURNAL_AND_INODE_OVERHEAD_INCLUDED')
    known = p['device_bytes'] + p['work_bytes'] + p['tmp_bytes']
    require(known <= p['aggregate_bytes'], 'AGGREGATE_DISK_ARITHMETIC')
    return {'status':'PASS_GEOMETRY_RECEIPT_CONSISTENCY_ONLY','profile':profile,
            'known_geometry_and_tmpfs_bytes':known,'aggregate_cap_bytes':p['aggregate_bytes'],
            'unproven_controlplane_outer_reserve_bytes':p['aggregate_bytes']-known,
            'actual_capacity_verified':False,'persistent_allocated_capacity_verified':False,
            'persistent_inode_capacity_verified':False,'formal_build_authorized':False,
            'FULL_LAUNCH_ENVELOPE_VERIFIED':False}
