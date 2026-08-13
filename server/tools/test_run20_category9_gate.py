"""
RUN 20 CYCLE 3, COMMIT C: THE CATEGORY-9 OPERATIONAL QUALIFICATION GATE.

WHAT MAKES THIS A GATE AND NOT A FIELD. The supervisory clarification states the failure
condition in terms: a field saying qualification = unqualified while downstream code still
consumes the numerical value normally is FAIL. So every condition below is tested twice: once on
the VERDICT, which is what the gate says, and once on the EXECUTION, which is whether the number
is still reachable and whether the signal still votes. A verdict with no execution consequence
fails this file.

THE NINE CONDITIONS AND THEIR CONTRACTED OUTCOMES, each with the reason it is that outcome and
not a neighbouring one:

  missing required evidence      ABSTAINED  nothing can be computed, so there is no value
  stale evidence                 DEGRADED   a value exists, is shown, and may not move a status
  missing provenance             DEGRADED   untraceable to an artefact, usable, may not vote
  conflicting source evidence    REJECTED   two records disagree on one governed fact and no
                                            revision lineage exists to choose between them
  incomplete audit chain         REJECTED   a critical field is noncompensatory, specification 9.4
  invalid or out-of-domain value REJECTED   a value exists and must not be used
  duplicate lineage              ALLOWED    the evidence is fine; it is simply not a second
                                            source, which the lineage partition handles and the
                                            gate must NOT double-punish by also degrading it
  derived or synthesized         ALLOWED as a reading of its own body, and never as independent
                                            corroboration
  raw bypass attempt             REJECTED   refused with an exception, so a bypass cannot be
                                            mistaken for an abstention

THE VACUOUS-GUARD LESSON. Every expected verdict below is a literal written by hand against the
contract above. None is computed by calling the gate. The severity ordering the gate uses is
never consulted by this file. And the suite carries a positive control: a clean package must
reach ALLOWED and must vote, so a gate that simply rejected everything would fail here.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import fusion, lineage  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.qualification_gate import (  # noqa: E402
    ABSTAINED,
    ALLOWED,
    CRITICAL_AUDIT_FIELDS,
    DEGRADED,
    REJECTED,
    QualifiedSignal,
    RawBypassError,
    fuse_qualified,
    preflight,
    qualify,
)

_passed = 0
_total = 0
_fail: list[str] = []
CUTOFF = datetime.date(2026, 1, 31)
FRESHNESS = {"cost_ledger": 30, "narrative": 90}


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(name + (f" -- {detail}" if detail else ""))


REQUIRED = ("bac", "ev", "ac")


def clean_package(**over):
    pkg = {
        "bac": 1000.0, "ev": 500.0, "ac": 550.0,
        "_provenance": {"bac": "DOC-1 rev B", "ev": "DOC-2 rev A", "ac": "DOC-2 rev A"},
        "_as_of": {f: datetime.date(2026, 1, 20) for f in REQUIRED},
        "_source_class": {f: "cost_ledger" for f in REQUIRED},
        "_audit": {"method_version": "evm-1", "evidence_id": "EV-9", "recorded_at": "2026-01-21",
                   "reviewer_note": "optional", "attachment_count": 3},
        "_domain": {"bac": (0.0, None), "ev": (0.0, None), "ac": (0.0, None)},
    }
    pkg.update(over)
    return pkg


def verdict_of(pkg):
    return preflight(pkg, REQUIRED, CUTOFF, FRESHNESS)["verdict"]


def gated(pkg, band="Amber", relationship=None, module_id="A1.7"):
    rec = (lineage.lineage_record(module_id, evidence_relationship=relationship)
           if relationship else lineage.MODULE_LINEAGE.get(module_id))
    return qualify(module_id, band, 1.234, preflight(pkg, REQUIRED, CUTOFF, FRESHNESS),
                   lineage=rec)


# ============================================== POSITIVE CONTROL: A CLEAN PACKAGE MUST GET THROUGH
clean = gated(clean_package())
check("POSITIVE CONTROL: a package declaring provenance, as-of dates inside its source class's "
      "freshness requirement, a complete audit record and in-domain values is ALLOWED",
      clean.verdict == ALLOWED, f"{clean.verdict} {clean.reasons}")
check("POSITIVE CONTROL: and it may vote, and its band and its value are both readable",
      clean.may_vote is True and clean.band == "Amber" and clean.value == 1.234)

# ====================================================================== 1. MISSING REQUIRED EVIDENCE
pkg = clean_package()
del pkg["ev"]
sig = qualify("A1.7", None, None, preflight(pkg, REQUIRED, CUTOFF, FRESHNESS),
              lineage=lineage.MODULE_LINEAGE["A1.7"], module_abstained=True)
check("condition 1, missing required evidence: the verdict is ABSTAINED", sig.verdict == ABSTAINED)
check("condition 1, EXECUTION: it casts no vote and offers no band",
      sig.may_vote is False and sig.band is None)
check("condition 1: and the reason names the field that was absent, so an abstention is not a "
      "bare refusal", any("ev" in r for r in sig.reasons), str(sig.reasons))
check("condition 1: zero is a value and is not missing, which specification 9.1 states directly",
      verdict_of(clean_package(ev=0.0)) == ALLOWED)

# ================================================================================ 2. STALE EVIDENCE
stale = clean_package(_as_of={"bac": datetime.date(2026, 1, 20),
                              "ev": datetime.date(2025, 12, 1),
                              "ac": datetime.date(2026, 1, 20)})
sig = gated(stale)
check("condition 2, stale evidence: the earned value is 61 days old against a 30 day "
      "requirement for its source class, and the verdict is DEGRADED", sig.verdict == DEGRADED,
      f"{sig.verdict} {sig.reasons}")
check("condition 2, EXECUTION: the band and the value remain readable, because the finding is "
      "still shown on the ledger", sig.band == "Amber" and sig.value == 1.234)
check("condition 2, EXECUTION: and it MAY NOT VOTE, which is the difference between this gate "
      "and a field", sig.may_vote is False)
check("condition 2: a record inside its requirement is not stale, so the rule is not a blanket "
      "refusal", verdict_of(clean_package()) == ALLOWED)
check("condition 2: freshness is per source class and never one universal age, so the same age "
      "under a 90 day class is not stale",
      verdict_of(clean_package(_as_of={f: datetime.date(2025, 12, 1) for f in REQUIRED},
                               _source_class={f: "narrative" for f in REQUIRED})) == ALLOWED)
check("condition 2: a record dated AFTER the period cutoff is not a freshness state but a "
      "malformed one, and is REJECTED rather than degraded",
      verdict_of(clean_package(_as_of={f: datetime.date(2026, 3, 1) for f in REQUIRED}))
      == REJECTED)
check("condition 2: a package declaring no as-of dates has no staleness claimed against it, "
      "because none can be measured and asserting one would be a fabrication",
      verdict_of({f: clean_package()[f] for f in REQUIRED}) == ALLOWED)

# =========================================================================== 3. MISSING PROVENANCE
sig = gated(clean_package(_provenance={"bac": "DOC-1 rev B", "ac": "DOC-2 rev A"}))
check("condition 3, missing provenance: a package that claims provenance and omits a field is "
      "DEGRADED", sig.verdict == DEGRADED, f"{sig.verdict} {sig.reasons}")
check("condition 3, EXECUTION: the value stays readable and the signal may not vote",
      sig.value == 1.234 and sig.may_vote is False)
check("condition 3: and a package that claims no provenance at all is not degraded for a "
      "capability this repository has never had, which would stop all voting as a side effect "
      "and assert a capability rather than enforce a contract",
      verdict_of({f: clean_package()[f] for f in REQUIRED}) == ALLOWED)

# ================================================================= 4. CONFLICTING SOURCE EVIDENCE
sig = gated(clean_package(_conflicts={"bac": [1000.0, 1250.0]}))
check("condition 4, conflicting source evidence: two source records disagree on one governed "
      "fact and the verdict is REJECTED", sig.verdict == REJECTED, f"{sig.verdict} {sig.reasons}")
check("condition 4, EXECUTION: the band and the value are BOTH unreadable, which is the "
      "difference between rejected and degraded",
      sig.band is None and sig.value is None and sig.may_vote is False)
check("condition 4: the reason states that no revision lineage exists to resolve them, rather "
      "than implying the platform chose",
      any("revision lineage" in r for r in sig.reasons), str(sig.reasons))
check("condition 4: two source records that AGREE are not a conflict",
      verdict_of(clean_package(_conflicts={"bac": [1000.0, 1000.0]})) == ALLOWED)
check("condition 4: and the rejected signal is still reportable as rejected, because an audit "
      "trail must say what was refused",
      sig.report()["qualification"] == REJECTED and sig.report()["band"] is None)

# =================================================================== 5. INCOMPLETE AUDIT CHAIN
for field in CRITICAL_AUDIT_FIELDS:
    audit = dict(clean_package()["_audit"])
    del audit[field]
    sig = gated(clean_package(_audit=audit))
    check(f"condition 5, incomplete audit chain: the critical field {field} is absent and the "
          f"verdict is REJECTED", sig.verdict == REJECTED, f"{sig.verdict}")
    check(f"condition 5, EXECUTION: with {field} absent the value is unreachable",
          sig.value is None and sig.may_vote is False)
check("condition 5: critical fields are NONCOMPENSATORY, so adding many optional fields to a "
      "record missing a critical one does not average the gap away",
      gated(clean_package(_audit={"evidence_id": "EV-9", "recorded_at": "2026-01-21",
                                  "note_a": 1, "note_b": 2, "note_c": 3, "note_d": 4,
                                  "note_e": 5, "note_f": 6})).verdict == REJECTED)
check("condition 5: a record missing only an OPTIONAL field is not rejected",
      gated(clean_package(_audit={"method_version": "evm-1", "evidence_id": "EV-9",
                                  "recorded_at": "2026-01-21"})).verdict == ALLOWED)

# ============================================================ 6. INVALID OR OUT-OF-DOMAIN VALUE
sig = gated(clean_package(ac=-550.0))
check("condition 6, out-of-domain value: an actual cost below zero is outside its declared "
      "domain and the verdict is REJECTED", sig.verdict == REJECTED, f"{sig.verdict}")
check("condition 6, EXECUTION: the value is unreachable and no vote is cast",
      sig.value is None and sig.may_vote is False)
check("condition 6: a value at the inclusive boundary of its domain is inside it",
      verdict_of(clean_package(ac=0.0)) == ALLOWED)
check("condition 6: a field with no declared domain has none enforced against it, because an "
      "undeclared bound is not a bound",
      verdict_of(clean_package(ac=-550.0, _domain={})) == ALLOWED)

# ======================================================================== 7. DUPLICATE LINEAGE
dup_a = gated(clean_package(), band="Amber", module_id="A1.7")
dup_b = gated(clean_package(), band="Amber", module_id="A1.8")
check("condition 7, duplicate lineage: the evidence itself is sound, so the gate's verdict is "
      "ALLOWED and it does NOT double-punish a signal the lineage partition already handles",
      dup_a.verdict == ALLOWED and dup_b.verdict == ALLOWED)
check("condition 7, EXECUTION: both may vote, and the combination still counts them as ONE body "
      "of evidence carrying the confidence of one",
      dup_a.may_vote and dup_b.may_vote
      and fusion.fuse_signals(fuse_qualified([dup_a, dup_b]))["lineage_groups"] == 1
      and abs(fusion.fuse_signals(fuse_qualified([dup_a, dup_b]))["mass"]["Amber"] - 0.7) < 5e-5)

# ============================================================= 8. DERIVED AND SYNTHESIZED EVIDENCE
derived = gated(clean_package(), band="Amber", relationship=lineage.DERIVED, module_id="D1")
synth = gated(clean_package(), band="Amber", relationship=lineage.SYNTHESIZED, module_id="S1")
check("condition 8, derived and synthesized evidence: both are ALLOWED, because being derived "
      "is a statement about independence and not about quality",
      derived.verdict == ALLOWED and synth.verdict == ALLOWED)
check("condition 8, EXECUTION: a synthesis of a signal already counted joins that signal's body "
      "of evidence and does not corroborate it",
      fusion.fuse_signals([dup_a.to_fusion_signal(),
                           {"status": "Amber", "module_id": "SY",
                            "lineage": lineage.lineage_record(
                                "SY", dependency_ids=("A1.7",),
                                evidence_relationship=lineage.SYNTHESIZED)}]
                          )["lineage_groups"] == 1)

# ======================================= 8b. THE THREE NON-EVIDENTIAL CLASSES, THE ANTI-FEEDBACK
for rel, mid in ((lineage.QUALITY_METADATA, "C9.1"),
                 (lineage.GOVERNANCE_OUTPUT, "B2.1"),
                 (lineage.DECISION_OUTPUT, "DEC.1")):
    sig = gated(clean_package(), band="Red", relationship=rel, module_id=mid)
    check(f"anti-feedback: a {rel} signal is REJECTED as project-condition evidence however "
          f"clean the evidence behind it is", sig.verdict == REJECTED, f"{sig.verdict}")
    check(f"anti-feedback, EXECUTION: its band and value are unreachable and it casts no vote",
          sig.band is None and sig.value is None and sig.may_vote is False)
    check(f"anti-feedback: and it cannot reach the combination even through the gate's own "
          f"converter, so Category 9 does not become another vote",
          fusion.fuse_signals(fuse_qualified([dup_a, sig]))["status"] == "Amber")

# ======================================================================= 9. RAW BYPASS ATTEMPT
for raw in ({"status": "Green", "module_id": "A1.7", "lineage": lineage.MODULE_LINEAGE["A1.7"]},
            "Green", None, 0.95):
    # The refusal must be the gate's OWN refusal. A mutation that deletes the guard leaves the
    # converter to fail with whatever the raw object happens not to support, and an incidental
    # AttributeError is not a refusal: it is an accident that would disappear the moment a caller
    # handed in an object that happened to have the right method. So any other exception, and no
    # exception at all, are both reds here, and both are named.
    try:
        fuse_qualified([dup_a, raw])
        outcome = "no refusal at all"
    except RawBypassError:
        outcome = "refused by the gate"
    except Exception as exc:  # noqa: BLE001 - the point is that anything else is wrong
        outcome = f"failed incidentally with {exc.__class__.__name__}"
    check(f"condition 9, raw bypass: a hand-built {type(raw).__name__} is refused at the "
          f"combination BY THE GATE, not by accident", outcome == "refused by the gate", outcome)
check("condition 9: the refusal is an EXCEPTION and not a silent drop, so a bypass cannot be "
      "mistaken for an abstention, which is a legitimate state",
      issubclass(RawBypassError, RuntimeError))
check("condition 9: and a properly qualified signal passes through the same converter",
      fuse_qualified([dup_a])[0]["status"] == "Amber")

# THE VALUE CANNOT BE READ AROUND THE VERDICT. Not a matter of caller discipline: there is no
# attribute holding the usable number when the verdict refuses.
rejected = gated(clean_package(ac=-550.0))
check("a rejected signal exposes no attribute from which the usable band or value could be read "
      "by an ordinary consumer",
      rejected.band is None and rejected.value is None
      and rejected.to_fusion_signal()["status"] is None)
check("and the unqualified figures are kept only under names that say they are unqualified, for "
      "the audit trail",
      rejected.unqualified_band == "Amber" and rejected.unqualified_value == 1.234)
try:
    QualifiedSignal("X", "Green", 1.0, "PROBABLY_FINE")
    check("a verdict outside the vocabulary is refused rather than defaulted", False)
except Exception as exc:
    check("a verdict outside the vocabulary is refused rather than defaulted",
          exc.__class__.__name__ == "QualificationError", repr(exc))

# =========================================================== 10. THE LIVE PATH THROUGH THE GATE
SI = {"bac": 1000.0, "ev": 500.0, "ac": 550.0, "pv": 520.0, "cpi": 500 / 550, "spi": 500 / 520}
res = compute_project(dict(SI), "S", "P1", CUTOFF)
q = {r["module_id"]: r for r in res["signal_qualification"]}
check("the live path routes both voters through the gate and reports a verdict for each",
      set(q) == {"A1.7", "A1.8"}, str(sorted(q)))
check("and on a complete evidence package both are ALLOWED and both vote",
      all(q[m]["qualification"] == ALLOWED and q[m]["may_vote"] for m in ("A1.7", "A1.8")))
check("and the resulting status is the one the combination produced",
      res["category_statuses"]["A1"]["status"] == "Red")
res2 = compute_project({"bac": 1000.0}, "S", "P1", CUTOFF)
q2 = {r["module_id"]: r for r in res2["signal_qualification"]}
check("a package that lets neither voter run reports both as ABSTAINED through the gate rather "
      "than simply going quiet",
      all(q2[m]["qualification"] == ABSTAINED for m in ("A1.7", "A1.8")))
check("and no status is fused from nothing", res2["project_status"] is None)
check("the gate's version is carried on the result, so a stored row records which contract "
      "qualified it", bool(res["signal_qualification_version"]))

if _fail:
    print(f"\n{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
