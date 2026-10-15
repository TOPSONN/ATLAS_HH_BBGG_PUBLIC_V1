program rng_noninterference_method_only
  implicit none
  integer :: mode, i, seed1, seed2, ran1_calls, xran1_calls
  real :: ran1,xran1,discard,a1,a2
  double precision :: r, trace(16)
  character(len=8) :: arg
  external ran1,xran1
  call get_command_argument(1,arg)
  read(arg,*) mode
  if (mode/=0.and.mode/=1) stop 90
  call rmarin(1802,9373)
  seed1=-12345
  seed2=-23456
  ran1_calls=0
  xran1_calls=0
  do i=1,16
    call ranmar(r)
    trace(i)=r
    if(mode==1) then
      discard=ran1(seed1)
      discard=ran1(seed1)
      ran1_calls=ran1_calls+2
      discard=xran1(seed2)
      xran1_calls=xran1_calls+1
    endif
  enddo
  a1=ran1(seed1)
  a2=xran1(seed2)
  write(*,*) 'METHOD_ONLY_RNG_CALLS',16,ran1_calls,xran1_calls
  do i=1,16
    write(*,'(A,I3,1X,ES25.17)') 'RANMAR_TRACE ',i,trace(i)
  enddo
  write(*,*) 'AUXILIARY_NEXT',a1,a2
end program
