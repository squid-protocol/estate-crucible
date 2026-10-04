      ****************************************************************
      * DCLGEN TABLE(PROD.INVENTORY)                                 *
      *        LIBRARY(PROD.INVN.DCLGEN(DCLINVT))                    *
      *        LANGUAGE(COBOL) QUOTE                                 *
      ****************************************************************
           EXEC SQL DECLARE PROD.INVENTORY TABLE
           ( ITEM_ID                        CHAR(12) NOT NULL,
             ON_HAND                        DECIMAL(9, 0) NOT NULL,
             LAST_COUNT                     DATE
           ) END-EXEC.
      ****************************************************************
      * COBOL DECLARATION FOR TABLE PROD.INVENTORY                   *
      ****************************************************************
       01  DCLINVENTORY.
           10  ITEM-ID                PIC X(12).
           10  ON-HAND                PIC S9(9) USAGE COMP-3.
           10  LAST-COUNT             PIC X(10).
      ****************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 3     *
      ****************************************************************
