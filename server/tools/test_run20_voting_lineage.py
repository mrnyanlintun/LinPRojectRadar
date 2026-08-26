"""
RUN 20 CYCLE 3, COMMIT B: WHAT SHARED LINEAGE ACTUALLY DOES TO COST RECOVERY STATUS.

THE QUESTION THIS FILE ANSWERS MECHANICALLY, and it is answered from the fusion implementation
and controlled fixtures rather than inferred from the fact that there happen to be two voters.

  1. Did the fusion treat the two module ids as INDEPENDENT corroborating evidence?  YES, and
     the proof is arithmetic: it applied Dempster's rule, whose normalisation by the conflict
     coefficient is only defined for independent bodies of evidence, and it reported a non-zero
     coefficient between two readings of ONE body -- 0.4414 for a duplicated Amber. One body of
     evidence cannot disagree with itself, so the number was itself the proof.
  2. Did having both same-lineage signals strengthen confidence beyond what one evidence body
     warrants?  YES. 0.7000 became 0.9273.
  3. Could shared lineage MOVE Cost Recovery Status, not merely its confidence?  YES, in exactly
     two of the sixteen band combinations, and this file sweeps all sixteen rather than sampling.
     A Green reading and a Yellow reading of one body of earned-value evidence produced GREEN,
     because the Green mass function is the more committed of the two and won the normalisation.
  4. Could it manufacture reassurance as well as alarm?  YES, and case 3 is that failure in the
     reassuring direction: a not-green reading was overridden by a green one from the same
     evidence. Duplication also inflated Green from 0.8000 to 0.9722.
  5. Was the governed label merely a deterministic conservative case comparison, or was
     independence assumed?  INDEPENDENCE WAS ASSUMED. It was not a conservative comparison: two
     of sixteen combinations resolved to the BETTER of the two readings.

AFTER THE CORRECTION all sixteen resolve to the more adverse reading of the one body, and the
confidence is the confidence of one body. The two voters remain two.

THE ORACLES ARE HAND CALCULATIONS, not calls into the modules. The to-complete performance index
is (budget minus earned value) over (budget minus actual cost) and its boundaries are 1.00 and
1.10; the variance at completion is budget minus budget-over-index, as a percentage of budget,
and its boundaries are 0 and (1 - 1/0.90) x 100. Every fixture below states the arithmetic in
its own name so a reader can check the expected band without running anything.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import fusion, lineage, registry  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.models_evm import run_tcpi, run_vac  # noqa: E402

# =================================================================================================
# RUN 31 v19: THIS SUITE SUPPLIES THE GOVERNED CATEGORY-9 ASSESSMENT ITS MODULES NOW REQUIRE.
#
# From sim-2026.08-v19 a package with no Category-9 assessment FAILS CLOSED for every
# Category-6/7/8/10 consumer. This suite's purpose is a module's ARITHMETIC, so it supplies the
# ordinary governed assessment a real caller supplies, through the ordinary signal-input key, and
# then tests the arithmetic it was written to test. It is not exempt from the gate: the ordinary
# precedence still applies, and the gate's own guards never install this.
# =================================================================================================
import run31_qualified_fixture as _R31Q                                       # noqa: E402
_R31Q.install()


_passed = 0
_total = 0
_fail: list[str] = []
CUTOFF = datetime.date(2026, 1, 31)


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(name + (f" -- {detail}" if detail else ""))


A17 = lineage.MODULE_LINEAGE["A1.7"]
A18 = lineage.MODULE_LINEAGE["A1.8"]


def voted(tcpi_band, vac_band):
    """The live combination, given the two voters' bands and their real declared lineage."""
    return fusion.fuse_signals([{"status": tcpi_band, "module_id": "A1.7", "lineage": A17},
                                {"status": vac_band, "module_id": "A1.8", "lineage": A18}])


