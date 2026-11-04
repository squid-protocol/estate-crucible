       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAKS2.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAKS2 - CUSTOMERS, TWO ALTERNATE KEYS.
      * TAX ID IS UNIQUE, NAME MAY REPEAT.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUS-FILE ASSIGN TO CUSKSD
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
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
           IF WS-CUS-STATUS NOT = '00'
              DISPLAY 'AIXAKS2 OPEN FAILED ' WS-CUS-STATUS
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-ADD
           PERFORM 2000-PROBE
           CLOSE CUS-FILE
           GOBACK.
       1000-ADD.
           MOVE 'CUS00001' TO CUS-ID
           MOVE '123456789' TO CUS-TAX
           MOVE 'SMITH' TO CUS-NAME
           WRITE CUS-REC
           PERFORM 9000-STATUS
           MOVE 'CUS00002' TO CUS-ID
           MOVE '987654321' TO CUS-TAX
           WRITE CUS-REC
           PERFORM 9000-STATUS
           MOVE 'CUS00003' TO CUS-ID
           MOVE '123456789' TO CUS-TAX
           WRITE CUS-REC
           PERFORM 9000-STATUS.
       2000-PROBE.
           MOVE '987654321' TO CUS-TAX
           READ CUS-FILE KEY IS CUS-TAX
               INVALID KEY DISPLAY 'TAX ID NOT FOUND'
           END-READ
           PERFORM 9000-STATUS.
       9000-STATUS.
           IF WS-CUS-STATUS = '22'
              DISPLAY 'DUPLICATE KEY ' CUS-ID
           END-IF
           IF WS-CUS-STATUS = '02'
              DISPLAY 'DUPLICATE NAME ' CUS-NAME
           END-IF.
