       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAESU.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAESU - MARK LOG RECORDS REVIEWED.
      * AN ESDS RECORD KEEPS ITS LENGTH; NO DELETE.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT LOG-FILE ASSIGN TO LOGUPD
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
       01  WS-MARKED              PIC 9(5) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O LOG-FILE
           PERFORM 8000-READ
           PERFORM 1000-MARK UNTIL WS-EOF
           CLOSE LOG-FILE
           DISPLAY 'AIXAESU MARKED ' WS-MARKED
           GOBACK.
       1000-MARK.
           IF LOG-TEXT = 'ORDER ORD00001 ACCEPTED'
              MOVE 'ORDER ORD00001 REVIEWED' TO LOG-TEXT
              REWRITE LOG-REC
              ADD 1 TO WS-MARKED
           END-IF
           PERFORM 8000-READ.
       8000-READ.
           READ LOG-FILE
              AT END
                 SET WS-EOF TO TRUE
           END-READ.
