#!/usr/bin/env python3
"""
Training mode run 5: the naming fixes, the computation chain, and the full recommendation.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_training_detail.py

The brief's required coverage: no module id or number reaches the training surface; a
category's detail lists the computations that fed it and names the one that leads it; an
abstaining computation is reported as an abstention rather than a value; the recommendation's
figures match the engine's state exactly, and a fault that changes a state figure changes the
recommendation.

THE DOM-level half of "no id appears anywhere" lives in tests_render.html group 10, which
renders the real ledger and reads the text back. This file covers what the SERVER emits and
what the shared render path is built from.
"""
from __future__ import annotations

import copy
import io
import json
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app import training_engine as eng  # noqa: E402
from app.training import _abstained_by_category  # noqa: E402
from app.simulation import compute_project, unported_modules  # noqa: E402
from app.simulation.registry import registry_index  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
ROOT = pathlib.Path(__file__).resolve().parents[2]

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


CV = 12_000_000.0
# A module id ("A1.1", "B2.14") or a bare category id ("A1", "C1") standing alone as a word.
# [A-D] + exactly ONE digit, optionally .N. A second digit disqualifies, so the contract form
# "AIA A201-2017" is not mistaken for a category id — a looser pattern flagged it, found by the
# browser drive.
MODULE_ID = re.compile(r"(?:^|[^A-Za-z0-9])[A-D]\d\.\d+(?![\dA-Za-z])")
CATEGORY_ID = re.compile(r"(?:^|[^A-Za-z0-9])[A-D]\d(?![\dA-Za-z.])")


def fresh(form="A201-2017", conditions="exacting", facility="standard", value=CV):
    return eng.initial_state(form, value, conditions, facility)


print("=" * 78)
print("PART 1: no module id or number reaches the training surface")
print("=" * 78)

# 1a. Every user-facing STRING the recommendation emits. `basis` is the machine block the
# tests read; the rendered fields are these.
RENDERED = ("headline", "what", "why", "who", "to_whom", "means", "next_step")
states = []
s = fresh()
for _ in range(8):
    states.append(copy.deepcopy(s))
    allowed = eng.allowed_decisions(s)
    s = eng.advance(s, "defer" if "defer" in allowed else allowed[0])
recs = [r for r in (eng.build_recommendation(st) for st in states) if r]
check(len(recs) >= 4, "several recommendations produced across a run to scan", str(len(recs)))
offenders = []
for r in recs:
    for field in RENDERED:
        text = r.get(field) or ""
        if MODULE_ID.search(text) or CATEGORY_ID.search(text):
            offenders.append((field, text[:80]))
check(not offenders,
      "no recommendation field carries a module id or a bare category id",
      str(offenders[:3]))
# Clause citations are NOT ids: they must survive. This is the check that stops the id sweep
# being implemented as a blunt digit strip.
check(any("15.1.3.1" in (r.get("why") or "") + (r.get("means") or "") for r in recs),
      "and clause citations survive the sweep: they are the point, not a number to remove")

# 1b. The client tables the training surface renders through. A category is rendered by NAME
# via the shared workspace lookup, so the id must not be interpolated into markup.
train_js = io.open(ROOT / "assets" / "js" / "training.js", encoding="utf-8").read()
check("esc(name)" not in train_js.split("function signalsHtml")[1].split("function ")[0]
      if "function signalsHtml" in train_js else False,
      "training.js no longer renders the raw category key in the signals table")
check("LinWorkspace.buildProjectDetailHtml" in train_js,
      "and renders through the platform's own ledger builder instead of a training-only one")
work_js = io.open(ROOT / "assets" / "js" / "workspace.js", encoding="utf-8").read()
check("buildProjectDetailHtml: buildProjectDetailHtml" in work_js,
      "which workspace.js exports for exactly that reuse")
check("categoryName(e.catId)" in work_js and "moduleName(m.module_id)" in work_js,
      "and that builder renders categories and computations through the NAME tables")

# 1c. The stale line is gone from the training page.
index_html = io.open(ROOT / "index.html", encoding="utf-8").read()
check("This build does not yet generate one" not in index_html,
      "the stale 'does not yet generate one' line is removed from the training page")
check('data-page="training"' in index_html,
      "while the training page itself is still there (the removal was surgical)")

