/* ============================================================
   lin-project-radar — data.js  (Phase 1)
   ------------------------------------------------------------
   NEW data model: projects start EMPTY. A project carries a
   numeric, zero-padded id ("01","02",…), a name, a sector
   (design | construction | hybrid — kept only for radar angle),
   and an EMPTY `signals` object until populated by ingest.

   There is NO fixed project count and NO hardcoded signals.
   This file only provides the first-run SEED: a couple of
   clearly-EMPTY example shells so the radar isn't blank. They
   are visibly "awaiting ingest" — never fabricated
   green/amber/red. store.js owns all reads/writes.

   BOUNDARY: synthetic demonstration data only. No real project,
   agency, employer, contractor, or vendor is referenced.
   ============================================================ */

// Sector is design | construction | hybrid (kept for radar angle only).
const LIN_SEED_PROJECTS = [
  { id: "01", name: "Example Project A", sector: "design",       reportingPeriod: "2026-06", signals: {}, fairnessSensitive: false },
  { id: "02", name: "Example Project B", sector: "construction", reportingPeriod: "2026-06", signals: {}, fairnessSensitive: false }
];

// Live in-memory arrays (managed by store.js). Empty until store init runs.
window.LIN_PROJECTS = [];
window.LIN_ARCHIVED = [];
