      program hh_nonphysical_kernel_replay
      implicit none
      include 'genps.inc'
      include 'nexternal.inc'
      include 'maxamps.inc'
      include 'run.inc'
      include 'run_config.inc'
      include 'cluster.inc'
      include 'coupl.inc'
      include 'lhe_event_infos.inc'
      include 'message.inc'
      double precision twgt,maxwgt,swgt(maxevents)
      integer lun,nw,itmin
      common/to_unwgt/twgt,maxwgt,swgt,lun,nw,itmin
      double precision tmean,trmean,tsigma
      integer dim,events,itm,kn,cur_it,invar,configs
      common/sample_common/tmean,trmean,tsigma,dim,events,itm,kn,
     $ cur_it,invar,configs
      double precision mean,rmean,sigma
      common/to_result/mean,rmean,sigma
      double precision grid(2,ng,0:maxinvar),grid2(0:ng,maxinvar)
      integer inon_zero(ng,maxinvar),non_zero
      common/data_grid/grid
      common/to_grid2/grid2,inon_zero,non_zero
      integer lastbin(maxdim)
      common/to_lastbin/lastbin
      double precision accur
      common/to_accuracy/accur
      integer use_cut
      common/to_weight/use_cut
      integer th_nunwgt,neventswritten
      double precision th_maxwgt
      common/theoretical_unwgt_max/th_maxwgt,th_nunwgt
      common/to_eventswritten/neventswritten
      integer isum_hel
      logical multi_channel,init_mode
      common/to_matrix/isum_hel,multi_channel
      common/to_determine_zero_hel/init_mode
      double precision amp2(maxamps),jamp2(0:maxflow)
      common/to_amps/amp2,jamp2
      integer ipsel,imirror,iproc,mincfig,maxcfig
      common/SubProc/ipsel
      common/to_mirror/imirror,iproc
      common/to_configs/mincfig,maxcfig
      character*101 hel_buf
      common/to_helicity/hel_buf
      double precision stot,m1,m2,bias_weight
      logical impact_xsec
      common/to_stot/stot,m1,m2
      common/bias/bias_weight,impact_xsec
      double precision pmass(nexternal)
      common/to_mass/pmass
      double precision point(maxinvar),p(0:3,nexternal),w,r,v
      double precision xmean(99),xsigma(99),xwmax(99),xeff(99),xrmean(99)
      common/to_iterations/xmean,xsigma,xwmax,xeff,xrmean
      integer i,j,step,oldit,before_nw,seed,iterations
      real ran1,xran1,discard
      character*32 mode,side
      call get_command_argument(1,mode)
      call get_command_argument(2,side)
      write(*,*) 'METHOD_ONLY_FIXED_STREAM_NO_PHASESPACE_NO_ME'
      twgt=0.0001d0
      maxwgt=0d0
      nw=0
      swgt=0d0
      lun=27
      itmin=4
      iterations=4
      use_cut=2
      accur=0d0
      if(mode.eq.'measurement') then
        use_cut=0
        iterations=3
        itmin=3
      endif
      if(mode.eq.'negative_accuracy') then
        accur=-.001d0
        itmin=1
      endif
      if(mode.eq.'positive_accuracy') then
        accur=.9d0
        itmin=1
      endif
      th_maxwgt=0d0
      th_nunwgt=0
      neventswritten=0
      xmean=0d0
      xsigma=0d0
      xwmax=0d0
      xeff=0d0
      xrmean=0d0
      isum_hel=0
      multi_channel=.true.
      MC_GROUPED_SUBPROC=.false.
      init_mode=.false.
      AlreadySetInBiasModule=.false.
      ipsel=1
      imirror=1
      iproc=1
      mincfig=1
      maxcfig=1
      jamp2=1d0
      amp2=1d0
      write(hel_buf,'(20i5)') (1,i=1,nexternal)
      ickkw=0
      use_syst=.false.
      clusinfo=.false.
      icluster=0
      ptclus=0d0
      lpp=1
      ebeam=2d0
      xbk=.5d0
      q2fact=1d0
      pmass=0d0
      m1=0d0
      m2=0d0
      stot=16d0
      g=1d0
      gal=1d0
      lhe_version=3d0
      impact_xsec=.true.
      bias_weight=1d0
      if(side.eq.'A') then
        call hh_open_reference(lun)
      else
        call hh_open_sink(lun)
      endif
      if(mode.eq.'deny_permanent') then
        call write_event(6,pb(0,1),1d0,nexternal,jpart(1,1),
     $   1,1d0,1d0,1d0,buff,use_syst,s_buff,nclus,buffclus)
        stop 99
      endif
      if(mode.eq.'deny_transient') then
        open(unit=99,file='UNREVIEWED_EMPTY_METHOD_FIXTURE')
        call write_event(99,pb(0,1),1d0,nexternal,jpart(1,1),
     $   1,1d0,1d0,1d0,buff,use_syst,s_buff,nclus,buffclus)
        stop 99
      endif
      if(mode.eq.'deny_rebound') then
        call hh_open_sink(25)
        close(25)
        open(unit=25,file='UNREVIEWED_REBOUND_EMPTY_FIXTURE')
        call write_event(25,pb(0,1),1d0,nexternal,jpart(1,1),
     $   1,1d0,1d0,1d0,buff,use_syst,s_buff,nclus,buffclus)
        stop 99
      endif
      if(mode.eq.'deny_rebound_scratch') then
        call hh_open_sink(25)
        close(25)
        open(unit=25,status='scratch')
        call write_event(25,pb(0,1),1d0,nexternal,jpart(1,1),
     $   1,1d0,1d0,1d0,buff,use_syst,s_buff,nclus,buffclus)
        stop 99
      endif
      if(mode.eq.'candidate_limit') then
        nw=maxevents
        p=0d0
        call write_leshouche(p,1d0,1,.true.)
        write(*,*) 'H_CANDIDATE_LIMIT',nw,maxevents
        call hh_io_report()
        stop
      endif
      call rmarin(1802,9373)
      call sample_init(4,250,iterations,4,1)
      point=0d0
      step=0
      do while(cur_it.le.itm)
        step=step+1
        if(step.gt.10000) stop 90
        oldit=cur_it
        call ranmar(r)
        ! Predeclared fixed weights, deliberately not physical kinematics.
        v=1d0+mod(step,7)
        if(mod(step,997).eq.0) v=30d0
        if(mod(step,11).eq.0) v=-v
        if(mod(step,13).eq.0) v=0d0
        if(mode.eq.'none_pass') v=0d0
        w=v/dble(events*itm)
        p=0d0
        p(0,1)=1d0
        p(3,1)=1d0
        p(0,2)=1d0
        p(3,2)=-1d0
        p(0,3)=.3d0
        p(1,3)=.7d0
        p(0,4)=.9d0
        p(2,4)=.4d0
        before_nw=nw
        call unwgt(p,w,1)
        if(nw.gt.before_nw) then
          write(*,*) 'H_CANDIDATE',step,nw
          call hh_real4('CANDIDATE',swgt(nw),w,0d0,0d0)
        endif
        if(mode.eq.'forced_secondary_store'.and.step.eq.64) then
          call store_events(.005d0,.false.)
        endif
        do j=1,4
          lastbin(j)=1+mod(step-1+7*(j-1),ng)
          point(j)=-1d0+2d0*(lastbin(j)-.5d0)/ng
        enddo
        nb_pass_cuts=step
        call sample_put_point(w,point,cur_it,1)
        write(*,*) 'H_POINT',step,cur_it,events,kn,nw,non_zero,
     $   th_nunwgt,neventswritten
        call hh_real4('SUM',mean,rmean,sigma,twgt)
        call hh_real4('TOTAL',tmean,trmean,tsigma,maxwgt)
        call hh_real4('GRID',sum(grid(1,:,1)),sum(grid2(:,1)),
     $   th_maxwgt,0d0)
        do j=1,4
          write(*,*) 'H_BIN',j,lastbin(j),inon_zero(lastbin(j),j)
          call hh_real4('BIN',grid(1,lastbin(j),j),
     $     grid2(lastbin(j),j),point(j),0d0)
        enddo
        if(cur_it.ne.oldit) then
          write(*,*) 'H_ITERATION',oldit,cur_it,events
          call hh_real4('ITERATION',xmean(oldit),xsigma(oldit),
     $     xrmean(oldit),xwmax(oldit))
          do j=1,ng
            call hh_real4('GRID_GEOMETRY',grid(2,j,1),grid(2,j,2),
     $       grid(2,j,3),grid(2,j,4))
          enddo
        endif
      enddo
      call sample_result(mean,rmean,sigma,itmin)
      call hh_real4('RESULT',mean,rmean,sigma,th_maxwgt)
      seed=1
      do i=1,4
        discard=ran1(seed)
        discard=xran1(seed)
        call ranmar(r)
      enddo
      call hh_io_report()
      write(*,*) 'H_COMPLETE',step,cur_it,events,nw,
     $ neventswritten,th_nunwgt
      close(lun)
      end
