"""Synthetic method tests; no native library, installed payload or MG5 execution."""
import ast
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from source import pdf_backend as b
spec=importlib.util.spec_from_file_location("phase13_backend_cli",Path(__file__).resolve().parents[1]/"scripts/audit_pdf_backend.py")
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)

def info_fixture():
    qs=[1.0,1.275,1.275]+[2+i/100 for i in range(43)]+[3.7262747,4.23139,10.0,100.0]
    vs=[.4-i*.002 for i in range(50)];vs[46]=.26466316;vs[47]=.25335777
    return {"SetIndex":263400,"DataVersion":2,"NumMembers":101,"Particle":2212,
        "OrderQCD":0,"FlavorScheme":"variable","NumFlavors":4,"AlphaS_OrderQCD":0,
        "AlphaS_Type":"ipol","Flavors":list(b.FLAVOURS),"MZ":4.1799998,
        "AlphaS_MZ":.2544023564420006,"AlphaS_Qs":qs,"AlphaS_Vals":vs,
        "MCharm":1.275,"MBottom":4.1799998,"MTop":173.07001}

def native_fixture():
    x={"native_flavours":list(b.FLAVOURS),"bottom_active":False,"native_LHAPDF_ID":263400,
        "reader_version":"6.5.6","native_file_resolution_checked":True,
        "selected_member_resolution":"EXCLUSIVE_EXTERNAL_MEMBER; BUILTIN_METADATA_FALLBACK_OBSERVED_AND_NO_SAME_NAME_INSTALLED_SET",
        "interpolation_errors":0,"nonfinite_errors":0,"finite_pdf_points":[{}]*4,"finite_xfx_values":36}
    for k in ["MG5_parser_executed","matching_validated","physical_component_validated","installed_directory_writes"]: x[k]=False
    for k in ["new_ME_calls","new_integrals","new_hard_events","new_Pythia_events","new_Delphes_events"]: x[k]=0
    return x

