"""
MITIGATION SUGGESTIONS FOR EVERY NON-GREEN READING, COMPOSED ONCE AND REPLAYED FOR EVER.

THIS IS A DELIBERATE CHANGE TO WHAT THE PLATFORM DOES, DECIDED BY THE OWNER (Run 140).
Until now the Suggested Decision card stated a FINDING and asked a QUESTION and never suggested
a response. From this run the card also suggests how to move each non-Green reading ONE BAND UP
-- Red toward Amber, Amber toward Yellow, Yellow toward Green. Nothing else about the card
changes: no band, threshold, weight or posture rule moves, and nothing on this path writes a
figure into a reading.

=================================================================================================
WHAT THE MODEL IS GIVEN, AND WHAT IT IS NOT ALLOWED TO DO
=================================================================================================

The model receives a context BUILT ENTIRELY IN CODE from the STORED MODULE ROW:

  1. the module's own evidence sentence, VERBATIM;
  2. its current band, the next band up, that boundary as the row itself stored it, and the gap
     -- all composed here, before the call, and handed over AS GIVEN FACTS. The model does not
     compute any of them;
  3. the module's own basis, threshold source and provenance, for grounding;
  4. a fixed instruction stating the hard limits.

The model's output is CANDIDATE MITIGATIONS ONLY -- the "how to move one band up" prose. The
reading line, the boundary line and the gap line on the card are composed HERE, in code, so
every figure the card shows remains traceable to the constant that decided it.

NO NUMBER IS COPIED OUT OF `simulation/`. This module performs ZERO reads into the simulation
package. `models.banded` refuses to store a band without its boundary sentence, its basis and
its threshold source, so the deciding constant is already ON THE ROW, in the words the module
itself chose. Reading it back from there is stricter than importing a private literal: a
boundary that moved upstream moves here with no edit, and a boundary that was never recorded
cannot be invented here because there is nothing to read.

=================================================================================================
DETERMINISM, WHICH MATTERS MORE THAN THE FEATURE
=================================================================================================

The platform's own determinism argument is recorded in `recognition.py:44-64` and this module
follows it exactly: a model call is NOT a deterministic function, so THE PLATFORM DOES NOT ASK
TWICE. One composition per module-reading, stored in `module_mitigations`, replayed byte-
identical on every later view, export and print. NO MODEL CALL HAPPENS AT RENDER TIME.

`temperature` IS NEVER PASSED. The clients attach it only when a caller asks for it, and
determinism here comes from recording the result, not from narrowing a distribution.

THE KEY IS A CONTENT FINGERPRINT, NOT A FOREIGN KEY, AND THAT IS FORCED BY THE TWO SOURCE
LAYERS. `documents._result_view` merges per category through `spec_projection.merge_python_row`:
a category the specification layer answered is served from `specification_readings`, one it did
not is served from `computed_results`. There is therefore NO single reading id to key on. The
fingerprint covers everything that could change what a mitigation should say -- the band, the
evidence sentence, the boundary, the basis, the threshold source, the provenance classes, every
override flag and every worst-of component -- plus the template version, the provider and the
model. Change any of them and the fingerprint changes, a fresh composition is stored, and the
old row REMAINS (superseded, never overwritten). Change none and no call is made at all.

THE v70 REASSEMBLY, WHEN IT RUNS, WILL MOVE SOME BANDS AND SOME FIGURES. Every affected
reading's fingerprint changes with them, so the reassembly run WILL recompose those mitigations
and supersede the old rows. That is the intended trigger, and it is the only one.

=================================================================================================
WHAT A SUGGESTION MUST NEVER CONTAIN -- ENFORCED, NOT REQUESTED
=================================================================================================

The old stance's refusals are kept, deliberately, because this card feeds an audit record. They
are stated in the instruction AND enforced by `validate` on every composition, and a failed
validation stores THE ABSENCE LINE, never the failed text:

  * no person, role, team or authority named;
  * no deadline or date;
  * no figure that does not appear in the supplied context;
  * no reference to another module's evidence;
  * two to four candidates, each ONE sentence.

=================================================================================================
UNBANDED AND ABSTAINING MODULES GET NOTHING, AND THAT IS NOT AN OMISSION
=================================================================================================

A module that asserted no band -- Safety_Performance below its exposure floor, or any module
that abstained on missing input -- has NO BAND TO IMPROVE. It gets no context, no call and no
block. The existing limitation text already says why it is unbanded. AN ABSTENTION IS NOT
CONVERTED INTO AN IMPLIED DEFICIENCY.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any, Mapping, Sequence

from . import ai_provider

#: Bumped whenever the instruction, the context shape or the validator changes. It is inside the
#: fingerprint, so bumping it recomposes every reading rather than replaying prose composed
#: against a different set of rules.
TEMPLATE_VERSION = "mitigation-2026-09-05"

#: The fixed absence line. One string, used by storage, by the served shape and by the card.
ABSENCE_LINE = "no mitigation composed for this reading"

MAX_TOKENS = 900
REQUEST_TIMEOUT_S = 90.0

#: The five shapes a non-Green reading can take. `shape` on the served entry is one of these.
SHAPES = ("threshold", "override", "worst_of", "ordinal", "derived")

#: The ladder, most adverse first. Bands are compared CASE-INSENSITIVELY and normalised through
#: `norm_band`, because A1.2 (CUSUM) returns LOWERCASE band strings and any `== "Red"` test
#: silently drops it.
LADDER = ("Red", "Amber", "Yellow", "Green")

#: The two modules whose band is derived from other modules' bands rather than from a figure of
#: their own. They have no ladder of their own to climb; the gap is stated in their own terms.
DERIVED_MODULES = frozenset({"B1.1", "B1.2"})

#: Every stored flag that means "this band was not set by distance to a threshold". THE
#: OVERRIDES ARE THE MAJORITY, NOT THE EXCEPTION -- 17 of the 30 modules carry a hard override or
#: a floor arm -- so all of them are consulted on EVERY module, not on a hand-picked three.
OVERRIDE_FLAGS = (
    "band_hard_override_fired",
    "band_override_fired",
    "band_exhaustion_arm_fired",
    "substantial_completion_floor_fired",
)

#: Where a fired override records what it was and what clears it, in the module's own words.
OVERRIDE_WORD_KEYS = (
    "band_override_words", "band_governing_rules", "band_override_conditions",
    "band_rules", "band_hard_override_words",
)

_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_MODULE_ID = re.compile(r"\b([A-C]\d{1,2}\.\d{1,2})\b")


# ----------------------------------------------------------------- bands, shapes, numbers

def norm_band(value: Any) -> str | None:
    """`"red"`, `"RED"` and `"Red"` are one band. A1.2 returns the first of those."""
    text = str(value or "").strip()
    if not text:
        return None
    for band in LADDER:
        if text.lower() == band.lower():
            return band
    return None


def numbers_in(text: str) -> set[str]:
    """Every number in a string, normalised so `1,200` and `1200` are the same figure."""
    return {m.group(0).replace(",", "").rstrip(".") for m in _NUM.finditer(str(text or ""))}


def classify_shape(mod: Mapping[str, Any]) -> str:
    """
    Which KIND of reading this is, established from the module's OWN STORED FLAGS.

    THIS IS NOT A LOOKUP TABLE OF MODULE IDS, deliberately: a module that gains or loses an
    override arm upstream classifies correctly here with no edit, and a module the author of
    this file never saw is classified by what it recorded rather than by whether it was listed.
    The one id-based arm is the derived pair, whose band comes from OTHER modules' bands and so
    records no flag of its own to read.
    """
    mid = str(mod.get("module_id") or "")
    if mid in DERIVED_MODULES:
        return "derived"
    if any(mod.get(flag) for flag in OVERRIDE_FLAGS):
        return "override"
    if mod.get("band_components"):
        return "worst_of"
    if _boundary_figure(mod, _next_band_up(mod)) is None:
        # No continuous edge was recorded for the band above this one, so there is no distance to
        # state. A6.4 (CPARS adjectival ratings), A4.8 (reported ratings and PM disposition) and
        # A4.7's second route are here: their ladders are ORDINAL, and inventing a numeric gap
        # for them would be exactly the invented figure the validator refuses in the output.
        return "ordinal"
    return "threshold"


# ----------------------------------------------------------------- the boundary, read back

def _boundary_text(mod: Mapping[str, Any]) -> str:
    """Everything the row recorded ABOUT its boundary, in the module's own words."""
    parts = [str(mod.get(k) or "") for k in
             ("band_boundary", "band_basis", "boundary", "basis")]
    return " ".join(p for p in parts if p)


