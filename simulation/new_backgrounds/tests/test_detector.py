"""Failure-path/numerical tests; synthetic rows never claim physical PASS."""
from pathlib import Path
import math
import os
import tempfile
import unittest

from simulation.new_backgrounds import delphes_stage as detector
from simulation.new_backgrounds import analyze_results as analysis


SCRATCH = Path(__file__).resolve().parents[3] / '.local' / 'phase6g_backgrounds' / 'detector_tests'


def method_directory():
    scratch = SCRATCH.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch)


class DetectorFailureTests(unittest.TestCase):
    def test_card_identity(self):
        self.assertEqual(detector.sha_file(detector.CARD), detector.CARD_SHA)

    def test_unreviewed_process(self):
        with method_directory() as directory:
            target = Path(directory) / 'never_created'
            with self.assertRaisesRegex(RuntimeError, 'process/seed'):
                detector.execute_delphes(target, {}, {}, {}, 610501, lambda *a: self.fail('called'), 'other')
            self.assertFalse(target.exists())

    def test_unreviewed_seed(self):
        with method_directory() as directory:
            target = Path(directory) / 'never_created'
            with self.assertRaisesRegex(RuntimeError, 'process/seed'):
                detector.execute_delphes(target, {}, {}, {}, 610401, lambda *a: self.fail('called'), 'zh')
            self.assertFalse(target.exists())

    def test_invalid_count(self):
        with method_directory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'count'):
                detector.execute_delphes(Path(directory) / 'no', {}, {}, {}, 610501, lambda *a: self.fail('called'), 'zh', 10000)

    def test_existing_output_protected(self):
        with method_directory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'exists'):
                detector.execute_delphes(Path(directory), {}, {}, {}, 610501, lambda *a: self.fail('called'), 'zh')

    def test_nonphysical_receipt_rejected(self):
        with method_directory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'actual full1000'):
                detector.execute_delphes(Path(directory) / 'no', {'validated_events': 1000, 'status': 'METHOD_ONLY'},
                                         {}, {}, 610501, lambda *a: self.fail('called'), 'zh')

    def test_reused_detector_unknown_process_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'reuse process/count'):
            detector._check_reused_detector({}, {}, {}, 'unread', Path('unused'), 'tth', 10)

    def test_reused_detector_full1000_forbidden(self):
        with self.assertRaisesRegex(RuntimeError, 'reuse process/count'):
            detector._check_reused_detector({}, {}, {}, 'unread', Path('unused'), 'zh', 1000)

    def test_reused_detector_unknown_status_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'reuse status'):
            detector._check_reused_detector({'status': 'METHOD_ONLY'}, {}, {}, 'unread', Path('unused'), 'zh', 10)

    def test_reused_detector_wrong_subset_path_rejected(self):
        with method_directory() as directory:
            base = Path(directory)
            reused = {'status': 'SOURCE_BOUND_READ_ONLY_DETECTOR_REUSE', 'original_directory': str(base / 'other'),
                      'source_manifest_path': str(base / 'run_manifest.json')}
            with self.assertRaisesRegex(RuntimeError, 'outside the preserved'):
                detector._check_reused_detector(reused, {}, {}, 'unread', base / 'unused', 'zh', 10)

    def test_short_hepmc_rejected(self):
        with method_directory() as directory:
            source, target = Path(directory) / 'method_invalid.hepmc3', Path(directory) / 'no.hepmc3'
            source.write_bytes(b'HepMC::Asciiv3-START_EVENT_LISTING\nE 0 0 0\nHepMC::Asciiv3-END_EVENT_LISTING\n')
            with self.assertRaisesRegex(RuntimeError, 'complete full1000'):
                detector._hepmc_subset(source, target, 10)
            self.assertFalse(target.exists())

    def test_no_hepmc_trailer_rejected(self):
        with method_directory() as directory:
            source, target = Path(directory) / 'method_invalid.hepmc3', Path(directory) / 'no.hepmc3'
            source.write_bytes(b'HepMC::Asciiv3-START_EVENT_LISTING\nE 0 0 0\n')
            with self.assertRaisesRegex(RuntimeError, 'complete full1000'):
                detector._hepmc_subset(source, target, 10)
            self.assertFalse(target.exists())

    def test_unknown_subset_count_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'prefix10/100'):
            detector._hepmc_subset('not_read', 'not_written', 5)

    def test_wrong_index_magic_rejected(self):
        with method_directory() as directory:
            source = Path(directory) / 'invalid.dat'
            source.write_bytes(b'METHOD_ONLY\n')
            with self.assertRaisesRegex(RuntimeError, 'magic'):
                detector._dat_subset(source, Path(directory) / 'no', 10, 'ATLAS_DELPHES_INPUT_V1')

    def test_mismatched_event_hash_rejected(self):
        with method_directory() as directory:
            source = Path(directory) / 'invalid.dat'
            source.write_bytes(b'ATLAS_DELPHES_INPUT_V1\nE 1 0 different 1 wrong\n')
            with self.assertRaisesRegex(RuntimeError, 'block mismatch'):
                detector._dat_subset(source, Path(directory) / 'no', 10, 'ATLAS_DELPHES_INPUT_V1', ['expected'])

    def test_short_index_rejected(self):
        with method_directory() as directory:
            source = Path(directory) / 'invalid.dat'
            source.write_bytes(b'ATLAS_DELPHES_INPUT_V1\nE 1 0\n')
            with self.assertRaisesRegex(RuntimeError, 'full1000'):
                detector._dat_subset(source, Path(directory) / 'no', 10, 'ATLAS_DELPHES_INPUT_V1')


