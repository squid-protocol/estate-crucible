       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAKS3.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAKS3 - CUSTOMER TAX ID CORRECTIONS, KSDS READ SEQUENTIALLY.
      * A REWRITE NEEDS A READ BEFORE IT; A TAX ID MUST STAY UNIQUE.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUS-FILE ASSIGN TO CUSKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS SEQUENTIAL
               RECORD KEY IS CUS-ID
               ALTERNATE RECORD KEY IS CUS-TAX
               ALTERNATE RECORD KEY IS CUS-NAME WITH DUPLICATES
               FILE STATUS IS WS-CUS-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  CUS-FILE
           RECORDING MODE IS F.
       01  CUS-REC.
           05  CUS-ID                 PIC X(8).
           05  CUS-TAX                PIC X(9).
           05  CUS-NAME               PIC X(20).
           05  FILLER                 PIC X(3).
       WORKING-STORAGE SECTION.
       01  WS-CUS-STATUS          PIC X(2).
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O CUS-FILE
           PERFORM 1000-BLIND
           PERFORM 2000-CLASH
           CLOSE CUS-FILE
           GOBACK.
       1000-BLIND.
           MOVE 'CUS00001' TO CUS-ID
           MOVE '555555555' TO CUS-TAX
           REWRITE CUS-REC
           IF WS-CUS-STATUS = '43'
              DISPLAY 'REWRITE WITHOUT READ'
           END-IF.
       2000-CLASH.
           READ CUS-FILE NEXT RECORD
               AT END DISPLAY 'NO CUSTOMERS'
           END-READ
           MOVE '987654321' TO CUS-TAX
           REWRITE CUS-REC
           IF WS-CUS-STATUS = '22'
              DISPLAY 'TAX ID TAKEN ' CUS-TAX
              MOVE 4 TO RETURN-CODE
           END-IF.
