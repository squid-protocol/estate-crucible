       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSADYN.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSADYN - PUT ONE AUDIT MESSAGE; THE MQI VERB NAMES
      * ARE HELD IN DATA ITEMS SO A TRACING STUB CAN REPLACE THEM.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-QMGR                PIC X(48) VALUE 'QM01'.
       01  WS-HCONN               PIC S9(9) COMP VALUE 0.
       01  WS-HOBJ                PIC S9(9) COMP VALUE 0.
       01  WS-COMPCODE            PIC S9(9) COMP VALUE 0.
       01  WS-REASON              PIC S9(9) COMP VALUE 0.
       01  WS-OO-OPTIONS          PIC S9(9) COMP VALUE 0.
       01  WS-CO-OPTIONS          PIC S9(9) COMP VALUE 0.
       01  WS-BUFLEN              PIC S9(9) COMP VALUE 80.
       01  WS-DATALEN             PIC S9(9) COMP VALUE 0.
       01  WS-BUF                 PIC X(80).
       01  WS-V-CONN              PIC X(8) VALUE 'MQCONN'.
       01  WS-V-OPEN              PIC X(8) VALUE 'MQOPEN'.
       01  WS-V-PUT               PIC X(8) VALUE 'MQPUT'.
       01  WS-V-CLOSE             PIC X(8) VALUE 'MQCLOSE'.
       01  WS-V-DISC              PIC X(8) VALUE 'MQDISC'.
       01  WS-MD.
           COPY MQSMD.
       01  WS-OD.
           COPY MQSOD.
       01  WS-PMO.
           COPY MQSPMO.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL WS-V-CONN USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSADYN CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-PUT
           CALL WS-V-DISC USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
       1000-PUT.
           MOVE 'AUDIT.LOG' TO MQS-OBJNAME
           MOVE 16 TO WS-OO-OPTIONS
           CALL WS-V-OPEN
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSADYN OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'AUDIT RUN COMPLETE' TO WS-BUF
           CALL WS-V-PUT
               USING WS-HCONN WS-HOBJ WS-MD WS-PMO WS-BUFLEN WS-BUF
               WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSADYN PUT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           CALL WS-V-CLOSE
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON.
