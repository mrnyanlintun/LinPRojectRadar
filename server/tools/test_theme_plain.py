#!/usr/bin/env python3
"""
The plain theme: its contrast, its status encoding, and the research gate.

Run (from server/):

    PYTHONIOENCODING=utf-8 DATABASE_URL=... SESSION_SECRET=... python tools/test_theme_plain.py

FOUR THINGS ARE ASSERTED, AND THE FIRST TWO ARE MEASURED RATHER THAN TRUSTED.

1. CONTRAST. Every colour is read OUT OF radar.css and the ratio is computed here, so a comment
   claiming a ratio cannot make this pass. Changing a hex in the stylesheet changes the number
   this file computes, and if it drops below AA the suite goes red.

2. STATUS WITHOUT HUE. Yellow and Amber are close in hue by nature and closer still once both
   are darkened for a white field, so on this theme the colour may not be the only carrier. The
   five status dots must resolve to five DISTINCT shapes, and the check compares the computed
   shape declarations against each other rather than asserting any particular one.

3. A RESEARCH ACCOUNT RENDERS THE FIXED THEME, even with another stored. Exercised through the
   real /exec endpoint with a value written directly into the column first, because the point is
   that a row that already exists is ignored.

4. THE SERVER REFUSES THE CHANGE. Not the interface: the refusal is asserted against a POST that
   a hidden control would never have sent.
"""
from __future__ import annotations

import io
import json
import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import sqlalchemy as sa  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import AuditEvent, Participant  # noqa: E402
from app.features import RESEARCH_FORBIDDEN_ACTIONS  # noqa: E402
from app.theme import DEFAULT_THEME, RESEARCH_THEME, THEMES  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
ROOT = pathlib.Path(__file__).resolve().parents[2]
CSS = ROOT / "assets" / "css" / "radar.css"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


# ---------------------------------------------------------------- contrast maths


