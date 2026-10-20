"""Offline policy/negative tests. No service, compiler, or human approval."""
import copy, json, os, tempfile, unittest
from pathlib import Path
from unittest import mock
from .. import backend as b


class BackendPolicyTests(unittest.TestCase):
    def test_profiles_are_exact_and_typed(self):
        self.assertEqual(b.load_profile(), b.PROFILE_FIXTURE)
        self.assertEqual(b.load_profile('BUILD_ONLY'), b.PROFILE_BUILD)
        for key, value in b.PROFILE_FIXTURE.items():
            altered = copy.deepcopy(b.PROFILE_FIXTURE)
            altered[key] = None
            with self.subTest(key=key), mock.patch.object(b.json, 'loads', return_value=altered):
                with self.assertRaisesRegex(ValueError, 'RESOURCE_PROFILE_DRIFT'):
                    b.load_profile()
        altered = dict(b.PROFILE_FIXTURE, max_tasks=True)
        with mock.patch.object(b.json, 'loads', return_value=altered):
            with self.assertRaisesRegex(ValueError, 'RESOURCE_PROFILE_DRIFT'):
                b.load_profile()

    def test_bounded_profile_includes_both_tmpfs_index_and_metadata(self):
        p = b.load_profile()
        disk = (p['work_tmpfs_bytes']+p['tmp_tmpfs_bytes']+
                (p['artifact_chunks']+1+2)*p['per_regular_file_bytes']+
                p['host_metadata_files']*p['host_metadata_bytes']+p['host_allocation_granule_bytes']+
                p['campaign_lock_allocated_reserve_bytes'])
        self.assertEqual(b.profile_bounds(p)['maximum_data_disk_bytes'], disk)
        for mode in ('fixture', 'BUILD_ONLY'):
            p = b.load_profile(mode); bounds = b.profile_bounds(p)
            self.assertLess(bounds['maximum_data_disk_bytes'], p['aggregate_disk_bytes'])
            self.assertLess(bounds['nominal_kernel_CPU_upper_seconds'], p['aggregate_CPU_seconds'])
        self.assertEqual(b.PROFILE_BUILD['aggregate_CPU_seconds'], 14400)
        self.assertEqual(b.PROFILE_BUILD['aggregate_wall_seconds'], 14400)
        self.assertEqual(b.PROFILE_BUILD['aggregate_disk_bytes'], 5*1024**3)

    def test_mounts_cannot_shadow_tmpfs_or_expose_host_tmp(self):
        for mode in ('fixture', 'BUILD_ONLY'):
            props = b.properties('/home/btu/simulations/hh_phase7i_resource_closure/test_01', mode)
            mounts = [v for v in props if v.startswith('TemporaryFileSystem=')]
            self.assertEqual(len(mounts), 2)
            self.assertTrue(any(v.startswith('TemporaryFileSystem=/tmp:') and 'noexec' in v for v in mounts))
            work = next(v for v in mounts if '/work:' in v)
            self.assertEqual('noexec' in work, mode == 'fixture')
            self.assertFalse(any(v.startswith('ReadWritePaths=') or v.startswith('BindPaths=') for v in props))
            self.assertIn('ProtectSystem=strict', props)
            self.assertIn('ProtectHome=read-only', props)
            self.assertIn('MemorySwapMax=0', props)
            self.assertIn('KillMode=control-group', props)
            self.assertIn('OOMPolicy=kill', props)
            self.assertIn('TasksMax=16', props)
            self.assertIn('CPUAffinity='+str(min(os.sched_getaffinity(0))), props)

    def test_fixed_openfile_transport_only(self):
        props = b.properties('/home/btu/simulations/hh_phase7i_resource_closure/test_01')
        opened = [v for v in props if v.startswith('OpenFile=')]
        self.assertEqual(len(opened), 4)
        self.assertEqual([v.split(':')[-2] for v in opened], ['chunk_00', 'chunk_01', 'index', 'campaign_lock'])
        self.assertFalse(any('tty' in v for v in opened))
        self.assertFalse(any('graceful' in v or 'truncate' in v or 'append' in v for v in opened))

    def test_no_arbitrary_commands_or_cases(self):
        unit = 'atlas-hh-phase7i-resource-'+'a'*32+'.service'
        command = b.fixed_command('normal', '/tmp/PLAN_ONLY', 'fixture', 'b'*64, unit)
        self.assertEqual(command[-10:], ['/usr/bin/python3', '-I', '-B', str(b.HERE/'worker.py'),
                                        '--mode', 'fixture', '--case', 'normal', '--source-identity', 'b'*64])
        for case in ('', '/bin/sh', 'normal;uname', 'physical'):
            with self.subTest(case=case), self.assertRaisesRegex(ValueError, 'UNREVIEWED_FIXTURE'):
                b.fixed_command(case, '/tmp/PLAN_ONLY', 'fixture', 'b'*64, unit)
        with self.assertRaisesRegex(ValueError, 'INVALID_SOURCE_IDENTITY'):
            b.fixed_command('normal', '/tmp/PLAN_ONLY', 'fixture', 'x', unit)
        with self.assertRaisesRegex(ValueError, 'FOREIGN_UNIT'):
            b.fixed_command('normal', '/tmp/PLAN_ONLY', 'fixture', 'b'*64, 'sshd.service')

    def test_future_profile_cannot_use_fixture_launcher(self):
        with mock.patch.object(b.subprocess, 'run') as process, mock.patch.object(Path, 'mkdir') as mkdir:
            for action in (b.start_job, b.run_job):
                with self.assertRaisesRegex(ValueError, 'BUILD_ONLY_REQUIRES_SEPARATE_MANUAL_START_BUILD'):
                    action('normal', '/tmp/NEVER_CREATED', mode='BUILD_ONLY')
            process.assert_not_called(); mkdir.assert_not_called()

    def test_foreign_cgroup_and_units_are_rejected(self):
        unit = 'atlas-hh-phase7i-resource-'+'a'*32+'.service'
        for relative in ('/', '/sys/fs/cgroup', '/user.slice/another.service', '/../init.scope'):
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, 'FOREIGN_CGROUP'):
                b.owned_cgroup(unit, relative)
        with mock.patch.object(b.subprocess, 'run') as process:
            for unit in ('sshd.service', 'init.scope', 'atlas-hh-phase7i-resource-../bad.service'):
                with self.assertRaisesRegex(ValueError, 'FOREIGN_UNIT'):
                    b.kill_owned(unit)
            process.assert_not_called()

    def test_wait_requires_empty_procs_and_unpopulated(self):
        busy = {'cgroup.procs': '', 'cgroup.events': 'populated 1\nfrozen 0\n'}
        empty = {'cgroup.procs': '', 'cgroup.events': 'populated 0\n'}
        path = Path('/FAKE_OWNED_CGROUP')
        with mock.patch.object(b, 'cgroup_read', side_effect=[busy, empty]), \
             mock.patch.object(b, 'kill_owned') as kill, mock.patch.object(b.time, 'sleep'):
            self.assertTrue(b.wait_empty(path, b.time.monotonic()+1)); kill.assert_called_once()
        with mock.patch.object(b, 'cgroup_read', return_value=busy), mock.patch.object(b, 'kill_owned') as kill:
            self.assertFalse(b.wait_empty(path, b.time.monotonic()-1)); kill.assert_not_called()

    def test_fixed_json_never_overwrites_or_exceeds_cap(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'result.json'
            b.new_json(path, {'method_only': True})
            with self.assertRaises(FileExistsError): b.new_json(path, {'changed': True})
            self.assertEqual(json.loads(path.read_text()), {'method_only': True})
            with self.assertRaisesRegex(ValueError, 'HOST_METADATA_BOUND'):
                b.new_json(Path(d)/'failure.json', {'x': 'A'*65536})
            with self.assertRaisesRegex(ValueError, 'HOST_METADATA_PATH_NOT_FIXED'):
                b.new_json(Path(d)/'arbitrary.json', {})
            self.assertFalse((Path(d)/'failure.json').exists())

    def test_source_snapshot_excludes_tests_evidence_and_docs(self):
        snap = b.source_snapshot(); paths = [r['path'] for r in snap['paths']]
        self.assertTrue(any(p.endswith('/backend.py') for p in paths))
        self.assertTrue(any(p.endswith('/integration_runtime/build.py') for p in paths))
        self.assertTrue(any(p.endswith('/config/build_profile.json') for p in paths))
        self.assertTrue(all('/tests/' not in p and '/evidence/' not in p and
                            not Path(p).name.startswith('test_') and not p.endswith('.md') for p in paths))
        self.assertEqual(snap['identity'], b.canonical(snap['paths']))

    def test_case_set_fixed_47_and_zero_physics_counters(self):
        self.assertEqual(len(b.CASES), 47)
        self.assertEqual(len(set(b.CASES)), 47)
        self.assertTrue(all(v == 0 and type(v) is int for v in b.ZERO.values()))

    def test_fixture_profile_type_mutation_rejected_even_when_equal(self):
        changed = dict(b.PROFILE_FIXTURE, new_ME_calls=False)
        self.assertEqual(changed, b.PROFILE_FIXTURE)
        with mock.patch.object(b.json, 'loads', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'RESOURCE_PROFILE_DRIFT'): b.load_profile()

    def test_unsafe_output_and_existing_paths_rejected(self):
        for path in ('relative/path', '/tmp/not_owned', str(Path.home()/'simulations/hh_phase7i_resource_closure'),
                     str(Path.home()/'simulations/hh_phase7i_resource_closure/../foreign')):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'FRESH_REAL_OUTPUT'):
                b.fresh(path)

    def test_source_contains_no_service_execution_at_import(self):
        import ast
        node = ast.parse((b.HERE/'backend.py').read_text())
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
                continue
            for call in (x for x in ast.walk(statement) if isinstance(x, ast.Call)):
                name = ast.unparse(call.func)
                self.assertNotIn(name, ('subprocess.run', 'start_job', 'run_job', 'monitor_job'))

    def test_future_build_unconditionally_blocks_before_tty_or_output(self):
        with mock.patch.object(b, '_current_human_tty') as tty, \
             mock.patch.object(b.subprocess, 'run') as process, mock.patch.object(Path, 'mkdir') as mkdir:
            for revision in ('a'*40, 'not-exact', None):
                with self.subTest(revision=revision), self.assertRaisesRegex(
                        ValueError, 'COMPLETE_CONTROLLER_RESOURCE_ENVELOPE_NOT_IMPLEMENTED'):
                    b.start_build('/NEVER_CREATED', revision)
            tty.assert_not_called(); process.assert_not_called(); mkdir.assert_not_called()

    def test_private_transport_proposal_negative_tty_checks_only(self):
        with mock.patch.object(b, '_current_human_tty', side_effect=OSError('NO_CONTROLLING_TTY')), \
             mock.patch.object(b.subprocess, 'run') as process, mock.patch.object(Path, 'mkdir') as mkdir:
            with self.assertRaisesRegex(OSError, 'NO_CONTROLLING_TTY'):
                b._start_build_transport_proposal('/NEVER_CREATED', 'a'*40)
            process.assert_not_called(); mkdir.assert_not_called()
        with mock.patch.object(b, '_current_human_tty') as tty:
            with self.assertRaisesRegex(ValueError, 'EXACT_REVIEWED_REVISION_REQUIRED'):
                b._start_build_transport_proposal('/NEVER_CREATED', 'not-exact')
            tty.assert_not_called()

    def test_fixture_cannot_receive_manual_tty_transport(self):
        with self.assertRaisesRegex(ValueError, 'HUMAN_TTY_TRANSPORT_FORBIDDEN'):
            b.properties('/tmp/PLAN_ONLY', human_tty={'path': '/dev/pts/0', 'rdev': 1, 'inode': 2})
        self.assertFalse(b.PROFILE_BUILD['formal_build_execution_authorized'])
        self.assertTrue(b.PROFILE_BUILD['formal_build_entrypoint_requires_new_explicit_authorization'])
        self.assertEqual(b.PROFILE_BUILD['RAM_profile_review_status'], 'EXPLICIT_HUMAN_APPROVED_RAM_ONLY')

    def test_explicit_RAM_review_preserves_limits_and_blocks_formal_execution(self):
        for profile, memory in ((b.load_profile('fixture'), 536870912),
                                (b.load_profile('BUILD_ONLY'), 2147483648)):
            self.assertEqual(profile['RAM_profile_review_status'], 'EXPLICIT_HUMAN_APPROVED_RAM_ONLY')
            self.assertEqual(profile['RAM_profile_review_source'],
                             'CURRENT_CHAT_EXPLICIT_USER_RAM_REVIEW_RELAYED_BY_ROOT')
            self.assertEqual(profile['aggregate_memory_bytes'], memory)
            self.assertEqual(profile['per_process_address_space_bytes'], memory)
            self.assertEqual(profile['swap_bytes'], 0)
            self.assertFalse(profile['formal_build_execution_authorized'])
            self.assertIn('FORMAL_BUILD_NOT_AUTHORIZED', profile['RAM_profile_review_execution_limit'])
            self.assertIn('COMPLETE_CONTROLLER_REMAINS_BLOCKED', profile['RAM_profile_review_execution_limit'])

    def test_manual_build_entry_order_and_no_review_creation(self):
        import ast
        tree = ast.parse((b.HERE/'backend.py').read_text())
        start = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == '_start_build_transport_proposal')
        calls = [x for x in ast.walk(start) if isinstance(x, ast.Call)]
        positions = {ast.unparse(x.func): x.lineno for x in calls}
        self.assertLess(positions['_current_human_tty'], positions['_start'])
        self.assertNotIn('HumanReview', positions)
        self.assertNotIn('confirm', positions)
        self.assertNotIn('confirm_fd', positions)
        self.assertNotIn('input', positions)

    def test_500_build_records_compact_but_hash_complete_journal(self):
        import hashlib
        rows = [{'kind': 'ATTESTED', 'valid': True}, {'kind': 'BUILD_PREPARE_ENTERED'}]
        rows += [{'kind': 'BUILD_CHECKPOINT', 'command_index': i, 'detail': 'X'*128}
                 for i in range(500)]
        rows += [{'kind': 'BUILD_ONLY_COMPLETE', 'native_zero_ME_verified': True,
                  'new_ME_calls': 0, 'new_integrals': 0, 'retained_physical_events': 0}]
        encoded = b''.join(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()+b'\n' for row in rows)
        self.assertGreater(len(encoded), 65536)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'stdout.log'; path.write_bytes(encoded)
            summary = b.build_record_summary(path, len(encoded))
            self.assertEqual(summary['record_count'], 503)
            self.assertEqual(summary['canonical_JSONL_sha256'], hashlib.sha256(encoded).hexdigest())
            self.assertEqual([row['kind'] for row in summary['records']],
                             ['ATTESTED', 'BUILD_CHECKPOINT', 'BUILD_ONLY_COMPLETE'])
            self.assertEqual(summary['records'][1]['command_index'], 499)
            self.assertTrue(summary['build_entered']); self.assertTrue(summary['zero_ME_verified'])
            b.new_json(Path(d)/'result.json', summary)
            self.assertLess((Path(d)/'result.json').stat().st_size, 65536)
            self.assertEqual(path.read_bytes(), encoded)

    def test_build_summary_never_invents_success_or_raises_caps(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'stdout.log'
            path.write_text(json.dumps({'kind': 'FAILED', 'reason': 'method only'})+'\n')
            summary = b.build_record_summary(path, 65536)
            self.assertFalse(summary['build_entered']); self.assertFalse(summary['zero_ME_verified'])
            self.assertEqual(summary['records'][0]['kind'], 'FAILED')
            with self.assertRaisesRegex(ValueError, 'HOST_STREAM_BOUND'):
                b.build_record_summary(path, 1)
            path.write_text(json.dumps({'kind': 'BUILD_CHECKPOINT', 'detail': 'X'*9000})+'\n')
            with self.assertRaisesRegex(ValueError, 'PAYLOAD_RECORD_BOUND'):
                b.build_record_summary(path, 65536)

    def test_wide_future_records_project_without_losing_raw_proof(self):
        import hashlib
        rows = [dict(kind='ATTESTED', valid=True, detail='X'*7500),
                dict(kind='BUILD_CHECKPOINT', command_index=499, detail='Y'*7500),
                dict(kind='BUILD_ONLY_COMPLETE', native_zero_ME_verified=True,
                     new_ME_calls=0, new_integrals=0, retained_physical_events=0, detail='Z'*7500)]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'stdout.log'
            raw = b''.join(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()+b'\n' for row in rows)
            path.write_bytes(raw); summary = b.build_record_summary(path, 65536)
            self.assertTrue(summary['build_entered']); self.assertTrue(summary['zero_ME_verified'])
            self.assertEqual(summary['canonical_JSONL_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(len(summary['records']), 3)
            for original, projected in zip(rows, summary['records']):
                self.assertLessEqual(len(json.dumps(projected, sort_keys=True, separators=(',', ':')).encode()), 2048)
                self.assertTrue(projected['metadata_projection_only'])
                self.assertEqual(projected['full_record_sha256'], b.canonical(original))
            self.assertIs(summary['records'][0]['valid'], True)
            self.assertEqual(summary['records'][1]['command_index'], 499)
            self.assertIs(summary['records'][2]['native_zero_ME_verified'], True)
            self.assertEqual(path.read_bytes(), raw)

    def test_no_me_proof_requires_actual_integer_zero_counter_fields(self):
        base = dict(kind='BUILD_ONLY_COMPLETE', native_zero_ME_verified=True,
                    new_ME_calls=0, new_integrals=0, retained_physical_events=0)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'stdout.log'
            for key in ('new_ME_calls', 'new_integrals', 'retained_physical_events'):
                for value in (None, False, 1, '0'):
                    row = dict(base, **{key: value}); path.write_text(json.dumps(row)+'\n')
                    with self.subTest(key=key, value=value):
                        self.assertFalse(b.build_record_summary(path, 65536)['zero_ME_verified'])
                row = dict(base); row.pop(key); path.write_text(json.dumps(row)+'\n')
                self.assertFalse(b.build_record_summary(path, 65536)['zero_ME_verified'])

    def test_host_allocated_extent_cannot_hide_under_small_logical_size(self):
        import types
        p = b.load_profile()
        fake = types.SimpleNamespace(st_mode=0o100600, st_nlink=1, st_size=0,
                                     st_blocks=(p['per_regular_file_bytes']//512)+1)
        with mock.patch.object(Path, 'lstat', return_value=fake), \
             mock.patch.object(Path, 'is_symlink', return_value=False):
            with self.assertRaisesRegex(ValueError, 'HOST_OUTPUT_ALLOCATED_CAP_EXCEEDED'):
                b._payload_observations(Path('/OFFLINE_FAKE'), p)
        self.assertEqual(b.PROFILE_FIXTURE['host_allocation_granule_bytes'], 4096)
        self.assertEqual(b.PROFILE_BUILD['host_allocation_granule_bytes'], 4096)

    def test_fixed_campaign_mutex_transport_readonly_and_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'.resource_envelope.lock'
            with mock.patch.object(b, 'campaign_lock_path', return_value=path):
                first = b.prepare_campaign_lock(); second = b.prepare_campaign_lock()
                self.assertEqual(first, second)
                self.assertEqual(first['descriptor_access'], 'read-only')
                self.assertEqual(path.stat().st_size, 0)
                self.assertEqual(path.stat().st_nlink, 1)
                self.assertEqual(first['uid'], os.getuid())
                props = b.properties('/tmp/PLAN_ONLY')
                self.assertEqual(props[-1], 'OpenFile='+str(path)+':campaign_lock:read-only')
            path.write_bytes(b'PREEXISTING_WRONG_CONTENT')
            with mock.patch.object(b, 'campaign_lock_path', return_value=path):
                with self.assertRaisesRegex(ValueError, 'CAMPAIGN_LOCK_IDENTITY'):
                    b.prepare_campaign_lock()
            self.assertEqual(path.read_bytes(), b'PREEXISTING_WRONG_CONTENT')

    def test_campaign_mutex_rejects_symlink_and_hardlink(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)/'target'; target.write_bytes(b'')
            path = Path(d)/'.resource_envelope.lock'; path.symlink_to(target)
            with mock.patch.object(b, 'campaign_lock_path', return_value=path):
                with self.assertRaisesRegex(ValueError, 'UNSAFE_CAMPAIGN_LOCK'):
                    b.prepare_campaign_lock()
            path.unlink(); os.link(target, path)
            with mock.patch.object(b, 'campaign_lock_path', return_value=path):
                with self.assertRaisesRegex(ValueError, 'CAMPAIGN_LOCK_IDENTITY'):
                    b.prepare_campaign_lock()
            self.assertEqual(target.stat().st_nlink, 2)
