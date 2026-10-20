"""Publication regression uses isolated temporary Git repositories only."""
import json, os, subprocess, tempfile, unittest
from pathlib import Path
from .. import publication as p

SAFE = p.PREFIX+'example.py'


class PublicationPayloadTests(unittest.TestCase):
    def test_exact_scope_and_utf8_source(self):
        self.assertTrue(p.allowed_path(SAFE))
        for path in p.ADAPTERS | p.WORKFLOWS:
            self.assertTrue(p.allowed_path(path))
        self.assertEqual(p.validate_payload(SAFE, '# harmless source\n'.encode())['bytes'], 18)
        for name in (p.PREFIX+'private/data.json', p.PREFIX+'raw/archive.json',
                     '.local/config.json', 'simulation/hh_signal/final_closure/config/physics_contract.json',
                     p.RUNTIME+'native_checks.f', p.PREFIX+'chunk_00.py', p.PREFIX+'report.pdf',
                     p.PREFIX+'figure.png', p.PREFIX+'events.lhe', p.PREFIX+'archive.tar',
                     p.PREFIX+'../private.json'):
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, 'OUTSIDE_PUBLICATION'):
                p.validate_payload(name, b'text\n')

    def test_exact_campaign_ci_workflow_allowed_without_prefix_relaxation(self):
        path = '.github/workflows/hh_signal_campaign.yml'
        self.assertIn(path, p.WORKFLOWS)
        self.assertEqual(len(p.WORKFLOWS), 4)
        p.validate_payload(path, b'name: source audit fixture\non: pull_request\n')
        for name in ('.github/workflows/unreviewed.yml', '.github/workflows/hh_signal_campaign_extra.yml',
                     '.github/workflows/hh_signal_campaign.yaml', '.github/workflows/private.yml'):
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, 'OUTSIDE_PUBLICATION'):
                p.validate_payload(name, b'name: forbidden workflow fixture\n')

    def test_binary_magic_source_extension_rejected(self):
        for raw in (b'\x7fELFbinary', b'MZbinary', b'PK\x03\x04archive', b'%PDF-1.7',
                    b'\x89PNG\r\n\x1a\n', b'valid\x00binary', b'\xff'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                p.validate_payload(SAFE, raw)
        p.validate_payload(SAFE, b"# Literal test bytes are text: b'\\x7fELF'\n")

    def test_finite_duplicate_free_json_and_case(self):
        p.validate_payload(p.PREFIX+'config/valid.json', b'{"n": 0, "value": null}\n')
        for raw in (b'{"a": NaN}', b'{"a": Infinity}', b'{"a": 1e9999}', b'{"a": 0, "a": 1}'):
            for suffix in ('.json', '.JSON'):
                with self.subTest(raw=raw, suffix=suffix), self.assertRaisesRegex(ValueError, 'INVALID_OR_NONFINITE_JSON'):
                    p.validate_payload(p.PREFIX+'config/bad'+suffix, raw)

    def test_per_file_mode_and_event_payload_limits(self):
        p.validate_payload(SAFE, b'#'+b'A'*(p.FILE_BYTES-2)+b'\n')
        with self.assertRaisesRegex(ValueError, 'PUBLICATION_FILE_CAP'):
            p.validate_payload(SAFE, b'A'*(p.FILE_BYTES+1))
        for mode in ('100755', '120000', '160000'):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'NONREGULAR'):
                p.validate_payload(SAFE, b'text', mode)
        with self.assertRaisesRegex(ValueError, 'RAW_EVENT_PAYLOAD'):
            p.validate_payload(SAFE, b'<event>\n1 2 3\n</event>\n')

    def test_policy_can_scan_its_own_source(self):
        here = Path(p.__file__)
        p.validate_payload(p.PREFIX+'publication.py', here.read_bytes())


class PublicationGitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q', '--initial-branch=main')
        self.git('config', 'user.name', 'Publication Method Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.write('historical.txt', b'PRESERVE HISTORICAL\n')
        self.write('reports/historical.png', b'\x89PNG\r\n\x1a\nBASELINE_FIXTURE_NOT_NEW_PUBLICATION')
        self.git('add', '--all'); self.git('commit', '-q', '-m', 'METHOD ONLY baseline')
        self.base = self.git('rev-parse', 'HEAD').decode().strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE, timeout=10)

    def write(self, name, raw):
        path = self.repo/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        return path

    def commit(self, message):
        self.git('add', '--all'); self.git('commit', '-q', '-m', message)

    def test_allowed_commit_and_index_pass_preserving_baseline_figure(self):
        self.write(SAFE, b'# safe\n'); self.commit('METHOD ONLY source')
        self.write(p.PREFIX+'tests/new_test.py', b'# safe pending index\n'); self.git('add', '--all')
        report = p.audit(self.repo, base=self.base)
        self.assertEqual(report['outgoing_commits'], 1)
        self.assertEqual(report['outgoing_commit_payloads'], 1)
        self.assertEqual(report['changed_index_payloads'], 2)
        self.assertFalse(report['baseline_artifacts_reinterpreted'])
        self.assertLessEqual(len(json.dumps(report).encode()), 65536)

    def test_intermediate_figure_removed_from_final_tree_still_rejected(self):
        name = p.PREFIX+'intermediate.png'
        self.write(name, b'\x89PNG\r\n\x1a\nNOT_A_REAL_FIGURE')
        self.commit('METHOD ONLY forbidden intermediate figure')
        (self.repo/name).unlink(); self.commit('METHOD ONLY remove figure')
        with self.assertRaisesRegex(ValueError, 'OUTSIDE_PUBLICATION'):
            p.audit(self.repo, base=self.base)

    def test_binary_disguised_as_source_is_rejected_in_commit(self):
        self.write(SAFE, b'\x7fELFNOT_EXECUTABLE_FIXTURE'); self.commit('METHOD ONLY binary disguise')
        with self.assertRaisesRegex(ValueError, 'BINARY_MAGIC'):
            p.audit(self.repo, base=self.base)

    def test_private_path_rejected_from_staged_index(self):
        self.write(p.PREFIX+'private/config.json', b'{"private_fixture": true}\n'); self.git('add', '--all')
        with self.assertRaisesRegex(ValueError, 'OUTSIDE_PUBLICATION'):
            p.audit(self.repo, base=self.base)

    def test_historical_deletion_rejected_even_without_new_payload(self):
        (self.repo/'historical.txt').unlink(); self.git('add', '--all')
        with self.assertRaisesRegex(ValueError, 'DELETION_RENAME'):
            p.audit(self.repo, base=self.base)

    def test_symlink_and_executable_modes_rejected(self):
        path = self.repo/SAFE; path.parent.mkdir(parents=True, exist_ok=True); path.symlink_to(self.repo/'historical.txt')
        self.git('add', '--all')
        with self.assertRaisesRegex(ValueError, 'DELETION_RENAME_OR_TYPE|NONREGULAR'):
            p.audit(self.repo, base=self.base)
        self.git('reset', '-q', '--hard', self.base); path.unlink(missing_ok=True)
        self.write(SAFE, b'# executable mode forbidden\n').chmod(0o755); self.git('add', '--all')
        with self.assertRaisesRegex(ValueError, 'NONREGULAR'):
            p.audit(self.repo, base=self.base)

    def test_index_raw_bytes_must_match_worktree(self):
        self.write(SAFE, b'# staged\n'); self.git('add', '--all'); self.write(SAFE, b'# unstaged\n')
        with self.assertRaisesRegex(ValueError, 'INDEX_WORKTREE_RAW_BYTE_MISMATCH'):
            p.audit(self.repo, base=self.base)

    def test_aggregate_all_snapshot_payload_bytes_cannot_exceed_cap(self):
        raw = b'#'+b'A'*(p.FILE_BYTES-2)+b'\n'
        for i in range(17): self.write(p.PREFIX+'test_'+str(i)+'.py', raw)
        self.git('add', '--all')
        with self.assertRaisesRegex(ValueError, 'PUBLICATION_AGGREGATE_CAP'):
            p.audit(self.repo, base=self.base)

    def test_oversized_git_blob_rejected_before_payload_read(self):
        from unittest import mock
        self.write(SAFE, b'A'*(p.FILE_BYTES+1)); self.git('add', '--all')
        original = p.git
        def guarded(repo, *args):
            if args[:2] == ('cat-file', 'blob'):
                self.fail('oversized blob contents must not be read')
            return original(repo, *args)
        with mock.patch.object(p, 'git', side_effect=guarded):
            with self.assertRaisesRegex(ValueError, 'PUBLICATION_FILE_CAP'):
                p.audit(self.repo, base=self.base)
