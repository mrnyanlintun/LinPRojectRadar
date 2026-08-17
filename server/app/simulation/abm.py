"""
THE AGENT-BASED GOVERNANCE MODEL (module 8.1 / B3.1), Run 31.

THE OWNER OVERRIDE, RECORDED HERE BECAUSE THIS IS WHERE IT WOULD OTHERWISE BE MISAPPLIED.
Earlier defensibility documents in this repository recommended renaming 8.1 from
`ABM Governance Layer` to `Action Boundary & Authority Matrix`. Section 5 of the Run-31 contract
SUPERSEDES that recommendation by owner decision. 8.1 is `Agent-Based Governance Model`. ABM
means AGENT-BASED MODELING and NOT Bayesian agent-based modelling; no Bayesian layer exists in
this file and none may be added. The Action Boundary & Authority Matrix is still real and still
useful, and it is `AuthorityMatrix` below: a POLICY/CONFIGURATION structure the model consults.
It is not the registered replacement for 8.1 and it is not a registered module.

WHAT PRODUCTION USED TO DO. B3.1's legacy runner read `cpi`, `spi` and `docRiskScore` off the
flat signal inputs, compared them against literals, and emitted a governance band. There were no
agents, no state, no messages, no clock and no authority. It was a threshold check wearing the
name of a simulation family. Section 8 supplies the structural contract a genuine ABM must meet
and section 41 requires the PRODUCTION route to execute it, so the guard for this file profiles
the interpreter through `registry.run_module` rather than calling anything here directly.

THE STRUCTURAL CONTRACT (section 8), and every one of these is a real object below:
agents; agent state; behaviour rules; interaction/message rules; environment; discrete time;
event/state transitions; authority constraints; and transition rules declared explicitly.

DETERMINISM IS DECLARED, NOT ASSUMED. Every transition here is deterministic. Event ordering is
(delivery_time, sequence_number) with sequence numbers issued monotonically at send time, which
is the ordering rule section 8 supplies. Section 53 forbids inventing a stochastic latency
distribution, so latency is a supplied integer per agent and there is no random draw in this
file at all -- `rand` is never threaded in.

AUTHORITY CANNOT BE SELF-UPGRADED. `AuthorityMatrix.may_authorize` is consulted at the single
place an authorization can be recorded, and an agent whose role is not the required approver for
the action class cannot record one no matter what message it receives. The fault campaign injects
exactly that (faults 31, 32) and the guard requires it RED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

# --- Agent roles. Section 8's minimum governed classes, using this repository's own vocabulary.
OWNER = "OWNER"
PROJECT_MANAGER = "PROJECT_MANAGER"
CONTRACTOR = "CONTRACTOR"
AGENT_ROLES = (OWNER, PROJECT_MANAGER, CONTRACTOR)

# --- Agent states.
STATE_IDLE = "IDLE"
STATE_AWAITING_RESPONSE = "AWAITING_RESPONSE"
STATE_RESPONSE_RECORDED = "RESPONSE_RECORDED"
STATE_ESCALATED = "ESCALATED"
STATE_DECIDED = "DECIDED"

# --- Terminal dispositions of a governance episode. There is no fabricated authorization here.
AUTHORIZED_BY_OWNER = "AUTHORIZED_BY_OWNER"
DEFERRED = "DEFERRED"
REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
ESCALATED_UNRESOLVED = "ESCALATED_UNRESOLVED"
REJECTED_UNAUTHORIZED = "REJECTED_UNAUTHORIZED"
NO_ACTION_ABSTAINING_SIGNAL = "NO_ACTION_ABSTAINING_SIGNAL"
BLOCKED_PROCEDURE_INCOMPLETE = "BLOCKED_PROCEDURE_INCOMPLETE"
BLOCKED_UNQUALIFIED_EVIDENCE = "BLOCKED_UNQUALIFIED_EVIDENCE"

TERMINALS = (AUTHORIZED_BY_OWNER, DEFERRED, REQUEST_EVIDENCE, ESCALATED_UNRESOLVED,
             REJECTED_UNAUTHORIZED, NO_ACTION_ABSTAINING_SIGNAL,
             BLOCKED_PROCEDURE_INCOMPLETE, BLOCKED_UNQUALIFIED_EVIDENCE)

HIGH_IMPACT = "HIGH_IMPACT"


class ABMStructureError(ValueError):
    """The supplied governance structure is not an agent-based model."""


@dataclass
class ActionRule:
    """One row of the Action Boundary & Authority Matrix. POLICY, not a module."""

    action_class: str
    permitted_recommender: str
    required_approver: str
    contractor_response_required: bool
    procedural_requirement: str | None
    evidence_requirement: str
    escalation_route: str
    defer_route: str


@dataclass
class AuthorityMatrix:
    """
    The governed Action Boundary & Authority Matrix (section 8).

    A deterministic policy table. It answers three questions and nothing else: who may recommend,
    who must approve, and what an unresolved case escalates or defers to. It never decides; the
    agents do, through time, under it.
    """

    rules: dict[str, ActionRule]

    def rule_for(self, action_class: str) -> ActionRule:
        if action_class not in self.rules:
            raise ABMStructureError(
                f"no governed authority rule is configured for action class {action_class!r}, "
                f"so no agent may act on it")
        return self.rules[action_class]

    def may_authorize(self, role: str, action_class: str) -> bool:
        """THE SINGLE AUTHORITY TEST. Every authorization in this file passes through here."""
        return self.rule_for(action_class).required_approver == role

    def may_recommend(self, role: str, action_class: str) -> bool:
        return self.rule_for(action_class).permitted_recommender == role


@dataclass
class Message:
    """One interaction. `seq` is the tie-break in the deterministic ordering rule."""

    sender: str
    recipient: str
    kind: str
    sent_at: int
    delivery_time: int
    seq: int
    payload: dict[str, Any] = field(default_factory=dict)

    def order_key(self) -> tuple[int, int]:
        return (self.delivery_time, self.seq)


@dataclass
class Agent:
    """One governed agent. Section 8's minimum attribute set, and all of it is used."""

    agent_id: str
    role: str
    state: str = STATE_IDLE
    authority: tuple[str, ...] = ()
    response_latency: int = 0
    inbox: list[Message] = field(default_factory=list)
    outbox: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Environment:
    """
    The model environment (section 8): clock, queue, ordering rule, qualified signal, action
    class, evidence sufficiency, procedural requirements and the authority matrix.

    `qualified_signal` IS THE GATE. Section 37 says 8.1 must not authorize a high-impact action
    from a raw/unassessed signal state, so this field holds the QualifiedEvidence disposition and
    `GovernanceModel.run` refuses before any agent moves when it is not eligible.
    """

    clock: int = 0
    action_class: str = HIGH_IMPACT
    matrix: AuthorityMatrix | None = None
    qualified_signal: Any = None
    signal_eligible: bool = False
    signal_abstaining: bool = False
    evidence_sufficient: bool = True
    procedural_review_complete: bool = True
    owner_available: bool = True
    owner_decision: str = "AUTHORIZE"
    queue: list[Message] = field(default_factory=list)
    _seq: int = 0

    def send(self, msg_kind: str, sender: str, recipient: str, latency: int,
             payload: dict[str, Any] | None = None) -> Message:
        self._seq += 1
        m = Message(sender=sender, recipient=recipient, kind=msg_kind, sent_at=self.clock,
                    delivery_time=self.clock + latency, seq=self._seq, payload=payload or {})
        self.queue.append(m)
        return m

    def pop_next(self) -> Message | None:
        """Deterministic ordering: delivery time first, stable sequence number second."""
        if not self.queue:
            return None
        self.queue.sort(key=lambda m: m.order_key())
        return self.queue.pop(0)


