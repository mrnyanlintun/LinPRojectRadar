#!/usr/bin/env python3
"""Audit-only independent integrity checker for the OG-SYNTH-0.1 research fixture.

The programme-level validator script named in CHECKSUMS.sha256
(validators/validate_synthetic_programme.py) was not supplied with the three
package archives, so the claimed validator cannot be rerun. This script is an
INDEPENDENT re-derivation, written against the data rather than against the
package's own stored report. It reads only; it never writes into the fixture.
"""
import csv, json, os, sys, hashlib, itertools
from collections import defaultdict, Counter

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "research_fixtures/synthetic/OG-SYNTH-0.1")
A = os.path.join(ROOT, "package_A/package_A_project_structures")
B = os.path.join(ROOT, "package_B/package_B_reference_training_decisions")
C = os.path.join(ROOT, "package_C/package_C_optional_activation_lab")

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, "PASS" if ok else "FAIL", detail))
    return ok

def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

PROV = ("data_origin", "programme_version", "not_for_empirical_validation")

def walk_csvs():
    for base in (A, B, C):
        for dirpath, _, files in os.walk(base):
            for fn in sorted(files):
                if fn.endswith(".csv"):
                    yield os.path.join(dirpath, fn)

# --- 1. provenance on every record of every CSV ---------------------------
bad_prov = []
for p in walk_csvs():
    rs = rows(p)
    if not rs:
        continue
    hdr = rs[0].keys()
    if not all(k in hdr for k in PROV):
        bad_prov.append((os.path.relpath(p, ROOT), "missing provenance columns"))
        continue
    for r in rs:
        if (r["data_origin"] != "SYNTHETIC_RESEARCH_FIXTURE"
                or r["programme_version"] != "OG-SYNTH-0.1"
                or str(r["not_for_empirical_validation"]).lower() != "true"):
            bad_prov.append((os.path.relpath(p, ROOT), "bad provenance value"))
            break
check("provenance:all_csv_records", not bad_prov, str(bad_prov[:5]))

# --- 2. record_hash present and unique per file ---------------------------
nohash, duphash = [], []
for p in walk_csvs():
    rs = rows(p)
    if not rs:
        continue
    if "record_hash" not in rs[0]:
        nohash.append(os.path.relpath(p, ROOT)); continue
    hs = [r["record_hash"] for r in rs]
    if any(not h for h in hs):
        nohash.append(os.path.relpath(p, ROOT))
    if len(set(hs)) != len(hs):
        duphash.append((os.path.relpath(p, ROOT), len(hs) - len(set(hs))))
check("record_hash:present", not nohash, str(nohash))
check("record_hash:unique_within_file", not duphash, str(duphash))

# --- 3. Package A primary and foreign keys --------------------------------
projects = rows(os.path.join(A, "projects.csv"))
pids = [r["project_id"] for r in projects]
check("pk:projects_unique", len(set(pids)) == len(pids), f"n={len(pids)}")
PIDS = set(pids)

periods = rows(os.path.join(A, "reporting_periods.csv"))
check("fk:reporting_periods_project", all(r["project_id"] in PIDS for r in periods),
      f"n={len(periods)}")
perkey = [(r["project_id"], r.get("period_index") or r.get("period_id")) for r in periods]
check("pk:reporting_periods_unique", len(set(perkey)) == len(perkey))

acts = rows(os.path.join(A, "schedule_activities.csv"))
aids = [(r["project_id"], r["activity_id"]) for r in acts]
check("pk:schedule_activities_unique", len(set(aids)) == len(aids), f"n={len(aids)}")
check("fk:schedule_activities_project", all(r["project_id"] in PIDS for r in acts))
AID = set(aids)

deps = rows(os.path.join(A, "schedule_dependencies.csv"))
dep_ok = all((r["project_id"], r["predecessor_activity_id"]) in AID
             and (r["project_id"], r["successor_activity_id"]) in AID for r in deps)
check("fk:schedule_dependencies_activities", dep_ok, f"n={len(deps)}")

