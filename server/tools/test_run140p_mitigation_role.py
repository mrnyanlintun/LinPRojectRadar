#!/usr/bin/env python3
"""
Run 140 P: THE `mitigation` ROLE IS A SETTING, RESOLVED THE SAME WAY EVERY OTHER ROLE IS.

WHAT IS REAL AND WHAT IS HARNESS, SAID FIRST AND PLAINLY.

There is NO provider key of any kind in this verification environment -- not ANTHROPIC_API_KEY,
not OPENAI_API_KEY, not GROQ_API_KEY. NOTHING IN THIS FILE CALLS A MODEL, and nothing here
simulates one having been called. Every check measures the PLATFORM'S OWN CODE: which
configuration `load_provider` resolves under a given environment, and which request body the
boundary builds. `claude-opus-5` is proved to be what the platform RESOLVES for the mitigation
call site; whether Anthropic's catalogue answers to that identifier is UNVERIFIED here and is
provable only on the owner's deployment, with the command `ai_provider.py` documents.

What is proved, BY EXECUTING THE RESOLVER rather than by reading the table:

  1. THE FOUR RUNGS, EACH ONE SEPARATELY.
       nothing set                             -> anthropic / claude-opus-5   (rung 3, in code)
       AI_PROVIDER set, role variable unset    -> the account variable wins over the code
       AI_MITIGATION_PROVIDER set              -> the role variable wins over the code
       both set                                -> the ROLE variable wins over the account one
       AI_MITIGATION_MODEL set                 -> the model identifier is re-pointable alone
  2. THE OTHER FOUR ROLES ARE BYTE-IDENTICAL BEFORE AND AFTER. The PRE-CHANGE ai_provider.py is
     recovered from git (Run 140's base commit), loaded as a SECOND, INDEPENDENT MODULE, and its
     resolver is EXECUTED across the same matrix of environments as the current one. Every field
     of every resolved ProviderConfig -- provider, wire, model, url, key_env, attribution -- is
     compared for extraction, spec, narration and recognition. This is the check the owner cares
     most about: the run added a call site and moved nothing.
  3. THE TABLE'S OWN INVARIANTS STILL HOLD. `mitigation` is in ROLES; every provider carries a
     mitigation model, so no deliberate `AI_MITIGATION_PROVIDER=groq` can KeyError; the two
     asserts guarding ROLE_DEFAULT_PROVIDERS are re-executed; `spec` is still groq (Run 130) and
     DEFAULT_PROVIDER is still "anthropic", neither touched by this run.
  4. NO `temperature` IS SENT FOR THIS ROLE. Measured on the real AnthropicClient against a
     captured transport: the body it posts for a mitigation config carries no "temperature" key
     when no caller supplies one. Run 128 established that claude-sonnet-5 rejects the parameter
     with a 400; the record-and-replay design carries the determinism instead, so the mitigation
     caller passes none and the boundary attaches none.
  5. /exec HEALTH REPORTS THE NEW CALL SITE, key presence only, never a key value.

Run (from server/):  python tools/test_run140p_mitigation_role.py
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import ai_provider as ap

REPO = pathlib.Path(__file__).resolve().parents[2]

#: The commit Run 140 branched from. The "before" side of check 2 is this file's bytes at that
#: commit -- not a transcription of them, and not this run's memory of them.
BASE_COMMIT = "ae6734e"
SOURCE_REL = "server/app/ai_provider.py"

#: The four roles that existed before this run. The run adds a fifth and moves none of these.
PRIOR_ROLES = ("extraction", "spec", "narration", "recognition")

#: Every environment the resolver is executed under. Chosen to exercise both rungs of the
#: environment, each role variable separately, and the two-variables-at-once precedence case.
CONDITIONS: dict[str, dict[str, str]] = {
    "nothing set": {},
    "AI_PROVIDER=groq": {"AI_PROVIDER": "groq"},
    "AI_PROVIDER=openai": {"AI_PROVIDER": "openai"},
    "AI_PROVIDER=anthropic": {"AI_PROVIDER": "anthropic"},
    "AI_EXTRACTION_PROVIDER=groq": {"AI_EXTRACTION_PROVIDER": "groq"},
    "AI_SPEC_PROVIDER=anthropic": {"AI_SPEC_PROVIDER": "anthropic"},
    "AI_NARRATION_PROVIDER=openai": {"AI_NARRATION_PROVIDER": "openai"},
    "AI_RECOGNITION_PROVIDER=groq": {"AI_RECOGNITION_PROVIDER": "groq"},
    "AI_PROVIDER=groq + AI_SPEC_PROVIDER=openai": {
        "AI_PROVIDER": "groq", "AI_SPEC_PROVIDER": "openai"},
    # The mitigation variables must not disturb the four prior roles either.
    "AI_MITIGATION_PROVIDER=groq": {"AI_MITIGATION_PROVIDER": "groq"},
    "AI_MITIGATION_MODEL=x": {"AI_MITIGATION_MODEL": "x"},
}

FAILURES: list[str] = []
CHECKS = 0


def check(label: str, got, want) -> None:
    global CHECKS
    CHECKS += 1
    ok = got == want
    if not ok:
        FAILURES.append(label)
    print(f"  [{'ok' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"        got  {got!r}\n        want {want!r}")


def fields(cfg) -> dict[str, str]:
    """Every field of a resolved configuration. Nothing is excluded from the comparison."""
    return {"provider": cfg.provider, "wire": cfg.wire, "model": cfg.model, "url": cfg.url,
            "key_env": cfg.key_env, "attribution": cfg.attribution}


def resolve_matrix(module, roles) -> dict:
    """EXECUTE the resolver -- this module's own `load_provider` -- over the whole matrix."""
    return {name: {role: fields(module.load_provider(role, environ=env)) for role in roles}
            for name, env in CONDITIONS.items()}


