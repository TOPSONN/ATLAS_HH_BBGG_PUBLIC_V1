      program hh_writer_boundary_probe
      implicit none
      include 'nexternal.inc'
      double precision p(0:3,nexternal)
      p=0d0
C     Synthetic boundary exercise only: no ME, no integration or event data.
      call write_leshouche(p,1d0,1,.true.)
      call store_events(-1d0,.true.)
      call clear_events
      call hh_guard_report
      end
