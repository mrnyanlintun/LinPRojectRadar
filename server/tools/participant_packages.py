"""
RUN 28 CLOSURE. THE PARTICIPANT PACKAGE CHAIN, DECLARED ONCE.

WHY A DECLARATION FILE. The chain has three links now and each is a different KIND of evidence:
v1 exists only inside a git object, v2 exists only inside a git object, and v3 is the tree you are
standing in. A guard that had to work that out from filenames would eventually get it wrong, and
the failure mode is the one this programme has already met twice -- a record that describes the
CURRENT tree while carrying a PREDECESSOR's name.

THE RULE THIS ENCODES. Exactly one record in the chain describes the live tree, and it is the one
marked current. Every other record must be reconstructible from the commit named beside it and
must NOT match the live tree, because if it did, either nothing changed or a predecessor has been
rewritten to agree with the present.
"""

from __future__ import annotations

from typing import NamedTuple


class Package(NamedTuple):
    identifier: str
    #: The checksum record, relative to the repository root.
    record: str
    #: The commit whose blobs the record describes. `None` means the live working tree.
    source_commit: str | None
    #: Why this link exists at all.
    why: str


#: Oldest first. Append; never edit a row, because each row is the evidence for the results
#: collected under that package.
PARTICIPANT_PACKAGES: tuple[Package, ...] = (
    Package(
        "og-participant-2026.08-v1",
        "code_audit/run12_participant_package_checksums.sha256",
        "c44e3ced94a22a9def35fa5a2be3a2268fbed6bb",
        "Run 12 Gates 11-12 froze the participant package for the study. Fourteen of its seventy "
        "files have legitimately moved on since, through Runs 21 to 26 and the Run-28 closure, so "
        "the LIVE TREE IS NOT EVIDENCE FOR IT and it is reconstructed from this commit.",
    ),
    Package(
        "og-participant-2026.08-v2",
        "code_audit/run28_closure_participant_package_checksums.sha256",
        "0293dc5dff40c66a61bc0f57330611de96c4f7b0",
        "The Run-28 closure's FIRST pass propagated the two approved Category-1 renames -- "
        "Regression to Mean CPI and ICE Ratio -- into assets/js/taxonomy.js, the participant "
        "ledger's own name source, which changed the package checksum and required a successor.",
    ),
    Package(
        "og-participant-2026.08-v3",
        "code_audit/run28_closure_v3_participant_package_checksums.sha256",
        "01e943ef71689c468dd343695fbc89901bc02964",
        "The Run-28 closure's SECOND pass applied the owner's A1.1 decision -- Monte Carlo EAC "
        "becomes Monte Carlo EAC Forecast -- to the naming authority and re-propagated it. Eleven "
        "package files carry that name and their bytes moved after the v2 record was taken. The "
        "second pass REGENERATED THE v2 RECORD IN PLACE instead of creating this successor, which "
        "made a record describe the tree rather than the package it names; the v2 record has been "
        "restored to its frozen bytes and this is the successor that should have been created.",
    ),
    Package(
        "og-participant-2026.08-v4",
        "code_audit/run29_participant_package_v4_checksums.sha256",
        # RUN 30 CLOSURE: v4 is a predecessor now, so it is pinned to the commit whose blobs it
        # describes rather than left reading the working tree. Leaving it on None would make TWO
        # records claim the live tree, which is exactly the masquerade this chain forbids.
        "ce03eb1f297d9615a9eac7dea34356a69846e5a3",
        "RUN 29 removed six proxy qualifiers from the registry, because the six modules they "
        "described -- Weather Day Impact, Change Order Frequency, Dispute Escalation Index, "
        "Subcontractor Performance, Sensitivity Analysis and Tornado Risk Ranking -- now carry "
        "out the canonical method their registered names claim. The defensibility evidence "
        "object served to participants is GENERATED from the registry, so its bytes moved with "
        "them. ONE package file changed and the change is the DELETION of six sentences that "
        "would now be false; no name, no threshold, no sequence step and no behaviour moved. The "
        "v3 record is NOT regenerated: it is pinned to the commit whose blobs it describes, "
        "which is the defect the Run-28 closure had to correct in the v2 record.",
    ),
    Package(
        "og-participant-2026.08-v5",
        "code_audit/run30_participant_package_v5_checksums.sha256",
        # RUN 31 PASS 2: v5 is a predecessor now, so it is pinned to the commit whose blobs it
        # describes rather than left reading the working tree. Leaving it on None would make TWO
        # records claim the live tree, which is exactly the masquerade this chain forbids and the
        # defect the Run-28 closure had to undo in the v2 record.
        "4dd59857c77c2c87aed0f741fd7a0e989efef5f2",
        "THE RUN-30 CLOSURE repointed all twenty Category-7 production identities onto the "
        "canonical layer. Two consequences reach the served defensibility evidence object, which "
        "is GENERATED from the registry and the structure maps. First, eight proxy qualifiers "
        "were deleted, because the eight modules they described no longer compute a proxy at "
        "all. Second, the generator was reading the structure map from canonical.py ALONE, so "
        "fifty-six modules whose defining structures live in the v3, v4 and v5 layers were being "
        "described to a reader as not requiring a canonical structure on the very day their "
        "production routes started requiring one; it now reads all four maps. ONE package file "
        "changed and both changes are corrections of statements that had become false. No name, "
        "no threshold, no sequence step and no participant behaviour moved. The v4 record is NOT "
        "regenerated: it is pinned to the commit whose blobs it describes, which is the defect "
        "the Run-28 closure had to correct in the v2 record.",
    ),
    Package(
        "og-participant-2026.08-v6",
        "code_audit/run31_participant_package_v6_checksums.sha256",
        # RUN 32 PINNED IT. v6 became a predecessor when the Run-32 rename moved eight of its
        # files, so the live tree stopped being its evidence and this is the commit whose blobs
        # it describes. The record itself is NOT regenerated.
        "93942ca03295d642dcbae4551faceca3643aadc8",
        "RUN 31 PASS 2 propagated the six owner-approved Category-8 names to every current "
        "surface, and eight participant-visible files carry a module display name: categories, "
        "decision-ui, deepdive, the two defensibility objects, knowledge, taxonomy and "
        "workspace. The delta is SIX DISPLAY-NAME SUBSTITUTIONS and nothing else -- 8.1 becomes "
        "Agent-Based Governance Model and expressly NOT Action Boundary & Authority Matrix, "
        "which remains the governed policy the model consults rather than a registered module, "
        "and no Bayesian terminology is introduced. No threshold, no evidence-review step, no "
        "preliminary assessment or lock, no AI reveal, no final capture, no final lock and no "
        "period advancement moved: THE EXPERIMENTAL SEQUENCE IS UNCHANGED. The delta is "
        "inverse-mappable -- applying the six reverse substitutions to those eight files "
        "reproduces the v5 bytes exactly, which the package suite asserts. The v5 record is NOT "
        "regenerated: it is pinned to the commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v7",
        "code_audit/run32_participant_package_v7_checksums.sha256",
        # RUN 32 FINAL CLOSURE PINNED IT. v7 became a predecessor when the closure corrected the
        # served defensibility metadata and finished the B4.7 name propagation, so the live tree
        # stopped being its evidence. The record itself is NOT regenerated.
        "93f08bcf36c8675aed3bb4d2b8b83011b8077bc0",
        "RUN 32 applied section 3 of the owner's supervisory contract: the ONE authorised "
        "Category-10 rename, Regret Minimization Index becomes Minimax Regret Decision Rule. The "
        "old name called the module an INDEX and it carried no payoff matrix, so no regret was "
        "defined in it at all -- regret is the gap between an outcome and the best outcome "
        "available in the same future state, and with no matrix of futures there is no best to "
        "measure against. Eight participant-visible files carry the display name: categories, "
        "decision-ui, the two defensibility objects, knowledge, simulations, taxonomy and "
        "workspace. The delta is ONE DISPLAY-NAME SUBSTITUTION and nothing else, and NO OTHER "
        "Category-10 rename is made. No threshold, no evidence-review step, no preliminary "
        "judgment, no preliminary lock, no AI reveal, no final judgment, no rationale or evidence "
        "capture, no final lock and no period advancement moved: THE EXPERIMENTAL SEQUENCE IS "
        "UNCHANGED. The delta is inverse-mappable -- applying the single reverse substitution to "
        "those eight files reproduces the v6 bytes exactly, which the package suite asserts. The "
        "v6 record is NOT regenerated: it is pinned to the commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v8",
        "code_audit/run32_closure_participant_package_v8_checksums.sha256",
        # PINNED when the method-class propagation moved three of its files. NOT regenerated.
        "6e7ce204567a3a3331ee894436cd21748bde381e",
        "THE RUN-32 FINAL CLOSURE corrected the served module-defensibility metadata and finished "
        "the B4.7 current-name propagation. Seven participant-visible files moved: categories, "
        "the defensibility evidence object, knowledge, module charts, neural flow, recommendation "
        "options and taxonomy. THIS DELTA IS NOT A DISPLAY-NAME SUBSTITUTION AND IS NOT CLAIMED "
        "TO BE ONE -- v7's was, and was proved so by inverse mapping; this one CORRECTS "
        "STATEMENTS THAT HAD BECOME FALSE, so only taxonomy.js inverse-maps by the identifier "
        "alone. The defensibility object is regenerated because its generator read four of the "
        "six canonical structure maps and its execution sentence was a binary, so eighty-nine of "
        "one hundred and one records carried a statement false about the current instrument; the "
        "seven Category-10 method descriptions in knowledge.js described the v19 proxies as "
        "current and carried band ladders for a status colour those modules do not emit; and "
        "B4.7's method-class key had stopped matching anything the runner emits, so the "
        "courses-of-action frame and the expected-regret chart had silently gone empty. NO "
        "ANALYTICAL EXECUTION CHANGED, and that is proved rather than asserted: all ninety-five "
        "dispatched modules were executed on identical governed inputs before and after, and "
        "every emitted row is byte-identical under one sha256 over the whole profile. THE "
        "EXPERIMENTAL SEQUENCE IS UNCHANGED: decision.js, decision-ui.js, workspace.js, "
        "deepdive.js and the questionnaires are byte for byte identical to v7. The v7 record is "
        "NOT regenerated: it is pinned to the commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v9",
        "code_audit/run32_b3_participant_package_v9_checksums.sha256",
        # PINNED when the qualifier reconciliation moved four of its files. NOT regenerated.
        "19a70556fe1b6ee8d17706cfbbc5d72e12051086",
        "THE METHOD-CLASS PROPAGATION. Six identifiers had been left behind when their display "
        "names were renamed -- A1.10 and A1.11 by Run 28, B3.2 to B3.5 by Run 31 -- so the client "
        "taxonomy carried an identifier the production runner had stopped emitting. A stale "
        "identifier does not raise: `getModuleStatus` matches the client's method_class against "
        "the server's signal array, the match simply fails, and the lookup returns null, so all "
        "six modules' statuses SILENTLY NEVER RENDERED. That was measured on the pre-change tree "
        "module by module before anything was edited. Three participant-visible files moved: "
        "categories, knowledge and taxonomy. One proxy qualifier the server still holds (B3.5's) "
        "had stopped rendering for the same reason and is restored under the current key; one the "
        "server has WITHDRAWN (A1.10's) was removed rather than renamed. Backward-compatible "
        "aliases are added for STORED ROWS ONLY and the current identifier remains primary. No "
        "analytical execution changed, proved by executing all 95 dispatched modules before and "
        "after on identical inputs under one sha256. THE EXPERIMENTAL SEQUENCE IS UNCHANGED: "
        "decision.js, decision-ui.js, workspace.js, deepdive.js and both questionnaires are byte "
        "for byte identical to v8. The v8 record is NOT regenerated.",
    ),
    Package(
        "og-participant-2026.08-v10",
        "code_audit/run32_qualifier_participant_package_v10_checksums.sha256",
        # PINNED BY RUN 33 when the Portfolio Health remediation moved three of its files. NOT
        # regenerated: this record is the evidence for the results collected under v10.
        "54409af2a07ac989489447379e8379cc9f95e15f",
        "THE PROXY-QUALIFIER RECONCILIATION AND THE ONE CLIENT AUTHORITY. Four participant-"
        "visible files moved: categories, knowledge, taxonomy and the defensibility evidence "
        "object. TWENTY-SEVEN proxy qualifiers were WITHDRAWN from the client map, leaving the "
        "two the server still holds. A proxy qualifier states that a module computes a PROXY "
        "instead of the method its name claims; Runs 28 to 32 repointed twenty-seven of them "
        "onto their canonical methods and withdrew the qualifier as they went, while the client "
        "mirror was never updated, so the handbook went on calling canonical modules proxies. "
        "Classification came from each module's PRODUCTION ROUTE, not from the server's silence. "
        "THREE STALE SERVER QUALIFIERS were withdrawn too (B3.5, B4.3, B4.4), which Runs 31 and "
        "32 had falsified and not removed, so the served defensibility object stopped claiming "
        "B4.3 is an explainable four-rule checklist rather than a constraint-satisfaction solver "
        "about a module that is one. BOTH CLIENT TAXONOMY ARTIFACTS ARE NOW GENERATED from one "
        "authority by build_client_taxonomy.py, so neither is hand-maintained; the two had "
        "already drifted, with nine modules carrying a disabled flag in taxonomy.js and not in "
        "categories.js, and categories.js gains those flags. The runtime taxonomy data is "
        "otherwise unchanged, reproduced row for row. No analytical execution changed, proved by "
        "executing all 95 dispatched modules before and after under one sha256. THE EXPERIMENTAL "
        "SEQUENCE IS UNCHANGED: decision.js, decision-ui.js, workspace.js, deepdive.js and both "
        "questionnaires are byte for byte identical to v9. The v9 record is NOT regenerated.",
    ),
    Package(
        "og-participant-2026.08-v11",
        "code_audit/run33_participant_package_v11_checksums.sha256",
        # RUN 36 CLOSURE: v11 is a predecessor now, so it is pinned to the commit whose blobs it
        # describes rather than left reading the working tree. Leaving it on None would make TWO
        # records claim the live tree, which is exactly the masquerade this chain forbids. The
        # commit is the Run-35 closure head, which is the tree v11's record was taken from.
        "dafc35d35bafe5af76e1ce48ef7daceab9daed2c",
        "THE CANONICAL PORTFOLIO HEALTH LAYER. Three participant-visible files moved: "
        "workspace.js, knowledge.js and the generated defensibility evidence object. THE "
        "PORTFOLIO HEALTH CARD NO LONGER SHOWS A STATUS DOT: every one of the five bands the v20 "
        "snapshot carried was uncalibrated -- the PH.2 percentile cut points, the PH.3 slope "
        "magnitudes, the PH.4 matched-cluster ladder, the PH.5 composite ladder and the PH.1 "
        "ladder hung off a synthetic laboratory threshold -- and a coloured dot is read as a "
        "project condition whatever the caption beside it says. The card now states the governed "
        "cohort, its period, its feature schema, its model version, the small-sample limitation "
        "below ten projects, and the reading or the abstention reason in words. The D1.2 proxy "
        "qualifier is WITHDRAWN from knowledge.js because every clause of it became false when "
        "the canonical layer replaced the proxy. THE EXPERIMENTAL SEQUENCE IS UNCHANGED: "
        "decision.js, decision-ui.js, deepdive.js and both questionnaires are byte for byte "
        "identical to v10, and the workspace.js delta is CONFINED TO THE PORTFOLIO HEALTH "
        "RENDERING BLOCK -- no step of the decision sequence, no reveal gate, no lock, no "
        "randomization, no server contract and no append-only record moved. The v10 record is "
        "NOT regenerated.",
    ),
    Package(
        "og-participant-2026.08-v12",
        "code_audit/run36_participant_package_v12_checksums.sha256",
        # RUN 36 CLOSURE: v12 is a predecessor now, pinned to the commit whose blobs it describes
        # rather than left reading the working tree, so only one record claims the live tree.
        "822d80928367c0f422fac5f2564705279e718dd1",
        "RUN 36. ONE participant-visible file moved: the GENERATED defensibility evidence "
        "object, and the change is confined to ONE module's record. A1.1 Monte Carlo EAC "
        "Forecast was served to the participant as CONDITIONAL_ON_GOVERNED_STRUCTURE, with "
        "`canonicalStructureRequired: true` and the sentence 'when that structure is absent the "
        "module returns Not Estimable'. EXECUTION DISPROVES ALL THREE: A1.1 declares "
        "`costDriverDistributions`, the governed intake accepts it, no route reads it, and the "
        "module computes from the budget and the indices whether it is supplied or not. The "
        "generator was inferring conditionality from the PRESENCE OF A DECLARATION instead of "
        "measuring it, and the measurement was already sitting unused two lines above. Exactly "
        "one module was misdescribed, derived by executing all 101 rather than assumed. The "
        "served record now says the runner computes from available evidence, that the declared "
        "structure is accepted by the intake but read by no current route so the reading is "
        "produced whether it is supplied or not, and `canonicalStructureRequired` is false. THE "
        "EXPERIMENTAL SEQUENCE IS UNCHANGED: decision.js, decision-ui.js, workspace.js, "
        "deepdive.js and both questionnaires are byte for byte identical to v11, and no step of "
        "the decision sequence, no reveal gate, no lock, no randomization, no server contract "
        "and no append-only record moved. The v11 record is NOT regenerated: it is pinned to the "
        "commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v13",
        "code_audit/run36_closure_participant_package_v13_checksums.sha256",
        # RUN 43. v13 became a PREDECESSOR when v14 was minted, so it is pinned to the commit
        # whose blobs it describes rather than being regenerated against the live tree -- the
        # defect the Run-28 closure had to correct in the v2 record.
        "428a6c60b189bc64117f30edfe773092d5aae2f6",
        "THE OWNER'S A1.1 RULING OF 2026-08-19. Three participant-visible files moved and ALL "
        "THREE ARE GENERATED from the registry: the served defensibility evidence object and both "
        "client taxonomy mirrors. A1.1 Monte Carlo EAC Forecast is operationally disabled for "
        "insufficient canonical input -- canonical execution needs the declared cost-driver "
        "distribution structure AND an authoritative rule for turning drawn driver figures into a "
        "forecast, the specification requires that rule and does not define it, and inventing one "
        "was refused. So the taxonomy mirrors gain its disabled flag and the defensibility record "
        "stops describing it as a module that computes. The retained budget-and-index "
        "approximation is preserved in the code and cannot be reached from production. THE "
        "EXPERIMENTAL SEQUENCE IS UNCHANGED: decision.js, decision-ui.js, workspace.js, "
        "deepdive.js and both questionnaires are byte for byte identical to v12, and no step of "
        "the decision sequence, no reveal gate, no lock, no randomization, no server contract and "
        "no append-only record moved. The v12 record is NOT regenerated: it is pinned to the "
        "commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v14",
        "code_audit/run43_participant_package_v14_checksums.sha256",
        # RUN 44. v14 became a PREDECESSOR when v15 was minted, so it is pinned to the commit
        # whose blobs it describes rather than left reading the working tree.
        "604291a",
        "RUN 43, THE RETIREMENT OF 38 MODULES FROM SERVICE. Five participant-visible files moved. "
        "THREE ARE GENERATED from the registry: both client taxonomy mirrors, which "
        "build_client_taxonomy.py now emits from registry.service_index() rather than from the "
        "whole registry so the 38 retired identities carry no taxonomy row at all, and detail.js, "
        "whose LIN_CATEGORIES comment records the registered Group A count. TWO CARRY A COUNT A "
        "PARTICIPANT READS -- knowledge.js and index.html -- and each now states three "
        "populations where it stated two: the registry holds 101 modules, 63 are in service, and "
        "the analytical server computes 62 of the 63. Retirement is not deletion: every retired "
        "module keeps its registry entry, its formula function and its audit lineage, and "
        "run_module() on all 101 identifiers returns output byte-identical to sim-2026.08-v27. "
        "THE EXPERIMENTAL SEQUENCE IS UNCHANGED: decision.js, decision-ui.js, workspace.js, "
        "deepdive.js and both questionnaires are byte for byte identical to v13, and no step of "
        "the decision sequence, no reveal gate, no lock, no randomization, no server contract and "
        "no append-only record moved. The v13 record is NOT regenerated: it is pinned to the "
        "commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v15",
        "code_audit/run44_participant_package_v15_checksums.sha256",
        # RUN 47 PINNED THIS. Two of its seventy files moved at Run 47, so the live tree is no
        # longer evidence for v15; it is pinned to the commit whose blobs it describes, exactly
        # as v14 was pinned when v15 superseded it.
        "fe2e2df",
        "RUN 44, THE PARTICIPANT-FACING RENDER DEFECTS. Four participant-visible files moved and "
        "ONE OF THE FOUR IS SEQUENCE-BEARING. THE EXPERIMENTAL SEQUENCE IS NOT UNCHANGED, and "
        "this record is the first since v10 that cannot say it is. assets/js/deepdive.js carries "
        "the Portfolio Health flyout, which told a participant Portfolio Health needed at least "
        "three projects with computed signals; after Run 43 retired every Portfolio Level module "
        "from service no number of projects makes it compute, so that sentence was false on "
        "every render of it. The correction was written and verified at Run 43H and REVERTED "
        "there rather than move a sequence-bearing byte without authority; Run 44 section 4.4 is "
        "that authority and orders it in those terms. WHAT MOVED INSIDE THAT FILE, EXACTLY: one "
        "added predicate derived from the taxonomy the page loaded, one added arm on the reason "
        "string, and the comment recording why. No step of the decision sequence, no reveal "
        "gate, no lock, no randomization, no server contract, no append-only record and NO "
        "user-facing control moved. THE OTHER THREE ARE RENDER REPAIRS: detail.js orders "
        "statuses case-insensitively through one shared rank and no longer names a module as the "
        "driver of a severity better than its own, and an absent document-risk score renders as "
        "absent while a genuine stored zero still renders as zero; signals.js labels CPI and SPI "
        "computed rather than extracted; radar.css gains the one rule that mark needs. NO SERVER "
        "COMPUTATION MOVED: run_module() on all 101 identifiers is byte-identical to "
        "sim-2026.08-v28 on both a full and a starved package, proved by executing both lines. "
        "decision.js, decision-ui.js, workspace.js and both questionnaires are byte for byte "
        "identical to v14. The v14 record is NOT regenerated: it is pinned to the commit whose "
        "blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v16",
        "code_audit/run47_participant_package_v16_checksums.sha256",
        # RUN 48 PINNED THIS. Three of its seventy files moved at Run 48, so the live tree is no
        # longer evidence for v16; it is pinned to the commit whose blobs it describes, exactly
        # as v15 was pinned when v16 superseded it.
        "2d82b21",
        "RUN 47, THE EVM CONSISTENCY CHECK. TWO participant-visible files moved and NEITHER IS "
        "SEQUENCE-BEARING, so this record can say again what v15 could not: decision.js, "
        "decision-ui.js, workspace.js, deepdive.js and both questionnaires are byte for byte "
        "identical to v15. assets/js/detail.js renders, as TEXT in the executive brief panel, "
        "every relation where one document stated both a value and the percentage that "
        "determines it against a known budget at completion and the two do not agree; the same "
        "file's BRIEF_CAT_LABEL loses the retired 'Cat N' scheme for groups and purposes. "
        "assets/js/recommendation_options.js renders the same text beside the recommendation. "
        "NO USER-FACING CONTROL WAS ADDED, MOVED OR REMOVED: both blocks were measured in the "
        "real browser DOM and contain zero controls of any kind. NO STORED FIGURE MOVED and "
        "nothing is derived into storage: the comparison is a pure function on the READ path "
        "and the document's own figure stands. NO SERVER COMPUTATION MOVED: the full served "
        "census with and without a disagreement present is identical. The v15 record is NOT "
        "regenerated: it is pinned to the commit whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v17",
        "code_audit/run48_participant_package_v17_checksums.sha256",
        # RUN 49 PINNED THIS. Two of its seventy files moved at Run 49, so the live tree is no
        # longer evidence for v17; it is pinned to the commit whose blobs it describes, exactly
        # as v16 was pinned when v17 superseded it.
        "5838a23",
        "RUN 48, THE PERIOD THE PROJECT DETAIL PAGE OPENS ON AND THE LIVE NAMING INSTANCES. "
        "THREE participant-visible files moved and ONE OF THE THREE IS SEQUENCE-BEARING. This "
        "record cannot say what v16 could, and says so rather than claiming otherwise. "
        "assets/js/deepdive.js moved on the owner's ruling 2 of 2026-08-22, which authorises a "
        "sequence-bearing file to be edited whenever an ordered fix requires it and carries its "
        "own named exception record. WHAT MOVED INSIDE THAT FILE, EXACTLY: the map from a legacy "
        "module number to the panel's displayed label now holds groups and purposes instead of "
        "the retired 'Cat N.M' notation, against NAMING_AUTHORITY.md:96; its fallback names a "
        "purpose instead of concatenating the retired prefix; and the panel's GROUPING number, "
        "which is written to a data attribute and is never displayed, is declared in its own map "
        "instead of being parsed back out of the displayed label. The grouping numbers are "
        "exactly the numbers the retired labels parsed to, measured panel by panel in the "
        "rendered DOM, so no panel moved to a different collapsible group. No step of the "
        "decision sequence, no reveal gate, no lock, no randomization, no server contract, no "
        "append-only record and NO USER-FACING CONTROL moved. THE OTHER TWO ARE READ-PATH AND "
        "NAMING REPAIRS: assets/js/detail.js reads back the stored row for the LATEST PERIOD "
        "THAT HAS BEEN COMPUTED instead of for the literal period 1, so every panel on the page "
        "stops showing period 1 on a project whose current period is not 1; the same file stops "
        "sending a category identifier into the executive brief's model prompt and drops the "
        "dead category label map four runs rediscovered. assets/js/charts3d.js loses the retired "
        "scheme from one chart node label. NO SERVER COMPUTATION MOVED: 101 registered, 63 in "
        "service, voting exactly A1.7 and A1.8, and no stored figure changed. decision.js, "
        "decision-ui.js, workspace.js and both questionnaires are byte for byte identical to "
        "v16. The v16 record is NOT regenerated: it is pinned to the commit whose blobs it "
        "describes.",
    ),
    Package(
        "og-participant-2026.08-v18",
        "code_audit/run49_participant_package_v18_checksums.sha256",
        "ad4f614",
        "RUN 49, THE COMPLETION OF THE NAMING CORRECTION. THREE participant-visible files moved "
        "and TWO OF THE THREE ARE SEQUENCE-BEARING. This record says so rather than claiming "
        "otherwise, and "
        "each carries its own named exception record, on the owner's rulings 1 and 4 of "
        "2026-08-22. WHAT MOVED INSIDE assets/js/deepdive.js, EXACTLY: the ten collapsible group "
        "headers drop the `Cat N` identifier span and render the group name alone; the Signal "
        "Stack banner, the Dempster-Shafer metric-box label, the synthesis comparison heading, "
        "its note and its three confidence sentences name what a module DOES instead of naming "
        "it by number; the synthesis comparison table drops the `Module NN` prefix from every "
        "row and the `Agrees with M09` column header; the Portfolio Health flyout drops the "
        "`D1.N` identifier from each module heading; and the panel label map is EXTENDED from "
        "nineteen keys to all seventy-seven keys the call sites actually pass, so each panel "
        "names its own category's purpose instead of collapsing onto one neutral phrase. The "
        "GROUPING number map, CAT_NUM_FROM_MODULE, WAS NOT TOUCHED, so no panel moved to a "
        "different collapsible group. WHAT MOVED INSIDE assets/js/decision-ui.js, EXACTLY: "
        "COMMENTS ONLY, at the three inert `period: 1` literals, recording that "
        "documents._resolve_period derives the period from the research assignment and ignores "
        "the value. Not one byte of executable text in that file changed. THE THIRD FILE IS NOT "
        "SEQUENCE-BEARING: assets/js/detail.js titles a section 'Documents and Extracted "
        "Signals' instead of using the ampersand the authority bars in user-facing text, and "
        "its executive brief prompt stops naming the retired scheme to the model while still "
        "forbidding the model to print any module identifier or category number. No step of the "
        "decision sequence, no reveal gate, no lock, no randomization, no server contract, no "
        "append-only record and NO USER-FACING CONTROL moved in either file. NO SERVER "
        "COMPUTATION MOVED: 101 registered, 63 in service, voting exactly A1.7 and A1.8, and no "
        "stored figure changed. decision.js, workspace.js and both questionnaires are byte for "
        "byte identical to v17. The v17 record is NOT regenerated: it is pinned to the commit "
        "whose blobs it describes.",
    ),
    Package(
        "og-participant-2026.08-v19",
        "code_audit/run51_participant_package_v19_checksums.sha256",
        None,
        "RUN 51, THE DELIVERY OF WHAT RUN 50 STOPPED ON. TWENTY-THREE participant-visible files "
        "moved and ALL SIX SEQUENCE-BEARING FILES ARE AMONG THEM. This record says so rather "
        "than claiming otherwise, and each of the six carries its OWN named exception record "
        "rather than being excused by widening a comparison, on the owner's rulings 1 to 6 of "
        "2026-08-22. WHAT MOVED INSIDE assets/js/deepdive.js, EXACTLY: the Portfolio Health "
        "flyout is deleted with its six symbols and its three buttons, which rendered nowhere "
        "and had no caller anywhere in the served application; the eight-module compliance panel "
        "is split into two panels, one per current category; the panel label map and the panel "
        "grouping map are replaced by ONE table of category keys from which both the label and "
        "the bucket are derived through the loaded taxonomy, correcting seven mis-filings; and "
        "the grouping loop's bound is derived from the taxonomy instead of a literal ten so the "
        "eleventh project-level category can render. assets/js/decision.js stops concatenating a "
        "category identifier and a module identifier into the action plan. assets/js/"
        "decision-ui.js and assets/js/workspace.js replace rendered em-dash placeholders with "
        "text saying what they mean. Both questionnaires replace em dashes inside existing "
        "labels and notes with words: NO ITEM, NO RESPONSE OPTION, NO SCALE AND NO ORDER "
        "CHANGED. No step of the decision sequence, no reveal gate, no lock, no randomization, "
        "no server contract, no append-only record and NO REACHABLE USER-FACING CONTROL moved. "
        "NO SERVER COMPUTATION MOVED: 101 registered, 63 in service, voting exactly A1.7 and "
        "A1.8, no stored figure changed and the behaviour digest is unchanged. The v18 record is "
        "NOT regenerated: it is pinned to the commit whose blobs it describes.",
    ),
)

