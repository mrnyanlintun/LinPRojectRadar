#!/usr/bin/env python3
"""
Run 93: THE MODEL IS A SETTING, NOT A CONSTANT.

WHAT IS REAL AND WHAT IS HARNESS, SAID FIRST AND PLAINLY.

There is NO provider key of any kind in this verification environment -- not ANTHROPIC_API_KEY,
not OPENAI_API_KEY, not a Groq key under any spelling. NOTHING IN THIS FILE CALLS A MODEL. Every
check here measures the PLATFORM'S OWN CODE: which configuration it resolves, which request it
builds, which header it sets, how it reads a response body, and how it refuses. The provider
boundaries are exercised against a captured transport, so what is proved is "the platform sends
this and reads that", never "the provider answered this". No result in this file may be reported
as any model's behaviour.

What is proved:

  1. THE DEFAULT IS THE CONFIGURED DEFAULT. With nothing configured, all three call sites
     resolve anthropic and the identifiers the provider table holds.
     RE-POINTED BY RUN 113, AND THE REASON MATTERS. Until Run 113 these were "the literals that
     were in the source before Run 93" -- never checked against any catalogue. The owner has now
     queried both catalogues from his deployment; anthropic moved to claude-sonnet-5 (narration
     to claude-haiku-4-5-20251001, the one identifier he did not name) and groq to
     openai/gpt-oss-*, because the llama identifiers ARE NOT IN GROQ'S CATALOGUE AT ALL. This
     suite is re-pointed, not weakened: it still asserts an EXACT string per role per provider.
  2. THE SWITCH IS A SETTING. The same functions, from the same unmodified source file, resolve
     a different provider, endpoint, key variable and model when the environment says so. The
     sha256 of every switched source file is taken once and re-taken after the switch and is
     identical, which is the executable form of "the code did not differ between them".
  3. EACH PROVIDER'S DIFFERENCES ARE AT ITS OWN BOUNDARY. The Anthropic boundary posts content
     blocks to /v1/messages with x-api-key and reads content[].text; the OpenAI-shape boundary
     posts a single string to /chat/completions with Authorization: Bearer and reads
     choices[0].message.content. Groq shares that boundary and differs only in host, key and
     model. The applier and the extractor above them are the same objects in both cases.
  4. AN UNCONFIGURED PROVIDER FAILS LOUDLY, naming the provider and the variable that was empty,
     and NEVER falls back to another provider or to an invented result.
  5. EVERY STORED READING RECORDS PROVIDER AND MODEL. Measured on the real ORM objects and the
     real store/read functions, and on the real 0031 migration.
  6. TRUNCATION AND ERRORS ARE SURFACED AS THE PLATFORM'S OWN TYPES on both boundaries.
  7. A PROMPT THE PROVIDER CANNOT CARRY IS REFUSED, NOT SHRUNK. The specification prompt is not
     touched to fit a provider (order section 8.5); a PDF document block that an OpenAI-shape
     endpoint has no field for raises rather than being silently dropped.
  8. NON-VACUITY. Each of the load-bearing checks is re-measured with the mechanism it depends
     on neutralised, and goes red for the intended reason, then restored.

Run (from server/):  python tools/test_run93_provider_switch.py
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import ai_provider as ap
from app import extraction_client as ec
from app import spec_readings as sr
from app.research_models import Document, SpecificationReading
from app.simulation import spec_apply as sa

REPO = pathlib.Path(__file__).resolve().parents[2]
FAILURES: list[str] = []
CHECKS = 0

# The files the switch had to touch. Their bytes are hashed before and after every provider
# switch in this file: the switch is a setting only if these do not move.
SWITCHED_SOURCES = [
    "server/app/ai_provider.py",
    "server/app/extraction_client.py",
    "server/app/simulation/spec_apply.py",
    "server/app/training_narration.py",
]


def check(label: str, got, want) -> None:
    global CHECKS
    CHECKS += 1
    ok = got == want
    if not ok:
        FAILURES.append(label)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")


def check_true(label: str, got) -> None:
    check(label, bool(got), True)


def source_digest() -> str:
    h = hashlib.sha256()
    for rel in SWITCHED_SOURCES:
        h.update((REPO / rel).read_bytes())
    return h.hexdigest()


class Captured:
    """
    A transport, NOT A MODEL. It records the request the platform built and returns a body the
    platform then parses. It proves what is sent and how a body is read. It proves NOTHING about
    what any provider would answer, and no check in this file claims otherwise.
    """

    def __init__(self, body: dict):
        self.body = body
        self.seen: list[tuple[dict, dict]] = []

    def install(self, client):
        # RUN 113 DEFECT, FOUND BY WATCHING THE SOCKET, NOT BY READING THE FILE.
        #
        # Three call sites in section 5 and section 8 passed the APPLIER here, not the client:
        # `o_cap.install(ProviderSpecApplier(build_client(...)))`. `_request` was then set on the
        # applier, which has no such method and never calls one, while the real client underneath
        # was left untouched -- so this file, whose first printed line is "NO MODEL IS CALLED IN
        # THIS FILE", made THREE LIVE HTTPS POSTS to https://api.groq.com/openai/v1/chat/
        # completions carrying the string "present-not-a-real-key" as a bearer token, on every
        # run since Run 93. The checks still passed, because `provider` and `model_id` are read
        # off the applier BEFORE the call and the resulting ProviderCallError is caught by
        # `apply_category` as state "failed" -- a check passing for the wrong reason.
        # The three sites now install on the CLIENT. This guard makes the mistake impossible to
        # repeat silently.
        def _request(request_body, headers):
            self.seen.append((request_body, headers))
            return self.body
        if not hasattr(client, "_request"):
            raise TypeError(
                f"Captured.install was handed a {type(client).__name__}, which has no _request "
                f"to replace. Install on the CLIENT, not on the applier that wraps it: doing "
                f"otherwise leaves the real transport live and posts to the real provider.")
        client._request = _request
        return client


ENV_ANTHROPIC = {"AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "present-not-a-real-key"}
ENV_GROQ = {"AI_PROVIDER": "groq", "GROQ_API_KEY": "present-not-a-real-key"}
ENV_OPENAI = {"AI_PROVIDER": "openai", "OPENAI_API_KEY": "present-not-a-real-key"}


def main() -> int:
    print("Run 93 -- the model is a setting. NO MODEL IS CALLED IN THIS FILE.")
    print(f"python: {sys.version.split()[0]}  ({sys.executable})")
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "GROQ_KEY", "Groq"):
        print(f"  key present in this environment: {name} = "
              f"{bool((os.environ.get(name) or '').strip())}")

    print("\n1. THE DEFAULT IS THE CONFIGURED DEFAULT (nothing set; re-pointed by Run 113)")
    bare: dict[str, str] = {}
    # RUN 113: re-pointed to the owner's measured identifiers. See the docstring.
    # RUN 130: `spec` LEFT THIS LOOP. The owner ruled that the category specification call's
    # provider belongs in the code, so `spec` now defaults to Groq through
    # `ai_provider.ROLE_DEFAULT_PROVIDERS` and is asserted separately below. The two roles
    # left here still default to Anthropic and MUST: Runs 124 and 126 rest on extraction's
    # behaviour. This is a re-pointing of an assertion the owner overruled, not a weakening --
    # every property the loop checked for `spec` is still checked for `spec`, against Groq.
    for role, model in (("extraction", "claude-sonnet-5"),
                        ("narration", "claude-haiku-4-5-20251001")):
        cfg = ap.load_provider(role, bare)
        check(f"{role} provider defaults to anthropic", cfg.provider, "anthropic")
        check(f"{role} model is the owner's measured identifier", cfg.model, model)
        check(f"{role} endpoint unchanged", cfg.url, "https://api.anthropic.com/v1/messages")
        check(f"{role} key variable", cfg.key_env, "ANTHROPIC_API_KEY")
    # RUN 130: the same four properties, for `spec`, against the provider it now defaults to.
    _spec = ap.load_provider("spec", bare)
    check("spec provider defaults to groq", _spec.provider, "groq")
    check("spec model is the groq table's spec identifier", _spec.model,
          ap.PROVIDERS["groq"]["models"]["spec"])
    check("spec endpoint is groq's", _spec.url,
          "https://api.groq.com/openai/v1/chat/completions")
    check("spec key variable is groq's", _spec.key_env, "GROQ_API_KEY")
    # RUN 130: the new rung is the BOTTOM of the chain -- both environment rungs still beat it.
    check("AI_SPEC_PROVIDER still overrides the role default",
          ap.load_provider("spec", {"AI_SPEC_PROVIDER": "anthropic"}).provider, "anthropic")
    check("AI_PROVIDER still sits between the variable and the role default",
          ap.load_provider("spec", {"AI_PROVIDER": "anthropic"}).provider, "anthropic")
    check("AI_SPEC_PROVIDER still beats AI_PROVIDER",
          ap.load_provider("spec", {"AI_PROVIDER": "anthropic",
                                    "AI_SPEC_PROVIDER": "groq"}).provider, "groq")
    # RUN 113: these two are no longer literals at all -- they are DERIVED from the provider
    # table, so they cannot go stale behind it. The assertion is kept and re-pointed.
    check("the module-level constants track the provider table",
          (ec.EXTRACTION_MODEL, sa.SPEC_MODEL), ("claude-sonnet-5", "claude-sonnet-5"))

    print("\n2. THE SWITCH IS A SETTING -- SAME SOURCE, DIFFERENT PROVIDER")
    before = source_digest()
    groq = {role: ap.load_provider(role, ENV_GROQ) for role in ap.ROLES}
    claude = {role: ap.load_provider(role, ENV_ANTHROPIC) for role in ap.ROLES}
    after = source_digest()
    check("source of every switched file is byte-identical across the two settings",
          after, before)
    check("spec provider under AI_PROVIDER=groq", groq["spec"].provider, "groq")
    check("spec endpoint under groq", groq["spec"].url,
          "https://api.groq.com/openai/v1/chat/completions")
    check("spec key variable under groq", groq["spec"].key_env, "GROQ_API_KEY")
    check("spec provider under AI_PROVIDER=anthropic", claude["spec"].provider, "anthropic")
    check("attribution string differs between the two",
          (claude["spec"].attribution, groq["spec"].attribution),
          ("anthropic/claude-sonnet-5", "groq/openai/gpt-oss-120b"))

    print("   the key variable NAME is itself a setting (the owner's Groq variable may differ)")
    named = ap.load_provider("spec", {"AI_PROVIDER": "groq", "AI_GROQ_KEY_ENV": "Groq"})
    check("AI_GROQ_KEY_ENV redirects which variable is read", named.key_env, "Groq")
    check("and presence is read from THAT variable",
          named.key_present({"Groq": "present-not-a-real-key"}), True)

    print("   the model is a setting too, per role and per provider")
    check("AI_SPEC_MODEL overrides",
          ap.load_provider("spec", {"AI_PROVIDER": "groq", "AI_SPEC_MODEL": "x-1"}).model, "x-1")
    check("AI_<PROVIDER>_BASE_URL overrides the endpoint",
          ap.load_provider("spec", {"AI_PROVIDER": "groq",
                                    "AI_GROQ_BASE_URL": "https://h/v9"}).url,
          "https://h/v9/chat/completions")
    check("a role may differ from the platform default",
          ap.load_provider("extraction",
                           {"AI_PROVIDER": "groq",
                            "AI_EXTRACTION_PROVIDER": "anthropic"}).provider, "anthropic")

    print("\n3. EACH PROVIDER'S DIFFERENCES ARE AT ITS OWN BOUNDARY")
    a_cap = Captured({"content": [{"type": "text", "text": "ANTHROPIC-BODY"}],
                      "stop_reason": "end_turn"})
    a_client = a_cap.install(ap.build_client(claude["spec"], environ=ENV_ANTHROPIC))
    o_cap = Captured({"choices": [{"finish_reason": "stop",
                                   "message": {"content": "OPENAI-BODY"}}]})
    o_client = o_cap.install(ap.build_client(groq["spec"], environ=ENV_GROQ))

    a_applier, o_applier = sa.ProviderSpecApplier(a_client), sa.ProviderSpecApplier(o_client)
    check("the applier class is the SAME object for both providers",
          a_applier.__class__ is o_applier.__class__, True)
    check("anthropic answer read from content[].text",
          a_applier.apply("A1", "PROMPT"), "ANTHROPIC-BODY")
    check("openai-shape answer read from choices[0].message.content",
          o_applier.apply("A1", "PROMPT"), "OPENAI-BODY")

    a_body, a_head = a_cap.seen[0]
    o_body, o_head = o_cap.seen[0]
    check("anthropic authenticates with x-api-key", "x-api-key" in a_head, True)
    check("anthropic sends its version header", a_head.get("anthropic-version"), "2023-06-01")
    check("anthropic sends content BLOCKS", a_body["messages"][0]["content"],
          [{"type": "text", "text": "PROMPT"}])
    check("openai-shape authenticates with Authorization: Bearer",
          o_head.get("authorization", "").startswith("Bearer "), True)
    check("openai-shape sends no anthropic version header", "anthropic-version" in o_head, False)
    check("openai-shape sends a single string message", o_body["messages"][0]["content"],
          "PROMPT")
    check("the model named in the body is the configured one, per provider",
          (a_body["model"], o_body["model"]),
          ("claude-sonnet-5", "openai/gpt-oss-120b"))
    check("NO KEY APPEARS IN EITHER REQUEST BODY",
          "present-not-a-real-key" in json.dumps(a_body) + json.dumps(o_body), False)
    check("the prompt reaching both providers is byte-identical",
          a_body["messages"][0]["content"][0]["text"] == o_body["messages"][0]["content"], True)

    print("\n4. AN UNCONFIGURED PROVIDER FAILS LOUDLY AND NEVER FALLS BACK")
    keyless = {"AI_PROVIDER": "groq"}
    cfg = ap.load_provider("spec", keyless)
    try:
        ap.build_client(cfg, environ=keyless)
        check("keyless provider raises", "no exception", "ProviderNotConfigured")
    except ap.ProviderNotConfigured as exc:
        msg = str(exc)
        check("the refusal names the provider", "'groq'" in msg, True)
        check("the refusal names the variable that was empty", "GROQ_API_KEY" in msg, True)
        check("the refusal says nothing else served in its place",
              "another provider" in msg, True)
        check("no key value is in the message", "present-not-a-real-key" in msg, False)
    try:
        ap.load_provider("spec", {"AI_PROVIDER": "definitely-not-a-provider"})
        check("unknown provider name raises", "no exception", "ProviderConfigError")
    except ap.ProviderConfigError as exc:
        check("an unknown provider is refused, not defaulted", "not one this platform" in str(exc),
              True)

    print("   and the platform-level builders honour that, with no second provider tried")
    saved = dict(os.environ)
    try:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ["AI_PROVIDER"] = "groq"
        os.environ.pop("GROQ_API_KEY", None)
        built = sa.build_applier({})
        check("build_applier with no key for the CONFIGURED provider gives the recorded stub, "
              "never another provider", built.__class__.__name__, "RecordedSpecApplier")
        check("and that row is stamped recorded, not a provider", built.provider, "recorded")
        try:
            sa.require_applier()
            check("require_applier raises", "no exception", "ProviderNotConfigured")
        except ap.ProviderNotConfigured as exc:
            check("require_applier names groq", "'groq'" in str(exc), True)
        try:
            ec.build_extractor(require_real=True)
            check("build_extractor(require_real) raises", "no exception", "ExtractionError")
        except ec.ExtractionError as exc:
            check("extraction refusal names the configured provider", "'groq'" in str(exc), True)
            check("extraction refusal names the variable", "GROQ_API_KEY" in str(exc), True)
        check("the keyless extractor is the stub, stamped as one",
              ec.build_extractor().provider, "stub")
    finally:
        os.environ.clear()
        os.environ.update(saved)
    check("environment restored", os.environ.get("AI_PROVIDER"), saved.get("AI_PROVIDER"))

    print("\n5. EVERY STORED READING RECORDS PROVIDER AND MODEL")
    check("specification_readings has a provider column",
          "provider" in SpecificationReading.__table__.c, True)
    check("documents has an extraction_provider column",
          "extraction_provider" in Document.__table__.c, True)
    mig = (REPO / "server/alembic/versions/0031_model_provider_attribution.py").read_text()
    check("0031 exists and follows 0030", 'down_revision = "0030_extraction_contract"' in mig,
          True)
    check("0031 adds both columns",
          all(t in mig for t in ('"specification_readings", sa.Column("provider"',
                                 '"documents", sa.Column("extraction_provider"')), True)

    row = sa.apply_category("A1", {"x": 1}, sa.ProviderSpecApplier(
        o_cap.install(ap.build_client(groq["spec"], environ=ENV_GROQ))))
    check("apply_category records the provider that answered", row["provider"], "groq")
    check("apply_category records the model beside it", row["model_id"],
          "openai/gpt-oss-120b")
    stored = SpecificationReading(
        reading_id="r93", category_key="A1", state="failed", counts={}, modules=[],
        missing_upstream=[], served_by=row["served_by"], provider=row["provider"],
        model_id=row["model_id"], simulation_version="t")
    payload = sr.reading_payload(stored)
    check("the stored row reaches the client carrying its provider",
          (payload["provider"], payload["modelId"]), ("groq", "openai/gpt-oss-120b"))

    print("\n6. TRUNCATION AND ERRORS SURFACE AS THE PLATFORM'S OWN TYPES")
    trunc_a = Captured({"content": [{"type": "text", "text": "{"}], "stop_reason": "max_tokens"})
    ta = sa.ProviderSpecApplier(trunc_a.install(
        ap.build_client(claude["spec"], environ=ENV_ANTHROPIC)))
    try:
        ta.apply("A1", "P")
        check("anthropic truncation raises", "no exception", "SpecApplicationError")
    except sa.SpecApplicationError as exc:
        check("anthropic truncation names the provider and the cap",
              "anthropic" in str(exc) and "8192" in str(exc), True)
    trunc_o = Captured({"choices": [{"finish_reason": "length", "message": {"content": "{"}}]})
    to = sa.ProviderSpecApplier(trunc_o.install(ap.build_client(groq["spec"], environ=ENV_GROQ)))
    try:
        to.apply("A1", "P")
        check("openai-shape truncation raises", "no exception", "SpecApplicationError")
    except sa.SpecApplicationError as exc:
        check("openai-shape truncation names the provider and the cap",
              "groq" in str(exc) and "8192" in str(exc), True)
    empty = Captured({"choices": []})
    te = sa.ProviderSpecApplier(empty.install(ap.build_client(groq["spec"], environ=ENV_GROQ)))
    try:
        te.apply("A1", "P")
        check("an empty choices list raises", "no exception", "SpecApplicationError")
    except sa.SpecApplicationError as exc:
        check("an empty answer is a failure, not an empty reading",
              "no choices" in str(exc), True)

    print("\n7. A PROMPT THE PROVIDER CANNOT CARRY IS REFUSED, NOT SHRUNK")
    pdf_block = {"type": "document",
                 "source": {"type": "base64", "media_type": "application/pdf", "data": "AAA="}}
    o_ext = ap.build_client(ap.load_provider("extraction", ENV_GROQ), environ=ENV_GROQ)
    try:
        o_ext.complete([pdf_block, {"type": "text", "text": "P"}], max_tokens=10)
        check("a document block on an openai-shape provider raises", "no", "ProviderCannotCarry")
    except ap.ProviderCannotCarry as exc:
        check("the refusal names the provider", "'groq'" in str(exc), True)
        check("the refusal states the document was NOT dropped",
              "NOT dropped" in str(exc), True)
    a_ext_cap = Captured({"content": [{"type": "text", "text": "{}"}], "stop_reason": "end_turn"})
    a_ext = a_ext_cap.install(
        ap.build_client(ap.load_provider("extraction", ENV_ANTHROPIC), environ=ENV_ANTHROPIC))
    a_ext.complete([pdf_block, {"type": "text", "text": "P"}], max_tokens=10)
    check("anthropic carries the document block unchanged",
          a_ext_cap.seen[0][0]["messages"][0]["content"][0], pdf_block)
    spec_len = len(sa.load_specification("A1"))
    check("the A1 specification text is non-trivial and was not shrunk to fit",
          spec_len > 5000, True)

    print("\n8. NON-VACUITY -- each mechanism neutralised, goes red, restored")
    src = REPO / "server/app/ai_provider.py"
    original = src.read_bytes()
    try:
        # (a) neutralise the loud refusal: make read_key return "" instead of raising.
        patched = original.replace(
            b'        raise ProviderNotConfigured(',
            b'        return ""  # RUN 93 NON-VACUITY INJECTION\n        raise ProviderNotConfigured(')
        check("injection (a) actually changed the bytes", patched != original, True)
        src.write_bytes(patched)
        import importlib
        reread = importlib.reload(importlib.import_module("app.ai_provider"))
        check("re-read from disk carries the injection",
              b"NON-VACUITY INJECTION" in src.read_bytes(), True)
        raised = True
        try:
            reread.read_key(reread.load_provider("spec", {"AI_PROVIDER": "groq"}),
                            {"AI_PROVIDER": "groq"})
            raised = False
        except reread.ProviderNotConfigured:
            pass
        check("WITH THE REFUSAL NEUTRALISED the keyless path stops raising (check can fail)",
              raised, False)
    finally:
        src.write_bytes(original)
        import importlib
        ap2 = importlib.reload(importlib.import_module("app.ai_provider"))
        check("source restored byte-for-byte",
              hashlib.sha256(src.read_bytes()).hexdigest(),
              hashlib.sha256(original).hexdigest())
        restored = False
        try:
            ap2.read_key(ap2.load_provider("spec", {"AI_PROVIDER": "groq"}),
                         {"AI_PROVIDER": "groq"})
        except ap2.ProviderNotConfigured:
            restored = True
        check("baseline rechecked: the refusal raises again", restored, True)

    # (b) neutralise the attribution: a stored reading that cannot say which model made it.
    spec_src = REPO / "server/app/simulation/spec_apply.py"
    spec_original = spec_src.read_bytes()
    try:
        line = b'        base["provider"] = getattr(applier, "provider", None)\n'
        check("injection (b) target line is present", line in spec_original, True)
        spec_src.write_bytes(spec_original.replace(line, b""))
        check("re-read from disk carries injection (b)",
              line in spec_src.read_bytes(), False)
        import importlib
        sa2 = importlib.reload(importlib.import_module("app.simulation.spec_apply"))
        blind = sa2.apply_category("A1", {"x": 1}, sa2.ProviderSpecApplier(
            o_cap.install(ap.build_client(groq["spec"], environ=ENV_GROQ))))
        check("WITH ATTRIBUTION NEUTRALISED the row cannot say which provider (check can fail)",
              blind["provider"], None)
    finally:
        spec_src.write_bytes(spec_original)
        import importlib
        sa3 = importlib.reload(importlib.import_module("app.simulation.spec_apply"))
        check("spec_apply.py restored byte-for-byte",
              hashlib.sha256(spec_src.read_bytes()).hexdigest(),
              hashlib.sha256(spec_original).hexdigest())
        again = sa3.apply_category("A1", {"x": 1}, sa3.ProviderSpecApplier(
            o_cap.install(ap.build_client(groq["spec"], environ=ENV_GROQ))))
        check("baseline rechecked: attribution is recorded again", again["provider"], "groq")

    passed = CHECKS - len(FAILURES)
    print(f"\nRESULT: {passed}/{CHECKS} checks passed")
    if FAILURES:
        print("FAILURES: " + ", ".join(FAILURES))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
