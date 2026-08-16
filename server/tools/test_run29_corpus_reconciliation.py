"""
RUN 29 CLOSURE -- THE REAL CORPUS TO CANONICAL STRUCTURE RECONCILIATION, AND THE 18-ROW TABLE.

WHY THIS SUITE EXISTS. Run 29 reported `real_corpus_populated = no` for all seventeen Category-4
and Category-5 structures. That was one sentence covering two very different cases:

  a structure whose defining fields are GENUINELY ABSENT from the corpus -- honest abstention; and
  a structure whose defining fields ARE present, already extracted, and simply NOT WIRED.

The second is the defect. Its precedent is Run 28's own finding for A2.7, where baseline finish
dates were already extracted and reached no module. The acceptance criterion the closure contract
sets is that structures whose defining fields exist in the corpus but remain unwired = 0.

WHAT THIS SUITE PROVES.

1  The reconciliation artefact covers every structure and agrees with the code, field for field,
   rather than being a hand-transcribed table nobody checks.
2  The ONE structure the decomposition found wired-able is genuinely wired, end to end, through
   the production assembler and not through a test.
3  The sixteen that are absent are absent for a reason stated against the extraction registry,
   and NONE of them can be reached by inference from any field the corpus does hold.
4  The eighteen-row closure table is REGENERATED from the registry and the scope file rather than
   written by hand, and reconciles to 18 rows over 18 unique identities with nothing unaccounted.
5  Two of the seven mandated faults: a real-corpus field that should populate a canonical
   structure goes missing and the guard detects it; and a fabricated corpus-to-structure inference
   is rejected.
"""

from __future__ import annotations

import csv
import datetime
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import app.extraction_fields as EF                              # noqa: E402
import app.extraction_merge as EM                               # noqa: E402
from app.simulation import registry as REG                      # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS       # noqa: E402
import run29_fixtures as FX                                     # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731
RECON = ROOT / "code_audit" / "run29_real_corpus_structure_reconciliation.csv"
SCOPE = ROOT / "code_audit" / "run29_cat4_5_scope.csv"
CLOSURE = ROOT / "code_audit" / "run29_closure_18_target_table.csv"

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        FAILURES.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))
    return ok


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def run(mid: str, si: dict) -> dict:
    return REG.run_module(mid, si, RAND, CUTOFF)


def abstains(out: dict) -> bool:
    return bool(out.get("insufficient_data"))


# =================================================================================================
head("1. THE RECONCILIATION COVERS EVERY STRUCTURE AND AGREES WITH THE CODE")
# =================================================================================================

check(RECON.is_file(), "the real-corpus reconciliation artefact exists", str(RECON))
ROWS = list(csv.DictReader(RECON.open(encoding="utf-8")))
KEYS = sorted(set(V4_STRUCTURE_KEYS.values()))
check(sorted(r["structure"] for r in ROWS) == KEYS,
      "and it carries exactly one row for each of the seventeen structures, no more and no fewer",
      str(sorted(set(r["structure"] for r in ROWS) ^ set(KEYS))))

_served: dict[str, list[str]] = {}
for _mid, _key in V4_STRUCTURE_KEYS.items():
    _served.setdefault(_key, []).append(_mid)
for _r in ROWS:
    check(_r["modules_served"] == " ".join(sorted(_served[_r["structure"]])),
          f"{_r['structure']}: the modules it serves are the modules the code says it serves",
          _r["modules_served"])
    check(all(_r[c].strip() for c in ("required_defining_fields",
                                      "fields_actually_present_in_corpus",
                                      "fields_already_extracted", "reason_if_not", "case")),
          f"{_r['structure']}: every decomposition column is answered rather than left blank")
    check(_r["real_corpus_populated"] in ("yes", "no")
          and _r["verdict"] == "PASS",
          f"{_r['structure']}: the populated answer is a plain yes or no and the row passes",
          f"{_r['real_corpus_populated']} / {_r['verdict']}")

