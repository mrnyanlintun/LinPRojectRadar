"""
The browser map key, exposed to the browser because a browser map key is meant to be there.

WHY THIS IS A KEY THE BROWSER SEES, UNLIKE THE GEOCODING KEY.

`geocode.py` is a SERVER call: the platform holds `GOOGLE_GEOCODING_API_KEY`, sends it to Google
from the backend, and never lets it reach a page. Its protection is secrecy plus an IP
restriction, and its rule (`geocode.py`) is "expose the derived, credential-free fact, never the
credential."

The Maps JavaScript API is the opposite by design. The map is drawn IN THE BROWSER, so the key
travels in the `<script src=...>` URL the browser loads, and there is no way to draw the map
without the browser having it. Google's own model for this is not secrecy: it is an HTTP-referrer
restriction on the key, which makes the key usable only from the platform's own origin, so a copy
of it lifted from the page is inert anywhere else. Exposing this key is therefore correct and
expected, and it is a DIFFERENT key from the geocoding one, with a different restriction.

WHY AN ENDPOINT AND NOT config.js. `assets/js/config.js` is a static file, served untouched, and
its `LIN_GOOGLE_CLIENT_ID` is a value baked in at authoring time. The map key must come from the
deployment's environment, not from a committed file, so the browser asks the server for it at the
moment it needs a map. Read at the point of use, never held on `Settings`, so a key rotated in the
environment takes effect on the next request without a restart, exactly as `geocode.py` reads its
own key.

NO KEY IS NOT AN ERROR. A deployment with no key set is a supported state: the endpoint reports
the absence plainly and the browser keeps the flat atlas as its no-key map rather than loading
anything from Google. `present` is the fact a page can branch on without the key itself.
"""

from __future__ import annotations

import os

# The browser Maps JavaScript API key. Distinct from GOOGLE_GEOCODING_API_KEY: that one is
# server-side and IP-restricted; this one is browser-side and HTTP-referrer-restricted.
MAPS_BROWSER_KEY_ENV = "GOOGLE_MAPS_BROWSER_KEY"


def browser_maps_key() -> str:
    """The configured browser map key, or '' when none is set. Absent and empty are the same."""
    return (os.environ.get(MAPS_BROWSER_KEY_ENV) or "").strip()


def map_config() -> dict:
    """
    What the browser needs to decide whether, and how, to draw a real map.

    `present` lets a page branch without ever needing the key when there is none; `apiKey` is the
    key itself, sent only when one is set, because a browser map cannot load without it.
    """
    key = browser_maps_key()
    return {
        "provider": "google" if key else None,
        "present": bool(key),
        # Only ever the real key or None. Never a placeholder, which a page could not tell from a
        # real key and would load a broken map with.
        "apiKey": key or None,
    }
