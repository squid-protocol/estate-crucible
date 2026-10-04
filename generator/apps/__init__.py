"""The estate's applications. Each module defines APP (data). Phase 0 has three hand-written
apps; `filler` makes seeded ones for the scale dial. Add an app by adding a module here and
listing it in HAND_APPS."""

from typing import Any

from . import acct, cust, loan

HAND_APPS: list[dict[str, Any]] = [acct.APP, cust.APP, loan.APP]