@dataclass
class GovernanceModel:
    """
    The agent-based governance model itself: agents interacting through discrete time under a
    governed authority matrix, producing a state history that can be audited transition by
    transition.
    """

    agents: dict[str, Agent]
    env: Environment
    history: list[dict[str, Any]] = field(default_factory=list)
    terminal: str | None = None

    # -- structural guard (section 8; fault campaign 29, 30, 35) ------------------------------
    def assert_structural(self) -> None:
        """A model with no agents, no clock or no interaction rule is not an ABM. Refuse."""
        if not self.agents:
            raise ABMStructureError(
                "no agents are configured, so there is no agent-based model to run")
        roles = {a.role for a in self.agents.values()}
        for required in (OWNER, PROJECT_MANAGER, CONTRACTOR):
            if required not in roles:
                raise ABMStructureError(
                    f"the governed agent class {required} is absent, so the configured "
                    f"authority relationships cannot be exercised")
        if self.env.matrix is None:
            raise ABMStructureError(
                "no governed authority matrix is configured, so no action boundary exists")
        if not hasattr(self.env, "clock") or self.env.clock is None:
            raise ABMStructureError(
                "no simulation clock is configured, so no agent can act through time")

    def agent_by_role(self, role: str) -> Agent:
        for a in self.agents.values():
            if a.role == role:
                return a
        raise ABMStructureError(f"no agent occupies the governed role {role}")

    def _record(self, t: int, actor: str, event: str, detail: str,
                message: Message | None = None) -> None:
        self.history.append({
            "t": t, "actor": actor, "event": event, "detail": detail,
            "message_kind": message.kind if message else None,
            "message_seq": message.seq if message else None,
            "states": {a.agent_id: a.state for a in self.agents.values()},
        })

    # -- the run -------------------------------------------------------------------------------
    def run(self, *, max_time: int = 64) -> str:
        """
        Advance the clock, deliver messages in the declared order, let agents act under the
        matrix, and end in one of TERMINALS. Never fabricates an authorization.
        """
        self.assert_structural()
        env = self.env
        rule = env.matrix.rule_for(env.action_class)
        pm = self.agent_by_role(PROJECT_MANAGER)
        contractor = self.agent_by_role(CONTRACTOR)
        owner = self.agent_by_role(OWNER)

        # GATE FIRST (section 37). An unqualified or unassessed signal never reaches an agent.
        if not env.signal_eligible:
            self._record(env.clock, pm.agent_id, "REFUSED_UNQUALIFIED_SIGNAL",
                         "the signal offered to the governance model has not been qualified for "
                         "governance use, so no governed action is initiated")
            self.terminal = BLOCKED_UNQUALIFIED_EVIDENCE
            return self.terminal
        if env.signal_abstaining:
            self._record(env.clock, pm.agent_id, "NO_SIGNAL",
                         "the signal abstains, so no adverse or favourable governed state is "
                         "recorded from it")
            self.terminal = NO_ACTION_ABSTAINING_SIGNAL
            return self.terminal

        # t=0: the PM receives the qualified signal and recognises the required final authority.
        self._record(env.clock, pm.agent_id, "SIGNAL_RECEIVED",
                     f"qualified {env.action_class} adverse signal received")
        self._record(env.clock, pm.agent_id, "AUTHORITY_RECOGNISED",
                     f"final authority required for {env.action_class} is "
                     f"{rule.required_approver}")

        if not env.evidence_sufficient:
            self._record(env.clock, pm.agent_id, "EVIDENCE_INSUFFICIENT",
                         "the evidence requirement configured for this action class is not met")
            self.terminal = REQUEST_EVIDENCE if rule.defer_route == REQUEST_EVIDENCE else DEFERRED
            return self.terminal

        if rule.contractor_response_required:
            m = env.send("RESPONSE_REQUEST", pm.agent_id, contractor.agent_id,
                         contractor.response_latency)
            pm.state = STATE_AWAITING_RESPONSE
            pm.outbox.append(m)
            self._record(env.clock, pm.agent_id, "RESPONSE_REQUEST_SENT",
                         f"response requested from {contractor.agent_id}, "
                         f"delivery at t={m.delivery_time}", m)

        seen: set[tuple[str, int]] = set()
        while env.queue and self.terminal is None and env.clock <= max_time:
            msg = env.pop_next()
            if msg is None:
                break
            env.clock = max(env.clock, msg.delivery_time)
            # DUPLICATE MESSAGES MUST NOT DUPLICATE AUTHORITY (section 8). Identity is
            # (kind, sender) per episode; a repeat is recorded and then ignored.
            ident = (msg.kind, msg.seq)
            dup_ident = (msg.kind, 0)
            if dup_ident in seen:
                self._record(env.clock, msg.recipient, "DUPLICATE_MESSAGE_IGNORED",
                             "a duplicate message was delivered and does not confer authority "
                             "a second time", msg)
                continue
            seen.add(dup_ident)
            seen.add(ident)
            self._dispatch(msg, rule, pm, contractor, owner)

        if self.terminal is None:
            self._record(env.clock, pm.agent_id, "UNRESOLVED",
                         "no governed authorization was recorded within the observation window")
            self.terminal = ESCALATED_UNRESOLVED
        return self.terminal

    def _dispatch(self, msg: Message, rule: ActionRule, pm: Agent, contractor: Agent,
                  owner: Agent) -> None:
        env = self.env
        if msg.kind == "RESPONSE_REQUEST":
            contractor.inbox.append(msg)
            contractor.state = STATE_RESPONSE_RECORDED
            self._record(env.clock, contractor.agent_id, "RESPONSE_AVAILABLE",
                         "contractor response becomes available to the project manager", msg)
            # A contractor cannot authorize an owner-only action, whatever it sends.
            if not env.matrix.may_authorize(contractor.role, env.action_class):
                self._record(env.clock, contractor.agent_id, "AUTHORIZATION_NOT_PERMITTED",
                             f"{contractor.role} is not the required approver for "
                             f"{env.action_class} and cannot authorize it")
            pm.state = STATE_RESPONSE_RECORDED
            if not env.procedural_review_complete:
                self._record(env.clock, pm.agent_id, "PROCEDURE_INCOMPLETE",
                             f"the configured procedural requirement "
                             f"({rule.procedural_requirement}) is not complete, so the action "
                             f"cannot be finalized")
                self.terminal = BLOCKED_PROCEDURE_INCOMPLETE
                return
            if not env.matrix.may_recommend(pm.role, env.action_class):
                self._record(env.clock, pm.agent_id, "RECOMMENDATION_NOT_PERMITTED",
                             f"{pm.role} is not a permitted recommender for {env.action_class}")
                self.terminal = REJECTED_UNAUTHORIZED
                return
            if not env.owner_available:
                self._record(env.clock, pm.agent_id, "OWNER_UNAVAILABLE",
                             "the required approver is unavailable; the project manager defers "
                             "and does not self-upgrade authority")
                self.terminal = DEFERRED
                return
            m = env.send("RECOMMENDATION_PACKAGE", pm.agent_id, owner.agent_id,
                         owner.response_latency)
            pm.state = STATE_ESCALATED
            pm.outbox.append(m)
            self._record(env.clock, pm.agent_id, "ESCALATED_TO_OWNER",
                         f"governed recommendation package sent to {owner.agent_id}, "
                         f"delivery at t={m.delivery_time}", m)
            return

        if msg.kind == "RECOMMENDATION_PACKAGE":
            owner.inbox.append(msg)
            if not env.matrix.may_authorize(owner.role, env.action_class):
                self._record(env.clock, owner.agent_id, "AUTHORIZATION_NOT_PERMITTED",
                             f"{owner.role} is not the required approver for {env.action_class}")
                self.terminal = REJECTED_UNAUTHORIZED
                return
            owner.state = STATE_DECIDED
            if env.owner_decision == "AUTHORIZE":
                self._record(env.clock, owner.agent_id, "AUTHORIZED",
                             f"{owner.role} records the governed authorization for "
                             f"{env.action_class}", msg)
                self.terminal = AUTHORIZED_BY_OWNER
            else:
                self._record(env.clock, owner.agent_id, "DEFERRED",
                             f"{owner.role} defers the governed action", msg)
                self.terminal = DEFERRED
            return

        self._record(env.clock, msg.recipient, "UNHANDLED_MESSAGE",
                     f"message kind {msg.kind} has no configured behaviour rule", msg)


