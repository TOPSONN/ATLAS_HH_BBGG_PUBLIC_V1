import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
from model_pdf import parse_slha_blocks, ufo_external_defaults, parse_cteq_header, validate_candidate, validate_pdf_metadata, inventory_directory
import json

class ModelPdfTests(unittest.TestCase):
    def setUp(self):
        self.candidate = json.loads((Path(__file__).resolve().parents[1] / "config/candidate_a.json").read_text())
    def metadata(self):
        return dict(set_name="SYNTHETIC_FIXED_4F_ONLY", member=0, lhaid=1, grid_sha256="a"*64, info_sha256="b"*64, flavour_pdg_ids=[-4,-3,-2,-1,1,2,3,4,21],
                    flavour_scheme="fixed", num_flavours=4, order_qcd=0, alpha_s_mz=.13,
                    alpha_s_order_qcd=0, alpha_s_flavour_scheme="fixed", alpha_s_num_flavours=4,
                    alpha_s_thresholds_GeV={"charm":1.3,"bottom_activation":None},
                    alpha_s_reference_scale_GeV=91.1876, alpha_s_type="analytic")
    def test_restriction_slha(self):
        data=parse_slha_blocks("Block MASS\n 4 0d0 # MC\n 5 4.7d0 # MB\n DECAY 25 1e-3\n")
        self.assertEqual(data["MASS"][4],0)
        self.assertEqual(str(data["MASS"][5]),"4.7")
    def test_ast_never_imports_or_executes(self):
        value=ufo_external_defaults("raise RuntimeError('MUST_NOT_RUN')\nMC=Parameter(value=1.27)\nMB=Parameter(value=4.7)")
        self.assertEqual(value,{"MC":1.27,"MB":4.7})
    def test_model_charm_not_ufo_default(self):
        changed=copy.deepcopy(self.candidate);changed["charm_mass_GeV"]=1.27
        with self.assertRaisesRegex(ValueError,"MASS"):validate_candidate(changed)
    def test_massless_bottom_rejected(self):
        changed=copy.deepcopy(self.candidate);changed["bottom_mass_GeV"]=0
        with self.assertRaisesRegex(ValueError,"MASS"):validate_candidate(changed)
    def test_p4_forbids_incoming_bottom(self):
        changed=copy.deepcopy(self.candidate);changed["initial_pdg_ids"] += [5,-5]
        with self.assertRaisesRegex(ValueError,"P4"):validate_candidate(changed)
    def test_null_pdf_is_blocked_never_zero(self):
        issues=validate_candidate(self.candidate)
        self.assertIn("PDF_METADATA_MISSING:alpha_s_mz",issues)
        self.assertIsNone(self.candidate["pdf"]["member"])
    def test_known_5f_is_rejected_even_when_other_fields_unknown(self):
        meta=copy.deepcopy(self.candidate['pdf']);meta['num_flavours']=5
        with self.assertRaisesRegex(ValueError,'FLAVOUR'):validate_pdf_metadata(meta,4)
    def test_boolean_alpha_order_is_not_integer_zero(self):
        meta=self.metadata();meta['alpha_s_order_qcd']=False
        with self.assertRaisesRegex(ValueError,'LO_'):validate_pdf_metadata(meta,4)
    def test_complete_synthetic_4f_schema(self):
        self.assertEqual(validate_pdf_metadata(self.metadata(),4),[])
    def test_5f_substitution_rejected(self):
        meta=self.metadata();meta["num_flavours"]=5
        with self.assertRaisesRegex(ValueError,"FLAVOUR"):validate_pdf_metadata(meta,4)
    def test_alpha_s_5f_rejected(self):
        meta=self.metadata();meta["alpha_s_num_flavours"]=5
        with self.assertRaisesRegex(ValueError,"FLAVOUR"):validate_pdf_metadata(meta,4)
    def test_variable_pdf_max4_supported(self):
        meta=self.metadata();meta["flavour_scheme"]="variable"
        self.assertEqual(validate_pdf_metadata(meta,4),[])
    def test_variable_alpha_max4_supported(self):
        meta=self.metadata();meta["alpha_s_flavour_scheme"]="variable"
        self.assertEqual(validate_pdf_metadata(meta,4),[])
    def test_zero_alpha_is_invalid(self):
        meta=self.metadata();meta["alpha_s_mz"]=0
        with self.assertRaisesRegex(ValueError,"ALPHA"):validate_pdf_metadata(meta,4)
    def test_two_loop_requires_new_review(self):
        meta=self.metadata();meta["alpha_s_order_qcd"]=1
        with self.assertRaisesRegex(ValueError,"LO_"):validate_pdf_metadata(meta,4)
    def test_member_zero_is_known_identity(self):
        self.assertEqual(validate_pdf_metadata(self.metadata(),4),[])
    def test_grid_hash_not_optional(self):
        meta=self.metadata();meta["grid_sha256"]=None
        self.assertIn("PDF_METADATA_MISSING:grid_sha256",validate_pdf_metadata(meta,4))
    def test_bottom_activation_inconsistent(self):
        meta=self.metadata();meta["alpha_s_thresholds_GeV"]["bottom_activation"]=4.5
        with self.assertRaisesRegex(ValueError,"BOTTOM"):validate_pdf_metadata(meta,4)
    def test_charm_threshold_cannot_be_zero(self):
        meta=self.metadata();meta["alpha_s_thresholds_GeV"]["charm"]=0
        with self.assertRaisesRegex(ValueError,"CHARM"):validate_pdf_metadata(meta,4)
    def test_alpha_reference_scale_not_assumed_mz(self):
        meta=self.metadata();meta['alpha_s_mz']=.2544;meta['alpha_s_reference_scale_GeV']=4.18;meta['alpha_s_type']='ipol'
        self.assertEqual(validate_pdf_metadata(meta,4),[])
        meta['alpha_s_reference_scale_GeV']=None
        self.assertIn('PDF_METADATA_MISSING:alpha_s_reference_scale_GeV',validate_pdf_metadata(meta,4))
    def test_payload_flavour_list_not_inferred_from_name(self):
        meta=self.metadata();meta['flavour_pdg_ids'] += [5,-5]
        with self.assertRaisesRegex(ValueError,'PARTON_ID'):validate_pdf_metadata(meta,4)
    def test_broken_symlink_is_explicit_missing_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'grid.dat').symlink_to('missing.dat')
            result=inventory_directory(root,'SYNTHETIC_METHOD_ONLY',0)
            self.assertEqual(result['files'][0]['status'],'BROKEN_SYMLINK')
            self.assertIsNone(result['files'][0]['sha256'])
            self.assertEqual(result['files'][0]['link_target'],'missing.dat')
    def test_symlink_directory_not_silently_inventoried(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'actual').mkdir();(root/'link').symlink_to('actual',target_is_directory=True)
            result=inventory_directory(root,'SYNTHETIC_METHOD_ONLY',0)
            self.assertEqual(result['untraversed_symlink_directories'][0]['relative_path'],'link')
    def test_bad_mass_threshold_missing(self):
        meta=self.metadata();meta["alpha_s_thresholds_GeV"]={}
        with self.assertRaisesRegex(ValueError,"CHARM"):validate_pdf_metadata(meta,4)
    def test_cteq_header_five_flavours(self):
        header="cteq6l1\nOrdr, Nfl, lambda Qmass\n1. 5. .1652 0 0 .2 1.3 4.5 180\nNX NT NfMx\n95 19 5"
        meta=parse_cteq_header(header)
        self.assertEqual(meta["maximum_flavours"],5)
        self.assertEqual(meta["quark_mass_parameters_GeV"]["bottom"],4.5)
        self.assertEqual(meta["maximum_pdf_parton_flavour"],5)
    def test_matching_scale_is_not_auto_chosen(self):
        changed=copy.deepcopy(self.candidate);changed["matching_scale_GeV"]=30
        with self.assertRaisesRegex(ValueError,"MATCHING"):validate_candidate(changed)
    def test_no_total_or_execution_promotion(self):
        for key,value in (("execution_enabled",True),("inclusive_background_total",True)):
            changed=copy.deepcopy(self.candidate);changed[key]=value
            with self.assertRaises(ValueError):validate_candidate(changed)
    def test_bounded_inventory_preserves_payload_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"grid.dat").write_bytes(b"1\n")
            (root/"hidden").mkdir();(root/"hidden/x.dat").write_bytes(b"2")
            result=inventory_directory(root,"SYNTHETIC_METHOD_ONLY",0)
            self.assertEqual([x["relative_path"] for x in result["files"]],["grid.dat"])
            self.assertEqual((root/"grid.dat").read_bytes(),b"1\n")
    def test_explicit_unknown_root(self):
        with tempfile.TemporaryDirectory() as directory:
            result=inventory_directory(Path(directory)/"absent","SYNTHETIC_METHOD_ONLY")
            self.assertFalse(result["exists"]);self.assertEqual(result["files"],[])
if __name__=="__main__":unittest.main()
