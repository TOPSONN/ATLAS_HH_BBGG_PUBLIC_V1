      program corrected_guard_method_only
      use hi_statistics
      use ieee_arithmetic
      implicit none
      include 'genps.inc'
      include 'nexternal.inc'
      include 'run.inc'
      include 'coupl.inc'
      include 'alfas.inc'
      real*8 p(0:3,nexternal),before(0:3,nexternal),g1,g2,q,a
      real*8 old(7),after(7),nan,inf,target,alphas,sumdot
      real*8 ranu(97),ranc,rancd,rancm,save_ran(100),random
      integer iranmr,jranmr,save_idx(2),idum1,idum2
      common/raset1/ranu,ranc,rancd,rancm
      common/raset2/iranmr,jranmr
      real ran1,xran1,x1,x2
      real*8 sumw,sumw2,grid(4),w,mean,error2
      integer candidates,stop_iter,which,i,skip
      character*16 arg
      external alphas,sumdot,ran1,xran1
      call get_command_argument(1,arg)
      read(arg,*) which
      call get_command_argument(2,arg)
      read(arg,*) skip
      target=250d0
      if(which.eq.14.or.which.eq.35.or.which.eq.36.or.
     $ which.eq.46) target=125d0
      if(which.eq.32) target=173d0
      if(which.eq.33) target=1000d0
      if(which.eq.34) target=6500d0
      p=0d0
      p(0,1)=target
      p(0,2)=target
      p(3,1)=target
      p(3,2)=-target
      if(which.eq.35.or.which.eq.36) then
        p(0,1)=6500d0
        if(which.eq.36) p(0,1)=1d12
        p(0,2)=target**2/p(0,1)
        p(3,1)=p(0,1)
        p(3,2)=-p(0,2)
      endif
      scale=dsqrt(max(0d0,sumdot(p(0,1),p(0,2),1d0)))*.5d0
      q=scale
      q2fact=scale**2
      MU_R=scale
      if(which.eq.4.or.which.eq.14.or.which.eq.32.or.
     $ which.eq.33.or.which.eq.34) MU_R=91.188d0
      asmz=.13d0
      nloop=1
      a=alphas(max(target,scale))
      G=sqrt(16d0*atan(1d0)*a)
      g1=.2d0
      g2=.3d0
      nan=ieee_value(0d0,ieee_quiet_nan)
      inf=ieee_value(0d0,ieee_positive_inf)
      select case(which)
      case(1)
        p=0d0
      case(2,22)
        g1=-.2d0
      case(3)
        g2=-.3d0
      case(5,23,24)
        scale=q*1.01d0
      case(6)
        q2fact(1)=q**2*1.01d0
      case(7)
        q2fact(2)=q**2*1.01d0
      case(8)
        G=0d0
      case(9)
        G=G*1.01d0
      case(10)
        q2fact(1)=nan
      case(11)
        q2fact(1)=inf
      case(12)
        q2fact(1)=-inf
      case(13)
        g1=0d0
        g2=0d0
      case(15)
        p(0,1)=nan
      case(16)
        scale=nan
      case(17)
        scale=inf
      case(18)
        q2fact(2)=nan
      case(19)
        q2fact(2)=inf
      case(20)
        q2fact(2)=-inf
      case(21)
        q2fact(1)=-q**2
      case(25)
        MU_R=nan
      case(26,38)
        MU_R=-1d0
      case(27)
        scale=0d0
      case(28)
        MU_R=1d0
      case(29,30)
        p(0,1)=inf
        if(which.eq.30) p(3,1)=inf
      case(31)
        G=nan
      case(37)
        MU_R=inf
      case(39)
        scale=q*(1d0+3d-11)
      case(40)
        scale=q*(1d0+3d-10)
      case(41)
        g1=nan
      case(42)
        g2=inf
      case(43)
        q2fact(2)=q**2*(1d0+8d-11)
      case(44)
        q2fact(2)=q**2*(1d0+2d-10)
      case(45)
        G=-G
      end select
      if(which.eq.22.or.which.eq.23) then
        q2fact(1)=0d0
        G=0d0
      endif
      if(which.eq.24) q2fact(1)=nan
      if(which.eq.38) g1=0d0
      q=sqrt(max(0d0,(p(0,1)+p(0,2))**2-
     $ (p(1,1)+p(1,2))**2-(p(2,1)+p(2,2))**2-
     $ (p(3,1)+p(3,2))**2))/2d0
      write(*,'(A,9(1X,ES25.16E3))') 'METHOD_INPUT',
     $ target,q,scale,MU_R,q2fact(1),q2fact(2),g1,g2,G
      call rmarin(1802,9373)
      idum1=-12345
      idum2=-67890
      do i=1,7
        call ranmar(random)
        x1=ran1(idum1)
        x2=xran1(idum2)
      enddo
      save_ran=(/ranu,ranc,rancd,rancm/)
      save_idx=(/iranmr,jranmr/)
      before=p
      old=(/G,MU_R,scale,q2fact(1),q2fact(2),g1,g2/)
      points=13
      calls=3
      loops=5
      writes=7
      entries=11
c     Artificial bookkeeping, with no physical integrand evaluation.
      sumw=0d0
      sumw2=0d0
      grid=0d0
      candidates=0
      stop_iter=0
      if(skip.eq.0) call hi_point(p,g1,g2)
      if(points.ne.14-skip) stop 93
      after=(/G,MU_R,scale,q2fact(1),q2fact(2),g1,g2/)
      if(any(transfer(old,(/0_8/),7).ne.
     $ transfer(after,(/0_8/),7))) stop 94
      if(any(transfer(before,(/0_8/),4*nexternal).ne.
     $ transfer(p,(/0_8/),4*nexternal))) stop 95
      if(any(transfer(save_ran,(/0_8/),100).ne.
     $ transfer((/ranu,ranc,rancd,rancm/),(/0_8/),100))) stop 96
      if(any(save_idx.ne.(/iranmr,jranmr/))) stop 97
      if(calls.ne.3.or.loops.ne.5.or.writes.ne.7.or.
     $ entries.ne.11) stop 98
      do i=1,64
        call ranmar(random)
        x1=ran1(idum1)
        x2=xran1(idum2)
        write(*,'(A,1X,Z16.16,2(1X,Z8.8))') 'METHOD_RNG',
     $ transfer(random,0_8),transfer(x1,0),transfer(x2,0)
        w=dble(mod(i,9)-4)/16d0
        sumw=sumw+w
        sumw2=sumw2+w*w
        grid(mod(i,4)+1)=grid(mod(i,4)+1)+w
        candidates=candidates+1
        if(i.eq.64) stop_iter=i
      enddo
      mean=sumw/dble(candidates)
      error2=(sumw2/dble(candidates)-mean**2)/dble(candidates)
      write(*,'(A,2I6,8(1X,Z16.16))') 'METHOD_STATE',
     $ candidates,stop_iter,transfer(sumw,0_8),transfer(sumw2,0_8),
     $ (transfer(grid(i),0_8),i=1,4),transfer(mean,0_8),
     $ transfer(error2,0_8)
      write(*,'(A)') 'METHOD_SUCCESS'
      flush(6)
      end
