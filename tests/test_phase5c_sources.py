#!/usr/bin/env python3
"""Offline contracts for the one-pass Phase5C documentation collector.

All HTTP/DNS/socket calls are mocked. Fixtures override the inherited
receipt globals and use temporary files; preserved historical inputs are
never changed and no research data or remote ROOT object is accessed.
"""
from email.message import Message
import io
import json
import os
from pathlib import Path
import ssl
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collect_phase5c_sources as subject
import diagnose_phase5b_storage as inherited

EXPECTED = {
    'limitations': ('https://opendata.atlas.cern/docs/data/for_research/limitations_pp', 65536),
    'format': ('https://opendata.atlas.cern/docs/documentation/data_format/physlite/', 65536),
    'coverage': ('https://opendata.atlas.cern/docs/data/for_research/pp_data', 65536),
    'overlap': ('https://opendata.atlas.cern/docs/data/for_research/evgen_collections', 65536),
    'variables': ('https://atlas-physlite-content-opendata.web.cern.ch/opendata_pp_physlite_variables.html', 262144),
    'mc_metadata': ('https://opendata.atlas.cern/docs/data/for_research/metadata', 524288),
}
HTML = b'<html><body>offline metadata fixture</body></html>'


class Response:
    def __init__(self, body=HTML, status=200, headers=None, fail_after=None):
        self.status = status
        self.headers = Message()
        if headers is None:
            headers = {'Content-Type': 'text/html; charset=utf-8',
                       'Content-Length': str(len(body))}
        for key, value in headers.items():
            self.headers[key] = value
        self.stream = io.BytesIO(body)
        self.read_sizes = []
        self.closed = False
        self.fail_after = fail_after

    def read(self, size):
        self.read_sizes.append(size)
        if self.fail_after is not None and len(self.read_sizes) > self.fail_after:
            raise OSError('https://user:SECRET@proxy/?capability=PRIVATE')
        return self.stream.read(size)

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Contract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.original = self.directory / 'original.json'
        self.baseline = {'phase5_charged_bytes': 5302259,
                         'cumulative_charged_bytes': 83436281}
        self.original.write_text(json.dumps(self.baseline), encoding='utf-8')
        self.addCleanup(patch.stopall)
        patch.object(inherited, 'ORIGINAL', self.original).start()
        patch.object(inherited, 'ORIGINAL_SHA', inherited.digest(self.original.read_bytes())).start()
        self.opener = Mock()
        self.opener.open.side_effect = AssertionError('Unexpected HTTP call')
        self.build_opener = patch.object(subject.urllib.request, 'build_opener',
                                         return_value=self.opener).start()
        patch.object(inherited.socket, 'getaddrinfo', side_effect=AssertionError('No DNS allowed')).start()
        patch.object(inherited.socket, 'socket', side_effect=AssertionError('No socket allowed')).start()
        self.context = ssl.create_default_context()

    def audit(self, name='run', priors=()):
        return subject.DocumentationAudit(self.directory / name, priors)

    def update_baseline(self, **updates):
        payload = dict(self.baseline)
        payload.update(updates)
        self.original.write_text(json.dumps(payload), encoding='utf-8')
        inherited.ORIGINAL_SHA = inherited.digest(self.original.read_bytes())

    def response(self, response):
        self.opener.open.side_effect = None
        self.opener.open.return_value = response

    def saved(self, audit):
        return json.loads((audit.directory / 'audit.json').read_text(encoding='utf-8'))

    def test_exact_six_endpoints_and_caps_no_root_get(self):
        self.assertEqual(subject.SOURCES, EXPECTED)
        audit = self.audit()
        self.opener.open.side_effect = [Response() for _ in EXPECTED]
        for key in EXPECTED:
            op = audit.get_document(key, self.context)
            self.assertEqual(op['status'], 'PASS_OFFICIAL_DOCUMENT')
        for call, (url, cap) in zip(self.opener.open.call_args_list, EXPECTED.values()):
            request = call.args[0]
            self.assertEqual(request.full_url, url)
            self.assertEqual(request.get_method(), 'GET')
            self.assertTrue(url.startswith('https://'))
            self.assertNotIn('.root', url)
            self.assertEqual(request.get_header('Accept-encoding'), 'identity')
        self.assertEqual([op['body_cap_bytes'] for op in audit.facts['operations']],
                         [cap for _, cap in EXPECTED.values()])
        self.assertEqual(audit.facts['ROOT_payload_bytes'], 0)
        self.assertEqual(audit.facts['remote_ROOT_operations'], 0)

    def test_unknown_key_raw_url_and_root_endpoint_refused(self):
        for index, key in enumerate(('unapproved', inherited.EOS, inherited.RECORD,
                                     EXPECTED['format'][0], 'root://eospublic.cern.ch/file.root', '../outside')):
            with self.subTest(key=key):
                audit = self.audit(name='key_' + str(index))
                with self.assertRaises(ValueError):
                    audit.get_document(key, self.context)
                self.assertEqual(audit.facts['operations'], [])
                self.build_opener.assert_not_called()

    def test_certificate_and_hostname_validation_both_required(self):
        for index, (mode, hostname) in enumerate(((ssl.CERT_NONE, False),
                                                (ssl.CERT_REQUIRED, False))):
            with self.subTest(mode=mode, hostname=hostname):
                audit = self.audit(name='tls_' + str(index))
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = mode
                context.check_hostname = hostname
                with self.assertRaises(ValueError):
                    audit.get_document('format', context)
                self.assertEqual(audit.facts['operations'], [])
                self.build_opener.assert_not_called()

    def test_verified_context_passed_unchanged_and_no_redirect_handler_used(self):
        audit = self.audit()
        self.response(Response())
        op = audit.get_document('format', self.context)
        handlers = self.build_opener.call_args.args
        self.assertTrue(any(isinstance(handler, subject.NoRedirect) for handler in handlers))
        https = next(handler for handler in handlers
                     if isinstance(handler, subject.urllib.request.HTTPSHandler))
        self.assertIs(https._context, self.context)
        self.assertTrue(op['tls_verification'])

    def test_phase5_pre_budget_guard_prevents_http_open(self):
        self.update_baseline(phase5_charged_bytes=subject.PHASE5_LIMIT - inherited.RESERVE - 65536,
                             cumulative_charged_bytes=subject.CUMULATIVE_LIMIT - 1000000)
        audit = self.audit()
        with self.assertRaises(RuntimeError):
            audit.get_document('format', self.context)
        self.build_opener.assert_not_called()
        self.assertEqual(self.saved(audit)['incremental_charged_bytes'], 0)

    def test_cumulative_pre_budget_guard_prevents_http_open(self):
        self.update_baseline(cumulative_charged_bytes=subject.CUMULATIVE_LIMIT - inherited.RESERVE - 65536)
        audit = self.audit()
        with self.assertRaises(RuntimeError):
            audit.get_document('format', self.context)
        self.build_opener.assert_not_called()
        self.assertEqual(audit.facts['operations'], [])

    def test_failure_reserve_charged_and_error_redacted(self):
        audit = self.audit()
        self.opener.open.side_effect = urllib.error.URLError('https://proxy-user:SECRET@proxy/?capability=PRIVATE')
        op = audit.get_document('limitations', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(op['error'], 'URLError')
        self.assertEqual(op['received_body_bytes'], 0)
        self.assertEqual(audit.totals(), (inherited.RESERVE, 5302259 + inherited.RESERVE,
                                         83436281 + inherited.RESERVE))
        for secret in ('SECRET', 'PRIVATE', 'proxy-user', 'capability='):
            self.assertNotIn(secret, json.dumps(self.saved(audit)))

    def test_six_failed_requests_all_charged_without_retry(self):
        audit = self.audit()
        original = self.original.read_bytes()
        self.opener.open.side_effect = urllib.error.URLError('offline synthetic failure')
        for key in EXPECTED:
            self.assertEqual(audit.get_document(key, self.context)['status'], 'BLOCKED')
        self.assertEqual(self.opener.open.call_count, 6)
        self.assertEqual(audit.totals()[0], 6 * inherited.RESERVE)
        self.assertEqual(sum(op['received_body_bytes'] for op in audit.facts['operations']), 0)
        self.assertEqual(self.original.read_bytes(), original)

    def test_exact_body_cap_saved_and_charged(self):
        audit = self.audit()
        cap = EXPECTED['format'][1]
        body = b'<html>' + b' ' * (cap - 13) + b'</html>'
        self.assertEqual(len(body), cap)
        response = Response(body)
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'PASS_OFFICIAL_DOCUMENT')
        self.assertEqual(op['received_body_bytes'], cap)
        self.assertEqual(audit.totals()[0], inherited.RESERVE + cap)
        self.assertEqual((audit.directory / 'format.html').read_bytes(), body)
        self.assertEqual(op['sha256'], subject.digest(body))
        self.assertTrue(response.closed)
        self.assertTrue(all(0 < size <= 65536 for size in response.read_sizes))

    def test_body_cap_plus_one_counted_and_not_saved(self):
        audit = self.audit()
        cap = EXPECTED['format'][1]
        response = Response(b'x' * (cap + 7), headers={'Content-Type': 'text/html'})
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(op['received_body_bytes'], cap + 1)
        self.assertEqual(response.read_sizes, [65536, 1])
        self.assertEqual(audit.totals()[0], inherited.RESERVE + cap + 1)
        self.assertFalse((audit.directory / 'format.html').exists())

    def test_advertised_length_invalid_or_over_cap_rejected_before_read(self):
        for index, length in enumerate(('-1', '65537', 'not-a-number')):
            with self.subTest(length=length):
                audit = self.audit(name='length_' + str(index))
                response = Response(headers={'Content-Type': 'text/html', 'Content-Length': length})
                self.response(response)
                op = audit.get_document('format', self.context)
                self.assertEqual(op['status'], 'BLOCKED')
                self.assertEqual(response.read_sizes, [])
                self.assertEqual(audit.totals()[0], inherited.RESERVE)

    def test_declared_length_truncation_not_document_pass(self):
        audit = self.audit()
        response = Response(headers={'Content-Type': 'text/html', 'Content-Length': str(len(HTML) + 5)})
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(op['received_body_bytes'], len(HTML))
        self.assertEqual(audit.totals()[0], inherited.RESERVE + len(HTML))
        self.assertFalse((audit.directory / 'format.html').exists())

    def test_empty_http200_is_not_document_pass(self):
        audit = self.audit()
        self.response(Response(body=b''))
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(op['received_body_bytes'], 0)
        self.assertFalse((audit.directory / 'format.html').exists())

    def test_unexpected_document_content_type_refused(self):
        for index, value in enumerate(('application/octet-stream', 'application/json', 'application/x-root', '')):
            with self.subTest(content_type=value):
                audit = self.audit(name='type_' + str(index))
                self.response(Response(headers={'Content-Type': value}))
                op = audit.get_document('format', self.context)
                self.assertEqual(op['status'], 'BLOCKED')
                self.assertFalse((audit.directory / 'format.html').exists())

    def test_gzip_encoded_body_refused_before_read(self):
        audit = self.audit()
        response = Response(headers={'Content-Type': 'text/html', 'Content-Encoding': 'gzip'})
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(audit.totals()[0], inherited.RESERVE)

    def test_header_lookup_case_insensitive_and_only_safe_headers_saved(self):
        audit = self.audit()
        response = Response(headers={'content-type': 'text/html', 'content-length': str(len(HTML)),
                                     'content-encoding': 'identity', 'Set-Cookie': 'PRIVATE',
                                     'Authorization': 'SECRET', 'Location': 'https://host/?capability=TOKEN'})
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'PASS_OFFICIAL_DOCUMENT')
        self.assertEqual(op['headers']['content-type'], 'text/html')
        for secret in ('PRIVATE', 'SECRET', 'TOKEN', 'capability='):
            self.assertNotIn(secret, json.dumps(self.saved(audit)))

    def test_non200_response_not_read_or_document_pass(self):
        audit = self.audit()
        response = Response(status=206)
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(audit.totals()[0], inherited.RESERVE)

    def test_http_redirect_never_followed_and_query_redacted(self):
        audit = self.audit()
        response = Response(body=b'error-body-not-consumed')
        self.opener.open.side_effect = urllib.error.HTTPError(EXPECTED['format'][0], 307, 'SECRET',
            {'Location': 'http://st-1.cern.ch:8443/path?capability=PRIVATE#TOKEN'}, response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'HTTP_STATUS')
        self.assertEqual(op['location'], 'http://st-1.cern.ch:8443/path')
        self.assertEqual(op['error'], 'HTTP_307')
        self.assertEqual(self.opener.open.call_count, 1)
        self.assertEqual(response.read_sizes, [])
        self.assertTrue(response.closed)
        self.assertEqual(audit.totals()[0], inherited.RESERVE)
        for secret in ('SECRET', 'PRIVATE', 'TOKEN', 'capability='):
            self.assertNotIn(secret, json.dumps(self.saved(audit)))

    def test_http_error_userinfo_location_redacted(self):
        audit = self.audit()
        self.opener.open.side_effect = urllib.error.HTTPError(EXPECTED['format'][0], 302, '',
            {'Location': 'https://user:SECRET@host/?capability=PRIVATE'}, io.BytesIO())
        op = audit.get_document('format', self.context)
        self.assertEqual(op['location'], 'UNSAFE_URL_REDACTED')
        self.assertNotIn('SECRET', json.dumps(self.saved(audit)))

    def test_reader_failure_retains_consumed_body_and_reserve(self):
        audit = self.audit()
        response = Response(fail_after=1)
        self.response(response)
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(op['received_body_bytes'], len(HTML))
        self.assertEqual(audit.totals()[0], inherited.RESERVE + len(HTML))
        self.assertFalse((audit.directory / 'format.html').exists())
        for secret in ('SECRET', 'PRIVATE', 'capability='):
            self.assertNotIn(secret, json.dumps(self.saved(audit)))

    def test_existing_directory_and_document_preserved(self):
        audit = self.audit()
        original_ledger = (audit.directory / 'audit.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.audit()
        self.assertEqual((audit.directory / 'audit.json').read_bytes(), original_ledger)
        document = audit.directory / 'format.html'
        document.write_bytes(b'user-owned')
        self.response(Response())
        op = audit.get_document('format', self.context)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(document.read_bytes(), b'user-owned')
        self.assertEqual(audit.totals()[0], inherited.RESERVE + len(HTML))

    def test_changed_original_receipt_rejected_before_output(self):
        self.original.write_bytes(self.original.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            self.audit()
        self.assertFalse((self.directory / 'run').exists())

    def test_cli_refuses_second_pass_before_audit_or_network(self):
        original_cwd = Path.cwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(self.directory)
        receipt = Path('.local/phase5c_sources_20261012/audit.json')
        receipt.parent.mkdir(parents=True)
        receipt.write_bytes(b'preserved-executed-receipt')
        with patch.object(sys, 'argv', ['collector', '--output-dir', 'unused', '--prior-audit', 'prior']), \
                patch.object(subject, 'DocumentationAudit', side_effect=AssertionError('Audit must not be constructed')):
            with self.assertRaises((ValueError, RuntimeError)):
                subject.main()
        self.assertEqual(receipt.read_bytes(), b'preserved-executed-receipt')
        self.assertFalse(Path('unused').exists())
        self.build_opener.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
