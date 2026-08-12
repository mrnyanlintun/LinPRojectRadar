#!/usr/bin/env python3
"""
RUN 11, GATE 4. THE DEFENSIBILITY CLAIM AUDIT.

THE PROPERTY. A claim may be made only if the repository contains evidence supporting that exact
claim. Two claims have no supporting evidence anywhere on this platform and cannot be made about
any module: that it is VALIDATED, and that it is CALIBRATED. There is no calibration set, no
fitted parameter, no holdout against real project outcomes and no comparison with observed
performance. What does exist is known-answer testing of stated formulas and, for many modules, a
domain and boundary enumeration. Those support one sentence and no more:

    "Arithmetic independently verified for the stated formula."

HOW THIS IS CHECKED. Not by reading a list of approved sentences, which would be the defect's own
sentence asserted back at itself. The live handbook object is parsed, every per-module string
field is swept, and any unqualified validation or calibration claim fails the suite. The evidence
statuses the browser now reads are separately required to be GENERATED from the registry rather
than hand-authored, and the generator is re-run here and its output compared byte for byte, so a
hand edit to the generated file fails too.

FAULT INJECTION at the end puts an unsupported "validated" claim into a scratch copy and requires
the audit to go red, after asserting the injection changed the bytes.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation.registry import DISABLED_CONCEPT_ONLY, load_registry  # noqa: E402

PASS = 0
TOTAL = 0
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, TOTAL
    TOTAL += 1
    if ok:
        PASS += 1
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL  {name}  {detail}")


#: The claims with no supporting evidence in this repository. Present tense and unqualified: the
#: pattern deliberately does NOT match "Validation for this method would consist of", which is a
#: statement about what has not been done and is the wording this run put in their place.
#: The negative lookbehind matters and is not a loophole. "It is not a calibrated forecast" is
#: the correction, not the defect, and a pattern that flagged it would force the handbook to stop
#: saying what a module is NOT — which is the most useful sentence on the page. Only an
#: AFFIRMATIVE claim fails.
UNSUPPORTED_CLAIM = re.compile(
    r"(?<!not )(?<!not a )(?<!never )\b(?:Validated by|validated by|is validated\b"
    r"|are validated\b|has been validated|empirically validated|empirically calibrated"
    r"|calibrated forecast|calibrated model|field-proven|field proven|proven in the field)\b"
)

HANDBOOK = ROOT / "assets" / "js" / "ds_defensibility_data.js"
EVIDENCE = ROOT / "assets" / "js" / "ds_defensibility_evidence.js"
GENERATOR = ROOT / "tools" / "build_run11_defensibility_evidence.py"


def handbook_modules(text: str) -> list[dict]:
    mods: list[dict] = []
    for m in re.finditer(r'"modules": \[', text):
        j = text.index("[", m.start())
        depth = 0
        for k in range(j, len(text)):
            if text[k] == "[":
                depth += 1
            elif text[k] == "]":
                depth -= 1
                if depth == 0:
                    break
        mods += json.loads(text[j:k + 1])
    return mods


def audit(text: str) -> list[tuple[str, str, str]]:
    out = []
    for mod in handbook_modules(text):
        for field, value in mod.items():
            if isinstance(value, str):
                hit = UNSUPPORTED_CLAIM.search(value)
                if hit:
                    out.append((mod.get("name", "?"), field, hit.group(0)))
    return out


live = HANDBOOK.read_text(encoding="utf-8")
mods = handbook_modules(live)
check("the handbook still holds a per-module record for every registered computation",
      len(mods) >= 100, f"{len(mods)} records")

residual = audit(live)
check("no module carries an unqualified validation or calibration claim",
      not residual, str(residual[:4]))

# The front matter is claim-bearing too, and it is where the broadest sentence lived.
front = live[:live.index('"modules"')]
front_hits = UNSUPPORTED_CLAIM.findall(front)
check("and the handbook front matter carries none either", not front_hits, str(front_hits[:4]))

# The permitted claim must actually appear, or the correction would have been a deletion rather
# than a replacement and the handbook would say nothing at all.
check("the permitted known-answer wording is stated somewhere in the evidence object",
      "Arithmetic independently verified for the stated formula."
      in EVIDENCE.read_text(encoding="utf-8"), "")
check("the platform-wide calibration status is stated as none",
      "Not calibrated." in EVIDENCE.read_text(encoding="utf-8"), "")
check("the platform-wide empirical status is stated as none",
      "Not empirically validated." in EVIDENCE.read_text(encoding="utf-8"), "")

# ------------------------------------------------------------------ generated, not hand-authored
check("the generator exists", GENERATOR.exists(), str(GENERATOR))
regenerated = subprocess.run([sys.executable, str(GENERATOR), "--stdout"],
                             cwd=str(ROOT), capture_output=True, text=True)
check("the generator runs cleanly", regenerated.returncode == 0, regenerated.stderr[-300:])
check("the committed evidence object is byte-identical to what the generator produces, so it "
      "cannot have been edited by hand",
      regenerated.stdout == EVIDENCE.read_text(encoding="utf-8"),
      f"{len(regenerated.stdout)} vs {len(EVIDENCE.read_text(encoding='utf-8'))}")

# ------------------------------------------------------------------ the nine statuses, separated
evidence_text = EVIDENCE.read_text(encoding="utf-8")
for field in ("implementation", "knownAnswer", "boundary", "calibration", "empirical",
              "canonicalStructure", "voting", "permittedClaim", "qualification"):
    check(f"the evidence object separates {field}", f"{field}:" in evidence_text, "")

registry = load_registry()
for m in registry:
    mid = m["new_id"]
    check(f"{mid} has an evidence record", f'"{mid}": {{' in evidence_text
          or f"'{mid}':" in evidence_text or f'{json.dumps(mid)}: {{' in evidence_text, "")

# A disabled module must claim nothing at all.
for mid in list(DISABLED_CONCEPT_ONLY)[:3]:
    i = evidence_text.find(json.dumps(mid) + ": {")
    seg = evidence_text[i:i + 900] if i >= 0 else ""
    check(f"{mid} is disabled and claims nothing", "No claim." in seg, seg[:120])

# ------------------------------------------------------------------ FAULT INJECTION
scratch = live.replace('"accreditationBasis": "', '"accreditationBasis": "Validated by field '
                       'comparison against completed programmes. ', 1)
check("INJECTION applied: the scratch handbook differs from the live one", scratch != live,
      "no change")
injected = audit(scratch)
check("INJECTION RED: an unsupported validated claim is detected by the audit",
      len(injected) > len(residual), f"{len(injected)} vs {len(residual)}")

scratch2 = live.replace('"implementationFidelity": "', '"implementationFidelity": "This is an '
                        'empirically calibrated model, and the bands are a calibrated model. ', 1)
check("INJECTION applied: the calibration scratch differs", scratch2 != live, "no change")
check("INJECTION RED: an unsupported calibration claim is detected",
      len(audit(scratch2)) > len(residual), "")

# And the generator guard: a hand edit to the generated file must be caught.
scratch3 = evidence_text.replace('"Not calibrated.', '"Calibrated against programme outcomes.', 1)
check("INJECTION applied: the evidence scratch differs", scratch3 != evidence_text, "no change")
check("INJECTION RED: a hand edit to the generated evidence object is detected",
      scratch3 != regenerated.stdout, "not detected")

print("")
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  " + f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
