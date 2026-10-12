#!/usr/bin/env python3
"""Mock-only Phase5B metadata diagnostics; no DNS, HTTP or ROOT access.

The original receipt fixture is locally SHA-pinned so the suite is portable.
Its fields mirror the historical receipt; the real receipt is never changed.
"""
import copy
import io
import json
from pathlib import Path
import socket
import ssl
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import diagnose_phase5b_storage as subject


class Response:
    def __init__(self, body=b'', headers=None, status=200, fail_after=None):
        self.status = status
        self.headers = {} if headers is None else headers
        self.stream = io.BytesIO(body)
        self.read_sizes = []
        self.closed = False
        self.fail_after = fail_after

    def read(self, size):
        self.read_sizes.append(size)
        if self.fail_after is not None and len(self.read_sizes) > self.fail_after:
            raise OSError('https://user:secret@host/?capability=PRIVATE_QUERY')
        return self.stream.read(size)

    def __enter__(self):
        return self

    def close(self):
        self.closed = True

    def __exit__(self, *args):
        self.close()


class Contract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.baseline = {'phase5_charged_bytes': 1811050,
                         'cumulative_charged_bytes': 79945072}
        self.original = self.directory / 'original.json'
        self.write_original(self.baseline)
        self.addCleanup(patch.stopall)
        patch.object(subject, 'ORIGINAL', self.original).start()
        patch.object(subject, 'ORIGINAL_SHA', subject.digest(self.original.read_bytes())).start()
        # Unexpected networking is a test failure; each allowed case replaces
        # these mocks with an explicit response or socket fixture.
        self.opener = Mock()
        self.opener.open.side_effect = AssertionError('Unexpected mock HTTP request')
        self.build_opener = patch.object(subject.urllib.request, 'build_opener',
                                         return_value=self.opener).start()
        self.getaddrinfo = patch.object(subject.socket, 'getaddrinfo',
                                       side_effect=AssertionError('Unexpected DNS')).start()
        self.socket = patch.object(subject.socket, 'socket',
                                  side_effect=AssertionError('Unexpected TCP')).start()

    def write_original(self, payload):
        self.original.write_text(json.dumps(payload), encoding='utf-8')

    def original_update(self, payload):
        self.write_original(payload)
        subject.ORIGINAL_SHA = subject.digest(self.original.read_bytes())

    def audit(self, name='run', prior=()):
        return subject.Audit(self.directory / name, prior)

    def prior(self, name='prior.json', operations=None, **updates):
        if operations is None:
            operations = [{'kind': 'HTTP_GET', 'target': subject.RECORD,
                           'reserve_bytes': subject.RESERVE, 'body_cap_bytes': 1048576,
                           'received_body_bytes': 13, 'status': 'PASS_HTTP_METADATA'}]
        charge = sum(op['reserve_bytes'] + op['received_body_bytes'] for op in operations)
        item = {'task': 'PHASE5B_METADATA_DIAGNOSTICS',
                'original_receipt_sha256': subject.ORIGINAL_SHA,
                'original_phase5_charged_bytes': self.baseline['phase5_charged_bytes'],
                'original_cumulative_charged_bytes': self.baseline['cumulative_charged_bytes'],
                'prior_receipts': [], 'operations': operations,
                'incremental_charged_bytes': charge,
                'phase5_charged_bytes': self.baseline['phase5_charged_bytes'] + charge,
                'cumulative_charged_bytes': self.baseline['cumulative_charged_bytes'] + charge,
                'ROOT_payload_bytes': 0, 'remote_ROOT_operations': 0,
                'status': 'COMPLETED_METADATA_DIAGNOSTICS'}
        item.update(updates)
        path = self.directory / name
        path.write_text(json.dumps(item), encoding='utf-8')
        return path

    def response(self, response):
        self.opener.open.side_effect = None
        self.opener.open.return_value = response

    def saved(self, audit):
        return json.loads((audit.directory / 'audit.json').read_text(encoding='utf-8'))

    def assert_rejected_before_request(self, audit, **kwargs):
        self.build_opener.reset_mock()
        self.opener.open.reset_mock()
        before = copy.deepcopy(audit.facts)
        with self.assertRaises((ValueError, RuntimeError, TypeError)):
            audit.http(kwargs.pop('url', subject.RECORD), 'unused.json', **kwargs)
        self.build_opener.assert_not_called()
        self.opener.open.assert_not_called()
        self.assertEqual(audit.facts, before)

    def test_original_receipt_mutation_rejected_before_output(self):
        self.original.write_bytes(self.original.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            self.audit()
        self.assertFalse((self.directory / 'run').exists())

    def test_baseline_charges_are_nonnegative_strict_integers(self):
        for field in self.baseline:
            for value in (-1, True, 1.25, '1811050'):
                with self.subTest(field=field, value=value):
                    payload = copy.deepcopy(self.baseline)
                    payload[field] = value
                    self.original_update(payload)
                    with self.assertRaises((ValueError, TypeError)):
                        self.audit(name=field + '_' + str(value))

    def test_baseline_cap_and_cumulative_order_rejected(self):
        for payload in ({'phase5_charged_bytes': subject.PHASE5_LIMIT + 1,
                         'cumulative_charged_bytes': subject.CUMULATIVE_LIMIT + 1},
                        {'phase5_charged_bytes': 100, 'cumulative_charged_bytes': 99}):
            with self.subTest(payload=payload):
                self.original_update(payload)
                with self.assertRaises(ValueError):
                    self.audit(name='invalid_' + str(payload['phase5_charged_bytes']))

    def test_prior_hash_charge_and_original_receipt_preserved(self):
        raw = self.original.read_bytes()
        prior = self.prior()
        prior_raw = prior.read_bytes()
        audit = self.audit(prior=[prior])
        charge = subject.RESERVE + 13
        self.assertEqual(audit.totals(), (0, 1811050 + charge, 79945072 + charge))
        self.assertEqual(audit.facts['prior_receipts'][0]['sha256'], subject.digest(prior_raw))
        self.assertEqual(audit.facts['prior_receipts'][0]['charged_bytes'], charge)
        audit.begin('DNS', 'opendata.cern.ch')
        self.assertEqual(audit.totals(), (subject.RESERVE, 1811050 + charge + subject.RESERVE,
                                         79945072 + charge + subject.RESERVE))
        self.assertEqual(self.original.read_bytes(), raw)
        self.assertEqual(prior.read_bytes(), prior_raw)

    def test_multiple_distinct_prior_receipts_all_charged(self):
        first = self.prior(name='one.json')
        second = self.prior(name='two.json', operations=[
            {'kind': 'DNS', 'target': 'eospublic.cern.ch', 'reserve_bytes': subject.RESERVE,
             'body_cap_bytes': 0, 'received_body_bytes': 0, 'status': 'BLOCKED'}])
        audit = self.audit(prior=[first, second])
        self.assertEqual(audit.totals()[1], 1811050 + 2 * subject.RESERVE + 13)
        self.assertEqual(len(audit.facts['prior_receipts']), 2)

    def test_duplicate_prior_same_path_or_bytes_rejected(self):
        first = self.prior()
        second = self.directory / 'same_content.json'
        second.write_bytes(first.read_bytes())
        for prior in ([first, first], [first, second]):
            with self.subTest(prior=prior):
                with self.assertRaises(ValueError):
                    self.audit(prior=prior)
                self.assertFalse((self.directory / 'run').exists())

    def test_prior_wrong_identity_or_charge_rejected(self):
        for updates in ({'original_receipt_sha256': '0' * 64},
                        {'incremental_charged_bytes': 0}):
            with self.subTest(updates=updates):
                path = self.prior(**updates)
                with self.assertRaises(ValueError):
                    self.audit(prior=[path])
                self.assertFalse((self.directory / 'run').exists())

    def test_prior_components_nonnegative_strict_integers(self):
        for field in ('reserve_bytes', 'received_body_bytes'):
            for value in (-1, True, 0.25):
                with self.subTest(field=field, value=value):
                    op = {'kind': 'HTTP_GET', 'target': subject.RECORD,
                          'reserve_bytes': subject.RESERVE, 'body_cap_bytes': 1048576,
                          'received_body_bytes': 13, 'status': 'PASS_HTTP_METADATA'}
                    op[field] = value
                    path = self.prior(operations=[op])
                    with self.assertRaises((ValueError, TypeError)):
                        self.audit(name=field + '_' + str(value), prior=[path])

    def test_prior_original_baseline_cannot_be_changed(self):
        for field in ('original_phase5_charged_bytes', 'original_cumulative_charged_bytes'):
            with self.subTest(field=field):
                path = self.prior(**{field: 0})
                with self.assertRaises(ValueError):
                    self.audit(name=field, prior=[path])

    def chain(self, prior_refs=None, **updates):
        first = self.prior(name='chain_first.json')
        first_charge = subject.RESERVE + 13
        reference = {'path': first.as_posix(), 'sha256': subject.digest(first.read_bytes()),
                     'charged_bytes': first_charge}
        second_charge = subject.RESERVE
        second = self.prior(name='chain_second.json', operations=[
            {'kind': 'DNS', 'target': 'eospublic.cern.ch', 'reserve_bytes': subject.RESERVE,
             'body_cap_bytes': 0, 'received_body_bytes': 0, 'status': 'BLOCKED'}],
            prior_receipts=[reference] if prior_refs is None else prior_refs,
            phase5_charged_bytes=1811050 + first_charge + second_charge,
            cumulative_charged_bytes=79945072 + first_charge + second_charge)
        if updates:
            item = json.loads(second.read_text())
            item.update(updates)
            second.write_text(json.dumps(item), encoding='utf-8')
        return first, second, reference

    def test_inherited_chain_charges_each_receipt_once(self):
        first, second, _ = self.chain()
        first_raw, second_raw = first.read_bytes(), second.read_bytes()
        audit = self.audit(prior=[first, second])
        charge = 2 * subject.RESERVE + 13
        self.assertEqual(audit.totals(), (0, 1811050 + charge, 79945072 + charge))
        audit.begin('DNS', 'opendata.cern.ch')
        self.assertEqual(audit.totals()[0], subject.RESERVE)
        self.assertEqual(first.read_bytes(), first_raw)
        self.assertEqual(second.read_bytes(), second_raw)

    def test_inherited_chain_missing_receipt_rejected(self):
        _, second, _ = self.chain()
        with self.assertRaises(ValueError):
            self.audit(prior=[second])
        self.assertFalse((self.directory / 'run').exists())

    def test_inherited_chain_duplicate_or_changed_hash_charge_rejected(self):
        for index, mutation in enumerate(('duplicate', 'hash', 'charge')):
            with self.subTest(mutation=mutation):
                first, second, reference = self.chain()
                item = json.loads(second.read_text())
                if mutation == 'duplicate':
                    item['prior_receipts'] = [reference, reference]
                elif mutation == 'hash':
                    item['prior_receipts'][0]['sha256'] = '0' * 64
                else:
                    item['prior_receipts'][0]['charged_bytes'] += 1
                second.write_text(json.dumps(item), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.audit(name='chain_bad_' + str(index), prior=[first, second])

    def test_prior_bool_incremental_and_aggregate_totals_rejected(self):
        for field in ('incremental_charged_bytes', 'phase5_charged_bytes',
                      'cumulative_charged_bytes'):
            for value in (True, -1, 0.25):
                with self.subTest(field=field, value=value):
                    first, second, _ = self.chain(**{field: value})
                    with self.assertRaises(ValueError):
                        self.audit(name='chain_' + field + '_' + str(value), prior=[first, second])

    def test_prior_aggregate_must_include_inherited_charges(self):
        first, second, _ = self.chain(phase5_charged_bytes=1811050 + subject.RESERVE,
                                      cumulative_charged_bytes=79945072 + subject.RESERVE)
        with self.assertRaises(ValueError):
            self.audit(prior=[first, second])

    def test_prior_operation_cap_reserve_and_body_consistency(self):
        changes = [('reserve_bytes', subject.RESERVE - 1), ('body_cap_bytes', True),
                   ('body_cap_bytes', -1), ('body_cap_bytes', 0.25),
                   ('body_cap_bytes', 1048577), ('received_body_bytes', 1048578)]
        for index, (field, value) in enumerate(changes):
            with self.subTest(field=field, value=value):
                op = {'kind': 'HTTP_GET', 'target': subject.RECORD,
                      'reserve_bytes': subject.RESERVE, 'body_cap_bytes': 1048576,
                      'received_body_bytes': 13, 'status': 'PASS_HTTP_METADATA'}
                op[field] = value
                prior = self.prior(operations=[op])
                with self.assertRaises(ValueError):
                    self.audit(name='op_' + str(index), prior=[prior])

    def test_prior_scope_refuses_root_payload_or_other_task(self):
        for index, updates in enumerate(({'ROOT_payload_bytes': 1},
                                         {'remote_ROOT_operations': 1},
                                         {'ROOT_payload_bytes': False},
                                         {'task': 'UNRELATED'})):
            with self.subTest(updates=updates):
                prior = self.prior(**updates)
                with self.assertRaises(ValueError):
                    self.audit(name='scope_' + str(index), prior=[prior])

    def test_existing_output_directory_preserved(self):
        output = self.directory / 'run'
        output.mkdir()
        sentinel = output / 'user-owned.txt'
        sentinel.write_bytes(b'do not replace')
        with self.assertRaises(FileExistsError):
            self.audit()
        self.assertEqual(sentinel.read_bytes(), b'do not replace')
        self.assertFalse((output / 'audit.json').exists())

    def test_phase5_budget_prevents_open_before_request(self):
        self.original_update({'phase5_charged_bytes': subject.PHASE5_LIMIT - subject.RESERVE,
                              'cumulative_charged_bytes': subject.CUMULATIVE_LIMIT - 1000000})
        audit = self.audit()
        self.assert_rejected_before_request(audit, maximum=1)
        self.assertEqual(self.saved(audit)['incremental_charged_bytes'], 0)

    def test_cumulative_budget_prevents_open_before_request(self):
        self.original_update({'phase5_charged_bytes': 1811050,
                              'cumulative_charged_bytes': subject.CUMULATIVE_LIMIT - subject.RESERVE})
        audit = self.audit()
        self.assert_rejected_before_request(audit, maximum=1)

    def test_caps_are_strict_nonnegative_integers(self):
        for cap in (-1, True, False, 0.25, '3'):
            with self.subTest(cap=cap):
                audit = self.audit(name='cap_' + str(cap))
                self.assert_rejected_before_request(audit, maximum=cap)

    def test_endpoint_specific_cap_enforced(self):
        for url, cap in ((subject.RECORD, 1048577), (subject.JOB, 65537),
                         (subject.CA_URLS[0], 8193)):
            with self.subTest(url=url):
                audit = self.audit(name='over_' + str(cap))
                self.assert_rejected_before_request(audit, url=url, maximum=cap)

    def test_disallowed_methods_and_head_body_refused(self):
        for method, cap in (('POST', 0), ('HEAD', 1), ('get', 1)):
            with self.subTest(method=method):
                audit = self.audit(name='method_' + method)
                self.assert_rejected_before_request(audit, method=method, maximum=cap)

    def test_no_root_payload_get_or_unapproved_endpoint(self):
        urls = [subject.EOS,
                subject.RECORD.replace('https:', 'http:'),
                'https://evil.invalid/api/records/93922',
                subject.RECORD + '?capability=PRIVATE_QUERY',
                subject.RECORD + '#PRIVATE_FRAGMENT',
                'https://user:secret@opendata.cern.ch/api/records/93922',
                'https://opendata.cern.ch/api/records/93915']
        for index, url in enumerate(urls):
            with self.subTest(url=url):
                audit = self.audit(name='endpoint_' + str(index))
                self.assert_rejected_before_request(audit, url=url, maximum=3)

    def test_unverified_tls_context_refused_before_request(self):
        audit = self.audit()
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.assert_rejected_before_request(audit, maximum=3, context=context)

    def test_output_path_must_be_basename_before_request(self):
        for index, name in enumerate(('../outside.json', '/tmp/outside.json', '', '.', '..', 'sub/file.json')):
            with self.subTest(name=name):
                audit = self.audit(name='name_' + str(index))
                with self.assertRaises(ValueError):
                    audit.http(subject.RECORD, name, 3)
                self.build_opener.assert_not_called()
                self.assertEqual(audit.facts['operations'], [])

    def test_get_exact_cap_accounted_and_saved_exclusively(self):
        audit = self.audit()
        response = Response(b'abc', {'Content-Length': '3', 'Content-Type': 'application/json',
                                      'Set-Cookie': 'secret-cookie'})
        self.response(response)
        raw, op = audit.http(subject.RECORD, 'record.json', 3)
        self.assertEqual(raw, b'abc')
        self.assertEqual(op['status'], 'PASS_HTTP_METADATA')
        self.assertEqual(op['received_body_bytes'], 3)
        self.assertEqual(op['sha256'], subject.digest(b'abc'))
        self.assertEqual(audit.totals()[0], subject.RESERVE + 3)
        self.assertEqual((audit.directory / 'record.json').read_bytes(), b'abc')
        self.assertNotIn('Set-Cookie', op['headers'])
        self.assertTrue(response.closed)
        self.assertTrue(all(0 < n <= 4 for n in response.read_sizes))
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(request.get_header('Accept-encoding'), 'identity')

    def test_head_root_object_never_reads_body(self):
        audit = self.audit()
        response = Response(b'must-not-read', {'Content-Length': str(subject.SIZE)})
        self.response(response)
        raw, op = audit.http(subject.EOS, 'root_head', method='HEAD')
        self.assertEqual(raw, b'')
        self.assertEqual(op['status'], 'PASS_HTTP_METADATA')
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(audit.totals()[0], subject.RESERVE)
        self.assertFalse((audit.directory / 'root_head').exists())
        self.assertEqual(audit.facts['ROOT_payload_bytes'], 0)

    def test_advertised_body_overrun_no_read_charge_retained(self):
        audit = self.audit()
        response = Response(b'abcdef', {'Content-Length': '6'})
        self.response(response)
        raw, op = audit.http(subject.RECORD, 'record.json', 3)
        self.assertIsNone(raw)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(audit.totals()[0], subject.RESERVE)
        self.assertTrue(response.closed)

    def test_unknown_length_body_cap_sentinel_counted(self):
        audit = self.audit()
        response = Response(b'abcdef')
        self.response(response)
        raw, op = audit.http(subject.RECORD, 'record.json', 3)
        self.assertIsNone(raw)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(response.read_sizes, [4])
        self.assertEqual(op['received_body_bytes'], 4)
        self.assertEqual(audit.totals()[0], subject.RESERVE + 4)
        self.assertFalse((audit.directory / 'record.json').exists())

    def test_encoded_metadata_refused_without_body_read(self):
        audit = self.audit()
        response = Response(b'compressed', {'Content-Encoding': 'gzip'})
        self.response(response)
        raw, op = audit.http(subject.RECORD, 'record.json', 20)
        self.assertIsNone(raw)
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual(audit.totals()[0], subject.RESERVE)

    def test_failure_after_consumed_body_retains_charge_and_redacts(self):
        audit = self.audit()
        response = Response(b'abc', fail_after=1)
        self.response(response)
        raw, op = audit.http(subject.RECORD, 'record.json', 9)
        self.assertIsNone(raw)
        self.assertEqual(op['received_body_bytes'], 3)
        self.assertEqual(audit.totals()[0], subject.RESERVE + 3)
        saved = (audit.directory / 'audit.json').read_text()
        for secret in ('PRIVATE_QUERY', 'capability=', 'user:secret', 'secret@'):
            self.assertNotIn(secret, saved)
        self.assertEqual(op['error'], 'OSError')
        self.assertTrue(response.closed)

    def test_output_name_collision_preserves_original_and_charge(self):
        audit = self.audit()
        (audit.directory / 'record.json').write_bytes(b'user-owned')
        self.response(Response(b'abc', {'Content-Length': '3'}))
        raw, op = audit.http(subject.RECORD, 'record.json', 3)
        self.assertIsNone(raw)
        self.assertEqual(op['status'], 'BLOCKED')
        self.assertEqual((audit.directory / 'record.json').read_bytes(), b'user-owned')
        self.assertEqual(audit.totals()[0], subject.RESERVE + 3)

    def test_http_redirect_not_followed_or_secret_persisted(self):
        audit = self.audit()
        response = Response(b'error body must not be read')
        error = urllib.error.HTTPError(subject.RECORD, 307, 'private detail',
                                       {'Location': 'http://st-1.cern.ch:8443/path?capability=PRIVATE_QUERY'},
                                       response)
        self.opener.open.side_effect = error
        raw, op = audit.http(subject.RECORD, 'record.json', 100)
        self.assertIsNone(raw)
        self.assertEqual(op['status'], 'HTTP_STATUS')
        self.assertEqual(op['location'], 'http://st-1.cern.ch:8443/path')
        self.assertEqual(op['error'], 'HTTP_307')
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(self.opener.open.call_count, 1)
        self.assertEqual(audit.totals()[0], subject.RESERVE)
        self.assertNotIn('PRIVATE_QUERY', (audit.directory / 'audit.json').read_text())

    def test_no_redirect_handler_raises_instead_of_new_request(self):
        request = urllib.request.Request(subject.RECORD)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            subject.NoRedirect().redirect_request(request, io.BytesIO(), 307, '',
                                                 {'Location': subject.EOS}, subject.EOS)
        self.assertEqual(caught.exception.code, 307)
        self.opener.open.assert_not_called()

    def test_http_error_body_not_consumed_and_reserve_not_reset(self):
        audit = self.audit()
        response = Response(b'server error SECRET')
        self.opener.open.side_effect = urllib.error.HTTPError(subject.RECORD, 503, 'secret', {}, response)
        _, op = audit.http(subject.RECORD, 'record.json', 20)
        self.assertEqual(op['received_body_bytes'], 0)
        self.assertEqual(response.read_sizes, [])
        self.assertEqual(audit.totals()[0], subject.RESERVE)
        self.assertEqual(op['error'], 'HTTP_503')
        audit.begin('DNS', 'opendata.cern.ch')
        self.assertEqual(audit.totals()[0], 2 * subject.RESERVE)

    def test_http_exception_sanitized_without_capability_or_proxy(self):
        audit = self.audit()
        self.opener.open.side_effect = OSError(111, 'https://proxy-user:PRIVATE@proxy/?capability=TOKEN')
        _, op = audit.http(subject.JOB, 'job.json', 10)
        self.assertEqual(op['error'], 'ConnectionRefusedError (errno 111)')
        serialized = json.dumps(self.saved(audit))
        for secret in ('PRIVATE', 'TOKEN', 'proxy-user', 'capability=', '?ref=master'):
            self.assertNotIn(secret, serialized)
        self.assertEqual(op['target'], subject.JOB.split('?')[0])

    def test_proxy_summary_credentials_and_endpoint_redacted(self):
        with patch.object(subject.urllib.request, 'getproxies', return_value={
                'https': 'http://name:PRIVATE@proxy.example:8080/?capability=TOKEN',
                'http': 'http://proxy.example:80', 'no': 'internal-private-host'}):
            summary = subject.proxy_summary()
        self.assertEqual(summary['https']['endpoint'], 'REDACTED')
        self.assertTrue(summary['https']['credential_present'])
        self.assertEqual(summary['https']['port'], 8080)
        self.assertNotIn('no', summary)
        for secret in ('PRIVATE', 'TOKEN', 'proxy.example', 'internal-private-host', 'name:'):
            self.assertNotIn(secret, json.dumps(summary))

    def test_dns_failure_is_charged_and_stops_tcp(self):
        audit = self.audit()
        self.getaddrinfo.side_effect = socket.gaierror(-2, 'private-proxy?capability=TOKEN')
        with patch.object(subject, 'ENDPOINTS', {'eospublic.cern.ch': (443, 1094)}), \
                patch.object(subject.urllib.request, 'getproxies', return_value={}):
            subject.network(audit)
        self.assertEqual(len(audit.facts['operations']), 1)
        self.assertEqual(audit.facts['operations'][0]['status'], 'BLOCKED')
        self.assertEqual(audit.totals()[0], subject.RESERVE)
        self.socket.assert_not_called()
        self.assertNotIn('TOKEN', json.dumps(self.saved(audit)))

    def test_ipv4_ipv6_tcp_failures_all_charged_and_no_tls(self):
        audit = self.audit()
        self.getaddrinfo.side_effect = None
        self.getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.1', 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 0, 0, 0))]
        connection = Mock()
        connection.__enter__ = Mock(return_value=connection)
        connection.__exit__ = Mock(return_value=False)
        connection.connect.side_effect = ConnectionRefusedError(111, 'PRIVATE')
        self.socket.side_effect = None
        self.socket.return_value = connection
        with patch.object(subject, 'ENDPOINTS', {'eospublic.cern.ch': (443,)}), \
                patch.object(subject.urllib.request, 'getproxies', return_value={}):
            subject.network(audit)
        ops = audit.facts['operations']
        self.assertEqual([op['kind'] for op in ops], ['DNS', 'DIRECT_TCP', 'DIRECT_TCP'])
        self.assertEqual([op['family'] for op in ops[1:]], ['IPv4', 'IPv6'])
        self.assertEqual(audit.totals()[0], 3 * subject.RESERVE)
        self.assertNotIn('PRIVATE', json.dumps(self.saved(audit)))

    def test_tls_failure_keeps_dns_tcp_tls_charges(self):
        audit = self.audit()
        self.getaddrinfo.side_effect = None
        self.getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.1', 0))]
        connection = Mock()
        connection.__enter__ = Mock(return_value=connection)
        connection.__exit__ = Mock(return_value=False)
        self.socket.side_effect = None
        self.socket.return_value = connection
        context = Mock()
        context.wrap_socket.side_effect = ssl.SSLCertVerificationError('secret certificate capability=TOKEN')
        with patch.object(subject, 'ENDPOINTS', {'eospublic.cern.ch': (443,)}), \
                patch.object(subject.urllib.request, 'getproxies', return_value={}), \
                patch.object(subject.ssl, 'create_default_context', return_value=context):
            subject.network(audit)
        self.assertEqual([op['kind'] for op in audit.facts['operations']],
                         ['DNS', 'DIRECT_TCP', 'DIRECT_TLS_DEFAULT_TRUST'])
        self.assertEqual(audit.facts['operations'][-1]['status'], 'BLOCKED')
        self.assertEqual(audit.totals()[0], 3 * subject.RESERVE)
        context.wrap_socket.assert_called_once_with(connection, server_hostname='eospublic.cern.ch')
        self.assertNotIn('TOKEN', json.dumps(self.saved(audit)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
