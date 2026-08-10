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
    // The "access" tab is the default-open one, so its scenario and project pickers must be
    // filled here at boot. showTab only fires on a tab CLICK, and clicking the already-active
    // tab did nothing, so these two used to render empty until the admin visited another tab and
    // came back. Fill them once now; showTab still refreshes them on later reveals.
    await loadScenarios();
    await loadProjects();
    await loadMonitoring();
  }

  // Called when an admin tab is revealed, so each tab fetches on first use rather than all
  // of them firing the moment Admin is opened.
  // Consolidated on 2026-08-02: five tabs became two. "access" carries what were Users and
  // access, Projects and assignment, and Project membership; "reporting" carries what were
  // Monitoring and Export. Both fetch on reveal, so opening Administration still does not fire
  // every request at once.
  function showTab(name) {
    if (name === "reporting") { loadMonitoring(); loadExports(); }
    if (name === "access") { loadScenarios(); loadProjects(); }
  }

  // Fill the Project membership picker from every non-archived project, so the admin chooses one
  // by name rather than typing an id they had no way to enumerate. Called at boot, on tab reveal,
  // and again after a project is created so a just-made project is immediately selectable.
  async function loadProjects() {
    var sel = $("ao-mem-project");
    if (!sel) return;
    var prior = sel.value;
    var resp = await call("adminprojectlist");
    if (!resp || resp.ok !== true) return;
    var projects = resp.projects || [];
    if (!projects.length) {
      sel.innerHTML = '<option value="" disabled selected>No projects yet</option>';
      return;
    }
    sel.innerHTML = '<option value="" disabled' + (prior ? "" : " selected") + '>Choose a project</option>'
      + projects.map(function (p) {
        return '<option value="' + esc(p.project_id) + '">' +
          esc(p.name || p.project_id) + " (" + esc(p.project_id) + ")</option>";
      }).join("");
    if (prior) sel.value = prior;   // keep the admin's current choice across a refresh
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
    // A PM is required, and refused here before the request rather than after it. Creating the
    // project first and discovering there is nobody to own it second is the state this whole
    // change exists to remove.
    var owner = $("ao-proj-owner").value;
    if (!owner) {
      errEl.textContent = "Choose who will be PM. A project cannot exist without one.";
      errEl.style.display = "block";
      return;
    }
    // ONE CALL, ONE TRANSACTION. This used to create the project and then add the PM in a
    // SECOND request, which did not work: creation already made the CALLER the PM, and the
    // follow-up was refused with "this project already has an active PM" because only one is
    // permitted. The project was created and the intended owner never got it. The server now
    // takes pm_participant_id and writes the membership row alongside the project row, so a
    // refusal leaves no project behind.
    var resp = await call("projectcreate", {
      name: name,
      sector: $("ao-proj-sector").value.trim(),
      address: $("ao-proj-address") ? $("ao-proj-address").value.trim() : "",
      pm_participant_id: owner
    });
    if (!resp || resp.ok !== true) {
      errEl.textContent = (resp && resp.error) || "Could not create the project.";
      errEl.style.display = "block";
      return;
    }
    var note = "Created " + name + ", with "
      + ($("ao-proj-owner").selectedOptions[0] || {}).text + " as PM.";
    // Same reason as the workspace: show what the geocoder matched, not what was typed.
    if (resp.geocodeError) note += " No map position: " + resp.geocodeError;
    else if (resp.formattedAddress) note += " Matched to: " + resp.formattedAddress;
    okEl.textContent = note;
    okEl.style.display = "block";
    $("ao-proj-name").value = "";
    $("ao-proj-sector").value = "";
    // The project just created must appear in the membership picker without a page reload.
    loadProjects();
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
    ["ao-mem-participant", "ao-proj-owner", "ao-assign-participant",
     "ao-assignmentlist-participant"].forEach(function (id) {
      var sel = $(id);
      if (!sel) return;
      // The PM picker used to open on "(nobody yet)", which is exactly the project this change
      // makes impossible. It now opens on a prompt that selects nothing, so an admin who does
      // not choose is stopped rather than silently creating an unowned project.
      sel.innerHTML = (id === "ao-proj-owner"
        ? '<option value="" disabled selected>Choose a PM</option>' : "") + options;
    });
  }

  /* ============================================================
     Part 1 — membership
     ============================================================ */

  function wireMembers() {
    $("ao-mem-load").addEventListener("click", loadMembers);
    $("ao-mem-add").addEventListener("click", addMember);
    if ($("ao-proj-delete")) $("ao-proj-delete").addEventListener("click", openDeleteProjectModal);
  }

  /* ---------- delete project (permanent) ----------
     Admin-only server-side (admindeleteproject, _require_admin) regardless of what this button
     does. Typed confirmation of the project id before the control enables — the same shape as
     admin.js's account delete — and deliberately not gated on window.confirm, which returns
     false in a headless or dialog-suppressing browser. */

  function openDeleteProjectModal() {
    var pid = $("ao-mem-project").value.trim();
    var errEl = $("ao-mem-error");
    errEl.style.display = "none";
    if (!pid) { errEl.textContent = "Choose a project first."; errEl.style.display = "block"; return; }
    if (!window.LinUI || !LinUI.openModal) return;
    var label = ($("ao-mem-project").selectedOptions[0] || {}).text || pid;
    LinUI.openModal({
      title: "Delete " + label + " permanently",
      mount: function (body, close) {
        body.innerHTML =
          '<p class="login-error" style="display:block">This removes the project for every ' +
            'PM and Observer on it, not just one person\'s access. Its documents, computed ' +
            'results, observations, membership and uploads are removed with it. It cannot be ' +
            'undone. If the project should be kept but set aside, use Archive instead.</p>' +
          '<label class="login-field-label">Type <strong>' + esc(pid) +
            '</strong> to confirm</label>' +
          '<input type="text" id="ao-proj-delete-confirm-input" class="ig-input">' +
          '<p id="ao-proj-delete-error" class="login-error" role="alert" style="display:none;"></p>' +
          '<button type="button" class="btn small" id="ao-proj-delete-submit" disabled>' +
            'Delete permanently</button>';

        var input = body.querySelector("#ao-proj-delete-confirm-input");
        var submitBtn = body.querySelector("#ao-proj-delete-submit");
        input.addEventListener("input", function () {
          submitBtn.disabled = input.value.trim() !== pid;
        });
        submitBtn.addEventListener("click", async function () {
          var innerErr = body.querySelector("#ao-proj-delete-error");
          innerErr.style.display = "none";
          submitBtn.disabled = true;
          var resp = await call("admindeleteproject", { project_id: pid });
          if (!resp || resp.ok !== true) {
            innerErr.textContent = (resp && resp.error) || "Could not delete this project.";
            innerErr.style.display = "block";
            submitBtn.disabled = false;
            return;
          }
          if (window.LinUI && LinUI.toast) LinUI.toast("Deleted", true);
          close();
          $("ao-mem-table").innerHTML = "";
          loadProjects();
          if (window.LinApp && LinApp.refresh) LinApp.refresh();
        });
      }
    });
  }

  async function loadMembers() {
    var pid = $("ao-mem-project").value.trim();
    var errEl = $("ao-mem-error");
    errEl.style.display = "none";
    if (!pid) { errEl.textContent = "Choose a project."; errEl.style.display = "block"; return; }
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
    if (!pid) { errEl.textContent = "Choose a project first."; errEl.style.display = "block"; return; }
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

  // The two kinds have different scopes (research_export.py's module docstring), and neither
  // the "filtered to research accounts" claim nor the meaning of the date window is true of
  // both — so both the banner and the window caption switch on the selection rather than
  // stating something once that is false half the time.
  var KIND_NOTE = {
    participant_inputs: "Filtered to research accounts server-side, always. Operational " +
      "users are never included, whatever is requested here.",
    project_health: "NOT filtered to research accounts: a project's analytical results carry " +
      "no account type of their own, so an operational project's results are exactly as " +
      "reachable here as a research project's."
  };
  var WINDOW_LABEL = {
    participant_inputs: { from: "From (start of window, over decision completion)",
                          to: "To (end of window, over decision completion)" },
    project_health: { from: "From (start of window, over when each result was computed)",
                      to: "To (end of window, over when each result was computed)" }
  };

  function updateKindNote() {
    var kind = $("ao-export-kind").value;
    $("ao-export-kind-note").textContent = KIND_NOTE[kind] || "";
    var labels = WINDOW_LABEL[kind] || WINDOW_LABEL.participant_inputs;
    $("ao-export-from-label").textContent = labels.from;
    $("ao-export-to-label").textContent = labels.to;
  }

  function wireExport() {
    $("ao-export-create").addEventListener("click", createExport);
    $("ao-export-kind").addEventListener("change", updateKindNote);
    updateKindNote();
    loadExports();
  }

  function localToIso(value) {
    if (!value) return undefined;
    var d = new Date(value);
    return isNaN(d.getTime()) ? undefined : d.toISOString();
  }

  function downloadBytes(base64, filename, mimeType) {
    var binary = atob(base64);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    var blob = new Blob([bytes], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  async function createExport() {
    var errEl = $("ao-export-error");
    errEl.style.display = "none";
    var resp = await call("adminexportcreate", {
      kind: $("ao-export-kind").value,
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
      return "<tr><td>" + esc(fmtDate(e.completed_at)) + "</td><td>" +
        esc(e.kind === "project_health" ? "Project health" : "Participant inputs") +
        "</td><td>" + esc(e.format) +
        "</td><td>" + esc(e.row_count) + "</td><td><code>" +
        esc((e.checksum || "").slice(0, 12)) + "…</code></td><td>" + esc(e.destination) +
        '</td><td><span class="ws-id" title="' + esc(e.export_id) + '">' + esc(shortId) +
        '</span></td><td><button class="ws-btn ws-btn-secondary" data-fetch="' +
        esc(e.export_id) + '">Fetch &amp; verify</button></td></tr>';
    }).join("");
    $("ao-export-table").innerHTML = rows ?
      '<table class="ws-table"><thead><tr><th>Taken</th><th>What</th><th>Format</th><th>Rows</th>' +
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
    var reviewHtml = resp.review_required
      ? '<div class="ws-warning">' + esc(resp.review_note || "") + "</div>" : "";
    var scopeHtml = '<p class="ws-note">' +
      esc(resp.research_account_filtered
        ? "Filtered to research accounts."
        : "NOT filtered to research accounts. A project's results carry no account type.") +
      "</p>";
    if (resp.format === "xlsx" && resp.payload_base64) {
      target.innerHTML = reviewHtml + scopeHtml +
        "<p><strong>Checksum verified.</strong> " + esc(resp.row_count) + " row(s), workbook.</p>";
      var fname = "export_" + (resp.kind || "participant_inputs") + "_" +
        String(exportId).slice(0, 8) + ".xlsx";
      downloadBytes(resp.payload_base64, fname,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
      return;
    }
    target.innerHTML = reviewHtml + scopeHtml +
      "<p><strong>Checksum verified.</strong> " + esc(resp.row_count) + " row(s), format " +
      esc(resp.format) + ".</p>" +
      '<textarea class="ws-input" style="width:100%; min-height:160px; font-family:var(--font-mono);" readonly>' +
      esc(resp.payload) + "</textarea>";
  }

  // T6. Exposed so app.js can boot this when the Admin section is opened and switch tabs.
  // Nothing else in the application may call into these.
  // reloadParticipants is called by admin.js after it creates an account, so the new participant
  // appears in the PM and member pickers without a full page reload.
  window.LinAdminOps = {
    boot: boot, showTab: showTab,
    reloadParticipants: function () { if (booted) return loadParticipants(); },
    reloadProjects: function () { if (booted) return loadProjects(); }
  };
})();
