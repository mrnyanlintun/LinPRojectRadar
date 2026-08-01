/* ============================================================
   Opus Gubernatio — admin-ops.js (T7)
   ------------------------------------------------------------
   Project membership, completion monitoring, and export. T6 folded
   admin-ops.html into index.html, so these are now tabs of the single
   Admin section rather than a second admin page a word apart in name.

   It calls nothing from sim.js/simulations.js/categories.js/knowledge.js,
   and — as with workspace.js — that is now a rule this file keeps rather
   than one its page kept for it.

   Every call here is refused server-side for a non-admin (_require_admin,
   audited as admin_action_denied). The role check in boot() is a
   convenience for a legitimate admin, not the security boundary; the
   section being hidden is not one either.

   ASSIGNMENT IS WITHDRAWN (T6 Part C) — see the note further down. The
   blinding rule that used to live here went with it: the assignment table
   was careful never to render config_id, and with no assignment table
   there is nothing left to blind. B3's backend actions are untouched.
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

  // T6. admin-ops.html is gone; these are tabs inside the Admin section of the main
  // application. There is no gate here any more — the section itself is admin-only (hidden by
  // auth.js's setAdminNavVisible) and, far more importantly, every action below is refused
  // server-side by _require_admin regardless of what this file does. The old client-side role
  // check was always a convenience and never the guard.
  var booted = false;

  async function boot() {
    if (booted) return;
    var who = await call("researchwhoami");
    if (!who || who.ok !== true || who.role !== "ResearchAdmin") return;
    booted = true;

    wireMembers();
    wireProjects();
    wireExport();

    await loadParticipants();
    await loadMonitoring();
  }

  // Called when an admin tab is revealed, so each tab fetches on first use rather than all
  // of them firing the moment Admin is opened.
  function showTab(name) {
    if (name === "monitoring") loadMonitoring();
    if (name === "export") loadExports();
    if (name === "projects") loadScenarios();
  }

  /* ============================================================
     Projects and assignment (T6)

     These two live on one tab because they are one act. The researcher creates a participant's
     project and the assignment that lets them decide on it in the same sitting; either alone
     leaves a state the platform cannot use.
     ============================================================ */

  function wireProjects() {
    $("ao-proj-create").addEventListener("click", createProject);
    $("ao-assign-btn").addEventListener("click", assignParticipant);
    $("ao-assignmentlist-load").addEventListener("click", loadAssignments);
  }

  async function loadScenarios() {
    var resp = await call("adminscenariolist");
    if (!resp || resp.ok !== true) return;
    var sel = $("ao-assign-scenario");
    if (!sel) return;
    // The scenario is named by its version and project type, never by its identifier — an id is
    // not a name, and an admin choosing between scenarios is choosing between descriptions.
    sel.innerHTML = (resp.scenarios || []).map(function (s) {
      var label = (s.scenario_version || "unnamed")
        + (s.project_type ? " · " + s.project_type : "")
        + (s.period_count ? " · " + s.period_count + " period(s)" : "");
      return '<option value="' + esc(s.scenario_id) + '">' + esc(label) + "</option>";
    }).join("");
  }

  async function createProject() {
    var errEl = $("ao-proj-error"), okEl = $("ao-proj-ok");
    errEl.style.display = "none"; okEl.style.display = "none";
    var name = $("ao-proj-name").value.trim();
    if (!name) {
      errEl.textContent = "A project name is required.";
      errEl.style.display = "block";
      return;
    }
    var resp = await call("projectcreate", { name: name, sector: $("ao-proj-sector").value.trim() });
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not create the project.";
      errEl.style.display = "block";
      return;
    }
    var pid = resp.project_id || resp.id;
    var owner = $("ao-proj-owner").value;
    var note = "Created " + name + ".";
    if (owner) {
      // Reported separately: a project that was created but could not be assigned is a state the
      // admin has to know about, not one to hide behind a single success message.
      var m = await call("adminmemberadd", { id: pid, participant_id: owner, project_role: "PM" });
      note += (m && m.ok === true)
        ? " Assigned as PM."
        : " NOT assigned: " + ((m && m.error) || "membership failed");
    }
    okEl.textContent = note;
    okEl.style.display = "block";
    $("ao-proj-name").value = "";
    $("ao-proj-sector").value = "";
  }

  async function assignParticipant() {
    var errEl = $("ao-assign-error"), okEl = $("ao-assign-ok");
    errEl.style.display = "none"; okEl.style.display = "none";
    var scenario = $("ao-assign-scenario").value;
    if (!scenario) {
      errEl.textContent = "Create a scenario before assigning anyone to one.";
      errEl.style.display = "block";
      return;
    }
    var resp = await call("adminassign", {
      participant_id: $("ao-assign-participant").value,
      order_group: $("ao-assign-order-group").value.trim(),
      scenario_set: $("ao-assign-scenario-set").value.trim(),
      scenario_ids: [scenario]
    });
    if (!resp || resp.ok !== true) {
      // Surfaced verbatim. B3 refuses an assignment whose condition sequence is not frozen, and
      // an admin needs that sentence rather than a generic failure.
      errEl.textContent = (resp && resp.error) || "Could not assign.";
      errEl.style.display = "block";
      return;
    }
    okEl.textContent = "Assigned " + (resp.pseudonymous_code || "") + ".";
    okEl.style.display = "block";
  }

  async function loadAssignments() {
    var resp = await call("adminassignmentlist",
                          { participant_id: $("ao-assignmentlist-participant").value });
    var target = $("ao-assignment-table");
    if (!resp || resp.ok !== true) {
      target.innerHTML = '<p class="ws-note">' + esc((resp && resp.error) || "Could not load.") + "</p>";
      return;
    }
    var rows = (resp.assignments || []).map(function (a) {
      // sequence_number and status only. config_id IS in this response — it names the condition —
      // and is deliberately never rendered, which is the one part of the old blinding rule that
      // still has something to protect.
      return "<tr><td>" + esc(a.sequence_number) + "</td><td>" + esc(a.status || "—") + "</td></tr>";
    }).join("");
    target.innerHTML = rows
      ? '<table class="ws-table"><thead><tr><th>Order</th><th>Status</th></tr></thead><tbody>'
        + rows + "</tbody></table>"
      : '<p class="ws-note">No assignments for this participant yet.</p>';
  }

  async function loadParticipants() {
    var resp = await call("adminparticipantlist");
    if (!resp || resp.ok !== true) return;
    STATE.participants = resp.participants || [];
    var options = STATE.participants.map(function (p) {
      return '<option value="' + esc(p.participant_id) + '">' +
        esc(p.pseudonymous_code) + " (" + esc(p.account_type) + ")</option>";
    }).join("");
    // T6 Part C: only the membership picker remains. The assignment pickers belonged to the
    // scenario-and-condition model, whose interface is withdrawn — see the note at the foot of
    // this file about why B3's backend is deliberately left intact.
    ["ao-mem-participant", "ao-proj-owner", "ao-assign-participant",
     "ao-assignmentlist-participant"].forEach(function (id) {
      var sel = $(id);
      if (!sel) return;
      // The PM picker on project creation is optional, so it alone gets an empty first option.
      sel.innerHTML = (id === "ao-proj-owner" ? '<option value="">(nobody yet)</option>' : "")
        + options;
    });
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
      $("ao-mem-table").innerHTML = '<p class="ws-note">No members yet.</p>';
      return;
    }
    var active = members.filter(function (m) { return m.active; });
    var revoked = members.filter(function (m) { return !m.active; });
    var rows = active.concat(revoked).map(function (m) {
      var badgeClass = m.project_role === "PM" ? "ws-badge-pm" : "ws-badge-observer";
      return "<tr" + (m.active ? "" : ' class="ws-revoked"') + ">" +
        "<td>" + esc(m.pseudonymous_code) + "</td>" +
        '<td><span class="ws-badge ' + badgeClass + '">' + esc(m.project_role) + "</span></td>" +
        "<td>" + esc(fmtDate(m.added_at)) + "</td>" +
        "<td>" + (m.active ?
          '<button class="ws-btn ws-btn-secondary" data-revoke="' +
          esc(m.member_id) + '">Revoke</button>' :
          "Revoked " + esc(fmtDate(m.revoked_at))) +
        "</td></tr>";
    }).join("");
    $("ao-mem-table").innerHTML =
      '<table class="ws-table"><thead><tr><th>Participant</th><th>Role</th>' +
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
     Part 2 — scenario assignment: WITHDRAWN (T6 Part C)
     ------------------------------------------------------------
     This held B3's model: pre-authored scenarios, and participants assigned to scenario sets
     and condition sequences. The design moved on — participants create their own projects,
     and there are no conditions left to counterbalance — so an interface for assigning someone
     to a scenario set no longer describes anything the platform does.

     The UI is withdrawn. B3's BACKEND IS DELIBERATELY UNTOUCHED: adminscenariocreate,
     adminscenariolist, adminassign and adminassignmentlist all still exist, still dispatch,
     and are still covered by test_assignment_blinding. The research design remains subject to
     the researcher's advisor, and deleting a tested backend to tidy a screen would make a
     reversible presentation decision into an irreversible one.

     Project membership (Part 1 above) is what replaced it, and is what the platform needs:
     an admin puts a person on a project as PM or Observer.
     ============================================================ */
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
        (stuck ? '<span class="ws-note">' + esc(stuck) + "</span>" : "—") + "</td></tr>";
    }).join("");
    $("ao-monitor-table").innerHTML =
      '<table class="ws-table"><thead><tr><th>Participant</th><th>Account type</th>' +
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
      // T6 Part E. The export id was the first and most prominent column, which made an
      // internal key the identity of the row. What identifies an export to a human is when it
      // was taken and how much it holds; the id stays only as truncated metadata, because an
      // operator matching a file against this table still needs it.
      var shortId = String(e.export_id || "");
      if (shortId.length > 10) shortId = shortId.slice(0, 8) + "…";
      return "<tr><td>" + esc(fmtDate(e.completed_at)) + "</td><td>" + esc(e.format) +
        "</td><td>" + esc(e.row_count) + "</td><td><code>" +
        esc((e.checksum || "").slice(0, 12)) + "…</code></td><td>" + esc(e.destination) +
        '</td><td><span class="ws-id" title="' + esc(e.export_id) + '">' + esc(shortId) +
        '</span></td><td><button class="ws-btn ws-btn-secondary" data-fetch="' +
        esc(e.export_id) + '">Fetch &amp; verify</button></td></tr>';
    }).join("");
    $("ao-export-table").innerHTML = rows ?
      '<table class="ws-table"><thead><tr><th>Taken</th><th>Format</th><th>Rows</th>' +
      "<th>Checksum</th><th>Destination</th><th>Reference</th><th></th></tr></thead><tbody>" +
      rows + "</tbody></table>" : '<p class="ws-note">No exports yet.</p>';
    $("ao-export-table").querySelectorAll("[data-fetch]").forEach(function (btn) {
      btn.addEventListener("click", function () { fetchExport(btn.dataset.fetch); });
    });
  }

  async function fetchExport(exportId) {
    var resp = await call("adminexportfetch", { export_id: exportId });
    var target = $("ao-export-fetch-result");
    if (!resp || resp.ok !== true) {
      var tampered = resp && /checksum verification failed/.test(resp.error || "");
      target.innerHTML = '<div class="ws-warning" style="border-color:var(--status-red);">' +
        "<strong>" + (tampered ? "Checksum verification failed. The payload was withheld." :
          "Fetch failed.") + "</strong><br>" + esc((resp && resp.error) || "") + "</div>";
      return;
    }
    target.innerHTML =
      '<div class="ws-warning">' + esc(resp.review_note || "") + "</div>" +
      "<p><strong>Checksum verified.</strong> " + esc(resp.row_count) + " row(s), format " +
      esc(resp.format) + ".</p>" +
      '<textarea class="ws-input" style="width:100%; min-height:160px; font-family:var(--font-mono);" readonly>' +
      esc(resp.payload) + "</textarea>";
  }

  // T6. Exposed so app.js can boot this when the Admin section is opened and switch tabs.
  // Nothing else in the application may call into these.
  window.LinAdminOps = { boot: boot, showTab: showTab };
})();
