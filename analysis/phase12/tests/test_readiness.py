"""Portable synthetic readiness fixtures. No network, native PDF or generator calls."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source"))
import readiness_policy as policy

class ReadinessEvidence(unittest.TestCase):
 def setUp(self):
  self.contract=json.loads((Path(__file__).resolve().parents[1]/"config/scientific_contract.json").read_text())
 def runtime(self):
  current=copy.deepcopy(self.contract["runtime_proposed_identity"])
  rows=[{"fixture_scope":"SYNTHETIC_METHOD_ONLY_NO_RUNTIME_OBSERVATION","evidence_class":"ACTUAL_RAW_RUNTIME_OBSERVATION",
         "status":"PASS_BOUNDED_READ_ONLY_SNAPSHOT","pid":pid,"parent_pid":100,"raw_identity":copy.deepcopy(current),
         "cold_cache_independence_claimed":False,"installed_file_write_performed":False,
         "new_ME_calls":0,"new_integrals":0,"new_hard_events":0,"new_pythia_events":0,"new_delphes_events":0,
         "file_metadata_after":{"device":1,"inode":2,"bytes":current["bytes"],"mtime_ns":1,"ctime_ns":1},
         "resolved_path":"/SYNTHETIC_METHOD_ONLY/config"} for pid in (101,102,103)]
  snapshots={"fixture_scope":"SYNTHETIC_METHOD_ONLY_NO_RUNTIME_OBSERVATION","evidence_class":"ACTUAL_RAW_RUNTIME_OBSERVATION",
             "status":"THREE_SEQUENTIAL_SNAPSHOTS_STABLE_WITH_LIMITS","snapshots":rows,"raw_bytes_stable":True,
             "file_identity_stable":True,"current_raw_identity":copy.deepcopy(current),
             "new_ME_calls":0,"new_integrals":0,"new_hard_events":0,"new_pythia_events":0,"new_delphes_events":0}
  proposal={"status":"PROPOSED_UNAPPROVED","new_observed_raw_identity":copy.deepcopy(current),"new_baseline_approved":False,
            "physical_execution_authorized":False,"dispatcher":None,"old_phase11_raw_gate":"BLOCKED_EXTERNAL_RUNTIME_CONFIGURATION_DRIFT"}
  return snapshots,proposal,current
 def native(self):
  c=self.contract
  info={"path":"/SYNTHETIC_METHOD_ONLY/set.info","bytes":2345,"sha256":c["PDF_info_sha256"]}
  member={"path":"/SYNTHETIC_METHOD_ONLY/set_0000.dat","bytes":683592,"sha256":c["PDF_member_sha256"]}
  flavours=[-4,-3,-2,-1,1,2,3,4,21]
  metadata={"set_name":c["PDF_candidate"],"data_version":2,"member":0,"member_lhaid":263400,"set_index":263400,
            "flavours":flavours.copy(),"bottom_pdf_activation":False,"PDF_order_QCD":0,"PDF_flavour_scheme":"variable",
            "PDF_maximum_flavours":4,"alpha_order_QCD":0,"alpha_type":"ipol","alpha_flavour_scheme":"variable",
            "alpha_maximum_flavours":4,"alpha_reference":copy.deepcopy(c["PDF_declared_alpha_reference"]),
            "info_identity":info,"member_identity":member}
  dependencies={info["path"]:copy.deepcopy(info),member["path"]:copy.deepcopy(member)}
  for index in range(8):
   name="/SYNTHETIC_METHOD_ONLY/dependency_"+str(index)
   dependencies[name]={"path":name,"bytes":1,"sha256":"a"*64}
  alpha=[{"Q_GeV":q,"alpha_s":value} for q,value in (
   (4.1799998,.254403024565842),(10.,.1965543155814504),(91.1876,.12470053368074485),
   (100.,.12282594881647993),(1000.,.08932158963547387))]
  diagnostic={"declared_reference":copy.deepcopy(c["PDF_declared_alpha_reference"]),
              "native_alpha_at_declared_Q":alpha[0]["alpha_s"],"absolute_difference":6.681238414185664e-7,
              "relative_difference":2.626248635282933e-6,"within_strict_diagnostic_tolerance":False,
              "strict_diagnostic_relative_tolerance":1e-6,"comparison_role":"DIAGNOSTIC_NOT_OFFICIAL_ACCURACY_TEST",
              "physical_ME_or_shower_alpha_binding":"UNVERIFIED_NOT_EXECUTED",
              "reference_is_exact_alpha_table_knot":False,"publisher_interpolation_accuracy_bound":None}
  native={"fixture_scope":"SYNTHETIC_METHOD_ONLY_NO_NATIVE_READBACK","evidence_class":"ACTUAL_ISOLATED_PDF_READBACK",
          "status":"PASS_ISOLATED_NATIVE_PDF_INTERFACE_WITH_LIMITS","reader_version":"6.5.6",
          "metadata":metadata,"native_flavours":flavours.copy(),"bottom_active":False,"native_LHAPDF_ID":263400,
          "finite_pdf_points":[{"x":x,"Q_GeV":q,"xfxQ":{str(flavour):1. for flavour in flavours}}
                               for x,q in ((.0001,10.),(.01,91.1876),(.1,1000.),(.5,100.))],
          "finite_xfx_values":36,"alpha_values":alpha,"nonfinite_errors":0,"interpolation_errors":0,
          "out_of_domain_guard_rejections":[{"native_xfxQ_called":False} for _ in range(5)],
          "raw_inputs_and_dependencies_before":dependencies,"raw_inputs_and_dependencies_after":copy.deepcopy(dependencies),
          "MG5_parser_executed":False,"matching_validated":False,"physical_component_validated":False,
          "installed_directory_writes":False,"alpha_reference_diagnostic":diagnostic,
          "new_ME_calls":0,"new_integrals":0,"new_hard_events":0,"new_Pythia_events":0,"new_Delphes_events":0,
          "source_sha256":{}}
  files=[dict(role=role,advertised_bytes=row["bytes"],received_bytes=row["bytes"],**row)
         for role,row in (("info",info),("member",member))]
  acquisition={"fixture_scope":"SYNTHETIC_METHOD_ONLY_NO_DOWNLOAD","evidence_class":"PUBLIC_SOURCE_AUDIT",
               "status":"PASS_COMPLETE_SELECTED_MEMBER_ACQUISITION","candidate":c["PDF_candidate"],"member":0,
               "maximum_selected_distributions":1,"aggregate_body_bytes":sum(row["bytes"] for row in files),
               "files":files,"TLS_certificate_verification":True,"unknown_redirects_allowed":False,
               "installed_path_writes":False,"physical_generation":False}
  return native,acquisition
 def test_current_source_contract_remains_inactive(self):
  self.assertTrue(policy.validate_contract(self.contract))
 def test_zero_member_is_known_identity_false_is_not_zero(self):
  self.assertEqual(self.contract["PDF_member"],0)
  c=copy.deepcopy(self.contract);c["PDF_member"]=False
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_every_production_counter_strictly_integer_zero(self):
  for key in policy.COUNTERS:
   for value in (None,False,1,-1):
    c=copy.deepcopy(self.contract);c[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):policy.validate_contract(c)
 def test_no_dispatch_or_approval_override(self):
  for key,value in (("dispatcher","MG5"),("approval_override_flag","--approved"),("physical_authorization",True),("MG5_PARSER_EXECUTED",True)):
   c=copy.deepcopy(self.contract);c[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):policy.validate_contract(c)
 def test_new_baseline_cannot_be_silently_approved(self):
  c=copy.deepcopy(self.contract);c["new_baseline_approved"]=True
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_semantic_equality_cannot_promote_old_raw_gate(self):
  c=copy.deepcopy(self.contract);c["old_phase11_raw_gate"]="PASS_SEMANTIC_ONLY"
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_missing_mandatory_unknown_setting_rejected(self):
  for key in self.contract["unresolved_settings"]:
   c=copy.deepcopy(self.contract);del c["unresolved_settings"][key]
   with self.subTest(key=key),self.assertRaises(ValueError):policy.validate_contract(c)
 def test_unknown_setting_cannot_be_zero_false_or_default(self):
  key=next(iter(self.contract["unresolved_settings"]))
  for value in (0,False,"default"):
   c=copy.deepcopy(self.contract);c["unresolved_settings"][key]["value"]=value
   with self.subTest(value=value),self.assertRaises(ValueError):policy.validate_contract(c)
 def test_reference_scale_not_inferred_as_physical_MZ(self):
  c=copy.deepcopy(self.contract);c["PDF_declared_alpha_reference"]["scale_GeV"]=91.1876
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_reference_value_not_inferred_from_set_name(self):
  c=copy.deepcopy(self.contract);c["PDF_declared_alpha_reference"]["value"]=.130
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_strict_diagnostic_false_cannot_be_erased(self):
  c=copy.deepcopy(self.contract);c["reference_field_vs_native_strict_diagnostic_pass"]=True
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_diagnostic_does_not_establish_physical_alpha_binding(self):
  c=copy.deepcopy(self.contract);c["PDF_ME_alpha_binding"]="VALIDATED"
  with self.assertRaises(ValueError):policy.validate_contract(c)
 def test_physical_gate_promotion_rejected(self):
  for key in policy.PHYSICS:
   c=copy.deepcopy(self.contract);c[key]="VALIDATED"
   with self.subTest(key=key),self.assertRaises(ValueError):policy.validate_contract(c)
 def test_complete_synthetic_runtime_profile(self):
  self.assertTrue(policy.validate_runtime(*self.runtime()))
 def test_stale_raw_hash_rejected_even_with_semantic_equality(self):
  snapshots,proposal,current=self.runtime();snapshots["semantic_equal"]=True
  snapshots["snapshots"][0]["raw_identity"]["sha256"]="0"*64
  with self.assertRaises(ValueError):policy.validate_runtime(snapshots,proposal,current)
 def test_wrong_process_count_duplicate_and_boolean_ids(self):
  for change in ("two","duplicate","boolean"):
   snapshots,proposal,current=self.runtime()
   if change=="two":snapshots["snapshots"].pop()
   elif change=="duplicate":snapshots["snapshots"][2]["pid"]=101
   else:snapshots["snapshots"][2]["pid"]=True
   with self.subTest(change=change),self.assertRaises(ValueError):policy.validate_runtime(snapshots,proposal,current)
 def test_each_snapshot_requires_actual_observation_role(self):
  snapshots,proposal,current=self.runtime();snapshots["snapshots"][1]["evidence_class"]="SYNTHETIC_METHOD_ONLY"
  with self.assertRaises(ValueError):policy.validate_runtime(snapshots,proposal,current)
 def test_runtime_aggregate_counters_cannot_hide_nonzero_or_unknown(self):
  for key in ('new_ME_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events'):
   for kind,value in (('missing',None),('boolean',False),('nonzero',1)):
    snapshots,proposal,current=self.runtime()
    if kind=='missing':del snapshots[key]
    else:snapshots[key]=value
    with self.subTest(key=key,kind=kind),self.assertRaisesRegex(ValueError,'AGGREGATE_PRODUCTION_COUNTER'):policy.validate_runtime(snapshots,proposal,current)
 def test_each_runtime_row_counter_is_mandatory_integer_zero(self):
  for key in ('new_ME_calls','new_integrals','new_hard_events','new_pythia_events','new_delphes_events'):
   for kind,value in (('missing',None),('boolean',False),('nonzero',1)):
    snapshots,proposal,current=self.runtime()
    if kind=='missing':del snapshots['snapshots'][1][key]
    else:snapshots['snapshots'][1][key]=value
    with self.subTest(key=key,kind=kind),self.assertRaisesRegex(ValueError,'RUNTIME_PRODUCTION_COUNTER'):policy.validate_runtime(snapshots,proposal,current)
 def test_synthetic_aggregate_cannot_impersonate_observation(self):
  snapshots,proposal,current=self.runtime();snapshots["evidence_class"]="SYNTHETIC_METHOD_ONLY"
  with self.assertRaises(ValueError):policy.validate_runtime(snapshots,proposal,current)
 def test_cold_cache_claim_or_installed_write_rejected(self):
  for key in ("cold_cache_independence_claimed","installed_file_write_performed"):
   snapshots,proposal,current=self.runtime();snapshots["snapshots"][0][key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):policy.validate_runtime(snapshots,proposal,current)
 def test_complete_synthetic_native_profile_with_false_diagnostic(self):
  native,acquisition=self.native();self.assertFalse(native["alpha_reference_diagnostic"]["within_strict_diagnostic_tolerance"])
  self.assertTrue(policy.validate_pdf(native,acquisition))
 def test_missing_actual_member_is_not_a_metadata_pass(self):
  with tempfile.TemporaryDirectory() as directory:
   missing=Path(directory)/"set_0000.dat"
   with self.assertRaisesRegex(ValueError,"MISSING"):policy.raw_identity(missing)
 def test_wrong_native_or_metadata_flavour_scope_rejected(self):
  for where in ("native","metadata"):
   native,acquisition=self.native()
   if where=="native":native["native_flavours"] += [-5,5]
   else:native["metadata"]["flavours"] += [-5,5];native["metadata"]["PDF_maximum_flavours"]=5
   with self.subTest(where=where),self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_missing_scientific_reference_metadata_rejected(self):
  native,acquisition=self.native();del native["metadata"]["alpha_reference"]
  with self.assertRaises((ValueError,KeyError)):policy.validate_pdf(native,acquisition)
 def test_download_partial_or_missing_pair_rejected(self):
  for kind in ("partial","missing"):
   native,acquisition=self.native()
   if kind=="partial":acquisition["files"][1]["received_bytes"]-=1
   else:acquisition["files"].pop()
   with self.subTest(kind=kind),self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_pair_sha_mismatch_rejected(self):
  native,acquisition=self.native();acquisition["files"][1]["sha256"]="0"*64
  with self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_nonfinite_native_value_cannot_hide_behind_zero_errors(self):
  for where in ("alpha","pdf"):
   native,acquisition=self.native()
   if where=="alpha":native["alpha_values"][0]["alpha_s"]=float("nan")
   else:native["finite_pdf_points"][0]["xfxQ"]["21"]=float("inf")
   with self.subTest(where=where),self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_domain_guard_cannot_call_native(self):
  native,acquisition=self.native();native["out_of_domain_guard_rejections"][0]["native_xfxQ_called"]=True
  with self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_native_counters_and_physical_claims_rejected(self):
  for key,value in (("new_ME_calls",False),("new_integrals",1),("MG5_parser_executed",True),("installed_directory_writes",True)):
   native,acquisition=self.native();native[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_native_reference_diagnostic_not_official_accuracy(self):
  native,acquisition=self.native();native["alpha_reference_diagnostic"]["comparison_role"]="OFFICIAL_ACCURACY_PASS"
  with self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_stale_native_source_whitespace_hash_is_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/"reader_fixture.txt";path.write_bytes(b"known = 1\n")
   native={"raw_inputs_and_dependencies_after":{},"source_sha256":{str(path):policy.raw_identity(path)["sha256"]}}
   path.write_bytes(b"known = 1 \n")
   with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED"):policy.recheck_native_inputs(native)
 def test_unknown_native_alpha_type_not_silently_accepted(self):
  native,acquisition=self.native();native["metadata"]["alpha_type"]="analytic"
  with self.assertRaises(ValueError):policy.validate_pdf(native,acquisition)
 def test_inactive_cards_cannot_execute_commands(self):
  self.assertTrue(policy.validate_inactive("# INACTIVE\n# generate p4 p4 > b b~ a a\n"))
  with self.assertRaises(ValueError):policy.validate_inactive("# INACTIVE\nlaunch\n")
if __name__=="__main__":unittest.main()
