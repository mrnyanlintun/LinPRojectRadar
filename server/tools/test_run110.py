"""
RUN 110. THE TWO THINGS THIS RUN BUILT, LOCKED IN, EACH WITH AN INJECTION PROVED ABLE TO FAIL.

SECTION 2.1 -- every extracted value becomes evidence.
SECTION 2.5 -- one module's fault is a failed reading, not a dead compute route.

Every rule here is asserted TWICE: once that it holds, and once that a deliberate violation of
it is DETECTED. A check that cannot fail is not evidence, and a suite of those would let the
next run delete the behaviour and still go green.

Run from `server/`:  python tools/test_run110.py
"""
import json, pathlib, sys
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))

from app import field_registry as FR
from app.extraction_merge import emit_observations, select_signal_inputs
from app.documents import _evidence_qualification
from app.simulation import registry as REG

P = F = 0
def ck(label, got, want):
    global P, F
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
    if ok: P += 1
    else: F += 1

print("=" * 96)
print("RUN 110 -- SECTION 2.1: EVERY EXTRACTED VALUE BECOMES EVIDENCE")
print("=" * 96)

ck("RAW is a declared kind", FR.RAW, "RAW")
ck("RAW is NOT one of the four selection behaviours",
   FR.RAW in {FR.SNAPSHOT, FR.EVENT, FR.DELTA, FR.PERMANENT}, False)
ck("a raw field name is namespaced by document type and label",
   FR.raw_field_name("oac_minutes", "weather_days_approved"),
   "evidence:oac_minutes:weather_days_approved")
ck("is_raw_field recognises one", FR.is_raw_field("evidence:x:y"), True)
ck("is_raw_field rejects a declared field", FR.is_raw_field("bac"), False)

# THE COLLISION GUARANTEE, over the WHOLE declared vocabulary rather than a sample. If any
# signalInputs field could ever equal a raw field name, a raw row could be selected as a real
# one and this entire design is unsafe.
collide = [f for f in FR.ALL_SI_FIELDS if FR.is_raw_field(f) or ":" in f]
ck("no declared signalInputs field can collide with a raw field name", collide, [])

DOC = {"sha256": "a" * 64, "doc_type": "oac_minutes", "filename": "oac.pdf", "document_id": "D1",
       "extraction": {"document_date": "2026-03-31", "outstanding_action_items": 2,
                      "weather_days_claimed": 9, "weather_days_approved": 7,
                      "weather_allowance_days": 10, "weather_time_extension_granted": True}}
rows = emit_observations(DOC)
raw_rows = [o for o in rows if o["kind"] == FR.RAW]
declared = [o for o in rows if o["kind"] != FR.RAW]

ck("one RAW row for every key the extraction returned",
   len(raw_rows), len(DOC["extraction"]))
ck("no extracted key is discarded",
   sorted(o["field"].split(":", 2)[2] for o in raw_rows), sorted(DOC["extraction"]))

wda = next(o for o in raw_rows if o["field"].endswith(":weather_days_approved"))
ck("a RAW row carries WHICH DOCUMENT", (wda["document_id"], wda["sha256"]), ("D1", "a" * 64))
ck("a RAW row carries WHAT THE DOCUMENT CALLED IT",
   wda["field"], "evidence:oac_minutes:weather_days_approved")
ck("a RAW row carries THE VALUE, untouched", wda["value"], 7)
ck("a RAW row carries the document's own date", str(wda["as_of"]), "2026-03-31")
ck("a boolean survives verbatim rather than being coerced",
   next(o for o in raw_rows if o["field"].endswith("granted"))["value"], True)

# 2.1 IS ADDITIVE. The declared emissions must be BYTE-IDENTICAL to what they were, so no
# reading can move because of this. Injection: if the RAW rows were being selected, or if any
# declared emission had been touched, this comparison fails.
si_all = select_signal_inputs(rows)
si_declared_only = select_signal_inputs(declared)
import hashlib
_d = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()[:16]
ck("selection over ALL rows is byte-identical to selection over the declared rows alone",
   _d(si_all), _d(si_declared_only))
