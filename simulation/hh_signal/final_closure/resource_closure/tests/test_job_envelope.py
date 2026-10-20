"""Only pure fixtures and mocked timers/kernel/exit; never arm a real timer."""
from __future__ import annotations
import copy
from contextlib import ExitStack
import errno
import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from simulation.hh_signal.final_closure.resource_closure import job_envelope as j

UNIT='atlas-hh-phase7i-s4-capacity-01.service'
GROUP='/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/'+UNIT
ID={'dev':29,'inode':800}
ORIGIN=1_000_000_000


def raw(cpu=10_000, *, empty=False):
    rows={key:(value+'\n').encode() for key,value in j.EFFECTIVE.items()}
    rows.update({'cpu.stat':('usage_usec %d\nuser_usec 7000\nsystem_usec 3000\n'%cpu).encode(),
        'memory.current':b'10000000\n','memory.peak':b'12000000\n',
        'memory.swap.current':b'0\n','memory.events':b''.join((name+' 0\n').encode() for name in j.EVENTS),
        'cgroup.events':('populated %d\nfrozen 0\n'%(not empty)).encode(),
        'cgroup.procs':b'' if empty else b'200\n201\n'})
    return rows


def snapshot(cpu=10_000, *, offset=100, empty=False, pid=200):
    return j.parse_cgroup_raw(raw(cpu,empty=empty),aggregate_cgroup=GROUP,cgroup_identity=ID,
        reader_pid=pid,sample_start_ns=ORIGIN+offset,sample_end_ns=ORIGIN+offset+1)


def manager(**changes):
    props={'Id':UNIT,'InvocationID':'e'*32,'ControlGroup':GROUP[len('/sys/fs/cgroup'):],
        'ActiveState':'inactive','SubState':'dead','Result':'success',
        'InactiveExitTimestampMonotonic':'1000000','InactiveEnterTimestampMonotonic':'3000000',
        'CPUUsageNSec':'2000000000','MemoryPeak':'12000000','MemorySwapPeak':'0',
        'ExecMainPID':'200','ExecMainCode':'1','ExecMainStatus':'0'}
    props.update(changes)
    return ''.join(name+'='+value+'\n' for name,value in props.items()).encode()


def expected():
    return {'unit':UNIT,'invocation_id':'e'*32,'aggregate_cgroup':GROUP,'cgroup_identity':ID.copy(),
        'controller_pid':200,'not_before_ns':500_000_000,'not_after_ns':20_000_000_000}


def final_snapshot(cpu=2_000_000):
    return j.parse_cgroup_raw(raw(cpu,empty=True),aggregate_cgroup=GROUP,cgroup_identity=ID,
        reader_pid=999,sample_start_ns=3_000_001_000,sample_end_ns=3_000_002_000)


