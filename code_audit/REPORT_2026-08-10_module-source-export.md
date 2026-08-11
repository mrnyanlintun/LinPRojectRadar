# Module source export by group, for external audit — 2026-08-10

**SUPERSEDED. Read `REPORT_2026-08-11_run5-export.md` instead.** The four group files this report
accompanied wrote 43 of the 52 Group A sections the counts on this page claim, omitting A4.2
through A4.10 (RFI Velocity, Submittal Rejection Rate, NCR Rate, Weather Day Impact, Change Order
Frequency, Dispute Escalation Index, Subcontractor Performance, Procurement Lead Time Monitor,
Specification Conflict Density), because nothing checked the emitted section count against the
expected id set. The group files in this directory have since been regenerated in full from the
registry, with that check now enforced; this report's own count tables and analysis below describe
the incomplete export and are kept only as the historical record of that defect, not as current
guidance. Any external review already performed against the four group files as they stood on
2026-08-10 was performed against that incomplete package and its Group A findings should be
re-read against the regenerated files.

This report accompanies four group files (`GROUP_A_project-health.md`, `GROUP_B_recommendation-
governance.md`, `GROUP_C_data-evidence-health.md`, `GROUP_D_portfolio-level.md`) and one shared-
machinery file (`SHARED_MACHINERY.md`), all in this `code_audit/` directory. Together they export
the full verbatim source of every module the analytical server computes, grouped, with each
module's inputs, literal constants and their provenance (or lack of it), outputs/banding, and
abstention behavior, for a reviewer with no repository access.

**Scope and method.** This audit read every file under `server/app/simulation/` in full:
`models.py`, `models_evm.py`, `models_ext.py`, `models_doc.py`, `models_gov.py`,
`models_fuzzy.py`, `models_evc.py`, `models_decision.py`, `models_dq.py`, `models_sim.py`,
`portfolio.py`, `fusion.py`, `rng.py`, `compute.py`, `registry.py`, plus
`server/tools/test_group_assignment.py` (the check that keeps `GROUP_ASSIGNMENT.md` honest),
`NAMING_AUTHORITY.md`, `GROUP_ASSIGNMENT.md`, `p0-baseline/module_renumbering_map.csv`,
`server/app/field_registry.py`, and the relevant sections of `T6_HANDOFF.md` (read in ~300-400
line chunks across its full 5389 lines, focusing on the sections the task named plus a scan of
section headings for any other literal-with-no-provenance findings). No code, test, or data file
outside `code_audit/` was modified.

**Out of scope, by design.** Correctness of the formulas is not evaluated; only their content,
inputs, and provenance are extracted and reported. The assembly code that builds `si["signals"]`,
`si["evm"]`, `si["mc"]`, `si["cusum"]`, `si["doc"]`, `si["events"]`, `si["sources"]` and the
portfolio-level `history` parameter (all outside `server/app/simulation/`, mostly in `documents.py`
and related merge code) was not independently re-derived line-by-line; each module's "Availability"
discussion in the group files states this and cross-references `field_registry.py` where that file
is the authority, and states plainly where a module consumes an assembled structure this audit did
not trace further.

---

## 1. Counts, established directly from the code

**Method:** loaded `server/app/simulation/models.py`'s `VALIDATED` dict (populated by
`_register_extensions()`, which merges in every group's extension dict:
`A1_EXTENSIONS`, `A2_EXTENSIONS`, `A3_EXTENSIONS`, `A4_EXTENSIONS`, `A5_EXTENSIONS`,
`A6_EXTENSIONS`, `GOV_BATCH_A`, `GOV_BATCH_B`, `EVC_EXTENSIONS`, `FUZZY_EXTENSIONS`,
`DQ_EXTENSIONS`, `DECISION_EXTENSIONS`), and `server/app/simulation/portfolio.py`'s
`PORTFOLIO_VALIDATED` dict. This audit hand-counted every module id listed in each group's dict
literal in the source files transcribed into the four group files (not merely trusted the size of
a Python collection).

**Result, counted by hand from the dict literals in the code (not from any document):**

