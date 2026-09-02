"""
RUN 118. THE EIGHT FACTORS, EACH PROVED TO BAND; EACH OVERRIDE PROVED TO FIRE AND NOT TO FIRE.

STANDING RULE 4: a check that cannot fail is worse than no check. Every assertion here is
paired -- the fault is introduced into the thing the check reads and then removed -- so nothing
below can pass by accident. THE LADDERS ARE EXERCISED AT THEIR RUNGS, not at one comfortable
value each: a ladder proved only in its middle is not proved.

This driver exercises `simulation/trade_factors.py` directly. The END-TO-END proof -- documents
through the real upload route, a firm's posture moving A4.8's band -- is `drive_run118_route.py`.

Run from `server/`:  python tools/drive_run118.py
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path("/home/user/LinPRojectRadar/server")))
from app.simulation import trade_factors as TF
from app.simulation.category_posture import AVERAGE_CUTS, BAND_SCORE

P = F = 0
def ck(name, got, want):
    global P, F
    ok = got == want
    globals().__setitem__("P" if ok else "F", (P if ok else F) + 1)
    print(("  PASS " if ok else "  FAIL ") + name + f"   got={got!r} want={want!r}")
    return ok

def rec(ref, kind, **kw):
    d = {"record_reference": ref, "record_kind": kind, "record_status": "open"}
    d.update(kw); return d

NEW = lambda r: TF._truthy(r.get("record_new_this_period"))

print("=" * 100)
print("RUN 118 -- THE EIGHT FACTOR LADDERS, THEIR OVERRIDES, THE AVERAGE, THE STOP-WORK BYPASS")
print("=" * 100)

# ---------------------------------------------------------------- 0. THE CUTS ARE NOT RESTATED
print("\n0. THE AVERAGING CUTS COME FROM `category_posture` AND ARE NOT RESTATED HERE")
ck("BAND_SCORE is the platform's", BAND_SCORE, {"Green": 2.0, "Yellow": 1.0, "Amber": -1.0, "Red": -2.0})
ck("AVERAGE_CUTS is the platform's", AVERAGE_CUTS, ((1.5, "Green"), (0.5, "Yellow"), (-0.5, "Amber")))
src = pathlib.Path("app/simulation/trade_factors.py").read_text()
ck("trade_factors imports band_average rather than copying it",
   "from .category_posture import AVERAGE_CUTS, BAND_SCORE, band_average" in src, True)
ck("trade_factors does not restate the cut 1.5", "1.5" in src.split("AVERAGE_WORDS")[0], False)

# ---------------------------------------------------------------- 1. NONCONFORMANCES
print("\n1. NONCONFORMANCES -- the displacement ladder, every rung, from a Green starting band")
def ncr(n, denom=100, start="Green", **kw):
    rs = [rec(f"N{i}", "nonconformance", record_new_this_period="yes", **kw) for i in range(n)]
    return TF.factor_nonconformances(rs, denom, starting_band=start, newness=NEW)
ck("1 per 100 -> under 2 -> no downgrade, stays Green", ncr(1)["band"], "Green")
ck("2 per 100 -> down one -> Yellow", ncr(2)["band"], "Yellow")
ck("4.9 per 100 (49/1000) -> still down one", ncr(49, 1000)["band"], "Yellow")
ck("5 per 100 -> down two -> Amber", ncr(5)["band"], "Amber")
ck("9 per 100 -> still down two", ncr(9)["band"], "Amber")
ck("10 per 100 -> Red outright", ncr(10)["band"], "Red")
ck("down two from Yellow is Red", ncr(5, start="Yellow")["band"], "Red")
ck("down two from Amber stops at Red", ncr(5, start="Amber")["band"], "Red")
ck("FALSIFY: 1.99 per 100 (199/10000) is NOT a downgrade", ncr(199, 10000)["band"], "Green")
ck("a CLOSED NCR stops counting immediately",
   TF.factor_nonconformances([rec(f"N{i}", "nonconformance", record_status="closed",
                                  record_new_this_period="yes") for i in range(20)],
                             100, starting_band="Green", newness=NEW)["band"], "Green")
ck("a row not stating newness is excluded and REPORTED",
   TF.factor_nonconformances([rec(f"N{i}", "nonconformance") for i in range(20)],
                             100, starting_band="Green", newness=NEW)["rows_newness_not_stated"], 20)
ck("NO starting band: a displacement rung produces NO band", ncr(2, start=None)["band"], None)
ck("NO starting band: the Red rung still fires", ncr(10, start=None)["band"], "Red")

print("   override -- fires:")
for w in ("life_safety", "structural", "code_compliance_failure", "hold_point_failure",
          "turnover_blocking"):
    r = TF.factor_nonconformances([rec("N1", "nonconformance", record_severity=w)], 1000,
                                  starting_band="Green", newness=NEW)
    ck(f"   '{w}' fires the NCR override", (r["band"], r["override_fired"]), ("Red", True))
r = TF.factor_nonconformances([rec("N1", "nonconformance", record_repeat_after_closed_action="yes")],
                              1000, starting_band="Green", newness=NEW)
ck("   a repeat NCR after a closed corrective action fires it", r["band"], "Red")
print("   override -- does NOT fire:")
r = TF.factor_nonconformances([rec("N1", "nonconformance", record_severity="cosmetic")], 1000,
                              starting_band="Green", newness=NEW)
ck("   'cosmetic' fires nothing and is not dropped to the nearest word",
   (r["band"], r["override_fired"]), ("Green", False))
r = TF.factor_nonconformances([rec("N1", "nonconformance", record_severity="life_safety",
                                   record_status="closed")], 1000, starting_band="Green", newness=NEW)
ck("   a CLOSED life-safety NCR does not fire it", r["override_fired"], False)

# ---------------------------------------------------------------- 2. FAILED INSPECTIONS
print("\n2. FAILED INSPECTIONS -- under 2 / 2 / 5 / 10 per cent")
def fi(n, denom=100, **kw):
    return TF.factor_failed_inspections(
        [rec(f"I{i}", "inspection_failure", **kw) for i in range(n)], denom)
for n, want in ((1, "Green"), (2, "Yellow"), (4, "Yellow"), (5, "Amber"), (9, "Amber"), (10, "Red")):
    ck(f"{n} per cent -> {want}", fi(n)["band"], want)
ck("FALSIFY: 0 failures is Green, not Red", fi(0)["band"], "Green")
r = TF.factor_failed_inspections(
    [rec(f"I{i}", "inspection_failure") for i in range(5)]
    + [rec(f"R{i}", "inspection_failure", record_is_reinspection="yes") for i in range(20)], 100)
ck("a REINSPECTION does not count again", (r["numerator"], r["band"], r["reinspections_excluded"]),
   (5, "Amber", 20))
print("   override -- fires / does not fire:")
for w in ("life_safety", "structural", "code_required", "hold_point", "turnover_blocking"):
    ck(f"   '{w}' fires", fi(1, 1000, record_severity=w)["band"], "Red")
ck("   'finish' fires nothing", fi(1, 1000, record_severity="finish")["band"], "Green")

# ---------------------------------------------------------------- 3. SAFETY
print("\n3. SAFETY -- TRIR = recordables x 200,000 / hours, the OSHA formula, the owner's cuts")
def sf(rc, hrs, records=()):
    return TF.factor_safety(list(records), rc, hrs)
ck("0.8 TRIR -> Green", sf(4, 1_000_000)["band"], "Green")
ck("1.0 TRIR -> Yellow (inclusive lower side)", sf(5, 1_000_000)["band"], "Yellow")
ck("2.0 TRIR -> Amber", sf(10, 1_000_000)["band"], "Amber")
ck("3.0 TRIR -> Red", sf(15, 1_000_000)["band"], "Red")
ck("the formula is OSHA's, the cuts are the owner's -- recorded separately",
   (sf(5, 1_000_000)["band_basis_id"], sf(5, 1_000_000)["boundary_basis_id"]),
   (TF.OSHA_TRIR_BASIS_ID, TF.OWNER_BASIS_ID))
r = sf(1, 9_999)
ck("below 10,000 hours: the RATE IS SHOWN, not replaced by a count",
   (r["rate"] is not None, r["band"] is not None, bool(r["small_exposure_hours_warning"])),
   (True, True, True))
r = sf(1, 10_000)
ck("FALSIFY: at 10,000 hours the warning does NOT fire", bool(r["small_exposure_hours_warning"]), False)
ck("no hours stated -> no rate and none assumed", sf(1, None)["band"], None)
print("   override -- fires / does not fire, on `_SAFETY_OVERRIDE_WORDS`, UNWIDENED:")
for w in ("fatality", "serious_life_threatening_event", "stop_work_order",
          "unresolved_high_severity_violation"):
    ck(f"   '{w}' fires", sf(0, 1_000_000, [rec("S1", "safety_incident", record_severity=w)])["band"], "Red")
ck("   'first_aid' fires nothing",
   sf(0, 1_000_000, [rec("S1", "safety_incident", record_severity="first_aid")])["band"], "Green")
ck("   a CLOSED fatality record does not fire it",
   sf(0, 1_000_000, [rec("S1", "safety_incident", record_severity="fatality",
                         record_status="closed")])["override_fired"], False)

# ---------------------------------------------------------------- 4. ENVIRONMENTAL
print("\n4. ENVIRONMENTAL -- 0 / above 0 / 5 / 10 per cent")
def env(overdue, denom=100, kw=None):
    rs = [rec(f"E{i}", "environmental_action", record_status="overdue") for i in range(overdue)]
    if kw: rs.append(rec("EX", "environmental_action", **kw))
    return TF.factor_environmental(rs, denom)
ck("exactly 0 per cent -> Green", env(0)["band"], "Green")
ck("above 0 (1 per cent) -> Yellow", env(1)["band"], "Yellow")
ck("4 per cent -> Yellow", env(4)["band"], "Yellow")
ck("5 per cent -> Amber", env(5)["band"], "Amber")
ck("10 per cent -> Red", env(10)["band"], "Red")
ck("FALSIFY: an action NOT marked overdue is not in the numerator",
   TF.factor_environmental([rec(f"E{i}", "environmental_action") for i in range(50)], 100)["band"],
   "Green")
print("   override -- fires / does not fire, on `_ENV_OVERRIDE`, UNWIDENED:")
for w in ("stop_work", "notice_of_violation", "enforcement_notice", "permit_suspension",
          "unauthorised_discharge"):
    ck(f"   '{w}' fires", env(0, 100, {"record_severity": w})["band"], "Red")
ck("   'housekeeping' fires nothing", env(0, 100, {"record_severity": "housekeeping"})["band"], "Green")

# ---------------------------------------------------------------- 5. QUALITY AUDIT
print("\n5. QUALITY AUDIT -- MAJOR findings / audits, a RATIO: 0 / above 0 / 1.0 / 2.0")
def qa(major, denom=25, extra=None):
    rs = [rec(f"F{i}", "audit_finding", record_severity="major") for i in range(major)]
    if extra: rs.append(rec("FX", "audit_finding", **extra))
    return TF.factor_quality_audit(rs, denom)
ck("0 -> Green", qa(0)["band"], "Green")
ck("above 0 (1/25 = 0.04) -> Yellow", qa(1)["band"], "Yellow")
ck("24/25 = 0.96 -> Yellow", qa(24)["band"], "Yellow")
ck("25/25 = 1.0 -> Amber", qa(25)["band"], "Amber")
ck("49/25 = 1.96 -> Amber", qa(49)["band"], "Amber")
ck("50/25 = 2.0 -> Red", qa(50)["band"], "Red")
r = TF.factor_quality_audit(
    [rec(f"F{i}", "audit_finding", record_severity="minor") for i in range(100)], 25)
ck("MINOR documentation observations are NOT counted",
   (r["numerator"], r["band"], r["minor_findings_not_counted"]), (0, "Green", 100))
r = TF.factor_quality_audit([rec("FX", "audit_finding")], 25)
ck("a finding stating NO severity enters neither arm and is reported",
   (r["numerator"], r["minor_findings_not_counted"], r["findings_stating_no_severity"]), (0, 0, 1))
print("   override -- fires / does not fire:")
for w in ("critical", "life_safety", "structural_integrity", "code_compliance", "hold_point"):
    ck(f"   '{w}' fires", qa(0, 25, {"record_severity": w})["band"], "Red")
ck("   'advisory' fires nothing", qa(0, 25, {"record_severity": "advisory"})["band"], "Green")

# ---------------------------------------------------------------- 6. PROCUREMENT
print("\n6. PROCUREMENT -- two arms, worst of them")
def pr(items, denom=100):
    return TF.factor_procurement([rec(f"P{i}", "late_delivery", **kw) for i, kw in enumerate(items)],
                                 denom)
ck("rate arm: 0 late -> Green", pr([])["band"], "Green")
ck("rate arm: 1 per cent, 1 day late -> Yellow", pr([{"record_days_late": 1}])["band"], "Yellow")
ck("rate arm: 5 per cent, all 1 day late -> Amber",
   pr([{"record_days_late": 1}] * 5)["band"], "Amber")
ck("rate arm: 10 per cent -> Red", pr([{"record_days_late": 1}] * 10)["band"], "Red")
r = pr([{"record_days_late": 5}])
ck("days-late FLOOR: 5 working days -> at least Yellow",
   (r["days_late_floor_band"], r["band"]), ("Yellow", "Yellow"))
r = pr([{"record_days_late": 6}])
ck("days-late FLOOR: 6 working days -> at least Amber, and the FLOOR beats a Yellow rate",
   (r["rate_arm_band"], r["days_late_floor_band"], r["band"]), ("Yellow", "Amber", "Amber"))
r = pr([{"record_days_late": 11}])
ck("days-late FLOOR: 11 working days -> Red on one item out of a hundred",
   (r["rate_arm_band"], r["band"]), ("Yellow", "Red"))
ck("FALSIFY: 10 working days is Amber, not Red", pr([{"record_days_late": 10}])["band"], "Amber")
r = TF.factor_procurement([rec("P1", "late_delivery", record_days_late=11)], 3)
ck("the days-late floor SURVIVES the small-denominator safeguard",
   (r["exposure_class"], r["rate"], r["band"]), (TF.EXPOSURE_TOO_FEW, None, "Red"))
print("   override -- fires / does not fire:")
ck("   a milestone forecast late fires",
   pr([{"record_days_late": 1, "record_milestone_forecast_late": "yes"}])["band"], "Red")
ck("   'no' does not fire",
   pr([{"record_days_late": 1, "record_milestone_forecast_late": "no"}])["band"], "Yellow")

# ---------------------------------------------------------------- 7. FIELD OBSERVATIONS
print("\n7. FIELD OBSERVATIONS -- CONFIRMED defects only: under 2 / 2 / 5 / 10")
def fo(n, denom=100, **kw):
    return TF.factor_field_observations(
        [rec(f"O{i}", "defect_observation", record_confirmed="yes", **kw) for i in range(n)], denom)
for n, want in ((1, "Green"), (2, "Yellow"), (5, "Amber"), (10, "Red")):
    ck(f"{n} per 100 -> {want}", fo(n)["band"], want)
r = TF.factor_field_observations(
    [rec(f"O{i}", "defect_observation") for i in range(50)], 100)
ck("an UNCONFIRMED observation is not counted -- not every comment",
   (r["numerator"], r["band"], r["observations_not_confirmed"]), (0, "Green", 50))
print("   override -- fires / does not fire:")
for w in ("structural", "life_safety", "code", "work_stoppage"):
    ck(f"   '{w}' fires (reported AND verified)", fo(1, 1000, record_severity=w)["band"], "Red")
r = TF.factor_field_observations(
    [rec("O1", "defect_observation", record_severity="structural")], 1000)
ck("   an UNVERIFIED structural observation does NOT fire it", r["override_fired"], False)

# ---------------------------------------------------------------- 8. COMMISSIONING
print("\n8. COMMISSIONING -- FIRST acceptance test: 0 / above 0 / 5 / 10 per cent")
def cx(n, denom=100, **kw):
    return TF.factor_commissioning(
        [rec(f"C{i}", "commissioning_failure", **kw) for i in range(n)], denom)
for n, want in ((0, "Green"), (1, "Yellow"), (5, "Amber"), (10, "Red")):
    ck(f"{n} per cent -> {want}", cx(n)["band"], want)
r = TF.factor_commissioning(
    [rec("C1", "commissioning_failure")]
    + [rec(f"C{i}", "commissioning_failure", record_is_reinspection="retest") for i in range(30)], 100)
ck("a RETEST does not count again", (r["numerator"], r["retests_excluded"]), (1, 30))
print("   override -- fires / does not fire:")
for w in ("critical", "life_safety", "functional_performance", "regulatory", "turnover"):
    ck(f"   '{w}' fires", cx(1, 1000, record_severity=w)["band"], "Red")
ck("   'punchlist' fires nothing", cx(1, 1000, record_severity="punchlist")["band"], "Yellow")

# ---------------------------------------------------------------- 9. SMALL DENOMINATOR
print("\n9. THE SMALL-DENOMINATOR SAFEGUARD, section 1.3")
r = fi(1, 2)
ck("1 failed inspection out of 2 does NOT produce Red -- it does not band at all",
   (r["exposure_class"], r["rate"], r["band"]), (TF.EXPOSURE_TOO_FEW, None, None))
ck("...and the finding stays visible", r["numerator"], 1)
r = fi(1, 9)
ck("9 in the denominator -> no rate banding", r["exposure_class"], TF.EXPOSURE_TOO_FEW)
r = fi(0, 10)
ck("10 -> bands, LABELLED limited exposure",
   (r["exposure_class"], r["limited_exposure"], r["band"]), (TF.EXPOSURE_LIMITED, True, "Green"))
r = fi(1, 10)
ck("...and 1 out of 10 is a real 10 per cent, which the ladder bands Red",
   (r["limited_exposure"], r["band"]), (True, "Red"))
r = fi(6, 24)
ck("24 -> still limited exposure, and it bands (25 per cent -> Red)",
   (r["exposure_class"], r["band"]), (TF.EXPOSURE_LIMITED, "Red"))
r = fi(1, 25)
ck("25 -> full, no label", (r["exposure_class"], r["limited_exposure"]), (TF.EXPOSURE_FULL, False))
r = fi(1, 0)
ck("a ZERO denominator never produces a rate",
   (r["exposure_class"], r["rate"]), (TF.EXPOSURE_NO_DENOMINATOR, None))
r = fi(1, 2, record_severity="life_safety")
ck("BUT the hard override still fires below the safeguard", r["band"], "Red")

# ---------------------------------------------------------------- 10. THE AVERAGE
print("\n10. THE AVERAGE, THE OVERRIDE BYPASS AND THE STOP-WORK BYPASS")
D = {"inspections_performed": 100, "exposure_hours": 1_000_000, "recordable_incidents": 0,
     "environmental_actions_due": 100, "audits_covering_firm": 25, "items_due": 100,
     "field_reports_covering_firm": 100, "systems_tested": 100}
def fp(records, start="Green", d=None):
    return TF.firm_posture(subcontractor="Acme", starting_band=start, records=list(records),
                           denominators=dict(D if d is None else d), newness=NEW)
r = fp([])
ck("all eight factors Green with clean records -> Green",
   (r["adjusted_posture"], r["factor_mean_score"], len(r["factors_banded"])), ("Green", 2.0, 8))
# Two Reds and six Greens: (2*-2 + 6*2)/8 = 1.0 -> Yellow. ONE WEAK FACTOR MOVES IT WITHOUT
# DOMINATING, which is the whole point of averaging.
r = fp([rec(f"I{i}", "inspection_failure") for i in range(10)]
       + [rec(f"O{i}", "defect_observation", record_confirmed="yes") for i in range(10)])
ck("two Red factors among eight -> mean 1.0 -> Yellow, NOT Red",
   (r["factor_mean_score"], r["adjusted_posture"], r["adjustment_rule"]),
   (1.0, "Yellow", "average_of_factor_bands"))
ck("...and the calculated adjustment is recorded", r["adjustment"], "down 1 band(s) from the stated rating")
r = fp([rec("I1", "inspection_failure", record_severity="life_safety")])
ck("ONE HARD OVERRIDE BYPASSES THE AVERAGE -> Red although seven factors are Green",
   (r["adjusted_posture"], r["adjustment_rule"], r["overrides_fired"]),
   ("Red", "hard_override", ["failed_inspections"]))
ck("FALSIFY: the same record without the severity word averages instead",
   fp([rec("I1", "inspection_failure")])["adjustment_rule"], "average_of_factor_bands")
r = fp([rec("S1", "safety_incident", record_severity="stop_work_order")])
ck("A STOP-WORK ORDER sets Red and bypasses the average",
   (r["adjusted_posture"], r["adjustment_rule"], r["stop_work_bypass"]),
   ("Red", "stop_work_order", True))
ck("...and it is recorded as its own class, not as an ordinary override",
   (len(r["stop_work_orders"]), r["stop_work_words"] is not None), (1, True))
ck("...and NO other factor pulls it back: seven Greens do not move it",
   fp([rec("S1", "safety_incident", record_severity="stop_work")] , start="Green")["adjusted_posture"],
   "Red")
r = fp([], start="Amber", d={})
ck("NO factor bands -> the stated rating stands UNADJUSTED (the Run 107 behaviour, kept)",
   (r["adjusted_posture"], r["adjustment_rule"]), ("Amber", "source_rating_unadjusted"))
r = TF.firm_posture(subcontractor="Nameless", starting_band=None,
                    records=[rec(f"I{i}", "inspection_failure") for i in range(10)],
                    denominators=dict(D), newness=NEW)
ck("SECTION 1.4: a firm with records and NO stated rating is assessed from the records",
   (r["source_rating_band"], r["adjusted_posture"] is not None), (None, True))

print("\n11. ACROSS FIRMS THE MOST ADVERSE GOVERNS")
a = fp([], start="Green"); b = fp([rec("S1", "x", record_severity="fatality")], start="Green")
b["subcontractor"] = "Zeta"
ck("the Red firm governs over the Green one", TF.governing([a, b])["subcontractor"], "Zeta")
ck("FALSIFY: with both Green the tie breaks on name, not on order",
   TF.governing([fp([], start="Green"), dict(fp([], start="Green"), subcontractor="Aaa")]
                )["subcontractor"], "Acme")

# =================================================================================================
# 12. RUN 118, SECOND ATTEMPT. THE AUDIT OF THE FIRST ATTEMPT'S OWN READING.
#
# The first attempt recorded in its docstring that "the source rating enters the average through
# the nonconformance factor and nowhere else" is the weakest joint in its reading of the order.
# It did not MEASURE what that costs. This section measures it, and the measurement is the
# leading finding of this run: the stated rating is ONE VOICE AMONG EIGHT and seven clean
# factors OUTVOTE IT UPWARDS.
#
# NOTHING IS FIXED HERE AND NO FLOOR IS INVENTED. The owner said the factors adjust the rating
# and did not say the adjustment is one-way. These checks PIN the behaviour so that it cannot
# change silently, and they fail the moment it does -- in EITHER direction.
# =================================================================================================
print("\n12. THE STATED RATING IS ONE VOICE AMONG EIGHT -- MEASURED, NOT ASSERTED")
for _start, _want, _adj in (("Red", "Green", "up 3 band(s) from the stated rating"),
                            ("Amber", "Green", "up 2 band(s) from the stated rating"),
                            ("Yellow", "Green", "up 1 band(s) from the stated rating"),
                            ("Green", "Green", "no movement from the stated rating")):
    r = TF.firm_posture(subcontractor="Acme", starting_band=_start, records=[],
                        denominators=dict(D), newness=NEW)
    ck(f"a firm rated {_start} with CLEAN records and full denominators -> {_want}",
       (r["adjusted_posture"], r["adjustment"], r["adjustment_rule"]),
       (_want, _adj, "average_of_factor_bands"))
r = TF.firm_posture(subcontractor="Acme", starting_band="Red", records=[],
                    denominators=dict(D), newness=NEW)
ck("...and eight of eight factors banded, so the stated Red is outvoted seven to one",
   (len(r["factors_banded"]), r["factor_bands"]["nonconformances"]), (8, "Red"))
ck("...and the LIFT IS NOT HELD FOR PM REVIEW: Green is not a reviewable posture",
   r["adjusted_posture"] in ("Amber", "Red"), False)
# THE FALSIFICATION OF THE ABOVE: remove the denominators and the lift must not happen.
r = TF.firm_posture(subcontractor="Acme", starting_band="Red", records=[],
                    denominators={}, newness=NEW)
ck("FALSIFY: with NO denominators nothing bands, so the stated Red stands",
   (r["adjusted_posture"], r["adjustment_rule"]), ("Red", "source_rating_unadjusted"))
# AND THE DOWNWARD DIRECTION STILL WORKS, so these checks are not merely pinning "always Green".
r = TF.firm_posture(subcontractor="Acme", starting_band="Green",
                    records=[rec(f"N{i}", "nonconformance", record_new_this_period="yes")
                             for i in range(60)]
                            + [rec(f"I{i}", "inspection_failure") for i in range(60)],
                    denominators=dict(D), newness=NEW)
ck("...and adverse records still move a Green firm DOWN, so these checks are two-sided",
   r["adjusted_posture"] in ("Amber", "Red", "Yellow"), True)

print("\n" + "=" * 100)
print(f"RUN 118 FACTOR SUITE: {P} passed, {F} failed, {P+F} total")
print("=" * 100)
sys.exit(1 if F else 0)
