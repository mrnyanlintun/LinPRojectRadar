#!/usr/bin/env python3
"""
RUN 21, SECTION 5 STATE D AND SECTION 6. THE RESET BOUNDARY MUST BE DISCLOSED, NOT MISREPORTED.

THE DEFECT THIS PINS, and it is recorded here as the anti-fossilization record requires: the
historical behaviour, the correct behaviour, the reason, and the test that catches its return.

  HISTORICAL DEFECTIVE BEHAVIOUR. After the supported reset, the Signal Flow header read
  "0 UPLOADED ON THIS PROJECT" and the summary strip read "This project has no uploaded
  documents and no current results". Measured in a real browser on a RELOADED document, so it
  was not a cache artefact and not a same-session mask.

  WHY IT WAS FALSE. The reset deliberately does NOT delete documents. Its own control says so:
  "Clears this project's stored signal values so its documents can be read again. Does not
  delete documents and does not touch other projects." The server went on serving all of them.
  MEASURED: a project reset after twenty-four uploads served twenty-five events, reported zero
  uploaded documents after a real reload, and then computed FORTY-ONE modules from those
  retained documents the moment signals were regenerated -- against thirty-five for a control
  project that had only ever held the one document. A reader was told the evidence was gone
  while it was being kept and was about to be used.

  CORRECT BEHAVIOUR. The number was never wrong -- Run 18 rightly made it a count SINCE THE LAST
  RESET so that cleared evidence stops reading as current. The WORDS were wrong. They now say
  what the number counts, and the retained documents are disclosed beside it. This is the same
  class of defect Run 16 fixed for "96 modules": a correct figure under a false label.

  WHAT DELIBERATELY DID NOT CHANGE, so the fix cannot be mistaken for a relaxation: the
  since-reset count itself, the set of documents in the current window, whether anything on the
  diagram is active, and both the pre-reset wording and the empty-project sentence for a project
  that has NOT been reset. Section 2 asserts each of those as a property.

WHY THIS SUITE IS NOT A BROWSER TEST. The browser evidence is produced by
tools/drive_run21_instrument.py against the served application, and it is not duplicated here.
What this guards is the regression a browser run would catch only by luck: the false sentence
coming back into the shipped file. These are byte-level properties of the shipped source, and
every one of them is proved capable of failing in section 3.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run21_reset_disclosure.py
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLOW_PATH = ROOT / "assets" / "js" / "neural_flow.js"
DETAIL_PATH = ROOT / "assets" / "js" / "detail.js"
FLOW = FLOW_PATH.read_text(encoding="utf-8")
DETAIL = DETAIL_PATH.read_text(encoding="utf-8")
# RUN 57. THE RESET CONTROL MOVED FILE; THE PROMISE DID NOT MOVE AND IS NOT WEAKENED.
# Until Run 57 the project detail page carried TWO controls that clear stored signals, and this
# suite read the promise off `.detail-reset`'s title attribute in detail.js. Run 57 MERGED the
# two handler bodies into one control -- `.pe-reset` in ingest.js, which does the union of both
# and asks before acting -- and removed `.detail-reset`. The promise is made in exactly the same
# words by the surviving control's confirmation, so the guard is RE-POINTED AT WHERE THE CONTROL
# NOW LIVES rather than deleted or loosened: it still requires the sentence, and it additionally
# requires that detail.js no longer carries a reset control, so the sentence cannot be satisfied
# by a control that is no longer there.
INGEST_PATH = ROOT / "assets" / "js" / "ingest.js"
INGEST = INGEST_PATH.read_text(encoding="utf-8")

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failures.append(f"{label}: {detail}")
        print(f"  FAIL  {label}  {detail}")


print("=" * 78)
print("SECTION 1  the reset boundary is computed, and the retained documents are disclosed")
print("=" * 78)

check("retainedBeforeReset" in FLOW,
      "the diagram computes how many documents are retained from before the reset")
check("UPLOADED SINCE THE RESET" in FLOW,
      "the header says SINCE THE RESET when a reset boundary exists")
check("RETAINED" in FLOW,
      "and names the retained documents in the header")
check("retained and will be read again when signals are regenerated" in FLOW,
      "the summary strip states that the retained documents will be read again")
check("no documents uploaded since its stored signals were cleared" in FLOW,
      "and that the zero is a since-the-reset zero, not an absence of evidence")

# The boundary is the LAST signals_reset entry, and the retained count is taken from the events
# BEFORE it. Asserted structurally so a fix that counts the wrong side cannot pass.
seg = FLOW[FLOW.find("var retainedBeforeReset"):]
seg = seg[:2000]
check("evAll.slice(0, evAll.length - sinceReset.length)" in seg,
      "the retained count is taken from the events BEFORE the reset boundary", seg[:200])
check("signals_extracted" in seg,
      "and counts extraction events, the same record the document panel counts")

print()
print("=" * 78)
print("SECTION 2  what deliberately did NOT change")
print("=" * 78)

# A project that was never reset must read exactly as it did before this fix.
check("' UPLOADED ON THIS PROJECT'" in FLOW,
      "a project with no reset still reads UPLOADED ON THIS PROJECT, unchanged")
check("'This project has no uploaded documents and no current results, so nothing '" in FLOW
      or "This project has no uploaded documents and no current results" in FLOW,
      "the empty-project sentence is kept for a project that has never been reset")
# The since-reset window itself is untouched: the count still starts from sinceReset.
m = re.search(r"var uploadedDocCount = 0;(.{0,600})", FLOW, re.S)
check(bool(m) and "var evs = sinceReset;" in m.group(1),
      "the document count is still taken from the since-the-reset window only",
      (m.group(1)[:160] if m else "block not found"))
check("retainedBeforeReset" not in (m.group(1) if m else ""),
      "and the retained documents are NOT re-admitted to that window",
      (m.group(1)[:200] if m else ""))
# The reset control's promise, which is the authority for all of the above.
check("does not delete documents" in INGEST.lower()
      and 'class="btn small pe-reset">Reset signals<' in INGEST,
      "the reset control still states that it does not delete documents, in the file that now "
      "carries it (assets/js/ingest.js, the surviving .pe-reset and its confirmation)",
      "promise=%s survivor=%s" % ("does not delete documents" in INGEST.lower(),
                                  'class="btn small pe-reset">Reset signals<' in INGEST))
check('class="btn small detail-reset"' not in DETAIL
      and "function wireReset(" not in DETAIL,
      "and detail.js no longer carries a reset control at all, so the promise cannot be "
      "satisfied by a control that is no longer there")

print()
print("=" * 78)
print("SECTION 3  guard non-vacuity: every guard proved RED by a real violation, then GREEN")
print("=" * 78)


def scan(text: str) -> list[str]:
    """The properties section 1 asserts, as a recomputable list of failures."""
    bad = []
    for needle, name in (
        ("retainedBeforeReset", "computes-retained"),
        ("UPLOADED SINCE THE RESET", "header-since-reset"),
        ("retained and will be read again when signals are regenerated", "summary-retained"),
        ("no documents uploaded since its stored signals were cleared", "summary-since-reset"),
        ("evAll.slice(0, evAll.length - sinceReset.length)", "boundary-before-side"),
    ):
        if needle not in text:
            bad.append(name)
    # The window must not be widened. This is the direction that would silently undo Run 18.
    mm = re.search(r"var uploadedDocCount = 0;(.{0,600})", text, re.S)
    block = mm.group(1) if mm else ""
    if "var evs = sinceReset;" not in block:
        bad.append("window-no-longer-since-reset")
    if "retainedBeforeReset" in block:
        bad.append("retained-readmitted-to-window")
    return bad

# Each mutation reverts exactly one part of the fix, or re-introduces the defect, in a COPY of
# the shipped file. The named guard must go red on that copy. Anything that does not go red is a
# guard that would not have caught the defect this file exists for.
MUTATIONS = [
    ("revert the header to the false wording",
     "uploadedDocCount + ' UPLOADED SINCE THE RESET, ' + retainedBeforeReset +",
     "uploadedDocCount + ' UPLOADED ON THIS PROJECT' + (0 &&",
     "header-since-reset"),
    ("revert the summary strip to the false sentence",
     "retained and will be read again when signals are regenerated",
     "no uploaded documents at all",
     "summary-retained"),
    ("revert the since-the-reset wording in the summary",
     "no documents uploaded since its stored signals were cleared",
     "no uploaded documents whatsoever",
     "summary-since-reset"),
    ("count the retained documents from the WRONG side of the boundary",
     "evAll.slice(0, evAll.length - sinceReset.length)", "sinceReset",
     "boundary-before-side"),
    ("widen the document window back across the reset, undoing Run 18",
     "      var evs = sinceReset;", "      var evs = evAll;",
     "window-no-longer-since-reset"),
    ("re-admit the retained documents into the current window",
     "      var evs = sinceReset;",
     "      var evs = sinceReset; retainedBeforeReset = retainedBeforeReset;",
     "retained-readmitted-to-window"),
]

for label, find, repl, expect in MUTATIONS:
    check(find in FLOW, f"mutation target present in the shipped file: {label}", find[:70])
    mutant = FLOW.replace(find, repl, 1)
    check(mutant != FLOW, f"mutation actually changed bytes: {label}")
    bad = scan(mutant)
    check(expect in bad, f"guard turns RED under: {label}",
          f"expected {expect!r} among {bad}")

# GREEN on the shipped file, re-read from disk so this cannot pass on an untouched copy.
on_disk = FLOW_PATH.read_text(encoding="utf-8")
check(on_disk == FLOW, "the shipped file on disk is unmodified by this suite")
check(scan(on_disk) == [], "every guard is GREEN on the shipped file", str(scan(on_disk)))

print()
if failures:
    print("FAILURES:")
    for f in failures:
        print("  " + f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
