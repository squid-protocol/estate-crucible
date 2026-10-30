       IDENTIFICATION DIVISION.
       PROGRAM-ID.    BDLDRPT.
       AUTHOR.       BATCH OPERATIONS.
      *------------------------------------------------------------
      * BDLDRPT - PRINT THE LOAD REPORT.
      * THE EXEC PARM (A REPORT TYPE) ARRIVES IN LS-PARM.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT RPT-FILE ASSIGN TO RPTOUT
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-RPT-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  RPT-FILE
           RECORDING MODE IS F.
       01  RPT-LINE               PIC X(80).
       WORKING-STORAGE SECTION.
       01  WS-RPT-STATUS          PIC X(2).
       LINKAGE SECTION.
       01  LS-PARM.
           05  LS-PARM-LEN            PIC S9(4) COMP.
           05  LS-PARM-TEXT           PIC X(8).
       PROCEDURE DIVISION USING LS-PARM.
       0000-MAIN.
           OPEN OUTPUT RPT-FILE
           IF LS-PARM-LEN > 0
              MOVE SPACES TO RPT-LINE
              MOVE LS-PARM-TEXT TO RPT-LINE
           ELSE
              MOVE 'REPORT DAILY' TO RPT-LINE
           END-IF
           WRITE RPT-LINE
           CLOSE RPT-FILE
           GOBACK.
