"""
RUN 143, PART 2. CARRY-FORWARD: THE SINGLE AUTHORITY.

THE STANCE THIS FILE ENACTS, AND IT REVERSES ONE THIS PLATFORM HELD IN WRITING.

Until sim-2026.09-v71 a module that abstained published nothing, and said so: "no reading is
reported and no other figure is used in its place." The owner has withdrawn that promise. A
module that abstains in the current period now DISPLAYS AND VOTES WITH its most recent earlier
banded reading from the same project. Both display and voting.

THE RULE, in the owner's order:

  1. A module that produced a band this period uses it. Nothing changes.
  2. A module that abstained or produced no band looks back through EARLIER PERIODS OF THE SAME
     PROJECT for its most recent reading that carried a band, and uses that.
  3. With no earlier banded reading it remains unassessed, exactly as it is today.

A carried reading counts toward its category posture and therefore toward the project status,
exactly as a current reading would. That needed no arithmetic change: `category_posture` takes
(module_id, band) pairs and knows nothing else, and `project_posture` sees only the five
postures. A carried reading enters as a band.

WHAT A CARRIED READING MUST STATE, AND WHY THAT IS THE MAJORITY OF THIS WORK.

A carried reading is not a current one and must never be indistinguishable from one. The
indistinguishability is this codebase's DEFAULT, not a risk it runs: `taxonomy.js`'s
`getModuleStatus` returns `row.module_results[i].status_color` and nothing else, and every
client surface that renders a module band goes through it. Appending a carried row to
`module_results` renders it as current on every surface with no marker, no code change and no
error. So every carried row is stamped, here and nowhere else, with:

    carried              True -- the marker every surface keys on
    carried_from_period  the period it came from, NAMED. Never "the previous period": Part 1
                         supersedes periods, and after a removal those reliably differ.
    carried_from_age     how many stored periods back it is, so the age is visible where the
                         staleness gate can no longer be applied to it
    carried_evidence     that period's own evidence sentence, UNALTERED
    carried_reason       this period's abstention sentence, kept, so the reader sees both what
                         is being carried and why nothing current exists
    evidence_metric      set to the carried sentence prefixed with a plain-language statement
                         that it is carried and from where, so even a surface that reads only
                         this field cannot show it as current

WHAT CARRY-FORWARD MUST NOT DO, and how each is enforced here:

  1. IT DOES NOT CROSS PROJECTS. The look-back is handed rows for one project only; the caller
     scopes the query. `select_carried` never sees another project's rows.
  2. IT DOES NOT CARRY AN ABSTENTION. `_banded` is a BAND TEST, not a presence test: the value
     must capitalise into `fusion.BAND_SEVERITY`. `registry.record` routes calibration-pending
     rows into `computed` with `status_color = None`, and those are readings without bands.
  3. IT DOES NOT CARRY ACROSS A REMOVED PERIOD'S GAP IMPROPERLY, and needs no gap logic to
     avoid it. Removal supersedes rather than deletes and every surface filters
     `superseded_by IS NULL`, so a removed period is invisible to the look-back, which skips
     to the most recent live earlier period. That is why the label names its period.
  4. IT DOES NOT RESURRECT A RETIRED MODULE. Run 96 deleted 51 modules from the registry, but
     pre-Run-96 stored rows STILL HOLD THOSE IDS WITH THEIR BANDS. The look-back never
     dispatches, so `MissingModuleError` never fires and the violation would be silent. The
     candidate set is INTERSECTED with `registry.service_index()`.
  5. IT DOES NOT APPLY where the abstention is a statement about THIS period's evidence quality
     rather than a missing input. See EXEMPT below.
  6. IT DOES NOT SILENTLY CHANGE A PERIOD'S OWN RECORD. `select_carried` returns NEW rows. The
     caller appends them to `computed` and LEAVES `abstained` UNTOUCHED, so the stored result
     still records what that period's evidence produced, with the carried reading recorded
     alongside it and not replacing it. The module appears in both lists, deliberately.

WHAT IS EXEMPT, AND IT IS PER ARM, NOT PER MODULE.

Keying exemption on module id alone gets A6.2, A1.5 and A1.2 wrong: each has arms that are a
missing input (carry) and arms that are a judgment about this period's evidence (do not carry).
So exemption is decided three ways, in this order:

  a. THE FAILURE PATH. `registry.py`'s containment guard promises of a module that raised:
     "NOTHING IS SUBSTITUTED for the missing reading -- no default, no band, no last-known
     value." That promise is KEPT. A module that crashed must never carry, because a carried
     band over a crash would report a defect as a reading.
  b. A REASON CODE, where the arm already carries one. Only the FAILURE code is here.

     RUN 144, RULING 1 -- THE CATEGORY-9 EXCLUSION IS LIFTED, BY THE OWNER, ON THE MECHANISM.
     Run 143 excluded `CATEGORY9_ASSESSMENT_MISSING` conservatively and reported it. It is now
     removed, and the reason is what the code at the refusal site actually does rather than
     what the code's name suggests. There are TWO Category-9 refusal paths in
     `qualification_boundary.py` and they carry DIFFERENT reason codes:

       `CATEGORY9_ASSESSMENT_MISSING` (`_refuse_missing`, :299) fires when `ev is None` --
       when NOTHING WAS EVER ASSESSED. It sets `qualification_state = UNASSESSED` and
       `consumer_executed = False`, and it is built on the same `insufficient(...)` primitive
       every missing-input module uses. Nothing was degraded, nothing was judged unfit,
       nothing was rejected: the gate never got a verdict to give. That is the MISSING-INPUT
       shape, which is exactly what the owner's stance says should carry. Lifting it does not
       let a degraded reading vote as a full one, because a degraded reading never reaches
       this code at all.

       `evidence_not_qualified_for_use` (`_refuse`, :309) fires when evidence EXISTS and the
       gate judged it not qualified for the use. THAT is the refusal a carried band would
       defeat, and it is a different code.

     Being unassessed is not the same as being found wanting, and only the second is a
     judgment about this period's evidence.

     RUN 145 RULING -- `evidence_not_qualified_for_use` IS ADDED, one entry in the same set
     ruling 1 removed one from. Run 144 found that the second code was carry-eligible while
     its own refusal sentence promised verbatim that "No earlier reading is carried forward in
     its place either: the refusal is about whether this evidence may be used at all, not
     about a missing input." The code did not keep that promise, and the leak was ACTIVE, not
     latent: one material conflict between two equal-precedence documents puts A6.1-A6.4,
     B1.1 and B1.2 on this code, and the four A6 rows -- Delivery Quality Performance, the
     category that gates the fifth vote -- each carried an earlier Green while the sentence on
     the same ledger denied anything was carried. The sentence was right; the behaviour moved.

  c. A DECLARATION AT THE ARM, `carry_forward_eligible=False` on the module's own returned
     dict. This is how the per-arm cases are handled, and it is deliberately NOT a match on
     the sentence text: sentences are being rewritten by this very run, and an exclusion that
     drifts when someone reworded a sentence would fail open, publishing a stale band exactly
     where the arm refused to publish a current one.

  Plus three whole modules, by id:

    C1.5  Information Completeness Ratio can never band at all (`models_cat89` returns four
          Nones), and its abstention sentence is indistinguishable from every other
          structure-absent module's, so the id is the only safe key.
    B1.1  a synthesis of THIS period's other module readings. Its own rule is that incomplete
          evidence cannot be calmer than Amber; a carried Green defeats it exactly.
    B1.2  deleted and rewritten by `compute.py` from the very postures carry-forward changes.

THE ORDERING KEY. Most recent first, and deterministic:

    ORDER BY period DESC, computed_at DESC, result_id DESC

`result_id` is a ULID and is the total tiebreak; `computed_at` alone is not, being a server
default two rows can share.

THE HORIZON, DECIDED. RUN 144 RULING 3: THERE IS NONE, AND THAT IS THE OWNER'S RULING, NOT THIS
FILE'S SILENCE. A reading carries from ANY earlier period of the same project. Two options were
put and both were rejected: a horizon derived from contract duration and approved extensions,
rejected as complexity without benefit; and a fixed 60-month cap, rejected because it can never
bind on any project this platform will carry, and a limit that cannot fire looks like a
safeguard while being none -- the exact shape of defect this codebase keeps finding.

SO THE AGE CARRIES THE WEIGHT INSTEAD, and that makes the age the WHOLE mechanism rather than a
note beside one. The staleness gate (`qualification_gate`) refuses stale EVIDENCE; a carried
READING is re-admitted to a later period without the gate seeing it again, so `carried_from_age`
is the only place that judgment can still be made -- by the reviewer. Every carried row surfaces
it, the caller surfaces the oldest in `project_status_basis`, and every surface that shows a
carried reading states the DISTANCE and not merely the source period, without a click and
without a hover. Nothing attaches a threshold, a warning or a colour change to any value of it:
the age is stated at every value and the reviewer judges it.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .fusion import BAND_SEVERITY
from .qualification_boundary import ABSTAIN_UNQUALIFIED
from .registry import MODULE_FAILED_CODE, service_index

__all__ = [
    "CARRIED_KEYS",
    "carry_candidates",
    "NEVER_CARRY_MODULES",
    "NEVER_CARRY_REASON_CODES",
    "carried_sentence",
    "is_carry_eligible",
    "normalise_band",
    "select_carried",
]

#: The three modules exempted by id, for the reasons in the docstring.
NEVER_CARRY_MODULES: frozenset[str] = frozenset({"C1.5", "B1.1", "B1.2"})

#: Reason codes whose abstention is a refusal about this period's evidence, not a missing input.
#: `module_execution_failed` keeps `registry.py`'s written promise: a module that crashed gets no
#: default, no band and no last-known value. RUN 144 RULING 1 removed
#: `CATEGORY9_ASSESSMENT_MISSING` from this set -- see WHAT IS EXEMPT (b) above; that code means
#: nothing was ever assessed, which is a missing input, not a refusal.
#: RUN 145 RULING added `evidence_not_qualified_for_use` (`ABSTAIN_UNQUALIFIED`, the code
#: `_refuse` writes when evidence EXISTS and the gate judged it unfit for this use). Its own
#: refusal sentence already promises verbatim that "No earlier reading is carried forward in its
#: place either", and until this entry existed the code did not keep that promise. The sentence
#: is right and the behaviour was wrong, so the behaviour moved. Note the literal is imported
#: from `qualification_boundary` rather than from `qualification_contract`: `CONTRACT_MISSING`
#: and `CONFIGURATION_MISSING` there share one string but are a reason code and a lookup
#: sentinel respectively, and neither is this one.
NEVER_CARRY_REASON_CODES: frozenset[str] = frozenset({
    MODULE_FAILED_CODE,
    ABSTAIN_UNQUALIFIED,
})

#: Every key this layer writes onto a carried row. Surfaces key on `carried`; the rest is what
#: the row must state. Exported so a check can assert no surface invents a carried field.
CARRIED_KEYS: tuple[str, ...] = (
    "carried",
    "carried_from_period",
    "carried_from_age",
    "carried_evidence",
    "carried_reason",
    "carried_source",
    "period_record",
)

#: The words that open a carried reading's evidence sentence. A surface that reads only
#: `evidence_metric` -- the export's flat column, a chart tooltip, a copied line -- still cannot
#: present it as current. `{period}` is the period the reading came from, named.
CARRIED_PREFIX = "Carried from {period}: this measure produced no reading from this period's evidence, so its most recent earlier reading is shown and is voting. That reading, from {period}, said: "


def normalise_band(value: Any) -> str | None:
    """
    The band a stored value asserts, or None.

    THIS IS A BAND TEST, NOT A PRESENCE TEST, and that distinction is the whole of trap one. A
    calibration-pending row sits in `computed` with `status_color = None`: it is a reading, and
    it has no band, and it must not carry. Capitalisation matches `category_posture`'s own test
    exactly, so a band this function accepts is a band the posture arithmetic will score.
    """
    if value is None:
        return None
    band = str(value).capitalize()
    return band if band in BAND_SEVERITY else None


def is_carry_eligible(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    """
    May this abstention carry? Returns (eligible, exemption_reason).

    `row` is an entry from `run["abstained"]` (registry.run_all), or a spec-projection
    abstention row. The three tests are in the order of the docstring: the failure path first,
    because a crash must never be reported as a reading whatever else the row says.
    """
    if row.get("module_failed"):
        return False, "the module failed while computing; a failure is never substituted for"
    code = row.get("abstention_reason_code")
    # RUN 144 RULING 1, THEN RUN 145. Every code in this set brings ITS OWN WORDS, so a reader
    # is never told a module crashed when it did not, nor that evidence was judged unfit when
    # nothing was ever assessed. The trailing generic sentence covers a code added to the set
    # without one; adding a code without adding its words here is a defect, not a shortcut.
    if code and code in NEVER_CARRY_REASON_CODES:
        if code == MODULE_FAILED_CODE:
            return False, "the module failed while computing; a failure is never substituted for"
        if code == ABSTAIN_UNQUALIFIED:
            return False, ("the gate judged this period's evidence not qualified for this use, "
                           "so no reading is taken from it and no earlier reading is carried "
                           "forward in its place: the refusal is about whether this evidence may "
                           "be used at all, not about a missing input")
        return False, ("this abstention states a judgment about this period's evidence, not a "
                       "missing input, so no earlier reading answers it")
    if row.get("carry_forward_eligible") is False:
        return False, (row.get("carry_forward_ineligible_reason")
                       or "this abstention states a judgment about this period's evidence, not "
                          "a missing input, so no earlier reading answers it")
    if row.get("module_id") in NEVER_CARRY_MODULES:
        return False, _NEVER_CARRY_WORDS[row["module_id"]]
    return True, None


_NEVER_CARRY_WORDS: dict[str, str] = {
    "C1.5": ("this measure reports the completeness of THIS period's information and can never "
             "carry a band, so there is no earlier reading to carry"),
    "B1.1": ("this measure is a synthesis of this period's other readings; carrying an earlier "
             "band would defeat its own rule that incomplete evidence cannot read calmer than "
             "Amber"),
    "B1.2": ("this measure is a weighted vote over this period's category postures and is "
             "recomputed from them, so an earlier band is not an input it can take"),
}


def carried_sentence(period: str, evidence: str | None) -> str:
    """The evidence sentence a carried row publishes: the marker, the period, then the original."""
    original = (evidence or "").strip()
    if not original:
        original = ("that period's reading was stored without an evidence sentence, so none is "
                    "shown and none is written here in its place.")
    return CARRIED_PREFIX.format(period=period) + original


def _prior_index(prior_periods: Sequence[Mapping[str, Any]]) -> list[tuple[Any, dict[str, Any]]]:
    """
    Flatten the caller's prior periods into (period, module_row) pairs, most recent first.

    `prior_periods` is the caller's already-ordered list of live earlier periods for ONE project.
    Each element is {"period": ..., "modules": [...]}. The caller does the SQL:

        WHERE project_id = :pid AND period < :current AND superseded_by IS NULL
        ORDER BY period DESC, computed_at DESC, result_id DESC

    and the caller normalises a `specification_readings` row through
    `spec_projection.module_rows` rather than re-deriving it, so both stores arrive here in the
    one shape. This function re-sorts defensively by period descending only where the caller
    supplied a sortable period, and otherwise trusts the caller's order, because the caller is
    the only layer that can see `computed_at` and `result_id`.
    """
    out: list[tuple[Any, dict[str, Any]]] = []
    for p in prior_periods:
        period = p.get("period")
        for m in (p.get("modules") or ()):
            if isinstance(m, Mapping) and m.get("module_id"):
                out.append((period, dict(m)))
    return out


def carry_candidates(run: Mapping[str, Any]) -> list[dict[str, Any]]:
    """
    Every module in this period that is a candidate to carry, from BOTH buckets.

    THE ORDER SAYS "abstained OR PRODUCED NO BAND", and those are two different buckets in this
    layer. `registry.record` routes a CALIBRATION-PENDING row -- the canonical method ran and
    produced a figure, and only the colour is withheld -- into `computed` with
    `status_color = None`. A6.2's exposure-floor arm and its near-miss-healthy arm land there,
    not in `abstained`. A carry step that read `abstained` alone would silently do nothing for
    them, and would also have made this run's per-arm exclusions dead code, which is how a
    conservative-looking build passes its own test and ships the defect.

    `origin` records which bucket the candidate came from, because the two are handled
    differently downstream: an abstention keeps its own entry in `abstained` and the carried
    reading is APPENDED to `computed`, while a bandless computed row is REPLACED by the carried
    reading, which embeds it verbatim in `period_record`. Either way the period's own record is
    stored in full and is not overwritten, which is rule 6.
    """
    out: list[dict[str, Any]] = []
    for entry in (run.get("abstained") or ()):
        row = dict(entry)
        row["_origin"] = "abstained"
        out.append(row)
    for entry in (run.get("computed") or ()):
        if normalise_band(entry.get("status_color")) is not None:
            continue
        row = dict(entry)
        row["_origin"] = "computed_bandless"
        row.setdefault("reason", entry.get("evidence_metric"))
        out.append(row)
    return out


def select_carried(abstained: Iterable[Mapping[str, Any]],
                   prior_periods: Sequence[Mapping[str, Any]],
                   *, in_service: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """
    The carried readings for one project-period. Returns NEW rows for `computed`.

    The caller appends these to `run["computed"]` and LEAVES `run["abstained"]` UNTOUCHED, which
    is rule 6: the period's own record still says what its evidence produced.
    """
    service = set(in_service) if in_service is not None else set(service_index())
    flat = _prior_index(prior_periods)
    # Age is measured in stored live periods, oldest-agnostic: the position of the source period
    # in the caller's ordered list, one-based. After a removal the removed period is not in the
    # list and does not count, which is the honest answer -- it is not the project's record.
    period_order: list[Any] = []
    for p in prior_periods:
        if p.get("period") not in period_order:
            period_order.append(p.get("period"))

    carried: list[dict[str, Any]] = []
    for row in abstained:
        module_id = row.get("module_id")
        if not module_id:
            continue
        eligible, _why = is_carry_eligible(row)
        if not eligible:
            continue
        # RULE 4. The retired-module guard, and it must be here rather than left to a dispatch
        # that never happens. A pre-Run-96 stored row holds a retired module's id and its band.
        if module_id not in service:
            continue
        for period, prior in flat:
            if prior.get("module_id") != module_id:
                continue
            band = normalise_band(prior.get("status_color", prior.get("band")))
            if band is None:
                # A reading without a band -- a calibration-pending row, or that period's own
                # abstention if the caller supplied one. Keep looking further back; an
                # unbanded reading is not "the most recent banded reading".
                continue
            new = dict(prior)
            new["module_id"] = module_id
            new["status_color"] = band
            new["carried"] = True
            new["carried_from_period"] = period
            new["carried_from_age"] = (period_order.index(period) + 1
                                       if period in period_order else None)
            new["carried_evidence"] = prior.get("evidence_metric")
            new["carried_reason"] = row.get("reason")
            new["carried_source"] = prior.get("source") or "computed_results"
            # RULE 6, ON THE ROW ITSELF. What THIS period's evidence produced, stored verbatim
            # beside the carried reading rather than replaced by it. For an abstention this
            # duplicates the entry that stays in `abstained`; for a bandless computed row, whose
            # place in `computed` the carried row takes, it is the ONLY copy and is why nothing
            # is lost by the replacement.
            new["period_record"] = dict(row)
            new["period_record"].pop("_origin", None)
            new["carried_origin"] = row.get("_origin") or "abstained"
            new["evidence_metric"] = carried_sentence(str(period),
                                                      prior.get("evidence_metric"))
            # A carried row is not this period's vote on anything but its band. Anything that
            # asserts freshness is dropped rather than replayed: the seed belonged to another
            # period's random stream, and the qualification record was written against another
            # period's evidence package.
            for stale in ("seed", "qualification", "gate_report", "computed_at", "result_id"):
                new.pop(stale, None)
            carried.append(new)
            break
    carried.sort(key=lambda r: str(r["module_id"]))
    return carried