class PureEnvelopeTests(unittest.TestCase):
    def state(self):
        return j.EnvelopeState(ORIGIN,GROUP,200)

    def test_absolute_cumulative_cpu_is_not_rate_or_delta(self):
        state=self.state()
        self.assertIsNone(state.observe(snapshot(2_999_999)))
        fault=state.observe(snapshot(3_000_000,offset=200))
        self.assertEqual((fault['reason'],fault['exit_status']),('CPU_EARLY_STOP',124))
        self.assertEqual(fault['observed_cpu_usec'],3_000_000)
        fresh=self.state()
        self.assertEqual(fresh.observe(snapshot(4_000_001))['reason'],'CPU_CAP_EXCEEDED')

    def test_fixed_thresholds_preserve_original_caps_and_full_false(self):
        result=self.state().summary()
        self.assertEqual((result['CPU_stop_usec'],result['CPU_contract_cap_usec']),(3_000_000,4_000_000))
        self.assertEqual((result['Main_stop_ns'],result['whole_job_wall_contract_ns']),(10_000_000_000,13_000_000_000))
        self.assertFalse(result['atomic_cgroup_total_CPU_kill'])
        self.assertFalse(result['hard_realtime_deadline'])
        self.assertTrue(result['main_origin_excludes_manager_activation'])
        self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_main_wall_early_stop_and_overcap_distinct(self):
        for offset,reason in ((9_999_999_999,'MAIN_WALL_EARLY_STOP'),(13_000_000_000,'MAIN_WALL_CAP_EXCEEDED')):
            result=self.state().observe(snapshot(offset=offset))
            self.assertEqual(result['reason'],reason)
            self.assertEqual(result['exit_status'],125)

    def test_first_fault_latched_never_replaced_by_later_valid_or_other_failure(self):
        state=self.state(); first=state.observe(snapshot(3_000_000))
        self.assertEqual(state.observe(snapshot(1,offset=200)),first)
        returned=state.fail('READBACK_INVALID','later')
        self.assertEqual(returned,first)
        returned['reason']='tampered'
        self.assertEqual(state.fault['reason'],'CPU_EARLY_STOP')

    def test_counter_reset_stale_clock_and_changed_cgroup_reject(self):
        for kind in ('cpu_reset','time_reset','group','inode'):
            state=self.state(); self.assertIsNone(state.observe(snapshot()))
            row=snapshot(20_000,offset=200)
            if kind=='cpu_reset':row['cpu_usage_usec']=9999
            if kind=='time_reset':row['sample_start_ns']=ORIGIN+1
            if kind=='group':row['aggregate_cgroup']=GROUP.replace('capacity','foreign')
            if kind=='inode':row['cgroup_identity']['inode']+=1
            with self.subTest(kind=kind):self.assertEqual(state.observe(row)['exit_status'],126)

    def test_bool_float_negative_missing_extra_pid_and_hash_rejected(self):
        for key,value in (('cpu_usage_usec',True),('cpu_usage_usec',1.0),('cpu_usage_usec',-1),
            ('sample_end_ns',None),('reader_pid',201),('populated',1),('pids',[200,True]),
            ('raw_sha256',{})):
            row=snapshot();row[key]=value
            with self.subTest(key=key,value=value):self.assertEqual(self.state().observe(row)['exit_status'],126)
        for kind in ('extra','missing'):
            row=snapshot()
            if kind=='extra':row['FULL_LAUNCH_ENVELOPE_VERIFIED']=True
            else:del row['cpu_usage_usec']
            self.assertEqual(self.state().observe(row)['exit_status'],126)

    def test_missing_peak_unknown_not_zero(self):
        row=snapshot();row['memory_peak_bytes']=None;row['raw_sha256']['memory.peak']=None
        result=self.state().observe(row)
        self.assertEqual(result['reason'],'READBACK_UNKNOWN')
        self.assertEqual(result['detail'],'MISSING_MEMORY_PEAK')

    def test_ram_swap_and_oom_stop_not_normal_pass(self):
        for kind in ('ram','swap','oom'):
            row=snapshot()
            if kind=='ram':row['memory_peak_bytes']=j.RAM_CAP+1
            if kind=='swap':row['swap_current_bytes']=1
            if kind=='oom':row['memory_events']['oom_kill']=1
            with self.subTest(kind=kind):self.assertEqual(self.state().observe(row)['reason'],'RAM_OR_SWAP_OR_OOM')

    def test_memory_peak_and_event_reset_reject(self):
        for kind in ('peak','event'):
            state=self.state();initial=snapshot()
            initial['memory_events']['high']=1
            state.observe(initial)
            row=snapshot(20000,offset=200);row['memory_events']['high']=1
            if kind=='peak':row['memory_peak_bytes']=11_000_000
            else:row['memory_events']['high']=0
            self.assertEqual(state.observe(row)['exit_status'],126)


