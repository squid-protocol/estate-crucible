000100***************************************************************** GLRSUM
000200*   GLRSUM  -  GL SUMMARY BY COST CENTRE                        * GLRSUM
000300*   NOTE: DO NOT COPY GLWORK HERE - SEE GLRCON 1000-COMPARE      *GLRSUM
000400***************************************************************** GLRSUM
000500/                                                                 GLRSUM
000600 IDENTIFICATION DIVISION.                                         GLRSUM
000700 PROGRAM-ID.    GLRSUM.                                           GLRSUM
000800 AUTHOR.       P KOWALCZYK.                                       GLRSUM
000900 DATE-WRITTEN. 11/19/91.                                          GLRSUM
001000 DATA DIVISION.                                                   GLRSUM
001100 WORKING-STORAGE SECTION.                                         GLRSUM
001200 01  WS-CC-TOTAL            PIC S9(11)V99 COMP-3 VALUE ZERO.      GLRSUM
001300 PROCEDURE DIVISION.                                              GLRSUM
001400 0000-MAINLINE.                                                   GLRSUM
001500     PERFORM 1000-SUM                                             GLRSUM
001600     GOBACK.                                                      GLRSUM
001700 1000-SUM.                                                        GLRSUM
001800     ADD 1 TO WS-CC-TOTAL.                                        GLRSUM
