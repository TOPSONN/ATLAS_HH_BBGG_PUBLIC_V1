module hh_anonymous_storage
  use iso_c_binding
  implicit none
  logical :: registered(0:200)=.false.
  integer :: opens=0,checks=0
  interface
    integer(c_int) function hh_reference_fd() bind(C)
      import c_int
    end function
    integer(c_int) function hh_check_fd(fd,unit) bind(C)
      import c_int
      integer(c_int),value :: fd,unit
    end function
    integer(c_int) function hh_remember_fd(fd,unit) bind(C)
      import c_int
      integer(c_int),value :: fd,unit
    end function
    integer(c_int) function hh_close_fd(fd) bind(C)
      import c_int
      integer(c_int),value :: fd
    end function
  end interface
contains
  subroutine checked(unit)
    integer,intent(in) :: unit
    logical :: connected
    inquire(unit=unit,opened=connected)
    if(unit<0.or.unit>200) stop 87
    if(.not.connected.or..not.registered(unit)) stop 87
    if(hh_check_fd(fnum(unit),unit)/=1) stop 87
    checks=checks+1
  end subroutine
end module

subroutine hh_open_sink(unit)
  use hh_anonymous_storage
  implicit none
  integer :: unit
  logical :: named
  if(unit/=25.and.unit/=27.and.unit/=37.and.unit/=67) stop 87
  open(unit=unit,status='scratch',form='formatted',access='sequential',action='readwrite')
  inquire(unit=unit,named=named)
  if(named) stop 87
  registered(unit)=.true.
  if(hh_remember_fd(fnum(unit),unit)/=1) stop 87
  opens=opens+1
  call checked(unit)
end subroutine

subroutine hh_open_reference(unit)
  use hh_anonymous_storage
  implicit none
  integer :: unit,fd,err
  character(len=80) :: path
  if(unit/=25.and.unit/=27.and.unit/=37.and.unit/=67) stop 87
  fd=hh_reference_fd()
  if(fd<0) stop 87
  write(path,'(A,I0)') '/proc/self/fd/',fd
  open(unit=unit,file=trim(path),status='old',form='formatted',access='sequential',action='readwrite')
  err=hh_close_fd(fd)
  if(err/=0) stop 87
  registered(unit)=.true.
  if(hh_remember_fd(fnum(unit),unit)/=1) stop 87
  opens=opens+1
  call checked(unit)
end subroutine

subroutine hh_require_transient(unit)
  use hh_anonymous_storage
  implicit none
  integer :: unit
  call checked(unit)
end subroutine

subroutine hh_io_report()
  use hh_anonymous_storage
  write(*,*) 'H_IO',opens,checks
end subroutine

subroutine hh_trace_stream(unit)
  use hh_anonymous_storage
  implicit none
  integer :: unit,err,lines
  character(len=8192) :: text
  call checked(unit)
  flush(unit)
  lines=0
  do
    read(unit,'(A)',iostat=err) text
    if(err<0) exit
    if(err/=0.or.lines>100000) stop 89
    ! These are NONPHYSICAL fixture buffers. Full traces stay local; published
    ! evidence contains hashes and numeric excerpts, never these mock records.
    write(*,'(A,1X,A)') 'H_RAW_NONPHYSICAL',trim(text)
    lines=lines+1
  enddo
  rewind(unit)
  write(*,*) 'H_RAW_LINES',lines
end subroutine

subroutine hh_real4(label,a,b,c,d)
  implicit none
  character(len=*) :: label
  double precision :: a,b,c,d
  write(*,'(A,1X,A,4(1X,Z16.16))') 'H_R',label,transfer(a,0_8),transfer(b,0_8),transfer(c,0_8),transfer(d,0_8)
end subroutine

real function ran1(seed)
  implicit none
  integer :: seed
  real :: hh_original_ran1
  ran1=hh_original_ran1(seed)
  write(*,'(A,1X,Z8.8)') 'H_RNG_RAN1',transfer(ran1,0)
end function

real function xran1(seed)
  implicit none
  integer :: seed
  real :: hh_original_xran1
  xran1=hh_original_xran1(seed)
  write(*,'(A,1X,Z8.8)') 'H_RNG_XRAN1',transfer(xran1,0)
end function

subroutine ranmar(value)
  implicit none
  double precision :: value
  call hh_original_ranmar(value)
  write(*,'(A,1X,Z16.16)') 'H_RNG_RANMAR',transfer(value,0_8)
end subroutine

double precision function dsig(a,b,mode)
  implicit none
  integer :: mode
  double precision :: a,b
  ! Native sample_put_point requests only the non-evaluating mode=2 update.
  if(mode/=2) stop 88
  write(*,*) 'H_DSIG_MODE2_NO_ME'
  dsig=0d0
end function

integer function get_maxsproc()
  get_maxsproc=1 ! Fixed mock process multiplicity, checked against HH maxsproc=1.
end function

subroutine write_good_hel(unit)
  integer :: unit
  write(unit,*) 'METHOD_ONLY_MOCK_HELICITY_GRID'
end subroutine
subroutine read_good_hel(unit)
  integer :: unit
  character(len=80) :: line
  read(unit,'(A)') line
  if(trim(adjustl(line))/='METHOD_ONLY_MOCK_HELICITY_GRID') stop 89
end subroutine

subroutine print_zero_amp()
  stop 88 ! Real helicity/ME initialization is outside this method test.
end subroutine

subroutine open_file_local(unit,name,opened)
  implicit none
  integer :: unit
  character(len=*) :: name
  logical :: opened
  integer :: err
  ! Equal method-only lookup: current isolated workspace, no parent/import.
  open(unit=unit,file=name,status='old',iostat=err)
  opened=err==0
end subroutine
