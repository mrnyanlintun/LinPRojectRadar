/* RUN 11, GATE 1 — THE BROWSER/SERVER ALGORITHM VERSION GUARD.

   THE PROBLEM THIS EXISTS FOR. sim.js and simulations.js carry the original browser
   implementations of the analytical modules. The server has since re-banded, guarded and in
   several cases retired what those functions compute: Run 7 closed sixteen open input domains,
   Run 10 corrected sixteen more, Run 10B closed the domain on a voting module, and Run 11 closes
   seven neighbours. None of that reached the browser copies, and none of it ever will, because
   the server is the single computational authority and a second implementation is the defect
   rather than the backup.

   So the browser copies are HISTORICAL TEST ARTEFACTS. They still run on the researcher-side
   deep dive, where re-running a model live in front of a reader is the whole point of the page.
   What they must never do is present a number as the current analysis. This file makes that
   mechanical rather than a matter of remembering.

   HOW IT WORKS. CLIENT_ALGORITHM_VERSION below is the stamp of the arithmetic actually
   implemented in sim.js and simulations.js. Every stored server result carries the
   simulation_version it was computed under. compare() returns "current" only when the two are
   the same string. They are not the same string and are not expected to become the same string;
   the honest outcome is a refusal that names both stamps, not a silent render.

   NOT A SECURITY BOUNDARY. Anyone can set window.LIN_ALLOW_CLIENT_ANALYTICS in a console. The
   guarantee is about what the shipped pages do, not about what a determined reader can force.
*/
(function () {
  "use strict";

  /* The arithmetic in sim.js and simulations.js is the pre-remediation implementation. It has
     never carried a server stamp and must not be given one: naming it after a server version
     would be the overclaim this guard exists to prevent. */
  var CLIENT_ALGORITHM_VERSION = "client-legacy-2026.07-historical";

  function serverVersionOf(project) {
    if (!project) return null;
    var v = project.simulation_version
      || (project.computed_results && project.computed_results.simulation_version)
      || (project.simulationSignals && project.simulationSignals.signal_metadata
          && project.simulationSignals.signal_metadata.simulation_version);
    return v ? String(v) : null;
  }

  /* Three outcomes, and no fourth. "current" needs both stamps present AND equal. An absent
     server stamp is "unknown", which is refused for the same reason a mismatch is: nothing here
     can tell whether it would have matched. */
  function compare(project) {
    var server = serverVersionOf(project);
    if (!server) {
      return {
        state: "unknown",
        client: CLIENT_ALGORITHM_VERSION,
        server: null,
        sentence: "These figures are recomputed in the browser by the historical client "
          + "implementation (" + CLIENT_ALGORITHM_VERSION + "). No stored analysis version was "
          + "found on this project, so they cannot be shown as the current analysis."
      };
    }
    if (server === CLIENT_ALGORITHM_VERSION) {
      return { state: "current", client: CLIENT_ALGORITHM_VERSION, server: server, sentence: "" };
    }
    return {
      state: "mismatch",
      client: CLIENT_ALGORITHM_VERSION,
      server: server,
      sentence: "These figures are recomputed in the browser by the historical client "
        + "implementation (" + CLIENT_ALGORITHM_VERSION + "). The stored analysis for this "
        + "project was computed by the server under " + server + ". They are not the same "
        + "arithmetic and the figures below are not the figures this project was scored on."
    };
  }

  function isCurrent(project) { return compare(project).state === "current"; }

  window.LinClientAlgorithmVersion = {
    CLIENT_ALGORITHM_VERSION: CLIENT_ALGORITHM_VERSION,
    serverVersionOf: serverVersionOf,
    compare: compare,
    isCurrent: isCurrent
  };
})();