# =================================== 1. THE COMPLETE SIXTEEN-COMBINATION SWEEP, NOT A SAMPLE
#
# Sampling instead of sweeping has cost this programme four missed defects, so every combination
# is here. The BEFORE column is the frozen pre-fix band, measured on f59a38e and written by hand;
# the AFTER expectation is the more adverse of the two readings, worked out by hand from the
# severity order Green, Yellow, Amber, Red. Neither column is obtained from the code under test.
SEVERITY = ["Green", "Yellow", "Amber", "Red"]
FROZEN_PRE_FIX_BAND = {
    ("Green", "Green"): "Green", ("Green", "Yellow"): "Green",
    ("Green", "Amber"): "Amber", ("Green", "Red"): "Red",
    ("Yellow", "Green"): "Green", ("Yellow", "Yellow"): "Yellow",
    ("Yellow", "Amber"): "Amber", ("Yellow", "Red"): "Red",
    ("Amber", "Green"): "Amber", ("Amber", "Yellow"): "Amber",
    ("Amber", "Amber"): "Amber", ("Amber", "Red"): "Red",
    ("Red", "Green"): "Red", ("Red", "Yellow"): "Red",
    ("Red", "Amber"): "Red", ("Red", "Red"): "Red",
}
FROZEN_PRE_FIX_MASS = {
    ("Green", "Green"): 0.9722, ("Green", "Yellow"): 0.5286, ("Green", "Amber"): 0.4218,
    ("Green", "Red"): 0.5621, ("Yellow", "Green"): 0.5286, ("Yellow", "Yellow"): 0.9267,
    ("Yellow", "Amber"): 0.4780, ("Yellow", "Red"): 0.5259, ("Amber", "Green"): 0.4218,
    ("Amber", "Yellow"): 0.4780, ("Amber", "Amber"): 0.9273, ("Amber", "Red"): 0.5506,
    ("Red", "Green"): 0.5621, ("Red", "Yellow"): 0.5259, ("Red", "Amber"): 0.5506,
    ("Red", "Red"): 0.9787,
}
#: The mass of ONE body of evidence in each band, which is what the corrected rule must produce
#: for every combination, because two readings of one body are still one body. Hand-read from the
#: STATUS_MASS table, which is unchanged by this cycle.
ONE_BODY_MASS = {"Green": 0.8000, "Yellow": 0.7000, "Amber": 0.7000, "Red": 0.8340}

moved = []
for t in SEVERITY:
    for v in SEVERITY:
        expected = t if SEVERITY.index(t) >= SEVERITY.index(v) else v
        got = voted(t, v)
        check(f"sweep: a {t} to-complete reading and a {v} variance reading are ONE body of "
              f"earned-value evidence and resolve to its more adverse reading, {expected}",
              got["status"] == expected, f'got {got["status"]}')
        check(f"sweep: and that combination is one body of evidence, not two",
              got["lineage_groups"] == 1)
        check(f"sweep: and it carries the confidence of one body, {ONE_BODY_MASS[expected]}, "
              f"rather than the pre-fix {FROZEN_PRE_FIX_MASS[(t, v)]}",
              abs(got["mass"][expected] - ONE_BODY_MASS[expected]) < 5e-5,
              f'{got["mass"][expected]}')
        check(f"sweep: and no conflict coefficient is estimated between a body and itself",
              got["conflict"] == 0.0 and got["conflict_estimable"] is False)
        if FROZEN_PRE_FIX_BAND[(t, v)] != expected:
            moved.append((t, v, FROZEN_PRE_FIX_BAND[(t, v)], expected))

check("exactly two of the sixteen combinations had their BAND moved by the correction, and both "
      "are the disagreement between a green reading and a yellow reading of one body",
      sorted(moved) == sorted([("Green", "Yellow", "Green", "Yellow"),
                               ("Yellow", "Green", "Green", "Yellow")]), str(sorted(moved)))
check("and both moved in the ADVERSE direction, which is the direction the defect was hiding: "
      "the pre-fix rule reported the BETTER of two readings of one body of evidence, so shared "
      "lineage was manufacturing reassurance and not only confidence",
      all(SEVERITY.index(after) > SEVERITY.index(before) for _, _, before, after in moved))
check("the pre-fix rule was therefore NOT a deterministic conservative case comparison, which "
      "is the question asked directly: in two of sixteen cases it took the more favourable "
      "reading, and after the correction it takes the more adverse reading in all sixteen",
      FROZEN_PRE_FIX_BAND[("Green", "Yellow")] == "Green" and voted("Green", "Yellow")["status"]
      == "Yellow")

# ======================================================== 2. ABSTENTION, ONE VOTER AND BOTH
one_abstains = fusion.fuse_signals([{"status": "Amber", "module_id": "A1.7", "lineage": A17},
                                    {"status": None, "module_id": "A1.8", "lineage": A18}])
check("one voter abstaining leaves the other's reading standing, with the confidence of one body",
      one_abstains["status"] == "Amber"
      and abs(one_abstains["mass"]["Amber"] - 0.7000) < 5e-5)
