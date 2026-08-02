/* ============================================================
   Opus Gubernatio — files.js
   ------------------------------------------------------------
   The Files tab: the project's Arora directory tree, the files in
   a folder, and a preview.

   THE PM NEVER CHOOSES A DESTINATION. The platform files each
   document from its detected type, so this surface exists to make
   that visible and correctable rather than to ask: every row shows
   the folder it landed in and its filing class, anything the
   platform was unsure about carries a review mark, and the PM can
   move it.

   NO RENDERER IS ATTEMPTED for a format the browser cannot show.
   CAD and Revit are out of scope, and the server says which case
   a file is (`preview` on each row), so an unsupported format
   shows the message and a download rather than an empty frame
   that reads as broken.

   EXTRACTION FAILURES ARE NOT HANDLED HERE. They already render
   per-file, verbatim, in the upload panel's existing dialog; a
   second error surface for the same event would be a second thing
   to keep in step.
   ============================================================ */
var LinFiles = (function () {
  "use strict";

  var STATE = { tree: [], files: [], folder: null, selected: null, occupiedOnly: true };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  // Defensive about getToken specifically, not just about LinAuth. A caller that has stubbed
  // LinAuth without that method (the render harness does) must get null rather than a
  // TypeError: a preview that cannot build a URL should render nothing, never take the page
  // down with it.
  function token() {
    return (window.LinAuth && typeof LinAuth.getToken === "function")
      ? LinAuth.getToken() : null;
  }
  function call(action, extra) {
    return LinStore.postWithTimeout(
      Object.assign({ action: action, session_token: token() }, extra || {}), 60000);
  }
  function projectId() {
    var sel = $("ws-files-project");
    return sel ? sel.value : null;
  }

  /* ---------- load ---------- */

  async function mount() {
    var pid = projectId();
    if (!pid) return;
    var err = $("ws-files-error");
    if (err) err.style.display = "none";
    var resp = await call("projectfiles", { id: pid, folder: STATE.folder || undefined });
    if (!resp || resp.ok !== true) {
      if (err) {
        err.textContent = (resp && resp.error) || "Could not load the project files.";
        err.style.display = "block";
      }
      return;
    }
    STATE.tree = resp.tree || [];
    STATE.files = resp.files || [];
    STATE.reviewCount = resp.review_count || 0;
    STATE.unsupportedMessage = resp.unsupported_preview_message || "";
    STATE.totalFiles = resp.total_files || 0;
    paintTree();
    paintList();
    wireDrop();
  }

  /* ---------- tree ---------- */

  function nodeHtml(node) {
    if (STATE.occupiedOnly && !node.occupied) return "";
    var kids = (node.children || []).map(nodeHtml).join("");
    var cls = "fx-node" + (node.occupied ? " fx-node-occupied" : "")
      + (STATE.folder === node.path ? " fx-node-selected" : "")
      + (node.placeholder ? " fx-node-pattern" : "");
    // A placeholder is a PATTERN, not a folder: it describes the shape of the folders filing
    // creates ("YYYY-MM-DD SITE OBS #"), so it is shown greyed and is not selectable.
    var label = node.placeholder
      ? '<span class="fx-node-label fx-pattern" title="A naming pattern, not a folder">'
        + esc(node.name) + "</span>"
      : '<button type="button" class="fx-node-label" data-folder="' + esc(node.path) + '">'
        + esc(node.name) + "</button>";
    return '<li class="' + cls + '">' + label
      + (kids ? '<ul class="fx-children">' + kids + "</ul>" : "") + "</li>";
  }

  function paintTree() {
    var root = $("ws-files-tree");
    if (!root) return;
    var body = STATE.tree.map(nodeHtml).join("");
    root.innerHTML = body
      ? '<ul class="fx-tree-root">' + body + "</ul>"
      : '<p class="ws-note">No documents have been filed yet. Untick "Only folders in use" to '
        + "see the whole Arora directory template.</p>";
    root.querySelectorAll("[data-folder]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        STATE.folder = btn.dataset.folder;
        STATE.selected = null;
        mount();
      });
    });
  }

  /* ---------- file list ---------- */

  function paintList() {
    var title = $("ws-files-list-title");
    if (title) {
      title.textContent = STATE.folder ? STATE.folder : "All files";
    }
    var badge = $("ws-files-review-badge");
    if (badge) {
      if (STATE.reviewCount > 0) {
        badge.textContent = STATE.reviewCount + " to review";
        badge.style.display = "";
      } else {
        badge.style.display = "none";
      }
    }
    var host = $("ws-files-list");
    if (!host) return;
    if (!STATE.files.length) {
      host.innerHTML = '<p class="ws-note">'
        + (STATE.folder ? "Nothing filed in this folder yet."
                        : "No documents have been filed for this project yet.") + "</p>";
      return;
    }
    var rows = STATE.files.map(function (f) {
      var flags = [];
      if (f.needs_filing_review) {
        flags.push('<span class="fx-flag fx-flag-review">Check filing</span>');
      }
      if (f.superseded) {
        flags.push('<span class="fx-flag">Superseded</span>');
      }
      // data-label on each cell is read by a mobile-only CSS rule (radar.css, the 640px
      // block) that stacks this table into cards rather than leaving it to overflow or to a
      // sideways scroll. The desktop table ignores the attribute entirely; it costs nothing
      // there. The File cell carries no label because it is the row's own heading, not a field.
      return "<tr>"
        + '<td><button type="button" class="fx-filename" data-doc="' + esc(f.document_id)
          + '">' + esc(f.filename) + "</button>" + flags.join("") + "</td>"
        + '<td data-label="State">' + esc(f.filing_label || "") + "</td>"
        + '<td class="fx-version" data-label="Version">v' + esc(f.version) + "</td>"
        + '<td data-label="Period">' + esc(f.period == null ? "" : "P" + f.period) + "</td>"
        + '<td class="fx-folder" data-label="Folder">' + esc(f.folder_path || "") + "</td>"
        + '<td><button type="button" class="ws-btn ws-btn-secondary fx-move" data-move="'
          + esc(f.document_id) + '">Move</button></td>'
        + "</tr>";
    }).join("");
    host.innerHTML = '<table class="ws-table fx-table"><thead><tr>'
      + "<th>File</th><th>State</th><th>Version</th><th>Period</th><th>Folder</th><th></th>"
      + "</tr></thead><tbody>" + rows + "</tbody></table>";

    host.querySelectorAll("[data-doc]").forEach(function (btn) {
      btn.addEventListener("click", function () { showPreview(btn.dataset.doc); });
    });
    host.querySelectorAll("[data-move]").forEach(function (btn) {
      btn.addEventListener("click", function () { openMove(btn.dataset.move); });
    });
  }

  /* ---------- preview ---------- */

  function fileById(id) {
    return STATE.files.filter(function (f) { return f.document_id === id; })[0] || null;
  }

  function contentUrl(f) {
    return "/documents/" + encodeURIComponent(f.document_id) + "/content?project_id="
      + encodeURIComponent(projectId()) + "&session_token=" + encodeURIComponent(token() || "");
  }

  function showPreview(documentId) {
    var f = fileById(documentId);
    var host = $("ws-files-preview");
    var title = $("ws-files-preview-title");
    var dl = $("ws-files-download");
    if (!f || !host) return;
    STATE.selected = documentId;
    if (title) title.textContent = f.filename;
    var url = contentUrl(f);
    if (dl) {
      dl.href = url;
      dl.style.display = "";
      dl.setAttribute("download", f.filename);
    }
    if (f.preview === "native") {
      host.innerHTML = '<iframe class="fx-preview-frame" title="Document preview" src="'
        + esc(url) + '"></iframe>';
      return;
    }
    // "download" and "unsupported" both decline to render. They differ in what they say,
    // because "your browser will not show this here" and "this platform will not render this
    // format at all" are different facts and a CAD file is the second.
    var message = f.preview === "download"
      ? "Preview opens in the application that reads this format. Download the file to open it."
      : (STATE.unsupportedMessage || "Format not supported for preview.");
    host.innerHTML = '<p class="fx-preview-message">' + esc(message) + "</p>";
  }

  /* ---------- move ---------- */

  function folderOptions() {
    var out = [];
    (function walk(nodes) {
      nodes.forEach(function (n) {
        if (!n.placeholder) out.push(n.path);
        walk(n.children || []);
      });
    })(STATE.tree);
    return out;
  }

  function openMove(documentId) {
    var f = fileById(documentId);
    if (!f || !window.LinUI || !LinUI.openModal) return;
    LinUI.openModal({
      title: "Move " + f.filename,
      mount: function (body, close) {
        body.innerHTML =
          '<p class="ws-note">Filed automatically into <strong>' + esc(f.folder_path || "")
            + "</strong>. Choose where it belongs.</p>"
          + '<label class="ws-field-label" for="fx-move-folder">Folder</label>'
          + '<select id="fx-move-folder" class="ws-input">'
          + folderOptions().map(function (p) {
              return '<option value="' + esc(p) + '"'
                + (p === f.folder_path ? " selected" : "") + ">" + esc(p) + "</option>";
            }).join("")
          + "</select>"
          + '<p id="fx-move-error" class="ws-error" style="display:none;"></p>'
          + '<button type="button" class="ws-btn" id="fx-move-submit">Move</button>';
        body.querySelector("#fx-move-submit").addEventListener("click", async function () {
          var errEl = body.querySelector("#fx-move-error");
          errEl.style.display = "none";
          var resp = await call("projectfilemove", {
            id: projectId(), document_id: documentId,
            folder: body.querySelector("#fx-move-folder").value
          });
          if (!resp || resp.ok !== true) {
            errEl.textContent = (resp && resp.error) || "Could not move the file.";
            errEl.style.display = "block";
            return;
          }
          if (window.LinUI && LinUI.toast) LinUI.toast("Moved", true);
          close();
          mount();
        });
      }
    });
  }

  /* ---------- drag and drop ---------- */

  function wireDrop() {
    var zone = $("ws-files-drop");
    if (!zone || zone.dataset.wired) return;
    zone.dataset.wired = "1";
    ["dragenter", "dragover"].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        zone.classList.add("fx-drop-over");
      });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      zone.addEventListener(ev, function (e) {
        e.preventDefault();
        if (ev === "dragleave" && zone.contains(e.relatedTarget)) return;
        zone.classList.remove("fx-drop-over");
      });
    });
    zone.addEventListener("drop", function (e) {
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) handleDrop(files);
    });
  }

  function readAsBase64(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        var result = String(reader.result || "");
        resolve(result.slice(result.indexOf(",") + 1));
      };
      reader.onerror = function () { reject(new Error("could not read " + file.name)); };
      reader.readAsDataURL(file);
    });
  }

  // THE THREE THINGS THE PERSON MUST SEE WITHOUT WAITING FOR EXTRACTION.
  //
  // Accepted, where it is going, and that analysis is running. The first two are known before
  // the request returns; the third resolves when it does. Each file gets its own row so a
  // batch does not collapse into one spinner, and the destination replaces "filing" in place
  // the moment the server says where it went.
  function dropRowHtml(name) {
    return '<div class="fx-droprow" data-name="' + esc(name) + '">'
      + '<span class="fx-droprow-spin" aria-hidden="true"></span>'
      + '<span class="fx-droprow-name">' + esc(name) + "</span>"
      + '<span class="fx-droprow-state">Accepted. Filing and analysing…</span>'
      + "</div>";
  }

  async function handleDrop(fileList) {
    var pid = projectId();
    var status = $("ws-files-drop-status");
    var errEl = $("ws-files-error");
    if (!pid || !status) return;
    if (errEl) errEl.style.display = "none";
    var items = Array.prototype.slice.call(fileList);
    status.innerHTML = items.map(function (f) { return dropRowHtml(f.name); }).join("");

    var payload = [];
    for (var i = 0; i < items.length; i++) {
      try {
        payload.push({
          filename: items[i].name,
          mimeType: items[i].type || "",
          dataBase64: await readAsBase64(items[i])
        });
      } catch (e) {
        setRowState(items[i].name, "Could not be read", true);
      }
    }
    if (!payload.length) return;

    var resp = await call("projectupload", { id: pid, documents: payload });
    if (!resp || resp.ok !== true) {
      // The upload panel's existing dialog is the error surface for extraction failures; a
      // request that did not land at all is reported here because there is no per-file result
      // for it to carry.
      if (errEl) {
        errEl.textContent = (resp && resp.error) || "The upload did not complete.";
        errEl.style.display = "block";
      }
      status.innerHTML = "";
      return;
    }
    (resp.files || []).forEach(function (f) {
      if (f.status === "failed") {
        setRowState(f.filename, "Extraction failed. See the upload panel for the reason.", true);
        return;
      }
      var where = f.folder_path || "";
      var label = f.filing_label || "Filed";
      var review = f.needs_filing_review ? " · marked for review" : "";
      setRowState(f.filename, label + " into " + where + review, false);
    });
    mount();
  }

  function setRowState(name, text, isError) {
    var status = $("ws-files-drop-status");
    if (!status) return;
    var row = status.querySelector('[data-name="' + (window.CSS && CSS.escape
      ? CSS.escape(name) : name) + '"]');
    if (!row) return;
    row.classList.add(isError ? "fx-droprow-error" : "fx-droprow-done");
    var state = row.querySelector(".fx-droprow-state");
    if (state) state.textContent = text;
  }

  /* ---------- wiring ---------- */

  function wireOnce() {
    var toggle = $("ws-files-occupied-only");
    if (toggle && !toggle.dataset.wired) {
      toggle.dataset.wired = "1";
      toggle.addEventListener("change", function () {
        STATE.occupiedOnly = toggle.checked;
        paintTree();
      });
    }
  }

  return {
    mount: function () { wireOnce(); return mount(); },
    // Exposed for the render harness, which asserts the tab's DOM without a server.
    _paint: function (tree, files, opts) {
      STATE.tree = tree || [];
      STATE.files = files || [];
      STATE.folder = (opts || {}).folder || null;
      STATE.reviewCount = (opts || {}).reviewCount || 0;
      STATE.unsupportedMessage = (opts || {}).unsupportedMessage || "";
      STATE.occupiedOnly = (opts || {}).occupiedOnly !== false;
      paintTree();
      paintList();
    },
    _preview: showPreview,
    _state: STATE
  };
})();
