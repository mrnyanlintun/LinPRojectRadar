"""
Run 76. THE SPECIFICATION IS THE MODULE.

WHAT THIS FILE IS. The call path that applies a WRITTEN SPECIFICATION to stored figures, per
category. It replaces the hand-written Python module layer for any category that has a
specification in `specifications/`; a category without one is untouched and still runs in Python.

WHAT THIS FILE IS NOT, and the boundary is the owner's ruling at section 4 of the Run 76 order:

  - It does NOT fuse. `category_posture` decides which status a category carries, in Python,
    here as before -- averaging in A1, A2, A3 and A4, worst-wins in A6 (Run 104).
    If a model decided which status wins, fusion could vary between runs on identical readings,
    and that is the one place variance would be indefensible.
  - It does NOT enforce the recommendation checks.
  - It does NOT store. Storage is the caller's, so that a result is written by the same code that
    writes every other result.

THE FOUR STATES, and they are four because the order forbids blurring them (section 6, and
section 12.4 fails the run if they are displayed as the same thing):

  COMPUTED     a value and its band, or a value with `band_asserted` false where the
               specification records the module as bandless.
  ABSTAINED    the evidence is not there. The module states which input it wants. CORRECT
               BEHAVIOUR, not a failure.
  OUT_OF_ORDER the specification could have applied, but the category's upstream inputs have not
               run. It names which upstream categories are missing. A WARNING, not a failure.
  FAILED       the call errored, or the model returned something unusable, or the specification
               could not be applied. THE PLATFORM'S FAULT, not the evidence's.

THE TWO PASSES. Pass one is the seven categories that read stored figures; pass two is the four
that read what pass one produced. A pass-one category that FAILS does not stop pass two -- but
pass two is given the DIFFERENCE between a category that abstained and one that failed, in
`upstream_report` below, or it would report a platform failure as an evidence gap.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import urllib.error
import urllib.request
from typing import Any

from .. import ai_provider
from .category_posture import category_posture
from .fusion import BAND_SEVERITY, worst_band

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SPEC_DIR = REPO_ROOT / "specifications"

# The four states. Strings, because they cross the API and reach the DOM, and a reader of a
# stored row must be able to tell them apart without consulting this file.
COMPUTED = "computed"
ABSTAINED = "abstained"
OUT_OF_ORDER = "out_of_order"
FAILED = "failed"
STATES = (COMPUTED, ABSTAINED, OUT_OF_ORDER, FAILED)

#: Category key -> the specification file that defines it. A category absent from this mapping
#: has NO specification and is still served by the Python module layer. Run 76 wrote one.
CATEGORY_SPECIFICATIONS: dict[str, str] = {
    "A1": "A1_cost_and_evm.md",
    "A2": "A2_schedule_performance.md",
    "A3": "A3_cost_risk.md",
    "A4": "A4_document_derived_signals.md",
    "A6": "A6_delivery_quality.md",
    "B1": "B1_signal_synthesis.md",
    "B2": "B2_evidence_combination.md",
    "B3": "B3_regulatory_authority.md",
    "B4": "B4_decision_optimisation.md",
    "C1": "C1_data_integrity.md",
}

#: The ten project-level categories, in the two passes the order names.
#:
#: RUN 96 REMOVED A5 SYSTEMS AND DYNAMICS FROM PASS ONE. Run 95 emptied the category and Run 96
#: removed its eight retired rows from the registry, so A5 no longer exists as a category at
#: all: dispatching it could only ever have produced a slot with nothing in it. Its
#: specification file went with the rows.
#:
#: HOW THE SPLIT WAS DERIVED, because the order names the categories by ordinal position rather
#: than by key. The taxonomy holds TWELVE entries; D1 Portfolio Health is portfolio-level and is
#: excluded from every project surface by `projectCats()` in detail.js, leaving ELEVEN, which is
#: the number the order states. Ordinals 1 to 7 are the categories that read STORED FIGURES:
#: A1 to A6 and C1 Data Integrity. Ordinals 8 to 11 are the four that read what those produced:
#: B1 Signal Synthesis fuses statuses, B2 Evidence Combination asks how complete the evidence
#: was, B3 Regulatory and B4 Decision Optimization act on a status already formed.
PASS_ONE: tuple[str, ...] = ("A1", "A2", "A3", "A4", "A6", "C1")
PASS_TWO: tuple[str, ...] = ("B1", "B2", "B3", "B4")
ALL_CATEGORIES: tuple[str, ...] = PASS_ONE + PASS_TWO


class SpecApplicationError(RuntimeError):
    """The call could not be made, or its answer could not be read. Always state FAILED."""


# --------------------------------------------------------------------------- specifications


def specification_path(category_key: str) -> pathlib.Path | None:
    name = CATEGORY_SPECIFICATIONS.get(category_key)
    return (SPEC_DIR / name) if name else None


def has_specification(category_key: str) -> bool:
    p = specification_path(category_key)
    return bool(p and p.is_file())


def load_specification(category_key: str) -> str:
    p = specification_path(category_key)
    if p is None:
        raise SpecApplicationError(
            f"No specification is registered for category {category_key}, so it cannot be "
            f"applied. This category is still served by the Python module layer.")
    if not p.is_file():
        raise SpecApplicationError(
            f"The specification registered for category {category_key} is not on disk at "
            f"{p}, so it cannot be applied.")
    return p.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- the prompt


PROMPT_PREAMBLE = """You are applying a written specification to a project's stored figures.

