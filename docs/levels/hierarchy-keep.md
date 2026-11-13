# Hierarchy Keep (Open World level 4, IMS)

gitgalaxy#7065, IBM IMS in batch (#4893). App `HKEP` (`generator/apps/hkep.py`; `estate/apps/HKEP/` is
generated, never hand-edited). Built before any IMS support lands, per Open World rule 5: the first run of
the scorer over this level is the first-time number, measured once, then it is development data.

## Slice 1 (this level doc's scope)

| horror | planted | IBM text it rests on |
|---|---|---|
| H-0096 | `HKEPDBD.asm`: DBD with SEGM KEEP, WALL (PARENT=KEEP), GATE (PARENT=WALL) | IMS 15 System utilities, DBD generation input record structure: SEGM statements in hierarchic order |
| H-0097 | `HKEPWALK.cbl` 1000-SCAN: unqualified GN through CBLTDLI, repeated until GB | IMS 15.4 APIs, GN/GHN call |
| H-0098 | `HKEPWALK.cbl` 2000-RESTART: a GN after GB | IMS 15.4 APIs, GN/GHN call |

New channels: `dli_calls`, `ims_gen` (SPEC section 3).

## Slice 2 (IMS 15.1 manual pages read; quotes in `spec/horrors.json`)

| horror | planted | IBM text it rests on |
|---|---|---|
| H-0117 | `HKEPPSB.asm`: PCB TYPE=DB, SENSEG KEEP, SENSEG WALL, PSBGEN | The database PCB statement; The SENSEG statement |
| H-0118 | `HKEPDB2.asm`: FIELD after each SEGM (KEEPKEY, WALLKEY) | FIELD statement overview; FIELD statements (NAME required for SSA fields) |
| H-0119 | `HKEPDB2.asm`: LCHILD NAME=(ENTRY,HKEPDB3) after KEEP's FIELD | LCHILD statement overview; LCHILD statements |
| H-0120 | `HKEPFIND.cbl`: GU with the qualified SSA `SSA-KEEP` | Segment search arguments (SSAs), Qualified SSAs |

Channel `ims_gen` gains FIELD, LCHILD, PCB, SENSEG and PSB kinds (SPEC section 3). New ids start at H-0117
(H-0114..H-0116 are the Bridge Road horrors; H-0111..H-0113 are on an open Warlords PR).

## Not yet planted (no IBM quote verified yet, so nothing planted)

DBD DATASET / XDFLD, PROCOPT values, SENSEG PARENT=, LCHILD POINTER= / PAIR=, command codes, multiple qualification statements, GHU / GNP / ISRT / REPL / DLET,
EXEC DLI, the `DFSRRC00` batch step and its `PARM`. Each needs its manual page read and quoted verbatim first.

## First-time run

pending (needs a tagged estate-crucible release and the gitgalaxy pin bump).
