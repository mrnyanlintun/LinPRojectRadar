"""
THE CATEGORY-9 OPERATIONAL QUALIFICATION GATE.

WHAT SPECIFICATION 18 ASKS FOR, and it asks for an ARCHITECTURE and not a field:

    Project Evidence -> Category 9 assessment -> Qualified Evidence -> analytical use.

and it says in terms that Category 9 output is metadata and qualification, and is NOT another
independent risk vote.

WHY `qualification.py` DOES NOT ALREADY DO THIS, and why it is not being replaced. That file
answers a different and honest question: what can be said about the evidence behind one computed
period, reported as separate named dimensions with no composite score. It is deliberately inert.
Its own docstring says so: provenance, timeliness and revision resolution are METADATA, they
never gate. That inertness was the correct answer to the question Run 11 asked, and it is exactly
what the supervisory clarification now calls a failure when it is the whole story:

    a field saying qualification = unqualified while downstream code still consumes the
    numerical value normally is FAIL.

So this file adds the part that was missing: a gate whose verdict CHANGES WHAT EXECUTES. It does
not soften `qualification.py` and it invents no evidence that this repository does not have.

THE ENFORCEMENT MECHANISM, which is the whole design. A qualified signal is an OBJECT, not a
dict with a flag on it. Its band and its value are behind properties that return None unless the
verdict permits use. There is no arrangement of caller code that reads the number while ignoring
the verdict, because when the verdict refuses there is no number to read. And `fuse_qualified`
refuses a raw dict outright, so a caller cannot route around the gate by hand-building the shape
the fusion expects.

THE FOUR VERDICTS, and what each one DOES rather than what it says.

  ALLOWED    the signal may be used, including as a vote on project status.
  DEGRADED   the signal is computed and stays on the ledger, and it MAY NOT VOTE. Something
             about the evidence behind it is qualified -- it is stale against its source class's
             own freshness requirement, or its provenance is incomplete -- and the platform will
             show the finding while declining to let it move a governed status.
  ABSTAINED  no value exists. The evidence required to compute it is absent. This is the
             existing abstention behaviour, reached through the gate rather than around it.
  REJECTED   a value exists and MUST NOT BE USED AT ALL. The evidence it rests on is
             self-contradictory, out of domain, or missing a field that the audit contract makes
             noncompensatory. A rejected signal has no band, casts no vote and is reported as
             rejected rather than quietly dropped.

WHY DEGRADED IS NOT A SCORE. There is no number here, no weighting and nothing to calibrate. A
degraded signal does not vote at nine tenths of a vote; it does not vote. The alternative --
discounting a stale source by some factor -- would require a factor, and no source in this
repository establishes one.
"""

from __future__ import annotations

from typing import Any, Iterable

from .lineage import NON_PROJECT_EVIDENCE, lineage_record

#: Bumped when the SHAPE or the MEANING of a verdict changes, never for a wording change.
GATE_VERSION = "cat9-gate-v1"

ALLOWED = "ALLOWED"
DEGRADED = "DEGRADED"
ABSTAINED = "ABSTAINED"
REJECTED = "REJECTED"

VERDICTS = (ALLOWED, DEGRADED, ABSTAINED, REJECTED)

#: The verdicts under which a value may be read at all.
USABLE = frozenset({ALLOWED, DEGRADED})
#: The verdicts under which a signal may vote on a governed project status. DEGRADED is
#: deliberately absent, and that absence is the whole difference between this file and a field.
MAY_VOTE = frozenset({ALLOWED})


class RawBypassError(RuntimeError):
    """
    A caller tried to hand the fusion something that never went through the gate.

    This is an exception rather than a silent drop on purpose. A silent drop makes a bypass look
    like an abstention, and an abstention is a legitimate state; the two must not be confusable.
    """


class QualificationError(ValueError):
    """A verdict outside the vocabulary, which is never a silent default."""


class QualifiedSignal:
    """
    One analytical signal with its Category-9 verdict, its lineage, and NO WAY TO READ ITS VALUE
    AROUND THE VERDICT.

    `band` and `value` are properties, not attributes. When the verdict refuses use they return
    None. The underlying figures are kept, under names that say what they are, so a rejected
    signal can still be REPORTED as rejected with its reason -- an audit trail needs to say what
    was refused -- but nothing that consumes a band or a number can reach them by accident.
    """

    __slots__ = ("module_id", "verdict", "reasons", "lineage",
                 "unqualified_band", "unqualified_value")

    def __init__(self, module_id: str, band, value, verdict: str,
                 reasons: Iterable[str] = (), lineage: dict | None = None):
        if verdict not in VERDICTS:
            raise QualificationError(f"{module_id}: {verdict!r} is not one of {VERDICTS}")
        self.module_id = module_id
        self.verdict = verdict
        self.reasons = tuple(reasons)
        self.lineage = lineage
        self.unqualified_band = band
        self.unqualified_value = value

    @property
    def band(self):
        """The condition band, or None when the verdict does not permit its use."""
        return self.unqualified_band if self.verdict in USABLE else None

    @property
    def value(self):
        """The numeric finding, or None when the verdict does not permit its use."""
        return self.unqualified_value if self.verdict in USABLE else None

    @property
    def may_vote(self) -> bool:
        return self.verdict in MAY_VOTE and self.unqualified_band is not None

    def to_fusion_signal(self) -> dict[str, Any]:
        """
        The shape `fusion.fuse_signals` consumes. A signal that may not vote presents no status,
        so the fusion sees an abstention and it contributes no mass -- not a neutral value, which
        would be indistinguishable from a measured one.
        """
        return {"status": self.unqualified_band if self.may_vote else None,
                "module_id": self.module_id,
                "lineage": self.lineage}

    def report(self) -> dict[str, Any]:
        """The audit row: what was refused, and why. Never the band when it may not be used."""
        return {"module_id": self.module_id, "qualification": self.verdict,
                "reasons": list(self.reasons), "band": self.band,
                "may_vote": self.may_vote,
                "evidence_relationship": (self.lineage or {}).get("evidence_relationship")}

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"<QualifiedSignal {self.module_id} {self.verdict}>"