The specification below defines every module in one category. Apply each module's stated method
to the figures supplied, and report what each one reads.

RULES, and they are not negotiable:

1. Use ONLY the figures supplied. Never substitute, estimate or infer a figure that is absent.
2. Where the specification states a formula, compute it at FULL PRECISION and derive the band
   from the full-precision value. Round for display only, after the band is decided.
3. Where the specification records a module as BANDLESS, report the value with "band": null and
   "band_asserted": false. Do not invent a band.
4. Where a module's abstention condition is met, report state "abstained" and quote the
   specification's exact abstention words. Do not paraphrase them.
5. Do not decide any category status or project status. That is not your work.

Answer with JSON only, no prose around it, in exactly this shape:

{"modules": [
  {"module_id": "A1.7", "state": "computed", "value": 0.9981051867436896,
   "display": "0.998", "band": "Green", "band_asserted": true,
   "evidence_metric": "...", "reason": null},
  {"module_id": "A1.3", "state": "abstained", "value": null, "display": null,
   "band": null, "band_asserted": false, "evidence_metric": null,
   "reason": "the exact abstention words from the specification"}
]}

"state" is one of "computed" or "abstained" only. You do not report "out_of_order" or "failed";
those are decided by the platform, not by you.
"""


#: Run 84. Fields carried in EVERY call regardless of whether the category's specification
#: names them. `evidenceQualification` gates sixteen modules across A6, B1, B2, B3 and B4
#: (measured in the Run 83 scan: 16/16 refuse when it is absent); carrying it everywhere is
#: cheap and removes the one dependency the name-derived scope could miss.
ALWAYS_CARRIED: tuple[str, ...] = ("evidenceQualification",)


def scope_signal_inputs(spec_text: str, signal_inputs: dict) -> dict:
    """
    Run 84. THE FIGURES A CALL CARRIES ARE THE FIGURES ITS SPECIFICATION NAMES.

    Before this, every category call serialized the ENTIRE signal_inputs dict -- one hundred
    plus fields and the full `sources` provenance block -- into every prompt, when a category
    reads a handful. The scope is DERIVED from the specification text at call time, never
    hand-maintained: a top-level field is carried when the specification names it in backticks
    (Run 77 wrote every input, governed path and corpus-assembled path name that way), plus
    ALWAYS_CARRIED. No specification names `sources`, so provenance is not carried.

    A field the specification names that the store does not hold is simply absent from the
    scoped dict, exactly as it was absent from the full dict: the specification's own contract
    is abstention on absence, and the prompt states the scoping so absence is never read as
    withholding.
    """
    if not isinstance(signal_inputs, dict):
        return signal_inputs
    return {k: v for k, v in signal_inputs.items()
            if k in ALWAYS_CARRIED or f"`{k}`" in spec_text}


def build_prompt(category_key: str, spec_text: str, signal_inputs: dict,
                 upstream_report: dict | None = None) -> str:
    scoped = scope_signal_inputs(spec_text, signal_inputs)
    parts = [PROMPT_PREAMBLE,
             f"\n=== SPECIFICATION FOR CATEGORY {category_key} ===\n",
             spec_text,
             "\n=== THE STORED FIGURES FOR THIS PROJECT AND PERIOD ===\n",
             "Only the stored fields this category's specification names are supplied. "
             "A field the specification names that does not appear here is not held by the "
             "store for this project and period; the module that wants it abstains.\n",
             json.dumps(scoped, sort_keys=True, indent=1, default=str)]
    if upstream_report:
        parts += [
            "\n=== WHAT THE UPSTREAM CATEGORIES PRODUCED ===\n",
            "Each entry says what happened to one upstream category. 'abstained' means the "
            "evidence was not there, which is a real answer about the evidence. 'failed' means "
            "the platform could not apply that category, which says NOTHING about the evidence "
            "and must not be reported as an evidence gap.\n",
            json.dumps(upstream_report, sort_keys=True, indent=1, default=str)]
    return "".join(parts)


# --------------------------------------------------------------------------- the clients


# Run 93: the endpoint, the key, the authentication header, the request shape and the model
# identifier all moved to `app.ai_provider`, which is the one boundary where a provider's
# differences live. These names remain because the module's own tests and tools import them; the
# live path no longer reads them.
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
# RUN 113. DERIVED FROM THE PROVIDER TABLE, NEVER RESTATED. Runs 93-112 left this a
# LITERAL COPY of the Anthropic default, so when Run 113 repointed the table this line
# would have silently gone stale -- a second, wrong answer to the question 'what model'.
# It is now the SAME OBJECT the table holds, so the divergence class cannot recur.
SPEC_MODEL = ai_provider.PROVIDERS["anthropic"]["models"]["spec"]
MAX_TOKENS = 8192
REQUEST_TIMEOUT_S = 180


class ProviderSpecApplier:
    """
    One HTTPS POST per category, through whichever provider is configured. The live path.
    Stateless, safe to share across threads.

    IT DOES NOT KNOW WHICH PROVIDER ANSWERED and neither does anything downstream of it, beyond
    the `provider` and `model_id` it reports so the reading can be stamped. Endpoint, header,
    request shape, response shape and refusal wording are all handled in `ai_provider`.
    """

    served_by = "model"

    def __init__(self, client) -> None:
        self._client = client

    @property
    def provider(self) -> str:
        return self._client.provider

    @property
    def model_id(self) -> str:
        return self._client.model_id

    def apply(self, category_key: str, prompt: str) -> str:
        try:
            return self._client.complete(
                [{"type": "text", "text": prompt}], max_tokens=MAX_TOKENS, temperature=0.0)
        except ai_provider.ProviderCallError as exc:
            # Surfaced as the platform's own error type, with the provider named inside it.
            raise SpecApplicationError(str(exc)) from None


# Kept as the historic name for the Anthropic boundary.
AnthropicSpecApplier = ProviderSpecApplier


class RecordedSpecApplier:
    """
    THE STUB, AND WHAT IT IS AND IS NOT.

    There is no `ANTHROPIC_API_KEY` in the verification environment, so the live path above cannot
    be exercised here. This serves RECORDED answers keyed by the sha256 of the prompt, exactly as
    `extraction_client.StubExtractor` serves recorded extractions, and REFUSES anything it has not
    been given.

    IT IS NOT A MODEL AND IT IS NOT EVIDENCE ABOUT ONE. It is deterministic by construction, so
    running the section-8 variance measurement against it measures THE HARNESS and returns zero
    variance no matter what a model would do. Every result it serves is stamped
    `served_by: "recorded"` so that no reader, and no report, can mistake one for a live reading.
    """

    served_by = "recorded"
    model_id = "recorded-fixture"
    # Run 93. Not a provider name: the honest statement that no provider was asked.
    provider = "recorded"

    def __init__(self, recorded: dict[str, str]) -> None:
        self._recorded = dict(recorded or {})

    @staticmethod
    def key_for(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def apply(self, category_key: str, prompt: str) -> str:
        key = self.key_for(prompt)
        if key in self._recorded:
            return self._recorded[key]
        # RUN 100. THE BARE CATEGORY KEY IS NOT CONSULTED, AND ITS REMOVAL IS THE POINT.
        #
        # This used to fall back to `self._recorded[category_key]`, which returned the recorded
        # A1 answer for ANY figures whatsoever: a project 100% complete and a project 25%
        # complete were measured receiving the identical posture, because the only thing the
        # lookup asked was "is this category A1". A recorded answer is a reading taken against
        # SPECIFIC FIGURES, and served against different ones it is not reproducibility, it is
        # a fabricated answer wearing a real one's clothes.
        #
        # The prompt sha256 above IS the figures: the prompt carries them, so an exact hash match
        # is exactly the guarantee "this answer was recorded against these figures". Anything
        # else abstains, with the reason stated, in the same words the categories that hold no
        # recorded answer at all already use. The recorded path exists for reproducibility and
        # may not stand in for a model.
        raise SpecApplicationError(
            f"no recorded answer is held for category {category_key} on these figures "
            f"(prompt sha256 {key[:16]}), and there is no model key in this environment to ask. "
            f"Nothing is invented in its place.")


def build_applier(recorded: dict[str, str] | None = None):
    """
    The configured provider's applier if its key is present, otherwise the recorded one.
    Never both, never a guess, and NEVER a different provider than the one configured.

    A configured provider whose key is missing is a deliberate, visible downgrade to the
    recorded applier ONLY in a keyless verification environment, exactly as before -- and every
    row it serves is stamped served_by "recorded", so no reader can mistake it for a model.
    """
    cfg = ai_provider.load_provider("spec")
    if cfg.key_present():
        return ProviderSpecApplier(
            ai_provider.build_client(cfg, timeout_s=REQUEST_TIMEOUT_S))
    return RecordedSpecApplier(recorded or {})


def require_applier():
    """
    The configured provider or a LOUD failure. No recorded fallback.

    `build_applier` keeps the keyless verification path alive; this is the entry point for
    anything that must be a real model call, and it raises ProviderNotConfigured naming the
    provider and the variable that was empty.
    """
    cfg = ai_provider.load_provider("spec")
    return ProviderSpecApplier(ai_provider.build_client(cfg, timeout_s=REQUEST_TIMEOUT_S))


# --------------------------------------------------------------------------- reading the answer


def parse_answer(text: str) -> list[dict]:
    """The model's JSON, or SpecApplicationError. A fenced block is unwrapped first."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else ""
        if raw.rstrip().endswith("```"):
            raw = raw.rstrip()[: -3]
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise SpecApplicationError("the answer carried no JSON object")
    try:
        parsed = json.loads(raw[start:end + 1])
    except ValueError as exc:
        raise SpecApplicationError(f"the answer is not valid JSON: {exc}") from None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("modules"), list):
        raise SpecApplicationError("the answer carried no 'modules' list")
    return parsed["modules"]


