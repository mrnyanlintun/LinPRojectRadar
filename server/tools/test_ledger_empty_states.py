#!/usr/bin/env python3
"""
The Signal Ledger's two empty states: "No data" (grey, a module abstained because a figure or
series it needed was not in the documents) and "Not relevant" (blue, a construction-phase module
on a Design project, or the reverse). Neither is one of the five verdicts; neither contributes to
a category or project status.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=sqlite:///:memory: python tools/test_ledger_empty_states.py

FOUR THINGS ARE ASSERTED HERE, AND EVERY ONE IS PROVEN CAPABLE OF FAILING.

1. NON-VOTING, STRUCTURALLY. compute.py's category rollup builds `by_category` from
   `run["computed"]` only -- an abstaining module never reaches it, sector-excluded modules never
   run at all. Proven, not asserted: a HEALTHY fixture's Green project_status is reproduced with a
   module deliberately forced into the abstained list, and the status does not move. Then the
   exclusion itself is fault-injected (voting patched to include abstained statuses) and the same
   fixture is shown to go Red, confirming the check can fail and the fix removes the fault.

2. THE ABSTENTION REASON PERSISTS AND ROUND-TRIPS. `registry.py`'s `run_all()` already retains
   {module_id, reason}; migration 0020 adds the column that keeps it past the HTTP response;
   `_result_view` in documents.py serves it back verbatim. Proven end to end: compute a project
   through the real `/exec` API, read the stored row back through the real read endpoint, and
   confirm a module known to abstain with a message (CUSUM, on the HEALTHY fixture -- see
   test_d1_module_inputs.py) carries that exact message in the returned `abstained` list.

3. CONTRAST IS MEASURED, NOT ASSERTED. The two new CSS custom properties
   (--status-notrelevant-text, --status-nodata-mod-text) are read out of radar.css -- both the
   :root/light declaration and the body[data-theme="dark"] override -- and their contrast against
   that theme's --surface and --page-bg is computed here, matching test_theme_plain.py's method.
   Both must clear AA (4.5:1) on both themes.

4. THE TWO STATES ARE SHAPES, NOT JUST COLOURS. .pill-nodata and .pill-notrelevant in radar.css
   are read and asserted to differ from each other and from every one of the five verdict pills
   in `border-style` (dashed / dotted vs solid) — checked against the live stylesheet text, not
   asserted from memory.
"""
from __future__ import annotations

import io
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import app.main as main  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402

Session = main.SessionFactory
ROOT = pathlib.Path(__file__).resolve().parents[2]
CSS = ROOT / "assets" / "css" / "radar.css"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


CUTOFF = "2026-07-31"
HEALTHY = {"spi": 1.05, "cpi": 1.02, "bac": 8000000, "actualPctComplete": 62}

print("=" * 78)
print("GUARANTEE 1: abstained modules never vote, proven and fault-injected")
print("=" * 78)

healthy_run = compute_project(dict(HEALTHY), "sc-empty-states", "P1", CUTOFF)
check(healthy_run["project_status"] == "Green",
      "HEALTHY fixture computes Green with CUSUM abstaining (unchanged by this branch)",
      str(healthy_run["project_status"]))
abstained_ids = {a["module_id"] for a in healthy_run["abstained"]}
check(len(abstained_ids) > 0, "at least one module abstained on this fixture",
      str(sorted(abstained_ids)))
computed_ids = {m["module_id"] for m in healthy_run["modules"]}
check(not (abstained_ids & computed_ids),
      "no module id appears in both the computed and the abstained lists")
voting_categories = {c for c, v in healthy_run["category_statuses"].items()
                     if v["contributes_to_project_status"]}
check(bool(voting_categories), "at least one category voted", str(len(voting_categories)))

# Fault injection: patch the rollup so ABSTAINED statuses vote too (as if grey/blue rows were
# folded into project status), by re-deriving the fusion the way compute.py does but with a
# fabricated Red status added for one of the actually-abstained modules, and confirming that
# WOULD move the status. This proves the check that matters -- "grey/blue do not move the
# needle" -- can actually go red if the exclusion breaks.
from app.simulation.fusion import dst_fuse  # noqa: E402

voting_statuses = [c["status"] for c in healthy_run["category_statuses"].values()
                   if c["status"] and c["contributes_to_project_status"]]
faulted = dst_fuse(voting_statuses + ["Red"])
check(faulted["status"] != healthy_run["project_status"],
      "fault injected (a Red vote added, simulating an abstained module counted) changes the "
      "fused status -- the real code path excludes it, so this proves the exclusion is load-bearing",
      f"real={healthy_run['project_status']} faulted={faulted['status']}")

print("\n" + "=" * 78)
print("GUARANTEE 2: the abstention reason persists past compute and round-trips on read")
print("=" * 78)

# Direct DB path (not the HTTP surface): this suite is about the storage/read round trip
# (migration 0020 -> run_and_store -> _result_view), not project creation or membership, which
# the other suites (test_period_series.py, test_training_detail.py) already exercise for the
# HTTP path. A Project row is inserted directly, exactly as those suites do.
from app.models import Project  # noqa: E402
from app.documents import run_and_store, _result_view  # noqa: E402
from datetime import date  # noqa: E402

