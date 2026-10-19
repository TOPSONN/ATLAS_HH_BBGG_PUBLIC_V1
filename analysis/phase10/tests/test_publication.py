import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('phase10_pub',Path(__file__).resolve().parents[1]/'scripts/validate_publication.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Publication(unittest.TestCase):
 def test_source_payload(self):m.validate_payload('analysis/phase10/source/x.py',b'print(1)\n',{'analysis/phase10/source/x.py'})
 def test_no_unapproved_figures_even_intermediate(self):
  for name,raw in [('x.png',b'abc'),('x.pdf',b'abc'),('x.txt',b'%PDF-1'),('x.json',b'\x89PNGabc')]:
   p='analysis/phase10/evidence/'+name
   with self.subTest(p=p),self.assertRaises(ValueError):m.validate_payload(p,raw,{p})
 def test_no_binary_or_event_sample(self):
  for suffix in ['.root','.lhe.gz','.jsonl','.hepmc3','.exe']:
   p='analysis/phase10/evidence/x'+suffix
   with self.subTest(p=p),self.assertRaises(ValueError):m.validate_payload(p,b'abc',{p})
 def test_old_source_modification_forbidden(self):
  p='analysis/phase9/scripts/x.py'
  with self.assertRaises(ValueError):m.validate_payload(p,b'abc',{p})
 def test_path_escape(self):
  for p in ['../analysis/phase10/x.py','/analysis/phase10/x.py','analysis/phase10/../x.py','analysis/phase10/evil\\x.py']:
   with self.subTest(p=p):self.assertFalse(m.allowed(p))
 def test_unlisted_file(self):
  with self.assertRaises(ValueError):m.validate_payload('analysis/phase10/x.py',b'abc',set())
 def test_oversized_and_empty_rejected(self):
  p='analysis/phase10/evidence/x.txt'
  for raw in [b'',b'a'*(2*1024**2)]:
   with self.assertRaises(ValueError):m.validate_payload(p,raw,{p})
 def test_index_line_ending_normalization_rejected(self):
  with self.assertRaises(ValueError):m.ensure_exact_bytes(b'a\nb\n',b'a\r\nb\r\n','x.csv')
 def test_index_exact(self):m.ensure_exact_bytes(b'a\r\n',b'a\r\n','x.csv')
if __name__=='__main__':unittest.main()
