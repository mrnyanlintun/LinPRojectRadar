# Category B3 — Regulatory and Authority Thresholds

Five modules: B3.1, B3.2, B3.3, B3.4, B3.5.

**These are rule checks, not measurements.** Each answers a question about authority, applicability
or conformance against a stated instrument, and each answers in a **fixed vocabulary**, never in a
score and never in a colour. **No module in this category has a band and none may be given one.**
All five are routed through `models_cat89._route`, which sets `status_color: None` and
`band_asserted: False` and re-asserts `status_color = None` after the canonical result is merged.

## The vocabulary, and it is closed

Rule dispositions, from `regulatory.RULE_DISPOSITIONS`:
`SATISFIED`, `NOT_SATISFIED`, `NOT_APPLICABLE`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`.

Applicability states, from `regulatory.APPLICABILITY_STATES`, which answer a **different question**
and share two names with the above by name only:
`APPLICABLE`, `NOT_APPLICABLE`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`.

## The one permitted form of words

Every rule result carries a `statement`, and there is exactly one template it may take
(`regulatory.CONFORMANCE_SENTENCE`):

> `"Available governed evidence {verb} the configured rule check under {citation} ({edition},
> effective {effective_date}), subject to responsible-authority review."`

with `{verb}` taken from a closed table: `SATISFIED` → *satisfies*; `NOT_SATISFIED` → *does not
satisfy*; `INSUFFICIENT_EVIDENCE` → *is insufficient for*; `REVIEW_REQUIRED` → *requires
responsible-authority review for*; `NOT_APPLICABLE` → *is not within the applicability of*.

**A specification applying these modules emits that sentence and no other.** It may never say a
project is "FAR compliant", "OMB compliant", "OSHA compliant", "EPA compliant", "legally
compliant", "legally noncompliant" or "certified compliant"; `regulatory.PROHIBITED_CLAIM_PATTERNS`
holds the full list and production output is guarded against it.

## Where the authority comes from

`regulatory.REGULATORY_SNAPSHOT` is the Run-31 supervisory authority snapshot, checked by
supervisory review and reproduced verbatim. **Nothing in this repository fetches a "latest" edition
from anywhere**, because an instrument whose regulatory answers change because a website changed is
not reproducible. Current editions under the snapshot: FAR `FAC 2026-01`; OMB `A-11 2025-08-29`.
**A rule whose edition is not the snapshot edition is superseded and evaluates to
`REVIEW_REQUIRED`.**

## The evaluation precedence, and it is the whole point

`regulatory.evaluate` runs **defect-first**, because every ordering that puts the positive test
earlier admits a positive answer from a rule nobody can date:

```
1. superseded edition            -> REVIEW_REQUIRED
2. applicability unknown         -> INSUFFICIENT_EVIDENCE
3. not applicable                -> NOT_APPLICABLE          (and NOT_APPLICABLE is not satisfied)
4. required evidence missing     -> INSUFFICIENT_EVIDENCE, listing what is missing
5. reviewer required and absent  -> REVIEW_REQUIRED
6. only now, the configured test -> SATISFIED / NOT_SATISFIED
```

The module's own logic is reached **only at step 6**, so no module can obtain a positive result
from a superseded rule or from absent evidence.

## The two shared declines

- **Structure absent**, from `canonical_v6.v6_structure`, writing `W` for the module's plain-words
  structure description: `"Awaiting W. This measure is named for a method that cannot be carried
  out without it, so no reading is reported and no other figure is used in its place."`
  Present but not a mapping: `"The information provided for this project in place of W is not in a
  form this measure can read, so no reading is taken from it."`
