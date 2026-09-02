"""
RUN 111. THE RECOGNITION STEP: MATCHING A PRINTED LABEL TO A NAMED QUANTITY.

WHAT RUN 110 LEFT. Every value an extraction returns is now stored as RAW evidence -- the
document, the period, the label the document printed it under, and the value, untouched. On the
census fixture that is 158 rows. NOTHING READ THEM. `select_signal_inputs` iterates a fixed key
order and no declared field name contains a colon, so a RAW row could not be reached by the
declared vocabulary even in principle. That was deliberate: reaching them requires deciding that
a value a document called `weather_days_approved` is the quantity a specification asks for, and
Run 110 refused to write a hand-coded synonym table in place of that decision.

THIS MODULE IS THE READER. It is the ONE place where a model is asked which stored value answers
a specification, and it is built so that the model's authority is as narrow as it can be made.

=================================================================================================
WHAT THE MODEL IS ALLOWED TO DO, AND IT IS ONE THING
=================================================================================================

It is shown a numbered list of candidates -- each one a label a document printed, with the value
printed under it -- and one specification written in plain terms. It returns ONE CANDIDATE ID, or
it returns that nothing in the list answers the specification.

    IT RETURNS AN IDENTIFIER, NOT A VALUE. The value is then read out of the evidence store by
    that identifier. A model that echoes a different number, invents a figure, or names a label
    that was not offered CANNOT put that figure into a reading: `recognise` looks the candidate
    up in the offered set and raises `RecognitionContractError` when the identifier is not one it
    offered. "It never invents a value" is therefore a property of the mechanism, not an
    instruction in a prompt that a model may or may not follow.

    IT NEVER DERIVES ONE FIGURE FROM ANOTHER. There is no arithmetic anywhere in this module. A
    quantity is answered by a value some document printed, or it is not answered.

    IT NEVER DECIDES A THRESHOLD, A BAND, A CATEGORY POSTURE OR A PROJECT STATUS. Nothing here
    reads or writes a boundary. This module produces governed STRUCTURES, which are handed to the
    same `canonical_v4` functions and the same band ladders that serve a structure typed in
    through the governed intake. Every boundary decision stays exactly where it was.

    IT NEVER PICKS A PROVIDER. `ai_provider.load_provider("recognition")` resolves the owner's
    setting. There is no fallback, no retry against another name, and no second provider.

=================================================================================================
DETERMINISM, WHICH MATTERS MORE THAN THE FEATURE
=================================================================================================

A model call is not a deterministic function. `temperature=0` narrows the distribution; it does
not make one. Serving stacks batch requests, and an identifier such as `claude-3-5-haiku-latest`
is an alias that can be repointed under a running deployment. A platform whose readings changed
between two computations of the same period would not be usable as a research instrument.

SO THE ANSWER IS NOT TO ASK TWICE. Determinism here is obtained by RECORDING THE MATCH AND
REUSING IT, keyed on a fingerprint of everything that could change the answer:

    * every candidate offered, in canonical order: document id, document type, sha256, period,
      label and value;
    * the exact specification text the model was shown;
    * the prompt template version;
    * the provider name and the model identifier.

Change any of those -- a superseding document, an edited specification, a switch from Anthropic
to Groq -- and the fingerprint changes, the question is asked again, and BOTH answers stay in the
store, each naming the evidence and the model that produced it. Change none of them and no call
is made at all: the recorded answer is returned byte-identical, for ever.

THREE ALTERNATIVES WERE CONSIDERED AND ARE UNSOUND. (1) "temperature=0 is enough" -- it is a
narrowing, not a guarantee, and it does not survive an alias being repointed. (2) "cache on the
project, period and module" -- it is deterministic and WRONG: a revised document changes the
evidence and the stale match would be replayed over it, which is worse than varying, because it
is silently incorrect. (3) "ask three times and take the majority" -- three draws from a
distribution are still a draw from a distribution, at three times the cost.

WHAT IS AND IS NOT GUARANTEED, STATED PLAINLY. Within one deployment's store, identical evidence
always produces the identical reading. The FIRST ask against a fingerprint that has never been
asked is one model call and is not itself reproducible; two deployments starting from empty
stores could in principle record different first answers. That is detectable rather than
invisible, because every match records the fingerprint, the provider and the model. Making two
deployments agree requires copying the match rows between them, which the fingerprint is exactly
the key for.

=================================================================================================
WHAT IS DELIBERATELY NOT RECOGNISED
=================================================================================================

Four structures carry AUTHORITY rather than shape, and Run 110 established that no document
states them:

    signalWeightPolicy            the owner's weights
    informationPackageRecord      the governed definition of a complete package
    independentEacPair            the CLAIM that a second forecast was independently prepared
    costRiskModel / milestoneForecastHistory   the governed intake

None of them appears in `RECIPES` and none may be added to it. In particular A1.11 Independent
EAC Reconciliation is NOT servable by recognition and this module does not attempt it: the thing
that is missing is not a number anyone printed, it is the assertion that two forecasts were
prepared independently of one another. That assertion can only come from whoever prepared them.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field as dc_field
from typing import Any, Callable, Sequence

from . import ai_provider

log = logging.getLogger("opus-gubernatio-server")

#: Bumped whenever the prompt text or the candidate rendering changes, because either changes
#: what the model was asked and therefore invalidates every recorded match made under the old
#: one. It is part of the fingerprint, so a bump re-asks rather than replaying a stale answer.
PROMPT_TEMPLATE_VERSION = "run111.recognition.v1"

#: The output cap. The answer is one small JSON object; a model that cannot finish inside this
#: is malfunctioning and `ProviderTruncated` says so rather than a partial object being parsed.
MAX_TOKENS = 512
REQUEST_TIMEOUT_S = 120.0

#: Asked at temperature 0. See the docstring: this NARROWS the distribution and is not what
#: makes the platform deterministic. The match store is.
TEMPERATURE = 0.0


class RecognitionError(RuntimeError):
    """Recognition could not be carried out. Always names what was asked and of whom."""


class RecognitionContractError(RecognitionError):
    """
    The provider answered, and the answer is not one this platform can act on.

    Carries the raw text, truncated, because on a deployment this is the message the owner has
    to debug from and "the model returned something unusable" is not debuggable.
    """


# =============================================================================================
# THE SPECIFICATION -- THE QUANTITY IN PLAIN TERMS, NOT A FIELD NAME
# =============================================================================================


@dataclass(frozen=True)
class QuantitySpec:
    """
    One quantity a module needs, stated the way section 4.1 requires: what it is, its units,
    what it is a proportion of where it is one, and what would disqualify a candidate.

    NO FIELD NAME APPEARS IN `what_it_is`. That is the whole point. A specification that named
    `weather_days_approved` would be the hand-coded synonym table under another name, and would
    match exactly one document's vocabulary -- the platform's own.
    """

    quantity_id: str
    what_it_is: str
    units: str
    proportion_of: str | None = None
    disqualifiers: tuple[str, ...] = ()
    #: True when the answer is expected to be one COLUMN of a printed table rather than a single
    #: figure -- a per-firm rating, an item's required date. Candidates are offered accordingly.
    columnar: bool = False

    def as_text(self) -> str:
        """The exact words the model is shown. Deterministic, and part of the fingerprint."""
        lines = [f"WHAT IT IS: {self.what_it_is}", f"UNITS: {self.units}"]
        if self.proportion_of:
            lines.append(f"IT IS A PROPORTION OF: {self.proportion_of}")
        if self.columnar:
            lines.append("SHAPE: one column of a printed table, one entry per row of that table.")
        else:
            lines.append("SHAPE: a single figure or a single stated value, not a table column.")
        if self.disqualifiers:
            lines.append("A CANDIDATE IS DISQUALIFIED IF:")
            lines.extend(f"  - {d}" for d in self.disqualifiers)
        return "\n".join(lines)


@dataclass(frozen=True)
class StructureRecipe:
    """
    One module's governed structure, and the quantities it is composed from.

    `build` RECEIVES the recognised values and RETURNS the structure. It performs no arithmetic
    and derives nothing: it places values the documents printed into the shape the canonical
    function reads. Where any required quantity was not recognised, `build` is never called and
    the structure is absent -- exactly as it is today -- so the module abstains on its own guard
    with its own words.
    """

    module_id: str
    structure_key: str
    what_the_module_needs: str
    quantities: tuple[QuantitySpec, ...]
    build: Callable[[dict[str, "Match"]], dict[str, Any] | None]
    #: Quantity ids that may be absent without the structure being abandoned.
    optional: frozenset[str] = dc_field(default_factory=frozenset)


# =============================================================================================
# THE CANDIDATES -- WHAT THE EVIDENCE STORE HOLDS, RENDERED FOR READING
# =============================================================================================


@dataclass(frozen=True)
class Candidate:
    """One thing a document printed, and everything needed to trace it back."""

    candidate_id: str
    document_id: str
    doc_type: str
    sha256: str
    filename: str
    period: int
    label: str
    value: Any
    #: Non-empty when this candidate is one COLUMN of a table the document printed.
    column: str | None = None

    @property
    def printed_as(self) -> str:
        return self.label if self.column is None else f"{self.label} [{self.column}]"

    def fingerprint_row(self) -> list[Any]:
        return [self.document_id, self.doc_type, self.sha256, self.period,
                self.label, self.column, _canonical(self.value)]


def _canonical(value: Any) -> str:
    """A value as one stable string. Sorted keys, no whitespace drift, total over any JSON."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _truncate(value: Any, limit: int = 240) -> str:
    text = _canonical(value)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def build_candidates(rows: Sequence[dict], *, columnar: bool) -> list[Candidate]:
    """
    The candidate set for one question, from RAW evidence rows.

    `rows` are dicts carrying document_id, doc_type, sha256, filename, period, label and value.

    TWO SHAPES, BECAUSE DOCUMENTS PRINT TWO SHAPES. A stated figure is one candidate. A table --
    a list of rows -- is offered as ONE CANDIDATE PER COLUMN HEADING, carrying that column's
    values in the table's own row order. Recognising "the column headed Rating is the rating"
    is the same act as recognising "the figure headed weather_days_approved is the approved
    days", and doing it this way means no column heading is ever hand-mapped.

    ORDER IS CANONICAL AND IDENTIFIERS ARE ASSIGNED FROM IT, so the same evidence always yields
    the same list under the same identifiers. Nothing here depends on database row order.
    """
    out: list[tuple[tuple, dict]] = []
    for r in rows:
        value = r.get("value")
        base = {"document_id": str(r.get("document_id") or ""),
                "doc_type": str(r.get("doc_type") or ""),
                "sha256": str(r.get("sha256") or ""),
                "filename": str(r.get("filename") or ""),
                "period": int(r.get("period") or 0),
                "label": str(r.get("label") or "")}
        table = _as_table(value)
        if columnar:
            if table is None:
                continue
            for col in sorted({str(k) for row in table for k in row}):
                col_values = [row.get(col) for row in table]
                out.append(((base["doc_type"], base["label"], col),
                            {**base, "value": col_values, "column": col}))
        else:
            if table is not None:
                continue          # a table is not a single stated value; it is not offered here
            out.append(((base["doc_type"], base["label"], ""), {**base, "value": value,
                                                                "column": None}))
    out.sort(key=lambda x: (x[0][0], x[0][1], x[0][2]))
    return [Candidate(candidate_id=f"E{i:03d}", **payload) for i, (_k, payload) in
            enumerate(out, start=1)]


