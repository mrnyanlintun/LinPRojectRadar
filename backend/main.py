"""
lin-project-radar backend — main.py  (Stage 2, items 20-29)
FastAPI port of the Apps Script (v9) endpoints. Storage is a simple JSON file
for now (Stage 3 → Postgres). All OpenAI calls read OPENAI_API_KEY from the
environment — no keys in source. CORS is open (same as Apps Script).
"""
import base64
import io
import json
import os
import re
import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

import simulations
import rag
from governance import PCEIFGovernanceRouter

load_dotenv()

API_VERSION = "lin-project-radar-backend-v2.1-reset-fullclear"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PROJECTS_PATH = os.path.join(DATA_DIR, "projects.json")
CORPUS_DIR = os.path.join(DATA_DIR, "corpus")

app = FastAPI(title="lin-project-radar backend", version=API_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=False,
)

_lock = threading.Lock()
_router = PCEIFGovernanceRouter()


# ---------------------------------------------------------------- JSON store
def _ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CORPUS_DIR, exist_ok=True)
    if not os.path.exists(PROJECTS_PATH):
        with open(PROJECTS_PATH, "w", encoding="utf-8") as f:
            json.dump({"projects": [], "seq": 0}, f)


def _load():
    _ensure_dirs()
    with open(PROJECTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _store(db):
    tmp = PROJECTS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)
    os.replace(tmp, PROJECTS_PATH)


def _find(db, pid):
    return next((p for p in db["projects"] if p.get("id") == pid), None)


# ---------------------------------------------------------------- security
_PROJECT_ID_RE = re.compile(r"^\d{2}$")


def validate_project_id(pid) -> str:
    """Path-traversal defence.

    Project ids are server-generated as ``str(seq).zfill(2)``, so a valid id
    is always two ASCII digits. Anything else (``..``, ``/etc/passwd``, an
    empty string, ``None``) is rejected with a 400 before it can be joined
    onto a filesystem path. Apply at the top of every route handler that uses
    an id as a path segment.

    Note: when ``seq`` grows past 99 the generator will start producing
    three-digit ids and this validator will reject them, which is the
    intended canary signal to widen the regex.
    """
    s = str(pid) if pid is not None else ""
    if not _PROJECT_ID_RE.match(s):
        raise HTTPException(status_code=400, detail=f"Invalid project id: {pid!r}")
    return s


# ---------------------------------------------------------------- OpenAI
def _openai_client():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception:
        return None


