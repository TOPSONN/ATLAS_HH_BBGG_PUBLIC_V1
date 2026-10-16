"""Isolated Git fixtures only. No real integration entry point is invoked."""
import hashlib,json,os,signal,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from .git_precheck import GitGuard,GitPrecheckError,EXPECTED_REMOTE,verify_checkout,regular_bytes

class GitPrecheckTests(unittest.TestCase):
    matrix=[]
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name)
        self.env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
        self.git('init','-q');self.git('config','user.name','Isolated method fixture')
        self.git('config','user.email','fixture@example.invalid');self.git('config','core.filemode','true')
        self.git('remote','add','origin',EXPECTED_REMOTE)
        for name,value in [('source.py','VALUE=1\n'),('physics.json','{"physics":"FIXTURE_ONLY"}\n'),('outside.txt','outside1\n')]:
            (self.repo/name).write_text(value)
        self.git('add','.');self.git('commit','-qm','METHOD_ONLY')
        self.rev=self.git('rev-parse','HEAD').strip();self.physics=hashlib.sha256((self.repo/'physics.json').read_bytes()).hexdigest()
    def tearDown(self):self.tmp.cleanup()
    def git(self,*args,check=True):
        r=subprocess.run(['git','-C',str(self.repo),*args],env=self.env,capture_output=True,text=True,timeout=10)
        if check:self.assertEqual(r.returncode,0,r.stderr)
        return r.stdout
    def verify(self,**kw):
        return verify_checkout(self.repo,self.rev,['source.py'],'physics.json',self.physics,**kw)
    def original(self):
        r=subprocess.run(['git','-C',str(self.repo),'status','--porcelain','--untracked-files=no'],env=self.env,capture_output=True,timeout=10)
        return r.returncode==0 and not r.stdout
    def rejects(self,label,*,original_dirty=True):
        original_clean=self.original()
        if original_dirty:self.assertFalse(original_clean,label)
        with self.assertRaises((GitPrecheckError,OSError,ValueError)):self.verify()
        self.matrix.append({'case':label,'original_status_clean':original_clean,'candidate':'REJECT','native_dispatch':False})
    def test_clean_original_and_new(self):
        before=(self.repo/'.git/index').read_bytes()
        self.assertTrue(self.original());r=self.verify();self.assertEqual(r['status'],'PASS_FULL_TRACKED_PREFLIGHT')
        self.assertEqual(before,(self.repo/'.git/index').read_bytes());self.assertEqual(r['tracked_files'],3)
    def test_wrong_head(self):
        self.rev='0'*40
        with self.assertRaisesRegex(GitPrecheckError,'REVISION_MISMATCH'):self.verify()
    def test_staged_modification(self):
        (self.repo/'outside.txt').write_text('staged\n');self.git('add','outside.txt');self.rejects('staged outside required scope')
    def test_unstaged_modification(self):
        (self.repo/'outside.txt').write_text('unstaged\n');self.rejects('unstaged outside required scope')
    def test_deleted_tracked_file(self):
        (self.repo/'outside.txt').unlink();self.rejects('deleted tracked file')
    def test_modified_reviewed_source(self):
        (self.repo/'source.py').write_text('VALUE=2\n');self.rejects('modified reviewed source')
    def test_modified_physics_contract(self):
        (self.repo/'physics.json').write_text('{}\n');self.rejects('modified physics contract')
    def test_wrong_reviewed_physics_hash(self):
        self.physics='0'*64
        with self.assertRaisesRegex(GitPrecheckError,'PHYSICS_CONTRACT_DRIFT'):self.verify()
    def test_invalid_git_index(self):
        (self.repo/'.git/index').write_bytes(b'INVALID_METHOD_FIXTURE')
        self.rejects('invalid Git index')
    def test_missing_required_tracked_path(self):
        with self.assertRaisesRegex(GitPrecheckError,'MISSING_REQUIRED_TRACKED_PATH'):
            verify_checkout(self.repo,self.rev,['missing.py'],'physics.json',self.physics)
    def test_unexpected_symlink(self):
        p=self.repo/'source.py';p.unlink();p.symlink_to('outside.txt');self.rejects('unexpected symlink')
    def test_symlink_parent(self):
        with self.assertRaisesRegex(GitPrecheckError,'UNEXPECTED_SYMLINK'):
            p=self.repo/'alias';p.symlink_to(self.repo,target_is_directory=True);regular_bytes(self.repo,'alias/source.py')
    def test_changed_mode_when_git_tracks_modes(self):
        (self.repo/'outside.txt').chmod(0o755);self.rejects('executable mode change core.filemode=true')
    def test_staged_rename(self):
        self.git('mv','outside.txt','renamed.txt');self.rejects('staged rename')
    def test_staged_replacement(self):
        (self.repo/'source.py').write_text('REPLACEMENT=1\n');self.git('add','source.py');self.rejects('staged source replacement')
    def test_untracked_is_same_scope_as_original(self):
        (self.repo/'personal.txt').write_text('METHOD_ONLY\n');self.assertTrue(self.original());self.verify()
    def test_assume_unchanged_cannot_hide_outside_change(self):
        self.git('update-index','--assume-unchanged','outside.txt');(self.repo/'outside.txt').write_text('hidden\n')
        self.rejects('assume-unchanged flag',original_dirty=False)
    def test_skip_worktree_cannot_hide_outside_change(self):
        self.git('update-index','--skip-worktree','outside.txt');(self.repo/'outside.txt').write_text('hidden\n')
        self.rejects('skip-worktree flag',original_dirty=False)
    def test_gitlink_requires_separate_review(self):
        self.git('update-index','--add','--cacheinfo','160000,'+self.rev+',nested')
        self.rejects('submodule index entry')
    def test_repository_identity(self):
        self.git('remote','set-url','origin','https://example.invalid/wrong.git')
        with self.assertRaisesRegex(GitPrecheckError,'REMOTE_MISMATCH'):self.verify()
    def test_git_environment_override(self):
        with patch.dict(os.environ,{'GIT_INDEX_FILE':str(self.repo/'fake')}):
            with self.assertRaisesRegex(GitPrecheckError,'UNSAFE_GIT_ENVIRONMENT'):self.verify()
    def test_unreviewed_fsmonitor_rejected(self):
        self.git('config','core.fsmonitor','/not/a/reviewed/hook')
        with self.assertRaisesRegex(GitPrecheckError,'UNREVIEWED_FSMONITOR'):self.verify()
    def test_inaccessible_tracked_path(self):
        p=self.repo/'outside.txt';p.chmod(0)
        try:
            with patch('os.access',return_value=False):
                with self.assertRaisesRegex(GitPrecheckError,'INACCESSIBLE'):self.verify()
        finally:p.chmod(0o644)
    def test_same_size_same_mtime_race(self):
        p=self.repo/'source.py';s=p.stat();p.write_text('VALUE=2\n');os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns))
        self.rejects('same size and restored mtime')
    def test_edit_between_status_and_hash(self):
        original=GitGuard.git;count=[0]
        def raced(guard,*args):
            data=original(guard,*args)
            if args[0]=='status':
                count[0]+=1
                if count[0]==2:(self.repo/'source.py').write_text('VALUE=2\n')
            return data
        with patch.object(GitGuard,'git',raced):
            with self.assertRaisesRegex(GitPrecheckError,'CRITICAL_INPUT_RACE'):self.verify()
    def test_index_race(self):
        original=GitGuard.git;count=[0]
        # Deterministically change an otherwise valid index extension/checksum.
        def mutate(guard,*args):
            data=original(guard,*args)
            if args[0]=='status':
                count[0]+=1
                if count[0]==2:
                    p=self.repo/'.git/index';b=p.read_bytes();b=b[:-20]+b'TEST'+(0).to_bytes(4,'big');p.write_bytes(b+hashlib.sha1(b).digest())
            return data
        with patch.object(GitGuard,'git',mutate):
            with self.assertRaisesRegex(GitPrecheckError,'INDEX_CHANGED'):self.verify()
    def test_outside_path_edit_after_status(self):
        original=GitGuard.git;count=[0]
        def raced(guard,*args):
            data=original(guard,*args)
            if args[0]=='status':
                count[0]+=1
                if count[0]==2:(self.repo/'outside.txt').write_text('changed after status\n')
            return data
        with patch.object(GitGuard,'git',raced):
            with self.assertRaisesRegex(GitPrecheckError,'TRACKED_METADATA_RACE'):self.verify()
    def test_git_subprocess_failure(self):
        with GitGuard(self.repo) as guard:
            with self.assertRaisesRegex(GitPrecheckError,'GIT_SUBPROCESS_FAILURE'):guard.git('not-a-git-command')
    def test_subprocess_timeout_kills_descendant_group(self):
        original=subprocess.Popen;pidfile=self.repo/'method_child_pid'
        code='import subprocess,time;from pathlib import Path;p=subprocess.Popen(["/bin/sleep","20"]);Path('+repr(str(pidfile))+').write_text(str(p.pid));time.sleep(20)'
        def fake(args,**kwargs):return original([sys.executable,'-B','-c',code],**kwargs)
        with GitGuard(self.repo,wall=5,command=.2) as guard,patch('subprocess.Popen',fake):
            with self.assertRaisesRegex(GitPrecheckError,'GIT_COMMAND_TIMEOUT'):guard.git('rev-parse','HEAD')
        pid=int(pidfile.read_text());q=Path('/proc')/str(pid)/'stat'
        for _ in range(50):
            if not q.exists() or q.read_text().rsplit(')',1)[1].split()[0]=='Z':break
            time.sleep(.01)
        else:self.fail('surviving subprocess-group descendant')
    def test_overall_watchdog_covers_python_work(self):
        with self.assertRaisesRegex(GitPrecheckError,'WALL_WATCHDOG'):
            with GitGuard(self.repo,wall=.1):time.sleep(1)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.,0.))
    def test_timeout_preserves_bounded_diagnostic(self):
        original=subprocess.Popen
        def fake(args,**kwargs):return original(['/bin/sleep','20'],**kwargs)
        with self.assertRaisesRegex(GitPrecheckError,'GIT_COMMAND_TIMEOUT') as caught:
            with GitGuard(self.repo,wall=5,command=.1) as guard,patch('subprocess.Popen',fake):guard.git('rev-parse','HEAD')
        row=caught.exception.diagnostics[-1]
        self.assertTrue(row['group_cleanup']);self.assertIn('GIT_COMMAND_TIMEOUT',row['reason'])
        self.assertLessEqual(len(row['stderr_excerpt']),512)
    def test_cpu_budget(self):
        with GitGuard(self.repo,cpu=.001) as guard:
            with self.assertRaisesRegex(GitPrecheckError,'CPU_BUDGET'):guard.git('rev-parse','HEAD')
    def test_plumbing_is_not_accepted_as_status_equivalence(self):
        p=self.repo/'outside.txt';s=p.stat();os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns+2000000000))
        before=(self.repo/'.git/index').read_bytes();self.assertTrue(self.original())
        result=subprocess.run(['git','-C',str(self.repo),'diff-files','--quiet'],env=self.env,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,1);self.verify()
        self.assertEqual(before,(self.repo/'.git/index').read_bytes())
    def test_observed_diff_refresh_side_effect_in_fixture(self):
        p=self.repo/'outside.txt';s=p.stat();os.utime(p,ns=(s.st_atime_ns,s.st_mtime_ns+2000000000))
        before=(self.repo/'.git/index').read_bytes();self.assertTrue(self.original());self.assertEqual(before,(self.repo/'.git/index').read_bytes())
        self.git('diff','--name-only')
        # Git versions differ: record the observed installed behavior, not a
        # requirement that every newer Git retain this undesirable side effect.
        self.matrix.append({'case':'diff stat-refresh behavior','index_changed_despite_optional_locks_0':before!=(self.repo/'.git/index').read_bytes(),'native_dispatch':False})

