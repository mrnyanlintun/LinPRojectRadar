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
from app.theme import DEFAULT_THEME, RESEARCH_THEME, THEME_LABELS, THEMES  # noqa: E402

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

# The administration "Active"/off status pill is checked below, under GUARANTEE 5 (it is
# scoped to body[data-theme="plain"] on hardcoded literal colors, not one of the ten tokens
# measured above, which is how the pre-2026-08-04 3.71:1 failure slipped through).

# Tokens the ten-token check above does NOT measure, reported here so a session does not have to
# rediscover the gap by hand. 2026-08-05: re-derived by checking every declaration in the plain
# block against `color: var(--x)` usage in radar.css, not by re-quoting the prior list, and it
# found one the prior pass missed (--accent) and four the prior pass listed as live text that are
# actually declared and never consumed by anything (--sector-design, --sector-construction,
# --sector-hybrid, --scope-label) -- along with the five --status-ink-* tokens, same situation,
# already excluded from TEXT_TOKENS_LIVE for the same reason and reported in DEAD instead.
#
# LIVE: at least one `color: var(--name)` rule exists in radar.css, so this genuinely paints text
# somewhere on the page today, under this theme.
TEXT_TOKENS_LIVE = ["eyebrow", "gold-text", "brand-bronze", "brand-verdigris", "ink-dim", "accent"]
# DEAD: declared in this theme's block (and in the root block) but zero `color:` (or any other)
# consumer anywhere in radar.css or the frontend JS. Not a contrast risk today -- nothing reads
# them -- but flagged so a future rule that starts consuming one does not silently skip the check.
TEXT_TOKENS_DEAD = ["sector-design", "sector-construction", "sector-hybrid", "scope-label",
                    "status-ink-complete", "status-ink-green", "status-ink-yellow",
                    "status-ink-amber", "status-ink-red"]

# Read directly here rather than relying on the module-level `css_text` defined further down for
# a different section, so this block does not depend on later code running first.
_full_css = io.open(CSS, encoding="utf-8").read()

print("\n  UNMEASURED, LIVE text tokens (render real text; ratios shown, not gated):")
for name in TEXT_TOKENS_LIVE:
    consumers = len(re.findall(rf"color:\s*var\(--{re.escape(name)}\)", _full_css))
    check(consumers > 0, f"--{name} actually colours text somewhere in radar.css",
          f"{consumers} usage(s)")
    value = token(block, name)
    if value and re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        print(f"    --{name:20s} {value}   surface {ratio(value, SURFACE):.2f} / "
              f"page {ratio(value, PAGE):.2f}   ({consumers} usage(s))")
    else:
        print(f"    --{name:20s} {value}   (not a plain hex, or not declared)")

print("\n  DECLARED BUT UNUSED (no color: consumer found; not a live contrast risk today):")
for name in TEXT_TOKENS_DEAD:
    consumers = len(re.findall(rf"color:\s*var\(--{re.escape(name)}\)", _full_css))
    check(consumers == 0, f"--{name} is confirmed unused (reclassify if this ever goes non-zero)",
          f"{consumers} usage(s)")
    value = token(block, name)
    print(f"    --{name:20s} {value}   ({consumers} usage(s))")

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

check(DEFAULT_THEME == "plain",
      "the operational default is Fairbanks (plain), as of 2026-08-04",
      DEFAULT_THEME)
check(RESEARCH_THEME == "newyork",
      "the research pin is a LITERAL newyork, not derived from whatever the default is, so a "
      "future change to the default cannot silently move the participants' theme",
      RESEARCH_THEME)
