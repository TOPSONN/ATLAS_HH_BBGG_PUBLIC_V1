#!/usr/bin/env python3
"""Bounded local MC inputs; Phase 1 transport reused without remote ROOT I/O."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import zlib

import fetch_phase1_sample as transport

NEW_LIMIT = 128 * 1024 * 1024
CUMULATIVE_LIMIT = 256 * 1024 * 1024
RECORD = 'https://opendata.cern.ch/api/records/93922'
SELECTED = (343981, 346214, 423103)
PINNED = {
    343981: ('PowhegPythia8EvtGen_NNLOPS_nnlo_30_ggH125_gamgam', 32086416, 'adler32:3e3f0a3b'),
    346214: ('PowhegPy8EG_NNPDF30_AZNLOCTEQ6L1_VBFH125_gamgam', 14414350, 'adler32:52f61c51'),
    423103: ('Pythia8EvtGen_A14NNPDF23LO_gammajet_DP70_140', 10489108, 'adler32:5bf96f22'),
}


class CheckedRedirect(transport.NoRedirect):
    handler_order = 499

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.username is not None or parsed.password is not None or parsed.fragment:
            # Reject before the inherited request logger can persist userinfo.
            raise ValueError('Unsafe userinfo or fragment in redirect target')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MCTransfer(transport.Transfer):
    """Public EOS HTTP redirects are explicit, scoped and never TLS claims.

    Identity/checksum metadata and CA requests use validated HTTPS. Some EOS
    endpoints issue HTTP public-storage locations; the inherited policy checks
    CERN storage host, port and exact pinned path and strips capability queries
    from durable logs. No authentication credentials are supplied to storage.
    """
    def __init__(self, directory, resume=False):
        super().__init__(directory, resume)
        self.opener.add_handler(CheckedRedirect())

    def trust_cern_ca(self):
        super().trust_cern_ca()
        self.opener.add_handler(CheckedRedirect())


def available_budget(historical):
    if not isinstance(historical, int) or historical < 0 or historical >= CUMULATIVE_LIMIT:
        raise ValueError('Invalid historical cumulative charge')
    return min(NEW_LIMIT, CUMULATIVE_LIMIT - historical)


def select(metadata):
    if str(metadata.get('recid')) != '93922' or metadata.get('doi') != '10.7483/OPENDATA.ATLAS.IMZO.7U52':
        raise ValueError('MC record identity mismatch')
    chosen = []
    for dsid in SELECTED:
        name, size, checksum = PINNED[dsid]
        key = f'ODEO_FEB2025_v0_GamGam_mc_{dsid}.{name}.GamGam.root'
        matches = [f for f in metadata['_files'] if f['key'] == key]
        if len(matches) != 1 or matches[0]['size'] != size or matches[0]['checksum'] != checksum:
            raise ValueError(f'Reviewed sample changed: {dsid}')
        uri = urllib.parse.urlsplit(matches[0]['uri'])
        if uri.scheme != 'root' or uri.netloc != 'eospublic.cern.ch' or uri.path != '//eos/opendata/atlas/rucio/opendata/' + key:
            raise ValueError('Unrecognised official file URI')
        chosen.append(dict(matches[0], dsid=dsid, https_url='https://eospublic.cern.ch/' + uri.path.lstrip('/')))
    return chosen


def verify_local(path, sample):
    raw = path.read_bytes()
    if len(raw) != sample['size'] or 'adler32:' + f'{zlib.adler32(raw) & 0xffffffff:08x}' != sample['checksum']:
        raise ValueError('Local input differs from official size/checksum')
    return hashlib.sha256(raw).hexdigest()


def download(directory, historical_ledger, resume=False):
    historical_raw = historical_ledger.read_bytes()
    historical = json.loads(historical_raw)['total_charged_bytes_including_diagnostics']
    # Scoped to this script process; the historical Phase 1 script is unchanged.
    transport.BUDGET = available_budget(historical)
    t = MCTransfer(directory, resume)
    if resume:
        if t.facts.get('historical_ledger_sha256') != hashlib.sha256(historical_raw).hexdigest():
            raise ValueError('Historical ledger changed; stop for reconciliation')
    t.facts.update(record=RECORD, budget_bytes=transport.BUDGET, new_limit_bytes=NEW_LIMIT,
                   cumulative_limit_bytes=CUMULATIVE_LIMIT, historical_charged_bytes=historical,
                   historical_ledger_sha256=hashlib.sha256(historical_raw).hexdigest(),
                   selected_dsids=list(SELECTED), remote_root_operations=0)
    t.facts.setdefault('files', [])
    t.save()
    try:
        record_path = directory / 'record93922.json'
        if record_path.exists():
            raw = record_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != t.facts['record_sha256']:
                raise ValueError('Saved record changed')
        else:
            response, item = t.request(RECORD, allowance=1024 * 1024)
            with response:
                raw = t.consume(response, item, 1024 * 1024)
            record_path.write_bytes(raw)
            t.facts['record_sha256'] = hashlib.sha256(raw).hexdigest()
            t.save()
        samples = select(json.loads(raw)['metadata'])
        # Verify all requested payloads fit before any ROOT-file access.
        remaining = sum(f['size'] for f in samples if not (directory / f['key']).exists())
        if t.payload_bytes + (len(t.requests) + 18) * 65536 + remaining > transport.BUDGET:
            raise ValueError('Pinned batch exceeds remaining transfer budget')
        t.trust_cern_ca()  # Checked certificates, only this process; charged requests.
        for sample in samples:
            path = directory / sample['key']
            if path.exists():
                digest = verify_local(path, sample)
                if not any(f['dsid'] == sample['dsid'] and f['sha256'] == digest for f in t.facts['files']):
                    raise ValueError('Existing file has no matching completed transfer evidence')
                continue
            url = sample['https_url']
            t.facts.update(https_url=url, filename=sample['key'], expected_size=sample['size'], expected_checksum=sample['checksum'])
            t.save()
            response, item = t.request(url, method='HEAD')
            with response:
                if response.status != 200 or response.headers.get('Content-Length') != str(sample['size']):
                    raise ValueError('HEAD differs from official object size')
            response, probe = t.eos_request(url, {'Range': 'bytes=0-0'}, sample['size'])
            partial = directory / (sample['key'] + f'.attempt{len(t.requests)}.partial')
            with response:
                if response.status == 206:
                    if response.headers.get('Content-Range') != f"bytes 0-0/{sample['size']}":
                        raise ValueError('Unexpected Content-Range')
                    t.consume(response, probe, 1, expected=1)
                elif response.status == 200:
                    with partial.open('xb') as output:
                        t.consume(response, probe, sample['size'], output, sample['size'])
                else:
                    raise ValueError('Unexpected range-probe response')
            final = probe
            if not partial.exists():
                response, final = t.eos_request(url, {}, sample['size'])
                with response:
                    if response.status != 200 or response.headers.get('Content-Length') != str(sample['size']):
                        raise ValueError('Full response differs from pinned size')
                    with partial.open('xb') as output:
                        t.consume(response, final, sample['size'], output, sample['size'])
            if sample['checksum'] != 'adler32:' + final['adler32']:
                raise ValueError('Published Adler-32 mismatch; inspection prohibited')
            partial.rename(path)
            t.facts['files'].append({'dsid': sample['dsid'], 'filename': sample['key'], 'size': sample['size'],
                                     'published_checksum': sample['checksum'], 'sha256': final['sha256'],
                                     'checksum_status': 'PASS', 'official_uri': sample['uri']})
            t.save()
        t.facts.update(status='PASS', cumulative_charged_bytes=historical + t.payload_bytes + len(t.requests) * 65536)
        t.facts.pop('error', None)
        t.save()
        return t.facts
    except Exception as error:
        t.facts.update(status='BLOCKED_ACCESS', error=str(error))
        t.save()
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', required=True, type=Path)
    p.add_argument('--historical-ledger', type=Path, default=Path('metadata/root_access_ledger.json'))
    p.add_argument('--resume', action='store_true', help='Continue the same ledger; never reset failed-transfer charges')
    a = p.parse_args()
    if not a.resume:
        a.output_dir.mkdir(parents=True, exist_ok=False)
    facts = download(a.output_dir, a.historical_ledger, a.resume)
    print(json.dumps({k: facts[k] for k in ('status', 'files', 'charged_bytes', 'cumulative_charged_bytes')}, indent=2))


if __name__ == '__main__':
    main()
