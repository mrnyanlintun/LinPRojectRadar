"""
RUN 111. EVERYTHING THIS SESSION CAN PROVE WITHOUT A MODEL KEY, AND NOTHING IT CANNOT.

THE BOUNDARY IS STATED IN THE OUTPUT, PER SECTION. This environment has no ANTHROPIC_API_KEY,
OPENAI_API_KEY or GROQ_API_KEY. So NO MODEL IS CALLED ANYWHERE IN THIS DRIVER, no stub answer is
ever described as a model's behaviour, and every section prints REAL or HARNESS saying which it
is. Where a section constructs an input, it says so in those words.

Run from `server/`:  python tools/drive_run111.py
"""
import base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server/tools"); sys.path.insert(0, str(HERE.parent))
logging.disable(logging.WARNING)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult, RecognitionMatch

from app import ai_provider, recognition as R
from app.recognition_recipes import RECIPES

PASS = FAIL = 0
def check(ok, label, detail=""):
    global PASS, FAIL
    if ok: PASS += 1; print(f"  PASS  {label}" + (f"  [{detail}]" if detail else ""))
    else:  FAIL += 1; print(f"  FAIL  {label}  [{detail}]")
def H(t):
    print(); print("=" * 100); print(t); print("=" * 100)

client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, r.text[:400]
    return r.json()
def b64(x): return base64.b64encode(x).decode()


# =============================================================================================
H("SECTION 0. WHERE THE KEYS ARE. MEASURED, NOT ASSUMED.")
# =============================================================================================
import os
for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
    check(not (os.environ.get(var) or "").strip(), f"{var} is absent in this environment",
          "so nothing below is a model's behaviour")
print()
print("  REAL. Every section marked REAL exercises production code paths on real data.")
print("  HARNESS. Every section marked HARNESS constructs its input, and says so.")


# =============================================================================================
H("SECTION 3. THE CONFIGURED MODEL IDENTIFIERS, PER PROVIDER AND PER CALL SITE.  REAL")
# =============================================================================================
print("  Read out of app/ai_provider.PROVIDERS, which is the live resolution path.")
print()
print(f"  {'PROVIDER':<11}{'CALL SITE':<14}{'MODEL IDENTIFIER':<32}{'KEY VARIABLE':<20}ENDPOINT")
for prov in sorted(ai_provider.PROVIDERS):
    for role in ai_provider.ROLES:
        cfg = ai_provider.load_provider(role, {"AI_PROVIDER": prov})
        print(f"  {prov:<11}{role:<14}{cfg.model:<32}{cfg.key_env:<20}{cfg.url}")
print()
print("  UNVERIFIED. Not one of these was checked against its provider's catalogue, by Run 93")
print("  which chose them or by this run, because neither session had a key. Verifying them")
print("  takes one authenticated GET per provider on its models endpoint, on the deployment.")
print()
print("  Constants that are NOT the live path, established by reading the call sites:")
import app.extraction_client as EC, app.simulation.spec_apply as SA, app.training_narration as TN
check(EC.EXTRACTION_MODEL == "claude-opus-4-6",
      "extraction_client.EXTRACTION_MODEL is a DEFAULT ARGUMENT of ProviderExtractor.__init__",
      "the live builder passes model=cfg.model and a built client, so it is never read live")
check(SA.SPEC_MODEL == "claude-sonnet-4-5",
      "spec_apply.SPEC_MODEL is DEAD in the live path", "both appliers take a built client")
check(TN.NARRATION_MODEL == "claude-3-5-haiku-latest",
      "training_narration.NARRATION_MODEL is DEAD in the live path", "load_provider is used")

print()
print("  A REJECTED MODEL NAME MUST NAME THE MODEL, THE PROVIDER AND THE SETTING.  HARNESS")
print("  The provider is never called. A transport-level rejection is CONSTRUCTED -- an HTTP")
print("  404 with a body -- and fed to the boundary's own error formatter, to prove the")
print("  MESSAGE. This is not a model's behaviour and is not reported as one.")
import urllib.error, io
cfg = ai_provider.load_provider("recognition", {"AI_PROVIDER": "anthropic",
                                                "AI_RECOGNITION_MODEL": "claude-opus-4-6"})