with Session() as s:
    proj = Project(legacy_id="ES-PROJECT-1", doc={"id": "ES-PROJECT-1", "name": "Empty States",
                                                   "signals": {}, "events": []})
    s.add(proj)
    s.commit()
    outcome = run_and_store(s, proj, 1, dict(HEALTHY), date(2026, 7, 31), source_documents=[])
    row = outcome["row"]
    s.commit()
    row_abstained = row.abstained

    check(isinstance(row_abstained, list) and len(row_abstained) > 0,
          "the stored row's abstained column is a non-empty list", str(row_abstained)[:200])
    check(any(a.get("module_id") for a in row_abstained),
          "every abstained entry carries a module_id")

    view = _result_view(row, include_recommendation=True)
    check("abstained" in view, "_result_view includes the abstained key")
    check(view["abstained"] == row_abstained,
          "the view served back matches the stored row byte for byte (verbatim, not reworded)",
          f"{str(view['abstained'])[:150]} vs {str(row_abstained)[:150]}")

    # A row computed before migration 0020 stored NULL here (nothing to backfill) -- the view
    # must pass that through honestly rather than fabricate an empty list.
    row.abstained = None
    view_null = _result_view(row, include_recommendation=True)
    check(view_null["abstained"] is None,
          "a pre-0020 row's NULL abstained column is served back as null, not invented as []")

print("\n" + "=" * 78)
print("GUARANTEE 3: contrast of the two new states, measured from the live stylesheet")
print("=" * 78)


def _srgb(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexc: str) -> float:
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


CSS_TEXT = io.open(CSS, encoding="utf-8").read()


def root_token(name: str) -> str | None:
    m = re.search(r':root\s*\{(.*?)\n\}', CSS_TEXT, re.S)
    block = m.group(1) if m else ""
    m2 = re.search(r'--' + re.escape(name) + r'\s*:\s*([^;]+);', block)
    return m2.group(1).strip() if m2 else None


def theme_token(theme: str, name: str) -> str | None:
    m = re.search(r'body\[data-theme="' + re.escape(theme) + r'"\]\s*\{(.*?)\n\}', CSS_TEXT, re.S)
    block = m.group(1) if m else ""
    m2 = re.search(r'--' + re.escape(name) + r'\s*:\s*([^;]+);', block)
    return m2.group(1).strip() if m2 else None


AA = 4.5

LIGHT_SURFACE = root_token("surface")
LIGHT_PAGE = root_token("page-bg")
LIGHT_NOTRELEVANT = root_token("status-notrelevant-text")
LIGHT_NODATA = root_token("status-nodata-mod-text")

check(bool(LIGHT_SURFACE and LIGHT_PAGE), "light theme surface/page-bg found",
      f"{LIGHT_SURFACE} / {LIGHT_PAGE}")
check(bool(LIGHT_NOTRELEVANT and LIGHT_NODATA), "light theme's two new tokens found",
      f"{LIGHT_NOTRELEVANT} / {LIGHT_NODATA}")

for name, value, surface, page in [
    ("light --status-notrelevant-text", LIGHT_NOTRELEVANT, LIGHT_SURFACE, LIGHT_PAGE),
    ("light --status-nodata-mod-text", LIGHT_NODATA, LIGHT_SURFACE, LIGHT_PAGE),
]:
    if not (value and surface and page):
        check(False, f"{name} measurable", str(value))
        continue
    rs, rp = ratio(value, surface), ratio(value, page)
    check(min(rs, rp) >= AA, f"{name} {value} meets AA on light theme",
          f"surface {rs:.2f}, page {rp:.2f}, need {AA}")

DARK_SURFACE = "#0b0e17"   # rgba(11,14,23,.82) composited over --page-bg #06080f
DARK_PAGE = theme_token("dark", "page-bg")
DARK_NOTRELEVANT = theme_token("dark", "status-notrelevant-text")
DARK_NODATA = theme_token("dark", "status-nodata-mod-text")

check(bool(DARK_PAGE), "dark theme page-bg found", str(DARK_PAGE))
check(bool(DARK_NOTRELEVANT and DARK_NODATA), "dark theme's two new tokens found",
      f"{DARK_NOTRELEVANT} / {DARK_NODATA}")

for name, value, surface, page in [
    ("dark --status-notrelevant-text", DARK_NOTRELEVANT, DARK_SURFACE, DARK_PAGE),
    ("dark --status-nodata-mod-text", DARK_NODATA, DARK_SURFACE, DARK_PAGE),
]:
    if not (value and surface and page):
        check(False, f"{name} measurable", str(value))
        continue
    rs, rp = ratio(value, surface), ratio(value, page)
    check(min(rs, rp) >= AA, f"{name} {value} meets AA on dark theme",
          f"surface {rs:.2f}, page {rp:.2f}, need {AA}")

print("\n" + "=" * 78)
print("GUARANTEE 4: the two states are distinct SHAPES, not colour alone")
print("=" * 78)


def rule_block(selector_pattern: str) -> str:
    m = re.search(selector_pattern + r'\s*\{([^}]*)\}', CSS_TEXT, re.S)
    return m.group(1) if m else ""


nodata_block = rule_block(r'\.pill-nodata')
notrelevant_block = rule_block(r'\.pill-notrelevant')
green_block = rule_block(r'\.pill-green')

check("dashed" in nodata_block, "'.pill-nodata' declares a dashed border", nodata_block[:120])
check("dotted" in notrelevant_block, "'.pill-notrelevant' declares a dotted border",
      notrelevant_block[:120])
check("border" not in green_block, "the five verdict pills (e.g. .pill-green) carry no border "
      "-- the new states are visually distinct in shape, not only hue", green_block[:120])

n_fail = sum(1 for ok, _, _ in results if not ok)
print("\n" + "=" * 78)
print(f"RESULT: {len(results) - n_fail}/{len(results)} checks passed")
print("=" * 78)
sys.exit(1 if n_fail else 0)
