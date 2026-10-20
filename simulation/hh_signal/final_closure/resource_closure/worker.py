"""Fixed service payload. Current execution scope: harmless resource fixtures.

BUILD_ONLY is unconditionally blocked until the complete host controller resource
boundary is implemented and independently reviewed. Approval alone cannot enable
this source proposal. No test creates human approval.
Archives are never extracted or dispatched by this module.
"""
from __future__ import annotations
import argparse,fcntl,json,os,resource,signal,stat,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO))
if __name__=='__main__':
    # One module instance holds the live enclosure across build imports.
    sys.modules['simulation.hh_signal.final_closure.resource_closure.worker']=sys.modules[__name__]
from simulation.hh_signal.final_closure.resource_closure import allocation_guard
_ALLOCATION=None
def _requests_build(argv):
    return any(value=='--mode=BUILD_ONLY' or
               (value=='--mode' and argv[i+1:i+2]==['BUILD_ONLY'])
               for i,value in enumerate(argv))

if __name__=='__main__' and _requests_build(sys.argv[1:]):
    os.write(1,(json.dumps({'kind':'FAILED','reason':'COMPLETE_CONTROLLER_RESOURCE_ENVELOPE_NOT_IMPLEMENTED',
                           'new_ME_calls':0,'new_integrals':0,'new_events':0})+'\n').encode())
    raise SystemExit(2)
if __name__=='__main__':
    try:_ALLOCATION=allocation_guard.install()
    except BaseException as error:
        os.write(1,(json.dumps({'kind':'FAILED','reason':str(error)[:1000],
                              'phase':'ALLOCATION_GUARD_BOOTSTRAP'})+'\n').encode())
        raise SystemExit(2)
from simulation.hh_signal.final_closure.resource_closure import backend,archive_io,fixtures
from simulation.hh_signal.final_closure.integration_runtime.contract import require
_CURRENT=None
_LOCK=None


def emit(kind,**value):
    line=json.dumps({'kind':kind,**value},sort_keys=True,separators=(',',':'),allow_nan=False)
    require(len(line.encode())<=8192,'PAYLOAD_RECORD_BOUND')
    print(line,flush=True)


def journal(kind,value):
    """Lossless bounded records on the capped fixed stdout descriptor."""
    import base64,hashlib
    data=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    require(len(data)<=1048576,'JOURNAL_ENTRY_BOUND')
    pieces=[data[i:i+3072] for i in range(0,len(data),3072)] or [b'']
    digest=hashlib.sha256(data).hexdigest()
    for i,piece in enumerate(pieces):
        emit('JOURNAL_PART',entry_kind=kind,part=i,parts=len(pieces),
             full_sha256=digest,base64=base64.b64encode(piece).decode('ascii'))


def descriptors(profile,mode):
    global _LOCK
    names=os.environ.get('LISTEN_FDNAMES','').split(':')
    expected=['chunk_'+format(i,'02d') for i in range(profile['artifact_chunks'])]+['index']
    if mode=='BUILD_ONLY':expected+=['human_tty']
    expected+=['campaign_lock']
    require(os.environ.get('LISTEN_PID')==str(os.getpid()) and names==expected and
            int(os.environ.get('LISTEN_FDS','0'))==len(expected),'PINNED_DESCRIPTOR_TRANSPORT_REQUIRED')
    result={name:3+i for i,name in enumerate(names)}
    inodes=set()
    for name,fd in result.items():
        fcntl.fcntl(fd,fcntl.F_SETFD,fcntl.fcntl(fd,fcntl.F_GETFD)|fcntl.FD_CLOEXEC)
        if name=='human_tty':continue
        if name=='campaign_lock':
            path=Path.home()/'simulations/.resource_envelope.lock';info=os.fstat(fd);original=path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and
                    info.st_size==0 and (info.st_dev,info.st_ino)==(original.st_dev,original.st_ino) and
                    fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDONLY,
                    'READONLY_CANONICAL_JOB_LOCK_REQUIRED')
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError('ANOTHER_ENCLOSED_JOB_ACTIVE')
            _LOCK={'acquired':True,'pid':os.getpid(),'read_only':True,'path':str(path),
                   'dev':info.st_dev,'inode':info.st_ino}
            continue
        info=os.fstat(fd);path=Path.cwd().parent/(name+'.bin')
        original=path.lstat();key=(info.st_dev,info.st_ino)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and
                key==(original.st_dev,original.st_ino) and key not in inodes and info.st_size==0,
                'ACTUAL_DESCRIPTOR_IDENTITY_OR_FRESHNESS_MISMATCH')
        inodes.add(key)
    return result


