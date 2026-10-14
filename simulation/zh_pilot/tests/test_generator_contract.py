"""Portable reviewed-card controls; method checks do not produce physics events."""
from copy import deepcopy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('phase6f_generator_check',REPO/'simulation/zh_pilot/scripts/check_generator.py')
check=importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class GeneratorContractTests(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads(check.CONTRACT.read_text(encoding='utf-8'))

    def test_actual_frozen_bundle_is_portably_consistent(self):
        result=check.validate_bundle(self.contract)
        self.assertEqual(result['preferred_profile'],'ZH_ZBB_STABLE_H')
        self.assertFalse(result['pilot_policy']['physical_events_authorized'])
        self.assertEqual(result['pilot_policy']['cross_section_pb'],'UNKNOWN_NOT_INTEGRATED')

    def test_included_and_missing_branching_factors_are_distinct(self):
        b=self.contract['profiles']['ZH_ZBB_STABLE_H']
        self.assertEqual(b['source_included_decay_ids'],['Z_to_b_bbar'])
        self.assertEqual(b['missing_decay_ids'],['H_to_gamma_gamma'])
        self.assertEqual(b['actual_production_amplitude_orders'],{'QCD':0,'QED':2})
        self.assertEqual(b['actual_decay_amplitude_orders'],{'QCD':0,'QED':1})

    def test_Z_br_cannot_be_added_twice_in_preferred_source_scope(self):
        self.contract['profiles']['ZH_ZBB_STABLE_H']['missing_decay_ids'].insert(0,'Z_to_b_bbar')
        with self.assertRaisesRegex(ValueError,'BR scope'):
            check.validate_bundle(self.contract)

    def test_physical_authority_cannot_be_forged(self):
        self.contract['pilot_policy']['physical_events_authorized']=True
        with self.assertRaisesRegex(ValueError,'Physical production'):
            check.validate_bundle(self.contract)

    def test_incorrect_production_and_decay_order_rejected(self):
        for field,value in [('actual_production_amplitude_orders',{'QCD':0,'QED':3}),
                            ('actual_decay_amplitude_orders',{'QCD':0,'QED':2}),
                            ('factorized_chain_amplitude_orders',{'QCD':0,'QED':2})]:
            changed=deepcopy(self.contract)
            changed['profiles']['ZH_ZBB_STABLE_H'][field]=value
            with self.assertRaises(ValueError):
                check.validate_bundle(changed)

    def test_old_continuum_scale_cannot_replace_threshold_scale(self):
        self.contract['physics']['scales']['muF1_gev']=125.
        with self.assertRaisesRegex(ValueError,'ZH scale'):
            check.validate_bundle(self.contract)

    def test_wrong_flavour_pdf_or_model_scheme_rejected(self):
        for field,value in [('pdlabel','nn23nlo'),('active_flavours',4),('pdf_order',2),('lhaid_is_used',True)]:
            changed=deepcopy(self.contract)
            changed['physics']['pdf'][field]=value
            with self.assertRaisesRegex(ValueError,'PDF scheme'):
                check.validate_bundle(changed)
        self.contract['physics']['proton_pdgs'].remove(5)
        with self.assertRaisesRegex(ValueError,'flavour scheme'):
            check.validate_bundle(self.contract)

    def test_no_unexecuted_gluon_component_or_higgs_decay_claim(self):
        for field in ('loop_induced_gg_ZH_included','H_gamma_gamma_tree_decay_included'):
            changed=deepcopy(self.contract)
            changed['physics'][field]=True
            with self.assertRaisesRegex(ValueError,'production scope'):
                check.validate_bundle(changed)

    def test_card_edit_and_rehashed_unreviewed_card_both_rejected(self):
        scratch=REPO/'.local/phase6f/tests'
        scratch.mkdir(parents=True,exist_ok=True)
        self.assertIn(REPO,scratch.resolve().parents)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            repo=Path(temp)
            for item in self.contract['cards']:
                dst=repo/item['path'];dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes((REPO/item['path']).read_bytes())
            card=self.contract['cards'][1]
            path=repo/card['path']
            path.write_bytes(path.read_bytes()+b'output /tmp/forbidden\nlaunch\n')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                check.validate_bundle(self.contract,repo)
            card['sha256']=check.file_sha256(path)
            with self.assertRaisesRegex(ValueError,'SHA256'):
                check.validate_bundle(self.contract,repo)

    def test_duplicate_missing_and_escaping_card_paths_rejected(self):
        for action in ('duplicate','missing','escape'):
            changed=deepcopy(self.contract)
            if action=='duplicate':changed['cards'].append(changed['cards'][0])
            elif action=='missing':changed['cards'].pop()
            else:changed['cards'][0]['path']='../outside.txt'
            with self.assertRaises(ValueError):
                check.validate_bundle(changed)

    def test_finite_exact_parameter_parsing_and_ambiguous_rejection(self):
        self.assertEqual(check.parse_param('Block MASS\n23 9.1188D1\nDECAY 25 6.38233934E-3\n')[('decay',25)],Decimal('0.00638233934'))
        for text in ('Block MASS\n23 91\n23 92\n','Block MASS\n25 NaN\n','DECAY 25 Auto\n','DECAY 23 2.4\n1.0 2 5 -5\n'):
            with self.assertRaises(Exception):check.parse_param(text)

    def test_run_card_duplicate_nonfinite_and_empty_hook_handling(self):
        self.assertEqual(check.parse_run(' = custom_fcts\nTrue = fixed_ren_scale\n216.188 = scale\n'),
                         {'custom_fcts':[],'fixed_ren_scale':True,'scale':216.188})
        for text in ('100 = nevents\n101 = nevents\n','1e999 = scale\n'):
            with self.assertRaises(ValueError):check.parse_run(text)

    def test_exact_masses_and_widths_are_not_pythia_effective_widths(self):
        self.contract['physics']['widths_gev']['Z']=2.504200690086664
        with self.assertRaisesRegex(ValueError,'mass/width'):
            check.validate_bundle(self.contract)

    def test_installed_parse_receipt_when_publicly_available(self):
        receipt_path=REPO/'simulation/zh_pilot/evidence/generator_checks.json'
        if not receipt_path.is_file():self.skipTest('Installed parse receipt not prepared yet')
        receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
        self.assertEqual(receipt['generator_contract_sha256'],check.file_sha256(check.CONTRACT))
        self.assertEqual(receipt['checker_source_sha256'],check.file_sha256(REPO/'simulation/zh_pilot/scripts/check_generator.py'))
        self.assertEqual(receipt['status'],'PASS_PARSE_AND_CARD_READBACK_ONLY')
        self.assertEqual(receipt['events_generated'],0)
        self.assertFalse(receipt['process_export_integration_launch_width_calculation_executed'])
        for profile in receipt['checks']:
            production=[r for r in profile['amplitude_records'] if r['scope']=='production']
            self.assertEqual(len(production),5)
            self.assertEqual({abs(r['initial_pdgs'][0]) for r in production},{1,2,3,4,5})
            self.assertTrue(all(r['diagram_count']==1 and r['actual_amplitude_orders']==[{'QCD':0,'QED':2}] for r in production))
            self.assertEqual(profile['decay_record_count'],int(profile['profile']=='ZH_ZBB_STABLE_H'))


if __name__=='__main__':unittest.main()