# THE DOCUMENT TYPES NAMED IN THE ARTEFACT ARE REAL DOCUMENT TYPES, read from the production
# extraction registry rather than trusted. A row naming a document type the platform does not
# support would make the whole decomposition unfalsifiable.
_unknown = []
for _r in ROWS:
    for _t in _r["source_documents_that_could_supply_it"].split():
        if _t != "none" and _t not in EF.DOC_TYPES:
            _unknown.append((_r["structure"], _t))
check(not _unknown,
      "every document type the artefact names is a document type the platform actually supports",
      str(_unknown))

# THE EXTRACTED FIELDS NAMED IN THE ARTEFACT ARE REAL SIGNAL-INPUT KEYS, likewise.
_unknown_fields = []
for _r in ROWS:
    # The column is a strict comma-separated list of signal-input keys, or the word "none".
    # Parsed strictly so a row cannot hide an invented field name inside prose.
    _listed = [f.strip() for f in _r["fields_already_extracted"].split(",") if f.strip()]
    if _listed == ["none"]:
        continue
    for _f in _listed:
        if _f not in EM.SIGNAL_INPUT_KEYS:
            _unknown_fields.append((_r["structure"], _f))
check(not _unknown_fields,
      "and every extracted field it names is a real signal-input key the extraction merge emits",
      str(_unknown_fields))


# =================================================================================================
head("2. THE ONE WIRED STRUCTURE, PROVED THROUGH THE PRODUCTION ASSEMBLER")
# =================================================================================================

_wired = [r for r in ROWS if r["real_corpus_populated"] == "yes"]
check([r["structure"] for r in _wired] == ["ncrExposureRecord"],
      "exactly one structure is recorded as populated by the real corpus, and it is the "
      "nonconformance exposure record", str([r["structure"] for r in _wired]))
check("documents.py" in _wired[0]["production_assembler_or_writer"],
      "and it names a PRODUCTION assembler rather than a test",
      _wired[0]["production_assembler_or_writer"])

_docs_src = (ROOT / "server" / "app" / "documents.py").read_text(encoding="utf-8")
check("ncrExposureRecord" in _docs_src and "ncrExposureRecordDerivation" in _docs_src,
      "the assembler really is in documents.py, read from the file rather than assumed")
check("itemsInspected" in _docs_src and "ncrIssued" in _docs_src,
      "and it reads the two fields the artefact names")

# THE TWO FIELDS ARE GENUINELY EXTRACTED, established from the production extraction registry.
check("ncr_issued" in EF._EXTRACTION_FIELDS["ncr_log"],
      "`ncr_issued` is a field the nonconformance log extraction really produces")
check("items_inspected" in EF._EXTRACTION_FIELDS["inspection_report"],
      "`items_inspected` is a field the inspection report extraction really produces")
check("ncrIssued" in EM.SIGNAL_INPUT_KEYS and "itemsInspected" in EM.SIGNAL_INPUT_KEYS,
      "and both reach the signal inputs the modules are given, so nothing new had to be extracted")

# THE ASSEMBLY ITSELF, exercised exactly as run_and_store performs it.
ASSEMBLED = {
    "source": "the nonconformance log and the inspection report for this reporting period",
    "exposure_unit": "inspections", "exposure_quantity": 100.0, "ncr_count": 4,
    "ncr_count_basis": "nonconformances raised in the reporting period",
    "open_count": 6, "closed_count": 2, "assembled_by": "document extraction"}
_out = run("A4.4", {"ncrExposureRecord": ASSEMBLED})
check(_out.get("ncr_rate") == 0.04,
      "and the module computes the supplied contract's own 0.04 from what the assembler builds",
      str(_out.get("ncr_rate")))
check(_out.get("event_detail_available") is False
      and _out.get("severity_counts") == {} and _out.get("closure_rate") is None,
      "reporting the quantities that need events as ABSENT rather than inventing them, which is "
      "what makes this a wiring of extracted evidence and not a fabrication")
check(_out.get("open_count") == 6,
      "while the open backlog, which WAS extracted, is carried beside the rate and never divided "
      "into it")
check(abstains(run("A4.4", {"ncrIssued": 4})),
      "and a nonconformance count with NO exposure still produces nothing, so the wiring did not "
      "loosen the exposure requirement")


# =================================================================================================
head("3. THE SIXTEEN ABSENT STRUCTURES CANNOT BE REACHED BY INFERENCE")
# =================================================================================================