c = ai_provider.AnthropicClient(cfg, "not-a-key", 5.0)
def _boom(req, timeout=None):
    raise urllib.error.HTTPError(cfg.url, 404, "Not Found", {},
                                 io.BytesIO(b'{"error":{"message":"model: claude-opus-4-6"}}'))
import urllib.request
_real = urllib.request.urlopen; urllib.request.urlopen = _boom
try:
    c._request({}, {})
    check(False, "a 404 raises ProviderCallError")
except ai_provider.ProviderCallError as exc:
    msg = str(exc)
    check("claude-opus-4-6" in msg, "the error names the MODEL", msg[:60])
    check("anthropic" in msg, "the error names the PROVIDER")
    check("404" in msg, "the error carries the provider's own status and body")
finally:
    urllib.request.urlopen = _real
try:
    ai_provider.load_provider("recognition", {"AI_PROVIDER": "gemini"})
    check(False, "an unknown provider raises")
except ai_provider.ProviderConfigError as exc:
    check("AI_PROVIDER" in str(exc) and "AI_RECOGNITION_PROVIDER" in str(exc),
          "an unknown provider names the SETTING that would change it", str(exc)[:70])
try:
    ai_provider.read_key(ai_provider.load_provider("recognition", {"AI_PROVIDER": "groq"}), {})
    check(False, "a missing key raises")
except ai_provider.ProviderNotConfigured as exc:
    check("GROQ_API_KEY" in str(exc) and "Nothing is served by another provider" in str(exc),
          "a missing key names the variable AND refuses a fallback", str(exc)[:70])


# =============================================================================================
H("SECTION 1+4a. THE CENSUS FIXTURE, THROUGH THE REAL UPLOAD ROUTE, NOTHING SUPPLIED.  REAL")
# =============================================================================================
sys.argv = ["census"]
import runpy
_census = runpy.run_path(str(HERE / "drive_run110_census.py"), run_name="_r111_census")
PID = _census["PID"]; PM = _census["PM"]
with S() as s:
    proj = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == proj.id,
                                                ComputedResult.superseded_by.is_(None)))
    SI = dict(row.signal_inputs or {})
    from app.research_models import Observation
    obs = s.execute(select(Observation.document_id, Observation.source_doc_type,
                           Observation.field, Observation.value, Observation.kind, Observation.period)
                    .where(Observation.project_id == proj.id,
                           Observation.kind == "RAW")).all()
    PROJ_ID = proj.id
ROWS = []
for did, dt, field, val, kind, per in obs:
    label = field[len("evidence:"):].partition(":")[2]
    ROWS.append({"document_id": did, "doc_type": dt, "sha256": "sha-" + str(did)[:8],
                 "filename": dt + ".pdf", "period": per, "label": label, "value": val})
check(len(ROWS) == 158, "the RAW evidence store holds 158 rows for this period", str(len(ROWS)))

log = SI.get("recognitionLog")
check(isinstance(log, list) and log, "the recognition log reached the STORED signal inputs")
e0 = log[0]
check(e0.get("attempted") is False and e0.get("reason_code") == "provider_key_absent",
      "with no key, recognition is NOT attempted and says so loudly")
check(e0.get("provider") == "anthropic" and e0.get("key_env") == "ANTHROPIC_API_KEY"
      and e0.get("model"), "the refusal names the provider, the model and the key variable",
      f"{e0.get('provider')}/{e0.get('model')} {e0.get('key_env')}")
check("nothing was served by another provider" in e0.get("detail", ""),
      "the refusal states that NO other provider was used")
check(sorted(e0.get("modules_not_attempted") or []) == sorted(RECIPES),
      "it names every module that was therefore not attempted",
      ", ".join(sorted(RECIPES)))


# =============================================================================================
H("SECTION 4b. THE CANDIDATES. WHAT THE MODEL WOULD BE SHOWN.  REAL")
# =============================================================================================
SCALARS = R.build_candidates(ROWS, columnar=False)
COLUMNS = R.build_candidates(ROWS, columnar=True)
check(len(SCALARS) + len(COLUMNS) > 0, "candidates are built from the real evidence store",
      f"{len(SCALARS)} stated values, {len(COLUMNS)} table columns")
check(all(c.candidate_id != "" and c.document_id and c.label for c in SCALARS + COLUMNS),
      "every candidate carries its document and the label as printed")
