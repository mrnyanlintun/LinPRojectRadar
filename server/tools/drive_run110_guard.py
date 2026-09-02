"""
RUN 110, ORDER SECTION 2.5, PROVED: A MODULE'S FAULT NO LONGER TAKES DOWN THE COMPUTE ROUTE.

Run 109 measured `models_cat89._route` raising `KeyError: 'C1.5'` on `MODULE_USE[module_id]`.
That exception escaped `run_module`, escaped `registry.run_all`, and 500-ed the whole
`projectcomputeall` route: NO module computed and NO `computed_results` row was stored, so a
single defective module silenced the thirty sound ones beside it.

FOUR MEASUREMENTS, IN ORDER, AND THE SECOND IS THE INJECTION PROVED ABLE TO FAIL:

  1. CONTROL. The real upload route, the real compute route, no fault. The route succeeds and a
     row is stored. This is the baseline the other three are read against.
  2. THE FALSIFICATION. The same fault, reaching `run_module` DIRECTLY -- the unguarded call the
     route used to make. It must RAISE. If it does not, the guard is being credited with
     surviving something that was never dangerous, and this whole section is worthless.
  3. THE GUARD, ON THE REAL HTTP ROUTE. The same fault, through the real `projectcomputeall`
     action. The route must return ok, a row must be stored, the thirty sound modules must all
     be present, and the faulting one must appear as a FAILED READING naming the exception.
  4. THE GUARD IS NOT A BLANKET SWALLOW. A `BaseException` (KeyboardInterrupt) is NOT a module
     fault and must still propagate. A guard that ate one would be hiding the operator's own
     interrupt.

THE FAULT IS INJECTED AT THE MODULE BOUNDARY, not written into a production file: `run_module`
is wrapped so that ONE named module raises. That is exactly the shape of the real C1.5 defect
(an exception raised inside the module's runner, before any result exists) without needing the
C1.5 governed structure, which has no intake path at all -- which is itself the finding Run 109
recorded and this run did not fix.

Run from `server/`:  python tools/drive_run110_guard.py
"""
import base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.CRITICAL)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult
from app.simulation import registry as REG

client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type":"text/plain"})
    return r.status_code, (r.json() if r.headers.get("content-type","").startswith("application/json") else {})
def b64(x): return base64.b64encode(x).decode()

STAMP=str(int(time.time())); ADMIN="r110g-"+STAMP; END="2026-03-31"
# TWO PROJECTS, and the reason matters: `projectcomputeall` does not recompute a project that
# already carries a current `computed_results` row, so injecting the fault and calling it again
# on the SAME project would read back the control's own row and prove nothing. The control and
# the guarded run are therefore two projects built from the identical two documents.
PID_CTL="PRJ-R110GC-"+STAMP; PID_FAULT="PRJ-R110GF-"+STAMP
FAULT = "A1.7"          # a module that BANDS in the control, so its loss is unmistakable
DOCS = [
 ("contract","contract_value",{"original_contract_sum":4_000_000,
    "project_start_date":"2026-01-01","project_end_date":"2027-06-30"}),
 ("pay","pay_application",{"amount_paid_to_date":1_000_000,"completed_to_date":1_000_000,
    "percent_complete_verified":25.0,"application_date":END,"document_date":END}),
]
def raw(t): return f"%PDF-1.4 R110G {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor({hashlib.sha256(raw(t)).hexdigest():(ty,ex) for t,ty,ex in DOCS}))
with S() as s:
    r=s.scalar(select(Participant).where(Participant.role=="ResearchAdmin"))
    if r is None: s.add(Participant(pseudonymous_code="R110G-A-"+STAMP,role="ResearchAdmin",access_token_hash=hash_access_token(ADMIN)))
    else: r.access_token_hash=hash_access_token(ADMIN)
    for pid in (PID_CTL, PID_FAULT):
        if s.scalar(select(Project).where(Project.legacy_id==pid)) is None:
            s.add(Project(legacy_id=pid,doc={"id":pid,"name":"Run 110 guard fixture","sector":"construction","signals":{},"events":[]}))
    s.commit()
