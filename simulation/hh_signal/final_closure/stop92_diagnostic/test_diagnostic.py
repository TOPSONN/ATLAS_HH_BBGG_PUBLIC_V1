"""Independent regression for the proposed overlay; never a physical job."""
import concurrent.futures,hashlib,json,os,tempfile,unittest
from pathlib import Path
from .overlay import candidate,restore,exact_point,diff,PREDICATES,ORIGINAL_SHA256
from .diagnostics import parse_record,MAX_RECORD_BYTES
from .methods import HERE,RUNTIME,execute

class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.original=(RUNTIME/'native_checks.f').read_text();self.proposed=candidate(self.original)
    def test_exact_overlay_projection_and_frozen_files(self):
        self.assertEqual(hashlib.sha256(self.original.encode()).hexdigest(),ORIGINAL_SHA256)
        self.assertEqual(restore(self.proposed),self.original)
        self.assertEqual((HERE/'native_checks_diagnostic.f').read_text(),self.proposed)
        self.assertEqual((HERE/'native_checks_diagnostic.patch').read_text(),diff(self.original,self.proposed))
        # Extraction must reach the subroutine END, not the first ENDIF.
        self.assertIn('points=points+1',exact_point(self.proposed))
        self.assertEqual(len(PREDICATES),5)
    def test_drift_and_weakened_predicates_rejected(self):
        for mutation in ['\n',self.original.replace('1d-10','1d-5'),self.original.replace('stop 92','continue')]:
            with self.assertRaises(ValueError):candidate(mutation)
        for mutation in [self.proposed.replace('1d-10','1d-5'),self.proposed.replace('stop 92','continue'),
                         self.proposed.replace('points=points+1','points=points+2'),self.proposed+'\n']:
            with self.assertRaises(ValueError):restore(mutation)
    def test_failure_only_exact_statements_flush_and_scalar_schema(self):
        for predicate,identifier,fields in PREDICATES:
            self.assertEqual(self.proposed.count(predicate+' then'),1)
            self.assertEqual(self.proposed.count('HI_FAILURE POINT92 '+identifier),1)
            self.assertNotIn('p(',','.join(v for _,v in fields))
        self.assertEqual(exact_point(self.proposed).count('flush(6)'),5)
        self.assertEqual(exact_point(self.proposed).count('stop 92'),5)
    def record(self,identifier=None,value='1.0000000000000000E+000'):
        _,name,fields=next(p for p in PREDICATES if identifier is None or p[1]==identifier)
        return 'HI_FAILURE POINT92 '+name+''.join(' '+key+'= '+value for key,_ in fields)
    def test_strict_parser_bounds_extra_fields_split_records(self):
        valid=self.record();self.assertLess(len(valid),MAX_RECORD_BYTES)
        for bad in [valid+'\n',valid+' p4= 1.0',valid.replace('q_GeV','unknown'),valid+' '*MAX_RECORD_BYTES,
                    valid.replace('POINT92_Q_OR_PDF','UNKNOWN'),valid.replace('1.0000000000000000E+000','********')]:
            with self.assertRaises(ValueError):parse_record(bad)
    def test_nonfinite_scalars_are_explicit_not_json_nan(self):
        record=self.record('POINT92_FACTORIZATION_SCALE','NaN')
        parsed=parse_record(record);encoded=json.dumps(parsed,allow_nan=False)
        self.assertIn('nonfinite',encoded)
        self.assertTrue(all(v['value'] is None for v in parsed['scalars'].values()))
    def test_parser_is_stateless_under_concurrent_receipt_readers(self):
        records=[self.record(p[1]) for p in PREDICATES]*8
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            actual=list(pool.map(parse_record,records))
        self.assertEqual(actual,list(map(parse_record,records)))
    def test_additive_metadata_scope_is_exact(self):
        from ..src.audit_payload import PREFIXES,compatibility,PATCHES
        from ...campaign.audit_payload import ALLOWED
        path='metadata/phase7i_stop92_diagnostic_status.json'
        self.assertIn(path,PREFIXES);self.assertIn(path,ALLOWED)
        self.assertFalse('metadata/phase7i_unrelated.json'.startswith(PREFIXES))
        target='simulation/hh_signal/campaign/audit_payload.py';old,new=PATCHES[target]
        before=old.encode();legacy=new.encode()
        tail=b"         'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml')\n"
        exact=b"         'reports/phase7_final_','metadata/phase7_final_','.github/workflows/hh_signal_final_closure.yml',\n         'metadata/phase7i_git_precheck_recovery.json',\n         'metadata/phase7i_stop92_diagnostic_status.json')\n"
        compatibility(target,before,legacy.replace(tail,exact))
        with self.assertRaises(ValueError):compatibility(target,before,legacy.replace(tail,exact.replace(b'stop92_diagnostic_status',b'unrelated')))

class NativeMethodTests(unittest.TestCase):
    def test_original_and_overlay_native_semantics_two_optimizations(self):
        for optimization in ['-O0','-O2']:
            with self.subTest(optimization=optimization),tempfile.TemporaryDirectory() as td:
                evidence=execute(Path(td)/'fresh',os.environ.get('FC','gfortran'),optimization)
                self.assertEqual(evidence['status'],'PASS_NONPHYSICAL_METHODS_ONLY')
                self.assertEqual(len(evidence['predicate_matrix']),24)
                self.assertEqual(len(evidence['failure_receipts']),6)
                self.assertEqual(evidence['actual_new_ME_calls'],0)
                ids={r['parsed']['identifier'] for r in evidence['predicate_matrix'] if r['parsed']}
                self.assertEqual(ids,{p[1] for p in PREDICATES})
                # Preserve and expose the inherited unchecked-q2fact NaN gap.
                self.assertEqual(evidence['predicate_matrix'][12]['original_exit'],0)
                self.assertEqual(evidence['predicate_matrix'][12]['diagnostic_exit'],0)

if __name__=='__main__':unittest.main()
