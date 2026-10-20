import json, unittest
from unittest.mock import patch
from simulation.hh_signal.final_closure.resource_closure import recovery_publication as p


class RecoveryPublicationTests(unittest.TestCase):
    def assert_report_rejected(self, suffix, raw):
        with patch.object(p.original, 'allowed_path', p.allowed):
            with self.assertRaisesRegex(ValueError, 'PRIVATE|RAW_MOUNTINFO|RECURSION_BOUND'):
                p.validate(p.REPORTS + 'synthetic_capture.' + suffix, raw)

    def test_fixed_base(self):
        self.assertEqual(p.BASE, 'b8ae4cc03c0ac408577909847e56f417fc28eba8')

    def test_scope_excludes_science_profiles_and_old_reports(self):
        for path in (p.PREFIX + 'backend.py', p.PREFIX + 'config/fixture_profile.json',
                     'reports/phase7i_resource_closure/full_controller_execution_01.json',
                     'simulation/hh_signal/final_closure/config/physics_contract.json'):
            self.assertFalse(p.allowed(path), path)
        self.assertTrue(p.allowed(p.PREFIX + 'full_controller.py'))
        self.assertTrue(p.allowed(p.REPORTS + 'status.json'))

    def test_private_path_figures_events_binaries_rejected(self):
        for suffix in ('private/a.json', 'a.pdf', 'a.png', 'a.lhe', 'a.root', 'a.exe', 'a.tar'):
            self.assertFalse(p.allowed(p.REPORTS + suffix))

    def test_raw_frame_recursively_rejected(self):
        for row in ({'kind': 'PRIVATE_MOUNTINFO_RAW', 'base64': 'L3Byb2M='},
                    {'nested': [{'kind': 'PRIVATE_MOUNTINFO_RAW'}]},
                    {'raw_mountinfo': 'opaque'}, {'mountinfo_bytes_base64': 'opaque'}):
            with self.assertRaises(ValueError), patch.object(p.original, 'allowed_path', p.allowed):
                p.validate(p.REPORTS + 'capture.json', json.dumps(row).encode())

    def test_raw_mount_line_rejected(self):
        with self.assertRaises(ValueError), patch.object(p.original, 'allowed_path', p.allowed):
            p.validate(p.REPORTS + 'capture.txt', b'31 1 0:1 / /persistent rw - ext4 /dev/sdd rw\n')

    def test_reviewed_projection_hash_and_no_runtime_claim_allowed(self):
        raw = json.dumps({'kind': 'MOUNTINFO_SAFE_PROJECTION', 'raw_sha256': 'a'*64,
                          'kernel_execution': 'NOT_AUTHORIZED', 'rows': []}).encode()
        with patch.object(p.original, 'allowed_path', p.allowed):
            self.assertEqual(p.validate(p.REPORTS + 'projection.json', raw)['bytes'], len(raw))

    def test_all_patched_global_policies_restored_on_failure(self):
        allowed, validate = p.original.allowed_path, p.original.validate_payload
        with self.assertRaises(ValueError):
            p.audit('/not/a/repository')
        self.assertIs(p.original.allowed_path, allowed)
        self.assertIs(p.original.validate_payload, validate)

    def test_uppercase_json_rejects_both_private_protocol_kinds(self):
        for kind in ('PRIVATE_MOUNTINFO_RAW', 'PRIVATE_CHILD_STDERR'):
            with self.subTest(kind=kind):
                self.assert_report_rejected('JSON', json.dumps({'kind': kind, 'base64': 'U1lOVEhFVElD'}).encode())

    def test_text_markdown_jsonl_reject_private_frame_after_safe_record(self):
        for suffix in ('txt', 'md'):
            for kind in ('PRIVATE_MOUNTINFO_RAW', 'PRIVATE_CHILD_STDERR'):
                with self.subTest(suffix=suffix, kind=kind):
                    raw = ('{"kind":"SAFE_METADATA","sha256":"' + 'a'*64 + '"}\n' +
                           json.dumps({'kind': kind, 'base64': 'U1lOVEhFVElD'}) + '\n').encode()
                    self.assert_report_rejected(suffix, raw)

    def test_unicode_escaped_kind_and_value_rejected_in_jsonl_and_fence(self):
        raw = br'{"ki\u006ed":"PRIVATE_MOUNTINFO_R\u0041W","base64":"U1lOVEhFVElD"}'
        for suffix, text in (('txt', b'Synthetic heading\n' + raw + b'\n'),
                             ('md', b'```json\n' + raw + b'\n```\n'),
                             ('md', b'```json ' + raw + b' ```\n')):
            with self.subTest(suffix=suffix):
                self.assert_report_rejected(suffix, text)

    def test_nested_serialized_json_strings_cannot_launder_private_fields(self):
        cases = ({'kind': 'PRIVATE_MOUNTINFO_RAW', 'base64': 'U1lOVEhFVElD'},
                 {'kind': 'PRIVATE_CHILD_STDERR', 'base64': 'U1lOVEhFVElD'},
                 {'raw_mountinfo': 'SYNTHETIC'}, {'mountinfo_bytes_base64': 'U1lOVEhFVElD'})
        for value in cases:
            wrapped = json.dumps({'evidence': json.dumps({'serialized': json.dumps(value)})}).encode()
            with self.subTest(value=value):
                self.assert_report_rejected('json', wrapped)

    def test_nested_raw_mountinfo_line_cannot_be_published_as_json_string(self):
        raw_line = '31 1 0:1 / /synthetic rw - ext4 /dev/synthetic rw\n'
        for value in ({'evidence': raw_line}, {'records': [json.dumps({'line': raw_line})]}):
            with self.subTest(value=value):
                self.assert_report_rejected('json', json.dumps(value).encode())

    def test_report_recursion_depth_is_explicit_fail_closed(self):
        value = {'safe': True}
        for index in range(36):
            value = {'nested': value}
        self.assert_report_rejected('json', json.dumps(value).encode())

    def test_safe_prose_mentions_are_not_actual_private_frames(self):
        raw = b'Policy rejects PRIVATE_MOUNTINFO_RAW and PRIVATE_CHILD_STDERR.\n'
        with patch.object(p.original, 'allowed_path', p.allowed):
            self.assertEqual(p.validate(p.REPORTS + 'policy.md', raw)['bytes'], len(raw))

    def test_patched_audit_uses_fixed_base_and_restores_policies_on_rejection(self):
        before_allowed, before_validate = p.original.allowed_path, p.original.validate_payload
        observed = []
        def rejected_audit(repo, base):
            observed.append((base, p.original.allowed_path, p.original.validate_payload))
            p.original.validate_payload(p.REPORTS + 'synthetic.txt',
                                        b'{"kind":"PRIVATE_CHILD_STDERR","base64":"U1lOVEhFVElD"}\n')
        with patch.object(p.original, 'audit', side_effect=rejected_audit):
            with self.assertRaisesRegex(ValueError, 'PRIVATE'):
                p.audit('SYNTHETIC_REPO_NO_GIT_EXECUTED')
        self.assertEqual(observed, [(p.BASE, p.allowed, p.validate)])
        self.assertIs(p.original.allowed_path, before_allowed)
        self.assertIs(p.original.validate_payload, before_validate)


if __name__ == '__main__':
    unittest.main()
