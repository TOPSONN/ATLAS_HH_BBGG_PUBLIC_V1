"""Failure-path fixtures only; no fabricated physical sample or PASS bundle."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from simulation.new_backgrounds.scripts import publish_references as publisher
from simulation.new_backgrounds.scripts import validate_references as validator

REPO=Path(__file__).resolve().parents[3]


def temporary():
    path=REPO/'.local/phase6g_backgrounds/publication_failure_tests';path.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(dir=path)


class PublicationFailureTests(unittest.TestCase):
    def test_missing_manifests_rejected(self):
        for values in ({},{'reference_samples/new_backgrounds/B04_ZH/unknown.txt':b'INVALID_ONLY'}):
            with self.subTest(values=list(values)),self.assertRaises(ValueError):validator.validate_files(values)

    def test_method_receipt_never_physical_acceptance(self):
        data=json.dumps({'schema_version':1,'status':'METHOD_ONLY'}).encode()
        with self.assertRaises(ValueError):validator.validate_files({'reference_samples/new_backgrounds/B04_ZH/manifest.json':data})

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):validator.load_json_bytes(b'{"status":1,"status":2}')

    def test_nonfinite_json_rejected(self):
        for data in (b'{"number":NaN}',b'{"number":1e309}'):
            with self.subTest(data=data),self.assertRaises(ValueError):validator.load_json_bytes(data)

    def test_unsafe_repo_paths_rejected(self):
        for path in ('../sample.root','/sample.root','C:/sample.root','reference_samples\\sample.root','reference_samples//sample.root'):
            with self.subTest(path=path),self.assertRaises(ValueError):validator.path_key(path)

    def test_private_paths_rejected(self):
        for data in (b'/'+b'home/'+b'btu/'+b'simulations/sample',b'/'+b'home/'+b'other/'+b'sample',
                b'C:'+b'\\'+b'Users'+b'\\'+b'User'+b'\\'+b'secret',b'C:'+b'/'+b'HH/'+b'sample',
                b'/'+b'mnt/'+b'c/'+b'HH/'+b'sample'):
            with self.subTest(data=data),self.assertRaises(ValueError):validator.scan_private(data,'NEGATIVE_PATH_ONLY')

    def test_synthetic_marker_rejected(self):
        with self.assertRaises(ValueError):validator.scan_private(b'SYNTHETIC_METHOD_ONLY','NEGATIVE_SCOPE_ONLY')

    def test_corrupt_gzip_crc_rejected(self):
        raw=bytearray(gzip.compress(b'INVALID_NONPHYSICAL_LITERAL',mtime=0));raw[-8]^=1
        with self.assertRaises((OSError,ValueError)):validator.inflate(bytes(raw),'NEGATIVE_CRC_ONLY')

    def test_gzip_inflation_bound_rejected(self):
        with mock.patch.object(validator,'MAX_INFLATED',8),self.assertRaises(ValueError):
            validator.inflate(gzip.compress(b'INVALID_LONG_NONPHYSICAL_LITERAL',mtime=0),'NEGATIVE_BOUND_ONLY')

    def test_truncated_hepmc_rejected(self):
        with self.assertRaises(ValueError):validator.hepmc_blocks(b'HepMC::Version 3.03.01\n')

    def test_wrong_sidecar_magic_rejected(self):
        with self.assertRaises(ValueError):validator.dat_events(b'WRONG_NEGATIVE_MAGIC\n','ATLAS_NEW_BACKGROUND_TRUTH_V1')

    def test_truncated_actual_truth_shape_rejected(self):
        row=[['E','1','1','0','0','0','0','0','0']]+[[marker,'0'] for marker in 'HGBOSDX']
        with self.assertRaises(ValueError):validator.truth_shape(row[:-1],1)

    def test_extra_actual_truth_shape_rejected(self):
        row=[['E','1','1','0','0','0','0','0','0']]+[[marker,'0'] for marker in 'HGBOSDX']+[ ['EXTRA','0'] ]
        with self.assertRaises(ValueError):validator.truth_shape(row,1)

    def test_wrong_truth_count_rejected(self):
        row=[['E','1','1','0','0','0','0','0','0']]+[[marker,'0'] for marker in 'HGBOSDX'];row[1]=['H','2','0']
        with self.assertRaises(ValueError):validator.truth_shape(row,1)

    def test_unknown_absolute_artifact_projection_rejected(self):
        with self.assertRaises(ValueError):publisher.public_projection({'input':'/unknown/absolute/sample.root'},Path('/kept/run'),Path('/kept/repo'),{})

    def test_source_only_run_refused_before_reference_writes(self):
        with temporary() as temp:
            folder=Path(temp);run=folder/'NEGATIVE_INCOMPLETE_SOURCE_ONLY';run.mkdir()
            (run/'run_manifest.json').write_text(json.dumps({'status':'PARTIAL_PHYSICAL_CHAIN','physical_generation_completed':False,'MG5_events_generated':1000}),encoding='utf-8')
            with self.assertRaises(ValueError):publisher.publish_references(run,folder/'NEGATIVE_TARGET_REPO')
            self.assertFalse((folder/'NEGATIVE_TARGET_REPO').exists())

    def test_wrong_target_counts_refused_before_receipt_reads(self):
        with temporary() as temp:
            folder=Path(temp);run=folder/'NEGATIVE_COUNTS_ONLY';run.mkdir()
            value={'status':'PASS_FULL_CHAIN_MODEL_SCOPE','physical_generation_completed':True,
                'MG5_events_generated':1000,'Pythia_events_attempted':999,'Pythia_events_written':999,'HepMC_validated_events':999,'Delphes_ROOT_entries':999}
            (run/'run_manifest.json').write_text(json.dumps(value),encoding='utf-8')
            with self.assertRaises(ValueError):publisher.prepare_plan(run,folder/'NEGATIVE_TARGET_REPO')
            self.assertFalse((folder/'NEGATIVE_TARGET_REPO').exists())

    def test_unbound_outside_source_file_refused(self):
        with temporary() as temp:
            folder=Path(temp);run=folder/'NEGATIVE_BOUNDARY_ONLY';run.mkdir();outside=folder/'INVALID.txt';outside.write_bytes(b'INVALID_ONLY')
            with self.assertRaises(ValueError):publisher.inside_file(outside,run)

    def test_retained_shower_method_or_missing_scope_rejected(self):
        for descriptor in ({},{'status':'METHOD_ONLY'},
                {'status':'SOURCE_BOUND_COMPLETED_SHOWER_REUSE_ZERO_PRODUCER_CALLS',
                 'Pythia_invocations_in_continuation':1,'new_source_events':0}):
            with self.subTest(descriptor=descriptor),self.assertRaises(ValueError):
                publisher.retained_shower_inputs(descriptor,Path('/fresh'),{'process':'zh'})

    def test_retained_shower_new_source_events_rejected(self):
        descriptor={'status':'SOURCE_BOUND_COMPLETED_SHOWER_REUSE_ZERO_PRODUCER_CALLS',
            'Pythia_invocations_in_continuation':0,'new_source_events':1000}
        with self.assertRaises(ValueError):publisher.retained_shower_inputs(descriptor,Path('/fresh'),{'process':'zh'})

    def test_retained_shower_output_overlap_rejected(self):
        with temporary() as temp:
            folder=Path(temp).resolve();descriptor={'status':'SOURCE_BOUND_COMPLETED_SHOWER_REUSE_ZERO_PRODUCER_CALLS',
                'Pythia_invocations_in_continuation':0,'new_source_events':0,'original_run':str(folder)}
            with self.assertRaises(ValueError):publisher.retained_shower_inputs(descriptor,folder,{'process':'zh'})

    def test_unpinned_nonphysical_retained_manifest_rejected(self):
        with temporary() as temp:
            folder=Path(temp).resolve();original=folder/'NEGATIVE_NONPHYSICAL';original.mkdir()
            manifest=original/'run_manifest.json';manifest.write_bytes(b'INVALID_NEGATIVE_ONLY')
            descriptor={'status':'SOURCE_BOUND_COMPLETED_SHOWER_REUSE_ZERO_PRODUCER_CALLS',
                'Pythia_invocations_in_continuation':0,'new_source_events':0,'original_run':str(original),
                'manifest_path':str(manifest),'manifest_sha256':publisher.file_sha(manifest),
                'full_shower_sha256':publisher.RETAINED_FULL_HEPMC_SHA}
            with self.assertRaises(ValueError):publisher.retained_shower_inputs(descriptor,folder/'fresh',{'process':'zh'})

    def test_method_build_cannot_authorize_installed_xml_projection(self):
        with self.assertRaises(ValueError):publisher.installed_xml_labels({'status':'METHOD_ONLY'})

    def test_missing_installed_xml_fingerprints_rejected(self):
        build={'status':'PASS_BUILD_AND_METHODS_ONLY','weight_source_commit':'83a5c9986f30746cfb390435a9b10ac55a758fca'}
        with self.assertRaises(ValueError):publisher.installed_xml_labels(build)

    def test_ambiguous_installed_xml_directories_rejected(self):
        build={'status':'PASS_BUILD_AND_METHODS_ONLY','weight_source_commit':'83a5c9986f30746cfb390435a9b10ac55a758fca',
            'installation_file_sha256':{'/invalid_one/ParticleData.xml':'0'*64,'/invalid_two/ParticleData.xml':'0'*64}}
        with self.assertRaises(ValueError):publisher.installed_xml_labels(build)

    def test_changed_installed_xml_bytes_rejected(self):
        with temporary() as temp:
            folder=Path(temp).resolve();path=folder/'ParticleData.xml';path.write_bytes(b'INVALID_FAILURE_CONTROL_ONLY')
            build={'status':'PASS_BUILD_AND_METHODS_ONLY','weight_source_commit':'83a5c9986f30746cfb390435a9b10ac55a758fca',
                'installation_file_sha256':{str(path):'0'*64}}
            with self.assertRaises(ValueError):publisher.installed_xml_labels(build)

    def test_modified_header_card_text_rejected_before_event_reads(self):
        raw=b'<LesHouchesEvents version="3.0"><header>3.5.16<MG5ProcCard>\nMODIFIED_NEGATIVE_CARD\n</MG5ProcCard></header><init/></LesHouchesEvents>'
        receipt={'card_hashes':{'process_card':validator.sha(b'\nORIGINAL_NEGATIVE_CARD\n')}}
        with self.assertRaisesRegex(ValueError,'header card identity mismatch'):validator.lhe_check(raw,receipt,{}, {})

    def test_removed_leading_header_newline_rejected_before_event_reads(self):
        raw=b'<LesHouchesEvents version="3.0"><header>3.5.16<MG5ProcCard>ORIGINAL_NEGATIVE_CARD\n</MG5ProcCard></header><init/></LesHouchesEvents>'
        receipt={'card_hashes':{'process_card':validator.sha(b'\nORIGINAL_NEGATIVE_CARD\n')}}
        with self.assertRaisesRegex(ValueError,'header card identity mismatch'):validator.lhe_check(raw,receipt,{}, {})


if __name__=='__main__':unittest.main()