def _bands_named(mod: Mapping[str, Any]) -> list[str]:
    """
    Which rungs this module's own boundary sentence actually names.

    "ONE BAND UP" IS NOT ALWAYS THE NEXT ROW OF A FOUR-RUNG LADDER, and assuming it is produces
    a boundary the module never had. A6.1's project-target path is GREEN/RED ONLY, so Red's next
    band up is GREEN. A1.2 (CUSUM) has NO YELLOW RUNG. A6.2's near-miss Amber has no ladder at
    all. None of them is hard-coded here: the rungs are read out of the module's own recorded
    boundary, so a ladder that changes upstream is followed rather than restated.
    """
    text = _boundary_text(mod)
    named = []
    for b in LADDER:
        if not re.search(rf"\b{b}\b", text, re.I):
            continue
        # A LADDER THAT SAYS A RUNG IS ABSENT MUST NOT BE READ AS NAMING IT. A1.2's boundary
        # sentence ends "there is no Yellow rung on this ladder", and a plain word-scan would
        # take that as a Yellow rung and send the reading toward a boundary that does not
        # exist. A rung named ONLY inside a negation is not a rung.
        if re.search(rf"\bno\b(?:\s+\w+){{0,2}}\s+{b}\b", text, re.I) and not re.search(
                rf"{b}\s+(?:at|when|on|above|below|>|<)", text, re.I):
            continue
        named.append(b)
    return named or list(LADDER)


