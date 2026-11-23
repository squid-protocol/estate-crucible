# Alternate Index Archipelago (Open World level 2)

gitgalaxy#7065, VSAM organizations and access paths (#4894). App `AIXA`
(`generator/apps/aixa.py`; `estate/apps/AIXA/` is generated, never hand-edited).

| member | what it plants | horrors |
|---|---|---|
| `AIXAKSD` | KSDS with `ALTERNATE RECORD KEY ... WITH DUPLICATES`, `START ... KEY IS`, `READ NEXT`, a random `READ ... KEY IS`, file status 02 / 22 / 23 tested in one paragraph | H-0076, H-0081 |
| `AIXARRD` | `ORGANIZATION IS RELATIVE`, `RELATIVE KEY IS` a working-storage item | H-0077 |
| `AIXAESD` | `ORGANIZATION IS SEQUENTIAL` over an ESDS, `OPEN EXTEND`, read back | H-0078 |
| `AIXADEF` step `IDC010` | `DEFINE CLUSTER` INDEXED / NUMBERED / NONINDEXED | H-0082 |
| `AIXADEF` step `IDC020` | `DEFINE ALTERNATEINDEX`, `DEFINE PATH`, `BLDINDEX` | H-0079 |
| `AIXARUN` | `//ORDKSD` on the base cluster next to `//ORDKSD1` on the PATH | H-0080 |
| `AIXARRS` | two RRDS SELECTs: `ACCESS SEQUENTIAL` after `START ... KEY IS NOT LESS THAN`, and `ACCESS RANDOM` with `WRITE` / `REWRITE` / `DELETE` by relative number | H-0106 |
| `AIXAESU` | the ESDS opened `I-O`: `READ` then `REWRITE` in place, no `DELETE` | H-0107 |
| `AIXAKS2` | KSDS with two alternate keys, `CUS-TAX` unique and `CUS-NAME WITH DUPLICATES` | H-0108 |
| `AIXADF2` | `DEFINE CLUSTER` for the history RRDS (IDC010); the customer KSDS, `UNIQUEKEY` and `NONUNIQUEKEY` alternate indexes, a PATH and a `BLDINDEX` each (IDC020) | H-0106, H-0108 |
| `AIXARU2` | `//CUSKSD` on the base cluster, `//CUSKSD1` on the TAX path, `//CUSKSD2` on the NAME path | H-0108 |
| `AIXAFOP` | `SELECT OPTIONAL` KSDS, a nonoptional KSDS and a SELECT whose record key disagrees with the cluster: open-time file status 05 / 35 / 39 | H-0129 |
| `AIXAFLK` | an RRDS read sequentially with a `PIC 9(2)` relative key (file status 14), a WRITE loop past the end of the ESDS (34), `CLOSE ... WITH LOCK` then `OPEN` (38) | H-0130 |
| `AIXAKS3` | a sequential-access KSDS: `REWRITE` right after `OPEN` (file status 43), then `READ NEXT` and a `REWRITE` giving the unique alternate key `CUS-TAX` a value another record holds (22); step `KS3040` of `AIXARU2` | H-0131 |
| `AIXAMOD` | a sequential KSDS used in states that forbid the statement: `WRITE` and `REWRITE` on a file open `INPUT` (file status 48, 49), a `READ NEXT` after the at-end condition (46), `OPEN` of an open file (41), `READ` (47) and `CLOSE` (42) of a closed one; step `MD5050` of `AIXARU2` | H-0132 |
| `AIXAVAR` | a KSDS with a variable-length FD (`RECORD IS VARYING IN SIZE FROM 30 TO 50 CHARACTERS DEPENDING ON`): `WRITE` of 60 and of 10 bytes (file status 44), a `READ` of a record outside the bounds (04); step `VR6060` of `AIXARU2` | H-0134 |
| `AIXAVRW` | the ESDS opened `I-O` with a variable-length FD (`RECORD IS VARYING IN SIZE FROM 40 TO 60 CHARACTERS`): `READ` of a 60-byte record, then `REWRITE` of 50 bytes, inside the bounds but not the size being replaced (file status 44); step `VW7070` of `AIXARU2` | H-0135 |

All programs compile under `cobc -std=ibm`.

New optional fields on `file_control` (listed in SPEC section 3): `alternate_keys`
(`[{name, duplicates}]`, present only when the SELECT has an ALTERNATE RECORD KEY) and `relative_key`
(present only when the SELECT has a RELATIVE KEY); `optional` (true, present only when the SELECT says OPTIONAL). The gitgalaxy scorer does not read them yet, so they
score as unscored until it does.

Known key question, not changed: the COBOL source alone does not tell an ESDS from a QSAM data set
(H-0078); only the `NONINDEXED` card does (H-0082).

## First-time run

| date | engine commit | scan | translate | result |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

The first run needs the owner's release and pin bump, and gitgalaxy's scorer to read the new fields.

Remaining slices: 37 and 9x, a KSDS REWRITE of a different-size record (44 is H-0135 for an ESDS only) and VLR(COMPAT) (04 becomes 00) (41, 42, 46, 47, 48 and 49 are H-0132; NOUPGRADE / NOUPDATE is H-0133; 04 and 44 are H-0134); the answer-key edge 2000-COPY -> 2100-REPLACE in AIXARRS (a PERFORM inside an INVALID KEY, see handoff 4894-aixa-check-20261122); scorer support for `alternate_keys` /
`relative_key` (gitgalaxy side); RBA / RRN access (CICS `RIDFLD`, cics-crucible side); alternate-index
upgrade-set behaviour at run time (a program reading a stale NOUPGRADE index); LINEAR and ZFS clusters; an ESDS with an alternate index (not supported in COBOL).
