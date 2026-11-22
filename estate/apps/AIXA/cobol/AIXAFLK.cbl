       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAFLK.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAFLK - FILE STATUS 14, 34 AND 38 OVER AN RRDS AND AN ESDS.
      * EACH STATUS IS TESTED IN ITS OWN PARAGRAPH.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SLOT-FILE ASSIGN TO SLOTS
               ORGANIZATION IS RELATIVE
               ACCESS MODE IS SEQUENTIAL
               RELATIVE KEY IS WS-SLOT-NO
               FILE STATUS IS WS-SLOT-STATUS.
           SELECT LOG-FILE ASSIGN TO LOGESD
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-LOG-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  SLOT-FILE
           RECORDING MODE IS F.
       01  SLOT-REC.
           05  SLOT-ID                PIC X(8).
           05  SLOT-QTY               PIC 9(5).
           05  FILLER                 PIC X(27).
       FD  LOG-FILE
           RECORDING MODE IS F.
       01  LOG-REC.
           05  LOG-TS                 PIC X(14).
           05  LOG-TEXT               PIC X(40).
           05  FILLER                 PIC X(6).
       WORKING-STORAGE SECTION.
       01  WS-SLOT-STATUS         PIC X(2).
       01  WS-LOG-STATUS          PIC X(2).
       01  WS-SLOT-NO             PIC 9(2).
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT SLOT-FILE
           PERFORM 1000-SCAN-SLOTS UNTIL WS-SLOT-STATUS NOT = '00'
           PERFORM 1100-SLOT-STATUS
           CLOSE SLOT-FILE
           OPEN EXTEND LOG-FILE
           PERFORM 2000-FILL-LOG UNTIL WS-LOG-STATUS NOT = '00'
           PERFORM 2100-LOG-STATUS
           CLOSE LOG-FILE WITH LOCK
           OPEN INPUT LOG-FILE
           PERFORM 3000-LOCK-STATUS
           DISPLAY 'AIXAFLK BAD ' WS-BAD
           GOBACK.
       1000-SCAN-SLOTS.
           READ SLOT-FILE NEXT RECORD
               AT END CONTINUE
           END-READ.
       1100-SLOT-STATUS.
           IF WS-SLOT-STATUS = '14'
              DISPLAY 'SLOT NUMBER TOO LARGE FOR THE RELATIVE KEY'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-SLOT-STATUS NOT = '10'
                 ADD 1 TO WS-BAD
              END-IF
           END-IF.
       2000-FILL-LOG.
           MOVE '20261122090000' TO LOG-TS
           MOVE 'FILL TO THE END OF THE EXTENT' TO LOG-TEXT
           WRITE LOG-REC.
       2100-LOG-STATUS.
           IF WS-LOG-STATUS = '34'
              DISPLAY 'LOG EXTENT FULL'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-LOG-STATUS NOT = '00'
                 ADD 1 TO WS-BAD
              END-IF
           END-IF.
       3000-LOCK-STATUS.
           IF WS-LOG-STATUS = '38'
              DISPLAY 'LOG FILE LOCKED'
              ADD 1 TO WS-BAD
           ELSE
              IF WS-LOG-STATUS NOT = '00'
                 ADD 1 TO WS-BAD
              END-IF
           END-IF.
