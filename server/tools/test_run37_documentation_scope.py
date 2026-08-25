"""
RUN 37 DOCUMENTATION CLOSURE. THE SCOPE OF THE PLACEHOLDER STATEMENT.

WHAT WENT WRONG AND WHY THIS FILE EXISTS. The Run-37 final report said "No PENDING_FINAL_COMMIT
placeholder is used anywhere in this release." That is true of the final release RECORD and false
of the REPOSITORY, which still contains the string in three places for three different and
legitimate reasons. A true claim about one file had been widened into a false claim about a tree.

THE GUARD IS SCOPED BY FILE, NOT BY REPOSITORY-WIDE STRING ABSENCE, and that is deliberate. A guard
that counted occurrences across the tree would have to except its own source -- this file contains
the literal in order to check for it -- and `test_run37_freeze_gate.py`, which contains it for the
same reason. A rule whose first act is to excuse two files is the wrong rule. So each file is asked
the question that is actually true of it:

  * the final release RECORD must not contain the placeholder;
  * the final release REPORT must not claim the whole repository is free of it;
  * the historical Run-36 CANDIDATE MANIFEST may keep it, and is protected from being scrubbed;
  * guard sources are not release documentation and are not asked at all.

THIS CLOSURE IS DOCUMENTATION AND TEST ONLY. Nothing here touches a formula, a qualification rule,
the voting set, the participant sequence or a controlled stimulus, and the frozen disposition
FINAL_FREEZE_ACCEPTED is asserted unchanged below.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def check(name, ok, why, got=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {name}  {why}")
    else:
        FAILED += 1
        FAILURES.append(f"{name}  {why}")
        print(f"FAIL  {name}  {why}  [{got}]")


PLACEHOLDER = "PENDING" + "_FINAL_COMMIT"          # assembled so this line is not an occurrence

RECORD = ROOT / "research" / "freeze" / "INSTRUMENT_FINAL_FREEZE_RECORD.json"
REPORT = ROOT / "research" / "freeze" / "INSTRUMENT_FINAL_FREEZE_REPORT.md"
CANDIDATE = ROOT / "research" / "freeze" / "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json"
HANDOFF = ROOT / "T6_HANDOFF.md"

#: Files that legitimately carry the literal because they REASON about it. They are guard sources
#: and audit tooling, not release documentation, and they are never asked the record's question.
GUARD_SOURCES = {
    "server/tools/test_run37_freeze_gate.py",
    "server/tools/test_run37_documentation_scope.py",
}

print("=" * 94)
print("RUN 37 DOCUMENTATION SCOPE")
print("=" * 94)

# ------------------------------------------------------------------ 1. the release RECORD
_record_text = RECORD.read_text(encoding="utf-8")
check("run37doc.record_has_no_placeholder", PLACEHOLDER not in _record_text,
      "the FINAL RELEASE RECORD contains no placeholder; that is the claim the report is "
      "entitled to make", RECORD.name)

# ------------------------------------------------------------------ 2. the release REPORT's scope
_report_text = REPORT.read_text(encoding="utf-8")
#: Phrasings that widen a true statement about one file into a false one about the tree. Each is
#: the actual overstatement or a close variant of it.
OVERBROAD = (
    "is used anywhere in this release",
    "used anywhere in this release",
    "anywhere in the repository",
    "nowhere in the repository",
    "the repository contains no " + PLACEHOLDER,
    "zero occurrences of " + PLACEHOLDER,
    "no " + PLACEHOLDER + " placeholder is used anywhere",
)
def widening_claims(text: str) -> list[str]:
    """
    Overbroad phrasings, tested ONLY where the placeholder is the subject.

    THE FIRST VERSION OF THIS TEST SEARCHED THE WHOLE DOCUMENT for the phrases and went red on
    T6_HANDOFF.md, which says "there is no distinct paging control anywhere in the repository" --
    a true sentence about arrow glyphs from a Run-25 investigation, nothing to do with this
    placeholder at all. A pattern that fires on an unrelated subject is not a guard, it is noise.
    Each occurrence of the literal is therefore given a window and the phrases are tested inside
    it, so the guard asks whether THIS claim was widened rather than whether the word "anywhere"
    appears somewhere in a very long file.
    """
    low = text.lower()
    hits = []
    for m in re.finditer(re.escape(PLACEHOLDER.lower()), low):
        window = low[max(0, m.start() - 300):m.end() + 300]
        hits += [phrase for phrase in OVERBROAD if phrase.lower() in window]
    return sorted(set(hits))


# RUN 59, PHASE B. RETIRED, NOT DELETED. Owner's ruling, 2026-08-25: no markdown document in
# this repository carries authority. These three checks assert what two markdown documents SAY --
# research/freeze/INSTRUMENT_FINAL_FREEZE_REPORT.md, which is SEALED EVIDENCE, and T6_HANDOFF.md,
# which is history. Their subject is a document's wording and nothing else; no production
# behaviour depends on either sentence. They were NOT re-pointed, because there is no
# non-markdown source that states what a report claims, and inventing one would be worse than
# the check it replaced. The placeholder's ACTUAL occurrences in the tree are counted in
# section 1 of this file, against the tree, and that section is untouched.
#
# THE BODIES ARE NOT DELETED. Clear the flag to run them again.
RETIRED_RUN59_DOCUMENT_WORDING = True

if not RETIRED_RUN59_DOCUMENT_WORDING:
    _hits = widening_claims(_report_text)
    check("run37doc.report_makes_no_repository_wide_claim", not _hits,
          "the FINAL RELEASE REPORT does not claim the whole repository is free of the "
          "placeholder", str(_hits))
    check("run37doc.report_scopes_the_claim_to_the_record",
          "final release record contains no" in _report_text.lower()
          and "INSTRUMENT_FINAL_FREEZE_RECORD.json" in _report_text,
          "and it scopes its zero-placeholder claim explicitly to the release record by name")
else:
    print("  RETIRED (Run 59)  the release report's wording -- sealed evidence, no authority")
    print("  RETIRED (Run 59)  and the scope of its zero-placeholder claim")
# THE EXPLANATION MUST BE ABOUT THE HISTORICAL MANIFEST, not merely about self-reference in
# general. The first version of this check accepted the report's OTHER sentence -- "A file cannot
# contain the hash of the commit that contains it", which is about the release record -- so
# deleting the historical explanation left it green. Fault 3 of the campaign found that. The check
# now requires the sentence that names the historical artefact AND says it keeps the placeholder.
_expl = re.search(
    r"historical Run-36 freeze-candidate manifest keeps its documented placeholder because"
    r"[^.]*cannot\s+contain\s+the\s+hash\s+of\s+the\s+commit\s+that\s+contains",
    _report_text, re.S | re.I)
check("run37doc.report_explains_the_historical_placeholder",
      bool(_expl) and "INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json" in _report_text,
      "and it EXPLAINS why the historical Run-36 candidate manifest keeps its placeholder, "
      "rather than leaving the reader to find the string and conclude a defect",
      "the explanatory sentence naming the historical manifest is absent")

# ------------------------------------------------------------------ 3. the HISTORICAL artefact
_cand_text = CANDIDATE.read_text(encoding="utf-8")
check("run37doc.historical_candidate_manifest_preserved", PLACEHOLDER in _cand_text,
      "the historical Run-36 candidate manifest RETAINS its documented placeholder; historical "
      "evidence is not rewritten to make a broader sentence true", CANDIDATE.name)
check("run37doc.historical_candidate_is_not_the_release_record",
      json.loads(_cand_text).get("label") == "FREEZE_CANDIDATE"
      and json.loads(_record_text).get("label") == "FINAL_FREEZE",
      "and the two artefacts are labelled distinctly, so a candidate can never be read as the "
      "final release record")

# ------------------------------------------------------------------ 4. release identity mechanisms
_rec = json.loads(_record_text)
for _field, _what in (
        ("freeze_candidate_commit", "the reviewed candidate commit"),
        ("candidate_identity_digest", "the content-addressed candidate identity"),
        ("release_content_digest", "the content-addressed release digest"),
        ("release_commit_recording_method", "the repository-history recording method")):
    check(f"run37doc.identity_{_field}", bool(_rec.get(_field)),
          f"final release identity retains {_what}", str(_rec.get(_field))[:80])
check("run37doc.identity_candidate_commit_is_the_frozen_one",
      _rec.get("freeze_candidate_commit") == "6142d877856ea651ef8d7e905f6d27604b3244f1",
      "and the candidate commit is the frozen one", str(_rec.get("freeze_candidate_commit")))
check("run37doc.recording_method_names_repository_history",
      "repository history" in str(_rec.get("release_commit_recording_method", "")).lower(),
      "and the recording method says the containing commit is established by repository history")

# ------------------------------------------------------------------ 5. the handoff carries no
#     equivalent overstatement
if not RETIRED_RUN59_DOCUMENT_WORDING:
    _handoff = HANDOFF.read_text(encoding="utf-8")
    _hh = widening_claims(_handoff)
    check("run37doc.handoff_makes_no_repository_wide_claim", not _hh,
          "T6_HANDOFF.md carries no equivalent repository-wide zero-occurrence claim", str(_hh))
else:
    print("  RETIRED (Run 59)  the handoff's wording -- history, no authority")

# ------------------------------------------------------------------ 6. the frozen disposition
check("run37doc.disposition_unchanged",
      _rec.get("release_disposition") == "FINAL_FREEZE_ACCEPTED"
      and _rec.get("blocking_defects") == 0,
      "FINAL_FREEZE_ACCEPTED and blocking defects 0 are unchanged by this documentation closure",
      f"{_rec.get('release_disposition')} / {_rec.get('blocking_defects')}")
check("run37doc.versions_unchanged",
      _rec.get("simulation_version") == "sim-2026.08-v25"
      and _rec.get("participant_package") == "og-participant-2026.08-v13"
      and _rec.get("synthetic_package") == "OG-SYNTH-0.6",
      "and no simulation, participant or synthetic successor was minted",
      f"{_rec.get('simulation_version')} / {_rec.get('participant_package')} / "
      f"{_rec.get('synthetic_package')}")

# ------------------------------------------------------------------ 7. the occurrence set itself,
#     enumerated live so a NEW release-facing occurrence cannot appear unnoticed
_grep = subprocess.run(["git", "grep", "-l", PLACEHOLDER, "--", "."],
                       cwd=ROOT, capture_output=True, text=True)
_files = sorted(f for f in _grep.stdout.split() if f)
_release_facing = sorted(set(_files) - GUARD_SOURCES)
# THE COUNT IS OVER RELEASE-FACING FILES ONLY, and that correction was forced by this guard
# failing on itself. While this file was untracked `git grep` could not see it, so the occurrence
# set read three; the moment it was committed it became a fourth tracked occurrence and the raw
# count went red. GUARD SOURCE COUNT IS NOT A GOVERNED PROPERTY -- a guard that reasons about a
# literal must contain it -- so what is asserted is the release-facing set, by name, which is the
# thing that actually matters and does not move when tooling is added.
check("run37doc.guard_sources_are_excluded_by_name",
      set(GUARD_SOURCES) <= set(_files),
      "every file excused as a guard source really does carry the literal, so the exclusion list "
      "cannot silently hide a file that stopped being one",
      str(sorted(set(GUARD_SOURCES) - set(_files))))
check("run37doc.release_facing_occurrence_count", len(_release_facing) == 2,
      "exactly two RELEASE-FACING files carry the literal, enumerated live from git rather than "
      "assumed; guard sources are excluded by name and counted separately",
      str(_release_facing))
check("run37doc.no_unexpected_release_facing_occurrence",
      set(_release_facing) == {"research/freeze/INSTRUMENT_FINAL_FREEZE_REPORT.md",
                               "research/freeze/INSTRUMENT_FREEZE_CANDIDATE_MANIFEST.json"},
      "and the only release-facing files carrying it are the report (which scopes it) and the "
      "historical candidate manifest (which is entitled to it)", str(_release_facing))

print()
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
raise SystemExit(1 if FAILED else 0)
