"""
RUN 69. THE CONTRACT MODIFICATION REGISTER, READ FROM THE DOCUMENT THAT PRINTS IT.

WHAT THIS CLOSES. B3.5 Contract Modification Governance abstained on "a governed contract
modification register", and the only thing the platform ever asked a change-order document for
was `change_order_count` -- a COUNT. `canonical_v6.modification_governance` states in its own
words that there is NO COUNT in its result, that A4.6 owns change frequency, and that
"signature existence is never authority". A count answers none of the three questions the module
asks of each modification: who executed it and under what authority, whether the
unilateral/bilateral distinction is honoured, and whether the governing written instrument
exists.

A modification register prints one row per modification carrying exactly those columns. So the
register is asked for as a table, on the `baseline_curve_json` precedent, and this reader maps
its printed headings onto the fields the canonical function reads.

WHAT IS REFUSED, AND EACH REFUSAL IS THE POINT

  * AUTHORITY IS NEVER READ OFF A SIGNATURE COLUMN. `authority_evidence` and `signed_parties`
    are matched from DISJOINT heading sets, and no signature heading can reach the authority
    field. This is the module's own stated rule enforced at the reader, so a register that
    prints signatures and no warrant reaches INSUFFICIENT_EVIDENCE rather than SATISFIED.
  * A MODIFICATION TYPE IS PASSED THROUGH OR LEFT ABSENT, NEVER GUESSED. The canonical function
    reads exactly "unilateral" or "bilateral" and returns an inapplicable verdict for anything
    else. A register printing "Change Order" in that column states no bilateral/unilateral
    distinction, and none is manufactured from the presence of two signatures.
  * A ROW WITH NO MODIFICATION IDENTITY IS DROPPED. There is nothing to attribute a governance
    verdict to.
  * NO ROW ACQUIRES A FEDERAL CONTEXT IT DOES NOT STATE. Where the register does not say, the
    key is absent and `modification_governance` falls through to the structure's own value,
    which is likewise only present where the document stated it.
"""
from __future__ import annotations

import re
from typing import Any

_HEADINGS: dict[str, tuple[str, ...]] = {
    "modification_id": (
        "modification id", "modification no", "modification number", "modification",
        "mod id", "mod no", "mod number", "mod", "change order no", "change order number",
        "change order id", "change order", "co no", "reference", "id",
    ),
    "executing_official": (
        "executing official", "contracting officer", "executed by", "issued by",
        "authorised official", "authorized official", "official", "approving officer",
    ),
    # THE WARRANT, THE DELEGATION, THE AUTHORITY CITED. Never a signature column -- see above.
    "authority_evidence": (
        "authority evidence", "authority reference", "authority", "warrant",
        "warrant number", "delegation", "delegation of authority", "authority citation",
        "contracting authority",
    ),
    "modification_type": (
        "modification type", "mod type", "type of modification", "type",
        "unilateral or bilateral", "instrument type",
    ),
    "signed_parties": (
        "signed parties", "signatories", "signed by", "parties signing", "signatures",
        "parties",
    ),
    "written_instrument": (
        "written instrument", "instrument", "form", "sf30", "sf 30", "standard form 30",
        "document reference", "instrument reference",
    ),
    "issue_date": ("issue date", "date issued", "issued", "modification date", "date"),
    "effective_date": ("effective date", "date effective", "effective"),
    "sf30_applicable": ("sf30 applicable", "sf 30 applicable", "sf30 required"),
    "federal_context": ("federal", "federal context", "federal acquisition", "regime"),
}

#: Headings that name a signature and must never reach `authority_evidence`. Enforced.
_SIGNATURE_MARKERS = ("sign", "signat", "party", "parties")

_TRUE = ("yes", "true", "y", "applicable", "required", "1")
_FALSE = ("no", "false", "n", "not applicable", "n/a", "na", "not required", "0")


def _norm(heading: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(heading).lower()).split())


def _pick(row: dict, field: str) -> Any:
    normalised = {_norm(k): v for k, v in row.items()}
    forbid_signature = field == "authority_evidence"
    for candidate in _HEADINGS[field]:
        if candidate in normalised:
            return normalised[candidate]
    for candidate in _HEADINGS[field]:
        for norm_heading, value in normalised.items():
            if candidate in norm_heading:
                if forbid_signature and any(m in norm_heading for m in _SIGNATURE_MARKERS):
                    continue
                return value
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    out = str(value).strip()
    return out or None


def _boolean(value: Any) -> bool | None:
    """Yes/no as printed, or None. An unrecognised cell is NOT read as false."""
    if isinstance(value, bool):
        return value
    text = _text(value)
    if text is None:
        return None
    low = text.lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    return None


def _parties(value: Any) -> list[str] | None:
    """The signatories the register printed, as a list. `modification_governance` counts them for
    the bilateral rule, so a single printed name must remain a single name."""
    if isinstance(value, (list, tuple)):
        out = [str(v).strip() for v in value if str(v).strip()]
        return out or None
    text = _text(value)
    if text is None:
        return None
    parts = [p.strip() for p in re.split(r"[;,/&]| and ", text) if p.strip()]
    return parts or None


def read_modification_register(register: Any) -> list[dict]:
    """
    `modifications_json` (a list of row objects keyed by the register's own headings) -> rows in
    the shape `canonical_v6.modification_governance` reads. Nothing is defaulted; a field the
    register did not print is absent from the row.
    """
    if not isinstance(register, list):
        return []
    out: list[dict] = []
    for raw_row in register:
        if not isinstance(raw_row, dict):
            continue
        mod_id = _text(_pick(raw_row, "modification_id"))
        if not mod_id:
            # A TOTALS ROW OR A BLANK ROW. There is nothing to attribute a governance verdict to.
            continue
        row: dict[str, Any] = {"modification_id": mod_id}
        for field in ("executing_official", "authority_evidence", "written_instrument",
                      "issue_date", "effective_date"):
            value = _text(_pick(raw_row, field))
            if value is not None:
                row[field] = value
        mtype = _text(_pick(raw_row, "modification_type"))
        if mtype is not None:
            low = mtype.lower()
            # PASSED THROUGH ONLY WHERE THE REGISTER NAMED THE DISTINCTION THE RULE IS ABOUT.
            # Anything else is carried verbatim, which makes the type rule INAPPLICABLE rather
            # than satisfied -- the module's own handling of a value it does not recognise.
            row["modification_type"] = ("unilateral" if low == "unilateral"
                                        else "bilateral" if low == "bilateral" else mtype)
        parties = _parties(_pick(raw_row, "signed_parties"))
        if parties is not None:
            row["signed_parties"] = parties
        for field in ("sf30_applicable", "federal_context"):
            flag = _boolean(_pick(raw_row, field))
            if flag is not None:
                row[field] = flag
        out.append(row)
    return out