| Group | Counted from | Count |
|---|---|---|
| A | base `VALIDATED` (7: A1.1, A1.2, A2.1, A2.2, A2.3, A3.1, A5.1) + `A1_EXTENSIONS` (9) + `A2_EXTENSIONS` (8) + `A3_EXTENSIONS` (8) + `A4_EXTENSIONS` (9) + `A5_EXTENSIONS` (7) + `A6_EXTENSIONS` (4) | **52** |
| B | `GOV_BATCH_A` (8) + `GOV_BATCH_B` (7) + `EVC_EXTENSIONS` (8) + `FUZZY_EXTENSIONS` (11) + `DECISION_EXTENSIONS` (2) | **36** |
| C | `DQ_EXTENSIONS` | **7** |
| D | `PORTFOLIO_VALIDATED` | **5** |
| **Total** | | **100** |

This matches `GROUP_ASSIGNMENT.md`'s counts (52/36/7/5, total 100) and
`server/tools/test_group_assignment.py`'s `EXPECTED_COUNTS`/`EXPECTED_TOTAL` constants exactly, by
independent hand-count of the dict literals rather than by trusting the artifact file or the
test's own assertion.

**Separately, this audit queried the registry CSV itself** (`p0-baseline/module_renumbering_map.csv`,
the file `registry.py`'s loader reads):

```
python3 -c "
import csv
from collections import Counter
rows=list(csv.DictReader(open('p0-baseline/module_renumbering_map.csv', encoding='utf-8-sig')))
live=[r for r in rows if r['new_id']!='RETIRED']
print(Counter(r['group'] for r in live), sum(1 for _ in live))"
```
Result: **A=53, B=36, C=7, D=5, total=101 live rows in the CSV** (two rows marked `RETIRED` are
excluded). The one-row difference in Group A (53 in the CSV vs. 52 actually computed) is exactly
**A4.1 Document Risk Score**, present in the CSV but absent from `VALIDATED` — confirmed directly:
`A4.1` does not appear in `A4_EXTENSIONS` or anywhere else in `models_doc.py`. This matches
`GROUP_ASSIGNMENT.md`'s own explanation verbatim.

**So: the registry code computes 100 modules (52/36/7/5), and the registry's own declared list
(the CSV) names 101 live entries (53/36/7/5), with the one-module gap in Group A being Document
Risk Score, excluded by design.**

---

## 2. Every other place a count appears in the repository, and whether it agrees

| Location | What it says | Agrees with the registry-computed 100 (52/36/7/5)? |
|---|---|---|
| `NAMING_AUTHORITY.md` §4 | "100 distinct computations... A 52, B 36, C 7, D 5" | **Agrees.** |
| `GROUP_ASSIGNMENT.md` | Table: A 52, B 36, C 7, D 5, total 100; separately states the registry declares 101 live entries and explains the A4.1 exclusion | **Agrees** with the 100-count; its stated 101-live-entries figure agrees with the CSV row count independently verified here. |
| `server/tools/test_group_assignment.py` | `EXPECTED_COUNTS = {"A": 52, "B": 36, "C": 7, "D": 5}`, `EXPECTED_TOTAL = 100` | **Agrees**, and is the automated check keeping the artifact in sync. |
| `p0-baseline/module_renumbering_map.csv` (row count) | 101 live rows (53 in Group A) | **Disagrees by exactly 1** — the CSV names 101 *declared* modules; the registry actually *computes* 100 (the documented Document Risk Score exclusion). |
| `assets/js/taxonomy.js` / `assets/js/categories.js` (`window.LIN_CATEGORIES`) | 12 categories, 101 modules — the whole taxonomy, including the never-computed Document Risk Score | **Disagrees by 1**, same reason. |
| `server/tools/test_map_and_module_count.py` | Docstring: "The detail page advertised 101 modules across 12 categories. That is the whole taxonomy." Also asserts `tx["projMods"] == 96` ("a project has 96 modules") | **Disagrees on both figures relative to the registry's 100/95**: 101 is the whole (uncomputed-Document-Risk-Score-included) taxonomy count; 96 is 101 minus the 5 Group D portfolio-only modules — neither equals the registry's 100 or 95 (100 minus Group D). This test pins the client-side taxonomy's counts, a different quantity from the server registry's. |
| `assets/js/app.js` `activeModuleTotal()` | Sums `LIN_CATEGORIES` (normally 101) but **falls back to a hardcoded literal `103`** if `LIN_CATEGORIES` is unavailable (per `REPORT_2026-08-10_map-and-module-count.md`) | **Disagrees with everything else found.** 103 matches neither the registry's 100, the CSV's 101, nor `LIN_CATEGORIES`'s own 101. |
| `assets/js/detail.js` `buildModuleAxes()` | Sums the whole `LIN_CATEGORIES` taxonomy (101) but is **dead code** — no callers anywhere, per both a 2026-08-10 report and `test_map_and_module_count.py` | Would agree with the 101-taxonomy figure if ever called; contributes no live disagreement since it is unreachable. Noted for completeness. |
| `REPORT_2026-08-05_chart-group-labels.md` | "12 categories / 101 modules total." | **Disagrees by 1**, same taxonomy-vs-registry distinction. |
| `T6_HANDOFF.md` (multiple sections) | Repeatedly states "12 categories / 101 modules total" for the client taxonomy; separately narrates the 2026-08-10 fix stopping the detail page from showing whole-taxonomy 101/103 figures on a single-project page (which should show 96) | Internally consistent with the taxonomy-side 101/96 figures; does not use the registry's 100/95 figures in these sections — a different accounting frame from `NAMING_AUTHORITY.md`/`GROUP_ASSIGNMENT.md`. |
| `assets/js/simulations.js:2345` (code comment) | "Quantifies the QUALITY of the inputs the other 100 modules..." | **Agrees** with the registry's 100. |

**Summary, reported factually per the task's instruction not to resolve it:** at least three
distinct counting frames are in active use: (1) the **registry-computed** 100 (52/36/7/5),
matching `NAMING_AUTHORITY.md`, `GROUP_ASSIGNMENT.md`, and `test_group_assignment.py`; (2) the
**client-side whole-taxonomy** 101 modules / 12 categories from `LIN_CATEGORIES`, matching the
CSV's live-row count and several report files, still nominally listing the never-computed Document
Risk Score; and (3) a **stale, disagreeing literal**, `activeModuleTotal()`'s fallback of **103**,
matching neither of the other two frames and left in place per the 2026-08-10 handoff report. This
audit does not resolve which is "correct."

---

## 3. Literals with no provenance — scale, summarized (exhaustive per-module listing is in the
group files)

