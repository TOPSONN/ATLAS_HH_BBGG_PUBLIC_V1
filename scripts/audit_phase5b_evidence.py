#!/usr/bin/env python3
"""Offline evidence identity/accounting checks; never grants a physical PASS."""
import argparse
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition: raise ValueError(message)


def unsigned(value):
    require(type(value) is int and value >= 0, 'Nonnegative integer required')
    return value


def digest(raw): return hashlib.sha256(raw).hexdigest()


def identity(row, lf=False):
    path = Path(row['path']); raw = path.read_bytes()
    if lf:
        require(digest(raw.replace(b'\r\n', b'\n')) == row['sha256_lf'], 'Text identity differs: ' + str(path))
    else:
        require(len(raw) == row['bytes'] and digest(raw) == row['sha256'], 'Raw identity differs: ' + str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true', help='Require all hash-bound local run/input/binary artifacts too')
    args = parser.parse_args()
    quality = json.loads(Path('metadata/phase5b_quality_gates.json').read_text(encoding='utf-8'))
    transfer = json.loads(Path('metadata/phase5b_transfer_audit.json').read_text(encoding='utf-8'))
    for row in quality['reports']: identity(row, lf=True)
    for row in quality['metadata_evidence']: identity(row)
    for row in quality['regression_source_inventory_lf']: identity(row, lf=True)
    for row in quality['new_tool_sources']: identity(row)
    for row in transfer['source_evidence']: identity(row)
    identity(transfer['published_hardened_source'])
    known = {}; total = body = operation_count = 0
    for row in transfer['new_receipts']:
        receipt = row['receipt']; increment = 0
        canonical = (json.dumps(receipt, indent=2) + '\n').encode('utf-8')
        require(digest(canonical) == row['sha256'] and len(canonical) == row['bytes'], 'Embedded raw receipt differs')
        require(row['sha256'] not in known, 'Duplicate own receipt')
        require(receipt['original_receipt_sha256'] == transfer['original_receipt']['sha256'], 'Original receipt identity differs')
        for op in receipt['operations']:
            reserve = unsigned(op['reserve_bytes']); received = unsigned(op['received_body_bytes'])
            require(reserve == 65536 and received <= unsigned(op['body_cap_bytes']) + 1, 'Operation charge differs')
            increment += reserve + received; body += received; operation_count += 1
        require(increment == unsigned(row['incremental_charged_bytes']) == unsigned(receipt['incremental_charged_bytes']), 'Own increment differs')
        seen = set(); inherited = 0
        for parent in receipt['prior_receipts']:
            key = parent['sha256']
            require(key in known and key not in seen and unsigned(parent['charged_bytes']) == known[key], 'Incomplete/duplicate/changed prior chain')
            seen.add(key); inherited += known[key]
        require(unsigned(receipt['phase5_charged_bytes']) == transfer['original_phase5_charged_bytes'] + increment + inherited, 'Receipt Phase5 total differs')
        require(unsigned(receipt['cumulative_charged_bytes']) == transfer['original_cumulative_charged_bytes'] + increment + inherited, 'Receipt cumulative differs')
        require(unsigned(receipt['ROOT_payload_bytes']) == 0, 'Unexpected ROOT payload')
        known[row['sha256']] = increment; total += increment
    require(total == transfer['new_incremental_charged_bytes'] and body == transfer['new_consumed_http_metadata_bytes'] and operation_count == transfer['new_application_operations'], 'Aggregate increment differs')
    for current, baseline, limit in (('phase5_charged_bytes', 'original_phase5_charged_bytes', 'phase5_limit_bytes'), ('cumulative_charged_bytes', 'original_cumulative_charged_bytes', 'cumulative_limit_bytes')):
        require(unsigned(transfer[current]) == unsigned(transfer[baseline]) + total <= unsigned(transfer[limit]), 'Budget aggregate differs')
    require(quality['final_verdict'] == 'BLOCKED_STORAGE_ACCESS' and quality['physical_model_ready'] is False, 'Physical verdict differs')
    require(quality['DSID302521']['acquired'] is False and quality['DSID302521']['entries_processed'] == 0, 'Unwitnessed native result')
    require(transfer['file_acquisition'] == 'NOT_ACQUIRED' and transfer['local_file_sha256'] is None and transfer['actual_adler32'] is None, 'Unwitnessed acquired identity')
    expected = {'A':'PASS','B':'PASS','C':'BLOCKED','D':'BLOCKED','E':'BLOCKED','F':'UNKNOWN','G':'UNKNOWN','H':'UNKNOWN','I':'PASS','J':'PASS'}
    require({name: row['state'] for name, row in quality['gates'].items()} == expected, 'Gate disposition differs')
    local_count = 0
    if args.local:
        rows = [transfer['original_receipt'], *transfer['new_receipts'], *quality['run_evidence'], *quality['focused_evidence'], *quality['DATA_actual_outputs'], quality['DATA_cache'], quality['selection_config'], *quality['executed_binary_hashes']]
        for row in rows: identity(row); local_count += 1
    print(json.dumps({'evidence_integrity':'PASS','scope':'Offline recorded identities/accounting only; no new physics/transport execution',
                      'local_hashes_verified':local_count,'Phase5_charged_bytes':transfer['phase5_charged_bytes'],'cumulative_charged_bytes':transfer['cumulative_charged_bytes'],
                      'continuum_access':'BLOCKED_NETWORK','physical_model_ready':False}))


if __name__ == '__main__': main()
