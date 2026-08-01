"""
Address to coordinates, via Nominatim (OpenStreetMap).

WHY THIS EXISTS AGAIN

The Apps Script backend (v10.29) geocoded server-side whenever a saved address changed, and
assets/js/ingest.js still carries a comment saying so: "PMs never type coordinates." That backend
was replaced by this service and the geocoding did not come with it. The result was that every
project created through projectcreate had no coordinates and never would, so the only projects
that could be placed on a map were the legacy ones whose coordinates were baked into their stored
documents years ago.

Asking a PM to type a latitude was considered and rejected. Nobody knows their project's
coordinates, so the field would collect blanks and errors.

WHY NOMINATIM

No API key and no account, which matters because a key is a thing to provision, rotate and leak.
It is adequate for the facility and airport addresses this platform deals in.

Its usage policy asks for two things, and both are met here:

  A descriptive User-Agent identifying the application. Sending a generic one gets an IP blocked,
  and the policy is explicit that this is the condition of free use.

  At most one request per second. Enforced by _throttle() below rather than trusted to
  call-site discipline. It costs nothing here: geocoding runs once per project, not per render.

FOUR RULES THIS MODULE KEEPS

  1. It never raises. Every failure returns a Result carrying an `error` string. A geocoder is a
     third party on the far side of a network, and a project must not fail to save because one
     was unreachable.

  2. It never blocks indefinitely. TIMEOUT_S is short and absolute. An unreachable geocoder costs
     one timeout and then the project saves without coordinates.

  3. It caches by normalized address. The same address is never looked up twice, which respects
     the rate limit and makes a re-save of an unchanged address free.

  4. It reports failure rather than swallowing it. The caller gets a sentence to show the user.
     A project that silently has no coordinates looks identical to one the geocoder could not
     find, and those are different problems with different fixes.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

log = logging.getLogger("opus-gubernatio-server")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# The policy asks for an application name and a contact. This identifies the platform rather than
# a browser, which is the thing that matters to them.
USER_AGENT = ("OpusGubernatio/1.0 (Doctor of Engineering praxis research, "
              "The George Washington University; https://linprojectradar.onrender.com)")

# Short and absolute. A project saving is more important than a project being placed.
TIMEOUT_S = 5.0

# The policy's limit. Enforced, not assumed.
MIN_INTERVAL_S = 1.0

_lock = threading.Lock()
_last_request_at = 0.0
_cache: dict[str, "Result"] = {}


@dataclass(frozen=True)
class Result:
    """Never an exception. `error` is None on success and a displayable sentence otherwise."""
    lat: float | None = None
    lng: float | None = None
    formatted: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.lat is not None and self.lng is not None


def normalize(address: str) -> str:
    """Cache key. Case and surrounding whitespace do not make a different place."""
    return " ".join(str(address or "").split()).lower()


def _throttle() -> None:
    """Sleep just long enough that two requests are never less than MIN_INTERVAL_S apart."""
    global _last_request_at
    now = time.monotonic()
    wait = MIN_INTERVAL_S - (now - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def geocode(address: str) -> Result:
    """
    Look up an address. Returns a Result; never raises, whatever happens on the network.

    A cached answer, including a cached failure, is returned without a request. Caching the
    failure matters as much as caching the success: an address Nominatim cannot find will not be
    findable a second later either, and retrying it on every save would spend the rate limit on a
    question already answered.
    """
    key = normalize(address)
    if not key:
        return Result(error="No address was given, so this project has no location.")

    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            return cached

        _throttle()
        params = urllib.parse.urlencode({"q": address, "format": "json", "limit": 1})
        request = urllib.request.Request(f"{NOMINATIM_URL}?{params}",
                                         headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - a geocoder must never break a save
            log.warning("geocode_failed", extra={"error_type": type(exc).__name__,
                                                 "detail": str(exc)[:200]})
            # NOT cached. This is a transport failure, not an answer about the address, and the
            # next attempt may well succeed. Caching it would make one bad minute permanent.
            return Result(error="The location service could not be reached, so this project has "
                                "no map position yet. Saving the address again will retry it.")

        if not payload:
            result = Result(error="That address could not be found. A more complete address, "
                                  "with the city and state, usually resolves it.")
            _cache[key] = result
            return result

        top = payload[0]
        try:
            result = Result(lat=float(top["lat"]), lng=float(top["lon"]),
                            formatted=top.get("display_name") or address)
        except (KeyError, TypeError, ValueError):
            result = Result(error="The location service returned an address without usable "
                                  "coordinates.")
        _cache[key] = result
        return result


def apply_to_doc(doc: dict, address: str) -> Result:
    """
    Geocode `address` and write the outcome into a project document.

    Writes the same field names the frontend already reads: lat, lng, formattedAddress and
    geocodeError. assets/js/ingest.js's geocodeOutcome() was written against those and has been
    waiting for something to populate them since the Apps Script backend went away.

    On failure the coordinate fields are cleared rather than left stale, because a project whose
    address changed to somewhere unfindable must not keep pointing at where it used to be.
    """
    result = geocode(address)
    doc["address"] = address
    if result.ok:
        doc["lat"] = result.lat
        doc["lng"] = result.lng
        doc["formattedAddress"] = result.formatted
        doc.pop("geocodeError", None)
    else:
        doc.pop("lat", None)
        doc.pop("lng", None)
        doc.pop("formattedAddress", None)
        doc["geocodeError"] = result.error
    return result
