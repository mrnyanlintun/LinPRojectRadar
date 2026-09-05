#!/usr/bin/env python3
"""
RUN 140, AGENT E. THE MITIGATION ENGINE, PROVED WITHOUT A LIVE MODEL CALL.

Run (from server/):

    DATABASE_URL=sqlite:///<throwaway>.db python tools/test_run140e_mitigation_engine.py

NO API KEY EXISTS IN THIS ENVIRONMENT, and nothing here simulates one having existed. The live
composition -- the single HTTPS request to Anthropic -- is the ONE thing not exercised. Every
other part of the path is exercised end to end against the real code:

  * the context builder, on all five shapes, each built from a stored module row;
  * the validator's five rules, including an injection carrying an invented figure, a named role
    AND a date, refused on all three at once;
  * storage and replay, with the number of calls COUNTED, not assumed;
  * the unbanded and abstaining paths, proved to make NO call at all;
  * the fired-override form;
  * the failed-call path storing and serving the fixed absence line;
  * the recomposition trigger and the supersede pointer.

THE FAKE TRANSPORT LIVES HERE, IN THE CHECK, AND NOWHERE ELSE. `mitigation.compose_one` takes
`caller` as a parameter whose default is the real `ask_provider`; production never passes it.
"""
from __future__ import annotations

import sys
import uuid

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from sqlalchemy import select

import app.main as main  # noqa: F401  -- binds the engine and creates the session factory
from app import ai_provider, mitigation
from app.research_models import ModuleMitigation

Session = main.SessionFactory
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))
    print(("PASS  " if ok else "FAIL  ") + label)


CFG = ai_provider.load_provider("mitigation", environ={})


# ------------------------------------------------------------------ the stored rows, as stored

THRESHOLD_ROW = {
    "module_id": "A3.3", "method_class": "Cost_Contingency_Adequacy", "status_color": "Amber",
    "band_asserted": True,
    "evidence_metric": "Contingency covers 0.62 of the P80 exposure at this period.",
    "band_boundary": "Green at or above 0.90; Yellow at or above 0.75; Amber at or above 0.60; "
                     "Red below 0.60, each boundary inclusive on its lower side.",
    "band_basis": "the owner's configured contingency adequacy ladder",
    "band_basis_id": "owner_configured_contingency_adequacy",
    "threshold_source": "owner_default", "threshold_source_words": "the owner's configured "
                                                                   "default",
    "band_provenance_class": "owner_calibrated",
    "band_provenance_words": "calibrated by the owner",
    "band_coverage_fraction": 0.62,
}

OVERRIDE_ROW = {
    "module_id": "A2.8", "method_class": "Critical_Path_Constraints", "status_color": "Red",
    "band_asserted": True,
    "evidence_metric": "An open constraint sits on the critical path.",
    "band_boundary": "Green at or above 0.95; Amber at or above 0.85; Red below 0.85.",
    "band_basis": "the owner's configured critical-path constraint rule",
    "threshold_source": "owner_default", "band_provenance_class": "owner_calibrated",
    "band_hard_override_fired": True,
    "band_override_conditions": ["open_constraint_on_critical_path"],
    "band_override_words": ("an open constraint on the critical path bands Red regardless of "
                            "the ratio; the override clears when no open constraint remains on "
                            "the critical path"),
}

WORST_OF_ROW = {
    "module_id": "A2.7", "method_class": "Float_Consumption", "status_color": "Amber",
    "band_asserted": True,
    "evidence_metric": "Float consumption bands Amber on its most adverse component.",
    "band_boundary": "Green at or below 0.25; Yellow at or below 0.50; Amber at or below 0.75; "
                     "Red above 0.75.",
    "band_basis": "the owner's configured float consumption ladder",
    "threshold_source": "owner_default", "band_provenance_class": "owner_calibrated",
    "band_components": [
        {"component": "total_float", "value": 0.61, "band": "Amber",
         "boundary": "Amber at or below 0.75"},
        {"component": "free_float", "value": 0.20, "band": "Green",
         "boundary": "Green at or below 0.25"},
    ],
    "band_aggregation_words": "the most adverse component posture governs.",
}