class NumericalMethodTests(unittest.TestCase):
    def test_zero_survivor_interval(self):
        actual = analysis.interval(0, 1000)
        self.assertGreater(actual['wilson95_high'], 0)
        self.assertAlmostEqual(actual['zero_survivor_one_sided95_upper'], 0.0029912495450953314)
        self.assertIn('NOT_PROOF', actual['zero_means'])

    def test_all_survivors_interval(self):
        actual = analysis.interval(1000, 1000)
        self.assertEqual(actual['estimate'], 1)
        self.assertLess(actual['all_survivor_one_sided95_lower'], 1)

    def test_invalid_interval_counts(self):
        for k, n in ((-1, 1000), (1001, 1000), (0, 0), (True, 1000)):
            with self.assertRaises(RuntimeError):
                analysis.interval(k, n)

    def test_weighted_sampling_formula(self):
        actual = analysis.weighted_statistics([1, 0, 1, 0])
        self.assertEqual(actual['source_weight_sum_pb'], 2)
        self.assertEqual(actual['source_weight_sum_squared_pb2'], 2)
        self.assertAlmostEqual(actual['source_sampling_variance_pb2'], 4 / 3)

    def test_signed_weights_preserved(self):
        actual = analysis.weighted_statistics([1, -1, 0])
        self.assertEqual(actual['source_weight_sum_pb'], 0)
        self.assertEqual(actual['source_weight_sum_squared_pb2'], 2)
        self.assertEqual(actual['source_sampling_variance_pb2'], 3)

    def test_constant_zero_sampling_variance(self):
        actual = analysis.weighted_statistics([0.123456789] * 1000)
        self.assertEqual(actual['source_sampling_variance_pb2'], 0)

    def test_nonfinite_sampling_values_rejected(self):
        for value in (float('nan'), float('inf')):
            with self.assertRaises(RuntimeError):
                analysis.weighted_statistics([value, 0])

    def test_nonfinite_json_rejected(self):
        for data in ('{"v":NaN}', '{"v":1e309}', '{"v":0,"v":1}'):
            with self.assertRaises(RuntimeError):
                analysis.strict_json(data)

    def test_missing_br_closure_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'closure'):
            analysis._model_br_contract({'status': 'PASS_MODEL_BR_WEIGHT_CLOSURE', 'scope': 'MODEL_BR_ONLY',
                                         'factor': 0.002, 'ledger_sha256': '0' * 64}, 'zh')

    def test_double_br_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'closure'):
            analysis._model_br_contract({'status': 'PASS_MODEL_BR_WEIGHT_CLOSURE', 'scope': 'MODEL_BR_ONLY',
                                         'factor': 0.002, 'ledger_sha256': '0' * 64,
                                         'factor_applications': 2, 'weight_closure': 'PASS'}, 'tth')

    def test_b06_higgs_br_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'B06'):
            analysis._model_br_contract({}, 'bbgj')

    def test_partial_native_report_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'full1000'):
            analysis.summarize_detector({'status': 'METHOD_ONLY'})


class ExistingInputPrefixReadback(unittest.TestCase):
    @unittest.skipUnless((Path.home() / 'simulations/pythia8_runs/bbgg_1k/shower.hepmc3').is_file(),
                         'actual retained full1000 HepMC input only available in WSL')
    def test_real_existing_source_prefix_preserves_record_bytes(self):
        source = Path.home() / 'simulations/pythia8_runs/bbgg_1k/shower.hepmc3'
        before = detector.sha_file(source)
        with method_directory() as directory:
            for events in (10, 100):
                target = Path(directory) / f'readonly_prefix_{events}.hepmc3'
                hashes = detector._hepmc_subset(source, target, events)
                self.assertEqual(len(hashes), events)
                data = target.read_bytes()
                self.assertEqual(sum(line.startswith(b'E ') for line in data.splitlines()), events)
                self.assertTrue(data.endswith(b'HepMC::Asciiv3-END_EVENT_LISTING\n'))
        self.assertEqual(detector.sha_file(source), before)


if __name__ == '__main__':
    unittest.main()