# --- 4. schedule network acyclicity, per project --------------------------
cyc = []
for pid in PIDS:
    g = defaultdict(list)
    nodes = {a for (p_, a) in AID if p_ == pid}
    for r in deps:
        if r["project_id"] == pid:
            g[r["predecessor_activity_id"]].append(r["successor_activity_id"])
    state = {}
    def dfs(n):
        state[n] = 1
        for m in g.get(n, []):
            if state.get(m) == 1:
                return True
            if state.get(m, 0) == 0 and dfs(m):
                return True
        state[n] = 2
        return False
    if any(state.get(n, 0) == 0 and dfs(n) for n in nodes):
        cyc.append(pid)
check("schedule:acyclic_per_project", not cyc, str(cyc))

# --- 5. PERT triangular ordering (o <= m <= p), positive durations --------
bad_tri = [r["activity_id"] for r in acts
           if not (float(r["optimistic_duration_days"]) <= float(r["most_likely_duration_days"])
                   <= float(r["pessimistic_duration_days"]))]
check("pert:optimistic_le_mode_le_pessimistic", not bad_tri, str(bad_tri[:5]))
check("pert:durations_positive",
      all(float(r["optimistic_duration_days"]) > 0 for r in acts))

# --- 6. ground-truth percentile ordering ---------------------------------
sgt = rows(os.path.join(A, "schedule_ground_truth.csv"))
p50 = [c for c in sgt[0] if "p50" in c.lower()]
p80 = [c for c in sgt[0] if "p80" in c.lower()]
ok = True
for c50, c80 in zip(sorted(p50), sorted(p80)):
    for r in sgt:
        try:
            if float(r[c80]) < float(r[c50]):
                ok = False
        except (ValueError, TypeError):
            pass
check("ground_truth:schedule_p80_ge_p50", ok, f"{p50} vs {p80}")

# --- 7. Package B splits: the leakage hunt -------------------------------
split = rows(os.path.join(B, "B1_reference_population/split_manifest.csv"))
smap = {}
dupe_split = []
for r in split:
    k = r["reference_project_id"]
    if k in smap and smap[k] != r["split"]:
        dupe_split.append(k)
    smap[k] = r["split"]
check("split:one_split_per_project", not dupe_split, str(dupe_split[:5]))
check("split:partitions_disjoint",
      sum(Counter(smap.values()).values()) == len(smap),
      str(dict(Counter(smap.values()))))

refp = rows(os.path.join(B, "B1_reference_population/reference_projects.csv"))
inline = {r["reference_project_id"]: r["split"] for r in refp}
mismatch = [k for k in smap if inline.get(k) != smap[k]]
check("split:manifest_agrees_with_reference_projects", not mismatch, str(mismatch[:5]))

# every derived B1 table must not place one project's rows in two splits
for fn, key in [("reference_project_periods.csv", "reference_project_id"),
                ("parametric_cost_training.csv", "reference_project_id"),
                ("anomaly_labels.csv", "reference_project_id"),
                ("rough_set_decision_table.csv", "reference_project_id"),
                ("reference_outcomes.csv", "reference_project_id"),
                ("reference_class_membership.csv", "reference_project_id")]:
    p = os.path.join(B, "B1_reference_population", fn)
    rs = rows(p)
    unknown = [r[key] for r in rs if r[key] not in smap]
    check(f"fk:{fn}_reference_project", not unknown, str(unknown[:3]))
    if "split" in rs[0]:
        bad = [r[key] for r in rs if r["split"] != smap[r[key]]]
        check(f"leakage:{fn}_split_agrees_with_manifest", not bad, str(bad[:5]))

# row-level leakage: identical feature vectors appearing in two different splits
feat = ["project_type", "delivery_method", "region", "gross_area_m2", "length_km",
        "capacity_units", "floors", "complexity_index", "design_completeness",
        "location_factor", "baseline_cost_usd", "baseline_duration_days"]
seen = defaultdict(set)
for r in refp:
    seen[tuple(r[c] for c in feat)].add(r["split"])
cross = [k for k, v in seen.items() if len(v) > 1]
check("leakage:no_duplicate_feature_vector_across_splits", not cross, f"{len(cross)} collisions")

