"""Corrupt or incomplete cached probes cannot establish numerical consistency."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_phase4_units import audit

class UnitProbe(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'probe.csv'
        self.rows=[{'entry':i,'collection':kind,'index':j,'count':2,'pt':40,'eta':0,'phi':3 if j else 0,'energy':40}
                   for i in range(10,100) for kind in ('photon','jet') for j in range(2)]
    def run_audit(self):
        with self.path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=self.rows[0].keys());w.writeheader();w.writerows(self.rows)
        return audit(self.path,343981)
    def test_consistent_remains_provisional(self):
        result=self.run_audit();self.assertEqual(result['numerical_consistency'],'PASS')
        self.assertEqual(result['unit_status'],'PROVISIONAL');self.assertEqual(result['exact_producer_association'],'UNKNOWN')
    def test_duplicate_or_missing_indices(self):
        self.rows[1]['index']=0
        with self.assertRaises(ValueError):self.run_audit()
        self.rows[1]['index']=1;self.rows.pop()
        with self.assertRaises(ValueError):self.run_audit()
    def test_unknown_collection(self):
        self.rows[0]['collection']='invented'
        with self.assertRaises(ValueError):self.run_audit()
    def test_wrong_range(self):
        self.rows[0]['entry']=0
        with self.assertRaises(ValueError):self.run_audit()
    def test_numeric_contradictions(self):
        for field,value in [('pt',-1),('phi',4),('energy',1),('eta','nan')]:
            previous=self.rows[0][field];self.rows[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.run_audit()
            self.rows[0][field]=previous
    def test_skim_threshold(self):
        self.rows[1]['pt']=24
        with self.assertRaises(ValueError):self.run_audit()

if __name__=='__main__':unittest.main()
