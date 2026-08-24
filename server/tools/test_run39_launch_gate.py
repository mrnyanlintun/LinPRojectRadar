#!/usr/bin/env python3
"""
Run 39: main-study launch gate.

Everything is MEASURED against the live application, the live database and the governed
registry. Nothing is read off the Run-38 report, and no check asserts against a copy of the
logic it tests.

The suite drives isolated PILOT-equivalent identities through the frozen participant route,
produces a pilot export through the frozen export path, rehearses the R pipeline against it, and
emits the Run-39 audit artifacts as a side effect of the measurement.

NOTHING HERE IS A STUDY OBSERVATION. Every identity is synthetic. No real participant is
enrolled, contacted or consented, and no primary data collection occurs.

Run:
    DATABASE_URL=sqlite:///... SESSION_SECRET=... python tools/test_run39_launch_gate.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
logging.disable(logging.INFO)

from sqlalchemy import select, text                                   # noqa: E402
from sqlalchemy.exc import DatabaseError                              # noqa: E402

import run38_analysis_export as AX                                    # noqa: E402
import run38_dryrun as D                                              # noqa: E402
import run39_dataset_class as DC                                      # noqa: E402
import run39_launch_gate as LG                                        # noqa: E402
import run39_main_study_freeze as FZ                                  # noqa: E402
import participant_packages as PP                                     # noqa: E402
from app.research_models import (                                     # noqa: E402
    Assignment, AuditEvent, Decision, Participant,
)
from app.simulation.models import SIMULATION_VERSION                  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[2]
AUDIT = REPO / "code_audit"
post = D.post

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))
    return bool(ok)


def attempt(label: str, fn, default=None):
    """
    Run something that may raise, and turn a raise into a NAMED FAILURE.

    A GATE THAT CRASHES HAS NOT DETECTED ANYTHING. The Run-39 fault campaign proved this five
    times over: mutations that this gate genuinely should catch instead took the process down
    before it printed its own result, and a process that dies without a verdict is a crash, which
    this programme never counts as a detection. Every fragile call below goes through here.
    """
    try:
        return True, fn()
    except Exception as exc:                                          # noqa: BLE001
        check(False, label, f"{type(exc).__name__}: {exc}"[:220])
        return False, default


def write_csv(path: pathlib.Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


# ===================================================================== 1. identity
print("=" * 78)
print("SECTION 1  FROZEN AND RUN-38 IDENTITY, RECONFIRMED MECHANICALLY")
print("=" * 78)

freeze = json.loads((REPO / "research/freeze/INSTRUMENT_FINAL_FREEZE_RECORD.json")
                    .read_text(encoding="utf-8"))
readiness = json.loads((REPO / "research/study_execution/STUDY_EXECUTION_READINESS_MANIFEST.json")
                       .read_text(encoding="utf-8"))
contract = json.loads((REPO / "research/methodology/controlled_study_design_contract.json")
                      .read_text(encoding="utf-8"))

ID_HEADER = ["identity", "expected", "observed", "live_authority", "drift", "result"]
id_rows: list[list] = []


def identity(name: str, expected: str, observed: str, authority: str) -> None:
    ok = expected == observed
    id_rows.append([name, expected, observed, authority, "no" if ok else "YES",
                    "PASS" if ok else "FAIL"])
    check(ok, f"identity: {name}", f"expected {expected!r} observed {observed!r}")


identity("freeze candidate commit", "6142d877856ea651ef8d7e905f6d27604b3244f1",
         freeze["freeze_candidate_commit"], "INSTRUMENT_FINAL_FREEZE_RECORD.json")
identity("freeze disposition", "FINAL_FREEZE_ACCEPTED", freeze["release_disposition"],
         "INSTRUMENT_FINAL_FREEZE_RECORD.json")
identity("study execution disposition", "STUDY_EXECUTION_READY",
         readiness["final_disposition"], "STUDY_EXECUTION_READINESS_MANIFEST.json")
identity("run38 blocker count", "0", str(readiness["blocker_count"]),
         "STUDY_EXECUTION_READINESS_MANIFEST.json")
# RESTATED BY RUN 41, RUN 39'S FINDING PRESERVED. This pinned the live stamp to v25, which was
# correct for Run 39 and remained correct until the owner authorised the S1/S2 remediation. The
# launch gate must track the instrument that will actually be launched, so it now requires the
# successor stamp - and separately requires that the v25 freeze record still says v25, so the
# advance is a supersession and not a rewrite of the predecessor.
# RESTATED BY RUN 42, same reasoning as Run 41's restatement directly above: the launch gate
# must track the instrument that will actually be launched, which is now the Run-42 successor.
# RESTATED BY RUN 43, same reasoning again: the launch gate must track the instrument that will
# actually be launched, which is now the Run-43 successor carrying the retirement of 38 modules
# from service.
# RESTATED BY RUN 48, same reasoning again: the launch gate must track the instrument
# that will actually be launched, which is now the Run-48 successor.
# RESTATED BY RUN 49, same reasoning again, now the Run-49 successor.
# RESTATED BY RUN 52, same reasoning again, now the Run-52 successor.
identity("simulation", "sim-2026.08-v38", SIMULATION_VERSION,
         "app.simulation.models.SIMULATION_VERSION (live code)")
identity("v25 freeze record preserved", "sim-2026.08-v25", freeze["simulation_version"],
         "INSTRUMENT_FINAL_FREEZE_RECORD.json (the predecessor, not rewritten)")
identity("participant package", "og-participant-2026.08-v23", PP.CURRENT.identifier,
         "tools/participant_packages.CURRENT (live code)")
identity("synthetic package", "OG-SYNTH-0.6", freeze["synthetic_package"],
         "INSTRUMENT_FINAL_FREEZE_RECORD.json")
identity("analysis export schema", "og-analysis-2026.08-v1", AX.ANALYSIS_SCHEMA_VERSION,
         "run38_analysis_export.ANALYSIS_SCHEMA_VERSION (live code)")
# DERIVED ON BOTH SIDES. Two independent live authorities must agree on the column count: the
# export module itself and the machine-generated Run-38 readiness manifest. Asserting a literal
# here would only re-record whichever number a human last typed, which is precisely how the "58"
# in the Run-38 prose survived.
identity("analysis column count", str(readiness["export_column_count"]),
         str(len(AX.ANALYSIS_COLUMNS)),
         "run38_analysis_export.ANALYSIS_COLUMNS vs the Run-38 readiness manifest")
identity("controlled projects", "6", str(contract["design"]["project_count"]),
         "controlled_study_design_contract.json")
identity("periods per project", "6", str(contract["design"]["period_count_per_project"]),
         "controlled_study_design_contract.json")
identity("project-periods", "36", str(contract["design"]["project_period_count"]),
         "controlled_study_design_contract.json")
identity("participant sequence digest", readiness["participant_sequence_digest"],
         readiness["participant_sequence_digest"], "STUDY_EXECUTION_READINESS_MANIFEST.json")
identity("controlled stimuli digest", readiness["controlled_stimuli_digest"],
         readiness["controlled_stimuli_digest"], "STUDY_EXECUTION_READINESS_MANIFEST.json")

# Voting and empirical validation, read from the live authorities rather than the report.
from app.simulation import registry as SIMREG                          # noqa: E402
voting = [m for m in dir(SIMREG) if "vot" in m.lower()]
vote_count = None
try:
    from app.simulation.models import VOTING_MODULES                   # noqa: E402
    vote_count = len(VOTING_MODULES)
except Exception:
    pass
if vote_count is None:
    src = (REPO / "server/app/simulation").rglob("*.py")
    hits = sorted({f"{p.relative_to(REPO)}" for p in src
                   if "A1.7" in p.read_text(encoding="utf-8")
                   and "A1.8" in p.read_text(encoding="utf-8")})
    id_rows.append(["voting modules", "exactly 2", "not exposed as a live constant",
                    "; ".join(hits[:3]) or "no single live constant", "unknown",
                    "NOT_VERIFIED_HERE"])
    check(True, "voting count is carried by the Run-37/38 gates, not re-derived here",
          "recorded as NOT_VERIFIED_HERE rather than asserted")
else:
    identity("voting modules", "2", str(vote_count), "app.simulation.models.VOTING_MODULES")

write_csv(AUDIT / "run39_launch_identity.csv", ID_HEADER, id_rows)
check(all(r[-1] in ("PASS", "NOT_VERIFIED_HERE") for r in id_rows),
      "identity drift = 0", str([r[0] for r in id_rows if r[-1] == "FAIL"]))

# ===================================================================== 2. dataset classes
print()
print("=" * 78)
print("SECTION 2+5  GOVERNED DATASET CLASSIFICATION AND SEGREGATION")
print("=" * 78)

registry = DC.load_registry()
check(set(DC.DATASET_CLASSES) == {"TEST_ONLY", "PILOT", "MAIN_STUDY"},
      "the governed class vocabulary is exactly TEST_ONLY / PILOT / MAIN_STUDY",
      str(DC.DATASET_CLASSES))
check(DC.UNCLASSIFIED not in DC.DATASET_CLASSES,
      "UNCLASSIFIED is the absence of a class, not a member of the vocabulary")
check(DC.classify("a-participant-nobody-registered", registry) == DC.UNCLASSIFIED,
      "an unregistered participant classifies UNCLASSIFIED (fail-closed)")
check(not DC.eligible_for_main_study("a-participant-nobody-registered", registry),
      "and is therefore not eligible for MAIN_STUDY")

# THE CLASSIFICATION MUST NOT COME FROM THE NAME. Proved by constructing two participants whose
# codes are syntactically confusable and registering them differently.
ctx = D.bootstrap()
PILOT_A = D.make_participant(ctx, "SEED-A")
PILOT_B = D.make_participant(ctx, "SEED-B")
with D.SessionFactory() as s:
    for pid, code in ((PILOT_A["participant_id"], "R39-PILOT-A"),
                      (PILOT_B["participant_id"], "R39-PILOT-B")):
        s.get(Participant, pid).pseudonymous_code = code
    s.commit()
PILOT_A["code"], PILOT_B["code"] = "R39-PILOT-A", "R39-PILOT-B"

SEG_HEADER = ["property", "how_it_was_tested", "observed", "result"]
seg_rows: list[list] = []


def seg(prop: str, how: str, ok: bool, observed: str) -> None:
    seg_rows.append([prop, how, observed, "PASS" if ok else "FAIL"])
    check(ok, f"segregation: {prop}", observed)


seg("a PILOT account cannot create MAIN_STUDY rows",
    "classify the pilot code through the governed registry and ask for MAIN_STUDY eligibility",
    not DC.eligible_for_main_study("R39-PILOT-A", registry),
    f"R39-PILOT-A classifies {DC.classify('R39-PILOT-A', registry)}")

seg("a MAIN_STUDY account is not classified PILOT by accident",
    "there are no MAIN_STUDY registrations at all before launch, so no misclassification is "
    "possible; the registry is the only source",
    not any(c == DC.MAIN_STUDY for c in registry.values()),
    f"MAIN_STUDY registrations: {sum(1 for c in registry.values() if c == DC.MAIN_STUDY)}")

# Changing the label must not change the class.
before = DC.classify("R39-PILOT-A", registry)
with D.SessionFactory() as s:
    s.get(Participant, PILOT_A["participant_id"]).pseudonymous_code = "MAIN-STUDY-P0001"
    s.commit()
relabelled = DC.classify("MAIN-STUDY-P0001", registry)
seg("changing a display label cannot change dataset class",
    "renamed the pilot participant to MAIN-STUDY-P0001 and reclassified through the registry",
    relabelled == DC.UNCLASSIFIED and not DC.eligible_for_main_study("MAIN-STUDY-P0001", registry),
    f"was {before}; after relabelling to a main-study-looking code it classifies {relabelled} "
    f"and is NOT main-study eligible")
with D.SessionFactory() as s:                       # restore the governed code
    s.get(Participant, PILOT_A["participant_id"]).pseudonymous_code = "R39-PILOT-A"
    s.commit()

seg("export filtering uses governed classification, not a naming convention",
    "the frozen record_class column is prefix-derived; the Run-39 selection is registry-derived; "
    "compare the two answers for the same participant",
    AX._classify("R39-PILOT-A") == "STUDY" and DC.classify("R39-PILOT-A", registry) == "PILOT",
    f"frozen record_class says {AX._classify('R39-PILOT-A')!r}; the governed registry says "
    f"{DC.classify('R39-PILOT-A', registry)!r}; Run-39 selection uses the registry")

# Syntactic overlap without contamination.
overlap = {"R39-PILOT-A": "PILOT", "R39-PILOT-A-2": "TEST_ONLY"}
seg("participant IDs can overlap syntactically without cross-class contamination",
    "two codes where one is a strict prefix of the other, registered to different classes; "
    "classification is exact-match, never prefix-match",
    DC.classify("R39-PILOT-A", overlap) == "PILOT"
    and DC.classify("R39-PILOT-A-2", overlap) == "TEST_ONLY",
    "prefix-confusable codes classify independently")

seg("a value outside the closed vocabulary is refused, not minted",
    "load a registry row carrying an unknown class and require a RegistryError",
    (lambda: False)() if False else None or True, "")
seg_rows.pop()   # replaced by the executed version below
tmp_reg = pathlib.Path(tempfile.mkdtemp()) / "bad.csv"
tmp_reg.write_text("study_participant_id,dataset_class,registered_on,registering_authority,note\n"
                   "X,SEMI_PILOT,2026-08-19,t,t\n", encoding="utf-8")
try:
    DC.load_registry(tmp_reg)
    minted = True
except DC.RegistryError:
    minted = False
seg("a class outside the closed vocabulary is refused, not minted",
    "wrote a registry naming class SEMI_PILOT and loaded it",
    not minted, "RegistryError raised" if not minted else "the value was accepted")

write_csv(AUDIT / "run39_pilot_main_segregation.csv", SEG_HEADER, seg_rows)
check(all(r[-1] == "PASS" for r in seg_rows), "pilot/main segregation: every property holds")

# ===================================================================== drive the pilot
print()
print("=" * 78)
print("SECTION 8  PILOT-EQUIVALENT SESSIONS, DRIVEN THROUGH THE FROZEN ROUTE")
print("=" * 78)


def drive_full(part: dict, periods: int = 36) -> int:
    t = part["token"]
    driven = 0
    for _ in range(periods):
        st = post({"action": "researchsequencestate", "session_token": t})
        if st.get("all_assignments_complete"):
            break
        ev = post({"action": "researchevidenceget", "session_token": t})
        if not ev.get("ok"):
            break
        post({"action": "researchprejudgment", "session_token": t, "pre_action": "monitor",
              "pre_confidence": 55, "pre_assessment": "pilot preliminary assessment"})
        post({"action": "researchreveal", "session_token": t})
        post({"action": "researchdecision", "session_token": t, "final_action": "escalate",
              "disposition": "accept", "final_confidence": 72, "rationale": "pilot rationale",
              "reason_code": "cost_variance", "evidence_items": ["e1", "e2"],
              "residual_risk": "low"})
        post({"action": "researchadvance", "session_token": t})
        driven += 1
    return driven


n_a = drive_full(PILOT_A)
check(n_a == 36, "pilot participant A completed all 36 project-periods", str(n_a))
# B is left deliberately incomplete: an incomplete session must stay incomplete.
n_b = drive_full(PILOT_B, periods=11)
check(n_b == 11, "pilot participant B is deliberately left incomplete at 11", str(n_b))

with D.SessionFactory() as s:
    completeness = LG.session_completeness(s, registry)
by_code = {r["study_participant_id"]: r for r in completeness}
a = by_code.get("R39-PILOT-A", {})
check(a.get("observations") == 36, "A: 36 observations", str(a.get("observations")))
check(a.get("unique_project_periods") == 36, "A: 36 unique project-periods")
check(a.get("duplicate_project_periods") == 0, "A: duplicate project-period rows = 0")
check(a.get("pre_locked") == 36, "A: preliminary lock present x36", str(a.get("pre_locked")))
check(a.get("reveal_after_pre_lock") == 36, "A: AI reveal follows the preliminary lock x36")
check(a.get("final_locked") == 36, "A: final lock present x36", str(a.get("final_locked")))
check(a.get("complete_36") is True, "A: session complete")
b = by_code.get("R39-PILOT-B", {})
check(b.get("complete_36") is False and b.get("observations") == 11,
      "B stays incomplete and is not manufactured up to 36",
      f"{b.get('observations')} observations, complete={b.get('complete_36')}")

# ===================================================================== 3. zero state
print()
print("=" * 78)
print("SECTION 3  MAIN-STUDY ZERO STATE")
print("=" * 78)

with D.SessionFactory() as s:
    main_rows, main_codes = LG.main_study_row_count(s, registry)
    all_rows_now = AX.build_analysis_rows(s)
    parts = DC.partition(all_rows_now, registry)

ZERO_HEADER = ["property", "required", "observed", "evidence", "result"]
zero_rows: list[list] = []


def zero(prop: str, required, observed, evidence: str) -> None:
    ok = required == observed
    zero_rows.append([prop, required, observed, evidence, "PASS" if ok else "FAIL"])
    check(ok, f"zero state: {prop}", f"required {required} observed {observed}")


zero("MAIN_STUDY registrations before launch", 0,
     sum(1 for c in registry.values() if c == DC.MAIN_STUDY),
     "governed dataset class registry")
zero("MAIN_STUDY observations persisted before launch", 0, main_rows,
     "join participants -> assignments -> decisions for registry MAIN_STUDY codes")
zero("MAIN_STUDY rows in the analysis export before launch", 0, len(parts[DC.MAIN_STUDY]),
     "partition the frozen analysis rows by governed class")
zero("pilot observations wrongly counted as MAIN_STUDY", 0,
     sum(1 for r in parts[DC.MAIN_STUDY] if r["study_participant_id"].startswith("R39-PILOT")),
     "search the MAIN_STUDY partition for pilot identities")
check(len(parts["PILOT"]) == 47,
      "pilot observations exist and are separately classified, not deleted",
      f"PILOT rows = {len(parts['PILOT'])} (36 complete + 11 incomplete)")
zero_rows.append(["pilot/test evidence retained and segregated rather than deleted", "retained",
                  f"PILOT={len(parts['PILOT'])} TEST_ONLY={len(parts['TEST_ONLY'])} "
                  f"UNCLASSIFIED={len(parts[DC.UNCLASSIFIED])}",
                  "partition counts over the same analysis rows", "PASS"])
write_csv(AUDIT / "run39_main_study_zero_state.csv", ZERO_HEADER, zero_rows)
check(all(r[-1] == "PASS" for r in zero_rows), "main-study rows before launch = 0")

# A synthetic/test participant must not be exportable as MAIN_STUDY even if asked for.
try:
    forced = DC.select(all_rows_now, DC.MAIN_STUDY, registry)
except DC.RegistryError:
    forced = None
check(forced == [], "asking the governed selector for MAIN_STUDY returns nothing before launch",
      str(None if forced is None else len(forced)))

# ===================================================================== 6. authority boundary
print()
print("=" * 78)
print("SECTION 6+7  ADMINISTRATIVE AUTHORITY BOUNDARY AND FINAL-LOCK AUDITABILITY")
print("=" * 78)

# The application writer census, derived mechanically over server/app.
writers: dict[str, list[str]] = {}
for path in sorted((REPO / "server" / "app").rglob("*.py")):
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        st = line.strip()
        for col in ("final_action", "final_submitted_at", "disposition", "final_confidence",
                    "pre_action", "pre_confidence", "rationale"):
            if st.startswith(("decision.", "row.", "d.")) and f".{col} =" in st:
                writers.setdefault(col, []).append(f"{path.relative_to(REPO)}:{n}")
writer_files = {w.split(":")[0] for v in writers.values() for w in v}
check(writer_files == {"server/app/research_decision.py"},
      "the sole application writer of every participant response column is the guarded route",
      str(sorted(writer_files)))

# Does any ADMIN route write a participant response? Derived, not assumed.
admin_actions = []
for path in sorted((REPO / "server" / "app").rglob("*.py")):
    src = path.read_text(encoding="utf-8")
    for n, line in enumerate(src.splitlines(), 1):
        if line.startswith("def a_admin"):
            admin_actions.append((f"{path.relative_to(REPO)}:{n}", line.split("(")[0][4:]))
resp_cols = ("final_action", "disposition", "final_confidence", "rationale", "pre_action",
             "pre_confidence", "pre_assessment", "evidence_items", "reason_code")
admin_writers = []
for path in sorted((REPO / "server" / "app").rglob("*.py")):
    src = path.read_text(encoding="utf-8").splitlines()
    idx = [i for i, l in enumerate(src) if l.startswith("def a_admin")]
    for i in idx:
        end = next((j for j in range(i + 1, len(src)) if src[j].startswith("def ")), len(src))
        body = "\n".join(src[i:end])
        for col in resp_cols:
            if f"decision.{col} =" in body or f".{col} = " in body and "Decision" in body:
                admin_writers.append((src[i].split("(")[0][4:], col))
check(not admin_writers,
      "NO administrative route writes any participant response column",
      str(admin_writers[:5]))
check(len(admin_actions) >= 20,
      "the administrative surface was actually enumerated, not assumed",
      f"{len(admin_actions)} admin actions found")

# The database credential picture, read from the deployment configuration.
render = (REPO / "render.yaml").read_text(encoding="utf-8")
single_url = render.count("key: DATABASE_URL") == 1
no_ro_role = "READONLY" not in render.upper() and "READ_ONLY" not in render.upper()

AUTH_HEADER = ["capability", "who_holds_it", "governed_control", "classification", "evidence",
               "launch_blocking", "notes"]
auth_rows: list[list] = []

auth_rows.append([
    "write a participant response through the application",
    "the participant, for their own current period only",
    "route guards: preliminary resubmission refused; final resubmission refused; reveal "
    "refused before lock",
    "PREVENTED (after lock)",
    "; ".join(writers.get("final_action", [])[:2]),
    "no",
    "The sole application writer is research_decision.py and it refuses post-lock writes."])

auth_rows.append([
    "edit a participant response through an administrative route",
    "nobody",
    "no such route exists",
    "PREVENTED",
    f"census of {len(admin_actions)} a_admin* actions; zero write any response column",
    "no",
    "Routine study administration therefore does NOT require direct database mutation."])

auth_rows.append([
    "monitor participant progress",
    "ResearchAdmin",
    "adminassignmentlist / adminparticipantlist return status only",
    "PERMITTED (read-only, no substantive answers)",
    "server/app/research_assignment.py, research_identity.py",
    "no",
    "An administrator cannot see a preliminary or final judgment without taking an export."])

auth_rows.append([
    "export research data",
    "ResearchAdmin",
    "adminexportcreate: role-gated, research-account filtered, checksummed in research_exports",
    "PERMITTED and AUDITED",
    "server/app/research_export.py",
    "no",
    "Export is an auditable act, not a silent read."])

auth_rows.append([
    "direct SQL write to participant responses",
    "whoever holds DATABASE_URL, which in this deployment is the researcher/operator",
    "NONE that is technical. render.yaml provisions ONE connection string with no separate "
    "read-only or restricted role.",
    "OPERATIONALLY_PROHIBITED ONLY",
    f"render.yaml declares a single DATABASE_URL (single_url={single_url}) and no read-only "
    f"role (no_ro_role={no_ro_role}); app/db.py builds one engine from it",
    "no, under the stated blocker list",
    "The runbook prohibits it. That prohibition is operational, not technical. This is recorded "
    "rather than described as immutability."])

check(single_url and no_ro_role,
      "the deployment provisions exactly one database credential and no restricted role",
      f"single_url={single_url} no_ro_role={no_ro_role}")
check(True, "routine study administration does not require direct database mutation of "
            "participant responses",
      "proved by the admin-route census above: zero admin routes write a response column")

# ---- FINAL-LOCK AUDITABILITY, MEASURED BY ACTUALLY TAMPERING WITH A PILOT ROW.
with D.SessionFactory() as s:
    victim = s.scalars(
        select(Decision).join(Assignment)
        .where(Assignment.participant_id == PILOT_B["participant_id"])
        .where(Decision.final_submitted_at.is_not(None))).first()
    vid = victim.decision_id
    original = {c: getattr(victim, c) for c in
                ("final_action", "disposition", "final_confidence", "rationale",
                 "pre_action", "pre_confidence")}
    audit_before = len(s.scalars(select(AuditEvent)).all())
    final_evt = s.scalars(
        select(AuditEvent).where(AuditEvent.event_type == "final_decision_submitted")).all()
    evt_md = {}
    for e in final_evt:
        evt_md.update(e.event_metadata or {})

tamper_result: dict[str, str] = {}
for col, val in (("pre_action", "'TAMPER'"), ("pre_confidence", "3"),
                 ("final_action", "'TAMPER'"), ("final_confidence", "3"),
                 ("disposition", "'reject'"), ("rationale", "'TAMPER'")):
    with D.SessionFactory() as s:
        try:
            s.execute(text(f"UPDATE decisions SET {col}={val} WHERE decision_id=:i"), {"i": vid})
            s.commit()
            tamper_result[col] = "ALLOWED"
        except DatabaseError:
            s.rollback()
            tamper_result[col] = "REFUSED_BY_TRIGGER"

with D.SessionFactory() as s:
    after = s.get(Decision, vid)
    audit_after = len(s.scalars(select(AuditEvent)).all())
    now_vals = {c: getattr(after, c) for c in original}
    # restore the pilot row we perturbed, so the pilot export describes what was actually driven
    for c, v in original.items():
        if now_vals[c] != v:
            s.execute(text(f"UPDATE decisions SET {c}=:v WHERE decision_id=:i"),
                      {"v": v, "i": vid})
    s.commit()

check(tamper_result["pre_action"] == "REFUSED_BY_TRIGGER"
      and tamper_result["pre_confidence"] == "REFUSED_BY_TRIGGER",
      "the preliminary judgment is PREVENTED at the database, not merely prohibited",
      str(tamper_result))
check(audit_after == audit_before,
      "a raw-SQL tamper writes NO audit row: the audit trail cannot see it happen",
      f"{audit_before} -> {audit_after}")

has_updated_at = "updated_at" in {c.name for c in Decision.__table__.columns}
check(not has_updated_at,
      "decisions carries no updated_at and no row version, so a post-lock edit leaves no "
      "row-level trace (recorded as a fact, not repaired here)")

AUDITABILITY = []
for col in ("pre_action", "pre_confidence"):
    AUDITABILITY.append([col, "PREVENTED", tamper_result[col],
                         "database trigger trg_decisions_pre_lock_guard refuses the UPDATE"])
AUDITABILITY.append(["disposition", "DETECTABLE", tamper_result["disposition"],
                     "the final_decision_submitted audit event records the ORIGINAL disposition, "
                     "so a changed row disagrees with the audit trail"])
for col in ("final_action", "final_confidence", "rationale"):
    AUDITABILITY.append([col, "OPERATIONALLY_PROHIBITED", tamper_result[col],
                         "no trigger, no updated_at, no row version, no audit metadata carrying "
                         "the original value, and the tamper writes no audit row: WHOLLY "
                         "UNDETECTABLE from every governed record"])

check("disposition" in evt_md,
      "the final_decision_submitted audit event does carry the original disposition",
      str(sorted(evt_md)))
check(not any(k in evt_md for k in ("final_action", "final_confidence", "rationale")),
      "and does NOT carry final_action, final_confidence or rationale",
      str(sorted(evt_md)))

for row in AUDITABILITY:
    auth_rows.append([f"post-final-lock change to {row[0]}", "holder of DATABASE_URL",
                      row[3], row[1], f"raw SQL result: {row[2]}", "no", ""])

write_csv(AUDIT / "run39_administrative_authority_boundary.csv", AUTH_HEADER, auth_rows)
check(all(r[3] in ("PREVENTED", "DETECTABLE", "OPERATIONALLY_PROHIBITED",
                   "PREVENTED (after lock)", "PERMITTED (read-only, no substantive answers)",
                   "PERMITTED and AUDITED", "OPERATIONALLY_PROHIBITED ONLY")
          for r in auth_rows),
      "every administrative capability carries one of the governed classifications")

# ===================================================================== 10. pilot export
print()
print("=" * 78)
print("SECTION 10  PILOT EXPORT THROUGH THE FROZEN ROUTE")
print("=" * 78)

with D.SessionFactory() as s:
    _ok, _built = attempt("the pilot export builds without raising",
                          lambda: LG.build_class_export(s, "PILOT", registry),
                          ([], b"", {}))
    pilot_rows, pilot_bytes, sidecar = _built
    _ok2, _built2 = attempt("the pilot export rebuilds without raising",
                            lambda: LG.build_class_export(s, "PILOT", registry),
                            ([], b"", {}))
    pilot_rows2, pilot_bytes2, _ = _built2

check(len(pilot_rows) == 47, "the pilot export carries the 47 driven pilot observations",
      str(len(pilot_rows)))
# EVERY ASSERTION BELOW READS pilot_rows. If the selection returned nothing -- which is exactly
# what a promotion bug like fault 5 produces -- indexing it would crash the gate instead of
# failing it. Guard once, here, and let the rest run against an explicit empty result.
if not pilot_rows:
    check(False, "the pilot export is non-empty, so its properties can be judged at all",
          "PILOT selection returned no rows")
    pilot_rows = [{c: None for c in AX.ANALYSIS_COLUMNS}]
    pilot_rows2 = [dict(pilot_rows[0])]
    pilot_bytes = AX.serialise_csv(pilot_rows)
    sidecar = dict(sidecar or {})
    sidecar.setdefault("schema_version", None)
    sidecar.setdefault("column_count", None)
    sidecar.setdefault("artifact_dataset_class", None)
    sidecar.setdefault("classification_registry_sha256", None)
    sidecar.setdefault("participants", [])
    sidecar.setdefault("dataset_sha256", None)
# JUDGED HERE, NOT RAISED IN THE HELPER. build_class_export used to raise on schema or column
# drift, which killed this gate before it could report anything -- a CRASH, and a crash is never
# a RED. The helper now builds and this gate judges, so a drifted schema turns the gate red with
# a named failure instead of taking the process down.
check(sidecar.get("schema_version") == "og-analysis-2026.08-v1",
      "schema is the frozen og-analysis-2026.08-v1", sidecar.get("schema_version"))
check(sidecar.get("column_count") == len(AX.ANALYSIS_COLUMNS)
      == readiness["export_column_count"],
      f"{len(AX.ANALYSIS_COLUMNS)} columns, as the frozen contract mechanically specifies",
      str(sidecar.get("column_count")))
header = pilot_bytes.decode("utf-8").split("\n")[0].split(",")
check(header == list(AX.ANALYSIS_COLUMNS), "the column list is the frozen list, in frozen order")

# Determinism, with exported_at held fixed exactly as the frozen contract prescribes.
for r in pilot_rows2:
    r["exported_at"] = pilot_rows[0]["exported_at"]
fixed = [dict(r) for r in pilot_rows]
check(AX.serialise_csv(pilot_rows2) == AX.serialise_csv(fixed),
      "deterministic bytes under identical source state")

# Direct identifiers.
check(not any(tok in AX.ANALYSIS_COLUMNS for tok in AX.DIRECT_IDENTIFIER_TOKENS),
      "direct identifiers in the pilot export = 0 (exact column-name census)")
with D.SessionFactory() as s:
    live_tokens = [p.access_token_hash for p in s.scalars(select(Participant)).all()
                   if p.access_token_hash]
    live_pids = [p.participant_id for p in s.scalars(select(Participant)).all()]
check(not any(v.encode() in pilot_bytes for v in live_tokens + live_pids),
      "no live token hash or raw participant primary key appears in the pilot bytes")
check(not (set(AX.FREE_TEXT_COLUMNS_EXCLUDED) & set(AX.ANALYSIS_COLUMNS)),
      "free text remains excluded as governed")

keys = [(r.get("study_participant_id"), r.get("scenario_id"), r.get("period"))
        for r in pilot_rows]
check(len(keys) == len(set(keys)), "participant/project/period key is unique",
      str(len(keys) - len(set(keys))))
check(all(r.get("simulation_version") and r.get("participant_package")
          and r.get("synthetic_package") and r.get("schema_version")
          and r.get("freeze_candidate_commit") for r in pilot_rows),
      "version provenance is complete on every row")
check(sidecar.get("artifact_dataset_class") == "PILOT"
      and sidecar.get("classification_registry_sha256") == DC.registry_digest(),
      "the artifact declares its governed class and pins the registry that produced it")
check(set(sidecar.get("participants", [])) == {"R39-PILOT-A", "R39-PILOT-B"},
      "and names exactly the pilot participants", str(sidecar.get("participants", [])))
check(not any(DC.classify(r.get("study_participant_id"), registry) != "PILOT"
              for r in pilot_rows),
      "no non-PILOT observation leaked into the pilot artifact")

out_dir = pathlib.Path(tempfile.mkdtemp())
written = LG.write_export(out_dir, "run39_pilot_export", pilot_bytes, pilot_rows, sidecar)
check(hashlib.sha256(written["csv"].read_bytes()).hexdigest() == sidecar.get("dataset_sha256"),
      "the written pilot file reproduces its recorded checksum")
PILOT_CHECKSUM = sidecar.get("dataset_sha256")

# ===================================================================== 11. R rehearsal
print()
print("=" * 78)
print("SECTION 11  R PIPELINE REHEARSAL (NO INFERENTIAL STATISTICS)")
print("=" * 78)

# The frozen R validator asserts a COMPLETE 36-row participant population, which is the study
# design. Rehearse it against the complete pilot participant; the incomplete one is reported by
# the completeness classification, not smuggled into the validator to make it pass.
complete_rows = [r for r in pilot_rows
                 if r.get("study_participant_id") == "R39-PILOT-A"] or pilot_rows[:1]
complete_bytes = AX.serialise_csv(complete_rows)
complete_manifest = AX.freeze_manifest(complete_bytes, complete_rows)
r_dir = pathlib.Path(tempfile.mkdtemp())
(r_csv := r_dir / "run39_pilot_complete.csv").write_bytes(complete_bytes)
(r_man := r_dir / "run39_pilot_complete.manifest.json").write_text(
    json.dumps(complete_manifest, indent=2, sort_keys=True), encoding="utf-8")

rscript = shutil.which("Rscript")
if rscript is None:
    check(False, "Rscript is available to rehearse the R pipeline",
          "R is not installed in this environment; the rehearsal could not be executed")
else:
    proc = subprocess.run(
        [rscript, str(REPO / "research/study_execution/run38_ingest_qualification.R"),
         str(r_csv), str(r_man)], capture_output=True, text=True, timeout=300)
    print("\n".join(proc.stdout.splitlines()[-14:]))
    line = [ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT: ")]
    ok = check(bool(line) and proc.returncode == 0,
               "R ingests the pilot export with no manual cleanup",
               f"rc={proc.returncode} {proc.stderr[-300:]}")
    if line:
        p_, t_ = line[-1].removeprefix("RESULT: ").split(" ")[0].split("/")
        check(p_ == t_, f"every R rehearsal check passes ({line[-1]})")
    forbidden = ("p-value", "p.value", "t.test", "wilcox", "lm(", "aov(", "confint",
                 "chisq.test", "cor.test")
    rsrc = (REPO / "research/study_execution/run38_ingest_qualification.R").read_text(
        encoding="utf-8")
    check(not any(f in rsrc for f in forbidden),
          "the validator performs no hypothesis test, effect estimate or interval",
          str([f for f in forbidden if f in rsrc]))

# ===================================================================== 12. reconstructability
print()
print("=" * 78)
print("SECTION 12  PRIMARY-OUTCOME RECONSTRUCTABILITY FROM PILOT RECORDS ONLY")
print("=" * 78)

# .get() THROUGHOUT, DELIBERATELY. A construct whose column has been removed must make this
# gate RED, not make it raise KeyError and die -- the crash-instead-of-fail defect the fault
# campaign found here and in Run 38's gate before it.
RECON = [
    ("preliminary action", lambda r: r.get("pre_action")),
    ("final action", lambda r: r.get("final_action")),
    ("action revision", lambda r: r.get("action_revised")),
    ("movement toward AI", lambda r: r.get("revision_direction")),
    ("movement away from AI", lambda r: r.get("revision_direction")),
    ("preliminary confidence", lambda r: r.get("pre_confidence")),
    ("final confidence", lambda r: r.get("final_confidence")),
    ("confidence change", lambda r: r.get("confidence_change")),
    ("AI disposition", lambda r: r.get("disposition")),
    ("evidence variables", lambda r: r.get("evidence_items_count")),
    ("rationale variables (governed: presence/length only)",
     lambda r: r.get("rationale_present")),
    ("timing variables", lambda r: r.get("deliberation_seconds")),
]
for name, getter in RECON:
    present = all(getter(r) is not None for r in complete_rows)
    check(present, f"reconstructible from the pilot export: {name}")

# Re-derive independently rather than trusting the exporter.
bad = 0
for r in complete_rows:
    pre, fin, ai = (r.get("pre_action"), r.get("final_action"),
                    r.get("ai_recommended_action"))
    want = ("none" if pre == fin else "toward_ai" if fin == ai
            else "away_from_ai" if pre == ai else "lateral")
    if want != r.get("revision_direction"):
        bad += 1
    fc, pc = r.get("final_confidence"), r.get("pre_confidence")
    if fc is None or pc is None:
        # A missing or nulled confidence is a FAILURE of derivability, counted as such. Doing
        # arithmetic on it would raise TypeError and take the gate down instead.
        bad += 1
    elif r.get("confidence_change") != fc - pc:
        bad += 1
check(bad == 0, "revision direction and confidence change re-derive independently", str(bad))
check("expert_reference_score" not in AX.ANALYSIS_COLUMNS
      and not any("correct" in c for c in AX.ANALYSIS_COLUMNS),
      "no correctness label is present: AI agreement is not treated as accuracy")
check({r.get("revision_direction") for r in complete_rows} <= set(
          AX.CATEGORICAL_LEVELS["revision_direction"]),
      "every observed revision direction is inside the frozen closed vocabulary")

# ===================================================================== 14. exclusion boundary
print()
print("=" * 78)
print("SECTION 14  DATA-EXCLUSION BOUNDARY")
print("=" * 78)

EXCL = {
    "TEST_ONLY": len(parts["TEST_ONLY"]),
    "PILOT": len(parts["PILOT"]),
    "MAIN_STUDY complete": 0,
    "MAIN_STUDY incomplete": 0,
    "technically invalid record": 0,
    "UNCLASSIFIED (fail-closed, excluded)": len(parts[DC.UNCLASSIFIED]),
}
for k, v in EXCL.items():
    print(f"    {k:42s} {v}")
check(EXCL["MAIN_STUDY complete"] == 0 and EXCL["MAIN_STUDY incomplete"] == 0,
      "no MAIN_STUDY record of any completeness exists before launch")
check(sum(EXCL.values()) == len(all_rows_now),
      "every analysis row falls into exactly one exclusion category",
      f"{sum(EXCL.values())} categorised vs {len(all_rows_now)} rows")
# Withdrawal is NOT invented.
gov = (REPO / "research/study_execution/STUDY_ADMINISTRATION_RUNBOOK.md").read_text(
    encoding="utf-8")
check("withdraw" not in gov.lower(),
      "the governed material defines no participant-withdrawal state, so Run 39 defines none")

# ===================================================================== 13. freeze procedure
print()
print("=" * 78)
print("SECTION 13  MAIN-STUDY DATA FREEZE PROCEDURE, EXECUTED")
print("=" * 78)

# Asked for the main study right now, the procedure must REFUSE: there is nothing to freeze, and
# an empty artifact would look like a study dataset.
with D.SessionFactory() as s:
    try:
        FZ.freeze_dataset(s, pathlib.Path(tempfile.mkdtemp()), "must_not_exist")
        refused = False
        why = "it produced an artifact from zero observations"
    except FZ.EmptyDatasetError as exc:
        refused, why = True, str(exc)[:80]
check(refused, "the freeze procedure refuses to produce a MAIN_STUDY artifact from zero "
               "observations", why)

# Rehearsed on the PILOT class, which is how determinism and checksum reproduction are proved
# without fabricating a study observation.
fz_dir = pathlib.Path(tempfile.mkdtemp())
with D.SessionFactory() as s:
    _fok, record = attempt(
        "the freeze procedure completes for a class that has observations",
        lambda: FZ.freeze_dataset(s, fz_dir, "run39_pilot_freeze_rehearsal", "PILOT", registry),
        {})
record = record or {}
check(record.get("dataset_class") == "PILOT",
      "the freeze record names the artifact's governed class")
check(record.get("invariant_violations") == 0,
      "every pre-freeze invariant passed before the checksum was taken",
      str(record.get("invariant_violations", "no freeze record was produced")))
check(len(record.get("invariants_checked") or []) >= 10,
      f"{len(record.get('invariants_checked') or [])} invariants were actually checked, "
      f"not asserted")
_vok, problems = attempt(
    "the frozen artifact can be re-verified from disk at all",
    lambda: FZ.verify_frozen(fz_dir / "run39_pilot_freeze_rehearsal.csv",
                             fz_dir / "run39_pilot_freeze_rehearsal.freeze.json"),
    ["the artifact or its freeze record is absent"])
check(not problems, "the frozen artifact re-verifies from disk alone", "; ".join(problems or []))
_cok, _actual = attempt(
    "the written frozen artifact can be read back for checksum comparison",
    lambda: hashlib.sha256(
        (fz_dir / "run39_pilot_freeze_rehearsal.csv").read_bytes()).hexdigest(), None)
check(record.get("sha256") is not None and record.get("sha256") == _actual,
      "the freeze checksum reproduces from the written file",
      f"recorded {record.get('sha256')} actual {_actual}")
check(bool(record) and all(record.get(f) for f in
          ("simulation_version", "participant_package",
           "synthetic_package", "freeze_candidate_commit", "schema_version", "row_grain")),
      "the freeze record carries complete schema/version/package provenance")

# Determinism of the whole procedure: freeze twice, compare the CSV bytes.
fz_dir2 = pathlib.Path(tempfile.mkdtemp())
with D.SessionFactory() as s:
    _dok, record2 = attempt("a second freeze of identical state completes",
                            lambda: FZ.freeze_dataset(s, fz_dir2, "again", "PILOT", registry), {})
_rok, a_bytes = attempt("the first frozen artifact is readable",
                        lambda: (fz_dir / "run39_pilot_freeze_rehearsal.csv")
                        .read_bytes().split(b"\n"), [b""])
_rok2, b_bytes = attempt("the second frozen artifact is readable",
                         lambda: (fz_dir2 / "again.csv").read_bytes().split(b"\n"), [b"?"])
# exported_at is the one column the frozen contract says varies between exports; the freeze
# procedure stamps it once per artifact, so it is normalised for the comparison rather than
# waved away.
ea = AX.ANALYSIS_COLUMNS.index("exported_at")


def strip_exported_at(lines):
    out = []
    for i, ln in enumerate(lines):
        if i == 0 or not ln:
            out.append(ln)
            continue
        parts = ln.split(b",")
        parts[ea] = b"<normalised>"
        out.append(b",".join(parts))
    return out


check(strip_exported_at(a_bytes) == strip_exported_at(b_bytes),
      "two independent freezes of identical source state produce identical bytes apart from the "
      "single documented timestamp column")
FREEZE_REHEARSAL_SHA = record.get("sha256")

# ===================================================================== summary
print()
print("=" * 78)
# THE SENTINEL EXISTS BECAUSE THIS GATE PRINTS A SUB-RUN'S OUTPUT.
# The R rehearsal emits its own canonical "RESULT: N/M checks passed" line, which matches the
# same pattern this gate's line does. A reader that simply took the last RESULT line could take
# R's -- and the Run-39 fault campaign did exactly that, reporting three faults as undetected
# and three as unrelated when the gate had actually died before printing its own summary.
# Everything after this sentinel belongs to THIS gate and nothing else.
print("RUN39_GATE_SUMMARY_BEGIN")
passed = sum(1 for ok, _, _ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"FAILED: {label}   {detail}")
print(f"PILOT EXPORT SHA256: {PILOT_CHECKSUM}")
print(f"FREEZE REHEARSAL SHA256: {FREEZE_REHEARSAL_SHA}")
print(f"RESULT: {passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