- **Evidence not qualified for the module's own use.** The INNER gate, reached only after the
  boundary above has been passed. All five are constructed `gated=True` and put their structure
  through Category 9 qualification before the canonical function is reached. Where the evidence does not qualify, verbatim:
  `"The evidence supplied for this measure has not been qualified for governance use, so no
  governed result is produced from it and no figure is used in its place."`
  Declared uses: `B3.1 governance_authorization` (requires a complete audit chain **and** fresh
  evidence), `B3.2 regulatory_applicability`, `B3.3 regulatory_conformance`,
  `B3.4 regulatory_conformance`, `B3.5 governance_authority_check` (requires a complete audit
  chain).

## The qualification boundary, and it fires BEFORE anything below

Every module in this category is wrapped, **in the dispatch table itself**, by
`qualification_boundary.install`. After that call there is no entry in `registry.VALIDATED` for a
gated module that reaches its runner without the boundary first, and `registry.run_module` looks
the runner up there — **so a consumer cannot route around it by hand-building a signal package.**

The boundary reads the project's declared Category-9 assessment from `signal_inputs` under the key
**`evidenceQualification`**, and asks it for this category's declared use: **`governance_rule_check`**.

**Absence fails closed.** A package carrying no Category-9 assessment is UNASSESSED, and UNASSESSED
is ineligible. Nothing is inferred, nothing is imputed, and the consumer does not execute first and
get stamped afterwards. The refusals, in their exact words and in the order they are reached:

1. **No governed qualification requirement declared for the route** — a configuration failure:
   `"No governed qualification requirement is declared for this route, so it is not executed. An
   undeclared route is a configuration failure and is blocked rather than allowed through."`
2. **`evidenceQualification` absent** — the case a project with no declared assessment reaches:
   `"The evidence offered to this measure carries no Category-9 assessment, so it is unassessed and
   not eligible for this use. No reading is produced and no figure is used in its place."`
3. **Declared but not eligible for this use:** `"The evidence supplied for this measure has not been
   qualified for this use, so it is not read and no figure is produced in its place. "` followed by
   the qualification reasons, joined with `"; "`.

Every one of those carries the reason code `evidence_not_qualified_for_use` and is stamped
`QUALIFICATION_BOUNDARY_V18`, so a reader of the ledger can tell **a refusal by the gate** from **a
module's own abstention**.

**This is the abstention a project with no declared Category-9 assessment will actually see for
every module in this category, and it is reached before any input named below is looked at.** The
per-module abstentions specified further down are what the module says once the boundary has been
passed.


---

## B3.1 — Agent-Based Governance Model

**Identity.** Live id `B3.1`. Method class `ABM_Governance`. A run of the project's own governance
process as a model: who may recommend, who must approve, who must respond, and where the process
actually ends up.

**Required inputs.** `abmGovernanceModel` — a mapping, and the only input read. It carries the
agents, the state each starts in, the authority matrix, the interaction structure and, optionally,
`signal_abstaining`.

**Method — a simulation, not a formula.** `canonical_v6.abm_governance` builds the model from the
structure and **runs it**. Everything real happens in `abm.py`: agents, states, messages, a clock,
**deterministic event ordering**, and the authority matrix. The reported result is the **terminal
state** the model reached, the **final clock time**, the action class, every agent with its role,
state, response latency and message counts, the authority matrix as configured, and the full state
history.

The runner passes `signal_eligible=True` unconditionally, because eligibility has already been
established by the qualification gate above; passing it again would be asking the same question
twice. `signal_abstaining` is read off the structure.

**Bands.** **None. This module asserts no band and none may be attached.** Calibration-pending.

**Interpretation.** The terminal state says where a governance action of this class actually comes
to rest under the authority matrix this project declared — approved, blocked, or stalled awaiting a
party who never responds. It is a statement about the process, not about the project's cost or
schedule.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed agent,
   authority-matrix and interaction structure"*.
2. Evidence not qualified for `governance_authorization` — which for this module requires **a
   complete audit chain and fresh evidence**: the qualification sentence above.
3. The model cannot be built from the structure: the route catches `ABMStructureError` and abstains
   with the message that error carries, so **the ABM's structural refusal surfaces as an abstention
   rather than as a traceback**.

