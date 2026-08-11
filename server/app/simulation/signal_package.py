"""
The flat-to-nested adapter: ONE assembly of the nested signal package the fourteen Group B
modules declare as their input contract, built from the flat `signalInputs` dictionary the
normal path actually supplies.

WHY THIS FILE EXISTS (external arithmetic audit of 2026-08-10, P0 finding 1). Fourteen
registered modules -- B1.1 to B1.4, B2.1 to B2.9 and B3.1 -- read nested assembled signal
objects (`si["evm"]`, `si["mc"]`, `si["cusum"]`, `si["doc"]`, `si["decision"]`,
`si["signals"]`, `si["simulationSignals"]["signal_array"]`). Extraction and `documents.py`
supply a FLAT dictionary (cpi, spi, bac, docRiskScore, ...). In the browser those nested
objects were assembled by `assets/js/sim.js` `buildSignals()` and carried on the project;
on the server nothing ever assembled them, so all fourteen abstained on every real run and a
normal run returned at most 81 of the 95 registered arithmetic modules. The abstention looked
like missing data and was a wiring failure, which is why it survived undetected.

ONE adapter, in one place, not fourteen per-module shims: `registry.run_all()` calls
`build_signals()` and `adapt()` and hands the result to exactly those fourteen modules. Every other module
continues to receive the unmodified flat dictionary -- `adapt()` never mutates the caller's
`si`, it returns a new dict, so the stored `signal_inputs` row and every other module's input
are byte-identical to what they were before this adapter existed.

WHAT THE ADAPTER IS ALLOWED TO DO, AND WHAT IT REFUSES TO DO.

It ROUTES evidence that already exists. It does not manufacture any. Specifically:

  * `evm`   comes from the flat `cpi` and `spi` (and `bac` where present). Absent unless BOTH
            indices are present: an EVM signal built on one index and a substituted 1.0 -- what
            the browser's `runModels` did -- is a fabrication, and D1 removed that class of
            behaviour from this layer.
  * `mc`    comes from THIS RUN'S OWN Monte Carlo module (A1.1) result. It is not re-simulated
            here: one arithmetic, one place. If A1.1 abstained (no bac, cpi or spi), there is
            no `mc` signal, and the modules that read it see an absent signal, which is the
            truth.
  * `cusum` comes from THIS RUN'S OWN CUSUM module (A1.2) result, same rule. A1.2 abstains
            without a real SPI history (D1 removed the synthesised twelve-point series), so a
            project in its first period has no cusum signal rather than an invented one.
  * `doc`   comes from the flat `docRiskScore`, the value the extraction model supplies and the
            server carries through unchanged.
  * `decision` comes from B1.1 Conservative Dominance's own output, computed in the tier before
            the modules that read it -- exactly the order the browser used
            (`signals.js` `decisionSnapshot()` before `runDST`).
  * `simulationSignals.signal_array` holds the results this same run has already computed, each
            as the {method_class, status_color, module_id} triple the voting modules read.

The only arithmetic in this file is `evm_status()` and `doc_status()`, both transcribed
character-for-character from `assets/js/sim.js` (`evmStatus`, `docStatus`), the instrument's own
signal-package assembler. They classify an assembled signal; they are not any module's formula,
and no module's formula is touched, reached differently, or changed by this file. `mc` and
`cusum` statuses are NOT recomputed here at all -- they are the status the corresponding module
already produced.

THE CASING IS PASSED THROUGH, NOT NORMALISED. `sim.js` emits lowercase "red"/"amber"/"green"
for every assembled signal status, and the server's A1.1/A1.2 emit the same lowercase values.
Several consuming modules compare against a capitalised vocabulary. That mismatch is audit
finding 3 (Conservative Dominance) and it is a defect in the CONSUMING modules, scheduled for
the defect run. Normalising it here would be changing those modules' arithmetic from outside,
which this run's exception explicitly forbids, and would hide the defect the next run must fix.
See REPORT_2026-08-11_run2-adapter.md, which records which modules it affects.

KNOWN DEVIATION -- CATEGORY 9 (audit P0 finding 2, and remediation_decisions_answered.md 3.1).
The architecture requires Group B to consume a VERSIONED QUALIFIED-SIGNAL PACKAGE produced by a
Category 9 eligibility gate. THAT GATE DOES NOT EXIST: `run_all` executes modules independently
and `compute_project` merely excludes Group C from the vote, so nothing decides whether a signal
is fit to be combined before it is combined. This adapter is therefore built on RAW,
UNQUALIFIED SIGNALS, by decision and not by oversight. Every result the fourteen modules produce
carries `signal_qualification: "unqualified"` so the deviation is legible in the API response
and the export rather than living only in a document.
"""