ORDINAL_ROW = {
    "module_id": "A6.4", "method_class": "CPARS_Ratings", "status_color": "Amber",
    "band_asserted": True,
    "evidence_metric": "The most recent CPARS quality rating is Marginal.",
    "band_boundary": "Green on Exceptional or Very Good; Yellow on Satisfactory; Amber on "
                     "Marginal; Red on Unsatisfactory.",
    "band_basis": "the CPARS adjectival rating scale",
    "threshold_source": "external_basis", "band_provenance_class": "external_standard",
}

DERIVED_ROW = {
    "module_id": "B1.1", "method_class": "Signal_Synthesis", "status_color": "Red",
    "band_asserted": True,
    "evidence_metric": "The synthesis bands Red on the bands of the modules feeding it.",
    "band_boundary": "Green, Yellow, Amber and Red are taken from the contributing modules' own "
                     "bands; this module sets no boundary of its own.",
    "band_basis": "the bands of the contributing modules",
    "threshold_source": "owner_default", "band_provenance_class": "owner_calibrated",
}

# A6.1's project-target path is GREEN/RED ONLY. Red's next band up is GREEN, not Amber.
GREEN_RED_ROW = {
    "module_id": "A6.1", "method_class": "Quality_Target", "status_color": "Red",
    "band_asserted": True,
    "evidence_metric": "The project quality target was not met this period.",
    "band_boundary": "Green when the project's own target is met; Red when it is not. There is "
                     "no intermediate band on this path.",
    "band_basis": "the project's own stated quality target",
    "threshold_source": "project_document", "band_provenance_class": "project_specific",
}

# A1.2 (CUSUM) returns LOWERCASE band strings and has NO YELLOW RUNG.
LOWERCASE_ROW = {
    "module_id": "A1.2", "method_class": "CUSUM_Drift", "status_color": "amber",
    "band_asserted": True,
    "evidence_metric": "The CUSUM statistic has crossed its decision interval.",
    "band_boundary": "Green below the decision interval; Amber at or above it; Red at or above "
                     "twice it. There is no Yellow rung on this ladder.",
    "band_basis": "the owner's configured CUSUM decision interval",
    "threshold_source": "owner_default", "band_provenance_class": "owner_calibrated",
}

UNBANDED_ROW = {
    "module_id": "A4.9", "method_class": "Safety_Performance", "status_color": None,
    "band_asserted": False,
    "band_withheld_reason": ("exposure hours this period are below the floor at which a rate is "
                             "meaningful; no band is asserted and no vote is cast"),
    "evidence_metric": "Exposure below the floor at which an incident rate is meaningful.",
}

ABSTAINED_ROW = {
    "module_id": "A1.7", "method_class": "Cost_Performance", "status_color": None,
    "band_asserted": False,
    "band_withheld_reason": "Insufficient data: earned value has not been reported.",
    "evidence_metric": "Insufficient data: earned value has not been reported.",
}

GREEN_ROW = dict(THRESHOLD_ROW, module_id="A1.8", status_color="Green")


# ------------------------------------------------------------------ 1. shape classification

for row, expect in ((THRESHOLD_ROW, "threshold"), (OVERRIDE_ROW, "override"),
                    (WORST_OF_ROW, "worst_of"), (ORDINAL_ROW, "ordinal"),
                    (DERIVED_ROW, "derived")):
    got = mitigation.classify_shape(row)
    check(got == expect,
          f"shape of {row['module_id']} classified from its own stored flags: {got} (want "
          f"{expect})")

check(set(mitigation.SHAPES) == {"threshold", "override", "worst_of", "ordinal", "derived"},
      "the five shapes in the contract are the five shapes the module declares")


# ------------------------------------------------------------------ 2. the code-built context

ctx = mitigation.build_context(THRESHOLD_ROW)
check(ctx["reading"] == THRESHOLD_ROW["evidence_metric"],
      "the reading line is the module's own evidence sentence VERBATIM")
check(THRESHOLD_ROW["band_boundary"] in ctx["next_band_line"],
      "the boundary line carries the module's own stored boundary sentence verbatim")
check(ctx["next_band"] == "Yellow",
      f"Amber's next band up on a four-rung ladder is Yellow (got {ctx['next_band']})")
