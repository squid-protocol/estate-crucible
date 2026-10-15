000100***************************************************************** INVTBAT
000200*   INVTBAT  -  STOCK STATUS REPORT, REORDER POINT CHECK        * INVTBAT
000300*   SYSTEM  :  INVT / INVENTORY CONTROL      DATE: 06/14/83     * INVTBAT
000400***************************************************************** INVTBAT
000500/                                                                 INVTBAT
000600 IDENTIFICATION DIVISION.                                         INVTBAT
000700 PROGRAM-ID.    INVTBAT.                                          INVTBAT
000800 AUTHOR.       D KOWALCZYK.                                       INVTBAT
000900 INSTALLATION. MATERIALS CONTROL.                                 INVTBAT
001000 DATE-WRITTEN. 06/14/83.                                          INVTBAT
001100*------------------------------------------------------------     INVTBAT
001200* INVTBAT - LIST STOCK AT OR BELOW REORDER POINT.                 INVTBAT
001300*------------------------------------------------------------     INVTBAT
001400 ENVIRONMENT DIVISION.                                            INVTBAT
001500 INPUT-OUTPUT SECTION.                                            INVTBAT
001600 FILE-CONTROL.                                                    INVTBAT
001700     SELECT STOCK-FILE ASSIGN TO STOCKIN                          INVTBAT
001800         ORGANIZATION IS SEQUENTIAL                               INVTBAT
001900         FILE STATUS IS WS-STOCK-STATUS.                          INVTBAT
002000     SELECT LIST-FILE ASSIGN TO STKLIST                           INVTBAT
002100         ORGANIZATION IS SEQUENTIAL                               INVTBAT
002200         FILE STATUS IS WS-LIST-STATUS.                           INVTBAT
002300 DATA DIVISION.                                                   INVTBAT
002400 FILE SECTION.                                                    INVTBAT
002500 FD  STOCK-FILE                                                   INVTBAT
002600     RECORDING MODE IS F.                                         INVTBAT
002700 01  STOCK-IN               PIC X(80).                            INVTBAT
002800 FD  LIST-FILE                                                    INVTBAT
002900     RECORDING MODE IS F.                                         INVTBAT
003000 01  LIST-LINE              PIC X(133).                           INVTBAT
003100 WORKING-STORAGE SECTION.                                         INVTBAT
003200 01  WS-STOCK-STATUS        PIC X(2).                             INVTBAT
003300 01  WS-LIST-STATUS         PIC X(2).                             INVTBAT
003400 01  WS-EOF                 PIC X VALUE 'N'.                      INVTBAT
003500 01  WS-LOW-COUNT           PIC 9(5) COMP-3 VALUE 0.              INVTBAT
003600 01  WS-REC.                                                      INVTBAT
003700     COPY INVTREC.                                                INVTBAT
003800 PROCEDURE DIVISION.                                              INVTBAT
003900 0000-MAINLINE SECTION.                                           INVTBAT
004000     OPEN INPUT STOCK-FILE OUTPUT LIST-FILE                       INVTBAT
004100     PERFORM 1000-PROCESS-STOCK UNTIL WS-EOF = 'Y'                INVTBAT
004200     CLOSE STOCK-FILE LIST-FILE                                   INVTBAT
004300     GOBACK.                                                      INVTBAT
004400 1000-PROCESS-STOCK SECTION.                                      INVTBAT
004500     PERFORM 1100-READ-STOCK                                      INVTBAT
004600     IF WS-EOF NOT = 'Y'                                          INVTBAT
004700        PERFORM 1200-CHECK-REORDER.                               INVTBAT
004800 1100-READ-STOCK SECTION.                                         INVTBAT
004900     READ STOCK-FILE INTO WS-REC AT END MOVE 'Y' TO WS-EOF.       INVTBAT
005000 1200-CHECK-REORDER SECTION.                                      INVTBAT
005100     IF STK-ON-HAND NOT > STK-REORDER-PT                          INVTBAT
005200        ADD 1 TO WS-LOW-COUNT                                     INVTBAT
005300        MOVE SPACES TO LIST-LINE                                  INVTBAT
005400        MOVE STK-PART-NO TO LIST-LINE                             INVTBAT
005500        WRITE LIST-LINE.                                          INVTBAT
