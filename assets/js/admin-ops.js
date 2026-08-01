/* ============================================================
   Opus Gubernatio — admin-ops.js (T7)
   ------------------------------------------------------------
   Project membership, assignment, completion monitoring, and export.
   Loaded ONLY on admin-ops.html — never on a participant-facing route,
   and never loads sim.js/simulations.js/categories.js/knowledge.js.

   Every call here is refused server-side for a non-admin regardless of
   this page's own gate (_require_admin, audited as admin_action_denied).
   This page's gate is a convenience for a legitimate admin, not the
   security boundary.

   BLINDING: the assignment table renders only sequence_number, scenario_id
   and status per row from a_adminassignmentlist. config_id IS present in
   that action's own response (it is the backend's already-designed
   admin-only shape) but is deliberately never rendered here — an admin
   auditing assignments does not need the condition name to do so, and
   omitting it here means this page can never become the first place a
   condition identifier leaks if it were ever reused on a route a
   participant could reach.
   ============================================================ */

(function () {
  "use strict";

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtDate(iso) {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleString(); } catch (e) { return iso; }
  }
  function token() { return window.LinAuth ? LinAuth.getToken() : null; }
  function call(action, extra) {
    return LinStore.postWithTimeout(Object.assign({ action: action, session_token: token() },
                                                   extra || {}), 60000);
  }

  var STATE = { participants: [] };

  document.addEventListener("DOMContentLoaded", boot);

  async function boot() {
    if (!token()) { showGate("You need to sign in as a ResearchAdmin to view this page."); return; }
    var who = await call("researchwhoami");
    if (!who || who.ok !== true) { showGate("Could not verify your session."); return; }
    if (who.role !== "ResearchAdmin") {
      showGate("This page is for ResearchAdmin accounts only. The server refuses every " +
        "action on this page regardless of what this message says.");
      return;
    }

    $("ao-gate").style.display = "none";
    $("ao-shell").style.display = "block";

    document.querySelectorAll(".ao-nav button").forEach(function (btn) {
      btn.addEventListener("click", function () { switchPanel(btn.dataset.panel); });
    });

    wireMembers();
    wireAssignment();
    wireExport();

    await loadParticipants();
    await loadMonitoring();
  }

  function showGate(msg) {
    $("ao-gate-message").textContent = msg;
    $("ao-gate").style.display = "block";
    $("ao-shell").style.display = "none";
  }

  function switchPanel(name) {
    document.querySelectorAll(".ao-nav button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.panel === name);
    });
    document.querySelectorAll(".ao-panel").forEach(function (p) {
      p.classList.toggle("active", p.id === "panel-" + name);
    });
  }

  async function loadParticipants() {
    var resp = await call("adminparticipantlist");
    if (!resp || resp.ok !== true) return;
    STATE.participants = resp.participants || [];
    var options = STATE.participants.map(function (p) {
      return '<option value="' + esc(p.participant_id) + '">' +
        esc(p.pseudonymous_code) + " (" + esc(p.account_type) + ")</option>";
    }).join("");
    ["ao-mem-participant", "ao-assign-participant", "ao-assignmentlist-participant"].forEach(
      function (id) { $(id).innerHTML = options; }
    );
  }

  /* ============================================================
     Part 1 — membership
     ============================================================ */

  function wireMembers() {
    $("ao-mem-load").addEventListener("click", loadMembers);
    $("ao-mem-add").addEventListener("click", addMember);
  }

  async function loadMembers() {
    var pid = $("ao-mem-project").value.trim();
    var errEl = $("ao-mem-error");
    errEl.style.display = "none";
    if (!pid) { errEl.textContent = "Enter a project id."; errEl.style.display = "block"; return; }
    var resp = await call("adminmemberlist", { id: pid });
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not load members.";
      errEl.style.display = "block";
      $("ao-mem-table").innerHTML = "";
      return;
    }
    renderMemberTable(resp.members || []);
  }

  function renderMemberTable(members) {
    if (!members.length) {
      $("ao-mem-table").innerHTML = '<p class="ao-note">No members yet.</p>';
      return;
    }
    var active = members.filter(function (m) { return m.active; });
    var revoked = members.filter(function (m) { return !m.active; });
    var rows = active.concat(revoked).map(function (m) {
      var badgeClass = m.project_role === "PM" ? "ao-badge-pm" : "ao-badge-observer";
      return "<tr" + (m.active ? "" : ' class="ao-revoked"') + ">" +
        "<td>" + esc(m.pseudonymous_code) + "</td>" +
        '<td><span class="ao-badge ' + badgeClass + '">' + esc(m.project_role) + "</span></td>" +
        "<td>" + esc(fmtDate(m.added_at)) + "</td>" +
        "<td>" + (m.active ?
          '<button class="ao-btn-secondary ao-btn ao-btn-danger" data-revoke="' +
          esc(m.member_id) + '">Revoke</button>' :
          "Revoked " + esc(fmtDate(m.revoked_at))) +
        "</td></tr>";
    }).join("");
    $("ao-mem-table").innerHTML =
      '<table class="ao-table"><thead><tr><th>Participant</th><th>Role</th>' +
      "<th>Added</th><th>Status</th></tr></thead><tbody>" + rows + "</tbody></table>";
    $("ao-mem-table").querySelectorAll("[data-revoke]").forEach(function (btn) {
      btn.addEventListener("click", function () { revokeMember(btn.dataset.revoke); });
    });
  }

  async function addMember() {
    var pid = $("ao-mem-project").value.trim();
    var errEl = $("ao-mem-error"), okEl = $("ao-mem-ok");
    errEl.style.display = "none"; okEl.style.display = "none";
    if (!pid) { errEl.textContent = "Enter a project id first."; errEl.style.display = "block"; return; }
    var resp = await call("adminmemberadd", {
      id: pid, participant_id: $("ao-mem-participant").value,
      project_role: $("ao-mem-role").value
    });
    if (!resp || resp.ok !== true) {
      // Surfaced verbatim, including B8's literal second-PM refusal — not a generic error.
      errEl.textContent = (resp && resp.error) || "Could not add member.";
      errEl.style.display = "block";
      return;
    }
    okEl.textContent = "Added as " + resp.project_role + ".";
    okEl.style.display = "block";
    await loadMembers();
  }

  async function revokeMember(memberId) {
    var resp = await call("adminmemberrevoke", { member_id: memberId });
    var errEl = $("ao-mem-error");
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not revoke member.";
      errEl.style.display = "block";
      return;
    }
    await loadMembers();
  }

  /* ============================================================
     Part 2 — assignment
     ============================================================ */

  function wireAssignment() {
    $("ao-scenario-create").addEventListener("click", createScenario);
    $("ao-assign-btn").addEventListener("click", assignParticipant);
    $("ao-assignmentlist-load").addEventListener("click", loadAssignments);
    loadScenarios();
  }

  async function loadScenarios() {
    var resp = await call("adminscenariolist");
    if (!resp || resp.ok !== true) return;
    var rows = (resp.scenarios || []).map(function (s) {
      return "<tr><td>" + esc(s.scenario_id) + "</td><td>" + esc(s.scenario_version) +
        "</td><td>" + esc(s.project_type || "—") + "</td><td>" + esc(s.status || "—") +
        "</td></tr>";
    }).join("");
    $("ao-scenario-table").innerHTML = rows ?
      '<table class="ao-table"><thead><tr><th>Scenario id</th><th>Version</th>' +
      "<th>Project type</th><th>Status</th></tr></thead><tbody>" + rows + "</tbody></table>" :
      '<p class="ao-note">No scenarios yet.</p>';
  }

  async function createScenario() {
    var version = $("ao-scenario-version").value.trim();
    if (!version) return;
    var resp = await call("adminscenariocreate", {
      scenario_version: version,
      project_type: $("ao-scenario-project-type").value.trim() || undefined
    });
    if (resp && resp.ok) {
      $("ao-scenario-version").value = "";
      $("ao-scenario-project-type").value = "";
      await loadScenarios();
    }
  }

  async function assignParticipant() {
    var errEl = $("ao-assign-error"), okEl = $("ao-assign-ok");
    errEl.style.display = "none"; okEl.style.display = "none";
    var ids = $("ao-assign-scenario-ids").value.split(",").map(function (s) { return s.trim(); })
      .filter(Boolean);
    var resp = await call("adminassign", {
      participant_id: $("ao-assign-participant").value,
      order_group: $("ao-assign-order-group").value.trim(),
      scenario_set: $("ao-assign-scenario-set").value.trim(),
      scenario_ids: ids
    });
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not assign.";
      errEl.style.display = "block";
      return;
    }
    okEl.textContent = "Assigned " + resp.assignments.length + " scenario(s) to " +
      resp.pseudonymous_code + ".";
    okEl.style.display = "block";
  }

  async function loadAssignments() {
    var pid = $("ao-assignmentlist-participant").value;
    var resp = await call("adminassignmentlist", { participant_id: pid });
    if (!resp || resp.ok !== true) {
      $("ao-assignment-table").innerHTML = '<p class="ao-error">' +
        esc((resp && resp.error) || "") + "</p>";
      return;
    }
    // Deliberately NOT rendering config_id or package_id, though the response carries them.
    // See the module docstring.
    var rows = (resp.assignments || []).map(function (a) {
      return "<tr><td>" + esc(a.sequence_number) + "</td><td>" + esc(a.scenario_id) +
        "</td><td>" + esc(a.status || "—") + "</td></tr>";
    }).join("");
    $("ao-assignment-table").innerHTML = rows ?
      '<table class="ao-table"><thead><tr><th>Sequence</th><th>Scenario</th><th>Status</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table>" :
      '<p class="ao-note">No assignments for this participant yet.</p>';
  }

  /* ============================================================
     Part 3 — completion monitoring
     ============================================================ */

  async function loadMonitoring() {
    var resp = await call("adminparticipantlist");
    if (!resp || resp.ok !== true) {
      $("ao-monitor-table").innerHTML = '<p class="ao-error">' +
        esc((resp && resp.error) || "") + "</p>";
      return;
    }
    var rows = (resp.participants || []).map(function (p) {
      var stuck = stuckHint(p);
      return "<tr><td>" + esc(p.pseudonymous_code) + "</td><td>" + esc(p.account_type) +
        "</td><td>" + (p.is_active ? "active" : "deactivated") + "</td><td>" +
        esc((p.consent && p.consent.status) || "—") + "</td><td>" +
        esc(p.current_scenario || "—") + "</td><td>" + esc(p.current_stage || "—") +
        "</td><td>" + esc(p.completion_status || "—") + "</td><td>" +
        (stuck ? '<span class="ao-note">' + esc(stuck) + "</span>" : "—") + "</td></tr>";
    }).join("");
    $("ao-monitor-table").innerHTML =
      '<table class="ao-table"><thead><tr><th>Participant</th><th>Account type</th>' +
      "<th>Active</th><th>Consent</th><th>Assigned scenario</th><th>Position</th>" +
      "<th>Completion</th><th>Stuck?</th></tr></thead><tbody>" + rows + "</tbody></table>";
  }

  // Where a participant is stuck — never a performance signal. Purely "what state, and does
  // it look like they need help," derived from stage/scenario presence, nothing about their
  // judgments or how they compare to anyone else.
  function stuckHint(p) {
    if (p.current_scenario && p.current_stage === "evidence") {
      return "assigned, has not yet submitted a preliminary judgment";
    }
    if (p.current_stage === "awaiting_reveal") {
      return "preliminary judgment submitted, awaiting reveal";
    }
    return null;
  }

  /* ============================================================
     Part 4 — export
     ============================================================ */

  function wireExport() {
    $("ao-export-create").addEventListener("click", createExport);
    loadExports();
  }

  function localToIso(value) {
    if (!value) return undefined;
    var d = new Date(value);
    return isNaN(d.getTime()) ? undefined : d.toISOString();
  }

  async function createExport() {
    var errEl = $("ao-export-error");
    errEl.style.display = "none";
    var resp = await call("adminexportcreate", {
      date_from: localToIso($("ao-export-from").value),
      date_to: localToIso($("ao-export-to").value),
      format: $("ao-export-format").value
    });
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not create export.";
      errEl.style.display = "block";
      return;
    }
    await loadExports();
  }

  async function loadExports() {
    var resp = await call("adminexportlist");
    if (!resp || resp.ok !== true) return;
    var rows = (resp.exports || []).map(function (e) {
      return "<tr><td>" + esc(e.export_id) + "</td><td>" + esc(e.format) + "</td><td>" +
        esc(e.row_count) + "</td><td><code>" + esc((e.checksum || "").slice(0, 12)) +
        "…</code></td><td>" + esc(e.destination) + "</td><td>" + esc(fmtDate(e.completed_at)) +
        '</td><td><button class="ao-btn-secondary ao-btn" data-fetch="' + esc(e.export_id) +
        '">Fetch &amp; verify</button></td></tr>';
    }).join("");
    $("ao-export-table").innerHTML = rows ?
      '<table class="ao-table"><thead><tr><th>Export id</th><th>Format</th><th>Rows</th>' +
      "<th>Checksum</th><th>Destination</th><th>Completed</th><th></th></tr></thead><tbody>" +
      rows + "</tbody></table>" : '<p class="ao-note">No exports yet.</p>';
    $("ao-export-table").querySelectorAll("[data-fetch]").forEach(function (btn) {
      btn.addEventListener("click", function () { fetchExport(btn.dataset.fetch); });
    });
  }

  async function fetchExport(exportId) {
    var resp = await call("adminexportfetch", { export_id: exportId });
    var target = $("ao-export-fetch-result");
    if (!resp || resp.ok !== true) {
      var tampered = resp && /checksum verification failed/.test(resp.error || "");
      target.innerHTML = '<div class="ao-warning" style="border-color:var(--status-red);">' +
        "<strong>" + (tampered ? "Checksum verification failed — payload withheld." :
          "Fetch failed.") + "</strong><br>" + esc((resp && resp.error) || "") + "</div>";
      return;
    }
    target.innerHTML =
      '<div class="ao-warning">' + esc(resp.review_note || "") + "</div>" +
      "<p><strong>Checksum verified.</strong> " + esc(resp.row_count) + " row(s), format " +
      esc(resp.format) + ".</p>" +
      '<textarea class="ao-input" style="width:100%; min-height:160px; font-family:var(--font-mono);" readonly>' +
      esc(resp.payload) + "</textarea>";
  }
})();