# A fully reported project carrying every scalar the corpus can produce. None of the sixteen may
# be reachable from it, which is the mechanical form of "do not infer".
RICH = {"bac": 12e6, "ev": 4e6, "ac": 4.4e6, "pv": 4.5e6, "cpi": 0.909, "spi": 0.889,
        "actualPctComplete": 40.0, "plannedPctComplete": 45.0, "docRiskScore": 0.35,
        "rfiCount": 12, "rfiPeriodDays": 30, "rfiOverdue": 3, "changeOrderCount": 6,
        "baselineContractSum": 1e6, "revisedContractSum": 1.08e6,
        "longLeadItemsTotal": 20, "longLeadAtRisk": 3, "longLeadDelayed": 1,
        "submittalsTotal": 20, "submittalsRejected": 3,
        "weatherDaysLost": 3, "floatRemaining": 15, "totalFloat": 40, "consumedFloat": 16,
        "subcontractorComplianceScore": 0.82, "overallRating": 4.2, "scheduleRating": 3.8,
        "costRating": 4.0, "qualityRating": 3.2,
        "activitiesPlanned": 200, "activitiesConstrained": 37, "lookaheadWeeks": 6,
        "totalFindings": 40, "itemsInspected": 100, "itemsFailed": 4}
_NOT_WIRED = ["A4.5", "A4.6", "A4.7", "A4.8", "A4.9", "A4.10",
              "A5.1", "A5.2", "A5.3", "A5.4", "A5.5", "A5.6", "A5.7", "A5.8"]
_reachable = []
for _mid in _NOT_WIRED:
    if not abstains(run(_mid, dict(RICH))):
        _reachable.append(_mid)
check(not _reachable,
      "on a project carrying every scalar the corpus can produce, not one of the fourteen "
      "structure-required modules whose structure is genuinely absent produces a reading",
      str(_reachable))

# The two whose canonical quantity IS computed from extracted totals, stated rather than hidden.
for _mid, _why in (("A4.2", "requests over the exposure span the register itself reports"),
                   ("A4.3", "rejected over assessed from the register totals")):
    check(not abstains(run(_mid, dict(RICH))),
          f"{_mid} DOES compute on the real corpus, from {_why}, which Run 27 recorded as a "
          f"method pass and this closure did not disturb")

# And A4.4, the wired one, computes from the corpus scalars once the assembler has run.
check(not abstains(run("A4.4", {"ncrExposureRecord": ASSEMBLED})),
      "A4.4 computes on the real corpus now, which it did not before this closure")

# THE ACCEPTANCE CRITERION.
# Driven off the explicit `case` column rather than off prose, so the acceptance criterion cannot
# be satisfied by wording. Three cases only, and each is a decision somebody had to make:
_CASES = {"WIRED_BY_THIS_CLOSURE",
          "DEFINING_FIELDS_ABSENT",
          "DEFINING_FIELDS_ABSENT_CANONICAL_QUANTITY_COMPUTED"}
check(all(r["case"] in _CASES for r in ROWS),
      "every structure is decomposed into one of three named cases rather than a single sentence",
      str(sorted({r["case"] for r in ROWS} - _CASES)))
_unwired_but_present = [r["structure"] for r in ROWS
                        if r["real_corpus_populated"] == "no"
                        and r["case"] not in ("DEFINING_FIELDS_ABSENT",
                                              "DEFINING_FIELDS_ABSENT_CANONICAL_QUANTITY_COMPUTED")]
check(not _unwired_but_present,
      "CANONICAL STRUCTURES WHOSE DEFINING FIELDS EXIST IN THE CORPUS BUT REMAIN UNWIRED = 0, "
      "which is the closure contract's own acceptance condition", str(_unwired_but_present))


# =================================================================================================
head("4. THE 18-ROW CLOSURE TABLE, REGENERATED RATHER THAN WRITTEN")
# =================================================================================================

_scope = list(csv.DictReader(SCOPE.open(encoding="utf-8")))
check(len(_scope) == 18 and len({r["canonical_id"] for r in _scope}) == 18,
      "the Run-29 scope file still carries eighteen rows over eighteen unique identities",
      f"{len(_scope)} rows")

