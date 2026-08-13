"""
RUN 20 CYCLE 3, COMMIT A: THE FRAMEWORK-LEVEL LINEAGE MODEL, AND THE PROPERTY IT EXISTS FOR.

THE REQUIRED PROPERTY, stated once so every check below can be read against it: ADDING A
SAME-LINEAGE COPY OR DERIVED TRANSFORMATION MUST NOT CREATE NEW INDEPENDENT CORROBORATION. Not
that the number is unchanged in general -- that a same-lineage addition may not INCREASE
evidential strength, and may not turn a body of evidence into two.

THE VACUOUS-GUARD LESSON, APPLIED HERE, because cycle 1 built a guard that could not fail. Every
expected partition below is written out BY HAND as an explicit list of module-id sets. None of
them is obtained by calling `lineage.partition`, `lineage._linked`, or anything else in the file
under test. Every frozen pre-fix number is a literal measured before the change and never
recomputed. And the suite carries POSITIVE CONTROLS: genuinely independent bodies of evidence
MUST still corroborate and MUST still raise the mass, so a change that simply made every
combination inert would fail this file rather than pass it.
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import fusion, lineage  # noqa: E402

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


def mass_on(result, band):
    return None if result is None else result["mass"][band]


def sig(rec, status):
    return {"status": status, "lineage": rec, "module_id": rec["module_id"]}


# =============================================================== 1. THE VOCABULARY IS COMPLETE
# The nine classes the supervisory clarification names, each required to exist by name. A tenth
# invented class would not fail here; a missing one would, which is the direction that matters.
REQUIRED_CLASSES = ("INDEPENDENT", "SAME_SOURCE", "DERIVED", "SAME_SOURCE_TRANSFORM",
                    "CORRELATED", "SYNTHESIZED", "QUALITY_METADATA", "GOVERNANCE_OUTPUT",
                    "DECISION_OUTPUT")
for cls in REQUIRED_CLASSES:
    check(f"the evidence relationship {cls} exists in production and carries its own name",
          getattr(lineage, cls, None) == cls)
check("and the vocabulary contains exactly those nine and nothing undeclared",
      set(lineage.EVIDENCE_RELATIONSHIPS) == set(REQUIRED_CLASSES),
      str(sorted(set(lineage.EVIDENCE_RELATIONSHIPS) ^ set(REQUIRED_CLASSES))))

# An unrecognised relationship must RAISE rather than default. A silent default to INDEPENDENT
# is the single mistake that would reintroduce the whole defect.
try:
    lineage.lineage_record("X", evidence_relationship="PROBABLY_FINE")
    check("an unrecognised evidence relationship is refused rather than defaulted", False)
except lineage.LineageError:
    check("an unrecognised evidence relationship is refused rather than defaulted", True)

# ==================================================== 2. EVERY SIGNAL RETAINS THE NAMED FIELDS
REQUIRED_FIELDS = ("module_id", "source_fact_ids", "source_document_ids", "dependency_ids",
                   "lineage_group_ids", "evidence_relationship", "derivation_chain")
for mid, rec in sorted(lineage.MODULE_LINEAGE.items()):
    check(f"the declared lineage of {mid} carries every required field",
          all(f in rec for f in REQUIRED_FIELDS),
          str(sorted(set(REQUIRED_FIELDS) - set(rec))))

# THE DERIVATION CHAIN, NOT ONLY THE FINAL MODULE ID. A derived or transformed signal whose chain
# is a single step has not retained a chain at all.
# RUN 20 CYCLE 5 CORRECTED THIS LIST, AND THE SUPERSEDED READING IS RECORDED WHERE IT CHANGED.
# A2.1 was in this list. It is no longer declared at all: cycle 5 established that A2.1 is PERT
# Network Criticality, not earned schedule, and that it abstains with the reason code
# canonical_structure_absent on every project this platform holds, so it emits no signal whose
# evidence there is anything to declare. This suite CRASHED with a KeyError when the entry was
# removed, rather than failing, which is the failure mode this programme has now recorded twelve
# times; the lookup goes through .get and a missing declaration is a named red.
for mid in ("A1.7", "A1.8", "A1.1", "A3.5", "PH.5"):
    rec = lineage.MODULE_LINEAGE.get(mid)
    check(f"{mid} is declared at all", rec is not None)
    check(f"{mid} retains its derivation chain rather than only its module id",
          rec is not None and len(rec["derivation_chain"]) >= 2,
          str(rec["derivation_chain"]) if rec else "no declaration")
check("A2.1 is NOT declared, because it abstains on an absent canonical structure on every "
      "project and so emits no signal whose evidence there is anything to declare",
      "A2.1" not in lineage.MODULE_LINEAGE)

# The two voters specifically, hand-read against specification 1.7 and 1.8. The to-complete index
# reaches the earned value directly; the variance at completion reaches it through the cost
# performance index. Both rest on the same three governed facts, and the chains show it.
check("the to-complete performance index declares the budget, the earned value and the actual "
      "cost as the facts it rests on",
      set(lineage.MODULE_LINEAGE["A1.7"]["source_fact_ids"]) == {"bac", "ev", "ac"})
check("the variance at completion declares the SAME three facts, because the cost performance "
      "index it reads is the earned value over the actual cost and is not itself a fact",
      set(lineage.MODULE_LINEAGE["A1.8"]["source_fact_ids"]) == {"bac", "ev", "ac"})
check("and its chain records that it reaches them through the cost performance index and the "
      "estimate at completion, which is what makes the dependence checkable by a reader",
      any("cost performance index" in s for s in lineage.MODULE_LINEAGE["A1.8"]["derivation_chain"])
      and any("estimate at completion" in s
              for s in lineage.MODULE_LINEAGE["A1.8"]["derivation_chain"]))
for mid in ("A1.7", "A1.8"):
    check(f"{mid} declares itself a same-source transform rather than an independent source",
          lineage.MODULE_LINEAGE[mid]["evidence_relationship"] == lineage.SAME_SOURCE_TRANSFORM)

# ============================================ 3. THE PARTITION, AGAINST HAND-WORKED EXPECTATIONS
#
# Each case names the records, and then names the partition A HUMAN WORKED OUT from the three
# rules, written as sets of module ids. Nothing here asks the implementation what it thinks.

IND_1 = lineage.lineage_record("IND1", source_fact_ids=("safety_incidents",))
IND_2 = lineage.lineage_record("IND2", source_fact_ids=("permit_status",))
DOCS = lineage.lineage_record("DOC1", source_fact_ids=("document_risk",),
                              lineage_group_ids=(lineage.DOCUMENT_BODY,))

PARTITION_CASES = [
    ("two signals sharing no fact and no group are two bodies of evidence",
     [IND_1, IND_2], [{"IND1"}, {"IND2"}]),
    ("the two voting modules share all three earned-value facts and are ONE body",
     [lineage.MODULE_LINEAGE["A1.7"], lineage.MODULE_LINEAGE["A1.8"]], [{"A1.7", "A1.8"}]),
    # RUN 20 CYCLE 5. SUPERSEDED READINGS RECORDED WHERE THEY CHANGED. This case read "the cost
    # performance index joins them, because its two facts are a subset of theirs". A1.1 is NOT
    # the cost performance index: it is Monte Carlo EAC, and it joins the same body for a
    # different and larger reason, that it forecasts the estimate at completion from the same
    # earned-value facts. The grouping is unchanged; only the false description of it is.
    ("Monte Carlo EAC joins the two voters, because it forecasts the same earned-value body",
     [lineage.MODULE_LINEAGE["A1.7"], lineage.MODULE_LINEAGE["A1.8"],
      lineage.MODULE_LINEAGE["A1.1"]], [{"A1.7", "A1.8", "A1.1"}]),
    # And this case read "the earned schedule shares the earned value and joins the same body",
    # driven from A2.1, which is PERT Network Criticality and not earned schedule, and which
    # cycle 5 removed from the table because it emits no signal on any project. The PROPERTY the
    # case was measuring is real and is kept, driven from a hand-written record rather than from
    # a module id that never carried the method: a signal sharing one earned-value fact joins the
    # body. Deleting the case would have lost the property with the misdescription.
    ("a signal sharing the earned value joins the earned-value body",
     [lineage.MODULE_LINEAGE["A1.7"],
      lineage.lineage_record("ES", source_fact_ids=("ev", "pv"),
                             evidence_relationship=lineage.SAME_SOURCE_TRANSFORM,
                             derivation_chain=("pv,ev", "earned schedule"))],
     [{"A1.7", "ES"}]),
    ("the portfolio-health synthesis shares NO raw fact with its constituents and is still "
     "joined to them, by the dependency ids rule, which is why that rule exists",
     [lineage.MODULE_LINEAGE["A1.7"], lineage.MODULE_LINEAGE["PH.5"]], [{"A1.7", "PH.5"}]),
    ("a document-evidence signal is a body of its own beside the earned-value body",
     [lineage.MODULE_LINEAGE["A1.7"], DOCS], [{"A1.7"}, {"DOC1"}]),
    ("dependence is transitive: two signals with no shared fact are one body when a third "
     "shares a fact with each",
     [lineage.lineage_record("T1", source_fact_ids=("f1",)),
      lineage.lineage_record("T2", source_fact_ids=("f2",)),
      lineage.lineage_record("T3", source_fact_ids=("f1", "f2"))], [{"T1", "T2", "T3"}]),
    ("a signal that DECLARES itself independent while resting on the same governed facts is "
     "grouped anyway, because a claim is not evidence",
     [lineage.lineage_record("HONEST", source_fact_ids=("ev", "ac"),
                             evidence_relationship=lineage.SAME_SOURCE_TRANSFORM),
      lineage.lineage_record("CLAIMANT", source_fact_ids=("ev", "ac"),
                             evidence_relationship=lineage.INDEPENDENT)],
     [{"HONEST", "CLAIMANT"}]),
    ("and a declared shared group binds two signals that share no fact at all, which is the "
     "case a fact list cannot express",
     [lineage.lineage_record("G1", lineage_group_ids=("BODY",)),
      lineage.lineage_record("G2", lineage_group_ids=("BODY",))], [{"G1", "G2"}]),
]

for name, recs, expected in PARTITION_CASES:
    got = [{recs[i]["module_id"] for i in g} for g in lineage.partition(recs)]
    check("partition: " + name,
          sorted(map(sorted, got)) == sorted(map(sorted, expected)),
          f"got {got}, hand-worked expectation {expected}")

# =============================== 4. THE EIGHT CASES THE SUPERVISORY CLARIFICATION NAMES, A TO H
#
# Each case fuses a baseline and then fuses the baseline PLUS one added signal, and requires that
# the evidential strength on the resulting band did not rise and that no second body of evidence
# appeared. The baseline is a single Amber earned-value signal, whose mass on Amber is 0.7000.

BASE = sig(lineage.MODULE_LINEAGE["A1.7"], "Amber")
base_result = fusion.fuse_signals([BASE])
near("the baseline is one Amber body of evidence carrying mass 0.7000 on Amber",
     mass_on(base_result, "Amber"), 0.7000)
check("and it is exactly one body of evidence", base_result["lineage_groups"] == 1)

CASE_ADDITIONS = [
    ("A", "an EXACT DUPLICATE of the signal already present",
     sig(lineage.MODULE_LINEAGE["A1.7"], "Amber"), False),
    ("B", "an ALGEBRAIC TRANSFORM of the same facts, declared as a distinct module",
     sig(lineage.lineage_record("XFORM", source_fact_ids=("bac", "ev", "ac"),
                                evidence_relationship=lineage.SAME_SOURCE_TRANSFORM,
                                derivation_chain=("bac,ev,ac", "1 / to-complete index")),
         "Amber"), False),
    ("C", "a DERIVED METRIC reaching the same facts through another ratio",
     sig(lineage.MODULE_LINEAGE["A1.8"], "Amber"), False),
    ("D", "a SECOND METHOD over the same raw facts",
     sig(lineage.MODULE_LINEAGE["A1.1"], "Amber"), False),
    ("E", "a SYNTHESIS of the signal, reused as evidence",
     sig(lineage.lineage_record("SYNTH", dependency_ids=("A1.7",),
                                evidence_relationship=lineage.SYNTHESIZED,
                                derivation_chain=("A1.7", "roll-up")), "Amber"), False),
    ("F", "a QUALITY result reused as project-risk evidence",
     sig(lineage.lineage_record("C9.1", evidence_relationship=lineage.QUALITY_METADATA),
         "Amber"), True),
    ("G", "a GOVERNANCE output fed back as evidence",
     sig(lineage.lineage_record("B2.1", evidence_relationship=lineage.GOVERNANCE_OUTPUT),
         "Amber"), True),
    ("H", "a DECISION output fed back as evidence",
     sig(lineage.lineage_record("DEC.1", evidence_relationship=lineage.DECISION_OUTPUT),
         "Amber"), True),
]

for letter, what, added, expect_excluded in CASE_ADDITIONS:
    got = fusion.fuse_signals([BASE, added])
    near(f"case {letter}: adding {what} leaves the mass on Amber at 0.7000, unchanged",
         mass_on(got, "Amber"), 0.7000)
    check(f"case {letter}: and it does not raise the mass above the single-body baseline",
          mass_on(got, "Amber") <= mass_on(base_result, "Amber") + 1e-12)
    check(f"case {letter}: and it does not create a second body of evidence",
          got["lineage_groups"] == 1, f'groups={got["lineage_groups"]}')
    check(f"case {letter}: and the fused band is unchanged", got["status"] == base_result["status"])
    if expect_excluded:
        check(f"case {letter}: the added signal is not project-condition evidence at all and is "
              f"excluded by name rather than being grouped into the body",
              [e["module_id"] for e in got["excluded_non_evidential"]]
              == [added["module_id"]], str(got["excluded_non_evidential"]))
    else:
        check(f"case {letter}: the added signal joins the existing body and is named in it",
              added["module_id"] in got["lineage_bodies"][0]["member_module_ids"])

# ANTI-FEEDBACK, STATED AS ITS OWN PROPOSITION rather than only as a side effect of cases F to H:
# a quality, governance or decision output must not be able to move the band even when it
# disagrees maximally with the project evidence, in EITHER direction.
for rel, mid in ((lineage.QUALITY_METADATA, "C9.1"),
                 (lineage.GOVERNANCE_OUTPUT, "B2.1"),
                 (lineage.DECISION_OUTPUT, "DEC.1")):
    for contrary in ("Green", "Red"):
        got = fusion.fuse_signals(
            [BASE, sig(lineage.lineage_record(mid, evidence_relationship=rel), contrary)])
        check(f"anti-feedback: a {rel} signal reading {contrary} cannot move an Amber project "
              f"band in either direction",
              got["status"] == "Amber" and abs(mass_on(got, "Amber") - 0.7000) < 5e-5,
              f'{got["status"]} {mass_on(got, "Amber")}')

# ================================================== 5. POSITIVE CONTROLS: THE SUITE CAN STILL FAIL
#
# If the change had simply made every combination inert, every check above would still pass and
# this file would be worthless. Genuinely independent bodies of evidence MUST still corroborate.
indep = fusion.fuse_signals([BASE, sig(IND_1, "Amber")])
near("POSITIVE CONTROL: two GENUINELY INDEPENDENT Amber bodies still corroborate to 0.9273, the "
     "same number the pre-fix rule produced, because independent corroboration is legitimate and "
     "the correction is about lineage and never about the arithmetic",
     mass_on(indep, "Amber"), 0.9273)
check("POSITIVE CONTROL: and they are counted as two bodies of evidence",
      indep["lineage_groups"] == 2)
check("POSITIVE CONTROL: and their conflict coefficient is estimable, where a single body's is not",
      indep["conflict_estimable"] is True
      and fusion.fuse_signals([BASE])["conflict_estimable"] is False)
three = fusion.fuse_signals([BASE, sig(IND_1, "Amber"), sig(IND_2, "Amber")])
check("POSITIVE CONTROL: a third independent body strengthens further still",
      mass_on(three, "Amber") > mass_on(indep, "Amber"))

# The conservative reading WITHIN a body, stated as its own proposition. One body of evidence
# read two ways that disagree takes the more adverse reading, and the disagreement is recorded
# rather than scored away.
mixed = fusion.fuse_signals([sig(lineage.MODULE_LINEAGE["A1.7"], "Green"),
                             sig(lineage.MODULE_LINEAGE["A1.8"], "Amber")])
check("one body of evidence read two ways that disagree takes the more adverse reading",
      mixed["status"] == "Amber" and mixed["lineage_groups"] == 1)
check("and the disagreement between the two readings is recorded rather than scored away",
      mixed["lineage_bodies"][0]["disagreement"] is True
      and sorted(mixed["lineage_bodies"][0]["member_bands"]) == ["Amber", "Green"])
check("while two readings that agree record no disagreement",
      fusion.fuse_signals([sig(lineage.MODULE_LINEAGE["A1.7"], "Green"),
                           sig(lineage.MODULE_LINEAGE["A1.8"], "Green")]
                          )["lineage_bodies"][0]["disagreement"] is False)

# Idempotence, as a property over every band rather than one worked example.
for band in fusion.BANDS:
    one = fusion.fuse_signals([sig(lineage.MODULE_LINEAGE["A1.7"], band)])
    for copies in (2, 3, 5):
        many = fusion.fuse_signals(
            [sig(lineage.MODULE_LINEAGE["A1.7"], band) for _ in range(copies)])
        check(f"idempotence: {copies} copies of one {band} body of evidence carry exactly the "
              f"mass of one",
              abs(many["mass"][band] - one["mass"][band]) < 1e-12
              and many["status"] == one["status"],
              f'{many["mass"][band]} vs {one["mass"][band]}')

# Abstention and unknown strings, specification 22 points 6, 7 and 8, re-proved on the new path.
check("a signal with no recognised status contributes nothing and does not become a body",
      fusion.fuse_signals([BASE, sig(IND_1, "not-a-status")])["lineage_groups"] == 1)
check("missing evidence cannot silently become Green: every signal abstaining fuses to nothing",
      fusion.fuse_signals([sig(IND_1, None), sig(IND_2, "")]) is None)
check("an unknown status string cannot become favourable evidence",
      fusion.fuse_signals([sig(IND_1, "probably ok")]) is None)

# The undeclared-lineage flag, which is what lets a caller refuse to fuse on an assumption.
check("a fusion over bare status strings reports that no lineage was declared for it",
      fusion.dst_fuse(["Amber", "Amber"])["lineage_declared"] is False)
check("and a fusion over declared signals reports that lineage WAS declared",
      fusion.fuse_signals([BASE, sig(IND_1, "Amber")])["lineage_declared"] is True)

# ============================ 6. THE FROZEN PRE-FIX MEASUREMENTS, AS LITERALS, NEVER RECOMPUTED
#
# Measured on f59a38e before any of this existed and written here by hand. They are retained
# because the supervisory clarification asks for the before and after side by side, and because
# a baseline the code can regenerate is not a baseline.
PRE_FIX = {"Amber_single": 0.7000, "Amber_duplicated": 0.9273,
           "Green_single": 0.8000, "Green_duplicated": 0.9722,
           "Red_single": 0.8340, "Red_duplicated": 0.9787,
           "self_conflict": 0.4414}
for band in ("Amber", "Green", "Red"):
    one = fusion.fuse_signals([sig(lineage.MODULE_LINEAGE["A1.7"], band)])
    dup = fusion.fuse_signals([sig(lineage.MODULE_LINEAGE["A1.7"], band),
                               sig(lineage.MODULE_LINEAGE["A1.8"], band)])
    near(f"the single {band} body still carries the value it always did, {PRE_FIX[band+'_single']}",
         one["mass"][band], PRE_FIX[band + "_single"])
    check(f"and the same-lineage pair no longer reaches the frozen pre-fix "
          f"{PRE_FIX[band + '_duplicated']}: it now carries {PRE_FIX[band + '_single']}",
          abs(dup["mass"][band] - PRE_FIX[band + "_single"]) < 5e-5
          and dup["mass"][band] < PRE_FIX[band + "_duplicated"] - 0.05,
          f'{dup["mass"][band]}')
dup_pair = fusion.fuse_signals([sig(lineage.MODULE_LINEAGE["A1.7"], "Amber"),
                                sig(lineage.MODULE_LINEAGE["A1.8"], "Amber")])
check("and the conflict coefficient a body of evidence reported against its own copy, frozen at "
      "0.4414, is gone: one body cannot disagree with itself and none is now estimated",
      dup_pair["conflict"] == 0.0 and dup_pair["conflict_estimable"] is False)

if _fail:
    print(f"\n{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
