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
| `MQSADYN` | the MQI verbs called through data items: `CALL WS-V-CONN USING ...` with `VALUE 'MQCONN'` | H-0100 |
| `MQSATRG` | MQGET of the trigger message structure from an initiation queue, `COPY MQSTM` | H-0101 |
| `MQSARRS` + `MQSALNK` step `LKRRS10` | SRRCMIT / SRRBACK; IEWL link-edit with CSQBRSTB and ATRSCSS | H-0111 |
| `MQSATMC` | LINKAGE `COPY MQSTMC2` (MQTMC2 character trigger message), `PROCEDURE DIVISION USING` | H-0112 |
| `MQSABKO` + `MQSALNK` step `LKBKO20` | MQ-only MQBACK; link-edit with CSQBSTUB | H-0113 |
| `MQSAPUT` | MQOPEN / MQPUT / MQCLOSE (no dedicated horror) | |

Slice 2 adds `MQSACNX`, `MQSASET`, the stand-in copybook `MQSCNO` and `MQSARUN` steps `CNX050`, `SET060`.
All six programs compile under `cobc -std=ibm` (`make check`, `make scale-smoke` pass).

Generator change: `op_call` in `generator/cobol.py` now wraps a long `USING` list onto continuation rows
(a one-line `CALL ... USING` went past column 72 for MQOPEN and MQGET). The call_sites fact line is the CALL line.

The MQ CALLs are keyed as `call_sites` with `resolves_to` null and as `gaps` (no estate member holds the
MQ stub). The gitgalaxy scorer has no MQ-specific channel, so no new scoring fields were added.

Slice 3 adds `MQSADYN`, `MQSATRG`, the stand-in copybook `MQSTM` (the nine MQTM fields at IBM's lengths, 684 bytes)
and `MQSARUN` steps `DYN070`, `TRG080`. `CALL identifier` is keyed form `identifier` with the target taken from the
item's VALUE, as in the other apps; no generator change was needed.

Not planted, on purpose: MQPUT with a distribution list. IBM's MQPUT page marks distribution lists "Not supported on
IBM MQ for z/OS", and this is a z/OS estate, so the member would be invalid there. It stays out until an estate
targets a distributed queue manager.

## First-time run

| date | engine commit | scan | translate | result |
|---|---|---|---|---|
| pending | pending | pending | pending | pending |

The first run needs the owner's estate-crucible release and pin bump.

Slice 4 adds `MQSARRS`, `MQSATMC`, `MQSABKO`, the stand-in copybook `MQSTMC2` (ten character fields, 732 bytes),
`MQSARUN` steps `RRS090`, `TMC100`, `BKO110`, and the link-edit job `MQSALNK`. Citations are from IBM MQ 9.3
(`release` set on each horror). H-0110 is taken by the Alternate Index Archipelago slice 3 (PR #25).

Remaining slices: IMS and CICS-MQ bridge programs; the `levels.json` rows for slice 4 (gitgalaxy side, separate PR).
