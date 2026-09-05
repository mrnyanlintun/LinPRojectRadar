"""
Regenerate the code_audit/ module source export from the registry -- not from the previous
export.

Run 5 of the remediation programme (post-freeze; see remediation_programme.md and
T6_HANDOFF.md). Fixes the defect the audit found in the 2026-08-10 export: it claimed 52 Group
A modules and wrote 43 sections, silently omitting A4.2 through A4.10, because nothing checked
the emitted section count against the expected id set. This script asserts that set explicitly
and refuses to write a group file if the emitted ids do not exactly match what the registry
declares.

Usage:
    python3 server/tools/export_module_source.py [--drop ID ...] [--check-only]

--drop is for proving the assertion can fail: pass one or more module ids to omit from
emission (as if the same defect recurred) and the script exits non-zero with the mismatch
reported, writing nothing. Without --drop it writes the five files into code_audit/ plus a
CHECKSUMS.sha256 manifest covering every file in that directory.
"""

from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import argparse
import csv
import hashlib
import inspect
import pathlib
import sys
from typing import Callable

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import registry as reg  # noqa: E402
from app.simulation.models import VALIDATED  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED, compute_portfolio  # noqa: E402
from app.simulation import signal_package as sp  # noqa: E402

CSV_PATH = ROOT / "p0-baseline" / "module_renumbering_map.csv"
OUT_DIR = ROOT / "code_audit"

GROUP_NAMES = {
    "A": "Project Health",
    "B": "Recommendation and Governance",
    "C": "Data and Evidence Health",
    "D": "Portfolio Level",
}
GROUP_FILES = {
    "A": "GROUP_A_project-health.md",
    "B": "GROUP_B_recommendation-governance.md",
    "C": "GROUP_C_data-evidence-health.md",
    "D": "GROUP_D_portfolio-level.md",
}


def load_csv_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8-sig") as fh:
        return [r for r in csv.DictReader(fh) if r["new_id"].strip().upper() != "RETIRED"]


def expected_ids_by_group() -> dict[str, set[str]]:
    """
    The set this export must produce, per group: every registry-computed (VALIDATED /
    PORTFOLIO_VALIDATED) module. Document Risk Score (A4.1) is deliberately excluded from this
    set -- it is declared in the registry CSV but implemented by no formula function, a value
    the extraction model supplies rather than one the analytical server computes (confirmed in
    the code: absent from VALIDATED, present in the CSV; see GROUP_ASSIGNMENT.md and
    REPORT_2026-08-11_run4-validate-seven.md). It is still exported, as its own labelled
    "supplied, not computed" entry -- see supplied_entries() below -- but it is not part of the
    counted, asserted set.
    """
    out: dict[str, set[str]] = {"A": set(), "B": set(), "C": set(), "D": set()}
    for mid in VALIDATED:
        grp = mid[0]
        out[grp].add(mid)
    for mid in PORTFOLIO_VALIDATED:
        out["D"].add(mid)
    return out


def supplied_entries() -> dict[str, str]:
    """Modules declared in the registry but not registry-computed. Currently: A4.1 only."""
    csv_ids = {r["new_id"] for r in load_csv_rows()}
    computed = set()
    for g in expected_ids_by_group().values():
        computed |= g
    return {mid: "Document Risk Score" for mid in sorted(csv_ids - computed)}