print()
print("=" * 78)
print("PART 2: the chain — contributors, the leader, and honest abstentions")
print("=" * 78)

st = fresh()
si, cutoff = eng.signal_inputs_from_state(st)
si["events"] = []
run = compute_project(si, "TRN-DETAIL", "P1", cutoff)
mods = run["modules"]
cats = run["category_statuses"]

by_cat: dict[str, list] = {}
for m in mods:
    by_cat.setdefault(m["category"], []).append(m)
check(len(by_cat) >= 6 and all(cats.get(c) for c in by_cat),
      "every category with contributors has a rollup to open", str(sorted(by_cat))[:90])
check(all(len(v) >= 1 for v in by_cat.values()),
      "and each carries the computations that fed it")

# THE MEASURED CORRECTION the report leads with: the category status is an evidence
# combination, NOT the worst contributor. If this ever became a true maximum the display's
# wording would be wrong, so it is asserted rather than assumed.
RANK = {"green": 0, "yellow": 1, "amber": 2, "red": 3}
BANDS = ["Green", "Yellow", "Amber", "Red"]
divergent = []
for cat, members in by_cat.items():
    worst = BANDS[max(RANK[str(m["status_color"]).lower()] for m in members)]
    if worst.lower() != str(cats[cat]["status"]).lower():
        divergent.append((cat, worst, cats[cat]["status"]))
check(divergent,
      "the category status DIFFERS from its worst contributor in this period: the rollup is "
      "an evidence combination, not worst-status-wins",
      str(divergent[:3]))
check(any(w == "Red" and str(f).lower() == "green" for _, w, f in divergent)
      or any(RANK[w.lower()] - RANK[str(f).lower()] >= 2 for _, w, f in divergent),
      "including at least one category whose worst contributor is two bands more severe than "
      "the category reads", str(divergent[:3]))

# Abstentions: named absences, derived from the registry, excluding group D and unported.
ab = _abstained_by_category(mods)
check(ab and all(isinstance(v, list) and v for v in ab.values()),
      "the server reports which computations abstained, per category",
      str({k: len(v) for k, v in ab.items()}))
present_ids = {m["module_id"] for m in mods}
check(not (set().union(*ab.values()) & present_ids),
      "no computation is reported as both producing a value and abstaining")
check(not any(i.startswith("D") for v in ab.values() for i in v),
      "group D is excluded: it is refused on a single-project path, which is a structural "
      "exclusion and not a per-period abstention")
check(not (set().union(*ab.values()) & set(unported_modules())),
      "and an unported computation is not miscounted as an abstention",
      str(unported_modules()))
idx = registry_index()
check(all(i in idx for v in ab.values() for i in v),
      "every abstention names a registered computation, so the screen can render its NAME")

# Group C's exclusion from project status is carried, not left to inference.
c_cats = [c for c, v in cats.items() if v.get("group") == "C"]
check(c_cats and all(cats[c]["contributes_to_project_status"] is False for c in c_cats),
      "Data & Evidence Health is marked as not contributing to project status",
      str(c_cats))
check(all(cats[c]["contributes_to_project_status"] is True
          for c, v in cats.items() if v.get("group") == "A"),
      "while Project Health does contribute, so the flag is discriminating and not a constant")

work_js_detail = work_js[work_js.index("function categoryDetailHtml"):]
# Matched against the EMITTED MARKUP, not the phrase: an earlier version of this check
# searched for the bare words and was satisfied by a comment that happened to quote them, so
# deleting the real marker left it green. Fault D3 found that.
check('ws-worst' in work_js_detail and "(most severe contributor)" in work_js_detail,
      "the detail names the most severe contributor as such, rather than claiming a maximum "
      "the fusion does not perform")
# Quoted LITERALS only. A first version scanned the whole slice and went red on an em dash
# inside a comment, which renders to nobody: "rendered text" means the strings that are emitted.
_detail_src = work_js_detail.split("function buildProjectDetailHtml")[0]
_literals = re.findall(r"""'[^'\\n]*'|\"[^\"\\n]*\"""", _detail_src)
check(not [x for x in _literals if "—" in x],
      "and no string the detail EMITS carries an em dash, per the naming authority",
      str([x for x in _literals if "—" in x])[:80])
check("ws-abstained" in work_js_detail and "abstained: no usable input" in work_js_detail,
      "and renders an abstention as a named absence")
