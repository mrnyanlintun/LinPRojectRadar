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


class TruncatedResponseError(ExtractionError):
    """
    The model's answer was CUT OFF, not malformed. These are different failures and the
    difference is actionable.

    A real schedule document failed three times with `model response was not JSON: '{\\n
    "planned_percent_complete": null, ... "activities_planned": 29,\\n "activities_constrain'`.
    That response is valid JSON, truncated mid-key. "Not JSON" describes a model that answered
    with prose or with something else entirely, and the honest response to that is to look at
    what it said; the honest response to a cut-off answer is to ask for less, because retrying
    truncates in exactly the same place every time. Three retries were spent on the wrong one.
    """


def describe_json_truncation(text: str) -> str | None:
    """
    `None` if `text` is a complete JSON value; otherwise a sentence NAMING WHERE IT STOPPED.

    Scans once, tracking string state, escapes and bracket depth, and remembering the most
    recent object key. Unterminated structure at the end means the text ran out before the value
    did, which is truncation and not a syntax error.

    Reporting the key matters more than reporting the offset. "It stopped while reading
    activities_constrained" tells a reader which field ran the response out of budget; "invalid
    JSON at character 412" tells them nothing they can act on.
    """
    depth = 0
    in_string = False
    escaped = False
    current: list[str] = []
    last_string: str | None = None
    last_key: str | None = None
    expecting_key = False
    saw_value = False
    for ch in text or "":
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
                last_string = "".join(current)
                if expecting_key:
                    last_key = last_string
            else:
                current.append(ch)
            continue
        if ch == '"':
            in_string, current = True, []
            continue
        if ch in "{[":
            depth += 1
            expecting_key = ch == "{"
            saw_value = True
            continue
        if ch in "}]":
            depth -= 1
            expecting_key = False
            continue
        if ch == ":":
            expecting_key = False
            continue
        if ch == ",":
            expecting_key = depth > 0
            continue
        if not ch.isspace():
            saw_value = True
    if not saw_value:
        return None
    if in_string:
        partial = "".join(current)
        if expecting_key:
            return (
                "the model's answer was cut off while writing a field name, after "
                f"{last_key!r}; the name it had reached was {partial!r}"
                if last_key else
                f"the model's answer was cut off while writing a field name, {partial!r}"
            )
        target = last_key or last_string
        return (
            f"the model's answer was cut off while writing the value of {target!r}"
            if target else "the model's answer was cut off inside a quoted value"
        )
    if depth > 0:
        return (
            f"the model's answer was cut off after the field {last_key!r}"
            if last_key else "the model's answer was cut off before the object was closed"
        )
    return None


# --------------------------------------------------------------------------- prompt


