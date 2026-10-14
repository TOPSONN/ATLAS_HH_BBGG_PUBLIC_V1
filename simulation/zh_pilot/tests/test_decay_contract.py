import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('phase6f_decay', REPO/'simulation/zh_pilot/scripts/check_decay_tables.py')
decay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decay)


class DecayContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((REPO/'simulation/zh_pilot/config/decay_contract.json').read_text())
        self.receipt = json.loads((REPO/'simulation/zh_pilot/evidence/decay_tables.json').read_text())

    def reject(self, key, value):
        self.contract[key] = value
        with self.assertRaises(ValueError):
            decay.validate_decay_contract(self.contract)

    def test_audited_default_is_method_only(self):
        result = decay.validate_decay_contract(self.contract)
        self.assertEqual(result['status'], 'METHOD_ONLY')
        self.assertEqual(result['events_generated'], 0)
        self.assertEqual(result['external_lhe_weight_closure'], 'UNKNOWN')
        self.assertEqual(self.contract['nominal_weight_columns'],
            ['input_contribution_pb', 'LHE_XWGTUP_pb', 'Pythia_Info_weight_pb', 'converter_weight_0_pb'])

    def test_physical_request_remains_blocked(self):
        with self.assertRaises(ValueError):
            decay.validate_decay_contract(self.contract, allow_planning=False)

    def test_actual_receipt_is_zero_event_table_probe(self):
        self.assertEqual(decay.validate_probe(self.receipt['tables']), 'PASS_NO_EVENT_TABLE_COMPATIBILITY_ONLY')
        self.assertEqual(self.receipt['next_calls'], 0)
        self.assertEqual(self.receipt['new_physics_events'], 0)

    def test_forcing_retains_inclusive_br_not_one(self):
        probe = self.receipt['tables']
        inclusive = decay.target_channel(probe['inclusive_after_init']['H'], [22, 22])
        forced = decay.target_channel(probe['preferred_B_H_only_after_init']['H'], [22, 22])
        self.assertEqual(forced['stored_inclusive_br'], inclusive['stored_inclusive_br'])
        self.assertLess(Decimal(forced['stored_inclusive_br']), Decimal('0.01'))
        self.assertEqual(probe['preferred_B_H_only_after_init']['Z'], probe['inclusive_after_init']['Z'])

    def test_changed_probe_physical_counter_rejected(self):
        probe = copy.deepcopy(self.receipt['tables'])
        probe['next_calls'] = 1
        with self.assertRaises(ValueError):
            decay.validate_probe(probe)

    def test_changed_preferred_z_table_rejected(self):
        probe = copy.deepcopy(self.receipt['tables'])
        probe['preferred_B_H_only_after_init']['Z']['channels'][0]['on_mode'] = 0
        with self.assertRaises(ValueError):
            decay.validate_probe(probe)

    def test_nan_and_infinity_rejected(self):
        for value in ('NaN', 'Infinity', '-Infinity', 'UNKNOWN', '-0.1', '1.01'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decay.exact_probability(value)
        with self.assertRaises(ValueError):
            decay.strict_json('{"BR": NaN}')

    def test_model_br_is_not_physical_adoption(self):
        for field in ('physical_adopted_BR', 'physical_adopted_total_width_gev', 'physical_adopted_partial_width_gev'):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.contract)
                changed['decays']['H_to_gamma_gamma'][field] = '0.002270'
                with self.assertRaises(ValueError):
                    decay.validate_decay_contract(changed)

    def test_weight_names_units_and_conversion_cannot_change(self):
        for field, value in (('nominal_weight_columns', []),
                             ('nominal_weight_columns', ['input_contribution_pb', 'LHE_XWGTUP_pb', 'Pythia_Info_weight_pb', 'invented_nominal']),
                             ('units', dict(self.contract['units'], pb_per_mb='1')),
                             ('units', dict(self.contract['units'], Pythia_Info_weight='MB'))):
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(self.contract)
                changed[field] = value
                with self.assertRaises(ValueError):
                    decay.validate_decay_contract(changed)

    def test_width_ratio_must_match(self):
        self.contract['decays']['H_to_gamma_gamma']['model_partial_width_gev'] = '0.0001'
        with self.assertRaises(ValueError):
            decay.validate_decay_contract(self.contract)

    def test_selfconsistent_fabricated_table_values_rejected(self):
        record = self.contract['decays']['H_to_gamma_gamma']
        record.update(model_total_width_gev='0.004', model_partial_width_gev='0.000008', model_inclusive_BR='0.002')
        with self.assertRaises(ValueError):
            decay.validate_decay_contract(self.contract)

    def test_probe_hash_mismatch_rejected(self):
        self.contract['probe_evidence']['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            decay.validate_decay_contract(self.contract)

    def test_unsafe_binding_rejected(self):
        for path in ('../outside.json', '/absolute/path.json'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                decay.checked_binding({'path': path, 'sha256': '0'*64})

    def test_source_z_decay_cannot_disappear_or_duplicate(self):
        for ledger in ([], ['Z_to_b_bbar', 'Z_to_b_bbar'], ['Z_to_b_bbar', 'H_to_gamma_gamma']):
            with self.subTest(ledger=ledger):
                self.reject('source_included_decay_ids', ledger)

    def test_truthy_unknown_cannot_authorize(self):
        self.reject('physical_production_authorized', 'UNKNOWN')

    def test_unknown_nominal_inclusion_cannot_be_replaced(self):
        self.reject('nominal_decay_ids_in_pythia_weight', [])

    def test_route_b_cannot_force_z(self):
        self.reject('pythia_forcing_switches', ['23:onMode = off', '25:onMode = off', '25:onIfMatch = 22 22'])

    def test_schema_boolean_rejected(self):
        self.reject('schema_version', True)

    def algebra(self, source=None, nominal=None, applied=None, **kw):
        return decay.synthetic_missing_br_factor(source_included_decay_ids=source or [],
            nominal_additional_decay_ids=nominal or [], already_applied_decay_ids=applied or [],
            branching_ratios={'Z_to_b_bbar': '0.15', 'H_to_gamma_gamma': '0.002'}, **kw)

    def test_synthetic_a_applies_two_missing_factors(self):
        factor, missing = self.algebra()
        self.assertEqual(factor, Decimal('0.00030'))
        self.assertEqual(set(missing), set(decay.DECAY_IDS))

    def test_synthetic_b_applies_h_only(self):
        factor, missing = self.algebra(source=['Z_to_b_bbar'])
        self.assertEqual(factor, Decimal('0.002'))
        self.assertEqual(missing, ['H_to_gamma_gamma'])

    def test_synthetic_nominal_embeds_h_no_reapply(self):
        self.assertEqual(self.algebra(source=['Z_to_b_bbar'], nominal=['H_to_gamma_gamma']), (Decimal(1), []))

    def test_synthetic_double_factor_rejected(self):
        with self.assertRaises(ValueError):
            self.algebra(source=['Z_to_b_bbar'], applied=['Z_to_b_bbar'])

    def test_synthetic_scope_cannot_be_physical(self):
        with self.assertRaises(ValueError):
            self.algebra(fixture_scope='PHYSICAL_PASS')

    def test_malformed_ledgers_fail_closed(self):
        for value in ('Z_to_b_bbar', ['Z_to_b_bbar', 'Z_to_b_bbar'], [{}], [''], ['Z_bb']):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decay.ids(value)


if __name__ == '__main__':
    unittest.main()