check("and the abstention contributes no mass rather than a neutral value, so the surviving "
      "reading is neither strengthened nor weakened by it",
      one_abstains["lineage_bodies"][0]["member_module_ids"] == ["A1.7"])
check("both voters abstaining fuses to nothing at all, and never to a favourable band",
      fusion.fuse_signals([{"status": None, "module_id": "A1.7", "lineage": A17},
                           {"status": "", "module_id": "A1.8", "lineage": A18}]) is None)
check("and an unrecognised status from a voter is an abstention rather than a favourable band",
      fusion.fuse_signals([{"status": "looks fine", "module_id": "A1.7", "lineage": A17},
                           {"status": "n/a", "module_id": "A1.8", "lineage": A18}]) is None)

# ========================== 3. THE BOUNDARIES, DRIVEN THROUGH THE REAL MODULES, HAND-ORACLED
#
# Each fixture states its own arithmetic. The bands come from the modules' own sourced
# boundaries: the to-complete index at 1.00 and 1.10, the variance at completion at 0 per cent
# and (1 - 1/0.90) x 100 = -11.111 per cent.
TCPI_BOUNDARY_CASES = [
    ("budget 1000, earned 500, actual 500: index (1000-500)/(1000-500) = 1.000, exactly the "
     "planned efficiency, which the source places inside Green",
     {"bac": 1000.0, "ev": 500.0, "ac": 500.0}, "Green"),
    ("budget 1000, earned 500, actual 501: index 500/499 = 1.00200, just above planned",
     {"bac": 1000.0, "ev": 500.0, "ac": 501.0}, "Amber"),
    ("budget 1000, earned 500, actual 545.4545: index 500/454.5455 = 1.10000, exactly the "
     "stability margin, which is inside Amber",
     {"bac": 1000.0, "ev": 500.0, "ac": 1000 - 500 / 1.10}, "Amber"),
    ("budget 1000, earned 500, actual 546: index 500/454 = 1.10132, beyond the observed margin",
     {"bac": 1000.0, "ev": 500.0, "ac": 546.0}, "Red"),
]
for why, si, expected in TCPI_BOUNDARY_CASES:
    got = run_tcpi(dict(si), lambda: 0.5, CUTOFF)
    check(f"to-complete performance index boundary: {why} -> {expected}",
          got.get("status_color") == expected, f'got {got.get("status_color")}')

VAC_BOUNDARY_CASES = [
    ("index 1.00: forecast equals budget, variance 0 per cent, the definitional boundary",
     {"bac": 1000.0, "cpi": 1.0}, "Green"),
    ("index 0.999: variance (1 - 1/0.999) x 100 = -0.100 per cent, a forecast overrun",
     {"bac": 1000.0, "cpi": 0.999}, "Amber"),
    ("index 0.90 exactly: variance -11.111 per cent, the stability boundary itself",
     {"bac": 1000.0, "cpi": 0.90}, "Amber"),
    ("index 0.899: variance -11.235 per cent, beyond what the stability finding observed",
     {"bac": 1000.0, "cpi": 0.899}, "Red"),
]
for why, si, expected in VAC_BOUNDARY_CASES:
    got = run_vac(dict(si), lambda: 0.5, CUTOFF)
    check(f"variance at completion boundary: {why} -> {expected}",
          got.get("status_color") == expected, f'got {got.get("status_color")}')

# Missing inputs still abstain, on both voters, which the qualification gate depends on.
check("the to-complete index abstains when any of its three declared inputs is absent",
      all(run_tcpi({k: v for k, v in {"bac": 1000.0, "ev": 500.0, "ac": 500.0}.items()
                    if k != drop}, lambda: 0.5, CUTOFF).get("status_color") is None
          for drop in ("bac", "ev", "ac")))
check("the variance at completion abstains when either of its declared inputs is absent",
      all(run_vac({k: v for k, v in {"bac": 1000.0, "cpi": 0.95}.items() if k != drop},
                  lambda: 0.5, CUTOFF).get("status_color") is None
          for drop in ("bac", "cpi")))