def _next_band_up(mod: Mapping[str, Any]) -> str | None:
    band = norm_band(mod.get("status_color"))
    if band is None or band == "Green":
        return None
    named = _bands_named(mod)
    for candidate in LADDER[LADDER.index(band) + 1:]:
        if candidate in named:
            return candidate
    return None


def _boundary_figure(mod: Mapping[str, Any], next_band: str | None) -> str | None:
    """
    The figure the boundary sentence attaches to the band above, or None when it attaches none.

    Read out of the sentence the module itself stored. NOTHING IS COMPUTED and nothing is
    imported from `simulation/`; a sentence that states its rung in words rather than in a
    number yields None, and the caller states the gap in words.

    RUN 150, FINDING B1. THIS READ WAS SILENTLY WRONG ON THE CODEBASE'S DOMINANT SENTENCE FORM,
    AND EVERY RUN 140 FIXTURE HAPPENED TO USE THE OTHER ONE.

    Two forms are in service and both are real emissions of real modules:

        NAME FIRST   "Green at or above 0.90; Yellow at or above 0.75; Amber at or above 0.60"
        NAME LAST    "at or above 0.95 is Green; at or above 0.9 and below 0.95 is Yellow"

    The old rule was "nearest number AFTER the band's name". On the name-first form that is
    right. On the name-last form the band's own figure sits BEFORE its name, so the nearest
    number after it is the NEXT clause's figure -- the rung below. A6.1, banded Amber at 0.85,
    reported "the Yellow boundary is at 0.8": the Amber floor, a figure the reading was already
    above, presented to a reviewer as the edge they had to reach. The name-last form is the
    majority form here -- it appears in eight modules under `simulation/` against 26 uses of the
    name-first form -- so this was not an edge case, and 342 passing checks did not see it
    because every stored fixture row was written in the name-first form.

    THE RULE NOW IS CLAUSE-SCOPED AND ENTRY-PHRASE-ANCHORED, which is correct on both forms and
    reads no further than the clause that names the band:

      1. the clause is the `;`-delimited fragment that names the band, so a figure can never be
         borrowed from the rung below or the rung above;
      2. within it, the figure is the one following the INCLUSIVE ENTRY phrase -- "at or above",
         "at or below" -- because that is the edge a reading must reach to enter the band;
      3. with no entry phrase in the clause ("Red below 0.60"), the clause's first figure;
      4. with no figure in the clause at all, the next clause naming the band is tried, and
         failing that None -- which is how an ordinal ladder still yields no invented number.
    """
    if not next_band:
        return None
    text = _boundary_text(mod)
    if not text:
        return None
    # Clause spans, so a band name can be located and then read ONLY within its own clause.
    spans: list[tuple[int, int]] = []
    start = 0
    for sep in re.finditer(r";", text):
        spans.append((start, sep.start()))
        start = sep.end()
    spans.append((start, len(text)))

    for lo, hi in spans:
        clause = text[lo:hi]
        if not re.search(rf"\b{next_band}\b", clause, re.I):
            continue
        entry = re.search(r"\bat or (?:above|below)\b", clause, re.I)
        num = _NUM.search(clause, entry.end()) if entry else _NUM.search(clause)
        if num:
            return num.group(0).replace(",", "").rstrip(".")
    return None