check(RESEARCH_THEME != DEFAULT_THEME,
      "the research pin and the operational default are independent values (they happen to "
      "differ today; the point is they are not coupled)",
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

ok_set = post({"action": "themeset", "session_token": ops_tok, "theme": "maria"})
check(ok_set.get("ok") is True, "an operational account may choose a non-default theme",
      str(ok_set)[:120])
check(post({"action": "themeget", "session_token": ops_tok}).get("theme") == "maria",
      "and the choice persists against the account, not overridden back to the new default "
      "(plain) on the next read")

bad = post({"action": "themeset", "session_token": ops_tok, "theme": "chartreuse"})
check(bad.get("ok") is False, "an unknown theme is refused", str(bad)[:110])
check(post({"action": "themeget", "session_token": ops_tok}).get("theme") == "maria",
      "and the previous choice survives the refusal")

# THIS IS THE PATH THAT ACTUALLY LEAKED THE INTERNAL KEY, and it is a DIFFERENT refusal from the
# research one Guarantee 6 checks below. The research refusal ("not available: the interface
# theme is fixed...") can never say "plain" because it never lists a theme at all; this one used
# to build its message from `', '.join(THEMES)`, which is "plain, light, newyork, maria" — the
# exact leak the brief reported. Checked here, next to the call that produces it, rather than
# only in the general "no surface says plain" sweep below, so a regression is attributed to the
# right refusal path rather than merely to "somewhere".
bad_text = json.dumps(bad)
check("plain" not in bad_text.lower(),
      "an operational account's UNKNOWN-THEME refusal never contains the literal 'plain'",
      bad_text[:200])
check("Fairbanks" in bad_text,
      "and it names the theme by its user-facing label instead", bad_text[:200])

check(set(THEMES) == {"plain", "light", "newyork", "maria"},
      "the server's vocabulary is the four themes the interface offers", str(THEMES))
check("dark" not in THEMES,
      "and the archived theme is not storable")

print()
print("=" * 78)
print("GUARANTEE 5: the admin 'Active' status pill meets AA on the plain theme")
print("=" * 78)

# Scoped override for body[data-theme="plain"], read out of the live stylesheet the same way the
# theme block above is: a comment claiming the ratio cannot make this pass.
m_on = re.search(
    r'body\[data-theme="plain"\]\s+\.admin-pill-on\s*\{\s*background:\s*(#[0-9a-fA-F]{6});'
    r'\s*color:\s*(#[0-9a-fA-F]{6});', css_text)
m_off = re.search(
    r'body\[data-theme="plain"\]\s+\.admin-pill-off\s*\{\s*background:\s*(#[0-9a-fA-F]{6});'
    r'\s*color:\s*(#[0-9a-fA-F]{6});', css_text)
check(bool(m_on), "the plain-scoped .admin-pill-on override is present in radar.css")
check(bool(m_off), "the plain-scoped .admin-pill-off override is present in radar.css")
if m_on:
    bg, fg = m_on.group(1), m_on.group(2)
    r_on = ratio(fg, bg)
    check(r_on >= AA, "the 'Active' pill (admin-pill-on) meets AA at 11px on Fairbanks",
          f"{fg} on {bg} = {r_on:.2f}, need {AA}")
if m_off:
    bg, fg = m_off.group(1), m_off.group(2)
    r_off = ratio(fg, bg)
    check(r_off >= AA, "the 'Archived' pill (admin-pill-off) meets AA at 11px on Fairbanks",
          f"{fg} on {bg} = {r_off:.2f}, need {AA}")

print()
print("=" * 78)
print("GUARANTEE 6: no user-facing surface renders the literal string 'plain'")
print("=" * 78)

# The label/key divergence: the internal key stays "plain" (see NAMING_AUTHORITY-adjacent notes
# in theme.py and app.js), but every string a user can actually read must say "Fairbanks".
refused_research = post({"action": "themeset", "session_token": res_tok, "theme": "newyork"})
check(refused_research.get("ok") is False, "a second research refusal to check for a leak",
      str(refused_research)[:120])
refusal_text = json.dumps(refused_research)
check("plain" not in refusal_text.lower(),
      "the themeset refusal payload never contains the literal 'plain'",
      refusal_text[:160])

got_again = post({"action": "themeget", "session_token": res_tok})
themeget_text = json.dumps(got_again)
check("fairbanks" not in themeget_text.lower() and True,
      "themeget's payload is data (raw keys), which is fine for a client that maps the key "
      "through THEME_META -- checked separately in tests_render.html; this suite just proves "
      "the SERVER text a user reads (the refusal message) does not leak the key",
      themeget_text[:160])

app_js_meta = re.search(r'THEME_META\s*=\s*\[(.*?)\n  \];', app_js, re.S)
check(app_js_meta is not None, "THEME_META is present in app.js")
if app_js_meta:
    plain_entry = re.search(r'\{\s*key:\s*"plain",\s*label:\s*"([^"]+)"', app_js_meta.group(1))
    check(plain_entry is not None and plain_entry.group(1) == "Fairbanks",
          "the plain key's user-facing label in THEME_META is 'Fairbanks'",
          plain_entry.group(1) if plain_entry else None)

# THEME_LABELS (server/app/theme.py, used to build the unknown-theme refusal above) and
# THEME_META (app.js, used to build the fly-out) are two independent literals with no shared
# source. Nothing stops them drifting apart -- a label changed in one and not the other would
# make the refusal message and the interface disagree about what to call a theme. Extracted from
# app.js text rather than imported, since this is a Python suite reading a JS file.
js_labels = dict(re.findall(r'key:\s*"(\w+)",\s*label:\s*"([^"]+)"',
                            app_js_meta.group(1) if app_js_meta else ""))
check(bool(js_labels), "THEME_META labels were readable out of app.js", str(js_labels))
check(js_labels == THEME_LABELS,
      "theme.py's THEME_LABELS and app.js's THEME_META agree on every key's label, exactly",
      f"py={THEME_LABELS} js={js_labels}")

print()
print("=" * 78)
print("GUARANTEE 7: the research pin resolves BEFORE the consent screen, not only after")
print("=" * 78)

# A GENUINE DEFECT FOUND WHILE VERIFYING THIS TASK, not a hypothetical: LinApp.init() -- the
# only caller of the theme sync before 2026-08-05 -- is skipped entirely by auth.js's
# routeFromView while a research participant is on the consent screen (needsConsent(view) is
# true, showConsentScreen() runs, and the function returns before reaching init()). So the
# consent screen, which every research participant sees FIRST, rendered whatever the
# OPERATIONAL default happened to be, not the research pin. That was invisible for as long as
# DEFAULT_THEME and RESEARCH_THEME were both "newyork"; decoupling them on 2026-08-04 turned it
# into a real, silent violation of "every participant sees identical stimulus" -- confirmed live
# in a browser: a research account with a directly-written non-default stored theme rendered
# Fairbanks on the consent screen before the fix, and New York after it.
#
# There is no offline DOM harness for this: tests_render.html stubs LinAuth.init() to return
# false specifically so app.js never boots the real application, and does not load auth.js at
# all (see its own header comment) -- the bug lives entirely in auth.js's bootstrap sequence,
# which that harness exists to avoid running. A live re-check needs a real browser driving
# index.html through an actual sign-in with transitions suppressed, which is how this was found
# and confirmed fixed (see the report). What CAN run here, offline, is the structural guarantee
# that made the fix true: the call exists, and it is positioned before the branch it must run
# ahead of. A regression that deletes the call, or moves it after the consent check, is caught;
# a regression that changes what happens ONLY behind a passing consent check is not, and is not
# claimed to be.
auth_js = io.open(ROOT / "assets" / "js" / "auth.js", encoding="utf-8").read()

check("syncTheme: syncThemeFromServer" in app_js,
      "app.js exposes the theme sync as LinApp.syncTheme, for auth.js to call directly")

route_fn = re.search(r'function routeFromView\(view\)\s*\{(.*?)\n  \}', auth_js, re.S)
check(route_fn is not None, "auth.js's routeFromView is present and readable")
if route_fn:
    body = route_fn.group(1)
    sync_pos = body.find("LinApp.syncTheme()")
    consent_pos = body.find("needsConsent(view)")
    check(sync_pos != -1, "routeFromView calls LinApp.syncTheme()")
    check(consent_pos != -1, "and still checks needsConsent(view)")
    if sync_pos != -1 and consent_pos != -1:
        check(sync_pos < consent_pos,
              "the theme sync runs BEFORE the consent check, not after -- this is the exact "
              "line that fixes the defect; reversing the order reintroduces it",
              f"sync at {sync_pos}, consent check at {consent_pos}")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