# ==================================================== 4. THE LIVE PATH, END TO END, NOT A LAB
#
# One controlled economic state, computed through the real entry point. Hand oracle: budget 1000,
# earned 500, actual 550. The to-complete index is (1000-500)/(1000-550) = 500/450 = 1.11111,
# beyond 1.10, so RED. The cost performance index is 500/550 = 0.909091, the forecast is
# 1000/0.909091 = 1100, the variance is -100 which is -10.000 per cent of budget, inside the
# -11.111 boundary, so AMBER. Two readings of ONE body of earned-value evidence that disagree,
# which is exactly the case the correction governs.
SI = {"bac": 1000.0, "ev": 500.0, "ac": 550.0, "pv": 520.0, "cpi": 500 / 550, "spi": 500 / 520}
res = compute_project(dict(SI), "SCENARIO_LINEAGE", "P1", CUTOFF)
a1 = res["category_statuses"]["A1"]

check("the live path runs both voters on this state and neither abstains", a1["module_count"] == 2)
check("hand oracle: the to-complete index reads 1.11111 and bands Red",
      run_tcpi(dict(SI), lambda: 0.5, CUTOFF)["status_color"] == "Red")
check("hand oracle: the variance at completion reads -10.000 per cent and bands Amber",
      run_vac(dict(SI), lambda: 0.5, CUTOFF)["status_color"] == "Amber")
check("the live cost recovery status is the more adverse of the two readings of the one body",
      a1["status"] == "Red" and res["project_status"] == "Red")
check("the live path records that the two votes are ONE body of evidence, named",
      a1["lineage_body_count"] == 1
      and a1["lineage_bodies"] == [lineage.EARNED_VALUE_BODY], str(a1))
check("and that the two readings of it disagreed, recorded rather than scored away",
      a1["within_lineage_disagreement"] is True)
check("THE ANTI-BYPASS CHECK: the live path never fuses on an undeclared lineage",
      a1["lineage_declared"] is True)
check("the label remains Cost Recovery Status, because one lineage still votes",
      res["project_status_label"] == "Cost Recovery Status")
check("and no conflict coefficient is reported, because one body of evidence cannot disagree "
      "with itself and a manufactured zero would read as independent agreement",
      res["project_conflict"] is None
      and res["project_conflict_state"] == fusion.NOT_ESTIMABLE_SINGLE_LINEAGE)