admin=post({"action":"researchlogin","access_token":ADMIN})[1]["session_token"]
c=post({"action":"adminparticipantcreate","session_token":admin,"pseudonymous_code":"R110G-PM-"+STAMP,"role":"Participant","account_type":"operational"})[1]
PM=post({"action":"researchlogin","access_token":c["access_token"]})[1]["session_token"]
for pid in (PID_CTL, PID_FAULT):
    post({"action":"adminmemberadd","session_token":admin,"id":pid,"participant_id":c["participant_id"],"project_role":"PM"})
    for t,ty,ex in DOCS:
        post({"action":"projectupload","session_token":PM,"id":pid,"period":1,"period_end":END,
              "documents":[{"filename":t+".pdf","mimeType":"application/pdf","dataBase64":b64(raw(t))}]})

def stored(pid):
    with S() as s:
        p=s.scalar(select(Project).where(Project.legacy_id==pid))
        row=s.scalar(select(ComputedResult).where(ComputedResult.project_id==p.id,
                                                  ComputedResult.superseded_by.is_(None)))
        if row is None: return None
        return ({m.get("module_id"):m for m in (row.module_results or [])},
                {a.get("module_id"):a for a in (row.abstained or [])})

REAL_RUN_MODULE = REG.run_module
class Injected(RuntimeError): pass
def faulting(new_id, si, rand, cutoff):
    if new_id == FAULT:
        raise Injected(f"injected fault in {new_id}")
    return REAL_RUN_MODULE(new_id, si, rand, cutoff)

P=lambda *a: print(*a)
P("="*100); P("RUN 110 SECTION 2.5 -- THE GENERAL GUARD, PROVED"); P("="*100)

# ---------------------------------------------------------------- 1. CONTROL, no fault
st, r = post({"action":"projectcomputeall","session_token":PM,"id":PID_CTL})
base = stored(PID_CTL)
P()
P("1. CONTROL -- real projectcomputeall, no fault injected")
P("   HTTP status                :", st)
P("   route ok                   :", r.get("ok"))
P("   computed_results row stored:", base is not None)
P(f"   {FAULT} state                 :",
  "BANDS "+str(base[0][FAULT].get("status_color")).upper() if base and FAULT in base[0] else "not computed")
P("   modules with any state     :", len(base[0])+len(base[1]) if base else 0)
CONTROL_TOTAL = (len(base[0])+len(base[1])) if base else 0

# ---------------------------------------------------- 2. THE FALSIFICATION: unguarded, raises
P()
P("2. FALSIFICATION -- the SAME fault reaching run_module directly, as the route used to")
try:
    faulting(FAULT, {}, lambda: 0.5, None)
    P("   *** run_module did NOT raise. The injection is not a fault and section 2.5 is unproved.")
    RAISED = False
except Injected as exc:
    P("   run_module raised           :", type(exc).__name__, "-", exc)
    P("   -> unguarded, this is exactly what escaped run_all and 500-ed the route")
    RAISED = True

# ------------------------------- 2b. THE ACTUAL PRE-CHANGE CODE, RUN AGAINST THE SAME FAULT
# Not an argument and not a replica: `app/simulation/registry.py` AS IT STANDS AT THE PARENT
# COMMIT is written out and imported under its own name, and ITS `run_all` is called with the
# same injected fault. If it survives, there was nothing to fix.
P()
P("2b. THE PRE-CHANGE registry.run_all, FROM THE PARENT COMMIT, WITH THE SAME FAULT")
import subprocess, importlib.util, tempfile
# RUN 111 REPAIR. THIS WAS PINNED TO `HEAD` AND HEAD MOVED.
#
# While Run 110's work was uncommitted, `HEAD:server/app/simulation/registry.py` WAS the
# pre-change file and this comparison was sound. The moment Run 110 committed, HEAD began to
# contain the guard, so the falsification step compared the new code against itself, found it
# survived, and printed "SECTION 2.5: NOT PROVED" on every run -- a check that had silently
# stopped being able to fail. It is pinned to the commit the guard was written against
# (`966927b`, Run 109) so that it can fail honestly again.
PRE_CHANGE_COMMIT = "966927b"
prev = subprocess.run(["git", "-C", "/home/user/LinPRojectRadar", "show",
                       PRE_CHANGE_COMMIT + ":server/app/simulation/registry.py"],
                      capture_output=True, text=True)
if prev.returncode != 0:
    P("   could not read the pre-change registry.py at " + PRE_CHANGE_COMMIT + ":", prev.stderr.strip()[:120]); OLD_DIED = None
