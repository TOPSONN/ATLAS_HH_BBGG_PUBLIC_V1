      program scalar_method_only
      implicit none
      include 'alfas.inc'
      real*8 q,alphas,p1(0:3),p2(0:3),sumdot,native,qguard,e1,e2
      integer i,j
      real*8 qs(17)
      external alphas,sumdot
      asmz=.13d0
      nloop=1
      qs=(/1.3d0,1.42d0*(1d0-1d-8),1.42d0,
     $ 1.42d0*(1d0+1d-8),4.7d0*(1d0-1d-8),4.7d0,
     $ 4.7d0*(1d0+1d-8),91.188d0,125d0,
     $ 173d0*(1d0-1d-8),173d0,173d0*(1d0+1d-8),
     $ 250d0,1000d0,6500d0,2d0,10d0/)
      do i=1,size(qs)
        q=qs(i)
        write(*,'(A,2(1X,ES25.16E3))') 'METHOD_ALPHA',q,alphas(q)
      enddo
c     Deterministic scalar grid, no phase-space generator and no ME.
c     Only scalar residuals are written, never the test vector arrays.
      do i=0,20
        e1=125d0+(6500d0-125d0)*dble(i)/20d0
        do j=0,20
          e2=125d0+(6500d0-125d0)*dble(j)/20d0
          p1=(/e1,0d0,0d0,e1/)
          p2=(/e2,0d0,0d0,-e2/)
c         Exact choice4 expression, followed by frozen scalefact=0.5.
          native=dsqrt(max(0d0,sumdot(p1,p2,1d0)))*.5d0
c         Exact hi_point expression on the same synthetic scalars.
          qguard=sqrt(max(0d0,(p1(0)+p2(0))**2-
     $ (p1(1)+p2(1))**2-(p1(2)+p2(2))**2-
     $ (p1(3)+p2(3))**2))/2d0
          write(*,'(A,2(1X,ES25.16E3))') 'METHOD_SCALE',
     $ abs(native/qguard-1d0),abs(native**2/qguard**2-1d0)
        enddo
      enddo
      end