Every group file lists, module by module, every numeric literal in that module's formula and
states explicitly whether the code carries any comment, docstring, or citation for it. The great
majority carry **no comment, no provenance** — this audit did not find a single banding threshold
(the Green/Amber/Red or four-tier cut points present in nearly every module) justified by a
comment anywhere in Groups A, B, or C. The few literals that do carry a provenance note are called
out individually where found (e.g. DSM Rework Propagation's docstring explaining a discrepancy
with a discarded 0.40 value, not the origin of the 0.30 actually used; the `1.28` P80 z-score
constant recognizable by shape though never labeled as such in a comment; Fermatean Fuzzy's `0.95`
renormalization decay documented as "reproduced verbatim" for bit-for-bit reasons, not for its
numeric meaning).

This audit counted, conservatively, **well over 150 individual uncommented numeric literals**
across the 100 modules (banding thresholds alone account for roughly 2-4 per module across the
~95 modules that band at all, plus formula-specific constants — weights, scale factors, caps,
floors, lookup-table entries). Several modules carry dense literal surfaces on their own: PLTS
(B2.6, 14 belief triples = 42 numbers), Belief Rule Base (B2.8, 8 rules x belief-triple + weight =
32 numbers), Hypersoft Sets (B2.20, a 24-entry lookup table), Dempster-Shafer (B2.1, 16 belief
quadruples = 64 numbers), and `fusion.py`'s shared `STATUS_MASS` table (16 numbers). This audit did
not produce one canonical total across the codebase; the group files are the exhaustive per-module
record.

**The three cases the task brief named specifically, verified against the current code:**

