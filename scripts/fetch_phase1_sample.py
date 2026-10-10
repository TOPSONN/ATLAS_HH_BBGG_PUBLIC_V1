#!/usr/bin/env python3
"""Bounded public metadata/file transfer only; never interprets ROOT events."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import zlib
from datetime import datetime, timezone

BUDGET = 256 * 1024 * 1024
MAX_SAMPLE = 64 * 1024 * 1024
RECORD = 'https://opendata.cern.ch/api/records/93915'
CA_URLS = [
    'https://ca.cern.ch/cafiles/certificates/CERN%20Root%20Certification%20Authority%202.crt',
    'https://ca.cern.ch/cafiles/certificates/CERN%20Grid%20Certification%20Authority%281%29.crt',
]
SAFE_HEADERS = {'content-length', 'content-range', 'content-type', 'accept-ranges', 'etag', 'last-modified', 'content-encoding'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect requires explicit inspection', headers, fp)


class Transfer:
    def __init__(self, directory, resume=False):
        self.directory = directory
        self.payload_bytes = 0
        self.requests = []
        self.facts = {'record': RECORD, 'checked_utc': datetime.now(timezone.utc).isoformat(),
                      'budget_bytes': BUDGET, 'accounting': 'HTTP response payload bytes; 64 KiB reserved per request for protocol overhead',
                      'status': 'ACCESS_UNVERIFIED', 'remote_root_operations': 0}
        self.opener = urllib.request.build_opener(NoRedirect())
        if resume:
            self.facts = json.loads((directory / 'access.json').read_text())
            self.payload_bytes = self.facts['payload_bytes']
            self.requests = self.facts['requests']
            if self.facts['status'] == 'PASS':
                raise RuntimeError('Already verified; existing sample will not be overwritten.')
            for request in self.requests:
                request['headers'] = {k: v for k, v in request.get('headers', {}).items() if k.lower() in SAFE_HEADERS}
                if request.get('location'):
                    request['location'] = request['location'].split('?')[0]

    def save(self):
        self.facts.update(payload_bytes=self.payload_bytes, requests=self.requests,
                          charged_bytes=self.payload_bytes + len(self.requests) * 65536,
                          last_updated_utc=datetime.now(timezone.utc).isoformat())
        (self.directory / 'access.json').write_text(json.dumps(self.facts, indent=2) + '\n')

    def request(self, url, method='GET', headers=None, allowance=0):
        if self.payload_bytes + (len(self.requests) + 1) * 65536 + allowance + 1 > BUDGET:
            raise RuntimeError('Transfer budget would be exceeded; no request sent.')
        item = {'url': url.split('?')[0], 'method': method, 'payload_bytes': 0}
        self.requests.append(item)
        self.save()
        request = urllib.request.Request(url, method=method, headers={
            'User-Agent': 'ATLAS-public-bounded-schema-validation/1',
            'Accept-Encoding': 'identity', 'Connection': 'close', **(headers or {})})
        try:
            response = self.opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            location = error.headers.get('Location')
            item.update(status=error.code, error=f'HTTP {error.code}', location=location.split('?')[0] if location else None)
            error.close()
            self.save()
            raise
        except Exception as error:
            item.update(error=str(error))
            self.save()
            raise
        item.update(status=response.status, headers={k: v for k, v in response.headers.items() if k.lower() in SAFE_HEADERS})
        self.save()
        return response, item

    def eos_request(self, url, headers, allowance):
        for _ in range(3):
            try:
                return self.request(url, headers=headers, allowance=allowance)
            except urllib.error.HTTPError as error:
                if error.code not in (301, 302, 307, 308):
                    raise
                target = error.headers.get('Location', '')
                parsed = urllib.parse.urlsplit(target)
                expected_path = urllib.parse.urlsplit(self.facts['https_url']).path
                if parsed.scheme not in ('http', 'https') or not re.fullmatch(r'st-[A-Za-z0-9-]+\.cern\.ch', parsed.hostname or '') or parsed.port != 8443 or parsed.path != expected_path:
                    raise RuntimeError('Unrecognised EOS storage redirect; stopped.')
                self.facts['storage_transport'] = parsed.scheme.upper()
                self.facts['storage_endpoint'] = target.split('?')[0]
                self.save()  # Redacted capability query never persisted or printed.
                url = target
        raise RuntimeError('EOS redirect limit exceeded.')

    def consume(self, response, item, maximum, output=None, expected=None):
        encoding = response.headers.get('Content-Encoding', 'identity')
        if encoding not in ('identity', ''):
            raise RuntimeError('Compressed HTTP representation refused for byte accounting.')
        length = response.headers.get('Content-Length')
        if length is not None and int(length) > maximum:
            raise RuntimeError('Advertised payload exceeds this request limit.')
        data = bytearray() if output is None else None
        size = 0
        digest = hashlib.sha256()
        checksum = 1
        while True:
            remaining = BUDGET - self.payload_bytes - len(self.requests) * 65536
            if remaining <= 0:
                raise RuntimeError('Cumulative budget exhausted; no further response read.')
            chunk = response.read(min(65536, maximum - size + 1, remaining))
            if not chunk:
                break
            size += len(chunk)
            self.payload_bytes += len(chunk)
            item['payload_bytes'] += len(chunk)
            self.save()
            if size > maximum or self.payload_bytes + len(self.requests) * 65536 > BUDGET:
                raise RuntimeError('Payload budget exceeded; transfer aborted, no ROOT inspection permitted.')
            digest.update(chunk)
            checksum = zlib.adler32(chunk, checksum)
            if output is not None:
                output.write(chunk)
            else:
                data.extend(chunk)
        if expected is not None and size != expected:
            raise RuntimeError(f'Expected {expected} bytes, received {size}.')
        item.update(sha256=digest.hexdigest(), adler32=f'{checksum & 0xffffffff:08x}')
        self.save()
        return bytes(data) if data is not None else item

    def trust_cern_ca(self):
        context = ssl.create_default_context()
        certificates = []
        for url in CA_URLS:
            response, item = self.request(url, allowance=65536)
            with response:
                raw = self.consume(response, item, 65536)
            pem = raw.decode('ascii') if raw.startswith(b'-----BEGIN') else ssl.DER_cert_to_PEM_cert(raw)
            context.load_verify_locations(cadata=pem)
            certificates.append({'url': url, 'sha256': item['sha256'], 'bytes': item['payload_bytes']})
        self.facts['tls'] = {'certificate_validation': True, 'hostname_validation': context.check_hostname,
                             'scope': 'this process only; system trust unchanged', 'additional_ca': certificates}
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
        self.save()


def download(directory, resume=False):
    transfer = Transfer(directory, resume)
    try:
        if resume:
            raw = (directory / 'record93915.json').read_bytes()
            if hashlib.sha256(raw).hexdigest() != transfer.requests[0]['sha256']:
                raise RuntimeError('Saved official record hash differs from the transfer ledger.')
        else:
            response, item = transfer.request(RECORD, allowance=1024 * 1024)
            with response:
                raw = transfer.consume(response, item, 1024 * 1024)
        (directory / 'record93915.json').write_bytes(raw)
        metadata = json.loads(raw)['metadata']
        if str(metadata['recid']) != '93915' or metadata['doi'] != '10.7483/OPENDATA.ATLAS.GYRR.GRP3':
            raise RuntimeError('Official record identity differs from the Phase 0 baseline.')
        candidates = [f for f in metadata['_files'] if f['key'].endswith('.GamGam.root')]
        if not candidates:
            raise RuntimeError('No suitable collision ROOT file listed.')
        sample = min(candidates, key=lambda f: f['size'])
        if not re.fullmatch(r'ODEO_[A-Za-z0-9_.-]+_GamGam_data\d+_period[A-Za-z0-9]+\.GamGam\.root', sample['key']):
            raise RuntimeError('Unexpected public collision filename; no access attempted.')
        if not 0 < sample['size'] <= MAX_SAMPLE:
            raise RuntimeError('Smallest suitable file exceeds the 64 MiB single-file limit.')
        uri = urllib.parse.urlsplit(sample['uri'])
        if uri.scheme != 'root' or uri.netloc != 'eospublic.cern.ch' or not uri.path.startswith('//eos/opendata/atlas/rucio/opendata/'):
            raise RuntimeError('Unrecognised official EOS URI; no access attempted.')
        url = 'https://eospublic.cern.ch/' + uri.path.lstrip('/')
        transfer.facts.update(filename=sample['key'], official_uri=sample['uri'],
                              https_url=url, https_derivation='same EOS host/path as the official root:// URI; verified by size/checksum',
                              expected_size=sample['size'], expected_checksum=sample['checksum'])
        transfer.save()  # Exact identity is durable before even HEAD/range access.
        if (directory / sample['key']).exists():
            raise RuntimeError('Existing local sample is preserved; no new file transfer attempted.')
        if resume and ('tls' in transfer.facts or 'CERTIFICATE_VERIFY_FAILED' in transfer.facts.get('error', '')):
            transfer.trust_cern_ca()
        try:
            response, head = transfer.request(url, method='HEAD')
        except urllib.error.URLError as error:
            if 'CERTIFICATE_VERIFY_FAILED' not in str(error) or 'tls' in transfer.facts:
                raise
            transfer.trust_cern_ca()
            response, head = transfer.request(url, method='HEAD')
        with response:
            if response.headers.get('Content-Length') != str(sample['size']):
                raise RuntimeError('HEAD size missing or differs from the official index; access stopped.')
        partial = directory / (sample['key'] + '.partial')
        if partial.exists():
            partial = directory / (sample['key'] + f'.attempt{len(transfer.requests)}.partial')
        response, probe = transfer.eos_request(url, headers={'Range': 'bytes=0-0'}, allowance=sample['size'])
        with response:
            if response.status == 206:
                if response.headers.get('Content-Range') != f"bytes 0-0/{sample['size']}":
                    raise RuntimeError('Unexpected ranged response; access stopped.')
                transfer.consume(response, probe, 1, expected=1)
                transfer.facts['range_support'] = 'VERIFIED: HTTP 206, exact Content-Range and one-byte payload'
            elif response.status == 200:
                transfer.facts['range_support'] = 'NOT_SUPPORTED: server ignored Range; bounded full response retained'
                with partial.open('xb') as output:
                    transfer.consume(response, probe, sample['size'], output=output, expected=sample['size'])
            else:
                raise RuntimeError('Unexpected range-probe status.')
        transfer.save()
        if not partial.exists():
            response, full = transfer.eos_request(url, headers={}, allowance=sample['size'])
            with response:
                if response.status != 200 or response.headers.get('Content-Length') != str(sample['size']):
                    raise RuntimeError('Full response status/size differs from the recorded object.')
                with partial.open('xb') as output:
                    transfer.consume(response, full, sample['size'], output=output, expected=sample['size'])
            final = full
        else:
            final = probe
        if sample['checksum'] != 'adler32:' + final['adler32']:
            raise RuntimeError('Published Adler-32 mismatch; physical inspection prohibited.')
        path = directory / sample['key']
        partial.rename(path)
        transfer.facts.update(status='PASS', checksum_status='PASS', sha256=final['sha256'], local_file=str(path.resolve()))
        transfer.facts.pop('error', None)
        transfer.save()
        return transfer.facts
    except Exception as error:
        transfer.facts.update(status='ACCESS_UNVERIFIED', error=str(error))
        transfer.save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='New, ignored directory; existing results are never overwritten.')
    parser.add_argument('--resume', action='store_true', help='Continue the same cumulative ledger after a failed access; no budget reset.')
    args = parser.parse_args()
    if not args.resume:
        args.output_dir.mkdir(parents=True, exist_ok=False)
    try:
        facts = download(args.output_dir, args.resume)
        print(json.dumps({k: facts[k] for k in ('status', 'filename', 'payload_bytes', 'charged_bytes', 'sha256')}, indent=2))
    except Exception as error:
        print('ACCESS_UNVERIFIED:', error)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
