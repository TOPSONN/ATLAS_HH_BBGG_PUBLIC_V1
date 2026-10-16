      program point_method_only
      use hi_statistics
      use ieee_arithmetic
      implicit none
      include 'genps.inc'
      include 'nexternal.inc'
      include 'run.inc'
      include 'coupl.inc'
      real*8 p(0:3,nexternal),before(0:3,nexternal),g1,g2,q,a
      real*8 weight,grid,old(9),after(9),nan,inf
      integer which,i
      integer*8 rng,candidates
      character*16 arg
      call get_command_argument(1,arg)
      read(arg,*) which
      q=250d0
      p=0d0
      p(0,1)=q
      p(0,2)=q
      p(3,1)=q
      p(3,2)=-q
      g1=.2d0
      g2=.3d0
      scale=q
      MU_R=q
      q2fact=q**2
      a=1d0/(1d0/.13d0+(23d0/3d0)/(8d0*atan(1d0))*
     $ log(q/91.188d0))
      G=sqrt(16d0*atan(1d0)*a)
      nan=ieee_value(0d0,ieee_quiet_nan)
      inf=ieee_value(0d0,ieee_positive_inf)
      select case(which)
      case(1)
        p=0d0
      case(2)
        g1=-.2d0
      case(3)
        g2=-.3d0
      case(4)
        MU_R=q*1.01d0
      case(5)
        q2fact(1)=q**2*1.01d0
      case(6)
        q2fact(2)=q**2*1.01d0
      case(7)
        G=0d0
      case(8)
        G=G*1.01d0
      case(9)
        MU_R=nan
      case(10)
        g1=inf
      case(11)
        G=nan
      case(12)
        q2fact(1)=nan
      case(13)
        q2fact(1)=inf
      case(14)
        g1=0d0
        g2=0d0
      case(15)
        g1=-1d0
        MU_R=1d0
        q2fact=0d0
        G=0d0
      case(16)
        MU_R=1d0
        q2fact=0d0
        G=0d0
      case(17)
        q2fact=0d0
        G=0d0
      case(18)
        g1=-1d0
        MU_R=nan
      case(19)
        g2=nan
      case(20)
        MU_R=inf
      case(21)
        G=inf
      case(22)
        p(0,1)=nan
      case(23)
c       Source-derived model reference scale; not a recorded real point.
        MU_R=91.188d0
      end select
      before=p
      weight=3.125d0
      grid=.625d0
      rng=123456789
      candidates=17
      calls=3
      loops=5
      writes=7
      entries=11
      points=13
      old=(/G,MU_R,scale,q2fact(1),q2fact(2),g1,g2,weight,grid/)
      call hi_point(p,g1,g2)
      after=(/G,MU_R,scale,q2fact(1),q2fact(2),g1,g2,weight,grid/)
      if(any(transfer(old,(/0_8/),9).ne.
     $ transfer(after,(/0_8/),9))) stop 93
      if(any(transfer(before,(/0_8/),4*nexternal).ne.
     $ transfer(p,(/0_8/),4*nexternal))) stop 94
      if(rng.ne.123456789.or.candidates.ne.17) stop 95
      if(points.ne.14.or.calls.ne.3.or.loops.ne.5.or.
     $ writes.ne.7.or.entries.ne.11) stop 96
      write(*,'(A,5I6,9(1X,Z16.16))') 'METHOD_STATE',
     $ points,calls,loops,writes,entries,
     $ (transfer(after(i),0_8),i=1,9)
      flush(6)
      end
