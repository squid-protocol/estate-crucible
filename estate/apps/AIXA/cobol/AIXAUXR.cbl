       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAUXR.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAUXR - ORDER EXTRACT REWRITTEN IN A UNIX FILE.
      * A UNIX FILE CANNOT BE OPEN I-O, SO REWRITE GIVES 49.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT UR-FILE ASSIGN TO UXRWR
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-UR-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  UR-FILE
           RECORDING MODE IS F.
       01  UR-REC.
           05  UR-ID                  PIC X(8).
           05  UR-TEXT                PIC X(32).
       WORKING-STORAGE SECTION.
       01  WS-UR-STATUS           PIC X(2).
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN OUTPUT UR-FILE
           MOVE 'ORD00001' TO UR-ID
           MOVE 'FIRST EXTRACT RECORD' TO UR-TEXT
           WRITE UR-REC
           REWRITE UR-REC
           PERFORM 1000-CHECK
           CLOSE UR-FILE
           DISPLAY 'AIXAUXR BAD ' WS-BAD
           GOBACK.
       1000-CHECK.
           IF WS-UR-STATUS = '49'
              DISPLAY 'REWRITE REFUSED FOR A UNIX FILE'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
