import importlib.util,json,math,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
spec=importlib.util.spec_from_file_location('interface',Path(__file__).resolve().parents[1]/'source/pdf_interface.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FakePDF:
 def __init__(self):self.calls=0
 def inRangeX(self,x):return True
 def inRangeQ(self,q):return True
 def xfxQ(self,pdg,x,q):self.calls+=1;return 1.
class Interface(unittest.TestCase):
 def setUp(self):self.domain={'xmin':1e-6,'xmax':1.,'Qmin_GeV':1.,'Qmax_GeV':1e5}
 def test_inside(self):p=FakePDF();self.assertEqual(m.guarded_xfx(p,21,.1,100.,self.domain),1.);self.assertEqual(p.calls,1)
 def test_outside_rejected_without_native_calls(self):
  p=FakePDF()
  for x,q in [(0.,10.),(1.1,10.),(.1,.5),(.1,2e5),(float('nan'),10.)]:
   with self.subTest(x=x,q=q),self.assertRaises(ValueError):m.guarded_xfx(p,21,x,q,self.domain)
  self.assertEqual(p.calls,0)
 def test_no_nonfinite(self):
  p=FakePDF();p.xfxQ=lambda *a:float('nan')
  with self.assertRaises(ValueError):m.guarded_xfx(p,21,.1,100.,self.domain)
 def test_native_range_disagreement(self):
  p=FakePDF();p.inRangeX=lambda x:False
  with self.assertRaises(ValueError):m.guarded_xfx(p,21,.1,100.,self.domain)
 def test_documented_points_only(self):
  c=json.loads((Path(__file__).resolve().parents[1]/'config/readback_points.json').read_text());self.assertTrue(m.validate_points(c));c['finite_xQ_points'].append([.1,13.])
  with self.assertRaises(ValueError):m.validate_points(c)
 def test_no_physical_authority(self):
  c=json.loads((Path(__file__).resolve().parents[1]/'config/readback_points.json').read_text());c['physical_generation_authorized']=True
  with self.assertRaises(ValueError):m.validate_points(c)

class ReferenceTolerance(unittest.TestCase):
 def test_unreviewed_or_nonfinite_tolerance_rejected(self):
  for val in (float('inf'),float('nan'),0.,.1,True):
   c=json.loads((Path(__file__).resolve().parents[1]/'config/readback_points.json').read_text());c['alpha_reference_relative_tolerance']=val
   with self.subTest(val=val),self.assertRaises(ValueError):m.validate_points(c)

class ReferenceInterpretation(unittest.TestCase):
 def test_interpolation_tolerance_not_promoted_to_publisher_accuracy(self):
  c=json.loads((Path(__file__).resolve().parents[1]/'config/readback_points.json').read_text());c['alpha_reference_comparison_role']='OFFICIAL_ACCURACY'
  with self.assertRaises(ValueError):m.validate_points(c)

class ReadbackOutputGuards(unittest.TestCase):
 def test_installed_or_other_root_cannot_be_payload(self):
  for path in ('/home/btu/opt/mg5amcnlo','/home/btu/miniforge3/envs/atlas-hh-root/share/LHAPDF','/tmp'):
   with self.subTest(path=path),self.assertRaises(ValueError):m.validate_readback_paths(Path(path),Path('/tmp/should_not_create'))
 def test_unknown_output_directory_rejected(self):
  with self.assertRaises(ValueError):m.validate_readback_paths(Path('/home/btu/simulations/hh_phase12/run_01/public_pdf_01'),Path('/tmp/should_not_create'))