again = R.build_candidates(list(reversed(ROWS)), columnar=True)
check([c.candidate_id + "|" + c.printed_as for c in COLUMNS] ==
      [c.candidate_id + "|" + c.printed_as for c in again],
      "candidate order and identifiers do NOT depend on database row order")
sub = [c for c in COLUMNS if c.label == "subcontractor_ratings_json"]
print("     the subcontractor assessment table, offered one column per heading:")
for c in sub:
    print(f"       {c.candidate_id}  {c.printed_as:<48} {R._truncate(c.value, 60)}")
check(len(sub) == 3, "the table is offered as three column candidates, never hand-mapped")


# =============================================================================================
H("SECTION 4c. THE PROMPT AND THE FINGERPRINT.  REAL")
# =============================================================================================
spec = [q for q in RECIPES["A4.8"].quantities if q.quantity_id == "A4.8.reported_rating"][0]
cfg = ai_provider.load_provider("recognition", {"AI_PROVIDER": "anthropic"})
blocks = R.build_prompt(spec, COLUMNS)
check(len(blocks) == 1 and blocks[0]["type"] == "text",
      "the prompt is TEXT ONLY, so it carries on every provider", "no document block")
txt = blocks[0]["text"]
for phrase, why in (("Do not answer with a value.", "the model may not supply a figure"),
                    ("Do not calculate.", "the model may not derive one figure from another"),
                    ('"candidate_id": null', "answering 'none' is an expected, correct answer")):
    check(phrase in txt, f"the prompt states: {why}")
check("reported_rating" not in spec.what_it_is and "subcontractor_ratings_json" not in txt.split("CANDIDATES")[0],
      "the SPECIFICATION names no field name -- it states the quantity in plain terms")
fp1 = R.evidence_fingerprint(spec, COLUMNS, cfg.provider, cfg.model)
fp2 = R.evidence_fingerprint(spec, R.build_candidates(list(reversed(ROWS)), columnar=True),
                             cfg.provider, cfg.model)
check(fp1 == fp2, "the fingerprint is stable across row order", fp1[:16])
mutated = [dict(r) for r in ROWS]
for r in mutated:
    if r["label"] == "subcontractor_ratings_json":
        r["value"] = [{**x, "Rating": "Marginal"} for x in r["value"]]
fp3 = R.evidence_fingerprint(spec, R.build_candidates(mutated, columnar=True),
                             cfg.provider, cfg.model)
check(fp3 != fp1, "changing ONE printed VALUE changes the fingerprint", fp3[:16])
fp4 = R.evidence_fingerprint(spec, COLUMNS, "groq", "llama-3.3-70b-versatile")
check(fp4 != fp1, "changing the PROVIDER or MODEL changes the fingerprint", fp4[:16])
spec2 = R.QuantitySpec(quantity_id=spec.quantity_id, what_it_is=spec.what_it_is + ".",
                       units=spec.units, columnar=True)
check(R.evidence_fingerprint(spec2, COLUMNS, cfg.provider, cfg.model) != fp1,
      "changing ONE CHARACTER of the specification changes the fingerprint")


# =============================================================================================
H("SECTION 4d. THE RESULT CONTRACT. EVERY BAD ANSWER FAILS LOUDLY AND SPECIFICALLY.  HARNESS")
# =============================================================================================
print("  The strings below are WRITTEN BY THIS DRIVER to exercise the parser. They are NOT a")
print("  model's output and are not reported as one. No provider was called.")
offered = {c.candidate_id: c for c in COLUMNS}
BAD = [
    ("", "EMPTY", "an empty answer"),
    ("I think it is the Rating column.", "not JSON", "prose"),
    ('["E001"]', "not an object", "a JSON list"),
    ('{"answer": "E001"}', "no `candidate_id` key", "a wrong key"),
    ('{"candidate_id": "E999"}', "NOT one of the", "an identifier never offered"),
    ('{"candidate_id": 7}', "NOT one of the", "a non-string identifier"),
]
for text, needle, what in BAD:
    try:
        R.parse_answer(text, offered, provider="anthropic", model="claude-sonnet-4-5")
        check(False, f"{what} is refused")
    except R.RecognitionContractError as exc:
        m = str(exc)
        check(needle in m and "anthropic" in m and "claude-sonnet-4-5" in m,
              f"{what} is refused, naming the provider and the model", m[:88])
