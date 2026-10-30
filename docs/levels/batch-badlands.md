# Batch Badlands (Open World level 1)

gitgalaxy#7065, JCL execution (#4891) and utilities (#4890). App `BDLD`
(`generator/apps/bdld.py`; `estate/apps/BDLD/` is generated, never hand-edited).

| job | what it plants | horrors |
|---|---|---|
| `BDLDNITE` | SORT, `&&` temp dataset, IKJEFT01 running a Db2 program, STEPLIB concatenation, `COND=`, IF/THEN/ELSE/ENDIF | H-0064, H-0065, H-0066, H-0067, H-0068 |
| `BDLDRST` | JOB `RESTART=LOAD020`, `EXEC PARM=` | H-0069 |
| `BDLDUTIL` | IDCAMS DELETE/SET/DEFINE/REPRO, IEBGENER, ICETOOL, DFSORT INREC/OUTREC/SUM | H-0067 |
| `BDLDGDG` | GDG `(0)` read and `(+1)` written in one job, GDG concatenated with an unnamed DD | H-0066, H-0070 |

Programs `BDLDDB2` (Db2, compiled with EXEC blocks stubbed) and `BDLDRPT` (PARM through LINKAGE)
compile under `cobc -std=ibm`.

Key additions (SPEC section 3): the `jcl_utility_cards` channel and the optional fields `parm`,
`if_cond`, `branch`, `restart` on `jcl_steps` and `temp`, `concat_of`, `dummy`, `inline_lines` on
`jcl_dds`. Every construct is cited in `horrors/H-0064.json` .. `H-0070.json`.

## First-time run

| date | engine commit | scan | translate | result |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

The first run needs gitgalaxy's scorer to read the new channel and fields (a gitgalaxy-side change,
not part of this PR).
