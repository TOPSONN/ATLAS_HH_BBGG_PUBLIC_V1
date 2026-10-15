program fixed_weight_kernel_method_only
  implicit none
  double precision :: weights(8), mean_a, mean_b, q_a,q_b
  integer :: i,original_candidates,suppressed_candidates
  weights=[1d0,2d0,4d0,8d0,3d0,5d0,7d0,11d0]
  mean_a=0d0
  mean_b=0d0
  q_a=0d0
  q_b=0d0
  original_candidates=0
  suppressed_candidates=0
  do i=1,8
    ! Numeric accumulation shape from native sample_put_point, applied only
    ! to a fixed METHOD_ONLY list. Not phase-space or a physical integral.
    mean_a=mean_a+abs(weights(i))
    q_a=q_a+weights(i)**2
    original_candidates=original_candidates+1
    mean_b=mean_b+abs(weights(i))
    q_b=q_b+weights(i)**2
  enddo
  if(mean_a/=mean_b.or.q_a/=q_b) stop 91
  write(*,*) 'METHOD_ONLY_FIXED_WEIGHT_SUMS',mean_a,q_a
  write(*,*) 'METHOD_ONLY_CANDIDATE_STATE',original_candidates,suppressed_candidates
end program
