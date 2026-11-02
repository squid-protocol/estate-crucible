       IDENTIFICATION DIVISION.
       PROGRAM-ID.    HKEPWALK.
       AUTHOR.       KEEP SYSTEMS.
      *------------------------------------------------------------
      * HKEPWALK - WALK THE KEEP DATABASE WITH UNQUALIFIED GN CALLS.
      * THE LOOP ENDS ON STATUS GB; ONE MORE GN RESTARTS THE WALK.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-GN                  PIC X(4) VALUE 'GN  '.
       01  WS-COUNT               PIC S9(4) COMP VALUE 0.
       01  WS-IO-AREA             PIC X(80).
       LINKAGE SECTION.
       01  IO-PCB.
           05  IO-LTERM               PIC X(8).
           05  IO-RSV                 PIC X(2).
           05  IO-STATUS              PIC X(2).
       01  DB-PCB.
           05  DB-DBD                 PIC X(8).
           05  DB-LEVEL               PIC X(2).
           05  DB-STATUS              PIC X(2).
       PROCEDURE DIVISION USING IO-PCB DB-PCB.
       0000-MAIN.
           PERFORM 1000-SCAN
           PERFORM 2000-RESTART
           GOBACK.
       1000-SCAN.
           CALL 'CBLTDLI' USING WS-GN DB-PCB WS-IO-AREA
           IF DB-STATUS = SPACES
              ADD 1 TO WS-COUNT
              PERFORM 1000-SCAN
           END-IF.
       2000-RESTART.
           CALL 'CBLTDLI' USING WS-GN DB-PCB WS-IO-AREA
           IF DB-STATUS = SPACES
              DISPLAY 'RESTARTED AT FIRST ROOT'
           END-IF.
