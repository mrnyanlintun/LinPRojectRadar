"""
RUN 20 CYCLE 4 (P0D): THE LINEAGE DISCLOSURE OF THE TWO ADVISORY DUPLICATE PAIRS.

WHAT THIS CYCLE IS AND IS NOT. Cycle 3 built the lineage framework and used it on the one path
that votes. It left two findings open with the same shape and no framework use at all: Change
Order Frequency duplicates Contract Modification Frequency, and Tornado Risk Ranking duplicates
the evidence of Sensitivity Analysis. Run 19 recorded both as lineage findings, DUPLICATE_WITH_8.5
and DUPLICATE_OF_5.2_EVIDENCE, and the framework to express them has existed since cycle 3 while
none of the four modules declared anything at all.

THIS CYCLE DECLARES LINEAGE. IT DOES NOT REBAND ANYTHING. No threshold, boundary, band or
arithmetic result of any of the four modules is touched, and the pinned outputs below prove it.
The method-label mismatches these four carry -- a count that is not a frequency without an
exposure, and a ranking that evaluates no output at any input's low or high -- are P1 work in the
register and are NOT addressed here. A lineage declaration is a statement about which body of
evidence a reading rests on. It is not a repair of the reading.

WHY THE PARTNER MODULES ARE DECLARED TOO. A partition needs both members. Declaring only 4.6 and
5.3 would leave their partners undeclared, and `fusion` would then report an undeclared lineage
and refuse to assume independence, which is safe but tells nobody anything. The disclosure is only
a disclosure when both ends of the duplication say what they rest on.

THE INDEPENDENT ORACLE FOR THE DECLARED FACTS. A declared fact list could be wrong in a way no
string comparison would catch, so the declaration is checked against EXECUTION and not only
against a hand-written expectation: for every governed input field behind a declared fact, the
module must ABSTAIN when that field is withheld. A module that computes a reading without a fact
it claims to rest on is not resting on it. This is deliberately not derived from the same
expression the declaration is built from -- the declarations in `lineage.MODULE_LINEAGE` are
hand-written literals, and the oracle here is the module's own runtime refusal.

THE PRE-FIX MEASUREMENTS ARE PINNED AS HISTORICAL DEFECTS, never as expected answers.
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import fusion, lineage, registry  # noqa: E402
sys.path.insert(0, str(HERE))
import run29_fixtures as FX  # noqa: E402


# RUN 20 CYCLE 6 UPDATED THIS SUITE AND DID NOT DELETE IT. The owner decision that followed
# cycle 5 overturned the transitive-closure treatment this file was written against: dependence
# is NOT transitive, and `lineage.partition` is gone. The cycle's findings stand and are kept as
# historical evidence; the call sites are moved onto the non-transitive separation and any claim
# the decision overturned is corrected IN PLACE with the correction stated, rather than quietly
# dropped. A deleted check is a check nobody can see was wrong.
def _parts(recs):
    """The bodies of evidence, as module-id index lists, under the non-transitive model."""
    return lineage.evidence_bodies(recs)["bodies"]


_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(name + (f" -- {detail}" if detail else ""))


def near(name: str, got, want, tol=5e-5) -> None:
    check(name, got is not None and abs(float(got) - float(want)) <= tol,
          f"got {got!r}, expected {want!r}")


# --------------------------------------------------------------------------- the fixture
#
# One synthetic project, written by hand from the field names the four modules declare. Six
# change orders, eight per cent scope growth, a cost index of 0.9091 and a schedule index of
# 0.9615 that are the honest ratios of the earned value figures beside them, a document risk
# score inside its share domain and a two-point progress shortfall. Nothing here is drawn from
# application output.

FIXTURE = {
    "changeOrderCount": 6,
    "baselineContractSum": 1000000.0,
    "revisedContractSum": 1080000.0,
    "bac": 1000000.0,
    "ev": 500000.0,
    "ac": 550000.0,
    "pv": 520000.0,
    "cpi": 500000.0 / 550000.0,
    "spi": 500000.0 / 520000.0,
    "docRiskScore": 0.42,
    "actualPctComplete": 50.0,
    "plannedPctComplete": 52.0,
}

#: THE ABSTENTION ORACLE, IN TWO ARMS, AND WHY IT HAS TO BE TWO.
#:
#: `lineage.py` states the rule its records follow: source facts are the governed facts a signal
#: ULTIMATELY rests on, not its immediate arguments, and a ratio is never a fact. So a module can
#: rest on the earned value while never being handed the earned value: Tornado Risk Ranking is
#: handed a cost performance index and a schedule performance index as fields, and those indices
#: are earned value over actual cost and earned value over planned value.
#:
#: A single-armed oracle -- withhold the field, expect an abstention -- would therefore have
#: called a TRUE declaration false. It did exactly that when this suite was first run, on three
#: checks, and the finding is recorded rather than quietly relaxed. The oracle is two-armed now:
#:
#:   DIRECT   the module reads the field itself. Withhold it and the module must abstain.
#:   THROUGH  the module reads a ratio that is defined over the fact. Withhold the RATIO's field
#:            and the module must abstain, AND the record's derivation chain must state the
#:            ratio's definition, so the path from the fact to the reading is written down and
#:            not merely asserted.
#:
#: Neither arm is derived from the expression the declaration is built from: the declarations are
#: hand-written literals in `lineage.MODULE_LINEAGE` and both arms are the module's own runtime
#: refusal.
FACT_FIELD = {
    "change_order_count": "changeOrderCount",
    "baseline_contract_sum": "baselineContractSum",
    "revised_contract_sum": "revisedContractSum",
    "bac": "bac",
    "ev": "ev",
    "ac": "ac",
    "pv": "pv",
    "doc_risk_score": "docRiskScore",
    "actual_pct_complete": "actualPctComplete",
    "planned_pct_complete": "plannedPctComplete",
}

#: The facts a module reaches THROUGH a supplied ratio rather than reading directly, with the
#: field that carries the ratio and the definition its derivation chain must state.
THROUGH_RATIO = {
    "A5.3": {
        "ev": ("cpi", "cost performance index = ev / ac"),
        "ac": ("cpi", "cost performance index = ev / ac"),
        "pv": ("spi", "schedule performance index = ev / pv"),
    },
}

# RUN 29 BROKE ONE OF THE TWO PAIRS, and breaking it is the correction rather than a loss.
# Change Order Frequency now computes from a governed change event register -- each change with
# its own identity, dates, type, cause, value and direction, over a declared exposure -- while
# Contract Modification Frequency still reads the two extracted contract sums and a count. They
# are no longer two readings of one body, so declaring them one would manufacture a
# corroboration that has stopped existing, which is the error Run 20 cycle 5 recorded in its
# other direction. The pair is asserted as SEPARATE below, with the reason, rather than dropped.
PAIRS = (("A5.2", "A5.3"),)
SEPARATED_BY_RUN_29 = (("A4.6", "B3.5"),)
FOUR = ("A4.6", "B3.5", "A5.2", "A5.3")


def run(mid, si):
    return registry.run_module(mid, si, lambda: 0.5, None)


def abstained(out) -> bool:
    """An abstention, in the vocabulary the modules actually use. Checked positively rather than
    as 'not the expected colour', so a module that returned some third thing is not read as an
    abstention by accident."""
    return (out.get("status_color") in (None, "", "Gray", "Grey", "Unknown")
            or out.get("insufficient") is True)


def rec_of(mid):
    """The declared record, or an empty mapping. A missing declaration must make this suite FAIL
    with a named check, never crash: three suites in this programme were caught only because the
    strict runner refuses a missing RESULT line after a KeyError, and that is not a standard to
    repeat in a file written afterwards."""
    return lineage.lineage_for(mid) or {}


def sig(mid, status):
    rec = lineage.lineage_for(mid)
    out = {"module_id": mid, "status": status}
    if rec:
        out["lineage"] = rec
    return out


# ============================================================ 1. NOTHING WAS REBANDED
#
# Pinned from the pre-declaration run of the same fixture, recorded before a single line of
# lineage was declared. If a lineage declaration ever moves a band, these fail.

print("== the four modules read exactly what they read before the declaration ==")

# RUN 29 REPLACED THE PINS FOR THREE OF THE FOUR, and the reason is the same one cycle 9 gave
# when it replaced them for A5.2: THIS SECTION PROVES THAT A LINEAGE DECLARATION NEVER MOVES A
# BAND, and it still proves exactly that. What moved these numbers is not a declaration but the
# owner's supplied Run-29 contract replacing three computations outright. A4.6 no longer bands a
# raw count jointly with contract growth, A5.2 no longer perturbs a hard-coded response, and
# A5.3 no longer ranks four present-state deviations. The pins are re-taken against the corrected
# modules, on the structures they now read, and still pin them.
_a46 = run("A4.6", {**FIXTURE, "changeEventRegister": FX.change_register()})
check("A4.6 asserts no colour on the fixture, because the frequency it now reports is not the "
      "quantity the old joint ladder was drawn over",
      _a46["status_color"] is None and _a46["calibration_pending"] is True,
      str(_a46.get("status_color")))
near("A4.6 reports one change per standardised thirty day period",
     _a46["change_frequency_per_30_days"], 1.0)
near("A4.6 reports the magnitude separately, at six per cent of the baseline contract",
     _a46["change_magnitude_net"], 0.06)
check("A4.6 produces no reading at all from the fixture's extracted contract sums",
      run("A4.6", FIXTURE).get("insufficient_data") is True)

_b35 = run("B3.5", FIXTURE)
check("B3.5 still bands Amber on the fixture", _b35["status_color"] == "Amber", str(_b35.get("status_color")))
check("B3.5 still reports six modifications", _b35["co_count"] == 6, str(_b35.get("co_count")))
near("B3.5 still reports eight per cent scope growth", _b35["scope_growth_pct"], 8.0)

_a52 = run("A5.2", {"sensitivityModel": FX.sensitivity_model()})
check("A5.2 asserts no colour, because a normalised sensitivity of a declared response is not "
      "the quantity the old ladder was drawn over",
      _a52["status_color"] is None and _a52["calibration_pending"] is True,
      str(_a52.get("status_color")))
near("A5.2 reproduces the supplied contract's own normalised sensitivity of 1.68",
     _a52["inputs"][0]["normalised_sensitivity"], 1.68)
check("A5.2 produces no reading at all from the fixture's earned-value scalars",
      run("A5.2", FIXTURE).get("insufficient_data") is True)

_a53 = run("A5.3", {"sensitivityModel": FX.sensitivity_model()})
check("A5.3 asserts no colour either", _a53["status_color"] is None
      and _a53["calibration_pending"] is True, str(_a53.get("status_color")))
check("A5.3 presents the swing the sensitivity analysis computed and creates no evidence of its "
      "own", _a53["independent_evidence"] is False and _a53["derived_from"] == "A5.2"
      and _a53["bars"][0]["response_at_low"] == _a52["inputs"][0]["response_at_low"],
      str(_a53.get("derived_from")))

# AND THE PAIR RUN 29 SEPARATED, asserted as separate with its reason rather than dropped.
for _a, _b in SEPARATED_BY_RUN_29:
    _fused = fusion.fuse_signals([sig(_a, "Amber"), sig(_b, "Amber")])
    check(f"{_a} and {_b} are now two bodies of evidence, because one reads a governed change "
          f"event register and the other reads two extracted contract sums",
          _fused["lineage_groups"] == 2, f"lineage_groups={_fused['lineage_groups']}")
    check(f"and the separation is declared rather than defaulted: both {_a} and {_b} carry a "
          f"lineage record", lineage.lineage_for(_a) is not None
          and lineage.lineage_for(_b) is not None)
    check(f"and they name different bodies, so nothing is asserted independent by accident",
          not (set(lineage.lineage_for(_a)["lineage_group_ids"])
               & set(lineage.lineage_for(_b)["lineage_group_ids"])),
          f"{lineage.lineage_for(_a)['lineage_group_ids']} vs "
          f"{lineage.lineage_for(_b)['lineage_group_ids']}")

# The four are advisory. A lineage declaration must not make any of them a voter.
for m in FOUR:
    check(f"{m} is not in the voting set", m not in registry.CORE_VOTING_MODULES)
check("the voting set is still exactly the two earned-value transforms",
      set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"}, str(sorted(registry.CORE_VOTING_MODULES)))


# ============================================================ 2. THE HISTORICAL DEFECT
#
# Pre-declaration, an undeclared duplicate pair sharpened belief exactly as the voting path did
# before cycle 3, and reported a conflict coefficient between two readings of one body.

print("== HISTORICAL DEFECT, must not return ==")

for a, b in PAIRS:
    both = fusion.fuse_signals([sig(a, "Amber"), sig(b, "Amber")])
    check(f"HISTORICAL DEFECT, must not return: {a} and {b} counted as two bodies of evidence",
          both["lineage_groups"] == 1, f"lineage_groups={both['lineage_groups']}")
    check(f"HISTORICAL DEFECT, must not return: {a} with {b} sharpening 0.7000 to 0.9273",
          abs(both["mass"]["Amber"] - 0.9273) > 1e-3, f"Amber={both['mass']['Amber']:.4f}")
    check(f"HISTORICAL DEFECT, must not return: a conflict of 0.4414 estimated between "
          f"{a} and {b}, which are two readings of one body",
          abs(both["conflict"] - 0.4414) > 1e-3, f"conflict={both['conflict']:.4f}")
    check(f"HISTORICAL DEFECT, must not return: the fusion of {a} and {b} reporting no "
          f"declared lineage at all", both["lineage_declared"] is True)


# ============================================================ 3. THE DECLARATIONS EXIST AND ARE WHOLE

print("== every one of the four declares a whole lineage record ==")

REQUIRED_FIELDS = ("module_id", "source_fact_ids", "source_document_ids", "dependency_ids",
                   "lineage_group_ids", "evidence_relationship", "derivation_chain")

for m in FOUR:
    rec = lineage.lineage_for(m)
    check(f"{m} declares a lineage record", rec is not None)
    if rec is None:
        continue
    for f in REQUIRED_FIELDS:
        check(f"{m} carries the {f} field", f in rec)
    check(f"{m} names itself in its record", rec["module_id"] == m, str(rec.get("module_id")))
    check(f"{m} declares a relationship inside the vocabulary",
          rec["evidence_relationship"] in lineage.EVIDENCE_RELATIONSHIPS,
          str(rec.get("evidence_relationship")))
    # RUN 29. Two of the four now genuinely DO have independence, because each is the only
    # reader of its own governed body: A4.6 reads the change event register nothing else reads,
    # and A5.2 reads the sensitivity model, whose only other reader is derived FROM it. Asserting
    # dependence for those two would manufacture a corroboration that does not exist, which is
    # the error in the other direction. So the assertion is made per module, by name, rather than
    # over all four, and every relationship is still pinned exactly.
    if m in ("B3.5", "A5.3"):
        check(f"{m} does NOT claim independence, because it does not have it",
              rec["evidence_relationship"] != lineage.INDEPENDENT,
              str(rec.get("evidence_relationship")))
        check(f"{m} declares a relationship that asserts dependence outright",
              rec["evidence_relationship"] in lineage.DEPENDENT_RELATIONSHIPS,
              str(rec.get("evidence_relationship")))
    else:
        check(f"{m} declares independence, and it is the only reader of its own governed body",
              rec["evidence_relationship"] == lineage.INDEPENDENT,
              str(rec.get("evidence_relationship")))
    check(f"{m} is project-condition evidence and not in the anti-feedback set",
          rec["evidence_relationship"] not in lineage.NON_PROJECT_EVIDENCE)
    check(f"{m} carries a derivation chain of more than the module id alone",
          len(rec["derivation_chain"]) >= 2, str(rec.get("derivation_chain")))
    # RUN 29. A module reading a governed STRUCTURE rests on the structure, not on a list of
    # scalar facts, so the requirement is that it rests on a named body OR a named fact. A
    # record naming neither would still be caught.
    check(f"{m} rests on at least one named governed fact or evidence body",
          len(rec["source_fact_ids"]) >= 1 or len(rec["lineage_group_ids"]) >= 1,
          f"facts={rec['source_fact_ids']} bodies={rec['lineage_group_ids']}")

# The relationships, each asserted by name so a silent reclassification is a red.
check("A4.6 is declared independent, on the governed change event register it alone reads",
      rec_of("A4.6").get("evidence_relationship") == lineage.INDEPENDENT)
check("B3.5 is declared a same-source transform of the same contract change record",
      rec_of("B3.5").get("evidence_relationship") == lineage.SAME_SOURCE_TRANSFORM)
check("A5.2 is declared independent, on the governed sensitivity model it alone computes from",
      rec_of("A5.2").get("evidence_relationship") == lineage.INDEPENDENT)
check("A5.3 is declared DERIVED rather than correlated, because it no longer recomputes over "
      "the same evidence: it takes A5.2's result as its only argument",
      rec_of("A5.3").get("evidence_relationship") == lineage.DERIVED
      and rec_of("A5.3").get("dependency_ids") == ("A5.2",))


# ============================================================ 4. THE FACTS ARE TRUE OF THE CODE
#
# The execution oracle. Withhold the field behind a declared fact and the module must abstain.

print("== every declared fact is a fact the module actually cannot compute without ==")

for m in FOUR:
    rec = lineage.lineage_for(m)
    if rec is None:
        continue
    for fact in rec["source_fact_ids"]:
        through = THROUGH_RATIO.get(m, {}).get(fact)
        if through is not None:
            ratio_field, definition = through
            check(f"{m} reaches {fact} through {ratio_field}, and its derivation chain states "
                  f"the definition rather than asserting the dependence",
                  any(definition in step for step in rec["derivation_chain"]),
                  f"chain={rec['derivation_chain']!r}")
            field = ratio_field
            why = f"so its declared fact {fact}, reached through {ratio_field}, is real"
        else:
            field = FACT_FIELD.get(fact)
            why = f"so its declared fact {fact} is real"
            check(f"{m}'s declared fact {fact} names a governed input field the fixture carries",
                  field is not None and field in FIXTURE, f"fact={fact!r}")
        if field is None or field not in FIXTURE:
            continue
        short = dict(FIXTURE)
        short.pop(field)
        out = run(m, short)
        check(f"{m} abstains when {field} is withheld, {why}", abstained(out),
              f"got status_color={out.get('status_color')!r}")

# A ratio is never a fact in this vocabulary. The two indices are steps in a chain, and neither
# may be declared as a governed fact by any of the four.
for m in FOUR:
    rec = lineage.lineage_for(m)
    if rec is None:
        continue
    check(f"{m} declares no ratio as a fact: cpi is absent from its fact list",
          "cpi" not in rec["source_fact_ids"])
    check(f"{m} declares no ratio as a fact: spi is absent from its fact list",
          "spi" not in rec["source_fact_ids"])


# ============================================================ 5. THE PARTITION SEES THE DUPLICATION

print("== the partition places each duplicate pair in one body of evidence ==")

for a, b in PAIRS:
    parts = _parts([r for r in (lineage.lineage_for(a), lineage.lineage_for(b)) if r])
    check(f"{a} and {b} partition into ONE body of evidence", len(parts) == 1,
          f"got {len(parts)} parts: {parts!r}")

# Order must not matter, and a third reading of the same body must not create a second body.
for a, b in PAIRS:
    parts = _parts([r for r in (lineage.lineage_for(b), lineage.lineage_for(a)) if r])
    check(f"{b} and {a} partition into ONE body in the reverse order too", len(parts) == 1)

# RUN 29. The four are now THREE bodies, not two: the sensitivity pair is still one body, and
# the two change-order modules are two, because they no longer read the same evidence. The count
# is stated exactly so a silent merge or split turns this red either way.
check("all four together are THREE bodies: the sensitivity pair is one, and the two "
      "change-order modules are two because they no longer read the same evidence",
      len(_parts([r for r in (lineage.lineage_for(m) for m in FOUR) if r])) == 3,
      str(_parts([r for r in (lineage.lineage_for(m) for m in FOUR) if r])))

# The contract change record and the earned-value and document facts share nothing, so the two
# pairs must NOT collapse into one body. A partition that merges everything is as wrong as one
# that merges nothing.
_cross = _parts(
    [r for r in (lineage.lineage_for("A4.6"), lineage.lineage_for("A5.2")) if r])
check("Change Order Frequency and Sensitivity Analysis rest on DIFFERENT bodies",
      len(_cross) == 2, str(_cross))


# ============================================================ 6. DUPLICATION NO LONGER STRENGTHENS

print("== a duplicate reading of one body changes nothing, in every band ==")

BANDS = ("Green", "Yellow", "Amber", "Red")
for a, b in PAIRS:
    for band in BANDS:
        one = fusion.fuse_signals([sig(a, band)])
        two = fusion.fuse_signals([sig(a, band), sig(b, band)])
        near(f"{a} alone and {a} with {b} carry the identical mass on {band}",
             two["mass"][band], one["mass"][band])
        check(f"{a} with {b} on {band} is one body of evidence", two["lineage_groups"] == 1)
        check(f"{a} with {b} on {band} estimates no conflict between a body and itself",
              two["conflict_estimable"] is False)
        check(f"{a} with {b} on {band} reports the same governed status as {a} alone",
              two["status"] == one["status"], f"{two['status']} vs {one['status']}")

# RUN 29. The within-body disagreement this block recorded was between the two change-order
# modules, which are no longer one body, so the demonstration moves to the pair that still IS
# one: the sensitivity model and the ranking derived from it. The property is identical -- two
# readings of one body disagreeing resolve to the more adverse and are never scored as conflict
# between independent sources -- and it is asserted on the pair the property now applies to.
_dis2 = fusion.fuse_signals([sig("A5.2", "Red"), sig("A5.3", "Amber")])
check("a within-body disagreement between the sensitivity reading and the ranking derived from "
      "it resolves to the more adverse of the two", _dis2["status"] == "Red",
      str(_dis2["status"]))
check("and the sensitivity pair is one body", _dis2["lineage_groups"] == 1)
check("and the disagreement is recorded rather than absorbed",
      any(b["disagreement"] for b in _dis2["lineage_bodies"]))
check("and it is not scored as conflict between independent sources",
      _dis2["conflict_estimable"] is False)
check("and it resolves the same way in the reverse order",
      fusion.fuse_signals([sig("A5.3", "Amber"), sig("A5.2", "Red")])["status"] == "Red")


# ============================================================ 7. THE POSITIVE CONTROL
#
# This file must be capable of failing. A declaration that suppressed everything would satisfy
# every check above and be worse than the defect.

print("== genuine corroboration still corroborates ==")

_independent = {
    "module_id": "SITE.1",
    "status": "Amber",
    "lineage": lineage.lineage_record(
        "SITE.1", source_fact_ids=("site_inspection", "weather_log"),
        evidence_relationship=lineage.INDEPENDENT,
        derivation_chain=("site inspection record", "adverse-day count")),
}
_corr = fusion.fuse_signals([sig("A4.6", "Amber"), _independent])
near("an independent Amber body still corroborates Change Order Frequency to 0.9273",
     _corr["mass"]["Amber"], 0.9273, tol=5e-4)
check("and it is counted as two bodies of evidence", _corr["lineage_groups"] == 2)
check("and its conflict is estimable, because the two bodies really can disagree",
      _corr["conflict_estimable"] is True)

_corr2 = fusion.fuse_signals([sig("A5.3", "Amber"), _independent])
near("an independent Amber body still corroborates Tornado Risk Ranking to 0.9273",
     _corr2["mass"]["Amber"], 0.9273, tol=5e-4)
check("and that is two bodies as well", _corr2["lineage_groups"] == 2)

# And the suppression must not leak sideways: adding the duplicate to a genuinely corroborated
# pair must leave the corroboration exactly where it was, neither strengthening nor weakening.
# RUN 29: the duplicate reading is now A5.3 over A5.2, so the leak test uses that pair.
_corr_sens = fusion.fuse_signals([sig("A5.2", "Amber"), _independent])
_three = fusion.fuse_signals([sig("A5.2", "Amber"), sig("A5.3", "Amber"), _independent])
near("adding the duplicate reading to a genuinely corroborated pair changes nothing at all",
     _three["mass"]["Amber"], _corr_sens["mass"]["Amber"])
check("and the count of bodies stays two", _three["lineage_groups"] == 2)


# ============================================================ 8. THE DECLARATION IS DISCLOSED, NOT BURIED

print("== the duplication is stated where a reader can find it ==")

_a46 = rec_of("A4.6")
_b35 = rec_of("B3.5")
check("the two change-order modules declare DIFFERENT evidence bodies, and the separation is "
      "stated where a reader can find it rather than being left to be inferred",
      set(_a46.get("lineage_group_ids", ())) & set(_b35.get("lineage_group_ids", ())) == set(),
      f"{_a46.get('lineage_group_ids')} vs {_b35.get('lineage_group_ids')}")
check("the two change-order modules declare DIFFERENT governed evidence: one names a change "
      "event register as its body and the other names the three extracted contract facts",
      set(_a46.get("source_fact_ids", ())) != set(_b35.get("source_fact_ids", ()))
      and bool(_b35.get("source_fact_ids")),
      f"{_a46.get('source_fact_ids')} vs {_b35.get('source_fact_ids')}")

_a52 = rec_of("A5.2")
_a53 = rec_of("A5.3")
check("the two sensitivity modules declare an overlapping evidence body",
      set(_a52.get("lineage_group_ids", ())) & set(_a53.get("lineage_group_ids", ())) != set())
# RUN 29. The two used to share governed FACTS, because each recomputed over the same
# earned-value and document scalars. They now share a governed BODY -- the sensitivity model --
# and the ranking rests on no facts of its own at all, because it computes nothing of its own:
# it takes the sensitivity result as its only argument. That is a stronger statement than the
# shared-facts one it replaces, and it is what the supplied Run-29 contract required.
check("the two sensitivity modules share a governed evidence body",
      set(_a52.get("lineage_group_ids", ())) & set(_a53.get("lineage_group_ids", ())) != set())
check("and Tornado Risk Ranking rests on NO facts Sensitivity Analysis does not, because it "
      "creates no evidence of its own",
      set(_a53.get("source_fact_ids", ())) - set(_a52.get("source_fact_ids", ())) == set(),
      f"{_a53.get('source_fact_ids')} vs {_a52.get('source_fact_ids')}")
check("and it names the signal it is derived from, so the derivation is readable rather than "
      "inferred", _a53.get("dependency_ids") == ("A5.2",)
      and _a53.get("parent_signal_ids") == ("A5.2",),
      f"{_a53.get('dependency_ids')}")

# The declarations must survive a round trip through the stored compute result, which is plain
# data. A record that only exists in memory discloses nothing to anyone reading the stored run.
# NOTE, recorded rather than asserted away: a record's tuples come back from JSON as lists, so a
# record does not compare EQUAL to its own round trip. Nothing stores these records today, and
# equality across a JSON boundary was never a contract of the model; what a disclosure needs is
# that the record can be serialised at all and that every field survives with the same contents.
# That is what is checked. The tuple-to-list asymmetry is carried into the neighbour sweep so a
# future consumer that does store these records is not surprised by it.
import json  # noqa: E402
for m in FOUR:
    rec = rec_of(m)
    try:
        back = json.loads(json.dumps(rec))
    except (TypeError, ValueError) as exc:
        back = None
        check(f"{m}'s record is serialisable at all", False, str(exc))
    if back is None:
        continue
    check(f"{m}'s record is serialisable", True)
    check(f"{m}'s record keeps every field across a serialisation boundary",
          set(back) == set(rec), f"{sorted(back)} vs {sorted(rec)}")
    check(f"{m}'s record keeps every field's contents across a serialisation boundary",
          all(list(back[k]) == list(rec[k]) if isinstance(rec[k], (list, tuple))
              else back[k] == rec[k] for k in rec),
          str(back))


print("")
if _fail:
    print("FAILURES:")
    for f in _fail:
        print("  -", f)
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