#: RUN 51. The files whose bytes moved between v18 and v19. TWENTY-THREE, and ALL SIX
#: sequence-bearing files are among them. Every exception is declared here rather than left for
#: a checksum to discover. Their authority is the owner's rulings 1 to 6 in the Run 51 order.
V18_TO_V19_CHANGED = (
    "assets/js/admin-ops.js",
    "assets/js/app.js",
    "assets/js/auditor.js",
    "assets/js/categories.js",
    "assets/js/charts3d.js",
    "assets/js/decision-ui.js",
    "assets/js/decision.js",
    "assets/js/deepdive.js",
    "assets/js/detail.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/export.js",
    "assets/js/ingest.js",
    "assets/js/knowledge.js",
    "assets/js/neural_flow.js",
    "assets/js/projectnet2d.js",
    "assets/js/signals.js",
    "assets/js/store.js",
    "assets/js/taxonomy.js",
    "assets/js/workspace.js",
    "assets/questionnaires/debrief.json",
    "assets/questionnaires/intake.json",
    "assets/visualizations/pceif_neural_signal_flow.html",
    "index.html",
)

#: The SIX sequence-bearing files Run 51 was authorised to move, and the only six it moved. A
#: SEVENTH sequence-bearing file does not exist, so this exception is the whole set; what keeps
#: the invariant real is that each is named WITH WHAT MOVED INSIDE IT in the v19 checksum
#: record's header, and that the record itself is compared byte for byte against the tree.
V18_TO_V19_SEQUENCE_EXCEPTION = (
    "assets/js/decision-ui.js",
    "assets/js/decision.js",
    "assets/js/deepdive.js",
    "assets/js/workspace.js",
    "assets/questionnaires/debrief.json",
    "assets/questionnaires/intake.json",
)