class BackendMethods(unittest.TestCase):
    def test_off_knot_reference_preserves_failed_strict_diagnostic(self):
        r=b.alpha_diagnostic(info_fixture(),.254403024565842)
        self.assertIs(r["strict_diagnostic_pass"],False)
        self.assertAlmostEqual(r["relative_difference"],2.626248635282933e-6)
        self.assertFalse(r["reference_is_exact_knot"])
        self.assertEqual(r["table_bracket"],[{"Q_GeV":3.7262747,"alpha_s":.26466316},{"Q_GeV":4.23139,"alpha_s":.25335777}])
        self.assertIsNone(r["official_accuracy_bound"])
        self.assertEqual(r["duplicate_Q_knots_GeV"],[1.275])
    def test_wrong_reference_is_rejected(self):
        x=info_fixture();x["MZ"]=91.1876
        with self.assertRaisesRegex(b.BackendReviewError,"WRONG_ALPHA_REFERENCE"):b.alpha_diagnostic(x,.254403024565842)
    def test_setname_0130_not_reference(self):
        x=info_fixture();x["AlphaS_MZ"]=.130
        with self.assertRaises(b.BackendReviewError):b.alpha_diagnostic(x,.254403024565842)
    def test_changed_historical_native_result_rejected(self):
        with self.assertRaisesRegex(b.BackendReviewError,"HISTORICAL_NATIVE_ALPHA_CHANGED"):b.alpha_diagnostic(info_fixture(),.2544023564420006)
    def test_nonfinite_native_rejected(self):
        for v in [math.nan,math.inf,-1,None]:
            with self.subTest(v=v),self.assertRaises(b.BackendReviewError):b.alpha_diagnostic(info_fixture(),v)
    def test_different_alpha_type_not_silently_analytic(self):
        x=info_fixture();x["AlphaS_Type"]="analytic"
        with self.assertRaises(b.BackendReviewError):b.alpha_diagnostic(x,.254403024565842)
    def test_wrong_order_rejected(self):
        x=info_fixture();x["AlphaS_OrderQCD"]=1
        with self.assertRaises(b.BackendReviewError):b.alpha_diagnostic(x,.254403024565842)
    def test_mismatched_alpha_tables_rejected(self):
        x=info_fixture();x["AlphaS_Vals"].pop()
        with self.assertRaises(b.BackendReviewError):b.alpha_diagnostic(x,.254403024565842)
    def test_unordered_table_rejected(self):
        x=info_fixture();x["AlphaS_Qs"][3]=0.5
        with self.assertRaises(b.BackendReviewError):b.alpha_diagnostic(x,.254403024565842)
    def test_no_bottom_flavour_and_max4(self):
        r=b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1"},native_fixture())
        self.assertTrue(r["Charm"]["activation_permitted_by_max4"])
        self.assertFalse(r["Bottom"]["activation_permitted_by_max4"])
        self.assertFalse(r["Top"]["activation_permitted_by_max4"])
        self.assertFalse(r["Bottom"]["ME_pole_mass_inference"])
    def test_wrong_member_id_rejected(self):
        x=native_fixture();x["native_LHAPDF_ID"]=263401
        with self.assertRaises(b.BackendReviewError):b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1"},x)
    def test_bottom_native_rejected(self):
        x=native_fixture();x["native_flavours"].append(5)
        with self.assertRaises(b.BackendReviewError):b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1"},x)
    def test_member_override_rejected(self):
        with self.assertRaisesRegex(b.BackendReviewError,"MEMBER_OVERRIDE"):b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1","MZ":91.1876},native_fixture())
    def test_numflavors_not_inferred_from_name(self):
        x=info_fixture();del x["NumFlavors"]
        with self.assertRaises(b.BackendReviewError):b.validate_metadata(x,{"PdfType":"central","Format":"lhagrid1"},native_fixture())
    def test_alpha_max5_not_accepted(self):
        x=info_fixture();x["AlphaS_NumFlavors"]=5
        with self.assertRaises(b.BackendReviewError):b.validate_metadata(x,{"PdfType":"central","Format":"lhagrid1"},native_fixture())
    def test_native_scope_cannot_be_promoted(self):
        x=native_fixture();x["MG5_parser_executed"]=True
        with self.assertRaisesRegex(b.BackendReviewError,"HISTORICAL_SCOPE"):b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1"},x)
    def test_nonzero_native_physics_count_rejected(self):
        x=native_fixture();x["new_ME_calls"]=1
        with self.assertRaisesRegex(b.BackendReviewError,"PHYSICS_COUNTER"):b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1"},x)
    def test_historical_unverified_fallback_rejected(self):
        x=native_fixture();x["selected_member_resolution"]="DEFAULT_FALLBACK"
        with self.assertRaises(b.BackendReviewError):b.validate_metadata(info_fixture(),{"PdfType":"central","Format":"lhagrid1"},x)
    def test_identity_raw_whitespace_and_size(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"input";p.write_bytes(b"a\n");old=b.identity(p);p.write_bytes(b"a \n")
            with self.assertRaisesRegex(b.BackendReviewError,"IDENTITY_MISMATCH"):b.compare_identity(p,old)
    def test_resolved_path_redirect_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);a=r/"a";c=r/"c";link=r/"link";a.write_text("same");c.write_text("same");link.symlink_to(a)
            old=b.identity(link);link.unlink();link.symlink_to(c)
            with self.assertRaisesRegex(b.BackendReviewError,"resolved_path"):b.compare_identity(link,old)
    def test_missing_payload_rejected(self):
        with self.assertRaisesRegex(b.BackendReviewError,"MISSING_REGULAR_INPUT"):b.identity("/NONEXISTENT_PHASE13_SYNTHETIC_PAYLOAD")
    def test_source_anchor_missing_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"source";p.write_text("wrong_anchor\n")
            with self.assertRaisesRegex(b.BackendReviewError,"SOURCE_WITNESS_MISSING"):b.witness(p,["ALPHAS=alphasPDF(Q)"])
    def test_wrong_backend_density_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"pdf_lhapdf62.cc"
            p.write_text("return ACTIVESETS[nset].activeMember()->xfxQ(ipart_copy, x, q);\n")
            with self.assertRaisesRegex(b.BackendReviewError,"SOURCE_WITNESS_MISSING"):
                b.witness(p,["activeMember()->xfxQ(ipart_copy,x,q)"])
            self.assertEqual(b.witness(p,["activeMember()->xfxQ(ipart_copy, x, q)"])["witnesses"][0]["line_numbers"],[1])
    def test_wrong_lo_lhaid_anchor_not_replaced_by_nlo_or_default(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"banner.py"
            p.write_text('self.add_param("lhaid", 230000, hidden=True)\n')
            with self.assertRaisesRegex(b.BackendReviewError,"SOURCE_WITNESS_MISSING"):
                b.witness(p,["self.add_param('lhaid', 230000"])
            self.assertEqual(b.witness(p,['self.add_param("lhaid", 230000'])["witnesses"][0]["line_numbers"],[1])
    def test_duplicate_metadata_key_rejected(self):
        with self.assertRaisesRegex(b.BackendReviewError,"DUPLICATE_METADATA"):b.parse_info("MZ: 1\nMZ: 2\n")
    def test_missing_historical_dependency_closure_rejected(self):
        with self.assertRaises(b.BackendReviewError):b.verify_historical_closure({})
    def test_no_native_package_import_or_subprocess(self):
        tree=ast.parse(Path(b.__file__).read_text())
        imports=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):imports.extend(i.name for i in n.names)
            elif isinstance(n,ast.ImportFrom):imports.append(n.module)
        self.assertFalse(set(imports)&{"lhapdf","madgraph","subprocess","os","ctypes"})
    def test_outputs_are_new_only(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"receipt.json";cli.write_fresh(p,{"scope":"SYNTHETIC_METHOD_ONLY"})
            before=p.read_bytes()
            with self.assertRaises(FileExistsError):cli.write_fresh(p,{"scope":"wrong"})
            self.assertEqual(p.read_bytes(),before)
    def test_output_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            r=Path(temp);real=r/"real";real.mkdir();link=r/"link";link.symlink_to(real,target_is_directory=True)
            with self.assertRaisesRegex(b.BackendReviewError,"REDIRECTED"):cli.write_fresh(link/"receipt.json",{})

if __name__=="__main__":unittest.main()
