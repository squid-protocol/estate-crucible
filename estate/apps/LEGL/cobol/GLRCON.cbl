000100***************************************************************** GLRCON
000200*                                                               * GLRCON
000300*   GLRCON  -  GENERAL LEDGER RECONCILIATION                    * GLRCON
000400*   SYSTEM  :  GL / FINANCIAL REPORTING                         * GLRCON
000500*   AUTHOR  :  H. VANDERMEER        DATE: 03/11/83              * GLRCON
000600*                                                               * GLRCON
000700*   INPUT   :  GLMAST (VSAM KSDS), GLTRAN (QSAM)                * GLRCON
000800*   OUTPUT  :  RECON REPORT (SYSOUT=A)                          * GLRCON
000900*   CALLS   :  NONE. (WAS: CALL 'DTCONV' USING WS-DATE)         * GLRCON
001000*                                                               * GLRCON
001100***************************************************************** GLRCON
001200/                                                                 GLRCON
001300 IDENTIFICATION DIVISION.                                         GLRCON
001400 PROGRAM-ID.    GLRCON.                                           GLRCON
001500 AUTHOR.       H VANDERMEER.                                      GLRCON
001600 INSTALLATION. CORPORATE ACCOUNTING.                              GLRCON
001700 DATE-WRITTEN. 03/11/83.                                          GLRCON
001800*------------------------------------------------------------     GLRCON
001900* CHANGE LOG                                                      GLRCON
002000* DATE     BY   REQ#     DESCRIPTION                              GLRCON
002100* -------- ---- -------- ------------------------------------     GLRCON
002200* 04/02/86 HV   R86-014  REMOVED COPY OLDDATE, USE GLDATE         GLRCON
002300* 11/19/91 PK   R91-233  PERFORM 9000-ABEND ON BAD STATUS         GLRCON
002400* 06/07/99 TS   Y2K-0412 CALL 'DTCONV' REPLACED BY WINDOWING      GLRCON
002500* 09/12/03 TS   R03-118  TAPE RESTART RETIRED (SEE 9900-...)      GLRCON
002600*           -->  PERFORM 9900-TAPE-RESTART NO LONGER CODED        GLRCON
002700*------------------------------------------------------------     GLRCON
002800 DATA DIVISION.                                                   GLRCON
002900 WORKING-STORAGE SECTION.                                         GLRCON
003000 01  WS-GL-DATE             PIC 9(8) VALUE ZERO.                  GLRCON
003100 01  WS-DIFF                PIC S9(11)V99 COMP-3 VALUE ZERO.      GLRCON
003200 01  WS-STATUS              PIC X(2) VALUE '00'.                  GLRCON
003300 PROCEDURE DIVISION.                                              GLRCON
003400 0000-MAINLINE.                                                   GLRCON
003500     PERFORM 1000-COMPARE                                         GLRCON
003600     IF WS-STATUS NOT = '00'                                      GLRCON
003700        PERFORM 9000-ABEND                                        GLRCON
003800     END-IF                                                       GLRCON
003900     GOBACK.                                                      GLRCON
004000 1000-COMPARE.                                                    GLRCON
004100     COMPUTE WS-DIFF = WS-DIFF + 0.                               GLRCON
004200 9000-ABEND.                                                      GLRCON
004300     DISPLAY 'GLRCON ABEND, STATUS ' WS-STATUS                    GLRCON
004400     MOVE 16 TO RETURN-CODE                                       GLRCON
004500     GOBACK.                                                      GLRCON
004600 9900-TAPE-RESTART.                                               GLRCON
004700     DISPLAY 'GLRCON RESTART FROM TAPE CHECKPOINT'.               GLRCON
