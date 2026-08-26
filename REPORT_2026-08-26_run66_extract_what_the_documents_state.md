# Run 66 — extract what the documents state

**Modules holding a current result: 7 before, 9 after. Categories carrying a status: 2 before,
2 after.** Fixture and browser agree on all four numbers.

The module count moved. **The category count did not, and that is a failure against §1.** The
reason is measured, not supposed: both categories that gained a computing module this run (A2,
A3) hold only modules that assert **no band** — `band_asserted: false`, `status_color: null`,
`calibration_pending: true` — so the category fuses to a null status. That is a band question and
§8.6 forbids touching it.

Repository: the Linux clone at `/home/user/LinPRojectRadar`. Branch `main` at `7b211ac`
(Run 65's voting change, still unpushed). **No production byte changed in this run**; the only
new file is a driver under `server/tools/`.

## The measurement

| | Before (`drive_run65_every_module_votes.py`) | After (`drive_run66_extract_what_documents_state.py`) |
|---|---|---|
| Modules holding a result, fixture | 7 | **9** |
| Modules holding a result, browser (`row_module_results`) | 7 | **9** |
| Categories carrying a status, fixture | 2 | 2 |
| Categories carrying a status, browser (`LIT_ON_PAGE`) | 2 | 2 |
| Module ids | A1.2, A1.7, A1.8, A3.2, A4.2, A4.3, A4.4 | + **A2.7**, **A3.6** |

Both runs: uploads through `projectupload`, computation through `projectcomputeall`, page loaded
from a live uvicorn server, nothing pre-primed, current period 2.

## What was already there, and what was actually missing

**No extraction field had to be added.** The two modules that lit were blocked by an absent
DOCUMENT, not by an absent field:

* **A2.7 Milestone Trend Analysis.** `milestones_json` is already asked of every
  `schedule_update` (`extraction_fields.py:180`), already parsed by
  `schedule_activities.read_activity_table`, already stored per period, and already assembled
  into `milestoneForecastHistory` by `documents._milestone_forecast_history` (line 938). No
  fixture had ever uploaded a schedule update carrying the table in **two** periods, so the store
  held fewer than two snapshots and A2.7 abstained on its own guard.
* **A3.6 Cost Risk Analysis P80.** `documents._persist_project_risks` reads risk rows from the
  document's own bytes via `risk_register.risk_rows_from_document`, and `documents.py:1541`
  assembles `costRiskModel` from the register plus the reported budget. Only a `.docx` is
  openable on this side of the model boundary, and no fixture had ever uploaded one.

## The hand-computed checks (§5.4)

**A2.7**, formula `MV = ForecastDate − BaselineDate`, `MD = Forecast_t − Forecast_t−1`:

| Milestone | Baseline | P1 forecast | P2 forecast | Variance | Drift | Direction |
|---|---|---|---|---|---|---|
| MS-01 | 2026-06-30 | 2026-07-04 | 2026-07-08 | +4, **+8** | +4 | deteriorating |
| MS-02 | 2026-09-30 | 2026-10-14 | 2026-10-28 | +14, **+28** | +14 | deteriorating |
| MS-03 | 2026-12-15 | 2026-12-15 | 2026-12-11 | 0, **−4** | −4 | improving |

Module reported `worst_variance_days = 28.0`, `deteriorating_count = 2`, `milestone_count = 3`.
Hand computation agrees on every cell.

**A3.6**, four independent Bernoulli point impacts on a $4,000,000 base. Enumerating all 16
subsets by hand: cumulative probability reaches 0.769 at $4,300,000 and 0.832 at $4,320,000, so
the exact 80th percentile is **$4,320,000**. Module reported `p80_total_cost = 4,320,000`.
Exact agreement.

## Every module still dark, and what made me conclude it

**Seventeen modules — the whole of A6, B1, B2, B3 (the order's C6 Regulatory), B4 — abstain with
one identical sentence**, read off the stored result row, not off any registry:

> "The evidence offered to this measure carries no Category-9 assessment, so it is unassessed and
> not eligible for this use. No reading is produced and no figure is used in its place."

`qualification_boundary.install` wraps every gated runner and refuses before the module executes
when `si["evidenceQualification"]` is absent. **A repository-wide grep finds `QUALIFICATION_KEY`
written nowhere**: no document type carries a Category-9 assessment, no extraction emits one, no
intake path supplies one. These seventeen are not an extraction problem and no amount of
extraction reaches them.

**The modules that refuse a substitute, in their own words** — each has the near-miss input
present in `signal_inputs` on the fixture and still declines:

* **A2.8 Look-Ahead Schedule Health.** `activitiesPlanned`, `activitiesConstrained` and
  `lookaheadWeeks` are all present in the stored `signal_inputs`. `canonical_v3.look_ahead_ready_fraction`
  still requires an inventory: each activity with its own identity and constraint status.
  Supplying the two counts would be inventing activity identities.
* **A2.9 Resource Loading Index.** `plannedLaborHours` and `actualLaborHours` are present.
  `canonical_v3.resource_loading`: *"A project-total planned-versus-actual labour ratio is not
  this index and is not computed here: the structure must be time-phased and must state the
  capacity, not only the demand."* Planned hours are not available capacity.
* **A3.3 Labor Productivity Index.** Needs quantity installed and quantity planned. **No document
  type in `_EXTRACTION_FIELDS` asks for an installed quantity at all** — the whole field table
  was read; the word does not appear.
* **A3.5 Overhead Absorption Rate.** `indirectCostPlan` and `indirectCostActual` are present from
  `cost_report`. `canonical_v3.overhead_absorption`: *"Indirect actual over indirect plan with no
  allocation base is not overhead absorption and is computed nowhere here."*

**A5 / the order's C7 (seven modules).** All seven abstain on absent governed structures
(`dsmDependencyModel`, `sensitivityModel`, `scenarioSet`, `systemDynamicsModel`, `queueModel`,
`agentSupplyChainModel`, `desProcessModel`). The corpus **does** hold these relations —
`dsm_edges.csv`, `system_dynamics_timeseries.csv`, `queue_events.csv`, `des_events.csv`,
`agents.csv` in `OG-SYNTH-0.3/.../package_A_project_structures/` — but every row carries
`data_origin = SYNTHETIC_RESEARCH_FIXTURE` and `not_for_empirical_validation = True`, and there is
no document route from any of them into a project. The order's expectation that C7 stays dark
holds, and the reason is the missing route, not missing data.

## The corpus, opened

`research_fixtures/` holds **371 files** (not 336): 277 `.csv`, 34 `.json`, 27 `.md`, 15
`.sha256`, 7 `.py`, 5 `.xlsx`, 3 `.zip`, 2 `.txt`. Every directory was listed and the
package_A tables were opened. **There is still no document of any of the 21 PM types anywhere in
the repository** — the tables are ground-truth oracles carrying generator provenance columns, not
pay applications or RFI logs. Stated for those types and moved past, per §3.

## Freeze and mint

**The behaviour digest did not move: no production byte changed.** Run 65's mint remains
outstanding; this run adds none. `test_run37_freeze_gate` prints `RESULT: 32/34 checks passed`,
failing `generator_runs` and `reproduces` — the inherited state, unchanged by this run, and not
weakened or bypassed.

## Found and not fixed

1. **A2 and A3 hold a computing module and still carry no status.** A2.7, A3.2 and A3.6 all
   report `band_asserted: false`. Until a boundary is established for those quantities, no
   category they sit in can light. This is the single thing standing between this run's module
   count and a category count.
2. **`evidenceQualification` has no writer anywhere in production.** Seventeen modules across
   five categories are unreachable until something supplies it.
3. **Only `.docx` tables are readable** by the register and schedule readers; a CSV or XLSX
   register uploaded as a document yields no rows.