def _as_table(value: Any) -> list[dict] | None:
    """A list of dicts, or None. A table is recognised by shape and by nothing else."""
    if isinstance(value, list) and value and all(isinstance(r, dict) for r in value):
        return value
    return None


# =============================================================================================
# THE PROMPT -- BUILT ONCE, FINGERPRINTED, AND NEVER VARIED BETWEEN RUNS
# =============================================================================================

_INSTRUCTIONS = """\
You are reading evidence transcribed from the documents of one construction project. Each
numbered candidate below is a LABEL one of those documents printed, with the value that was
printed under it. The labels are the documents' own words; they are not this platform's names
for anything.

You are given ONE SPECIFICATION describing a single quantity in plain terms.

Decide which ONE candidate, if any, is the quantity the specification describes.

RULES YOU MUST FOLLOW:
  1. Answer with a candidate identifier from the list. Do not answer with a value.
  2. Do not calculate. Do not derive the quantity from two or more candidates.
  3. Do not answer with a candidate that is a different quantity which happens to be close, or
     that would need converting, rescaling or reinterpreting to answer the specification.
  4. If no candidate is the quantity described, say so. Answering "none" is a correct answer and
     is expected whenever the documents did not state this quantity.

Reply with a single JSON object and nothing else, in one of these two forms:

  {"candidate_id": "E012", "printed_as": "<the label as shown>", "why": "<one short sentence>"}
  {"candidate_id": null, "why": "<one short sentence saying what was missing>"}
"""


