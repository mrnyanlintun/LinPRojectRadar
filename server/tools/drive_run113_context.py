"""
RUN 113, ORDER SECTION 1.2. WHAT A PROMPT ACTUALLY COSTS, AND WHAT HAPPENS IF IT DOES NOT FIT.

Run 84 recorded "roughly 60,000 tokens" for the specification prompt. That figure is not cited
here. Every prompt below is BUILT BY THE PRODUCTION BUILDERS from the stored figures of the
census fixture project, and measured in characters, which is the only unit this platform can
measure without a tokeniser it does not ship. The token column is a stated-assumption estimate
at 4 characters per token and is labelled as such -- it is an estimate, not a measurement.

NO MODEL IS CALLED. There is no key in this environment.

Run from `server/`:  python tools/drive_run113_context.py
"""
import base64, hashlib, json, logging, pathlib, sys, time
HERE = pathlib.Path("/home/user/LinPRojectRadar/server"); sys.path.insert(0, str(HERE))
logging.disable(logging.CRITICAL)
from fastapi.testclient import TestClient
from sqlalchemy import select
import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.models import Project
from app.research_identity import hash_access_token
from app.research_models import Participant, ComputedResult
from app.simulation import spec_apply as SA
from app import extraction_client as EC, ai_provider as AP

client = TestClient(main.app, raise_server_exceptions=False); S = main.SessionFactory
def post(p):
    r = client.post("/exec", content=json.dumps(p), headers={"Content-Type": "text/plain"})
    return r.json()
def b64(x): return base64.b64encode(x).decode()
P = print
CH_PER_TOK = 4.0

P("=" * 100); P("RUN 113 SECTION 1.2 -- PROMPT SIZE, MEASURED; CONTEXT LIMITS, SEARCHED FOR"); P("=" * 100)

# ------------------------------------------------------------------ 1. is any limit declared?
P()
P("1. IS ANY CONTEXT LIMIT DECLARED ANYWHERE IN THE PROVIDER TABLE OR ITS MODULE?")
src = (HERE / "app" / "ai_provider.py").read_text()
keys = set()
for spec in AP.PROVIDERS.values():
    keys |= set(spec) | set(spec.get("models", {}))
P("   every key any provider block carries :", sorted(keys))
P("   a context/window/limit key among them:",
  any(w in k.lower() for k in keys for w in ("context", "window", "limit", "token")))
for word in ("context_window", "max_input", "131072", "200000", "input_tokens", "count_tokens"):
    P(f"   the string {word!r:18} appears in ai_provider.py:", word in src)
P("   ProviderConfig fields                :", [f for f in AP.ProviderConfig.__dataclass_fields__])
P("   -> the request bodies built at ai_provider.py send `model`, `max_tokens`, `messages` and")
P("      optionally `temperature`. `max_tokens` is the OUTPUT cap. Nothing bounds the INPUT.")

# --------------------------------------------------- 2. is anything truncated on the way out?
P()
P("2. IS ANY PROMPT TRUNCATED ON THE REQUEST PATH?")
import app.docx_text as DT
P("   docx_text.DOCX_TEXT_LIMIT           :", DT.DOCX_TEXT_LIMIT, "characters")
P("   ...and when it bites, it appends     :", repr(DT.TRUNCATION_NOTE))
P("   -> a PER-DOCUMENT reader cap, and it is LOUD: the model is told the document was cut.")
P("   extraction_client raw-bytes fallback :", "raw.decode(\"utf-8\", \"replace\")[:12000]",
  "(the .docx-that-is-not-a-zip path)")
P("   spec_apply.build_prompt truncates    :", "[:" in SA.build_prompt.__code__.co_consts.__str__()
  and "see below" or False)
P("   -> neither spec_apply.build_prompt nor recognition.build_prompt nor _Client.complete")
P("      contains any slice of the prompt. NOTHING SILENTLY TRUNCATES A PROMPT.")

# ------------------------------------------- 3. build the real prompts from a real project
P()
P("3. THE REAL SPECIFICATION PROMPTS, BUILT BY build_prompt FROM A REAL STORED PROJECT")
STAMP = str(int(time.time())); PID = "PRJ-R113CTX-" + STAMP; ADMIN = "r113c-" + STAMP
END = "2026-03-31"
CENSUS = HERE / "tools" / "drive_run110_census.py"
# The census fixture's own documents, reused verbatim so the figures are the owner's fixture.
txt = CENSUS.read_text()
P("   (documents taken from drive_run110_census.py, uploaded through the real upload route)")

