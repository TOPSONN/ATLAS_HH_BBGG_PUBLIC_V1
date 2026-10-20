"""Independent arithmetic and adversarial fixtures, with no runtime provenance."""
from __future__ import annotations
import copy
from fractions import Fraction
from decimal import Decimal
import unittest
from unittest.mock import patch

from simulation.hh_signal.final_closure.resource_closure import workflow_evidence as w


def sample():
    unit = 'atlas-hh-phase7i-evidence-fixture.service'
    group = '/user.slice/user-1000.slice/user@1000.service/app.slice/' + unit
    expected = {'schema': 'PHASE7I_WORKFLOW_EXPECTED_V1', 'source_revision': 'a' * 40,
                'run_id': 'b' * 32, 'unit': unit, 'aggregate_cgroup': group,
                'controller_pid': 100, 'child_pid': 101, 'not_before_ns': 900_000_000,
                'not_after_ns': 20_000_000_000, 'limits': dict(w.LIMITS)}
    phases = [{'name': name, 'start_ns': 1_100_000_000 + i * 100_000_000,
               'end_ns': 1_200_000_000 + i * 100_000_000,
               'aggregate_cgroup': group, 'completed': True} for i, name in enumerate(w.PHASES)]
    observations = []
    for at, usage, current, peak in [(1_000_000_000, 0, 10_000_000, 10_000_000),
                                      (2_900_000_000, 500_000, 20_000_000, 30_000_000),
                                      (3_500_000_000, 700_000, 0, 30_000_000)]:
        observations.append({'at_ns': at, 'aggregate_cgroup': group, 'cpu_usage_usec': usage,
                             'cpu_max': '3000 10000', 'cpu_max_burst_usec': 0,
                             'memory_max_bytes': 536_870_912, 'memory_current_bytes': current,
                             'memory_peak_bytes': peak, 'swap_max_bytes': 0, 'swap_current_bytes': 0,
                             'memory_events': dict.fromkeys(w.EVENTS, 0)})
    evidence = {'schema': 'PHASE7I_WORKFLOW_EVIDENCE_V1', 'source_revision': 'a' * 40,
                'run_id': 'b' * 32, 'unit': unit, 'evidence_kind': 'SYNTHETIC',
                'receipt_complete': True, 'phases': phases,
                'members': {name: {'pid': expected[name + '_pid'], 'cgroup': group}
                            for name in ('controller', 'child')},
                'timeline': {'clock': 'CLOCK_MONOTONIC_NS', 'activation_start_ns': 1_000_000_000,
                             'main_entered_ns': 1_100_000_000, 'main_exit_ns': 3_000_000_000,
                             'cleanup_complete_ns': 3_500_000_000},
                'observations': observations,
                'controller_final': {'at_ns': 2_900_000_000, 'aggregate_cgroup': group,
                                     'controller_alive': True, 'cgroup_populated': True, 'pids': [100]},
                'manager_cleanup': {'at_ns': 3_500_000_000, 'aggregate_cgroup': group,
                                    'observer': 'systemd_manager', 'controller_alive': False,
                                    'cgroup_populated': False, 'pids': []},
                'disk': {'scope': 'VOLATILE_ONLY', 'allocated_bytes': 1024,
                         'hard_limit_bytes': 9_437_184, 'inode_count': 4, 'inode_limit': 1280}}
    return evidence, expected


