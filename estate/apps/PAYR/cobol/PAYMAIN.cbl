       IDENTIFICATION DIVISION.
       PROGRAM-ID.    PAYMAIN.
       AUTHOR.       PAYROLL.
      *------------------------------------------------------------
      * PAYMAIN - PAYROLL RUN. CONTAINS PAYCALC (NESTED); PAYRPT IS
      * BATCH-COMPILED FROM THE SAME MEMBER.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SOURCE-COMPUTER.    IBM-ZOS.
       OBJECT-COMPUTER.    IBM-ZOS.
       SPECIAL-NAMES.
           C01 IS TOP-OF-PAGE.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT PAY-FILE ASSIGN TO PAYOUT
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-PAY-STATUS.
       I-O-CONTROL.
           APPLY WRITE-ONLY ON PAY-FILE.
       DATA DIVISION.
       FILE SECTION.
       FD  PAY-FILE
           RECORDING MODE IS F.
       01  PAY-REC                PIC X(80).
       WORKING-STORAGE SECTION.
       01  WS-PAY-STATUS          PIC X(2).
       01  WS-EMP.
           COPY PAYTPL REPLACING ==:TAG:== BY ==EMP==.
       01  WS-CONST.
           COPY 'PAYCON'.
       01  WS-LOCAL-DATE.
           COPY DATEWS.
       01  WS-SHARED-DATE.
           COPY DATEWS IN SHRCPY.
       PROCEDURE DIVISION.
       MAINLINE SECTION.
       0100.
           OPEN OUTPUT PAY-FILE
           MOVE SPACES TO EMP-NAME
           PERFORM 0200
           CALL 'PAYCALC'
           CALL 'PAYRPT'
           CLOSE PAY-FILE
           GOBACK.
       0200.
           MOVE 'E00001' TO EMP-ID
           MOVE PC-MAX-HOURS TO WS-PAY-STATUS.
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    PAYCALC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-I                   PIC 9(4) COMP VALUE 0.
       01  WS-GROSS               PIC S9(7)V99 COMP-3 VALUE 0.
       PROCEDURE DIVISION.
       MAINLINE SECTION.
       1000-CALC.
           PERFORM UNTIL EXIT
              ADD 1 TO WS-I
              IF WS-I > 12
                 EXIT PERFORM
              END-IF
              ADD 100 TO WS-GROSS
           END-PERFORM
           PERFORM 2000-ROUND
           GOBACK.
       2000-ROUND.
           COMPUTE WS-GROSS ROUNDED = WS-GROSS * 1.
       END PROGRAM PAYCALC.
       END PROGRAM PAYMAIN.
       IDENTIFICATION DIVISION.
        PROGRAM-ID. 'PAYRPT'.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-LINES               PIC 9(4) COMP VALUE 0.
       PROCEDURE DIVISION.
       MAINLINE SECTION.
       0100.
           ADD 1 TO WS-LINES
           DISPLAY 'PAYRPT ' WS-LINES
           GOBACK.
       END PROGRAM 'PAYRPT'.
