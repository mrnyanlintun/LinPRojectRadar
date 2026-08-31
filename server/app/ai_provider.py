"""
WHICH MODEL SERVES THE PLATFORM IS A SETTING, NOT A CONSTANT. (Run 93)

Before this module the provider, the endpoint, the authentication header, the request shape and
the model identifier were literals in three separate files. Switching provider meant editing
source and redeploying different code. This module is the single boundary where a provider's
differences live, so that switching is an environment change in both directions and the rest of
the platform sees one interface.

THE INTERFACE THE PLATFORM SEES

    cfg = load_provider("extraction")      # or "spec" or "narration"
    client = build_client(cfg)             # raises ProviderNotConfigured if the key is absent
    text = client.complete(blocks, max_tokens=..., temperature=...)

`blocks` is the Anthropic content-block vocabulary, because that is the vocabulary the platform
already builds and it is the richer of the two: {"type": "text"} and {"type": "document"}. Each
boundary translates it into its own wire shape, or REFUSES loudly when it cannot carry it. It
never quietly drops a block, because a prompt silently shorn of its document is a plausible
answer about nothing.

WHAT IS DELIBERATELY NOT HERE

No fallback. If the configured provider has no key, or is unreachable, the call fails naming the
provider and what was missing. It does not try another provider and it does not return a
plausible answer from no model at all. A reading that came from a different model than the
deployment was configured for is unusable as evidence, and one invented from no model is worse.

NO KEY VALUE EVER LEAVES THIS MODULE. Following `settings.py`: presence is a fact worth
reporting, the credential is not. `key_present()` returns a bool; nothing here logs, formats or
repr's a key, and `ProviderConfig` holds the NAME of the environment variable, never its value.

THE KEY VARIABLE NAME IS ITSELF CONFIGURABLE. Each provider has a documented default
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`), and `AI_<PROVIDER>_KEY_ENV` overrides
it, so a deployment whose Groq key sits under some other variable name matches it by setting
rather than by a code change -- which is the whole point of this module.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

# The three call sites, named. See the report's "every call site switched".
ROLES = ("extraction", "spec", "narration")

# --------------------------------------------------------------------------- provider table
#
# `wire` is the request/response shape, not the vendor: Groq serves the OpenAI chat-completions
# shape at its own host, so it shares that boundary and differs only in endpoint, key and models.
#
# DEFAULTS ARE TODAY'S BEHAVIOUR. With nothing configured the platform resolves provider
# "anthropic" and exactly the three model identifiers that were literals in the source before
# this module existed: claude-opus-4-6 for extraction, claude-sonnet-4-5 for specification
# application, claude-3-5-haiku-latest for training narration. A deployment that sets nothing
# keeps behaving as it did.

PROVIDERS: dict[str, dict[str, Any]] = {
    "anthropic": {
        "wire": "anthropic",
        "base_url": "https://api.anthropic.com",
        "path": "/v1/messages",
        "key_env": "ANTHROPIC_API_KEY",
        "models": {
            "extraction": "claude-opus-4-6",
            "spec": "claude-sonnet-4-5",
            "narration": "claude-3-5-haiku-latest",
        },
    },
    "openai": {
        "wire": "openai",
        "base_url": "https://api.openai.com/v1",
        "path": "/chat/completions",
        "key_env": "OPENAI_API_KEY",
        "models": {
            "extraction": "gpt-4o",
            "spec": "gpt-4o",
            "narration": "gpt-4o-mini",
        },
    },
    "groq": {
        "wire": "openai",
        "base_url": "https://api.groq.com/openai/v1",
        "path": "/chat/completions",
        "key_env": "GROQ_API_KEY",
        "models": {
            "extraction": "llama-3.3-70b-versatile",
            "spec": "llama-3.3-70b-versatile",
            "narration": "llama-3.1-8b-instant",
        },
    },
}

DEFAULT_PROVIDER = "anthropic"
ANTHROPIC_VERSION = "2023-06-01"


class ProviderConfigError(RuntimeError):
    """The configuration itself is unusable -- an unknown provider name, an empty model."""


class ProviderNotConfigured(RuntimeError):
    """The configured provider has no key. Names the provider and the variable that was empty."""


class ProviderCallError(RuntimeError):
    """The configured provider was asked and could not answer. Never a fallback to another."""


class ProviderTruncated(ProviderCallError):
    """The answer was CUT OFF by the output cap, not malformed. A different, actionable fault."""


class ProviderCannotCarry(ProviderCallError):
    """
    The prompt the platform built cannot be expressed in this provider's request shape.

    Raised, never worked around. Run 84 scoped the specification prompt from ~130k tokens to
    ~60k by deriving the needed figures from the specification text; a provider that cannot
    accept what the platform builds is a FINDING ABOUT THAT PROVIDER, and shrinking the
    specification or dropping a document to make it fit would silently change what was measured.
    """


@dataclass(frozen=True)
class ProviderConfig:
    """What serves one role. Carries the key's VARIABLE NAME, never the key."""

    role: str
    provider: str
    wire: str
    model: str
    url: str
    key_env: str

    @property
    def attribution(self) -> str:
        """`provider/model`, the single string stamped on a stored reading."""
        return f"{self.provider}/{self.model}"

    def key_present(self, environ: dict[str, str] | None = None) -> bool:
        env = os.environ if environ is None else environ
        return bool((env.get(self.key_env) or "").strip())


