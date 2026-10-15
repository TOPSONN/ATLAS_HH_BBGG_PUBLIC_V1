! Pure coupling function on retained LHE scales, never a cross-section integral.
program retained_scales_only
  implicit none
  real(8) :: q,a1,a2,asmz
  integer :: nloop,ios
  common /a_block/ asmz,nloop
  real(8),external :: alphas
  do
    read(*,*,iostat=ios) q
    if(ios/=0) exit
    asmz=0.13d0
    nloop=1
    a1=alphas(q)
    nloop=2
    a2=alphas(q)
    write(*,'(3ES26.16E3)') q,a1,a2
  end do
end program
