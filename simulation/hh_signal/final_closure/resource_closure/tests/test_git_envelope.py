"""Nonphysical Git-envelope adapter tests; every process/timer/resource call mocked."""
from contextlib import contextmanager, ExitStack
from pathlib import Path
from types import SimpleNamespace
import signal
import subprocess
import unittest
from unittest.mock import Mock, patch
from simulation.hh_signal.final_closure.integration_runtime import git_precheck as g
from simulation.hh_signal.final_closure.integration_runtime import contract
from simulation.hh_signal.final_closure.resource_closure import job_envelope as e

GROUP='/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/atlas-hh-phase7i-mock.service'

class Stream:
    def __init__(self,fd):self.fd=fd;self.closed=False
    def fileno(self):return self.fd
    def close(self):self.closed=True

class Child:
    pid=987654321
    returncode=None
    def __init__(self,stdin):
        self.stdout=Stream(101);self.stderr=Stream(102)
        self.stdin=Stream(103) if stdin==subprocess.PIPE else None
        self.wait_calls=[]
    def wait(self,timeout):
        self.wait_calls.append(timeout)
        if self.returncode is None:self.returncode=-9
        return self.returncode

class Selector:
    def __init__(self):self.items={};self.closed=False
    def register(self,stream,event,name):
        self.items[stream.fd]=SimpleNamespace(fileobj=stream,data=name)
    def unregister(self,stream):self.items.pop(stream.fd,None)
    def get_map(self):return self.items
    def select(self,timeout):return [(v,0) for v in list(self.items.values())]
    def close(self):self.closed=True

def chunks(data):
    return [data[i:i+4096] for i in range(0,len(data),4096)]+[b'']

@contextmanager
def borrowed():
    state=e.EnvelopeState(1,GROUP,987654321)
    p=e.PeriodicEnvelope(state,Mock(side_effect=AssertionError('UNREVIEWED_CGROUP_READ')))
    p.owned=True
    with ExitStack() as stack:
        stack.enter_context(patch.object(e,'_OWNER',p))
        timer=stack.enter_context(patch.object(g.signal,'getitimer',return_value=(.005,.01)))
        stack.enter_context(patch.object(g.signal,'getsignal',return_value=p._handler))
        arm=stack.enter_context(patch.object(g.signal,'setitimer',side_effect=AssertionError('REAL_TIMER_MUTATION')))
        handler=stack.enter_context(patch.object(g.signal,'signal',side_effect=AssertionError('REAL_HANDLER_MUTATION')))
        stack.enter_context(patch.object(g.time,'monotonic',return_value=0.))
        stack.enter_context(patch.object(g.time,'process_time',return_value=0.))
        stack.enter_context(patch.dict(g.os.environ,{},clear=True))
        yield p,timer,arm,handler