def normalise_module(row: Any) -> dict:
    """One module's row, in the shape every surface downstream reads. Unusable rows FAIL."""
    if not isinstance(row, dict):
        raise SpecApplicationError("a module row was not an object")
    module_id = str(row.get("module_id") or "").strip()
    if not module_id:
        raise SpecApplicationError("a module row carried no module_id")
    state = str(row.get("state") or "").strip().lower()
    if state not in (COMPUTED, ABSTAINED):
        raise SpecApplicationError(
            f"{module_id} reported state {state!r}; a specification may report only "
            f"'computed' or 'abstained'")
    band = row.get("band")
    if band is not None:
        band = str(band)
        # A band the fusion rule cannot rank is not silently ranked. A1.2 legitimately emits
        # lower case, so the comparison is on the capitalised form and the emitted spelling is
        # preserved exactly as the specification records it.
        if band.capitalize() not in BAND_SEVERITY:
            raise SpecApplicationError(
                f"{module_id} reported band {band!r}, which is not one of "
                f"{sorted(BAND_SEVERITY)}")
    if state == ABSTAINED and not str(row.get("reason") or "").strip():
        raise SpecApplicationError(f"{module_id} abstained without stating what it wants")
    return {
        "module_id": module_id,
        "state": state,
        "value": row.get("value"),
        "display": row.get("display"),
        "band": band,
        "band_asserted": bool(row.get("band_asserted")) and band is not None,
        "evidence_metric": row.get("evidence_metric"),
        "reason": row.get("reason"),
    }


