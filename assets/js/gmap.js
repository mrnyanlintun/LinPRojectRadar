/* Shared Google Maps plumbing, used by BOTH the project detail map (one site, street zoom) and
   the portfolio Map view (many sites, framed). One key, one loader, one no-key answer, so the two
   surfaces cannot drift into two behaviours — which is exactly what happened when the portfolio
   kept the flat atlas while the detail page moved to Google.

   The key is a BROWSER map key, exposed on purpose and read from the deployment's environment via
   the same-origin /mapconfig endpoint (see server/app/map_config.py). Without a key nothing here
   touches any Google host: config() reports the absence and the caller shows a note.

   The container this is verified in cannot reach maps.gstatic.com (the same block that ruled
   MapLibre out), so ensure() resolves immediately when window.google.maps already exists — that is
   the seam a test stands a stub in on, so the client logic is exercised without a network map. */
(function () {
  "use strict";

  var _configPromise = null;
  var _gmapsPromise = null;

  // The /mapconfig answer, fetched once per page load. A rejected fetch resolves to the no-key
  // shape rather than rejecting, so a briefly-unreachable endpoint degrades to "no key" exactly as
  // an absent key does, instead of throwing into a section render.
  function config() {
    if (_configPromise) return _configPromise;
    _configPromise = fetch("/mapconfig", { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : { present: false, apiKey: null }; })
      .catch(function () { return { present: false, apiKey: null }; });
    return _configPromise;
  }

  // Resolves to the google.maps namespace, loading the Maps JavaScript API once if it is not
  // already present. If window.google.maps already exists it resolves immediately (the test seam).
  function ensure(apiKey) {
    if (window.google && window.google.maps) return Promise.resolve(window.google.maps);
    if (_gmapsPromise) return _gmapsPromise;
    _gmapsPromise = new Promise(function (resolve, reject) {
      var cbName = "__ogGoogleMapsReady";
      var timer = setTimeout(function () { reject(new Error("google maps load timed out")); }, 15000);
      window[cbName] = function () {
        clearTimeout(timer);
        try { delete window[cbName]; } catch (e) { window[cbName] = undefined; }
        if (window.google && window.google.maps) resolve(window.google.maps);
        else reject(new Error("google maps callback fired without the namespace"));
      };
      var s = document.createElement("script");
      s.async = true;
      s.src = "https://maps.googleapis.com/maps/api/js?key=" + encodeURIComponent(apiKey)
        + "&v=weekly&loading=async&callback=" + cbName;
      s.onerror = function () { clearTimeout(timer); reject(new Error("google maps script failed to load")); };
      document.head.appendChild(s);
    });
    return _gmapsPromise;
  }

  // The CSS variable a status is drawn from, resolved against the live theme to a colour. Same
  // mapping the atlas and globe used, kept here so the one status-colour rule outlives the atlas.
  function statusVarName(status) {
    var s = String(status || "").toLowerCase();
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return "--status-complete";
    if (s.indexOf("green") >= 0) return "--status-green";
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return "--status-yellow";
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return "--status-amber";
    if (s.indexOf("red") >= 0) return "--status-red";
    return "--status-nodata";
  }
  function statusColor(status) {
    var name = statusVarName(status);
    try {
      var v = (getComputedStyle(document.body).getPropertyValue(name) || "").trim();
      if (v) return v;
    } catch (e) { /* fall through to a neutral default */ }
    return "#6f7d70";
  }

  // Relative luminance of a #rrggbb / #rgb colour, for choosing black-or-white letter ink so the
  // colour-blind-safe status letter reads on any of the five fills.
  function inkFor(hex) {
    var h = String(hex || "").trim().replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    if (h.length !== 6) return "#0b0f14";
    var r = parseInt(h.slice(0, 2), 16) / 255, g = parseInt(h.slice(2, 4), 16) / 255, b = parseInt(h.slice(4, 6), 16) / 255;
    function lin(c) { return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
    var L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
    return L > 0.45 ? "#0b0f14" : "#ffffff";
  }

  // Test seam: the /mapconfig answer and the Maps-API load are each cached for the page's lifetime.
  // A render test that exercises both the keyed and the no-key branch in one page resets them.
  function __resetForTest() { _configPromise = null; _gmapsPromise = null; }

  window.LinGMap = {
    config: config,
    ensure: ensure,
    statusColor: statusColor,
    inkFor: inkFor,
    __resetForTest: __resetForTest
  };
})();