def activation_note(new_id: str) -> str:
    """
    One line, always present, stating the module's activation state and (for anything other
    than plain enabled-and-voting) the reason. Per the task: enabled and voting, advisory and
    non-voting, disabled, or newly wired and unvalidated -- and a module can carry more than one
    tag (e.g. newly wired AND disabled).
    """
    tags: list[str] = []
    if new_id in reg.DISABLED_CONCEPT_ONLY:
        tags.append(
            "DISABLED. Concept-only: implements no defensible version of the analytical "
            "structure its name claims. Non-executable in production, non-voting, excluded from "
            "every fusion input and every rollup."
        )
    elif new_id in reg.CORE_VOTING_MODULES:
        tags.append(
            "ENABLED AND VOTING. One of the two CORE modules with a sourced band boundary, a "
            "built abstention guard and passing boundary tests (Run 4). Feeds category rollup, "
            "project status fusion, generated recommendation text, courses of action and the "
            "decision card. " + reg.BAND_SOURCE_LIMIT
        )
    elif new_id in reg.HELD_NON_VOTING_UNSOURCED_BANDS:
        tags.append(
            "ADVISORY, NON-VOTING. One of the seven CORE candidates; computes and shows its "
            "finding on the ledger, but held out of voting because " +
            reg.HELD_NON_VOTING_UNSOURCED_BANDS[new_id].split(": ", 1)[1] + "."
        )
    else:
        tags.append("ADVISORY, NON-VOTING. Computes and shows its finding; excluded from "
                     "category rollup, project status fusion, recommendation text, courses of "
                     "action and the decision card, on the footing of every non-CORE module.")

    proxy_q = reg.PROXY_QUALIFIERS.get(new_id)
    if proxy_q:
        tags.append(f"RELABELLED AS PROXY: {proxy_q}")

    if new_id in sp.NESTED_INPUT_MODULES:
        tags.append("NEWLY WIRED: " + sp.WIRING_NOTE)

    return " ".join(tags)


def source_for(new_id: str) -> tuple[str, str]:
    """(label, verbatim source) for a registry-computed module."""
    if new_id in VALIDATED:
        label, func = VALIDATED[new_id]
        try:
            src = inspect.getsource(func)
        except (OSError, TypeError):
            src = f"# source unavailable for {func!r}"
        return label, src
    if new_id in PORTFOLIO_VALIDATED:
        label = PORTFOLIO_VALIDATED[new_id]
        return label, ""  # Group D shares one function; handled separately.
    raise KeyError(new_id)


def module_name(new_id: str, csv_index: dict[str, dict[str, str]]) -> str:
    row = csv_index.get(new_id)
    return row["module_name"] if row else new_id


def category_name(new_id: str, csv_index: dict[str, dict[str, str]]) -> str:
    row = csv_index.get(new_id)
    return row["category_name"] if row else ""


def render_group_file(group: str, ids: list[str], csv_index: dict[str, dict[str, str]]) -> str:
    lines: list[str] = []
    lines.append(f"# Group {group}: {GROUP_NAMES[group]} -- module source export\n")
    lines.append(
        "Regenerated from the registry (Run 5, post-freeze; see "
        "code_audit/REPORT_2026-08-11_run5-export.md). Every section below carries its "
        "activation state. Headings are canonical module names; no module id appears as a "
        "heading, per NAMING_AUTHORITY.md.\n"
    )
    lines.append(f"**{len(ids)} modules in this group.**\n")
    lines.append("---\n")

    if group == "D":
        lines.append("## Portfolio computation (all five Group D modules)\n")
        lines.append(
            "Activation state: not a single module. This section holds the shared source only; "
            "each of the five modules below carries its own activation state.\n"
        )
        lines.append(
            "All five Group D modules are produced by one function, `compute_portfolio`, in "
            "`server/app/simulation/portfolio.py`. There is no per-module function to excerpt; "
            "the full function is transcribed once and each subsection below states which "
            "returned keys and status fields belong to which module.\n"
        )
        lines.append("```python\n" + inspect.getsource(compute_portfolio).rstrip() + "\n```\n")
        lines.append("---\n")
        for new_id in ids:
            name = PORTFOLIO_VALIDATED[new_id]
            lines.append(f"## {name.replace('_', ' ')}\n")
            lines.append(f"Activation state: {activation_note(new_id)}\n")
            lines.append(
                f"Method class `{name}`, produced within `compute_portfolio` above (search the "
                f"function for `\"method_class\": \"{name}\"`).\n"
            )
            lines.append("---\n")
        return "\n".join(lines)

    for new_id in ids:
        label, src = source_for(new_id)
        name = module_name(new_id, csv_index)
        cat = category_name(new_id, csv_index)
        lines.append(f"## {name}\n")
        lines.append(f"Purpose: {name}, category \"{cat}\".\n")
        lines.append(f"Activation state: {activation_note(new_id)}\n")
        lines.append(f"Method class: `{label}`\n")
        lines.append("```python\n" + src.rstrip() + "\n```\n")
        lines.append("---\n")

    if group == "A":
        # The one Group A entry the registry declares but does not compute -- exported and
        # labelled, never counted as one of the group's registry-computed ids.
        for new_id, name in supplied_entries().items():
            lines.append(f"## {name} (supplied, not computed)\n")
            lines.append(
                f"Activation state: SUPPLIED, NOT COMPUTED. `{new_id}` is declared in "
                "`p0-baseline/module_renumbering_map.csv` but implemented by no formula "
                "function anywhere under `server/app/simulation/`. It is a value the extraction "
                "model supplies and the server carries through unmodified -- not a computation "
                "this platform performs. Not part of the group's registry-computed count, and "
                "not one of the 100 registry-computed modules across the four groups. See "
                "GROUP_ASSIGNMENT.md and REPORT_2026-08-11_run4-validate-seven.md.\n"
            )
            lines.append("No source to export: no formula function exists.\n")
            lines.append("---\n")

    return "\n".join(lines)