#: RUN 49. The files whose bytes moved between v17 and v18. TWO, and BOTH are sequence-bearing.
#: Both exceptions are declared here rather than left for a checksum to discover. Their authority
#: is the owner's rulings 1 and 4 in the Run 49 order. deepdive.js: every surviving rendered
#: instance of the retired "Cat N" scheme, plus the extension of the panel label map to every key
#: the call sites pass. decision-ui.js: comments only, and nothing else at all. detail.js is
#: the THIRD file and is NOT sequence-bearing: one section title loses its ampersand, and the
#: executive brief prompt stops naming the retired scheme to the model while still forbidding
#: the model to print any identifier.
V17_TO_V18_CHANGED = (
    "assets/js/decision-ui.js",
    "assets/js/deepdive.js",
    "assets/js/detail.js",
)

#: The TWO sequence-bearing files Run 49 was authorised to move, and the only two it moved. Every
#: other member of SEQUENCE_BEARING_FILES must still be byte-identical across this successor.
#: Naming the exceptions rather than widening the comparison is what keeps the invariant a real
#: one: a THIRD file moving here still fails.
V17_TO_V18_SEQUENCE_EXCEPTION = ("assets/js/decision-ui.js", "assets/js/deepdive.js")

#: RUN 48. The files whose bytes moved between v16 and v17. THREE, and one of them --
#: deepdive.js -- IS SEQUENCE-BEARING. The exception is declared here rather than left for a
#: checksum to discover, on exactly the Run 44 construction. Its authority is the owner's ruling
#: 2 in the Run 48 order; its content is the deep-dive panel label map, its fallback, and the
#: grouping number that used to be parsed out of the label, and nothing else.
V16_TO_V17_CHANGED = (
    "assets/js/charts3d.js",
    "assets/js/deepdive.js",
    "assets/js/detail.js",
)

