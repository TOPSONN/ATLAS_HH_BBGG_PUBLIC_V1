#!/usr/bin/env python3
"""Bounded metadata diagnostics; never opens or reads a remote ROOT object."""
import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import platform
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

from fetch_phase5_continuum import NAME, SIZE, CHECKSUM, safe_error, safe_url
from fetch_phase1_sample import CA_URLS, SAFE_HEADERS, NoRedirect

ORIGINAL = Path('.local/phase5_access_20261012/access.json')
ORIGINAL_SHA = 'be764a03f335e9cf238b9e8f1f67a8fd82bfa07aeb2ae145f490e8d6547ab134'
RESERVE = 65536
PHASE5_LIMIT = 134217728
CUMULATIVE_LIMIT = 268435456
RECORD = 'https://opendata.cern.ch/api/records/93922'
EOS = 'https://eospublic.cern.ch/eos/opendata/atlas/rucio/opendata/' + NAME
JOB = ('https://gitlab.cern.ch/api/v4/projects/atlas-physics%2Fpmg%2Finfrastructure%2Fmc15joboptions/'
       'repository/files/share%2FDSID302xxx%2FMC15.302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.py?ref=master')
CA_SHA = ('187f4f7b1315ebd2b72547c1accf2ec4077d51c14a0ce574904a9fdaea8a320c',
          '7b28ce158439ad742b4be0d7dbf05cbdf715038f5e41ea1424caad3bb4e69d8a')
ENDPOINTS = {
    'opendata.cern.ch': (443,), 'ca.cern.ch': (443,),
    'eospublic.cern.ch': (443, 1094), 'gitlab.cern.ch': (443,),
    'st-096-dd904134.cern.ch': (8443,), 'st-120-100gb-bknoxg.cern.ch': (8443,)}

GET_CAPS = {RECORD: 1048576, JOB: 65536, **{url: 8192 for url in CA_URLS}}
HEAD_URLS = {EOS, 'https://opendata.cern.ch/api/files/95bcca35-f11d-474a-b954-230ea0dbcaca/' + NAME}


def unsigned(value):
    if type(value) is not int or value < 0:
        raise ValueError('Nonnegative integer accounting required')
    return value


def digest(raw): return hashlib.sha256(raw).hexdigest()


