"""Synthetic bounded MC driver contracts; generator weights are never yields."""
import csv,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path

driver=Path(sys.argv.pop(1));fixtures=Path(sys.argv.pop(1));config=Path(sys.argv.pop(1))
marker=fixtures/'current_fixture_path.txt'
fixture=Path(marker.read_text().strip())
def csv_rows(path):return list(csv.DictReader(io.StringIO(path.read_text())))

class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)

    def run_driver(self,mode=16,dsid=600001,start=0,end=3,scale='1',status='PROVISIONAL',output=None,input_path=None,extra=()):
        output=output or self.directory/'result'
        result=subprocess.run([str(driver),str(input_path or fixture/(str(mode)+'.root')),str(output),str(dsid),str(start),str(end),str(scale),status,str(config),*extra],text=True,capture_output=True)
        return result,output

    def test_raw_counts_ignore_generator_weights_and_sf(self):
        result,out=self.run_driver();self.assertEqual(result.returncode,0,result.stderr)
        summary=json.loads((out/'summary.json').read_text());weights=json.loads((out/'weight_diagnostics.json').read_text())
        self.assertEqual(summary['entries_read'],3);self.assertEqual(summary['C9_selected'],3)
        self.assertFalse(summary['normalization_applied']);self.assertFalse(summary['scale_factors_applied'])
        self.assertEqual(summary['unit_status'],'PROVISIONAL');self.assertEqual(summary['truth_matching'],'PROVISIONAL_SAME_EVENT_GEOMETRIC_ONLY')
        self.assertEqual(summary['mass_closure_status'],'PASS');self.assertEqual(summary['mass_closure_pairs'],6)
        self.assertEqual(summary['mass_closure_failures'],0)
        self.assertEqual((weights['positive'],weights['negative'],weights['zero']),(1,1,1))
        self.assertEqual((weights['sumw'],weights['sumw2']),(1,5))
        rows=csv_rows(out/'events.csv');self.assertEqual([float(row['mc_weight']) for row in rows],[-1,2,0])
        self.assertEqual(int(rows[0]['event']),9007199254740993)
        self.assertEqual([int(row['events_after']) for row in csv_rows(out/'cutflow.csv')],[3]*10)
        import ROOT
        with ROOT.TFile.Open(str(out/'histograms.root'),'READ') as root:
            self.assertEqual(root.Get('mc_m_gg_C9').GetEntries(),3)
            self.assertEqual(root.Get('mc_photon_pt_C9').GetEntries(),6)
            self.assertEqual(root.Get('mc_jet_pt_C9').GetEntries(),6)
        self.assertFalse(list(out.glob('*.pdf')));self.assertFalse(list(out.glob('*.png')))
        matching=csv_rows(out/'matching_threshold_summary.csv');self.assertEqual(len(matching),12)
        self.assertTrue(all(int(row['truth_missing_events'])==3 and int(row['eligible_reco'])==0 and row['geometric_reco_match_fraction']=='' and row['geometric_truth_match_fraction']=='' for row in matching))
        self.assertEqual(csv_rows(out/'matching_assignments.csv'),[])

    def test_same_event_matching_indices_and_separate_scopes(self):
        result,out=self.run_driver(mode=19);self.assertEqual(result.returncode,0,result.stderr)
        matching=csv_rows(out/'matching_threshold_summary.csv');self.assertEqual(len(matching),12)
        for row in matching:
            self.assertEqual((int(row['events']),int(row['eligible_reco']),int(row['eligible_truth']),int(row['matched_pairs'])),(3,6,6,6))
            self.assertEqual((float(row['geometric_reco_match_fraction']),float(row['geometric_truth_match_fraction'])),(1,1))
            self.assertEqual((int(row['unmatched_reco']),int(row['unmatched_truth'])),(0,0))
            self.assertIn('NOT_ORIGIN_PURITY',row['classification'])
        assignments=csv_rows(out/'matching_assignments.csv');self.assertEqual(len(assignments),72)
        self.assertEqual({row['scope'] for row in assignments},{'ALL_VALID','C9'})
        self.assertTrue(all(int(row['event'])==9007199254740993+int(row['entry']) and row['reco_index']==row['truth_index'] and float(row['delta_r'])==0 for row in assignments))
        objects=csv_rows(out/'truth_objects.csv');self.assertEqual(len(objects),12)
        self.assertTrue(all(row['raw_energy']=='' and row['energy_available']=='0' for row in objects))

    def test_signed_truth_mass_and_negative_sf_are_preserved_unapplied(self):
        result,out=self.run_driver(mode=25);self.assertEqual(result.returncode,0,result.stderr)
        summary=json.loads((out/'summary.json').read_text())
        self.assertEqual(summary['negative_truth_jet_mass_values'],3);self.assertAlmostEqual(summary['minimum_truth_jet_mass'],-.0245,places=6)
        self.assertEqual(summary['negative_btag_scale_factors'],3);self.assertEqual(summary['minimum_btag_scale_factor'],-1)
        self.assertEqual(summary['C9_selected'],3);self.assertFalse(summary['truth_energy_inferred'])
        jets=[row for row in csv_rows(out/'truth_objects.csv') if row['object_group']=='jet']
        self.assertEqual(len(jets),6);self.assertTrue(all(float(row['raw_mass'])<0 for row in jets if row['index']=='0'))
        self.assertTrue(all(row['raw_energy']=='' for row in jets))
        self.assertTrue(all(row['usage']=='NOT_APPLIED' for row in csv_rows(out/'normalization_sf_diagnostics.csv')))

    def test_exact_phase3_cut_configuration(self):
        altered=self.directory/'strict.ini';altered.write_text(config.read_text().replace('photon_leading_pt_min_gev=35','photon_leading_pt_min_gev=70'))
        result=subprocess.run([str(driver),str(fixture/'16.root'),str(self.directory/'strict'), '600001','0','3','1','PROVISIONAL',str(altered)],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        counts=[int(row['events_after']) for row in csv_rows(self.directory/'strict'/'cutflow.csv')]
        self.assertEqual(counts[:3],[3,3,3]);self.assertEqual(counts[3:],[0]*7)

    def test_duplicate_identity_block(self):
        result,out=self.run_driver(mode=17);self.assertNotEqual(result.returncode,0);self.assertIn('Duplicate MC',result.stderr)
        self.assertFalse((out/'summary.json').exists())

    def test_wrong_dsid_block(self):
        result,out=self.run_driver(dsid=600002);self.assertNotEqual(result.returncode,0);self.assertIn('DSID',result.stderr)
        self.assertFalse((out/'summary.json').exists())

    def test_ranges_are_not_silently_extended_or_truncated(self):
        for start,end in [(-1,2),(0,0),(0,4),(0,10001)]:
            with self.subTest(start=start,end=end):
                result,out=self.run_driver(start=start,end=end,output=self.directory/f'out_{start}_{end}')
                self.assertNotEqual(result.returncode,0);self.assertFalse(out.exists())

    def test_input_and_numeric_guards(self):
        for arguments in [{'input_path':'root://invalid/input.root'},{'scale':'nan'},{'scale':'0'},{'status':'VERIFIED'},{'dsid':0},{'dsid':2**32},{'extra':('unexpected',)}]:
            with self.subTest(arguments=arguments):
                result,out=self.run_driver(**arguments)
                self.assertNotEqual(result.returncode,0);self.assertFalse(out.exists())

    def test_existing_output_preserved(self):
        directory=self.directory/'occupied';directory.mkdir();sentinel=directory/'sentinel.txt';sentinel.write_text('preserve')
        result,_=self.run_driver(output=directory);self.assertNotEqual(result.returncode,0);self.assertEqual(sentinel.read_text(),'preserve')

    def test_double_weight_is_not_narrowed(self):
        result,out=self.run_driver(mode=1);self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(all(float(row['mc_weight'])==-2.5 for row in csv_rows(out/'events.csv')))
        self.assertEqual(json.loads((out/'weight_diagnostics.json').read_text())['sumw'],-7.5)

if __name__=='__main__':unittest.main()