# --------------------------------------------------------------------------- one category


def apply_category(category_key: str, signal_inputs: dict, applier=None,
                   upstream_report: dict | None = None,
                   missing_upstream: list[str] | None = None) -> dict:
    """
    Apply one category's specification to one project-period's figures.

    Returns a row carrying, always: the category, its four state counts, its fused status, and
    the modules. NEVER RAISES: a failure is a FAILED row, because a category that blows up must
    leave the other ten intact (order section 2, reason 1).
    """
    base: dict[str, Any] = {
        "category": category_key,
        "state": None, "status": None, "served_by": None, "model_id": None,
        # Run 93. WHICH PROVIDER answered, beside which model. A figure from one model and a
        # figure from another are not the same evidence.
        "provider": None,
        "modules": [],
        "counts": {COMPUTED: 0, ABSTAINED: 0, OUT_OF_ORDER: 0, FAILED: 0},
        "reason": None,
        "missing_upstream": list(missing_upstream or []),
    }

    # OUT OF ORDER IS DECIDED BEFORE THE CALL, and it is not a failure. The specification could
    # have applied; the upstream categories have not run. Pressing again after they have run
    # should compute it.
    if missing_upstream:
        base["state"] = OUT_OF_ORDER
        base["counts"][OUT_OF_ORDER] = 1
        base["reason"] = (
            "This category reads what the categories before it produced, and "
            + ", ".join(sorted(missing_upstream))
            + (" has not run yet." if len(missing_upstream) == 1 else " have not run yet.")
            + " Run them and press this again.")
        return base

    try:
        spec_text = load_specification(category_key)
        applier = applier or build_applier()
        prompt = build_prompt(category_key, spec_text, signal_inputs, upstream_report)
        base["served_by"] = getattr(applier, "served_by", "unknown")
        base["model_id"] = getattr(applier, "model_id", None)
        base["provider"] = getattr(applier, "provider", None)
        answer = applier.apply(category_key, prompt)
        rows = [normalise_module(r) for r in parse_answer(answer)]
    except SpecApplicationError as exc:
        base["state"] = FAILED
        base["counts"][FAILED] = 1
        base["reason"] = str(exc)
        return base
    except Exception as exc:  # noqa: BLE001 -- a category failure must not stop the others
        base["state"] = FAILED
        base["counts"][FAILED] = 1
        base["reason"] = f"{type(exc).__name__}: {exc}"
        return base

    base["modules"] = rows
    for r in rows:
        base["counts"][r["state"]] += 1
    base["state"] = COMPUTED if base["counts"][COMPUTED] else ABSTAINED
    # FUSION IS PYTHON AND STAYS PYTHON. Only modules that actually spoke, and only bands the
    # rule can rank: an abstention is an absence of a reading, not an adverse one.
    # RUN 104. THE POSTURE RULE IS `category_posture` and it is the SAME function the Python
    # rollup and `spec_projection` call: A1, A2, A3 and A4 average their banded modules' scores,
    # A6 takes the worst, and a category the owner did not assign keeps worst-wins. Only modules
    # that actually spoke, and only bands the vocabulary can rank: an abstention is an absence of
    # a reading, not an adverse one, and it is not a zero in the average either.
    #
    # THE ARITHMETIC IS NOT STORED ON THE READING. `SpecificationReading` has fixed columns and
    # this run adds no migration; `spec_projection.category_statuses` recomputes the posture from
    # the stored module rows by this same function, so the working is served without a column.
    posture = category_posture(
        category_key,
        [(r.get("module_id"), r["band"]) for r in rows
         if r["state"] == COMPUTED and r["band"] is not None],
        # RUN 105, GOAL THREE. This call site filters to the banded modules, so the count of
        # modules the category actually produced is passed explicitly.
        modules_in_category=len(rows))
    base["status"] = posture["status"]
    base["posture_rule"] = posture["posture_rule"]
    base["posture_arithmetic"] = posture["posture_arithmetic"]
    base["posture_single_reading"] = posture["posture_single_reading"]
    base["posture_thinness_words"] = posture["posture_thinness_words"]
    return base


