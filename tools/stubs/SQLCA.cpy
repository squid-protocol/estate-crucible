      * STAND-IN FOR THE DB2 SQLCA, FOR THE GNUCOBOL CHECK ONLY.
      * WRITTEN FOR THIS REPOSITORY FROM THE DOCUMENTED FIELD NAMES;
      * NOT IBM'S COPYBOOK.
       01  SQLCA.
           05  SQLCAID                PIC X(8).
           05  SQLCABC                PIC S9(9) COMP-5.
           05  SQLCODE                PIC S9(9) COMP-5.
           05  SQLERRM.
               49  SQLERRML           PIC S9(4) COMP-5.
               49  SQLERRMC           PIC X(70).
           05  SQLERRP                PIC X(8).
           05  SQLERRD                PIC S9(9) COMP-5 OCCURS 6 TIMES.
           05  SQLWARN                PIC X(11).
           05  SQLSTATE               PIC X(5).
