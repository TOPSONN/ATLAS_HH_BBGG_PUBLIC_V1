"""Small isolated observers and I/O boundary changes; no estimator replacement."""
import re
from .contract import *
from simulation.hh_signal.semantics_recovery.overlay import replace_once
from simulation.hh_signal.config_lock.controller import patch_driver

def apply(original,seed):
    out=dict(original)
    d=patch_driver(out['SubProcesses/P0_gg_hh/driver.f'],seed)
    # Preserve the historical F/G guard sources. Only this isolated new route
    # admits a supervisor capability, after separately reviewed revision approval.
    d=replace_once(d,"      write(*,*) 'HH_INTEGRATION_NOT_AUTHORIZED'\n      stop 80\n",
        '      call hi_control_gate('+str(seed)+'_8)\n')
    # Move initialization-only exit after native input parsing, before mapping
    # or sampling. INIT_GOOD_HEL is source-verified to contain no ME calls.
    old="      if(hh_probe_mode.eq.'1') then\n      call hh_guard_report\n      write(*,*) 'HH_NATIVE_PREFLIGHT_ONLY_ZERO_ME_CALLS'\n      stop\n      endif\n"
    d=replace_once(d,old,'')
    d=replace_once(d,'      call hi_control_gate('+str(seed)+'_8)',
        "      if(hh_probe_mode.ne.'1') call hi_control_gate("+str(seed)+'_8)')
    at='      call get_user_params(ncall,itmax,itmin,mincfig)'
    d=replace_once(d,at,at+'\n      call hi_inputs(ncall,itmax,itmin)\n'+
        "      if(hh_probe_mode.eq.'1') then\n      call hi_config\n      call hh_io_report\n"+
        "      write(*,*) 'HI_PREFLIGHT_ZERO_ME'\n      stop\n      endif\n      call hi_config")
    d=replace_once(d,"      open(unit=lun,status='scratch')",'      call hh_open_sink(lun)')
    d=replace_once(d,'      close(lun)\n      end','      close(lun)\n      call hi_finish\n      call hh_io_report\n      end')
    d=replace_once(d,'      call sample_full(ndim,ncall,itmax,itmin,dsig,ninvar,nconfigs)',
        '      call hi_endpoint(ncall,itmax,itmin)\n      call sample_full(ndim,ncall,itmax,itmin,dsig,ninvar,nconfigs)')
    out['SubProcesses/P0_gg_hh/driver.f']=d
    ds=out['Source/dsample.f']
    require(ds.count('               fx = dsig(p,wgt,0) !Evaluate function')==2,'DSIG_OBSERVER_BOUNDARIES')
    ds=ds.replace('               fx = dsig(p,wgt,0) !Evaluate function',
        '               call hi_integrand\n               fx = dsig(p,wgt,0) !Evaluate function')
    ds=replace_once(ds,'            write(*,222) \'Iteration\',cur_it,\'Mean: \',rmean,',
        '            call hi_iteration(cur_it,events,kn,mean,sigma,rmean)\n'+
        '            write(*,222) \'Iteration\',cur_it,\'Mean: \',rmean,')
    require(ds.count('      if (chi2 .gt. 1) tsigma=tsigma*sqrt(chi2)')==2,'RESULT_OBSERVER_BOUNDARIES')
    ds=ds.replace('      if (chi2 .gt. 1) tsigma=tsigma*sqrt(chi2)',
        '      if (chi2 .gt. 1) tsigma=tsigma*sqrt(chi2)\n      call hi_result(trmean,tsigma,chi2,cur_it-1,kevent,nw,nun)')
    ds=replace_once(ds,"      open(unit=67,file='events.lhe',status='unknown')",'      call hh_open_sink(67)')
    out['Source/dsample.f']=ds
    u=out['SubProcesses/unwgt.f']
    u=replace_once(u,"      open(unit = lunw, file='events.lhe', status='unknown')",'      call hh_open_sink(lunw)')
    u=replace_once(u,'      neventswritten = i',
        '      call hi_tail(nw,i,nover,th_nunwgt,xover,xtot,\n     $ target_wgt,th_maxwgt)\n      neventswritten = i')
    out['SubProcesses/unwgt.f']=u
    rw=replace_once(out['Source/rw_events.f'],"         open (unit=lun_ban, status='scratch')",'         call hh_open_sink(lun_ban)')
    at=rw.index("      write(lun,'(a)') '<event>'",rw.index('      subroutine write_event(lun,'))
    rw=rw[:at]+'      call hh_require_transient(lun)\n      call hi_writer\n'+rw[at:]
    out['Source/rw_events.f']=rw
    r=out['Source/ranmar.f']
    r=replace_once(r,'        call rmarin(ij,kl)',
        '        call hi_seed(iseed/31300_8,ioffset,joffset,\n     $ jconfig,ij,kl)\n        call rmarin(ij,kl)')
    out['Source/ranmar.f']=r
    m=out['SubProcesses/P0_gg_hh/matrix1.f']
    m,count=re.subn(r'(?m)^( +)CALL CPU_TIME\(T_BEFORE\)$',
        lambda z:z[1]+'CALL hi_me_enter\n'+z[0],m)
    require(count==3,'LOOP_ENTRY_BOUNDARIES_CHANGED')
    m=replace_once(m,'      H_RETURN_CODES(H) = H_RETURN_CODES(H)+1',
        '      H_RETURN_CODES(H) = H_RETURN_CODES(H)+1\n      call hi_loop(RETURN_CODE,FINITE,ONEEPS,TWOEPS,PREC)')
    out['SubProcesses/P0_gg_hh/matrix1.f']=m
    a=out['SubProcesses/P0_gg_hh/auto_dsig1.f']
    a=replace_once(a,'      CALL SMATRIX1(P1,DSIGUU)',
        '      CALL hi_point(PP,G1,G2)\n      CALL SMATRIX1(P1,DSIGUU)')
    out['SubProcesses/P0_gg_hh/auto_dsig1.f']=a
    return out
