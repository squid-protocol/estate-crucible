"""The estate's applications. Each module defines APP (data). Phase 3 has twenty hand-written
apps; `filler` makes seeded ones for the scale dial. Add an app by adding a module here and
listing it in HAND_APPS."""

from typing import Any

from . import (acct, bill, clms, cust, deco, deut, gled, gulf, invn, kyuy, legl, loan, modn, nord, ordr, payr, pced,
               rpts, ship, taxr)

HAND_APPS: list[dict[str, Any]] = [acct.APP, cust.APP, loan.APP, bill.APP, invn.APP, payr.APP, gled.APP,
                                   modn.APP, clms.APP, nord.APP, deut.APP, kyuy.APP, gulf.APP,
                                   ordr.APP, ship.APP, taxr.APP, deco.APP, legl.APP, pced.APP, rpts.APP]
