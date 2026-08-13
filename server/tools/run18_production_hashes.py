#!/usr/bin/env python3
"""
RUN 18, GATE 12. PRODUCTION AND PARTICIPANT PROTECTION.

Hashes every production file the run is forbidden to change after the corrected UI baseline is
frozen, and compares against a stored manifest. Two modes:

    python tools/run18_production_hashes.py --write   # record the baseline manifest
    python tools/run18_production_hashes.py           # verify nothing moved since

WHAT IS COVERED. The served application (server/app/), the participant-facing assets
(assets/, index.html), the registry baseline (p0-baseline/), and the questionnaire and
visualisation payloads participants actually see. Test and audit trees are deliberately NOT
covered: Run 18 is expected to add to them.

WHY A MANIFEST AND NOT `git diff`. A git diff proves the working tree matches a commit. It does
not prove that the commit itself did not carry a production change, and it says nothing once the
audit-only phase has produced several commits of its own. The manifest is a content hash taken
at the moment the baseline was frozen, so every later check is against the frozen bytes rather
than against whatever the most recent commit happens to contain.

It also re-proves the three invariants that must hold for the whole audit phase, from the live
registry rather than from a copy: voting is exactly {A1.7, A1.8}; the eight concept-only modules
are DISABLED_UNSAFE; Material Cost Variance is DISABLED_EVIDENCE_UNDER_REVIEW and is not voting.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "code_audit" / "run18_production_baseline.sha256"

COVERED = (
    ("server/app", ("*.py",)),
    ("assets", ("*.js", "*.css", "*.json", "*.html")),
    ("p0-baseline", ("*.csv", "*.json", "*.md")),
)
SINGLE_FILES = ("index.html",)

passed = total = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def covered_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for rel, patterns in COVERED:
        base = ROOT / rel
        if not base.exists():
            continue
        for pat in patterns:
            out.extend(p for p in base.rglob(pat)
                       if "__pycache__" not in p.parts and p.is_file())
    out.extend(ROOT / f for f in SINGLE_FILES if (ROOT / f).is_file())
    return sorted(set(out))


def digest(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def manifest_now() -> dict[str, str]:
    return {str(p.relative_to(ROOT)): digest(p) for p in covered_files()}


def registry_invariants() -> None:
    sys.path.insert(0, str(ROOT / "server"))
    from app.simulation.registry import (  # noqa: E402
        CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, DISABLED_EVIDENCE_UNDER_REVIEW)
    check(set(CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
          "the voting set is exactly TCPI and Variance at Completion",
          str(sorted(CORE_VOTING_MODULES)))
    check(len(CORE_VOTING_MODULES) == 2, "the voting set has exactly two members",
          str(len(CORE_VOTING_MODULES)))
    check(len(DISABLED_CONCEPT_ONLY) == 8,
          "the eight concept-only methods remain operationally disabled",
          str(sorted(DISABLED_CONCEPT_ONLY)))
    check(set(DISABLED_EVIDENCE_UNDER_REVIEW) == {"A3.4"},
          "Material Cost Variance remains disabled under evidence review",
          str(sorted(DISABLED_EVIDENCE_UNDER_REVIEW)))
    check("A3.4" not in CORE_VOTING_MODULES, "Material Cost Variance is not voting")
    overlap = set(DISABLED_CONCEPT_ONLY) & set(CORE_VOTING_MODULES)
    check(overlap == set(), "no concept-only module is in the voting set", str(overlap))


def main() -> int:
    write = "--write" in sys.argv
    now = manifest_now()
    if write:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text("".join(f"{h}  {p}\n" for p, h in sorted(now.items())),
                            encoding="utf-8")
        print(f"wrote {MANIFEST} covering {len(now)} production files")
        registry_invariants()
        print(f"\nRESULT: {passed}/{total} checks passed")
        return 0 if passed == total else 1

    check(MANIFEST.exists(), "the frozen production manifest exists")
    if not MANIFEST.exists():
        print(f"\nRESULT: {passed}/{total} checks passed")
        return 1
    stored = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        h, p = line.split("  ", 1)
        stored[p] = h
    added = sorted(set(now) - set(stored))
    removed = sorted(set(stored) - set(now))
    changed = sorted(p for p in set(now) & set(stored) if now[p] != stored[p])
    check(added == [], "no production file was added after the baseline freeze", str(added))
    check(removed == [], "no production file was removed after the baseline freeze",
          str(removed))
    check(changed == [], "no production file changed after the baseline freeze", str(changed))
    check(len(stored) > 100, "the manifest covers the whole production surface",
          str(len(stored)))
    registry_invariants()
    print(f"\nRESULT: {passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
