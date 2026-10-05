       IDENTIFICATION DIVISION.
       PROGRAM-ID.    SHPINQ.
       AUTHOR.       LOGISTICS IT.
      *------------------------------------------------------------
      * SHPINQ - SHIPMENT INQUIRY (TRANSACTION SHPI).
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-COMMAREA.
           COPY SHPCOMM.
       01  WS-ORDER.
           COPY ORDREC.
       01  WS-RATE-PARM.
           COPY SHPRATE.
           COPY DFHAID.
       01  WS-RESP                PIC S9(8) COMP.
       LINKAGE SECTION.
       01  DFHCOMMAREA            PIC X(60).
       PROCEDURE DIVISION.
       0000-MAIN.
           IF EIBCALEN = 0
              EXEC CICS SEND TEXT FROM(WS-COMMAREA) ERASE
              END-EXEC
              EXEC CICS RETURN TRANSID('SHPI')
                        COMMAREA(WS-COMMAREA)
              END-EXEC
           END-IF
           MOVE DFHCOMMAREA TO WS-COMMAREA
           IF EIBAID = DFHPF3
              EXEC CICS XCTL PROGRAM('SHPMENU')
              END-EXEC
           END-IF
           PERFORM 1000-RATE
           PERFORM 2000-AUDIT
           EXEC CICS RETURN TRANSID('SHPI')
                     COMMAREA(WS-COMMAREA)
           END-EXEC.
       1000-RATE.
           MOVE CA-ORD-ID TO ORD-ID
           EXEC CICS LINK PROGRAM('SHPRATE')
                     COMMAREA(WS-COMMAREA)
           END-EXEC.
       2000-AUDIT.
           EXEC CICS LINK PROGRAM('SHPAUDT')
                     COMMAREA(WS-COMMAREA)
           END-EXEC.