@contextmanager
def processes(*,stdout=b'',stderr=b'',code=0,wait_pending=False,broken_input=False,
              cleanup_failure=False,wait_error=None):
    child_box=[];written=[];sel=Selector()
    payload={101:chunks(stdout),102:chunks(stderr)}
    getlimit={g.resource.RLIMIT_CPU:(2,2),g.resource.RLIMIT_FSIZE:(65536,65536),
              g.resource.RLIMIT_CORE:(0,0)}
    limit_calls=[]
    def popen(argv,**kw):
        kw['preexec_fn']()
        child=Child(kw['stdin']);child_box.append(child)
        return child
    def read(fd,n):
        assert n<=4096
        return payload[fd].pop(0)
    def write(fd,value):
        assert fd==103 and 0<len(value)<=4096
        if broken_input:raise BrokenPipeError()
        written.append(bytes(value));return len(value)
    def wait4(pid,flags):
        assert pid==987654321
        if wait_error:raise wait_error
        if wait_pending:return 0,0,None
        return pid,0,SimpleNamespace(ru_utime=.01,ru_stime=.02,ru_maxrss=123)
    def killpg(pid,sig):
        assert pid==987654321 and sig==signal.SIGKILL
    with ExitStack() as stack:
        pop=stack.enter_context(patch.object(g.subprocess,'Popen',side_effect=popen))
        stack.enter_context(patch.object(g.selectors,'DefaultSelector',return_value=sel))
        stack.enter_context(patch.object(g.os,'set_blocking'))
        stack.enter_context(patch.object(g.os,'read',side_effect=read))
        stack.enter_context(patch.object(g.os,'write',side_effect=write))
        stack.enter_context(patch.object(g.os,'wait4',side_effect=wait4))
        stack.enter_context(patch.object(g.os,'waitstatus_to_exitcode',return_value=code))
        kill=stack.enter_context(patch.object(g.os,'killpg',side_effect=killpg))
        stack.enter_context(patch.object(g.os,'sysconf',return_value=100))
        stack.enter_context(patch.object(g.Path,'read_text',return_value='987654321 (fixture) '+' '.join(['0']*25)))
        stack.enter_context(patch.object(g.resource,'getrlimit',side_effect=lambda k:getlimit[k]))
        stack.enter_context(patch.object(g.resource,'setrlimit',side_effect=lambda k,v:limit_calls.append((k,v))))
        temp=stack.enter_context(patch.object(g.tempfile,'TemporaryFile',side_effect=AssertionError('BORROWED_PATH_MUST_NOT_CREATE_OUTPUT_FILE')))
        if cleanup_failure:stack.enter_context(patch.object(Child,'wait',side_effect=subprocess.TimeoutExpired('mock',3)))
        yield SimpleNamespace(children=child_box,written=written,selector=sel,limits=limit_calls,
                              kill=kill,popen=pop,temp=temp)

