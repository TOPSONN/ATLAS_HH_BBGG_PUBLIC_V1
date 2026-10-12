#!/usr/bin/env python3
"""Only the explicitly approved 302521 object; preserve all historical charges."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import re
import subprocess
import urllib.error
import urllib.parse

import fetch_phase1_sample as transport
from fetch_phase4_samples import MCTransfer, verify_local

PHASE5_LIMIT = 128 * 1024 * 1024
CUMULATIVE_LIMIT = 256 * 1024 * 1024
NAME = 'ODEO_FEB2025_v0_GamGam_mc_302521.Pythia8EvtGen_A14NNPDF23LO_2DP20_Mass_100_160.GamGam.root'
SIZE = 110755804
CHECKSUM = 'adler32:b43248ea'

WSL_HTTP_CLIENT = r'''
import json,re,sys,urllib.request,urllib.parse
try:
    spec=json.loads(sys.stdin.readline())
    parsed=urllib.parse.urlsplit(spec['url'])
    if (parsed.scheme!='http' or not re.fullmatch(r'st-[A-Za-z0-9-]+\.cern\.ch',parsed.hostname or '') or
        parsed.port!=8443 or parsed.path!=spec['expected_path'] or parsed.username is not None or
        parsed.password is not None or parsed.fragment): raise ValueError('endpoint refused')
    maximum=spec['maximum_body_bytes']
    if type(maximum) is not int or maximum<0: raise ValueError('body cap refused')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args): raise RuntimeError('redirect refused')
    opener=urllib.request.build_opener(NoRedirect())
    request=urllib.request.Request(spec['url'],headers=spec['headers'])
    with opener.open(request,timeout=30) as response:
        safe={k:v for k,v in response.headers.items() if k.lower() in spec['safe_headers']}
        sys.stdout.buffer.write((json.dumps({'status':response.status,'headers':safe})+'\n').encode())
        sys.stdout.buffer.flush()
        consumed=0
        for command in sys.stdin:
            verb,requested=command.strip().split()
            requested=int(requested)
            if verb!='READ' or not 0<requested<=65536: raise ValueError('read refused')
            if consumed+requested>maximum+1: raise ValueError('body cap exceeded')
            chunk=response.read(requested);consumed+=len(chunk)
            sys.stdout.buffer.write((str(len(chunk))+'\n').encode()+chunk)
            sys.stdout.buffer.flush()
except Exception as error:
    # Capability query and exception URL are never printed or persisted.
    sys.stderr.write(type(error).__name__);sys.exit(1)
'''


def safe_error(error):
    """Do not copy URLs, userinfo or capability-bearing exception text."""
    name=type(error).__name__
    errno=getattr(error,'errno',None)
    return name+(f' (errno {errno})' if type(errno) is int else '')


def safe_url(value):
    try:
        parsed=urllib.parse.urlsplit(value)
        if parsed.username is not None or parsed.password is not None:
            return 'UNSAFE_URL_REDACTED'
        return urllib.parse.urlunsplit(parsed._replace(query='',fragment=''))
    except Exception:
        return 'INVALID_URL_REDACTED'


def teardown_child(child):
    """Always attempt all stream closes, termination, wait and kill fallback."""
    if child is None:return
    try:
        try:running=child.poll() is None
        except Exception:running=True
        if running:
            try:child.terminate()
            except Exception:pass
        try:child.wait(timeout=5)
        except Exception:
            try:child.kill()
            except Exception:pass
            try:child.wait(timeout=5)
            except Exception:pass
    finally:
        for name in ('stdin','stdout','stderr'):
            pipe=getattr(child,name,None)
            if pipe is not None:
                try:pipe.close()
                except Exception:pass


def publish_exclusively(partial,final):
    # The files are in one directory/filesystem. Hard-link creation is atomic
    # and fails on an existing target on both Linux and Windows; no rename's
    # platform-dependent replacement semantics and no failed partial deletion.
    os.link(partial,final)
    partial.unlink()


class WSLResponse:
    def __init__(self, child,maximum_body_bytes):
        self.child = child
        self.maximum_body_bytes=maximum_body_bytes;self.consumed=0
        try:
            if type(maximum_body_bytes) is not int or maximum_body_bytes<0:raise ValueError('Invalid WSL body cap')
            line = child.stdout.readline(8193)
            if not line or len(line)>8192 or not line.endswith(b'\n'):
                raise RuntimeError('Missing or oversized WSL metadata frame')
            meta = json.loads(line)
            if type(meta['status']) is not int or not isinstance(meta['headers'],dict):raise ValueError('Invalid WSL metadata')
            self.status = meta['status']
            # Preserve HTTP's case-insensitive lookup used by inherited consume.
            from email.message import Message
            self.headers = Message()
            for key,value in meta['headers'].items():
                if key.lower() not in transport.SAFE_HEADERS or not isinstance(value,str):raise ValueError('Unsafe WSL header')
                self.headers[key] = value
        except Exception:
            teardown_child(child);raise
    def read(self, size):
        try:
            if type(size) is not int or not 0<size<=65536 or self.consumed+size>self.maximum_body_bytes+1:
                raise ValueError('Invalid or over-budget bounded WSL read')
            self.child.stdin.write(f'READ {size}\n'.encode());self.child.stdin.flush()
            line=self.child.stdout.readline(8)
            if not re.fullmatch(rb'[0-9]{1,5}\n',line):raise RuntimeError('Invalid WSL body frame')
            count=int(line)
            if not 0<=count<=size: raise ValueError('WSL returned an invalid read length')
            raw=self.child.stdout.read(count)
            if len(raw)!=count: raise RuntimeError('Incomplete WSL response frame')
            self.consumed+=count;return raw
        except Exception:
            teardown_child(self.child);raise
    def __enter__(self): return self
    def __exit__(self, *args):
        teardown_child(self.child)


class ContinuumTransfer(MCTransfer):
    def __init__(self, directory, resume=False, storage_via_wsl=False, https_storage=False):
        super().__init__(directory,resume)
        if resume:
            if (type(self.payload_bytes) is not int or self.payload_bytes<0 or not isinstance(self.requests,list) or
                any(not isinstance(item,dict) or type(item.get('payload_bytes')) is not int or item['payload_bytes']<0 for item in self.requests)):
                raise ValueError('Invalid resumed byte accounting')
            observed=sum(item['payload_bytes'] for item in self.requests)
            if observed!=self.payload_bytes or self.facts.get('charged_bytes')!=observed+len(self.requests)*65536:
                raise ValueError('Resumed receipt totals disagree with preserved requests')
        self.storage_via_wsl=storage_via_wsl
        self.https_storage=https_storage
    def save(self):
        # Dynamic dispatch also sanitizes errors logged by the unchanged Phase1
        # request implementation before they ever reach this Phase5 receipt.
        for mapping in [self.facts,*self.requests]:
            for key in ('url','location','storage_endpoint'):
                if mapping.get(key):mapping[key]=safe_url(mapping[key])
            if 'error' in mapping:
                value=mapping['error']
                if not isinstance(value,str) or not re.fullmatch(r'(HTTP [0-9]{3}|[A-Za-z_][A-Za-z0-9_]*( \(errno -?[0-9]+\))?)',value):
                    mapping['error']='EXCEPTION_DETAILS_REDACTED'
        super().save()
    def eos_request(self,url,headers,allowance):
        if not self.https_storage: return super().eos_request(url,headers,allowance)
        for _ in range(3):
            try:
                return self.request(url,headers=headers,allowance=allowance)
            except urllib.error.HTTPError as error:
                if error.code not in (301,302,307,308): raise
                location=error.headers.get('Location','')
                error.close()
                target=urllib.parse.urlsplit(location)
                if (target.scheme not in ('http','https') or
                    not re.fullmatch(r'st-[A-Za-z0-9-]+\.cern\.ch',target.hostname or '') or
                    target.port!=8443 or target.path!=urllib.parse.urlsplit(self.facts['https_url']).path or
                    target.username is not None or target.password is not None or target.fragment):
                    raise ValueError('Unrecognised EOS storage redirect')
                # Stronger transport requested on the exact scoped CERN endpoint;
                # certificate/hostname verification remain mandatory.
                url=urllib.parse.urlunsplit(target._replace(scheme='https'))
                self.facts.update(storage_transport='HTTPS',https_storage_upgrade_requested=target.scheme=='http',
                                  storage_endpoint=url.split('?')[0]);self.save()
        raise ValueError('EOS redirect limit exceeded')
    def request(self,url,method='GET',headers=None,allowance=0):
        if not self.storage_via_wsl or urllib.parse.urlsplit(url).scheme != 'http':
            try:return super().request(url,method,headers,allowance)
            except Exception as error:
                if self.requests:self.requests[-1].update(error=safe_error(error))
                self.save();raise
        if os.name != 'nt' or method != 'GET':
            raise ValueError('WSL public storage adapter requires Windows and GET')
        # eos_request already validates the CERN host, port and exact pinned path.
        parsed=urllib.parse.urlsplit(url)
        if (not re.fullmatch(r'st-[A-Za-z0-9-]+\.cern\.ch',parsed.hostname or '') or
            parsed.port!=8443 or parsed.username is not None or parsed.password is not None or parsed.fragment or
            parsed.path != urllib.parse.urlsplit(self.facts['https_url']).path):
            raise ValueError('Storage endpoint or path mismatch')
        if self.payload_bytes + (len(self.requests)+1)*65536 + allowance+1 > transport.BUDGET:
            raise ValueError('Transfer budget would be exceeded; no request sent')
        item={'url':url.split('?')[0],'method':method,'payload_bytes':0,'runtime':'Ubuntu WSL public HTTP storage; no TLS claim'}
        self.requests.append(item);self.save()
        child=None
        try:
            child=subprocess.Popen(['wsl.exe','-d','Ubuntu','--','/usr/bin/python3','-c',WSL_HTTP_CLIENT],
                                   stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            spec={'url':url,'headers':{'Accept-Encoding':'identity','Connection':'close',**(headers or {})},
                  'safe_headers':list(transport.SAFE_HEADERS),'maximum_body_bytes':allowance,'expected_path':parsed.path}
            child.stdin.write((json.dumps(spec)+'\n').encode());child.stdin.flush()
            response=WSLResponse(child,allowance)
        except Exception as error:
            teardown_child(child)
            item['error']=safe_error(error);self.save();raise
        item.update(status=response.status,headers=dict(response.headers.items()));self.save()
        return response,item


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def select(raw):
    metadata = json.loads(raw)['metadata']
    if str(metadata.get('recid')) != '93922' or metadata.get('doi') != '10.7483/OPENDATA.ATLAS.IMZO.7U52':
        raise ValueError('Official record identity changed')
    matches = [f for f in metadata['_files'] if f['key'] == NAME]
    if len(matches) != 1 or matches[0]['size'] != SIZE or matches[0]['checksum'] != CHECKSUM:
        raise ValueError('Approved filename/size/checksum changed')
    uri = urllib.parse.urlsplit(matches[0]['uri'])
    if uri.scheme != 'root' or uri.netloc != 'eospublic.cern.ch' or uri.path != '//eos/opendata/atlas/rucio/opendata/' + NAME:
        raise ValueError('Official URI differs from approved object')
    return dict(matches[0], dsid=302521, https_url='https://eospublic.cern.ch/' + uri.path.lstrip('/'))


def budget(prior, documents):
    if type(prior) is not int or type(documents) is not int or min(prior, documents) < 0:
        raise ValueError('Invalid accounting values')
    remaining = min(PHASE5_LIMIT - documents, CUMULATIVE_LIMIT - prior - documents)
    if remaining < SIZE + 12 * 65536:
        raise ValueError('Approved object and request reserves do not fit')
    return remaining


def download(output, record, phase4_ledger, phase4_docs, phase5_docs, resume=False, storage_via_wsl=False, https_storage=False):
    if not resume and (output/'access.json').exists():raise ValueError('Existing transfer ledger requires resume')
    raw_record = record.read_bytes()
    sample = select(raw_record)
    raw_previous = phase4_ledger.read_bytes()
    raw_old_docs = phase4_docs.read_bytes()
    raw_docs = phase5_docs.read_bytes()
    previous = json.loads(raw_previous)['cumulative_charged_bytes']
    if type(previous) is not int or previous<0:raise ValueError('Invalid historical ledger charge')
    old = json.loads(raw_old_docs)
    old_charge = old.get('charged_bytes')
    if old_charge is None:
        bodies=[r.get('received_body_bytes', r.get('payload_bytes', 0)) for r in old['requests']]
        if any(type(value) is not int or value<0 for value in bodies):raise ValueError('Invalid historical documentation charge')
        old_charge = sum(bodies)+len(bodies)*65536
    if type(old_charge) is not int or old_charge<0:raise ValueError('Invalid historical documentation charge')
    prior = previous + old_charge
    documents = json.loads(raw_docs)['charged_bytes']
    transport.BUDGET = budget(prior, documents)
    pins = {'record_sha256': sha(raw_record), 'phase4_ledger_sha256': sha(raw_previous),
            'phase4_documentation_sha256': sha(raw_old_docs), 'phase5_documentation_sha256': sha(raw_docs)}
    t = ContinuumTransfer(output, resume, storage_via_wsl, https_storage)
    if resume and any(t.facts.get(k) != v for k, v in pins.items()):
        raise ValueError('Pinned ledger or metadata changed; reconcile without resetting charges')
    if resume and (t.facts.get('historical_charged_bytes')!=prior or
                   t.facts.get('phase5_documentation_charged_bytes')!=documents):
        raise ValueError('Historical or documentation charges changed during resume')
    t.facts.update(**pins, record='https://opendata.cern.ch/api/records/93922',
        budget_bytes=transport.BUDGET, phase5_limit_bytes=PHASE5_LIMIT,
        cumulative_limit_bytes=CUMULATIVE_LIMIT, historical_charged_bytes=prior,
        phase5_documentation_charged_bytes=documents, selected_dsids=[302521],
        authorization='Human approved single pinned DSID 302521 file and Phase 5 128 MiB cap; no physical normalization approval',
        remote_root_operations=0, https_url=sample['https_url'], filename=NAME,
        expected_size=SIZE, expected_checksum=CHECKSUM)
    t.save()
    def save_totals():
        t.facts.update(phase5_charged_bytes=documents + t.payload_bytes + len(t.requests) * 65536,
                       cumulative_charged_bytes=prior + documents + t.payload_bytes + len(t.requests) * 65536)
        t.save()
    try:
        if (output / NAME).exists():
            raise ValueError('Existing final file will not be overwritten')
        # Only these charged, verified HTTPS CA bodies supplement process-local trust.
        t.trust_cern_ca()
        response, item = t.request(sample['https_url'], method='HEAD')
        with response:
            if response.status != 200 or response.headers.get('Content-Length') != str(SIZE):
                raise ValueError('HEAD differs from official size')
        response, probe = t.eos_request(sample['https_url'], {'Range': 'bytes=0-0'}, SIZE)
        partial = output / (NAME + f'.attempt{len(t.requests)}.partial')
        with response:
            if response.status == 206:
                if response.headers.get('Content-Range') != f'bytes 0-0/{SIZE}':
                    raise ValueError('Unexpected range response')
                t.consume(response, probe, 1, expected=1)
            elif response.status == 200:
                with partial.open('xb') as file:
                    t.consume(response, probe, SIZE, file, SIZE)
            else:
                raise ValueError('Unexpected probe status')
        final = probe
        if not partial.exists():
            response, final = t.eos_request(sample['https_url'], {}, SIZE)
            with response:
                if response.status != 200 or response.headers.get('Content-Length') != str(SIZE):
                    raise ValueError('Full response differs from approved size')
                with partial.open('xb') as file:
                    t.consume(response, final, SIZE, file, SIZE)
        if CHECKSUM != 'adler32:' + final['adler32'] or verify_local(partial, sample) != final['sha256']:
            raise ValueError('Published checksum verification failed; inspection prohibited')
        publish_exclusively(partial,output / NAME)
        t.facts.update(status='PASS', files=[{'dsid':302521, 'filename':NAME, 'size':SIZE,
            'published_checksum':CHECKSUM, 'sha256':final['sha256'], 'checksum_status':'PASS',
            'official_uri':sample['uri']}])
        t.facts.pop('error', None)
        save_totals()
    except Exception as error:
        t.facts.update(status='BLOCKED_ACCESS', error=safe_error(error))
        save_totals()
        # Redirect capability-bearing exception text must not reach CLI output.
        if isinstance(error,ValueError):raise ValueError(safe_error(error)) from None
        raise RuntimeError(safe_error(error)) from None
    return t.facts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorized-dsid', required=True, type=int, choices=[302521])
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--record', required=True, type=Path)
    parser.add_argument('--phase4-ledger', type=Path, default=Path('metadata/phase4_transfer_ledger.json'))
    parser.add_argument('--phase4-docs', type=Path, default=Path('.local/phase4_v2_weight_sources_20261012/access.json'))
    parser.add_argument('--phase5-docs', type=Path, default=Path('.local/phase5_sources_20261012/access.json'))
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--storage-via-wsl', action='store_true', help='Windows verified HTTPS metadata/CA, Ubuntu WSL public HTTP storage; capability query only through stdin')
    parser.add_argument('--https-storage', action='store_true', help='Try verified HTTPS on the exact CERN storage redirect endpoint')
    args = parser.parse_args()
    if not args.resume:
        args.output_dir.mkdir(parents=True, exist_ok=False)
    facts = download(args.output_dir, args.record, args.phase4_ledger, args.phase4_docs, args.phase5_docs, args.resume, args.storage_via_wsl, args.https_storage)
    print(json.dumps({k:facts[k] for k in ('status','files','charged_bytes','phase5_charged_bytes','cumulative_charged_bytes')}, indent=2))


if __name__ == '__main__':
    main()
