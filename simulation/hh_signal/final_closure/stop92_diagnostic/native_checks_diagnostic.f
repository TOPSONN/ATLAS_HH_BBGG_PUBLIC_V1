      subroutine hi_control_gate(seed)
      use iso_c_binding
      implicit none
      integer*8 seed
      interface
        integer(c_int) function hi_check_parent(seed) bind(C)
          import c_int,c_int64_t
          integer(c_int64_t),value :: seed
        end function
      end interface
      if(hi_check_parent(seed).ne.1) then
        write(*,*) 'HI_FAILURE SUPERVISOR_REQUIRED'
        stop 80
      endif
      end

      subroutine hi_endpoint(ncall,itmax,itmin)
      implicit none
      integer ncall,itmax,itmin,mo
      call get_moffset(mo)
      if((mo.ne.0.and.mo.ne.1).or.ncall.ne.250.or.
     $ itmax.ne.4-mo.or.itmin.ne.4-mo) stop 91
      end

      subroutine hi_native_loop_count(n)
      implicit none
      integer n,u(0:9),t(0:9),h(0:9),n_evals
      double precision average,max_precision,min_precision
      common/MADLOOPSTATS/average,max_precision,min_precision,n_evals,
     $ u,t,h
      n=n_evals
      end

      subroutine hi_inputs(ncall,itmax,itmin)
      implicit none
      include 'genps.inc'
      integer ncall,itmax,itmin,use_cut,mo,expected
      common/to_weight/use_cut
      integer isum_hel
      logical multi_channel
      common/to_matrix/isum_hel,multi_channel
      call get_moffset(mo)
      expected=4-mo
      if(mo.ne.0.and.mo.ne.1) stop 79
      if(ncall.ne.250.or.itmax.ne.expected.or.itmin.ne.expected)
     $ stop 91
      if(multi_channel.or.isum_hel.ne.0) stop 91
      if((mo.eq.0.and.use_cut.ne.2).or.
     $ (mo.eq.1.and.use_cut.ne.0)) stop 91
      write(*,*) 'HI_INPUTS',ncall,itmax,itmin,use_cut,isum_hel,
     $ multi_channel
      flush(6)
      end

      subroutine hi_config
      implicit none
      include 'genps.inc'
      include 'run.inc'
      include 'PDF/pdf.inc'
      include 'alfas.inc'
      include 'MODEL/coupl.inc'
      write(*,*) 'HI_PDF ',pdlabel,' ',pdsublabel(1),' ',
     $ pdsublabel(2)
      write(*,*) 'HI_ALPHA',asmz,nloop
      write(*,*) 'HI_MASS',MDL_MH,MDL_MT,MDL_MB
      write(*,*) 'HI_SCALE',dynamical_scale_choice,scalefact,
     $ fixed_ren_scale,fixed_fac_scale1,fixed_fac_scale2
      write(*,*) 'HI_BEAMS',ebeam(1),ebeam(2),lpp(1),lpp(2)
      flush(6)
      end

      subroutine hi_point(p,g1,g2)
      use hi_statistics
      implicit none
      include 'genps.inc'
      include 'nexternal.inc'
      include 'run.inc'
      include 'coupl.inc'
      real*8 p(0:3,nexternal),g1,g2,q,a,expected
      q=sqrt(max(0d0,(p(0,1)+p(0,2))**2-
     $ (p(1,1)+p(1,2))**2-(p(2,1)+p(2,2))**2-
     $ (p(3,1)+p(3,2))**2))/2d0
      call finite(q)
      call finite(MU_R)
      call finite(g1)
      call finite(g2)
      if(q.le.0d0.or.g1.lt.0d0.or.g2.lt.0d0) then
      write(*,'(A,4(A,ES25.16E3))')
     $ 'HI_FAILURE POINT92 POINT92_Q_OR_PDF',
     $ ' q_GeV=',q,
     $ ' g1_dimensionless=',g1,
     $ ' g2_dimensionless=',g2,
     $ ' native_scale_GeV=',scale
      flush(6)
      stop 92
      endif
      if(abs(MU_R/q-1d0).gt.1d-10) then
      write(*,'(A,5(A,ES25.16E3))')
     $ 'HI_FAILURE POINT92 POINT92_RENORMALIZATION_SCALE',
     $ ' q_GeV=',q,
     $ ' MU_R_GeV=',MU_R,
     $ ' native_scale_GeV=',scale,
     $ ' MU_R_over_q=',MU_R/q,
     $ ' relative_mismatch=',abs(MU_R/q-1d0)
      flush(6)
      stop 92
      endif
      if(any(abs(q2fact/q**2-1d0).gt.1d-10)) then
      write(*,'(A,6(A,ES25.16E3))')
     $ 'HI_FAILURE POINT92 POINT92_FACTORIZATION_SCALE',
     $ ' q_GeV=',q,
     $ ' q2fact1_GeV2=',q2fact(1),
     $ ' q2fact2_GeV2=',q2fact(2),
     $ ' QF1_squared_over_q2=',q2fact(1)/q**2,
     $ ' QF2_squared_over_q2=',q2fact(2)/q**2,
     $ ' native_scale_GeV=',scale
      flush(6)
      stop 92
      endif
      a=G**2/(16d0*atan(1d0))
      call finite(a)
      if(a.le.0d0) then
      write(*,'(A,4(A,ES25.16E3))')
     $ 'HI_FAILURE POINT92 POINT92_ALPHA_NONPOSITIVE',
     $ ' q_GeV=',q,
     $ ' alpha_actual=',a,
     $ ' MU_R_GeV=',MU_R,
     $ ' native_scale_GeV=',scale
      flush(6)
      stop 92
      endif
      expected=1d0/(1d0/.13d0+
     $ (23d0/3d0)/(8d0*atan(1d0))*log(q/91.188d0))
      if(abs(a/expected-1d0).gt.1d-10) then
      write(*,'(A,5(A,ES25.16E3))')
     $ 'HI_FAILURE POINT92 POINT92_ALPHA_RUNNING_MISMATCH',
     $ ' q_GeV=',q,
     $ ' alpha_actual=',a,
     $ ' alpha_expected=',expected,
     $ ' relative_mismatch=',abs(a/expected-1d0),
     $ ' native_scale_GeV=',scale
      flush(6)
      stop 92
      endif
      points=points+1
      end
