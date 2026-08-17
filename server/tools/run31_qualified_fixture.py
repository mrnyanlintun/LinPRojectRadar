"""
RUN 31 v19: THE GOVERNED CATEGORY-9 ASSESSMENT A TEST FIXTURE MUST NOW SUPPLY.

WHY SUITES NEED THIS AT ALL. Under `sim-2026.08-v19` the owner's closure decision is that a
package carrying NO Category-9 assessment FAILS CLOSED for every Category-6/7/8/10 consumer.
That is a real behaviour change and it reaches every fixture: a suite that hands a module raw
signal inputs and expects a reading is, from v19 onward, a caller offering unassessed evidence,
and the governed answer is refusal.

THIS IS THE SAME SITUATION PASS 1 MET WITH GOVERNED STRUCTURES and it is resolved the same way.
When the canonical layer began requiring a defining structure, fixtures representing projects
that genuinely had the evidence were given the structure; they were not exempted from the
requirement. Here, fixtures whose scientific purpose is a module's ARITHMETIC are given the
assessment their module now requires, so the test reaches the arithmetic it was written to check.

WHAT THIS IS NOT. It is not an exemption and it does not soften the gate. `QUALIFIED_ASSESSMENT`
is an ordinary governed declaration of exactly the kind a real caller supplies, it goes in
through the ordinary signal-input key, and it is subject to the ordinary `assess()` precedence --
a fixture that also declares a missing critical field, a material conflict or a future date is
still refused. The gate's OWN guards -- `test_run31_pass2_acceptance` and
`test_run31_version_boundaries` -- never install this, because they exist to test the boundary
rather than to get past it.

THE ASSESSMENT IS DELIBERATELY MINIMAL AND HONEST. It declares only what a laboratory fixture can
truthfully declare: that the evidence was assessed, is timely for the use, is verified and comes
from a system of record. It declares NO reliability weight, so `assess()` returns
QUALIFIED_WITH_LIMITATIONS and records that no governed reliability mapping exists -- which is
the truthful state, and is why nothing here fabricates a number.
"""

from __future__ import annotations

#: The governed assessment a laboratory fixture supplies. Ordinary declaration, ordinary key.
QUALIFIED_ASSESSMENT: dict[str, object] = {
    "evidence_id": "RUN31-LAB-FIXTURE",
    "qualification_state": "QUALIFIED",
    "timeliness_status": "TIMELY",
    "verification_status": "verified",
    "source_authority": "system_of_record",
    "data_origin": "SYNTHETIC_RESEARCH_FIXTURE",
    "not_for_empirical_validation": True,
}

KEY = "evidenceQualification"


def qualified(si: dict) -> dict:
    """Return `si` with the governed assessment attached, without mutating the caller's dict."""
    if not isinstance(si, dict):
        return si
    if KEY in si:
        return si
    out = dict(si)
    out[KEY] = dict(QUALIFIED_ASSESSMENT)
    return out


def install() -> None:
    """
    Attach the governed assessment to signal inputs reaching the production dispatcher.

    Patches the registry MODULE OBJECT so every spelling of the import is reached. A fixture that
    supplies its OWN assessment is left alone, so a suite testing refusal still tests refusal.
    """
    from app.simulation import registry as _registry
    if getattr(_registry, "_run31_qualified_installed", False):
        return
    live = _registry.run_module

    def _resolve(new_id, si, rand, period_cutoff, *a, **k):
        return live(new_id, qualified(si), rand, period_cutoff, *a, **k)

    _registry.run_module = _resolve
    _registry._run31_qualified_installed = True
