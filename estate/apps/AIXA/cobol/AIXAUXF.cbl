       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXAUXF.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXAUXF - ORDER EXTRACT IN A Z/OS UNIX FILE.
      * PATH= ON A DD IS A UNIX FILE, NOT A VSAM PATH. OPEN I-O: 37.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT UX-FILE ASSIGN TO UXOUT
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-UX-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  UX-FILE
           RECORDING MODE IS F.
       01  UX-REC.
           05  UX-ID                  PIC X(8).
           05  UX-TEXT                PIC X(32).
       WORKING-STORAGE SECTION.
       01  WS-UX-STATUS           PIC X(2).
       01  WS-BAD                 PIC 9(3) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN I-O UX-FILE
           PERFORM 1000-CHECK
           DISPLAY 'AIXAUXF BAD ' WS-BAD
           GOBACK.
       1000-CHECK.
           IF WS-UX-STATUS = '37'
              DISPLAY 'OPEN I-O REFUSED FOR A UNIX FILE'
           ELSE
              ADD 1 TO WS-BAD
           END-IF.