**One property a reader must be told.** The result carries `deterministic: True` and
`stochastic_latency: False`. This module does **not** sample, and it is correctly absent from
`models.STOCHASTIC`.

---

## B3.2 — FAR/Agency EVMS Applicability Monitor

**Identity.** Live id `B3.2`. Method class `EVMS_Applicability`. Does an Earned Value Management
System requirement apply to this acquisition at all?

**Required inputs.** `evmsApplicabilityEvidence` — a mapping, and the only input read. The fields
it is decided from: `federal_context`, `acquisition_designation`, `major_acquisition`, `agency`,
`agency_procedure_requires_evms`, `clause_id`, `evms_not_applicable_established`,
`conflicting_evidence`, `acquisition_id`, `award_date`, `evidence_source`.

**Method — a decision rule, evaluated in this exact precedence.** Governing instrument
`FAR 34.201` (`FAC 2026-01`, effective 2026-03-13).

```
1. conflicting_evidence is non-empty                  -> REVIEW_REQUIRED
2. federal_context is None                            -> INSUFFICIENT_EVIDENCE
3. federal_context is False and agency_procedure_requires_evms is True
                                                      -> APPLICABLE
4. federal_context is False otherwise                 -> NOT_APPLICABLE
5. evms_not_applicable_established is True            -> NOT_APPLICABLE
6. acquisition_designation is None or agency is None  -> INSUFFICIENT_EVIDENCE
7. major_acquisition is True and designation == "development"
                                                      -> APPLICABLE
8. agency_procedure_requires_evms is True, or clause_id present
                                                      -> APPLICABLE
9. major_acquisition is None or agency_procedure_requires_evms is None
                                                      -> INSUFFICIENT_EVIDENCE
10. otherwise                                         -> NOT_APPLICABLE
```

The reason attached to each outcome is fixed and is quoted verbatim:
1. `"the governed applicability evidence conflicts: "` followed by the conflicts joined with `"; "`.
2. `"whether this is a Federal acquisition is not established by the evidence"`.
3. `"a non-Federal contract requirement establishes that EVMS applies"`.
4. `"this is not a Federal acquisition and no contract requirement establishing EVMS applicability
   is recorded"`.
5. `"the governed evidence establishes EVMS is not applicable in this acquisition, agency and
   contract context"`.
6. `"the acquisition designation or agency is not established, and neither is inferred from cost or
   schedule performance"`.
7. `"this is a major acquisition for development under the configured rule"`.
8. `"an explicit agency procedure or contract clause requires EVMS for this acquisition"`.
9. `"major-acquisition status or the applicable agency procedure is not established, so
   applicability is not determined"`.
10. `"this acquisition is not major for development and no agency procedure or clause requiring
    EVMS is recorded"`.

**Bands.** **None. There is no band, no score and no colour here.** The answer is one of the four
applicability states, with its reason and its conformance sentence.

**Interpretation.** Applicability is a question about the **acquisition, the agency, the agency
procedure and the contract clause**, and it is answered from that evidence or not at all.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"governed acquisition,
   agency and clause applicability evidence"*.
2. Evidence not qualified for `regulatory_applicability`: the qualification sentence above.

**The property that matters most here.** **Nothing in this module reads `bac`, `cpi`, `spi`, `ev`
or `ac`, and inferring applicability from any of them is forbidden.** A specification applying this
module must not consult a performance figure under any circumstance, including where the
applicability evidence is thin. Thin evidence produces `INSUFFICIENT_EVIDENCE`; it never produces a
guess.

---

## B3.3 — Versioned A-11 Capital Programming Conformance Check

**Identity.** Live id `B3.3`. Method class `A11_Conformance`. Conformance against **the A-11 rules
the project actually configured**, and nothing beyond them.