def attest(mode,source_identity):
    require(_ALLOCATION is not None and _ALLOCATION.get('pid')==os.getpid() and
            _ALLOCATION.get('program_sha256')==allocation_guard.program_identity(),'LIVE_INHERITED_ALLOCATION_FILTER_REQUIRED')
    profile=backend.load_profile(mode);work=Path.cwd()
    require(work.name=='work' and work.is_absolute(),'PRIVATE_WORK_DIRECTORY_REQUIRED')
    root=Path.home()/'simulations'/('hh_phase7i_resource_closure' if mode=='fixture' else 'hh_final_closure')
    require(work.is_relative_to(root) and not any(p.is_symlink() for p in (work,*work.parents)),
            'OWNED_EXECUTION_NAMESPACE_REQUIRED')
    fds=descriptors(profile,mode)
    rows=Path('/proc/self/cgroup').read_text().splitlines()
    require(len(rows)==1 and rows[0].startswith('0::'),'UNIFIED_CGROUP_REQUIRED')
    relative=rows[0][3:];unit=Path(relative).name;cg=backend.owned_cgroup(unit,relative)
    raw=backend.cgroup_read(cg)
    require(raw.get('cpu.max','').strip()==f"{profile['cpu_quota_percent']*profile['cpu_quota_period_usec']//100} {profile['cpu_quota_period_usec']}",
            'EFFECTIVE_CPU_QUOTA_MISMATCH')
    for field,target in [('cpu.max.burst',0),('memory.max',profile['aggregate_memory_bytes']),
                         ('memory.swap.max',0),('memory.oom.group',1),('pids.max',profile['max_tasks'])]:
        require(raw.get(field,'').strip()==str(target),'EFFECTIVE_'+field+'_MISMATCH')
    require(len(os.sched_getaffinity(0))==1,'SINGLE_CPU_AFFINITY_REQUIRED')
    require(bool(os.statvfs(REPO).f_flag&os.ST_RDONLY) and bool(os.statvfs(cg).f_flag&os.ST_RDONLY),'SOURCE_AND_CGROUP_READONLY_REQUIRED')
    limits={}
    for name,kind,value in [('AS',resource.RLIMIT_AS,profile['per_process_address_space_bytes']),
                           ('CPU',resource.RLIMIT_CPU,profile['per_process_CPU_seconds']),
                           ('FSIZE',resource.RLIMIT_FSIZE,profile['per_regular_file_bytes']),
                           ('CORE',resource.RLIMIT_CORE,0)]:
        limits[name]=list(resource.getrlimit(kind));require(limits[name]==[value,value],'EFFECTIVE_RLIMIT_'+name)
    mounts=[]
    for path,bytecap,inodecap in [(work,profile['work_tmpfs_bytes'],profile['work_tmpfs_inodes']),
                                 (Path('/tmp'),profile['tmp_tmpfs_bytes'],profile['tmp_tmpfs_inodes'])]:
        match=[line.split() for line in Path('/proc/self/mountinfo').read_text().splitlines()
               if len(line.split())>6 and line.split()[4]==str(path)]
        require(len(match)==1 and match[0][match[0].index('-')+1]=='tmpfs','PRIVATE_TMPFS_MOUNT_REQUIRED')
        v=os.statvfs(path)
        require(v.f_blocks*v.f_frsize==bytecap and v.f_files==inodecap,'EFFECTIVE_TMPFS_CAP_MISMATCH')
        require('nosuid' in match[0][5].split(',') and 'nodev' in match[0][5].split(','),'TMPFS_SECURITY_FLAGS')
        if path==Path('/tmp') or not profile['work_executable']:
            require('noexec' in match[0][5].split(','),'TMPFS_NOEXEC_REQUIRED')
        mounts.append({'path':str(path),'bytes':bytecap,'inodes':inodecap,'filesystem':'tmpfs'})
    writable=[]
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields=line.split()
        if 'rw' in fields[5].split(','):writable.append(fields[4])
    require(set(writable)=={str(work),'/tmp'},'UNACCOUNTED_WRITABLE_MOUNT')
    current=backend.source_snapshot()
    require(current['identity']==source_identity,'PAYLOAD_SOURCE_IDENTITY_MISMATCH')
    fact={'valid':True,'exclusive_job_lock':_LOCK,'allocation_guard':_ALLOCATION,'mode':mode,'pid':os.getpid(),'cgroup':str(cg),'source_identity':source_identity,
          'profile_identity':backend.canonical(profile),'limits':limits,'mounts':mounts,
          'repository_readonly':bool(os.statvfs(REPO).f_flag&os.ST_RDONLY),
          'cgroup_readonly':bool(os.statvfs(cg).f_flag&os.ST_RDONLY),
          'affinity_count':len(os.sched_getaffinity(0)),'writable_mounts':sorted(writable),
          'effective':{k:raw[k].strip() for k in ('cpu.max','cpu.max.burst','memory.max','memory.swap.max','memory.oom.group','pids.max')},
          'bounds':backend.profile_bounds(profile)}
    emit('ATTESTED',**fact)
    return {'profile':profile,'work':work,'fds':fds,'cgroup':cg,'fact':fact,'mode':mode,'pid':os.getpid()}