def _reading_figure(mod: Mapping[str, Any]) -> str | None:
    """
    The module's OWN reading value, at the precision the row stored it at.

    Run 135 stored several raw quantities at full precision for exactly this purpose. Any
    `band_*` numeric field is that module's own recorded figure; where none exists the first
    number in the module's own evidence sentence is used, which is still the module's figure and
    still not computed here.
    """
    for key in sorted(mod):
        if not key.startswith("band_"):
            continue
        val = mod.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        return repr(float(val)) if isinstance(val, float) else str(val)
    found = _NUM.search(str(mod.get("evidence_metric") or ""))
    return found.group(0).replace(",", "").rstrip(".") if found else None


def _override_clears(mod: Mapping[str, Any]) -> str | None:
    """What fired, and what clears it, taken from the module's own override logic."""
    said: list[str] = []
    for key in OVERRIDE_WORD_KEYS:
        val = mod.get(key)
        if not val:
            continue
        if isinstance(val, str):
            said.append(val.strip())
        elif isinstance(val, (list, tuple)):
            said.extend(str(v) for v in val if v)
        elif isinstance(val, Mapping):
            said.append(json.dumps(val, sort_keys=True, default=str))
    fired = [f for f in OVERRIDE_FLAGS if mod.get(f)]
    if fired:
        said.insert(0, "the arm that fired: " + ", ".join(fired))
    return "; ".join(dict.fromkeys(s for s in said if s)) or None


# ----------------------------------------------------------------- the code-built context

def build_context(mod: Mapping[str, Any]) -> dict[str, Any] | None:
    """
    Everything the model is handed for one reading, composed HERE and never by the model.

    Returns None for a reading with no band to improve -- an unbanded module, an abstention, or
    a Green. THE CALLER MAKES NO CALL ON A None, which is how "an unbanded module triggers no
    model call" is enforced rather than merely intended.
    """
    band = norm_band(mod.get("status_color"))
    if band is None or band == "Green":
        return None
    if mod.get("band_asserted") is False or mod.get("band_withheld_reason"):
        return None
    # ------------------------------------------------- RUN 143, PART 2. A CARRIED READING GETS
    # NO MITIGATION. RUN 144 RULING 2: THE OWNER RULED, AND THE RULING IS NO CHANGE. Replaying
    # an earlier period's mitigation verbatim against a reading nobody produced this period
    # would present stale advice as current. The exclusion below is unedited; what Run 144 added
    # is `tools/test_run144_ruling2.py`, which proves it by COUNTING PROVIDER CALLS at the
    # `caller=` boundary rather than inferring no call from a None return -- including for the
    # A6 measures that only began carrying under ruling 1.
    #
    # TWO REASONS, AND EITHER ALONE IS ENOUGH.
    #
    # THE FINGERPRINT WOULD REPLAY THE WRONG ANSWER. `reading_fingerprint` covers the module,
    # the band, the evidence sentence, the boundary, the basis and the flags -- and NOT the
    # period and NOT any carrying marker. A carried reading reproduces the earlier period's
    # figures exactly, so it hashes to the earlier period's fingerprint and REPLAYS that
    # period's stored mitigation verbatim, with nothing anywhere saying the finding it
    # addresses is stale. A reviewer would read a fresh-looking suggestion about a reading no
    # document of this period produced.
    #
    # AND THE HONEST ACTION IS NOT A BAND-MOVEMENT SUGGESTION. What a reviewer should do about
    # an adverse reading carried from two periods back is upload this period's evidence for it.
    # This composer's entire contract is to suggest what would move a band toward the next rung
    # on the module's own ladder; "obtain the missing document" is not that, and dressing it as
    # that would be the composer answering a question it was not asked.
    #
    # THE CARD IS NOT LEFT SILENT. The carried chip states the period, the source period's own
    # evidence sentence and this period's reason for producing nothing -- which is a more
    # precise instruction than any mitigation would be. Widening the fingerprint to include the
    # period would compose a NEW suggestion per period for an unchanged reading, which is a
    # provider call and a stored row for a finding that did not move; that is the alternative,
    # and the owner considered it and did not take it.
    if mod.get("carried") is True:
        return None
    mid = str(mod.get("module_id") or "")
    shape = classify_shape(mod)
    next_band = _next_band_up(mod)

    reading = str(mod.get("evidence_metric") or "").strip()
    boundary_sentence = str(mod.get("band_boundary") or "").strip()

    if next_band:
        next_line = (f"The next band up is {next_band}. The boundary this reading was measured "
                     f"against, as the module recorded it: {boundary_sentence}")
    else:
        next_line = ("This module's own ladder records no band above the one it is in; the "
                     "boundary it was measured against, as the module recorded it: "
                     + boundary_sentence)

    edge = _boundary_figure(mod, next_band)
    here = _reading_figure(mod)
    gap_line: str
    if shape == "override":
        clears = _override_clears(mod)
        gap_line = (
            "This band was not set by a distance to a threshold. An override arm fired, and it "
            "governs regardless of the ratio. What fired and what clears it, from the module's "
            "own logic: " + (clears or "recorded on the reading without further words")
            + ". There is no threshold gap to close; the band moves when the fired condition is "
              "cleared.")
    elif edge is not None and here is not None:
        try:
            gap_line = (
                f"The reading stands at {here}; the {next_band} boundary is at {edge}; the gap "
                f"is {abs(float(here) - float(edge))!r}, at the precision the row stores.")
        except (TypeError, ValueError):
            gap_line = (f"The reading stands at {here} and the {next_band} boundary at {edge}, "
                        f"as the module recorded them.")
    else:
        gap_line = (
            "No continuous gap is defined for this reading: its ladder is stated in the "
            "module's own terms rather than as a numeric edge, so the distance to the band "
            "above is not a number and none is stated here.")

    context: dict[str, Any] = {
        "module_id": mid,
        "band": band,
        "shape": shape,
        "next_band": next_band,
        "reading": reading,
        "next_band_line": next_line,
        "gap_line": gap_line,
        "basis": str(mod.get("band_basis") or "").strip() or None,
        "boundary": boundary_sentence or None,
        "threshold_source": mod.get("threshold_source_words") or mod.get("threshold_source"),
        "provenance": mod.get("band_provenance_words") or mod.get("band_provenance_class"),
        "specification_section": mod.get("method_class"),
    }
    if shape == "worst_of":
        context["components"] = [
            {"component": c.get("component"), "value": c.get("value"), "band": c.get("band"),
             "boundary": c.get("boundary")}
            for c in (mod.get("band_components") or []) if isinstance(c, Mapping)]
        context["aggregation"] = mod.get("band_aggregation_words")
    if shape == "override":
        context["override"] = _override_clears(mod)
    return context


