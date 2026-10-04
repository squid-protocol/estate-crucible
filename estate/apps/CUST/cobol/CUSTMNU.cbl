       IDENTIFICATION DIVISION.
       PROGRAM-ID.    CUSTMNU.
       AUTHOR.       CUSTOMER SYSTEMS.
      *------------------------------------------------------------
      * CUSTMNU - CUSTOMER SYSTEMS MENU (TRANSACTION CMNU).
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-MENU-TEXT PIC X(40)
                              VALUE 'CUSTOMER SYSTEMS: CINQ = INQUIRY'.
       PROCEDURE DIVISION.
       0000-MAIN.
           EXEC CICS SEND TEXT FROM(WS-MENU-TEXT) ERASE
           END-EXEC
           EXEC CICS RETURN TRANSID('CMNU')
           END-EXEC.