#: The ONE sequence-bearing file Run 48 was authorised to move, and the only one it moved. Every
#: other member of SEQUENCE_BEARING_FILES must still be byte-identical across this successor.
#: Naming the exception rather than widening the comparison is what keeps the invariant a real
#: one: a second file moving here still fails.
V16_TO_V17_SEQUENCE_EXCEPTION = ("assets/js/deepdive.js",)

#: RUN 47. The files whose bytes moved between v15 and v16. TWO, and NEITHER is sequence-bearing,
#: so the invariant v15 had to break is intact again: all six sequence-bearing files are byte for
#: byte identical across this successor.
V15_TO_V16_CHANGED = (
    "assets/js/detail.js",
    "assets/js/recommendation_options.js",
)

#: RUN 44. The files whose bytes moved between v14 and v15. FOUR, and one of them -- deepdive.js
#: -- IS SEQUENCE-BEARING. It is the first successor since v10 of which that is true, and the
#: exception is declared here rather than left for a checksum to discover. Its authority is the
#: owner's order at Run 44 section 4.4; its content is the Portfolio Health flyout's reason
#: sentence and nothing else.
V14_TO_V15_CHANGED = (
    "assets/css/radar.css",
    "assets/js/deepdive.js",
    "assets/js/detail.js",
    "assets/js/signals.js",
)

