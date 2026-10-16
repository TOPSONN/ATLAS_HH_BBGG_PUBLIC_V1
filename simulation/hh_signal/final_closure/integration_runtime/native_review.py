"""Independent native synthetic point/observer checks, with no ME library link."""
import os,re,subprocess,sys
from .contract import *
from .overlay import apply
from .build import CHANGED
from simulation.hh_signal.semantics_recovery.runner import command
from simulation.hh_signal.campaign.common import mg_environment
from simulation.hh_signal.integration_audit.audit import save

PROBE='''      program point_method_only
      use hi_statistics
      implicit none
      include 'genps.inc'
      include 'nexternal.inc'
      include 'run.inc'
      include 'coupl.inc'
      real*8 p(0:3,nexternal),a,g1,g2
      character*20 mode
      call get_command_argument(1,mode)
      p=0d0
      p(0,1)=125d0
      p(0,2)=125d0
      p(3,1)=125d0
      p(3,2)=-125d0
      p(0,3)=125d0
      p(0,4)=125d0
      MU_R=125d0
      q2fact=125d0**2
      a=1d0/(1d0/.13d0+(23d0/3d0)/(8d0*atan(1d0))*
     $ log(125d0/91.188d0))
      G=sqrt(16d0*atan(1d0)*a)
      g1=.2d0
      g2=.3d0
      if(mode.eq.'ren_scale') MU_R=126d0
      if(mode.eq.'fac_scale') q2fact(1)=126d0**2
      if(mode.eq.'alpha') G=G*1.01d0
      if(mode.eq.'pdf') g1=-1d0
      if(mode.eq.'nan') G=ieee_value(1d0,ieee_quiet_nan)
      call hi_point(p,g1,g2)
      if(points.ne.1) stop 99
      write(*,*) 'HI_SYNTHETIC_POINT_PASS_NO_ME_LIBRARY'
      end
'''

def projection(original,transformed):
    """Undo only enumerated observations/I/O changes; require byte equality."""
    projected={}
    for rel,text in transformed.items():
        if rel.endswith('/driver.f'):continue  # entry/control protocol intentionally differs
        if rel=='Source/dsample.f':
            text=text.replace('               call hi_integrand\n','')
            text=text.replace('            call hi_iteration(cur_it,events,kn,mean,sigma,rmean)\n','')
            text=text.replace('      call hi_result(trmean,tsigma,chi2,cur_it-1,kevent,nw,nun)\n','')
            text=text.replace('      call hh_open_sink(67)',"      open(unit=67,file='events.lhe',status='unknown')")
        elif rel=='SubProcesses/unwgt.f':
            text=text.replace('      call hi_tail(nw,i,nover,th_nunwgt,xover,xtot,\n     $ target_wgt,th_maxwgt)\n','')
            text=text.replace('      call hh_open_sink(lunw)',"      open(unit = lunw, file='events.lhe', status='unknown')")
        elif rel=='Source/rw_events.f':
            text=text.replace('         call hh_open_sink(lun_ban)',"         open (unit=lun_ban, status='scratch')")
            text=text.replace('      call hh_require_transient(lun)\n      call hi_writer\n','')
        elif rel=='Source/ranmar.f':
            text=text.replace('        call hi_seed(iseed/31300_8,ioffset,joffset,\n     $ jconfig,ij,kl)\n','')
        elif rel.endswith('/matrix1.f'):
            text=re.sub(r'(?m)^ +CALL hi_me_enter\n','',text)
            text=text.replace('      call hi_loop(RETURN_CODE,FINITE,ONEEPS,TWOEPS,PREC)\n','')
        elif rel.endswith('/auto_dsig1.f'):text=text.replace('      CALL hi_point(PP,G1,G2)\n      ','      ')
        require(text==original[rel],'COMPUTATIONAL_SOURCE_PROJECTION_FAILED:'+rel)
        projected[rel]=__import__('hashlib').sha256(text.encode()).hexdigest()
    return projected

def review(out):
    out=safe_root(out);require(not out.exists(),'PRESERVE_EXISTING_NATIVE_REVIEW');out.mkdir(parents=True)
    native=Path.home()/'simulations/hh_signal_runs/campaign_01/7b/source/process'
    original={r:(native/r).read_text() for r in CHANGED};p=projection(original,apply(original,910001))
    cfg=read_json(REPO/'.local/mg5_installation.json');env=mg_environment(cfg)
    fc=Path(cfg['toolchain_prefix'])/'bin/x86_64-conda-linux-gnu-gfortran';sub=native/'SubProcesses/P0_gg_hh'
    (out/'probe.f').write_text(PROBE)
    flags=[fc,'-O0','-std=legacy','-ffixed-line-length-none','-ffree-line-length-none','-ffunction-sections','-fdata-sections',
        '-I'+str(sub),'-I'+str(native/'Source'),'-I'+str(native/'Source/MODEL'),'-J'+str(out)]
    exe=out/'point_method_only'
    command([*flags,HERE/'observers.f90',HERE/'native_checks.f',out/'probe.f','-Wl,--gc-sections','-o',exe],out,env)
    symbols=subprocess.check_output(['nm','--defined-only',str(exe)],text=True,timeout=30)
    require(not re.search(r'\b\w*(?:sloopmatrix|smatrix1|sample_full)\w*\b',symbols,re.I),'PHYSICAL_ME_OR_SURVEY_IN_METHOD_BINARY')
    cases=[]
    for mode,expected in [('valid',0),('ren_scale',92),('fac_scale',92),('alpha',92),('pdf',92),('nan',90)]:
        r,_=command([exe,mode],out,env,expected=expected)
        cases.append({'mode':mode,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    cc=str(fc).replace('gfortran','gcc');library=out/'control.so'
    command([cc,'-shared','-fPIC',HERE/'control.c','-o',library],out,env)
    from .containment import capability
    fd=capability(910001,'a'*40)
    try:
        code='import ctypes,os;f=ctypes.CDLL(os.environ["TEST_LIBRARY"]).hi_check_parent;f.argtypes=[ctypes.c_int64];print(f(910001),f(910019))'
        r=subprocess.run([sys.executable,'-B','-c',code],env={**env,'TEST_LIBRARY':str(library),'HH_SUPERVISOR_FD':str(fd)},
            pass_fds=(fd,),capture_output=True,text=True,timeout=10,start_new_session=True)
        require(r.returncode==0 and r.stdout.strip()=='1 0','NATIVE_SEALED_SUPERVISOR_CONTROL')
    finally:os.close(fd)
    result={'status':'PASS_INDEPENDENT_NATIVE_METHOD_ONLY_REVIEW','source_identity':sources(),
        'computational_source_projection':p,'synthetic_point_cases':cases,'control_native_positive_and_wrong_seed':'PASS_C_API_ONLY',
        'method_executable_sha256':sha(exe),'no_ME_or_sampler_symbols':True,'new_genuine_ME_calls':0,'new_integrals':0}
    save(out/'native_review.json',result);return result

if __name__=='__main__':print(json.dumps(review(sys.argv[1]),indent=2))