def _env(environ: dict[str, str] | None) -> Any:
    return os.environ if environ is None else environ


def configured_provider(environ: dict[str, str] | None = None) -> str:
    """
    The provider name, lowercased. `AI_PROVIDER` is the switch; a role may override it with
    `AI_EXTRACTION_PROVIDER` / `AI_SPEC_PROVIDER` / `AI_NARRATION_PROVIDER`, so a deployment can
    move extraction to one provider while the analytical layer stays where it is.
    """
    env = _env(environ)
    return (env.get("AI_PROVIDER") or "").strip().lower() or DEFAULT_PROVIDER


def load_provider(role: str, environ: dict[str, str] | None = None) -> ProviderConfig:
    """Resolve the configuration for one role. Raises ProviderConfigError, never guesses."""
    if role not in ROLES:
        raise ProviderConfigError(
            f"{role!r} is not one of the platform's model call sites {ROLES}.")
    env = _env(environ)

    name = ((env.get(f"AI_{role.upper()}_PROVIDER") or "").strip().lower()
            or configured_provider(env))
    spec = PROVIDERS.get(name)
    if spec is None:
        raise ProviderConfigError(
            f"AI provider {name!r} is not one this platform knows how to call. "
            f"Set AI_PROVIDER (or AI_{role.upper()}_PROVIDER) to one of "
            f"{', '.join(sorted(PROVIDERS))}.")

    upper = name.upper()
    model = ((env.get(f"AI_{role.upper()}_MODEL") or "").strip()
             or (env.get(f"AI_{upper}_{role.upper()}_MODEL") or "").strip()
             or spec["models"][role])
    if not model:
        raise ProviderConfigError(
            f"no model is configured for {name} {role}; set AI_{role.upper()}_MODEL.")

    base = ((env.get(f"AI_{upper}_BASE_URL") or "").strip()
            or str(spec["base_url"])).rstrip("/")
    key_env = (env.get(f"AI_{upper}_KEY_ENV") or "").strip() or str(spec["key_env"])

    return ProviderConfig(role=role, provider=name, wire=str(spec["wire"]), model=model,
                          url=base + str(spec["path"]), key_env=key_env)


def read_key(cfg: ProviderConfig, environ: dict[str, str] | None = None) -> str:
    """
    The key, or a loud refusal naming the provider AND the variable that was empty.

    The return value is a credential. It is passed straight into a request header by the caller
    and is never logged, formatted into a message, or stored.
    """
    env = _env(environ)
    key = (env.get(cfg.key_env) or "").strip()
    if not key:
        raise ProviderNotConfigured(
            f"AI provider {cfg.provider!r} is configured for the {cfg.role} call site but "
            f"{cfg.key_env} is not set in this environment. Set {cfg.key_env}, or point "
            f"AI_{cfg.provider.upper()}_KEY_ENV at the variable that holds the key, or change "
            f"AI_PROVIDER. Nothing is served by another provider in its place and no result is "
            f"produced without a model.")
    return key


# --------------------------------------------------------------------------- the boundaries