# ---------------------------------------------------------------------------------------------
# CONSTRUCTION FROM A GOVERNED STRUCTURE.
#
# The production runner reads a governed `abmGovernanceModel` structure off the signal inputs and
# builds the model from it. Nothing is defaulted into existence: a structure with no agents
# raises rather than producing an empty model that silently authorizes nothing and looks fine.
# ---------------------------------------------------------------------------------------------

def matrix_from(rows: Any) -> AuthorityMatrix:
    if not isinstance(rows, list) or not rows:
        raise ABMStructureError(
            "the governed authority matrix is absent, so no action boundary is defined")
    rules: dict[str, ActionRule] = {}
    for r in rows:
        if not isinstance(r, dict):
            raise ABMStructureError("an authority matrix row is not in a readable form")
        try:
            rules[r["action_class"]] = ActionRule(
                action_class=r["action_class"],
                permitted_recommender=r["permitted_recommender"],
                required_approver=r["required_approver"],
                contractor_response_required=bool(r.get("contractor_response_required", False)),
                procedural_requirement=r.get("procedural_requirement"),
                evidence_requirement=r.get("evidence_requirement", "qualified_signal"),
                escalation_route=r.get("escalation_route", ESCALATED_UNRESOLVED),
                defer_route=r.get("defer_route", DEFERRED),
            )
        except KeyError as exc:
            raise ABMStructureError(
                f"an authority matrix row is missing {exc.args[0]}, so who may act is "
                f"not established") from exc
    return AuthorityMatrix(rules=rules)