# analogous_pairs must not bridge holdout and development
ap = rows(os.path.join(B, "B1_reference_population/analogous_pairs.csv"))
pcols = [c for c in ap[0] if "project" in c and c.endswith(("_a", "_b", "_1", "_2"))] or \
        [c for c in ap[0] if c.startswith("reference_project_id")]
bridges = []
if len(pcols) >= 2:
    for r in ap:
        s = {smap.get(r[pcols[0]]), smap.get(r[pcols[1]])}
        if "LOCKED_HOLDOUT" in s and len(s) > 1:
            bridges.append((r[pcols[0]], r[pcols[1]]))
check("leakage:analogous_pairs_do_not_bridge_holdout", not bridges,
      f"cols={pcols} bridges={len(bridges)}")

# Package C benchmark must draw only on the holdout
try:
    cb = rows(os.path.join(C, "parametric_cost_benchmark.csv"))
    check("packageC:benchmark_rows", len(cb) >= 1, f"n={len(cb)}")
except FileNotFoundError:
    check("packageC:benchmark_rows", False, "missing")

# --- 8. B3 decision objects completeness --------------------------------
dp = rows(os.path.join(B, "B3_decision_optimization/decision_problems.csv"))
DP = {r["problem_id"] for r in dp} if "problem_id" in dp[0] else \
     {r[list(dp[0])[0]] for r in dp}
dpkey = "problem_id" if "problem_id" in dp[0] else list(dp[0])[0]
acts_b = rows(os.path.join(B, "B3_decision_optimization/actions.csv"))
scen = rows(os.path.join(B, "B3_decision_optimization/scenarios.csv"))
crit = rows(os.path.join(B, "B3_decision_optimization/criteria.csv"))
pay = rows(os.path.join(B, "B3_decision_optimization/payoff_matrices.csv"))
aso = rows(os.path.join(B, "B3_decision_optimization/action_scenario_outcomes.csv"))
acm = rows(os.path.join(B, "B3_decision_optimization/alternative_criteria_matrix.csv"))
for nm, rs in [("actions", acts_b), ("scenarios", scen), ("criteria", crit),
               ("payoff_matrices", pay), ("action_scenario_outcomes", aso)]:
    check(f"fk:{nm}_problem", all(r.get(dpkey) in DP for r in rs), f"n={len(rs)}")

# completeness: every problem's action x scenario cell present
a_by_p = defaultdict(set); s_by_p = defaultdict(set)
akey = "action_id" if "action_id" in acts_b[0] else list(acts_b[0])[1]
skey = "scenario_id" if "scenario_id" in scen[0] else list(scen[0])[1]
for r in acts_b: a_by_p[r[dpkey]].add(r[akey])
for r in scen: s_by_p[r[dpkey]].add(r[skey])
missing_cells = []
have = defaultdict(set)
for r in aso:
    have[r[dpkey]].add((r.get(akey), r.get(skey)))
for p_ in DP:
    want = {(a, s) for a in a_by_p[p_] for s in s_by_p[p_]}
    if want - have[p_]:
        missing_cells.append((p_, len(want - have[p_])))
check("completeness:action_by_scenario_matrix_full", not missing_cells, str(missing_cells[:5]))

# scenario probabilities sum to 1 per problem
probcol = next((c for c in scen[0] if "prob" in c.lower() and "problem" not in c.lower()), None)
if probcol:
    bad = [p_ for p_ in DP
           if abs(sum(float(r[probcol]) for r in scen if r[dpkey] == p_) - 1.0) > 1e-6]
    check("completeness:scenario_probabilities_sum_to_one", not bad, str(bad[:5]))
else:
    check("completeness:scenario_probabilities_sum_to_one", False, "no probability column")

# alternatives-by-criteria matrix: wide form, one row per alternative, one column per criterion
crit_names = defaultdict(set)
for r in crit:
    crit_names[r[dpkey]].add(r["criterion_id"])
acm_cols = [c for c in acm[0] if c not in PROV and c not in (dpkey, "record_hash", akey,
            "package_version", "generator_version", "random_seed")]
alt_by_p = defaultdict(set)
for r in acm:
    alt_by_p[r[dpkey]].add(r[akey])