class Audit:
    def __init__(self, directory, prior_paths=()):
        raw = ORIGINAL.read_bytes()
        if digest(raw) != ORIGINAL_SHA: raise ValueError('Original access receipt changed')
        baseline = json.loads(raw)
        phase5 = unsigned(baseline['phase5_charged_bytes'])
        cumulative = unsigned(baseline['cumulative_charged_bytes'])
        if phase5 > PHASE5_LIMIT or cumulative > CUMULATIVE_LIMIT or cumulative < phase5:
            raise ValueError('Original accounting outside ceilings')
        self.prior = []
        items = []
        for path in prior_paths:
            prior_raw = path.read_bytes(); item = json.loads(prior_raw)
            if item['original_receipt_sha256'] != ORIGINAL_SHA: raise ValueError('Prior identity differs')
            if (item.get('task') != 'PHASE5B_METADATA_DIAGNOSTICS' or
                unsigned(item['original_phase5_charged_bytes']) != phase5 or
                unsigned(item['original_cumulative_charged_bytes']) != cumulative or
                unsigned(item['ROOT_payload_bytes']) != 0 or
                unsigned(item['remote_ROOT_operations']) != 0):
                raise ValueError('Prior baseline or scope differs')
            charge = 0
            for op in item['operations']:
                reserve = unsigned(op['reserve_bytes'])
                body = unsigned(op['received_body_bytes'])
                cap = unsigned(op['body_cap_bytes'])
                if reserve != RESERVE or cap > 1048576 or body > cap + 1:
                    raise ValueError('Prior operation accounting differs')
                charge += reserve + body
            if charge != unsigned(item['incremental_charged_bytes']): raise ValueError('Prior accounting differs')
            self.prior.append({'path': path.as_posix(), 'sha256': digest(prior_raw), 'charged_bytes': charge})
            items.append(item)
        if len({p['sha256'] for p in self.prior}) != len(self.prior): raise ValueError('Duplicate prior receipt')
        charges = {p['sha256']: p['charged_bytes'] for p in self.prior}
        for item in items:
            inherited = 0; seen = set()
            for previous in item['prior_receipts']:
                key = previous['sha256']
                if key in seen or key not in charges or unsigned(previous['charged_bytes']) != charges[key]:
                    raise ValueError('Prior chain incomplete or duplicated')
                seen.add(key); inherited += charges[key]
            expected = unsigned(item['incremental_charged_bytes']) + inherited
            if (unsigned(item['phase5_charged_bytes']) != phase5 + expected or
                unsigned(item['cumulative_charged_bytes']) != cumulative + expected):
                raise ValueError('Prior aggregate accounting differs')
        if phase5 + sum(charges.values()) > PHASE5_LIMIT or cumulative + sum(charges.values()) > CUMULATIVE_LIMIT:
            raise ValueError('Prior accounting exceeds ceilings')
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=False)
        self.facts = {'task': 'PHASE5B_METADATA_DIAGNOSTICS', 'runtime': platform.system(),
            'python': platform.python_version(), 'checked_utc': datetime.now(timezone.utc).isoformat(),
            'original_receipt_sha256': ORIGINAL_SHA, 'original_phase5_charged_bytes': baseline['phase5_charged_bytes'],
            'original_cumulative_charged_bytes': baseline['cumulative_charged_bytes'], 'prior_receipts': self.prior,
            'operations': [], 'status': 'RUNNING', 'ROOT_payload_bytes': 0, 'remote_ROOT_operations': 0,
            'accounting': 'Consumed HTTP response bodies plus 64KiB per DNS/TCP/TLS/HTTP operation; control and wire traffic not measured; no bulk transfer'}
        self.save()

    def totals(self):
        own = sum(op['reserve_bytes'] + op['received_body_bytes'] for op in self.facts['operations'])
        delta = own + sum(p['charged_bytes'] for p in self.prior)
        return own, self.facts['original_phase5_charged_bytes'] + delta, self.facts['original_cumulative_charged_bytes'] + delta

    def save(self):
        own, phase5, cumulative = self.totals()
        self.facts.update(incremental_charged_bytes=own, phase5_charged_bytes=phase5,
                          cumulative_charged_bytes=cumulative)
        (self.directory / 'audit.json').write_text(json.dumps(self.facts, indent=2) + '\n', encoding='utf-8', newline='\n')

    def begin(self, kind, target, allowance=0):
        unsigned(allowance)
        if allowance > 1048576: raise ValueError('Metadata cap exceeds one MiB')
        _, phase5, cumulative = self.totals()
        if allowance < 0 or phase5 + RESERVE + allowance + 1 > PHASE5_LIMIT or cumulative + RESERVE + allowance + 1 > CUMULATIVE_LIMIT:
            raise RuntimeError('Budget would be exceeded before request')
        op = {'kind': kind, 'target': safe_url(target) if '://' in target else target,
              'reserve_bytes': RESERVE, 'body_cap_bytes': allowance, 'received_body_bytes': 0, 'status': 'STARTED'}
        self.facts['operations'].append(op); self.save(); return op

    def http(self, url, name, maximum=0, method='GET', context=None):
        unsigned(maximum)
        if method == 'GET':
            if url not in GET_CAPS or not 0 < maximum <= GET_CAPS[url]: raise ValueError('GET endpoint/cap refused')
        elif method == 'HEAD':
            if maximum != 0 or url not in HEAD_URLS: raise ValueError('HEAD endpoint/cap refused')
        else: raise ValueError('Method refused')
        if Path(name).name != name or name in ('', '.', '..'): raise ValueError('Output name refused')
        context = context or ssl.create_default_context()
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise ValueError('Certificate and hostname verification required')
        op = self.begin('HTTP_' + method, url, maximum)
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
        request = urllib.request.Request(url, method=method, headers={'Accept-Encoding': 'identity', 'User-Agent': 'ATLAS-bounded-Phase5B/1', 'Connection': 'close'})
        raw = bytearray()
        try:
            with opener.open(request, timeout=8) as response:
                op.update(http_status=response.status, headers={k:v for k,v in response.headers.items() if k.lower() in SAFE_HEADERS}, tls_verification=True)
                if response.headers.get('Content-Encoding', 'identity') not in ('identity', ''): raise ValueError('Encoded body refused')
                length = response.headers.get('Content-Length')
                if method != 'HEAD' and length is not None and int(length) > maximum: raise ValueError('Body cap advertised overrun')
                if method != 'HEAD':
                    while True:
                        _, phase5, cumulative = self.totals()
                        allowance = min(maximum - len(raw) + 1, PHASE5_LIMIT-phase5, CUMULATIVE_LIMIT-cumulative, 65536)
                        if allowance <= 0: raise RuntimeError('Body budget exhausted')
                        chunk = response.read(allowance)
                        if not chunk: break
                        raw.extend(chunk); op['received_body_bytes'] += len(chunk); self.save()
                        if len(raw) > maximum: raise RuntimeError('Body cap exceeded')
                op['status'] = 'PASS_HTTP_METADATA'
                if raw:
                    path = self.directory / name
                    with path.open('xb') as handle: handle.write(raw)
                    op.update(saved_name=name, sha256=digest(raw))
                return bytes(raw), op
        except urllib.error.HTTPError as error:
            op.update(status='HTTP_STATUS', http_status=error.code, error='HTTP_' + str(error.code),
                      location=safe_url(error.headers.get('Location', '')))
            error.close(); return None, op
        except Exception as error:
            op.update(status='BLOCKED', error=safe_error(error)); return None, op
        finally:
            self.save()


