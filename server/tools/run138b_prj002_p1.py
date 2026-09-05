"""RUN 138B, TASK 4. PRJ-002 period 1, reassembled from raw extractions under v70.

Pure functions only: no model call, no database, no network. Run with cwd = server/.

The raw extraction records are the two documents PRJ-002 period 1 files, as
`tools/test_run132_actual_cost_selection.py` states them; that file is the repository's record
of what those documents say. Nothing here is imputed and nothing is adjusted to reach a figure.

The PRE-v70 column is RECONSTRUCTED, not read from a store: no local corpus of stored results
exists in this tree. It is built by putting back exactly the two defects the corrections removed
-- the pay application's amount-paid-to-date selected as `ac`, and `_round3` applied to `cpi` at
storage -- and running the same v70 module code over it. It is therefore a faithful statement of
what those two defects do to this period's outputs, and NOT a claim about any stored row.
"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.extraction_merge import assemble_signal_inputs, _round3
from app.simulation.compute import compute_project
from app.simulation.registry import registry_index
from app.simulation import models_evm as E
from app.decision_brief import compose_decision_brief
from datetime import date


def doc(sha, dt, ex):
    return {"sha256": sha, "doc_type": dt, "filename": sha + ".pdf", "extraction": ex}


MONTHLY_REPORT = doc("mr1", "monthly_report", {
    "actual_cost": 1900000, "earned_value": 1815000, "planned_value": 1900000,
    "actual_percent_complete": 60.5, "planned_percent_complete": 63.3,
    "budget_at_completion": 3000000, "report_period": "2025-01-31"})
PAY_APPLICATION = doc("pa1", "pay_application", {
    "amount_paid_to_date": 1633500, "completed_to_date": 1815000,
    "percent_complete_verified": 60.5, "original_contract_sum": 3000000,
    "original_contingency": 150000, "remaining_contingency": 90000,
    "period_to_date": "2025-01-31"})

RAW = [MONTHLY_REPORT, PAY_APPLICATION]
CUTOFF = date(2025, 1, 31)
PERIOD = "2025-01"


IDX = registry_index()


def sect(t):
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


sect("1. v70 ASSEMBLY FROM RAW EXTRACTIONS")
si = assemble_signal_inputs(RAW, cutoff=CUTOFF)
print(f"BAC = {si['bac']!r}")
print(f"PV  = {si['pv']!r}")
print(f"EV  = {si['ev']!r}")
print(f"selected ac = {si['ac']!r}")
print("ac provenance = " + json.dumps((si.get('sources') or {}).get('ac'), default=str))
print(f"stored cpi   = {si['cpi']!r}")
print(f"EV / ac      = {si['ev'] / si['ac']!r}")
print(f"stored cpi is rounded? {si['cpi'] != si['ev'] / si['ac']}")
print(f"_round3 of that quotient would be {_round3(si['ev'] / si['ac'])!r}")
print(f"stored spi   = {si['spi']!r}")

sect("2. A1.7 TCPI AND A1.8 VAC, DIRECT")
t = E.run_tcpi(si, lambda: 0.5, None)
v = E.run_vac(si, lambda: 0.5, None)
print(f"A1.7 TCPI  formula (BAC-EV)/(BAC-ac) = ({si['bac']}-{si['ev']})/({si['bac']}-{si['ac']})")
print(f"     raw = {t.get('tcpi')!r}   band = {t.get('status_color')!r}")
print(f"A1.8 VAC   vac_pct = (1 - 1/CPI)*100 on CPI {si['cpi']!r}")
print(f"     vac = {v.get('vac')!r}  vac_pct raw = {v.get('vac_pct')!r}  band = "
      f"{v.get('status_color')!r}")

sect("3. FULL v70 COMPUTATION")
new = compute_project(si, "run138b", PERIOD, CUTOFF, project_id="PRJ-002")


def dump(res, label):
    print(f"\n--- {label} ---")
    print(f"simulation_version = {res['simulation_version']}")
    for cat in ("A1", "A3"):
        rows = [m for m in res["modules"] if m.get("category") == cat]
        print(f"\n{cat} module results ({len(rows)} computed):")
        for m in sorted(rows, key=lambda r: r["module_id"]):
            print(f"   {m['module_id']:<8} {str(m.get('status_color')):<8} "
                  f"{m.get('title') or m.get('name') or ''}")
        ab = [m for m in res["abstained"]
              if (IDX.get(m["module_id"]) or {}).get("category") == cat]
        for m in sorted(ab, key=lambda r: r["module_id"]):
            print(f"   {m['module_id']:<8} ABSTAINED  reason: {m.get('reason')} "
                  f"[{m.get('abstention_reason_code')}]")
    print("\nCategory postures:")
    for k, c in sorted(res["category_statuses"].items()):
        print(f"   {k:<4} {str(c.get('status')):<16} rule={c.get('posture_rule')} "
              f"arith={c.get('posture_arithmetic')} avg={c.get('posture_average')} "
              f"set_by={c.get('status_set_by')}")
    b = res["project_status_basis"]
    print(f"\nPROJECT STATUS = {res['project_status']!r}")
    print(f"   weighted band = {b.get('fused_band')!r}")
    print("   basis: " + json.dumps({k: v for k, v in b.items()
                                     if k not in ("required_missing_detail",)},
                                    default=str)[:2000])
    return res


dump(new, "v70 (reassembled from raw)")

sect("4. DECISION BRIEF, v70")
brief = compose_decision_brief(category_statuses=new["category_statuses"],
                               module_results=new["modules"],
                               status_basis=new["project_status_basis"],
                               row={"projectId": "PRJ-002", "period": PERIOD})
for block in brief["order"]:
    if block in brief:
        print(f"\n[{block}]")
        print(json.dumps(brief[block], indent=2, default=str)[:2500])

sect("5. PRE-v70 RECONSTRUCTION (both defects put back)")
old = dict(si)
old["ac"] = 1633500
old["sources"] = dict(si.get("sources") or {})
old["sources"]["ac"] = {"docType": "pay_application", "field": "amount_paid_to_date",
                        "sha256": "pa1", "value": 1633500}
old["cpi"] = _round3(old["ev"] / old["ac"])
print(f"prior ac  = {old['ac']!r} from pay_application.amount_paid_to_date")
print(f"prior cpi = {old['cpi']!r}  (unrounded would be {old['ev'] / old['ac']!r})")
oldres = compute_project(old, "run138b", PERIOD, CUTOFF, project_id="PRJ-002")
dump(oldres, "pre-v70 (reconstructed)")
oldbrief = compose_decision_brief(category_statuses=oldres["category_statuses"],
                                  module_results=oldres["modules"],
                                  status_basis=oldres["project_status_basis"],
                                  row={"projectId": "PRJ-002", "period": PERIOD})

sect("6. COMPARISON")
print(f"ac   : {old['ac']!r} (pay_application) -> {si['ac']!r} (monthly_report)")
print(f"CPI  : {old['cpi']!r} -> {si['cpi']!r}")
print(f"project: {oldres['project_status']!r} -> {new['project_status']!r}")
for k in sorted(set(oldres["category_statuses"]) | set(new["category_statuses"])):
    a = (oldres["category_statuses"].get(k) or {}).get("status")
    b = (new["category_statuses"].get(k) or {}).get("status")
    print(f"   {k:<4} {str(a):<16} -> {str(b):<16} {'CHANGED' if a != b else ''}")
oldm = {m["module_id"]: m.get("status_color") for m in oldres["modules"]}
newm = {m["module_id"]: m.get("status_color") for m in new["modules"]}
print("\nModule band changes:")
any_ch = False
for mid in sorted(set(oldm) | set(newm)):
    if oldm.get(mid) != newm.get(mid):
        any_ch = True
        print(f"   {mid:<8} {str(oldm.get(mid)):<8} -> {str(newm.get(mid)):<8}")
if not any_ch:
    print("   (none)")
print("\nBrief blocks that differ: " +
      ", ".join(sorted(b for b in set(brief) | set(oldbrief)
                       if json.dumps(brief.get(b), sort_keys=True, default=str)
                       != json.dumps(oldbrief.get(b), sort_keys=True, default=str))))

sect("7. PAY-APPLICATION-ONLY: THE ABSTENTION CASE")
po = assemble_signal_inputs([PAY_APPLICATION], cutoff=CUTOFF)
print(f"ac = {po['ac']!r}   cpi = {po['cpi']!r}   'ac' in sources: "
      f"{'ac' in (po['sources'] or {})}")
pores = compute_project(po, "run138b", PERIOD, CUTOFF, project_id="PRJ-002-payonly")
for mid in ("A1.7", "A1.8"):
    row = next((m for m in pores["abstained"] if m["module_id"] == mid), None)
    print(f"   {mid} abstained: {row is not None}  reason: "
          f"{(row or {}).get('reason')} [{(row or {}).get('abstention_reason_code')}]")
    print(f"   {mid} in computed: {any(m['module_id'] == mid for m in pores['modules'])}")
print(f"   project status = {pores['project_status']!r}")
print("   EVM analysis withheld -- authoritative actual cost is unavailable for the "
      "reporting period.")