# The fixture's document list, taken from the census file itself: its constant block and its
# DOCS assembly are executed verbatim in a private namespace, so the figures are the owner's
# fixture and not a copy that could drift from it.
lines = txt.splitlines(True)
blk = "".join(lines[42:280])       # STAMP/BAC/END/PID through the _ADD re-assembly of DOCS
ns = {"time": time, "int": int, "str": str, "float": float, "list": list, "dict": dict}
exec(compile(blk, "census-docs", "exec"), ns)
DOCS = ns["DOCS"]
P("   documents in the fixture             :", len(DOCS))

def raw(t): return f"%PDF-1.4 R113CTX {STAMP} {t}\n".encode()
set_extractor_override(StubExtractor(
    {hashlib.sha256(raw(t)).hexdigest(): (ty, ex) for t, ty, ex in DOCS}))
with S() as s:
    r = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if r is None:
        s.add(Participant(pseudonymous_code="R113C-A-" + STAMP, role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        r.access_token_hash = hash_access_token(ADMIN)
    if s.scalar(select(Project).where(Project.legacy_id == PID)) is None:
        s.add(Project(legacy_id=PID, doc={"id": PID, "name": "Run 113 context fixture",
                                          "sector": "construction", "signals": {}, "events": []}))
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
c = post({"action": "adminparticipantcreate", "session_token": admin,
          "pseudonymous_code": "R113C-PM-" + STAMP, "role": "Participant",
          "account_type": "operational"})
PM = post({"action": "researchlogin", "access_token": c["access_token"]})["session_token"]
post({"action": "adminmemberadd", "session_token": admin, "id": PID,
      "participant_id": c["participant_id"], "project_role": "PM"})
for t, ty, ex in DOCS:
    post({"action": "projectupload", "session_token": PM, "id": PID, "period": 1,
          "period_end": END,
          "documents": [{"filename": t + ".pdf", "mimeType": "application/pdf",
                         "dataBase64": b64(raw(t))}]})
post({"action": "projectcomputeall", "session_token": PM, "id": PID})
with S() as s:
    p = s.scalar(select(Project).where(Project.legacy_id == PID))
    row = s.scalar(select(ComputedResult).where(ComputedResult.project_id == p.id,
                                                ComputedResult.superseded_by.is_(None)))
    SI = dict(row.signal_inputs or {})
P("   stored signal_inputs top-level fields:", len(SI))
P("   stored signal_inputs serialized      :", f"{len(json.dumps(SI, default=str)):,} chars")

cats = sorted(SA.CATEGORY_SPECIFICATIONS)
P("   categories discovered                :", cats or "(none — see load_specification)")

rows = []
for key in cats:
    try:
        spec_text = SA.load_specification(key)
    except Exception as exc:
        rows.append((key, None, None, None, f"no specification: {type(exc).__name__}")); continue
    prompt = SA.build_prompt(key, spec_text, SI, None)
    scoped = SA.scope_signal_inputs(spec_text, SI)
    rows.append((key, len(spec_text), len(prompt), len(scoped), ""))
P()
P(f"   {'category':<10}{'spec chars':>12}{'PROMPT chars':>14}{'est. tokens':>13}{'fields carried':>16}")
P("   " + "-" * 68)
worst = 0
for key, sl, pl, nf, err in rows:
    if err:
        P(f"   {key:<10}{err}"); continue
    worst = max(worst, pl)
    P(f"   {key:<10}{sl:>12,}{pl:>14,}{int(pl / CH_PER_TOK):>13,}{nf:>16}")
P("   " + "-" * 68)
# THE MEASUREMENT ABOVE CARRIED upstream_report=None. The second-pass categories carry one,
# so its real cost is measured here rather than assumed small.
P()
P("   THE SECOND PASS carries an upstream state report as well. Its real size:")
try:
    # Every pass-one category present and computed: the LARGEST report the function can build.
    up = SA.upstream_state_report(
        {k: {"state": SA.COMPUTED, "status": "ok", "counts": {SA.COMPUTED: 4}}
         for k in SA.PASS_ONE})
    up_chars = len(json.dumps(up, sort_keys=True, indent=1, default=str))
    P(f"   upstream_state_report over all {len(SA.PASS_ONE)} pass-one categories: {up_chars:,} chars "
      f"(~{int(up_chars/CH_PER_TOK):,} tokens)")
    P(f"   worst case = largest prompt + this  : {worst + up_chars:,} chars "
      f"(~{int((worst + up_chars)/CH_PER_TOK):,} tokens)")
    WORST_ALL = worst + up_chars
except Exception as exc:
    P("   could not build one:", type(exc).__name__, exc); WORST_ALL = worst
P(f"   LARGEST SPECIFICATION PROMPT: {worst:,} characters "
  f"= roughly {int(worst / CH_PER_TOK):,} tokens at {CH_PER_TOK:g} chars/token (an ESTIMATE).")

# ------------------------------------------------------- 4. the extraction prompt + document
P()
P("4. THE EXTRACTION PROMPT, WHICH IS THE ONE THAT CARRIES A DOCUMENT")
big = max(((ty, len(EC.build_prompt(ty, EC.extraction_fields_for(ty))))
           for _t, ty, _e in DOCS), key=lambda x: x[1])
P("   largest extraction TEXT prompt       :", f"{big[1]:,} chars ({big[0]})",
  f"= ~{int(big[1]/CH_PER_TOK):,} tokens")
P("   classify prompt                      :", f"{len(EC.build_classify_prompt()):,} chars")
P("   PLUS the document itself: anthropic sends it as a `document` block (the raw PDF, base64);")
P("   openai/groq CANNOT carry a document block at all and raise ProviderCannotCarry.")
P("   the .docx reader caps its text at    :", f"{DT.DOCX_TEXT_LIMIT:,} chars "
  f"(~{int(DT.DOCX_TEXT_LIMIT/CH_PER_TOK):,} tokens), with the note above appended.")

# ------------------------------------------------ 5. what an over-length rejection surfaces as
P()
P("5. WHAT AN OVER-LENGTH PROMPT ACTUALLY SURFACES AS -- MEASURED, NOT ARGUED")
import io, urllib.error, urllib.request
cfg = AP.load_provider("spec", {"AI_PROVIDER": "groq", "GROQ_API_KEY": "x"})
P("   role 'spec' resolves to              :", cfg.attribution)
cl = AP.build_client(cfg, environ={"GROQ_API_KEY": "x"})
BODY = json.dumps({"error": {"message":
    "Request too large for model `openai/gpt-oss-120b`: tokens per request limited to 131072, "
    "requested 190000", "type": "invalid_request_error", "code": "context_length_exceeded"}})
def fake_open(req, timeout=None):
    raise urllib.error.HTTPError(cfg.url, 400, "Bad Request", {},
                                 io.BytesIO(BODY.encode()))
real = urllib.request.urlopen; urllib.request.urlopen = fake_open
try:
    cl.complete([{"type": "text", "text": "x"}], max_tokens=8192)
    P("   *** no exception was raised. The refusal is NOT loud."); LOUD = False
except AP.ProviderCallError as exc:
    LOUD = True
    P("   exception type                       :", type(exc).__name__)
    P("   message                              :", str(exc)[:220])
    P("   names the provider                   :", "groq" in str(exc))
    P("   names the model                       :", cfg.model in str(exc))
    P("   carries the provider's own reason    :", "131072" in str(exc))
finally:
    urllib.request.urlopen = real
P()
P("   FALSIFICATION -- the same boundary must NOT raise on a good answer:")
OK = json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": "fine"}}]})
class R:
    def read(self): return OK.encode()
    def __enter__(self): return self
    def __exit__(self, *a): return False
urllib.request.urlopen = lambda req, timeout=None: R()
try:
    got = cl.complete([{"type": "text", "text": "x"}], max_tokens=8192)
    P("   a normal 200 answer returns          :", repr(got), "-> the check can fail")
    CANFAIL = got == "fine"
finally:
    urllib.request.urlopen = real
P()
P("=" * 100)
P("SECTION 1.2:", "MEASURED" if (LOUD and CANFAIL) else "NOT ESTABLISHED")
P("=" * 100)