ck("no RAW field appears in signalInputs",
   [k for k in si_all if FR.is_raw_field(k)], [])

print()
print("  -- INJECTION: the Category-9 conflict rule must ignore RAW rows AND still be able to fire")
def _obs(field, value, tier, kind):
    return {"field": field, "value": value, "tier": tier, "kind": kind,
            "as_of": "2026-03-31", "doc_type": "d" + str(value)}
# Two documents printing the same COLUMN HEADING with different values is not a contradiction.
raw_pair = [_obs("evidence:ncr_log:report_period", "2026-03", None, FR.RAW),
            _obs("evidence:safety_report:report_period", "2026-02", None, FR.RAW)]
ck("two RAW rows stating different values raise NO material conflict",
   _evidence_qualification(1, raw_pair)["material_conflicts"], [])
# THE SAME SHAPE AS DECLARED FIELDS MUST STILL FIRE. Without this, the check above would pass
# on a rule that had simply stopped working.
declared_pair = [_obs("bac", 4_000_000, 0, FR.SNAPSHOT), _obs("bac", 5_000_000, 0, FR.SNAPSHOT)]
conf = _evidence_qualification(1, declared_pair)["material_conflicts"]
ck("the SAME disagreement between DECLARED fields still raises a conflict",
   [c["field"] for c in conf], ["bac"])

print()
print("=" * 96)
print("RUN 110 -- SECTION 2.5: A MODULE'S FAULT IS A FAILED READING, NOT A DEAD ROUTE")
print("=" * 96)

REAL = REG.run_module
class Injected(RuntimeError): pass
FAULT = "A1.7"

def faulting(new_id, si, rand, cutoff):
    if new_id == FAULT: raise Injected("injected")
    return REAL(new_id, si, rand, cutoff)

REG.run_module = faulting
try:
    out = REG.run_all({}, "scenario", "1", None)
finally:
    REG.run_module = REAL

results = {r["module_id"] for r in out["computed"]}
abst = {a["module_id"]: a for a in out["abstained"]}
ck("run_all did not raise and returned a result set", isinstance(out, dict), True)
ck("the faulting module produced NO computed result", FAULT in results, False)
ck("the faulting module produced a LEDGER ROW", FAULT in abst, True)
ck("the row is marked as a failure, not an absence", abst[FAULT].get("module_failed"), True)
ck("the row names the exception type", abst[FAULT]["module_failure"]["type"], "Injected")
ck("the row carries the stable failure code",
   abst[FAULT].get("abstention_reason_code"), REG.MODULE_FAILED_CODE)
ck("the failure code is its own code, not an evidence-absence code",
   REG.MODULE_FAILED_CODE, "module_execution_failed")
ck("no band is asserted for a failed module",
   [r for r in out["computed"] if r["module_id"] == FAULT], [])
ck("the failure is logged, not silent -- the sentence says the module failed",
   "the module failed" in str(abst[FAULT].get("reason")), True)

control = REG.run_all({}, "scenario", "1", None)
ctl_ids = {r["module_id"] for r in control["computed"]} | {a["module_id"] for a in control["abstained"]}
all_ids = results | set(abst)
ck("every OTHER module still has a state, exactly as with no fault",
   sorted(all_ids - {FAULT}), sorted(ctl_ids - {FAULT}))

# INJECTION PROVED ABLE TO FAIL: a BaseException is not a module fault and must escape.
def interrupting(new_id, si, rand, cutoff):
    if new_id == FAULT: raise KeyboardInterrupt("operator")
    return REAL(new_id, si, rand, cutoff)
REG.run_module = interrupting
try:
    REG.run_all({}, "scenario", "1", None)
    swallowed = True
except KeyboardInterrupt:
    swallowed = False
finally:
    REG.run_module = REAL
ck("a KeyboardInterrupt is NOT swallowed by the guard", swallowed, False)

print()
print("=" * 96)
print(f"RESULT: {P}/{P + F} checks passed")
print("=" * 96)
sys.exit(1 if F else 0)
