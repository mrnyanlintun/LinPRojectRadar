#!/usr/bin/env python3
"""
RUN 21, SECTION 9. THE CATEGORY-9 AND LINEAGE CONTROLS, AS THEY SURVIVE TRANSPORT AND
PRESENTATION.

WHAT THIS DOES AND DOES NOT CLAIM. Run 20 established the lineage model, the Category-9
qualification gate, the raw-bypass refusal and the anti-feedback rejection, and proved each by
deliberate violation. NONE OF THAT IS REDESIGNED OR RE-DERIVED HERE, and this file deliberately
does not restate the combination arithmetic: specification 24 forbids a second copy of a
function as its own oracle. What Run 21 must show is narrower and was never shown before: that
the website cannot BYPASS those controls through its projection and presentation code.

THE THREE WAYS A FRONTEND COULD UNDO A BACKEND LINEAGE CONTROL, and how each is closed:

  1. BY RECOMPUTING. If the browser held its own combination rule it could fuse the same signals
     again without the lineage partition, and the double-counting Run 20 removed from the server
     would reappear on screen. Section 2 proves NO file the participant route loads contains a
     combination entry point, by scanning the shipped index.html script list, and proves the
     scanner works by finding those entry points where they really do live.

  2. BY LOSING THE STRUCTURE IN TRANSPORT. If the fusion result reached the client as a band and
     nothing else, a reader could not tell two corroborating bodies from two views of one, and
     any per-row aggregation would silently treat them as independent. Section 1 executes the
     REAL shipped fusion and asserts the body structure it publishes -- how many bodies, which
     module represents each, whether the separation was exact, and whether conflict is estimable.

  3. BY FLATTENING QUALIFICATION. If an unqualified or abstaining signal arrived indistinguishable
     from a qualified one, the page would have no way to render the difference. Section 3
     asserts the qualification and abstention codes are carried on the exported/API row.

Every guard is proved capable of failing in section 4.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run21_lineage_presentation.py
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}: {detail}")
        print(f"  FAIL  {label}  {detail}")


from app.simulation.fusion import fuse_signals  # noqa: E402
from app.simulation.lineage import lineage_record  # noqa: E402

print("=" * 78)
print("SECTION 1  the structure a reader needs is PUBLISHED by the fusion, not just a band")
print("=" * 78)

# Two signals declared to rest on the SAME primitive source: one body of evidence, whatever the
# module ids are. This is the shape the lineage control exists to handle.
same_body = [
    {"module_id": "A1.7", "status": "Amber",
     "lineage": dict(lineage_record("A1.7"), primitive_source_ids=["fact:ev"],
                     evidence_relationship="SAME_SOURCE_TRANSFORM")},
    {"module_id": "A1.8", "status": "Amber",
     "lineage": dict(lineage_record("A1.8"), primitive_source_ids=["fact:ev"],
                     evidence_relationship="SAME_SOURCE_TRANSFORM")},
]
# Two signals resting on DISJOINT primitive sources: genuinely two bodies, and real
# corroboration that the control must NOT destroy.
two_bodies = [
    {"module_id": "A1.7", "status": "Amber",
     "lineage": dict(lineage_record("A1.7"), primitive_source_ids=["fact:ev"],
                     evidence_relationship="INDEPENDENT")},
    {"module_id": "A3.5", "status": "Amber",
     "lineage": dict(lineage_record("A3.5"), primitive_source_ids=["fact:overhead"],
                     evidence_relationship="INDEPENDENT")},
]

one = fuse_signals(same_body)
two = fuse_signals(two_bodies)

for name, res in (("one body", one), ("two bodies", two)):
    check(isinstance(res, dict), f"{name}: the fusion publishes a result")
    for key in ("lineage_groups", "lineage_bodies", "conflict_estimable",
                "body_selection_exact", "lineage_declared"):
        check(key in res, f"{name}: the result carries {key}, so a reader can tell "
                          f"corroboration from repetition", str(sorted(res))[:200])

check(one["lineage_groups"] == 1,
      "SAME-LINEAGE: two transforms of one body are published as ONE body of evidence",
      f"lineage_groups={one['lineage_groups']} bodies={one.get('lineage_bodies')}")
check(two["lineage_groups"] == 2,
      "INDEPENDENT: two disjoint bodies are still published as TWO, so real corroboration "
      "is not destroyed", f"lineage_groups={two['lineage_groups']}")

# THE PROPERTY THE DOUBLE-COUNTING DEFECT VIOLATED, stated on the published numbers rather than
# recomputed: adding a second view of the SAME body must not sharpen belief the way a second
# INDEPENDENT body does.
single = fuse_signals([same_body[0]])
check(abs(one["mass"]["Amber"] - single["mass"]["Amber"]) < 1e-9,
      "SAME-LINEAGE: a second view of one body does not sharpen belief at all",
      f"single={single['mass']['Amber']} duplicated={one['mass']['Amber']}")
check(two["mass"]["Amber"] > single["mass"]["Amber"] + 1e-9,
      "INDEPENDENT: a genuinely independent second body still does sharpen it",
      f"single={single['mass']['Amber']} two-bodies={two['mass']['Amber']}")
check(one.get("conflict") in (0, 0.0) or not one.get("conflict_estimable"),
      "SAME-LINEAGE: one body of evidence does not report disagreement with itself",
      f"conflict={one.get('conflict')} estimable={one.get('conflict_estimable')}")

print()
print("=" * 78)
print("SECTION 2  the browser holds no combination rule, so it cannot recreate the "
      "double-counting")
print("=" * 78)

# The entry points of the combination, named from the server's own module.
COMBINATION_ENTRY_POINTS = ("dst_combine", "dst_fuse", "fuse_signals", "fuse_qualified",
                            "dstCombine", "dstFuse", "fuseSignals")

index_scripts = [s.lstrip("./") for s in
                 re.findall(r'<script[^>]+src="([^"]+)"', INDEX)]
participant_js = [ROOT / s for s in index_scripts if s.startswith("assets/js/")]
check(len(participant_js) > 20,
      "the participant route's script list was really read, so the scan below is not vacuous",
      str(len(participant_js)))

offenders = []
for path in participant_js:
    if not path.is_file():
        continue
    body = path.read_text(encoding="utf-8")
    for name in COMBINATION_ENTRY_POINTS:
        if re.search(r"\b" + re.escape(name) + r"\s*\(", body):
            offenders.append(f"{path.name}:{name}")
check(not offenders,
      "no file the participant route loads calls a combination entry point, so no frontend "
      "aggregation can recreate the double-counting removed from the backend", str(offenders))

# THE SCANNER MUST BE ABLE TO FIND THESE WHERE THEY REALLY ARE, or the check above proves
# nothing at all. This is the exact vacuity Run 20 found nine times.
server_fusion = (ROOT / "server" / "app" / "simulation" / "fusion.py").read_text(encoding="utf-8")
found_server = [n for n in COMBINATION_ENTRY_POINTS
                if re.search(r"\b" + re.escape(n) + r"\s*\(", server_fusion)]
check(len(found_server) >= 2,
      "and the scanner DOES find combination entry points in the server's own fusion module, "
      "so its silence on the browser is meaningful", str(found_server))

print()
print("=" * 78)
print("SECTION 3  qualification and abstention survive to the exported/API row")
print("=" * 78)
from app.research_export import MODULE_RESULT_COLUMNS  # noqa: E402

for col in ("signal_qualification", "activation_state", "band_source", "status_color"):
    check(col in MODULE_RESULT_COLUMNS,
          f"the module-result row carries {col}, so an unqualified signal is distinguishable "
          f"from a qualified one", str(MODULE_RESULT_COLUMNS))

from app.simulation.qualification_gate import (  # noqa: E402
    ABSTAINED, ALLOWED, DEGRADED, REJECTED, NON_PROJECT_EVIDENCE, qualify)

# The four verdicts must be DISTINCT values, or a surface cannot render the difference however
# carefully it is written.
verdicts = {ALLOWED, DEGRADED, ABSTAINED, REJECTED}
check(len(verdicts) == 4, "the gate publishes four distinct verdicts", str(verdicts))

# An abstaining module carries no band. This is the property the frontend relies on to avoid
# painting a traffic light on an abstention, and it is asserted on the gate's own output.
q = qualify("A2.1", None, None, {"verdict": ALLOWED, "reasons": []}, module_abstained=True)
check(q.verdict == ABSTAINED, "a module that abstained is qualified ABSTAINED", str(q.verdict))
check(q.band is None, "and carries NO band, so no surface can render it as a traffic light",
      str(q.band))
check(q.may_vote is False, "and may not vote")

# A quality, governance or decision output is REJECTED as project-condition evidence, at the
# gate as well as inside the combination.
rel = sorted(NON_PROJECT_EVIDENCE)[0]
qr = qualify("C1.4", "Green", 1.0, {"verdict": ALLOWED, "reasons": []},
             lineage=dict(lineage_record("C1.4"), evidence_relationship=rel))
check(qr.verdict == REJECTED,
      f"a {rel} signal is REJECTED as project-condition evidence", str(qr.verdict))
check(qr.may_vote is False, "and may not vote")

print()
print("=" * 78)
print("SECTION 4  guard non-vacuity: each guard proved RED by a real violation")
print("=" * 78)

# 1. The same-lineage guard must go red if the two signals are declared INDEPENDENT when they
#    are not. This is the defect itself, reintroduced by declaration.
mislabelled = [dict(s) for s in same_body]
for s in mislabelled:
    s["lineage"] = dict(s["lineage"], primitive_source_ids=[f"fact:{s['module_id']}"],
                        evidence_relationship="INDEPENDENT")
bad = fuse_signals(mislabelled)
check(bad["lineage_groups"] == 2,
      "NON-VACUITY: declaring one body as two really does produce two groups, so the "
      "one-group assertion above is not true by construction",
      f"lineage_groups={bad['lineage_groups']}")
check(bad["mass"]["Amber"] > one["mass"]["Amber"] + 1e-9,
      "NON-VACUITY: and really does sharpen belief, which is the harm the control prevents",
      f"correct={one['mass']['Amber']} mislabelled={bad['mass']['Amber']}")

# 2. The browser scanner must go red on a file that DOES contain a combination call.
fake = "function x(){ return dst_fuse([1,2]); }"
hit = [n for n in COMBINATION_ENTRY_POINTS if re.search(r"\b" + re.escape(n) + r"\s*\(", fake)]
check(hit == ["dst_fuse"],
      "NON-VACUITY: the browser scanner turns RED on a file that calls a combination entry "
      "point", str(hit))

# 3. The abstention guard must go red if a band is supplied with the abstention.
q2 = qualify("A2.1", "Green", 1.0, {"verdict": ALLOWED, "reasons": []}, module_abstained=False)
check(q2.band == "Green" and q2.verdict == ALLOWED,
      "NON-VACUITY: a module that did NOT abstain keeps its band and is ALLOWED, so the "
      "abstention assertions above are not true of everything", f"{q2.verdict} {q2.band}")
check(q2.may_vote is True, "NON-VACUITY: and MAY vote, so the may_vote assertions above are not true of everything")

# 4. The export-column guard must go red on a column that is not there.
check("a_column_that_does_not_exist" not in MODULE_RESULT_COLUMNS,
      "NON-VACUITY: the column check turns RED for a column the row does not carry")

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print("  " + f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