1. **Cost Risk Analysis P80 (A3.6, `run_cost_risk` in `models_ext.py`).** Spread computed as
   `max(0.03, abs(1 - cpi)) * 0.5`, multiplied by a literal `1.28`. No distribution, no sample, no
   comment on any of the three literals. Confirmed to match `T6_HANDOFF.md`'s 2026-08-10 "risk
   register read as data" section exactly, including that section's statement that the suite
   reproduces the reported $10,555,811 / 79.7% figures from this exact formula.

2. **Reference Class Forecasting (A3.1, `run_rcf` in `models.py`).** Nine literal multipliers
   `[1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52]`, no comment or citation. The shared
   `pctile()` helper is confirmed index-based (`floor(q * (len-1))`), not interpolating, over this
   fixed nine-element list, so P80 is mechanically always exactly `1.38` (index 6) and the
   reported overrun is always exactly `+38.0%`, on every project, every period. This audit
   independently walked the index arithmetic by hand and confirms the handoff's assertion. **The
   module cannot abstain today**: `bac` is read via `num(si.get("bac"), 0.0)`, silently
   substituting 0.0 for a missing budget rather than gating entry; there is no `insufficient()`
   call anywhere in `run_rcf`.

3. **Regret Minimization Index (B4.7, `run_regret_minimization` in `models_gov.py`).** Verified
   against the current code, not history. The fixed payoff matrix (`monitor: {0,5,30}`,
   `investigate: {5,0,10}`, `escalate: {15,8,0}`) and future-state probabilities
   (`{improves: 0.3, stable: 0.4, worsens: 0.3}`) are **still present**, still compute a fixed
   `expected_regret` of `{"monitor": 11, "investigate": 5, "escalate": 8}` on every call (matching
   the `{11, 5, 8}` triple the task brief names), and this dict is **still printed** in the
   module's own output as a top-level `expected_regret` key. What has changed by the current
   session (per the code comment `# Signal-state override: escalate on FAR breach, investigate
   below 0.95.`) is that the actual `recommended_action`/`status_color` is now driven almost
   entirely by a `cpi`/`spi` threshold override — the fixed-literal minimax step only decides the
   outcome when both `cpi >= 0.95` and `spi >= 0.95`, and there it always resolves to
   "investigate" (never "monitor"), because `investigate`'s fixed expected regret (5) is always
   lower than `monitor`'s (11) under these unchanging literals. If the task brief's "the card no
   longer prints these constants" refers to a display layer outside `server/app/simulation/`, that
   layer was not located by this registry-scoped audit — reported as a discrepancy, not resolved.

**Other findings cross-checked against the handoff, as instructed:**

- **Monte Carlo `p80_eac` (A1.1).** Confirmed the handoff's framing: stores its own `p80_eac` from
  a Beta-PERT model whose envelope (`o=m_eac*(1-0.10*s)`, `p=m_eac*(1+0.40*s)`) and spread weights
  (`0.5/0.3/0.2`) are all uncommented — a larger invented-parameter surface than Cost Risk
  Analysis's, per the handoff. The module itself is unchanged; only a display card outside this
  audit's scope stopped quoting it. Independently found: `monte_carlo_eac`'s CUSUM-penalty branch
  reads `cusumBreached`/`cusumDrift`/`cusumThreshold` from its `inputs` dict, but
  `run_monte_carlo` never passes any of the three in — dead code, always the zero-valued fallback.
- **Parametric Cost Index (A3.8).** Confirmed the handoff's correction directly in the code: no
  invented multipliers or spread constants; its only literals are the three RAG banding cut points
  on a ratio of two independently-computed EAC conventions over four genuinely extracted figures.
- **Schedule Risk Analysis P80 (A2.10).** Not named in the task brief but structurally identical
  to Cost Risk Analysis (`max(0.05, 1-spi)*0.5`, times the same literal `1.28`) — flagged in the
  Group A file as sharing the same critique, though the handoff text names only the cost-side
  module.
- **`fusion.py`'s `STATUS_MASS` table.** Sixteen fixed belief-mass values with no comment,
  structurally similar to the per-module belief tables throughout Group B.

---