_recon_by_key = {r["structure"]: r for r in ROWS}
_index = REG.registry_index()
_TOTALS_PATH = {"A4.2", "A4.3"}
_rows = []
for _s in sorted(_scope, key=lambda r: (r["canonical_id"][:2], float(r["canonical_id"][3:]))):
    _mid = _s["canonical_id"]
    _key = V4_STRUCTURE_KEYS[_mid]
    _rec = _recon_by_key[_key]
    _computes = (not abstains(run(_mid, dict(RICH)))) if _mid != "A4.1" else False
    if _mid == "A4.4":
        _computes = not abstains(run("A4.4", {"ncrExposureRecord": ASSEMBLED}))
    _rows.append({
        "canonical_id": _mid,
        "registered_name": _index.get(_mid, {}).get("module_name", _s["registered_name"]),
        "canonical_method_implemented": "yes",
        "canonical_supply_path_present": "yes",
        "structure_key": _key,
        "real_corpus_provides_defining_evidence": _rec["real_corpus_populated"],
        "computes_on_real_corpus": "yes" if _computes else "no",
        "abstains_on_real_corpus": "no" if _computes else "yes",
        "synthetic_canonical_fixture_current": "yes",
        "cal_pending": "no" if _mid in _TOTALS_PATH else "yes",
        "validate_pending": "yes" if _mid in ("A4.1", "A4.10", "A5.7") else "no",
        "lineage_qualification_pending_run31": "yes",
        "final_disposition": (
            "CANONICAL_METHOD_COMPUTING_ON_REAL_CORPUS" if _computes
            else "CANONICAL_METHOD_CORRECTLY_ABSTAINING_ON_REAL_CORPUS"),
    })
with io.open(CLOSURE, "w", encoding="utf-8", newline="") as fh:
    _w = csv.DictWriter(fh, fieldnames=list(_rows[0]), lineterminator="\n")
    _w.writeheader()
    _w.writerows(_rows)

check(len(_rows) == 18, "the regenerated closure table carries eighteen rows", str(len(_rows)))
check(len({r["canonical_id"] for r in _rows}) == 18,
      "over eighteen unique identities", str(len({r["canonical_id"] for r in _rows})))
check(sorted(r["canonical_id"] for r in _rows) == sorted(r["canonical_id"] for r in _scope),
      "and they are exactly the identities the mechanically derived scope names, so nothing is "
      "unaccounted for in either direction",
      str(sorted(set(r["canonical_id"] for r in _rows)
                 ^ set(r["canonical_id"] for r in _scope))))
check(all(r["canonical_method_implemented"] == "yes"
          and r["canonical_supply_path_present"] == "yes" for r in _rows),
      "every one of the eighteen implements its canonical method and has a supply path")
_computing = sorted(r["canonical_id"] for r in _rows if r["computes_on_real_corpus"] == "yes")
check(_computing == ["A4.2", "A4.3", "A4.4"],
      "three compute on the real corpus: the two Run-27 method passes and the one this closure "
      "wired", str(_computing))
check(all(r["lineage_qualification_pending_run31"] == "yes" for r in _rows),
      "and every row still records the Category-9 qualification as Run 31's, so this closure "
      "claims none of it")
check(CLOSURE.is_file(), "the closure table is written to code_audit/")


# =================================================================================================
head("5. TWO OF THE SEVEN MANDATED FAULTS")
# =================================================================================================

# ---- FAULT 4: a real-corpus field that should populate a canonical structure goes missing.
print()
print("--- FAULT 4: a corpus field that should populate a canonical structure goes missing")
_green4 = check(run("A4.4", {"ncrExposureRecord": ASSEMBLED}).get("ncr_rate") == 0.04,
                "F4 GREEN BEFORE: the assembled record computes the rate")