def proxy_summary():
    summary = {}
    for key, value in urllib.request.getproxies().items():
        if key.lower() not in ('http','https','all'): continue
        parsed = urllib.parse.urlsplit(value)
        summary[key] = {'configured': bool(value), 'scheme': parsed.scheme,
                        'credential_present': parsed.username is not None or parsed.password is not None,
                        'endpoint': 'REDACTED', 'port': parsed.port}
    return summary


def network(audit):
    audit.facts['proxy'] = proxy_summary(); audit.save()
    for host, ports in ENDPOINTS.items():
        op = audit.begin('DNS', host)
        try:
            addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            chosen = {}
            for family, _, _, _, address in addresses:
                if family in (socket.AF_INET, socket.AF_INET6) and family not in chosen:
                    ipaddress.ip_address(address[0]); chosen[family] = address[0]
            op.update(status='PASS_DNS', addresses={str(family):ip for family,ip in chosen.items()})
        except Exception as error:
            op.update(status='BLOCKED', error=safe_error(error)); chosen = {}
        audit.save()
        for family, ip in chosen.items():
            for port in ports:
                item = audit.begin('DIRECT_TCP', host + ':' + str(port))
                item.update(family='IPv4' if family==socket.AF_INET else 'IPv6', address=ip)
                start = time.monotonic()
                try:
                    with socket.socket(family, socket.SOCK_STREAM) as connection:
                        connection.settimeout(2); connection.connect((ip,port))
                    item['status'] = 'PASS_TCP'
                except Exception as error: item.update(status='BLOCKED', error=safe_error(error))
                item['seconds'] = round(time.monotonic()-start,3); audit.save()
                if port == 443 and item['status'] == 'PASS_TCP':
                    tls = audit.begin('DIRECT_TLS_DEFAULT_TRUST', host + ':443')
                    tls['family'] = item['family']
                    try:
                        with socket.socket(family, socket.SOCK_STREAM) as connection:
                            connection.settimeout(3); connection.connect((ip,port))
                            with ssl.create_default_context().wrap_socket(connection, server_hostname=host) as secure:
                                tls.update(status='PASS_TLS', version=secure.version(), certificate_validation=True, hostname_validation=True)
                    except Exception as error: tls.update(status='BLOCKED', error=safe_error(error))
                    audit.save()


def sources(audit):
    raw, op = audit.http(RECORD, 'record93922.json', 1048576)
    if raw is None: return
    record = json.loads(raw)
    rows = [row for row in record['metadata']['_files'] if row['key'] == NAME]
    if len(rows)!=1 or rows[0]['size']!=SIZE or rows[0]['checksum']!=CHECKSUM: raise ValueError('Current pinned identity differs')
    expected = 'root://eospublic.cern.ch//eos/opendata/atlas/rucio/opendata/' + NAME
    if rows[0]['uri'] != expected: raise ValueError('Official URI differs')
    audit.facts['official_file'] = rows[0]; audit.facts['record_sha256'] = digest(raw); audit.save()
    bucket = record['links']['bucket']
    if bucket != 'https://opendata.cern.ch/api/files/' + rows[0]['bucket']: raise ValueError('Bucket identity differs')
    audit.http(bucket+'/'+urllib.parse.quote(NAME,safe=''), 'api_file_head', method='HEAD')
    context = ssl.create_default_context()
    all_ca = True
    for index, (url, expected_sha) in enumerate(zip(CA_URLS, CA_SHA)):
        ca, _ = audit.http(url, 'cern_ca_' + str(index) + '.crt', 8192)
        if ca is None or digest(ca)!=expected_sha:
            all_ca = False; continue
        pem = ca.decode('ascii') if ca.startswith(b'-----BEGIN') else ssl.DER_cert_to_PEM_cert(ca)
        context.load_verify_locations(cadata=pem)
    if all_ca: audit.http(EOS, 'eos_head', method='HEAD', context=context)
    audit.http(JOB, 'job302521_master.json', 65536)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action',choices=('network','sources'),required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--prior-audit',type=Path,action='append',default=[])
    args=parser.parse_args()
    audit=Audit(args.output_dir,args.prior_audit)
    try:
        (network if args.action=='network' else sources)(audit)
        audit.facts['status']='COMPLETED_METADATA_DIAGNOSTICS'
    except Exception as error:
        audit.facts.update(status='BLOCKED_DIAGNOSTICS', error=safe_error(error))
    finally: audit.save()
    print(json.dumps({'status':audit.facts['status'],'operations':len(audit.facts['operations']),
        'incremental_charged_bytes':audit.facts['incremental_charged_bytes'],'ROOT_payload_bytes':0}))


if __name__=='__main__': main()
