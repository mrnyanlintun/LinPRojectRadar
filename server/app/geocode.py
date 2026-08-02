"""
Address to coordinates, via Google Geocoding with a US Census fallback.

WHY THIS EXISTS

The Apps Script backend geocoded server-side whenever a saved address changed, and
assets/js/ingest.js still carries a comment saying so: "PMs never type coordinates." That backend
was replaced by this service and the geocoding did not come with it, so every project created
through projectcreate had no coordinates and never would.

Asking a PM to type a latitude was considered and rejected. Nobody knows their project's
coordinates, so the field would collect blanks and errors.

WHY NOT NOMINATIM ANY MORE

It was the original provider, chosen because it needs no key. It has been replaced by decision.
Nothing here talks to it and nothing should be added back.

THE SEAM

`_PROVIDERS` is the seam, and it is a list of functions, not an abstraction layer. Each takes an
address and returns an `_Attempt`: what happened, and the coordinates if it found any. `geocode()`
walks the list in order and stops at the first provider that answers with a position. Adding a
third provider is appending a function to that list; it is not a plugin system, a registry, or a
base class, because two providers do not justify one and a third would not either.

  Google    primary. Needs GOOGLE_GEOCODING_API_KEY. Worldwide.
  Census    fallback. No key, no account, United States addresses only.

The fallback runs when Google finds nothing or cannot be reached, including when its key is absent
or rejected. A deployment with no key still geocodes US addresses, which is most of them here, and
says plainly that it is running without the primary provider.

FOUR RULES THIS MODULE KEEPS, UNCHANGED FROM THE PREVIOUS PROVIDER

  1. It never raises. Every failure returns a Result carrying an `error` string. A geocoder is a
     third party on the far side of a network, and a project must not fail to save because one
     was unreachable.

  2. It never blocks indefinitely. TIMEOUT_S is short and absolute, and it is per provider, so the
     worst case is one timeout per provider rather than an unbounded wait.

  3. It caches by normalized address, but ONLY when the answer is about the address. A position,
     or every provider agreeing the address is not findable, is cached. A timeout, an exhausted
     quota, a rejected key and an absent key are NOT cached: they are facts about the service or
     the deployment, and caching one would make a bad minute permanent.

  4. It reports failure rather than swallowing it, and it distinguishes the failures. "Not found",
     "ambiguous", "quota exhausted", "key rejected" and "not configured" are different problems
     with different fixes, and a user who cannot tell them apart cannot act on any of them.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass

log = logging.getLogger("opus-gubernatio-server")

# Read at the point of use, never held on Settings. Same rule the service already follows for
# ANTHROPIC_API_KEY: expose the derived, credential-free fact, never the credential.
GOOGLE_KEY_ENV = "GOOGLE_GEOCODING_API_KEY"

GOOGLE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

# The Census benchmark to resolve against. Pinned rather than left to the service's default so an
# upstream default change cannot silently move every coordinate this platform stores.
CENSUS_BENCHMARK = "Public_AR_Current"

# Short and absolute, per provider. A project saving is more important than a project being placed.
TIMEOUT_S = 5.0

_lock = threading.Lock()
_cache: dict[str, "Result"] = {}

# What a provider attempt concluded. These are distinguished because a user can act on the
# difference: NOT_FOUND means fix the address, QUOTA and UNAVAILABLE mean try later, REJECTED and
# NOT_CONFIGURED mean fix the deployment.
FOUND = "found"
AMBIGUOUS = "ambiguous"      # a position, but more than one candidate or a partial match
NOT_FOUND = "not_found"      # the provider answered, and the answer is "no such address"
UNAVAILABLE = "unavailable"  # transport, timeout, or the provider's own error
QUOTA = "quota"
REJECTED = "rejected"        # the key was refused
NOT_CONFIGURED = "not_configured"

# Outcomes that are an answer ABOUT THE ADDRESS rather than about the service. Only these are
# safe to cache.
_DEFINITIVE = frozenset({FOUND, AMBIGUOUS, NOT_FOUND})


@dataclass(frozen=True)
class Result:
    """Never an exception. `error` is None on success and a displayable sentence otherwise."""
    lat: float | None = None
    lng: float | None = None
    formatted: str | None = None
    error: str | None = None
    # Which provider supplied the position, for the report and the logs. None on failure.
    provider: str | None = None
    # True when the provider returned a position it is not certain about: several candidates, or
    # a partial match. The position is still used; the matched address shown back to the user is
    # how they check it, which is why that has always been surfaced.
    ambiguous: bool = False

    @property
    def ok(self) -> bool:
        return self.lat is not None and self.lng is not None


@dataclass(frozen=True)
class _Attempt:
    """One provider's answer. Internal: callers see Result."""
    provider: str
    outcome: str
    lat: float | None = None
    lng: float | None = None
    formatted: str | None = None
    detail: str = ""


def normalize(address: str) -> str:
    """Cache key. Case and surrounding whitespace do not make a different place."""
    return " ".join(str(address or "").split()).lower()