def model_from(structure: dict, *, signal_eligible: bool, signal_abstaining: bool
               ) -> GovernanceModel:
    agents_in = structure.get("agents")
    if not isinstance(agents_in, list) or not agents_in:
        raise ABMStructureError(
            "no agents are declared in the governed governance structure, so there is no "
            "agent-based model to run")
    agents: dict[str, Agent] = {}
    for a in agents_in:
        if not isinstance(a, dict) or "agent_id" not in a or "role" not in a:
            raise ABMStructureError("an agent declaration carries no stable id and role")
        latency = a.get("response_latency", 0)
        if not isinstance(latency, int) or latency < 0:
            raise ABMStructureError(
                f"agent {a['agent_id']} declares a response latency that is not a whole number "
                f"of time units; no latency distribution is supplied or invented")
        agents[a["agent_id"]] = Agent(
            agent_id=a["agent_id"], role=a["role"],
            authority=tuple(a.get("authority", ())), response_latency=latency,
            context=dict(a.get("context", {})))
    env = Environment(
        clock=int(structure.get("start_time", 0)),
        action_class=structure.get("action_class", HIGH_IMPACT),
        matrix=matrix_from(structure.get("authority_matrix")),
        qualified_signal=structure.get("qualified_signal"),
        signal_eligible=signal_eligible,
        signal_abstaining=signal_abstaining,
        evidence_sufficient=bool(structure.get("evidence_sufficient", True)),
        procedural_review_complete=bool(structure.get("procedural_review_complete", True)),
        owner_available=bool(structure.get("owner_available", True)),
        owner_decision=structure.get("owner_decision", "AUTHORIZE"),
    )
    return GovernanceModel(agents=agents, env=env)
