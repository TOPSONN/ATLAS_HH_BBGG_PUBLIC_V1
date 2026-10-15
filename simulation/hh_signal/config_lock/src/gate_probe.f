      program hh_gate_synthetic_context_probe
      implicit none
      include 'genps.inc'
      include 'run.inc'
      include 'PDF/pdf.inc'
      include 'alfas.inc'
      include 'MODEL/coupl.inc'
      integer*8 iseed
      common/to_seed/iseed
      character*30 mode
      integer idbmup,pdfgup,pdfsup,idwtup,nprup,lprup
      double precision ebmup,xsecup,xerrup,xmaxup
      common/heprup/idbmup(2),ebmup(2),pdfgup(2),pdfsup(2),
     $ idwtup,nprup,xsecup(100),xerrup(100),xmaxup(100),lprup(100)
      call get_command_argument(1,mode)
C     Synthetic initialized context only. Never a source/ME/integral.
      iseed=910001
      pdlabel='cteq6l1'
      pdsublabel='cteq6l1'
      nloop=1
      asmz=.13d0
      fixed_ren_scale=.false.
      fixed_fac_scale1=.false.
      fixed_fac_scale2=.false.
      dynamical_scale_choice=4
      scalefact=.5d0
      lpp=1
      ebeam=6500d0
      MDL_MH=125d0
      MDL_MT=173d0
      MDL_MB=4.7d0
      pdfsup=10042
      if(mode.eq.'pdf') pdlabel='nn23lo1'
      if(mode.eq.'labels') pdsublabel(1)='nn23lo1'
      if(mode.eq.'alpha') nloop=2
      if(mode.eq.'seed') iseed=21
      if(mode.eq.'mass') MDL_MT=172d0
      if(mode.eq.'header') pdfsup=247000
      call hh_before_sampling(910001_8)
      end
