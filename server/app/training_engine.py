"""
Training mode run 2: the deterministic core of the loop.

Everything in this module is a PURE FUNCTION of its inputs. No clock, no randomness, no session:
the same state and the same decision produce the same next state on any machine on any day. That
is the teaching contract — directors disagree about the right call, they do not disagree that
escalating spends float — and it is also what makes the loop verifiable: a check can replay a
run and expect identical bytes.

THE MECHANICS ARE FIXED EVEN WHERE THE JUDGEMENT IS OPEN. The effect table lives here as data
(`EFFECTS` below plus the profile figures), in one place, so Lin can correct a figure without
reading the advance logic. Figures marked "designed" have no external authority — they are the
elicited layer `training_us_contract_regimes.md` says is ours to set, and they are stated in the
brief so a trainee can reason about them rather than discovering hidden rules.

THE TWO CLOCKS MUST NOT BLUR. The PERIOD advances one step per decision; the NOTICE CLOCK runs
in days inside the run's calendar. The event lands on day 10 of period one and the trainee
decides on day 20 of every period, so the first decision is taken 10 days after the event and
each deferral adds 30 more. Under A201's 21 days or ConsensusDocs' 14, ONE deferral spends the
window even though only one period passed. That asymmetry is the point, not an accident.

CONTRACT PERIODS COME FROM `training_us_contract_regimes.md` AND ARE NOT OVERRIDABLE. The three
forms' figures are transcribed from that file with their clause citations; that file's own
caveat (A201 and ConsensusDocs periods are from law-firm summaries, unverified against the
licensed documents — roadmap item 14) travels with them. No clause text is reproduced, only
periods and citations, per the file's copyright note.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

# ---------------------------------------------------------------- run geometry (designed)

PERIOD_DAYS = 30          # one reporting period
PERIODS_TOTAL = 10        # contract duration: 300 days
DECISION_DAY = 20         # the trainee decides on day 20 of each period
EVENT_DAY = 10            # the standing change event lands on day 10 of period one
SCHEDULE_START = date(2026, 1, 5)   # fixed, so every date in a run is deterministic
TOTAL_FLOAT_DAYS = 12     # designed: small enough that one escalation plus two deferrals
                          # exhausts it and puts liquidated damages in play

# ---------------------------------------------------------------- money rules (designed)

# Liquidated damages per day: derived from contract value, rounded to the nearest 500 dollars,
# with the RATE following the brief's facility condition (run 3 correction 4). A hospital and a
# warehouse do not carry the same daily exposure, so the brief names the facility and the rate
# follows from it, inside the common 0.02 to 0.05 percent band. The band ends are designed
# figures; the derivation from contract value is unchanged.
LD_ROUND = 500
LD_RATES_BY_FACILITY: dict[str, float] = {
    "critical": 0.0005,      # hospital, airfield operations: the top of the band
    "standard": 0.00035,     # commercial, institutional: mid band
    "utilitarian": 0.0002,   # warehouse, storage: the bottom of the band
}
FACILITY_LABELS: dict[str, str] = {
    "critical": "critical occupancy, hospital grade: every day of delay is clinical capacity",
    "standard": "standard commercial occupancy",
    "utilitarian": "utilitarian occupancy, warehouse grade: delay costs storage, not operations",
}
DEFAULT_FACILITY = "standard"

# Run 3 correction 2: escalation float cost is not flat. It scales with how long the position
# has been left open, so early recognition is rewarded: cost in days = base + 2 per full period
# the dispute has sat open, capped. The curve is linear in deferred periods, by design simple
# enough to state in one sentence on the screen.
ESCALATE_FLOAT_PER_PERIOD_OPEN = 2
ESCALATE_FLOAT_CAP_DAYS = 12

# Run 3 correction 3: credibility is asymmetric. One aggressive escalation spends a point at
# once and destroys any accumulated goodwill; earning a point takes this many concessions.
CRED_EARN_CONCESSIONS = 2

# ---------------------------------------------------------------- discrete events (run 3)
#
# THE DESIGNED EVENT FIGURES, in one table, per the brief: probability and duration are
# elicited, not regulatory — the DOB regime sets WHAT lifting requires (a Certificate of
# Correction plus whatever the cause demands), not how long a response takes. Every figure
# here is a designed training figure for Lin to correct.
EVENT_FIGURES: dict[str, Any] = {
    # The base near miss: exogenous, scheduled by the run's geometry, not a rate the trainee
    # manages and never disclosed in advance. Nobody foresees it.
    "near_miss_period": 4,
    # Every near miss converts to a stop work order in this run (designed 1.0; the elicited
    # probability layer can lower it later without touching the machinery).
    "swo_conversion": 1.0,
    # The incident itself costs little — the stop work order is the mechanism.
    "incident_direct_cost_rate": 0.001,
    # Acceleration raises the hazard deterministically: each accelerated period adds this much,
    # and a hazard reaching 1.0 fires a second near miss the following period. Deterministic on
    # purpose — same decisions, same incidents — so the debrief can say "the acceleration did
    # this" rather than "bad luck".
    "acceleration_hazard_per_use": 0.5,
    "hazard_threshold": 1.0,
    # Acceleration itself: buys float back at a premium priced by the profile's multiplier.
    "acceleration_float_recovered_days": 4,
    "acceleration_cost_rate": 0.01,
    # Duration follows the RESPONSE, not the incident. A strong response assembles the full
    # correction package at once; a minimal one does the least each round and stays stopped
    # longer, with a longer productivity shadow after restart.
    "response": {
        "respond_strong": {
            "days_lost": {"exacting": 6, "steady": 5},
            "cost_rate": 0.008,
            "restart_periods": 1,
        },
        "respond_minimal": {
            "days_lost": {"exacting": 18, "steady": 14},
            "cost_rate": 0.002,
            "restart_periods": 2,
        },
    },
}

# The standing change event, scaled from contract value so a larger project argues about
# larger money: estimated impact cost is 1.5 percent of contract value. Twelve days is the
# stated schedule content of the change (informational this run; time relief is not modelled).
IMPACT_COST_RATE = 0.015
IMPACT_DAYS = 12

# ---------------------------------------------------------------- regimes across the run (run 4)
#
# Run 4 makes the choice of form matter beyond the claim-notice check. Three mechanics, all
# deterministic, all form-specific:
#
# THE DIFFERING SITE CONDITION (trap 1). A second discrete matter, discovered on day 3 of
# period five — 17 days old at that period's decision. The geometry is the trap: 17 days is
# INSIDE A201's 21 day claim window and OUTSIDE its 14 day differing-site-conditions window
# (Section 3.7.4, shortened from 21 in the 2007 edition), so a trainee applying the claim
# period from memory is told, at the first opportunity, that the site-conditions period
# governed and had already run. Under ConsensusDocs there is no fixed day count — the duty is
# to stop affected work and give prompt written notice (Section 3.16.2), modelled as: notice at
# the FIRST decision after discovery preserves, anything later is not prompt. Under FAR the
# duty is notice promptly and BEFORE the conditions are disturbed (52.236-2(a)), modelled as:
# notice at the first decision preserves; a period of continued work disturbs the condition and
# the entitlement is gone. Same discovery, three different failures, decided by the form alone.
DSC_PERIOD = 5
DSC_DISCOVERY_DAY = 3            # of the period; 17 days before that period's decision day
DSC_COST_RATE = 0.008            # estimated impact of the condition: 0.8 percent of value
DSC_DAYS = 6                     # stated schedule content, informational
A201_DSC_NOTICE_DAYS = 14        # Section 3.7.4

# THE CONSENSUSDOCS SECOND STEP (trap 2). Notice within 14 days, then documentation within 21
# days after the notice (Section 8.4). A 30 day period has no decision point inside the 21 day
# documentation window, so the step is modelled at period grain: an escalation gives notice and
# holds the recovery CONDITIONAL; the following period's decision is the documentation window,
# and DEFERRING it is going quiet — the claim dies with the two-step citation. Any active
# decision keeps the file moving and the documentation lands. Designed abstraction, stated.
#
# THE FAR GROWTH AND CERTIFICATION (traps 3 and 4). Under FAR a deferred claim GROWS — work
# continues under the change and its cost accumulates at this rate per deferred period. The 20
# day lookback (52.243-4(d), trap 3, built in run 2) shrinks what notice can reach; and a claim
# whose value crossed 100,000 dollars during the LAST deferred period is submitted on the form
# prepared before it grew — uncertified, and an uncertified claim over the threshold is not a
# claim at all (FAR 52.233-1, 41 USC 7103). A claim already over the threshold at the previous
# decision point was known to need certification and carries it.
FAR_CLAIM_GROWTH_RATE = 0.0025   # per deferred period, FAR only
FAR_CERTIFICATION_THRESHOLD = 100_000.0

CONTINGENCY_RATE = 0.05   # original contingency: 5 percent of contract value

DEFAULT_CONTRACT_VALUE = 12_000_000.0
MIN_CONTRACT_VALUE = 1_000_000.0
MAX_CONTRACT_VALUE = 500_000_000.0

# ---------------------------------------------------------------- contract forms
#
# Periods per training_us_contract_regimes.md. Clause numbers cited, text never reproduced.
# `claim_notice_days` None means the form has no fixed notice bar; FAR instead has the 20-day
# cost lookback of FAR 52.243-4(d): costs incurred more than 20 days before written notice are
# simply unrecoverable. Nothing is time-barred; the money is gone.
CONTRACT_FORMS: dict[str, dict[str, Any]] = {
    "A201-2017": {
        "label": "AIA A201-2017",
        "claim_notice_days": 21,
        "claim_notice_citation": "Section 15.1.3.1",
        "second_step": None,
        "lookback_days": None,
        "brief_note": ("Claims for additional cost or time require notice within 21 days "
                       "(Section 15.1.3.1). Article 15 claims must be served by certified or "
                       "registered mail or by courier with proof of delivery."),
    },
    "ConsensusDocs 200": {
        "label": "ConsensusDocs 200",
        "claim_notice_days": 14,
        "claim_notice_citation": "Section 8.4",
        # The two-step clock: notice within 14 days, supporting documentation within 21 days
        # after the notice. Run 2 models step one; the documentation step is stated in the
        # brief and becomes mechanical when discrete events land (run 3).
        "second_step": "documentation within 21 days after the notice (Section 8.4)",
        "lookback_days": None,
        "brief_note": ("Notice of a claim within 14 days, then supporting documentation within "
                       "21 days after that notice (Section 8.4). Giving notice and then going "
                       "quiet loses the claim."),
    },
    "Federal FAR": {
        "label": "Federal (FAR)",
        "claim_notice_days": None,
        "claim_notice_citation": "FAR 52.243-4(d)",
        "second_step": None,
        "lookback_days": 20,
        "brief_note": ("No fixed notice bar, but no adjustment for costs incurred more than 20 "
                       "days before written notice (FAR 52.243-4(d)). Claims over 100,000 "
                       "dollars must be certified (FAR 52.233-1, 41 USC 7103)."),
    },
}

# ---------------------------------------------------------------- site and market conditions
#
# The non-contractual figures, chosen per run and stated in the brief. Two profiles. Every
# number is designed (the elicited layer). Acceleration multiplier and restart loss are stated
# in the brief because a PM prices a recovery plan against them, but they become mechanical
# only when discrete stoppages land in run 3; this run's mechanics use the three figures
# marked (mechanical).
CONDITION_PROFILES: dict[str, dict[str, Any]] = {
    "exacting": {
        "labour": "tight: qualified trades are scarce and diverted supervision is expensive",
        "procurement": "exposed: long lead items dominate the critical path",
        "owner": "formal: entitlement is honoured, quantum is contested",
        # (mechanical) the BASE of the escalation curve: what a prompt, well-documented
        # escalation costs. Run 3 correction 2 made the cost scale with time left open.
        "escalate_float_days_base": 4,
        "defer_drift_float_days": 3,    # (mechanical) coordination drift per deferred period
        "low_credibility_recovery_factor": 0.85,  # (mechanical) quantum contested when trust is low
        "acceleration_cost_multiplier": 1.5,
        "restart_productivity_loss": 0.15,
    },
    "steady": {
        "labour": "available: trades can be added without premium",
        "procurement": "stocked: no long lead item is currently critical",
        "owner": "collaborative: disputes are resolved on the figures",
        "escalate_float_days_base": 3,
        "defer_drift_float_days": 2,
        "low_credibility_recovery_factor": 0.95,
        "acceleration_cost_multiplier": 1.25,
        "restart_productivity_loss": 0.10,
    },
}

DECISIONS = ("escalate", "absorb", "defer", "accelerate")
RESPONSES = ("respond_strong", "respond_minimal")

# ---------------------------------------------------------------- the effect table
#
# THIS IS THE TABLE THE REPORT QUOTES, revised per run 3's four corrections. Decision against
# state change, fixed for the same conditions. The three tensions:
#
#   escalate  protects entitlement, spends float
#   absorb    protects the relationship, spends contingency
#   defer     protects both, and runs the notice clock down
#
# | decision       | float                        | contingency   | actual cost              | owner credibility     | dispute, clock, hazard                    |
# |----------------|------------------------------|---------------|--------------------------|-----------------------|-------------------------------------------|
# | escalate       | minus base + 2 per full      | unchanged     | plus 0.2% of value       | minus 1 (floor 1) and | notice served; entitlement decided by the |
# |                | period left open, cap 12     |               | (claim preparation)      | progress reset to 0   | form's window against days since event    |
# |                | (base 4 exacting, 3 steady)  |               |                          |                       |                                           |
# | absorb         | unchanged                    | minus impact  | plus impact cost         | plus ONE PROGRESS     | dispute closed, entitlement waived        |
# |                |                              | cost (1.5% cv)| (work is done anyway)    | step; 2 steps = +1    |                                           |
# | defer          | minus defer_drift days       | unchanged     | plus 0.3% of value       | unchanged             | clock runs 30 more days; drift repeats    |
# |                | (3 exacting, 2 steady)       |               | (unmanaged change)       |                       | every deferred period                     |
# | accelerate     | RECOVERS 4 days              | unchanged     | plus 1.0% of value times | unchanged             | hazard plus 0.5; at 1.0 a second near     |
# |                |                              |               | the profile multiplier   |                       | miss fires the following period           |
# | respond strong | minus days lost (6 exacting, | unchanged     | plus 0.8% of value (the  | unchanged             | stop work order lifts; restart shadow     |
# | (during SWO)   | 5 steady)                    |               | full correction package) |                       | 1 period at reduced earning               |
# | respond minimal| minus days lost (18 exacting,| unchanged     | plus 0.2% of value       | unchanged             | lifts late; restart shadow 2 periods      |
# | (during SWO)   | 14 steady)                   |               |                          |                       |                                           |
#
# Earned value: a period earns one tenth of contract value when undisturbed; a period spent
# with the dispute open (deferred) earns 90 percent; a restart period earns
# (1 - restart_productivity_loss) of what it otherwise would. Factors multiply. Lost earning
# is never recovered. cpi and spi are DERIVED (ev over ac, ev over pv), never set directly.
#
# Resolution of a preserved escalation: unchanged from run 2 — the NEXT period books the change
# order; recoverable = impact cost, times the FAR lookback fraction where that form applies,
# times the low-credibility factor when credibility BEFORE the escalation was 2 or less. The
# FAR path halving money where A201 and ConsensusDocs bar the claim is deliberately untouched.
#
# CREDIBILITY IS ASYMMETRIC (correction 3): one escalation spends a point at once AND resets
# earn progress to zero; earning takes CRED_EARN_CONCESSIONS concessions per point. During a
# stop work order the dispute clock still runs: the correction package consumes the attention
# the notice would have needed, which is itself a lesson.

ESCALATE_PREP_COST_RATE = 0.002    # claim preparation, plus affected work held
DEFER_DRIFT_COST_RATE = 0.003      # unmanaged change cost drift per deferred period
DEFER_EV_FACTOR = 0.90             # a disturbed period earns 90 percent
CRED_START, CRED_MIN, CRED_MAX = 3, 1, 5
LOW_CREDIBILITY_AT_OR_BELOW = 2


def _round3(v: float) -> float:
    return round(v, 3)


def derive_ld_per_day(contract_value: float, facility: str = DEFAULT_FACILITY) -> float:
    rate = LD_RATES_BY_FACILITY[facility]
    return round(contract_value * rate / LD_ROUND) * LD_ROUND


def escalation_float_cost(state: dict[str, Any], days_open: int | None = None) -> int:
    """
    Correction 2's curve: base + 2 days per FULL PERIOD the position has been left open,
    capped. Early on a well-documented position is cheap; late on a contested one is dear.
    Periods open is derived from the clock itself, so the cost and the clock cannot disagree
    about how long the position has sat. `days_open` lets the caller price the act on
    whichever open matter is oldest (run 4: the site condition, when the claim has closed);
    the default is the claim's own clock.
    """
    profile = CONDITION_PROFILES[state["conditions"]]
    if days_open is None:
        days_open = state["dispute"]["days_since_event"]
    periods_open = max(0, (days_open - (DECISION_DAY - EVENT_DAY)) // PERIOD_DAYS)
    return min(ESCALATE_FLOAT_CAP_DAYS,
               profile["escalate_float_days_base"]
               + ESCALATE_FLOAT_PER_PERIOD_OPEN * periods_open)


def period_dates(period: int) -> dict[str, str]:
    """The fixed calendar of one period: start, decision day, end. All ISO strings."""
    start = SCHEDULE_START + timedelta(days=(period - 1) * PERIOD_DAYS)
    return {
        "from": start.isoformat(),
        "decision": (start + timedelta(days=DECISION_DAY - 1)).isoformat(),
        "to": (start + timedelta(days=PERIOD_DAYS - 1)).isoformat(),
    }


def build_brief(contract_form: str, contract_value: float, conditions: str,
                facility: str = DEFAULT_FACILITY) -> dict[str, Any]:
    """
    The three things every run opens with: the form and its periods, the liquidated damages
    derivation, the site and market conditions. Reachable at any point in the run, so this is
    a pure projection the state endpoint can return every time.
    """
    form = CONTRACT_FORMS[contract_form]
    profile = CONDITION_PROFILES[conditions]
    ld = derive_ld_per_day(contract_value, facility)
    return {
        "contract_form": contract_form,
        "contract_form_label": form["label"],
        "claim_notice_days": form["claim_notice_days"],
        "claim_notice_citation": form["claim_notice_citation"],
        "second_step": form["second_step"],
        "lookback_days": form["lookback_days"],
        "contract_note": form["brief_note"],
        "contract_value": contract_value,
        "facility": facility,
        "facility_label": FACILITY_LABELS[facility],
        "liquidated_damages_per_day": ld,
        "liquidated_damages_rate": LD_RATES_BY_FACILITY[facility],
        "liquidated_damages_rule": (
            "Liquidated damages are derived from contract value at a daily rate set by the "
            "facility's criticality, within the common 0.02 to 0.05 percent band, rounded to "
            f"the nearest 500 dollars. This facility carries "
            f"{LD_RATES_BY_FACILITY[facility] * 100:.3f} percent per day."),
        "schedule": {
            "start": SCHEDULE_START.isoformat(),
            "periods": PERIODS_TOTAL,
            "period_days": PERIOD_DAYS,
            "total_float_days": TOTAL_FLOAT_DAYS,
        },
        "conditions": {
            "profile": conditions,
            "labour": profile["labour"],
            "procurement": profile["procurement"],
            "owner": profile["owner"],
            "acceleration_cost_multiplier": profile["acceleration_cost_multiplier"],
            "restart_productivity_loss": profile["restart_productivity_loss"],
        },
        "standing_event": {
            "description": ("An unforeseen utility conflict was identified on day 10 of period "
                            "one. The estimated impact is stated below. The response is yours: "
                            "escalate it as a claim, absorb it, or defer the decision."),
            "estimated_cost": round(contract_value * IMPACT_COST_RATE, 2),
            "estimated_days": IMPACT_DAYS,
            "event_day": EVENT_DAY,
        },
        "safety_note": (
            "Site safety runs under a stop work order regime: on issue, all work stops except "
            "safety work, and lifting requires a Certificate of Correction plus whatever the "
            "cause demands. The response decides the duration. Accelerating the work raises "
            "the chance of an incident."),
        "disclaimer": build_disclaimer(contract_form),
        "designed_figures_note": (
            "Site and market figures, the liquidated damages coefficient and the decision "
            "effects are designed training figures with no external authority. Contract notice "
            "periods follow the named form and are not adjustable in training."),
    }


def initial_state(contract_form: str, contract_value: float, conditions: str,
                  facility: str = DEFAULT_FACILITY) -> dict[str, Any]:
    """
    Period one, before any decision: the event is 10 days old on decision day.

    The money figures are AS OF THE DECISION DAY, day 20 of a 300 day schedule, so the run
    opens with 20 days of clean progress (cpi and spi both 1.0) rather than an empty project
    every module abstains on. Each advance then adds exactly one period's worth.
    """
    opening = round(contract_value * DECISION_DAY / (PERIODS_TOTAL * PERIOD_DAYS), 2)
    return {
        "period": 1,
        "contract_form": contract_form,
        "conditions": conditions,
        "facility": facility,
        "bac": contract_value,
        "baseline_contract_sum": contract_value,
        "revised_contract_sum": contract_value,
        "ev": opening,
        "ac": opening,
        "pv": opening,
        "float_total_days": TOTAL_FLOAT_DAYS,
        "float_consumed_days": 0,
        "contingency_original": round(contract_value * CONTINGENCY_RATE, 2),
        "contingency_remaining": round(contract_value * CONTINGENCY_RATE, 2),
        "owner_credibility": CRED_START,
        # Correction 3: earning is stepped. Progress counts concessions; CRED_EARN_CONCESSIONS
        # of them convert to one point. An escalation resets it to zero.
        "credibility_progress": 0,
        "change_order_count": 0,
        "dispute": {
            "status": "open",              # open | escalated | absorbed | resolved
            "entitlement": "undecided",    # undecided | preserved | waived | lost
            "estimated_cost": round(contract_value * IMPACT_COST_RATE, 2),
            "estimated_days": IMPACT_DAYS,
            "days_since_event": DECISION_DAY - EVENT_DAY,
            "recovered_amount": None,
            "pending_recovery": None,
        },
        "liquidated_damages_per_day": derive_ld_per_day(contract_value, facility),
        "liquidated_damages_exposure": 0.0,
        # Run 3: the discrete event machinery. `hazard` accumulates from acceleration and fires
        # a near miss at the threshold; `incident` is the current event and `incidents` the
        # record. The SCHEDULE (near_miss_period) lives in code, never in state or a response.
        "hazard": 0.0,
        "incident": {"status": "none"},
        "incidents": [],
        # Run 4: the differing site condition, discovered in period DSC_PERIOD. None until
        # then — its existence before discovery is exactly the kind of forecast the state view
        # must not carry, and None serialises to nothing a trainee can read ahead.
        "dsc": None,
        # Run 4, FAR only: True when the claim's value crossed the certification threshold
        # during the last deferred period, so an immediate escalation submits the form
        # prepared before it grew.
        "claim_crossed_threshold_last_period": False,
        # Correction 1: what the LAST advance changed, so the cost of waiting is visible in the
        # period's figures and can be reasoned about rather than discovered in a diff.
        "period_changes": None,
        "decisions": [],
    }


def notice_position(state: dict[str, Any]) -> dict[str, Any]:
    """
    The notice clock as the trainee should read it, per the run's contract form. Derived,
    never stored, so the clock and the state cannot disagree.
    """
    form = CONTRACT_FORMS[state["contract_form"]]
    days = state["dispute"]["days_since_event"]
    window = form["claim_notice_days"]
    if window is not None:
        remaining = window - days
        return {
            "kind": "notice_bar",
            "window_days": window,
            "days_since_event": days,
            "days_remaining": remaining,
            "expired": remaining < 0,
            "citation": form["claim_notice_citation"],
        }
    lookback = form["lookback_days"]
    fraction = 1.0 if days <= lookback else _round3(lookback / days)
    return {
        "kind": "cost_lookback",
        "lookback_days": lookback,
        "days_since_event": days,
        "recoverable_fraction": fraction,
        "expired": False,
        "citation": form["claim_notice_citation"],
    }


def dsc_position(state: dict[str, Any]) -> dict[str, Any] | None:
    """
    The differing site condition's clock, per form. None before discovery. Derived, never
    stored, like the claim's — the two clocks are SEPARATE surfaces because conflating them is
    exactly the mistake trap 1 exists to teach.
    """
    dsc = state.get("dsc")
    if not dsc:
        return None
    form_name = state["contract_form"]
    days = dsc["days_since_event"]
    if form_name == "A201-2017":
        remaining = A201_DSC_NOTICE_DAYS - days
        return {
            "kind": "dsc_notice_bar",
            "window_days": A201_DSC_NOTICE_DAYS,
            "days_since_event": days,
            "days_remaining": remaining,
            "expired": remaining < 0,
            "citation": "Section 3.7.4",
            "note": ("A differing site condition has its own period, shorter than the claim "
                     "window: 14 days from first observance, not 21."),
        }
    if form_name == "ConsensusDocs 200":
        return {
            "kind": "dsc_prompt",
            "days_since_event": days,
            "first_opportunity": dsc.get("first_opportunity", False),
            "expired": not dsc.get("first_opportunity", False),
            "citation": "Section 3.16.2",
            "note": ("No fixed day count: stop the affected work and give prompt written "
                     "notice. Prompt means now."),
        }
    return {
        "kind": "dsc_undisturbed",
        "days_since_event": days,
        "first_opportunity": dsc.get("first_opportunity", False),
        "expired": not dsc.get("first_opportunity", False),
        "citation": "FAR 52.236-2(a)",
        "note": ("Notice promptly, and before the conditions are disturbed. A period of "
                 "continued work disturbs them."),
    }


def allowed_decisions(state: dict[str, Any]) -> tuple[str, ...]:
    """
    What may be decided this period. During a stop work order the ONLY decision is the
    response: all work has stopped, and the correction package is the thing in front of the
    PM. Every other period offers the standard set.
    """
    if state.get("incident", {}).get("status") == "stopped":
        return RESPONSES
    return DECISIONS


def advance(state: dict[str, Any], decision: str) -> dict[str, Any]:
    """
    Apply one decision to one period and produce the next period's state. Pure: no clock, no
    randomness, no session. The effect table above is the specification; this is its only
    implementation. Incidents included: the near miss schedule and the hazard threshold are
    deterministic, so the same decisions always meet the same events.
    """
    allowed = allowed_decisions(state)
    if decision not in DECISIONS + RESPONSES:
        raise ValueError(f"unknown decision: {decision}")
    if decision not in allowed:
        if state.get("incident", {}).get("status") == "stopped":
            raise ValueError("a stop work order is in effect; the decision this period is the "
                             "response: respond_strong or respond_minimal")
        raise ValueError("no stop work order is in effect; there is nothing to respond to")
    if state["period"] > PERIODS_TOTAL:
        raise ValueError("the run is complete; no further period exists")

    s = {**state, "dispute": {**state["dispute"]},
         "incident": {**state.get("incident", {"status": "none"})},
         "incidents": list(state.get("incidents") or []),
         "dsc": ({**state["dsc"]} if state.get("dsc") else None),
         "decisions": list(state["decisions"])}
    profile = CONDITION_PROFILES[s["conditions"]]
    bac = s["bac"]
    form_name = s["contract_form"]
    dispute_open = s["dispute"]["status"] == "open"
    dsc_open = bool(s["dsc"]) and s["dsc"]["status"] == "open"
    period_earn = s["baseline_contract_sum"] / PERIODS_TOTAL
    # The FAR certification flag describes the LAST period only; it is re-derived below when a
    # deferral grows the claim across the threshold, and cleared otherwise.
    crossed_last_period = s.get("claim_crossed_threshold_last_period", False)
    s["claim_crossed_threshold_last_period"] = False

    # Correction 1's visibility: everything below is diffed against these at the end, so what
    # the period cost is a stated figure, not archaeology.
    before = {"float": s["float_consumed_days"], "ac": s["ac"],
              "contingency": s["contingency_remaining"],
              "credibility": s["owner_credibility"]}
    notes: list[str] = []

    # ---- the period's base progress. pv always earns a full increment; ev factors multiply:
    # a deferred-dispute period earns 90 percent, a restart period earns
    # (1 - restart_productivity_loss) — a stopped site does not come back at full production.
    disturbed = (dispute_open or dsc_open) and decision == "defer"
    ev_factor = DEFER_EV_FACTOR if disturbed else 1.0
    if s["incident"].get("status") == "restarting":
        ev_factor *= (1.0 - profile["restart_productivity_loss"])
        s["incident"]["restart_periods_left"] = s["incident"]["restart_periods_left"] - 1
        notes.append("Restart productivity loss applied to this period's earning.")
        if s["incident"]["restart_periods_left"] <= 0:
            s["incident"] = {"status": "none"}
    s["pv"] = round(s["pv"] + period_earn, 2)
    s["ev"] = round(s["ev"] + period_earn * ev_factor, 2)
    s["ac"] = round(s["ac"] + period_earn, 2)

    # ---- a preserved escalation booked last period resolves now, as a change order. The
    # differing site condition books through the same mechanism.
    for matter in (s["dispute"], s["dsc"] or {}):
        pending = matter.get("pending_recovery")
        if pending is not None:
            s["bac"] = round(s["bac"] + pending, 2)
            s["revised_contract_sum"] = round(s["revised_contract_sum"] + pending, 2)
            s["change_order_count"] = s["change_order_count"] + 1
            matter["recovered_amount"] = pending
            matter["pending_recovery"] = None
            matter["status"] = "resolved"

    # ---- ConsensusDocs' second step (trap 2). A claim noticed LAST period holds its recovery
    # conditional on the documentation following within 21 days of the notice (Section 8.4). A
    # 30 day period has no decision point inside that window, so the step is decided at period
    # grain: deferring the period after notice is going quiet, and the claim dies; any active
    # decision keeps the file moving and the documentation lands.
    if s["dispute"].get("status") == "noticed":
        conditional = s["dispute"].get("conditional_recovery")
        if decision == "defer":
            s["dispute"]["status"] = "escalated"
            s["dispute"]["entitlement"] = "lost"
            s["dispute"]["conditional_recovery"] = None
            notes.append("Notice was given and then the file went quiet: ConsensusDocs "
                         "requires supporting documentation within 21 days after the notice "
                         "(Section 8.4), and the claim is lost.")
        else:
            s["dispute"]["status"] = "escalated"
            s["dispute"]["entitlement"] = "preserved"
            s["dispute"]["pending_recovery"] = conditional
            s["dispute"]["conditional_recovery"] = None
            notes.append("The supporting documentation followed the notice within the second "
                         "21 day step (Section 8.4); the claim is preserved.")

    # ---- the decision itself. Run 4: an act serves EVERY open matter it can — one letter
    # each, the same afternoon — so escalate notices both the claim and the site condition,
    # absorb absorbs both, defer defers both. The act's own costs (float, preparation,
    # credibility) are paid ONCE per act; each matter's entitlement is decided by its own
    # clock and its own clause.
    if decision == "escalate" and (dispute_open or dsc_open):
        # Credibility "at the moment of escalation" is the standing EARNED BY PRIOR CONDUCT,
        # read before this escalation's own minus one — the act of escalating strains the
        # relationship going forward, it does not retroactively cheapen the claim it carries.
        credibility_before = s["owner_credibility"]
        days_open = (s["dispute"]["days_since_event"] if dispute_open
                     else s["dsc"]["days_since_event"])
        float_cost = escalation_float_cost(s, days_open)
        s["float_consumed_days"] = s["float_consumed_days"] + float_cost
        s["ac"] = round(s["ac"] + bac * ESCALATE_PREP_COST_RATE, 2)
        s["owner_credibility"] = max(CRED_MIN, s["owner_credibility"] - 1)
        # Correction 3: an aggressive escalation also destroys accumulated goodwill.
        s["credibility_progress"] = 0
        notes.append(f"Escalation float cost {float_cost} days: the position had been open "
                     f"{days_open} days, and a late escalation on a contested position costs "
                     "more than an early one.")

        def _discount(amount: float) -> float:
            if credibility_before <= LOW_CREDIBILITY_AT_OR_BELOW:
                return round(amount * profile["low_credibility_recovery_factor"], 2)
            return amount

        if dispute_open:
            position = notice_position(s)
            if position["kind"] == "notice_bar":
                if position["expired"]:
                    s["dispute"]["status"] = "escalated"
                    s["dispute"]["entitlement"] = "lost"
                elif form_name == "ConsensusDocs 200":
                    # Trap 2's setup: notice in the window is STEP ONE. The recovery is held
                    # conditional on the documentation following (see the noticed block above,
                    # which decides it next period).
                    s["dispute"]["status"] = "noticed"
                    s["dispute"]["entitlement"] = "conditional"
                    s["dispute"]["conditional_recovery"] = _discount(
                        s["dispute"]["estimated_cost"])
                    notes.append("Notice given within 14 days (Section 8.4, step one). The "
                                 "supporting documentation must follow within 21 days after "
                                 "the notice; going quiet now loses the claim.")
                else:
                    s["dispute"]["status"] = "escalated"
                    s["dispute"]["entitlement"] = "preserved"
                    s["dispute"]["pending_recovery"] = _discount(
                        s["dispute"]["estimated_cost"])
            else:
                # FAR: never time barred, but two mechanics of its own. Certification first
                # (trap 4): a claim whose value crossed 100,000 dollars during the LAST
                # deferred period is submitted on the form prepared before it grew, and an
                # uncertified claim over the threshold is not a claim at all.
                if crossed_last_period \
                        and s["dispute"]["estimated_cost"] > FAR_CERTIFICATION_THRESHOLD:
                    s["dispute"]["status"] = "escalated"
                    s["dispute"]["entitlement"] = "lost"
                    notes.append("The claim grew past 100,000 dollars while deferred and was "
                                 "submitted uncertified: over the threshold, an uncertified "
                                 "claim is not a claim at all and the Contracting Officer has "
                                 "no duty to decide it (FAR 52.233-1, 41 USC 7103).")
                else:
                    # The lookback (trap 3, unchanged from run 2): recoverable shrinks.
                    s["dispute"]["status"] = "escalated"
                    s["dispute"]["entitlement"] = "preserved"
                    s["dispute"]["pending_recovery"] = _discount(round(
                        s["dispute"]["estimated_cost"] * position["recoverable_fraction"], 2))
        if dsc_open:
            dpos = dsc_position(s)
            if dpos["expired"]:
                s["dsc"]["status"] = "escalated"
                s["dsc"]["entitlement"] = "lost"
                if form_name == "A201-2017":
                    # Trap 1, fired: the trainee who applied the 21 day claim period to a site
                    # condition finds the 14 day period ran before the first review.
                    notes.append("The differing site condition required notice within 14 days "
                                 "of first observance (Section 3.7.4), and "
                                 f"{s['dsc']['days_since_event']} days have passed. The 21 day "
                                 "claim period (Section 15.1.3.1) does not apply to site "
                                 "conditions.")
                elif form_name == "ConsensusDocs 200":
                    notes.append("The affected work was not stopped and the notice was not "
                                 "prompt (Section 3.16.2); the site condition claim is lost.")
                else:
                    notes.append("The conditions were disturbed before notice was given "
                                 "(FAR 52.236-2(a)); the Government can no longer verify "
                                 "them, and the entitlement is gone.")
            else:
                s["dsc"]["status"] = "escalated"
                s["dsc"]["entitlement"] = "preserved"
                s["dsc"]["pending_recovery"] = _discount(s["dsc"]["estimated_cost"])
                notes.append("The site condition was noticed at the first opportunity and "
                             "the entitlement is preserved.")
    elif decision == "absorb" and (dispute_open or dsc_open):
        for matter, label in ((s["dispute"] if dispute_open else None, "change"),
                              (s["dsc"] if dsc_open else None, "site condition")):
            if matter is None:
                continue
            cost = matter["estimated_cost"]
            drawn = min(cost, s["contingency_remaining"])
            s["contingency_remaining"] = round(s["contingency_remaining"] - drawn, 2)
            s["ac"] = round(s["ac"] + cost, 2)
            matter["status"] = "absorbed"
            matter["entitlement"] = "waived"
        # Correction 3, the earning side: a concession is one PROGRESS STEP, and it takes
        # CRED_EARN_CONCESSIONS of them to earn a point. One act, one step, however many
        # matters it absorbed.
        s["credibility_progress"] = s["credibility_progress"] + 1
        if s["credibility_progress"] >= CRED_EARN_CONCESSIONS:
            s["owner_credibility"] = min(CRED_MAX, s["owner_credibility"] + 1)
            s["credibility_progress"] = 0
            notes.append("Sustained concessions have earned a point of owner credibility.")
        else:
            notes.append("A concession builds goodwill, but one is not enough to earn a "
                         "credibility point.")
    elif decision == "defer" and (dispute_open or dsc_open):
        s["float_consumed_days"] = s["float_consumed_days"] + profile["defer_drift_float_days"]
        s["ac"] = round(s["ac"] + bac * DEFER_DRIFT_COST_RATE, 2)
        notes.append(f"Deferral drift: {profile['defer_drift_float_days']} float days and "
                     f"{DEFER_DRIFT_COST_RATE * 100:.1f} percent of contract value while a "
                     "matter stays open. Waiting has a price before the cliff.")
        if dispute_open:
            s["dispute"]["days_since_event"] = s["dispute"]["days_since_event"] + PERIOD_DAYS
            if form_name == "Federal FAR":
                # Trap 4's setup: a deferred federal claim GROWS, and crossing the threshold
                # while deferred is what makes next period's escalation uncertified.
                previous = s["dispute"]["estimated_cost"]
                s["dispute"]["estimated_cost"] = round(
                    previous + bac * FAR_CLAIM_GROWTH_RATE, 2)
                if previous <= FAR_CERTIFICATION_THRESHOLD \
                        < s["dispute"]["estimated_cost"]:
                    s["claim_crossed_threshold_last_period"] = True
                    notes.append("The deferred claim has grown past 100,000 dollars. Claims "
                                 "over the threshold must be certified (FAR 52.233-1).")
            position = notice_position(s)
            if position.get("expired"):
                s["dispute"]["entitlement"] = "lost"
        if dsc_open:
            s["dsc"]["days_since_event"] = s["dsc"]["days_since_event"] + PERIOD_DAYS
            s["dsc"]["first_opportunity"] = False
    elif decision == "accelerate":
        recovered = min(EVENT_FIGURES["acceleration_float_recovered_days"],
                        s["float_consumed_days"])
        s["float_consumed_days"] = s["float_consumed_days"] - recovered
        premium = round(bac * EVENT_FIGURES["acceleration_cost_rate"]
                        * profile["acceleration_cost_multiplier"], 2)
        s["ac"] = round(s["ac"] + premium, 2)
        s["hazard"] = round(s["hazard"] + EVENT_FIGURES["acceleration_hazard_per_use"], 2)
        notes.append(f"Acceleration recovered {recovered} float days at a premium, and a "
                     "compressed site carries a higher chance of an incident.")
        # A dispute left open while accelerating still ages: nobody tended the notice. The
        # site condition ages the same way, and a period of compressed work disturbs it.
        if dispute_open:
            s["dispute"]["days_since_event"] = s["dispute"]["days_since_event"] + PERIOD_DAYS
            if notice_position(s).get("expired"):
                s["dispute"]["entitlement"] = "lost"
        if dsc_open:
            s["dsc"]["days_since_event"] = s["dsc"]["days_since_event"] + PERIOD_DAYS
            s["dsc"]["first_opportunity"] = False
    elif decision in RESPONSES:
        figures = EVENT_FIGURES["response"][decision]
        days_lost = figures["days_lost"][s["conditions"]]
        s["float_consumed_days"] = s["float_consumed_days"] + days_lost
        s["ac"] = round(s["ac"] + bac * figures["cost_rate"], 2)
        s["incident"] = {
            "status": "restarting",
            "cause": s["incident"].get("cause"),
            "period_occurred": s["incident"].get("period_occurred"),
            "response": decision,
            "days_lost": days_lost,
            "restart_periods_left": figures["restart_periods"],
        }
        s["incidents"][-1] = {**s["incidents"][-1], "response": decision,
                              "days_lost": days_lost}
        notes.append(f"The stop work order cost {days_lost} days: the duration followed the "
                     "response, not the incident.")
        # The correction package consumed the attention the notice needed: an open dispute
        # still ages through a stoppage, and so does an open site condition.
        if dispute_open:
            s["dispute"]["days_since_event"] = s["dispute"]["days_since_event"] + PERIOD_DAYS
            if notice_position(s).get("expired"):
                s["dispute"]["entitlement"] = "lost"
        if dsc_open:
            s["dsc"]["days_since_event"] = s["dsc"]["days_since_event"] + PERIOD_DAYS
            s["dsc"]["first_opportunity"] = False
    # A decision recorded after the dispute has closed changes nothing but the record: the
    # period still progresses above, and the decision is still logged below. Stated rather
    # than refused, because "there is nothing left to decide" is itself something the next
    # period's screen should show.

    # ---- liquidated damages exposure follows float, mechanically.
    over = max(0, s["float_consumed_days"] - s["float_total_days"])
    s["liquidated_damages_exposure"] = round(over * s["liquidated_damages_per_day"], 2)
    if over:
        notes.append(f"Float is exhausted: {over} days beyond the contract date at "
                     f"{s['liquidated_damages_per_day']:,.0f} dollars per day.")

    s["decisions"].append({"period": s["period"], "decision": decision})
    s["period"] = s["period"] + 1

    # ---- the differing site condition is discovered as period DSC_PERIOD opens (run 4).
    # Day 3 of the period, 17 days before its decision day: inside A201's 21 day claim window
    # and outside its 14 day site-conditions window, which is trap 1's geometry. Undisclosed
    # until now, like the near miss below.
    if s["period"] == DSC_PERIOD and s.get("dsc") is None:
        s["dsc"] = {
            "status": "open",
            "entitlement": "undecided",
            "estimated_cost": round(bac * DSC_COST_RATE, 2),
            "estimated_days": DSC_DAYS,
            "days_since_event": DECISION_DAY - DSC_DISCOVERY_DAY,
            "first_opportunity": True,
            "recovered_amount": None,
            "pending_recovery": None,
        }
        notes.append("A differing site condition was uncovered on day 3 of this period: "
                     "rock where the borings showed soil. Its notice runs on its own clock, "
                     "under its own clause, per the contract form in the brief.")

    # ---- the discrete event trigger, for the period now beginning. Deterministic: the base
    # near miss is scheduled by the run's geometry (never disclosed in advance), and the
    # hazard the trainee raised by accelerating fires a further one at the threshold. Every
    # near miss converts to a stop work order at the designed rate of 1.0 this run. The
    # incident itself costs little; the stop work order is the mechanism.
    if s["incident"].get("status") in (None, "none"):
        cause = None
        if s["period"] == EVENT_FIGURES["near_miss_period"] \
                and not any(i.get("cause") == "scheduled" for i in s["incidents"]):
            cause = "scheduled"
        elif s["hazard"] >= EVENT_FIGURES["hazard_threshold"]:
            s["hazard"] = round(s["hazard"] - EVENT_FIGURES["hazard_threshold"], 2)
            cause = "acceleration"
        if cause is not None:
            s["ac"] = round(s["ac"] + bac * EVENT_FIGURES["incident_direct_cost_rate"], 2)
            s["incident"] = {"status": "stopped", "cause": cause,
                             "period_occurred": s["period"]}
            s["incidents"].append({"cause": cause, "period_occurred": s["period"]})
            notes.append(
                "A near miss on site has become a stop work order. All work has stopped "
                "except safety work. Lifting requires a Certificate of Correction plus "
                "whatever the cause demands; the response decides the duration."
                + (" The compressed schedule from acceleration is the cause."
                   if cause == "acceleration" else ""))

    # ---- correction 1's visibility: what this advance actually changed, stated.
    s["period_changes"] = {
        "decision": decision,
        "float_days_spent": s["float_consumed_days"] - before["float"],
        "cost_added": round(s["ac"] - before["ac"] - period_earn, 2),
        "contingency_spent": round(before["contingency"] - s["contingency_remaining"], 2),
        "credibility_change": s["owner_credibility"] - before["credibility"],
        "notes": notes,
    }
    return s


def signal_inputs_from_state(state: dict[str, Any]) -> tuple[dict[str, Any], date]:
    """
    Project the state into the platform's signalInputs vocabulary, and the period's cutoff.

    EVERY key the merge would produce exists, in the merge's own order, with None for anything
    the training state genuinely does not know — docRiskScore, quality figures, RFI ledgers —
    so abstention applies exactly as it does on a real project. cpi and spi are derived here
    with the same expression and rounding the merge uses (ev over ac, ev over pv, three
    places), never stored on the state, so the two layers cannot disagree about a ratio.
    """
    from .extraction_merge import SIGNAL_INPUT_KEYS

    period = state["period"]
    dates = period_dates(period)
    si: dict[str, Any] = {k: None for k in SIGNAL_INPUT_KEYS}

    si["bac"] = state["bac"]
    si["ev"] = state["ev"]
    si["ac"] = state["ac"]
    si["pv"] = state["pv"]
    if state["bac"]:
        si["actualPctComplete"] = _round3(state["ev"] / state["bac"] * 100)
        si["plannedPctComplete"] = _round3(state["pv"] / state["bac"] * 100)
    si["baselineStart"] = SCHEDULE_START.isoformat()
    si["baselineEnd"] = (SCHEDULE_START
                         + timedelta(days=PERIODS_TOTAL * PERIOD_DAYS - 1)).isoformat()
    si["workPeriodFrom"] = dates["from"]
    si["workPeriodTo"] = dates["to"]
    si["docDate"] = dates["decision"]
    si["totalFloat"] = state["float_total_days"]
    si["consumedFloat"] = state["float_consumed_days"]
    si["floatRemaining"] = state["float_total_days"] - state["float_consumed_days"]
    si["originalContingency"] = state["contingency_original"]
    si["remainingContingency"] = state["contingency_remaining"]
    si["baselineContractSum"] = state["baseline_contract_sum"]
    si["revisedContractSum"] = state["revised_contract_sum"]
    si["changeOrderCount"] = state["change_order_count"] or None

    si["sources"] = {}
    si["cpi"] = _round3(state["ev"] / state["ac"]) if state["ac"] else None
    si["spi"] = _round3(state["ev"] / state["pv"]) if state["pv"] else None

    cutoff = date.fromisoformat(dates["decision"])
    return si, cutoff


def build_disclaimer(contract_form: str) -> dict[str, Any]:
    """
    Run 4, Part 3: operational training material, NOT a legal notice. States which rules the
    run uses and which figures are designed rather than sourced. The platform's approved
    notice text stands unchanged and is not restated or paraphrased here; nothing in this
    block is liability or consent language.
    """
    form = CONTRACT_FORMS[contract_form]
    return {
        "governing_form": form["label"],
        "jurisdiction": "United States",
        "amendment_note": (
            f"This run applies the periods of {form['label']} as published. Contract periods "
            "are routinely amended in negotiation, so a real project may not match its own "
            "form. The first move on any real project is to check which rules actually "
            "govern."),
        "sourced_figures": (
            "The notice periods, clause citations, certification threshold and cost lookback "
            "follow the named contract form and public law, as recorded in "
            "training_us_contract_regimes.md."),
        "designed_figures": (
            "Everything else is a designed training figure with no external authority: the "
            "decision effects and their drift, the escalation cost curve, the credibility "
            "mechanics, the liquidated damages band and its facility rates, the acceleration "
            "cost and hazard figures, the stoppage durations and restart productivity "
            "losses, and the event schedule."),
    }
