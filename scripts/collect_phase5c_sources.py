#!/usr/bin/env python3
"""Single-pass, capped official documentation GETs; no ROOT payload transport."""
import argparse
from pathlib import Path
import ssl
import urllib.error
import urllib.request
from diagnose_phase5b_storage import Audit, CA_SHA, digest, unsigned, PHASE5_LIMIT, CUMULATIVE_LIMIT
from fetch_phase1_sample import NoRedirect, SAFE_HEADERS
from fetch_phase5_continuum import safe_error, safe_url

SOURCES = {
 'limitations': ('https://opendata.atlas.cern/docs/data/for_research/limitations_pp', 65536),
 'format': ('https://opendata.atlas.cern/docs/documentation/data_format/physlite/', 65536),
 'coverage': ('https://opendata.atlas.cern/docs/data/for_research/pp_data', 65536),
 'overlap': ('https://opendata.atlas.cern/docs/data/for_research/evgen_collections', 65536),
 'variables': ('https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html', 262144),
 'mc_metadata': ('https://opendata.atlas.cern/docs/data/for_research/metadata', 524288),
}
COMPLETED_RECEIPT = Path('.local/phase5c_sources_20261012/audit.json')


class DocumentationAudit(Audit):
    def get_document(self, key, context):
        if key not in SOURCES: raise ValueError('Unapproved document')
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise ValueError('Verified TLS required')
        url, maximum = SOURCES[key]
        unsigned(maximum)
        op = self.begin('PHASE5C_DOCUMENT_GET', url, maximum)
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
        request = urllib.request.Request(url, headers={'Accept-Encoding':'identity','Connection':'close','User-Agent':'ATLAS-bounded-Phase5C/1'})
        raw = bytearray()
        try:
            with opener.open(request, timeout=8) as response:
                op.update(http_status=response.status, tls_verification=True,
                          headers={k:v for k,v in response.headers.items() if k.lower() in SAFE_HEADERS})
                if response.status != 200: raise ValueError('Unexpected response')
                if response.headers.get('Content-Encoding','identity') not in ('identity',''): raise ValueError('Encoded body refused')
                content_type = response.headers.get('Content-Type','').split(';',1)[0].strip().lower()
                if content_type not in ('text/html','application/xhtml+xml'):
                    raise ValueError('HTML document content type required')
                length = response.headers.get('Content-Length')
                if length is not None and (int(length) < 0 or int(length) > maximum): raise ValueError('Advertised cap overrun')
                while True:
                    _, phase5, cumulative = self.totals()
                    allowance = min(maximum-len(raw)+1, PHASE5_LIMIT-phase5, CUMULATIVE_LIMIT-cumulative, 65536)
                    if allowance <= 0: raise RuntimeError('Body budget exhausted')
                    chunk = response.read(allowance)
                    if not chunk: break
                    raw.extend(chunk); op['received_body_bytes'] += len(chunk); self.save()
                    if len(raw) > maximum: raise RuntimeError('Body cap exceeded')
                if not raw: raise ValueError('Empty document refused')
                if length is not None and len(raw) != int(length): raise ValueError('Declared length mismatch')
                with (self.directory / (key+'.html')).open('xb') as handle: handle.write(raw)
                op.update(status='PASS_OFFICIAL_DOCUMENT', saved_name=key+'.html', sha256=digest(raw))
        except urllib.error.HTTPError as error:
            op.update(status='HTTP_STATUS', http_status=error.code, error='HTTP_'+str(error.code),
                      location=safe_url(error.headers.get('Location','')))
            error.close()
        except Exception as error: op.update(status='BLOCKED', error=safe_error(error))
        finally: self.save()
        return op


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--prior-audit', type=Path, action='append', required=True)
    args = parser.parse_args()
    # This collector's bookkeeping accepts Phase5B priors only. Never omit the
    # already consumed Phase5C pass or repeat its failed endpoints on a new dir.
    if COMPLETED_RECEIPT.exists():
        raise RuntimeError('Phase5C documentation pass already recorded; stop retries. New evidence and an accounting-aware replacement are required.')
    audit = DocumentationAudit(args.output_dir, args.prior_audit)
    audit.facts.update(task='PHASE5C_DOCUMENTATION_ACCESS', baseline_commit='1c7da77fe4c852c929be39b10544220033de9fec',
                       scope='Six exact official documentation endpoints once each; no ROOT GET, no transport retry or new dataset')
    context = ssl.create_default_context()
    # Reuse locally pinned public CA documents, without another request.
    for index, expected in enumerate(CA_SHA):
        raw = (Path('.local/phase5b_windows_sources_20261012') / ('cern_ca_'+str(index)+'.crt')).read_bytes()
        if digest(raw) != expected: raise ValueError('Pinned CA changed')
        context.load_verify_locations(cadata=raw.decode('ascii') if raw.startswith(b'-----BEGIN') else ssl.DER_cert_to_PEM_cert(raw))
    audit.save()
    for key in SOURCES: audit.get_document(key, context)
    audit.facts['status']='COMPLETED_DOCUMENTATION_PASS' if all(op['status']=='PASS_OFFICIAL_DOCUMENT' for op in audit.facts['operations']) else 'PARTIAL_DOCUMENTATION_ACCESS'
    audit.save()
    print({'status':audit.facts['status'],'operations':len(audit.facts['operations']),
           'new_charged_bytes':audit.facts['incremental_charged_bytes'],'ROOT_payload_bytes':0})


if __name__ == '__main__': main()