class FrozenInputGuards(unittest.TestCase):
    def setUp(self):
        from . import run
        from .contract import SEEDS,PHYSICS_SHA,sources,sha
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.run=run
        rows=[]
        for seed in SEEDS:
            folder=self.root/f'replica_{seed}';folder.mkdir()
            (folder/'exe').write_bytes(b'METHOD_ONLY_NOT_EXECUTABLE')
            (folder/'card').write_text('METHOD_ONLY\n')
            library=folder/'library';library.write_bytes(b'METHOD_ONLY_LIBRARY')
            rows.append({'seed':seed,'executable':'exe','executable_sha256':sha(folder/'exe'),
                'immutable':[{'path':'card','sha256':sha(folder/'card')}],
                'dynamic_dependencies':[{'path':str(library),'sha256':sha(library),'name':'METHOD_ONLY'}]})
        (self.root/'review_build.json').write_text(json.dumps({'source_identity':sources(),'physics_contract_sha256':PHYSICS_SHA,'replicas':rows}))
    def tearDown(self):self.tmp.cleanup()
    def check(self):
        with patch.object(self.run,'safe_root',lambda p:Path(p)):return self.run.check_build(self.root)
    def test_clean_method_only_build(self):self.check()
    def test_stopped_attempt_is_not_reused_or_overwritten(self):
        marker=self.root/'review_failure.json';marker.write_text('IMMUTABLE_METHOD_FIXTURE')
        with self.assertRaisesRegex(ValueError,'STOPPED_ATTEMPT_IMMUTABLE'):self.run.require_fresh_attempt(self.root)
        self.assertEqual(marker.read_text(),'IMMUTABLE_METHOD_FIXTURE')
    def test_modified_executable_rejected(self):
        (self.root/'replica_910001/exe').write_bytes(b'MODIFIED')
        with self.assertRaisesRegex(ValueError,'EXECUTABLE_DRIFT'):self.check()
    def test_wrong_dynamic_library_hash_rejected(self):
        (self.root/'replica_910001/library').write_bytes(b'MODIFIED')
        with self.assertRaisesRegex(ValueError,'SHARED_LIBRARY_DRIFT'):self.check()
    def test_modified_card_rejected(self):
        (self.root/'replica_910001/card').write_text('MODIFIED')
        with self.assertRaisesRegex(ValueError,'IMMUTABLE_BUILD_INPUT_DRIFT'):self.check()
    def test_missing_immutable_source_rejected(self):
        (self.root/'replica_910001/card').unlink()
        with self.assertRaises(OSError):self.check()
    def test_historical_public_native_build_binding(self):
        from .contract import HERE,read_json,verify_source_binding
        b=read_json(HERE/'evidence/executable_review.json')['public_native_build']
        r=verify_source_binding(b,public=True)
        self.assertEqual(r['status'],'UNCHANGED_NATIVE_BUILD_NEW_SOURCE_REAPPROVAL_REQUIRED')
        self.assertIs(r['restart_authorized'],False)
    def test_changed_recovery_source_identity_rejected(self):
        from . import contract
        b=contract.read_json(contract.HERE/'evidence/executable_review.json')['public_native_build']
        m=contract.read_json(contract.REPO/contract.RECOVERY_METADATA)
        m['current_execution_source_identity'][0]['sha256']='0'*64
        with patch.object(contract,'read_json',return_value=m):
            with self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY_DRIFT'):contract.verify_source_binding(b,public=True)

if __name__=='__main__':unittest.main(verbosity=2)
