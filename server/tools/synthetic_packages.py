"""
RUN 29 CLOSURE. THE SYNTHETIC PACKAGE CHAIN, DECLARED ONCE.

WHY A DECLARATION FILE, and why it mirrors `participant_packages.py`. The synthetic research
programme has four links now and they are not all the same kind of thing: v0.1, v0.2 and v0.3 are
vendored programme builds, each with its own checksum record, and v0.4 is a SUCCESSOR OVERLAY that
adds the Category-4 and Category-5 canonical known-answer tables the supplied Run-29 contracts are
defined on. A guard that had to work that out from directory names would eventually get it wrong.

THE IDENTITY RULE THIS ENCODES, stated for a chain whose predecessors are genuinely unchanged
rather than superseded in place. The participant rule -- exactly one record matches the live tree
-- does not transfer, because every predecessor synthetic build still sits in the tree untouched
and its record still verifies. The equivalent rule that IS checkable here, and that catches the
same failure, is:

  1. every record verifies against its own files, predecessors included;
  2. the CURRENT record names every canonical fixture file the current line reads that no
     predecessor names;
  3. no predecessor record names a file the successor added; and
  4. NO FILE OUTSIDE A PREDECESSOR'S OWN RECORD MAY CARRY THAT PREDECESSOR'S PROGRAMME VERSION.

Rule 4 is the masquerade rule. A current file stamped with a predecessor's identifier claims to be
evidence collected under a package it was never part of, which is exactly the staleness the
participant chain's identity guard exists to prevent, in the form this chain can express it.
"""

from __future__ import annotations

import pathlib
from typing import NamedTuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "research_fixtures" / "synthetic"


class SyntheticPackage(NamedTuple):
    identifier: str
    #: The package root, relative to the repository root.
    root: str
    #: The checksum record, relative to the repository root, or None where the build shipped
    #: without one. A link with no record is declared as having none rather than being omitted.
    record: str | None
    #: What the paths INSIDE the record are relative to: the package root, or the repository root.
    record_paths_relative_to: str
    #: True for the one link the current analytical line reads its canonical fixtures from.
    current: bool
    #: Why this link exists at all.
    why: str


#: Oldest first. Append; never edit a row, because each row is the evidence for the results
#: collected under that package.
SYNTHETIC_PACKAGES: tuple[SyntheticPackage, ...] = (
    SyntheticPackage(
        "OG-SYNTH-0.1",
        "research_fixtures/synthetic/OG-SYNTH-0.1",
        None,
        "package_root",
        False,
        "The first synthetic programme build, integrated by Run 9. It shipped WITHOUT a "
        "package-level checksum record, which is declared here rather than hidden: the chain "
        "says so instead of a guard silently skipping it. Superseded by v0.2 and kept as the "
        "evidence for the results collected under it.",
    ),
    SyntheticPackage(
        "OG-SYNTH-0.2",
        "research_fixtures/synthetic/OG-SYNTH-0.2/Opus_Gubernatio_Synthetic_Programme_v0.2",
        "research_fixtures/synthetic/OG-SYNTH-0.2/"
        "Opus_Gubernatio_Synthetic_Programme_v0.2/CHECKSUMS.sha256",
        "package_root",
        False,
        "The build the Run-9 integration suite reads and the Run-10B canonical integration was "
        "first written against.",
    ),
    SyntheticPackage(
        "OG-SYNTH-0.3",
        "research_fixtures/synthetic/OG-SYNTH-0.3/Opus_Gubernatio_Synthetic_Programme_v0.3",
        "research_fixtures/synthetic/OG-SYNTH-0.3/"
        "Opus_Gubernatio_Synthetic_Programme_v0.3/CHECKSUMS.sha256",
        "package_root",
        False,
        "The Monte Carlo and DSM correction build, and the one the production-structure "
        "importers read their project tables from.",
    ),
    SyntheticPackage(
        "OG-SYNTH-0.4",
        "research_fixtures/synthetic/OG-SYNTH-0.4",
        "research_fixtures/synthetic/OG-SYNTH-0.4/CHECKSUMS.sha256",
        "repository_root",
        True,
        "RUN 29's CLOSURE. Three Category-4 and Category-5 modules were still being exercised "
        "against the shapes the PREVIOUS analytical line read: an audited findings cohort for the "
        "nonconformance rate, an occupancy log for the queueing measure, and a typed-in state "
        "history for the agent based model. The supplied contracts name all three as not being "
        "the method. The six projects' real evidence is imported into the canonical shapes "
        "directly from v0.3, unchanged; this successor adds the known-answer tables at the "
        "figures the supplied contracts state, including the one supplier, one carrier, one "
        "project model v0.3 cannot express because all forty-eight of its agents are suppliers.",
    ),
)

#: The one link the current canonical fixtures are read from.
CURRENT = SYNTHETIC_PACKAGES[-1]

#: The canonical fixture files the current link adds. Named here so a guard can assert that the
#: successor record covers them and that no predecessor record does.
CURRENT_ONLY_FILES = (
    "research_fixtures/synthetic/OG-SYNTH-0.4/README.md",
    "research_fixtures/synthetic/OG-SYNTH-0.4/package_A_project_structures/"
    "abm_agents_known_answer.csv",
    "research_fixtures/synthetic/OG-SYNTH-0.4/package_A_project_structures/"
    "abm_environment_known_answer.csv",
    "research_fixtures/synthetic/OG-SYNTH-0.4/package_A_project_structures/"
    "ncr_exposure_known_answer.csv",
    "research_fixtures/synthetic/OG-SYNTH-0.4/package_A_project_structures/"
    "queue_model_known_answer.csv",
)

#: The three importers the closure replaced, and the canonical successor of each. The old ones are
#: KEPT because the Run-19 and Run-10B suites read them as the historical record of what the
#: previous line was integrated against; rewriting them would destroy that record.
REPLACED_IMPORTERS = {
    "A4.4": ("audited_nonconformance_cohort", "ncr_exposure_record"),
    "A5.6": ("queues", "queue_model"),
    "A5.7": ("agents", "known_answer_agent_supply_chain_model"),
}


def parse_record(text: str) -> dict[str, str]:
    """digest -> path, from a checksum record, ignoring comments and blank lines."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, rel = line.partition("  ")
        if rel.strip():
            out[rel.strip()] = digest.strip()
    return out
