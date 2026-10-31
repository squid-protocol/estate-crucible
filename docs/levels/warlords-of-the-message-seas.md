# Warlords of the Message Seas (Open World level 3)

gitgalaxy#7065, IBM MQ in batch (#4892). App `MQSA` (`generator/apps/mqsa.py`; `estate/apps/MQSA/` is
generated, never hand-edited). Slice 1: the static-CALL MQ verbs, MQ structures as estate-written
stand-in copybooks (IBM's are never shipped), and the STEPLIB concatenation of a batch MQ step.

| member | what it plants | horrors |
|---|---|---|
| `MQSAREP` | MQCONN, MQPUT1 and MQDISC as static CALLs with long USING lists wrapped over rows | H-0086 |
| `MQSAGET` | MQGET with a GMO wait interval, looped until reason 2033 | H-0087 |
| `MQSAGET` | MQCMIT in the finish paragraph, MQBACK in the error paragraph | H-0088 |
| `MQSAINQ` | MQINQ with selector words held as data items | H-0089 |
| `MQSAGET` | `COPY MQSMD` / `MQSOD` / `MQSGMO` under 01 groups | H-0090 |
| `MQSARUN` step `PUT010` | `//STEPLIB` followed by `MQM.SCSQAUTH` and `MQM.SCSQLOAD` concatenations | H-0091 |
| `MQSACNX` | MQCONNX with a connect options structure from `COPY MQSCNO` | H-0092 |
| `MQSASET` | MQSET (opened with the set option) over one-word selector and integer blocks | H-0093 |
| `MQSAPUT` | MQOPEN / MQPUT / MQCLOSE (no dedicated horror) | |

Slice 2 adds `MQSACNX`, `MQSASET`, the stand-in copybook `MQSCNO` and `MQSARUN` steps `CNX050`, `SET060`.
All six programs compile under `cobc -std=ibm` (`make check`, `make scale-smoke` pass).

Generator change: `op_call` in `generator/cobol.py` now wraps a long `USING` list onto continuation rows
(a one-line `CALL ... USING` went past column 72 for MQOPEN and MQGET). The call_sites fact line is the CALL line.

The MQ CALLs are keyed as `call_sites` with `resolves_to` null and as `gaps` (no estate member holds the
MQ stub). The gitgalaxy scorer has no MQ-specific channel, so no new scoring fields were added.

## First-time run

| date | engine commit | scan | translate | result |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

The first run needs the owner's estate-crucible release and pin bump.

Remaining slices: MQPUT with distribution lists; RRS stubs (CSQBRSTB, CSQBSTUB link-edit);
MQ triggers; IMS and CICS-MQ bridge programs; an MQ-only back-out fixture; dynamic CALLs to MQ verbs.
