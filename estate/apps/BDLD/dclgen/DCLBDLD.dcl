      ****************************************************************
      * DCLGEN TABLE(PROD.BDLD_SUMMARY)                              *
      *        LIBRARY(PROD.BDLD.DCLGEN(DCLBDLD))                    *
      *        LANGUAGE(COBOL) QUOTE                                 *
      ****************************************************************
           EXEC SQL DECLARE PROD.BDLD_SUMMARY TABLE
           ( ACCT_ID                        CHAR(10) NOT NULL,
             TOTAL_AMT                      DECIMAL(9, 0) NOT NULL
           ) END-EXEC.
      ****************************************************************
      * COBOL DECLARATION FOR TABLE PROD.BDLD_SUMMARY                *
      ****************************************************************
       01  DCLBDLD-SUMMARY.
           10  ACCT-ID                PIC X(10).
           10  TOTAL-AMT              PIC S9(9) USAGE COMP-3.
      ****************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 2     *
      ****************************************************************
