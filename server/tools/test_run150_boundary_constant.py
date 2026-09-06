#!/usr/bin/env python3
"""
RUN 150, PROOF 3. THE BOUNDARY IS READ FROM THE DECIDING CONSTANT, AND BREAKING THAT READ IS
CAUGHT.

Run (from server/):

    PYTHONPATH=$(pwd) python tools/test_run150_boundary_constant.py

The order's second required part of a mitigation is "the next band's boundary, read from the same
constant the band decision reads, with the comparison stated in the ladder's own inclusivity
terms. A COPIED THRESHOLD DRIFTS." Run 140 satisfied that indirectly: the engine reads the
boundary out of the module's OWN STORED SENTENCE, which `models.banded` refuses to store without,
and which the module itself formats from the deciding constant. Nothing is copied into
`mitigation.py` and nothing is imported from `simulation/`.

WHAT RUN 140 DID NOT PROVE, AND THIS FILE DOES: that the figure the engine PULLS OUT of that
sentence is in fact the deciding constant. That is a separate claim, it is the one the order's
proof 3 asks for, and IT WAS FALSE ON THE CODEBASE'S MAJORITY SENTENCE FORM.

    RUN 150, FINDING B1. Two boundary sentence forms are in service:

        NAME FIRST   "Green at or above 0.90; Yellow at or above 0.75; ..."
        NAME LAST    "at or above 0.95 is Green; at or above 0.9 and below 0.95 is Yellow; ..."

    `_boundary_figure` took "the nearest number AFTER the band's name". On the name-last form the
    band's figure sits BEFORE its name, so the read returned the NEXT clause's figure -- the rung
    BELOW. A6.1, banded Amber at a real 0.85 through the real `_band_quality_compliance`, reported
    its Yellow boundary as 0.8. 0.8 is the AMBER floor. A reviewer would have been told the edge
    they had to reach was a figure they were already past.

    The name-last form is the MAJORITY form: eight modules under `simulation/` emit it, against
    26 uses of the name-first form. Every Run 140 fixture row happened to be written name-first,
    which is why 342 checks passed over it.

This file compares the engine's extracted figure against the constant read INDEPENDENTLY, through
`simulation.band_reference.entry` -- the single accessor production uses, the same one the module
formatting the sentence uses. Nothing under `simulation/` is modified; it is read only.

THE INJECTION THE ORDER ASKS FOR IS SECTION 5: one boundary is pointed at a stale copy of the
constant, and the comparison is shown to FAIL rather than to pass quietly. It is then restored and
shown to pass again.

No model call happens anywhere in this file. Nothing here needs an API key, and nothing is
simulated: the sentences are real emissions or are rendered from the real constants.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import mitigation
from app.simulation import band_reference, models_cat89

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("  [PASS] " if ok else "  [FAIL] ") + label)


def row_for(sentence: str, band: str, *, module_id: str, reading: float) -> dict:
    """A stored row carrying nothing but what the module itself recorded about its band."""
    return {"module_id": module_id, "status_color": band, "band_asserted": True,
            "evidence_metric": f"The reading stands at {reading}.",
            "band_boundary": sentence, "band_basis": "the owner's configured ladder",
            "band_reading_value": reading}


def same_number(a: str | None, b) -> bool:
    """Equality as NUMBERS, so 0.9 and 0.90 compare equal and a missing read never passes."""
    if a is None:
        return False
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


# =====================================================================================
print("\n1. THE REAL EMISSION. A6.1's own band function, its own sentence, its own constant.")
# =====================================================================================
# `_band_quality_compliance` is called EXACTLY as production calls it and returns the real
# (colour, boundary, basis, ...) tuple. The sentence below is not written here; it is whatever
# that function produced. The constants are read separately from the same file the function read.

CUTS = band_reference.entry("quality_first_pass_acceptance_bands")
check(CUTS.get("configured") is True,
      "the deciding constant for A6.1 is configured in `band_reference_data.json`")

# One reading per non-Green band, so every rung of the real ladder is exercised.
A61_CASES = [
    # reading, expected band, the constant naming the NEXT band up's entry edge
    (0.85, "Amber", "yellow_at_or_above"),
    (0.92, "Yellow", "green_at_or_above"),
    (0.50, "Red", "amber_at_or_above"),
]

for reading, expect_band, constant_key in A61_CASES:
    colour, boundary, basis = models_cat89._band_quality_compliance(
        {"first_pass_acceptance_rate": reading, "critical_quality_failures": []}, {})[:3]
    check(colour == expect_band,
          f"A6.1 at a real {reading} bands {expect_band} (the module said {colour!r})")
    row = row_for(boundary, colour, module_id="A6.1", reading=reading)
    next_band = mitigation._next_band_up(row)
    edge = mitigation._boundary_figure(row, next_band)
    want = CUTS[constant_key]
    check(same_number(edge, want),
          f"A6.1/{colour}: the boundary the engine reads for {next_band} is the deciding "
          f"constant `{constant_key}` = {want} (engine read {edge!r})")

    # FINDING B1, STATED AS ITS OWN ASSERTION so a regression names itself rather than
    # showing up as a number that merely looks plausible.
    below = CUTS.get("amber_at_or_above") if colour == "Amber" else None
    if below is not None:
        check(not same_number(edge, below),
              f"A6.1/{colour}: the figure read is NOT the rung BELOW ({below}) -- finding B1, "
              f"the defect the name-last sentence form produced")

    # And the whole composed gap line carries that same constant, not a reformatting of it.
    ctx = mitigation.build_context(row)
    check(ctx is not None, f"A6.1/{colour}: a context is built for a non-Green reading")
    if ctx:
        check(str(want) in ctx["gap_line"] or f"{float(want)}" in ctx["gap_line"],
              f"A6.1/{colour}: the COMPOSED gap line states the constant {want} verbatim")
        check(next_band in ctx["next_band_line"],
              f"A6.1/{colour}: the next-band line names {next_band}")
        check(boundary in ctx["next_band_line"],
              f"A6.1/{colour}: the next-band line carries the module's OWN sentence verbatim, "
              f"so the inclusivity terms are the ladder's own words")


# =====================================================================================
print("\n2. BOTH SENTENCE FORMS, over EVERY configured band set in the reference file.")
# =====================================================================================
# The forms are the two real shapes found under `simulation/`. THE NUMBERS ARE NEVER TYPED HERE:
# every figure is read from `band_reference.entry`, so a constant revised in that file changes
# what this check demands with no edit.

LADDER = ["Red", "Amber", "Yellow", "Green"]


def edges_for(key: str) -> dict[str, tuple[float, str]] | None:
    """{band: (figure, sense)} for a set that states an entry edge per rung, else None."""
    row = band_reference.entry(key)
    if not row.get("configured"):
        return None
    out: dict[str, tuple[float, str]] = {}
    for band in LADDER:
        for sense in ("at_or_above", "at_or_below"):
            val = row.get(f"{band.lower()}_{sense}")
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                out[band] = (float(val), sense.replace("_", " "))
    return out or None


SETS = [k for k, v in band_reference.reference_data().items()
        if isinstance(v, dict) and edges_for(k)]
check(len(SETS) >= 6,
      f"the reference file states an entry edge per rung for {len(SETS)} band sets, "
      f"and all of them are exercised on both forms")

form_checks = 0
form_failures: list[str] = []
for key in SETS:
    edges = edges_for(key) or {}
    named = [b for b in LADDER if b in edges]
    for i, band in enumerate(named[:-1]):
        upper = named[i + 1]
        fig, sense = edges[upper]
        # The two real forms, built from the constants and from nothing else.
        name_first = "; ".join(f"{b} {edges[b][1]} {edges[b][0]}" for b in reversed(named))
        name_last = "; ".join(f"{edges[b][1]} {edges[b][0]} is {b}" for b in reversed(named))
        for form_name, sentence in (("name-first", name_first), ("name-last", name_last)):
            row = row_for(sentence, band, module_id=key, reading=fig)
            got = mitigation._boundary_figure(row, upper)
            form_checks += 1
            if not same_number(got, fig):
                form_failures.append(f"{key} [{form_name}] {band}->{upper}: read {got!r}, "
                                     f"deciding constant is {fig}")

for failure in form_failures:
    check(False, failure)
check(not form_failures,
      f"all {form_checks} band-set/rung/form combinations read the deciding constant exactly, "
      f"on BOTH sentence forms")


# =====================================================================================
print("\n3. THE COMPARISON IS ANCHORED IN THE LADDER'S OWN INCLUSIVITY TERMS.")
# =====================================================================================
# A downward-favourable ladder ("at or below") must not be read as an upward one. Two of the
# configured sets are downward, and getting the sense wrong would state the wrong edge.
DOWNWARD = [k for k in SETS
            if any(s == "at or below" for _, s in (edges_for(k) or {}).values())]
check(len(DOWNWARD) >= 2,
      f"{len(DOWNWARD)} configured band sets are DOWNWARD-favourable and are covered above: "
      f"{', '.join(sorted(DOWNWARD))}")
for key in DOWNWARD:
    edges = edges_for(key) or {}
    named = [b for b in LADDER if b in edges]
    if len(named) < 2:
        continue
    band, upper = named[0], named[1]
    fig = edges[upper][0]
    sentence = "; ".join(f"{edges[b][1]} {edges[b][0]} is {b}" for b in reversed(named))
    row = row_for(sentence, band, module_id=key, reading=fig)
    ctx = mitigation.build_context(row)
    check(ctx is not None and "at or below" in ctx["next_band_line"],
          f"{key}: the composed next-band line keeps the ladder's own 'at or below' wording")


# =====================================================================================
print("\n4. AN ORDINAL LADDER STILL YIELDS NO NUMBER, so the fix invented nothing.")
# =====================================================================================
ordinal = row_for(
    "Green when the rating is Exceptional or Very Good; Yellow when it is Satisfactory; "
    "Amber when it is Marginal; Red when it is Unsatisfactory.", "Amber",
    module_id="A6.4", reading=0)
ordinal.pop("band_reading_value")
ordinal["evidence_metric"] = "The adjectival rating recorded is Marginal."
check(mitigation._boundary_figure(ordinal, mitigation._next_band_up(ordinal)) is None,
      "an ordinal ladder yields NO boundary figure -- no number is invented for it")
check(mitigation.classify_shape(ordinal) == "ordinal",
      "and the reading classifies as ordinal, so the gap is stated in words")
octx = mitigation.build_context(ordinal)
check(octx is not None and "no continuous gap is defined" in octx["gap_line"].lower(),
      "its gap line says no continuous gap is defined rather than stating a figure")


# =====================================================================================
print("\n5. THE INJECTION. One boundary is pointed at a STALE COPY of the constant.")
# =====================================================================================
# This is the order's proof 3. A drifted sentence is EXACTLY how this fails in production: the
# constant is revised in `band_reference_data.json` and a module's sentence still states the old
# figure. Nothing under `simulation/` is written; the STORED ROW is what carries the stale copy,
# which is where the drift would actually land.

colour, real_sentence, _ = models_cat89._band_quality_compliance(
    {"first_pass_acceptance_rate": 0.85, "critical_quality_failures": []}, {})[:3]
live = CUTS["yellow_at_or_above"]
stale = round(float(live) - 0.05, 10)
check(float(stale) != float(live), "the stale copy differs from the live constant")

drifted = real_sentence.replace(f"at or above {live} and below", f"at or above {stale} and below",
                                1)
check(drifted != real_sentence,
      "the stale copy was substituted into the module's stored boundary sentence")

bad_row = row_for(drifted, colour, module_id="A6.1", reading=0.85)
bad_edge = mitigation._boundary_figure(bad_row, mitigation._next_band_up(bad_row))
check(same_number(bad_edge, stale),
      f"the engine reads the STALE figure {stale} out of the drifted sentence, as it must -- it "
      f"reads what the row stored")
check(not same_number(bad_edge, live),
      "and that figure is NOT the deciding constant")

# THE PROOF ITSELF: the comparison this file performs -- extracted figure against the constant
# read independently -- REFUSES the drifted row. A check that could not fail here would be
# worthless, so it is exercised in the failing direction before it is trusted in the passing one.
def constant_matches(row: dict, constant: float) -> bool:
    return same_number(mitigation._boundary_figure(row, mitigation._next_band_up(row)), constant)


check(constant_matches(bad_row, live) is False,
      "PROOF 3: the constant comparison FAILS on the drifted boundary -- the break is CAUGHT")

# RESTORED.
good_row = row_for(real_sentence, colour, module_id="A6.1", reading=0.85)
check(constant_matches(good_row, live) is True,
      "PROOF 3: restored -- the undrifted sentence compares equal to the deciding constant again")
check(models_cat89._band_quality_compliance(
    {"first_pass_acceptance_rate": 0.85, "critical_quality_failures": []}, {})[1] == real_sentence,
      "the module's own emission is unchanged: the injection touched only the stored row")


# =====================================================================================
print("\n6. NOTHING UNDER `simulation/` IS IMPORTED BY THE ENGINE.")
# =====================================================================================
# Re-asserted here because this file DOES import `simulation` -- a check may read what production
# must not. The engine's own code is re-tokenised so the two facts cannot be confused.
import io
import tokenize

with open(mitigation.__file__, "rb") as fh:
    toks = list(tokenize.tokenize(io.BytesIO(fh.read()).readline))
code_text = " ".join(t.string for t in toks
                     if t.type not in (tokenize.COMMENT, tokenize.STRING))
check("simulation" not in code_text,
      "`mitigation.py`'s CODE names `simulation` nowhere -- the constant reaches it only via the "
      "stored row, and this check's own import of it is a check-side read")


# =====================================================================================
passed = sum(1 for ok, _ in results if ok)
print("\nNO API KEY EXISTS IN THIS ENVIRONMENT AND NONE IS SIMULATED. Nothing above needs one: "
      "no composition is performed, only the code-built context and the boundary read.")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