abstain_block = work_js_detail[work_js_detail.index("var abstained ="):
                               work_js_detail.index("return '<div class=\"ws-cat-detail\"")]
check("statusDotColor" not in abstain_block and "ws-dot" not in abstain_block,
      "with NO colour and NO status dot: an abstention is not a value",
      abstain_block[:120])

print()
print("=" * 78)
print("PART 3: the recommendation is generated from the state, exactly")
print("=" * 78)

st = fresh()
rec = eng.build_recommendation(st)
check(rec is not None, "period one produces a recommendation")
for field in RENDERED + ("deadline_date", "basis", "policy"):
    check(bool(rec.get(field)), f"the recommendation states {field}",
          str(rec.get(field))[:60])
check(len((rec["what"] or "").split()) > 6,
      "'what' is a specific instruction, not a verb", rec["what"][:90])
check("investigate" != (rec["what"] or "").strip().lower(),
      "and is no longer the bare word it was")

# THE FIGURES MATCH THE STATE EXACTLY. Not "approximately", not re-derived differently.
basis = rec["basis"]
check(basis["cpi"] == round(st["ev"] / st["ac"], 3)
      and basis["spi"] == round(st["ev"] / st["pv"], 3),
      "cost and schedule performance in the recommendation are the state's own ratios",
      f"{basis['cpi']}/{basis['spi']}")
check(basis["float_remaining_days"] == st["float_total_days"] - st["float_consumed_days"],
      "float remaining matches the state", str(basis["float_remaining_days"]))
check(basis["dispute_estimated_cost"] == st["dispute"]["estimated_cost"],
      "the claim value matches the state", str(basis["dispute_estimated_cost"]))
check(basis["contingency_remaining"] == st["contingency_remaining"],
      "contingency matches the state")
pos = eng.notice_position(st)
check(basis["dispute_position"]["days_remaining"] == pos["days_remaining"],
      "and the days remaining are the notice clock's own, not a second count",
      str(basis["dispute_position"]))
# The figures also have to appear in the PROSE the trainee reads, or matching state is moot.
check(f"{int(st['dispute']['estimated_cost']):,}" in rec["what"],
      "the claim value appears in the prose the trainee reads", rec["what"][:90])
check(str(pos["days_remaining"]) in rec["why"] and str(pos["window_days"]) in rec["why"],
      "as do the days remaining and the window they run against", rec["why"][:110])
check(pos["citation"] in rec["why"],
      "with the governing clause cited", pos["citation"])

# A FAULT THAT CHANGES A STATE FIGURE CHANGES THE RECOMMENDATION. Proven by perturbing the
# state, not by patching the generator: if the recommendation were narrated free of the
# state, this would not move.
moved = copy.deepcopy(st)
moved["float_consumed_days"] = 7
rec_moved = eng.build_recommendation(moved)
check(rec_moved["why"] != rec["why"] and "5 days of float" in rec_moved["why"],
      "spending float changes the recommendation's own reasoning", rec_moved["why"][:110])
richer = copy.deepcopy(st)
richer["dispute"]["estimated_cost"] = 250_000.0
check("250,000" in eng.build_recommendation(richer)["what"],
      "and changing the claim value changes the figure it recommends acting on")
later = eng.advance(copy.deepcopy(st), "defer")
rec_later = eng.build_recommendation(later)
check(rec_later is not None and "ran out" in rec_later["why"],
      "once the window closes the recommendation changes what it recommends, from notice to "
      "closing it out", (rec_later or {}).get("why", "")[:110])
check("Absorb" in rec_later["what"] or "absorb" in rec_later["what"],
      "recommending absorption rather than a notice that can no longer preserve anything",
      rec_later["what"][:90])

print()
print("=" * 78)
print("PART 3b: form-specific service, and the fallibility policy")
print("=" * 78)

a201 = eng.build_recommendation(fresh("A201-2017"))
check("Email is not service" in a201["means"] and "Article 15" in a201["means"],
      "A201: the recommendation states that a claim is not served by email",
      a201["means"][:110])
cd = eng.build_recommendation(fresh("ConsensusDocs 200"))
check("8.4" in cd["means"] and "21 days" in cd["means"],
      "ConsensusDocs: the means carries the second step", cd["means"][:110])
