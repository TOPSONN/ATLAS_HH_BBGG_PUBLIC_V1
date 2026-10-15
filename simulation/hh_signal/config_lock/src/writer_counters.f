      subroutine hh_guard_count(kind)
      implicit none
      integer kind
      integer*8 counts(3)
      common/hh_guard_counts/counts
      if (kind.lt.1.or.kind.gt.3) stop 87
      counts(kind)=counts(kind)+1
      end

      subroutine hh_guard_report
      implicit none
      integer*8 counts(3)
      common/hh_guard_counts/counts
      write(*,*) 'HH_GUARD_SUPPRESSED_CALLS',counts
      end

      block data hh_guard_init
      implicit none
      integer*8 counts(3)
      common/hh_guard_counts/counts
      data counts/0,0,0/
      end