class GitEnvelopeTests(unittest.TestCase):
    def test_default_still_refuses_an_existing_timer(self):
        with patch.object(g.signal,'getitimer',return_value=(.005,.01)), \
             patch.object(g.signal,'signal') as handler,patch.object(g.signal,'setitimer') as timer:
            with self.assertRaisesRegex(g.GitPrecheckError,'EXISTING_WALL_WATCHDOG'):
                with g.GitGuard('/mock'):pass
            handler.assert_not_called();timer.assert_not_called()

    def test_fake_outer_or_subclass_is_not_an_approved_periodic_envelope(self):
        class Other(e.PeriodicEnvelope):pass
        for value in [object(),Mock(),object.__new__(Other)]:
            with self.subTest(value=type(value).__name__),patch.object(g.signal,'signal') as handler, \
                 patch.object(g.signal,'setitimer') as timer:
                with self.assertRaisesRegex(g.GitPrecheckError,'UNREVIEWED_OUTER_WATCHDOG'):
                    with g.GitGuard('/mock',outer_watchdog=value):pass
                handler.assert_not_called();timer.assert_not_called()

    def test_borrowed_timer_is_never_paused_rearmed_or_restored(self):
        with borrowed() as (p,timer,arm,handler):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:guard.check()
            self.assertGreaterEqual(timer.call_count,2)
            arm.assert_not_called();handler.assert_not_called()

    def test_borrowed_timer_is_untouched_when_git_scope_raises(self):
        with borrowed() as (p,timer,arm,handler):
            with self.assertRaisesRegex(ValueError,'FIXTURE'):
                with g.GitGuard('/mock',outer_watchdog=p):raise ValueError('FIXTURE')
            arm.assert_not_called();handler.assert_not_called()

    def test_borrow_rejects_inactive_or_foreign_timer(self):
        for value in [(0.,.01),(.005,0.),(.1,.01)]:
            with self.subTest(timer=value),borrowed() as (p,timer,arm,handler):
                timer.return_value=value
                with self.assertRaises(e.EnvelopeAbort):
                    with g.GitGuard('/mock',outer_watchdog=p):pass
                arm.assert_not_called();handler.assert_not_called()

    def test_borrow_rejects_changed_handler_or_owner(self):
        for change in ['handler','owner']:
            with self.subTest(change=change),borrowed() as (p,timer,arm,handler):
                with patch.object(g.signal,'getsignal',return_value=None) if change=='handler' else patch.object(e,'_OWNER',None):
                    with self.assertRaises(e.EnvelopeAbort):
                        with g.GitGuard('/mock',outer_watchdog=p):pass
                arm.assert_not_called();handler.assert_not_called()

    def test_owner_is_revalidated_during_each_check(self):
        with borrowed() as (p,timer,arm,handler):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                timer.return_value=(0.,0.)
                with self.assertRaises(e.EnvelopeAbort):guard.check()
            arm.assert_not_called();handler.assert_not_called()

    def test_original_git_wall_and_cpu_checks_still_apply(self):
        for kind in ['wall','cpu']:
            with self.subTest(kind=kind),borrowed() as (p,timer,arm,handler):
                with g.GitGuard('/mock',outer_watchdog=p) as guard:
                    if kind=='cpu':guard.child_cpu=31.
                    else:guard.start=-181.
                    with self.assertRaisesRegex(g.GitPrecheckError,'GIT_PREFLIGHT_'):
                        guard.check()

    def test_child_limits_never_raise_inherited_finite_soft_or_hard(self):
        inputs={g.resource.RLIMIT_CPU:(1,2),g.resource.RLIMIT_FSIZE:(4096,65536),g.resource.RLIMIT_CORE:(0,0)}
        with patch.object(g.resource,'getrlimit',side_effect=lambda k:inputs[k]),patch.object(g.resource,'setrlimit') as setlimit:
            g.GitGuard.child_limits(30)
        self.assertEqual([x.args for x in setlimit.call_args_list],[
            (g.resource.RLIMIT_CPU,(1,1)),(g.resource.RLIMIT_FSIZE,(4096,4096)),(g.resource.RLIMIT_CORE,(0,0))])

    def test_unlimited_parent_keeps_original_configured_child_caps(self):
        with patch.object(g.resource,'getrlimit',return_value=(g.resource.RLIM_INFINITY,g.resource.RLIM_INFINITY)), \
             patch.object(g.resource,'setrlimit') as setlimit:
            g.GitGuard.child_limits(17)
        self.assertEqual([x.args for x in setlimit.call_args_list],[
            (g.resource.RLIMIT_CPU,(17,17)),(g.resource.RLIMIT_FSIZE,(g.OUTPUT_BYTES,g.OUTPUT_BYTES)),(g.resource.RLIMIT_CORE,(0,0))])

    def test_full_git_output_larger_than_inherited_fsize_uses_bounded_ram(self):
        data=b'H tracked/path.py\0'*12000
        self.assertGreater(len(data),65536)
        with borrowed() as (p,*_),processes(stdout=data) as proc:
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                self.assertEqual(guard.git('ls-files','-v','-z'),data)
            self.assertEqual(guard.records[-1]['capture_mode'],'BOUNDED_PIPE_RAM')
            self.assertEqual(guard.records[-1]['stdout_bytes'],len(data))
            self.assertEqual(proc.limits,[(g.resource.RLIMIT_CPU,(2,2)),(g.resource.RLIMIT_FSIZE,(65536,65536)),(g.resource.RLIMIT_CORE,(0,0))])
            proc.temp.assert_not_called();self.assertTrue(proc.selector.closed)
            self.assertTrue(proc.children[0].stdout.closed and proc.children[0].stderr.closed)
            proc.kill.assert_called_once()

    def test_exact_output_cap_is_rejected_without_retaining_more_than_cap(self):
        for stream in ['stdout','stderr']:
            with self.subTest(stream=stream),borrowed() as (p,*_),processes(**{stream:b'x'*g.OUTPUT_BYTES}) as proc:
                with g.GitGuard('/mock',outer_watchdog=p) as guard:
                    with self.assertRaisesRegex(g.GitPrecheckError,'GIT_OUTPUT_CAP'):
                        guard.git('status','--porcelain')
                self.assertEqual(guard.records[-1][stream+'_bytes'],g.OUTPUT_BYTES)
                self.assertTrue(guard.records[-1]['group_cleanup'])
                self.assertTrue(proc.selector.closed);proc.kill.assert_called_once()

    def test_nonempty_stderr_is_rejected_and_diagnostic_stays_bounded(self):
        with borrowed() as (p,*_),processes(stderr=b'warning'*200) as proc:
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_UNEXPECTED_DIAGNOSTIC'):
                    guard.git('status')
            self.assertLessEqual(len(guard.records[-1]['stderr_excerpt']),512)

    def test_failed_git_exit_is_not_promoted_to_success(self):
        with borrowed() as (p,*_),processes(stdout=b'partial',code=7):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_SUBPROCESS_FAILURE:status:7'):
                    guard.git('status')
            self.assertEqual(guard.records[-1]['exit'],7)

    def test_stdin_is_incremental_and_complete_while_outputs_are_drained(self):
        data=b'reviewed:source.py\n'*3000
        with borrowed() as (p,*_),processes(stdout=b'exact blob') as proc:
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                self.assertEqual(guard.git('cat-file','--batch',stdin_bytes=data),b'exact blob')
            self.assertEqual(b''.join(proc.written),data)
            self.assertGreater(len(proc.written),1)
            self.assertTrue(proc.children[0].stdin.closed)
            self.assertEqual(guard.records[-1]['stdin_bytes'],len(data))

    def test_stdin_cap_rejects_before_any_process(self):
        with borrowed() as (p,*_),processes() as proc:
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_INPUT_CAP'):
                    guard.git('cat-file','--batch',stdin_bytes=b'x'*65537)
            proc.popen.assert_not_called()

    def test_broken_input_pipe_is_fail_closed_with_cleanup(self):
        with borrowed() as (p,*_),processes(broken_input=True) as proc:
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_INPUT_CLOSED_BEFORE_COMPLETE'):
                    guard.git('cat-file','--batch',stdin_bytes=b'exact request')
            self.assertTrue(proc.children[0].stdin.closed)
            proc.kill.assert_called_once()

    def test_wait_error_keeps_original_reason_and_closes_streams(self):
        for cleanup_failure in (False,True):
            with self.subTest(cleanup_failure=cleanup_failure),borrowed() as (p,*_), \
                 processes(wait_error=OSError('WAIT_ERROR'),cleanup_failure=cleanup_failure) as proc:
                with g.GitGuard('/mock',outer_watchdog=p) as guard:
                    with self.assertRaisesRegex(OSError,'WAIT_ERROR'):guard.git('status')
                self.assertEqual(guard.records[-1]['reason'],'WAIT_ERROR')
                self.assertEqual(guard.records[-1]['group_cleanup'],not cleanup_failure)
                self.assertTrue(proc.children[0].stdout.closed and proc.children[0].stderr.closed)
                proc.kill.assert_called_once()

    def test_command_timeout_still_kills_and_reaps_group(self):
        with borrowed() as (p,*_),processes(wait_pending=True) as proc:
            with g.GitGuard('/mock',outer_watchdog=p,command=.1) as guard:
                guard.check=Mock()
                with patch.object(g.time,'monotonic',side_effect=[0.,.2,.3,.4,.5]):
                    with self.assertRaisesRegex(g.GitPrecheckError,'GIT_COMMAND_TIMEOUT'):
                        guard.git('rev-parse','HEAD')
            row=guard.records[-1]
            self.assertTrue(row['timed_out'] and row['group_cleanup'])
            proc.kill.assert_called_once();self.assertEqual(proc.children[0].wait_calls,[3])

    def test_cleanup_failure_never_yields_a_successful_git_result(self):
        with borrowed() as (p,*_),processes(stdout=b'complete',cleanup_failure=True):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_GROUP_CLEANUP_FAILED'):
                    guard.git('status')
            self.assertFalse(guard.records[-1]['group_cleanup'])
            self.assertEqual(guard.records[-1]['cleanup_error'],'TimeoutExpired')

    def test_fd_cleanup_failure_is_unknown_and_preserves_original_failure(self):
        original_close=Stream.close
        def close(stream):
            if stream.fd==101:raise OSError('FD_CLOSE_ERROR')
            return original_close(stream)
        with borrowed() as (p,*_),processes(wait_error=OSError('ORIGINAL_WAIT_ERROR')) as proc, \
             patch.object(Stream,'close',close):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(OSError,'ORIGINAL_WAIT_ERROR'):guard.git('status')
            row=guard.records[-1]
            self.assertEqual(row['reason'],'ORIGINAL_WAIT_ERROR')
            self.assertFalse(row['group_cleanup'])
            self.assertEqual(row['group_termination'],'CONFIRMED')
            self.assertEqual(row['fd_cleanup'],'UNKNOWN')
            self.assertEqual(row['fd_cleanup_errors'],['OSError'])
            self.assertFalse(proc.children[0].stdout.closed)

    def test_successful_capture_plus_fd_close_error_is_never_pass(self):
        original_close=Stream.close;count=[0]
        def close(stream):
            if stream.fd==101:
                count[0]+=1
                if count[0]==1:return
                raise OSError('FINAL_FD_CLOSE_ERROR')
            return original_close(stream)
        with borrowed() as (p,*_),processes(stdout=b'complete') as proc,patch.object(Stream,'close',close):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_GROUP_CLEANUP_FAILED'):
                    guard.git('status')
            self.assertEqual(guard.records[-1]['fd_cleanup'],'UNKNOWN')
            self.assertFalse(guard.records[-1]['group_cleanup'])

    def test_selector_close_failure_is_unknown_and_cannot_mask_original_error(self):
        for original_error in (None,OSError('ORIGINAL_WAIT_ERROR')):
            with self.subTest(original_error=original_error),borrowed() as (p,*_), \
                 processes(stdout=b'complete',wait_error=original_error), \
                 patch.object(Selector,'close',side_effect=OSError('SELECTOR_CLOSE_ERROR')):
                with g.GitGuard('/mock',outer_watchdog=p) as guard:
                    error=OSError if original_error else g.GitPrecheckError
                    text='ORIGINAL_WAIT_ERROR' if original_error else 'GIT_GROUP_CLEANUP_FAILED'
                    with self.assertRaisesRegex(error,text):guard.git('status')
                row=guard.records[-1]
                self.assertEqual(row['selector_cleanup'],'UNKNOWN')
                self.assertEqual(row['selector_cleanup_error'],'OSError')
                self.assertFalse(row['group_cleanup'])
                if original_error:self.assertEqual(row['reason'],'ORIGINAL_WAIT_ERROR')

    def test_invalid_or_oversized_read_is_rejected_before_buffer_mutation(self):
        for value in ('text',bytearray(b'data'),memoryview(b'data'),b'x'*4097):
            with self.subTest(value=type(value).__name__),borrowed() as (p,*_),processes(), \
                 patch.object(g.os,'read',return_value=value):
                with g.GitGuard('/mock',outer_watchdog=p) as guard:
                    with self.assertRaisesRegex(g.GitPrecheckError,'INVALID_GIT_PIPE_READ'):
                        guard.git('status')
                self.assertEqual(guard.records[-1]['stdout_bytes'],0)
                self.assertEqual(guard.records[-1]['stderr_bytes'],0)

    def test_zero_malformed_or_oversized_write_is_rejected_immediately(self):
        for value in (0,-1,True,1.5,3):
            with self.subTest(value=value),borrowed() as (p,*_),processes(), \
                 patch.object(g.os,'write',return_value=value):
                with g.GitGuard('/mock',outer_watchdog=p) as guard:
                    with self.assertRaisesRegex(g.GitPrecheckError,'INVALID_GIT_PIPE_WRITE'):
                        guard.git('cat-file','--batch',stdin_bytes=b'ab')
                self.assertTrue(guard.records[-1]['group_cleanup'])

    def test_valid_short_writes_preserve_all_requested_stdin_bytes(self):
        written=[]
        def short_write(fd,data):
            amount=min(7,len(data));written.append(data[:amount]);return amount
        with borrowed() as (p,*_),processes(stdout=b'blob'),patch.object(g.os,'write',side_effect=short_write):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                self.assertEqual(guard.git('cat-file','--batch',stdin_bytes=b'exact bytes'*100),b'blob')
        self.assertEqual(b''.join(written),b'exact bytes'*100)

    def test_kill_failure_still_waits_and_preserves_original_kill_exception(self):
        failure=PermissionError('KILL_DENIED')
        child=SimpleNamespace(pid=987654321,wait=Mock(return_value=0))
        with patch.object(g.os,'killpg',side_effect=failure):
            with self.assertRaisesRegex(PermissionError,'KILL_DENIED') as caught:
                g.GitGuard.kill(child)
        self.assertIs(caught.exception,failure)
        child.wait.assert_called_once_with(timeout=3)

    def test_kill_and_wait_failure_keep_kill_primary_and_cleanup_unknown(self):
        failure=PermissionError('KILL_DENIED')
        wait_failure=subprocess.TimeoutExpired('mock',3)
        child=SimpleNamespace(pid=987654321,wait=Mock(side_effect=wait_failure))
        with patch.object(g.os,'killpg',side_effect=failure):
            with self.assertRaisesRegex(PermissionError,'KILL_DENIED') as caught:
                g.GitGuard.kill(child)
        self.assertIs(caught.exception,failure)
        self.assertEqual(caught.exception.git_wait_error,'TimeoutExpired')
        child.wait.assert_called_once_with(timeout=3)
        with borrowed() as (p,*_),processes(stdout=b'complete',cleanup_failure=True), \
             patch.object(g.os,'killpg',side_effect=PermissionError('KILL_DENIED')):
            with g.GitGuard('/mock',outer_watchdog=p) as guard:
                with self.assertRaisesRegex(g.GitPrecheckError,'GIT_GROUP_CLEANUP_FAILED'):
                    guard.git('status')
            row=guard.records[-1]
            self.assertFalse(row['group_cleanup'])
            self.assertEqual(row['group_termination'],'UNKNOWN')
            self.assertEqual(row['cleanup_error'],'PermissionError')
            self.assertEqual(row['cleanup_reason'],'KILL_DENIED')
            self.assertEqual(row['cleanup_wait_error'],'TimeoutExpired')

    def test_default_check_revision_does_not_introduce_an_outer_argument(self):
        result={'critical_source_sha256':{'source.py':'f'*64}}
        with patch.object(g,'verify_checkout',return_value=result) as verify:
            contract.check_revision('a'*40)
        self.assertEqual(verify.call_args.kwargs,{})

    def test_full_check_revision_preserves_full_source_callable_and_passes_exact_outer(self):
        from simulation.hh_signal.final_closure.integration_runtime import route_a
        p=object.__new__(e.PeriodicEnvelope)
        def verify(repo,revision,required,physics,physics_sha,**kw):
            self.assertEqual(required(),['source.py',contract.RECOVERY_METADATA])
            self.assertEqual(physics_sha,contract.PHYSICS_SHA)
            self.assertIs(kw['guard_options']['outer_watchdog'],p)
            return {'critical_source_sha256':{'source.py':'f'*64}}
        with patch.object(route_a,'full_sources',return_value=[{'path':'source.py'}]) as full, \
             patch.object(g,'verify_checkout',side_effect=verify):
            result=contract.check_revision('a'*40,full=True,outer_watchdog=p)
        full.assert_called_once()
        self.assertEqual(result['source_identity'],[{'path':'source.py','sha256':'f'*64}])

if __name__=='__main__':unittest.main()
