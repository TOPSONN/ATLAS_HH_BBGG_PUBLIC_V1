      program hh_initialization_probe
      implicit none
      include 'pdf.inc'
      include 'alfas.inc'
      integer*8 base
      integer*8 iseed
      common/to_seed/iseed
      integer groups(2),sets(2),iproc,moffset,i,ios
      double precision q(5),alphas
      character*30 arg
      external alphas
      data q/91.188d0,125d0,250d0,500d0,1000d0/
      call get_command_argument(1,arg)
      read(arg,*,iostat=ios) base
      if(ios.ne.0.or.base.le.0) stop 81
      include 'probe_assignments.inc'
      asmz=0d0
      nloop=0
C     Initialize the actual PDF and native coupling; no density or ME call.
      call pdfwrap
      call get_pdfup(pdlabel,groups,sets,lhaid)
      call get_base(base)
      call get_offset(iproc)
      call get_moffset(moffset)
      write(*,'(A,3(1X,A))') 'HH_PDF',pdlabel,pdsublabel
      write(*,*) 'HH_ALPHA ',asmz,nloop
      write(*,*) 'HH_PDFSUP ',sets
      write(*,*) 'HH_BASE_SEED ',base
      write(*,*) 'HH_COMPILED_SEED ',iseed
      write(*,*) 'HH_OFFSETS ',iproc,moffset
      do i=1,5
        write(*,*) 'HH_RUNNING ',q(i),alphas(q(i))
      enddo
      end
