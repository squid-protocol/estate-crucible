       IDENTIFICATION DIVISION.
       PROGRAM-ID.    CUSTINQ.
       AUTHOR.       CUSTOMER SYSTEMS.
      *------------------------------------------------------------
      * CUSTINQ - CUSTOMER INQUIRY (TRANSACTION CINQ).
      * PSEUDO-CONVERSATIONAL.
      * FIRST ENTRY (EIBCALEN = 0) SENDS THE EMPTY MAP AND RETURNS.
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-COMMAREA.
           COPY CUSTCOMM.
           COPY CUSTMS.
           COPY DFHAID.
       01  WS-RESP                PIC S9(8) COMP.
       01  WS-DATE-AREA.
           COPY DATEWS.
       01  WS-I                   PIC S9(4) COMP.
       LINKAGE SECTION.
       01  DFHCOMMAREA            PIC X(50).
       PROCEDURE DIVISION.
       0000-MAIN.
           IF EIBCALEN = 0
              MOVE LOW-VALUES TO CUSTMAPO
              EXEC CICS SEND MAP('CUSTMAP') MAPSET('CUSTMS') ERASE
              END-EXEC
              EXEC CICS
                  RETURN TRANSID('CINQ')
                  COMMAREA(WS-COMMAREA)
              END-EXEC
           END-IF
           MOVE DFHCOMMAREA TO WS-COMMAREA
           PERFORM 1000-RECEIVE-MAP
           IF EIBAID = DFHPF3
              PERFORM RETURN-TO-MENU
           END-IF
           PERFORM 2000-LOOKUP-CUSTOMER
           PERFORM 3000-SEND-MAP
           PERFORM 4000-FIND-BLANK
           EXEC CICS RETURN TRANSID('CINQ')
                     COMMAREA(WS-COMMAREA)
           END-EXEC.
       1000-RECEIVE-MAP.
           EXEC CICS RECEIVE MAP('CUSTMAP') MAPSET('CUSTMS')
                     INTO(CUSTMAPI) RESP(WS-RESP)
           END-EXEC
           MOVE CUSTIDI TO CA-CUST-ID.
       RETURN-TO-MENU.
           MOVE 'RETURNING TO MENU' TO CA-MSG
           PERFORM 9100-SAVE-STATE
           EXEC CICS XCTL PROGRAM('CUSTMNU')
                     COMMAREA(WS-COMMAREA)
           END-EXEC.
       2000-LOOKUP-CUSTOMER.
           EXEC CICS LINK PROGRAM('CUSTDBIO')
                     COMMAREA(WS-COMMAREA)
           END-EXEC
           IF CA-RETURN-CODE NOT = 0
              MOVE CA-MSG TO MSGO
           END-IF.
       3000-SEND-MAP.
           MOVE CA-CUST-ID TO CUSTIDO
           EXEC CICS SEND MAP('CUSTMAP') MAPSET('CUSTMS')
                     DATAONLY CURSOR
           END-EXEC.
       4000-FIND-BLANK.
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 8
              IF CA-CUST-ID (WS-I:1) = SPACE
                 EXIT PERFORM
              END-IF
           END-PERFORM
           PERFORM 9100-SAVE-STATE.
       9100-SAVE-STATE.
           MOVE SPACES TO CA-CUST-ID.
