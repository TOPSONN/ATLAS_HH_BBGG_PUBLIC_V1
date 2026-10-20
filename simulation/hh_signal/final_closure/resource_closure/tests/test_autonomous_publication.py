"""Narrow stacked publication policy; pure byte tests, no Git/network calls."""
import json
import unittest
from unittest import mock
from simulation.hh_signal.final_closure.resource_closure import autonomous_publication as p


class AutonomousPublicationTests(unittest.TestCase):
    def test_fixed_reviewed_base(self):
        self.assertEqual(p.BASE,'5431e0b2efba20863cddaccc37679af32e13a7f4')

    def test_source_and_new_reports_allowed(self):
        for name in p.EXACT:
            self.assertTrue(p.allowed(name),name)
        self.assertTrue(p.allowed(p.REPORTS+'REPORT_ZH_TW.md'))

    def test_historical_science_profiles_and_figures_forbidden(self):
        for name in (p.PREFIX+'allocation_guard.py',p.PREFIX+'config/build_profile.json',
                     'reports/phase7i_namespace_storage_recovery/evidence.json',
                     p.REPORTS+'raw.png',p.REPORTS+'plot.pdf',p.REPORTS+'private.env',
                     p.REPORTS+'sample.root',p.REPORTS+'out.lhe',p.REPORTS+'a.so'):
            self.assertFalse(p.allowed(name),name)

    def test_serialized_private_frames_not_published(self):
        private={'kind':'PRIVATE_MOUNTINFO_RAW','base64':'INERT'}
        for name,raw in ((p.REPORTS+'a.json',json.dumps(private).encode()),
                         (p.REPORTS+'a.md',json.dumps(json.dumps(private)).encode())):
            with self.subTest(name=name),mock.patch.object(p.original,'allowed_path',p.allowed):
                with self.assertRaises(ValueError):p.validate(name,raw)

    def test_raw_mount_rows_never_public(self):
        with mock.patch.object(p.original,'allowed_path',p.allowed):
            with self.assertRaises(ValueError):
                p.validate(p.REPORTS+'a.md',b'1 9 0:1 / / ro - ext4 INERT ro\n')

    def test_clean_bounded_report_with_null_measurements_passes(self):
        raw=json.dumps({'cpu_seconds':None,'FULL_LAUNCH_ENVELOPE_VERIFIED':False,
                        'status':'LEVEL_A_ONLY'}).encode()
        with mock.patch.object(p.original,'allowed_path',p.allowed):
            p.validate(p.REPORTS+'a.json',raw)

    def test_original_audit_policy_restored_after_rejection(self):
        allowed=p.original.allowed_path;validate=p.original.validate_payload
        with mock.patch.object(p.original,'audit',side_effect=ValueError('INERT')):
            with self.assertRaises(ValueError):p.audit()
        self.assertIs(p.original.allowed_path,allowed)
        self.assertIs(p.original.validate_payload,validate)

    def test_original_size_caps_unchanged(self):
        with mock.patch.object(p.original,'allowed_path',p.allowed):
            with self.assertRaises(ValueError):
                p.validate(p.REPORTS+'large.md',b'x'*131073)


    def test_unsafe_report_paths_and_nonregular_modes_rejected(self):
        for suffix in ('../outside.json','private/a.json','a/../../outside.md','chunk_1.txt',
                       'a.tar','a.png','a.PDF','a.so'):
            with self.subTest(suffix=suffix):
                self.assertFalse(p.allowed(p.REPORTS+suffix))
        for mode in ('100755','120000','160000'):
            with self.subTest(mode=mode),mock.patch.object(p.original,'allowed_path',p.allowed):
                with self.assertRaises(ValueError):p.validate(p.REPORTS+'safe.md',b'INERT',mode)

    def test_inherited_binary_secret_and_strict_json_checks_remain_active(self):
        examples=(('a.md',b'%PDF-SYNTHETIC'),('a.md',b'\x89PNG\r\n\x1a\nSYNTHETIC'),
                  ('a.md',b'ghp_'+b'a'*36),('a.json',b'{"x":1,"x":2}'),
                  ('a.json',b'{"x":NaN}'),('a.json',b'{"x":1e9999}'))
        for name,raw in examples:
            with self.subTest(name=name,raw=raw[:30]),mock.patch.object(p.original,'allowed_path',p.allowed):
                with self.assertRaises(ValueError):p.validate(p.REPORTS+name,raw)
        self.assertEqual(p.original.AGGREGATE_BYTES,2*1024**2)
        self.assertEqual(p.original.FILE_BYTES,131072)

    def test_private_unicode_nested_and_child_stderr_frames_rejected_across_formats(self):
        frame=br'{"ki\u006ed":"PRIVATE_CHILD_STD\u0045RR","base64":"SYNTHETIC"}'
        examples=(('a.JSON',frame),('a.txt',b'INERT\n'+frame+b'\n'),
                  ('a.md',bytes([96])*3+b'json '+frame+b' '+bytes([96])*3),
                  ('a.json',json.dumps({'evidence':json.dumps({'raw_mountinfo':'SYNTHETIC'})}).encode()))
        for name,raw in examples:
            with self.subTest(name=name),mock.patch.object(p.original,'allowed_path',p.allowed):
                with self.assertRaises(ValueError):p.validate(p.REPORTS+name,raw)

    def test_exact_base_and_policies_delegate_to_original_full_payload_audit(self):
        before=(p.original.allowed_path,p.original.validate_payload)
        observed=[]
        def original_audit(repo,base):
            observed.append((repo,base,p.original.allowed_path,p.original.validate_payload))
            return {'status':'SYNTHETIC_DELEGATION_ONLY'}
        with mock.patch.object(p.original,'audit',side_effect=original_audit):
            self.assertEqual(p.audit('SYNTHETIC_REPO'),{'status':'SYNTHETIC_DELEGATION_ONLY'})
        self.assertEqual(observed,[('SYNTHETIC_REPO',p.BASE,p.allowed,p.validate)])
        self.assertIs(p.original.allowed_path,before[0])
        self.assertIs(p.original.validate_payload,before[1])

    def test_no_general_runtime_science_or_old_evidence_delta(self):
        forbidden=(p.PREFIX+'backend.py',p.PREFIX+'worker.py',p.PREFIX+'config/fixture_profile.json',
                   p.PREFIX+'config/build_profile.json',
                   'simulation/hh_signal/final_closure/integration_runtime/approval.py',
                   'simulation/hh_signal/final_closure/integration_runtime/route_a.py',
                   'reports/phase7i_resource_closure/REPORT.md',
                   'reports/phase7i_namespace_storage_recovery/status.json')
        for path in forbidden:
            with self.subTest(path=path):self.assertFalse(p.allowed(path))

    def test_offline_audit_rejects_canonical_kernel_paths_for_audited_events(self):
        from simulation.hh_signal.final_closure.resource_closure import offline_regression as r
        isolated={key:([] if isinstance(value,list) else 0) for key,value in r.COUNTS.items()}
        with mock.patch.dict(r.COUNTS,isolated,clear=True):
            for event in ('open','os.listdir','os.scandir'):
                for path in ('/proc/self/status','/sys//fs/cgroup/cpu.stat',
                             '/tmp/../proc/self/mountinfo','/tmp/../sys/fs/cgroup/cpu.max'):
                    args=(path,'r',0) if event=='open' else (path,)
                    with self.subTest(event=event,path=path):
                        with self.assertRaisesRegex(RuntimeError,'OFFLINE_FORBIDDEN'):
                            r.audit(event,args)
            self.assertEqual(len(r.COUNTS['forbidden_attempts']),12)

    def test_offline_audit_negative_events_are_synthetic_not_native_dispatch(self):
        from simulation.hh_signal.final_closure.resource_closure import offline_regression as r
        isolated={key:([] if isinstance(value,list) else 0) for key,value in r.COUNTS.items()}
        cases=(('subprocess.Popen',('/usr/bin/python3',['python3','-V'],None,None)),
               ('os.system',('SYNTHETIC_COMMAND_NEVER_EXECUTED',)),
               ('os.fork',()),('os.killpg',(999999,9)),('fcntl.ioctl',(9,0,None)),
               ('ctypes.dlopen',('SYNTHETIC_LIBRARY_NEVER_OPENED',)),
               ('import',('madgraph.interface',None,None,None,None)))
        with mock.patch.dict(r.COUNTS,isolated,clear=True):
            for event,args in cases:
                with self.subTest(event=event),self.assertRaisesRegex(RuntimeError,'OFFLINE_FORBIDDEN'):
                    r.audit(event,args)
            self.assertEqual(len(r.COUNTS['forbidden_attempts']),len(cases))

    def test_deliberately_skipped_synthetic_suite_cannot_be_offline_pass(self):
        from simulation.hh_signal.final_closure.resource_closure import offline_regression as r
        class DeliberateSkip(unittest.TestCase):
            def runTest(self):raise unittest.SkipTest('SYNTHETIC_NEGATIVE_ONLY')
        isolated={key:([] if isinstance(value,list) else 0) for key,value in r.COUNTS.items()}
        suite=unittest.TestSuite([DeliberateSkip()])
        with mock.patch.dict(r.COUNTS,isolated,clear=True), \
             mock.patch.object(r,'snapshot',return_value=[]), \
             mock.patch.object(r.sys,'addaudithook'), \
             mock.patch.object(r.unittest.TestLoader,'loadTestsFromNames',return_value=suite):
            receipt,selected,log=r.run()
        self.assertEqual(receipt['skipped'],1)
        self.assertEqual(receipt['status'],'FAIL_OFFLINE')

if __name__=='__main__':unittest.main()
