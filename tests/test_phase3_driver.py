import csv,json,subprocess,sys,tempfile,unittest
from pathlib import Path
exe=Path(sys.argv.pop(1)); config=Path(sys.argv.pop(1))
fields='entry,run,event,valid,photon_n,jet_n,photon1_pt,photon2_pt,photon1_eta,photon2_eta,jet1_pt,jet2_pt,jet1_eta,jet2_eta,m_gg,m_jj,deltaR_gg,deltaR_jj,deltaEta_gg,deltaPhi_gg,deltaEta_jj,deltaPhi_jj,p1_tight_id,p2_tight_id,p1_tight_iso,p2_tight_iso,roundoff_objects,issue'.split(',')
class SelectionDriverTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.dir=Path(self.temp.name)
        self.input=self.dir/'synthetic.csv';self.output=self.dir/'selection'
        base={k:0 for k in fields};base.update(valid=1,photon_n=2,jet_n=2,photon1_pt=40,photon2_pt=30,
          photon1_eta=0,photon2_eta=1,jet1_pt=40,jet2_pt=30,jet1_eta=0,jet2_eta=1,m_gg=125,m_jj=100,
          p1_tight_id=1,p2_tight_id=1,p1_tight_iso=1,p2_tight_iso=1,issue='')
        self.rows=[dict(base,entry=i,event=9007199254740993+i) for i in range(12)]
        self.rows[1]['photon1_pt']=35;self.rows[2]['photon2_pt']=25;self.rows[3]['photon1_eta']=1.4
        self.rows[4]['m_gg']=105;self.rows[5]['m_gg']=160;self.rows[6]['jet2_pt']=25;self.rows[7]['jet2_eta']=2.5
        self.rows[8]['valid']=0;self.rows[9]['photon1_pt']='nan'
        self.rows[10].update(jet_n=0,jet1_pt='',jet2_pt='',jet1_eta='',jet2_eta='',m_jj='')
        self.rows[11].update(jet1_pt=30,jet2_pt=40)
    def run_app(self,status='PROVISIONAL',output=None,selection_config=None):
        with self.input.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(self.rows)
        return subprocess.run([str(exe),str(self.input),str(selection_config or config),str(output or self.output),status],capture_output=True,text=True)
    def test_threshold_cutflow_and_invalid_events(self):
        r=self.run_app();self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        with (self.output/'cutflow.csv').open() as f: rows=list(csv.DictReader(f))
        self.assertEqual([int(r['events_after']) for r in rows],[12,9,9,8,7,6,6,5,4,3])
        for r in rows: self.assertEqual(int(r['events_before'])-int(r['events_after']),int(r['rejected_events']))
        self.assertEqual(len(list(self.output.glob('*.png'))),4)
        self.assertEqual(json.loads((self.output/'summary.json').read_text())['new_ROOT_entry_reads'],0)
        with (self.output/'histogram_inventory.csv').open() as f: hist={r['name']:r for r in csv.DictReader(f)}
        self.assertEqual(float(hist['m_gg_preselection']['filled_values']),3)
        self.assertEqual(float(hist['m_gg_preselection']['overflow']),0)
    def test_unknown_units(self):
        self.assertNotEqual(self.run_app(status='UNKNOWN').returncode,0);self.assertFalse(self.output.exists())
    def test_duplicate_entry_rejected(self):
        self.rows[3]['entry']=2;self.assertNotEqual(self.run_app().returncode,0)
    def test_reversed_order_rejected(self):
        self.rows.reverse();self.assertNotEqual(self.run_app().returncode,0)
    def test_reproducible_cutflow(self):
        self.assertEqual(self.run_app().returncode,0)
        other=self.dir/'repeat';self.assertEqual(self.run_app(output=other).returncode,0)
        self.assertEqual((self.output/'cutflow.csv').read_bytes(),(other/'cutflow.csv').read_bytes())
    def test_no_overwrite(self):
        self.output.mkdir();(self.output/'sentinel').write_text('preserve')
        self.assertNotEqual(self.run_app().returncode,0);self.assertEqual((self.output/'sentinel').read_text(),'preserve')
    def test_nonboolean_flag(self):
        self.rows[0]['p1_tight_id']=2;self.assertNotEqual(self.run_app().returncode,0)
    def test_malformed_number(self):
        self.rows[0]['photon1_pt']='not_numeric';self.assertNotEqual(self.run_app().returncode,0)
    def test_unconfigured_weight_forbidden(self):
        bad=self.dir/'bad.ini';bad.write_text(config.read_text()+'event_weight=2\n')
        self.assertNotEqual(self.run_app(selection_config=bad).returncode,0)
if __name__=='__main__':unittest.main()
