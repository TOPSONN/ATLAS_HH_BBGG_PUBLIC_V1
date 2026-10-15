      PROGRAM HH_EVENT_REWEIGHT
C     Only genuine source momenta supplied by the Python source validator.
C     One fresh native process per event/benchmark avoids coupling caches.
      IMPLICIT NONE
      INCLUDE 'coupl.inc'
      INCLUDE 'mp_coupl.inc'
      REAL*8 P(0:3,4),A(0:3,0:1),PREC(0:1),KL,ASIN,SCALE
      INTEGER I,J,RC
      CHARACTER*80 ARG
      CALL GET_COMMAND_ARGUMENT(1,ARG)
      READ(ARG,*) KL
      CALL SETPARA('param_card.dat')
      OPEN(97,FILE='PS.input',STATUS='OLD',ACTION='READ')
      READ(97,*) ASIN,SCALE
      DO I=1,4
        READ(97,*) (P(J,I),J=0,3)
      ENDDO
      CLOSE(97)
      CALL UPDATE_AS_PARAM2(SCALE*SCALE,ASIN)
      CALL MP_UPDATE_AS_PARAM()
      GC_30=GC_30*KL
      MP__GC_30=MP__GC_30*REAL(KL,16)
      WRITE(*,'(A,5ES26.16E3)') 'HH_ME_INPUT ',KL,MU_R,
     $ G**2/(4D0*ACOS(-1D0)),ABS(GC_37),ABS(GC_30)
      DO I=1,6
        CALL ML5_0_SLOOPMATRIX_THRES(P,A,-1.0D0,PREC,RC)
      ENDDO
      WRITE(*,'(A,4ES26.16E3,I8)') 'HH_ME_RESULT ',
     $ A(1,0),A(2,0),A(3,0),PREC(0),RC
      END
