"""The estate's applications. Each module defines APP (data). Phase 1 has nine hand-written
apps; `filler` makes seeded ones for the scale dial. Add an app by adding a module here and
listing it in HAND_APPS."""

from typing import Any

from . import acct, bill, clms, cust, gled, invn, loan, modn, payr

HAND_APPS: list[dict[str, Any]] = [acct.APP, cust.APP, loan.APP, bill.APP, invn.APP, payr.APP, gled.APP,
                                   modn.APP, clms.APP]