from __future__ import annotations

from typing import Any

#: The fourteen modules whose declared input contract is the nested package, in the order the
#: adapter must run them: each tier consumes what the tier before it produced. This ordering is
#: the browser's own (`signals.js`: build the signal package, take the decision snapshot, run the
#: evidence-combination models, then the voting ensembles over their results).
#:
#: Tier 1 reads evm/mc/cusum/doc statuses only.
#: Tier 2 additionally reads `decision.state`, which is tier 1's B1.1 output.
#: Tier 3 additionally reads `simulationSignals.signal_array`, the results computed so far.
ADAPTER_TIERS: tuple[tuple[str, ...], ...] = (
    ("B1.1", "B3.1"),
    ("B2.1", "B2.2", "B2.3", "B2.4", "B2.5", "B2.6", "B2.7", "B2.8", "B2.9"),
    ("B1.2", "B1.3", "B1.4"),
)

#: All fourteen, for membership tests.
NESTED_INPUT_MODULES: frozenset[str] = frozenset(m for tier in ADAPTER_TIERS for m in tier)

#: Stamped on every result and every abstention of the fourteen. The owner's settled decision
#: (remediation_decisions_answered.md 3.2) is that they are reachable, shown, and explicitly
#: marked as newly wired and unvalidated -- in the export, the API and the methods documentation,
#: NOT on the participant surface.
WIRING_NOTE = (
    "Newly wired and unvalidated: this module could not execute on the normal computation path "
    "before the flat-to-nested signal adapter, so its output has never been validated against "
    "real project evidence. Advisory, non-voting."
)

#: The recorded Category 9 deviation, carried on the data rather than only in the report.
SIGNAL_QUALIFICATION = "unqualified"
CATEGORY_9_DEVIATION = (
    "Consumes raw signals. The Category 9 eligibility gate the architecture requires, which "
    "would qualify a versioned signal package before evidence combination and governance read "
    "it, is not implemented; nothing gates these inputs on evidence quality."
)

#: The four assembled signal keys, in the order they are reported.
SIGNAL_KEYS = ("evm", "mc", "cusum", "doc")

#: How each key is named in a sentence a person reads. The abstention reason these produce is
#: rendered on the Signal Ledger, which the previous run established is reachable from the
#: participant decision sequence, so it carries no key names, no module ids and no numbering.
SIGNAL_NAMES = {
    "evm": "the cost and schedule indices",
    "mc": "the cost forecast",
    "cusum": "the performance trend",
    "doc": "the document risk score",
}


def evm_status(cpi: float, spi: float) -> str:
    """Transcribed from assets/js/sim.js `evmStatus`. Lowercase, as the instrument emits."""
    if cpi < 0.90 or spi < 0.85:
        return "red"
    if cpi < 0.95 or spi < 0.95:
        return "amber"
    return "green"


def doc_status(score: float) -> str:
    """Transcribed from assets/js/sim.js `docStatus`. Lowercase, as the instrument emits."""
    if score >= 0.70:
        return "red"
    if score >= 0.30:
        return "amber"
    return "green"


def _module_result(computed: list[dict], module_id: str) -> dict | None:
    for row in computed:
        if row.get("module_id") == module_id:
            return row
    return None


