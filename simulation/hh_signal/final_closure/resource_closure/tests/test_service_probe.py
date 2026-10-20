"""Offline probe policy only. Never launch a systemd service in unit tests."""
import copy,subprocess,unittest
from pathlib import Path
from unittest import mock
from .. import backend,service_probe as p

class ProbePolicyTests(unittest.TestCase):
    def test_fixed_true_and_same_limits_except_unused_transport(self):
        unit='atlas-hh-phase7i-resource-'+'a'*32+'.service'
        output='/tmp/PLAN_ONLY'
        cmd=p.command(output,unit)
        self.assertEqual(cmd[-1],'/usr/bin/true')
        self.assertEqual(cmd.count('/usr/bin/true'),1)
        self.assertNotIn('/usr/bin/python3',cmd)
        props=cmd[5:-1]
        self.assertEqual(props[::2],['--property']*len(props[::2]))
        expected=[v for v in backend.properties(output) if not v.startswith(
            ('OpenFile=','StandardOutput=','StandardError='))]
        self.assertEqual(props[1::2],expected+['StandardOutput=null','StandardError=null'])
        self.assertFalse(any(v.startswith('OpenFile=') for v in cmd))

    def test_rejects_foreign_units_before_any_process(self):
        with mock.patch.object(p.subprocess,'run') as proc:
            for unit in ('sshd.service','','atlas-hh-phase7i-resource-../bad.service'):
                with self.assertRaisesRegex(ValueError,'FOREIGN_UNIT'):
                    p.command('/tmp/PLAN_ONLY',unit)
            proc.assert_not_called()

    def test_pending_ram_blocks(self):
        profile=copy.deepcopy(backend.PROFILE_FIXTURE)
        profile['RAM_profile_review_status']='PENDING'
        with mock.patch.object(backend,'load_profile',return_value=profile):
            with self.assertRaisesRegex(ValueError,'RAM_PROFILE_NOT_EXPLICITLY_REVIEWED'):
                p.command('/tmp/PLAN_ONLY','atlas-hh-phase7i-resource-'+'a'*32+'.service')

    def test_exit_zero_requires_complete_manager_state(self):
        launch={'returncode':0}
        data={'LoadState':'loaded','ActiveState':'active','SubState':'exited',
              'Result':'success','ExecMainCode':'1','ExecMainStatus':'0','MainPID':'0'}
        self.assertEqual(p.classify(launch,data),p.STATUS_OK)
        for key in data:
            altered=dict(data);altered.pop(key)
            self.assertEqual(p.classify(launch,altered),p.STATUS_BLOCKED)
        self.assertEqual(p.classify({'returncode':2},data),p.STATUS_BLOCKED)
        self.assertEqual(p.classify(launch,dict(data,Result='resources')),p.STATUS_BLOCKED)

    def test_unknown_measurements_are_null(self):
        for value in ('','[not set]',None,'infinity','-1'):
            self.assertIsNone(p.optional_int({'CPUUsageNSec':value},'CPUUsageNSec'))
        self.assertIsNone(p.optional_int({},'MemoryPeak'))
        self.assertEqual(p.optional_int({'CPUUsageNSec':'0'},'CPUUsageNSec'),0)

    def test_build_cannot_be_enabled_by_probe_or_ram(self):
        self.assertFalse(backend.load_profile('BUILD_ONLY')['formal_build_execution_authorized'])
        with mock.patch.object(p.subprocess,'run') as proc:
            with self.assertRaisesRegex(ValueError,'COMPLETE_CONTROLLER'):
                backend.start_build('/NEVER_CREATED','a'*40)
            proc.assert_not_called()

    def test_cleanup_kill_timeout_still_stops_and_queries_exact_unit(self):
        unit='atlas-hh-phase7i-resource-'+'a'*32+'.service'
        calls=[]
        def action(argv,timeout):
            calls.append(argv)
            if 'kill' in argv:raise subprocess.TimeoutExpired(argv,timeout)
            return {'returncode':0,'stdout':'','stderr':''}
        after={'Id':unit,'ActiveState':'inactive','MainPID':'0'}
        with mock.patch.object(p,'call',side_effect=action),mock.patch.object(
            p,'show',return_value=({'returncode':0},after)),mock.patch.object(
            Path,'exists',return_value=False):
            row=p.cleanup_unit(unit,Path('/OFFLINE_KNOWN_CGROUP'))
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[1],['/usr/bin/systemctl','--user','stop',unit])
        self.assertTrue(row['cleanup_verified'])
        self.assertEqual(row['kernel_cleanup'],'KNOWN_CGROUP_REMOVED')

    def test_cleanup_missing_main_pid_and_missing_kernel_reads_are_unknown(self):
        unit='atlas-hh-phase7i-resource-'+'a'*32+'.service'
        good={'Id':unit,'ActiveState':'failed','MainPID':'0'}
        for after in (good,{k:v for k,v in good.items() if k!='MainPID'}):
            with mock.patch.object(p,'call',return_value={'returncode':0}),mock.patch.object(
                p,'show',return_value=({'returncode':0},after)),mock.patch.object(
                Path,'exists',return_value=True),mock.patch.object(backend,'cgroup_read',return_value={}):
                row=p.cleanup_unit(unit,Path('/OFFLINE_KNOWN_CGROUP'))
            self.assertFalse(row['cleanup_verified'])
            self.assertEqual(row['kernel_cleanup'],'NOT_PROVEN_EMPTY')
        with mock.patch.object(p,'call',return_value={'returncode':0}),mock.patch.object(
            p,'show',return_value=({'returncode':0},good)):
            row=p.cleanup_unit(unit,None)
        self.assertFalse(row['cleanup_verified']);self.assertEqual(row['kernel_cleanup'],'NOT_OBSERVED')

    def test_cleanup_requires_explicit_empty_kernel_cgroup(self):
        unit='atlas-hh-phase7i-resource-'+'a'*32+'.service'
        after={'Id':unit,'ActiveState':'failed','MainPID':'0'}
        cases=[({},False),({'cgroup.procs':'','cgroup.events':'populated 1'},False),
               ({'cgroup.procs':'123','cgroup.events':'populated 0'},False),
               ({'cgroup.procs':'','cgroup.events':'populated 0'},True)]
        for snapshot,expected in cases:
            with mock.patch.object(p,'call',return_value={'returncode':0}),mock.patch.object(
                p,'show',return_value=({'returncode':0},after)),mock.patch.object(
                Path,'exists',return_value=True),mock.patch.object(
                backend,'cgroup_read',return_value=snapshot):
                row=p.cleanup_unit(unit,Path('/OFFLINE_KNOWN_CGROUP'))
            self.assertEqual(row['cleanup_verified'],expected)

    def test_nonzero_query_never_becomes_success(self):
        unit='atlas-hh-phase7i-resource-'+'a'*32+'.service'
        with mock.patch.object(p,'call',return_value={
            'returncode':2,'stdout':'Id='+unit+'\nMainPID=0\n','stderr':'query error'}):
            with self.assertRaisesRegex(ValueError,'UNIT_QUERY_FAILED'):
                p.show(unit)
