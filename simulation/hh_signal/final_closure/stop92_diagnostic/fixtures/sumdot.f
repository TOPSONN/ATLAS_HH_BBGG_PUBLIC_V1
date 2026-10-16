      DOUBLE PRECISION FUNCTION SumDot(P1,P2,dsign)
c************************************************************************
c     Invarient mass of 2 particles
c************************************************************************
      IMPLICIT NONE
c
c     Arguments
c
      double precision p1(0:3),p2(0:3),dsign
c
c     Local
c      
      integer i
      double precision ptot(0:3)
c
c     External
c
      double precision dot
      external dot
c-----
c  Begin Code
c-----

      do i=0,3
         ptot(i)=p1(i)+dsign*p2(i)
      enddo
      SumDot = dot(ptot,ptot)
      RETURN
      END

