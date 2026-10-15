      subroutine hh_before_sampling(expected_seed)
      implicit none
      include 'genps.inc'
      include 'run.inc'
      include 'PDF/pdf.inc'
      include 'alfas.inc'
      include 'MODEL/coupl.inc'
      integer*8 expected_seed,iseed
      common/to_seed/iseed
      integer pdfg(2),pdfs(2),io,mo
      integer idbmup,pdfgup,pdfsup,idwtup,nprup,lprup
      double precision ebmup,xsecup,xerrup,xmaxup
      common/heprup/idbmup(2),ebmup(2),pdfgup(2),pdfsup(2),
     $ idwtup,nprup,xsecup(100),xerrup(100),xmaxup(100),lprup(100)
      double precision alphas,expected
      external alphas
      if(pdlabel.ne.'cteq6l1') stop 71
      if(any(pdsublabel.ne.'cteq6l1')) stop 72
      if(nloop.ne.1.or.abs(asmz-.13d0).gt.1d-14) stop 73
      if(iseed.ne.expected_seed) stop 74
      if(fixed_ren_scale.or.fixed_fac_scale1.or.
     $ fixed_fac_scale2) stop 75
      if(dynamical_scale_choice.ne.4.or.
     $ abs(scalefact-.5d0).gt.1d-14) stop 75
      if(any(lpp.ne.1).or.any(ebeam.ne.6500d0)) stop 75
      if(MDL_MH.ne.125d0.or.MDL_MT.ne.173d0.or.
     $ MDL_MB.ne.4.7d0) stop 76
      call get_pdfup(pdlabel,pdfg,pdfs,lhaid)
      if(any(pdfs.ne.10042).or.any(pdfsup.ne.10042)) stop 77
      expected=1d0/(1d0/.13d0+
     $ (23d0/3d0)/(8d0*atan(1d0))*log(250d0/91.188d0))
      if(abs(alphas(250d0)-expected).gt.1d-10*expected) stop 78
      call get_offset(io)
      call get_moffset(mo)
      if(io.ne.0.or.(mo.ne.0.and.mo.ne.1)) stop 79
      write(*,*) 'HH_PRE_SAMPLING_CONFIG_PASS',iseed,io,mo
      end