# The gap is composed IN CODE from two figures BOTH read back off the stored row.
check("0.62" in ctx["gap_line"] and "0.75" in ctx["gap_line"],
      "the gap line states the reading's own figure and the next band's own boundary figure")
check(repr(abs(0.62 - 0.75)) in ctx["gap_line"],
      f"the gap is the arithmetic difference at full stored precision: {ctx['gap_line']}")

# "ONE BAND UP" IS NOT ALWAYS THE NEXT ROW OF THE LADDER -- proved on the two awkward cases.
g = mitigation.build_context(GREEN_RED_ROW)
check(g["next_band"] == "Green",
      f"A6.1's Green/Red-only path: Red's next band up is GREEN (got {g['next_band']})")
lc = mitigation.build_context(LOWERCASE_ROW)
check(lc is not None and lc["band"] == "Amber",
      "A1.2's LOWERCASE band string is normalised and the reading is not silently dropped")
check(lc["next_band"] == "Green",
      f"A1.2 has no Yellow rung, so Amber's next band up is Green (got {lc['next_band']})")

o = mitigation.build_context(ORDINAL_ROW)
check("No continuous gap is defined" in o["gap_line"],
      "an ordinal ladder states no numeric gap rather than inventing one")

ov = mitigation.build_context(OVERRIDE_ROW)
check("override arm fired" in ov["gap_line"]
      and "band_hard_override_fired" in ov["gap_line"]
      and "clears" in ov["gap_line"],
      "a fired override states WHAT FIRED and WHAT CLEARS IT, not a threshold gap")

w = mitigation.build_context(WORST_OF_ROW)
check(len(w["components"]) == 2 and w["components"][0]["band"] == "Amber",
      "a worst-of reading hands over every component with its own value, band and boundary")

check(mitigation.build_context(UNBANDED_ROW) is None,
      "an UNBANDED module (Safety_Performance below its exposure floor) yields NO context")
check(mitigation.build_context(ABSTAINED_ROW) is None,
      "an ABSTAINING module yields NO context")
check(mitigation.build_context(GREEN_ROW) is None, "a Green reading yields no context")


# ------------------------------------------------------------------ 3. the validator

GOOD = ["Re-baseline the contingency draws against the current P80 exposure.",
        "Retire closed risks from the exposure model so the coverage fraction reflects live "
        "risks only."]
check(mitigation.validate(GOOD, ctx) == [],
      "a clean two-candidate output is accepted with no refusals")

# THE INJECTION, THE STANDARD WAY: one output carrying ALL THREE defects at once.
INJECTED = [
    "The PM should re-baseline the contingency draws to reach 0.99 coverage by 2026-12-31.",
    "Retire closed risks from the exposure model.",
]
refusals = mitigation.validate(INJECTED, ctx)
blob = " | ".join(refusals)
check("named a person, role, team or authority" in blob and "pm" in blob,
      f"INJECTION refused rule 1, the named role: {blob[:120]}")
check("used a figure that was not supplied" in blob and "0.99" in blob,
      "INJECTION refused rule 3, the invented figure 0.99")
check("stated a deadline or a date" in blob and "2026" in blob,
      "INJECTION refused rule 2, the date")
check(len([r for r in refusals if r.startswith(("named", "used", "stated"))]) == 3,
      f"ALL THREE refused at once, in one pass: {len(refusals)} refusals raised")

check(any("another module" in r for r in
          mitigation.validate(["Align with A1.7's earned value reading.",
                               "Retire closed risks."], ctx)),
      "rule 4: a reference to another module's evidence is refused")
check(any("length" in r for r in mitigation.validate(["Only one candidate."], ctx)),
      "rule 5: one candidate is refused (two to four are allowed)")
check(any("length" in r for r in mitigation.validate(["A. B.", "C."], ctx)),
      "rule 5: a candidate carrying more than one sentence is refused")
check(mitigation.validate(["Raise coverage toward 0.75.", "Retire closed risks."], ctx) == [],
      "a figure that WAS supplied in the context (the 0.75 boundary) is accepted")


# ------------------------------------------------------------------ 4. storage, replay, counts