def _get_json(url: str) -> dict:
    """One HTTP GET returning parsed JSON. Raises; callers convert it to an _Attempt."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return json.loads(response.read().decode("utf-8"))


# --------------------------------------------------------------------------- providers


def _google(address: str) -> _Attempt:
    """
    Google Geocoding API.

    Every documented status is handled by name. Treating anything non-200 as one undifferentiated
    failure is what makes a rejected key look like an address problem, which sends whoever is
    debugging it to the wrong place.
    """
    key = (os.environ.get(GOOGLE_KEY_ENV) or "").strip()
    if not key:
        # Inert, and says so. No request is made, so an unconfigured deployment costs nothing and
        # leaks nothing.
        return _Attempt("google", NOT_CONFIGURED,
                        detail="the address service is not configured on this deployment")

    params = urllib.parse.urlencode({"address": address, "key": key})
    try:
        payload = _get_json(f"{GOOGLE_URL}?{params}")
    except Exception as exc:  # noqa: BLE001 - a geocoder must never break a save
        log.warning("geocode_provider_failed", extra={"provider": "google",
                                                      "error_type": type(exc).__name__,
                                                      "detail": str(exc)[:200]})
        return _Attempt("google", UNAVAILABLE, detail="the address service could not be reached")

    status = str(payload.get("status") or "")
    # error_message is Google's own explanation and is the useful half of a REQUEST_DENIED. It is
    # logged, never shown: it can name the key restriction that refused the request.
    if status not in ("OK", "ZERO_RESULTS"):
        log.warning("geocode_provider_status",
                    extra={"provider": "google", "status": status,
                           "detail": str(payload.get("error_message"))[:200]})

    if status == "OK":
        results = payload.get("results") or []
        if not results:
            return _Attempt("google", NOT_FOUND)
        top = results[0]
        loc = ((top.get("geometry") or {}).get("location") or {})
        try:
            lat = float(loc["lat"])
            lng = float(loc["lng"])
        except (KeyError, TypeError, ValueError):
            return _Attempt("google", UNAVAILABLE,
                            detail="the address service returned a match without coordinates")
        # More than one candidate, or Google itself flagging the match as partial. Both mean the
        # position is a best guess rather than an identification.
        unsure = len(results) > 1 or bool(top.get("partial_match"))
        return _Attempt("google", AMBIGUOUS if unsure else FOUND,
                        lat=lat, lng=lng,
                        formatted=top.get("formatted_address") or address)

    if status == "ZERO_RESULTS":
        return _Attempt("google", NOT_FOUND)
    if status in ("OVER_QUERY_LIMIT", "OVER_DAILY_LIMIT"):
        return _Attempt("google", QUOTA,
                        detail="the address service has reached its usage limit for now")
    if status == "REQUEST_DENIED":
        return _Attempt("google", REJECTED,
                        detail="the address service rejected this deployment's credentials")
    # INVALID_REQUEST, UNKNOWN_ERROR, and anything a future API version introduces.
    return _Attempt("google", UNAVAILABLE, detail="the address service returned an error")


def _census(address: str) -> _Attempt:
    """
    United States Census Geocoder. No key, no account, US addresses only.

    It answers only for addresses it can match to its own reference set, so a non-US address is a
    NOT_FOUND here rather than an error. That is why the composed message below never claims an
    address does not exist on the strength of Census alone.
    """
    params = urllib.parse.urlencode({"address": address, "benchmark": CENSUS_BENCHMARK,
                                     "format": "json"})
    try:
        payload = _get_json(f"{CENSUS_URL}?{params}")
    except Exception as exc:  # noqa: BLE001
        log.warning("geocode_provider_failed", extra={"provider": "census",
                                                      "error_type": type(exc).__name__,
                                                      "detail": str(exc)[:200]})
        return _Attempt("census", UNAVAILABLE,
                        detail="the fallback address service could not be reached")

    matches = ((payload.get("result") or {}).get("addressMatches") or [])
    if not matches:
        return _Attempt("census", NOT_FOUND)
    top = matches[0]
    coords = top.get("coordinates") or {}
    try:
        # Census names them x and y, and they are longitude and latitude in that order.
        lng = float(coords["x"])
        lat = float(coords["y"])
    except (KeyError, TypeError, ValueError):
        return _Attempt("census", UNAVAILABLE,
                        detail="the fallback address service returned a match without coordinates")
    unsure = len(matches) > 1
    return _Attempt("census", AMBIGUOUS if unsure else FOUND,
                    lat=lat, lng=lng, formatted=top.get("matchedAddress") or address)


# THE SEAM. Order is precedence. Append to add a provider.
_PROVIDERS = (_google, _census)


# --------------------------------------------------------------------------- composition


_RETRY_TAIL = " Saving the address again will retry it."
_CHECK_TAIL = (" Try the street address OR the facility name, not both together, with the city "
               "and state. Check the result on the map before relying on it.")


def _compose_error(attempts: list[_Attempt]) -> str:
    """
    One sentence naming what actually happened, not a generic failure.

    COMPOSED OPERATIONAL WORDING, FLAGGED FOR REVIEW. These are not liability or consent
    statements, but they are what a user reads when a location does not resolve, and they were
    written here rather than approved.
    """
    outcomes = {a.outcome for a in attempts}

    # Every provider that ran gave a real answer about the address, and the answer was no.
    if outcomes and outcomes <= {NOT_FOUND}:
        return "That address could not be found." + _CHECK_TAIL

    # The primary is misconfigured or refusing. Name it, because nobody can fix what they cannot
    # see, and it is a deployment problem rather than the user's address being wrong.
    google = next((a for a in attempts if a.provider == "google"), None)
    if google is not None and google.outcome in (REJECTED, NOT_CONFIGURED, QUOTA):
        others_found_nothing = any(a.outcome == NOT_FOUND for a in attempts if a is not google)
        lead = google.detail[0].upper() + google.detail[1:] + "."
        if others_found_nothing:
            # Census ran and said no. It only covers the United States, so this is not proof the
            # address does not exist, and the message must not claim that it is.
            return (lead + " A United States address service was tried instead and did not "
                    "match this address." + _RETRY_TAIL)
        return lead + " The address has not been matched yet." + _RETRY_TAIL

    # Everything else: reachability.
    return ("The location service could not be reached, so this address has not been matched "
            "yet." + _RETRY_TAIL)


def geocode(address: str) -> Result:
    """
    Look up an address through the provider seam. Returns a Result; never raises.

    A cached answer, including a cached not-found, is returned without a request. Caching the
    not-found matters as much as caching the position: an address no provider can find will not
    become findable a second later, and retrying it on every save spends quota on a question
    already answered.

    A service failure is never cached. See rule 3 in the module docstring.
    """
    key = normalize(address)
    if not key:
        return Result(error="No address was given, so this project has no location.")

    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            return cached

        attempts: list[_Attempt] = []
        for provider in _PROVIDERS:
            attempt = provider(address)
            attempts.append(attempt)
            if attempt.outcome in (FOUND, AMBIGUOUS):
                result = Result(lat=attempt.lat, lng=attempt.lng,
                                formatted=attempt.formatted or address,
                                provider=attempt.provider,
                                ambiguous=attempt.outcome == AMBIGUOUS)
                _cache[key] = result
                return result

        result = Result(error=_compose_error(attempts))
        # Cache only when every provider gave an answer about the address rather than about
        # itself. A quota, a rejected key or a timeout must be retried on the next save.
        if attempts and all(a.outcome in _DEFINITIVE for a in attempts):
            _cache[key] = result
        return result


def apply_to_doc(doc: dict, address: str, previous: dict | None = None) -> Result:
    """
    Geocode `address` and write the outcome into a project document.

    Writes the same field names the frontend already reads: lat, lng, formattedAddress and
    geocodeError. assets/js/ingest.js's geocodeOutcome() was written against those.

    A FAILED GEOCODE DOES NOT ERASE COORDINATES IT CANNOT REPLACE.

    This used to clear lat/lng/formattedAddress on every failure, reasoning that a project whose
    address changed to somewhere unfindable must not keep pointing at where it used to be. The
    reasoning was sound about the pin and wrong about the data: the geocoder was unreachable from
    this deployment, so in practice EVERY address edit destroyed the project's location and
    replaced it with nothing. A transport failure is not an answer about the address; it is the
    absence of one, and discarding stored data on the strength of it is the same silent-loss shape
    the rest of this codebase refuses.

    So the coordinates stay, and `geocodeStale` marks them as belonging to a previous address.
    Every surface that renders a location reads that flag and says so rather than presenting an
    old match as the current one.

    Nothing is retained when there was nothing to retain: a project geocoding for the first time
    still ends with no coordinates and a geocodeError.

    `previous` is the STORED document, when the caller has one. It matters because w_save replaces
    the stored doc wholesale with the client's copy, so reading the retained coordinates out of
    `doc` alone would trust a client that may not have sent them. Defaults to `doc` for callers
    building a document from nothing.
    """
    result = geocode(address)
    doc["address"] = address
    if result.ok:
        doc["lat"] = result.lat
        doc["lng"] = result.lng
        doc["formattedAddress"] = result.formatted
        doc.pop("geocodeError", None)
        doc.pop("geocodeStale", None)
        return result

    prior = previous if previous is not None else doc
    doc["geocodeError"] = result.error
    if prior.get("lat") is not None and prior.get("lng") is not None:
        # Retained, and flagged. formattedAddress is carried with the coordinates deliberately: it
        # names the address they actually matched, which is precisely what a reader needs in order
        # to see that it is not the address now stored in doc["address"].
        doc["lat"] = prior.get("lat")
        doc["lng"] = prior.get("lng")
        if prior.get("formattedAddress") is not None:
            doc["formattedAddress"] = prior.get("formattedAddress")
        doc["geocodeStale"] = True
    else:
        doc.pop("lat", None)
        doc.pop("lng", None)
        doc.pop("formattedAddress", None)
        doc.pop("geocodeStale", None)
    return result