def build_prompt(spec: QuantitySpec, candidates: Sequence[Candidate]) -> list[dict]:
    """
    The content blocks for one question. TEXT ONLY, deliberately: the evidence has already been
    extracted and transcribed, so no document is re-sent, which means this call carries the same
    shape on every provider and `ProviderCannotCarry` cannot fire for it.
    """
    lines = ["SPECIFICATION", "", spec.as_text(), "", "CANDIDATES", ""]
    for c in candidates:
        lines.append(f'  {c.candidate_id}  printed as "{c.printed_as}" in a '
                     f'{c.doc_type or "document"} for period {c.period}')
        lines.append(f'        value: {_truncate(c.value)}')
    if not candidates:
        lines.append("  (the evidence store holds nothing of this shape for this period)")
    return [{"type": "text", "text": _INSTRUCTIONS + "\n" + "\n".join(lines)}]


def evidence_fingerprint(spec: QuantitySpec, candidates: Sequence[Candidate],
                         provider: str, model: str) -> str:
    """
    THE DETERMINISM KEY. Everything that could change the answer, and nothing that could not.

    Deliberately NOT included: the project id, the wall clock, the order rows came back from the
    database, and the candidate identifiers (which are derived from the canonical order and so
    are already implied by it). Deliberately INCLUDED: the provider and the model, because two
    models are two answers to the same question and must not share one recorded answer.
    """
    payload = {
        "template": PROMPT_TEMPLATE_VERSION,
        "quantity_id": spec.quantity_id,
        "specification": spec.as_text(),
        "provider": provider,
        "model": model,
        "candidates": [c.fingerprint_row() for c in candidates],
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def prompt_fingerprint(blocks: Sequence[dict]) -> str:
    return hashlib.sha256(_canonical(list(blocks)).encode("utf-8")).hexdigest()


# =============================================================================================
# THE RESULT CONTRACT -- STRICT, AND LOUD ABOUT ANYTHING ELSE
# =============================================================================================


@dataclass(frozen=True)
class Match:
    """
    One recognition outcome. `matched` False is a RESULT, not a failure: the documents did not
    state this quantity, and the module will abstain saying what it looked for.

    `value` is read from the evidence store by candidate id. It is NEVER the model's echo.
    """

    quantity_id: str
    matched: bool
    fingerprint: str
    provider: str
    model: str
    prompt_sha256: str
    why: str = ""
    candidate_id: str | None = None
    label: str | None = None
    column: str | None = None
    document_id: str | None = None
    doc_type: str | None = None
    sha256: str | None = None
    filename: str | None = None
    period: int | None = None
    value: Any = None
    #: True when this Match was replayed from the store rather than asked. See the docstring.
    from_store: bool = False

    def trace(self) -> dict[str, Any]:
        """What the reading records so a reader can check it. Section 4.4."""
        return {
            "quantity_id": self.quantity_id,
            "matched": self.matched,
            "printed_label": self.label if self.column is None
            else f"{self.label} [{self.column}]",
            "document_id": self.document_id,
            "document_type": self.doc_type,
            "document_sha256": self.sha256,
            "filename": self.filename,
            "period": self.period,
            "recognised_by": f"{self.provider}/{self.model}",
            "evidence_fingerprint": self.fingerprint,
            "prompt_sha256": self.prompt_sha256,
            "replayed_from_recorded_match": self.from_store,
            "model_reason": self.why,
        }


def parse_answer(text: str, offered: dict[str, Candidate], *, provider: str,
                 model: str) -> tuple[str | None, str]:
    """
    (candidate_id or None, why), or `RecognitionContractError` naming EXACTLY what came back.

    A FENCED BLOCK IS UNWRAPPED and nothing else is tolerated. Prose around the object, a list, a
    bare value, an identifier that was not offered: each is its own message, because on a
    deployment the difference between "the model refused" and "the model named a label I never
    showed it" is the difference between a settings problem and a defect.
    """
    raw = (text or "").strip()
    if raw.startswith("```"):
        body = raw.split("```")
        raw = (body[1] if len(body) > 1 else "").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    if not raw:
        raise RecognitionContractError(
            f"{provider} ({model}) returned an EMPTY answer to a recognition question. "
            f"Expected a JSON object carrying `candidate_id`. Nothing was matched and no value "
            f"was taken from any document.")
    try:
        obj = json.loads(raw)
    except ValueError as exc:
        raise RecognitionContractError(
            f"{provider} ({model}) returned an answer that is not JSON ({exc}). Expected a "
            f"single JSON object carrying `candidate_id`. What came back was: "
            f"{raw[:400]!r}") from None
    if not isinstance(obj, dict):
        raise RecognitionContractError(
            f"{provider} ({model}) returned a JSON {type(obj).__name__}, not an object. "
            f"Expected {{\"candidate_id\": ...}}. What came back was: {raw[:400]!r}")
    if "candidate_id" not in obj:
        raise RecognitionContractError(
            f"{provider} ({model}) returned a JSON object with no `candidate_id` key. Its keys "
            f"were {sorted(map(str, obj))!r}. What came back was: {raw[:400]!r}")
    why = str(obj.get("why") or "").strip()[:400]
    cid = obj.get("candidate_id")
    if cid is None:
        return None, why
    if not isinstance(cid, str) or cid not in offered:
        raise RecognitionContractError(
            f"{provider} ({model}) answered with candidate identifier {cid!r}, which is NOT one "
            f"of the {len(offered)} candidates it was shown "
            f"({', '.join(sorted(offered)[:12])}{'...' if len(offered) > 12 else ''}). No value "
            f"was taken from any document: this platform reads the value out of its own evidence "
            f"store by the identifier it offered, so an identifier it did not offer cannot "
            f"produce a figure. What came back was: {raw[:400]!r}")
    return cid, why


# =============================================================================================
# THE CALL -- ONE PROVIDER, THE OWNER'S, AND NO FALLBACK
# =============================================================================================


def ask_provider(blocks: list[dict], cfg: ai_provider.ProviderConfig,
                 environ: dict[str, str] | None = None) -> str:
    """
    The single point where a model is asked a recognition question.

    NO FALLBACK AND NO RETRY AGAINST A DIFFERENT NAME. Every failure propagates carrying the
    provider and the model identifier -- `ProviderNotConfigured` names the environment variable,
    `ProviderCallError` carries the provider's own HTTP status and body, `ProviderTruncated` says
    the answer was cut off rather than malformed.
    """
    client = ai_provider.build_client(cfg, timeout_s=REQUEST_TIMEOUT_S, environ=environ)
    return client.complete(blocks, max_tokens=MAX_TOKENS, temperature=TEMPERATURE)


#: Substituted ONLY by `tools/drive_run111.py` to prove that a replayed match makes no call at
#: all -- it is replaced with a function that RAISES, so a call that should not happen fails
#: the driver instead of passing silently. It is never given an answer to return: this platform
#: does not simulate a model call, and no stub result is ever recorded as a model's behaviour.
_ASK: Callable[..., str] = ask_provider


def recognise(spec: QuantitySpec, candidates: Sequence[Candidate], store: "MatchStore",
              cfg: ai_provider.ProviderConfig,
              environ: dict[str, str] | None = None) -> Match:
    """
    One quantity, recognised: replayed from the store if it has been asked before, otherwise
    asked once and recorded.

    THE VALUE COMES FROM THE STORE, NOT FROM THE ANSWER. See the module docstring.
    """
    offered = {c.candidate_id: c for c in candidates}
    fp = evidence_fingerprint(spec, candidates, cfg.provider, cfg.model)

    recorded = store.get(spec.quantity_id, fp)
    if recorded is not None:
        return _match_from_record(spec, recorded, offered, fp, cfg, from_store=True)

    blocks = build_prompt(spec, candidates)
    psha = prompt_fingerprint(blocks)
    text = _ASK(blocks, cfg, environ)
    cid, why = parse_answer(text, offered, provider=cfg.provider, model=cfg.model)
    record = {"candidate_id": cid, "why": why, "prompt_sha256": psha,
              "provider": cfg.provider, "model": cfg.model,
              "template_version": PROMPT_TEMPLATE_VERSION,
              "candidate_count": len(candidates)}
    if cid is not None:
        c = offered[cid]
        record.update({"label": c.label, "column": c.column, "document_id": c.document_id,
                       "doc_type": c.doc_type, "sha256": c.sha256, "filename": c.filename,
                       "period": c.period})
    store.put(spec.quantity_id, fp, record)
    return _match_from_record(spec, record, offered, fp, cfg, from_store=False)


def _match_from_record(spec: QuantitySpec, record: dict, offered: dict[str, Candidate],
                       fp: str, cfg: ai_provider.ProviderConfig, *, from_store: bool) -> Match:
    cid = record.get("candidate_id")
    common = {"quantity_id": spec.quantity_id, "fingerprint": fp,
              "provider": str(record.get("provider") or cfg.provider),
              "model": str(record.get("model") or cfg.model),
              "prompt_sha256": str(record.get("prompt_sha256") or ""),
              "why": str(record.get("why") or ""), "from_store": from_store}
    if cid is None:
        return Match(matched=False, **common)
    c = offered.get(str(cid))
    if c is None:
        # A recorded match whose candidate is no longer offered CANNOT happen while the
        # fingerprint covers the candidate set -- the fingerprint would have changed. It is
        # refused rather than tolerated, because tolerating it is how a stale figure gets in.
        raise RecognitionContractError(
            f"the recorded match for {spec.quantity_id} names candidate {cid!r}, which is not "
            f"in the candidate set its fingerprint {fp[:12]} was taken over. The match store "
            f"and the evidence store disagree; no value is read and none is substituted.")
    return Match(matched=True, candidate_id=c.candidate_id, label=c.label, column=c.column,
                 document_id=c.document_id, doc_type=c.doc_type, sha256=c.sha256,
                 filename=c.filename, period=c.period, value=c.value, **common)


# =============================================================================================
# THE MATCH STORE
# =============================================================================================


class MatchStore:
    """
    Append-only record of what was matched to what, keyed by (quantity, fingerprint).

    A row is NEVER updated. The same quantity asked over changed evidence is a new fingerprint
    and therefore a new row, and both stay readable -- which is what makes "why did this reading
    change?" answerable from the database rather than from a report.
    """

    def __init__(self, session, project_id) -> None:
        self._session = session
        self._project_id = project_id
        self._cache: dict[tuple[str, str], dict] = {}

    def get(self, quantity_id: str, fingerprint: str) -> dict | None:
        key = (quantity_id, fingerprint)
        if key in self._cache:
            return self._cache[key]
        from sqlalchemy import select
        from .research_models import RecognitionMatch
        row = self._session.scalar(
            select(RecognitionMatch).where(
                RecognitionMatch.project_id == self._project_id,
                RecognitionMatch.quantity_id == quantity_id,
                RecognitionMatch.evidence_fingerprint == fingerprint))
        if row is None:
            return None
        rec = dict(row.match or {})
        self._cache[key] = rec
        return rec

    def put(self, quantity_id: str, fingerprint: str, record: dict) -> None:
        from .research_models import RecognitionMatch
        self._session.add(RecognitionMatch(
            project_id=self._project_id, quantity_id=quantity_id,
            evidence_fingerprint=fingerprint, provider=str(record.get("provider") or ""),
            model=str(record.get("model") or ""),
            prompt_sha256=str(record.get("prompt_sha256") or ""),
            template_version=str(record.get("template_version") or ""),
            match=record))
        self._session.flush()
        self._cache[(quantity_id, fingerprint)] = record


class InMemoryMatchStore(MatchStore):
    """The same contract without a database, for the parts of the driver that need no session."""

    def __init__(self) -> None:                      # noqa: D107
        self._rows: dict[tuple[str, str], dict] = {}

    def get(self, quantity_id, fingerprint):
        return self._rows.get((quantity_id, fingerprint))

    def put(self, quantity_id, fingerprint, record):
        self._rows[(quantity_id, fingerprint)] = record


# =============================================================================================
# THE ORCHESTRATOR -- ONE ENTRY POINT, CALLED FROM THE DOCUMENT ASSEMBLY PATH
# =============================================================================================
#
# WHY HERE AND NOT INSIDE A MODULE. A module is a pure function of its signal inputs: it has no
# session, no project and no period, and giving it one would put a network call inside the
# simulation layer. Recognition therefore runs where every other governed structure this
# platform assembles from documents is assembled -- `documents.assemble_and_store` -- and hands
# the module a structure, exactly as `_run69_structures` does. Not one module changes.
#
# `setdefault` AT THE CALL SITE, so a structure supplied through the governed intake or read
# from a document by the declared vocabulary is NEVER displaced by a recognised one. Recognition
# is the last resort, not the first.


def raw_candidate_rows(observations: list[dict], documents: list[dict],
                       period: int) -> list[dict]:
    """The RAW evidence rows of one period, in the shape `build_candidates` reads."""
    from .field_registry import RAW, RAW_PREFIX, is_raw_field
    names = {str(d.get("document_id")): str(d.get("filename") or "") for d in documents}
    rows = []
    for o in observations:
        field = str(o.get("field") or "")
        if o.get("kind") != RAW or not is_raw_field(field):
            continue
        rest = field[len(RAW_PREFIX):]
        doc_type, _, label = rest.partition(":")
        rows.append({"document_id": str(o.get("document_id") or ""),
                     "doc_type": doc_type, "sha256": str(o.get("sha256") or ""),
                     "filename": names.get(str(o.get("document_id") or ""), ""),
                     "period": int(period), "label": label, "value": o.get("value")})
    return rows


def recognised_structures(session, project, period: int, observations: list[dict],
                          documents: list[dict],
                          environ: dict[str, str] | None = None
                          ) -> tuple[dict[str, Any], list[dict]]:
    """
    (structures, log). NEITHER IS EVER SILENT.

    The log carries one entry per recipe: whether recognition was attempted, and if not, exactly
    why -- naming the provider, the model and the environment variable that was empty -- and if
    so, every quantity, whether it was answered, and by which printed label in which document.
    It is written onto the stored signal inputs, so the owner reads it out of the stored result
    rather than out of a server log.

    IT RAISES NOTHING. A recognition fault is a fault of one recipe: it is recorded on the log,
    the structure is not produced, and the module abstains exactly as it does today. One
    provider outage must not take down an upload, and Run 110's guard is about a different
    failure -- a module raising -- and is not a substitute for this.
    """
    from .recognition_recipes import RECIPES

    log_rows: list[dict] = []
    try:
        cfg = ai_provider.load_provider("recognition", environ)
    except ai_provider.ProviderConfigError as exc:
        log_rows.append({"attempted": False, "reason_code": "provider_not_configured",
                         "detail": str(exc)})
        return {}, log_rows
    if not cfg.key_present(environ):
        log_rows.append({
            "attempted": False, "reason_code": "provider_key_absent",
            "provider": cfg.provider, "model": cfg.model, "key_env": cfg.key_env,
            "detail": (f"AI provider {cfg.provider!r} is configured for the recognition call "
                       f"site with model {cfg.model!r}, and {cfg.key_env} is not set in this "
                       f"environment. NO recognition was attempted, no value was read from any "
                       f"document by recognition, and nothing was served by another provider in "
                       f"its place. Set {cfg.key_env}, or point AI_{cfg.provider.upper()}_KEY_ENV "
                       f"at the variable that holds the key, or change AI_PROVIDER."),
            "modules_not_attempted": sorted(RECIPES)})
        return {}, log_rows

    rows = raw_candidate_rows(observations, documents, period)
    scalars = build_candidates(rows, columnar=False)
    columns = build_candidates(rows, columnar=True)
    store = MatchStore(session, project.id)

    out: dict[str, Any] = {}
    for module_id in sorted(RECIPES):
        recipe = RECIPES[module_id]
        entry: dict[str, Any] = {
            "attempted": True, "module_id": module_id,
            "structure_key": recipe.structure_key,
            "what_it_looked_for": recipe.what_the_module_needs,
            "provider": cfg.provider, "model": cfg.model,
            "scalar_candidates_offered": len(scalars),
            "column_candidates_offered": len(columns),
            "quantities": [],
        }
        matches: dict[str, Match] = {}
        unanswered: list[str] = []
        try:
            for spec in recipe.quantities:
                pool = columns if spec.columnar else scalars
                m = recognise(spec, pool, store, cfg, environ)
                matches[spec.quantity_id] = m
                entry["quantities"].append(m.trace())
                if not m.matched and spec.quantity_id not in recipe.optional:
                    unanswered.append(spec.quantity_id)
        except (RecognitionError, ai_provider.ProviderCallError,
                ai_provider.ProviderNotConfigured) as exc:
            entry["outcome"] = "recognition_failed"
            entry["reason_code"] = type(exc).__name__
            entry["detail"] = (
                f"{type(exc).__name__} while recognising for {module_id} through provider "
                f"{cfg.provider!r} with model {cfg.model!r}: {exc} -- no structure was composed "
                f"for this module, no figure was substituted, and no other provider was asked. "
                f"The model identifier is the setting AI_RECOGNITION_MODEL (or "
                f"AI_{cfg.provider.upper()}_RECOGNITION_MODEL); the provider is AI_PROVIDER or "
                f"AI_RECOGNITION_PROVIDER.")
            log_rows.append(entry)
            log.warning("recognition failed for %s: %s", module_id, entry["detail"])
            continue
        if unanswered:
            entry["outcome"] = "not_recognised"
            entry["unanswered_quantities"] = unanswered
            entry["detail"] = (
                f"the evidence stored for this period answers none of {unanswered!r}, so no "
                f"{recipe.structure_key} was composed and no figure was invented for the "
                f"quantities that were not found. What the module needs is: "
                f"{recipe.what_the_module_needs}.")
            log_rows.append(entry)
            continue
        structure = recipe.build(matches)
        if structure is None:
            entry["outcome"] = "structure_not_composable"
            entry["detail"] = (
                f"every quantity {recipe.structure_key} needs was recognised, but the recognised "
                f"values do not compose one register -- see `recognition_recipes.build` for the "
                f"specific refusal. Nothing was padded, truncated or aligned by guess.")
            log_rows.append(entry)
            continue
        structure["recognition"] = [matches[q.quantity_id].trace() for q in recipe.quantities]
        out[recipe.structure_key] = structure
        entry["outcome"] = "structure_composed"
        entry["detail"] = (
            f"{recipe.structure_key} composed from "
            + "; ".join(f"{m.quantity_id} <- {m.trace()['printed_label']!r} in "
                        f"{m.doc_type} {m.filename or m.document_id}"
                        for m in matches.values()))
        log_rows.append(entry)
    return out, log_rows


def recognition_diagnostics(environ: dict[str, str] | None = None) -> dict[str, Any]:
    """
    What the recognition call site is configured for, for `/exec` health. PRESENCE ONLY.

    The owner reads this on his deployment before he uploads anything, which is the point: a
    wrong model identifier should be visible from the health endpoint rather than discovered
    from a failed upload.
    """
    from .recognition_recipes import RECIPES
    out: dict[str, Any] = {
        "promptTemplateVersion": PROMPT_TEMPLATE_VERSION,
        "modulesWithRecipes": sorted(RECIPES),
        "modulesDeliberatelyExcluded": {
            "A1.11": "independentEacPair is an authority claim, not a figure any document states",
            "A4.7": "the escalation process is a governance artefact declared by whoever governs "
                    "it, not a quantity a document prints",
        },
    }
    try:
        cfg = ai_provider.load_provider("recognition", environ)
    except ai_provider.ProviderConfigError as exc:
        out["error"] = str(exc)
        return out
    out.update({"provider": cfg.provider, "model": cfg.model, "keyEnv": cfg.key_env,
                "keyPresent": cfg.key_present(environ), "attribution": cfg.attribution,
                "modelSetting": "AI_RECOGNITION_MODEL or "
                                f"AI_{cfg.provider.upper()}_RECOGNITION_MODEL",
                "providerSetting": "AI_PROVIDER or AI_RECOGNITION_PROVIDER"})
    return out
