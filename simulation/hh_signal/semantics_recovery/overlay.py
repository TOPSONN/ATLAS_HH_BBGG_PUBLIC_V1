"""Hash-checked isolated I/O overlay; original computational bodies retained."""
import re
from .contract import require,sha,identity
from simulation.hh_signal.config_lock.contract import lock

def replace_once(text,old,new):
    require(text.count(old)==1,'OVERLAY_BOUNDARY_NOT_UNIQUE:'+old[:65]);return text.replace(old,new)

def sources(native):
    frozen={r['path']:r['sha256'] for r in lock()['frozen_runtime_sources']+lock()['runtime_build_auxiliary']}
    paths=['Source/dsample.f','Source/ranmar.f','Source/ran1.f','Source/rw_events.f',
        'SubProcesses/unwgt.f','SubProcesses/P0_gg_hh/addmothers.f',
        'SubProcesses/P0_gg_hh/get_color.f','SubProcesses/P0_gg_hh/cluster.f','Source/DHELAS/aloha_functions.f']
    result={}
    for rel in paths:
        require(rel in frozen and sha(native/rel)==frozen[rel],'MISSING_OR_CHANGED_NATIVE_IDENTITY:'+rel)
        result[rel]=(native/rel).read_text()
    return result

def build_overlay(original,reference=False,mutation=None):
    # A: a normal named Fortran connection to an already-unlinked POSIX file.
    # B: Fortran STATUS=SCRATCH. Both retain full formatted write/read/rewind.
    boundary='hh_open_reference' if reference else 'hh_open_sink'
    out=dict(original)
    out['SubProcesses/unwgt.f']=replace_once(out['SubProcesses/unwgt.f'],
        "      open(unit = lunw, file='events.lhe', status='unknown')",'      call '+boundary+'(lunw)')
    out['Source/dsample.f']=replace_once(out['Source/dsample.f'],
        "      open(unit=67,file='events.lhe',status='unknown')",'      call '+boundary+'(67)')
    # read_event's auxiliary banner buffer is also a reviewed anonymous sink.
    out['Source/rw_events.f']=replace_once(out['Source/rw_events.f'],
        "         open (unit=lun_ban, status='scratch')",'         call '+boundary+'(lun_ban)')
    # Equal read-only instrumentation in A/B. Retains all native arithmetic.
    t=out['SubProcesses/unwgt.f']
    t=replace_once(t,'      neventswritten = i',
        "      write(*,*) 'H_TAIL',nw,i,nover,th_nunwgt\n      call hh_real4('TAIL',xover,xtot,target_wgt,th_maxwgt)\n      neventswritten = i")
    t=replace_once(t,'            th_nunwgt = th_nunwgt +1\n         endif\n      enddo',
        "            th_nunwgt = th_nunwgt +1\n         endif\n         write(*,*) 'H_ACCEPT',i,store_event(i)\n      enddo")
    out['SubProcesses/unwgt.f']=t
    # Observe complete formatted scratch content without using read_event or
    # changing bias/RNG/common state; restore the exact native rewind position.
    out['SubProcesses/unwgt.f'],count=re.subn(r'(?im)^(      rewind\(lun\))$',
        r"\1\n      call hh_trace_stream(lun)",out['SubProcesses/unwgt.f'])
    require(count==3,'NATIVE_REWIND_BOUNDARIES_CHANGED')
    ds=out['Source/dsample.f']
    ds=replace_once(ds,'            chi2 = chi2 + mean**2 * (mean**2 / sigma)',
        "            chi2 = chi2 + mean**2 * (mean**2 / sigma)\n            call hh_real4('CHI_ACCUMULATOR',chi2,tsigma,mean,sigma)")
    ds,count=re.subn(r'(?m)^( +)(tsigma = tsigma\*sqrt\([^\n]+)$',
        lambda m:m[1]+"call hh_real4('CHI_BEFORE',chi2,tsigma,tmean,trmean)\n"+m[0]+"\n"+
            m[1]+"call hh_real4('NATIVE_ERROR_AFTER',chi2,tsigma,tmean,trmean)",ds)
    require(count==3,'NATIVE_ERROR_BOUNDARIES_CHANGED')
    out['Source/dsample.f']=ds
    rw=out['Source/rw_events.f']
    start=rw.index('      subroutine write_event(lun,')
    at=rw.index("      write(lun,'(a)') '<event>'",start)
    rw=rw[:at]+"      call hh_require_transient(lun)\n      call hh_real4('SERIAL',wgt,scale,aqcd,aqed)\n"+rw[at:]
    rw=replace_once(rw,'      return\n 99   done=.true.',
        "      call hh_real4('READBACK',wgt,sscale,aqcd,aqed)\n      return\n 99   done=.true.")
    out['Source/rw_events.f']=rw
    # Expose each native RNG result without consuming an additional draw.
    out['Source/ran1.f']=re.sub(r'\bxran1\b','hh_original_xran1',out['Source/ran1.f'],flags=re.I)
    out['Source/dsample.f']=replace_once(out['Source/dsample.f'],'      function ran1(idum)','      function hh_original_ran1(idum)')
    out['Source/dsample.f']=replace_once(out['Source/dsample.f'],'      ran1=r(j)','      hh_original_ran1=r(j)')
    out['Source/ranmar.f']=replace_once(out['Source/ranmar.f'],'      subroutine ranmar(rvec)','      subroutine hh_original_ranmar(rvec)')
    if mutation:
        require(not reference,'REFERENCE_MUTATION_FORBIDDEN')
        cases={'candidate':('SubProcesses/unwgt.f','      nw = nw+1','      nw = nw'),
            'stopping':('Source/dsample.f','            if (cur_it .gt. itm) then','            if (cur_it .gt. itm-1) then'),
            'grid':('Source/dsample.f','grid(1, i, j) + abs(wgt)','grid(1, i, j) + 1.001d0*abs(wgt)'),
            'arithmetic':('Source/dsample.f','               sigma=sigma+twgt1**2','               sigma=sigma+2d0*twgt1**2'),
            'tail':('SubProcesses/unwgt.f',"      write(*,*) 'H_TAIL',nw,i,nover,th_nunwgt", "      write(*,*) 'H_TAIL',nw,i,nover,0")}
        if mutation!='aux_rng':
            require(mutation in cases,'UNKNOWN_MUTATION');path,old,new=cases[mutation];out[path]=replace_once(out[path],old,new)
    return out