else:
    # It must live INSIDE the package: it resolves its CSV from `__file__` and imports its
    # siblings relatively. Written, imported, and removed again in the `finally` below, so the
    # tree is exactly as it was before this driver ran.
    tmp = pathlib.Path("/home/user/LinPRojectRadar/server/app/simulation/_registry_at_head.py")
    tmp.write_text(prev.stdout)
    try:
        import importlib
        old_reg = importlib.import_module("app.simulation._registry_at_head")
    finally:
        tmp.unlink(missing_ok=True)
    P("   loaded pre-change registry.py at " + PRE_CHANGE_COMMIT + ", bytes:",
      len(prev.stdout))
    P("   it contains the guard                  :", "guarded(new_id" in prev.stdout)
    old_real = old_reg.run_module
    def old_faulting(new_id, si, rand, cutoff):
        if new_id == FAULT: raise Injected(f"injected fault in {new_id}")
        return old_real(new_id, si, rand, cutoff)
    old_reg.run_module = old_faulting
    try:
        old_reg.run_all({}, "s", "1", None)
        P("   *** the PRE-CHANGE run_all SURVIVED the fault. Nothing needed fixing.")
        OLD_DIED = False
    except Injected as exc:
        P("   the PRE-CHANGE run_all DIED:", type(exc).__name__, "-", exc)
        P("   -> this is the escape that 500-ed projectcomputeall and stored no row at all")
        OLD_DIED = True
    finally:
        old_reg.run_module = old_real

# ---------------------------------------------------- 3. THE GUARD, ON THE REAL HTTP ROUTE
REG.run_module = faulting
try:
    st2, r2 = post({"action":"projectcomputeall","session_token":PM,"id":PID_FAULT})
    after = stored(PID_FAULT)
finally:
    REG.run_module = REAL_RUN_MODULE
P()
P("3. THE GUARD -- the same fault, through the REAL projectcomputeall route")
P("   HTTP status                :", st2)
P("   route ok                   :", r2.get("ok"), "| error:", str(r2.get("error"))[:120] or "none")
P("   computed_results row stored:", after is not None)
if after:
    res, abst = after
    P("   modules with any state     :", len(res)+len(abst), f"(control had {CONTROL_TOTAL})")
    P(f"   {FAULT} in computed results   :", FAULT in res)
    row = abst.get(FAULT)
    P(f"   {FAULT} recorded as a row     :", row is not None)
    if row:
        P("     module_failed            :", row.get("module_failed"))
        P("     module_failure           :", json.dumps(row.get("module_failure")))
        P("     abstention_reason_code   :", row.get("abstention_reason_code"))
        P("     sentence                 :", str(row.get("reason"))[:150])
    others = sorted(set(res) | set(abst) - {FAULT})
    P("   every OTHER module still has a state:", len([m for m in others if m != FAULT]))
    P("   status_color asserted for the failed module:",
      repr((res.get(FAULT) or {}).get("status_color")) if FAULT in res else "no result row at all")

# ---------------------------------------------------- 4. NOT A BLANKET SWALLOW
P()
P("4. THE GUARD IS NOT A BLANKET SWALLOW -- a BaseException still propagates")
def interrupting(new_id, si, rand, cutoff):
    if new_id == FAULT: raise KeyboardInterrupt("operator interrupt")
    return REAL_RUN_MODULE(new_id, si, rand, cutoff)
REG.run_module = interrupting
try:
    REG.run_all({}, "s", "1", None)
    P("   *** KeyboardInterrupt was SWALLOWED. The guard is too wide.")
    PROPAGATED = False
except KeyboardInterrupt:
    P("   KeyboardInterrupt propagated out of run_all, as it must")
    PROPAGATED = True
except Exception as exc:
    P("   propagated as", type(exc).__name__, exc); PROPAGATED = True
finally:
    REG.run_module = REAL_RUN_MODULE

P()
P("="*100)
ok = (OLD_DIED is True and st2 == 200 and r2.get("ok") and after is not None and RAISED and PROPAGATED
      and after and FAULT in after[1] and after[1][FAULT].get("module_failed") is True
      and (len(after[0]) + len(after[1])) == CONTROL_TOTAL)
P("SECTION 2.5:", "PROVED" if ok else "NOT PROVED")
P("="*100)
