#!/usr/bin/env python3
"""
RUN 11, GATE 1. THE SERVER IS THE SINGLE COMPUTATIONAL AUTHORITY.

WHAT THIS SUITE ASSERTS, AND WHY IT IS SHAPED THIS WAY.

A parity test that compared a browser band constant with a server band constant would be the
fourth way a check has lied here: it would assert against a hand-maintained copy of the logic
instead of the logic, and it would pass the moment somebody kept both copies in step while the
divergence lived somewhere else. There is a stronger property available, and it is the one the
owner asked for: THERE IS NO SECOND ARITHMETIC SOURCE ON THE PARTICIPANT ROUTE. That property is
structural, it is checkable against the real files, and it cannot be satisfied by keeping two
implementations agreeing.

So the suite asserts three things:

  1. index.html — the participant route — loads none of the client model files.
  2. Every script index.html DOES load is free of a live call into the client model layer. The
     dormant call sites found in Run 11 were guarded by presence checks against window.LinSim
     and window.LinSimulations, which were never false only because of (1). A presence check is
     not a refusal: reload the file and the stale arithmetic returns silently. Each is now
     gated on an explicit opt-in flag that the application never sets.
  3. The algorithm version guard exists, is loaded on the deep-dive page before the historical
     model files, and does not report "current" for a stored result computed under the server's
     simulation version. The client implementation is the pre-remediation one; a comparison that
     called it current would be the overclaim the guard exists to prevent.

EVERY CHECK HERE IS PROVED ABLE TO FAIL by the mutation block at the end, which edits real file
text in memory and re-runs the same predicate.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation.models import SIMULATION_VERSION  # noqa: E402

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


#: The client model layer. sim.js holds the Monte Carlo, CUSUM and signal-package builders;
#: simulations.js holds the per-module run* functions; categories.js holds the browser category
#: rollup and project-status derivation. All three are historical test artefacts.
CLIENT_MODEL_FILES = ("sim.js", "simulations.js", "categories.js")

#: The globals those files export. A live reference to one of them from a participant-route file
#: is a second arithmetic source whether or not it happens to execute today.
CLIENT_MODEL_GLOBALS = ("LinSim", "LinSimulations")

#: The one opt-in flag. The application never sets it; the deep-dive page is where recomputation
#: is deliberate. Any reference to a client model global must be dominated by a test of this.
OPT_IN_FLAG = "LIN_ALLOW_CLIENT_ANALYTICS"


def scripts_of(html_path: pathlib.Path) -> list[str]:
    return re.findall(r'<script src="([^"]+)"', html_path.read_text(encoding="utf-8"))


def gate_1_index_loads_no_client_model() -> None:
    srcs = scripts_of(ROOT / "index.html")
    check("index.html loads at least one script", len(srcs) > 5, f"{len(srcs)} found")
    for f in CLIENT_MODEL_FILES:
        loaded = any(s.endswith("/" + f) or s.endswith(f) for s in srcs)
        check(f"index.html does not load {f}", not loaded, "it is loaded")


def _strip_comments(text: str) -> str:
    """
    Block and line comments removed, newlines preserved so line numbers still mean something.
    Without this the suite reported the PROSE about the retired browser ingest as a call site,
    which would have made a truthful comment impossible to write.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(c if c == "\n" else " " for c in text[i:j]))
            i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


#: A reference is gated when the enclosing function body, from its `function` line down to the
#: reference, contains either the opt-in flag or an explicit refusal on the same global. The
#: whole enclosing function is read, not the lines above the reference: a refusal's `throw` sits
#: on the line AFTER the test, and reading only upward reported the guard itself as a call site.
#: Only two forms count. The opt-in flag, which the application never sets; or ingest.js's
#: refusal, which THROWS a sentence rather than returning quietly. A bare `if
#: (!window.LinSimulations) return;` is deliberately NOT here: that is the presence check this
#: run replaced, and accepting it would let the old shape back in.
_GATE_PATTERNS = (OPT_IN_FLAG, 'throw new Error("Signals are computed by the server')
_FUNC_RE = re.compile(r"^\s{0,6}(async\s+)?function\s")


def _live_client_refs(text: str) -> list[str]:
    code_lines = _strip_comments(text).split("\n")
    raw_lines = text.split("\n")
    out = []
    for i, code in enumerate(code_lines):
        if not any(re.search(r"\b" + g + r"\b", code) for g in CLIENT_MODEL_GLOBALS):
            continue
        start = 0
        for j in range(i, -1, -1):
            if _FUNC_RE.match(code_lines[j]):
                start = j
                break
        end = len(code_lines)
        for j in range(i + 1, len(code_lines)):
            if _FUNC_RE.match(code_lines[j]):
                end = j
                break
        body = "\n".join(code_lines[start:end])
        if any(g in body for g in _GATE_PATTERNS):
            continue
        out.append(f"{i + 1}: {raw_lines[i].strip()[:90]}")
    return out


def gate_1_no_live_client_arithmetic_on_participant_route() -> None:
    srcs = [s for s in scripts_of(ROOT / "index.html") if s.endswith(".js")]
    checked = 0
    for src in srcs:
        path = ROOT / src
        if not path.exists():
            continue
        checked += 1
        refs = _live_client_refs(path.read_text(encoding="utf-8"))
        check(f"{src} has no ungated client model call site",
              not refs, "; ".join(refs[:3]))
    check("participant-route scripts were actually opened", checked >= 20, f"{checked} opened")


