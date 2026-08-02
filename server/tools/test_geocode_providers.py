#!/usr/bin/env python3
"""
The geocoding provider seam: Google primary, US Census fallback.

Run (from server/):

    python tools/test_geocode_providers.py

WHY THIS SUITE EXISTS SEPARATELY FROM test_workspace_t3t5.

That suite replaces `app.geocode.geocode` wholesale with a stub, which is right for what it tests
(that a project still saves when a geocoder fails) and means it never exercises a provider at all.
Every branch below was therefore uncovered: the difference between a rejected key, an exhausted
quota and an address that does not exist was untested, and those are the branches a user has to be
able to tell apart.

NO NETWORK. `_get_json` is the single HTTP seam in the module, and it is replaced here. Nothing in
this file reaches Google, the Census, or anything else, so it is deterministic and runs offline.

CACHING IS ASSERTED, NOT ASSUMED. The rule is that an answer about the ADDRESS is cached and an
answer about the SERVICE is not, because caching a rejected key would make one misconfigured
minute permanent. Both halves are checked.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

import app.geocode as geo  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


# --------------------------------------------------------------------- fixtures

GOOGLE_OK = {
    "status": "OK",
    "results": [{"formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
                 "geometry": {"location": {"lat": 37.4224764, "lng": -122.0842499}}}],
}
GOOGLE_OK_MULTI = {
    "status": "OK",
    "results": [
        {"formatted_address": "Springfield, IL, USA",
         "geometry": {"location": {"lat": 39.7817213, "lng": -89.6501481}}},
        {"formatted_address": "Springfield, MA, USA",
         "geometry": {"location": {"lat": 42.1014831, "lng": -72.589811}}},
    ],
}
GOOGLE_OK_PARTIAL = {
    "status": "OK",
    "results": [{"formatted_address": "Main St, Anytown, USA", "partial_match": True,
                 "geometry": {"location": {"lat": 40.0, "lng": -75.0}}}],
}
CENSUS_OK = {
    "result": {"addressMatches": [
        {"matchedAddress": "1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500",
         "coordinates": {"x": -77.03518753691, "y": 38.89869893252}}]},
}
CENSUS_NONE = {"result": {"addressMatches": []}}


class _Router:
    """Answers by URL prefix, so one stub serves both providers and records what was called."""

    def __init__(self, google=None, census=None):
        self.google = google
        self.census = census
        self.calls: list[str] = []

    def __call__(self, url: str) -> dict:
        if url.startswith(geo.GOOGLE_URL):
            self.calls.append("google")
            if isinstance(self.google, Exception):
                raise self.google
            if self.google is None:
                raise AssertionError("google was called but this case supplies no google payload")
            return self.google
        if url.startswith(geo.CENSUS_URL):
            self.calls.append("census")
            if isinstance(self.census, Exception):
                raise self.census
            if self.census is None:
                raise AssertionError("census was called but this case supplies no census payload")
            return self.census
        raise AssertionError(f"unexpected geocoder URL: {url[:60]}")


def run(address: str, *, google=None, census=None, key: str | None = "test-key"):
    """One geocode with a fresh cache and a controlled environment. Returns (result, router)."""
    geo._cache.clear()
    router = _Router(google=google, census=census)
    real_get, real_key = geo._get_json, os.environ.get(geo.GOOGLE_KEY_ENV)
    geo._get_json = router
    if key is None:
        os.environ.pop(geo.GOOGLE_KEY_ENV, None)
    else:
        os.environ[geo.GOOGLE_KEY_ENV] = key
    try:
        return geo.geocode(address), router
    finally:
        geo._get_json = real_get
        if real_key is None:
            os.environ.pop(geo.GOOGLE_KEY_ENV, None)
        else:
            os.environ[geo.GOOGLE_KEY_ENV] = real_key


print("=" * 78)
print("GUARANTEE 1: Google answers, and the fallback is not consulted")
print("=" * 78)
r, router = run("1600 Amphitheatre Pkwy", google=GOOGLE_OK)
check(r.ok, "a Google match produces a position", str(r.error))
check(r.provider == "google", "and it is attributed to Google", str(r.provider))
check(abs((r.lat or 0) - 37.4224764) < 1e-9 and abs((r.lng or 0) + 122.0842499) < 1e-9,
      "with Google's own coordinates", f"{r.lat},{r.lng}")
check(r.formatted == "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
      "and Google's formatted address, which is what is shown back to the user", str(r.formatted))
check(r.ambiguous is False, "a single exact result is not flagged ambiguous")
check(router.calls == ["google"], "the fallback is not called when the primary succeeds",
      str(router.calls))

print()
print("=" * 78)
print("GUARANTEE 2: the fallback runs when Google finds nothing or cannot be reached")
print("=" * 78)
r, router = run("1600 Pennsylvania Ave", google={"status": "ZERO_RESULTS", "results": []},
                census=CENSUS_OK)
check(r.ok and r.provider == "census",
      "Google finding nothing falls through to the Census", f"{r.ok} {r.provider}")
check(router.calls == ["google", "census"], "and both were called, in order", str(router.calls))
check(r.formatted == "1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500",
      "the Census matched address is shown back", str(r.formatted))

r, router = run("1600 Pennsylvania Ave", google=TimeoutError("timed out"), census=CENSUS_OK)
check(r.ok and r.provider == "census",
      "an unreachable Google falls through to the Census", f"{r.ok} {r.provider}")

print()
print("=" * 78)
print("GUARANTEE 3: the four failure conditions are told apart")
print("=" * 78)
# Each of these is a different problem with a different fix, and the whole point of handling the
# statuses by name is that the sentence a user reads says which one happened.
r, _ = run("nowhere at all", google={"status": "ZERO_RESULTS", "results": []},
           census=CENSUS_NONE)
check("could not be found" in (r.error or ""),
      "not found: both providers answered, and the answer was no", str(r.error)[:70])

r, _ = run("x", google={"status": "REQUEST_DENIED", "error_message": "API key not valid"},
           census=CENSUS_NONE)
check("credentials" in (r.error or ""),
      "key rejected: named as a credentials problem", str(r.error)[:70])
check("API key not valid" not in (r.error or ""),
      "and Google's raw error_message is not shown to the user", str(r.error)[:70])

r, _ = run("x", google={"status": "OVER_QUERY_LIMIT"}, census=CENSUS_NONE)
check("usage limit" in (r.error or ""), "quota: named as a usage limit", str(r.error)[:70])

r, router = run("x", google=None, census=CENSUS_NONE, key=None)
check("not configured" in (r.error or ""),
      "no key: named as a deployment configuration problem", str(r.error)[:70])
check(router.calls == ["census"],
      "and no request is made to Google at all when the key is absent", str(router.calls))

r, _ = run("x", google=TimeoutError("t"), census=TimeoutError("t"))
check("could not be reached" in (r.error or ""),
      "unreachable: named as a reachability problem", str(r.error)[:70])

# The message must not claim an address does not exist on the strength of a US-only fallback.
r, _ = run("10 Downing Street, London", google={"status": "REQUEST_DENIED"}, census=CENSUS_NONE)
check("could not be found" not in (r.error or ""),
      "a US-only fallback finding nothing is NOT reported as the address not existing",
      str(r.error)[:80])

print()
print("=" * 78)
print("GUARANTEE 4: an uncertain match is flagged but still used")
print("=" * 78)
r, _ = run("Springfield", google=GOOGLE_OK_MULTI)
check(r.ok, "several candidates still produce a position")
check(r.ambiguous is True, "and it is flagged ambiguous", str(r.ambiguous))
r, _ = run("Main St", google=GOOGLE_OK_PARTIAL)
check(r.ok and r.ambiguous is True, "a partial match is flagged ambiguous",
      f"{r.ok} {r.ambiguous}")

print()
print("=" * 78)
print("GUARANTEE 5: an answer about the service is never cached")
print("=" * 78)
# Caching a rejected key would make one misconfigured minute permanent, and the retry the message
# promises the user would silently never happen.
geo._cache.clear()
router = _Router(google={"status": "REQUEST_DENIED"}, census=CENSUS_NONE)
real_get = geo._get_json
os.environ[geo.GOOGLE_KEY_ENV] = "k"
geo._get_json = router
try:
    geo.geocode("somewhere")
    first = len(router.calls)
    geo.geocode("somewhere")
    second = len(router.calls)
finally:
    geo._get_json = real_get
check(second > first, "a rejected key is retried on the next save, not cached",
      f"calls {first} then {second}")

geo._cache.clear()
router = _Router(google={"status": "ZERO_RESULTS", "results": []}, census=CENSUS_NONE)
geo._get_json = router
try:
    geo.geocode("nowhere at all")
    first = len(router.calls)
    geo.geocode("nowhere at all")
    second = len(router.calls)
finally:
    geo._get_json = real_get
    os.environ.pop(geo.GOOGLE_KEY_ENV, None)
check(second == first, "an address both providers reject IS cached, and not asked again",
      f"calls {first} then {second}")

print()
print("=" * 78)
print("GUARANTEE 6: the retained-coordinates behaviour survives the provider change")
print("=" * 78)
# This is the contract the previous geocode fix established. It is asserted here against the NEW
# provider path, because a provider swap is exactly the kind of change that quietly regresses it.
geo._cache.clear()
router = _Router(google=TimeoutError("t"), census=TimeoutError("t"))
geo._get_json = router
try:
    stored = {"lat": 38.8977, "lng": -77.0365, "formattedAddress": "Washington, DC"}
    doc = {}
    res = geo.apply_to_doc(doc, "221B Baker Street, London", previous=stored)
finally:
    geo._get_json = real_get
check(res.ok is False, "the geocode failed, as the case requires")
check(doc.get("lat") == 38.8977 and doc.get("lng") == -77.0365,
      "a failed geocode does NOT erase the coordinates it cannot replace",
      f"{doc.get('lat')},{doc.get('lng')}")
check(doc.get("geocodeStale") is True, "and the retained position is flagged as stale",
      str(doc.get("geocodeStale")))
check(doc.get("formattedAddress") == "Washington, DC",
      "carrying the address those coordinates actually matched", str(doc.get("formattedAddress")))
check(doc.get("address") == "221B Baker Street, London",
      "while the stored address is the one the user typed", str(doc.get("address")))

geo._cache.clear()
router = _Router(google=TimeoutError("t"), census=TimeoutError("t"))
geo._get_json = router
try:
    fresh = {}
    geo.apply_to_doc(fresh, "somewhere unfindable", previous={})
finally:
    geo._get_json = real_get
check("lat" not in fresh and "geocodeStale" not in fresh,
      "nothing is retained when there was nothing to retain",
      str({k: fresh.get(k) for k in ("lat", "geocodeStale")}))

print()
print("=" * 78)
print("GUARANTEE 7: the retired provider is gone")
print("=" * 78)
_src = open(geo.__file__, encoding="utf-8").read().lower()
check("nominatim.openstreetmap.org" not in _src,
      "no request is made to the retired provider's endpoint")
check(not hasattr(geo, "NOMINATIM_URL"), "and its URL constant no longer exists")

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