def build_signals(si: dict, computed: list[dict]) -> tuple[dict, dict]:
    """
    Assemble the four signal objects from the flat inputs and this run's own results.

    Returns (signals, absence): `signals` holds only the keys that could be assembled from
    evidence that is actually present, and `absence` explains, per missing key, exactly what was
    missing. Nothing is defaulted, substituted or synthesised: a key the evidence cannot support
    is ABSENT, which is the state every consuming module already models.
    """
    signals: dict[str, Any] = {}
    absence: dict[str, str] = {}

    cpi, spi = si.get("cpi"), si.get("spi")
    if cpi is not None and spi is not None:
        signals["evm"] = {"cpi": cpi, "spi": spi, "bac": si.get("bac"),
                          "status": evm_status(cpi, spi)}
    else:
        missing = [{"cpi": "the cost index", "spi": "the schedule index"}[k]
                   for k in ("cpi", "spi") if si.get(k) is None]
        absence["evm"] = ("this period's evidence carries no cost index and schedule index "
                          "pair (" + " and ".join(missing) + " absent)")

    mc = _module_result(computed, "A1.1")
    if mc is not None:
        signals["mc"] = {
            # THE KEY THE MODULES ACTUALLY READ. See the report: the browser's buildSignals
            # emitted `p80eacOverrunPct` while every consuming module reads `p80DeltaPct`, so in
            # the browser this arm read undefined and fell through `|| 0` to the calmest branch
            # on every project. Both keys are carried here; the one the contract names holds the
            # real figure.
            "p80DeltaPct": mc.get("overrun_pct_p80"),
            "p80eacOverrunPct": mc.get("overrun_pct_p80"),
            "p80": mc.get("p80_eac"),
            "p50": mc.get("p50_eac"),
            "status": mc.get("status_color"),
        }
    else:
        absence["mc"] = "the cost forecast computation abstained this period"

    cu = _module_result(computed, "A1.2")
    if cu is not None:
        signals["cusum"] = {
            "breached": cu.get("breached"),
            "maxStat": cu.get("max_stat"),
            "H": cu.get("H"),
            "status": cu.get("status_color"),
        }
    else:
        absence["cusum"] = "the performance trend computation abstained this period"

    score = si.get("docRiskScore")
    if score is not None:
        signals["doc"] = {"score": score, "status": doc_status(score)}
    else:
        absence["doc"] = "this period's evidence carries no document risk score"

    return signals, absence


def adapt(si: dict, signals: dict, *, decision: dict | None = None,
          signal_array: list[dict] | None = None) -> dict:
    """
    The flat dictionary plus the nested objects, as ONE new dict. The caller's `si` is never
    mutated: what is stored on the computed_results row, and what every other module receives,
    stays exactly what it was.
    """
    out = dict(si)
    for key, value in signals.items():
        out[key] = value
    nested = dict(signals)
    if decision is not None:
        out["decision"] = decision
        nested["decision"] = decision
    out["signals"] = nested
    out["simulationSignals"] = {"signal_array": list(signal_array or [])}
    return out


def decision_snapshot(conservative: dict | None) -> dict | None:
    """
    The `decision` signal, from B1.1 Conservative Dominance's own result. Mirrors
    `signals.js` `decisionSnapshot()`, which likewise derived it rather than storing a second
    copy. None when B1.1 abstained: an absent decision signal, not an invented one.
    """
    if not conservative:
        return None
    return {"state": conservative.get("state"), "conflict": conservative.get("conflict")}


def array_entry(row: dict) -> dict:
    """One `signal_array` element, in the shape the voting ensembles read."""
    return {"module_id": row.get("module_id"), "method_class": row.get("method_class"),
            "status_color": row.get("status_color")}


def supplied_and_absent(signals: dict, absence: dict) -> str:
    """
    A stated reason, for an abstention record. A module of the fourteen that still abstains
    must say what it was given and what it was not, so the abstention can be read as a data gap
    or as a wiring gap rather than being silent about which it is.
    """
    supplied = [SIGNAL_NAMES[k] for k in SIGNAL_KEYS if k in signals]
    missing = [k for k in SIGNAL_KEYS if k not in signals]
    parts = ["This computation reads an assembled signal package. It was supplied "
             + (", ".join(supplied) if supplied else "no signals")]
    if missing:
        parts.append("Not available this period: "
                     + "; ".join(f"{SIGNAL_NAMES[k]}, because {absence.get(k, 'it was not assembled')}"
                                 for k in missing))
    return ". ".join(parts) + "."