#: The ONE sequence-bearing file Run 44 was authorised to move, and the only one it moved. Every
#: other member of SEQUENCE_BEARING_FILES must still be byte-identical across this successor.
#: Naming the exception rather than widening the comparison is what keeps the invariant a real
#: one: a second file moving here still fails.
V14_TO_V15_SEQUENCE_EXCEPTION = ("assets/js/deepdive.js",)

#: RUN 43. The files whose bytes moved between v13 and v14. FIVE: three generated from the
#: registry and two carrying a count a participant reads. Not one carries a step of the
#: experimental sequence.
V13_TO_V14_CHANGED = (
    "assets/js/categories.js",
    "assets/js/detail.js",
    "assets/js/knowledge.js",
    "assets/js/taxonomy.js",
    "index.html",
)

#: RUN 36. The files whose bytes moved between v11 and v12. ONE file, and it is generated.
V11_TO_V12_CHANGED = (
    "assets/js/ds_defensibility_evidence.js",
)

#: RUN 36 CLOSURE. The files whose bytes moved between v12 and v13. THREE, and ALL THREE ARE
#: GENERATED from the registry: the served defensibility object and both client taxonomy mirrors.
#: Not one of them is hand-authored and not one carries a step of the experimental sequence.
V12_TO_V13_CHANGED = (
    "assets/js/categories.js",
    "assets/js/ds_defensibility_evidence.js",
    "assets/js/taxonomy.js",
)