# ------------------------------------------------------------------------------ THE PREFLIGHT
#
# PROJECT EVIDENCE -> CATEGORY-9 PREFLIGHT -> ANALYTICAL MODULE. This runs BEFORE a module, on
# the evidence it declares it needs, and its verdict is what the module's own verdict starts
# from. Everything it reads is DECLARED by the evidence itself; nothing is inferred and nothing
# is assumed present. Where a field carries no as-of date, no staleness is claimed -- the
# repository does not record one, and claiming a freshness it cannot measure would be the
# fabrication this programme exists to prevent.

#: Critical, noncompensatory audit fields, specification 9.4: a missing method version, evidence
#: identity or required timestamp is not averaged away by the presence of many optional ones.
CRITICAL_AUDIT_FIELDS = ("method_version", "evidence_id", "recorded_at")


def preflight(evidence: dict, required_fields: Iterable[str], period_cutoff,
              freshness_days: dict[str, int] | None = None) -> dict[str, Any]:
    """
    Assess one project-evidence package against what a module requires.

    `evidence` carries the values under their field names, and MAY carry, under the reserved
    keys below, what it knows about itself. Everything is optional except the values, because a
    package that declares nothing must be assessed as declaring nothing rather than as clean:

      _as_of          field name -> date the value was effective
      _source_class   field name -> source class, whose freshness requirement is looked up
      _provenance     field name -> document identity the value was read from
      _conflicts      field name -> list of differing values for the SAME governed fact
      _audit          the audit record, checked against CRITICAL_AUDIT_FIELDS
      _domain         field name -> (low, high) inclusive bounds the value must lie in

    Returns a verdict and the reasons for it. A REJECTED preflight is a harder state than an
    ABSTAINED one: absent evidence means nothing can be computed, contradictory or out-of-domain
    evidence means something CAN be computed and must not be.
    """
    required = tuple(required_fields)
    reasons: list[str] = []
    verdict = ALLOWED

    def worsen(new: str) -> None:
        nonlocal verdict
        order = {ALLOWED: 0, DEGRADED: 1, ABSTAINED: 2, REJECTED: 3}
        if order[new] > order[verdict]:
            verdict = new

    as_of = evidence.get("_as_of") or {}
    source_class = evidence.get("_source_class") or {}
    provenance = evidence.get("_provenance") or {}
    conflicts = evidence.get("_conflicts") or {}
    domains = evidence.get("_domain") or {}
    audit = evidence.get("_audit")
    freshness = freshness_days or {}

    # 1. MISSING REQUIRED EVIDENCE. Nothing can be computed, so the module abstains. Zero is a
    #    value and is not missing; None and absence are.
    missing = [f for f in required if evidence.get(f) is None]
    if missing:
        worsen(ABSTAINED)
        reasons.append("required evidence absent: " + ", ".join(sorted(missing)))

    # 2. INVALID OR OUT-OF-DOMAIN VALUE. A value exists and must not be used.
    out_of_domain = []
    for f in required:
        v = evidence.get(f)
        bounds = domains.get(f)
        if v is None or bounds is None:
            continue
        low, high = bounds
        if (low is not None and v < low) or (high is not None and v > high):
            out_of_domain.append(f"{f}={v} outside [{low}, {high}]")
    if out_of_domain:
        worsen(REJECTED)
        reasons.append("out of domain: " + "; ".join(sorted(out_of_domain)))

    # 3. CONFLICTING SOURCE EVIDENCE, specification 9.6. Two source records disagree about the
    #    SAME governed fact. The platform records no revision lineage joining a document revision
    #    to the field a module reads -- qualification.py states that as NOT_ESTIMABLE -- so it
    #    genuinely cannot choose between them, and choosing silently is the failure. Rejected.
    conflicting = [f for f in required
                   if f in conflicts and len({*conflicts[f], evidence.get(f)}) > 1]
    if conflicting:
        worsen(REJECTED)
        reasons.append("source records disagree on the same governed fact, and no revision "
                       "lineage exists to resolve them: " + ", ".join(sorted(conflicting)))

    # 4. INCOMPLETE AUDIT CHAIN, specification 9.4, noncompensatory. Only assessed when an audit
    #    record is presented at all; a package that presents none is handled at 5 as missing
    #    provenance rather than being failed for a record it never claimed to have.
    if audit is not None:
        absent = [f for f in CRITICAL_AUDIT_FIELDS if not audit.get(f)]
        if absent:
            worsen(REJECTED)
            reasons.append("audit chain incomplete, critical fields absent and not compensable "
                           "by optional ones: " + ", ".join(absent))

    # 5. MISSING PROVENANCE. A value that cannot be traced to the artefact that produced it is
    #    usable and reportable, and may not move a governed status. Degraded, not rejected.
    #
    #    ASSESSED ONLY WHEN THE PACKAGE CLAIMS TO CARRY PROVENANCE AT ALL, and the distinction is
    #    load-bearing rather than a convenience. This repository records a document TYPE per
    #    sourced field and no document identity; qualification.py states that as a PARTIAL
    #    dimension and refuses to turn it into a penalty. A gate that degraded every field on
    #    every project for a provenance the platform has never recorded would not be enforcing a
    #    contract, it would be asserting a capability the repository does not have and stopping
    #    all voting as a side effect. So: a package that presents no provenance map makes no
    #    provenance claim and none is assessed; a package that presents one and omits a field is
    #    claiming provenance it does not have for that field, and that IS assessed. The same rule
    #    governs the as-of dates, the audit record, the domains and the conflicts above.
    unprovenanced = ([f for f in required
                      if evidence.get(f) is not None and not provenance.get(f)]
                     if "_provenance" in evidence else [])
    if unprovenanced:
        worsen(DEGRADED)
        reasons.append("no document identity recorded for: " + ", ".join(sorted(unprovenanced)))

    # 6. STALE EVIDENCE, specification 9.2, against the source class's OWN freshness requirement
    #    and never one universal age. Assessed only where the package declares an as-of date;
    #    where it declares none, no staleness is claimed, because none can be measured.
    stale = []
    for f in required:
        d = as_of.get(f)
        cls = source_class.get(f)
        allowed = freshness.get(cls)
        if d is None or allowed is None or period_cutoff is None:
            continue
        age = (period_cutoff - d).days
        if age > allowed:
            stale.append(f"{f} is {age} days old against a {allowed} day requirement for {cls}")
        elif age < 0:
            worsen(REJECTED)
            reasons.append(f"{f} is dated after the period cutoff, which is not a freshness "
                           f"state but a malformed one")
    if stale:
        worsen(DEGRADED)
        reasons.append("stale against the source class requirement: " + "; ".join(sorted(stale)))

    return {"verdict": verdict, "reasons": reasons, "gate_version": GATE_VERSION,
            "required_fields": list(required)}


