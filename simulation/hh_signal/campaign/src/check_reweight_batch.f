      PROGRAM HH_EVENT_REWEIGHT_BATCH
C     Same genuine point, explicit DP/MP coupling reset per benchmark.
C     Results require independent fresh-process regression before use.
      IMPLICIT NONE
      INCLUDE 'coupl.inc'
      INCLUDE 'mp_coupl.inc'
      REAL*8 P(0:3,4),A(0:3,0:1),PREC(0:1),ASIN,SCALE,KS(7)
      COMPLEX*16 BASE30
      COMPLEX*32 MPBASE30
      INTEGER I,J,K,RC
      DATA KS/-1D0,0D0,1D0,2D0,2.5D0,5D0,1D0/
      CALL SETPARA('param_card.dat')
      OPEN(97,FILE='PS.input',STATUS='OLD',ACTION='READ')
      READ(97,*) ASIN,SCALE
      DO I=1,4
        READ(97,*) (P(J,I),J=0,3)
      ENDDO
      CLOSE(97)
      CALL UPDATE_AS_PARAM2(SCALE*SCALE,ASIN)
      CALL MP_UPDATE_AS_PARAM()
      BASE30=GC_30
      MPBASE30=MP__GC_30
      WRITE(*,'(A,4ES26.16E3)') 'HH_MODEL_FROZEN ',MDL_MH,
     $ MDL_MT,MDL_MB,MDL_WH
      DO K=1,7
        CALL UPDATE_AS_PARAM2(SCALE*SCALE,ASIN)
        CALL MP_UPDATE_AS_PARAM()
        GC_30=BASE30*KS(K)
        MP__GC_30=MPBASE30*REAL(KS(K),16)
        WRITE(*,'(A,5ES26.16E3)') 'HH_ME_INPUT ',KS(K),MU_R,
     $   G**2/(4D0*ACOS(-1D0)),ABS(GC_37),ABS(GC_30)
        DO I=1,6
          CALL ML5_0_SLOOPMATRIX_THRES(P,A,-1.0D0,PREC,RC)
        ENDDO
        WRITE(*,'(A,5ES26.16E3,I8)') 'HH_BATCH_RESULT ',
     $   KS(K),A(1,0),A(2,0),A(3,0),PREC(0),RC
      ENDDO
      END
