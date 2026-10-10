import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

script = Path(sys.argv.pop(1))
class UnitEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name); self.probe=self.path/'probe.csv'
        self.rows=[dict(entry=i,collection=k,index=j,count=2,pt=p,eta=0,phi=0 if j==0 else 3.14,energy=p if k=='photon' else p+10)
                   for i in range(10,100) for k in ['photon','jet'] for j,p in enumerate([40,30])]
    def execute(self):
        with self.probe.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(self.rows[0])); writer.writeheader(); writer.writerows(self.rows)
        return subprocess.run([sys.executable,'-B',str(script),str(self.probe),str(self.path/'evidence.csv'),str(self.path/'summary.json')],capture_output=True,text=True)
    def test_provisional_not_exact_production(self):
        r=self.execute(); self.assertEqual(r.returncode,0,r.stderr)
        summary=json.loads((self.path/'summary.json').read_text())
        self.assertEqual(summary['status'],'PROVISIONAL'); self.assertEqual(summary['producer_match'],'UNKNOWN')
        with (self.path/'evidence.csv').open() as f:
            evidence=list(csv.DictReader(f))
        self.assertEqual(len(evidence),8); self.assertTrue(all(r['classification']=='PROVISIONAL' for r in evidence))
        self.assertNotIn(b'\r', (self.path/'evidence.csv').read_bytes())
    def test_nonfinite(self):
        self.rows[0]['pt']='nan'; self.assertNotEqual(self.execute().returncode,0)
    def test_energy_contradiction(self):
        self.rows[0]['energy']=10; self.assertNotEqual(self.execute().returncode,0)
    def test_angular_contradiction(self):
        self.rows[0]['phi']=180; self.assertNotEqual(self.execute().returncode,0)
    def test_possible_mev_scale(self):
        for r in self.rows: r['pt']*=1000; r['energy']*=1000
        self.assertNotEqual(self.execute().returncode,0)
    def test_missing_entry(self):
        self.rows=[r for r in self.rows if r['entry']!=10]; self.assertNotEqual(self.execute().returncode,0)
    def test_no_overwrite(self):
        self.assertEqual(self.execute().returncode,0)
        original=(self.path/'evidence.csv').read_bytes()
        self.assertNotEqual(self.execute().returncode,0)
        self.assertEqual((self.path/'evidence.csv').read_bytes(),original)
if __name__=='__main__': unittest.main()
