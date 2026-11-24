# Bridge Road (MQ bridges to IMS and CICS)

gitgalaxy#7065, IBM MQ (#4892). App `MQBR` (`generator/apps/mqbr.py`; `estate/apps/MQBR/` is generated, never
hand-edited). Messages that start IMS and CICS work: the sender builds a header structure (MQIIH, MQCIH) in front of
the data, and the bridge reads it. Structures are estate-written stand-in copybooks at IBM's documented lengths.

| member | what it plants | horrors |
|---|---|---|
| `MQBRIMS` | MQPUT of MQIIH (84 bytes) + LL ZZ + transaction code + data; MQMD format for the IMS bridge | H-0114 |
| `MQBRCIH` | MQPUT of MQCIH version 2 (180 bytes) + COMMAREA, DPL link type | H-0115 |
| `MQBRMPP` | IMS transaction: GU input, ISRT reply to the IO PCB | H-0116 |
| `MQBRRUN` | JCL running the two senders with the MQ STEPLIB concatenation (no dedicated horror) | |

Not planted, on purpose (no verified quote yet): the IMS region step (DFSRRC00) and PSB, bridge queue and storage
class definitions, the program the CICS bridge links to, MQIIH transaction state and conversational use.