#: The one link that describes the working tree.
CURRENT = PARTICIPANT_PACKAGES[-1]

#: The files whose bytes moved between v10 and v11.
V10_TO_V11_CHANGED = (
    "assets/js/ds_defensibility_evidence.js", "assets/js/knowledge.js",
    "assets/js/workspace.js",
)

#: The sequence-bearing files that must be byte-identical from v10 to v11. workspace.js is NOT
#: here, because it genuinely moved -- and what replaces the blanket claim is a stronger one,
#: asserted in the guard: the workspace.js delta is confined to the Portfolio Health rendering
#: block, and every OTHER sequence-bearing file is unchanged. A list that quietly kept
#: workspace.js while its bytes moved would be the false claim this file exists to prevent.
V10_TO_V11_SEQUENCE_UNCHANGED = (
    "assets/js/decision.js", "assets/js/decision-ui.js", "assets/js/deepdive.js",
    "assets/questionnaires/intake.json", "assets/questionnaires/debrief.json",
)

#: The v11 workspace.js delta must touch ONLY these identifiers, which are the Portfolio Health
#: rendering block and nothing else. Named so the guard asserts against a contract rather than
#: against a line count.
#: THE ANCHOR THAT BOUNDS THE v11 workspace.js DELTA. Everything BEFORE this line -- which is
#: present byte for byte in both v10 and v11 -- must be identical between the two, which is a
#: structural statement rather than a vocabulary of tokens. A token list was tried first and was
#: the wrong instrument: a multi-line expression's continuation lines carry no distinguishing
#: token, so the check either flagged real portfolio lines or had to be widened until it accepted
#: anything. The portfolio-rendering block is the TAIL of this file, so a prefix comparison says
#: exactly what is meant: no step of the decision sequence, no reveal gate, no lock, no
#: randomization, no server contract and no append-only record moved.
V11_WORKSPACE_PORTFOLIO_ANCHOR = (
    "    // Portfolio Health is a property of the whole portfolio, not of each project:")

