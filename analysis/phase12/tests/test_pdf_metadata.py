import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from pdf_metadata import SET_NAME, inspect_local_pair, parse_metadata, read_member_header, validate_metadata


def metadata():
    return {'SetDesc':'SYNTHETIC_SCHEMA_FIXTURE central average','SetIndex':263400,'Authors':'SYNTHETIC_SCHEMA_FIXTURE','Reference':'arXiv:1410.8849','Format':'lhagrid1','DataVersion':2,'NumMembers':101,'Particle':2212,'Flavors':[-4,-3,-2,-1,1,2,3,4,21],'OrderQCD':0,'FlavorScheme':'variable','NumFlavors':4,'XMin':1e-9,'XMax':1.,'QMin':1.,'QMax':1e5,'MZ':4.1799998,'MCharm':1.275,'MBottom':4.1799998,'MTop':173.07001,'AlphaS_MZ':.2544023564420006,'AlphaS_OrderQCD':0,'AlphaS_Type':'ipol','AlphaS_Qs':[1.,1.275,1.275,4.1799998,10.,1e5],'AlphaS_Vals':[.5,.42,.42,.2544023564420006,.2,.06],'ForcePositive':2}


def serialized(info):
    return '\n'.join(k+': '+repr(v) for k,v in info.items())+'\n'

