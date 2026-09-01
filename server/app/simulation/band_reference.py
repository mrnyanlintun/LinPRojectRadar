"""
CONFIGURED BAND REFERENCE DATA, READ FROM A FILE, NEVER WRITTEN AS A LITERAL IN CODE.

RUN 101 SECTION 12.3 fails the run for storing the safety industry average as a literal in code.
The reason is not stylistic: that figure is REVISED ANNUALLY, and a literal carries no year, no
source and no way to tell a current figure from a stale one. So every published or conventional
reference number a band is drawn against lives in `band_reference_data.json` beside its unit, its
year and its source, and this module is the only way production reads it.

A NUMBER THAT IS NOT CONFIGURED IS NOT SUBSTITUTED. `configured_value` returns None when the
entry says `configured: false`, and the caller abstains. Nothing here supplies a default: a
default IS an invented threshold, which is the whole defect this run exists to remove.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PATH = Path(__file__).with_name("band_reference_data.json")

_CACHE: dict[str, Any] | None = None


def reference_data() -> dict[str, Any]:
    global _CACHE
    if _CACHE is None:
        with _PATH.open(encoding="utf-8") as fh:
            _CACHE = json.load(fh)
    return _CACHE


def entry(key: str) -> dict[str, Any]:
    """One configured entry, or an explicitly unconfigured one. Never raises for a known key."""
    row = reference_data().get(key)
    if not isinstance(row, dict):
        return {"configured": False, "value": None, "source": None,
                "why_absent": f"no reference entry named {key!r} is configured"}
    return row


def configured_value(key: str) -> Any:
    """The entry's value when it is configured, else None. No default is ever supplied."""
    row = entry(key)
    return row.get("value") if row.get("configured") else None


def source_of(key: str) -> str | None:
    return entry(key).get("source")
