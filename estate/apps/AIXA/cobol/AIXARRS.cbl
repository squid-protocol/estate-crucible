       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXARRS.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXARRS - COPY PICK SLOTS TO A HISTORY RRDS.
      * IN BY SEQUENCE FROM SLOT 5, OUT BY NUMBER.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SLOT-IN ASSIGN TO SLOTIN
               ORGANIZATION IS RELATIVE
               ACCESS MODE IS SEQUENTIAL
               RELATIVE KEY IS WS-IN-NO
               FILE STATUS IS WS-IN-STATUS.
           SELECT SLOT-OUT ASSIGN TO SLOTOUT
               ORGANIZATION IS RELATIVE
               ACCESS MODE IS RANDOM
               RELATIVE KEY IS WS-OUT-NO
               FILE STATUS IS WS-OUT-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  SLOT-IN
           RECORDING MODE IS F.
       01  IN-REC.
           05  IN-ID                  PIC X(8).
           05  IN-QTY                 PIC 9(5).
           05  FILLER                 PIC X(27).
       FD  SLOT-OUT
           RECORDING MODE IS F.
       01  OUT-REC.
           05  OUT-ID                 PIC X(8).
           05  OUT-QTY                PIC 9(5).
           05  FILLER                 PIC X(27).
       WORKING-STORAGE SECTION.
       01  WS-IN-STATUS           PIC X(2).
       01  WS-OUT-STATUS          PIC X(2).
       01  WS-IN-NO               PIC 9(4) VALUE ZERO.
       01  WS-OUT-NO              PIC 9(4) VALUE ZERO.
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                 VALUE 'Y'.
       01  WS-COPIED              PIC 9(5) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT SLOT-IN
           OPEN I-O SLOT-OUT
           PERFORM 1000-POSITION
           PERFORM 2000-COPY UNTIL WS-EOF
           PERFORM 3000-TRIM
           CLOSE SLOT-IN
           CLOSE SLOT-OUT
           DISPLAY 'AIXARRS COPIED ' WS-COPIED
           GOBACK.
       1000-POSITION.
           MOVE 5 TO WS-IN-NO
           START SLOT-IN KEY IS NOT LESS THAN WS-IN-NO
               INVALID KEY SET WS-EOF TO TRUE
           END-START.
       2000-COPY.
           READ SLOT-IN
               AT END SET WS-EOF TO TRUE
           END-READ
           IF NOT WS-EOF
              MOVE IN-REC TO OUT-REC
              MOVE WS-IN-NO TO WS-OUT-NO
              WRITE OUT-REC
                  INVALID KEY PERFORM 2100-REPLACE
              END-WRITE
              ADD 1 TO WS-COPIED
           END-IF.
       2100-REPLACE.
           REWRITE OUT-REC
               INVALID KEY DISPLAY 'SLOT LOST ' WS-OUT-NO
           END-REWRITE.
       3000-TRIM.
           MOVE 99 TO WS-OUT-NO
           DELETE SLOT-OUT RECORD
               INVALID KEY DISPLAY 'SLOT 99 NOT THERE'
           END-DELETE.