class PDFMetadataTests(unittest.TestCase):
    def test_member_zero_and_LO_zero_are_known_values(self):
        result=validate_metadata(metadata(),0)
        self.assertEqual(result['member'],0);self.assertEqual(result['PDF_order_QCD'],0);self.assertEqual(result['alpha_order_QCD'],0)
    def test_reference_is_declared_scale_not_name_or_Z(self):
        result=validate_metadata(metadata())
        self.assertEqual(result['alpha_reference']['scale_GeV'],4.1799998)
        self.assertNotEqual(result['alpha_reference']['scale_GeV'],91.1876)
        self.assertNotEqual(result['alpha_reference']['value'],.130)
    def test_documented_max4_fallback_is_explicit(self):
        result=validate_metadata(metadata());self.assertEqual(result['alpha_maximum_flavours'],4)
        self.assertIn('DOCUMENTED_FALLBACK',result['alpha_maximum_flavours_source_key'])
    def test_variable_max4_is_not_incorrectly_rejected(self):
        result=validate_metadata(metadata());self.assertEqual(result['PDF_flavour_scheme'],'variable');self.assertFalse(result['bottom_pdf_activation'])
    def test_bottom_evolution_mass_is_not_activation(self):
        result=validate_metadata(metadata());self.assertGreater(result['thresholds']['Bottom']['declared_evolution_mass_GeV'],0)
        self.assertFalse(result['thresholds']['Bottom']['activation_permitted_by_maximum_flavours'])
    def test_duplicate_Q_threshold_nodes_are_allowed(self):
        result=validate_metadata(metadata());self.assertEqual(result['duplicate_alpha_Q_nodes_GeV'],[1.275])
    def test_missing_scientific_field_rejected(self):
        info=metadata();del info['MZ']
        with self.assertRaisesRegex(ValueError,'MISSING_SCIENTIFIC'):
            validate_metadata(info)
    def test_zero_reference_coupling_rejected(self):
        info=metadata();info['AlphaS_MZ']=0
        with self.assertRaisesRegex(ValueError,'NONFINITE_OR_INVALID'):
            validate_metadata(info)
    def test_boolean_member_not_zero(self):
        with self.assertRaisesRegex(ValueError,'INVALID_INTEGER'):
            validate_metadata(metadata(),False)
    def test_member_not_reviewed_rejected(self):
        with self.assertRaisesRegex(ValueError,'CENTRAL_MEMBER_ZERO'):
            validate_metadata(metadata(),1)
    def test_five_flavour_pdf_rejected(self):
        info=metadata();info['NumFlavors']=5
        with self.assertRaisesRegex(ValueError,'PDF_NOT_MAXIMUM_FOUR'):
            validate_metadata(info)
    def test_bottom_in_flavour_list_rejected(self):
        info=metadata();info['Flavors']+=[5,-5]
        with self.assertRaisesRegex(ValueError,'WRONG_FOUR_FLAVOUR'):
            validate_metadata(info)
    def test_five_flavour_alpha_override_rejected(self):
        info=metadata();info['AlphaS_NumFlavors']=5
        with self.assertRaisesRegex(ValueError,'ALPHA_NOT_MAXIMUM_FOUR'):
            validate_metadata(info)
    def test_NLO_pdf_rejected(self):
        info=metadata();info['OrderQCD']=1
        with self.assertRaisesRegex(ValueError,'NON_LO_PDF'):
            validate_metadata(info)
    def test_NLO_alpha_rejected(self):
        info=metadata();info['AlphaS_OrderQCD']=1
        with self.assertRaisesRegex(ValueError,'NON_LO_ALPHA'):
            validate_metadata(info)
    def test_unknown_alpha_type_rejected(self):
        info=metadata();info['AlphaS_Type']='analytic'
        with self.assertRaisesRegex(ValueError,'UNREVIEWED_ALPHA'):
            validate_metadata(info)
    def test_nonfinite_reference_rejected(self):
        info=metadata();info['AlphaS_MZ']=float('nan')
        with self.assertRaisesRegex(ValueError,'NONFINITE'):
            validate_metadata(info)
    def test_inconsistent_alpha_lists_rejected(self):
        info=metadata();info['AlphaS_Vals'].pop()
        with self.assertRaisesRegex(ValueError,'INVALID_ALPHA_INTERPOLATION'):
            validate_metadata(info)
    def test_unordered_alpha_Qs_rejected(self):
        info=metadata();info['AlphaS_Qs'][1]=9.
        with self.assertRaisesRegex(ValueError,'UNORDERED_ALPHA'):
            validate_metadata(info)
    def test_reference_out_of_table_rejected(self):
        info=metadata();info['MZ']=2e5
        with self.assertRaisesRegex(ValueError,'REFERENCE_OUTSIDE'):
            validate_metadata(info)
    def test_unreviewed_data_version_rejected(self):
        info=metadata();info['DataVersion']=3
        with self.assertRaisesRegex(ValueError,'UNREVIEWED_DATA_VERSION'):
            validate_metadata(info)
    def test_duplicate_info_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            parse_metadata('MZ: 4.18\nMZ: 91.1876\n')
    def test_parser_roundtrip_small_flow_subset(self):
        self.assertEqual(parse_metadata(serialized(metadata())),metadata())
    def test_empty_description_rejected(self):
        info=metadata();info['Reference']=''
        with self.assertRaisesRegex(ValueError,'EMPTY_SCIENTIFIC'):
            validate_metadata(info)
    def test_missing_actual_member_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);info=base/(SET_NAME+'.info');info.write_text(serialized(metadata()))
            with self.assertRaisesRegex(ValueError,'ACTUAL_MEMBER_MISSING'):
                inspect_local_pair(info,base/(SET_NAME+'_0000.dat'))
    def test_header_success_is_not_native_grid_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);info=base/(SET_NAME+'.info');member=base/(SET_NAME+'_0000.dat')
            info.write_text(serialized(metadata()));member.write_text('PdfType: central\nFormat: lhagrid1\n---\nNOT_A_REAL_GRID\n')
            result=inspect_local_pair(info,member)
            self.assertEqual(result['native_member_readability'],'NOT_TESTED_BY_METADATA_VALIDATION')
            self.assertFalse(result['physical_component_validated']);self.assertEqual(result['member_header']['PdfType'],'central')
    def test_member_flavour_override_revalidated(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);info=base/(SET_NAME+'.info');member=base/(SET_NAME+'_0000.dat')
            info.write_text(serialized(metadata()));member.write_text('PdfType: central\nNumFlavors: 5\n---\n')
            with self.assertRaisesRegex(ValueError,'PDF_NOT_MAXIMUM_FOUR'):
                inspect_local_pair(info,member)
    def test_replica_cannot_impersonate_selected_central(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);info=base/(SET_NAME+'.info');member=base/(SET_NAME+'_0000.dat')
            info.write_text(serialized(metadata()));member.write_text('PdfType: replica\n---\n')
            with self.assertRaisesRegex(ValueError,'NOT_CENTRAL'):
                inspect_local_pair(info,member)
    def test_missing_header_terminator_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            member=Path(folder)/'bad.dat';member.write_text('PdfType: central\n')
            with self.assertRaisesRegex(ValueError,'HEADER_TERMINATOR'):
                read_member_header(member)
    def test_no_network_native_or_generator_dispatch(self):
        source=(Path(__file__).resolve().parents[1]/'source/pdf_metadata.py').read_text()
        for forbidden in ('import lhapdf','import madgraph','subprocess','urllib','requests','write_text','write_bytes'):
            self.assertNotIn(forbidden,source)

if __name__=='__main__':unittest.main()