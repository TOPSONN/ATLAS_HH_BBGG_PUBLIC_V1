      PROGRAM PHASE7A_FIXED_POINT
C     Numerical matrix element only. No phase-space RNG or event writer.
      IMPLICIT NONE
      INCLUDE 'coupl.inc'
      INCLUDE 'mp_coupl.inc'
      REAL*8 P(0:3,4),A(0:3,0:1),PREC(0:1),KL
      INTEGER I,J,RC
      CHARACTER*80 ARG
      CALL GET_COMMAND_ARGUMENT(1,ARG)
      READ(ARG,*) KL
      CALL SETPARA('param_card.dat')
      OPEN(97,FILE='PS.input',STATUS='OLD',ACTION='READ')
      DO I=1,4
        READ(97,*) (P(J,I),J=0,3)
      ENDDO
      CLOSE(97)
      CALL UPDATE_AS_PARAM()
C     GC_30 is independently bound to -6*i*lambda*v (H,H,H).
C     This is a diagnostic rescaling, not a new production UFO model.
      GC_30=GC_30*KL
      MP__GC_30=MP__GC_30*REAL(KL,16)
      WRITE(*,'(A,7ES26.16E3)') 'PHASE7A_PARAMETERS ',MDL_MH,
     $ MDL_MT,MDL_MB,MU_R,G**2/(4D0*ACOS(-1D0)),ABS(GC_37),
     $ ABS(GC_30)
      DO I=1,6
        CALL ML5_0_SLOOPMATRIX_THRES(P,A,-1.0D0,PREC,RC)
      ENDDO
      WRITE(*,'(A,4ES26.16E3,I8)') 'PHASE7A_RESULT ',
     $ A(1,0),A(2,0),A(3,0),PREC(0),RC
      END
