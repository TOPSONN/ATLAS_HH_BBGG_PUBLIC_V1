import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('p11_pub',Path(__file__).resolve().parents[1]/'scripts/validate_publication.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Publication(unittest.TestCase):
 def test_source_allowed(self):m.payload('analysis/phase11/x.py',b'# source\n',{'analysis/phase11/x.py'})
 def test_no_pdf_png_even_in_intermediate(self):
  for name,raw in [('x.pdf',b'a'),('x.png',b'a'),('x.txt',b'%PDF-1'),('x.json',b'\x89PNGfoo')]:
   p='analysis/phase11/evidence/'+name
   with self.subTest(name=name),self.assertRaises(ValueError):m.payload(p,raw,{p})
 def test_no_binary_events(self):
  for suffix in ('.root','.lhe.gz','.hepmc3','.jsonl','.exe'):
   p='analysis/phase11/evidence/x'+suffix
   with self.subTest(suffix=suffix),self.assertRaises(ValueError):m.payload(p,b'abc',{p})
 def test_old_source_modifications_forbidden(self):
  for phase in (6,7,8,9,10):
   p=f'analysis/phase{phase}/x.py'
   with self.subTest(phase=phase),self.assertRaises(ValueError):m.payload(p,b'a',{p})
 def test_escape_unlisted_rejected(self):
  for p in ('../analysis/phase11/x.py','/analysis/phase11/x.py','analysis/phase11/../x.py','analysis/phase11/x\\y.py'):
   with self.subTest(p=p):self.assertFalse(m.allowed(p))
  with self.assertRaises(ValueError):m.payload('analysis/phase11/x.py',b'a',set())
 def test_crlf_exact_bytes_preserved(self):
  m.exact_bytes(b'x\r\n',b'x\r\n','x.csv')
  with self.assertRaises(ValueError):m.exact_bytes(b'x\n',b'x\r\n','x.csv')
 def test_empty_unbounded_rejected(self):
  p='analysis/phase11/evidence/x.txt'
  for raw in (b'',b'x'*(2*1024**2)):
   with self.assertRaises(ValueError):m.payload(p,raw,{p})
if __name__=='__main__':unittest.main()
