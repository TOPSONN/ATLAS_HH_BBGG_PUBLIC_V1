      double precision function dot(p1,p2)
C****************************************************************************
C     4-Vector Dot product
C****************************************************************************
      implicit none
      double precision p1(0:3),p2(0:3), dot2
      dot=p1(0)*p2(0)-p1(1)*p2(1)-p1(2)*p2(2)-p1(3)*p2(3)

      if(dabs(dot).lt.1d-6)then ! solve numerical problem
         dot2 = p1(0)*p2(0)+p1(1)*p2(1)+p1(2)*p2(2)+p1(3)*p2(3)
         dot2 = max(1e-99,dot2)
         if (dot/dot2.lt.1e-6) dot=0d0
      endif

      end