class StrictRawParserTests(unittest.TestCase):
    def decode(self,value):
        return j.parse_cgroup_raw(value,aggregate_cgroup=GROUP,cgroup_identity=ID,
            reader_pid=200,sample_start_ns=1,sample_end_ns=2)

    def test_exact_raw_snapshot_and_effective_limits(self):
        decoded=self.decode(raw())
        self.assertTrue(j.validate_snapshot(decoded))
        self.assertEqual(decoded['cpu_usage_usec'],10_000)
        self.assertEqual(set(decoded['raw_sha256']),set(j.RAW_NAMES))
        optional=raw();optional['cpu.stat']+=b'core_sched.force_idle_usec 123\n'
        self.assertEqual(self.decode(optional)['cpu_usage_usec'],10_000)
        unknown=raw();unknown['cpu.stat']+=b'unreviewed_future_counter 0\n'
        with self.assertRaises(ValueError):self.decode(unknown)
        for key in j.EFFECTIVE:
            value=raw();value[key]=b'max\n'
            with self.subTest(key=key),self.assertRaises(ValueError):self.decode(value)

    def test_missing_peak_stays_none_and_other_missing_fails(self):
        value=raw();value['memory.peak']=None
        self.assertIsNone(self.decode(value)['memory_peak_bytes'])
        for key in ('cpu.stat','memory.current','memory.events'):
            value=raw();del value[key]
            with self.subTest(key=key),self.assertRaises(ValueError):self.decode(value)

    def test_bad_raw_duplicate_keys_units_encoding_and_bounds(self):
        for content in (b'usage_usec 1\nusage_usec 2\n',b'usage_nsec 1\n',b'usage_usec NaN\n',
            b'usage_usec -1\n',b'usage_usec 1.0\n',b'x'*4097,b'usage_usec 1',b'usage_usec 1\r\n'):
            value=raw();value['cpu.stat']=content
            with self.subTest(content=content[:30]),self.assertRaises((ValueError,UnicodeError)):self.decode(value)

    def test_pid_duplicates_excess_and_populated_conflicts(self):
        for content in (b'200\n200\n',b'0\n',b'200',b''.join(('%d\n'%i).encode() for i in range(1,18)),b''):
            value=raw();value['cgroup.procs']=content
            with self.subTest(content=content),self.assertRaises(ValueError):self.decode(value)
        self.assertEqual(self.decode(raw(empty=True))['pids'],[])

    def test_paths_and_identity_are_typed_fixed_aggregate(self):
        for path in ('/tmp','/sys/fs/cgroup/../escape',GROUP+'/worker',GROUP.replace('user@1000','user@1001')):
            with self.subTest(path=path),self.assertRaises(ValueError):j.EnvelopeState(1,path,200)
        for ident in ({'dev':True,'inode':2},{'dev':1,'inode':0},{'dev':1,'inode':2,'extra':0}):
            with self.assertRaises(ValueError):j.FixedCgroupReader(UNIT,GROUP,ident,200)


class FixedReaderMockTests(unittest.TestCase):
    def test_constructor_performs_no_kernel_reads(self):
        with patch.object(j.os,'open',side_effect=AssertionError('no open')),patch.object(j.os,'stat',side_effect=AssertionError('no stat')):
            j.FixedCgroupReader(UNIT,GROUP,ID,200)

    def context(self,*,pid=200,uid=1000,member=None,changed=False,missing=None):
        stack=ExitStack();values=raw()
        def read(path):
            if path=='/proc/self/cgroup':return (member or '0::'+GROUP[len('/sys/fs/cgroup'):]+'\n').encode()
            name=path.rsplit('/',1)[1]
            if name==missing:raise FileNotFoundError(name)
            return values[name]
        stack.enter_context(patch.object(j.FixedCgroupReader,'_read',side_effect=read))
        stack.enter_context(patch.object(j.os,'getpid',return_value=pid))
        stack.enter_context(patch.object(j.os,'getuid',return_value=uid))
        ids=[SimpleNamespace(st_dev=ID['dev'],st_ino=ID['inode']),SimpleNamespace(st_dev=ID['dev'],st_ino=ID['inode']+(1 if changed else 0))]
        stack.enter_context(patch.object(j.os,'stat',side_effect=ids))
        stack.enter_context(patch.object(j.time,'monotonic_ns',side_effect=[10,20]))
        return stack

    def test_future_reader_all_OS_observations_mocked(self):
        with self.context():value=j.FixedCgroupReader(UNIT,GROUP,ID,200)()
        self.assertEqual(value['sample_start_ns'],10)
        self.assertEqual(value['sample_end_ns'],20)
        self.assertTrue(j.validate_snapshot(value))

    def test_current_pid_uid_membership_and_identity_changes_reject(self):
        for options in ({'pid':201},{'uid':1001},{'member':'0::/wrong\n'},{'changed':True}):
            with self.subTest(options=options),self.context(**options),self.assertRaises(ValueError):
                j.FixedCgroupReader(UNIT,GROUP,ID,200)()

    def test_missing_peak_nullable_other_file_exception(self):
        with self.context(missing='memory.peak'):
            self.assertIsNone(j.FixedCgroupReader(UNIT,GROUP,ID,200)()['memory_peak_bytes'])
        with self.context(missing='cpu.stat'),self.assertRaises(FileNotFoundError):
            j.FixedCgroupReader(UNIT,GROUP,ID,200)()

    def test_bounded_read_nofollow_closes_on_success_and_overflow(self):
        for blocks,expected_error in (([b'a\n',b''],False),([b'x'*5],True)):
            with patch.object(j.os,'open',return_value=50) as opened,patch.object(j.os,'read',side_effect=blocks),patch.object(j.os,'close') as closed:
                if expected_error:
                    with self.assertRaises(ValueError):j.FixedCgroupReader._read('/fixed/mock',4)
                else:self.assertEqual(j.FixedCgroupReader._read('/fixed/mock',4),b'a\n')
                self.assertEqual(opened.call_args.args[1],j.os.O_RDONLY|j.os.O_CLOEXEC|j.os.O_NOFOLLOW)
                closed.assert_called_once_with(50)


