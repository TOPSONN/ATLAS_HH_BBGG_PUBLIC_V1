"""Pure wiring checks: the new adapter is never allowed to arm live here."""
import stat
import unittest
from types import SimpleNamespace
from unittest import mock
from simulation.hh_signal.final_closure.resource_closure import full_controller as c


class S4ControllerWiringTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNone(c._ACTIVE_ENVELOPE)

    def test_alarm_spans_whole_body_and_both_full_git_checks(self):
        from .test_full_controller import FullControllerMockWorkflow
        case = FullControllerMockWorkflow()
        with case.workflow_fixture() as fixture:
            monitor = c._make_job_envelope.return_value
            def checked(*args, **kwargs):
                self.assertIs(kwargs['outer_watchdog'], monitor)
                self.assertIs(c._ACTIVE_ENVELOPE, monitor)
                self.assertTrue(monitor.arm.called)
                self.assertFalse(monitor.close.called)
                return {'git_preflight':{'status':'PASS','index_sha256':'a'*64,
                    'wall_seconds':.01,'CPU_seconds':.005,'tracked_files':1444,
                    'critical_source_sha256':{'INERT':'b'*64}},
                    'physics_sha256':'c'*64,'source_identity':'d'*64}
            fixture.check.side_effect=checked
            self.assertEqual(c.main(['workflow']),0)
            self.assertEqual(fixture.check.call_count,2)
            monitor.arm.assert_called_once()
            monitor.check_latched.assert_called_once()
            monitor.close.assert_called_once()
            self.assertIsNone(c._ACTIVE_ENVELOPE)

    def test_original_body_error_survives_close_failure(self):
        error=ValueError('ORIGINAL_FAILURE')
        monitor=mock.Mock()
        monitor.close.side_effect=RuntimeError('CLOSE_UNKNOWN')
        @c.monitored_workflow
        def body():raise error
        with mock.patch.object(c,'_make_job_envelope',return_value=monitor), \
             mock.patch.object(c,'emit') as output, \
             mock.patch.object(c.os,'_exit') as terminate:
            with self.assertRaisesRegex(ValueError,'ORIGINAL_FAILURE') as got:body()
        self.assertIs(got.exception,error)
        terminate.assert_called_once_with(126)
        self.assertTrue(output.call_args.args[0]['envelope_close_pending'])
        self.assertEqual(error.envelope_cleanup_status['status'],'UNKNOWN')
        self.assertIsNone(c._ACTIVE_ENVELOPE)

    def test_arm_rejection_never_enters_body(self):
        monitor=mock.Mock();monitor.arm.side_effect=ValueError('ARM_REJECTED')
        body=mock.Mock()
        with mock.patch.object(c,'_make_job_envelope',return_value=monitor), \
             mock.patch.object(c,'emit'):
            with self.assertRaisesRegex(ValueError,'ARM_REJECTED'):
                c.monitored_workflow(body)()
        body.assert_not_called()
        monitor.close.assert_called_once()
        self.assertIsNone(c._ACTIVE_ENVELOPE)

    def test_foreign_or_oversize_cgroup_rejected_before_adapter(self):
        for raw in (b'0::/FOREIGN\n',b'x'*4097):
            with self.subTest(raw_bytes=len(raw)), \
                 mock.patch.object(c.Path,'open',mock.mock_open(read_data=raw)), \
                 mock.patch.object(c.os,'getuid',return_value=1000), \
                 mock.patch.object(c.job_envelope,'FixedCgroupReader') as reader:
                with self.assertRaises(ValueError):c._make_job_envelope(10)
                reader.assert_not_called()

    def test_emergency_callback_only_uses_fixed_self_exit_status(self):
        raw=('0::/user.slice/user-1000.slice/user@1000.service/app.slice/'+c.UNIT+'\n').encode()
        info=SimpleNamespace(st_dev=44,st_ino=55,st_mode=stat.S_IFDIR|0o755)
        with mock.patch.object(c.Path,'open',mock.mock_open(read_data=raw)), \
             mock.patch.object(c.Path,'stat',return_value=info), \
             mock.patch.object(c.os,'getuid',return_value=1000), \
             mock.patch.object(c.os,'getpid',return_value=222), \
             mock.patch.object(c.job_envelope,'EnvelopeState'), \
             mock.patch.object(c.job_envelope,'FixedCgroupReader'), \
             mock.patch.object(c.job_envelope,'PeriodicEnvelope') as make, \
             mock.patch.object(c.os,'_exit') as stop, \
             mock.patch.object(c.os,'write') as output:
            c._make_job_envelope(10)
            callback=make.call_args.kwargs['emergency_stop']
            for code in (124,125,126):callback({'exit_status':code})
            for bad in ({'exit_status':0},{'exit_status':True},{},None):
                callback(bad)
            self.assertEqual(stop.call_args_list,[mock.call(124),mock.call(125),
                mock.call(126),mock.call(126),mock.call(126),mock.call(126),mock.call(126)])
            output.assert_not_called()


    def test_initial_head_borrows_bounded_guard_and_keeps_one_second(self):
        from simulation.hh_signal.final_closure.integration_runtime import git_precheck as g
        monitor=object()
        with mock.patch.object(c,'_ACTIVE_ENVELOPE',monitor), mock.patch.object(g,'GitGuard') as make:
            make.return_value.__enter__.return_value.git.return_value=b'a'*40+b'\n'
            self.assertEqual(c._current_revision(),'a'*40)
            make.assert_called_once_with(c.REPO,wall=1,command=1,status=1,outer_watchdog=monitor)
            make.return_value.__enter__.return_value.git.assert_called_once_with('rev-parse','HEAD')
            make.return_value.__exit__.assert_called_once()

    def test_child_head_uses_one_second_default_bounded_guard(self):
        from simulation.hh_signal.final_closure.integration_runtime import git_precheck as g
        with mock.patch.object(c,'_ACTIVE_ENVELOPE',None),mock.patch.object(g,'GitGuard') as make:
            make.return_value.__enter__.return_value.git.return_value=b'a'*40+b'\n'
            self.assertEqual(c._current_revision(),'a'*40)
            make.assert_called_once_with(c.REPO,wall=1,command=1,status=1,outer_watchdog=None)

    def test_initial_head_rejects_malformed_or_extra_output(self):
        from simulation.hh_signal.final_closure.integration_runtime import git_precheck as g
        for raw in (b'a'*40,b'a'*40+b'\n\n',b' '+b'a'*40+b'\n',b'G'*40+b'\n'):
            with self.subTest(raw=raw),mock.patch.object(g,'GitGuard') as make:
                make.return_value.__enter__.return_value.git.return_value=raw
                with self.assertRaisesRegex(ValueError,'CURRENT_REVISION_ENCODING'):
                    c._current_revision()

    def test_initial_head_failure_has_no_unbounded_fallback(self):
        from simulation.hh_signal.final_closure.integration_runtime import git_precheck as g
        with mock.patch.object(g,'GitGuard') as make,mock.patch.object(c.subprocess,'run') as fallback:
            make.return_value.__enter__.return_value.git.side_effect=g.GitPrecheckError('GIT_OUTPUT_CAP')
            with self.assertRaisesRegex(g.GitPrecheckError,'GIT_OUTPUT_CAP'):c._current_revision()
            fallback.assert_not_called()
            make.return_value.__exit__.assert_called_once()


if __name__ == '__main__':unittest.main()
