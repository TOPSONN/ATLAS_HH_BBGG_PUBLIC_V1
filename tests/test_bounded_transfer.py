"""Offline transfer-budget checks; no ROOT parsing or network requests."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error

spec = importlib.util.spec_from_file_location('bounded', Path(__file__).resolve().parents[1] / 'scripts/fetch_phase1_sample.py')
bounded = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bounded)


class Reply(io.BytesIO):
    status = 200

    def __init__(self, data, headers):
        super().__init__(data)
        self.headers = headers


class NeverOpen:
    def open(self, *_args, **_kwargs):
        raise AssertionError('A refused transfer must not reach the network.')


class TransferSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.transfer = bounded.Transfer(self.directory)

    def tearDown(self):
        self.temp.cleanup()

    def test_budget_refuses_before_request(self):
        self.transfer.opener = NeverOpen()
        self.transfer.payload_bytes = bounded.BUDGET - 65536
        with self.assertRaises(RuntimeError):
            self.transfer.request('https://example.invalid', allowance=1)
        self.assertEqual(self.transfer.requests, [])

    def test_resume_never_resets_budget(self):
        self.transfer.payload_bytes = 123
        self.transfer.requests = [{'url': 'https://example.invalid', 'payload_bytes': 123}]
        self.transfer.save()
        resumed = bounded.Transfer(self.directory, resume=True)
        self.assertEqual(resumed.payload_bytes, 123)
        self.assertEqual(len(resumed.requests), 1)
        self.assertEqual(resumed.facts['charged_bytes'], 123 + 65536)

    def consume(self, data, headers, maximum, expected=None):
        item = {'payload_bytes': 0}
        self.transfer.requests.append(item)
        return self.transfer.consume(Reply(data, headers), item, maximum, expected=expected)

    def test_oversized_advertisement_read_zero(self):
        with self.assertRaises(RuntimeError):
            self.consume(b'12345', {'Content-Length': '5'}, 4)
        self.assertEqual(self.transfer.payload_bytes, 0)

    def test_unadvertised_oversize_stops_with_one_byte_probe(self):
        with self.assertRaises(RuntimeError):
            self.consume(b'x' * 100, {}, 4)
        self.assertEqual(self.transfer.payload_bytes, 5)

    def test_truncation_cannot_pass(self):
        with self.assertRaises(RuntimeError):
            self.consume(b'abc', {'Content-Length': '4'}, 4, expected=4)
        self.assertEqual(self.transfer.payload_bytes, 3)

    def test_compressed_encoding_refused_before_read(self):
        with self.assertRaises(RuntimeError):
            self.consume(b'abc', {'Content-Encoding': 'gzip'}, 4)
        self.assertEqual(self.transfer.payload_bytes, 0)

    def test_exact_payload_counted_and_hashed(self):
        self.assertEqual(self.consume(b'abc', {'Content-Length': '3'}, 3, expected=3), b'abc')
        self.assertEqual(self.transfer.payload_bytes, 3)
        self.assertEqual(self.transfer.requests[0]['sha256'], 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

    def test_unknown_storage_redirect_refused(self):
        class Redirect:
            def open(self, request, **_kwargs):
                raise urllib.error.HTTPError(request.full_url, 307, '', {'Location': 'http://example.invalid/data.root'}, None)
        self.transfer.opener = Redirect()
        self.transfer.facts['https_url'] = 'https://eospublic.cern.ch/eos/opendata/data.root'
        with self.assertRaises(RuntimeError):
            self.transfer.eos_request(self.transfer.facts['https_url'], {}, 4)
        self.assertEqual(len(self.transfer.requests), 1)


if __name__ == '__main__':
    unittest.main()
