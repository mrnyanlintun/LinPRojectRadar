/* ============================================================
   lin-project-radar — Apps Script paste-ready block
   Version: v10.24-reset-dedup
   ------------------------------------------------------------
   ROOT CAUSE: Code.gs had TWO `resetSignals_` definitions.
   In Apps Script / JavaScript the SECOND definition wins at
   runtime. The second (weak) version did NOT clear history,
   events, or simulationSignals — so after every "Reset signals"
   click, the Uploaded Documents table still showed prior
   uploads, CUSUM carried its stale multi-period SPI series,
   and projects mis-graded on re-ingest.

   THE WEAK DUPLICATE (the one that was active) looked like:

     function resetSignals_(body) {
       ...
       project.signalInputs = { bac:null, ... small skeleton ... };
       project.signals = {};
       project.status = 'awaiting_ingest';
       project.events = project.events || [];   // kept old events
       project.events.push({ event:'signals_reset', at:... }); // appended
       writeProjectJson_(folder, project);
       ...
     }

   HOW TO APPLY
   1. Search Code.gs for ALL occurrences of
        function resetSignals_(
      You should find TWO. Delete BOTH of them entirely
      (the good near-the-top version AND the weak one lower down).
   2. Paste the single canonical function below in their place
      (anywhere outside another function is fine — top of file
      or just above doPost is conventional).
   3. Update your apiVersion string to 'lin-project-radar-backend-v10.24-reset-dedup'
      (see PING_FIX at the bottom of this file).
   4. Deploy → Manage deployments → Edit → New version → Deploy.
   5. Confirm: GET  <your /exec URL>?action=ping
      Response should include "lin-project-radar-backend-v10.24-reset-dedup".

   WHY each field is cleared:
     signals           — EVM/MC/CUSUM/doc block; drives hasSignals() gate
     signalInputs      — null so extractSignals_ rebuilds the full skeleton
                         on the next ingest (not undefined → avoids merge bugs)
     simulationSignals — 108-module sim array (sim count pill on the list page)
     history           — CRITICAL: feeds CUSUM multi-period SPI; phantom
                         breaches appear on re-ingest if not cleared
     events            — Uploaded Documents table + overwrite log; clearing
                         it empties the table (there is no separate documents
                         array — events filtered to signals_extracted backs it)
     documents /
     uploadedDocuments /
     docs              — belt-and-suspenders if any of these arrays exist
     status            — set to 'awaiting_ingest' (matches extractSignals_ gate)
     reportingPeriod   — null so next ingest sets a fresh data date
     derivedState      — null (stale derivations from previous run)
     corpus            — NOT cleared (Technical Auditor reference store,
                         unrelated to signal ingest)
   ============================================================ */

function resetSignals_(body) {
  var id = body && body.id != null ? String(body.id).trim() : '';
  if (!id) return { ok: false, error: 'Missing project id' };

  var parent = parentFolder_();
  var folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project ' + id + ' not found' };

  var project = readProjectJson_(folder);
  if (!project) return { ok: false, error: 'project.json missing for ' + id };

  project.signals = null;
  project.signalInputs = null;          // re-ingest rebuilds the full skeleton in extractSignals_
  project.simulationSignals = null;
  project.history = [];                 // feeds CUSUM multi-period SPI — must clear
  project.events = [];                  // Uploaded Documents table + overwrite log — must clear
  ['documents', 'uploadedDocuments', 'docs'].forEach(function (k) {
    if (Object.prototype.toString.call(project[k]) === '[object Array]') project[k] = [];
  });
  project.status = 'awaiting_ingest';
  project.reportingPeriod = null;
  project.derivedState = null;
  // do NOT clear corpus (Technical Auditor store)

  writeProjectJson_(folder, project);
  return { ok: true, id: id, reset: true };
}

/* ---- PING_FIX: bump apiVersion to confirm the deploy --------
   Find the line in doGet/doPost that handles action === 'ping'
   (or 'health') and set:

     var API_VERSION = 'lin-project-radar-backend-v10.24-reset-dedup';

   or inline in the return:

     return jsonOut_({ ok: true, apiVersion: 'lin-project-radar-backend-v10.24-reset-dedup' });

   Then  GET <your /exec URL>?action=ping  must show that string.
   ------------------------------------------------------------ */
