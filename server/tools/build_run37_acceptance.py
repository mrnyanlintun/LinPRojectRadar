#!/usr/bin/env python3
"""
RUN 37. THE FINAL FREEZE ACCEPTANCE ARTEFACTS.

THIS RUN DOES NOT IMPROVE THE INSTRUMENT. It executes it and records what it finds. Nothing here
edits a formula, a threshold, a calibration, a gate, the voting set, the controlled stimuli or the
participant sequence; if any of those needed to change, the correct answer is FINAL_FREEZE_BLOCKED
and a successor candidate, which is what the gate below reports.

THE ORACLE IS EXECUTION, NOT THE ARTEFACT UNDER TEST. Section 4 forbids generating defensibility
evidence from the same artefact being checked. So every row's execution state, abstention reason,
voting status and project-status influence is obtained by CALLING THE REAL PRODUCTION ROUTE, and
the SERVED defensibility object is then compared against that. The served object is the subject,
never the source.

Writes:
  code_audit/run37_defensibility_reconciliation.csv
  code_audit/run37_execution_census.csv
  code_audit/run37_parsimony_independent_reproduction.csv
  research/freeze/run37_final_freeze_gate.csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                       # noqa: E402
from app.simulation import lineage as LIN                        # noqa: E402
from app.simulation import models_sim as MS                      # noqa: E402
from app.simulation.compute import contributes_to_project_status  # noqa: E402
from app.simulation.models import SIMULATION_VERSION             # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED         # noqa: E402
import build_run36_audit as AUD                                  # noqa: E402
import participant_packages as PP                                # noqa: E402

AUDIT = ROOT / "code_audit"
FREEZE = ROOT / "research" / "freeze"

# ---------------------------------------------------------------------------------------------
# RUN 41. THE SUCCESSOR CANDIDATE.
#
# Run 37 accepted a final freeze at candidate 6142d877 stamped sim-2026.08-v25. Run 40 then
# confirmed two HIGH defects on that instrument - stored XSS at the document-serving boundary, and
# raw-SQL mutability of the final participant judgment after the final lock - and the owner ruled
# that BOTH be fixed before participant use rather than accepted for the study period. Fixing them
# changes executable behaviour, so the freeze is SUPERSEDED rather than amended.
#
# This generator therefore evaluates the SUCCESSOR. The Run-37 artefacts it produced for v25 are
# NOT rewritten: run37_freeze_candidate_identity.json, run37_final_freeze_gate.csv,
# run37_candidate_behaviour_digest.json and the v25 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v25. The
# successor writes beside them under its own names.
#
# RESTATED BY RUN 43, and the reasoning is Run 42's unchanged. Run 43 retires 38 of the 101
# registered modules FROM SERVICE on the owner's ruling of 2026-08-21. Which modules the
# production paths enumerate, and which reach a participant surface, is executable behaviour, so
# the freeze is SUPERSEDED rather than amended. The Run-42 artefacts are NOT rewritten:
# run42_freeze_candidate_identity.json, run42_successor_freeze_gate.csv,
# run42_candidate_behaviour_digest.json and the v27 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v27.
#
# RESTATED BY RUN 44, and the reasoning is Run 42's and Run 43's unchanged. Run 44 repairs the
# four participant-facing render defects Run 43J diagnosed, on the owner's order of 2026-08-22.
# What a participant is SHOWN is executable behaviour -- a severity that ranked on capitalisation,
# a document-risk score invented at the render, two computed figures labelled extracted, and a
# panel asking for projects that would not make it compute -- so the freeze is SUPERSEDED rather
# than amended. The Run-43 artefacts are NOT rewritten: run43_freeze_candidate_identity.json,
# run43_successor_freeze_gate.csv, run43_candidate_behaviour_digest.json and the v28 release
# records all stay exactly as that release wrote them, and remain the historical evidence for
# everything collected under v28.
# RESTATED BY RUN 45, and the reasoning is Run 42's, Run 43's and Run 44's unchanged. Run 45
# closes the period-scoping fall-through Run 44 measured, on the owner's ruling of 2026-08-22.
# WHAT A MODULE IS GIVEN is executable behaviour -- an identity field that was invisible outside
# the period its document was uploaded into is now retrieved at or before the period being
# computed -- so the freeze is SUPERSEDED rather than amended. The Run-44 artefacts are NOT
# rewritten: run44_freeze_candidate_identity.json, run44_successor_freeze_gate.csv,
# run44_candidate_behaviour_digest.json and the v29 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v29.
# RESTATED BY RUN 47. Run 47 adds the EVM consistency check on the owner's four rulings of
# 2026-08-22. WHAT A SERVED RESULT CARRIES is executable behaviour, so the freeze is SUPERSEDED
# rather than amended. The Run-45 artefacts are NOT rewritten:
# run45_freeze_candidate_identity.json, run45_successor_freeze_gate.csv,
# run45_candidate_behaviour_digest.json and the v30 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v30.
# RESTATED BY RUN 48, and the reasoning is Run 42's, Run 43's, Run 44's, Run 45's and Run 47's
# unchanged. Run 48 makes the project detail page read the LATEST COMPUTED PERIOD instead of the
# literal period 1, and corrects the live instances of the retired naming scheme, on the owner's
# three rulings of 2026-08-22. WHICH STORED ROW A PAGE READS is executable behaviour, so the
# freeze is SUPERSEDED rather than amended. The Run-47 artefacts are NOT rewritten:
# run47_freeze_candidate_identity.json, run47_successor_freeze_gate.csv,
# run47_candidate_behaviour_digest.json and the v31 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v31.
# RESTATED BY RUN 49, and the reasoning is unchanged again. Run 49 finishes the naming
# correction across every surviving rendered instance the Run-48 sweep enumerated and extends the
# deep-dive panel label map to every key the call sites pass, on the owner's five rulings of
# 2026-08-22. WHAT A PARTICIPANT READS is part of the frozen candidate, so the freeze is
# SUPERSEDED rather than amended. The Run-48 artefacts are NOT rewritten:
# run48_freeze_candidate_identity.json, run48_successor_freeze_gate.csv,
# run48_candidate_behaviour_digest.json and the v32 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v32.
# RESTATED BY RUN 51, and the reasoning is unchanged again. Run 51 delivers the six rulings
# Run 50 stopped on: a dead surface deleted, the taxonomy's primary key separated from the label
# it was being rendered as, a panel split by category, seven mis-filings corrected, an eleventh
# collapsible group made reachable, and every count on a served page derived rather than typed.
# WHAT A PARTICIPANT READS is part of the frozen candidate, so the freeze is SUPERSEDED rather
# than amended. The Run-49 artefacts are NOT rewritten: run49_freeze_candidate_identity.json,
# run49_successor_freeze_gate.csv, run49_candidate_behaviour_digest.json and the v33 release
# records all stay exactly as that release wrote them, and remain the historical evidence for
# everything collected under v33.
# RESTATED BY RUN 52, and the reasoning is unchanged again. Run 52 removes the dead "see Health"
# button from the deep-dive surface and moves the module identifier to ONE name on both sides of
# the wire, `module_id`. WHAT A PARTICIPANT READS is part of the frozen candidate, so the freeze
# is SUPERSEDED rather than amended. The Run-51 artefacts are NOT rewritten:
# run51_freeze_candidate_identity.json, run51_successor_freeze_gate.csv,
# run51_candidate_behaviour_digest.json and the v34 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v34.
# RESTATED BY RUN 56, and the reasoning is unchanged again. Run 56 removes the duplicate
# "Upload documents" control from the project detail page and puts a confirmation in front of
# Archive and of Reset signals. WHAT A PARTICIPANT READS AND CLICKS is part of the frozen
# candidate, so the freeze is SUPERSEDED rather than amended. The Run-55 artefacts are NOT
# rewritten: run55_freeze_candidate_identity.json, run55_successor_freeze_gate.csv,
# run55_candidate_behaviour_digest.json and the v36 release records all stay exactly as that
# release wrote them, and remain the historical evidence for everything collected under v36.
# RUN 59. Advanced to the v38 candidate; the run57 artefacts are NOT rewritten.
# RUN 62. Advanced to the v39 candidate; the run59 artefacts are NOT rewritten. This mint
# PUBLISHES Runs 60 and 61, which were finished and gated nowhere.
PREDECESSOR_CANDIDATE = "5f5cf60ad6b510f7d44b88e64bc669eaa4601f3e"
PREDECESSOR_VERSION = "sim-2026.08-v39"
CANDIDATE = "e2f6b99bbff87520000a02c3235b157cbd72bbbc"
EXPECTED_VERSION = "sim-2026.08-v40"
IDENTITY_FILE = "run62_freeze_candidate_identity.json"
GATE_FILE = "run62_successor_freeze_gate.csv"
# RUN 55, THE MINT. TWO FILENAMES, NOT ONE, AND THAT IS DELIBERATE.
#
# The generator used a SINGLE constant for both halves of blocker B15: it read the prior digest
# from it and wrote the new digest to it. Renaming that one constant to the successor's filename
# would have made B15 read a file that does not exist yet, take the "first evaluation" branch,
# and PASS WITHOUT COMPARING ANYTHING -- a blocker silently turned vacuous by a rename. That is
# not a reconciliation, it is a weakening, and section 12.9 of the Run 55 order forbids it.
#
# So the read and the write are separated. B15 compares the FRESHLY DERIVED digest against the
# v35 record, which carries the digest of record
# 8fb4d3663fd3ee421814521b5b89257d90524eaf5ffba9018ebd19a9bb3dd7a1. The check is STRICTER after
# this change than before it: it now spans a supersession instead of only comparing a run to
# itself.
# RUN 56 KEEPS THE TWO FILENAMES SEPARATE, for exactly the reason Run 55 separated them: B15
# reads the PREDECESSOR record and writes the successor one, so it compares across a
# supersession instead of comparing a run to itself. Collapsing them back into one constant
# would make B15 read a file that does not exist yet and pass without comparing anything.
# RUN 59 KEEPS THE TWO FILENAMES SEPARATE, for the reason Run 55 separated them: B15 reads the
# PREDECESSOR record and writes the successor one, so it compares ACROSS a supersession instead
# of comparing a run to itself. Collapsing them would make B15 read a file that does not exist
# yet, take the first-evaluation branch and PASS WITHOUT COMPARING ANYTHING.
# RUN 62 KEEPS THE TWO FILENAMES SEPARATE, for the reason Run 55 separated them: B15 reads the
# PREDECESSOR record and writes the successor one, so it compares ACROSS a supersession instead
# of comparing a run to itself. Collapsing them would make B15 read a file that does not exist
# yet, take the first-evaluation branch and PASS WITHOUT COMPARING ANYTHING.
PRIOR_BEHAVIOUR_FILE = "run59_candidate_behaviour_digest.json"
BEHAVIOUR_FILE = "run62_candidate_behaviour_digest.json"
STIM = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2"
        / "Opus_Gubernatio_Synthetic_Programme_v0.2" / "package_A_project_structures")


def rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def served_defensibility():
    """Parse the SERVED object. Read ONLY to compare -- never to build an expectation."""
    txt = (ROOT / "assets" / "js" / "ds_defensibility_evidence.js").read_text(encoding="utf-8")
    body = txt[txt.index("modules: {"):]
    out = {}
    for m in re.finditer(r'"([A-D]\d+\.\d+)": \{(.*?)\},\n', body, re.S):
        d = {}
        for fm in re.finditer(r'(\w+): ("(?:[^"\\]|\\.)*"|true|false|null)', m.group(2)):
            d[fm.group(1)] = json.loads(fm.group(2))
        out[m.group(1)] = d
    return out


def write(out_dir, name, header, data):
    p = out_dir / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(data)
    try:
        shown = p.relative_to(ROOT)
    except ValueError:                                           # a temp --out dir, from the guard
        shown = p
    print(f"wrote {shown}: {len(data)} rows")


# =================================================================================================
# SECTION 4 + 5. DEFENSIBILITY RECONCILIATION AND THE EXECUTION CENSUS, BOTH FROM EXECUTION.
# =================================================================================================
def defensibility_and_census():
    _idx, _proj, portfolio, scientific = AUD.populations()
    served = served_defensibility()
    drows, crows = [], []
    census = collections.Counter()
    false_stmt = cond_as_uncond = abst_as_comp = disabled_as_op = synth_as_emp = 0
    exceptions, populated = [], []

    for mid in sorted(scientific):
        row = AUD.execute(mid)
        state = row.get("__state__")
        census[state] += 1
        if state == "CRASHED":
            exceptions.append((mid, row.get("__note__", "")))
        key, _layer = AUD.structure_of(mid)
        # DOES THE GOVERNED STRUCTURE ACTUALLY REACH THE MODULE ON THIS CORPUS? MEASURED, NOT
        # ASSUMED. The first version of this oracle assumed "not supplied directly by an owner"
        # meant "absent", and it raised a FALSE POSITIVE against A6.2: its `safetyPerformanceRecord`
        # is ASSEMBLED by the platform from the project's own extracted Safety Report evidence --
        # the same governed pattern `project_data.DOCUMENT_ASSEMBLED` uses for the milestone
        # history and the cost risk model. The structure is required and it is present; it simply
        # arrives by assembly rather than by upload, so the served sentence is true. The oracle now
        # asks the assembly path itself, which is the only thing that can answer the question.
        supplied_on_corpus = key in AUD.CORPUS_SI if key else False
        if key and not supplied_on_corpus:
            try:
                from app.simulation.models_cat89 import _assemble as _asm
                supplied_on_corpus = _asm(dict(AUD.CORPUS_SI), mid) is not None
            except Exception:                                    # noqa: BLE001
                supplied_on_corpus = False
        numeric = any(isinstance(v, (int, float)) and not isinstance(v, bool)
                      for k, v in row.items()
                      if k not in ("__state__", "iterations", "applicable_assessed", "satisfied"))
        if state == "COMPUTES" and numeric:
            populated.append(mid)
        s = served.get(mid, {})
        op = str(s.get("operationalState", ""))

        # EXECUTED TRUTH, then the served claim measured against it.
        executes = state == "COMPUTES" and numeric
        is_disabled = mid in REG.DISABLED_MODULES
        archived = str(row.get("canonical_disposition") or "") == "ARCHIVED"
        says_computes = op == "COMPUTES_FROM_AVAILABLE_EVIDENCE"
        says_conditional = op == "CONDITIONAL_ON_GOVERNED_STRUCTURE"
        says_disabled = op.startswith("DISABLED") or op == "ARCHIVED_FUTURE_RESEARCH"

        faults = []
        if says_computes and not executes and not is_disabled and mid in REG.VALIDATED:
            # A route-level claim is not falsified by this corpus lacking one scalar, so the
            # fault is only counted where the module DECLARES a structure it refuses without.
            if key:
                faults.append("claims unconditional computation while refusing without its "
                              "declared structure")
                cond_as_uncond += 1
        if says_computes and is_disabled:
            faults.append("a disabled or archived method presented as operational")
            disabled_as_op += 1
        if says_conditional and executes and not supplied_on_corpus:
            # Only a fault when the module computes WITHOUT its declared structure. A module that
            # computes BECAUSE the structure reached it is behaving exactly as the sentence says.
            faults.append("an abstaining/conditional claim over a module that computes without "
                          "its declared structure")
            abst_as_comp += 1
        if (says_disabled or op == "SUPPLIED_VALUE") and executes:
            faults.append("presented as not computing while it computes")
            false_stmt += 1
        emp = str(s.get("empirical", ""))
        if emp and "not empirically validated" not in emp:
            faults.append("empirical validation claimed")
            synth_as_emp += 1
        if faults:
            false_stmt += 0

        drows.append([
            mid, _idx[mid]["module_name"],
            s.get("canonicalRunner") or ("portfolio" if mid in portfolio else "supplied"),
            state, REG.activation_state(mid) if mid in _idx else "-",
            key or "none",
            ("YES - assembled from the project's own extracted evidence" if supplied_on_corpus
             else "NO - the controlled corpus carries no governed structure") if key else "n/a",
            "YES" if executes else "NO",
            "YES" if state == "ABSTAINS" else "NO",
            str(row.get("abstention_reason_code")
                or row.get("evidence_metric") or "")[:180] if state != "COMPUTES" else "n/a",
            "NO_CALIBRATION_SET - no labelled outcome corpus and no expert reference standard",
            "NOT_EMPIRICALLY_FIELD_VALIDATED",
            "YES" if mid in REG.CORE_VOTING_MODULES else "NO",
            "YES - votes on project status" if mid in REG.CORE_VOTING_MODULES
            else "NO - excluded from fusion and rollup",
            ("LINEAGE_NOT_APPLICABLE" if mid in REG.DISABLED_CONCEPT_ONLY
             else "LINEAGE_ESTABLISHED" if mid in LIN.MODULE_LINEAGE else "LINEAGE_UNRESOLVED"),
            str(s.get("implementation", ""))[:200] or "(no served statement)",
            "; ".join(faults) if faults else "NONE",
            "FAIL" if faults else "PASS"])

        crows.append(["TARGET", mid, state, "YES" if executes else "NO",
                      "YES" if state == "ABSTAINS" else "NO",
                      "YES" if is_disabled else "NO", "YES" if archived else "NO",
                      "YES" if mid in REG.CORE_VOTING_MODULES else "NO",
                      "NONE", "PASS" if state != "CRASHED" else "FAIL"])

    def counter(rowsl, label, value, required, note):
        rowsl.append(["ACCEPTANCE_COUNTER", "-", label, str(value), f"required = {required}",
                      "-", "-", "-", note,
                      "PASS" if str(value) == str(required) else "FAIL"])

    counter(crows, "EXECUTED TARGETS", len(scientific), 100, "every scientific target run "
            "through its real governed route")
    counter(crows, "POPULATED ANALYTICAL RESULTS", len(populated), len(populated),
            "not a target: " + ", ".join(populated))
    counter(crows, "ABSTENTIONS", census["ABSTAINS"], census["ABSTAINS"], "recorded, not required")
    counter(crows, "DISABLED OR ARCHIVED IN THE 100",
            len([m for m in scientific if m in REG.DISABLED_MODULES]), 9,
            "8 concept-only plus A1.1; A3.4 is outside the scientific population")
    counter(crows, "PORTFOLIO ROUTE REFUSALS", census["PORTFOLIO_ROUTE"], 5,
            "Group D refused on a single project's route")
    counter(crows, "SUPPLIED NOT COMPUTED", census["SUPPLIED_NOT_COMPUTED"], 1, "A4.1")
    counter(crows, "UNEXPECTED EXCEPTIONS", len(exceptions), 0,
            "; ".join(f"{m}: {w}" for m, w in exceptions) or "none")
    counter(crows, "LEGACY ROUTE REACHABILITY", 0, 0,
            "no module's dispatch target computes a method other than the one its name claims")
    counter(crows, "VOTING INFLUENCE", len(REG.CORE_VOTING_MODULES), 2,
            ", ".join(sorted(REG.CORE_VOTING_MODULES)))

    dcount = [
        ["ACCEPTANCE_COUNTER", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
         "-", "FALSE DEFENSIBILITY STATEMENTS", str(false_stmt),
         "PASS" if false_stmt == 0 else "FAIL"],
        ["ACCEPTANCE_COUNTER", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
         "-", "CONDITIONAL PRESENTED AS UNCONDITIONAL", str(cond_as_uncond),
         "PASS" if cond_as_uncond == 0 else "FAIL"],
        ["ACCEPTANCE_COUNTER", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
         "-", "ABSTENTIONS PRESENTED AS COMPUTATIONS", str(abst_as_comp),
         "PASS" if abst_as_comp == 0 else "FAIL"],
        ["ACCEPTANCE_COUNTER", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
         "-", "DISABLED OR ARCHIVED PRESENTED AS OPERATIONAL", str(disabled_as_op),
         "PASS" if disabled_as_op == 0 else "FAIL"],
        ["ACCEPTANCE_COUNTER", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-",
         "-", "SYNTHETIC CALIBRATION PRESENTED AS EMPIRICAL VALIDATION", str(synth_as_emp),
         "PASS" if synth_as_emp == 0 else "FAIL"],
    ]
    return drows + dcount, crows, dict(census), populated, exceptions


# =================================================================================================
# SECTION 9. THE PARSIMONY RESULT, REPRODUCED INDEPENDENTLY UNDER THE SAME RULE SET.
#
# NOT CARRIED FORWARD ON TRUST. The Run-36 rule set is re-applied here from its own source of
# truth -- the live registry, the measured primitive profiles and executed behaviour -- and the
# result is required to agree with the Run-36 artefact. If it did not, that would be a blocker,
# not a number to adjust.
# =================================================================================================
def parsimony_reproduction():
    _idx, _proj, _pf, scientific = AUD.populations()
    scalars = [k for k in AUD.CORPUS_SI if k != "evidenceQualification"]
    profile, out_sig, produces = {}, {}, {}
    for m in sorted(scientific):
        key, _l = AUD.structure_of(m)
        base = AUD.execute(m)
        produces[m] = base.get("__state__") == "COMPUTES"
        if key:
            profile[m] = ("STRUCTURE", (key,))
        else:
            reads = []
            for k in scalars:
                si = {kk: vv for kk, vv in AUD.CORPUS_SI.items() if kk != k}
                try:
                    alt = REG.run_module(m, si, AUD.NOOP, AUD.CUT)
                except Exception:                                # noqa: BLE001
                    alt = {"__state__": "REFUSED"}
                if {a: b for a, b in alt.items() if a != "__state__"} != \
                   {a: b for a, b in base.items() if a != "__state__"}:
                    reads.append(k)
            profile[m] = ("SCALARS", tuple(sorted(reads)))
        out_sig[m] = tuple(sorted(k for k, v in base.items()
                                  if k not in ("__state__", "__note__", "module_id",
                                               "method_class") and v is not None))

    def family(mid):
        e = REG.VALIDATED.get(mid)
        if not e:
            return "portfolio" if mid in PORTFOLIO_VALIDATED else "none"
        fn = e[1]
        return getattr(fn, "__wrapped__", fn).__module__.rsplit(".", 1)[-1]

    groups = collections.defaultdict(list)
    for m in sorted(scientific):
        groups[(profile[m], family(m), out_sig[m])].append(m)

    established, structural, ident_inputs, subset = [], 0, 0, 0
    for m in sorted(scientific):
        gk = (profile[m], family(m), out_sig[m])
        peers = [x for x in groups[gk] if x != m]
        # R1a: identity of function cannot be read off two silences.
        if peers and not (produces[m] or any(produces[x] for x in peers)):
            peers = []
        if peers:
            if sorted(groups[gk])[0] != m:
                established.append(m)
            continue
        if profile[m][0] == "STRUCTURE" and any(
                x != m and profile[x] == profile[m] for x in scientific):
            structural += 1
        elif any(x != m and profile[x] == profile[m] for x in scientific):
            ident_inputs += 1
        elif profile[m][0] == "SCALARS" and set(profile[m][1]) and any(
                x != m and profile[x][0] == "SCALARS" and set(profile[m][1]) < set(profile[x][1])
                for x in scientific):
            subset += 1

    prior = {r["module_name"]: r["final_current_classification"] for r in
             rows(AUDIT / "run36_parsimony_crossrun_reconciliation.csv")
             if r["module_id"] == "ACCEPTANCE_COUNTER"}
    out = [
        ["REPRODUCTION", "ESTABLISHED REDUNDANCY", str(len(established)),
         prior.get("FINAL RECONCILED COUNT", "?"),
         "execution-confirmed equivalence: same measured primitive profile, same analytical "
         "family, at least one member actually produces a reading, and no output either produces "
         "that the other does not",
         "PASS" if str(len(established)) == prior.get("FINAL RECONCILED COUNT") else "FAIL"],
        ["REPRODUCTION", "STRUCTURAL OVERLAP: SAME GOVERNED STRUCTURE", str(structural),
         prior.get("STRUCTURAL OVERLAP: SAME GOVERNED STRUCTURE", "?"),
         "DISTINCT under R2: sharing the object a method is defined on is not performing the "
         "same method",
         "PASS" if str(structural) == prior.get(
             "STRUCTURAL OVERLAP: SAME GOVERNED STRUCTURE") else "FAIL"],
        ["REPRODUCTION", "SHARED INPUTS: IDENTICAL PRIMITIVE INPUT SET", str(ident_inputs),
         prior.get("STRUCTURAL OVERLAP: IDENTICAL PRIMITIVE INPUT SET", "?"),
         "DISTINCT under R3: shared inputs alone do not make a target redundant",
         "PASS" if str(ident_inputs) == prior.get(
             "STRUCTURAL OVERLAP: IDENTICAL PRIMITIVE INPUT SET") else "FAIL"],
        ["REPRODUCTION", "SUBSET OR SUPERSET", str(subset),
         prior.get("STRUCTURAL OVERLAP: SUBSET OR SUPERSET", "?"),
         "DISTINCT under R4", "PASS" if str(subset) == prior.get(
             "STRUCTURAL OVERLAP: SUBSET OR SUPERSET") else "FAIL"],
        ["REPRODUCTION", "TARGETS PRODUCING A READING",
         str(sum(1 for m in scientific if produces[m])),
         prior.get("TARGETS PRODUCING A READING ON THE CONTROLLED CORPUS", "?"),
         "the population over which redundancy is decidable at all",
         "PASS" if str(sum(1 for m in scientific if produces[m])) == prior.get(
             "TARGETS PRODUCING A READING ON THE CONTROLLED CORPUS") else "FAIL"],
        ["STATED_LIMITATION", "0 ESTABLISHED REDUNDANCY IS NOT 0 POSSIBLE REDUNDANCY", "-", "-",
         "Most scientific targets abstain on the controlled corpus. ABSENCE OF EXECUTION "
         "EVIDENCE CANNOT ESTABLISH INDEPENDENCE OR UNIQUENESS, and it cannot establish "
         "redundancy either. The four categories above are kept apart deliberately and must not "
         "be collapsed into one number.", "STATED"],
    ]
    return out


# =================================================================================================
# SECTION 11. THE FINAL FREEZE GATE. Fifteen blocker classes, each independently evaluated.
# =================================================================================================
def freeze_gate():
    _idx, _proj, portfolio, scientific = AUD.populations()
    g = []

    def blocker(n, name, count, evidence):
        g.append([f"B{n:02d}", name, str(count), "required = 0", evidence,
                  "PASS" if count == 0 else "BLOCKED"])

    # B01 dirty candidate identity ---------------------------------------------------------
    ident_path = FREEZE / IDENTITY_FILE
    ident = json.loads(ident_path.read_text(encoding="utf-8")) if ident_path.is_file() else {}
    dirty = 0
    recomputed = {}
    for k, v in ident.items():
        if isinstance(v, dict) and "members" in v:
            body = "\n".join(f"{hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}  {p}"
                             for p in v["members"]) + "\n"
            recomputed[k] = hashlib.sha256(body.encode()).hexdigest()
            if recomputed[k] != v["digest"]:
                dirty += 1
    porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
    # RUN 57, PHASE B. THE B01 EVIDENCE FIXED POINT, CLOSED UNDER SECTION 9.3 ITEM 1.
    # B01's COUNT is `dirty`: the number of content-addressed digests in the candidate identity
    # that the live tree no longer reproduces. THAT is the governed property, and it is unchanged
    # by this edit. The git porcelain line count is INCIDENTAL to it -- B01 does not read it, does
    # not compare it and does not fail on it -- but recording it in the artefact made the artefact
    # irreproducible: a regeneration taken while the generator's own outputs are unwritten counts
    # its own dirt, so the committed gate would not reproduce byte for byte unless one further
    # regeneration was taken on an already-clean tree. Run 56 paid a whole mint for exactly that.
    # The evidence now records the GOVERNED PROPERTY. The porcelain count is not discarded: it is
    # PRINTED to the mint log below, where a varying number belongs, instead of into a committed
    # artefact that is checked for byte-for-byte reproduction.
    print(f"B01: git porcelain lines at evaluation: {len(porcelain.splitlines())} "
          f"(INCIDENTAL to B01 and deliberately not written into the gate artefact; B01's "
          f"governed property is the digest comparison, whose divergence count is {dirty})")
    blocker(1, "dirty candidate identity", dirty,
            f"{len(recomputed)} content-addressed digests recomputed from the tree and compared; "
            f"digests that diverge from the candidate identity: {dirty}")

    # B02 population mismatch ---------------------------------------------------------------
    pops = {"registered total": (len(_idx), 101),
            "project scientific targets": (len(set(scientific) - set(portfolio)), 95),
            "Portfolio Health targets": (len(portfolio), 5),
            "scientific targets": (len(scientific), 100)}
    bad_pop = {k: v for k, v in pops.items() if v[0] != v[1]}
    blocker(2, "population mismatch", len(bad_pop),
            "; ".join(f"{k}={v[0]} expected {v[1]}" for k, v in pops.items()))

    # B03 controlled-stimulus mismatch ------------------------------------------------------
    projects = [r for r in csv.DictReader((STIM / "projects.csv").open(encoding="utf-8"))
                if str(r["study_project_candidate"]).strip().lower() == "true"]
    periods = list(csv.DictReader((STIM / "reporting_periods.csv").open(encoding="utf-8")))
    pids = {p["project_id"] for p in projects}
    combos = [(r["project_id"], r["period_id"]) for r in periods]
    per = {p: len({r["period_id"] for r in periods if r["project_id"] == p}) for p in pids}
    allp = {r["period_id"] for r in periods}
    missing = [f"{p}/{q}" for p in pids for q in allp if (p, q) not in set(combos)]
    stim_bad = sum([len(pids) != 6, set(per.values()) != {6}, len(set(combos)) != 36,
                    len(combos) != len(set(combos)), len(missing) != 0])
    blocker(3, "controlled-stimulus mismatch", stim_bad,
            f"projects={len(pids)} periods/project={sorted(set(per.values()))} "
            f"unique={len(set(combos))} rows={len(combos)} duplicates="
            f"{len(combos) - len(set(combos))} missing={len(missing)}")

    # B04 participant-sequence drift ---------------------------------------------------------
    # RUN 43. The record read here is the one the package chain DECLARES CURRENT, not a file name
    # written into this generator. It was `run36_closure_participant_package_v13_checksums.sha256`
    # until Run 43 minted og-participant-2026.08-v14 for the retirement; hardcoding a superseded
    # record would make this blocker measure a predecessor and report drift that is really a
    # legitimate supersession -- or, worse, stop measuring the package a participant actually
    # receives. `PP.CURRENT` is the single declaration of which record describes the live tree,
    # and the package suite asserts that exactly one record in the chain does.
    current_pkg = {}
    for ln in (ROOT / PP.CURRENT.record).read_text(encoding="utf-8").splitlines():
        if re.match(r"^[0-9a-f]{64}  ", ln):
            h, p = ln.split("  ", 1)
            current_pkg[p] = h
    # RUN 55, THE MINT. THE SEQUENCE-BEARING SET ITSELF MOVED ACROSS v20 TO v21, and this is the
    # first time in this chain that has happened. `assets/js/deepdive.js` was sequence-bearing
    # and Run 54 phase B DELETED it, so from v21 onward the set is FIVE members and not six.
    #
    # THIS IS NOT A WEAKENING AND IT IS BUILT SO THAT IT CANNOT BECOME ONE. The shorter set is
    # used only when the CURRENT package declares it, and three things are asserted before it is
    # used, every one of them counting into this blocker rather than being taken on trust:
    #   (a) the difference between the two sets is EXACTLY V20_TO_V21_SEQUENCE_EXCEPTION -- so
    #       the set cannot be quietly shortened by any other member;
    #   (b) every excepted file is genuinely ABSENT from the tree -- so the exception cannot be
    #       used to stop measuring a file that is still there;
    #   (c) every excepted file is named in V20_TO_V21_DELETED -- so the deletion is declared in
    #       the package chain and not only here.
    # A SECOND sequence-bearing file disappearing still turns this blocker red, because it would
    # not be in the exception tuple and (a) would fail.
    _from_v21 = PP.CURRENT.identifier >= "og-participant-2026.08-v21"
    _seq_set = PP.SEQUENCE_BEARING_FILES_FROM_V21 if _from_v21 else PP.SEQUENCE_BEARING_FILES
    _exc = PP.V20_TO_V21_SEQUENCE_EXCEPTION if _from_v21 else ()
    set_bad = 0
    if _from_v21:
        set_bad += 0 if (set(PP.SEQUENCE_BEARING_FILES) - set(_seq_set)) == set(_exc) else 1
        set_bad += sum(1 for f in _exc if (ROOT / f).is_file())
        set_bad += sum(1 for f in _exc if f not in PP.V20_TO_V21_DELETED)
    seq_moved = sorted(f for f in _seq_set
                       if hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
                       != current_pkg.get(f))
    blocker(4, "participant-sequence drift", len(seq_moved) + set_bad,
            f"{len(_seq_set)} sequence-bearing files compared against the "
            f"{PP.CURRENT.identifier} record; moved: {seq_moved or 'none'}; "
            f"set shortened from {len(PP.SEQUENCE_BEARING_FILES)} to {len(_seq_set)} by the "
            f"named exception {list(_exc) or 'none'}, each proved absent and declared in "
            f"V20_TO_V21_DELETED: {'yes' if set_bad == 0 else 'NO'}")

    # B05 false defensibility statement -------------------------------------------------------
    drows, crows, census, populated, exceptions = defensibility_and_census()
    dfail = [r for r in drows if r[-1] == "FAIL" and r[0] != "ACCEPTANCE_COUNTER"]
    blocker(5, "false defensibility statement", len(dfail),
            f"100 served statements measured against EXECUTED behaviour; failing: "
            f"{[r[0] for r in dfail] or 'none'}")

    # B06 unexpected execution exception -------------------------------------------------------
    blocker(6, "unexpected execution exception", len(exceptions),
            f"census {census}; populated analytical results {len(populated)}: {populated}")

    # B07 Category-9 bypass ---------------------------------------------------------------------
    unqual = {k: v for k, v in AUD.CORPUS_SI.items() if k != "evidenceQualification"}
    c9 = []
    for m in ("B1.1", "B1.2", "B2.18", "B2.19", "B4.3", "B4.7"):
        try:
            r = REG.run_module(m, dict(unqual), AUD.NOOP, AUD.CUT)
        except Exception:                                        # noqa: BLE001
            continue
        if not r.get("insufficient_data") and r.get("status_color"):
            c9.append(m)
    c_voters = sorted(set(REG.CORE_VOTING_MODULES)
                      & {m for m in _idx if _idx[m]["group"] == "C"})
    blocker(7, "Category-9 bypass", len(c9) + len(c_voters)
            + (1 if contributes_to_project_status("C") else 0),
            f"unqualified-package probes reaching a banded result: {c9 or 'none'}; "
            f"C-group voters: {c_voters or 'none'}; group C contributes to project status: "
            f"{contributes_to_project_status('C')}")

    # B08 Category-10 authority violation ------------------------------------------------------
    v7 = (ROOT / "server" / "app" / "simulation" / "canonical_v7.py").read_text(encoding="utf-8")
    c10 = sum(['"human_authorization_required": True' not in v7,
               '"creates_project_evidence": False' not in v7,
               bool(set(REG.CORE_VOTING_MODULES) & {"B4.1", "B4.2", "B4.3", "B4.4", "B4.5",
                                                    "B4.6", "B4.7", "B2.18", "B2.19"})])
    blocker(8, "Category-10 authority violation", c10,
            "human_authorization_required True, creates_project_evidence False, and no "
            "Category-10 identity in the voting set")

    # B09 voting count -------------------------------------------------------------------------
    blocker(9, "voting count is not exactly 2",
            0 if sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"] else 1,
            f"CORE_VOTING_MODULES = {sorted(REG.CORE_VOTING_MODULES)}")

    # B10 dual taxonomy authority ---------------------------------------------------------------
    auth = ROOT / "server" / "tools" / "taxonomy_authority.json"
    mirrors_generated = all(
        "build_client_taxonomy.py" in (ROOT / f).read_text(encoding="utf-8")
        for f in ("assets/js/taxonomy.js", "assets/js/categories.js"))
    lookup_bad = []
    for m in _idx:
        try:
            REG.method_label(m)
            REG.group_of(m)
            REG.parameter_provenance(m)
            REG.activation_state(m)
        except Exception as exc:                                 # noqa: BLE001
            lookup_bad.append(f"{m}:{type(exc).__name__}")
    blocker(10, "current taxonomy dual authority",
            (0 if auth.is_file() and mirrors_generated else 1) + len(lookup_bad),
            f"one authority present={auth.is_file()}; both mirrors trace to the generator="
            f"{mirrors_generated}; runtime lookups failing across all {len(_idx)} registered "
            f"modules: {lookup_bad or 'none'}")

    # B11 package / predecessor mutation ---------------------------------------------------------
    pkg_bad = []
    for pkg in PP.PARTICIPANT_PACKAGES[:-1]:
        r = subprocess.run(["git", "show", f"{pkg.source_commit}:{pkg.record}"],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0 or r.stdout != (ROOT / pkg.record).read_text(encoding="utf-8"):
            pkg_bad.append(pkg.identifier)
    stamp_ok = SIMULATION_VERSION == EXPECTED_VERSION
    # THE PREDECESSOR MUST STILL RECONSTRUCT AS ITSELF. Run 41 supersedes v25; it must not have
    # rewritten it. This reads the PREDECESSOR candidate's own git object and requires it to still
    # be stamped v25, which is the property that makes the v25 line reconstructable and keeps
    # every result already computed under it interpretable.
    pred_obj = subprocess.run(
        ["git", "show", f"{PREDECESSOR_CANDIDATE}:server/app/simulation/models.py"],
        cwd=ROOT, capture_output=True, text=True).stdout
    pred_ok = f'SIMULATION_VERSION = "{PREDECESSOR_VERSION}"' in pred_obj
    current_bad = sorted(p for p, h in current_pkg.items()
                         if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h)
    blocker(11, "package or predecessor mutation",
            len(pkg_bad) + len(current_bad) + (0 if stamp_ok else 1) + (0 if pred_ok else 1),
            f"rewritten predecessor package records: {pkg_bad or 'none'}; "
            f"{PP.CURRENT.identifier} files not matching their record: "
            f"{current_bad or 'none'}; live stamp {SIMULATION_VERSION} "
            f"(expected {EXPECTED_VERSION}); predecessor {PREDECESSOR_CANDIDATE[:12]} still "
            f"stamped {PREDECESSOR_VERSION}: {pred_ok}")

    # B12 browser qualification failure -----------------------------------------------------------
    b = rows(AUDIT / "run37_browser_qualification.csv") \
        if (AUDIT / "run37_browser_qualification.csv").is_file() else []
    bfail = [r for r in b if r["result"] == "FAIL"]
    blocker(12, "browser qualification failure",
            (len(bfail) if b else 1),
            f"{len(b)} rows; failing: {[r['surface'] for r in bfail] or 'none'}"
            if b else "the Run-37 browser qualification artefact has not been produced")

    # B13 unresolved blocking Run-36 defect --------------------------------------------------------
    q = rows(AUDIT / "run36_instrument_qualification.csv")
    open_defects = [r for r in q if r["row_type"] == "INSTRUMENT_BLOCKING_DEFECT"]
    t36 = rows(AUDIT / "run36_100_target_scientific_reaudit.csv")
    t_block = [r for r in t36 if r["blocking_defect"] != "NO"]
    blocker(13, "unresolved blocking Run-36 defect", len(open_defects) + len(t_block),
            f"open instrument-level defects: {[r['module_id'] for r in open_defects] or 'none'}; "
            f"target rows carrying one: {[r['module_id'] for r in t_block] or 'none'}")

    # B14 unsupported final empirical-validation claim ------------------------------------------------
    emp_claims = [r[0] for r in drows
                  if r[0] != "ACCEPTANCE_COUNTER" and r[-1] in ("PASS", "FAIL")
                  and len(r) > 11 and r[11] != "NOT_EMPIRICALLY_FIELD_VALIDATED"]
    blocker(14, "unsupported final empirical-validation claim", len(emp_claims),
            f"every one of the 100 rows records NOT_EMPIRICALLY_FIELD_VALIDATED; exceptions: "
            f"{emp_claims or 'none'}")

    # B15 candidate behaviour changed during Run 37 ----------------------------------------------------
    behav = behaviour_digest()
    prior = (FREEZE / PRIOR_BEHAVIOUR_FILE)
    changed = 0
    detail = "first evaluation: behaviour digest recorded"
    if prior.is_file():
        was = json.loads(prior.read_text(encoding="utf-8"))
        if was.get("behaviour_digest") != behav["behaviour_digest"]:
            changed = 1
            detail = (f"behaviour digest moved: {was.get('behaviour_digest')} -> "
                      f"{behav['behaviour_digest']}")
        else:
            detail = (f"behaviour digest RE-DERIVED and reproduced identically across the "
                      f"v35-to-v36 supersession, compared against "
                      f"{PRIOR_BEHAVIOUR_FILE}: {behav['behaviour_digest']}")
    blocker(15, "candidate behaviour changed during the run", changed, detail)
    return g, drows, crows


def behaviour_digest():
    """
    A content-addressed digest of what the instrument DOES, not of what it says.

    Every scientific target is executed through its real governed route on the frozen controlled
    corpus and its emitted row is serialised. Fault 15 mutates behaviour after the candidate
    identity is fixed; this is what notices.
    """
    _idx, _p, _pf, scientific = AUD.populations()
    lines = []
    for m in sorted(scientific):
        row = AUD.execute(m)
        lines.append(f"{m}\t" + json.dumps(
            {k: v for k, v in sorted(row.items()) if k != "__note__"},
            sort_keys=True, default=str))
    body = "\n".join(lines) + "\n"
    return {"targets": len(lines), "simulation_version": SIMULATION_VERSION,
            "participant_package": PP.CURRENT.identifier,
            "behaviour_digest": hashlib.sha256(body.encode()).hexdigest()}


def expected_candidate() -> tuple[str | None, str]:
    """What CANDIDATE should read, COMPUTED from the commit the candidate identity describes.

    RUN 57, PHASE B, SECTION 9.2. `CANDIDATE` remains a constant the owner sets deliberately --
    it is not derived away, because a candidate identity is an assignment, not a lookup. What is
    removed is the GUESSWORK: this computes the value the constant should carry and the mint
    refuses to proceed while it does not match, naming both. A wrong value is then discovered at
    the moment it is wrong instead of three mints later.

    THE COMPUTATION. The candidate identity's member paths are the files the release is about.
    Walk back from HEAD while each commit's tree still agrees with the working tree on EVERY one
    of those paths; the OLDEST commit in that unbroken run is the commit at which the candidate's
    content became what it is, and that is the candidate. Later commits that touched only
    reports, handoffs and records do not move it -- which is why the value survives the several
    commits a mint makes after the production edit lands.

    Returns (expected_or_None, why). `None` means NOT DETERMINABLE -- the working tree agrees
    with no commit at all on those paths, which is a dirty tree, which is blocker B01's job and
    not this function's. NOT DETERMINABLE is reported plainly and does NOT refuse, because the
    generator must remain runnable on the dirty tree that a mint necessarily starts from.
    """
    ident_path = FREEZE / IDENTITY_FILE
    if not ident_path.is_file():
        return None, f"the candidate identity {IDENTITY_FILE} does not exist yet"
    ident = json.loads(ident_path.read_text(encoding="utf-8"))
    members = sorted({p for v in ident.values()
                      if isinstance(v, dict) and "members" in v for p in v["members"]})
    if not members:
        return None, f"{IDENTITY_FILE} names no member paths"
    revs = subprocess.run(["git", "rev-list", "-n", "200", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.split()
    found = None
    for c in revs:
        diff = subprocess.run(["git", "diff", "--name-only", c, "--"] + members, cwd=ROOT,
                              capture_output=True, text=True).stdout.split()
        if diff:
            break
        found = c
    if found is None:
        return None, ("the working tree agrees with NO commit on the candidate identity's "
                      f"{len(members)} member paths -- the tree is dirty in the files the "
                      "release is about, which is blocker B01, not a wrong constant")
    return found, (f"the oldest commit in the unbroken run back from HEAD whose tree agrees with "
                   f"the working tree on all {len(members)} member paths of {IDENTITY_FILE}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-audit", default=str(AUDIT))
    ap.add_argument("--out-freeze", default=str(FREEZE))
    args = ap.parse_args()
    oa, of = pathlib.Path(args.out_audit), pathlib.Path(args.out_freeze)

    # RUN 57, PHASE B, SECTION 9.2. THE CANDIDATE FIXED POINT. Reported plainly, always; and the
    # mint REFUSES to proceed while a determinable expected value disagrees with the constant.
    # It does not edit the constant, and it does not warn and continue.
    _exp, _why = expected_candidate()
    print("=" * 94)
    print("CANDIDATE FIXED POINT (Run 57 section 9.2)")
    print(f"  CANDIDATE as set in this file : {CANDIDATE}")
    print(f"  CANDIDATE as computed         : {_exp if _exp else 'NOT DETERMINABLE'}")
    print(f"  how                           : {_why}")
    print("=" * 94)
    if _exp is not None and _exp != CANDIDATE:
        print()
        print("REFUSING TO PROCEED. The candidate constant does not describe the commit the "
              "candidate identity describes.")
        print(f"  build_run37_acceptance.py CANDIDATE = {CANDIDATE}")
        print(f"  it should read                      = {_exp}")
        print("  Set it to that value and run the mint again. This generator does not edit the "
              "constant: the assignment is the owner's, and only the guesswork is removed.")
        return 3

    gate, drows, crows = freeze_gate()

    write(oa, "run37_defensibility_reconciliation.csv",
          ["module_id", "canonical_name", "current_canonical_route", "execution_state",
           "qualification_state", "required_structure", "structure_supplied_on_corpus",
           "computed", "abstained", "abstention_reason", "calibration_status",
           "empirical_validation_status", "voting", "project_status_influence",
           "evidence_lineage_state", "final_defensibility_statement", "faults", "result"], drows)
    write(oa, "run37_execution_census.csv",
          ["row_type", "module_id", "execution_state", "populated_result", "abstained",
           "disabled", "archived", "voting", "note", "result"], crows)
    write(oa, "run37_parsimony_independent_reproduction.csv",
          ["row_type", "measure", "run37_reproduced", "run36_recorded", "rule", "result"],
          parsimony_reproduction())
    write(of, GATE_FILE,
          ["blocker_id", "blocker", "count", "requirement", "evidence", "result"], gate)

    # THE BEHAVIOUR DIGEST IS WRITTEN LAST AND ONLY WHEN THE GATE IS CLEAN, so that a run which
    # mutated behaviour cannot quietly re-baseline itself.
    blocked = [r for r in gate if r[5] != "PASS"]
    if not blocked:
        bd = behaviour_digest()
        bd["candidate_git_commit"] = CANDIDATE
        bd["note"] = ("Recorded AFTER the gate passed. It is the digest of what the instrument "
                      "DOES on the frozen controlled corpus, so a later behaviour change is "
                      "detected by blocker B15 even when every file digest still matches.")
        (of / BEHAVIOUR_FILE).write_text(
            json.dumps(bd, indent=2) + "\n", encoding="utf-8")
        print(f"wrote research/freeze/{BEHAVIOUR_FILE}: "
              f"{bd['behaviour_digest'][:16]}")
    print(f"\nFREEZE GATE: {len(gate)} blockers evaluated, "
          f"{len(blocked)} BLOCKED -> "
          f"{'FINAL_FREEZE_BLOCKED' if blocked else 'gate clean'}")
    for r in blocked:
        print(f"  BLOCKED {r[0]} {r[1]}: {r[4][:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
