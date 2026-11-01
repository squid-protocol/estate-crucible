       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQSAGET.
       AUTHOR.       ORDER SYSTEMS.
      *------------------------------------------------------------
      * MQSAGET - DRAIN THE ORDER QUEUE UNDER SYNCPOINT.
      * THE LOOP ENDS ON REASON 2033 (NO MESSAGE).
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
       01  WS-MD.
           COPY MQSMD.
       01  WS-OD.
           COPY MQSOD.
       01  WS-GMO.
           COPY MQSGMO.
       01  WS-DONE-FLAG           PIC X VALUE 'N'.
           88  WS-DONE                VALUE 'Y'.
       01  WS-COUNT               PIC 9(5) VALUE ZERO.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSAGET CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'ORDERS.IN' TO MQS-OBJNAME
           MOVE 1 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQSAGET OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-GET UNTIL WS-DONE
           PERFORM 3000-FINISH
           GOBACK.
       1000-GET.
           MOVE 3 TO MQS-GMO-OPTIONS
           MOVE 5000 TO MQS-GMO-WAITINT
           CALL 'MQGET'
               USING WS-HCONN WS-HOBJ WS-MD WS-GMO WS-BUFLEN WS-BUF
               WS-DATALEN WS-COMPCODE WS-REASON
           IF WS-COMPCODE = 0
              PERFORM 2000-HANDLE
           ELSE
              IF WS-REASON = 2033
                 SET WS-DONE TO TRUE
              ELSE
                 PERFORM 9000-BACKOUT
              END-IF
           END-IF.
       2000-HANDLE.
           ADD 1 TO WS-COUNT.
       3000-FINISH.
           CALL 'MQCMIT' USING WS-HCONN WS-COMPCODE WS-REASON
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           DISPLAY 'MQSAGET ORDERS ' WS-COUNT.
       9000-BACKOUT.
           CALL 'MQBACK' USING WS-HCONN WS-COMPCODE WS-REASON
           DISPLAY 'MQSAGET BACKED OUT ' WS-REASON
           MOVE 8 TO RETURN-CODE
           SET WS-DONE TO TRUE.
