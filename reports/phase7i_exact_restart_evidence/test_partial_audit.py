"""Pure Python negative regression; no native program or physics evaluation."""
import copy,json,unittest
from pathlib import Path
from audit_partial import audit

class PartialAudit(unittest.TestCase):
    def setUp(self):self.r=json.loads((Path(__file__).parent/'execution_receipt.public.json').read_text())
    def test_actual_partial_receipt_has_no_cross_section(self):
        a=audit(self.r)
        self.assertIsNone(a['sigma_pb']);self.assertIsNone(a['native_internal_error_pb'])
        self.assertEqual(a['observed_outer_ME_entries'],0);self.assertIsNone(a['integrand_calls'])
        self.assertEqual(a['effective_RANMAR_state'],[910001,0,0,1,26066,23739])
    def test_method_fixture_cannot_become_actual_dispatch(self):
        self.r['stages'][0]['receipt']['execution_class']='METHOD_ONLY'
        with self.assertRaisesRegex(ValueError,'METHOD_EVIDENCE'):audit(self.r)
    def test_partial_cannot_be_promoted_to_complete(self):
        self.r['status']='COMPLETE_FIXED_ENDPOINTS'
        with self.assertRaisesRegex(ValueError,'MUST_NOT_BE_PROMOTED'):audit(self.r)
    def test_followup_seed_forbidden(self):
        s=copy.deepcopy(self.r['stages'][0]);s['seed']=910019;self.r['stages'].append(s)
        with self.assertRaisesRegex(ValueError,'FOLLOWUP_WORK'):audit(self.r)
    def test_same_seed_measurement_forbidden(self):
        s=copy.deepcopy(self.r['stages'][0]);s['stage']='measurement';self.r['stages'].append(s)
        with self.assertRaisesRegex(ValueError,'FOLLOWUP_WORK'):audit(self.r)
    def test_entry_marker_must_change_the_observed_count(self):
        self.r['stages'][0]['receipt']['records'].append('HI_ME_ENTRY 17')
        self.assertEqual(audit(self.r)['observed_outer_ME_entries'],17)
    def test_no_invented_final_counter(self):
        self.r['stages'][0]['receipt']['records'].append('HI_COUNTS 0 0 0 0 0')
        with self.assertRaisesRegex(ValueError,'FINAL_COUNTER'):audit(self.r)
    def test_wrong_seed_state_is_rejected(self):
        rows=self.r['stages'][0]['receipt']['records']
        rows[:]=[s.replace('26066','26067') if s.startswith('HI_SEED ') else s for s in rows]
        with self.assertRaisesRegex(ValueError,'RANMAR_STATE'):audit(self.r)
    def test_wrong_source_is_rejected(self):
        self.r['reviewed_revision']='be106725481a58873b8e13a0dd72f03599865ac9'
        with self.assertRaisesRegex(ValueError,'SOURCE_MISMATCH'):audit(self.r)
    def test_missing_stop_diagnostic_is_unknown_not_success(self):
        self.r['stages'][0]['receipt']['bounded_runtime_errors']=[]
        with self.assertRaisesRegex(ValueError,'MISSING_STOP92'):audit(self.r)

if __name__=='__main__':unittest.main()
