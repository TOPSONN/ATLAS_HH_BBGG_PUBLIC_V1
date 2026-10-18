      subroutine rmarin(ij,kl)
*     -----------------
* initializing routine for ranmar, must be called before generating
* any pseudorandom numbers with ranmar. the input values should be in
* the ranges 0<=ij<=31328 ; 0<=kl<=30081
      implicit real*8(a-h,o-z)
      character*30 filename
      logical file_exists
      common/ raset1 / ranu(97),ranc,rancd,rancm
      common/ raset2 / iranmr,jranmr
      save /raset1/,/raset2/
* this shows correspondence between the simplified input seeds ij, kl
* and the original marsaglia-zaman seeds i,j,k,l.
* to get the standard values in the marsaglia-zaman paper (i=12,j=34
* k=56,l=78) put ij=1802, kl=9373
      write(*,*) "Ranmar initialization seeds",ij,kl
c
c    18/6/2012 TJS  Added check to ensure ij and kl are in range
c      
      if (ij .lt. 0 .or. ij .gt. 31328 .or.
     $     kl .lt. 0 .or. kl .gt. 30081) then
         filename='../../error'
         INQUIRE(FILE="../../RunWeb", EXIST=file_exists)
         if(.not.file_exists) filename = '../' // filename
         open(unit=26,file=filename,status='unknown')
         if (ij .lt. 0 .or. ij .gt. 31328) then
            write(26,*) 'Bad initialization value of ij in rmarin ', ij
            write(*,*) 'Bad initialization value of ij in rmarin ', ij
         elseif (kl .lt. 0 .or. kl .gt. 30081) then
            write(26,*) 'Bad initialization value of kl in rmarin ', kl
            write(*,*) 'Bad initialization value of kl in rmarin ', kl
         endif
         stop
      endif

      i = mod( ij/177 , 177 ) + 2
      j = mod( ij     , 177 ) + 2
      k = mod( kl/169 , 178 ) + 1
      l = mod( kl     , 169 )
      do 300 ii = 1 , 97
        s =  0d0
        t = .5d0
        do 200 jj = 1 , 24
          m = mod( mod(i*j,179)*k , 179 )
          i = j
          j = k
          k = m
          l = mod( 53*l+1 , 169 )
          if(mod(l*m,64) .ge. 32) s = s + t
          t = .5d0*t
  200   continue
        ranu(ii) = s
  300 continue
      ranc  =   362436d0 / 16777216d0
      rancd =  7654321d0 / 16777216d0
      rancm = 16777213d0 / 16777216d0
      iranmr = 97
      jranmr = 33
      end
