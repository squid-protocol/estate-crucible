      ****************************************************************
      * DCLGEN TABLE(PROD.CUSTOMER)                                  *
      *        LIBRARY(PROD.CUST.DCLGEN(DCLCUST))                    *
      *        LANGUAGE(COBOL) QUOTE                                 *
      ****************************************************************
           EXEC SQL DECLARE PROD.CUSTOMER TABLE
           ( CUST_ID                        CHAR(8) NOT NULL,
             CUST_NAME                      VARCHAR(30) NOT NULL,
             CUST_BAL                       DECIMAL(11, 2),
             CUST_UPD_DATE                  DATE
           ) END-EXEC.
      ****************************************************************
      * COBOL DECLARATION FOR TABLE PROD.CUSTOMER                    *
      ****************************************************************
       01  DCLCUSTOMER.
           10  CUST-ID                PIC X(8).
           10  CUST-NAME.
               49  CUST-NAME-LEN          PIC S9(4) USAGE COMP.
               49  CUST-NAME-TEXT         PIC X(30).
           10  CUST-BAL               PIC S9(9)V9(2) USAGE COMP-3.
           10  CUST-UPD-DATE          PIC X(10).
      ****************************************************************
      * THE NUMBER OF COLUMNS DESCRIBED BY THIS DECLARATION IS 4     *
      ****************************************************************
