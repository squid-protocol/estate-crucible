       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQBRCIH.
       AUTHOR.       BRIDGE SYSTEMS.
      *------------------------------------------------------------
      * MQBRCIH - RUN A CICS PROGRAM VIA THE CICS DPL BRIDGE.
      * MESSAGE: MQCIH FOLLOWED BY THE COMMAREA.
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
       01  WS-MD.
           COPY MQBMD.
       01  WS-OD.
           COPY MQBOD.
       01  WS-PMO.
           COPY MQBPMO.
       01  WS-MSGLEN              PIC S9(9) COMP VALUE 220.
       01  WS-MSG.
           05  WS-CIH.
               COPY MQBCIH.
           05  WS-COMMAREA            PIC X(40) VALUE 'ORD00001 100'.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQBRCIH CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'CICS.BRIDGE.ORDQ' TO MQB-OBJNAME
           MOVE 16 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQBRCIH OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-BUILD
           CALL 'MQPUT'
               USING WS-HCONN WS-HOBJ WS-MD WS-PMO WS-MSGLEN WS-MSG
               WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQBRCIH PUT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           CALL 'MQCMIT' USING WS-HCONN WS-COMPCODE WS-REASON
           CALL 'MQCLOSE'
               USING WS-HCONN WS-HOBJ WS-CO-OPTIONS WS-COMPCODE
               WS-REASON
           CALL 'MQDISC' USING WS-HCONN WS-COMPCODE WS-REASON
           GOBACK.
       1000-BUILD.
           MOVE 'MQCICS  ' TO MQB-FORMAT
           MOVE 'CICS.BRIDGE.REPLYQ' TO MQB-REPLYQ
           MOVE 'ORDCOMM ' TO MQB-CIH-FORMAT
           MOVE 1 TO MQB-CIH-LINKTYPE
           MOVE 273 TO MQB-CIH-UOWCONTROL.