def context_numbers(context: Mapping[str, Any]) -> set[str]:
    """Every figure handed in. A number in the output that is not in here is INVENTED."""
    return numbers_in(json.dumps(context, sort_keys=True, default=str))


# ----------------------------------------------------------------- the instruction

INSTRUCTION = """\
You are composing candidate MITIGATIONS for one project-controls reading on an audit record.

Everything below is GIVEN. You do not compute, revise, restate or question any figure, band,
boundary or gap; they were composed in code from the stored reading and they are already on the
card. Your entire output is the prose that suggests HOW THIS READING COULD MOVE ONE BAND UP.

Write TWO to FOUR candidates. Each candidate is exactly ONE sentence, on its own line, with no
bullet, number or label. Write nothing else at all -- no preamble, no heading, no closing line.

HARD LIMITS. Each one is checked mechanically and a single breach discards your whole output:
1. Name NO person, NO role, NO team and NO authority. Write "re-baseline the draws", never "the
   PM should re-baseline the draws" and never "escalate to the owner".
2. State NO deadline and NO date, and no month, quarter or year.
3. Use NO figure that does not appear above. Every number you write must be one handed to you.
   If you are unsure a number was given, write the sentence without it.
4. Refer to NO other module and to no other module's evidence. Address only this reading.
5. Each sentence is declarative and about the work, not about who does it.
"""


def build_prompt(context: Mapping[str, Any]) -> list[dict]:
    """The blocks handed to the client. Deterministic in the context: same context, same bytes."""
    facts = json.dumps(context, sort_keys=True, indent=2, default=str)
    return [{"type": "text",
             "text": (f"{INSTRUCTION}\n\nTHE READING, AS GIVEN:\n{facts}\n\n"
                      f"Candidates, one sentence per line:")}]


