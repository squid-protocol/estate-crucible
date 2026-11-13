       IDENTIFICATION DIVISION.
       PROGRAM-ID.    MQBRIMS.
       AUTHOR.       BRIDGE SYSTEMS.
      *------------------------------------------------------------
      * MQBRIMS - START THE ORDER TRANSACTION IN IMS VIA THE BRIDGE.
      * MESSAGE: MQIIH, THEN LL ZZ, THE TRANCODE AND THE DATA.
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
       01  WS-MSGLEN              PIC S9(9) COMP VALUE 108.
       01  WS-MSG.
           05  WS-IIH.
               COPY MQBIIH.
           05  WS-LL                  PIC S9(4) COMP VALUE 24.
           05  WS-ZZ                  PIC S9(4) COMP VALUE 0.
           05  WS-TRANCODE            PIC X(8) VALUE 'ORDENTRY'.
           05  WS-DATA                PIC X(12) VALUE 'ORD00001 100'.
       PROCEDURE DIVISION.
       0000-MAIN.
           CALL 'MQCONN' USING WS-QMGR WS-HCONN WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQBRIMS CONNECT FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           MOVE 'IMS.BRIDGE.ORDQ' TO MQB-OBJNAME
           MOVE 16 TO WS-OO-OPTIONS
           CALL 'MQOPEN'
               USING WS-HCONN WS-OD WS-OO-OPTIONS WS-HOBJ WS-COMPCODE
               WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQBRIMS OPEN FAILED ' WS-REASON
              MOVE 12 TO RETURN-CODE
              GOBACK
           END-IF
           PERFORM 1000-BUILD
           CALL 'MQPUT'
               USING WS-HCONN WS-HOBJ WS-MD WS-PMO WS-MSGLEN WS-MSG
               WS-COMPCODE WS-REASON
           IF WS-COMPCODE NOT = 0
              DISPLAY 'MQBRIMS PUT FAILED ' WS-REASON
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
           MOVE 'MQIMS   ' TO MQB-FORMAT
           MOVE 'IMS.BRIDGE.REPLYQ' TO MQB-REPLYQ
           MOVE '1' TO MQB-IIH-COMMIT
           MOVE 'MQSTR   ' TO MQB-IIH-FORMAT.