def require_build_enclosure(root):
    """Full controller is unimplemented; no profile/receipt/approval overrides it."""
    require(False,'COMPLETE_CONTROLLER_RESOURCE_ENVELOPE_NOT_IMPLEMENTED')
    require(_CURRENT is not None and _CURRENT['mode']=='BUILD_ONLY' and
            _CURRENT['pid']==os.getpid(),'FULL_BUILD_RESOURCE_ENCLOSURE_REQUIRED')
    require(Path(root)==_CURRENT['work']/'build','BUILD_ROOT_OUTSIDE_PRIVATE_TMPFS')
    checked=attest('BUILD_ONLY',_CURRENT['fact']['source_identity'])
    require(checked['cgroup']==_CURRENT['cgroup'],'ENCLOSURE_CGROUP_CHANGED')
    return checked['fact']


def run_fixture(case,state):
    from simulation.hh_signal.final_closure.integration_runtime import build_process
    from simulation.hh_signal.final_closure.integration_runtime.containment import Budget
    from simulation.hh_signal.final_closure.integration_runtime.contract import check_revision
    work=state['work']; tree=work/'fixture';tree.mkdir();budget=Budget(tree)
    chunks=[state['fds']['chunk_'+format(i,'02d')] for i in range(2)]
    def write_json(name,value):
        data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
        require(len(data)<65536,'FIXTURE_RECEIPT_BOUND');(tree/name).write_bytes(data)
    def fixed_child(argv):
        try:
            result,measured=build_process.invoke(argv,tree,backend.host_env(),budget)
            emit('CHILD_MEASURED',**measured);return result
        except BaseException as exc:
            if hasattr(exc,'build_measurement'):emit('CHILD_MEASURED',**exc.build_measurement)
            raise
    def preflight(ctx):
        # This is the actual full tracked-worktree reader, with no native call.
        import subprocess
        revision=subprocess.check_output(['/usr/bin/git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        result=check_revision(revision,full=True)
        write_json('preflight.json',{'status':result['git_preflight']['status'],
                                   'revision':revision,'identity':backend.canonical(result)})
    def compile_fixture(ctx):
        fixed_child(['/usr/bin/python3','-I','-B','-c',
                     "from pathlib import Path;Path('inert_object.txt').write_text('fixed harmless object\\n')"])
    def loader_fixture(ctx):
        result=fixed_child(['/usr/bin/python3','-I','-B','-c',
                            "from pathlib import Path;print(Path('inert_object.txt').read_text().strip())"])
        require(result.stdout.strip()=='fixed harmless object','INERT_READBACK_MISMATCH')
    def receipt(ctx):write_json('receipt.json',{'status':'INERT_FULL_WORKFLOW_ONLY',**fixtures.ZERO})
    def postflight(ctx):
        require(backend.source_snapshot()['identity']==state['fact']['source_identity'],'SOURCE_DRIFT')
        require(json.loads((tree/'receipt.json').read_text())['new_ME_calls']==0,'ZERO_DECLARATION_DRIFT')
        write_json('postflight.json',{'status':'INERT_SOURCE_AND_RECEIPT_READBACK'})
    def export(ctx):
        summary=archive_io.write_archive(tree,chunks,index_fd=state['fds']['index'])
        index=archive_io.read_archive_index(state['fds']['index'],expected_sha256=summary['index_sha256'])
        checked=archive_io.verify_archive(chunks,index,receipt_names=('receipt.json',))
        emit('ARCHIVE_VERIFIED',index_sha256=summary['index_sha256'],member_count=len(index['members']))
    def child_action(mode,ctx):
        return fixed_child(['/usr/bin/python3','-I','-B',str(HERE/'fixtures.py'),'--action',mode])
    def missing(ctx):
        from simulation.hh_signal.final_closure.integration_runtime.build import prepare
        from simulation.hh_signal.final_closure.integration_runtime.approval import verify
        # Negative only: neither construct nor accept a HumanReview.
        for call in [lambda:verify(None,{}),lambda:prepare(Path.home()/'simulations/hh_final_closure/inert_denial_never_created',
                                                         revision='0'*40,build_review=None)]:
            try:call()
            except ValueError as exc:
                require(str(exc)=='SEPARATE_HUMAN_REVIEW_REQUIRED_NOT_EDITABLE_DATA','LEGACY_DENIAL_REASON_CHANGED')
            else:raise ValueError('MISSING_HUMAN_APPROVAL_ACCEPTED')
        return True
    def archive_bound(ctx):
        q=work/'overlarge';q.mkdir()
        for i in range(3):(q/('inert_'+str(i))).write_bytes(b'X'*65536)
        archive_io.write_archive(q,chunks,index_fd=state['fds']['index'])
    ctx={'work':work,'emit':emit,'source_canary':work.parent/'readonly_canary.txt',
         'cgroup_path':state['cgroup'],'chunk_fds':chunks,'child_action':child_action,
         'legacy_missing_approval':missing,'archive_bound':archive_bound,
         'allocation_bypass':lambda ctx:allocation_guard.probe(chunks,work),
         'job_lock':lambda ctx:probe_job_lock(state),
         'phase_callbacks':dict(zip(fixtures.PHASES,(preflight,compile_fixture,loader_fixture,receipt,postflight,export)))}
    return fixtures.run_fixture(case,ctx)


def probe_job_lock(state):
    """Future fixed negative; a separate open description must be denied."""
    path=Path.home()/'simulations/.resource_envelope.lock'
    require(_LOCK is not None and _LOCK['pid']==os.getpid(),'LIVE_JOB_OWNER_REQUIRED')
    owner=os.getpid();reader,writer=os.pipe2(os.O_CLOEXEC);child=os.fork()
    if child==0:
        os.close(reader)
        try:
            os.close(state['fds']['campaign_lock'])
            other=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
            try:
                info=os.fstat(other)
                require((info.st_dev,info.st_ino)==(_LOCK['dev'],_LOCK['inode']),'LOCK_INODE_CHANGED')
                try:fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError as error:
                    result={'owner_pid':owner,'separate_open_description':True,'denied':True,
                            'errno':error.errno,'path':str(path)}
                else:result={'denied':False,'reason':'SECOND_JOB_LOCK_ACCEPTED'}
            finally:os.close(other)
        except BaseException as error:result={'denied':False,'reason':str(error)[:500]}
        os.write(writer,json.dumps(result).encode());os.close(writer);os._exit(0)
    os.close(writer)
    try:
        data=os.read(reader,2048);pid,status=os.waitpid(child,0)
        require(pid==child and status==0,'JOB_LOCK_PROBE_CHILD_FAILED')
        return json.loads(data)
    finally:os.close(reader)


def run_build(args,state):
    """Non-executable transport proposal pending full controller implementation."""
    require(False,'COMPLETE_CONTROLLER_RESOURCE_ENVELOPE_NOT_IMPLEMENTED')
    from simulation.hh_signal.final_closure.integration_runtime.approval import confirm_fd,scope
    from simulation.hh_signal.final_closure.integration_runtime.route_a import full_sources
    from simulation.hh_signal.final_closure.integration_runtime.build import prepare
    tty=state['fds']['human_tty'];info=os.fstat(tty)
    require(os.isatty(tty) and stat.S_ISCHR(info.st_mode) and
            info.st_rdev==args.tty_rdev and info.st_ino==args.tty_inode,'PINNED_CALLER_TTY_IDENTITY_MISMATCH')
    root=state['work']/'build'
    # All source preflight, cloning, compiler and formal zero-ME checks occur
    # only after external review plus this actual manual same-PID boundary.
    review=confirm_fd(scope('BUILD_ONLY',args.revision,root,full_sources()),tty)
    emit('BUILD_PREPARE_ENTERED',revision=args.revision)
    result=prepare(root,revision=args.revision,build_review=review)
    summary=archive_io.write_archive(root,[state['fds']['chunk_'+format(i,'02d')]
                  for i in range(state['profile']['artifact_chunks'])],
                  limits=archive_io.BUILD_ONLY_LIMITS,index_fd=state['fds']['index'])
    index=archive_io.read_archive_index(state['fds']['index'],limits=archive_io.BUILD_ONLY_LIMITS,expected_sha256=summary['index_sha256'])
    archive_io.verify_archive([state['fds']['chunk_'+format(i,'02d')] for i in range(state['profile']['artifact_chunks'])],
        index,limits=archive_io.BUILD_ONLY_LIMITS,receipt_names=('review_build.json',))
    require(result['new_ME_calls']==result['new_integrals']==result['retained_physical_events']==0,'FORMAL_ZERO_ME_COUNTER_GATE')
    emit('BUILD_ONLY_COMPLETE',native_zero_ME_verified=True,archive=summary,new_ME_calls=result['new_ME_calls'],
         new_integrals=result['new_integrals'],retained_physical_events=result['retained_physical_events'])
    return result


def main(argv=None):
    global _CURRENT
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--mode',required=True,choices=('fixture','BUILD_ONLY'))
    p.add_argument('--case',required=True,choices=fixtures.CASES)
    p.add_argument('--source-identity',required=True)
    p.add_argument('--revision');p.add_argument('--tty-rdev',type=int);p.add_argument('--tty-inode',type=int)
    args=p.parse_args(argv)
    signal.signal(signal.SIGXFSZ,signal.SIG_DFL);signal.signal(signal.SIGXCPU,signal.SIG_DFL)
    try:
        state=attest(args.mode,args.source_identity);_CURRENT=state
        if args.mode=='fixture':run_fixture(args.case,state)
        else:run_build(args,state)
        return 0
    except BaseException as exc:
        emit('FAILED',reason=str(exc)[:1500],error_type=type(exc).__name__)
        return 2
    finally:_CURRENT=None

if __name__=='__main__':raise SystemExit(main())