class PeriodicAdapterMockTests(unittest.TestCase):
    def setUp(self):self.prior_owner=j._OWNER;j._OWNER=None
    def tearDown(self):j._OWNER=self.prior_owner

    def setup_adapter(self,reader=None,callback=None):
        return j.PeriodicEnvelope(j.EnvelopeState(ORIGIN,GROUP,200),reader or Mock(return_value=snapshot()),callback)

    def timers(self,*,previous=(0.0,0.0),old_handler=None,thread_ok=True):
        stack=ExitStack();thread=object()
        stack.enter_context(patch.object(j.threading,'current_thread',return_value=thread))
        stack.enter_context(patch.object(j.threading,'main_thread',return_value=thread if thread_ok else object()))
        stack.enter_context(patch.object(j.signal,'getitimer',return_value=previous))
        self.stored_handler=[j.signal.SIG_DFL if old_handler is None else old_handler]
        stack.enter_context(patch.object(j.signal,'getsignal',side_effect=lambda signum:self.stored_handler[0]))
        def set_handler(signum,handler):
            prior=self.stored_handler[0];self.stored_handler[0]=handler;return prior
        self.signal=stack.enter_context(patch.object(j.signal,'signal',side_effect=set_handler))
        self.timer=stack.enter_context(patch.object(j.signal,'setitimer',return_value=(0.0,0.0)))
        return stack

    def test_arm_initial_read_before_timer_and_restore_exact_handler(self):
        old=lambda *args:None;adapter=self.setup_adapter()
        with self.timers(old_handler=old):
            adapter.arm();self.assertTrue(adapter.owned)
            self.timer.assert_called_once_with(j.signal.ITIMER_REAL,.01,.01)
            adapter.close()
            self.assertEqual(self.signal.call_args.args,(j.signal.SIGALRM,old))
            self.assertEqual(self.timer.call_args.args,(j.signal.ITIMER_REAL,0,0))
        self.assertFalse(adapter.owned);self.assertIsNone(j._OWNER)

    def test_active_prior_timer_or_nonmain_thread_refused_untouched(self):
        for opts in ({'previous':(1.0,0.0)},{'previous':(0.0,1.0)},{'thread_ok':False}):
            adapter=self.setup_adapter()
            with self.subTest(opts=opts),self.timers(**opts),self.assertRaises(ValueError):adapter.arm()
            self.signal.assert_not_called();self.timer.assert_not_called()

    def test_second_owner_and_rearm_refused(self):
        first=self.setup_adapter();second=self.setup_adapter()
        with self.timers():
            first.arm()
            with self.assertRaises(ValueError):second.arm()
            with self.assertRaises(ValueError):first.arm()
            first.close();first.close()

    def test_initial_limit_fault_calls_callback_without_installing_timer(self):
        callback=Mock();adapter=self.setup_adapter(Mock(return_value=snapshot(3_000_000)),callback)
        with self.timers(),self.assertRaises(j.EnvelopeAbort):adapter.arm()
        callback.assert_called_once();self.timer.assert_not_called();self.signal.assert_not_called()
        self.assertEqual(callback.call_args.args[0]['exit_status'],124)

    def test_alarm_raises_even_if_exit_callback_mock_returns(self):
        reader=Mock(side_effect=[snapshot(),snapshot(3_000_000,offset=200)])
        callback=Mock();adapter=self.setup_adapter(reader,callback)
        with self.timers():
            adapter.arm()
            with self.assertRaises(j.EnvelopeAbort) as caught:adapter._handler(j.signal.SIGALRM,None)
            self.assertEqual(caught.exception.envelope_fault['exit_status'],124)
            self.assertEqual(self.timer.call_args.args,(j.signal.ITIMER_REAL,0,0))
            adapter._handler(j.signal.SIGALRM,None)
            callback.assert_called_once()
            with self.assertRaises(j.EnvelopeAbort):adapter.check_latched()
            adapter.close()

    def test_nested_handler_ignored_and_no_handler_work_before_arm(self):
        reader=Mock(return_value=snapshot());adapter=self.setup_adapter(reader)
        with self.timers():
            adapter._handler(j.signal.SIGALRM,None);reader.assert_not_called()
            adapter.arm();before=reader.call_count;adapter.in_handler=True
            adapter._handler(j.signal.SIGALRM,None)
            self.assertEqual(reader.call_count,before)
            adapter.in_handler=False;adapter.close()

    def test_reader_exception_latches_unknown_and_stops(self):
        reader=Mock(side_effect=[snapshot(),PermissionError(errno.EACCES,'inert denied')])
        adapter=self.setup_adapter(reader)
        with self.timers():
            adapter.arm()
            with self.assertRaises(j.EnvelopeAbort) as caught:adapter._handler(j.signal.SIGALRM,None)
            self.assertEqual(caught.exception.envelope_fault['exit_status'],126)
            adapter.close()

    def test_callback_exit_exception_keeps_original_fault(self):
        callback=Mock(side_effect=SystemExit(125))
        reader=Mock(side_effect=[snapshot(),snapshot(offset=10_000_000_000)])
        adapter=self.setup_adapter(reader,callback)
        with self.timers():
            adapter.arm()
            with self.assertRaises(SystemExit) as caught:adapter._handler(j.signal.SIGALRM,None)
            self.assertEqual(caught.exception.envelope_fault['exit_status'],125)
            adapter.close()

    def test_timer_install_failure_restores_handler(self):
        adapter=self.setup_adapter()
        with self.timers():
            self.timer.side_effect=[OSError('inert arm failure'),(0.0,0.0)]
            with self.assertRaisesRegex(OSError,'arm failure'):adapter.arm()
            self.assertEqual(self.signal.call_count,2)
        self.assertFalse(adapter.owned);self.assertIsNone(j._OWNER)

    def test_close_failure_keeps_unknown_owner_and_first_fault(self):
        adapter=self.setup_adapter()
        with self.timers():
            adapter.arm();self.timer.side_effect=OSError('inert disable failure')
            with self.assertRaises(j.EnvelopeAbort) as caught:adapter.close()
            self.assertEqual(caught.exception.envelope_fault['reason'],'TIMER_RESTORE_UNKNOWN')
            self.assertTrue(adapter.owned);self.assertIs(j._OWNER,adapter)

    def test_active_borrow_assert_and_check_now_do_not_pause_or_reset_timer(self):
        adapter=self.setup_adapter(Mock(side_effect=[snapshot(),snapshot(20000,offset=200)]))
        with self.timers():
            adapter.arm();before=self.timer.call_count;handlers=self.signal.call_count
            with patch.object(j.signal,'getitimer',return_value=(.005,.01)):
                self.assertTrue(adapter.assert_active_timer())
                self.assertEqual(adapter.check_now()['cpu_usage_usec'],20000)
            self.assertEqual(self.timer.call_count,before)
            self.assertEqual(self.signal.call_count,handlers)
            adapter.close()

    def test_invalid_borrow_timer_or_foreign_handler_reject_without_mutation(self):
        for kind in ('expired','wrong_interval','bool','foreign_handler','wrong_owner'):
            adapter=self.setup_adapter()
            with self.subTest(kind=kind),self.timers():
                adapter.arm();before=self.timer.call_count;handlers=self.signal.call_count
                value=(.005,.01)
                if kind=='expired':value=(0.0,.01)
                if kind=='wrong_interval':value=(.005,1.0)
                if kind=='bool':value=(True,.01)
                if kind=='foreign_handler':self.stored_handler[0]=j.signal.SIG_IGN
                if kind=='wrong_owner':j._OWNER=None
                with patch.object(j.signal,'getitimer',return_value=value),self.assertRaises(j.EnvelopeAbort):
                    adapter.assert_active_timer()
                self.assertEqual(self.timer.call_count,before)
                self.assertEqual(self.signal.call_count,handlers)
                j._OWNER=None

    def test_foreign_handler_close_never_disables_or_restores_it(self):
        for kind in ('foreign_handler','foreign_owner','non_main_thread'):
            adapter=self.setup_adapter()
            with self.subTest(kind=kind),self.timers():
                adapter.arm()
                if kind=='foreign_handler':self.stored_handler[0]=j.signal.SIG_IGN
                if kind=='foreign_owner':j._OWNER=object()
                before=self.timer.call_count;handlers=self.signal.call_count
                with patch.object(j.threading,'current_thread',return_value=object()) if kind=='non_main_thread' else ExitStack():
                    with self.assertRaises(j.EnvelopeAbort):adapter.close()
                self.assertEqual(self.timer.call_count,before)
                self.assertEqual(self.signal.call_count,handlers)
                j._OWNER=None