far = eng.build_recommendation(fresh("Federal FAR"))
check("Contracting Officer" in far["to_whom"],
      "FAR: it goes to the Contracting Officer", far["to_whom"])
check("52.233-1" in far["next_step"] or "certif" in far["next_step"].lower(),
      "and the next step raises certification", far["next_step"][:110])
check("lookback" in far["why"].lower() or "unrecoverable" in far["why"].lower(),
      "with the cost lookback as the reason, since FAR has no bar", far["why"][:110])
check(a201["means"] != far["means"] and a201["to_whom"] != far["to_whom"],
      "the service route genuinely differs by form")

# NOT AN ORACLE. The policy is fixed, stated, and demonstrably not always the best call.
check(rec["policy"] == eng.RECOMMENDATION_POLICY == "entitlement first, maximal correction",
      "the recommendation carries its policy, so its bias is inspectable", rec["policy"])
# The demonstration: a small impact under a collaborative owner still gets "escalate", even
# though absorbing costs less and keeps the relationship. That is the contracts-first habit,
# and a trainee who follows it every time is not thinking.
kind = fresh("A201-2017", conditions="steady")
kind["dispute"]["estimated_cost"] = 5_000.0
kind_rec = eng.build_recommendation(kind)
check("notice" in kind_rec["headline"].lower() or "Serve" in kind_rec["what"],
      "a trivial impact under a collaborative owner STILL draws a notice recommendation: the "
      "policy is confident and defensible and not always right", kind_rec["headline"])
check(kind_rec["basis"]["dispute_estimated_cost"] == 5_000.0,
      "and it is arguing over 5,000 dollars, which the trainee can see and reject")
# Nothing on the rendered surface labels it fallible: an oracle that announces its own
# unreliability is no longer something the trainee has to weigh.
joined = " ".join(str(kind_rec.get(f) or "") for f in RENDERED).lower()
check("may be wrong" not in joined and "not always" not in joined,
      "the rendered text does not hedge: the trainee must judge it, not be told to")

print()
print("=" * 78)
print("OVER HTTP: the surface carries both, and the gate still holds")
print("=" * 78)

ADMIN_TOKEN = "training-detail-admin"
with Session() as s_:
    row = s_.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s_.add(Participant(pseudonymous_code="DET-ADMIN", role="ResearchAdmin",
                           access_token_hash=hash_access_token(ADMIN_TOKEN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN_TOKEN)
    s_.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN_TOKEN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "DET-OPS", "role": "Participant",
                "account_type": "operational"})
ops = post({"action": "researchlogin",
            "access_token": created["access_token"]})["session_token"]

view = post({"action": "trainingstart", "session_token": ops,
             "contract_form": "A201-2017", "conditions": "exacting",
             "contract_value": 12_000_000})
check(view.get("ok") is True, "a run starts", str(view)[:100])
check(isinstance(view.get("recommendation"), dict)
      and view["recommendation"].get("what"),
      "the state view carries the full recommendation", str(view.get("recommendation"))[:90])
check(isinstance(view.get("abstained_by_category"), dict)
      and view["abstained_by_category"],
      "and the abstention map the detail view renders",
      str(list((view.get("abstained_by_category") or {}))[:5]))
vr = view["recommendation"]
check(vr["basis"]["float_remaining_days"] == view["state"]["float_total_days"]
      - view["state"]["float_consumed_days"],
      "the recommendation's figures match the state IN THE SAME PAYLOAD, so the screen cannot "
      "show two different numbers")
after = post({"action": "trainingdecision", "session_token": ops,
              "run_id": view["run_id"], "decision": "defer"})
check(after["recommendation"]["why"] != vr["why"],
      "and it moves when the state moves, over HTTP")
# `after` already spent period one, so the run needs the REMAINING periods and no more:
# decisions past completion are refused, and a refusal dict would silently stand in for the
# completed view.
done = after
while done.get("status") == "active":
    allowed = done.get("allowed_decisions") or ["defer"]
    done = post({"action": "trainingdecision", "session_token": ops,
                 "run_id": view["run_id"],
                 "decision": "defer" if "defer" in allowed else allowed[0]})
    assert done.get("ok") is True, done
check(done.get("status") == "complete" and done.get("recommendation") is None,
      "a complete run recommends nothing: there is no period left to act in",
      str(done.get("recommendation"))[:60])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
