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

All six programs compile under `cobc -std=ibm`.

New optional fields on `file_control` (listed in SPEC section 3): `alternate_keys`
(`[{name, duplicates}]`, present only when the SELECT has an ALTERNATE RECORD KEY) and `relative_key`
(present only when the SELECT has a RELATIVE KEY). The gitgalaxy scorer does not read them yet, so they
score as unscored until it does.

Known key question, not changed: the COBOL source alone does not tell an ESDS from a QSAM data set
(H-0078); only the `NONINDEXED` card does (H-0082).

## First-time run

| date | engine commit | scan | translate | result |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

The first run needs the owner's release and pin bump, and gitgalaxy's scorer to read the new fields.

Remaining slices: scorer support for `alternate_keys` /
`relative_key` (gitgalaxy side); RBA / RRN access (CICS `RIDFLD`, cics-crucible side); alternate-index
upgrade-set behaviour; LINEAR and ZFS clusters; an ESDS with an alternate index (not supported in COBOL).
