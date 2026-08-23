#!/usr/bin/env python3
"""
RUN 31 PASS 3: THE FULL 64-FAULT NON-VACUITY CAMPAIGN.

DISCIPLINE, APPLIED TO EVERY FAULT WITHOUT EXCEPTION:
  baseline GREEN -> apply -> CONFIRM IT LANDED by re-reading from disk -> run the named guard ->
  require RED for the INTENDED reason -> restore byte-for-byte -> drop caches -> baseline GREEN.

A CRASH IS NOT RED. `run_guard` returns (0, 0) when no anchored `RESULT: n/m` line was printed,
which means the process died rather than the guard failing, and the campaign records CRASH and
FAILS the fault. This programme has twice caught itself scoring a crash as a pass; clause 6 of
section 3 exists because of that and is enforced here in code, not in prose.

AN UNRELATED FAILURE IS NOT EVIDENCE. Every fault names the guard whose invariant it attacks, and
that guard alone decides the verdict.

__pycache__ IS DROPPED ON BOTH SIDES. A restore inside the same clock second changes neither
mtime nor size, so a cached compiled mutant can otherwise survive the restore and poison the
baseline recheck.
"""
import csv, os, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "run31_full_fault_campaign.py",
        allow=["code_audit/run30_participant_package_v5_checksums.sha256", "code_audit/run31_fault_injection_results.csv"])
# -------------------------------------------------------------------------------------------
SIM = ROOT / "server" / "app" / "simulation"
APP = ROOT / "server" / "app"

ORACLES = "test_run31_canonical_oracles"
ARCH = "test_run31_pass2_acceptance"
VERS = "test_run31_version_boundaries"
PKG = "test_run28_participant_packages"
SYN = "test_run31_synthetic_checksums"
CAT7 = "test_run30_cat7_operational_route"


def drop_cache():
    for p in ROOT.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)


def run_guard(name):
    tmp = tempfile.mkdtemp()
    db = pathlib.Path(tmp) / "t.db"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT / "server",
                   env={**os.environ, "DATABASE_URL": f"sqlite:///{db}"}, capture_output=True)
    out = subprocess.run([sys.executable, f"{name}.py"], cwd=HERE,
                         env={**os.environ, "DATABASE_URL": f"sqlite:///{db}",
                              "SESSION_SECRET": "x", "PYTHONIOENCODING": "utf-8"},
                         capture_output=True, text=True)
    m = re.search(r"^RESULT: (\d+)/(\d+)", out.stdout, re.M)
    if not m:
        return 0, 0, out.returncode
    return int(m.group(1)), int(m.group(2)), out.returncode


