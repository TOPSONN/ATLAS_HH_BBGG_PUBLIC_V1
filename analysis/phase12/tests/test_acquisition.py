import importlib.util,json,unittest,copy,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('acquisition',Path(__file__).resolve().parents[1]/'source/pdf_acquisition.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Acquisition(unittest.TestCase):
 def fixture(self):return json.loads((Path(__file__).resolve().parents[1]/'config/acquisition_contract.json').read_text())
 def test_current_contract(self):self.assertTrue(m.validate_contract(self.fixture()))
 def test_wrong_or_installed_destinations(self):
  for dest in ('/home/btu/opt/mg5amcnlo','/home/btu/miniforge3/envs/atlas-hh-root/share/LHAPDF','/tmp'):
   c=self.fixture();c['allowed_output_parent']=dest
   with self.subTest(dest=dest),self.assertRaises(ValueError):m.validate_contract(c)
 def test_one_distribution_only(self):
  c=self.fixture();c['candidate']='other'
  with self.assertRaises(ValueError):m.validate_contract(c)
 def test_no_unreviewed_execution(self):
  for key in ('install_into_existing_directories','MG5_import_or_execution','physical_authorization'):
   c=self.fixture();c[key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):m.validate_contract(c)
 def test_terms_required(self):
  c=self.fixture();c['terms_review']['checked']=False
  with self.assertRaises(ValueError):m.validate_contract(c)
 def test_sizes_and_encodings(self):
  for h in ({},{'Content-Length':'x'},{'Content-Length':'0'},{'Content-Length':'83886081'},{'Content-Length':'7','Content-Encoding':'gzip'}):
   with self.subTest(h=h),self.assertRaises(ValueError):m.advertised_length(h,83886080)
  self.assertEqual(m.advertised_length({'Content-Length':'683592'},83886080),683592)
 def test_broken_download(self):
  with self.assertRaises(ValueError):m.exact_complete(5,6)
 def test_unknown_redirect(self):
  with self.assertRaises(ValueError):m.NoRedirect().redirect_request(None,None,302,'',{},'https://mirror.invalid/x')

 def test_real_temporary_parent_is_accepted_read_only(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);before=list(p.iterdir());self.assertEqual(m.verify_output_parent(p),p);self.assertEqual(list(p.iterdir()),before)
 def test_symlink_parent_cannot_redirect_to_installed_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);installed=p/'installed_fixture';installed.mkdir();link=p/'allowed_parent';link.symlink_to(installed,target_is_directory=True)
   with self.assertRaisesRegex(ValueError,'SYMLINK_OUTPUT_PARENT_FORBIDDEN'):m.verify_output_parent(link)
   self.assertEqual(list(installed.iterdir()),[])
 def test_symlink_ancestor_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);real=p/'real';real.mkdir();(real/'child').mkdir();link=p/'alias';link.symlink_to(real,target_is_directory=True)
   with self.assertRaisesRegex(ValueError,'SYMLINK_OUTPUT_PARENT_FORBIDDEN'):m.verify_output_parent(link/'child')
 def test_missing_parent_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(ValueError,'OUTPUT_PARENT_MISSING_OR_NOT_DIRECTORY'):m.verify_output_parent(Path(td)/'absent')
 def test_file_parent_is_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'file';p.write_bytes(b'original')
   with self.assertRaisesRegex(ValueError,'OUTPUT_PARENT_MISSING_OR_NOT_DIRECTORY'):m.verify_output_parent(p)
   self.assertEqual(p.read_bytes(),b'original')
 def test_relative_or_parent_escape_is_rejected(self):
  for p in ('relative','/tmp/../tmp'):
   with self.subTest(p=p),self.assertRaisesRegex(ValueError,'UNSAFE_OUTPUT_PARENT'):m.verify_output_parent(Path(p))
 def test_timeouts_are_reviewed_integers(self):
  for key in ('timeout_seconds','total_wall_seconds'):
   for value in (None,True,0,120.0,1000000):
    c=self.fixture();c[key]=value
    with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'FINITE_REVIEWED_TIMEOUTS'):m.validate_contract(c)