def build_prompt(doc_type: str, fields: list[str]) -> str:
    """
    Port of the legacy per-type extraction prompt (.gs `extractSignals_`, lines 846-849).

    Three deliberate additions to the legacy text, each flagged here because it changes model
    behaviour:

    1. `document_risk_score` is constrained to 0..1. The legacy prompt never constrained it,
       while `sim.js` clamps it to [0,1] and bands at 0.30/0.70, and `decision.js:80` carries a
       standing comment that the field "carries inconsistent scales — raw counts as well". An
       unconstrained score is silently misread as a band by everything downstream.
    2. An explicit instruction to return null rather than guess. The legacy said "do not invent
       values"; this says what to do instead, which is the part a model actually acts on.
    3. LABEL-MATCHING, added 2026-08-05 after the first real-document run. "Never guess, infer,
       or carry a value over from a different field" was not enough on its own: run against a
       real contract value summary, the model took the header's reporting period ("Period | 1
       March 2026 through 31 March 2026", plainly labelled as the period, in the same block as
       the issue date and the data date) and returned it as `project_start_date` /
       `project_end_date`. The document has no project baseline dates at all. Both values were
       well-formed, in-range dates, so neither guard (`validate_doc_risk_score`,
       `validate_numeric_fields`) could have caught it — a malformed-numeric refusal only fires
       on a value that cannot be read as the requested TYPE, and a substituted date is a
       perfectly good date. The old instruction forbade carrying a value FROM a named field TO
       another named field; it never told the model that a value under NO matching label at all
       is equally not a source. This paragraph closes that gap, generalised across the whole
       field vocabulary rather than written for dates alone: the failure is "a value of the
       right type sitting nearby", and that shape is not specific to dates.

       No field in the vocabulary (`extraction_fields.ALL_FIELDS`) legitimately needs a value the
       model derives rather than one the document states. This was checked, not assumed: every
       name in that list is a total, a date, a rating, a percentage or a count a construction
       report states directly, and the platform's own standing description
       (`NAMING_AUTHORITY.md` section 3) already commits to "reads the reported figures", not
       "extracts" or "computes" them — `CPI`/`SPI` are the one place a value IS derived, and
       those are computed server-side, never asked of the model ("Do not compute indices",
       below, predates this change).

       ONE NAMED EXCEPTION, added alongside the same run: `milestones_json` is not a scalar, and
       the same run's second document showed the model returning null for a genuine activity
       table because nothing told it a document's own schedule table IS a milestones_json
       source or how to shape one field's value as a table. That is not the same failure as
       substitution — it is UNDER-application of "read what is there", not over-application —
       but the fix has to name the shape explicitly because a whole-table answer inside one
       JSON field is not something the general instructions describe.
    """
    milestones_hint = (
        " milestones_json, if requested and the document contains a schedule, activity or "
        "milestone table, is a JSON array with one object per row of that table, using the "
        "table's own column headings as keys and its values as printed (do not reformat or "
        "reinterpret a value inside this table — dates inside it are NOT required to be "
        "YYYY-MM-DD, unlike every other date field below); return an empty array only if the "
        "document has no such table."
    ) if "milestones_json" in fields else ""
    # RUN 68. THE SECOND TABLE FIELD, and it needs its own sentence for the same reason the
    # first one did: a whole-table answer inside one JSON field is not something the general
    # instructions describe, and without naming the shape the model returns null for a table
    # that is plainly printed on the page. The hint asks for the ROWS AS PRINTED and forbids
    # completing, extending or interpolating the curve, because a baseline period the document
    # does not print is exactly the invented value the extractor must never supply.
    baseline_hint = (
        " baseline_curve_json, if requested and the document contains a time-phased baseline "
        "table (a period-by-period profile of planned value, planned cost or planned spend), is "
        "a JSON array with one object per PRINTED ROW of that table, using the table's own column "
        "headings as keys and its values as printed; return every row the document prints and "
        "no others -- do not extend, complete or interpolate the profile, and do not compute a "
        "cumulative figure from a periodic one or the other way round unless the document "
        "prints both columns; return an empty array only if the document has no such table."
    ) if "baseline_curve_json" in fields else ""
    # RUN 69. THE THIRD AND FOURTH TABLE FIELDS. Same reason as the first two: a whole-table
    # answer inside one JSON field is not something the general instructions describe, and
    # without naming the shape the model returns null for a table that is plainly printed.
    resource_hint = (
        " resource_profile_json, if requested and the document contains a resource histogram or "
        "resource-loading table (a period-by-period profile of resource demand against resource "
        "availability), is a JSON array with one object per PRINTED ROW of that table, using the "
        "table's own column headings as keys and its values as printed; return every row the "
        "document prints and no others -- do not total, extend or interpolate the profile, and "
        "never repeat a demand figure as an availability figure or the other way round; return "
        "an empty array only if the document has no such table."
    ) if "resource_profile_json" in fields else ""
    modifications_hint = (
        " modifications_json, if requested and the document contains a contract modification or "
        "change register, is a JSON array with one object per PRINTED ROW of that register, "
        "using the register's own column headings as keys and its values as printed; return "
        "every row the document prints and no others. Do not infer that an official held "
        "authority because a document is signed, and do not supply an authority reference the "
        "register does not print; return an empty array only if the document has no such table."
    ) if "modifications_json" in fields else ""
    # RUN 72. THE SCALE OF A RATIO FIELD, NAMED, because the general sentence below is false
    # of it. "Percentages as numbers 0-100" is correct for every 0..100 quantity in the
    # vocabulary and WRONG for a compliance rate, which the numeric contract bounds at 1.0. A
    # real Environmental Compliance Report printing "Environmental compliance rate 1.000" was
    # refused whole because extraction returned 100 for it: under the instructions as they
    # stood, 100 was the compliant answer to a document that states 1.000. The guard did its
    # job -- the instruction was the defect. The field list comes from
    # `extraction_merge.ratio_scaled_extraction_keys()`, which reads the same
    # `BOUNDED_MAX_SI_FIELDS` table the refusal reads, so the prompt and the range check can
    # never disagree about which fields are shares.
    from .extraction_merge import ratio_scaled_extraction_keys

    _ratio = [k for k in ratio_scaled_extraction_keys() if k in fields]
    ratio_hint = (
        " " + ", ".join(_ratio) + (" is" if len(_ratio) == 1 else " are") +
        " a SHARE between 0 and 1 inclusive, not a percentage: return the figure exactly as the "
        "document prints it (a document stating 1.000 gives 1.000, and one stating 0.94 gives "
        "0.94), and never multiply it by one hundred. If the document prints only the counts "
        "behind such a share and never the share itself, return null -- do not divide one count "
        "by the other. "
    ) if _ratio else ""
    return (
        "You are a precise construction project-controls data extractor. Read this ONE document "
        f"(type: {doc_type}) and return ONLY these fields as clean JSON: "
        f"{json.dumps(fields)}. "
        "A field is returned ONLY when the document itself states that field, under a label or "
        "heading whose meaning matches the field's name. A different value sitting nearby, under "
        "a different label, is never a substitute, even if it is a plausible value of the right "
        "type and in a sensible range: a reporting period is not a project start or end date, an "
        "issue date or a data date is not a baseline date, and a schedule-progress percentage is "
        "not a cost-basis percentage. If you cannot point to the specific label in the document "
        "that names this field, return null for it. Counting entries in the document's own table "
        "is reading a stated fact, not inferring one, when the field name plainly refers to that "
        "table (for example, a count of rows in a schedule or activity table)." + milestones_hint + baseline_hint + resource_hint + modifications_hint +
        " Use null for any field genuinely not present in the document. Never guess, invent, or "
        "carry a value over from a different field or a different document. Do not compute "
        "indices. "
        "Numbers as plain numbers (no currency symbols, no thousands separators). "
        "Return every number on the scale the document prints it on: never convert a ratio "
        "into a percentage or a percentage into a ratio, never rescale, and never restate a "
        "figure in different units from the ones the document uses. "
        "Percentages as numbers 0-100. Dates as YYYY-MM-DD. " + ratio_hint +
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
        # TRUNCATION IS CHECKED FIRST, and it is checked before the salvage attempt below.
        # A cut-off response is not malformed JSON and calling it that sent three retries at a
        # failure that reproduces identically every time. See TruncatedResponseError.
        cut = describe_json_truncation(text)
        if cut is not None:
            raise TruncatedResponseError(
                "the model ran out of output space before it finished answering: " + cut +
                ". Retrying will stop in the same place; the answer has to be made smaller."
            ) from None
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
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        # THE API SAYS SO ITSELF. `stop_reason` is the authoritative statement that the answer
        # was cut off by the output cap rather than finished; `describe_json_truncation` is the
        # fallback for a caller that never sees this field. Raising here means the message names
        # truncation even when the truncated prefix happens to close its own braces.
        if str(payload.get("stop_reason") or "") == "max_tokens":
            cut = describe_json_truncation(text)
            raise TruncatedResponseError(
                f"the model ran out of output space ({max_tokens} tokens) before it finished "
                "answering" + (": " + cut if cut else "") +
                ". Retrying will stop in the same place; the answer has to be made smaller."
            )
        return text

    @staticmethod
    def _content_block(raw: bytes, mime_type: str, filename: str = "",
                       elide_tables: dict[int, str] | None = None) -> dict:
        """
        A .docx is read locally into text and tables; PDFs go as a document block; anything
        else is decoded as text.

        THE DOCX BRANCH IS FIRST, AND IT IS DECIDED FROM THE BYTES. A .docx is a ZIP archive, so
        before this branch existed it fell through to the raw-decode below and became 12000
        characters of deflate-compressed binary — measured on a real file, 5071 U+FFFD
        replacement characters, with the truncation consumed by ZIP headers before the body was
        reached. It is tested before the PDF branch rather than after because `signals.js` sends
        `file.type || "application/pdf"`, so a docx the browser did not type arrives CLAIMING to
        be a PDF and a mime-first test would send the archive as a PDF document block.

        See `docx_text` for why reading it locally is the better route for these documents and
        not a workaround: the tables survive as structure rather than as guessed layout, and
        there is no OCR step.

        The legacy split PDF-versus-text the same way (`claudePdfExtract_` vs `claudeChat_`) and
        truncated text at 12000 characters. That truncation is preserved for the raw-bytes
        branch: it bounds a prompt built from an unknown blob. The docx branch carries its own,
        larger bound, because that text has already been parsed and a pay application's summary
        rows can sit past 12000 characters.
        """
        from .docx_text import docx_content_block, is_docx

        if is_docx(raw, mime_type, filename):
            return docx_content_block(raw, elide_tables)
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
        block = self._content_block(raw, mime_type, filename)
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
        # PART 2, THE SEPARATION. Where the reader can take the activity table itself, the
        # table stops competing with the scalar fields for one response's output budget:
        # `milestones_json` is not asked for, and the table's rows are not sent either. The
        # scalar fields then have the whole budget, which is what they always needed and never
        # had — the response that failed three times died at its seventh scalar key.
        from .risk_register import risk_table_from_document
        from .schedule_table import activity_table_from_document

        table = activity_table_from_document(raw, mime_type, filename)
        elide: dict[int, str] | None = None
        if table is not None:
            fields = [f for f in fields if f != "milestones_json"]
            elide = {table.index: table.elision_note()}
        # THE SAME SEPARATION FOR THE RISK REGISTER, and it was never asked for as a field, so
        # there is nothing to drop from `fields` -- only the rows to keep out of the prompt. A
        # register of five hundred risks and one of twenty therefore cost the same call: the
        # header row survives so the model can still see the document HAS a register and answer
        # its scalar fields, and the unbounded part is read by `risk_register` from the document
        # itself.
        risks = risk_table_from_document(raw, mime_type, filename)
        if risks is not None and (table is None or risks.index != table.index):
            elide = dict(elide or {})
            elide[risks.index] = risks.elision_note()
        block = self._content_block(raw, mime_type, filename, elide)
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
