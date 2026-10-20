import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('phase13f_publication',ROOT/'analysis/phase13f/source/publication.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Publication(unittest.TestCase):
 def test_source_allowed(self):p.payload('analysis/phase13f/source/a.py',b'print(1)\n',{'analysis/phase13f/source/a.py'})
 def test_foreign_old_sources_rejected(self):
  for name in ('analysis/phase13/source/parser_contract.py','simulation/a.py','reports/phase13_final_report.md','../escape.py'):
   with self.subTest(name=name),self.assertRaises(ValueError):p.payload(name,b'X',{name})
 def test_binary_and_figure_payloads(self):
  for suffix,raw in (('.png',b'PNG'),('.pdf',b'PDF'),('.json',b'\x7fELF'),('.dat',b'GRID'),('.txt',b'%PDF-FAKE')):
   name='analysis/phase13f/evidence/a'+suffix
   with self.subTest(suffix=suffix),self.assertRaises(ValueError):p.payload(name,raw,{name})
 def test_private_config_body_rejected(self):
  name='analysis/phase13f/evidence/disguised.txt'
  with self.assertRaises(ValueError):p.payload(name,b'fortran_compiler = A\ncpp_compiler = B\nauto_update = C\nmg5_path = D\nlhapdf = E\n',{name})
 def test_event_and_raw_json_rejected(self):
  for raw in (b'<LesHouchesEvents version="3">',b'{"raw_configuration_bytes":"secret"}'):
   name='analysis/phase13f/evidence/a.json'
   with self.subTest(raw=raw),self.assertRaises(ValueError):p.payload(name,raw,{name})
 def test_unlisted_rejected(self):
  with self.assertRaises(ValueError):p.payload('analysis/phase13f/source/a.py',b'A',set())
 def test_only_exact_workflow_allowed(self):
  self.assertTrue(p.allowed('.github/workflows/phase13f-resource-closure.yml'));self.assertFalse(p.allowed('.github/workflows/other.yml'))