class Counter:
    """The fake transport. IT LIVES IN THE CHECK. Every call through it is COUNTED."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def __call__(self, blocks, cfg, environ=None):
        self.calls += 1
        return self.text


class Boom:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, blocks, cfg, environ=None):
        self.calls += 1
        raise ai_provider.ProviderCallError("simulated provider failure (no key present)")


PROJECT_ID = uuid.uuid4()
session = Session()
try:
    # The FK is ON, so a project row must exist for the CASCADE to point at.
    from app.models import Project
    session.add(Project(id=PROJECT_ID, legacy_id=f"R140E-{PROJECT_ID.hex[:8]}",
                        doc={"name": "Run 140 E fixture"}, record_version=1,
                        archived=False, is_training=False))
    session.flush()

    store = mitigation.MitigationStore(session, PROJECT_ID)
    good_text = "\n".join(GOOD)

    c1 = Counter(good_text)
    first = mitigation.compose_one(THRESHOLD_ROW, store=store, period=3, cfg=CFG, caller=c1)
    check(c1.calls == 1, f"first composition made EXACTLY ONE call (counted: {c1.calls})")
    check(first["candidates"] == GOOD, "the accepted candidates are served as composed")
    check(first["absent_reason"] is None, "an accepted composition carries no absence reason")
    check(set(first) == {"module_id", "band", "shape", "reading", "next_band", "gap",
                         "candidates", "absent_reason", "composed_at", "model", "provider"},
          "the served entry carries all ELEVEN contract keys and no others")
    check(isinstance(first["candidates"], list) and first["absent_reason"] is None,
          "`candidates` is a list and `absent_reason` is null when it is non-empty")

    c2 = Counter("THIS TEXT MUST NEVER APPEAR")
    second = mitigation.compose_one(THRESHOLD_ROW, store=store, period=3, cfg=CFG, caller=c2)
    check(c2.calls == 0,
          f"REPLAY MADE NO CALL AT ALL -- calls counted on the second render: {c2.calls}")
    check(second["candidates"] == first["candidates"],
          "two renders of the same reading produce BYTE-IDENTICAL mitigation text")
    check(second == first, "the whole served entry is identical on replay, not only the prose")

    rows = session.execute(select(ModuleMitigation).where(
        ModuleMitigation.project_id == PROJECT_ID)).scalars().all()
    check(len(rows) == 1, f"one composition stored one row (found {len(rows)})")
    check(rows[0].provider == "anthropic" and rows[0].model == "claude-opus-5",
          f"the row records the resolved provider and model: {rows[0].provider}/{rows[0].model}")

    # THE UNBANDED PATH MAKES NO CALL. Counted, not assumed.
    c3 = Counter(good_text)
    check(mitigation.compose_one(UNBANDED_ROW, store=store, period=3, cfg=CFG, caller=c3) is None
          and c3.calls == 0,
          f"an UNBANDED module returns no block and makes NO call (counted: {c3.calls})")
    c4 = Counter(good_text)
    check(mitigation.compose_one(ABSTAINED_ROW, store=store, period=3, cfg=CFG,
                                 caller=c4) is None and c4.calls == 0,
          f"an ABSTAINING module returns no block and makes NO call (counted: {c4.calls})")

    # THE FAILED CALL STORES AND SERVES THE ABSENCE LINE, AND IS NEVER RETRIED.
    boom = Boom()
    failed = mitigation.compose_one(OVERRIDE_ROW, store=store, period=3, cfg=CFG, caller=boom)
    check(boom.calls == 1 and failed["candidates"] == []
          and failed["absent_reason"] == mitigation.ABSENCE_LINE,
          "a failed call serves the fixed absence line and no candidates")
    stored_absent = session.execute(select(ModuleMitigation).where(
        ModuleMitigation.module_id == "A2.8")).scalars().one()
    check(stored_absent.mitigations == [mitigation.ABSENCE_LINE],
          "the absence line is STORED, so the failure is a recorded answer and not a hole")
    boom2 = Boom()
    mitigation.compose_one(OVERRIDE_ROW, store=store, period=3, cfg=CFG, caller=boom2)
    check(boom2.calls == 0,
          f"A MISSING MITIGATION IS NEVER SILENTLY RETRIED AT RENDER (calls: {boom2.calls})")

    # A REFUSED VALIDATION STORES THE ABSENCE LINE, NEVER THE FAILED TEXT.
    bad = Counter("\n".join(INJECTED))
    refused = mitigation.compose_one(ORDINAL_ROW, store=store, period=3, cfg=CFG, caller=bad)
    check(bad.calls == 1 and refused["absent_reason"] == mitigation.ABSENCE_LINE,
          "a refused validation serves the absence line")
    kept = session.execute(select(ModuleMitigation).where(
        ModuleMitigation.module_id == "A6.4")).scalars().one()
    check(kept.mitigations == [mitigation.ABSENCE_LINE]
          and "PM should" not in str(kept.mitigations),
          "THE FAILED TEXT IS NOT STORED -- only the absence line is")

    # THE OVERRIDE FORM, ON THE SERVED ENTRY.
    check("There is no threshold gap to close" in failed["gap"]
          and "band_hard_override_fired" in failed["gap"],
          "an override-driven Red serves the FIRED-OVERRIDE form, not a threshold gap")

    # THE RECOMPOSITION TRIGGER: the reading changes, the fingerprint changes, the old row is
    # kept and superseded, and a fresh composition is stored.
    moved = dict(THRESHOLD_ROW, status_color="Red",
                 evidence_metric="Contingency covers 0.41 of the P80 exposure at this period.",
                 band_coverage_fraction=0.41)
    fp_old = mitigation.reading_fingerprint(
        THRESHOLD_ROW, mitigation.build_context(THRESHOLD_ROW),
        provider=CFG.provider, model=CFG.model)
    fp_new = mitigation.reading_fingerprint(
        moved, mitigation.build_context(moved), provider=CFG.provider, model=CFG.model)
    check(fp_old != fp_new, "a moved band with changed figures changes the reading fingerprint")
    c5 = Counter(good_text)
    mitigation.compose_one(moved, store=store, period=3, cfg=CFG, caller=c5)
    check(c5.calls == 1, f"the changed reading was RECOMPOSED (calls: {c5.calls})")
    a33 = session.execute(select(ModuleMitigation).where(
        ModuleMitigation.module_id == "A3.3")).scalars().all()
    check(len(a33) == 2, f"BOTH rows remain: the old text is kept, not overwritten ({len(a33)})")
    old = [r for r in a33 if r.reading_fingerprint == fp_old][0]
    new = [r for r in a33 if r.reading_fingerprint == fp_new][0]
    check(old.superseded_by == new.mitigation_id,
          "the superseded row POINTS AT the row that replaced it")
    check(new.superseded_by is None, "the live row is not superseded")

    # An unchanged reading under a NEW PERIOD is a new key and composes afresh -- the store is
    # keyed per period, so a period that recomputes the same figures does not borrow last
    # period's prose.
    c6 = Counter(good_text)
    mitigation.compose_one(THRESHOLD_ROW, store=store, period=4, cfg=CFG, caller=c6)
    check(c6.calls == 1, "a new period is a new key and composes once for that period")

    session.rollback()
finally:
    session.close()


# ------------------------------------------------------------------ 5. no simulation reads

# Comments and docstrings discuss both words at length; what matters is the CODE, so the
# tokenizer is used rather than a substring scan over prose.
import io
import tokenize

code = "".join(
    tok.string if tok.type not in (tokenize.COMMENT, tokenize.STRING) else " "
    for tok in tokenize.generate_tokens(io.StringIO(open(mitigation.__file__).read()).readline))
check("simulation" not in code,
      "the engine's CODE performs ZERO imports or reads into `server/app/simulation/`")
check("temperature" not in code,
      "`temperature` appears nowhere in the engine's CODE, so it is never passed to a client")


passed = sum(1 for ok, _ in results if ok)
print()
print("NOTE: no ANTHROPIC_API_KEY exists in this environment. The live composition -- the single "
      "HTTPS request -- was NOT exercised and is NOT simulated. Everything above ran against the "
      "real engine with a counting fake transport injected at the `caller` parameter, which "
      "production never supplies.")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