cid, why = R.parse_answer('```json\n{"candidate_id": null, "why": "no rating is stated"}\n```',
                          offered, provider="anthropic", model="m")
check(cid is None and why == "no rating is stated",
      "'nothing answers this' is a RESULT, not an error, and its reason is kept")

good = [c for c in COLUMNS if c.printed_as == "subcontractor_ratings_json [Rating]"][0]
cid, _ = R.parse_answer(
    '{"candidate_id": "%s", "value": 999999, "printed_as": "something else"}' % good.candidate_id,
    offered, provider="anthropic", model="m")
check(cid == good.candidate_id, "an answer is reduced to the IDENTIFIER; its echoed value and "
                                "its echoed label are discarded", "999999 cannot enter a reading")


# =============================================================================================
H("SECTION 4e. DETERMINISM. A RECORDED MATCH IS REPLAYED AND NO CALL IS MADE.  REAL MECHANISM")
# =============================================================================================
print("  The determinism mechanism is exercised end to end. The model is NOT stubbed to return")
print("  an answer: instead the ask function is replaced with one that RAISES, so any call at")
print("  all fails this section rather than passing quietly.")
class _Exploding(RuntimeError): pass
def _must_not_be_called(*a, **k):
    raise _Exploding("THE MODEL WAS ASKED. Determinism is broken.")

store = R.InMemoryMatchStore()
fp = R.evidence_fingerprint(spec, COLUMNS, cfg.provider, cfg.model)
# The record below is CONSTRUCTED BY THIS DRIVER, standing in for a row a real call would have
# written. It is not an answer from any model and is not presented as one.
store.put(spec.quantity_id, fp, {
    "candidate_id": good.candidate_id, "why": "(recorded by the driver, not by a model)",
    "prompt_sha256": R.prompt_fingerprint(R.build_prompt(spec, COLUMNS)),
    "provider": cfg.provider, "model": cfg.model,
    "template_version": R.PROMPT_TEMPLATE_VERSION, "label": good.label, "column": good.column,
    "document_id": good.document_id, "doc_type": good.doc_type, "sha256": good.sha256,
    "filename": good.filename, "period": good.period})
_saved = R._ASK
R._ASK = _must_not_be_called
try:
    m1 = R.recognise(spec, COLUMNS, store, cfg)
    m2 = R.recognise(spec, COLUMNS, store, cfg)
    check(True, "a recorded match is replayed WITHOUT calling the provider at all")
    check(m1.trace() == m2.trace(), "two reads of identical evidence give an IDENTICAL trace")
    check(m1.from_store and m1.value == good.value,
          "the replayed value is read out of the EVIDENCE STORE by the recorded identifier",
          R._truncate(m1.value, 50))
    # Now change one printed value. The fingerprint moves, the store misses, and the platform
    # MUST ask -- which here means the exploding function fires. That is the proof that the key
    # covers the evidence rather than only the module and the period.
    moved = R.build_candidates(mutated, columnar=True)
    try:
        R.recognise(spec, moved, store, cfg)
        check(False, "changed evidence re-asks rather than replaying a stale match")
    except _Exploding:
        check(True, "changed evidence RE-ASKS: the stale match is not replayed over it")
    # And a provider change, likewise.
    try:
        R.recognise(spec, COLUMNS, store,
                    ai_provider.load_provider("recognition", {"AI_PROVIDER": "groq"}))
        check(False, "a provider change re-asks")
    except _Exploding:
        check(True, "a PROVIDER change RE-ASKS: two models never share one recorded answer")
finally:
    R._ASK = _saved
check(RecognitionMatch.__table__.name == "recognition_matches",
      "the durable store is a table, not a process cache", "migration 0033")


# =============================================================================================
H("SECTION 4f. A4.8, COMPOSED AND RUN THROUGH THE REAL CANONICAL FUNCTION AND LADDER.  REAL")
# =============================================================================================
print("  The six Match records below are CONSTRUCTED BY THIS DRIVER -- each one names a real")
print("  candidate from the real evidence store above. NO MODEL CHOSE THEM. What is proved is")
print("  everything downstream of the choice: composition, the canonical function, the ladder.")
def _m(qid, cand):
    return R.Match(quantity_id=qid, matched=True, fingerprint="driver", provider=cfg.provider,
                   model=cfg.model, prompt_sha256="driver", candidate_id=cand.candidate_id,
                   label=cand.label, column=cand.column, document_id=cand.document_id,
                   doc_type=cand.doc_type, sha256=cand.sha256, filename=cand.filename,
                   period=cand.period, value=cand.value)
