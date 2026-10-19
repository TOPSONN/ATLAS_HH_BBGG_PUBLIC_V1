"""SYNTHETIC_METHOD_TEST: publication payload and complete-manifest negatives.

No genuine Git operation, native analysis, generator or network request occurs.
Virtual repository fixtures contain only bounded UTF-8 source/evidence stubs.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_publication as v

class PublicationPayloadTests(unittest.TestCase):
    def payload(self,name,data=b'// harmless source\n',covered=True):
        return v.validate_payload(name,data,{name} if covered else set())
    def test_positive_utf8_source(self):
        self.payload('analysis/phase9/apps/synthetic.cxx','// 繁體中文 source-only fixture\n'.encode())
        self.payload('reports/phase9_synthetic.md','# 無物理推論\n'.encode())
    def test_unlisted_source_and_csv_rejected(self):
        for name in ('analysis/phase9/apps/unlisted.cxx','analysis/phase9/evidence/unlisted.csv'):
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'UNLISTED_OR_DISALLOWED_PAYLOAD'):
                self.payload(name,covered=False)
    def test_two_mib_csv_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNBOUNDED_PAYLOAD'):
            self.payload('analysis/phase9/evidence/huge.csv',b'x'*(2*1024**2))
    def test_pdf_extension_rejected_even_plain_text(self):
        with self.assertRaisesRegex(ValueError,'FORBIDDEN_PAYLOAD_TYPE'):
            self.payload('analysis/phase9/evidence/unapproved.PDF',b'plain text')
    def test_png_extension_rejected_even_plain_text(self):
        with self.assertRaisesRegex(ValueError,'FORBIDDEN_PAYLOAD_TYPE'):
            self.payload('analysis/phase9/evidence/unapproved.png',b'plain text')
    def test_native_hepmc3_extensions_rejected(self):
        for suffix in ('.hepmc3','.hepmc3.gz'):
            with self.subTest(suffix=suffix),self.assertRaisesRegex(ValueError,'FORBIDDEN_PAYLOAD_TYPE'):
                self.payload('analysis/phase9/evidence/raw'+suffix,b'HepMC::Version 3.0\n')
    def test_event_jsonl_rejected(self):
        with self.assertRaisesRegex(ValueError,'FORBIDDEN_PAYLOAD_TYPE'):
            self.payload('analysis/phase9/evidence/raw.jsonl',b'{"event":1}\n')
    def test_binary_or_figure_magic_under_csv_rejected(self):
        for raw in (b'%PDF-1.7\n',b'\x89PNG\r\n',b'root\0\0',b'\x7fELF\0',b'MZ\0\0'):
            with self.subTest(magic=raw),self.assertRaisesRegex(ValueError,'BINARY_OR_FIGURE_MAGIC'):
                self.payload('analysis/phase9/evidence/disguised.csv',raw)
    def test_non_utf8_payload_rejected(self):
        with self.assertRaises(UnicodeDecodeError):
            self.payload('analysis/phase9/evidence/non_utf8.csv',b'\xff\xfe')
    def test_unknown_or_outside_scope_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_PAYLOAD_TYPE'):
            self.payload('analysis/phase9/evidence/raw.bin',b'data')
        with self.assertRaisesRegex(ValueError,'UNLISTED_OR_DISALLOWED_PAYLOAD'):
            self.payload('reference_samples/unreviewed.csv',b'a,b\n')
    def virtual_unlisted(self,location):
        with tempfile.TemporaryDirectory(prefix='phase9_publication_synthetic_') as td:
            repo=Path(td)
            names={'analysis/phase9/apps/stub.cxx':b'// synthetic method\n',
                   'analysis/phase9/evidence/stub.json':b'{"evidence_class":"SYNTHETIC_METHOD_TEST"}\n'}
            for name,data in names.items():
                p=repo/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            rows=[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in names.items()]
            meta=repo/'metadata';meta.mkdir()
            (meta/'phase9_source_manifest.json').write_text(json.dumps({'base_revision':v.BASE,'source_files':[rows[0]],'published_evidence':[rows[1]]}))
            gates={'physical_total_background':'BLOCKED','physical_significance':'NOT_EVALUATED','physical_CLs':'NOT_EVALUATED','physical_kappa_interval':'NOT_EVALUATED','figure_publication_authorized':False}
            gates.update({k:0 for k in ('new_ME_calls','new_integrals','new_hard_events','new_Pythia_events','new_Delphes_events')})
            (meta/'phase9_quality_gates.json').write_text(json.dumps(gates))
            leaked='analysis/phase9/evidence/unlisted.csv';(repo/leaked).write_text('a,b\n1,2\n')
            def fake_git(command,**kwargs):
                args=command[3:]
                if location=='staged' and args==['diff','--cached','--name-only']:return leaked+'\n'
                if location=='untracked' and args==['ls-files','--others','--exclude-standard']:return leaked+'\n'
                return ''
            with patch.object(v.subprocess,'check_output',side_effect=fake_git):
                with self.assertRaisesRegex(ValueError,'UNLISTED_OR_DISALLOWED_PAYLOAD'):
                    v.validate(repo)
    def test_staged_unlisted_csv_cannot_bypass_manifest(self):
        self.virtual_unlisted('staged')
    def test_untracked_unlisted_csv_cannot_bypass_manifest(self):
        self.virtual_unlisted('untracked')

if __name__=='__main__':unittest.main()