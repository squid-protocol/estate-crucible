       IDENTIFICATION DIVISION.
       PROGRAM-ID.    RPTHDR.
       AUTHOR.       MIS REPORTING.
       DATE-WRITTEN. 05/20/97.
      *------------------------------------------------------------
      * RPTHDR - PRINT THE MONTHLY OPERATIONS HEADINGS.
      *------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT RPT-FILE ASSIGN TO RPTOUT
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-RPT-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  RPT-FILE
           RECORDING MODE IS F.
       01  RPT-LINE               PIC X(80).
       WORKING-STORAGE SECTION.
       01  WS-RPT-STATUS          PIC X(2).
       01  HDR-LINE-1             PIC X(80) VALUE 'ACME MANUFACTURING  -
      -    '  MONTHLY OPERATIONS SUMMARY  -  CONFIDENTIAL'.
       01  HDR-LINE-2             PIC X(80) VALUE 'REGION   PLANT    UNI
      -    'TS BUILT    UNITS SHIPPED    BACKLOG  STATUS'.
       01  WS-PAGE                PIC 9(4) VALUE 0.
       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN OUTPUT RPT-FILE
           PERFORM 1000-HEADINGS
           CLOSE RPT-FILE
           GOBACK.
       1000-HEADINGS.
           ADD 1 TO WS-PAGE
           WRITE RPT-LINE FROM HDR-LINE-1
           WRITE RPT-LINE FROM HDR-LINE-2.
