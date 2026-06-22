/* ============================================================
   lin-project-radar — Apps Script paste-ready block
   ------------------------------------------------------------
   Fixes "Reset signals" so it FULLY clears a project back to a
   true "Awaiting ingest" state. The old reset left history +
   events behind, so re-uploaded docs stacked on stale data
   (phantom CUSUM breaches from a stale multi-period SPI series,
   and an Uploaded Documents table that kept showing old uploads).

   HOW TO APPLY
   1. In your Apps Script project (Code.gs), REPLACE your existing
      `resetSignals_` function with the one below.
   2. This version calls your existing Drive load/save helpers
      (loadProject_ / saveProject_). If yours are named differently,
      KEEP your current load/save lines and replace ONLY the
      field-clearing block (the fix is the field list, not the I/O).
   3. Bump your ping/health apiVersion string (see PING_FIX below) so
      `?action=ping` confirms the new build deployed.
   4. Deploy → Manage deployments → Edit → New version → Deploy.

   The "Uploaded Documents" table on the detail page is backed by
   project.events filtered to type === "signals_extracted" — there is
   no separate documents array — so clearing events:[] empties it.
   Do NOT clear `corpus` here: that is the Technical Auditor's
   reference store, unrelated to signal ingest.
   ============================================================ */

function resetSignals_(body) {
  var id = body && body.id != null ? String(body.id).trim() : '';
  if (!id) return { ok: false, error: 'Missing project id' };

  // Reuse your existing loader (the one your current resetSignals_ already uses).
  var project = loadProject_(id);
  if (!project) return { ok: false, error: 'Project ' + id + ' not found' };

  // ---- field-clearing block: return the project to "Awaiting ingest" ----
  project.signals = null;            // computed EVM / MC / CUSUM / doc block (drives hasSignals)
  project.signalInputs = null;       // extracted raw inputs (cpi/spi/bac/ev/ac/pv/…)
  project.simulationSignals = null;  // 108-module simulation array (sim count pill)
  project.history = [];              // CRITICAL: feeds CUSUM's multi-period SPI series
  project.events = [];               // signals_extracted (Uploaded Documents table) + overwrite log
  ['documents', 'uploadedDocuments', 'docs'].forEach(function (k) {
    if (Object.prototype.toString.call(project[k]) === '[object Array]') project[k] = [];
  });
  project.status = null;             // (or 'awaiting' if your code expects a string)
  project.reportingPeriod = null;
  project.derivedState = null;
  // ----------------------------------------------------------------------

  // Reuse your existing saver (writes project.json back to Drive).
  saveProject_(project);

  return { ok: true, id: id, reset: true };
}

/* ---- PING_FIX: bump your apiVersion so the deploy is confirmable ----
   Wherever your doGet/doPost handles action === 'ping' (or 'health'),
   change the returned apiVersion string, e.g.:

     return jsonOut_({ ok: true, apiVersion: 'v10.23-reset-fullclear' });

   Then GET  <your /exec URL>?action=ping  should show the new string.
*/