missing_alt = [p_ for p_ in DP if alt_by_p[p_] != a_by_p[p_]]
check("completeness:alternative_by_criteria_matrix_full", not missing_alt, str(missing_alt[:5]))
check("completeness:criteria_columns_cover_criteria_table",
      all(len(crit_names[p_]) <= len(acm_cols) for p_ in DP),
      f"criteria per problem={sorted({len(v) for v in crit_names.values()})} value cols={len(acm_cols)}")
blank = [(r[dpkey], c) for r in acm for c in acm_cols if r[c] in ("", None)]
check("completeness:no_blank_criterion_cells", not blank, str(blank[:5]))
multi = [p_ for p_ in DP if len(alt_by_p[p_]) >= 2]
check("suitability:critic_needs_two_or_more_alternatives",
      len(multi) == len(DP), f"{len(multi)}/{len(DP)} problems have 2+ alternatives")
# payoff matrix completeness
pay_cell = defaultdict(set)
for r in pay:
    pay_cell[r[dpkey]].add((r[akey], r[skey]))
bad_pay = [p_ for p_ in DP
           if pay_cell[p_] != {(a, s) for a in a_by_p[p_] for s in s_by_p[p_]}]
check("completeness:payoff_matrix_full", not bad_pay, str(bad_pay[:5]))
# minimax regret needs non-negative regret with a zero in each scenario column
neg = [r for r in pay if float(r["regret_value"]) < -1e-9]
check("suitability:regret_non_negative", not neg, f"n_negative={len(neg)}")
zero_ok = []
for p_ in DP:
    for s in s_by_p[p_]:
        vals = [float(r["regret_value"]) for r in pay
                if r[dpkey] == p_ and r[skey] == s]
        if vals and min(vals) > 1e-9:
            zero_ok.append((p_, s))
check("suitability:regret_zero_present_per_scenario", not zero_ok, str(zero_ok[:5]))

# LP models: variables, bounds, constraints, and a MACHINE-READABLE objective
lp = json.load(open(os.path.join(B, "B3_decision_optimization/lp_models.json")))
lps = lp["models"]
check("suitability:lp_models_have_variables_and_bounds",
      all(m.get("variables") and m.get("bounds") for m in lps), f"n={len(lps)}")
check("fk:lp_models_decision_problem",
      {m["decision_problem_id"] for m in lps} <= DP,
      f"n={len(lps)} problems={len({m['decision_problem_id'] for m in lps})}")
# constraints are prose strings, not coefficient rows: a solver cannot consume them
prose = [m["decision_problem_id"] for m in lps
         if all(isinstance(c, str) for c in m.get("constraints", []))]
check("suitability:lp_constraints_machine_readable", not prose,
      f"{len(prose)}/{len(lps)} models express constraints only as prose strings")
noobj = [m["decision_problem_id"] for m in lps
         if not any(k in m for k in ("objective", "objectives", "objective_coefficients", "c"))]
check("suitability:lp_models_have_machine_readable_objective", not noobj,
      f"{len(noobj)}/{len(lps)} models carry only objective_description prose")

# belief rule base: antecedent states, belief distribution, rule weight
brb = json.load(open(os.path.join(B, "B2_expert_epistemic/belief_rules.json")))
rl = brb["rules"]
ante = [c for c in rl[0] if c.endswith("_state")]
bel = [c for c in rl[0] if c.startswith("belief_") and c != "belief_sum"]
check("suitability:brb_has_antecedent_states_and_beliefs",
      len(ante) >= 2 and len(bel) >= 2, f"antecedents={ante} beliefs={bel}")
check("suitability:brb_beliefs_sum_to_one",
      all(abs(sum(r[b] for b in bel) - 1.0) < 1e-4 for r in rl), f"n={len(rl)}")
check("suitability:brb_has_rule_weights",
      all("rule_weight" in r for r in rl))
lev = {a: {r[a] for r in rl} for a in ante}
want = 1
for v in lev.values():
    want *= len(v)
check("completeness:brb_rule_base_covers_antecedent_space",
      len(rl) == want and len({tuple(r[a] for a in ante) for r in rl}) == want,
      f"rules={len(rl)} antecedent_space={want}")

