       IDENTIFICATION DIVISION.
       PROGRAM-ID.    ORDPRICE.
       AUTHOR.       M OKAFOR.
      *------------------------------------------------------------
      * ORDPRICE - PRICE ONE ORDER LINE. CALLED BY ORDMAIN.
      *------------------------------------------------------------
       DATA DIVISION.
       LINKAGE SECTION.
       01  LK-ORDER.
           COPY ORDREC.
       PROCEDURE DIVISION USING LK-ORDER.
       0000-MAIN.
           COMPUTE ORD-PRICE = ORD-QTY * 1.25
           GOBACK.