**Required inputs.** `a11RuleRegister` — a mapping, and the only input read. It carries
`a11_edition` and a `rules` list; each rule row carries `rule_id`, `section`, `effective_date`,
`summary`, `applicability_conditions`, `required_evidence`, `reviewer_role`, `superseded`,
`applicable`, `evidence`, `satisfied` and `reviewer`.

**Method — a rule check per row.** Each row is constructed as a `RegulatoryRule` under authority
family `OMB`, citation `OMB Circular A-11`, at the register's declared edition, and evaluated
through `regulatory.evaluate` with the precedence given at the head of this file. Where the rule
cannot even be constructed — a `RuleVersionError` — that row's result is `REVIEW_REQUIRED` with the
error's own message as the reason. The module reports every row's result, plus
`configured_subset_result`: a count of rows per disposition.

**Bands.** **None, and no aggregate conformance figure either.** The per-disposition counts are
counts, not a score.

**The ceiling on what this module may claim, and it is on the result itself.** `subset_only` is
`True` on **every** result, `global_a11_claim` is always `None`, and the result carries the note
verbatim: *"this result covers only the rules configured in the supplied register and is not a
statement about Circular A-11 as a whole"*. The summary field is deliberately named
`configured_subset_result` so **no caller can mistake it for a certification**. A specification
applying this module reproduces that ceiling in its own words and never states or implies A-11
conformance as a whole.

**Interpretation.** The reading says what the configured subset of rules came to, one row at a
time. A register of three rules all satisfied is three rules satisfied; it is not a compliant
project.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a configured A-11 rule
   register"*.
2. Evidence not qualified for `regulatory_conformance`: the qualification sentence above.
3. `rules` absent, empty or unreadable: `"Awaiting a configured A-11 rule register. No entries are
   recorded, so there is nothing to assess and no figure is produced in place of one."`

---

## B3.4 — EVMS Reporting Compliance Monitor

**Identity.** Live id `B3.4`. Method class `EVMS_Reporting_Compliance`. Were the required EVMS
reports delivered, on time and complete?

**Required inputs.** `evmsReportingRecord` — a mapping, and the only input read. It must carry
`applicability_evidence` — the B3.2 structure, riding on the reporting record so both are assessed
from the same governed record — together with `clause_id`, `required_cadence`, `due_date`,
`received_date`, `required_artifacts_expected`, `required_artifacts_received`, `reporting_period`,
`exception`, `contract_version` and `provenance`.

**Method — applicability first, then two figures.** Governing instrument `FAR 34.201`.

```
1. Run B3.2's decision rule on applicability_evidence.
   applicability == NOT_APPLICABLE  -> result NOT_APPLICABLE, and NO violation is issued
   applicability != APPLICABLE      -> result INSUFFICIENT_EVIDENCE
2. clause_id or required_cadence absent -> INSUFFICIENT_EVIDENCE
3. ReportingDelayDays   = ReceivedDate - DueDate           (null where either date is absent)
   CompletenessFraction = ArtifactsReceived / ArtifactsExpected   (null unless expected > 0)
4. no received_date                     -> NOT_SATISFIED
   completeness == 1.0 and delay <= 0   -> SATISFIED
   otherwise                            -> NOT_SATISFIED
```

Reasons, verbatim: `"EVMS is not applicable to this acquisition, so no reporting conformance
question arises and no violation is issued"`; `"EVMS applicability is not established, so reporting
conformance is not assessed and no compliance is recorded"`; `"the governing clause or the required
reporting cadence is not recorded, so conformance is not assessed"`; `"no report is recorded as
received for this reporting period"`; `"the configured reporting cadence and artifact set were
met"`; `"the configured reporting cadence or artifact set was not met"`.

`minimum_federal_cadence` is reported as `"monthly"`.

**Bands.** **None. No traffic-light threshold is invented**; the delay in days and the completeness
fraction are reported as they stand.