## 4. Inputs found to be dead-on-arrival today

Cross-referenced against `server/app/field_registry.py`'s `FIELD_KINDS` (emittable),
`UNEMITTABLE_FIELDS`, and `NEEDS` (declared-servable series/event-sets). This audit confirmed
`server/app/document_evidence.py` exists (377 lines) but judged availability primarily against
`field_registry.py`, which is the layer that governs what can reach `signalInputs`.

**Confirmed dead-on-arrival:**

1. **`indirectCostPlan` / `indirectCostActual`** (read by Overhead Absorption Rate, A3.5). Neither
   key appears anywhere in `field_registry.FIELD_KINDS`. This module abstains on every real
   project today, unless something outside `field_registry.py` (not located) supplies them.

2. **`rfiNumber` / `rfiResponseTimeDays`.** Both listed in `field_registry.UNEMITTABLE_FIELDS`,
   with that file's own comment stating why ("written only by the individual `rfi` form, which no
   longer arrives"). RFI Velocity (A4.2) reads both as fallbacks; those fallback branches are dead
   code since the primary fields (`rfiCount`, `rfiAvgResponseDays`) are the ones actually
   emittable.

3. **`fairnessSensitive`** (referenced at length in a `models_decision.py` comment, not read by
   any current code path). Not a `field_registry.py` entry. Confirmed genuinely dead by the
   module's own comment.

**Near-misses, not confirmed dead:**

4. **`spiHistory` / `cpiHistory`** — declared `servable: True`, but need at least 2 prior computed
   periods; a brand-new project's first two periods genuinely lack them (expected, documented
   behavior, not a registry gap).

5. **`milestoneHistory`** — declared servable "SERVABLE SINCE 0021" per `field_registry.py`'s own
   comment; additionally requires milestone *names* to match exactly across periods.

6. **`docDate`** — listed in `UNEMITTABLE_FIELDS` by name, but the same file clarifies it is
   derived at selection time from the latest `as_of` among selected observations; not independently
   traced further (the derivation code is outside `field_registry.py`).

**Orphaned in the opposite direction:** `qualityRating` is emittable (SNAPSHOT) but no module in
the simulation layer reads it — Contractor Performance Score (A6.4) reads only `overallRating`,
`scheduleRating`, `costRating`.

**Total dead-on-arrival input fields found: 5 distinct dead references** (`indirectCostPlan`,
`indirectCostActual`, `fairnessSensitive`, `rfiNumber`, `rfiResponseTimeDays`), each cited in its
module's "Availability" section in the relevant group file.

---

## 5. Modules whose source could not be located, or whose registry entry didn't match the code

**None.** All 100 registered modules were located in `server/app/simulation/`, their source quoted
in full in the corresponding group file, and each `method_class` string checked against its
`module_name` in `p0-baseline/module_renumbering_map.csv` — every one matched (accounting for the
expected CamelCase/underscore naming difference).

**One naming/implementation mismatch worth the reviewer's attention, though not a missing-source
case:** in Constraint Satisfaction Analysis (B4.3), one of the four constraints is labeled `"FAR
threshold (overrun < 25%)"` in its own output but is actually implemented as `si["cpi"] > 0.80` —
no EAC, no overrun percentage, and no `25` literal appear anywhere in that constraint's actual
check. Flagged in the Group B file.

**Document Risk Score (A4.1)** is the one CSV-declared module with no corresponding computation
anywhere in the code — the documented, deliberate exclusion `GROUP_ASSIGNMENT.md` itself explains,
not a "could not be located" finding. Per the task brief, it is excluded from the group files.

---

## 6. Deliverables in this directory

- `GROUP_A_project-health.md` — 52 modules
- `GROUP_B_recommendation-governance.md` — 36 modules
- `GROUP_C_data-evidence-health.md` — 7 modules
- `GROUP_D_portfolio-level.md` — 5 modules
- `SHARED_MACHINERY.md` — status banding helpers, Dempster-Shafer fusion, abstention contract,
  vote bucketing, JS-compatibility numeric helpers, quoted once and referenced by name
- `REPORT_2026-08-10_module-source-export.md` — this file