def _srgb(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def theme_block(name: str) -> str:
    """The declaration block for one theme, read out of the live stylesheet."""
    text = io.open(CSS, encoding="utf-8").read()
    m = re.search(r'body\[data-theme="' + re.escape(name) + r'"\]\s*\{(.*?)\n\}', text, re.S)
    return m.group(1) if m else ""


def token(block: str, name: str) -> str | None:
    m = re.search(r'--' + re.escape(name) + r'\s*:\s*([^;]+);', block)
    return m.group(1).strip() if m else None


print("=" * 78)
print("GUARANTEE 1: the plain theme's contrast, measured from the stylesheet")
print("=" * 78)

block = theme_block("plain")
check(bool(block), "the plain theme block exists in radar.css", f"{len(block)} chars")

SURFACE = token(block, "surface")
PAGE = token(block, "page-bg")
check(SURFACE == "#ffffff", "surface is white", str(SURFACE))
check(bool(PAGE), "page background is declared", str(PAGE))

AA = 4.5
TEXT_TOKENS = ["text", "heading", "muted", "faint", "phosphor",
               "status-green-text", "status-yellow-text", "status-amber-text",
               "status-red-text", "status-complete-text"]
measured: dict[str, tuple[float, float]] = {}
for name in TEXT_TOKENS:
    value = token(block, name)
    ok_hex = bool(value and re.fullmatch(r"#[0-9a-fA-F]{6}", value))
    check(ok_hex, f"--{name} is a plain hex this file can measure", str(value))
    if not ok_hex:
        continue
    on_surface = ratio(value, SURFACE)
    on_page = ratio(value, PAGE)
    measured[name] = (on_surface, on_page)
    worst = min(on_surface, on_page)
    check(worst >= AA,
          f"--{name} {value} meets AA on both surface and page",
          f"surface {on_surface:.2f}, page {on_page:.2f}, need {AA}")

print("\n  measured ratios (surface / page):")
for name, (a, b) in measured.items():
    print(f"    {name:24s} {a:6.2f} / {b:6.2f}")

# Graphical objects (blips, pins, the globe's markers) need 3:1, not 4.5:1.
GRAPHIC = 3.0
sea = token(block, "globe-sphere")
land = token(block, "globe-land")
grat = token(block, "globe-graticule")
check(bool(sea and land and grat), "the globe's sea, land and graticule are declared",
      f"{sea} {land} {grat}")
if sea and land and grat:
    check(ratio(land, sea) >= GRAPHIC, "globe land clears 3:1 against the sea, so coastlines read",
          f"{ratio(land, sea):.2f}")
    check(ratio(grat, sea) >= GRAPHIC, "globe graticule clears 3:1 against the sea",
          f"{ratio(grat, sea):.2f}")
    worst_marker, worst_name = 99.0, ""
    for name in ("green", "yellow", "amber", "red", "complete"):
        fill = token(block, f"status-{name}")
        if fill and re.fullmatch(r"#[0-9a-fA-F]{6}", fill):
            r = ratio(fill, sea)
            if r < worst_marker:
                worst_marker, worst_name = r, name
    check(worst_marker >= GRAPHIC,
          "every status marker clears 3:1 against the sea",
          f"worst is {worst_name} at {worst_marker:.2f}")
    # The complaint this theme answers: a near-black sphere on a white page reads as a hole.
    check(luminance(sea) > luminance("#808080"),
          "the sea is lighter than mid grey, so the globe is not a hole in a white page",
          f"luminance {luminance(sea):.3f}")

print()
print("=" * 78)
print("GUARANTEE 2: status is never carried by hue alone")
print("=" * 78)

css_text = io.open(CSS, encoding="utf-8").read()
shapes: dict[str, str] = {}
for name in ("green", "yellow", "amber", "red", "complete"):
    m = re.search(r'\.status-dot-' + name + r'\s*\{([^}]*(?:border-radius|clip-path)[^}]*)\}',
                  css_text)
    decl = ""
    for mm in re.finditer(r'\.status-dot-' + name + r'\s*\{([^}]*)\}', css_text):
        body = mm.group(1)
        if "clip-path" in body or "border-radius" in body:
            decl = re.sub(r'\s+', " ", body).strip()
    shapes[name] = decl
    check(bool(decl), f"{name} declares a shape, not only a colour", decl[:60])

distinct = len({v for v in shapes.values() if v})
check(distinct == 5,
      "all five statuses resolve to five DISTINCT shapes, so Yellow and Amber differ "
      "without relying on hue",
      f"{distinct} distinct of {len(shapes)}; " + "; ".join(f"{k}={v[:26]}" for k, v in shapes.items()))

# The legend is the surface where a reader learns the encoding, so it must name each status
# in words. Read out of app.js's LEGEND_BANDS rather than asserted.
app_js = io.open(ROOT / "assets" / "js" / "app.js", encoding="utf-8").read()
bands = re.search(r'LEGEND_BANDS\s*=\s*\[(.*?)\];', app_js, re.S)
check(bands is not None, "the status legend's band table is present in app.js")
if bands:
    names = re.findall(r'\[\s*"([^"]+)"', bands.group(1))
    for want in ("Complete", "Green", "Yellow", "Amber", "Red"):
        check(want in names, f"the legend names {want} in words, not only in colour", str(names))
    check("legend-name" in app_js,
          "and the legend renders that word next to the swatch")

print()
print("=" * 78)
print("GUARANTEE 3: a research account renders the fixed theme, whatever is stored")
print("=" * 78)

ADMIN = "theme-bootstrap-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="THEME-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]