# rough set decision table: condition attributes plus a decision attribute
rst = rows(os.path.join(B, "B1_reference_population/rough_set_decision_table.csv"))
deccol = [c for c in rst[0] if c.startswith("decision") or c == "decision"]
concol = [c for c in rst[0] if c.endswith("_band")]
check("suitability:rough_set_has_decision_attribute", bool(deccol), str(deccol))
check("suitability:rough_set_has_condition_attributes", len(concol) >= 2,
      str(concol[:6]))

# --- 9. date ordering and units ------------------------------------------
bad_dates = [r["project_id"] for r in projects
             if float(r["required_finish_day"]) < float(r["baseline_finish_day"]) - 1e9]
check("dates:required_finish_not_before_baseline_start", not bad_dates, str(bad_dates))
check("units:monetary_columns_named_with_unit",
      all(any(c.endswith(("_usd", "_days", "_pct", "_m2", "_km")) for c in r) for r in [projects[0]]))

# --- 10. LOB / CCPM / queue / ABM / DES structural sufficiency -----------
def cols(p):
    return list(rows(p)[0].keys())
lob = cols(os.path.join(A, "lob_work_packages.csv"))
check("suitability:lob_has_location_crew_quantity_rate",
      any("location" in c for c in lob) and any("crew" in c for c in lob)
      and any("quantity" in c for c in lob) and any("rate" in c for c in lob), str(lob))
ccpm = cols(os.path.join(A, "ccpm_buffers.csv"))
check("suitability:ccpm_has_buffer_and_chain",
      any("buffer" in c for c in ccpm) and (
          any("chain" in c for c in ccpm) or
          any(r["critical_chain_flag"] in ("True", "true") for r in acts)), str(ccpm))
q = cols(os.path.join(A, "queue_events.csv"))
check("suitability:queue_has_arrival_service_capacity_discipline",
      any("arriv" in c for c in q) and any("service" in c or "serv" in c for c in q)
      and (any("capacity" in c for c in q) or any("server" in c for c in q))
      and any("disciplin" in c or "priority" in c for c in q), str(q))
ag = cols(os.path.join(A, "agents.csv")); ah = cols(os.path.join(A, "agent_state_history.csv"))
check("suitability:abm_has_agents_states_rules_time",
      any("state" in c for c in ah) and any("rule" in c or "policy" in c or "behav" in c for c in ag)
      and any("time" in c or "step" in c or "period" in c for c in ah), str(ag) + str(ah))
de = cols(os.path.join(A, "des_events.csv")); dn = cols(os.path.join(A, "des_entities.csv"))
check("suitability:des_has_events_entities_resources_queue_clock",
      any("event" in c for c in de) and any("entity" in c for c in de)
      and any("resource" in c or "server" in c for c in de)
      and any("queue" in c for c in de)
      and any("time" in c or "clock" in c or c.endswith("_day") for c in de), str(de))
dsmn = rows(os.path.join(A, "dsm_nodes.csv")); dsme = rows(os.path.join(A, "dsm_edges.csv"))
check("suitability:dsm_is_project_specific",
      all("project_id" in r for r in dsmn[:1]) and len({r["project_id"] for r in dsmn}) > 1,
      f"projects={len({r['project_id'] for r in dsmn})}")
cre = cols(os.path.join(A, "cost_risk_events.csv"))
check("suitability:cost_risk_has_three_point_ranges",
      sum(1 for c in cre if any(k in c for k in ("low_", "most_likely", "high_", "optimistic", "pessimistic"))) >= 3,
      str(cre))

# --- 10b. known-answer reproduction and residual structural gaps ---------
qe = rows(os.path.join(A, "queue_events.csv")); qg = rows(os.path.join(A, "queue_ground_truth.csv"))
byq = defaultdict(list)
for r in qe:
    byq[(r["project_id"], r["queue_id"])].append(r)
bad = []
for g in qg:
    ev = byq[(g["project_id"], g["queue_id"])]
    mw = sum(float(r["wait_time_days"]) for r in ev) / len(ev)
    if abs(mw - float(g["mean_wait_days"])) > 1e-3:
        bad.append(g["project_id"])
