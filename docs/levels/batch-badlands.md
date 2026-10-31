# Batch Badlands (Open World level 1)

gitgalaxy#7065, JCL execution (#4891) and utilities (#4890). App `BDLD`
(`generator/apps/bdld.py`; `estate/apps/BDLD/` is generated, never hand-edited).

| job | what it plants | horrors |
|---|---|---|
| `BDLDNITE` | SORT, `&&` temp dataset, IKJEFT01 running a Db2 program, STEPLIB concatenation, `COND=`, IF/THEN/ELSE/ENDIF | H-0064, H-0065, H-0066, H-0067, H-0068 |
| `BDLDRST` | JOB `RESTART=LOAD020`, `EXEC PARM=` | H-0069 |
| `BDLDUTIL` | IDCAMS DELETE/SET/DEFINE/REPRO, IEBGENER, ICETOOL, DFSORT INREC/OUTREC/SUM | H-0067 |
| `BDLDPRCJ` + `proclib/BDLDPRC` | cataloged procedure with symbolic parameters (`&HLQ..`, `PARM='&RPT'`) next to a real `&&` temp dataset; `JCLLIB ORDER=`; `EXEC BDLDPRC,RPT=MONTHLY` | H-0071 |
| `BDLDUT2` | IDCAMS LISTCAT / ALTER (hyphen continuation) / PRINT, IEBCOPY COPY + SELECT, DFSORT JOINKEYS x2 / REFORMAT / SORT FIELDS=COPY / OUTFIL x2 | H-0072 |
| `BDLDGDG` | GDG `(0)` read and `(+1)` written in one job, GDG concatenated with an unnamed DD | H-0066, H-0070 |

Programs `BDLDDB2` (Db2, compiled with EXEC blocks stubbed) and `BDLDRPT` (PARM through LINKAGE)
compile under `cobc -std=ibm`.

Slice 2 (gitgalaxy#7065): H-0068 now keys the `RUN PROGRAM(BDLDDB2)` call as a `call_sites` fact (verb `RUN PROGRAM`); `jcl_dds` gains `symbolic`.

Known key question, not changed: `BDLDDB2` keys the SQL `INSERT` with `access` `update`; SPEC section 3 defines no `sql_statements` access vocabulary, so which word IBM semantics call for is undecided.

Remaining slices: LISTCAT/ALTER variety beyond cards, restart with checkpoints, SYSOUT variety, proc overrides (`step.dd DD`), INCLUDE members; the other three levels (#4894, #4892, #4893).

Key additions (SPEC section 3): the `jcl_utility_cards` channel and the optional fields `parm`,
`if_cond`, `branch`, `restart` on `jcl_steps` and `temp`, `concat_of`, `dummy`, `inline_lines` on
`jcl_dds`. Every construct is cited in `horrors/H-0064.json` .. `H-0070.json`.

## First-time run

| date | engine commit | scan | translate | result |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

The first run needs gitgalaxy's scorer to read the new channel and fields (a gitgalaxy-side change,
not part of this PR).