def make(code: str, account_type: str) -> tuple[str, str]:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": account_type})
    assert created.get("ok"), created
    tok = post({"action": "researchlogin",
                "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], tok


res_id, res_tok = make("THEME-RESEARCH", "research")
ops_id, ops_tok = make("THEME-OPS", "operational")

check(RESEARCH_THEME == DEFAULT_THEME,
      "the fixed research theme is the existing default, so the study's stimulus is unchanged",
      f"{RESEARCH_THEME} vs {DEFAULT_THEME}")

# THE PRECONDITION THAT MAKES THE NEXT CHECK MEAN ANYTHING: write a DIFFERENT theme into the
# research account's column directly. Without this the account would render the fixed theme
# anyway and the check would pass for the wrong reason.
OTHER = "plain"
check(OTHER != RESEARCH_THEME, "the stored value differs from the fixed one", OTHER)
with Session() as s:
    s.execute(sa.text("UPDATE participants SET theme = :t WHERE participant_id = :p"),
              {"t": OTHER, "p": res_id})
    s.commit()
with Session() as s:
    stored_now = s.execute(sa.text("SELECT theme FROM participants WHERE participant_id = :p"),
                           {"p": res_id}).scalar()
check(stored_now == OTHER, "and it really is in the column now", str(stored_now))

got = post({"action": "themeget", "session_token": res_tok})
check(got.get("ok") is True, "a research account can ask what it renders", str(got)[:120])
check(got.get("theme") == RESEARCH_THEME,
      "and is told the FIXED theme, not the one stored against it",
      f"stored {stored_now}, rendered {got.get('theme')}")
check(got.get("fixed") is True, "and is told the theme is fixed", str(got.get("fixed")))
check(got.get("stored") == OTHER,
      "the ignored value is still reported, so it is visible rather than silently dropped",
      str(got.get("stored")))

ops_got = post({"action": "themeget", "session_token": ops_tok})
check(ops_got.get("theme") == DEFAULT_THEME,
      "an operational account that has never chosen gets the existing default, so nobody's "
      "appearance changes without them choosing",
      str(ops_got.get("theme")))
check(ops_got.get("fixed") is False, "and is not fixed", str(ops_got.get("fixed")))

print()
print("=" * 78)
print("GUARANTEE 4: the SERVER refuses the change, not the interface")
print("=" * 78)

# THE REFUSAL IS IN TWO PLACES AND THE BEHAVIOURAL CHECK BELOW CANNOT TELL THEM APART.
# `gate_action` refuses before dispatch; `a_themeset` refuses again inside the handler. Fault
# injection proved the gap: removing `themeset` from RESEARCH_FORBIDDEN_ACTIONS left the whole
# suite green, because the handler caught it. That is defence in depth working, and it is also a
# check that cannot see half of what it claims to cover. So the outer layer is asserted
# structurally as well as behaviourally.
check("themeset" in RESEARCH_FORBIDDEN_ACTIONS,
      "the pre-dispatch gate lists themeset, so the refusal does not rest on the handler alone",
      str(sorted(RESEARCH_FORBIDDEN_ACTIONS)))
check("themeget" not in RESEARCH_FORBIDDEN_ACTIONS,
      "and themeget is NOT gated: a participant may ask what it renders")

before = 0
with Session() as s:
    before = len(s.scalars(select(AuditEvent).where(
        AuditEvent.event_type == "theme_change_denied")).all())

refused = post({"action": "themeset", "session_token": res_tok, "theme": "plain"})
check(refused.get("ok") is False,
      "a research account posting themeset directly is refused", str(refused)[:140])
check("fixed" in (refused.get("error") or "").lower(),
      "and the reason says the theme is fixed for this account", str(refused.get("error"))[:90])
with Session() as s:
    after = len(s.scalars(select(AuditEvent).where(
        AuditEvent.event_type == "theme_change_denied")).all())
    stored_after = s.execute(sa.text("SELECT theme FROM participants WHERE participant_id = :p"),
                             {"p": res_id}).scalar()
check(after > before, "the refusal is audited", f"{before} then {after}")
check(stored_after == OTHER, "and nothing was written", str(stored_after))

# THE INNER LAYER, PROVEN INDEPENDENTLY. Everything above goes through /exec, where the gate
# refuses first, so those checks stay green even with the handler's own guard deleted: fault
# injection showed exactly that. Calling the handler directly is the only way to reach it with
# the gate bypassed, and it is worth reaching, because "an upstream gate will catch it" is how a
# handler comes to be relied on after the gate is refactored away.
from app.theme import a_themeset  # noqa: E402
import os  # noqa: E402
_secret = os.environ.get("SESSION_SECRET", "")
with Session() as s:
    direct = a_themeset(s, {"session_token": res_tok, "theme": "plain"}, _secret, 28800)
check(direct.get("ok") is False,
      "the handler itself refuses a research account, with the pre-dispatch gate bypassed",
      str(direct)[:130])

ok_set = post({"action": "themeset", "session_token": ops_tok, "theme": "plain"})
check(ok_set.get("ok") is True, "an operational account may choose", str(ok_set)[:120])
check(post({"action": "themeget", "session_token": ops_tok}).get("theme") == "plain",
      "and the choice persists against the account")

bad = post({"action": "themeset", "session_token": ops_tok, "theme": "chartreuse"})
check(bad.get("ok") is False, "an unknown theme is refused", str(bad)[:110])
check(post({"action": "themeget", "session_token": ops_tok}).get("theme") == "plain",
      "and the previous choice survives the refusal")

check(set(THEMES) == {"plain", "light", "newyork", "maria"},
      "the server's vocabulary is the four themes the interface offers", str(THEMES))
check("dark" not in THEMES,
      "and the archived theme is not storable")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