class WorkflowEvidenceTests(unittest.TestCase):
    def assertClosed(self, result):
        self.assertIs(result['FULL_CONTROLLER_RESOURCE_ENFORCEMENT_IMPLEMENTED'], False)
        self.assertIs(result['FULL_LAUNCH_ENVELOPE_VERIFIED'], False)
        self.assertEqual(result['runtime_acceptance'], 'NOT_ESTABLISHED_BY_PURE_JSON_VERIFIER')

    def check_failure(self, evidence, expected):
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertClosed(result)

    def test_independent_exact_integer_arithmetic_and_full_wall(self):
        evidence, expected = sample()
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'PASS_NUMERICAL_AUDIT')
        actual = result['measurements']
        self.assertEqual(actual['aggregate_CPU_observed_lower_bound_usec'], 700_000)
        self.assertEqual(actual['aggregate_wall_observed_ns'], 2_500_000_000)
        self.assertEqual(actual['peak_RAM_observed_lower_bound_bytes'], 30_000_000)
        self.assertEqual(actual['max_observed_swap_current_bytes'], 0)
        independent_rate = Fraction(2_500_000_000, 1000) * Fraction(3000, 10000) + 3000
        self.assertEqual(actual['nominal_CPU_rate_budget_usec'], independent_rate)
        self.assertNotEqual(actual['aggregate_CPU_observed_lower_bound_usec'], independent_rate)
        self.assertIs(actual['CPU_activation_and_cleanup_covered'], True)
        self.assertEqual(result['persistent_capacity_acceptance'],
                         'NOT_ESTABLISHED_BY_DECLARED_NUMBERS_OR_VOLATILE_SCOPE')
        self.assertClosed(result)

    def test_runtime_label_and_forged_approval_never_enable_full(self):
        evidence, expected = sample()
        evidence['evidence_kind'] = 'UNVERIFIED_RUNTIME'
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'PASS_NUMERICAL_AUDIT')
        self.assertClosed(result)
        for name, value in [('FULL_LAUNCH_ENVELOPE_VERIFIED', True), ('authorized', True),
                             ('human_approval', {'valid': True})]:
            altered = copy.deepcopy(evidence)
            altered[name] = value
            self.check_failure(altered, expected)

    def test_exact_phases_order_and_no_extra_phase(self):
        evidence, expected = sample()
        for transform in (lambda p: p[:-1], lambda p: p + p[-1:],
                          lambda p: [p[1], p[0], *p[2:]]):
            altered = copy.deepcopy(evidence)
            altered['phases'] = transform(altered['phases'])
            self.check_failure(altered, expected)

    def test_incomplete_receipt_and_phase_are_unknown(self):
        evidence, expected = sample()
        for target in ('receipt', 'phase'):
            altered = copy.deepcopy(evidence)
            if target == 'receipt':
                altered['receipt_complete'] = False
            else:
                altered['phases'][3]['completed'] = False
            result = w.verify(altered, expected)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertClosed(result)

    def test_counter_units_extra_keys_and_all_noninteger_numbers_rejected(self):
        evidence, expected = sample()
        for value in [True, False, -1, 0.0, float('nan'), float('inf'), Decimal('700000'), Fraction(1, 2), '700000', 2**63]:
            altered = copy.deepcopy(evidence)
            altered['observations'][-1]['cpu_usage_usec'] = value
            self.check_failure(altered, expected)
        altered = copy.deepcopy(evidence)
        altered['observations'][-1]['cpu_usage_seconds'] = 1
        self.check_failure(altered, expected)
        evidence['timeline']['clock'] = 'CLOCK_MONOTONIC_USEC'
        self.check_failure(evidence, expected)

    def test_counter_reset_nonzero_baseline_and_cpu_over_cap_rejected(self):
        evidence, expected = sample()
        for changes in ((0, 1), (2, 400_000), (2, 4_000_001)):
            altered = copy.deepcopy(evidence)
            altered['observations'][changes[0]]['cpu_usage_usec'] = changes[1]
            self.check_failure(altered, expected)

    def test_missing_activation_or_cleanup_counter_is_unknown_lower_bound(self):
        evidence, expected = sample()
        for index in (0, 2):
            altered = copy.deepcopy(evidence)
            altered['observations'][index]['cpu_usage_usec'] = None
            result = w.verify(altered, expected)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertFalse(result['measurements']['CPU_activation_and_cleanup_covered'])
            self.assertClosed(result)
        evidence['observations'][0]['at_ns'] += 1
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertFalse(result['measurements']['CPU_activation_and_cleanup_covered'])
        evidence, expected = sample()
        for index in (0, 2):
            evidence['observations'][index]['cpu_usage_usec'] = None
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIsNone(result['measurements']['aggregate_CPU_observed_lower_bound_usec'])

    def test_missing_memory_peak_never_becomes_zero(self):
        evidence, expected = sample()
        for row in evidence['observations']:
            row.pop('memory_peak_bytes')
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIsNone(result['measurements']['peak_RAM_observed_lower_bound_bytes'])
        self.assertFalse(result['measurements']['memory_peak_complete'])
        self.assertClosed(result)

    def test_partial_peak_is_explicit_lower_bound_and_unknown(self):
        evidence, expected = sample()
        evidence['observations'][-1]['memory_peak_bytes'] = None
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['measurements']['peak_RAM_observed_lower_bound_bytes'], 30_000_000)
        self.assertFalse(result['measurements']['memory_peak_complete'])

    def test_ram_current_peak_swap_and_oom_negatives(self):
        evidence, expected = sample()
        changes = [('memory_max_bytes', 1), ('memory_current_bytes', 536_870_913),
                   ('memory_peak_bytes', 536_870_913), ('memory_peak_bytes', 1),
                   ('swap_max_bytes', 1), ('swap_current_bytes', 1)]
        for name, value in changes:
            altered = copy.deepcopy(evidence)
            altered['observations'][-1][name] = value
            self.check_failure(altered, expected)
        for event in ('oom', 'oom_kill', 'oom_group_kill'):
            altered = copy.deepcopy(evidence)
            altered['observations'][-1]['memory_events'][event] = 1
            self.check_failure(altered, expected)
        evidence['observations'][1]['memory_events']['max'] = 1
        self.check_failure(evidence, expected)
        evidence['observations'][0]['memory_events'] = None
        evidence['observations'][-1]['memory_events']['max'] = 1
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIn('MEMORY_EVENT_ACTIVATION_BASELINE_MISSING', result['unknown'])

    def test_wall_boundary_exactly_13s_then_one_ns_over(self):
        evidence, expected = sample()
        for end, expected_status in [(14_000_000_000, 'PASS_NUMERICAL_AUDIT'),
                                     (14_000_000_001, 'FAIL')]:
            altered = copy.deepcopy(evidence)
            altered['timeline']['cleanup_complete_ns'] = end
            altered['manager_cleanup']['at_ns'] = end
            altered['observations'][-1]['at_ns'] = end
            result = w.verify(altered, expected)
            self.assertEqual(result['status'], expected_status)
            self.assertEqual(result['measurements']['aggregate_wall_observed_ns'], end - 1_000_000_000)
            self.assertClosed(result)

    def test_phase_overlap_and_main_exit_before_cleanup_rejected(self):
        evidence, expected = sample()
        evidence['phases'][1]['start_ns'] = evidence['phases'][0]['start_ns']
        self.check_failure(evidence, expected)
        evidence, expected = sample()
        evidence['timeline']['main_exit_ns'] = evidence['timeline']['cleanup_complete_ns'] + 1
        self.check_failure(evidence, expected)

    def test_foreign_run_source_unit_path_or_stale_time_rejected(self):
        evidence, expected = sample()
        for key, value in [('run_id', 'c' * 32), ('source_revision', 'c' * 40),
                           ('unit', 'other.service')]:
            altered = copy.deepcopy(evidence)
            altered[key] = value
            self.check_failure(altered, expected)
        for suffix in ('/worker', '/other.service', '/../escape', '//'):
            altered = copy.deepcopy(evidence)
            altered['members']['child']['cgroup'] += suffix
            self.check_failure(altered, expected)
        evidence['observations'][1]['at_ns'] = expected['not_after_ns'] + 1
        self.check_failure(evidence, expected)

    def test_controller_self_alive_cannot_claim_empty(self):
        evidence, expected = sample()
        for key, value in [('controller_alive', False), ('cgroup_populated', False), ('pids', [])]:
            altered = copy.deepcopy(evidence)
            altered['controller_final'][key] = value
            self.check_failure(altered, expected)

    def test_postmortem_cleanup_independent_and_complete(self):
        evidence, expected = sample()
        for key, value in [('controller_alive', True), ('cgroup_populated', True),
                           ('pids', [100]), ('observer', 'controller')]:
            altered = copy.deepcopy(evidence)
            altered['manager_cleanup'][key] = value
            self.check_failure(altered, expected)
        evidence['manager_cleanup'] = None
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['cleanup'], 'UNKNOWN')
        self.assertClosed(result)

    def test_disk_byte_inode_bounds_and_no_persistent_promotion(self):
        evidence, expected = sample()
        for key, value in [('allocated_bytes', 16_777_217), ('hard_limit_bytes', 16_777_217),
                           ('inode_count', 1281)]:
            altered = copy.deepcopy(evidence)
            altered['disk'][key] = value
            self.check_failure(altered, expected)
        evidence['disk']['scope'] = 'PERSISTENT_UNVERIFIED'
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'PASS_NUMERICAL_AUDIT')
        self.assertClosed(result)
        evidence['disk']['allocated_bytes'] = None
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertIsNone(result['measurements']['allocated_disk_observed_bytes'])

    def test_expected_contract_cannot_expand_caps_or_accept_other_ancestry(self):
        evidence, expected = sample()
        for name in w.LIMITS:
            altered = copy.deepcopy(expected)
            altered['limits'][name] += 1
            self.check_failure(evidence, altered)
        expected['aggregate_cgroup'] = '/not-reviewed.slice/' + expected['unit']
        self.check_failure(evidence, expected)

    def test_strict_json_duplicate_nan_float_depth_and_size(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.0}', b'\xff', b'x' * 65_537):
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, UnicodeError)):
                w.loads(raw)
        evidence, expected = sample()
        nested = evidence['disk']
        for _ in range(17):
            nested['nested'] = {}
            nested = nested['nested']
        self.check_failure(evidence, expected)

    def test_cumulative_cpu_cap_rejected_even_when_activation_baseline_missing(self):
        evidence, expected = sample()
        evidence['observations'][0]['cpu_usage_usec'] = None
        evidence['observations'][1]['cpu_usage_usec'] = 4_100_000
        evidence['observations'][2]['cpu_usage_usec'] = 4_200_000
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'FAIL')
        self.assertTrue(any('CUMULATIVE_CPU_USAGE_OVER_CAP' in value for value in result['errors']))
        self.assertEqual(result['measurements']['cumulative_CPU_max_observed_usec'], 4_100_000)
        self.assertClosed(result)
        evidence, expected = sample()
        evidence['observations'][0]['cpu_usage_usec'] = None
        evidence['observations'][-1]['cpu_usage_usec'] = 4_000_000
        result = w.verify(evidence, expected)
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertEqual(result['measurements']['cumulative_CPU_max_observed_usec'], 4_000_000)
        self.assertFalse(result['measurements']['CPU_activation_and_cleanup_covered'])
        self.assertClosed(result)

    def test_resource_observations_cannot_escape_lifecycle_window(self):
        for index, when in ((0, 950_000_000), (2, 3_600_000_000)):
            evidence, expected = sample()
            evidence['observations'][index]['at_ns'] = when
            result = w.verify(evidence, expected)
            with self.subTest(index=index, when=when):
                self.assertEqual(result['status'], 'FAIL')
                self.assertTrue(any('RESOURCE_OBSERVATION_OUTSIDE_JOB_WINDOW' in value for value in result['errors']))
                self.assertClosed(result)

    def test_no_io_or_process_side_effects_and_deterministic_result(self):
        evidence, expected = sample()
        before = copy.deepcopy((evidence, expected))
        with patch('builtins.open', side_effect=AssertionError('NO_IO')):
            first = w.verify(evidence, expected)
            second = w.verify(evidence, expected)
        self.assertEqual(first, second)
        self.assertEqual((evidence, expected), before)


if __name__ == '__main__':
    unittest.main()
