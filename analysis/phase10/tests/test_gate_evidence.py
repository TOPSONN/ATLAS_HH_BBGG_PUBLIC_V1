import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('phase10_gate_builder',Path(__file__).resolve().parents[1]/'scripts/build_gate_matrix.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class GateReceiptBinding(unittest.TestCase):
 def fixtures(self):
  return {
   'source-review':dict(evidence_class='ACTUAL_EXISTING_DATA_READBACK',status='PASS_WITH_LIMITS',new_physical_events=0,external_independent_human_approval=False),
   'heavy-flavour':dict(evidence_class='ACTUAL_EXISTING_DATA_READBACK',status='VALIDATED_WITH_LIMITS',source_events_joined=6000,source_events_stratified=3000,heavy_flavour_generator_exclusivity='UNVERIFIED',new_physical_events=0),
   'photon':dict(evidence_class='ACTUAL_EXISTING_DATA_READBACK',status='BLOCKED_MISSING_COMPATIBLE_OBSERVABLES',actual_existing_events_joined=6000,physical_fake_rate='UNKNOWN',compatible_public_calibration_imported=False,synthetic_result_used_in_physical_output=False,new_ME_calls=0,new_integrals=0,new_hard_events=0,new_Pythia_events=0,new_Delphes_events=0),
   'sideband':dict(evidence_class='SYNTHETIC_METHOD_ONLY',status='PASS_SYNTHETIC_METHOD_ONLY',checks={'closure':True},import_into_physical_results=False,new_physical_events=0),
   'precision':dict(evidence_class='HISTORICAL_SOURCE_AUDIT',status='PASS_INDEPENDENT_PRECISION_ARITHMETIC_WITH_LIMITS',error_count=0,new_independent_hard_events=0),
   'pilot':dict(evidence_class='FUTURE_UNEXECUTED_PROPOSAL',status='PREPARED_INACTIVE_BLOCKED',execution_authorized=False,physical_pilot_executed=False,instantiable=False,actual_new_production={k:0 for k in ('new_me_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events')},offline_validation={'valid_inactive_contract':True,'errors':[]})}
 def run_builder(self,fixtures):
  with tempfile.TemporaryDirectory() as td:
   args=['build_gate_matrix.py'];root=Path(td)
   for key,value in fixtures.items():
    p=root/(key+'.json');p.write_text(json.dumps(value));args+=['--'+key,str(p)]
   args+=['--output',str(root/'result.json')]
   with patch.object(sys,'argv',args):m.main()
 def test_pilot_actual_me_counter_cannot_be_hidden_by_hardcoded_matrix_zero(self):
  f=self.fixtures();f['pilot']['actual_new_production']['new_me_calls']=1
  with self.assertRaisesRegex(ValueError,'PILOT_PRODUCTION_COUNTERS'):self.run_builder(f)
 def test_failed_offline_contract_cannot_become_policy_pass(self):
  f=self.fixtures();f['pilot']['offline_validation']['valid_inactive_contract']=False
  with self.assertRaisesRegex(ValueError,'PILOT_OFFLINE'):self.run_builder(f)
 def test_synthetic_input_cannot_impersonate_real_hf(self):
  f=self.fixtures();f['heavy-flavour']['evidence_class']='SYNTHETIC_METHOD_ONLY'
  with self.assertRaisesRegex(ValueError,'MISSING_BOUND_EVIDENCE'):self.run_builder(f)
if __name__=='__main__':unittest.main()
