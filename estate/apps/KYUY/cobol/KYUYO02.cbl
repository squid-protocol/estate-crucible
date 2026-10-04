       IDENTIFICATION DIVISION.
       PROGRAM-ID.    KYUYO02.
      *------------------------------------------------------------
      * KYUYO02 - è‹ó^åvéZ (SHIFT-JIS, PC DOWNLOAD)
      *------------------------------------------------------------
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  è‹ó^äz                    PIC 9(7) VALUE 0.
       01  ï\ëË                     PIC X(16) VALUE 'è‹ó^ñæç◊'.
       01  WS-END                 PIC S9(4) COMP.
       PROCEDURE DIVISION.
       è‹ó^èàóù.
           ADD 1000 TO è‹ó^äz
           DISPLAY ï\ëË
           GOBACK.