# --------------------------------------------------------------------------- the two passes


def upstream_state_report(pass_one_rows: dict[str, dict]) -> dict:
    """
    What pass two is told about pass one, and the WHOLE POINT of it is that a category that
    ABSTAINED and one that FAILED are distinguishable here. C8's job is to say how complete the
    evidence was; handed a failure as an absence it would report a platform fault as an evidence
    gap.
    """
    report: dict[str, dict] = {}
    for key in PASS_ONE:
        row = pass_one_rows.get(key)
        if row is None:
            report[key] = {"state": "not_run",
                           "means": "this category was not called at all"}
            continue
        state = row.get("state")
        report[key] = {
            "state": state,
            "status": row.get("status"),
            "counts": row.get("counts"),
            "means": {
                COMPUTED: "this category read the evidence and produced findings",
                ABSTAINED: ("the evidence for this category is not there. This IS a statement "
                            "about the evidence."),
                OUT_OF_ORDER: "this category is itself waiting on categories before it",
                FAILED: ("the platform could not apply this category. This says NOTHING about "
                         "the evidence and must not be counted as an evidence gap."),
            }.get(state, "unknown"),
        }
    return report


def run_two_pass(signal_inputs: dict, applier=None,
                 categories: tuple[str, ...] | None = None) -> dict:
    """
    The full run. Pass one, fuse, pass two, fuse again.

    The seven and the four are independent WITHIN a pass, so a caller may run each pass's
    categories concurrently; this reference implementation runs them in order, which produces the
    identical result because no pass-one category reads another pass-one category.
    """
    wanted = set(categories or ALL_CATEGORIES)
    pass_one: dict[str, dict] = {}
    for key in PASS_ONE:
        if key in wanted and has_specification(key):
            pass_one[key] = apply_category(key, signal_inputs, applier)

    report = upstream_state_report(pass_one)
    # A pass-one category that FAILED does not stop pass two. What stops a pass-two category is
    # having NOTHING to read: no pass-one category produced a finding.
    produced = [k for k, r in pass_one.items() if r.get("state") == COMPUTED]
    missing = [] if produced else [k for k in PASS_ONE if has_specification(k)] or list(PASS_ONE)

    pass_two: dict[str, dict] = {}
    for key in PASS_TWO:
        if key in wanted and has_specification(key):
            pass_two[key] = apply_category(key, signal_inputs, applier,
                                           upstream_report=report, missing_upstream=missing)

    rows = {**pass_one, **pass_two}
    # THE PROJECT STATUS. Worst category wins, and the pass-two categories vote too. Python.
    cat_bands = [str(r["status"]) for r in rows.values() if r.get("status")]
    return {
        "categories": rows,
        "upstream_report": report,
        "project_status": worst_band(cat_bands) if cat_bands else None,
        "served_by": next((r.get("served_by") for r in rows.values() if r.get("served_by")),
                          None),
    }
