       identification division.
       program-id.    pcedlow.
       author.       pricing team.
      *------------------------------------------------------------
      * pcedlow - round a price total. keyed in lower case.
      *------------------------------------------------------------
       data division.
       working-storage section.
       01  ws-cents               pic s9(9) comp value 0.
       01  ws-flag                pic x value 'n'.
           88  ws-rounded             value 'y'.
       linkage section.
       01  lk-total               pic s9(7)v99 comp-3.
       procedure division using lk-total.
       main-para.
           perform round-total
           if ws-rounded
              display 'pcedlow rounded'
           end-if
           goback.
       round-total.
           compute ws-cents = lk-total * 100
           compute lk-total rounded = ws-cents / 100
           set ws-rounded to true.