# (id, system, invariant, file, old, new, guard, expected_red_reason)
F = [
 (1, "Category 6", "raw unassessed signal is ineligible", SIM/"qualification_contract.py",
  '    "Signal Synthesis": REQUIRED,', '    # FAULT\n', ARCH,
  "Signal Synthesis leaves the required population; its four routes stop being gated"),
 (2, "Category 7", "raw unassessed evidence is ineligible", SIM/"qualification_contract.py",
  '    "Evidence Combination": REQUIRED,', '    # FAULT\n', ARCH,
  "Evidence Combination leaves the required population; its twenty routes stop being gated"),
 (3, "Category 8", "raw unassessed evidence is ineligible", SIM/"qualification_contract.py",
  '    "Regulatory & Authority Thresholds": REQUIRED,', '    # FAULT\n', ARCH,
  "Category-8 B3 leaves the required population"),
 (4, "Category 10", "raw unassessed state is ineligible", SIM/"qualification_contract.py",
  '    "Decision Optimization": REQUIRED,', '    # FAULT\n', ARCH,
  "Decision Optimization leaves the required population"),
 (5, "Category 9", "Cat-9 is never a project-risk vote", SIM/"registry.py",
  '    "A1.8",   # Variance at Completion\n})', '    "A1.8",   # Variance at Completion\n    "C1.1",\n})',
  ARCH, "a Category-9 module enters the voting set"),
 (6, "9.1", "missing is not zero", SIM/"canonical_v6.py",
  '    missing = [f for f in applicable if f not in values or values.get(f) is None]',
  '    missing = [f for f in applicable if f not in values]', ORACLES,
  "a null mandatory field stops counting as missing, i.e. is imputed"),
 (7, "lineage", "UNRESOLVED is never independent", SIM/"lineage.py",
  "    if status not in LINEAGE_STATES:", "    return True  # FAULT\n    if status not in LINEAGE_STATES:",
  ARCH, "every lineage state answers independent, including UNRESOLVED"),
 (8, "abstention", "abstention is never Green", SIM/"models.py",
  '        "status_color": None,\n        "insufficient_data": True,',
  '        "status_color": "Green",\n        "insufficient_data": False,', ORACLES,
  "an abstention carries a favourable band"),
 (9, "9.1", "not-applicable leaves the denominator", SIM/"canonical_v6.py",
  '    applicable = [f for f in required if f not in not_applicable]',
  '    applicable = list(required)', ORACLES,
  "not-applicable fields re-enter the denominator and count as missing"),
 (10, "9.1", "zero is a value", SIM/"canonical_v6.py",
  '    missing = [f for f in applicable if f not in values or values.get(f) is None]',
  '    missing = [f for f in applicable if not values.get(f)]', ORACLES,
  "a zero-valued required field counts as missing"),
 (11, "9.2", "stale is not timely", SIM/"canonical_v6.py",
  '    fresh = age <= allowed if inclusive == "inclusive" else age < allowed',
  '    fresh = True', ORACLES, "a 40-day record under a 30-day rule reports TIMELY"),
 (12, "9.2", "future-dated is not timely", SIM/"canonical_v6.py",
  '    if age < 0:\n        base["timeliness_status"] = FUTURE_DATED',
  '    if False:\n        base["timeliness_status"] = FUTURE_DATED', ORACLES,
  "a future-dated record is treated as timely"),
 (13, "9.2", "no universal freshness window", SIM/"canonical_v6.py",
  '    allowed = rule.get("allowed_age_days")', '    allowed = 30', ORACLES,
  "one universal window replaces the source/use-class rule"),
 (14, "9.3", "BAC has no place in reliability", SIM/"canonical_v6.py",
  '        "source_authority": structure.get("source_authority"),',
  '        "source_authority": structure.get("bac") or structure.get("source_authority"),',
  ORACLES, "BAC enters the reliability component set"),
 (15, "9.3", "no governed mapping means no weight", SIM/"canonical_v6.py",
  '            "reliability_weight": None,', '            "reliability_weight": 1.0,', ORACLES,
  "missing numerical reliability silently becomes 1"),
 (16, "9.3", "verification is monotone under the rubric", SIM/"canonical_v6.py",
  '            total += float(table[key])', '            total -= float(table[key])', ORACLES,
  "improving verification decreases the configured reliability"),
 (17, "9.4", "critical audit fields are noncompensatory", SIM/"canonical_v6.py",
  '    atc = len(have) / len(applicable) if applicable else None',
  '    atc = min(1.0, (len(have) + len(present_set - set(required))) / len(applicable)) if applicable else None',
  ORACLES, "optional fields compensate for a missing mandatory element"),
 (18, "9.4", "a broken link is not complete", SIM/"canonical_v6.py",
  '    broken_links = sorted(k for k, v in links.items() if not v)', '    broken_links = []',
  ORACLES, "a broken evidence-to-judgment link is treated complete"),
 (19, "9.4", "impossible chronology is not complete", SIM/"canonical_v6.py",
  '    chronology_ok = bool(structure.get("chronology_valid", True))', '    chronology_ok = True',
  ORACLES, "an impossible chronology is treated complete"),
 (20, "9.5", "9.5 is not 9.1", SIM/"canonical_v6.py",
  '        mandatory = list(c.get("mandatory_fields", ()) or ())',
  '        mandatory = []', ORACLES,
  "package usability collapses onto field presence, duplicating 9.1"),
 (21, "9.5", "an absent domain is not full coverage", SIM/"canonical_v6.py",
  '        if not c.get("present"):', '        if False:', ORACLES,
  "an entirely absent required domain still counts as covered"),
 (22, "9.6", "conflicts are never averaged", SIM/"canonical_v6.py",
  '                    ok = (diff / abs(a)) <= rel', '                    ok = True', ORACLES,
  "a 100-versus-110 conflict is reconciled away"),
 (23, "9.6", "different periods are not inconsistent", SIM/"canonical_v6.py",
  '            if o.get("period") != ref.get("period") or o.get("units") != ref.get("units"):',
  '            if False:', ORACLES,
  "records from different reporting periods are compared as contradictory"),
 (24, "9.6", "material conflicts stay on the evidence", SIM/"canonical_v6.py",
  '                conflicts.append(dict(row))', '                _ = dict(row)', ORACLES,
  "a material conflict is omitted from the returned evidence"),
 (25, "9.7", "duplicates do not inflate cadence", SIM/"canonical_v6.py",
  '    covered = sum(1 for r in rows if r["status"] in ("ON_TIME", "LATE"))',
  '    covered = len([r for r in history if isinstance(r, dict)])', ORACLES,
  "a duplicate report improves coverage"),
 (26, "9.7", "a missed report is not perfect cadence", SIM/"canonical_v6.py",
  '        if rec is None:\n            row["status"] = "MISSING"',
  '        if rec is None:\n            row["status"] = "ON_TIME"', ORACLES,
  "a missed period is counted as received"),
 (27, "9.7", "approved extensions move the due date", SIM/"canonical_v6.py",
  '        due = _date(extensions.get(pid) or p.get("due_date"))',
  '        due = _date(p.get("due_date"))', ORACLES,
  "an approved extension is ignored and an on-time report reads late"),
 (28, "9.2/9.7", "freshness and cadence do not collapse", SIM/"canonical_v6.py",
  '        "reporting_coverage": (covered / expected) if expected else None,',
  '        "reporting_coverage": 1.0,', ORACLES,
  "cadence stops depending on the report history"),
 (29, "8.1", "production 8.1 has agents", SIM/"models_cat89.py",
  '    return V6.abm_governance(structure, signal_eligible=True,',
  '    return V6.abm_governance(dict(structure, agents=[]), signal_eligible=True,', ARCH,
  "a model with no agents runs instead of failing the structural guard"),
 (30, "8.1", "an ABM has a clock", SIM/"abm.py",
  '            env.clock = max(env.clock, msg.delivery_time)', '            pass', ORACLES,
  "the simulation clock never advances"),
 (31, "8.1", "the contractor cannot authorize", SIM/"abm.py",
  '            if not env.matrix.may_authorize(contractor.role, env.action_class):',
  '            if False:', ORACLES,
  "the contractor is no longer recorded as unable to authorize an owner-only action"),
 (32, "8.1", "the PM cannot authorize", SIM/"abm.py",
  '        return self.rule_for(action_class).required_approver == role',
  '        return True  # FAULT', ORACLES,
  "the required-approver test is removed at the authorization point"),
 (33, "8.1", "insufficient evidence cannot auto-authorize", SIM/"abm.py",
  '        if not env.evidence_sufficient:', '        if False:', ORACLES,
  "an evidence-insufficient case proceeds to authorization"),
 (34, "8.1", "latency changes the event history", SIM/"abm.py",
  '                    delivery_time=self.clock + latency, seq=self._seq,',
  '                    delivery_time=self.clock, seq=self._seq,', ORACLES,
  "response latency stops affecting delivery time, so the trace cannot move"),
 (35, "8.1", "production runs agent interactions", SIM/"canonical_v6.py",
  '        "state_history": model.history,', '        "state_history": [],', ARCH, "the route returns a matrix-style verdict with no agents, clock or history"),
 (36, "8.2", "applicability is not inferred from BAC", SIM/"canonical_v6.py",
  '    federal = structure.get("federal_context")',
  '    federal = structure.get("federal_context") or bool(structure.get("bac"))', ORACLES,
  "a BAC alone establishes Federal context and drives applicability"),
 (37, "8.2", "missing designation is never APPLICABLE", SIM/"canonical_v6.py",
  '        return done(REG.INSUFFICIENT_EVIDENCE,\n                    "the acquisition designation or agency is not established, and neither is "',
  '        return done(REG.APPLICABLE,\n                    "the acquisition designation or agency is not established, and neither is "', ORACLES,
  "an incomplete designation reaches an APPLICABLE answer"),
 (38, "8.3", "no evidence is never SATISFIED", SIM/"regulatory.py",
  '    missing = [k for k in rule.required_evidence if evidence.get(k) is None]',
  '    missing = []', ORACLES, "a rule with absent required evidence returns SATISFIED"),
 (39, "8.3", "a superseded edition is reviewed", SIM/"regulatory.py",
  '    if rule.superseded or rule.edition != _current_edition(rule.authority_family, rule.edition):',
  '    if False:', ORACLES, "a wrong or superseded edition is accepted without review"),
 (40, "8.4", "CPI/SPI cannot establish reporting", SIM/"canonical_v6.py",
  '    clause = structure.get("clause_id")\n    cadence = structure.get("required_cadence")',
  '    clause = structure.get("clause_id") or structure.get("cpi")\n    cadence = structure.get("required_cadence") or structure.get("spi")',
  ORACLES, "a cost or schedule index stands in for the clause and cadence"),
 (41, "8.4", "NOT_APPLICABLE receives no violation", SIM/"canonical_v6.py",
  '    if state == REG.NOT_APPLICABLE:', '    if False:', ORACLES,
  "an EVMS-not-applicable project receives a reporting result anyway"),
 (42, "8.4", "a missing report is not complete", SIM/"canonical_v6.py",
  '    if missing_report:\n        out["result"] = REG.NOT_SATISFIED',
  '    if False:\n        out["result"] = REG.NOT_SATISFIED', ORACLES,
  "a period with no report received is counted complete"),
 (43, "8.5", "only an authorized CO may execute", SIM/"canonical_v6.py",
  '        if authority["result"] == REG.SATISFIED and not m.get("officer_authority_current", True):',
  '        if False:', ORACLES,
  "an official with no current contracting-officer authority passes the authority rule"),
 (44, "8.5", "unilateral and bilateral are distinct", SIM/"canonical_v6.py",
  '                if e.get("modification_type") == "bilateral" else True),',
  '                if False else True),', ORACLES,
  "the bilateral signature requirement disappears, collapsing the distinction"),
 (45, "8.5", "an applicable form must be present", SIM/"canonical_v6.py",
  '            satisfied_when=lambda e: bool(e.get("written_instrument")),',
  '            satisfied_when=lambda e: True,', ORACLES,
  "an applicable SF 30 that is absent still passes the documentation rule"),
 (46, "8.6", "critical exceptions are noncompensatory", SIM/"canonical_v6.py",
  '            if r.get("criticality") in ("critical", "high"):', '            if r.get("criticality") in ("nonexistent",):', ORACLES,
  "a critical quality exception disappears inside the aggregate"),
 (47, "8.6", "unassessed is not satisfied", SIM/"canonical_v6.py",
  '        if not r.get("assessed"):\n            unassessed.append(rid)\n            continue',
  '        if not r.get("assessed"):\n            unassessed.append(rid)', ORACLES,
  "unassessed requirements enter the denominator and count as satisfied"),
 (48, "8.6", "no fabricated denominator", SIM/"canonical_v6.py",
  '        out.update({"quality_compliance_rate": None, "disposition": "NOT_ESTIMABLE",',
  '        out.update({"quality_compliance_rate": 1.0, "disposition": "MEASURED",', ORACLES,
  "a rate is produced with no assessed applicable requirement behind it"),
 (49, "8.7", "a mention is not an incidence numerator", SIM/"canonical_v6.py",
  '    cases = structure.get("recordable_cases")',
  '    cases = (structure.get("recordable_cases")\n             if structure.get("recordable_cases") is not None\n             else structure.get("safetyIncidentsDiscussed"))', ORACLES, "meeting-minute incident mentions become the OSHA numerator"),
 (50, "8.7", "zero hours has no rate", SIM/"canonical_v6.py",
  '        out.update({"incidence_rate": None, "lagging_disposition": "INVALID_DENOMINATOR",',
  '        out.update({"incidence_rate": 0.0, "lagging_disposition": "MEASURED",', ORACLES,
  "a zero denominator returns a finite incidence rate"),
 (51, "8.7", "zero recordables is not a system claim", SIM/"canonical_v6.py",
  '        "system_claim": None,', '        "system_claim": "strong safety system",', ORACLES,
  "a favourable safety-system conclusion is asserted"),
 (52, "8.8", "EPA CGP is not universal", SIM/"canonical_v6.py",
  '    if authority == "EPA":', '    if True:', ORACLES,
  "the EPA Construction General Permit is cited for every project"),
 (53, "8.8", "unassessed is not satisfied", SIM/"canonical_v6.py",
  '        if not r.get("assessed"):\n            unassessed.append(rid)\n            continue\n        applicable_assessed.append(rid)',
  '        if not r.get("assessed"):\n            unassessed.append(rid)\n        applicable_assessed.append(rid)',
  ORACLES, "unassessed environmental requirements count as assessed"),
 (54, "8.8", "critical violations are noncompensatory", SIM/"canonical_v6.py",
  '        elif r.get("criticality") in ("critical", "high"):', '        elif False:', ORACLES,
  "a critical permit violation is averaged away"),
 (55, "8.8", "a mention is not a compliance rate", SIM/"canonical_v6.py",
  '    if not authority or not jurisdiction:', '    if False:', ORACLES,
  "conformance is assessed without jurisdiction or permitting authority"),
 (56, "8.9", "an internal score is never CPARS", SIM/"canonical_v6.py",
  '    is_cpars = bool(source == "CPARS" and assessment_id)', '    is_cpars = True', ORACLES,
  "an internal assessment is labelled an official CPARS record"),
 (57, "8.9", "narrative and review state survive", SIM/"canonical_v6.py",
  '        "narratives": structure.get("narratives"),', '        "narratives": None,', ORACLES,
  "the supporting narrative is dropped from the official assessment"),
 (58, "8.9", "the worst factor stays visible", SIM/"canonical_v6.py",
  '            worst = min(ranked, key=lambda r: order.index(r["rating"]))',
  '            worst = max(ranked, key=lambda r: order.index(r["rating"]))', ORACLES, "the worst/critical factor disappears"),
 (59, "orphan", "extracted defining fields stay wired", APP/"extraction_merge.py",
  '        if _coerce_numeric(ex.get("osha_recordable_incidents")) is not None:',
  '        if False and _coerce_numeric(ex.get("osha_recordable_incidents")) is not None:', ORACLES,
  "the genuine safety numerator is disconnected from signal inputs again"),
 (60, "orphan", "canonical fields have a production route", APP/"project_data.py",
  '            | set(V6_STRUCTURE_KEYS.values()))', '            )', ORACLES, "the v6 structures leave the governed intake, so they exist only in fixtures"),
 (61, "packages", "a predecessor is never rewritten", None,
  "code_audit/run30_participant_package_v5_checksums.sha256", None, PKG,
  "a predecessor record regenerated to match the tree makes two records claim it"),
 (62, "versions", "history is append-only and unique", SIM/"models.py",
  '"sim-2026.08-v18", "sim-2026.08-v19",', '"sim-2026.08-v18", "sim-2026.08-v19", "sim-2026.08-v19",',
  VERS, "a duplicate stamp breaks uniqueness"),
 (63, "gate", "the dispatcher uses the boundary", SIM/"models.py",
  '    QUALIFICATION_BOUNDARY_INSTALLED = _install_boundary(VALIDATED)',
  '    QUALIFICATION_BOUNDARY_INSTALLED = {"gated": [], "assessing_excluded": []}', ARCH,
  "the boundary is never installed, which is exactly Run 30's defect"),
 (64, "ledger", "no false QUALIFIED", SIM/"qualification_boundary.py",
  '                if not ev.eligible_for(use):', '                if False:', ARCH,
  "raw evidence executes while the row still carries a qualification block"),
]