def load_pre_change_module():
    """
    The PRE-CHANGE ai_provider.py, recovered from git and loaded as its own module object.

    Returns None (and says so) if git cannot produce the base commit's copy, so the report can
    say the comparison was not made rather than quietly reporting one that never ran.
    """
    try:
        blob = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{BASE_COMMIT}:{SOURCE_REL}"],
            capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"  [!!] cannot recover {SOURCE_REL} at {BASE_COMMIT}: {exc}")
        return None
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="run140p_")) / "ai_provider_before.py"
    tmp.write_bytes(blob)
    spec = importlib.util.spec_from_file_location("run140p_ai_provider_before", tmp)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module   # @dataclass resolves annotations through sys.modules
    spec.loader.exec_module(module)   # its two asserts run here too, on the old table
    return module


class CapturedTransport:
    """
    Stands in for `_Client._request`. Records the body and headers the boundary BUILT and
    returns a fixed, obviously-synthetic payload. It is not a model and no result taken through
    it may be reported as one.
    """

    def __init__(self) -> None:
        self.body: dict | None = None
        self.headers: dict | None = None

    def install(self, client):
        def _request(body, headers):
            self.body, self.headers = body, headers
            return {"content": [{"type": "text", "text": "captured"}], "stop_reason": "end_turn"}
        client._request = _request   # noqa: SLF001 -- the point of the harness
        return client


