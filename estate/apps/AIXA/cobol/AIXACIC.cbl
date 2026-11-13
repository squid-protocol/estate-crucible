       IDENTIFICATION DIVISION.
       PROGRAM-ID.    AIXACIC.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * AIXACIC - ONLINE LOOKUP (TRANSACTION AXLK).
      * AUDIT LOG RECORD BY BYTE ADDRESS, PICK SLOT BY RECORD NUMBER.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-LOG-REC.
           05  WL-TS                  PIC X(14).
           05  WL-TEXT                PIC X(40).
           05  FILLER                 PIC X(6).
       01  WS-SLOT-REC.
           05  WSL-ID                 PIC X(8).
           05  WSL-QTY                PIC 9(5).
           05  FILLER                 PIC X(27).
       01  WS-LOG-RBA             PIC S9(8) COMP VALUE ZERO.
       01  WS-SLOT-RRN            PIC S9(8) COMP VALUE ZERO.
       01  WS-RESP                PIC S9(8) COMP.
       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-LOG-BY-RBA
           PERFORM 2000-SLOT-BY-RRN
           EXEC CICS RETURN
           END-EXEC.
       1000-LOG-BY-RBA.
           MOVE ZERO TO WS-LOG-RBA
           EXEC CICS READ FILE('AIXALOG') INTO(WS-LOG-REC)
                     RIDFLD(WS-LOG-RBA) RBA
                     RESP(WS-RESP)
           END-EXEC
           IF WS-RESP NOT = 0
              MOVE 4 TO RETURN-CODE
           END-IF.
       2000-SLOT-BY-RRN.
           MOVE 3 TO WS-SLOT-RRN
           EXEC CICS READ FILE('AIXASLT') INTO(WS-SLOT-REC)
                     RIDFLD(WS-SLOT-RRN) RRN
                     RESP(WS-RESP)
           END-EXEC
           IF WS-RESP NOT = 0
              MOVE 4 TO RETURN-CODE
           END-IF.