def openai_chat(messages, max_tokens=900, temperature=0.2, image_b64=None, image_mime="application/pdf"):
    """Single chat completion. Returns the text, or None if unconfigured/error."""
    client = _openai_client()
    if client is None:
        return None
    try:
        if image_b64:
            # multimodal fallback — attach the document as an image part
            messages = messages + [{
                "role": "user",
                "content": [{
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                }],
            }]
        resp = client.chat.completions.create(
            model=OPENAI_MODEL, messages=messages,
            max_tokens=max_tokens, temperature=temperature,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return None


# ---------------------------------------------------------------- PDF + prescreen
def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text.strip()
    except Exception:
        return ""


def isolation_forest_prescreen(text: str) -> dict:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 5:
        return {"anomalies": [], "anomaly_count": 0}
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import IsolationForest
        vectorizer = TfidfVectorizer(max_features=100, stop_words="english")
        X = vectorizer.fit_transform(lines).toarray()
        model = IsolationForest(contamination=0.05, random_state=42)
        preds = model.fit_predict(X)
        anomalies = [lines[i] for i, p in enumerate(preds) if p == -1]
        return {"anomalies": anomalies[:5], "anomaly_count": len(anomalies)}
    except Exception:
        return {"anomalies": [], "anomaly_count": 0}


# ---------------------------------------------------------------- helpers
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _regex_money(text, *labels):
    for lab in labels:
        m = re.search(lab + r"[^0-9$]{0,20}\$?\s*([0-9][0-9,]{2,})", text, re.IGNORECASE)
        if m:
            return _num(m.group(1).replace(",", ""))
    return None


def _compute(si: dict) -> dict:
    ev, ac, pv = _num(si.get("ev")), _num(si.get("ac")), _num(si.get("pv"))
    cpi = si.get("cpi")
    spi = si.get("spi")
    if cpi is None and ev and ac:
        cpi = round(ev / ac, 3)
    if spi is None and ev and pv:
        spi = round(ev / pv, 3)
    return {"cpi": cpi, "spi": spi}


EXTRACT_FIELDS = ["bac", "ev", "ac", "pv", "actualPctComplete", "plannedPctComplete", "docRiskScore"]


def extract_signal_inputs(text: str, doc_type: str) -> dict:
    """OpenAI extraction with a regex fallback when the key is absent."""
    sys = ("You extract Earned Value figures from a construction document and return STRICT JSON "
           "with keys bac, ev, ac, pv, actualPctComplete, plannedPctComplete, docRiskScore, "
           "baselineStart, baselineEnd, workPeriodFrom, workPeriodTo. Use null when a value is not present. "
           "Numbers only (no currency symbols). Dates as plain strings.")
    out = openai_chat(
        [{"role": "system", "content": sys},
         {"role": "user", "content": f"Document type: {doc_type}\n\n{text[:12000]}"}],
        max_tokens=500,
    )
    si = {}
    if out:
        try:
            si = json.loads(re.search(r"\{.*\}", out, re.DOTALL).group(0))
        except Exception:
            si = {}
    # regex fallback (also fills gaps the model missed)
    si.setdefault("bac", _regex_money(text, "budget at completion", "contract sum", "contract value", "bac"))
    si.setdefault("ev", _regex_money(text, "earned value", "work completed to date", "ev"))
    si.setdefault("ac", _regex_money(text, "actual cost", "amount paid to date", "paid to date", "ac"))
    si.setdefault("pv", _regex_money(text, "planned value", "scheduled value", "pv"))
    return si


# ================================================================ routes
@app.get("/health")
def health():
    return {"ok": True, "apiVersion": API_VERSION}


@app.get("/list")
def list_projects():
    db = _load()
    return {"ok": True, "projects": [p for p in db["projects"] if not p.get("archived")]}


@app.get("/listarchived")
def list_archived():
    db = _load()
    return {"ok": True, "projects": [p for p in db["projects"] if p.get("archived")]}


@app.get("/get")
def get_project(id: str):
    pid = validate_project_id(id)
    db = _load()
    p = _find(db, pid)
    return {"ok": bool(p), "project": p}


@app.get("/gethistory")
def get_history(id: str):
    pid = validate_project_id(id)
    db = _load()
    p = _find(db, pid)
    return {"ok": bool(p), "history": (p or {}).get("history", [])}


@app.post("/create")
def create_project(body: dict):
    with _lock:
        db = _load()
        db["seq"] = db.get("seq", 0) + 1
        pid = str(db["seq"]).zfill(2)
        sector = body.get("sector", "design")
        prefix = {"design": "SYN-DSN", "construction": "SYN-CON"}.get(sector, "SYN-CMB")
        proj = {
            "id": pid, "code": f"{prefix}-{pid}", "name": body.get("name", "Untitled"),
            "sector": sector, "archived": False, "events": [],
            "createdAt": _now(),
        }
        db["projects"].append(proj)
        _store(db)
        return {"ok": True, "project": proj}


@app.post("/save")
def save_project(body: dict):
    incoming = body.get("project") or body
    pid = validate_project_id(incoming.get("id"))
    with _lock:
        db = _load()
        p = _find(db, pid)
        if p is None:
            db["projects"].append(incoming)
            saved = incoming
        else:
            p.update(incoming)
            saved = p
        _store(db)
        return {"ok": True, "project": saved}


@app.post("/archive")
def archive_project(body: dict):
    return _set_archived(validate_project_id(body.get("id")), True)


@app.post("/restore")
def restore_project(body: dict):
    return _set_archived(validate_project_id(body.get("id")), False)


def _set_archived(pid, flag):
    with _lock:
        db = _load()
        p = _find(db, pid)
        if p:
            p["archived"] = flag
            _store(db)
        return {"ok": bool(p), "project": p}


@app.post("/chat")
def chat(body: dict):
    q = body.get("question", "")
    # Honour a client-supplied max_tokens (the executive brief asks for 1200 to
    # fit its 4-section format), clamped to a sane range; default stays at 400.
    try:
        mt = int(body.get("max_tokens") or 400)
    except (TypeError, ValueError):
        mt = 400
    mt = max(200, min(2000, mt))
    answer = openai_chat(
        [{"role": "system", "content": "You are Lin, a concise governance/PM assistant for a synthetic AEC demo."},
         {"role": "user", "content": q}],
        max_tokens=mt,
    )
    if answer is None:
        answer = "AI is not configured on this backend (set OPENAI_API_KEY)."
    # optional governance synthesis when a signal_array is supplied
    out = {"ok": True, "answer": answer}
    if isinstance(body.get("signal_array"), list):
        out["governance"] = _router.synthesize(body["signal_array"], body.get("human_override"))
    return out


@app.post("/analyze")
def analyze(body: dict):
    text = body.get("text", "")
    spec = body.get("spec")
    prompt = "Summarize the document risk in 3-4 sentences."
    if spec:
        prompt += " Then compare against the spec excerpt and label CONFLICT, GAP, or CONSISTENT."
    analysis = openai_chat(
        [{"role": "system", "content": prompt},
         {"role": "user", "content": (text or "")[:8000] + (f"\n\nSPEC:\n{spec[:3000]}" if spec else "")}],
        max_tokens=400,
    )
    return {"ok": True, "analysis": analysis or "AI not configured."}


@app.post("/extractsignals")
def extractsignals(body: dict):
    # /extractsignals does not currently persist by id, but we still validate
    # to fail closed and keep the contract uniform across project routes.
    if body.get("id") is not None:
        validate_project_id(body.get("id"))
    doc_type = body.get("docType", "")
    text = body.get("text")
    data_b64 = body.get("dataBase64")
    mime = body.get("mimeType", "")

    file_bytes = None
    if data_b64:
        try:
            file_bytes = base64.b64decode(data_b64)
        except Exception:
            file_bytes = None

    multimodal_b64 = None
    # Item 21 — pypdf text path with multimodal fallback for scanned PDFs
    if not text and file_bytes and mime == "application/pdf":
        text = extract_pdf_text(file_bytes)
        if not text or len(text) < 200:
            text = None
            multimodal_b64 = data_b64  # scanned/image-only → OpenAI vision

    text = text or ""

    # Item 22 — Isolation Forest pre-screen on longer docs
    prescreen = isolation_forest_prescreen(text) if len(text) > 500 else {"anomalies": [], "anomaly_count": 0}

    si = extract_signal_inputs(text, doc_type) if (text or multimodal_b64) else {}
    if multimodal_b64 and not any(si.get(k) for k in EXTRACT_FIELDS):
        # ask the vision model directly
        out = openai_chat(
            [{"role": "system", "content": "Extract EVM figures as STRICT JSON (bac, ev, ac, pv, "
              "actualPctComplete, plannedPctComplete, docRiskScore). Numbers only; null when absent."}],
            image_b64=multimodal_b64, image_mime=mime, max_tokens=400,
        )
        if out:
            try:
                si.update(json.loads(re.search(r"\{.*\}", out, re.DOTALL).group(0)))
            except Exception:
                pass

    computed = _compute(si)
    missing = []
    for key, label, doc in [
        ("ev", "EV (earned value)", "Pay Application"),
        ("ac", "AC (actual cost)", "Pay Application"),
        ("pv", "PV (planned value)", "Time-phased Schedule"),
    ]:
        if not _num(si.get(key)):
            missing.append({"field": label, "note": f"Upload {doc}"})

    ready = computed.get("cpi") is not None or computed.get("spi") is not None
    applied = [k for k in EXTRACT_FIELDS if si.get(k) is not None]

    return {
        "ok": True,
        "signalInputs": si,
        "computed": computed,
        "missing": missing,
        "applied": applied,
        "readyToRun": ready,
        "anomaly_count": prescreen["anomaly_count"],
        "anomalies": prescreen["anomalies"],
    }


@app.post("/overwritesignal")
def overwritesignal(body: dict):
    pid = validate_project_id(body.get("id"))
    with _lock:
        db = _load()
        p = _find(db, pid)
        field, value = body.get("field"), body.get("value")
        si = (p.get("signalInputs") if p else None) or {}
        old = si.get(field)
        si[field] = value
        sources = si.setdefault("sources", {})
        if not isinstance(sources.get(field), list):
            sources[field] = [sources[field]] if sources.get(field) else []
        sources[field].append({
            "value": _num(value),
            "docType": "manual_override",
            "fileName": None,
            "at": _now(),
            "reason": body.get("reason") or "Manual override by PM",
        })
        if p is not None:
            p["signalInputs"] = si
            p.setdefault("events", []).append({
                "type": "signal_overwritten", "field": field, "from": old, "to": value,
                "reason": body.get("reason"), "at": _now(),
            })
            _store(db)
        return {"ok": True, "signalInputs": si, "computed": _compute(si),
                "readyToRun": _compute(si).get("cpi") is not None or _compute(si).get("spi") is not None}


@app.post("/resetsignals")
def resetsignals(body: dict):
    pid = validate_project_id(body.get("id"))
    with _lock:
        db = _load()
        p = _find(db, pid)
        if p:
            # Fully clear ALL ingested signal data so the project returns to a true
            # "Awaiting ingest" state — re-uploaded docs must not stack on stale
            # data. Leaving history/events behind was the root cause of phantom
            # CUSUM breaches (stale multi-period SPI series) and a docs table that
            # kept showing prior uploads.
            for k in ("signals", "signalInputs", "simulationSignals"):
                p.pop(k, None)
            p["history"] = []   # feeds CUSUM's multi-period SPI series
            p["events"] = []    # signals_extracted (backs the Uploaded Documents table) + overwrite log
            for k in ("documents", "uploadedDocuments", "docs"):
                if k in p:
                    p[k] = []
            # NOTE: do NOT touch `corpus` — that is the Technical Auditor's reference
            # store, unrelated to signal ingest.
            p["status"] = None
            p["reportingPeriod"] = None
            p["derivedState"] = None
            _store(db)
        return {"ok": bool(p), "id": pid, "reset": bool(p), "project": p}


@app.post("/simulate")
def simulate(body: dict):
    return {"ok": True, "signals": simulations.run_all(body.get("signalInputs", {}))}


@app.post("/tts")
def tts(body: dict):
    # Placeholder — Stage 2 demo keeps TTS client-side. Returns a no-op contract.
    return {"ok": True, "audio": None, "note": "TTS not enabled on this backend tier."}


@app.post("/ingestcorpus")
def ingestcorpus(body: dict):
    pid = validate_project_id(body.get("id"))
    name = body.get("name", "corpus.pdf")
    doc_type = body.get("docType", "")
    sections = body.get("masterFormatSections") or []
    db_dir = os.path.join(CORPUS_DIR, pid)
    os.makedirs(db_dir, exist_ok=True)

    file_bytes = None
    if body.get("dataBase64"):
        try:
            file_bytes = base64.b64decode(body["dataBase64"])
        except Exception:
            file_bytes = None

    # Item 23 — build/merge requirements_db.json per project
    if file_bytes:
        new_db = rag.build_requirements_db(file_bytes, doc_type)
        if not sections:
            sections = rag.detect_sections(extract_pdf_text(file_bytes))
        req_path = os.path.join(db_dir, "requirements_db.json")
        existing = {}
        if os.path.exists(req_path):
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        for sec, chunks in new_db.items():
            existing.setdefault(sec, []).extend(chunks)
        with open(req_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

    file_id = f"f{int(time.time() * 1000)}"
    meta = {"fileId": file_id, "name": name, "docType": doc_type,
            "createdAt": _now(), "masterFormatSections": sections}
    # record in a per-project corpus index
    idx_path = os.path.join(db_dir, "corpus_index.json")
    idx = []
    if os.path.exists(idx_path):
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                idx = json.load(f)
        except Exception:
            idx = []
    idx.append(meta)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)

    return {"ok": True, "file": meta, "masterFormatSections": sections}


@app.get("/listcorpus")
def listcorpus(id: str):
    pid = validate_project_id(id)
    idx_path = os.path.join(CORPUS_DIR, pid, "corpus_index.json")
    if not os.path.exists(idx_path):
        return {"ok": True, "corpus": []}
    with open(idx_path, "r", encoding="utf-8") as f:
        return {"ok": True, "corpus": json.load(f)}


@app.post("/audit")
def audit(body: dict):
    pid = validate_project_id(body.get("id"))
    review_type = body.get("reviewType", "material_submittal")
    submission_b64 = body.get("submissionBase64")

    submittal_text = ""
    if submission_b64:
        try:
            submittal_text = extract_pdf_text(base64.b64decode(submission_b64))
        except Exception:
            submittal_text = ""

    # Item 23 — retrieve relevant corpus chunks
    req_path = os.path.join(CORPUS_DIR, pid, "requirements_db.json")
    context = ""
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8") as f:
                context = rag.retrieve_relevant_chunks(json.load(f), submittal_text)
        except Exception:
            context = ""

    sys = ("You are a technical reviewer. Audit the submission against the reference spec excerpts. "
           "Return STRICT JSON: {items:[{item, remark, citation, status}], summary:{total, approved, "
           "approvedAsNoted, rejected, remarks}}. Each citation MUST read "
           "'SECTION NN NN NN, p.<page>, ¶<paragraph>' using the reference sections; omit unknown parts. "
           "status is one of Approved, Approved as Noted, Rejected, Remark.")
    out = openai_chat(
        [{"role": "system", "content": sys},
         {"role": "user", "content": f"Review type: {review_type}\n\nSUBMISSION:\n{submittal_text[:6000]}\n\nREFERENCES:\n{context[:6000]}"}],
        max_tokens=1200,
    )
    result = {"items": [], "summary": {"total": 0}}
    if out:
        try:
            result = json.loads(re.search(r"\{.*\}", out, re.DOTALL).group(0))
        except Exception:
            pass
    result["ok"] = True
    return result


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