def qualify(module_id: str, band, value, preflight_result: dict,
            lineage: dict | None = None,
            module_abstained: bool = False) -> QualifiedSignal:
    """
    ANALYTICAL MODULE -> CATEGORY-9 SIGNAL QUALIFICATION. Turn a module's raw output into a
    qualified signal, carrying the preflight verdict forward and adding what only the signal
    itself can show.

    A module that abstained on its own terms is ABSTAINED whatever the preflight said, because
    there is no value; and a signal whose evidence relationship is quality, governance or
    decision output is REJECTED as project-condition evidence however good its evidence is, which
    is the anti-feedback rule stated at the gate as well as inside the combination. Two places
    enforce it because a signal can reach a synthesis without passing through the fusion.
    """
    order = {ALLOWED: 0, DEGRADED: 1, ABSTAINED: 2, REJECTED: 3}
    verdict = preflight_result.get("verdict", ALLOWED)
    reasons = list(preflight_result.get("reasons", []))

    if module_abstained or band is None:
        if order[ABSTAINED] > order[verdict]:
            verdict = ABSTAINED
            reasons.append("the module produced no band on this evidence")

    rel = (lineage or {}).get("evidence_relationship")
    if rel in NON_PROJECT_EVIDENCE:
        verdict = REJECTED
        reasons.append(f"a {rel} signal is a statement about the evidence or about a decision "
                       f"already taken, and is not project-condition evidence")

    return QualifiedSignal(module_id, band, value, verdict, reasons,
                           lineage or lineage_record(module_id))


def fuse_qualified(signals) -> list[dict[str, Any]]:
    """
    QUALIFIED SIGNAL -> SYNTHESIS / GOVERNANCE / DECISION SUPPORT.

    Converts qualified signals into the shape the combination consumes, and REFUSES anything
    that is not a QualifiedSignal. That refusal is the raw-bypass guard: a caller cannot skip the
    gate by hand-building `{"status": ..., "lineage": ...}`, because the shape alone is not
    enough to get past this function.
    """
    out = []
    for s in signals or []:
        if not isinstance(s, QualifiedSignal):
            raise RawBypassError(
                "a raw signal reached the combination without passing the Category-9 gate: "
                f"{type(s).__name__}. Build it with qualify() rather than by hand.")
        out.append(s.to_fusion_signal())
    return out
