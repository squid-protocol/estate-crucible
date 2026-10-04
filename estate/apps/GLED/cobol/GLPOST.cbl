000100 IDENTIFICATION DIVISION.
000200 PROGRAM-ID.
000300     GLPOST.
000400 AUTHOR.       GENERAL LEDGER.
000500 DATE-WRITTEN. 02/01/84.
000600*------------------------------------------------------------
000700* GLPOST - POST JOURNAL ENTRIES TO THE LEDGER.
000800*------------------------------------------------------------
000900 ENVIRONMENT DIVISION.
001000 INPUT-OUTPUT SECTION.
001100 FILE-CONTROL.
001200     SELECT JRNL-FILE ASSIGN TO                                   GL001000
001300         JRNLIN                                                   GL001000
001400         ORGANIZATION IS SEQUENTIAL
001500         FILE STATUS IS WS-JRNL-STATUS.
001600 DATA DIVISION.
001700 FILE SECTION.
001800 FD  JRNL-FILE
001900     RECORDING MODE IS F.
002000 01  JRNL-REC.
002100     05  JRNL-ACCT              PIC X(12).
002200     05  JRNL-AMT               PIC S9(11)V99 COMP-3.
002300     05  FILLER                 PIC X(61).
002400 WORKING-STORAGE SECTION.
002500 01  WS-JRNL-STATUS         PIC X(2).
002600     88  WS-JRNL-EOF            VALUE '10'.
002700 01  WS-TOTAL               PIC S9(13)V99 COMP-3 VALUE ZERO.
002800 PROCEDURE        DIVISION.
002900 0000-MAIN.                                                       GL000100
003000     OPEN INPUT JRNL-FILE                                         GL000100
003100     PERFORM 1000-INIT                                            GL000100
003200     PERFORM 2000-POST UNTIL WS-JRNL-EOF                          GL000100
003300     PERFORM END-IPROC1                                           GL000100
003400     PERFORM End-Program                                          GL000100
003500     GOBACK.                                                      GL000100
003600 1000-INIT. MOVE ZERO TO WS-TOTAL
003700     PERFORM 1100-OPEN-MSG.
003800 1100-OPEN-MSG
003900     .
004000     DISPLAY 'GLPOST START'.
004100 2000-POST.                                                       GL002000
004200     READ JRNL-FILE                                               GL002000
004300        AT END                                                    GL002000
004400           SET WS-JRNL-EOF TO TRUE                                GL002000
004500        NOT AT END                                                GL002000
004600           ADD JRNL-AMT TO WS-TOTAL                               GL002000
004700     END-READ.                                                    GL002000
004800 END-IPROC1.
004900     CLOSE JRNL-FILE.
005000 End-Program.
005100     DISPLAY 'GLPOST TOTAL ' WS-TOTAL.