**Interpretation.** A delay of zero or less and a completeness of exactly 1.0 is the only
satisfied state; anything else is not satisfied. Note that the delay figure is reported even where
the answer is not satisfied, so a reader can see whether the report was a day late or a month late.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed EVMS
   reporting record"*.
2. Evidence not qualified for `regulatory_conformance`: the qualification sentence above.

**Two properties a reader must be told.** First, **this module reads B3.2's answer, not B3.2's
inputs.** Second, **`cpi` and `spi` are not read here and cannot establish anything.** Where
applicability is unresolved the module returns `INSUFFICIENT_EVIDENCE` and **cannot manufacture
compliance**; where applicability is `NOT_APPLICABLE` it **cannot issue a reporting violation**.

---

## B3.5 — Contract Modification Governance Check

**Identity.** Live id `B3.5`. Method class `Modification_Governance`. Was each contract
modification executed by someone with the authority to execute it, in the right form, on the right
instrument?

**Required inputs.** `contractModificationRegister` — a mapping, and the only input read. It
carries `federal_context`, `contract_id` and a `modifications` list; each modification carries
`modification_id`, `executing_official`, `authority_evidence`, `officer_authority_current`,
`modification_type`, `signed_parties`, `sf30_applicable`, `written_instrument`, `contract_id`,
`federal_context`, `issue_date`, `effective_date`, `funding_evidence`, `price_ceiling_status`,
`required_approvals`, `exceptions`, `reviewer` and `provenance`.

**Method — three rule checks per modification**, each through `regulatory.evaluate` with the
precedence at the head of this file. `regime` is `FEDERAL` where `federal_context` is truthy and
`NON_FEDERAL` otherwise, and each rule is applicable only in the federal regime.

**Authority — `FAR 43.102`** (required evidence `modification_id`, `executing_official`,
`authority_evidence`; reviewer role *contracting officer*).
```
satisfied when: authority_evidence is present AND executing_official is present
                AND authority_evidence != "NONE"
then: if satisfied but officer_authority_current is False -> NOT_SATISFIED, reason verbatim
      "the executing official is not recorded as a contracting officer acting within the scope
       of their authority"
```

**Type — `FAR 43.103`** (required evidence `modification_id`, `modification_type`,
`signed_parties`; reviewer role *contracting officer*).
```
modification_type not in ("unilateral", "bilateral")  -> unresolved -> INSUFFICIENT_EVIDENCE
modification_type == "bilateral"  -> satisfied when at least two signed parties
modification_type == "unilateral" -> satisfied
```

**Form — `FAR 43.301`.**
```
applicable = None            when sf30_applicable is None      -> INSUFFICIENT_EVIDENCE
applicable = True            when federal AND sf30_applicable
applicable = False           otherwise                          -> NOT_APPLICABLE
satisfied when: written_instrument is present
```

**Bands.** **None. There is no score and no colour.** Each modification carries three rule results,
each in the closed disposition vocabulary with its own conformance sentence.

**Interpretation.** The reading says, per modification, whether the project can show the authority
under which it was executed — not whether the modification was a good idea and not how much it
cost.

**Abstention.**
1. Structure absent or not a mapping: the two sentences above, with `W` = *"a governed contract
   modification register"*.
2. Evidence not qualified for `governance_authority_check` — which for this module requires **a
   complete audit chain**: the qualification sentence above.
3. `modifications` absent, empty or unreadable: `"Awaiting a governed contract modification
   register. No entries are recorded, so there is nothing to assess and no figure is produced in
   place of one."`

**Two properties a reader must be told, and both are prohibitions.** First, **signature existence
is never authority.** `authority_evidence` is a separate required field from `signed_parties`, and
a modification with signatures but no authority evidence is `INSUFFICIENT_EVIDENCE`, not satisfied.
Second, **this is not A4.6.** There is **no count** in this result: A4.6 owns change frequency and
magnitude exposure, and using a change count as this module's result is forbidden.

---

## Stopped specifications

None. All five modules in this category have unambiguous sources and are specified above.