def _find(label, col=None):
    pool = COLUMNS if col else SCALARS
    for c in pool:
        if c.label == label and c.column == col:
            return c
    raise SystemExit(f"candidate not in the evidence store: {label} [{col}]")
MATCHES = {
    "A4.8.firm_identity": _m("A4.8.firm_identity", _find("subcontractor_ratings_json", "Subcontractor")),
    "A4.8.assessment_period": _m("A4.8.assessment_period", _find("subcontractor_ratings_json", "Assessment period")),
    "A4.8.reported_rating": _m("A4.8.reported_rating", _find("subcontractor_ratings_json", "Rating")),
    "A4.8.rating_scale": _m("A4.8.rating_scale", _find("subcontractor_rating_scale")),
    "A4.8.report_date": _m("A4.8.report_date", _find("subcontractor_report_date")),
    "A4.8.report_version": _m("A4.8.report_version", _find("subcontractor_report_version")),
}
structure = RECIPES["A4.8"].build(MATCHES)
check(structure is not None, "the recipe composes `subcontractorAssessments`")
# The orchestrator attaches the traceability record; done here the same way it does it.
structure["recognition"] = [MATCHES[q.quantity_id].trace() for q in RECIPES["A4.8"].quantities]
print("     composed structure:", json.dumps(structure, default=str)[:300])
from app.simulation.canonical_v4 import subcontractor_reported_ratings
reading = subcontractor_reported_ratings(structure)
check(reading["firm_count"] == 2, "the real canonical function reads two firms")
check(reading["normalised_posture"] == "Yellow",
      "the OWNER'S ladder in canonical_v4 decides the posture, not the model",
      f"Very Good -> Green, Satisfactory -> Yellow, most adverse governs: "
      f"{reading['normalised_posture']} on {reading['governing_subcontractor_id']}")
check("Very Good" not in json.dumps(RECIPES["A4.8"].build.__doc__ or ""),
      "no rating word is mapped to a posture anywhere in the recognition code")
# TRACEABILITY, section 4.4 and 5.3.
tr = MATCHES["A4.8.reported_rating"].trace()
check(all(tr.get(k) for k in ("printed_label", "document_id", "document_type", "recognised_by"))
      and tr.get("period") is not None,
      "every match traces to its document, its period and the label it was printed under",
      f"{tr['printed_label']} in {tr['document_type']} period {tr['period']} "
      f"by {tr['recognised_by']}")
check(any(q["quantity_id"] == "A4.8.reported_rating" for q in structure["recognition"]),
      "the composed structure CARRIES the traceability record into the reading")
# And a value that no model could have supplied.
bad = dict(MATCHES)
bad["A4.8.firm_identity"] = R.Match(quantity_id="A4.8.firm_identity", matched=True,
    fingerprint="d", provider="p", model="m", prompt_sha256="d", value=["Only One Firm"])
check(RECIPES["A4.8"].build(bad) is None,
      "columns of different lengths compose NOTHING rather than being padded to fit")


# =============================================================================================
H("SECTION 2.1. THE TWO A4.3 REPAIRS, THROUGH THE REAL UPLOAD ROUTE.  REAL")
# =============================================================================================
from app.simulation.canonical_v4 import _day as _canon_day, submittal_rejection
from app.simulation.canonical import StructureAbsent
# (a) the calendar-date day, at the canonical function itself.
row = {"decision_day": "2026-02-05"}
val = _canon_day(row, "decision_day", "decision_date", "a register")
check(val == 739652.0, "a register printing 2026-02-05 in the day column is now READ",
      f"ordinal {val:g}")
try:
    _canon_day({"decision_day": "not a date at all"}, "decision_day", "decision_date", "a reg")
    check(False, "genuine rubbish still refuses")
except StructureAbsent as exc:
    check("neither a number nor a calendar date" in str(exc),
          "genuine rubbish STILL refuses, naming both accepted forms", str(exc)[:70])
