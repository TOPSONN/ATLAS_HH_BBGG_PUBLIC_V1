module hi_statistics
  use ieee_arithmetic
  implicit none
  integer(8) :: calls=0,loops=0,writes=0,points=0,entries=0
  integer(8) :: codes(0:999)=0
  real(8) :: maxprecision=0d0
contains
  subroutine finite(x)
    real(8),intent(in) :: x
    if(.not.ieee_is_finite(x)) then
      write(*,*) 'HI_FAILURE NONFINITE'
      flush(6)
      stop 90
    endif
  end subroutine
end module

subroutine hi_integrand
  use hi_statistics
  calls=calls+1
end subroutine

subroutine hi_loop(code,f,one,two,prec)
  use hi_statistics
  integer :: code
  real(8) :: f,one,two,prec
  loops=loops+1
  write(*,*) 'HI_ME_RETURN',loops,code,prec
  flush(6)
  call finite(f);call finite(one);call finite(two);call finite(prec)
  if(code<0.or.code>999) stop 90
  codes(code)=codes(code)+1
  maxprecision=max(maxprecision,prec)
  if(mod(code/100,10)==4.or.prec<0d0) then
    write(*,*) 'HI_FAILURE LOOP_RETURN',code,prec
    flush(6)
    stop 90
  endif
  ! Same native pole-warning predicate, converted into a declared failure gate
  ! before the diagnostic prints physical momenta. No failed point is replaced.
  if(f/=0d0.and.mod(code,10)/=7) then
    if((one+two)/f>1000d0*prec.and.(one+two)/f>1d-5) then
      write(*,*) 'HI_FAILURE LOOP_POLES',code,prec
      flush(6)
      stop 90
    endif
  endif
end subroutine

subroutine hi_me_enter
  use hi_statistics
  entries=entries+1
  write(*,*) 'HI_ME_ENTRY',entries
  flush(6)
end subroutine

subroutine hi_iteration(i,target,attempts,mean,error,raw)
  use hi_statistics
  integer :: i,target,attempts
  real(8) :: mean,error,raw
  call finite(mean);call finite(error);call finite(raw)
  if(error<=0d0.or.mean<=0d0) stop 90
  write(*,*) 'HI_ITERATION',i,target,attempts,mean,error,raw,calls,loops
  flush(6)
end subroutine

subroutine hi_result(mean,error,chi,iterations,nonzero,candidates,native_retained)
  use hi_statistics
  integer :: iterations,nonzero,candidates,native_retained
  real(8) :: mean,error,chi
  call finite(mean);call finite(error);call finite(chi)
  if(error<=0d0.or.mean<=0d0) stop 90
  write(*,*) 'HI_RESULT',mean,error,chi,iterations,nonzero,candidates,native_retained
  flush(6)
end subroutine

subroutine hi_tail(nw,nwritten,nover,nth,xover,xtot,target,maximum)
  use hi_statistics
  integer :: nw,nwritten,nover,nth
  real(8) :: xover,xtot,target,maximum
  call finite(xover);call finite(xtot);call finite(target);call finite(maximum)
  write(*,*) 'HI_TAIL',nw,nwritten,nover,nth,xover,xtot,target,maximum
  flush(6)
end subroutine

subroutine hi_writer
  use hi_statistics
  writes=writes+1
end subroutine

subroutine hi_seed(base,io,joffset,config,ij,kl)
  use hi_statistics
  integer(8) :: base
  integer :: io,joffset,config,ij,kl
  write(*,*) 'HI_SEED',base,io,joffset,config,ij,kl
  flush(6)
end subroutine

subroutine hi_finish
  use hi_statistics
  integer :: i,native_count
  call hi_native_loop_count(native_count)
  if(native_count/=loops.or.entries/=loops) stop 93
  write(*,*) 'HI_NATIVE_LOOP_COUNT',native_count
  write(*,*) 'HI_COUNTS',calls,loops,writes,points,maxprecision
  do i=0,999
    if(codes(i)>0) write(*,*) 'HI_LOOP_CODE',i,codes(i)
  enddo
  write(*,*) 'HI_COMPLETE'
  flush(6)
end subroutine