def main() -> int:
    print(__doc__.strip().splitlines()[0])

    # ---------------------------------------------------------------- 1. the four rungs
    print("\n1. THE RESOLUTION CHAIN FOR `mitigation`, EACH RUNG EXECUTED")

    got = fields(ap.load_provider("mitigation", environ={}))
    check("nothing set -> provider is anthropic", got["provider"], "anthropic")
    check("nothing set -> model is the Opus identifier", got["model"], "claude-opus-5")
    check("nothing set -> attribution stamped on a record",
          got["attribution"], "anthropic/claude-opus-5")
    check("nothing set -> anthropic wire and endpoint",
          (got["wire"], got["url"]), ("anthropic", "https://api.anthropic.com/v1/messages"))
    check("nothing set -> key variable named, never its value",
          got["key_env"], "ANTHROPIC_API_KEY")

    acct = ap.load_provider("mitigation", environ={"AI_PROVIDER": "groq"})
    check("AI_PROVIDER=groq (role variable unset) beats the code default",
          (acct.provider, acct.model), ("groq", "openai/gpt-oss-120b"))

    role = ap.load_provider("mitigation", environ={"AI_MITIGATION_PROVIDER": "openai"})
    check("AI_MITIGATION_PROVIDER=openai beats the code default",
          (role.provider, role.model), ("openai", "gpt-4o"))

    both = ap.load_provider("mitigation", environ={
        "AI_PROVIDER": "groq", "AI_MITIGATION_PROVIDER": "openai"})
    check("AI_MITIGATION_PROVIDER beats AI_PROVIDER when both are set",
          (both.provider, both.model), ("openai", "gpt-4o"))

    remo = ap.load_provider("mitigation", environ={"AI_MITIGATION_MODEL": "claude-opus-9-test"})
    check("AI_MITIGATION_MODEL re-points the identifier alone, provider unchanged",
          (remo.provider, remo.model), ("anthropic", "claude-opus-9-test"))

    # ---------------------------------------------------------------- 2. the other four roles
    print("\n2. THE OTHER FOUR ROLES, BEFORE AND AFTER, RESOLVER EXECUTED ON BOTH")
    before_mod = load_pre_change_module()
    check("the pre-change ai_provider.py was recovered and imported",
          before_mod is not None, True)
    if before_mod is not None:
        check("the recovered module is the PRE-change one (no mitigation role)",
              "mitigation" in before_mod.ROLES, False)
        before = resolve_matrix(before_mod, PRIOR_ROLES)
        after = resolve_matrix(ap, PRIOR_ROLES)
        check("every prior role resolves byte-identically across every condition",
              json.dumps(after, sort_keys=True), json.dumps(before, sort_keys=True))
        for r in PRIOR_ROLES:
            check(f"  role {r}: identical across all {len(CONDITIONS)} conditions",
                  json.dumps({k: v[r] for k, v in after.items()}, sort_keys=True),
                  json.dumps({k: v[r] for k, v in before.items()}, sort_keys=True))
        check("the model string of every prior role, per provider, is unmoved",
              {p: {r: ap.PROVIDERS[p]["models"][r] for r in PRIOR_ROLES} for p in ap.PROVIDERS},
              {p: {r: before_mod.PROVIDERS[p]["models"][r] for r in PRIOR_ROLES}
               for p in before_mod.PROVIDERS})
        check("the only new model key, per provider, is `mitigation`",
              {p: sorted(set(ap.PROVIDERS[p]["models"]) - set(before_mod.PROVIDERS[p]["models"]))
               for p in ap.PROVIDERS},
              {p: ["mitigation"] for p in ap.PROVIDERS})

    # ---------------------------------------------------------------- 3. table invariants
    print("\n3. THE TABLE'S INVARIANTS, RE-EXECUTED")
    check("`mitigation` is a declared call site", "mitigation" in ap.ROLES, True)
    check("ROLES gained exactly one name",
          list(ap.ROLES), ["extraction", "spec", "narration", "recognition", "mitigation"])
    check("every provider carries a mitigation model (no KeyError on a deliberate switch)",
          sorted(p for p in ap.PROVIDERS if "mitigation" in ap.PROVIDERS[p]["models"]),
          sorted(ap.PROVIDERS))
    check("role defaults name only real call sites (assert re-run)",
          set(ap.ROLE_DEFAULT_PROVIDERS) <= set(ap.ROLES), True)
    check("role defaults name only known providers (assert re-run)",
          set(ap.ROLE_DEFAULT_PROVIDERS.values()) <= set(ap.PROVIDERS), True)
    check("`mitigation` is named explicitly in the code default table",
          ap.ROLE_DEFAULT_PROVIDERS.get("mitigation"), "anthropic")
    check("`spec` is still groq -- Run 130 untouched",
          ap.ROLE_DEFAULT_PROVIDERS.get("spec"), "groq")
    check("DEFAULT_PROVIDER is unmoved", ap.DEFAULT_PROVIDER, "anthropic")
    check("an unknown provider for this role still refuses loudly",
          _refusal("mitigation", {"AI_MITIGATION_PROVIDER": "opus"}), True)

    # ---------------------------------------------------------------- 4. temperature
    print("\n4. NO `temperature` IS ATTACHED FOR THIS ROLE")
    cap = CapturedTransport()
    client = cap.install(ap.AnthropicClient(ap.load_provider("mitigation", environ={}),
                                            "not-a-key", 5.0))
    client.complete([{"type": "text", "text": "compose a mitigation"}], max_tokens=256)
    check("the body the boundary built has NO temperature key",
          "temperature" in (cap.body or {}), False)
    check("the body names the resolved Opus identifier",
          (cap.body or {}).get("model"), "claude-opus-5")
    cap2 = CapturedTransport()
    c2 = cap2.install(ap.AnthropicClient(ap.load_provider("mitigation", environ={}),
                                         "not-a-key", 5.0))
    c2.complete([{"type": "text", "text": "x"}], max_tokens=8, temperature=0.0)
    check("the omission is the CALLER's, not the boundary's: a supplied temperature IS attached",
          (cap2.body or {}).get("temperature"), 0.0)

    # ---------------------------------------------------------------- 5. health
    print("\n5. /exec HEALTH NAMES THE NEW CALL SITE, PRESENCE ONLY")
    diag = ap.provider_diagnostics(environ={})
    check("diagnostics carry a mitigation entry", "mitigation" in diag["roles"], True)
    check("it reports the resolved provider and model",
          (diag["roles"]["mitigation"].get("provider"), diag["roles"]["mitigation"].get("model")),
          ("anthropic", "claude-opus-5"))
    check("it reports key PRESENCE, a bool, never a key",
          diag["roles"]["mitigation"]["keyPresent"], False)
    check("no diagnostics field holds anything but the key's variable NAME",
          diag["roles"]["mitigation"]["keyEnv"], "ANTHROPIC_API_KEY")

    passed = CHECKS - len(FAILURES)
    print(f"\nRESULT: {passed}/{CHECKS} checks passed")
    if FAILURES:
        print("FAILURES: " + "; ".join(FAILURES))
    return 1 if FAILURES else 0


def _refusal(role: str, env: dict[str, str]) -> bool:
    try:
        ap.load_provider(role, environ=env)
    except ap.ProviderConfigError:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