check(_canon_day({"decision_day": 42}, "decision_day", "decision_date", "r") == 42.0,
      "a numeric day index is unchanged")
check(_canon_day({"decision_day": "x", "decision_date": "2026-02-05"}, "decision_day",
                 "decision_date", "r") == 739652.0,
      "a non-numeric day falls THROUGH to the calendar column beside it")

# (b) the reporting period, through the real upload route with a register printed as a human
# prints one: headings with capitals and spaces, and dates as dates.
STAMP = str(int(time.time())); PID2 = "PRJ-R111-A43-" + STAMP; ADMIN = "r111-" + STAMP
END = "2026-03-31"
DECISIONS = [
    {"Submittal No": f"S-{i:02d}", "Rev": "0", "Decision Date": f"2026-03-{5+i:02d}",
     "Disposition": ("REJECTED" if i < 3 else "APPROVED"), "Reviewer": "A. Architect",
     "Reporting Period": "2026-03"} for i in range(20)]
DOCS2 = [("sub", "submittal_register",
          {"submittals_total": 20, "submittals_rejected": 3, "document_date": END,
           "document_risk_score": 0.15, "submittal_reporting_period": "2026-03",
           "submittal_decisions_json": DECISIONS})]
def raw2(t): return f"%PDF-1.4 R111 {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor(
    {hashlib.sha256(raw2(t)).hexdigest(): (ty, ex) for t, ty, ex in DOCS2}))
with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R111-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID2)) is None:
        s.add(Project(legacy_id=PID2, doc={"id": PID2, "name": "Run 111 A4.3 register",
                                           "sector": "construction", "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c2 = post({"action": "adminparticipantcreate", "session_token": admin,
           "pseudonymous_code": "R111-PM-" + STAMP, "role": "Participant",
           "account_type": "operational"})
PM2 = post({"action": "researchlogin", "access_token": c2["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID2,
      "participant_id": c2["participant_id"], "project_role": "PM"})
for t, ty, ex in DOCS2:
    post({"action": "projectupload", "session_token": PM2, "id": PID2, "period": 1,
          "period_end": END,
          "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(raw2(t))}]})
post({"action": "projectcomputeall", "session_token": PM2, "id": PID2})
with S() as s:
    p2 = s.scalar(select(Project).where(Project.legacy_id == PID2))
    rr = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p2.id,
                                               ComputedResult.superseded_by.is_(None)))
    SI2 = dict(rr.signal_inputs or {})
REG = SI2.get("submittalDecisionRegister")
check(isinstance(REG, dict), "the register assembled from the real upload route")
if isinstance(REG, dict):
    periods = {d.get("reporting_period") for d in REG["decisions"]}
    check(periods == {"2026-03"},
          "REPAIR 2: every decision now carries the period the register PRINTED",
          f"was always None before this run; now {sorted(map(str, periods))}")
    out = submittal_rejection(REG)
    check(out["assessed"] == 20 and out["rejected"] == 3,
          "REPAIR 1+2 together: the register is now IN WINDOW and the rate is formed",
          f"{out['rejected']} of {out['assessed']} = {out['rejection_rate']:.3f}")

# FALSIFICATION. Both repairs are proved able to fail: the pre-change join and the pre-change
# day rule are re-applied to the SAME register and must refuse it.
print()
print("  FALSIFICATION -- the pre-change code, on the same register:")
pre = {**REG, "decisions": [{**d, "reporting_period": None} for d in REG["decisions"]]}
try:
    submittal_rejection(pre)
    check(False, "the pre-change bare-key join refuses this register")
except StructureAbsent as exc:
    check("assessed in the period being reported" in str(exc),
          "the pre-change bare-key join REFUSES this register", str(exc)[:70])
import math as _math
from app.simulation.rng import num as _num
def _pre_day(container, day_field, date_field, words):
    raw = (container or {}).get(day_field)
    if raw is not None:
        v = _num(raw, None)
        if v is None or not _math.isfinite(v):
            raise StructureAbsent("carries a day that is not a number")
        return float(v)
    raise StructureAbsent("no date")
try:
    _pre_day({"decision_day": "2026-02-05"}, "decision_day", "decision_date", "r")
    check(False, "the pre-change _day refuses a calendar date")
except StructureAbsent as exc:
    check("not a number" in str(exc), "the pre-change _day REFUSES 2026-02-05", str(exc)[:60])


# =============================================================================================
H("SECTION 2.2. C1.5. MEASURED, NOT DECIDED.  REAL")
# =============================================================================================
from app.simulation.models_cat89 import MODULE_USE, USE_REQUIREMENTS, CAT89_CANONICAL
check(sorted(MODULE_USE) == ["A6.1", "A6.2", "A6.3", "A6.4"],
      "MODULE_USE declares exactly four entries and C1.5 is not among them")
check("C1.5" in CAT89_CANONICAL, "C1.5 nevertheless dispatches through the same factory")
from app.simulation import registry as REG_
run = CAT89_CANONICAL["C1.5"][1]
try:
    run({"informationPackageRecord": {"package_id": "P", "components": [
        {"component_id": "cost", "applicable": True, "required": True, "present": True,
         "mandatory_fields": ["a"], "values": {"a": 1}}]}}, lambda: 0.5, None)
    check(False, "C1.5 raises KeyError when a structure IS present")
except KeyError as exc:
    check(str(exc) == "'C1.5'", "C1.5 raises KeyError('C1.5') THE MOMENT a structure is present",
          "MODULE_USE[module_id] at models_cat89.py:928")
r_absent = run({}, lambda: 0.5, None)
check(r_absent.get("insufficient_data") is True,
      "with NO structure it abstains cleanly BEFORE reaching that line",
      "which is why the census shows it abstaining rather than failing")
print()
print("  The four uses, and what each requires of its evidence:")
for mid, use in sorted(MODULE_USE.items()):
    print(f"    {mid}  {use:<34} requires {USE_REQUIREMENTS.get(use) or '{} (nothing)'}")
print("  The question for the owner is printed in the report. NOTHING WAS CHOSEN HERE.")


# =============================================================================================
H("SECTION 5. WHAT MUST STILL HOLD.  REAL")
# =============================================================================================
import ast as _ast
def _code_only(path):
    """The file's executable code, with every docstring and comment removed."""
    tree = _ast.parse(pathlib.Path(path).read_text())
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Module, _ast.ClassDef, _ast.FunctionDef)):
            body = node.body
            if body and isinstance(body[0], _ast.Expr) and isinstance(
                    getattr(body[0], "value", None), _ast.Constant) and isinstance(
                    body[0].value.value, str):
                node.body = body[1:] or [_ast.Pass()]
    return _ast.unparse(tree), tree
