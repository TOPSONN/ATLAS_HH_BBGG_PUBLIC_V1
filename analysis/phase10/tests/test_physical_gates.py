import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from physical_gates import assemble,validate,STATUSES,COUNTERS,ROLES
class PhysicalPolicy(unittest.TestCase):
 def matrix(self):return assemble({k:{'evidence_class':ROLES[k],'sha256':'a'*64} for k in ('source_review','heavy_flavour','photon','sideband','precision','pilot')})
 def test_actual_blockers_survive_synthetic_pass(self):
  m=self.matrix();self.assertTrue(validate(m));self.assertEqual(m['PHOTON_FAKE_RATE'],'UNKNOWN');self.assertEqual(m['PHYSICAL_TOTAL_BACKGROUND'],'BLOCKED')
 def test_each_missing_or_promoted_gate_rejected(self):
  for k in STATUSES:
   for value in (None,'VALIDATED','PASS'):
    m=self.matrix();m[k]=value
    with self.subTest(k=k,value=value),self.assertRaises(ValueError):validate(m)
 def test_each_production_counter_rejected(self):
  for k in COUNTERS:
   m=self.matrix();m[k]=1
   with self.subTest(k=k),self.assertRaises(ValueError):validate(m)
 def test_false_is_not_integer_counter(self):
  m=self.matrix();m['NEW_ME_CALLS']=False
  with self.assertRaises(ValueError):validate(m)
 def test_unknown_nuisance_values_not_zero(self):
  m=self.matrix();m['physical_nuisances']['values']=[0.]
  with self.assertRaises(ValueError):validate(m)
 def test_unknown_nuisance_covariance_not_zero(self):
  m=self.matrix();m['physical_nuisances']['covariance']=[[0.]]
  with self.assertRaises(ValueError):validate(m)
 def test_physical_sum_forbidden(self):
  m=self.matrix();m['physical_background_sum_pb']=0.
  with self.assertRaises(ValueError):validate(m)
 def test_unknown_fake_is_not_zero(self):
  m=self.matrix();m['physical_fake_probability']=0.
  with self.assertRaises(ValueError):validate(m)
 def test_human_approval_not_fabricated(self):
  m=self.matrix();m['external_human_approval']=True
  with self.assertRaises(ValueError):validate(m)
 def test_synthetic_import_rejected(self):
  m=self.matrix();m['synthetic_used_in_physical_results']=True
  with self.assertRaises(ValueError):validate(m)
 def test_pilot_and_figures_forbidden(self):
  for k in ('PHYSICAL_PILOT_EXECUTED','FIGURE_PUBLICATION_AUTHORIZED'):
   m=self.matrix();m[k]=True
   with self.subTest(k=k),self.assertRaises(ValueError):validate(m)
 def test_missing_receipt_fails_closed(self):
  m=self.matrix();del m['evidence']['photon']
  with self.assertRaises(ValueError):validate(m)
 def test_synthetic_cannot_impersonate_actual_evidence(self):
  m=self.matrix();m['evidence']['photon']['evidence_class']='SYNTHETIC_METHOD_ONLY'
  with self.assertRaises(ValueError):validate(m)
 def test_digest_must_be_exact_sha256(self):
  for bad in ['a','A'*64,'g'*64]:
   m=self.matrix();m['evidence']['photon']['sha256']=bad
   with self.subTest(bad=bad),self.assertRaises(ValueError):validate(m)
if __name__=='__main__':unittest.main()