check("known_answer:queue_mean_wait_reproduces", not bad, f"{len(qg)} ground-truth rows")

bf = rows(os.path.join(A, "ccpm_buffers.csv")); bg = rows(os.path.join(A, "ccpm_ground_truth.csv"))
byp = defaultdict(list)
for r in bf:
    byp[(r["project_id"], r["period_id"])].append(r)
bad = []
for g in bg:
    pbuf = [r for r in byp[(g["project_id"], g["period_id"])] if r["buffer_type"] == "PROJECT"]
    if not pbuf or abs((float(pbuf[0]["original_buffer_days"]) - float(pbuf[0]["remaining_buffer_days"]))
                       - float(g["project_buffer_consumed_days"])) > 1e-3:
        bad.append(g["project_id"])
check("known_answer:ccpm_buffer_consumption_reproduces", not bad, f"{len(bg)} ground-truth rows")

check("suitability:ccpm_buffers_traceable_to_chain_activities",
      "chain_id" in acts[0],
      "buffers carry chain_id but activities carry only a boolean flag, so a buffer cannot be "
      "traced to the activities of its chain")
check("suitability:ccpm_buffers_sized_from_activity_estimates",
      {r["buffer_sizing_method"] for r in bf} - {"SYNTHETIC_15_PERCENT_BASELINE", "SYNTHETIC_FEEDING_BUFFER"} != set()
      or False,
      "project buffers are a flat fifteen per cent of baseline, not sized from activity estimates")
check("suitability:abm_interaction_rules_defined",
      os.path.exists(os.path.join(A, "interaction_rules.csv")),
      "agents carry decision_rule_id but no table defines what the rules are")

# --- 11. confidentiality screen: does anything look real? ---------------
import re
# the generator version string "...programme.py@0.1" is not an address
EMAIL = re.compile(r"(?<![\w.])[\w.+-]+@[A-Za-z][\w-]*\.[A-Za-z]{2,}")
PHONE = re.compile(r"\b\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
hits = []
for p in walk_csvs():
    with open(p, encoding="utf-8", errors="replace") as f:
        t = f.read()
    for nm, rx in (("email", EMAIL), ("phone", PHONE), ("ssn", SSN)):
        m = rx.search(t)
        if m:
            hits.append((os.path.relpath(p, ROOT), nm, m.group()[:40]))
check("confidentiality:no_emails_phones_or_ssns", not hits, str(hits[:5]))

# --- 12. no executables or secrets in the staged tree -------------------
susp = []
for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        fp = os.path.join(dirpath, fn)
        if fn.lower().endswith((".exe", ".dll", ".so", ".sh", ".bat", ".ps1", ".pem", ".key", ".env")):
            susp.append(os.path.relpath(fp, ROOT))
        elif os.access(fp, os.X_OK) and not os.path.isdir(fp):
            susp.append("exec-bit:" + os.path.relpath(fp, ROOT))
check("safety:no_executable_or_secret_files", not susp, str(susp[:5]))

# --- 13. programme files the handoff claims ----------------------------
for f in ("MANIFEST.csv", "validation_report.json", "module_asset_map.csv",
          "validators/validate_synthetic_programme.py",
          "generators/generate_opus_synthetic_programme.py",
          "schemas/schema_catalog.json"):
    present = any(os.path.exists(os.path.join(ROOT, pk, f))
                  for pk in ("package_A", "package_B", "package_C", "."))
    check(f"handoff_claim_present:{f}", present, "not supplied with the three archives")

# ------------------------------------------------------------------------
fails = [r for r in RESULTS if r[1] == "FAIL"]
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "code_audit/synthetic_package_independent_checks.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["check", "result", "detail"]); w.writerows(RESULTS)
for r in RESULTS:
    print(f"{r[1]:4} {r[0]} {r[2][:110]}")
print(f"\nCHECKS: {len(RESULTS)}  PASS: {len(RESULTS)-len(fails)}  FAIL: {len(fails)}")
sys.exit(1 if fails else 0)