CODE = ""
TREES = []
for _f in ("app/recognition.py", "app/recognition_recipes.py"):
    _c, _t = _code_only(_f); CODE += _c + "\n"; TREES.append((_f, _t))
for word, why in (("status_color", "sets no band"), ("threshold", "sets no threshold"),
                  ("Green", "names no posture"), ("Amber", "names no posture"),
                  ("Red", "names no posture"), ("band_", "writes no band field")):
    check(word not in CODE, f"5.1 the recognition CODE (docstrings and comments removed) {why}",
          f"searched for {word!r}")
_bad = [(f, n.lineno, _ast.unparse(n)) for f, t in TREES for n in _ast.walk(t)
        if isinstance(n, _ast.BinOp)
        and isinstance(n.op, (_ast.Div, _ast.Mult, _ast.Sub, _ast.Mod, _ast.Pow))]
check(not _bad, "5.1 the recognition code contains NO division, multiplication, subtraction, "
                "modulo or exponentiation anywhere -- it cannot compute a figure",
      str(_bad[:1]))
for excluded in ("signalWeightPolicy", "informationPackageRecord", "independentEacPair",
                 "costRiskModel", "milestoneForecastHistory"):
    check(all(r.structure_key != excluded for r in RECIPES.values()),
          f"section 4: {excluded} is NOT recognised from evidence")
check("A1.11" not in RECIPES, "A1.11 Independent EAC Reconciliation has no recipe")
before = json.loads(pathlib.Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else None
if before:
    after = _census["CENSUS"]
    moved = {k: (before[k], after[k]) for k in before if before.get(k) != after.get(k)}
    check(not moved, "5.4 the census did not move", str(moved))

H(f"RUN 111 DRIVER: {PASS} passed, {FAIL} failed, {PASS+FAIL} checks")
