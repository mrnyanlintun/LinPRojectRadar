"""
The document-extraction model call, and the concurrency around it.

ONE CALL PER UNIQUE DOCUMENT, EVER

Extraction is cached on the sha256 of the bytes (see `documents` in migration 0009), so this
module is only ever reached for a document the platform has genuinely never seen. That is why
it uses the most accurate model available rather than the fastest: a wrong EV figure does not
slow the study down, it corrupts a data point that a participant then judges. The cost of the
strong model is paid once per document for the lifetime of the platform.

WHY urllib AND NOT THE anthropic SDK

`server/requirements.txt` is pinned and the build has already been bitten twice by
interpreter-specific wheels (see the note above `new_ulid` in research_models.py). The API call
is one POST with a JSON body; the SDK would add a dependency and a version surface to a build
that gains nothing from either. `urllib.request` is stdlib and cannot break the Render build.

PER-DOC-TYPE FIELD LISTS, NOT ONE UNIVERSAL LIST

`extraction_fields.extraction_fields_for` returns a short list per document type. Asking a
pay application for all 87 known fields invites the model to fill in plausible values for
fields the document does not contain, and every one of those becomes a fabricated project
controls input. The narrow list is an accuracy measure, not a token-saving one.

PARALLELISM

Sequential extraction of 27 documents at ~5s each is over two minutes; ten concurrent is
roughly fifteen seconds. The work is entirely network-bound, so a thread pool is the right
tool and the GIL is irrelevant. This is in the first implementation rather than a later
optimisation because the sequential version is unusable at a realistic period's document count.

THE STUB

`ANTHROPIC_API_KEY` is set on Render but is not available in local verification. When it is
absent, `StubExtractor` serves recorded extractions keyed by sha256 and refuses anything it has
not been given. It exists so the caching, concurrency, assembly and storage paths can be
exercised deterministically; it is NOT a fallback that silently degrades production. A missing
key in an environment that expects real extraction is an error, not a quiet substitution — see
`build_extractor`.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from .extraction_fields import (
    CLASSIFY_HINTS,
    DOC_TYPES,
    UNMAPPED,
    extraction_fields_for,
    guess_type_from_filename,
    is_mapped,
)

log = logging.getLogger("opus-gubernatio-server")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Accuracy over speed, deliberately. See the module docstring.
EXTRACTION_MODEL = "claude-opus-4-6"

# Ten concurrent calls. Chosen to sit well inside the provider's per-minute limits while still
# collapsing a 27-document period from >2 minutes to well under half a minute.
DEFAULT_CONCURRENCY = 10

MAX_TOKENS = 1536
REQUEST_TIMEOUT_S = 120


class ExtractionError(RuntimeError):
    """Raised when a document could not be extracted. Never swallowed into a null result."""


# --------------------------------------------------------------------------- prompt


def build_prompt(doc_type: str, fields: list[str]) -> str:
    """
    Port of the legacy per-type extraction prompt (.gs `extractSignals_`, lines 846-849).

    Two deliberate additions to the legacy text, both flagged here because they change model
    behaviour:

    1. `document_risk_score` is constrained to 0..1. The legacy prompt never constrained it,
       while `sim.js` clamps it to [0,1] and bands at 0.30/0.70, and `decision.js:80` carries a
       standing comment that the field "carries inconsistent scales — raw counts as well". An
       unconstrained score is silently misread as a band by everything downstream.
    2. An explicit instruction to return null rather than guess. The legacy said "do not invent
       values"; this says what to do instead, which is the part a model actually acts on.
    """
    return (
        "You are a precise construction project-controls data extractor. Read this ONE document "
        f"(type: {doc_type}) and return ONLY these fields as clean JSON: "
        f"{json.dumps(fields)}. "
        "Use null for any field that is not present in the document. Never guess, infer, or "
        "carry a value over from a different field. Do not compute indices. "
        "Numbers as plain numbers (no currency symbols, no thousands separators). "
        "Percentages as numbers 0-100. Dates as YYYY-MM-DD. "
        "document_risk_score, if requested, is a number between 0 and 1 inclusive, where 0 is "
        "no concern and 1 is severe concern; never a count and never a percentage. "
        "Return JSON only, no markdown, no commentary."
    )


def build_classify_prompt() -> str:
    """Port of `identifyOnly_` (.gs ~685), including its content-sniffing hints."""
    return (
        "Classify this construction project document. Return ONLY JSON of the form "
        '{"docType": "...", "confidence": 0.0}. '
        f"docType must be exactly one of {json.dumps(list(DOC_TYPES))}, or the string "
        f'"{UNMAPPED}" if it is none of them. ' + CLASSIFY_HINTS +
        "Do not force a match: if the document is not clearly one of the listed types, return "
        f'"{UNMAPPED}".'
    )


_FENCE = re.compile(r"```(?:json)?", re.IGNORECASE)


def parse_json_response(raw: str) -> dict:
    """
    De-fence and parse. The legacy stripped ``` markers with a regex and called JSON.parse;
    the API is not schema-constrained, so the same defence is still required.
    """
    text = _FENCE.sub("", raw or "").strip()
    if not text:
        raise ExtractionError("model returned an empty response")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # A model that wrapped the object in prose. Take the outermost braces rather than
        # failing the whole document.
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ExtractionError(f"model response was not JSON: {text[:200]!r}") from None
        try:
            parsed = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            raise ExtractionError(f"model response was not JSON: {text[:200]!r}") from None
    if not isinstance(parsed, dict):
        raise ExtractionError(f"model returned {type(parsed).__name__}, expected an object")
    return parsed


# --------------------------------------------------------------------------- real client


class AnthropicExtractor:
    """One HTTPS POST per document. Stateless, so it is safe to share across threads."""

    def __init__(self, api_key: str, model: str = EXTRACTION_MODEL,
                 url: str = ANTHROPIC_URL) -> None:
        self._api_key = api_key
        self.model = model
        self._url = url

    # ``model_id`` is recorded on every document row so a later reader can tell which weights
    # produced a stored figure.
    @property
    def model_id(self) -> str:
        return self.model

    def _post(self, prompt: str, content_block: dict, max_tokens: int) -> str:
        body = json.dumps({
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": [content_block,
                                                      {"type": "text", "text": prompt}]}],
        }).encode("utf-8")
        req = urllib.request.Request(
            self._url, data=body, method="POST",
            headers={
                "content-type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            raise ExtractionError(f"extraction API returned {exc.code}: {detail}") from None
        except urllib.error.URLError as exc:
            raise ExtractionError(f"extraction API unreachable: {exc.reason}") from None
        blocks = payload.get("content") or []
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")

    @staticmethod
    def _content_block(raw: bytes, mime_type: str) -> dict:
        """
        PDFs go as a document block; anything else is decoded as text.

        The legacy split the same way (`claudePdfExtract_` vs `claudeChat_`) and truncated text
        at 12000 characters. That truncation is preserved: it bounds the prompt, and the fields
        being extracted appear in a document's summary tables rather than its appendices.
        """
        if (mime_type or "").lower() == "application/pdf":
            return {
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf",
                           "data": base64.b64encode(raw).decode("ascii")},
            }
        text = raw.decode("utf-8", "replace")[:12000]
        return {"type": "text", "text": "DOCUMENT TEXT:\n" + text}

    def classify(self, raw: bytes, mime_type: str, filename: str) -> str:
        """
        Return a doc_type, or UNMAPPED.

        NEVER inherits confidence from a rejected classification. The legacy did
        (`confidence: parsed.confidence != null ? parsed.confidence : 0.7` at .gs 788), which
        meant a document whose type had just been thrown away still carried the model's
        certainty about that discarded answer. The filename heuristic is consulted only as a
        fallback, and if it too declines, the document is UNMAPPED rather than relabelled.

        THE CONFIDENCE IS NOW KEPT, AND THE RULE ABOVE IS UNCHANGED. The prompt has always
        asked for `{"docType", "confidence"}` and this method has always parsed it and then
        dropped it, so no caller had ever seen it. `classify_with_confidence` returns both, and
        returns confidence ONLY when the model's own claim is the thing that decided the type.
        A filename fallback or an UNMAPPED outcome carries None, which is exactly the
        "rejected classification" case this docstring already refuses to inherit from. This
        method keeps its single-value signature because every existing caller wants a type.
        """
        return self.classify_with_confidence(raw, mime_type, filename)[0]

    def classify_with_confidence(self, raw: bytes, mime_type: str,
                                 filename: str) -> tuple[str, float | None]:
        """(doc_type, confidence). Confidence is None unless the model's own claim was used."""
        block = self._content_block(raw, mime_type)
        try:
            answer = parse_json_response(self._post(build_classify_prompt(), block, 256))
        except ExtractionError:
            guessed = guess_type_from_filename(filename)
            return (guessed if guessed else UNMAPPED), None
        claimed = str(answer.get("docType") or "").strip().lower()
        if is_mapped(claimed):
            raw_confidence = answer.get("confidence")
            try:
                confidence = float(raw_confidence) if raw_confidence is not None else None
            except (TypeError, ValueError):
                # Unreadable is not confident. Same posture as the numeric contract: a value
                # that cannot be read is never silently treated as a good one.
                confidence = None
            if confidence is not None and not 0.0 <= confidence <= 1.0:
                confidence = None
            return claimed, confidence
        guessed = guess_type_from_filename(filename)
        return (guessed if guessed else UNMAPPED), None

    def extract(self, raw: bytes, mime_type: str, filename: str,
                doc_type: str | None = None) -> tuple[str, dict]:
        """Return (doc_type, extracted_fields). Raises ExtractionError on failure."""
        resolved, fields, _confidence = self.extract_with_confidence(
            raw, mime_type, filename, doc_type)
        return resolved, fields

    def extract_with_confidence(self, raw: bytes, mime_type: str, filename: str,
                                doc_type: str | None = None
                                ) -> tuple[str, dict, float | None]:
        """
        Return (doc_type, extracted_fields, classification_confidence).

        Confidence is None when this call did not classify — a caller-supplied type is taken as
        given, and the platform has no opinion about how sure someone else was.
        """
        resolved = (doc_type or "").strip().lower()
        confidence: float | None = None
        if not is_mapped(resolved):
            resolved, confidence = self.classify_with_confidence(raw, mime_type, filename)
        if resolved == UNMAPPED:
            # No field list applies, so there is nothing to ask for. Storing the document with
            # an empty extraction is honest; asking the generic two-field default would produce
            # a docRiskScore for a document type nothing knows how to interpret.
            return UNMAPPED, {}, confidence
        fields = extraction_fields_for(resolved)
        block = self._content_block(raw, mime_type)
        extracted = parse_json_response(self._post(build_prompt(resolved, fields), block,
                                                   MAX_TOKENS))
        # Keep only what was asked for. A model that volunteers extra keys must not be able to
        # widen the stored extraction beyond the type's declared field list.
        return resolved, {k: v for k, v in extracted.items() if k in set(fields)}, confidence


# --------------------------------------------------------------------------- stub


class StubExtractor:
    """
    Serves recorded extractions keyed by sha256, for environments without an API key.

    It REFUSES an unknown hash rather than inventing an extraction. A stub that quietly returns
    empty fields would let a test assert that caching and assembly work while the numbers being
    asserted came from nowhere.
    """

    model_id = "stub/recorded-v1"

    def __init__(self, recorded: dict[str, tuple[str, dict]],
                 delay_s: float = 0.0) -> None:
        self._recorded = dict(recorded)
        # Lets a test demonstrate that N concurrent calls take ~1x rather than ~Nx the
        # single-document time, without waiting on a real network.
        self._delay_s = delay_s
        self.calls: list[str] = []

    def classify(self, raw: bytes, mime_type: str, filename: str) -> str:
        import hashlib
        return self._recorded.get(hashlib.sha256(raw).hexdigest(), (UNMAPPED, {}))[0]

    def extract(self, raw: bytes, mime_type: str, filename: str,
                doc_type: str | None = None) -> tuple[str, dict]:
        rec_type, fields, _confidence = self.extract_with_confidence(
            raw, mime_type, filename, doc_type)
        return rec_type, fields

    def extract_with_confidence(self, raw: bytes, mime_type: str, filename: str,
                                doc_type: str | None = None
                                ) -> tuple[str, dict, float | None]:
        """
        A recording may carry a confidence as a third element. One that does not returns None,
        which is the honest answer: a recording made before confidences were kept never had
        one, and inventing a high value would make every stub-backed check assert filing
        behaviour the real classifier had never demonstrated.
        """
        import hashlib
        sha = hashlib.sha256(raw).hexdigest()
        if self._delay_s:
            time.sleep(self._delay_s)
        self.calls.append(sha)
        if sha not in self._recorded:
            raise ExtractionError(
                f"stub extractor has no recording for sha256 {sha[:12]}…; refusing to invent "
                "an extraction. Record it, or run against the real model."
            )
        recording = self._recorded[sha]
        rec_type, fields = recording[0], recording[1]
        confidence = recording[2] if len(recording) > 2 else None
        return rec_type, dict(fields), confidence


def build_extractor(*, require_real: bool = False,
                    recorded: dict[str, tuple[str, dict]] | None = None,
                    delay_s: float = 0.0):
    """
    Real extractor if ANTHROPIC_API_KEY is set, otherwise the stub.

    `require_real=True` turns a missing key into an error. Production passes it, so a
    misconfigured deployment fails loudly at the first upload instead of silently filling the
    research record with stub output.
    """
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if key:
        return AnthropicExtractor(key)
    if require_real:
        raise ExtractionError(
            "ANTHROPIC_API_KEY is not set. Refusing to extract with the stub in an environment "
            "that requires real extraction."
        )
    return StubExtractor(recorded or {}, delay_s=delay_s)


# --------------------------------------------------------------------------- concurrency


def extract_many(extractor, jobs: list[dict],
                 concurrency: int = DEFAULT_CONCURRENCY) -> list[dict]:
    """
    Extract `jobs` concurrently, preserving input order in the returned list.

    Each job: {"sha256", "content", "mime_type", "filename", "doc_type"}.
    Each result: {"sha256", "ok", "doc_type", "extraction", "error", "confidence",
    "elapsed_s"}.

    A failure is captured per job rather than raised, so one unreadable document in a batch of
    twenty-seven does not discard the twenty-six that extracted cleanly. The caller decides
    what to do with the failures; nothing is silently treated as an empty extraction.

    Order is preserved because the caller reports back to the PM per uploaded file, and a
    reordered result list would attribute one document's outcome to another's filename.
    """
    if not jobs:
        return []
    workers = max(1, min(concurrency, len(jobs)))

    # Imported inside the function, as documents.py does with the simulation package: it keeps
    # the module-level direction client -> fields only, and this is the one call site.
    from .extraction_merge import validate_doc_risk_score, validate_numeric_fields

    def run(job: dict) -> dict:
        started = time.monotonic()
        try:
            # Prefer the confidence-bearing call. An extractor predating it (a caller's own
            # stub in a test, for instance) still works and simply reports no confidence,
            # which `needs_review` treats as reviewable rather than as fine.
            if hasattr(extractor, "extract_with_confidence"):
                doc_type, extraction, confidence = extractor.extract_with_confidence(
                    job["content"], job.get("mime_type") or "", job.get("filename") or "",
                    job.get("doc_type"),
                )
            else:
                doc_type, extraction = extractor.extract(
                    job["content"], job.get("mime_type") or "", job.get("filename") or "",
                    job.get("doc_type"),
                )
                confidence = None
            # THE POINT THE VALUE ENTERS. Refusing here, before the caller writes a Document
            # row, is what makes "no out-of-range value reaches storage" true rather than
            # merely checked later: documents.py only persists results whose ok is True, so a
            # refusal leaves nothing behind to clean up. Raising rather than returning a
            # failure shape is deliberate — the except below already converts any exception
            # into the per-file {ok: False, error} the PM sees in the "Extraction failed"
            # dialog, so the reason reaches the uploader through machinery that exists.
            validate_doc_risk_score((extraction or {}).get("document_risk_score"),
                                    filename=job.get("filename") or None)
            # D2, same boundary, same reasoning. A numeric field that is present but not
            # readable as a number ("TBD" for earned value), or readable but out of contract
            # (a negative count), refuses the WHOLE document here — before the caller writes
            # a Document row — so nothing is half-stored and no observation row can carry a
            # coerced zero. The per-file {ok: False, error} shape delivers the field name and
            # the reason to the uploader through the existing extraction-failure dialog.
            validate_numeric_fields(doc_type, extraction,
                                    filename=job.get("filename") or None)
            return {"sha256": job["sha256"], "ok": True, "doc_type": doc_type,
                    "extraction": extraction, "error": None,
                    "confidence": confidence,
                    "elapsed_s": round(time.monotonic() - started, 3)}
        except Exception as exc:  # noqa: BLE001 — one document must not sink the batch
            log.warning("extraction failed for %s: %s", job.get("filename"), exc)
            return {"sha256": job["sha256"], "ok": False, "doc_type": None,
                    "extraction": None, "error": str(exc), "confidence": None,
                    "elapsed_s": round(time.monotonic() - started, 3)}

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="extract") as pool:
        return list(pool.map(run, jobs))
