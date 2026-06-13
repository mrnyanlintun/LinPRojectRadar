/* ============================================================
   Lin Project Radar — tz.js
   Timezone selection. Default: America/New_York (EST/EDT).
   Choice persists in localStorage. Display timestamps use the
   selected zone; audit JSON always keeps a UTC ISO timestamp
   for record integrity (see decision.js buildAuditRecord).
   ============================================================ */

(function () {
  "use strict";

  const STORE_KEY = "lin-radar-tz";
  const DEFAULT_ZONE = "America/New_York";

  const ZONES = [
    { id: "America/New_York",    label: "Eastern (EST/EDT)" },
    { id: "America/Chicago",     label: "Central (CST/CDT)" },
    { id: "America/Denver",      label: "Mountain (MST/MDT)" },
    { id: "America/Los_Angeles", label: "Pacific (PST/PDT)" },
    { id: "UTC",                 label: "UTC" }
  ];

  let current = DEFAULT_ZONE;
  try { current = localStorage.getItem(STORE_KEY) || DEFAULT_ZONE; } catch (e) {}
  if (!ZONES.some((z) => z.id === current)) current = DEFAULT_ZONE;

  function zoneAbbrev(zone, date) {
    try {
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: zone, timeZoneName: "short"
      }).formatToParts(date || new Date());
      const tzPart = parts.find((p) => p.type === "timeZoneName");
      return tzPart ? tzPart.value : zone;
    } catch (e) { return zone; }
  }

  window.LinTZ = {
    zones: ZONES,

    get() { return current; },

    set(zone) {
      if (!ZONES.some((z) => z.id === zone)) return;
      current = zone;
      try { localStorage.setItem(STORE_KEY, zone); } catch (e) {}
      document.dispatchEvent(new CustomEvent("lin:tz-changed", { detail: { zone } }));
    },

    /* Clock string, e.g. "14:03:22 EST" */
    clock(date) {
      const d = date || new Date();
      const time = new Intl.DateTimeFormat("en-US", {
        timeZone: current, hour12: false,
        hour: "2-digit", minute: "2-digit", second: "2-digit"
      }).format(d);
      return `${time} ${zoneAbbrev(current, d)}`;
    },

    /* Full display timestamp, e.g. "2026-06-12 14:03:22 EST" */
    format(dateOrIso) {
      const d = dateOrIso instanceof Date ? dateOrIso : new Date(dateOrIso);
      if (isNaN(d)) return String(dateOrIso);
      const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: current, hour12: false,
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit"
      }).format(d).replace(",", "");
      return `${parts} ${zoneAbbrev(current, d)}`;
    }
  };
})();
