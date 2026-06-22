/* ============================================================
   lin-project-radar — Apps Script paste-ready block
   ------------------------------------------------------------
   Adds totalFloat / consumedFloat to the field list and mapping
   in Code.gs so the backend can extract Float Consumption (Cat 2,
   module 2.5) from uploaded schedule documents.

   HOW TO APPLY
   1. In EXTRACT_FIELDS (the array of field names your extractSignals_
      function iterates over), add the two new keys:
        "totalFloat", "consumedFloat"
   2. In the FIELD_MAP (the object that tells the LLM what each field
      means), add the two new entries shown below.
   3. Bump your apiVersion string so ?action=ping confirms the deploy.
   4. Deploy → Manage deployments → Edit → New version → Deploy.

   Where to look in Code.gs:
   - Search for  EXTRACT_FIELDS  or  fieldMap  (the object literal
     that has entries like  bac: "Budget At Completion").
   - If your Code.gs names these differently (e.g. SIGNAL_FIELDS),
     find the equivalent array/object and add there.
   ============================================================ */

// ---- STEP 1 — add to your EXTRACT_FIELDS array ----
// Before (example):
//   const EXTRACT_FIELDS = ["bac", "ev", "ac", "pv", "actualPctComplete",
//                            "plannedPctComplete", "docRiskScore"];
// After:
//   const EXTRACT_FIELDS = ["bac", "ev", "ac", "pv", "actualPctComplete",
//                            "plannedPctComplete", "docRiskScore",
//                            "totalFloat", "consumedFloat"];


// ---- STEP 2 — add to your FIELD_MAP object ----
// Paste these two lines inside your existing fieldMap / FIELD_MAP object:
//
//   totalFloat:    "Total schedule float available (days). From Time-phased Schedule or Lookahead.",
//   consumedFloat: "Schedule float already consumed (days). From Schedule Update or Delay Log.",
//
// Full example of the two entries:
var FLOAT_FIELD_MAP_ADDITIONS = {
  totalFloat:    "Total schedule float available (days). From Time-phased Schedule or Lookahead.",
  consumedFloat: "Schedule float already consumed (days). From Schedule Update or Delay Log."
};


// ---- STEP 3 — bump apiVersion ----
// In your doGet/doPost ping handler, change the returned string, e.g.:
//   return jsonOut_({ ok: true, apiVersion: 'v10.24-float-fields' });


// ---- REFERENCE — what the frontend does with these fields ----
// simulations.js → runFloatConsumption(si):
//   floatRemaining   = si.totalFloat  - si.consumedFloat
//   consumptionRate  = si.consumedFloat / si.totalFloat     (0..1)
//   status: Green (rate ≤ 0.5), Yellow (≤ 0.70), Amber (≤ 0.85), Red (> 0.85)
//
// Once both fields are present in signalInputs, module 2.5 will compute
// and vote in the Cat 2 DST rollup instead of returning "No data".