#: The files whose bytes moved between v9 and v10.
V9_TO_V10_CHANGED = (
    "assets/js/categories.js", "assets/js/ds_defensibility_evidence.js",
    "assets/js/knowledge.js", "assets/js/taxonomy.js",
)

#: The files whose bytes moved between v8 and v9, and the six identifiers that moved them.
V8_TO_V9_CHANGED = (
    "assets/js/categories.js", "assets/js/knowledge.js", "assets/js/taxonomy.js",
)

#: CURRENT <- SUPERSEDED. Matched against for stored rows only; never emitted, never displayed.
V9_METHOD_CLASS_PROPAGATION = {
    "CPI_Shrinkage_Forecast": "Regression_To_Mean",
    "Independent_EAC_Reconciliation": "ICE_Ratio",
    "EVMS_Applicability": "FAR_Threshold",
    "A11_Conformance": "OMB_A11_Check",
    "EVMS_Reporting_Compliance": "EVM_Reporting_Threshold",
    "Modification_Governance": "Contract_Mod_Frequency",
}

#: The files whose bytes moved between v7 and v8. Unlike every earlier link, this delta is NOT a
#: pure display substitution and no inverse mapping is claimed for it: it corrects statements that
#: had become false. Only `taxonomy.js` inverse-maps by the identifier alone.
V7_TO_V8_CHANGED = (
    "assets/js/categories.js", "assets/js/ds_defensibility_evidence.js",
    "assets/js/knowledge.js", "assets/js/module_charts.js", "assets/js/neural_flow.js",
    "assets/js/recommendation_options.js", "assets/js/taxonomy.js",
)

#: The files that CARRY THE PARTICIPANT EXPERIMENTAL SEQUENCE. They must be byte for byte
#: identical between v7 and v8, which is what makes "the sequence is unchanged" a checkable claim
#: rather than a sentence in a report.
SEQUENCE_BEARING_FILES = (
    "assets/js/decision.js", "assets/js/decision-ui.js", "assets/js/workspace.js",
    "assets/js/deepdive.js", "assets/questionnaires/intake.json",
    "assets/questionnaires/debrief.json",
)

#: The files whose bytes moved between v6 and v7, and the ONE substitution that moved them.
V6_TO_V7_CHANGED = (
    "assets/js/categories.js", "assets/js/decision-ui.js",
    "assets/js/ds_defensibility_data.js", "assets/js/ds_defensibility_evidence.js",
    "assets/js/knowledge.js", "assets/js/simulations.js", "assets/js/taxonomy.js",
    "assets/js/workspace.js",
)

#: NEW -> OLD. Applying this to the v7 bytes must reproduce the v6 bytes exactly.
V7_TO_V6_INVERSE = {
    "Minimax Regret Decision Rule": "Regret Minimization Index",
}

#: The files whose bytes moved between v5 and v6, and the six substitutions that moved them.
V5_TO_V6_CHANGED = (
    "assets/js/categories.js", "assets/js/decision-ui.js", "assets/js/deepdive.js",
    "assets/js/ds_defensibility_data.js", "assets/js/ds_defensibility_evidence.js",
    "assets/js/knowledge.js", "assets/js/taxonomy.js", "assets/js/workspace.js",
)

#: NEW -> OLD. Applying these to the v6 bytes must reproduce the v5 bytes exactly.
V6_TO_V5_INVERSE = {
    "Agent-Based Governance Model": "ABM Governance Layer",
    "FAR/Agency EVMS Applicability Monitor": "FAR Threshold Monitor",
    "Versioned A-11 Capital Programming Conformance Check": "OMB A-11 Check",
    "EVMS Reporting Compliance Monitor": "EVM Reporting Threshold",
    "Contract Modification Governance Check": "Contract Modification Frequency",
    "Contractor Performance Assessment Signal": "Contractor Performance Score",
}

#: The files whose bytes moved between v4 and v5.
V4_TO_V5_CHANGED = (
    "assets/js/ds_defensibility_evidence.js",
)

_STRUCTURE_PHRASE_REQUIRED = "required and enforced by the canonical-structure layer"
_STRUCTURE_PHRASE_NOT = "not required by this module"

#: The eight qualifier sentences the Run-30 closure deleted. Restoring them, and restoring the
#: pre-closure structure statement, reconstructs the v4 text.
_RESTORED_QUALIFIERS_V5 = (
    ("B2.10", "hard-coded transformations of raw CPI, SPI and document risk"),
    ("B2.11", "hard-coded memberships consuming raw metrics; no calibration evidenced"),
    ("B2.12", "designed perturbations, not elicited or observed hesitant assessments"),
    ("B2.13", "membership intervals that are designed constants"),
    ("B2.14", "entropy over designed state probabilities; measures the lookup, not the project"),
    ("B2.15", "fixed mappings from raw metrics; no governed possibility distribution"),
    ("B2.16", "algebraically bounded but fixed memberships on raw unqualified inputs"),
    ("B2.17", "formula-shaped with designed memberships, no empirical or elicitation basis"),
)