class _Client:
    def __init__(self, cfg: ProviderConfig, api_key: str, timeout_s: float) -> None:
        self.cfg = cfg
        self._key = api_key
        self._timeout = timeout_s

    @property
    def provider(self) -> str:
        return self.cfg.provider

    @property
    def model_id(self) -> str:
        return self.cfg.model

    @property
    def attribution(self) -> str:
        return self.cfg.attribution

    def _request(self, body: dict, headers: dict) -> dict:
        req = urllib.request.Request(
            self.cfg.url, data=json.dumps(body).encode("utf-8"), method="POST",
            headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            raise ProviderCallError(
                f"{self.cfg.provider} ({self.cfg.model}) returned {exc.code}: {detail}") from None
        except urllib.error.URLError as exc:
            raise ProviderCallError(
                f"{self.cfg.provider} ({self.cfg.model}) is unreachable: {exc.reason}") from None
        except ValueError as exc:
            raise ProviderCallError(
                f"{self.cfg.provider} ({self.cfg.model}) returned a body that is not JSON: "
                f"{exc}") from None

    def complete(self, blocks: list[dict], max_tokens: int,
                 temperature: float | None = None) -> str:
        raise NotImplementedError


class AnthropicClient(_Client):
    """Endpoint /v1/messages, x-api-key, content blocks in, content[].text out."""

    def complete(self, blocks: list[dict], max_tokens: int,
                 temperature: float | None = None) -> str:
        body: dict[str, Any] = {
            "model": self.cfg.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": list(blocks)}],
        }
        if temperature is not None:
            body["temperature"] = temperature
        payload = self._request(body, {
            "content-type": "application/json",
            "x-api-key": self._key,
            "anthropic-version": ANTHROPIC_VERSION,
        })
        text = "".join(b.get("text", "") for b in (payload.get("content") or [])
                       if b.get("type") == "text")
        if str(payload.get("stop_reason") or "") == "max_tokens":
            raise ProviderTruncated(
                f"{self.cfg.provider} ({self.cfg.model}) ran out of output space "
                f"({max_tokens} tokens) before it finished answering.", )
        return text


class OpenAICompatClient(_Client):
    """
    Endpoint /chat/completions, Authorization: Bearer, a single string message in,
    choices[0].message.content out. Serves OpenAI and Groq, which speak the same shape.

    A `document` block has NO equivalent here. Neither provider's chat-completions endpoint
    accepts an arbitrary base64 PDF the way Anthropic's `document` block does, so rather than
    dropping the document and asking the model to read a prompt about nothing, this refuses and
    says which provider could not carry it.
    """

    def complete(self, blocks: list[dict], max_tokens: int,
                 temperature: float | None = None) -> str:
        parts = []
        for b in blocks:
            kind = b.get("type")
            if kind == "text":
                parts.append(b.get("text", ""))
            else:
                raise ProviderCannotCarry(
                    f"the {self.cfg.role} prompt contains a {kind!r} content block, and "
                    f"provider {self.cfg.provider!r} has no request shape that carries it. "
                    f"The document was NOT dropped and no answer was produced from the "
                    f"remaining text. Use a provider that accepts document input for this "
                    f"call site, or supply the document as text.")
        body: dict[str, Any] = {
            "model": self.cfg.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": "\n\n".join(parts)}],
        }
        if temperature is not None:
            body["temperature"] = temperature
        payload = self._request(body, {
            "content-type": "application/json",
            "authorization": "Bearer " + self._key,
        })
        choices = payload.get("choices") or []
        if not choices:
            err = (payload.get("error") or {}).get("message")
            raise ProviderCallError(
                f"{self.cfg.provider} ({self.cfg.model}) returned no choices"
                + (f": {err}" if err else "."))
        first = choices[0] or {}
        if str(first.get("finish_reason") or "") == "length":
            raise ProviderTruncated(
                f"{self.cfg.provider} ({self.cfg.model}) ran out of output space "
                f"({max_tokens} tokens) before it finished answering.")
        return str(((first.get("message") or {}).get("content")) or "")


_WIRES = {"anthropic": AnthropicClient, "openai": OpenAICompatClient}


def build_client(cfg: ProviderConfig, timeout_s: float = 120.0,
                 environ: dict[str, str] | None = None) -> _Client:
    """The client for this configuration. Raises ProviderNotConfigured when the key is absent."""
    klass = _WIRES.get(cfg.wire)
    if klass is None:  # unreachable while PROVIDERS and _WIRES agree; not silently tolerated
        raise ProviderConfigError(f"no request boundary is implemented for wire {cfg.wire!r}")
    return klass(cfg, read_key(cfg, environ), timeout_s)


def provider_diagnostics(environ: dict[str, str] | None = None) -> dict[str, Any]:
    """
    What is configured, for /exec health. PRESENCE ONLY -- no key value, ever.
    """
    out: dict[str, Any] = {"defaultProvider": configured_provider(environ), "roles": {}}
    for role in ROLES:
        try:
            cfg = load_provider(role, environ)
        except ProviderConfigError as exc:
            out["roles"][role] = {"error": str(exc)}
            continue
        out["roles"][role] = {
            "provider": cfg.provider,
            "model": cfg.model,
            "keyEnv": cfg.key_env,
            "keyPresent": cfg.key_present(environ),
            "attribution": cfg.attribution,
        }
    return out