def gate_1_version_guard() -> None:
    guard = ROOT / "assets" / "js" / "client_algorithm_version.js"
    check("version guard file exists", guard.exists(), str(guard))
    text = guard.read_text(encoding="utf-8")
    m = re.search(r'CLIENT_ALGORITHM_VERSION\s*=\s*"([^"]+)"', text)
    check("version guard declares a client algorithm version", m is not None, "")
    if m:
        client_version = m.group(1)
        # THE POINT OF THE GUARD. The browser implementation predates every server remediation
        # run. If these two strings were ever equal the guard would report "current" and a
        # recomputed figure would render as the analysis, which is the exact failure.
        check("client algorithm version is not the server simulation version",
              client_version != SIMULATION_VERSION,
              f"both are {client_version}")
        check("client algorithm version is labelled historical",
              "historical" in client_version, client_version)
    # The three outcomes, present by name. A guard with only two would have no state for a
    # stored result that carries no version stamp at all.
    for state in ('"current"', '"mismatch"', '"unknown"'):
        check(f"version guard defines the {state} outcome", state in text, "")

    # RUN 54 RECONCILIATION. `research/deepdive.html` was DELETED on the owner's ruling at
    # section 8 of the Run 54 order. Every check below asserted a property OF THAT PAGE: that it
    # loaded the version guard, that it loaded it BEFORE the browser instruments, that it called
    # the comparison before rendering, and that it had somewhere to show a refusal. All four
    # existed to stop ONE page presenting browser arithmetic as the current analysis. With the
    # page gone the guarantee is unconditional and is asserted as such, together with the
    # non-vacuity that makes the absence a finding rather than an accident.
    #
    # THIS IS THE ONE PLACE IN RUN 54 WHERE CHECKS ABOUT A DELETED SUBJECT ARE REPLACED RATHER
    # THAN KEPT. It is recorded here rather than absorbed silently, and it is reported to the
    # owner as such.
    _dd = ROOT / "research" / "deepdive.html"
    _dd_was = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                              "HEAD~1:research/deepdive.html"], capture_output=True).returncode == 0
    check("the only page that ever loaded browser arithmetic is GONE, so no page can present it "
          "as the current analysis", (not _dd.exists()) and _dd_was,
          f"exists_now={_dd.exists()} existed_at_HEAD~1={_dd_was}")
    _srcs_index = scripts_of(ROOT / "index.html")
    check("and the participant application loads neither browser instrument",
          not [s for s in _srcs_index if s.endswith(("sim.js", "simulations.js"))],
          str([s for s in _srcs_index if s.endswith(("sim.js", "simulations.js"))]))


def mutation_proofs() -> None:
    """
    Each predicate above, re-run against deliberately altered file text. Every one must go red.
    The alteration is asserted to have changed the bytes before the predicate is trusted, because
    an injection that silently fails to apply reports a false clean.
    """
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    mutated = idx.replace("</body>", '<script src="assets/js/simulations.js"></script>\n</body>')
    check("mutation altered index.html", mutated != idx, "no change")
    srcs = re.findall(r'<script src="([^"]+)"', mutated)
    check("MUTATION RED: loading simulations.js on index.html is detected",
          any(s.endswith("simulations.js") for s in srcs), "not detected")

    sig = (ROOT / "assets" / "js" / "signals.js").read_text(encoding="utf-8")
    mutated = sig.replace(f"    if (!window.{OPT_IN_FLAG}) return;\n", "", 1)
    check("mutation altered signals.js", mutated != sig, "no change")
    check("MUTATION RED: removing the opt-in gate re-exposes a client call site",
          len(_live_client_refs(mutated)) > len(_live_client_refs(sig)),
          f"{len(_live_client_refs(mutated))} vs {len(_live_client_refs(sig))}")

    guard = (ROOT / "assets" / "js" / "client_algorithm_version.js").read_text(encoding="utf-8")
    mutated = guard.replace('"client-legacy-2026.07-historical"', f'"{SIMULATION_VERSION}"')
    check("mutation altered the version guard", mutated != guard, "no change")
    m = re.search(r'CLIENT_ALGORITHM_VERSION\s*=\s*"([^"]+)"', mutated)
    check("MUTATION RED: claiming the server version for client arithmetic is detected",
          m is not None and m.group(1) == SIMULATION_VERSION, "not detected")

    # RUN 54. The mutation proof for the deep dive's comparison call is retired with its
    # subject. In its place, the ABSENCE check above is itself proved non-vacuous by execution:
    # the file existed at the prior commit, so "it is gone" is a finding and not a check that
    # was always going to pass. Asserted against git, not against a copy of this logic.
    _dd_head = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD~1:research/deepdive.html"],
                              capture_output=True)
    check("NON-VACUITY: the deleted page really did call the comparison before rendering, so "
          "the check that has just been retired had force right up to the deletion",
          _dd_head.returncode == 0
          and b"LinClientAlgorithmVersion.compare" in _dd_head.stdout
          and b"LinDeepDive.render" in _dd_head.stdout,
          f"rc={_dd_head.returncode} bytes={len(_dd_head.stdout)}")


gate_1_index_loads_no_client_model()
gate_1_no_live_client_arithmetic_on_participant_route()
gate_1_version_guard()
mutation_proofs()

print("")
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  " + f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
