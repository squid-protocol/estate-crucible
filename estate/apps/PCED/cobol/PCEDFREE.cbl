       >>SOURCE FORMAT FREE
IDENTIFICATION DIVISION.
PROGRAM-ID.    PCEDFREE.
*> ------------------------------------------------------------
*>  PCEDFREE - PRICE BAND REPORT, FREE FORMAT.
*> ------------------------------------------------------------
DATA DIVISION.
WORKING-STORAGE SECTION.
    01  WS-BAND.
       05  WS-LOW                 PIC 9(5) VALUE 0.
       05  WS-HIGH                PIC 9(5) VALUE 99999.
PROCEDURE DIVISION.
MAIN-PARA.
    PERFORM SHOW-BAND
    GOBACK.
SHOW-BAND.
    DISPLAY 'BAND ' WS-LOW ' - ' WS-HIGH.