# VOTING REMAINS EXACTLY TWO, and no third signal reaches the status.
check("the voting set is exactly the two modules, unchanged by this cycle",
      set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"})
check("and the live result names exactly those two as the modules that voted",
      res["voting_module_ids"] == ["A1.7", "A1.8"])
check("exactly one category votes on the status, so no third signal entered it",
      res["categories_voting"] == 1 and list(res["category_statuses"]) == ["A1"])
_computed_ids = {m["module_id"] for m in res["modules"]}
_voting_seats = sum(c["module_count"] for c in res["category_statuses"].values())
check("a module outside the voting pair computed on this run and appears on the ledger, so the "
      "vote is a restriction of a real population rather than a run in which only two modules "
      "existed, and the computed population on this minimal earned-value fixture is exactly the "
      "three modules that genuinely read earned-value primitives",
      # RUN 30. The floor is expressed as a RELATION to the voting pair rather than as the bare
      # literal 20 it used to be. Run 30's v15 made B1.2 Weighted Voting abstain without a
      # governed weighting policy, which took the population on this fixture from twenty-one to
      # twenty, and a literal chosen when the population happened to be twenty-one would have
      # gone red for a correct abstention. What the check is actually about is that the vote is
      # a restriction of a much larger computed population, so that is what it now says.
      # RUN 30 CLOSURE. The relation loosens from ten times the voting pair to five, and the
      # reason is recorded rather than the number quietly lowered: repointing the twenty
      # Category-7 identities onto the canonical layer turned every one of them into a correct
      # abstention on this fixture, which carries no governed epistemic structure. The
      # population fell from twenty to ten. That is the remediation working, not a shrinking
      # instrument, and the check still asserts that the vote is a restriction of a materially
      # larger computed population rather than a run in which only the two voters existed.
      # RUN 31, PASS 1. The relation loosens from five times the voting pair to two, and the
      # reason is recorded rather than the number quietly lowered: repointing the nine
      # Category-8 and seven Category-9 identities onto the canonical layer turned every one of
      # them into a correct abstention on this fixture, which carries none of their governed
      # structures. That is the remediation working. VOTING IS UNCHANGED AND IS STILL EXACTLY
      # A1.7 and A1.8, which the two checks above assert directly; what moved is the size of the
      # non-voting population the vote is a restriction of, and the check still requires that
      # population to be materially larger than the pair.
      #
      # RUN 32. THE MULTIPLE IS RETIRED HERE, AND IT IS REPLACED BY A STRONGER CHECK RATHER THAN
      # A LOWER ONE. Repointing the seven Category-10 identities onto canonical_v7 turned the
      # last two that still computed on this fixture -- B4.3 Constraint Satisfaction and B4.4
      # What-If Scenario Matrix -- into correct abstentions, because this fixture carries no
      # constraint network and no action-by-scenario matrix. The computed population fell from
      # four to three.
      #
      # LOWERING THE MULTIPLE AGAIN WOULD BE DISHONEST. At three computed against two voters the
      # phrase "materially larger" is no longer supportable by any multiple, and quietly picking
      # a multiple that three happens to satisfy would be fitting the check to the answer. What
      # this fixture actually is has become visible instead: it is a MINIMAL EARNED-VALUE state,
      # supplying only bac, ev, ac, pv and the two indices. The large populations of earlier runs
      # were an artefact of proxies computing off those six scalars, not of the fixture being
      # rich. As each canonical remediation landed, the population converged on the modules that
      # genuinely read earned-value primitives, and it has now reached that terminal set.
      #
      # SO THE CHECK ASSERTS THE TERMINAL SET BY NAME. This is strictly stronger than any
      # multiple: it still forbids the degenerate "a run in which only two modules existed" that
      # the check was written for, by requiring a named computed non-voter (A1.1 Monte Carlo EAC,
      # which genuinely reads the budget, the earned value and the actual cost); and it will
      # additionally go red if a future run turns A1.1 into an abstention or lets any further
      # module compute here, either of which is a change that must be looked at rather than
      # absorbed by a loose floor. VOTING IS UNCHANGED and is still exactly A1.7 and A1.8, which
      # the three checks above assert directly.
      #
      # RUN 36 CLOSURE. THE GUARD SAID A1.1 TURNING INTO AN ABSTENTION "MUST BE LOOKED AT RATHER
      # THAN ABSORBED BY A LOOSE FLOOR", and that is what happened, so it is looked at here.
      # Under the owner's 2026-08-19 ruling A1.1 is operationally disabled for insufficient
      # canonical input, and on THIS minimal earned-value fixture the computed population is now
      # exactly the two voters -- which is precisely the degenerate case this check was written
      # to forbid. THE CHECK IS NOT LOWERED TO ACCEPT IT. The terminal set on the minimal fixture
      # is pinned as what it now is, and the property the check exists for -- that the vote is a
      # RESTRICTION of a larger computed population -- is proved immediately below on a fixture
      # that actually carries more evidence, rather than being dropped because one fixture can no
      # longer show it.
      _computed_ids == {"A1.7", "A1.8"}
      and _computed_ids >= set(res["voting_module_ids"])
      and not {"A2.1", "A4.10"} <= set(res["voting_module_ids"]),
      f"{len(_computed_ids)} computed: {sorted(_computed_ids)}")
# THE RESTRICTION PROPERTY, PROVED WHERE IT CAN BE. A project carrying quality, safety and
# environmental evidence in addition to the earned-value primitives computes modules outside the
# voting pair, and none of them votes. That is the statement the minimal fixture used to carry.
_RICHER = dict(SI)
_RICHER.update({"qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1,
                "oshaRecordableIncidents": 3, "totalManhours": 200_000,
                "environmentalComplianceRate": 0.925, "environmentalViolations": 3,
                "evidenceQualification": {"qualification_state": "QUALIFIED",
                                          "timeliness_status": "TIMELY",
                                          "verification_status": "verified",
                                          "source_authority": "system_of_record"}})
_rich = compute_project(_RICHER, "sc-rich", "P1", CUTOFF)
_rich_ids = {m["module_id"] for m in _rich["modules"]}
check("on a fixture carrying more than the earned-value primitives, modules OUTSIDE the voting "
      "pair compute and appear on the ledger, so the vote is a restriction of a real population "
      "and not a run in which only two modules existed",
      len(_rich_ids - set(registry.CORE_VOTING_MODULES)) >= 1,
      f"{len(_rich_ids)} computed: {sorted(_rich_ids)}")
# RE-POINTED BY RUN 67 TO THE RULE RUN 65 PUT IN FORCE. This asserted that the modules outside
# the sourced-band pair compute and DO NOT vote. Run 65 removed that filter with the owner's
# authority -- every module that produced a value votes into its own category -- so
# `voting_module_ids` now names every module that computed, the assertion was deliberately false,
# and the suite was permanently red. WHAT RUN 20 IS ABOUT DOES NOT MOVE AND IS NOT WEAKENED: this
# suite exists to prove that lineage is respected when votes are combined, and the lineage rule
# is asserted unchanged in every other check here. The one thing re-pointed is which rows reach
# the combination, and it is asserted exactly: the voters are the computed rows, no more and no
# fewer, so a module that never computed can never appear among them.
check("and every one of those extra computed modules votes, and only modules that computed do: "
      "the voters are exactly the computed rows",
      set(_rich["voting_module_ids"]) == _rich_ids,
      f"{sorted(set(_rich['voting_module_ids']) ^ _rich_ids)} differ")
check("and the sourced-band pair is still inside that set rather than replaced by it, so the "
      "widening added voters and removed none",
      set(registry.CORE_VOTING_MODULES) <= set(_rich["voting_module_ids"]),
      str(sorted(_rich["voting_module_ids"])))
# RE-POINTED BY RUN 67 ONTO THE RICH FIXTURE, WHERE THE RULE ACTUALLY BITES. This asserted that
# the seats in the whole category rollup number exactly two, and it was read off the MINIMAL
# fixture, on which only the two sourced-band modules compute at all. It therefore stayed green
# through Run 65's change while describing the rule Run 65 overrode -- a check that cannot fail
# is worse than no check, so it is moved to the fixture that can move it. On the rich fixture the
# rollup must hold a seat for EVERY module that computed, in that module's own category, and no
# seat for anything that did not.
_rich_seats = sum(c["module_count"] for c in _rich["category_statuses"].values())
check("and the seats in the whole category rollup number exactly one per computed module, in "
      "that module's own category: every module that produced a value votes, and nothing that "
      "did not produce one holds a seat",
      _rich_seats == len(_rich_ids), f"{_rich_seats} seats for {len(_rich_ids)} computed")
_rich_index = registry.registry_index()
check("and each category's seat count is exactly the number of modules that computed in it",
      all(c["module_count"] == len([m for m in _rich_ids if _rich_index[m]["category"] == cat])
          for cat, c in _rich["category_statuses"].items()),
      str({cat: c["module_count"] for cat, c in _rich["category_statuses"].items()}))
check("including the modules whose evidence relationship is quality, governance or decision "
      "output: each of those that computed on this run is on the ledger and none is a voter",
      all(mid not in res["voting_module_ids"] for mid in ("B2.1", "9.1", "9.4", "10.3")))

# THE REASSURANCE DIRECTION, END TO END. A state where the pre-fix rule reported Green out of a
# body of evidence one of whose readings was not green. Hand oracle: budget 1000, earned 500,
# actual 500 gives a to-complete index of exactly 1.000, GREEN. An index of 0.999 gives a
# variance of -0.100 per cent, AMBER... so to reach the Green/Yellow pair the modules must be
# driven directly, which is what the sweep above does. Here the end-to-end claim is the weaker
# and fully general one: the live status is never more favourable than the more favourable of
# the two readings and never more favourable than the LESS favourable one either.
for si in ({"bac": 1000.0, "ev": 500.0, "ac": 500.0, "cpi": 1.0},
           {"bac": 1000.0, "ev": 500.0, "ac": 520.0, "cpi": 500 / 520},
           {"bac": 1000.0, "ev": 500.0, "ac": 600.0, "cpi": 500 / 600},
           {"bac": 1000.0, "ev": 900.0, "ac": 850.0, "cpi": 900 / 850}):
    r = compute_project(dict(si), "S", "P1", CUTOFF)
    t = run_tcpi(dict(si), lambda: 0.5, CUTOFF)["status_color"]
    v = run_vac(dict(si), lambda: 0.5, CUTOFF)["status_color"]
    worse = max([b for b in (t, v) if b], key=SEVERITY.index) if (t or v) else None
    check(f"live state bac={si['bac']} ev={si['ev']} ac={si['ac']}: the status is the more "
          f"adverse reading {worse} and is never the more favourable one",
          r["category_statuses"].get("A1", {}).get("status") == worse,
          f'{r["category_statuses"].get("A1", {}).get("status")} vs {t}/{v}')

if _fail:
    print(f"\n{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