def prompt_sha256(blocks: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(list(blocks), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def reading_fingerprint(mod: Mapping[str, Any], context: Mapping[str, Any], *,
                        provider: str, model: str) -> str:
    """
    THE RECOMPOSITION TRIGGER, AND IT IS A CONTENT FINGERPRINT BECAUSE THERE IS NO READING ID.

    Covered: the module, the band, its evidence sentence, its boundary, its basis, its threshold
    source, both provenance classes, every override flag, every worst-of component, the whole
    code-built context, the template version, the provider and the model. A new period that
    computes the same figures replays; a reassembly that moves the band, or a change to any
    figure under it, changes this string and forces a fresh composition with the old row kept.
    """
    payload = {
        "module_id": mod.get("module_id"),
        "status_color": norm_band(mod.get("status_color")),
        "evidence_metric": mod.get("evidence_metric"),
        "band_boundary": mod.get("band_boundary"),
        "band_basis": mod.get("band_basis"),
        "band_basis_id": mod.get("band_basis_id"),
        "threshold_source": mod.get("threshold_source"),
        "band_provenance_class": mod.get("band_provenance_class"),
        "band_boundary_provenance_class": mod.get("band_boundary_provenance_class"),
        "flags": {f: bool(mod.get(f)) for f in OVERRIDE_FLAGS},
        "override_words": _override_clears(mod),
        "components": mod.get("band_components"),
        "context": context,
        "template_version": TEMPLATE_VERSION,
        "provider": provider,
        "model": model,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# ----------------------------------------------------------------- the validator

#: Words that name a person, a role, a team or an authority. A suggestion carrying any of them is
#: prescribing WHO ACTS, which this card has never done and does not begin doing now.
_ROLE_WORDS = (
    "pm", "project manager", "manager", "owner", "sponsor", "director", "officer", "engineer",
    "superintendent", "foreman", "supervisor", "lead", "chief", "executive", "board",
    "committee", "steering", "team", "crew", "staff", "personnel", "contractor",
    "subcontractor", "vendor", "supplier", "architect", "consultant", "auditor", "inspector",
    "analyst", "planner", "scheduler", "estimator", "controller", "administrator", "authority",
    "stakeholder", "sponsorship", "management", "leadership", "escalate", "escalation",
    "delegate", "assign", "assigned", "approver", "he", "she", "they", "someone", "somebody",
    "whoever", "accountable",
)

#: Anything that fixes a suggestion to a moment in time.
_DATE_WORDS = (
    "deadline", "due date", "by end of", "no later than", "within the week", "next week",
    "this week", "next month", "this month", "next quarter", "this quarter", "asap",
    "target date", "cutoff date", "milestone date",
)
_MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
           "september", "october", "november", "december",
           "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_DATE_PATTERNS = (
    re.compile(r"\b(?:19|20)\d{2}\b"),                       # a year
    re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b"),   # 3/14 or 3-14-2026
    re.compile(r"\bq[1-4]\b", re.I),                         # a quarter
)


def _sentence_count(line: str) -> int:
    return len([p for p in re.split(r"[.!?](?:\s|$)", line.strip()) if p.strip()])


def validate(candidates: Sequence[str], context: Mapping[str, Any]) -> list[str]:
    """
    The five rules, checked mechanically. Returns the refusals; EMPTY MEANS ACCEPTED.

    A NON-EMPTY RETURN MEANS THE TEXT IS NOT STORED AND NOT RENDERED. The absence line is stored
    in its place. There is no partial acceptance, no editing of the model's words to make them
    pass, and no retry: an output that broke a rule is discarded whole, because keeping the
    sentences that happened to pass would put the model in the position of choosing which of the
    owner's refusals apply.
    """
    refusals: list[str] = []
    lines = [str(c).strip() for c in candidates if str(c).strip()]

    # RULE 5 -- length.
    if not 2 <= len(lines) <= 4:
        refusals.append(f"length: {len(lines)} candidates offered, two to four are allowed")
    for line in lines:
        if _sentence_count(line) > 1:
            refusals.append(f"length: more than one sentence in {line[:60]!r}")
            break
        if len(line) > 320:
            refusals.append(f"length: {len(line)} characters in one candidate, over 320")
            break

    allowed = context_numbers(context)
    this_module = str(context.get("module_id") or "")
    blob = " ".join(lines)
    low = blob.lower()

    # RULE 1 -- no person, role, team or authority.
    named = sorted({w for w in _ROLE_WORDS
                    if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", low)})
    if named:
        refusals.append("named a person, role, team or authority: " + ", ".join(named))

    # RULE 2 -- no deadline or date.
    dated = {w for w in _DATE_WORDS + _MONTHS
             if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", low)}
    dated |= {m.group(0) for p in _DATE_PATTERNS for m in p.finditer(blob)}
    if dated:
        refusals.append("stated a deadline or a date: " + ", ".join(sorted(dated)))

    # RULE 3 -- no invented figure.
    invented = sorted(numbers_in(blob) - allowed)
    if invented:
        refusals.append("used a figure that was not supplied: " + ", ".join(invented))

    # RULE 4 -- no other module's evidence.
    others = sorted({m.group(1) for m in _MODULE_ID.finditer(blob)} - {this_module})
    if others:
        refusals.append("referred to another module: " + ", ".join(others))

    return refusals


def parse_candidates(text: str) -> list[str]:
    """One candidate per line. Bullets and numbering are stripped; nothing else is edited."""
    out: list[str] = []
    for raw in str(text or "").splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", raw).strip()
        if line:
            out.append(line)
    return out


# ----------------------------------------------------------------- storage, append-only

class MitigationStore:
    """
    `module_mitigations`, append-only. Nothing here is UPDATEd except to set `superseded_by`.

    The precedent is `recognition_matches` and the reasons are the same: an answer is recorded
    with the fingerprint of the question that produced it, and a question already answered under
    that fingerprint is REPLAYED WITH NO CALL MADE AT ALL.
    """

    def __init__(self, session, project_id) -> None:
        self._session = session
        self._project_id = project_id

    def get(self, period: int, module_id: str, fingerprint: str) -> dict | None:
        from sqlalchemy import select

        from .research_models import ModuleMitigation
        row = self._session.execute(
            select(ModuleMitigation).where(
                ModuleMitigation.project_id == self._project_id,
                ModuleMitigation.period == period,
                ModuleMitigation.module_id == module_id,
                ModuleMitigation.reading_fingerprint == fingerprint,
                ModuleMitigation.superseded_by.is_(None))).scalars().first()
        if row is None:
            return None
        return {"mitigations": row.mitigations, "provider": row.provider, "model": row.model,
                "created_at": row.created_at, "shape": row.shape, "band": row.band}

    def put(self, period: int, module_id: str, fingerprint: str, *, band: str, shape: str,
            context: Mapping[str, Any], provider: str, model: str, prompt_hash: str,
            mitigations: Any) -> str:
        from .research_models import ModuleMitigation
        row = ModuleMitigation(
            project_id=self._project_id, period=period, module_id=module_id,
            reading_fingerprint=fingerprint, band=band, shape=shape, context=dict(context),
            provider=provider, model=model, prompt_sha256=prompt_hash,
            template_version=TEMPLATE_VERSION, mitigations=mitigations)
        self._session.add(row)
        self._session.flush()
        self.supersede(period, module_id, fingerprint, row.mitigation_id)
        return row.mitigation_id

    def supersede(self, period: int, module_id: str, keep_fingerprint: str,
                  by_mitigation_id: str) -> None:
        """
        The ONE permitted UPDATE, and it adds a pointer rather than changing an answer.

        Every earlier live row for this module-period whose fingerprint is NOT the one just
        stored is marked superseded BY that row. THE OLD TEXT STAYS EXACTLY AS COMPOSED, so
        "why did this change?" is answerable from the table alone. This is what makes the
        recomposition rule -- replay unless the reading changed, then supersede and compose
        afresh -- visible in the store rather than merely asserted in a docstring.
        """
        from sqlalchemy import select

        from .research_models import ModuleMitigation
        rows = self._session.execute(
            select(ModuleMitigation).where(
                ModuleMitigation.project_id == self._project_id,
                ModuleMitigation.period == period,
                ModuleMitigation.module_id == module_id,
                ModuleMitigation.reading_fingerprint != keep_fingerprint,
                ModuleMitigation.superseded_by.is_(None))).scalars().all()
        for row in rows:
            row.superseded_by = by_mitigation_id


class NullStore:
    """No table and no persistence, for a caller with no session. It never replays and never
    stores, so a caller holding one composes at most once per process and never at all in
    production, where a session is always supplied."""

    def get(self, period, module_id, fingerprint):  # noqa: D102
        return None

    def put(self, *a, **k):  # noqa: D102
        return None

    def supersede(self, *a, **k):  # noqa: D102
        return None


# ----------------------------------------------------------------- the composition

def ask_provider(blocks: list[dict], cfg: "ai_provider.ProviderConfig",
                 environ: dict[str, str] | None = None) -> str:
    """
    The only place a model is called for this role. NO `temperature` IS PASSED, EVER.

    `ai_provider.load_provider("mitigation")` resolves the owner's setting. There is no fallback,
    no retry against another name and no second provider: Groq is not a fallback for this role
    unless the owner sets the environment variable that routes it there.
    """
    client = ai_provider.build_client(cfg, timeout_s=REQUEST_TIMEOUT_S, environ=environ)
    return client.complete(blocks, max_tokens=MAX_TOKENS)


def compose_one(mod: Mapping[str, Any], *, store, period: int, cfg, environ=None,
                caller=ask_provider) -> dict[str, Any] | None:
    """
    One reading: replay if it is stored, otherwise compose once, validate, and store the result.

    RETURNS None WHEN THE READING HAS NO BAND TO IMPROVE, and in that case NO CALL IS MADE and
    the caller renders no block for it.

    EVERY FAILURE PATH STORES THE ABSENCE LINE. A key that is absent, a provider that errors, an
    output that is truncated, an output the validator refuses -- all of them store
    `[ABSENCE_LINE]`, which then REPLAYS like any other answer. A MISSING MITIGATION IS NEVER
    SILENTLY RETRIED AT RENDER: that is the whole point of storing the absence rather than
    leaving a hole the next render would try to fill with a second call.
    """
    context = build_context(mod)
    if context is None:
        return None
    mid = str(mod.get("module_id") or "")
    fingerprint = reading_fingerprint(mod, context, provider=cfg.provider, model=cfg.model)

    stored = store.get(period, mid, fingerprint)
    if stored is not None:
        return _served(context, stored["mitigations"], provider=stored["provider"],
                       model=stored["model"], created=stored.get("created_at"))

    blocks = build_prompt(context)
    prompt_hash = prompt_sha256(blocks)
    refusals: list[str] = []
    try:
        text = caller(blocks, cfg, environ)
        candidates = parse_candidates(text)
        refusals = validate(candidates, context)
        payload: Any = candidates if not refusals else [ABSENCE_LINE]
    except Exception as exc:                              # noqa: BLE001 -- every failure stores
        refusals = [f"{type(exc).__name__}: {exc}"]
        payload = [ABSENCE_LINE]

    store.put(period, mid, fingerprint, band=context["band"], shape=context["shape"],
              context=context, provider=cfg.provider, model=cfg.model,
              prompt_hash=prompt_hash, mitigations=payload)
    return _served(context, payload, provider=cfg.provider, model=cfg.model)


def _served(context: Mapping[str, Any], payload: Any, *, provider: str, model: str,
            created=None) -> dict[str, Any]:
    """The served shape. The reading, boundary and gap lines here were composed IN CODE."""
    items = [str(c) for c in (payload or []) if str(c).strip()]
    absent = (not items) or items == [ABSENCE_LINE]
    when = created.date().isoformat() if hasattr(created, "date") else (
        created if isinstance(created, str) else date.today().isoformat())
    return {
        "module_id": context["module_id"],
        "band": context["band"],
        "shape": context["shape"],
        "reading": context["reading"],
        "next_band": context["next_band_line"],
        "gap": context["gap_line"],
        "candidates": [] if absent else items,
        "absent_reason": ABSENCE_LINE if absent else None,
        "composed_at": when,
        "model": model,
        "provider": provider,
    }


def mitigations_for_card(session, project_id, period: int,
                         adverse_rows: Sequence[Mapping[str, Any]],
                         modules: Sequence[Mapping[str, Any]],
                         environ: dict[str, str] | None = None,
                         caller=ask_provider) -> list[dict[str, Any]]:
    """
    The `mitigations` key, in the card's own severity order.

    `adverse_rows` is `decision_brief._adverse_readings` output -- the card's REAL population,
    already ordered red, amber, yellow, then category, then module id. Ordering is not
    recomputed here, so the mitigation list and the adverse-readings block can never disagree.
    """
    by_id = {str(m.get("module_id")): m for m in (modules or []) if m.get("module_id")}
    store = MitigationStore(session, project_id) if session is not None else NullStore()
    try:
        cfg = ai_provider.load_provider("mitigation", environ)
    except Exception:                                     # noqa: BLE001
        return []
    out: list[dict[str, Any]] = []
    for row in adverse_rows or []:
        mod = by_id.get(str(row.get("module_id")))
        if mod is None:
            continue
        entry = compose_one(mod, store=store, period=period, cfg=cfg, environ=environ,
                            caller=caller)
        if entry is not None:
            out.append(entry)
    return out
