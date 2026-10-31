       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAESD.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAESD - AUDIT LOG IN AN ESDS.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOG-FILE ASSIGN TO LOGESD
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-LOG-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  LOG-FILE
           RECORDING MODE IS F.
       01  LOG-REC.
           05  LOG-TS                 PIC X(14).
           05  LOG-TEXT               PIC X(40).
           05  FILLER                 PIC X(6).
       WORKING-STORAGE SECTION.
       01  WS-LOG-STATUS          PIC X(2).
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                 VALUE 'Y'.
       01  WS-COUNT               PIC 9(5) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN EXTEND LOG-FILE
           PERFORM 1000-APPEND
           CLOSE LOG-FILE
           OPEN INPUT LOG-FILE
           PERFORM 8000-READ
           PERFORM 2000-COUNT UNTIL WS-EOF
           CLOSE LOG-FILE
           DISPLAY 'AIXAESD RECORDS ' WS-COUNT
           GOBACK.
       1000-APPEND.
           MOVE '20261031120000' TO LOG-TS
           MOVE 'ORDER ORD00001 ACCEPTED' TO LOG-TEXT
           WRITE LOG-REC.
       2000-COUNT.
           ADD 1 TO WS-COUNT
           PERFORM 8000-READ.
       8000-READ.
           READ LOG-FILE
              AT END
                 SET WS-EOF TO TRUE
           END-READ.
