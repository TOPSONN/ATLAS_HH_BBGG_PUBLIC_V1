import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from pilot_policy import *
class PilotBoundary(unittest.TestCase):
 def contract(self):return json.loads((Path(__file__).resolve().parents[1]/'config/bounded_pilot_contract.json').read_text())
 def test_current_contract_is_inactive(self):self.assertTrue(validate_contract(self.contract()))
 def test_no_missing_field_can_be_defaulted_to_zero(self):
  c=self.contract();key=next(iter(c['unresolved_fields']));c['unresolved_fields'][key]['value']=0
  with self.assertRaises(ValueError):validate_contract(c)
 def test_each_nonzero_physics_counter_rejected(self):
  for key in COUNTERS:
   c=self.contract();c[key]=1
   with self.subTest(key=key),self.assertRaises(ValueError):validate_contract(c)
 def test_false_is_not_integer_zero(self):
  c=self.contract();c['NEW_ME_CALLS']=False
  with self.assertRaises(ValueError):validate_contract(c)
 def test_illustrative_limits_do_not_grant_approval(self):
  c=self.contract();c['resource_review']['new_hard_events']['approved_limit']=1000
  with self.assertRaises(ValueError):validate_contract(c)
 def test_claimed_resource_enforcement_rejected(self):
  c=self.contract();c['resource_review']['ME_evaluations']['enforcement_status']='ENFORCED'
  with self.assertRaises(ValueError):validate_contract(c)
 def test_approval_boolean_cannot_activate_dispatcher(self):
  for key,value in [('execution_authorized',True),('instantiable',True),('dispatcher','mg5'),('approval_override_flag','--approved')]:
   c=self.contract();c[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):validate_contract(c)
 def test_unknown_nuisance_covariance_cannot_be_zero(self):
  c=self.contract();c['unknown_nuisances']['covariance']=[[0.]]
  with self.assertRaises(ValueError):validate_contract(c)
 def test_method_tests_cannot_unlock_physical_gate(self):
  for key in PHYSICAL_GATES:
   c=self.contract();c[key]='VALIDATED'
   with self.subTest(key=key),self.assertRaises(ValueError):validate_contract(c)
 def test_human_signoff_not_fabricated(self):
  c=self.contract();c['external_human_review_approval']=True
  with self.assertRaises(ValueError):validate_contract(c)
 def test_no_physical_sum_or_fake_probability(self):
  for key,value in [('inclusive_background_total',True),('calibrated_fake_probability',0.)]:
   c=self.contract();c[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):validate_contract(c)
 def test_fresh_output_required(self):
  c=self.contract();c['existing_output_reuse_allowed']=True
  with self.assertRaises(ValueError):validate_contract(c)
 def test_card_comment_safety(self):
  self.assertTrue(validate_inactive_card('# INACTIVE\n# generate p p > a a\n'))
  with self.assertRaises(ValueError):validate_inactive_card('# INACTIVE\nlaunch\n')
 def test_missing_compatibility_means_none_ready(self):
  r={k:{field:dict(status='BLOCKED',evidence='source hash',reason='missing compatible installed binding') for field in REQUIREMENT_KEYS} for k in COMPONENTS};self.assertEqual(select_component(r),'NONE_READY')
 def test_distinguish_source_eligible_from_execution_approval(self):
  r={k:{field:dict(status='SOURCE_SUPPORTED',evidence='fixture',reason='synthetic contract only') for field in REQUIREMENT_KEYS} for k in COMPONENTS};self.assertEqual(select_component(r),COMPONENTS[0]);self.assertFalse(self.contract()['execution_authorized'])
 def test_missing_pdf_or_ir_or_alpha_requirement_rejected(self):
  for key in REQUIREMENT_KEYS:
   c=self.contract();del c['source_requirements'][COMPONENTS[0]][key]
   with self.subTest(key=key),self.assertRaises(ValueError):validate_contract(c)
 def test_selected_candidate_cannot_ignore_blocked_source_requirements(self):
  c=self.contract();c['selected_component']=COMPONENTS[0]
  with self.assertRaises(ValueError):validate_contract(c)
 def test_omitted_scientific_fields_fail_closed(self):
  for key in PAYLOAD_KEYS:
   c=self.contract();del c[key]
   with self.subTest(key=key),self.assertRaises(ValueError):validate_contract(c)
 def test_retained_counter_type_is_strict(self):
  for value in (False,0.):
   c=self.contract();c['retained_new_physical_events']=value
   with self.subTest(value=value),self.assertRaises(ValueError):validate_contract(c)
 def test_5f_pdf_cannot_fill_unselected_4f_contract(self):
  c=self.contract();c['PDF_member_flavour_scheme']={'set':'cteq6l1','num_flavours':5}
  with self.assertRaises(ValueError):validate_contract(c)
 def test_unknown_alpha_or_cuts_not_zero_or_default(self):
  for key in ('alpha_s_and_thresholds','photon_IR_definition','generation_cuts','shower_settings','scale_definition'):
   for value in (0,False,{}):
    c=self.contract();c[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate_contract(c)
 def test_fabricated_all_supported_rows_do_not_select_unconfigured_component(self):
  c=self.contract();c['selected_component']=COMPONENTS[0]
  for row in c['source_requirements'][COMPONENTS[0]].values():row['status']='SOURCE_SUPPORTED'
  with self.assertRaises(ValueError):validate_contract(c)
 def test_future_cpu_limit_is_explicit_unknown_not_threads_times_wall(self):
  c=self.contract();self.assertIsNone(c['aggregate_future_CPU_seconds']);c['aggregate_future_CPU_seconds']=14400
  with self.assertRaises(ValueError):validate_contract(c)
class SignedWeightAlgebra(unittest.TestCase):
 def test_signed_cancellation_not_zero_uncertainty(self):
  s=signed_source_statistics([1.,-1.,0.,0.],[True]*4);self.assertEqual(s['sumw'],0);self.assertGreater(s['fixed_N_variance'],0);self.assertIsNone(s['relative_SE'])
 def test_all_original_failures_kept(self):self.assertAlmostEqual(signed_source_statistics([2.]*4,[True,False,False,False])['fixed_N_variance'],4.)
 def test_negative_selected_sum_keeps_sign(self):self.assertEqual(signed_source_statistics([-2.,1.,1.],[True,False,False])['sumw'],-2.)
 def test_nonfinite_weight_rejected(self):
  with self.assertRaises(ValueError):signed_source_statistics([float('nan'),1.],[True]*2)
if __name__=='__main__':unittest.main()