class PostmortemRawTests(unittest.TestCase):
    def test_independent_postmortem_values_are_not_execution_authentication(self):
        result=j.validate_postmortem(manager(),final_snapshot(),expected())
        self.assertEqual(result['status'],'PASS_RAW_NUMERICAL_ONLY')
        self.assertEqual(result['CPU_observed_upper_ns'],2_000_000_999)
        self.assertEqual(result['wall_observed_upper_ns'],2_000_001_000)
        self.assertTrue(result['normal_workflow_exit_observed'])
        self.assertFalse(result['raw_execution_origin_authenticated'])
        self.assertFalse(result['manager_control_plane_capacity_accounted'])
        self.assertFalse(result['FULL_LAUNCH_ENVELOPE_VERIFIED'])

    def test_manager_microseconds_are_not_ns_and_cpu_is_ns(self):
        result=j.validate_postmortem(manager(CPUUsageNSec='4000000001'),final_snapshot(),expected())
        self.assertEqual(result['status'],'FAIL')
        result=j.validate_postmortem(manager(InactiveEnterTimestampMonotonic='15000001'),
            dict(final_snapshot(),sample_start_ns=15_000_002_000,sample_end_ns=15_000_003_000),expected())
        self.assertEqual(result['reason'],'POSTMORTEM_FULL_WALL_OVER_CAP')

    def test_quantization_at_cap_is_conservative(self):
        for value,status in (('3999999000','PASS_RAW_NUMERICAL_ONLY'),('4000000000','FAIL')):
            result=j.validate_postmortem(manager(CPUUsageNSec=value),final_snapshot(3_999_999),expected())
            self.assertEqual(result['status'],status)

    def test_missing_group_and_missing_peak_never_imply_zero_or_empty(self):
        self.assertEqual(j.validate_postmortem(manager(),None,expected())['status'],'UNKNOWN')
        for changes in ({'MemoryPeak':'[not set]'},{'CPUUsageNSec':'18446744073709551615'},
                        {'InactiveExitTimestampMonotonic':'0'}):
            self.assertEqual(j.validate_postmortem(manager(**changes),final_snapshot(),expected())['status'],'UNKNOWN')

    def test_bad_manager_keys_duplicates_nonfinite_and_lf_rejected(self):
        for value in (manager()+b'Id=x\n',manager()+b'Extra=0\n',manager()[:-1],
                      manager(CPUUsageNSec='NaN'),manager(CPUUsageNSec='-1'),manager(Result='invented'),
                      manager(ActiveState='inactive',SubState='failed'),
                      manager(ActiveState='failed',SubState='dead')):
            with self.subTest(value=value[-30:]),self.assertRaises(ValueError):j.parse_manager_raw(value)

    def test_wrong_run_group_pid_time_residual_processes_or_malformed_sample_fail(self):
        for key,value in (('InvocationID','f'*32),('Id',UNIT.replace('capacity','foreign')),
                          ('ControlGroup','/user.slice/foreign'),('ExecMainPID','201'),
                          ('ActiveState','active')):
            self.assertEqual(j.validate_postmortem(manager(**{key:value}),final_snapshot(),expected())['status'],'FAIL')
        for key,value in (('populated',True),('pids',[200]),('sample_end_ns',True),('raw_sha256',{})):
            row=final_snapshot();row[key]=value
            self.assertEqual(j.validate_postmortem(manager(),row,expected())['status'],'FAIL')

    def test_oom_cleanup_consistency_never_becomes_normal_workflow_success(self):
        row=final_snapshot();row['memory_events']['oom_kill']=1
        result=j.validate_postmortem(manager(Result='oom-kill',ExecMainCode='2',ExecMainStatus='9'),row,expected())
        self.assertEqual(result['status'],'PASS_RAW_NUMERICAL_ONLY')
        self.assertEqual(result['OOM_events_observed'],1)
        self.assertFalse(result['normal_workflow_exit_observed'])
        failed=j.validate_postmortem(manager(ActiveState='failed',SubState='failed'),final_snapshot(),expected())
        self.assertEqual(failed['status'],'PASS_RAW_NUMERICAL_ONLY')
        self.assertFalse(failed['normal_workflow_exit_observed'])


if __name__=='__main__':unittest.main()