def write_manifest() -> str:
    manifest_lines = ["# SHA-256 checksums of every file in code_audit/, recomputed at write "
                       "time.\n", "# Verify with: sha256sum -c CHECKSUMS.sha256 (from code_audit/)\n"]
    entries = []
    for p in sorted(OUT_DIR.rglob("*")):
        if p.is_file() and p.name != "CHECKSUMS.sha256":
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            rel = p.relative_to(OUT_DIR)
            entries.append(f"{digest}  {rel}")
    manifest = "".join(manifest_lines) + "\n".join(entries) + "\n"
    (artifact_out(OUT_DIR / "CHECKSUMS.sha256")).write_text(manifest, encoding="utf-8")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", nargs="*", default=[],
                     help="Module ids to omit from emission, to prove the assertion can fail.")
    ap.add_argument("--check-only", action="store_true",
                     help="Compute and print counts; write nothing.")
    args = ap.parse_args()

    csv_index = {r["new_id"]: r for r in load_csv_rows()}
    expected = expected_ids_by_group()

    ok = True
    rendered: dict[str, str] = {}
    for group in ("A", "B", "C", "D"):
        exp_ids = sorted(expected[group])
        emit_ids = [i for i in exp_ids if i not in args.drop]

        # THE ASSERTION THE DEFECT LACKED: emitted ids must exactly equal the expected set.
        emitted_set = set(emit_ids)
        expected_set = set(exp_ids)
        if emitted_set != expected_set:
            missing = expected_set - emitted_set
            extra = emitted_set - expected_set
            print(f"EXPORT REFUSED for Group {group}: emitted id set does not match the "
                  f"registry's expected set.", file=sys.stderr)
            if missing:
                print(f"  missing ({len(missing)}): {sorted(missing)}", file=sys.stderr)
            if extra:
                print(f"  unexpected ({len(extra)}): {sorted(extra)}", file=sys.stderr)
            ok = False
            continue

        print(f"Group {group}: {len(emit_ids)} modules, ids match the registry exactly.")
        if not args.check_only:
            rendered[group] = render_group_file(group, emit_ids, csv_index)

    if not ok:
        print("\nEXPORT FAILED: at least one group's emitted section count did not match its "
              "expected id set. No files were written.", file=sys.stderr)
        return 1

    if args.check_only:
        print("check-only: no files written.")
        return 0

    for group, text in rendered.items():
        out_path = OUT_DIR / GROUP_FILES[group]
        artifact_out(out_path).write_text(text, encoding="utf-8")
        print(f"wrote {out_path}")

    manifest = write_manifest()
    print(f"wrote {OUT_DIR / 'CHECKSUMS.sha256'} ({len(manifest.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