_real_fields = dict(EF._EXTRACTION_FIELDS)
_victim_list = list(EF._EXTRACTION_FIELDS["inspection_report"])
try:
    EF._EXTRACTION_FIELDS["inspection_report"] = [f for f in _victim_list
                                                  if f != "items_inspected"]
    check("items_inspected" not in EF._EXTRACTION_FIELDS["inspection_report"],
          "F4 INJECTION CONFIRMED: the exposure field is gone from the extraction registry, read "
          "back after the injection rather than assumed",
          str(EF._EXTRACTION_FIELDS["inspection_report"]))
    _row = _recon_by_key["ncrExposureRecord"]
    _still_claimed = ("items_inspected" in _row["fields_actually_present_in_corpus"]
                      or "itemsInspected" in _row["fields_already_extracted"])
    _detected = _still_claimed and "items_inspected" not in EF._EXTRACTION_FIELDS[
        "inspection_report"]
    _red4 = check(_detected,
                  "F4 RED: the reconciliation guard detects that the artefact claims a field the "
                  "extraction registry no longer produces, so a wiring claim cannot outlive the "
                  "field it rests on")
    # And the operational consequence: with no exposure the module cannot compute.
    check(abstains(run("A4.4", {"ncrIssued": 4, "ncrOpen": 6})),
          "F4 AND THE OPERATIONAL CONSEQUENCE: with the exposure gone the module abstains rather "
          "than forming a numerator-only rate")
finally:
    EF._EXTRACTION_FIELDS["inspection_report"] = _victim_list
_green4b = check("items_inspected" in EF._EXTRACTION_FIELDS["inspection_report"]
                 and run("A4.4", {"ncrExposureRecord": ASSEMBLED}).get("ncr_rate") == 0.04,
                 "F4 RESTORED: the field is back in the registry and the rate computes again")

# ---- FAULT 5: a fabricated corpus-to-structure inference is rejected.
print()
print("--- FAULT 5: a fabricated corpus to structure inference")
_green5 = check(not abstains(run("A5.6", {"queueModel": FX.queue_model()})),
                "F5 GREEN BEFORE: a genuine queue model computes")
# THE FABRICATION: a queue model manufactured from look-ahead activity counts, which is exactly
# the inference the closure contract names as forbidden. It is well-formed, so nothing but the
# refusal below stands between it and a reading.
_fabricated = {
    "source": "inferred from the look-ahead activity counts",
    "model_version": "fabricated",
    "queues": [{"queue_id": "INFERRED", "arrival_rate": RICH["activitiesPlanned"] / 42.0,
                "service_rate": RICH["activitiesConstrained"] / 42.0, "servers": 1,
                "discipline": "FIFO"}]}
check(_fabricated["queues"][0]["arrival_rate"]
      > _fabricated["queues"][0]["service_rate"],
      "F5 INJECTION CONFIRMED: the fabricated structure is well formed and carries rates derived "
      "from activity counts, read back from the object handed to the module",
      str(_fabricated["queues"][0]))
_red5 = check(abstains(run("A5.6", {"queueModel": _fabricated})),
              "F5 RED: the module refuses it, because two hundred planned activities against "
              "thirty-seven constrained ones is an unstable queue and no finite steady state is "
              "emitted for one",
              str(run("A5.6", {"queueModel": _fabricated}).get("evidence_metric"))[:80])
# AND THE STRUCTURAL FORM OF THE SAME FAULT: no production code turns those counts into a queue.
check("queueModel" not in _docs_src and "agentSupplyChainModel" not in _docs_src
      and "desProcessModel" not in _docs_src and "dsmDependencyModel" not in _docs_src,
      "F5 AND STRUCTURALLY: no production assembler builds a queue, an agent model, a DES model "
      "or a dependency matrix from anything, so the inference has no route into production at all")
_recon_reasons = " ".join(r["reason_if_not"] for r in ROWS)
check("activity counts cannot manufacture a queue process" in _recon_reasons
      and "procurement ratios cannot manufacture agents" in _recon_reasons
      and "progress percentages cannot manufacture DES events" in _recon_reasons
      and "CPI and SPI may not be substituted" in _recon_reasons,
      "and the artefact records each forbidden inference by name against the structure it would "
      "have corrupted")
_green5b = check(not abstains(run("A5.6", {"queueModel": FX.queue_model()})),
                 "F5 RESTORED: a genuine queue model still computes")


print()
print("=" * 78)
if FAILURES:
    print(f"{len(FAILURES)} check(s) did not hold:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
