"""Independent failures for the new-only hatched-step contract.

All mutations use temporary copies. The preserved original 32-case gate suite
continues to run separately and is not edited by this extension.
"""
import copy,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path

module_path=Path(sys.argv.pop(1));fixture_root=Path(sys.argv.pop(1))
spec=importlib.util.spec_from_file_location('hatched_gate',module_path)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
selected_directory=gate.fixture_directory(fixture_root,fixture_root/'current_fixture_path.txt')
fixtures=[path for path in selected_directory.rglob('*.plot.json')
          if (metadata:=json.loads(path.read_text())).get('plot_mode')=='HATCHED_STEP'
          and metadata.get('band_support') is not None and metadata.get('structural_zero_exclusions')]
if not fixtures:raise ValueError('A generated supported-range hatched fixture is required')
fixture=max(fixtures,key=lambda path:path.stat().st_mtime_ns)

class HatchedGateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/fixture.name
        self.base=Path(str(self.path).removesuffix('.plot.json'))
        source=Path(str(fixture).removesuffix('.plot.json'))
        for ext in ['.pdf','.png','.root','.plot.json','.caption.md']:
            shutil.copyfile(str(source)+ext,str(self.base)+ext)
        self.metadata=json.loads(self.path.read_text())

    def write_metadata(self):
        import ROOT
        self.path.write_text(json.dumps(self.metadata))
        Path(str(self.base)+'.caption.md').write_text(self.metadata['caption'])
        with gate.native_serialization_style(),ROOT.TFile.Open(str(self.base)+'.root','UPDATE') as root:
            ROOT.TNamed('atlas_plot_metadata',json.dumps(self.metadata)).Write('atlas_plot_metadata',ROOT.TObject.kOverwrite)
            ROOT.TNamed('atlas_plot_caption',self.metadata['caption']).Write('atlas_plot_caption',ROOT.TObject.kOverwrite)

    def native(self,name,edit):
        import ROOT
        with gate.native_serialization_style(),ROOT.TFile.Open(str(self.base)+'.root','UPDATE') as root:
            obj=root.Get(name);self.assertTrue(bool(obj));edit(obj)
            obj.Write(name,ROOT.TObject.kOverwrite)

    def rejected(self,pattern=None):
        context=self.assertRaisesRegex(ValueError,pattern) if pattern else self.assertRaises(ValueError)
        with context:gate.validate_one(self.path)

    def metadata_rejected(self,pattern):
        with self.assertRaisesRegex(ValueError,pattern):gate.validate_plot_mode(self.metadata)

    def test_complete_fixture_passes(self):
        result=gate.validate_one(self.path)
        self.assertEqual(result['plot_mode'],'HATCHED_STEP')
        self.assertEqual(result['hatched_numerics']['native_poisson_oracle'],'PASS')
        self.assertGreaterEqual(result['colored_diagonal_vector_paths'],4)

    def test_original_mode_cannot_masquerade(self):
        self.metadata.pop('plot_mode');self.metadata_rejected('cannot masquerade')

    def test_unknown_mode(self):
        self.metadata['plot_mode']='FILLED_MC';self.metadata_rejected('Unknown plot mode')

    def test_mc_is_not_count_uncertainty(self):
        self.metadata['sample_kind']='MC';self.metadata_rejected('cannot represent MC')

    def test_missing_mode_metadata(self):
        self.metadata.pop('band_object_name');self.metadata_rejected('Required hatched metadata')

    def test_wrong_native_name(self):
        self.metadata['band_object_name']='different_band';self.metadata_rejected('object names disagree')

    def test_confidence_level_not_invented(self):
        self.metadata['confidence_level']=.95;self.metadata_rejected('statistical model')

    def test_statistical_model_not_systematics(self):
        self.metadata['statistical_model']='MC systematic envelope';self.metadata_rejected('statistical model')

    def test_solid_fill_metadata_rejected(self):
        self.metadata['hatched_style']['band_fill_style']=1001;self.metadata_rejected('Wrong hatched style')

    def test_wrong_line_color(self):
        self.metadata['hatched_style']['line_color']=1;self.metadata_rejected('Wrong hatched style')

    def test_wrong_line_width(self):
        self.metadata['hatched_style']['line_width']=3;self.metadata_rejected('Wrong hatched style')

    def test_interpolated_band_option_rejected(self):
        self.metadata['hatched_style']['band_draw_option']='3 SAME';self.metadata_rejected('Wrong hatched style')

    def test_legend_no_mc_claim(self):
        self.metadata['hatched_style']['legend_labels'][1]='MC uncertainty';self.metadata_rejected('misstates statistical meaning')

    def test_wrong_data_period_rejected(self):
        self.metadata['sample_kind']='DATA';self.metadata['period']='2015 periodD'
        self.metadata['hatched_style']['legend_labels'][0]='Data (step histogram)'
        self.metadata['hatched_style']['visible_period']='2015 data';self.metadata_rejected('disagrees with provenance')

    def test_future_declared_data_period_permitted(self):
        # This exercises declared metadata, not fabricated future collision data.
        self.metadata['sample_kind']='DATA';self.metadata['period']='2016 periodA';self.metadata['energy_tev']=13
        self.metadata['hatched_style']['legend_labels'][0]='Data (step histogram)'
        self.metadata['hatched_style']['visible_period']='2016 periodA'
        self.assertEqual(gate.validate_plot_mode(self.metadata),'HATCHED_STEP')
        self.assertIn('2016 periodA',gate.compact_labels(self.metadata))

    def test_no_systematics_scope_required(self):
        self.metadata['caption']=self.metadata['caption'].replace('systematics','unvalidated additional scope')
        self.metadata_rejected('missing statistical scope')

    def test_legend_overlaps_annotation(self):
        self.metadata['hatched_style']['legend_box']=copy.deepcopy(self.metadata['hatched_style']['annotation_box'])
        self.metadata_rejected('overlaps annotation')

    def test_band_halfwidth_covers_full_bins(self):
        def change(band):band.SetPointEXhigh(0,band.GetErrorXhigh(0)/2)
        self.native(self.metadata['band_object_name'],change);self.rejected('rectangle coverage')

    def test_band_count_matches_source(self):
        def change(band):band.SetPoint(0,band.GetPointX(0),band.GetPointY(0)+1)
        self.native(self.metadata['band_object_name'],change);self.rejected('rectangle coverage')

    def test_band_lower_error_matches_source(self):
        def change(band):band.SetPointEYlow(0,band.GetErrorYlow(0)+.25)
        self.native(self.metadata['band_object_name'],change);self.rejected('rectangle coverage')

    def test_band_upper_error_matches_source(self):
        def change(band):band.SetPointEYhigh(0,band.GetErrorYhigh(0)+.25)
        self.native(self.metadata['band_object_name'],change);self.rejected('rectangle coverage')

    def test_band_x_position_matches_source(self):
        def change(band):band.SetPoint(0,band.GetPointX(0)+.25,band.GetPointY(0))
        self.native(self.metadata['band_object_name'],change);self.rejected('rectangle coverage')

    def test_original_interval_x_errors_stay_zero(self):
        self.native(self.metadata['source_intervals_object_name'],lambda graph:graph.SetPointEXlow(0,.5))
        self.rejected('Full native Poisson')

    def test_original_interval_errors_recomputed_independently(self):
        def change(graph):graph.SetPointEYhigh(0,graph.GetErrorYhigh(0)+.25)
        self.native(self.metadata['source_intervals_object_name'],change);self.rejected('Full native Poisson')

    def test_duplicate_band_bin_rejected(self):
        def change(band):band.SetPoint(1,band.GetPointX(0),band.GetPointY(1))
        self.native(self.metadata['band_object_name'],change);self.rejected('rectangle coverage')

    def test_missing_band_bin_rejected(self):
        self.native(self.metadata['band_object_name'],lambda band:band.RemovePoint(0));self.rejected('Missing or duplicate')

    def test_duplicate_eligible_mask_rejected(self):
        self.metadata['eligible_bin_indices'].append(self.metadata['eligible_bin_indices'][0])
        self.write_metadata();self.rejected('duplicate hatched eligible')

    def test_missing_eligible_mask_rejected(self):
        self.metadata['eligible_bin_indices'].pop();self.write_metadata();self.rejected('mask does not match')

    def test_invalid_mask_type_rejected(self):
        self.metadata['eligible_bin_indices'][0]=True;self.write_metadata();self.rejected('Invalid or duplicate')

    def test_excluded_nonzero_bin_cannot_be_hidden(self):
        index=self.metadata['structural_zero_exclusions'][0]
        self.native(self.metadata['source_object_name'],lambda hist:hist.SetBinContent(index,1));self.rejected('Excluded hatched bin contains events')

    def test_upper_boundary_bin_event_cannot_be_hidden(self):
        index=self.metadata['structural_zero_exclusions'][-1]
        self.native(self.metadata['source_object_name'],lambda hist:hist.SetBinContent(index,1));self.rejected('Excluded hatched bin contains events')

    def test_structural_zero_mask_is_exact_complement(self):
        self.metadata['structural_zero_exclusions'].pop();self.write_metadata();self.rejected('mask does not match')

    def test_support_requires_aligned_bin_edges(self):
        self.metadata['band_support']['low']+=.25;self.write_metadata();self.rejected('not aligned')

    def test_null_support_cannot_keep_partial_band(self):
        self.metadata['band_support']=None;self.write_metadata();self.rejected('mask does not match')

    def test_native_solid_band_rejected(self):
        self.native(self.metadata['band_object_name'],lambda band:band.SetFillStyle(1001));self.rejected('Native band')

    def test_native_wrong_band_color_rejected(self):
        self.native(self.metadata['band_object_name'],lambda band:band.SetFillColor(1));self.rejected('Native band')

    def test_native_wrong_step_style_rejected(self):
        self.native(self.metadata['source_object_name'],lambda hist:hist.SetLineWidth(3));self.rejected('Native hatched step style')

    def test_weighted_native_variances_rejected(self):
        index=self.metadata['eligible_bin_indices'][0]
        self.native(self.metadata['source_object_name'],lambda hist:hist.SetBinError(index,(hist.GetBinContent(index)+1)**.5))
        self.rejected('Weighted native histogram')

    def test_missing_full_original_intervals_rejected(self):
        import ROOT
        with ROOT.TFile.Open(str(self.base)+'.root','UPDATE') as root:root.Delete(self.metadata['source_intervals_object_name']+';*')
        self.rejected('Full native counting intervals absent')

    def test_negative_source_count_rejected(self):
        index=self.metadata['eligible_bin_indices'][0]
        self.native(self.metadata['source_object_name'],lambda hist:hist.SetBinContent(index,-1));self.rejected('nonnegative integer')

    def test_fractional_source_count_rejected(self):
        index=self.metadata['eligible_bin_indices'][0]
        self.native(self.metadata['source_object_name'],lambda hist:hist.SetBinContent(index,1.5));self.rejected('nonnegative integer')

    def test_eligible_zero_count_upper_interval_preserved(self):
        import ROOT
        with ROOT.TFile.Open(str(self.base)+'.root','READ') as root:
            hist=root.Get(self.metadata['source_object_name']);band=root.Get(self.metadata['band_object_name'])
            positions=[i for i,index in enumerate(self.metadata['eligible_bin_indices']) if hist.GetBinContent(index)==0]
            self.assertTrue(positions)
            for position in positions:self.assertGreater(band.GetErrorYhigh(position),0)
        self.assertEqual(gate.validate_one(self.path)['automated_status'],'PASS')

    def test_resource_only_hatches_are_not_visible_proof(self):
        # ROOT plain PDFs also define unused hatch resources. Their existence
        # must not pass a page-content diagonal-stroke test.
        import ROOT
        original=Path(__file__).resolve().parents[1]/'reports/figures/atlas_v2/phase2/m_gg.pdf'
        self.assertTrue(original.is_file(),'Preserved original PDF required by the project contract')
        color=ROOT.gROOT.GetColor(861)
        with self.assertRaisesRegex(ValueError,'diagonal vector hatch paths absent'):
            gate.pdf_hatch_paths(original,(color.GetRed(),color.GetGreen(),color.GetBlue()))

    def test_hatch_proof_is_inside_band_not_only_legend(self):
        import ROOT
        color=ROOT.gROOT.GetColor(861)
        # An empty physical region cannot be satisfied by the real legend's
        # hatch sample or by ROOT's unused diagonal-pattern resources.
        with self.assertRaisesRegex(ValueError,'diagonal vector hatch paths absent'):
            gate.pdf_hatch_paths(str(self.base)+'.pdf',(color.GetRed(),color.GetGreen(),color.GetBlue()),[])

    def test_marker_selects_only_successful_fixture(self):
        self.assertEqual(gate.fixture_directory(fixture_root,fixture_root/'current_fixture_path.txt'),selected_directory)

    def test_missing_success_marker_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'marker missing'):
            gate.fixture_directory(fixture_root,Path(self.temp.name)/'absent_marker.txt')

    def test_marker_cannot_escape_output_directory(self):
        marker=Path(self.temp.name)/'marker.txt';marker.write_text(self.temp.name+'\n')
        with self.assertRaisesRegex(ValueError,'escapes dedicated output'):
            gate.fixture_directory(fixture_root,marker)

if __name__=='__main__':unittest.main()