def _v4_era_structure_ids(root) -> set:
    """The module ids the v4 generator called structure-requiring: the ones whose identifiers
    appear in canonical.py, which is the only map it scanned. Derived, never listed."""
    import re
    src = (root / "server" / "app" / "simulation" / "canonical.py").read_text(encoding="utf-8")
    return set(re.findall(r'"([A-D]\d+\.\d+)"', src))


def to_v4_era(text: str, root) -> str:
    """Map the current package file back to its v4-era text.

    TWO REVERSALS, both mechanical. The eight deleted qualifier sentences are put back, and the
    structure statement is put back to what the v4 generator produced -- which is what the
    canonical.py scan alone yielded. Byte identity after this is the proof that nothing else
    moved in the file.
    """
    v4_ids = _v4_era_structure_ids(root)
    out = []
    for line in text.split("\n"):
        marker = line.strip()
        if marker.startswith('"') and '": { name:' in marker:
            mid = marker.split('"')[1]
            if mid not in v4_ids:
                line = line.replace(f'canonicalStructure: "{_STRUCTURE_PHRASE_REQUIRED}"',
                                    f'canonicalStructure: "{_STRUCTURE_PHRASE_NOT}"', 1)
        out.append(line)
    text = "\n".join(out)
    for mid, qualifier in _RESTORED_QUALIFIERS_V5:
        marker = f'"{mid}": {{ name: '
        head, sep, rest = text.partition(marker)
        if not sep:
            continue
        line, nl, tail = rest.partition("\n")
        line = line.replace(_QUALIFICATION_TAIL,
                            f"{_QUALIFICATION_TAIL} Stated proxy: {qualifier}.", 1)
        text = head + marker + line + nl + tail
    return text

#: The files whose bytes moved between v3 and v4, and the ONLY change permitted in them: the
#: deletion of the six proxy-qualifier sentences the Run-29 remediation made false. The
#: normalisation below maps a current file back to its v3-era text by restoring those six
#: sentences; byte identity after it is the proof that nothing else moved.
V3_TO_V4_CHANGED = (
    "assets/js/ds_defensibility_evidence.js",
)

#: (module id, the qualifier sentence that was deleted). Restoring them reconstructs the v3 text.
_RESTORED_QUALIFIERS = (
    ("A4.5", "a lost-days over available-float ratio with ungoverned bands, computed only from "
             "verified lost days and a reported float figure"),
    ("A4.6", "contract growth plus a raw count; no time or exposure denominator"),
    ("A4.7", "an ad hoc 0.3 / 0.3 / 0.4 weighted sum; weights and dependence uncalibrated"),
    ("A4.8", "a precomputed compliance score; provenance and construction unvalidated"),
    ("A5.2", "local CPI perturbation plus deviations, not calibrated multivariate sensitivity"),
    ("A5.3", "a ranking of four present-state deviations; no outcome-response ranges estimated"),
)

_QUALIFICATION_TAIL = ("No empirical evidence of predictive performance is held for this "
                       "module.")


def to_v3_era(text: str) -> str:
    """Map a current package file back to its v3-era text by restoring the six qualifiers."""
    for mid, qualifier in _RESTORED_QUALIFIERS:
        marker = f'"{mid}": {{ name: '
        head, sep, rest = text.partition(marker)
        if not sep:
            continue
        line, nl, tail = rest.partition("\n")
        line = line.replace(_QUALIFICATION_TAIL,
                            f"{_QUALIFICATION_TAIL} Stated proxy: {qualifier}.", 1)
        text = head + marker + line + nl + tail
    return text

#: The files whose bytes moved between v2 and v3, and the ONLY change permitted in them: the
#: owner's A1.1 rename. Every one is a display surface. The normalisation below maps a current
#: file back to its v2-era text; byte identity after it is the proof that nothing else moved.
V2_TO_V3_CHANGED = (
    "assets/js/categories.js",
    "assets/js/charts3d.js",
    "assets/js/decision-ui.js",
    "assets/js/deepdive.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/ds_defensibility_evidence.js",
    "assets/js/knowledge.js",
    "assets/js/neural_flow.js",
    "assets/js/recommendation_options.js",
    "assets/js/taxonomy.js",
    "assets/js/workspace.js",
)

#: The inverse of the rename, applied longest-first. The last three entries undo de-duplications
#: the rename itself required: the v2-era prose said "Monte Carlo EAC Monte Carlo outputs" and
#: "Monte Carlo EAC forecast", and renaming without collapsing those would have produced
#: "Monte Carlo EAC Forecast Monte Carlo outputs" and "Monte Carlo EAC Forecast forecast".
_INVERSE_RENAME = (
    ("Monte Carlo EAC Forecast outputs", "Monte Carlo EAC Monte Carlo outputs"),
    ("the schedule analogue of the Monte Carlo EAC Forecast.",
     "the schedule analogue of the Monte Carlo EAC Monte Carlo cost forecast."),
    ("the full Monte Carlo EAC Forecast run", "the full Monte Carlo EAC Monte Carlo run"),
    ("<h3>Monte Carlo EAC Forecast, why a range",
     "<h3>Monte Carlo EAC forecast, why a range"),
    ('["green","Monte Carlo EAC Forecast"', '["green","Monte Carlo EAC forecast"'),
    ("Monte Carlo EAC Forecast", "Monte Carlo EAC"),
)


def to_v2_era(text: str) -> str:
    """Map a current package file back through the A1.1 rename to its v2-era text."""
    for new, old in _INVERSE_RENAME:
        text = text.replace(new, old)
    return text


#: The participant PROTOCOL surface inside the package: every file that carries a step of the
#: decision sequence, the reveal gate, the lock, the randomization, the server contract or the
#: append-only record. NONE of these may differ between v2 and v3 by a single byte. Derived from
#: what each file does, not from what it is named: `decision.js` and `decision-ui.js` are not the
#: same thing -- the first runs the sequence, the second holds a module-id-to-display-name table --
#: and only the second is in the changed list above.
PROTOCOL_SURFACE = (
    "assets/js/decision.js",
    "assets/js/store.js",
    "assets/js/app.js",
    "assets/js/auth.js",
    "assets/js/data.js",
    "assets/js/signals.js",
    "assets/js/detail.js",
    "assets/js/questionnaires.js",
    "assets/js/disclaimers.js",
    "assets/js/features.js",
    "assets/js/config.js",
    "assets/js/export.js",
    "assets/js/training.js",
    "assets/questionnaires/intake.json",
    "assets/questionnaires/debrief.json",
    "index.html",
)