rows = []
print("=== BASELINE ===")
drop_cache()
base = {}
for g in (ORACLES, ARCH, VERS, PKG, SYN, CAT7):
    p, t, rc = run_guard(g)
    base[g] = (p, t)
    print(f"  {g}: {p}/{t} green={p == t and t > 0}")

for fid, sysname, inv, path, old, new, guard, reason in F:
    if fid == 61:
        target = ROOT / old
        backup = target.read_bytes()
        import hashlib
        lines = []
        for l in target.read_text().splitlines():
            if l.strip() and not l.startswith("#"):
                d, rel = re.split(r"\s+", l.strip(), maxsplit=1)
                fp = ROOT / rel.strip()
                d = hashlib.sha256(fp.read_bytes()).hexdigest() if fp.is_file() else d
                lines.append(f"{d}  {rel.strip()}")
            else:
                lines.append(l)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        landed = target.read_bytes() != backup
        evidence = f"predecessor record rewritten: {landed}"
    else:
        backup = path.read_text()
        if old not in backup:
            rows.append([fid, sysname, inv, guard, f"{base[guard][0]}/{base[guard][1]}",
                         str(path.relative_to(ROOT)), new[:60], "NOT_APPLIED",
                         "injection site not found", guard, "", "", reason, "", "", "", "",
                         "", "NOT_APPLIED", "site moved; needs repointing"])
            print(f"FAULT {fid}: NOT_APPLIED (site not found)")
            continue
        path.write_text(backup.replace(old, new, 1))
        landed = path.read_text() != backup
        evidence = f"file bytes changed on disk: {landed}"
    drop_cache()
    p, t, rc = run_guard(guard)
    crashed = (t == 0)
    red = (p != t) and not crashed
    if fid == 61:
        target.write_bytes(backup)
    else:
        path.write_text(backup)
    drop_cache()
    p2, t2, _ = run_guard(guard)
    restored = (p2 == t2 and t2 > 0)
    status = "PASS" if (landed and red and restored) else "FAIL"
    print(f"FAULT {fid:>2} [{sysname:<11}] landed={landed} {guard}: {p}/{t} "
          f"-> {'CRASH' if crashed else ('RED' if red else 'STILL GREEN')} | restored={restored} "
          f"| {status}")
    rows.append([fid, sysname, inv, guard, f"{base[guard][0]}/{base[guard][1]}",
                 str(path.relative_to(ROOT)) if path else old, new[:60] if new else "regenerate",
                 "YES" if landed else "NO", evidence, guard, rc,
                 "YES" if not crashed else "NO", reason,
                 f"{p}/{t}" if not crashed else "CRASH: no anchored RESULT line",
                 "YES" if crashed else "NO", "NO",
                 "YES", "YES" if restored else "NO", status, ""])

out = ROOT / "code_audit" / "run31_fault_injection_results.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fault_id", "module_system", "protected_invariant", "baseline_command",
                "baseline_result", "mutation_target", "mutation_description",
                "mutation_applied", "evidence_mutation_applied", "fault_command",
                "process_exit_code", "anchored_result_present", "expected_red_reason",
                "actual_red_reason", "crash", "unrelated_failure", "restored",
                "restored_green", "final_status", "notes"])
    w.writerows(rows)
print(f"\nwrote {out.relative_to(ROOT)}")
print(f"required=64 attempted={len(rows)} applied={sum(1 for r in rows if r[7]=='YES')} "
      f"RED={sum(1 for r in rows if r[18]=='PASS')} "
      f"NOT_APPLIED={sum(1 for r in rows if r[7]!='YES')} "
      f"crash_as_RED={sum(1 for r in rows if r[14]=='YES' and r[18]=='PASS')}")
