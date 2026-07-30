
/**
 * Lin Project Radar — Apps Script backend (single file)
 * v10.26-drop-cat12 — Cat 12 Systems Engineering removed from the
 *   framework (103 modules / 10 project-level categories plus the portfolio-level Health suite); chat prompt updated.
 *   Carries v10.25 fix: resetSignals_ preserves signals_extracted
 *   events so the Uploaded Documents table survives resets.
 * ============================================================================
 * SCRIPT PROPERTIES REQUIRED:
 *   OPENAI_API_KEY     — TTS only
 *   ANTHROPIC_API_KEY  — all AI calls
 *
 * REQUIRED MANIFEST (appsscript.json): oauthScopes must include the FULL
 *   https://www.googleapis.com/auth/drive scope plus script.external_request
 *   and documents; webapp.executeAs = USER_DEPLOYING. If writes fail with a
 *   DriveApp permission error: myaccount.google.com/permissions > remove this
 *   script's access > run testHealth() > approve the full dialog ("See, edit,
 *   create, and delete") > Manage deployments > New version.
 *
 * DEPLOY:
 *   1) Paste as Code.gs (replace everything). Ctrl+S.
 *   2) Services: Drive API must be enabled.
 *   3) Deploy > Manage deployments > New version > Deploy.
 *   5) Verify: ?action=ping returns v10.31-milestones
 * ============================================================================
 */
var PARENT_FOLDER_NAME  = 'Lin Project Radar';
var ARCHIVE_FOLDER_NAME = '00_Archive';
var CORPUS_FOLDER_NAME  = '_corpus';
var AUDIT_FOLDER_NAME   = '_audits';
var LIB_FOLDER_NAME     = '_lib';
var API_VERSION         = 'lin-project-radar-backend-v10.36-roster-json';
var OPENAI_MODEL        = 'gpt-4.1';
var OPENAI_API_BASE     = 'https://api.openai.com/v1';
var TTS_MODEL           = 'tts-1';
var TTS_DEFAULT_VOICE   = 'onyx';
var CLAUDE_MODEL_OPUS   = 'claude-opus-4-8';
var CLAUDE_MODEL_SONNET = 'claude-sonnet-4-6';
var ANTHROPIC_API_BASE  = 'https://api.anthropic.com/v1';
var ANTHROPIC_VERSION   = '2023-06-01';
function doOptions(e) {
  return ContentService.createTextOutput('').setMimeType(ContentService.MimeType.TEXT);
}
function doGet(e) {
  var p = (e && e.parameter) ? e.parameter : {};
  var action = String(p.action || 'health').toLowerCase();
  try {
    if (action === 'health')           return out_(okHealth_());
    if (action === 'list')             return out_({ ok: true, projects: listProjects_() });
    if (action === 'listslim')         return out_({ ok: true, projects: listProjectsSlim_() });
    if (action === 'listarchived')     return out_({ ok: true, projects: listArchived_() });
    if (action === 'get')              return out_(getProject_(p.id));
    if (action === 'listcorpus')       return out_(listCorpus_(p.id));
    if (action === 'listauditresults') return out_(listAuditResults_(p.id));
    if (action === 'gethistory')       return out_(getHistory_(p.id));
    if (action === 'getportfoliohealth') return out_({ ok: true, health: readPortfolioHealth_() });
    if (action === 'ping' || action === 'version') return out_(pingDiagnostic_());
    return out_({ ok: false, error: 'Unknown GET action: ' + action });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  }
}
function doPost(e) {
  var body = {};
  try {
    body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
  } catch (parseErr) {
    return out_({ ok: false, error: 'Invalid JSON body: ' + String(parseErr) });
  }
  var action = String(body.action || '').toLowerCase();
  try {
    if (action === 'create')           return out_(createProject_(body));
    if (action === 'save')             return out_(saveProject_(body));
    if (action === 'archive')          return out_(archiveProject_(body));
    if (action === 'restore')          return out_(restoreProject_(body));
    if (action === 'setprojectnumber') return out_(setProjectNumber_(body));
    if (action === 'chat')             return out_(chat_(body));
    if (action === 'analyze')          return out_(analyze_(body));
    if (action === 'extractsignals')   return out_(extractSignals_(body));
    if (action === 'identifyonly')     return out_(identifyOnly_(body));
    if (action === 'overwritesignal')  return out_(overwriteSignal_(body));
    if (action === 'resetsignals')     return out_(resetSignals_(body));
    if (action === 'tts')              return out_(tts_(body));
    if (action === 'ingestcorpus')     return out_(ingestCorpus_(body));
    if (action === 'audit')            return out_(audit_(body));
    if (action === 'portfolioanalyze') return out_(portfolioAnalyze_(body));
    if (action === 'saveportfoliohealth') return out_(savePortfolioHealth_(body));
    if (action === 'savehistory')      return out_(saveHistory_(body));
    if (action === 'saveauditresult')  return out_(saveAuditResult_(body));
    return out_({ ok: false, error: 'Unknown POST action: ' + action });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  }
}
/* --------------------------- folders ---------------------------- */
function parentFolder_() {
  var it = DriveApp.getFoldersByName(PARENT_FOLDER_NAME);
  return it.hasNext() ? it.next() : DriveApp.createFolder(PARENT_FOLDER_NAME);
}
function projectFolderById_(parent, id) {
  var it = parent.getFoldersByName(String(id));
  return it.hasNext() ? it.next() : null;
}
function directFolder_(folder, name) {
  var it = folder.getFoldersByName(name);
  return it.hasNext() ? it.next() : null;
}
function ensureSubfolder_(projectFolder, name) {
  var f = directFolder_(projectFolder, name);
  return f ? f : projectFolder.createFolder(name);
}
function readProjectJson_(folder) {
  var files = folder.getFilesByName('project.json');
  if (!files.hasNext()) return null;
  try { return JSON.parse(files.next().getBlob().getDataAsString()); }
  catch (err) { return null; }
}
function writeProjectJson_(folder, project) {
  project.updatedAt = new Date().toISOString();
  var content = JSON.stringify(project, null, 2);
  var files = folder.getFilesByName('project.json');
  if (files.hasNext()) files.next().setContent(content);
  else folder.createFile('project.json', content, 'application/json');
  return project;
}
function pad2_(n) { return (n < 10 ? '0' : '') + n; }
function nextNumericId_(parent) {
  var max = 0;
  var it = parent.getFolders();
  while (it.hasNext()) {
    var name = it.next().getName();
    if (name === ARCHIVE_FOLDER_NAME) continue;
    var n = parseInt(name, 10);
    if (!isNaN(n) && n > max) max = n;
  }
  var arch = directFolder_(parent, ARCHIVE_FOLDER_NAME);
  if (arch) {
    var ai = arch.getFolders();
    while (ai.hasNext()) {
      var an = parseInt(ai.next().getName(), 10);
      if (!isNaN(an) && an > max) max = an;
    }
  }
  return pad2_(max + 1);
}
/* ========================= KNOWLEDGE LIBRARY ========================= */
function readLib_() {
  var parent = parentFolder_();
  var libFolder = directFolder_(parent, LIB_FOLDER_NAME);
  if (!libFolder) return [];
  var files = [];
  var it = libFolder.getFiles();
  while (it.hasNext()) {
    var f = it.next();
    if (f.getName().endsWith('.txt')) {
      try { files.push({ name: f.getName(), content: f.getBlob().getDataAsString() }); } catch (e) {}
    }
  }
  return files;
}
function retrieveLibContext_(question, maxFiles) {
  maxFiles = maxFiles || 3;
  var lib = readLib_();
  if (!lib.length) return '';
  var qLower = question.toLowerCase();
  var keywords = {
    'pceif_definition.txt': ['pceif','framework','two-layer','layer 1','layer 2','signal-to-action',
      'governance','what is','define','definition','purpose','thesis','contribution'],
    'signal_taxonomy.txt': ['signal','monte carlo','cusum','nlp','anomaly','forecast','probabilistic',
      'document','rfi','submittal','three signal','prediction','model','stack'],
    'governance_framework.txt': ['evm','cpi','spi','far','omb','nist','regulatory','audit',
      'compliance','authority','contracting','accountability','public','override','human'],
    'escalation_logic.txt': ['escalate','escalation','response','action','monitor','recover',
      'conflict','diverge','override','document','key term','definition','hypothesis','rq'],
    'faq_simulated.txt': ['why','how','what does','explain','validate','research','methodology',
      'interviewer','fairness gate','contractor','scope','praxis']
  };
  var scored = lib.map(function(f) {
    var kws = keywords[f.name] || [];
    var score = 0;
    kws.forEach(function(kw) { if (qLower.indexOf(kw) >= 0) score++; });
    if (f.name === 'faq_simulated.txt' && (qLower.indexOf('?') >= 0 || qLower.indexOf('what') >= 0 || qLower.indexOf('why') >= 0 || qLower.indexOf('how') >= 0)) score += 0.5;
    return { file: f, score: score };
  });
  scored.sort(function(a, b) { return b.score - a.score; });
  var top = scored.slice(0, maxFiles).filter(function(s) { return s.score > 0; });
  if (!top.length) {
    top = scored.filter(function(s) {
      return s.file.name === 'pceif_definition.txt' || s.file.name === 'faq_simulated.txt';
    }).slice(0, 2);
  }
  return top.map(function(s) {
    return '=== ' + s.file.name.replace('.txt','').toUpperCase() + ' ===\n' + s.file.content;
  }).join('\n\n');
}
/* --------------------------- health ---------------------------- */
function okHealth_() {
  var parent = parentFolder_();
  var props = PropertiesService.getScriptProperties();
  var libFolder = directFolder_(parent, LIB_FOLDER_NAME);
  var libFiles = 0;
  if (libFolder) { var it = libFolder.getFiles(); while (it.hasNext()) { it.next(); libFiles++; } }
  return {
    ok: true, apiVersion: API_VERSION,
    parentFolder: parent.getName(), parentFolderId: parent.getId(),
    openaiKeyPresent:    Boolean(props.getProperty('OPENAI_API_KEY')),
    anthropicKeyPresent: Boolean(props.getProperty('ANTHROPIC_API_KEY')),
    libPresent: Boolean(libFolder), libFileCount: libFiles,
    timestamp: new Date().toISOString(),
    endpoints: [
      '?action=health','?action=list','?action=listslim','?action=listarchived',
      '?action=get&id=01','?action=listcorpus&id=01','?action=listauditresults&id=01','?action=gethistory&id=01',
      'POST create','POST save','POST setprojectnumber','POST archive','POST restore',
      'POST chat','POST analyze','POST extractsignals','POST overwritesignal','POST tts',
      'POST ingestcorpus','POST audit','POST resetsignals','POST saveauditresult','POST savehistory','POST portfolioanalyze'
    ]
  };
}
function pingDiagnostic_() {
  var props = PropertiesService.getScriptProperties();
  return {
    ok: true, version: API_VERSION,
    deployedAt_note: 'If this version is not v10.36-roster-json, the deployment did NOT update.',
    anthropicKeyPresent: Boolean(props.getProperty('ANTHROPIC_API_KEY')),
    openaiKeyPresent: Boolean(props.getProperty('OPENAI_API_KEY')),
    postActionsRegistered: [
      'create','save','setprojectnumber','archive','restore','chat','analyze','extractsignals',
      'overwritesignal','resetsignals','tts','ingestcorpus','audit',
      'portfolioanalyze','savehistory','saveauditresult','identifyonly'
    ],
    portfolioanalyzeRegistered: true,
    timestamp: new Date().toISOString()
  };
}
/* --------------------------- project actions -------------------- */
function listProjects_() {
  var parent = parentFolder_();
  var projects = [];
  var it = parent.getFolders();
  while (it.hasNext()) {
    var f = it.next();
    if (f.getName() === ARCHIVE_FOLDER_NAME) continue;
    var p = readProjectJson_(f);
    if (p) projects.push(p);
  }
  projects.sort(function (a, b) { return String(a.id).localeCompare(String(b.id)); });
  return projects;
}
function listProjectsSlim_() {
  // v10.28: lightweight portfolio list — no simulation arrays, no event bodies
  return listProjects_().map(function (p) {
    var sim = p.simulationSignals && p.simulationSignals.signal_array ? p.simulationSignals.signal_array.length : 0;
    var docs = 0;
    (p.events || []).forEach(function (e) { if (e && e.event === 'signals_extracted') docs++; });
    return {
      id: p.id, name: p.name, sector: p.sector, status: p.status,
      updatedAt: p.updatedAt || null,
      cpi: p.signalInputs ? p.signalInputs.cpi : null,
      spi: p.signalInputs ? p.signalInputs.spi : null,
      docRiskScore: p.signalInputs ? p.signalInputs.docRiskScore : null,
      actualPctComplete: p.signalInputs ? p.signalInputs.actualPctComplete : null,
      simModuleCount: sim, docCount: docs,
      lat: p.lat != null ? p.lat : null, lng: p.lng != null ? p.lng : null,
      address: p.address || null, formattedAddress: p.formattedAddress || null,
      slim: true
    };
  });
}
function listArchived_() {
  var parent = parentFolder_();
  var archive = directFolder_(parent, ARCHIVE_FOLDER_NAME);
  if (!archive) return [];
  var projects = [];
  var it = archive.getFolders();
  while (it.hasNext()) { var p = readProjectJson_(it.next()); if (p) projects.push(p); }
  projects.sort(function (a, b) { return String(a.id).localeCompare(String(b.id)); });
  return projects;
}
function getProject_(id) {
  if (!id) return { ok: false, error: 'Missing id' };
  var parent = parentFolder_();
  var folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Not found: ' + id };
  return { ok: true, project: readProjectJson_(folder) };
}
function createProject_(body) {
  var parent = parentFolder_();
  var id = body.id != null && String(body.id).trim() !== '' ? String(body.id).trim() : nextNumericId_(parent);
  if (/[\/\\"']/.test(id)) return { ok: false, error: 'Project number contains invalid characters' };
  if (projectFolderById_(parent, id)) return { ok: false, error: 'Project number already exists: ' + id };
  var archive0 = directFolder_(parent, ARCHIVE_FOLDER_NAME);
  if (archive0 && archive0.getFoldersByName(id).hasNext()) return { ok: false, error: 'Project number exists in archive: ' + id };
  var folder = parent.createFolder(id);
  var sector = String(body.sector || 'design').toLowerCase();
  if (['design','construction','hybrid'].indexOf(sector) < 0) sector = 'design';
  var project = {
    id: id, name: body.name || ('Project ' + id), sector: sector,
    signals: {}, events: [{ event: 'project_created', at: new Date().toISOString() }],
    status: 'awaiting_ingest', createdAt: new Date().toISOString()
  };
  writeProjectJson_(folder, project);
  return { ok: true, project: project };
}
function saveProject_(body) {
  var p = body.project;
  if (!p || !p.id) return { ok: false, error: 'Missing project' };
  var parent = parentFolder_();
  var folder = projectFolderById_(parent, p.id);
  if (!folder) return { ok: false, error: 'Not found: ' + p.id };
  p = geocodeIfNeeded_(p);
  writeProjectJson_(folder, p);
  return { ok: true, project: p };
}
/* v10.29 — server-side address -> lat/lng translation. PMs type an address
   only; coordinates are resolved with Apps Script's built-in geocoder.
   Re-geocodes only when the address changed; clears coords when cleared. */
function geocodeIfNeeded_(p) {
  try {
    var addr = p.address != null ? String(p.address).trim() : '';
    if (!addr) {
      p.lat = null; p.lng = null; p.geocodedAddress = null;
      p.formattedAddress = null; p.geocodeError = null;
      return p;
    }
    if (p.lat != null && p.lng != null && p.geocodedAddress === addr) return p;
    var geo = Maps.newGeocoder().geocode(addr);
    if (geo && geo.status === 'OK' && geo.results && geo.results.length) {
      var loc = geo.results[0].geometry.location;
      p.lat = Math.round(loc.lat * 1e6) / 1e6;
      p.lng = Math.round(loc.lng * 1e6) / 1e6;
      p.geocodedAddress = addr;
      p.formattedAddress = geo.results[0].formatted_address || addr;
      p.geocodeError = null;
    } else {
      p.geocodeError = 'Address could not be resolved (' + (geo ? geo.status : 'no response') + '). Refine the address and save again.';
    }
  } catch (e) {
    p.geocodeError = 'Geocoding unavailable: ' + String(e);
  }
  return p;
}
function archiveProject_(body) {
  var id = body.id;
  if (!id) return { ok: false, error: 'Missing id' };
  var parent = parentFolder_();
  var folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Not found: ' + id };
  var archive = directFolder_(parent, ARCHIVE_FOLDER_NAME) || parent.createFolder(ARCHIVE_FOLDER_NAME);
  var proj = readProjectJson_(folder);
  if (proj) {
    proj.status = 'archived';
    proj.events = proj.events || [];
    proj.events.push({ event: 'project_archived', at: new Date().toISOString() });
    writeProjectJson_(folder, proj);
  }
  folder.moveTo(archive);
  return { ok: true, archived: true, id: id, timestamp: new Date().toISOString() };
}
function restoreProject_(body) {
  var id = body.id;
  if (!id) return { ok: false, error: 'Missing id' };
  var parent = parentFolder_();
  var archive = directFolder_(parent, ARCHIVE_FOLDER_NAME);
  if (!archive) return { ok: false, error: 'No archive folder' };
  var it = archive.getFoldersByName(String(id));
  if (!it.hasNext()) return { ok: false, error: 'Archived project not found: ' + id };
  var folder = it.next();
  folder.moveTo(parent);
  var project = readProjectJson_(folder);
  if (project) {
    project.status = 'awaiting_ingest';
    project.events = project.events || [];
    project.events.push({ event: 'project_restored', at: new Date().toISOString() });
    writeProjectJson_(folder, project);
  }
  return { ok: true, restored: true, id: id, project: project, timestamp: new Date().toISOString() };
}
/* ========================= API HELPERS ========================= */
function openaiKey_() {
  var k = PropertiesService.getScriptProperties().getProperty('OPENAI_API_KEY');
  if (!k) throw new Error('OPENAI_API_KEY not set');
  return k;
}
function claudeKey_() {
  var k = PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY');
  if (!k) throw new Error('ANTHROPIC_API_KEY not set in Script Properties');
  return k;
}
function claudeChat_(systemPrompt, userContent, maxTokens, model) {
  model = model || CLAUDE_MODEL_SONNET;
  var resp = UrlFetchApp.fetch(ANTHROPIC_API_BASE + '/messages', {
    method: 'POST', contentType: 'application/json',
    headers: { 'x-api-key': claudeKey_(), 'anthropic-version': ANTHROPIC_VERSION },
    payload: JSON.stringify({
      model: model, max_tokens: maxTokens || 1024,
      system: systemPrompt,
      messages: [{ role: 'user', content: userContent }]
    }),
    muteHttpExceptions: true
  });
  if (resp.getResponseCode() !== 200)
    throw new Error('Claude ' + resp.getResponseCode() + ': ' + resp.getContentText().substring(0, 300));
  return JSON.parse(resp.getContentText()).content[0].text;
}
function openaiChat_(systemPrompt, userContent, maxTokens) {
  var resp = UrlFetchApp.fetch(OPENAI_API_BASE + '/chat/completions', {
    method: 'POST', contentType: 'application/json',
    headers: { 'Authorization': 'Bearer ' + openaiKey_() },
    payload: JSON.stringify({
      model: OPENAI_MODEL,
      messages: [{ role: 'system', content: systemPrompt }, { role: 'user', content: userContent }],
      temperature: 0.2, max_tokens: maxTokens || 512
    }),
    muteHttpExceptions: true
  });
  if (resp.getResponseCode() !== 200)
    throw new Error('OpenAI ' + resp.getResponseCode() + ': ' + resp.getContentText().substring(0, 200));
  return JSON.parse(resp.getContentText()).choices[0].message.content;
}
function openaiMultimodal_(promptText, dataB64, mimeType, maxTokens) {
  var isImage = (mimeType === 'image/png' || mimeType === 'image/jpeg' || mimeType === 'image/gif' || mimeType === 'image/webp');
  if (isImage) {
    var resp = UrlFetchApp.fetch(OPENAI_API_BASE + '/chat/completions', {
      method: 'POST', contentType: 'application/json',
      headers: { 'Authorization': 'Bearer ' + openaiKey_() },
      payload: JSON.stringify({
        model: OPENAI_MODEL,
        messages: [{ role: 'user', content: [
          { type: 'text', text: promptText },
          { type: 'image_url', image_url: { url: 'data:' + mimeType + ';base64,' + dataB64 } }
        ]}],
        temperature: 0.1, max_tokens: maxTokens || 1024,
        response_format: { type: 'json_object' }
      }),
      muteHttpExceptions: true
    });
    if (resp.getResponseCode() !== 200)
      throw new Error('OpenAI image ' + resp.getResponseCode() + ': ' + resp.getContentText().substring(0, 300));
    return JSON.parse(resp.getContentText()).choices[0].message.content;
  }
  var bytes = Utilities.base64Decode(dataB64);
  var blob = Utilities.newBlob(bytes, mimeType, 'upload.pdf');
  var boundary = '----FormBoundary' + Utilities.getUuid().replace(/-/g,'');
  var bodyParts = '--' + boundary + '\r\n' +
    'Content-Disposition: form-data; name="purpose"\r\n\r\nassistants\r\n' +
    '--' + boundary + '\r\n' +
    'Content-Disposition: form-data; name="file"; filename="upload.pdf"\r\n' +
    'Content-Type: application/pdf\r\n\r\n';
  var bodyBytes = Utilities.newBlob(bodyParts).getBytes()
    .concat(blob.getBytes())
    .concat(Utilities.newBlob('\r\n--' + boundary + '--\r\n').getBytes());
  var uploadResp = UrlFetchApp.fetch(OPENAI_API_BASE + '/files', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + openaiKey_(), 'Content-Type': 'multipart/form-data; boundary=' + boundary },
    payload: Utilities.newBlob(bodyBytes).getBytes(),
    muteHttpExceptions: true
  });
  if (uploadResp.getResponseCode() !== 200)
    throw new Error('OpenAI file upload ' + uploadResp.getResponseCode() + ': ' + uploadResp.getContentText().substring(0, 300));
  var fileId = JSON.parse(uploadResp.getContentText()).id;
  var chatResp = UrlFetchApp.fetch(OPENAI_API_BASE + '/chat/completions', {
    method: 'POST', contentType: 'application/json',
    headers: { 'Authorization': 'Bearer ' + openaiKey_() },
    payload: JSON.stringify({
      model: OPENAI_MODEL,
      messages: [{ role: 'user', content: [
        { type: 'text', text: promptText },
        { type: 'file', file: { file_id: fileId } }
      ]}],
      temperature: 0.1, max_tokens: maxTokens || 1024,
      response_format: { type: 'json_object' }
    }),
    muteHttpExceptions: true
  });
  try { UrlFetchApp.fetch(OPENAI_API_BASE + '/files/' + fileId, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + openaiKey_() }, muteHttpExceptions: true }); } catch(e) {}
  if (chatResp.getResponseCode() !== 200)
    throw new Error('OpenAI PDF chat ' + chatResp.getResponseCode() + ': ' + chatResp.getContentText().substring(0, 300));
  return JSON.parse(chatResp.getContentText()).choices[0].message.content;
}
/* --------------------------- chat_ ------------------------------ */
function chat_(body) {
  var question = body.question;
  if (!question) return { ok: false, error: 'question is required' };
  // v10.30: the chat ALWAYS sees the full portfolio roster (one line per
  // project) so it can never deny a project exists. Compact detail is added
  // for the selected project AND for any project ids mentioned in the question.
  // v10.36: prefer the persisted portfolio JSON (one file read) over walking
  // every project folder; fall back to the walk when the JSON is absent.
  var roster = null;
  var ph = readPortfolioHealth_();
  if (ph && ph.projects && ph.projects.length) {
    roster = ph.projects.map(function (p) {
      return { id: p.id, name: p.name, sector: p.sector, status: p.status };
    });
  }
  if (!roster || !roster.length) {
    roster = listProjects_().map(function (p) {
      return { id: p.id, name: p.name, sector: p.sector, status: p.status };
    });
  }
  var projectContext = 'PORTFOLIO ROSTER (every project that exists):\n' + JSON.stringify(roster);
  function compactFor_(pj) {
    var counts = { Green:0, Yellow:0, Amber:0, Red:0, other:0 };
    if (pj.simulationSignals && pj.simulationSignals.signal_array) {
      pj.simulationSignals.signal_array.forEach(function (m) {
        var s = m && m.status_color; if (counts[s] != null) counts[s]++; else counts.other++;
      });
    }
    return {
      id: pj.id, name: pj.name, sector: pj.sector, status: pj.status,
      address: pj.formattedAddress || pj.address || null,
      signalInputs: pj.signalInputs || null,
      moduleStatusCounts: counts,
      recentEvents: (pj.events || []).slice(-6),
      redModules: (function () {
        var out = [];
        if (pj.simulationSignals && pj.simulationSignals.signal_array) {
          pj.simulationSignals.signal_array.forEach(function (mm) {
            if (mm && mm.status_color === 'Red') out.push({ module: mm.method_class || mm.name, evidence: mm.evidence_metric || null });
          });
        }
        return out.slice(0, 12);
      })(),
      governance: pj.simulationSignals ? {
        decision: pj.simulationSignals.governance_decision || pj.simulationSignals.decision || null,
        recommendation: pj.simulationSignals.recommendation || null,
        authority: pj.simulationSignals.authority || null
      } : null
    };
  }
  var included = {};
  if (body.id) {
    var got = getProject_(body.id);
    if (got.ok && got.project) {
      included[String(body.id)] = true;
      projectContext += '\n\nSELECTED PROJECT (compact):\n' + JSON.stringify(compactFor_(got.project), null, 2);
    }
  }
  // Detect project ids mentioned in the question (max 2 extra) — matches
  // roster ids as whole tokens, with or without a "project" prefix.
  var qLow = ' ' + String(question).toLowerCase() + ' ';
  var extra = 0;
  for (var ri = 0; ri < roster.length && extra < 2; ri++) {
    var rid = String(roster[ri].id);
    if (included[rid]) continue;
    var ridLow = rid.toLowerCase();
    var mentioned = qLow.indexOf(' ' + ridLow + ' ') >= 0 ||
                    qLow.indexOf('project ' + ridLow) >= 0 ||
                    qLow.indexOf('#' + ridLow) >= 0 ||
                    (rid.length === 2 && rid.charAt(0) === '0' && (qLow.indexOf(' ' + ridLow.substring(1) + ' ') >= 0 || qLow.indexOf('project ' + ridLow.substring(1)) >= 0));
    if (mentioned) {
      var g2 = getProject_(rid);
      if (g2.ok && g2.project) {
        included[rid] = true; extra++;
        projectContext += '\n\nMENTIONED PROJECT ' + rid + ' (compact):\n' + JSON.stringify(compactFor_(g2.project), null, 2);
      }
    }
  }
  var libContext = retrieveLibContext_(question, 3);
  if (body.snapshot && body.snapshot.summary) {
    var snap = body.snapshot;
    var catSummary = '';
    if (snap.categories) {
      Object.keys(snap.categories).forEach(function(k) {
        var c = snap.categories[k];
        if (!c.parked && c.status) catSummary += c.num + ' ' + c.name + ': ' + c.status + '\n';
      });
    }
    projectContext = 'STORED SNAPSHOT (' + (snap.period || '') + ') — ' +
      (snap.summary ? snap.summary.total_modules : '?') + ' modules computed:\n' + catSummary +
      '\nGovernance: ' + (snap.governance ? snap.governance.state : 'unknown') +
      '\nAuthority: ' + (snap.governance ? snap.governance.authority : 'unknown') +
      '\nAction: ' + (snap.governance ? snap.governance.action : 'unknown') +
      '\nEvidence confidence: ' + (snap.summary && snap.summary.evidence_agreement ? snap.summary.evidence_agreement.confidence : 'unknown');
  }
  var system =
    'You are Lin, a project controls advisor for the PCEIF platform. ' +
    'Answer like a senior colleague giving a quick verbal briefing. Warm, direct, professional. ' +
    'STRICT RULES: ' +
    '1. For status questions, 4 to 5 sentences. Enough context, not a full report. ' +
    '2. Never read out raw metric figures. No CPI values, SPI values, P80 numbers, percentages, or module numbers. ' +
    '3. Use plain English: on track, running over budget, schedule is slipping, needs attention, escalation required. ' +
    '4. No bullet points, no headers, no markdown, no numbered lists. ' +
    '5. No preamble. Start the answer immediately. ' +
    '6. The platform has 103 signal modules across 10 project-level categories plus the portfolio-level Health suite. ' +
    'Cat 1-5 generate signals. Cat 6 synthesizes. Cat 7 combines evidence. Cat 8 detects ML anomalies. ' +
    'Cat 9 governs. Cat 10 checks data integrity. Cat 11 optimizes decisions. ' +
    '7. Confidence guidance: if most evidence methods agree, act with confidence. If they diverge, investigate first. ' +
    '10. Category numbering: project categories are 1-10 (1 EVM, 2 Schedule Simulation, 3 Cost Simulation, 4 Document & Risk Signals, 5 System Dynamics, 6 Signal Synthesis, 7 Evidence Combination, 8 Governance & Compliance, 9 Data Integrity, 10 Decision Optimization). ML & AI Pattern Detection is the portfolio-level Portfolio Health suite (modules PH.1-PH.5), not a numbered category. Never refer to Category 8 as ML, and never use the old numbers 9/10/11 for Governance/Data Integrity/Optimization. ' +
    '9. When asked about a specific project by number or name, ALWAYS answer with: current status, the key signals (CPI, SPI, document risk, red modules if any), the recommendation, and the governance decision context, drawing from the compact context provided. Never reply that you lack project status when a SELECTED or MENTIONED PROJECT block is present. ' +
    '8. The PORTFOLIO ROSTER lists every project that exists. Never claim a project does not exist if it appears in the roster; if its detail is not in context, answer from its roster line (name, sector, status) and note that opening the project gives the full picture. ' +
    (libContext ? '\n\n--- KNOWLEDGE ---\n' + libContext : '') +
    '\n\n--- PROJECT DATA ---\n' + projectContext;
  var answer = claudeChat_(system, question, 800, CLAUDE_MODEL_SONNET);
  return {
    ok: true, question: question, answer: answer,
    scope: body.id ? ('project ' + body.id) : 'portfolio',
    libUsed: Boolean(libContext),
    timestamp: new Date().toISOString()
  };
}
/* --------------------------- analyze_ --------------------------- */
function analyze_(body) {
  var text = body.text;
  if (!text) return { ok: false, error: 'text is required' };
  var docType = body.docType || 'document';
  var spec = body.spec || '';
  var system = 'You are a construction project-controls document analyst. You read project documents ' +
    '(RFIs, RFAs, meeting minutes, specs) and produce a SHORT, factual, plain-language summary of ' +
    'schedule/cost/coordination risk. You do not invent facts. You note whether the document, compared ' +
    'to the provided specification/code excerpt, raises a conflict, a gap the spec is silent on, or ' +
    'appears consistent. This is an illustrative demonstration analysis, not a validated compliance determination.';
  var userContent = 'Document type: ' + docType + '\n\nDOCUMENT:\n' + text;
  if (spec) userContent += '\n\nSPECIFICATION / CODE EXCERPT TO COMPARE AGAINST:\n' + spec;
  userContent += '\n\nReturn: (1) a 2-4 sentence risk summary; (2) if a spec/code excerpt was provided, ' +
    'a one-line comparison verdict — CONFLICT / GAP (spec silent) / CONSISTENT — with a brief reason. ' +
    'Keep it under ~150 words.';
  var summary = claudeChat_(system, userContent, 500, CLAUDE_MODEL_SONNET);
  return { ok: true, docType: docType, comparedToSpec: Boolean(spec), analysis: summary, timestamp: new Date().toISOString() };
}
/* ========================= DRIVE OCR ========================= */
function extractTextFromPDFViaDriveOCR_(fileId) {
  try {
    var file = DriveApp.getFileById(fileId);
    var blob = file.getBlob();
    var rawBytes = blob.getBytes();
    var rawStr = '';
    for (var i = 0; i < rawBytes.length; i++) rawStr += String.fromCharCode(rawBytes[i] & 0xFF);
    var extracted = '';
    var pos = 0;
    while (pos < rawStr.length) {
      var btIdx = rawStr.indexOf('BT', pos);
      if (btIdx < 0) break;
      var etIdx = rawStr.indexOf('ET', btIdx);
      if (etIdx < 0) break;
      var block = rawStr.substring(btIdx, etIdx + 2);
      var i2 = 0;
      while (i2 < block.length) {
        if (block[i2] === '(') {
          var j = i2 + 1, str = '';
          while (j < block.length && block[j] !== ')') {
            if (block[j] === '\\') { j += 2; continue; }
            str += block[j]; j++;
          }
          var after = block.substring(j + 1, j + 5).replace(/^\s+/, '');
          if (after.indexOf('Tj') === 0 || after.indexOf('TJ') === 0) extracted += str + ' ';
          i2 = j + 1;
        } else { i2++; }
      }
      pos = etIdx + 2;
    }
    extracted = extracted.replace(/\\n/g,' ').replace(/\\r/g,' ').replace(/\\t/g,' ').replace(/  +/g,' ').trim();
    if (extracted.length > 50) { Logger.log('PDF text extraction: ' + extracted.length + ' chars'); return extracted; }
    try {
      var pdfBlob = blob.setContentType('application/pdf');
      var fileMetadata = { title: 'PCEIF_Temp_OCR_' + Utilities.getUuid(), mimeType: MimeType.GOOGLE_DOCS };
      var tempFile = Drive.Files.insert(fileMetadata, pdfBlob, { ocr: true, ocrLanguage: 'en', fields: 'id' });
      var doc = DocumentApp.openById(tempFile.id);
      var ocrText = doc.getBody().getText();
      Drive.Files.remove(tempFile.id);
      if (ocrText && ocrText.trim().length > 50) { Logger.log('Drive OCR: ' + ocrText.length + ' chars'); return ocrText; }
    } catch(e2) { Logger.log('Drive OCR failed: ' + e2.toString()); }
    return '';
  } catch (err) { Logger.log('extractTextFromPDFViaDriveOCR_ error: ' + err.toString()); return ''; }
}
function claudePdfExtract_(promptText, dataB64, maxTokens, model) {
  model = model || CLAUDE_MODEL_SONNET;
  var resp = UrlFetchApp.fetch(ANTHROPIC_API_BASE + '/messages', {
    method: 'POST', contentType: 'application/json',
    headers: { 'x-api-key': claudeKey_(), 'anthropic-version': ANTHROPIC_VERSION },
    payload: JSON.stringify({
      model: model, max_tokens: maxTokens || 1024,
      messages: [{ role: 'user', content: [
        { type: 'document', source: { type: 'base64', media_type: 'application/pdf', data: dataB64 } },
        { type: 'text', text: promptText }
      ]}]
    }),
    muteHttpExceptions: true
  });
  if (resp.getResponseCode() !== 200)
    throw new Error('Claude PDF ' + resp.getResponseCode() + ': ' + resp.getContentText().substring(0, 300));
  return JSON.parse(resp.getContentText()).content[0].text;
}
/* ===================== DOCUMENT TYPE IDENTIFICATION ===================== */
function identifyOnly_(body) {
  var id = body.id;
  var dataB64 = body.dataBase64;
  var mimeType = body.mimeType || 'application/pdf';
  var fileName = body.fileName || 'document.pdf';
  if (!dataB64) return { ok: false, error: 'dataBase64 is required' };
  var validTypes = ['pay_application','monthly_report','rfi','oac_minutes','schedule_update',
    'change_order','field_report','inspection_report','ncr_log','subcontractor_report',
    'procurement_log','lookahead_schedule','resource_report','cost_report','past_performance_report',
    'safety_report','quality_audit_report','environmental_report','historical_data','time_phased_schedule',
    'contract_value','schedule_of_values','submittal','correspondence_notice','risk_register','commissioning_report','rfi_log','rfa_log'];
  var parent = parentFolder_();
  var folder = id ? projectFolderById_(parent, id) : null;
  var storedFileId = null;
  try {
    var tmpFolder = folder ? ensureSubfolder_(folder, '_signals') : parent;
    var bytes = Utilities.base64Decode(dataB64);
    var blob = Utilities.newBlob(bytes, mimeType, fileName);
    var stored = tmpFolder.createFile(blob);
    storedFileId = stored.getId();
  } catch (e) {}
  var prompt = 'You are a construction document classifier. Identify the document type. ' +
    'Return ONLY clean JSON: {"docType":"<type>","confidence":<0-1>,"period":"<period if found>"}. ' +
    'Valid types: ' + validTypes.join(', ') + '. ' +
    'Match on content: pay application has contract sum and amount paid; monthly report has EV/AC/PV; ' +
    'RFI has request for information; OAC minutes has meeting attendees; change order has revised contract sum; ' +
    'NCR log has non-conformance; cost report has indirect/material cost; safety report has OSHA incidents. ' +
    'No markdown.';
  var raw = '';
  try {
    raw = claudePdfExtract_(prompt, dataB64, 256, CLAUDE_MODEL_SONNET);
  } catch (e) {
    var guess2 = guessTypeFromFilename_(fileName);
    return { ok: true, docType: guess2, confidence: 0.4, source: 'filename_fallback', fileName: fileName, storedFileId: storedFileId };
  }
  var parsed = {};
  try {
    parsed = JSON.parse(raw.replace(/```json/g,'').replace(/```/g,'').trim());
  } catch (e) {
    var guess3 = guessTypeFromFilename_(fileName);
    return { ok: true, docType: guess3, confidence: 0.4, source: 'parse_fallback', fileName: fileName, storedFileId: storedFileId };
  }
  var docType = String(parsed.docType || '').toLowerCase();
  if (validTypes.indexOf(docType) < 0) docType = guessTypeFromFilename_(fileName);
  return { ok: true, docType: docType, confidence: parsed.confidence || 0.7, period: parsed.period || null, source: 'ai', fileName: fileName, storedFileId: storedFileId };
}
function guessTypeFromFilename_(fileName) {
  var f = String(fileName).toLowerCase();
  if (f.indexOf('pay') >= 0 || f.indexOf('payapp') >= 0) return 'pay_application';
  if (f.indexOf('monthly') >= 0 || f.indexOf('progress') >= 0) return 'monthly_report';
  if (f.indexOf('rfa') >= 0 && f.indexOf('log') >= 0) return 'rfa_log';
  if (f.indexOf('rfi') >= 0 && f.indexOf('log') >= 0) return 'rfi_log';
  if (f.indexOf('rfi') >= 0) return 'rfi';
  if (f.indexOf('oac') >= 0 || f.indexOf('minutes') >= 0) return 'oac_minutes';
  if (f.indexOf('schedule') >= 0 && f.indexOf('look') >= 0) return 'lookahead_schedule';
  if (f.indexOf('schedule') >= 0) return 'schedule_update';
  if (f.indexOf('change') >= 0 || f.indexOf('_co_') >= 0) return 'change_order';
  if (f.indexOf('field') >= 0) return 'field_report';
  if (f.indexOf('inspect') >= 0) return 'inspection_report';
  if (f.indexOf('ncr') >= 0) return 'ncr_log';
  if (f.indexOf('subcontractor') >= 0 || f.indexOf('subcon') >= 0) return 'subcontractor_report';
  if (f.indexOf('procurement') >= 0) return 'procurement_log';
  if (f.indexOf('resource') >= 0) return 'resource_report';
  if (f.indexOf('cost') >= 0) return 'cost_report';
  if (f.indexOf('past') >= 0 || f.indexOf('performance') >= 0) return 'past_performance_report';
  if (f.indexOf('safety') >= 0) return 'safety_report';
  if (f.indexOf('quality') >= 0 || f.indexOf('audit') >= 0) return 'quality_audit_report';
  if (f.indexOf('environ') >= 0) return 'environmental_report';
  if (f.indexOf('historic') >= 0) return 'historical_data';
  return 'monthly_report';
}
/* ===================== SIGNAL EXTRACTION ===================== */
function extractAuto_(dataB64, text, mimeType, fileName) {
  var validTypes = ['pay_application','monthly_report','rfi','oac_minutes','schedule_update',
    'change_order','field_report','inspection_report','ncr_log','subcontractor_report',
    'procurement_log','lookahead_schedule','resource_report','cost_report','past_performance_report',
    'safety_report','quality_audit_report','environmental_report','historical_data','time_phased_schedule',
    'contract_value','schedule_of_values','submittal','correspondence_notice','risk_register','commissioning_report','rfi_log','rfa_log'];
  var allFields = ["activities_constrained","activities_planned","actual_cost","actual_labor_hours","actual_percent_complete","amount_paid_to_date","analogous_overrun_pct","application_date","at_risk","audit_date","audit_score","baseline_contract_sum","budget_at_completion","change_order_count","completed_to_date","completion_year","compliance_rate","compliance_score","consumed_float","cost_rating","critical_deficiency_count","critical_findings","data_date","deficiency_count","delayed","document_date","document_risk_score","earned_value","environmental_issues_discussed","float_remaining","incident_rate","indirect_cost_actual","indirect_cost_plan","items_failed","items_inspected","long_lead_items_total","lookahead_weeks","material_cost_baseline","material_cost_current","ncr_closed","ncr_issued","ncr_open","on_time_deliveries","original_contingency","original_contract_sum","osha_recordable_incidents","outstanding_action_items","overall_rating","percent_complete_verified","period_to_date","planned_labor_hours","planned_percent_complete","planned_value","planned_value_to_date","project_end_date","project_start_date","quality_deficiencies_noted","quality_issues_discussed","quality_rating","remaining_contingency","report_date","report_period","response_time_days","revised_completion_date","revised_contract_sum","rfi_count","rfi_number","rfi_period_days","safety_actions_open","safety_incidents_discussed","schedule_rating","scheduled_deliveries","scheduled_value_total","similar_project_bac","similar_project_final_cost","subcontractor_disputes","subcontractor_issues_discussed","submittals_rejected","submittals_total","total_findings","total_float","total_manhours","violations","weather_days_discussed","weather_days_lost","work_period_from","work_period_to"];
  var prompt = 'You are a precise construction project-controls data extractor. Read this ONE document. ' +
    'First decide which single document type it is, from this list: ' + validTypes.join(', ') + '. ' +
    'Then extract every field below that actually appears in the document (use null when a field is not present). ' +
    'Return ONLY clean JSON in exactly this shape, no markdown: ' +
    '{"docType":"<one type from the list>","confidence":<0-1>,"fields":{<each field name>:<value or null>}}. ' +
    'The fields object must use these exact keys: ' + JSON.stringify(allFields) + '. ' +
    'Numbers as plain numbers (no $ or commas). Percentages as numbers 0-100. Do not compute CPI/SPI. ' +
    'Do not invent values. JSON only.';
  var raw;
  if (dataB64) {
    raw = claudePdfExtract_(prompt, dataB64, 2048, CLAUDE_MODEL_SONNET);
  } else if (text) {
    raw = claudeChat_(prompt, 'DOCUMENT TEXT:\n' + String(text).substring(0, 12000), 2048, CLAUDE_MODEL_SONNET);
  } else {
    throw new Error('No document data provided');
  }
  var parsed;
  try {
    parsed = JSON.parse(String(raw).replace(/```json/g,'').replace(/```/g,'').trim());
  } catch (e) {
    throw new Error('Auto-extract parse failed: ' + String(e) + ' :: ' + String(raw).substring(0,300));
  }
  var docType = String(parsed.docType || '').toLowerCase();
  if (validTypes.indexOf(docType) < 0) docType = guessTypeFromFilename_(fileName);
  return { docType: docType, confidence: parsed.confidence != null ? parsed.confidence : 0.7, fields: parsed.fields || {} };
}
function extractSignals_(body) {
  var id = body.id, docType = String(body.docType || '').toLowerCase();
  var text = body.text, dataB64 = body.dataBase64;
  var mimeType = body.mimeType || 'application/pdf';
  var fileName = body.fileName || (docType + '_' + Date.now());
  if (!id) return { ok: false, error: 'id is required' };
  if (!text && !dataB64) return { ok: false, error: 'Provide text or dataBase64' };
  var autoExtracted = null;
  if (!docType || docType === 'auto') {
    try {
      autoExtracted = extractAuto_(dataB64, text, mimeType, fileName);
      docType = autoExtracted.docType;
    } catch (eAuto) {
      return { ok: false, error: 'Auto extraction failed: ' + String(eAuto) };
    }
  }
  var parent = parentFolder_();
  var folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  var project = readProjectJson_(folder);
  if (!project) return { ok: false, error: 'project.json missing for ' + id };
  project.signalInputs = project.signalInputs || {
    bac:null,ev:null,ac:null,pv:null,actualPctComplete:null,plannedPctComplete:null,
    docRiskScore:null,baselineStart:null,baselineEnd:null,workPeriodFrom:null,workPeriodTo:null,docDate:null,
    totalFloat:null,consumedFloat:null,originalContingency:null,remainingContingency:null,
    rfiCount:null,rfiPeriodDays:null,submittalsTotal:null,submittalsRejected:null,
    changeOrderCount:null,baselineContractSum:null,revisedContractSum:null,
    weatherDaysLost:null,floatRemaining:null,oshaIncidentRate:null,totalManhours:null,
    qualityAuditScore:null,totalFindings:null,criticalFindings:null,
    environmentalComplianceRate:null,environmentalViolations:null,
    ncrIssued:null,ncrClosed:null,ncrOpen:null,subcontractorComplianceScore:null,
    longLeadItemsTotal:null,longLeadAtRisk:null,longLeadDelayed:null,
    activitiesPlanned:null,activitiesConstrained:null,lookaheadWeeks:null,
    plannedLaborHours:null,actualLaborHours:null,indirectCostPlan:null,indirectCostActual:null,
    materialCostBaseline:null,materialCostCurrent:null,overallRating:null,scheduleRating:null,
    costRating:null,qualityRating:null,analogousOverrunPct:null,analogousBac:null,analogousFinalCost:null,
    subcontractorIssuesDiscussed:null,outstandingActionItems:null,subcontractorDisputes:null,
    safetyIncidentsDiscussed:null,safetyActionsOpen:null,environmentalIssuesDiscussed:null,
    qualityIssuesDiscussed:null,weatherDaysDiscussed:null,rfiNumber:null,rfiResponseTimeDays:null,
    qualityDeficienciesNoted:null,itemsInspected:null,itemsFailed:null,criticalDeficiencyCount:null,
    rfiOpen:null,rfiOverdue:null,rfiAvgResponseDays:null,rfiOldestOpenDays:null,
    rfaTotal:null,rfaApproved:null,rfaRejected:null,rfaResubmit:null,rfaOpen:null,rfaAvgReviewDays:null,
    sources:{}
  };
  var si = project.signalInputs;
  var storedFileId = body.storedFileId || null;
  if (dataB64 && !storedFileId) {
    try {
      var sigFolder = ensureSubfolder_(folder, '_signals');
      var bytes = Utilities.base64Decode(dataB64);
      var blob2 = Utilities.newBlob(bytes, mimeType, fileName);
      var stored = sigFolder.createFile(blob2);
      storedFileId = stored.getId();
    } catch (e) {}
  }
  var fieldsWanted = extractionFieldsFor_(docType);
  var promptText = 'You are a precise construction project-controls data extractor. Read this ONE document ' +
    '(type: ' + docType + ') and return ONLY these fields as clean JSON (null if a field is not present): ' +
    JSON.stringify(fieldsWanted) + '. Do not compute indices. Do not invent values. ' +
    'Numbers as plain numbers (no $ or commas). Percentages as numbers 0-100. Return JSON only, no markdown.';
  var raw = '';
  var extracted = {};
  if (autoExtracted) {
    extracted = autoExtracted.fields || {};
  } else {
    try {
      if (dataB64) {
        raw = claudePdfExtract_(promptText, dataB64, 1024, CLAUDE_MODEL_SONNET);
      } else if (text) {
        raw = claudeChat_(promptText, 'DOCUMENT TEXT:\n' + text.substring(0, 12000), 1024, CLAUDE_MODEL_SONNET);
      } else {
        return { ok: false, error: 'No text or file to extract from' };
      }
    } catch (e) { return { ok: false, error: 'Claude extraction failed: ' + String(e) }; }
    try {
      extracted = JSON.parse(raw.replace(/```json/g,'').replace(/```/g,'').trim());
    } catch (e) { return { ok: false, error: 'Extraction parse failed: ' + String(e), raw: String(raw).substring(0,400) }; }
  }
  var now = new Date().toISOString();
  var applied = [];
  function setField(key, val) {
    if (val === null || val === undefined || val === '') return;
    si[key] = val; si.sources[key] = { docType: docType, value: val, at: now }; applied.push(key);
  }
  function setDate(key, val) {
    if (val === null || val === undefined || val === '' || String(val).toLowerCase() === 'null') return;
    si[key] = String(val); si.sources[key] = { docType: docType, value: String(val), at: now }; applied.push(key);
  }
  if (docType === 'contract_value') {
    setField('bac', numOrNull_(extracted.original_contract_sum));
    setDate('baselineStart', extracted.project_start_date);
    setDate('baselineEnd', extracted.project_end_date);
  } else if (docType === 'schedule_of_values') {
    setField('ev', numOrNull_(extracted.completed_to_date));
    if (si.bac === null) setField('bac', numOrNull_(extracted.scheduled_value_total));
    setDate('docDate', extracted.period_to_date);
  } else if (docType === 'pay_application') {
    setField('ac', numOrNull_(extracted.amount_paid_to_date));
    setField('actualPctComplete', numOrNull_(extracted.percent_complete_verified));
    if (si.bac === null) setField('bac', numOrNull_(extracted.original_contract_sum));
    if (si.ev === null) setField('ev', numOrNull_(extracted.completed_to_date));
    setDate('workPeriodFrom', extracted.work_period_from);
    setDate('workPeriodTo', extracted.work_period_to);
    setDate('docDate', extracted.application_date);
    if (numOrNull_(extracted.original_contingency) !== null) setField('originalContingency', numOrNull_(extracted.original_contingency));
    if (numOrNull_(extracted.remaining_contingency) !== null) setField('remainingContingency', numOrNull_(extracted.remaining_contingency));
  } else if (docType === 'time_phased_schedule') {
    setField('pv', numOrNull_(extracted.planned_value_to_date));
    setField('plannedPctComplete', numOrNull_(extracted.planned_percent_complete));
    setDate('docDate', extracted.data_date);
    if (numOrNull_(extracted.total_float) !== null) setField('totalFloat', numOrNull_(extracted.total_float));
    if (numOrNull_(extracted.consumed_float) !== null) setField('consumedFloat', numOrNull_(extracted.consumed_float));
  } else if (docType === 'monthly_report') {
    if (si.ev === null) setField('ev', numOrNull_(extracted.earned_value));
    if (si.ac === null) setField('ac', numOrNull_(extracted.actual_cost));
    if (si.pv === null) setField('pv', numOrNull_(extracted.planned_value));
    if (si.actualPctComplete === null) setField('actualPctComplete', numOrNull_(extracted.actual_percent_complete));
    if (si.plannedPctComplete === null) setField('plannedPctComplete', numOrNull_(extracted.planned_percent_complete));
    if (si.bac === null) setField('bac', numOrNull_(extracted.budget_at_completion));
    setDate('docDate', extracted.report_date);
  } else if (['rfi','submittal','oac_minutes','correspondence_notice','risk_register','inspection_report','field_report'].indexOf(docType) >= 0) {
    var risk = numOrNull_(extracted.document_risk_score);
    if (risk !== null) setField('docRiskScore', risk);
    setDate('docDate', extracted.document_date);
    if (docType === 'rfi') {
      var rfiCount = numOrNull_(extracted.rfi_count);
      if (rfiCount !== null) { si.rfiCount = (si.rfiCount || 0) + rfiCount; applied.push('rfiCount'); }
      if (numOrNull_(extracted.rfi_number) !== null) { si.rfiNumber = Math.max(si.rfiNumber || 0, numOrNull_(extracted.rfi_number)); applied.push('rfiNumber'); }
      if (numOrNull_(extracted.rfi_period_days) !== null) setField('rfiPeriodDays', numOrNull_(extracted.rfi_period_days));
      if (numOrNull_(extracted.response_time_days) !== null) setField('rfiResponseTimeDays', numOrNull_(extracted.response_time_days));
    }
    if (docType === 'oac_minutes') {
      if (numOrNull_(extracted.subcontractor_issues_discussed) !== null) setField('subcontractorIssuesDiscussed', numOrNull_(extracted.subcontractor_issues_discussed));
      if (numOrNull_(extracted.outstanding_action_items) !== null) setField('outstandingActionItems', numOrNull_(extracted.outstanding_action_items));
      if (numOrNull_(extracted.subcontractor_disputes) !== null) setField('subcontractorDisputes', numOrNull_(extracted.subcontractor_disputes));
      if (numOrNull_(extracted.safety_incidents_discussed) !== null) setField('safetyIncidentsDiscussed', numOrNull_(extracted.safety_incidents_discussed));
      if (numOrNull_(extracted.safety_actions_open) !== null) setField('safetyActionsOpen', numOrNull_(extracted.safety_actions_open));
      if (numOrNull_(extracted.environmental_issues_discussed) !== null) setField('environmentalIssuesDiscussed', numOrNull_(extracted.environmental_issues_discussed));
      if (numOrNull_(extracted.quality_issues_discussed) !== null) setField('qualityIssuesDiscussed', numOrNull_(extracted.quality_issues_discussed));
      if (numOrNull_(extracted.weather_days_discussed) !== null) setField('weatherDaysDiscussed', numOrNull_(extracted.weather_days_discussed));
    }
    if (docType === 'submittal') {
      if (numOrNull_(extracted.submittals_total) !== null) setField('submittalsTotal', numOrNull_(extracted.submittals_total));
      if (numOrNull_(extracted.submittals_rejected) !== null) setField('submittalsRejected', numOrNull_(extracted.submittals_rejected));
    }
    if (docType === 'field_report') {
      if (numOrNull_(extracted.weather_days_lost) !== null) setField('weatherDaysLost', numOrNull_(extracted.weather_days_lost));
      if (numOrNull_(extracted.float_remaining) !== null) setField('floatRemaining', numOrNull_(extracted.float_remaining));
      if (numOrNull_(extracted.quality_deficiencies_noted) !== null) setField('qualityDeficienciesNoted', numOrNull_(extracted.quality_deficiencies_noted));
    }
    if (docType === 'inspection_report') {
      if (numOrNull_(extracted.items_inspected) !== null) setField('itemsInspected', numOrNull_(extracted.items_inspected));
      if (numOrNull_(extracted.items_failed) !== null) setField('itemsFailed', numOrNull_(extracted.items_failed));
      if (numOrNull_(extracted.deficiency_count) !== null) setField('qualityDeficienciesNoted', numOrNull_(extracted.deficiency_count));
      if (numOrNull_(extracted.critical_deficiency_count) !== null) setField('criticalDeficiencyCount', numOrNull_(extracted.critical_deficiency_count));
    }
  } else if (docType === 'change_order') {
    if (numOrNull_(extracted.revised_contract_sum) !== null) setField('bac', numOrNull_(extracted.revised_contract_sum));
    if (numOrNull_(extracted.change_order_count) !== null) setField('changeOrderCount', numOrNull_(extracted.change_order_count));
    else { si.changeOrderCount = (si.changeOrderCount || 0) + 1; }
    if (numOrNull_(extracted.baseline_contract_sum) !== null && si.baselineContractSum === null) setField('baselineContractSum', numOrNull_(extracted.baseline_contract_sum));
    if (numOrNull_(extracted.revised_contract_sum) !== null) setField('revisedContractSum', numOrNull_(extracted.revised_contract_sum));
    var newEnd = extracted.revised_completion_date;
    if (newEnd && String(newEnd).toLowerCase() !== 'null' && newEnd !== si.baselineEnd) {
      var oldEnd = si.baselineEnd;
      si.baselineEnd = String(newEnd);
      si.sources['baselineEnd'] = { docType: 'change_order', value: String(newEnd), at: now };
      applied.push('baselineEnd');
      project.events = project.events || [];
      project.events.push({ event:'baseline_adjusted_eot', field:'baselineEnd', from:oldEnd, to:String(newEnd), via:'change_order', at:now });
    }
  } else if (docType === 'safety_report') {
    var incidentRate = numOrNull_(extracted.incident_rate);
    if (incidentRate === null && numOrNull_(extracted.osha_recordable_incidents) !== null && numOrNull_(extracted.total_manhours) !== null)
      incidentRate = round3_((numOrNull_(extracted.osha_recordable_incidents) / numOrNull_(extracted.total_manhours)) * 200000);
    if (incidentRate !== null) setField('oshaIncidentRate', incidentRate);
    if (numOrNull_(extracted.total_manhours) !== null) setField('totalManhours', numOrNull_(extracted.total_manhours));
    setDate('docDate', extracted.report_period);
  } else if (docType === 'quality_audit_report') {
    if (numOrNull_(extracted.audit_score) !== null) setField('qualityAuditScore', numOrNull_(extracted.audit_score));
    if (numOrNull_(extracted.total_findings) !== null) setField('totalFindings', numOrNull_(extracted.total_findings));
    if (numOrNull_(extracted.critical_findings) !== null) setField('criticalFindings', numOrNull_(extracted.critical_findings));
    setDate('docDate', extracted.audit_date);
  } else if (docType === 'environmental_report') {
    if (numOrNull_(extracted.compliance_rate) !== null) setField('environmentalComplianceRate', numOrNull_(extracted.compliance_rate));
    if (numOrNull_(extracted.violations) !== null) setField('environmentalViolations', numOrNull_(extracted.violations));
    setDate('docDate', extracted.report_date);
  } else if (docType === 'ncr_log') {
    if (numOrNull_(extracted.ncr_issued) !== null) setField('ncrIssued', numOrNull_(extracted.ncr_issued));
    if (numOrNull_(extracted.ncr_closed) !== null) setField('ncrClosed', numOrNull_(extracted.ncr_closed));
    if (numOrNull_(extracted.ncr_open) !== null) setField('ncrOpen', numOrNull_(extracted.ncr_open));
    setDate('docDate', extracted.report_period);
  } else if (docType === 'subcontractor_report') {
    var compScore = numOrNull_(extracted.compliance_score);
    if (compScore === null && numOrNull_(extracted.on_time_deliveries) !== null && numOrNull_(extracted.scheduled_deliveries) !== null && numOrNull_(extracted.scheduled_deliveries) !== 0)
      compScore = round3_(numOrNull_(extracted.on_time_deliveries) / numOrNull_(extracted.scheduled_deliveries));
    if (compScore !== null) setField('subcontractorComplianceScore', compScore);
    setDate('docDate', extracted.report_period);
  } else if (docType === 'procurement_log') {
    if (numOrNull_(extracted.long_lead_items_total) !== null) setField('longLeadItemsTotal', numOrNull_(extracted.long_lead_items_total));
    if (numOrNull_(extracted.at_risk) !== null) setField('longLeadAtRisk', numOrNull_(extracted.at_risk));
    if (numOrNull_(extracted.delayed) !== null) setField('longLeadDelayed', numOrNull_(extracted.delayed));
    setDate('docDate', extracted.report_date);
  } else if (docType === 'lookahead_schedule') {
    if (numOrNull_(extracted.activities_planned) !== null) setField('activitiesPlanned', numOrNull_(extracted.activities_planned));
    if (numOrNull_(extracted.activities_constrained) !== null) setField('activitiesConstrained', numOrNull_(extracted.activities_constrained));
    if (numOrNull_(extracted.lookahead_weeks) !== null) setField('lookaheadWeeks', numOrNull_(extracted.lookahead_weeks));
    setDate('docDate', extracted.report_date || new Date().toISOString().substring(0,10));
  } else if (docType === 'resource_report') {
    if (numOrNull_(extracted.planned_labor_hours) !== null) setField('plannedLaborHours', numOrNull_(extracted.planned_labor_hours));
    if (numOrNull_(extracted.actual_labor_hours) !== null) setField('actualLaborHours', numOrNull_(extracted.actual_labor_hours));
  } else if (docType === 'cost_report') {
    if (numOrNull_(extracted.indirect_cost_plan) !== null) setField('indirectCostPlan', numOrNull_(extracted.indirect_cost_plan));
    if (numOrNull_(extracted.indirect_cost_actual) !== null) setField('indirectCostActual', numOrNull_(extracted.indirect_cost_actual));
    if (numOrNull_(extracted.material_cost_baseline) !== null) setField('materialCostBaseline', numOrNull_(extracted.material_cost_baseline));
    if (numOrNull_(extracted.material_cost_current) !== null) setField('materialCostCurrent', numOrNull_(extracted.material_cost_current));
    setDate('docDate', extracted.report_date);
  } else if (docType === 'past_performance_report') {
    if (numOrNull_(extracted.overall_rating) !== null) setField('overallRating', numOrNull_(extracted.overall_rating));
    if (numOrNull_(extracted.schedule_rating) !== null) setField('scheduleRating', numOrNull_(extracted.schedule_rating));
    if (numOrNull_(extracted.cost_rating) !== null) setField('costRating', numOrNull_(extracted.cost_rating));
    if (numOrNull_(extracted.quality_rating) !== null) setField('qualityRating', numOrNull_(extracted.quality_rating));
  } else if (docType === 'historical_data') {
    if (numOrNull_(extracted.analogous_overrun_pct) !== null) setField('analogousOverrunPct', numOrNull_(extracted.analogous_overrun_pct));
    if (numOrNull_(extracted.similar_project_bac) !== null) setField('analogousBac', numOrNull_(extracted.similar_project_bac));
    if (numOrNull_(extracted.similar_project_final_cost) !== null) setField('analogousFinalCost', numOrNull_(extracted.similar_project_final_cost));
    setDate('docDate', extracted.completion_year ? String(extracted.completion_year) : null);
  }
  // v10.31: milestone snapshot accumulation (schedule_update / monthly_report).
  // Appends a dated snapshot to project-level milestoneHistory via si.__milestoneSnapshot,
  // consumed by extractSignals_ after merge.
  if ((docType === 'schedule_update' || docType === 'monthly_report') && extracted.milestones_json) {
    try {
      var msRaw = extracted.milestones_json;
      var msArr = typeof msRaw === 'string' ? JSON.parse(msRaw) : msRaw;
      if (Object.prototype.toString.call(msArr) === '[object Array]' && msArr.length) {
        si.__milestoneSnapshot = {
          at: (extracted.data_date || extracted.report_date || new Date().toISOString().slice(0,10)),
          milestones: msArr.map(function (m) {
            return { name: String(m.name || ''), baseline: m.baseline_date || null, forecast: m.forecast_date || null };
          }).filter(function (m) { return m.name; })
        };
      }
    } catch (e) { /* malformed table — skip snapshot */ }
  }
  if (docType === 'rfi_log') {
    if (numOrNull_(extracted.rfi_total) !== null) setField('rfiCount', numOrNull_(extracted.rfi_total));
    if (numOrNull_(extracted.rfi_open) !== null) setField('rfiOpen', numOrNull_(extracted.rfi_open));
    if (numOrNull_(extracted.rfi_overdue) !== null) setField('rfiOverdue', numOrNull_(extracted.rfi_overdue));
    if (numOrNull_(extracted.avg_response_days) !== null) setField('rfiAvgResponseDays', numOrNull_(extracted.avg_response_days));
    if (numOrNull_(extracted.rfi_period_days) !== null) setField('rfiPeriodDays', numOrNull_(extracted.rfi_period_days));
    if (numOrNull_(extracted.oldest_open_days) !== null) setField('rfiOldestOpenDays', numOrNull_(extracted.oldest_open_days));
    setDate('docDate', extracted.log_date);
  } else if (docType === 'rfa_log') {
    if (numOrNull_(extracted.rfa_total) !== null) setField('rfaTotal', numOrNull_(extracted.rfa_total));
    if (numOrNull_(extracted.rfa_approved) !== null) setField('rfaApproved', numOrNull_(extracted.rfa_approved));
    if (numOrNull_(extracted.rfa_rejected) !== null) setField('rfaRejected', numOrNull_(extracted.rfa_rejected));
    if (numOrNull_(extracted.rfa_resubmit) !== null) setField('rfaResubmit', numOrNull_(extracted.rfa_resubmit));
    if (numOrNull_(extracted.rfa_open) !== null) setField('rfaOpen', numOrNull_(extracted.rfa_open));
    if (numOrNull_(extracted.avg_review_days) !== null) setField('rfaAvgReviewDays', numOrNull_(extracted.avg_review_days));
    if (si.submittalsTotal === null && numOrNull_(extracted.rfa_total) !== null) setField('submittalsTotal', numOrNull_(extracted.rfa_total));
    if (si.submittalsRejected === null && numOrNull_(extracted.rfa_rejected) !== null) setField('submittalsRejected', numOrNull_(extracted.rfa_rejected));
    setDate('docDate', extracted.log_date);
  } else if (docType === 'schedule_update') {
    setField('plannedPctComplete', numOrNull_(extracted.planned_percent_complete));
    if (numOrNull_(extracted.planned_value_to_date) !== null) setField('pv', numOrNull_(extracted.planned_value_to_date));
    if (numOrNull_(extracted.total_float) !== null) setField('totalFloat', numOrNull_(extracted.total_float));
    if (numOrNull_(extracted.consumed_float) !== null) setField('consumedFloat', numOrNull_(extracted.consumed_float));
    if (numOrNull_(extracted.activities_planned) !== null) setField('activitiesPlanned', numOrNull_(extracted.activities_planned));
    if (numOrNull_(extracted.activities_constrained) !== null) setField('activitiesConstrained', numOrNull_(extracted.activities_constrained));
    if (numOrNull_(extracted.lookahead_weeks) !== null) setField('lookaheadWeeks', numOrNull_(extracted.lookahead_weeks));
  } else if (docType === 'commissioning_report') {
    var crisk = numOrNull_(extracted.document_risk_score);
    if (crisk !== null) setField('docRiskScore', crisk);
  }
  var computed = { cpi: null, spi: null };
  if (si.ev !== null && si.ac !== null && si.ac !== 0) computed.cpi = round3_(si.ev / si.ac);
  if (si.ev !== null && si.pv !== null && si.pv !== 0) computed.spi = round3_(si.ev / si.pv);
  if (computed.spi === null && si.actualPctComplete !== null && si.plannedPctComplete !== null && si.plannedPctComplete !== 0)
    computed.spi = round3_(si.actualPctComplete / si.plannedPctComplete);
  si.cpi = computed.cpi; si.spi = computed.spi;
  var missing = [];
  if (si.bac === null) missing.push({ field:'BAC', note:'Upload Contract Value or Pay Application' });
  if (si.ev === null)  missing.push({ field:'EV (completed-to-date)', note:'Upload Schedule of Values' });
  if (si.ac === null)  missing.push({ field:'AC (paid-to-date)', note:'Upload Pay Application' });
  if (si.pv === null && si.plannedPctComplete === null) missing.push({ field:'PV / planned %', note:'Upload Time-phased Schedule' });
  if (computed.cpi === null) missing.push({ field:'CPI', note:'Needs EV and AC' });
  if (computed.spi === null) missing.push({ field:'SPI', note:'Needs EV and PV (or actual & planned %)' });
  project.events = project.events || [];
  project.events.push({ event:'signals_extracted', docType:docType, appliedFields:applied, storedFileId:storedFileId, at:now });
  // v10.31: fold milestone snapshot into accumulating history (dedupe by date)
  if (project.signalInputs && project.signalInputs.__milestoneSnapshot) {
    var snap = project.signalInputs.__milestoneSnapshot;
    delete project.signalInputs.__milestoneSnapshot;
    project.milestoneHistory = project.milestoneHistory || [];
    project.milestoneHistory = project.milestoneHistory.filter(function (s) { return s && s.at !== snap.at; });
    project.milestoneHistory.push(snap);
    project.milestoneHistory.sort(function (a, b) { return String(a.at).localeCompare(String(b.at)); });
    if (project.milestoneHistory.length > 12) project.milestoneHistory = project.milestoneHistory.slice(-12);
  }
  writeProjectJson_(folder, project);
  return {
    ok:true, id:id, docType:docType,
    baselineStart:si.baselineStart, baselineEnd:si.baselineEnd,
    workPeriodFrom:si.workPeriodFrom, workPeriodTo:si.workPeriodTo,
    docDate:si.docDate, storedFileId:storedFileId,
    extracted:extracted, applied:applied, signalInputs:si,
    computed:computed, missing:missing,
    readyToRun:(computed.cpi !== null && computed.spi !== null),
    timestamp:now
  };
}
function extractionFieldsFor_(docType) {
  switch (docType) {
    case 'contract_value':      return ['original_contract_sum','project_start_date','project_end_date'];
    case 'schedule_of_values':  return ['completed_to_date','scheduled_value_total','period_to_date'];
    case 'pay_application':     return ['amount_paid_to_date','percent_complete_verified','original_contract_sum','completed_to_date','work_period_from','work_period_to','application_date','original_contingency','remaining_contingency'];
    case 'time_phased_schedule':return ['planned_value_to_date','planned_percent_complete','data_date','total_float','consumed_float'];
    case 'schedule_update':     return ['planned_percent_complete','planned_value_to_date','data_date','total_float','consumed_float','activities_planned','activities_constrained','lookahead_weeks','milestones_json'];
    case 'change_order':        return ['revised_contract_sum','revised_completion_date','change_order_date','change_order_count','baseline_contract_sum'];
    case 'monthly_report':      return ['earned_value','actual_cost','planned_value','actual_percent_complete','planned_percent_complete','budget_at_completion','report_date','milestones_json'];
    case 'rfi':                 return ['document_risk_score','document_date','rfi_count','rfi_period_days','rfi_number','submitted_date','response_date','response_time_days'];
    case 'submittal':           return ['document_risk_score','document_date','submittals_total','submittals_rejected'];
    case 'oac_minutes':         return ['document_risk_score','document_date','subcontractor_issues_discussed','outstanding_action_items','subcontractor_disputes','safety_incidents_discussed','safety_actions_open','environmental_issues_discussed','quality_issues_discussed','weather_days_discussed'];
    case 'correspondence_notice':
    case 'risk_register':       return ['document_risk_score','document_date'];
    case 'inspection_report':   return ['document_risk_score','document_date','items_inspected','items_passed','items_failed','deficiency_count','critical_deficiency_count'];
    case 'field_report':        return ['document_risk_score','document_date','weather_days_lost','float_remaining','quality_deficiencies_noted','safety_observations','environmental_observations','subcontractor_observations'];
    case 'commissioning_report':return ['document_risk_score','document_date'];
    case 'safety_report':       return ['osha_recordable_incidents','total_manhours','incident_rate','report_period'];
    case 'quality_audit_report':return ['total_findings','critical_findings','deficiency_count','audit_score','audit_date'];
    case 'environmental_report':return ['permit_conditions_total','violations','compliance_rate','report_date'];
    case 'ncr_log':             return ['ncr_issued','ncr_closed','ncr_open','ncr_overdue','report_period'];
    case 'subcontractor_report':return ['scheduled_deliveries','on_time_deliveries','compliance_score','report_period'];
    case 'procurement_log':     return ['long_lead_items_total','on_schedule','at_risk','delayed','report_date'];
    case 'lookahead_schedule':  return ['activities_planned','activities_constrained','constraint_rate','lookahead_weeks'];
    case 'resource_report':     return ['planned_labor_hours','actual_labor_hours','planned_equipment_days','actual_equipment_days'];
    case 'cost_report':         return ['indirect_cost_plan','indirect_cost_actual','material_cost_baseline','material_cost_current','report_date'];
    case 'past_performance_report': return ['overall_rating','schedule_rating','cost_rating','quality_rating','source'];
    case 'historical_data':     return ['analogous_overrun_pct','analogous_project_type','completion_year','similar_project_bac','similar_project_final_cost'];
    case 'rfi_log':             return ['rfi_total','rfi_open','rfi_answered','rfi_overdue','avg_response_days','rfi_period_days','oldest_open_days','log_date'];
    case 'rfa_log':             return ['rfa_total','rfa_approved','rfa_rejected','rfa_resubmit','rfa_open','avg_review_days','log_date'];
    default:                    return ['document_risk_score','document_date'];
  }
}
function numOrNull_(v) {
  if (v === null || v === undefined || v === '') return null;
  var n = Number(String(v).replace(/[^0-9.\-]/g,''));
  return isNaN(n) ? null : n;
}
function round3_(n) { return Math.round(n * 1000) / 1000; }
/* --- overwriteSignal_ --- */
function overwriteSignal_(body) {
  var id = body.id, field = body.field, newVal = body.value, reason = body.reason || '';
  if (!id || !field) return { ok: false, error: 'id and field are required' };
  var parent = parentFolder_(), folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  var project = readProjectJson_(folder);
  if (!project || !project.signalInputs) return { ok: false, error: 'No extracted signals to overwrite' };
  var si = project.signalInputs, oldVal = si.hasOwnProperty(field) ? si[field] : null;
  si[field] = numOrNull_(newVal);
  if (si.ev !== null && si.ac !== null && si.ac !== 0) si.cpi = round3_(si.ev / si.ac);
  if (si.ev !== null && si.pv !== null && si.pv !== 0) si.spi = round3_(si.ev / si.pv);
  project.events = project.events || [];
  project.events.push({ event:'signal_overwritten', field:field, from:oldVal, to:si[field], reason:reason, at:new Date().toISOString() });
  writeProjectJson_(folder, project);
  return { ok:true, id:id, field:field, from:oldVal, to:si[field], signalInputs:si };
}
/* --- resetSignals_ — canonical strong version (clears history, events, simulationSignals) --- */
function setProjectNumber_(body) {
  var id = body.id != null ? String(body.id).trim() : '';
  var newId = body.newId != null ? String(body.newId).trim() : '';
  if (!id || !newId) return { ok: false, error: 'id and newId are required' };
  if (/[\/\\"']/.test(newId)) return { ok: false, error: 'Project number contains invalid characters' };
  if (newId === id) return { ok: true, id: id, unchanged: true };
  var parent = parentFolder_();
  var folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  if (projectFolderById_(parent, newId)) return { ok: false, error: 'Project number already exists: ' + newId };
  var archive = directFolder_(parent, ARCHIVE_FOLDER_NAME);
  if (archive && archive.getFoldersByName(newId).hasNext()) return { ok: false, error: 'Project number exists in archive: ' + newId };
  var project = readProjectJson_(folder);
  if (!project) return { ok: false, error: 'project.json missing for ' + id };
  folder.setName(newId);
  var oldId = project.id;
  project.id = newId;
  project.events = project.events || [];
  project.events.push({ event: 'project_number_changed', from: oldId, to: newId, at: new Date().toISOString() });
  writeProjectJson_(folder, project);
  return { ok: true, id: newId, from: oldId };
}
function resetSignals_(body) {
  var id = body.id;
  if (!id) return { ok: false, error: 'id is required' };
  var parent = parentFolder_(), folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  var project = readProjectJson_(folder);
  if (!project) return { ok: false, error: 'project.json missing for ' + id };
  project.signals = null;
  project.signalInputs = null;
  project.simulationSignals = null;
  project.history = [];
  // v10.25: preserve upload history so Uploaded Documents survives reset
  var uploadEvents = (project.events || []).filter(function(e) {
    return e && (e.event === 'signals_extracted');
  });
  project.events = uploadEvents;
  project.events.push({ event: 'signals_reset', at: new Date().toISOString() });
  ['documents', 'uploadedDocuments', 'docs'].forEach(function (k) {
    if (Object.prototype.toString.call(project[k]) === '[object Array]') project[k] = [];
  });
  project.status = 'awaiting_ingest';
  project.reportingPeriod = null;
  project.derivedState = null;
  // do NOT clear corpus — that is the Technical Auditor store
  writeProjectJson_(folder, project);
  return { ok: true, id: id, reset: true };
}
/* --- saveHistory_ --- */
function saveHistory_(body) {
  var id = body.id, snapshot = body.snapshot;
  if (!id) return { ok: false, error: 'id is required' };
  if (!snapshot) return { ok: false, error: 'snapshot is required' };
  var parent = parentFolder_(), folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  var historyFolder = directFolder_(folder, '_history') || folder.createFolder('_history');
  var period = snapshot.period || new Date().toISOString().substring(0,7);
  var fileName = period + '_snapshot.json';
  var existing = historyFolder.getFilesByName(fileName);
  while (existing.hasNext()) existing.next().setTrashed(true);
  historyFolder.createFile(Utilities.newBlob(JSON.stringify(snapshot, null, 2), 'application/json', fileName));
  var project = readProjectJson_(folder);
  if (project) {
    project.events = project.events || [];
    project.events.push({ event:'snapshot_saved', period:period, total_modules: snapshot.summary ? snapshot.summary.total_modules : null, governance_state: snapshot.governance ? snapshot.governance.state : null, at:new Date().toISOString() });
    writeProjectJson_(folder, project);
  }
  return { ok:true, period:period, fileName:fileName };
}
/* --- getHistory_ --- */
function getHistory_(id) {
  if (!id) return { ok: false, error: 'id is required' };
  var parent = parentFolder_(), folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  var historyFolder = directFolder_(folder, '_history');
  if (!historyFolder) return { ok:true, history:[] };
  var snapshots = [];
  var files = historyFolder.getFilesByType('application/json');
  while (files.hasNext()) {
    try { snapshots.push(JSON.parse(files.next().getBlob().getDataAsString())); } catch(e) {}
  }
  snapshots.sort(function(a,b){ return String(a.period).localeCompare(String(b.period)); });
  return { ok:true, history:snapshots };
}
/* --- saveAuditResult_ --- */
function saveAuditResult_(body) {
  var id = body.id;
  if (!id) return { ok: false, error: 'id is required' };
  var parent = parentFolder_(), folder = projectFolderById_(parent, id);
  if (!folder) return { ok: false, error: 'Project not found: ' + id };
  var auditsFolder = directFolder_(folder, '_audits') || folder.createFolder('_audits');
  var auditId = 'audit_' + new Date().getTime();
  var result = { audit_id:auditId, run_at:body.run_at || new Date().toISOString(), corpus_files:body.corpus_files||[], submittal_file:body.submittal_file||'', items:body.items||[], overall_verdict:body.overall_verdict||'', summary:body.summary||'' };
  auditsFolder.createFile(Utilities.newBlob(JSON.stringify(result, null, 2), 'application/json', auditId + '.json'));
  var project = readProjectJson_(folder);
  if (project) {
    project.events = project.events || [];
    project.events.push({ event:'audit_saved', audit_id:auditId, at:result.run_at, verdict:result.overall_verdict, submittal:result.submittal_file });
    writeProjectJson_(folder, project);
  }
  return { ok:true, audit_id:auditId };
}
/* ------------------------------ TTS ----------------------------- */
function cleanTextForSpeech_(text) {
  var t = String(text || '');
  t = t.replace(/[*][*]([^*]+)[*][*]/g,'$1').replace(/[*]([^*]+)[*]/g,'$1').replace(/[*]/g,'');
  t = t.replace(/#{1,6} */g,'').replace(/`/g,'').replace(/_/g,'').replace(/[#~^]/g,'');
  t = t.replace(/[|]/g,', ').replace(/> */g,'').replace(/·/g,'. ').replace(/—/g,', ').replace(/ {2,}/g,' ').trim();
  return t.substring(0,400);
}
function tts_(body) {
  var text = body.text;
  if (!text) return { ok: false, error: 'text is required' };
  var voice = body.voice || TTS_DEFAULT_VOICE;
  var cleanText = cleanTextForSpeech_(text);
  if (!cleanText || cleanText.length < 3) return { ok: false, error: 'text too short after cleaning' };
  var resp = UrlFetchApp.fetch(OPENAI_API_BASE + '/audio/speech', {
    method:'POST', contentType:'application/json',
    headers:{ 'Authorization': 'Bearer ' + openaiKey_() },
    payload: JSON.stringify({ model:'tts-1', input:cleanText, voice:voice, response_format:'mp3', speed:1.25 }),
    muteHttpExceptions:true
  });
  if (resp.getResponseCode() !== 200) return { ok:false, error:'TTS ' + resp.getResponseCode() + ': ' + resp.getContentText().substring(0,300) };
  var blob = resp.getBlob();
  return { ok:true, audioBase64:Utilities.base64Encode(blob.getBytes()), mime:blob.getContentType()||'audio/mpeg', voice:voice };
}
/* ========================= TECHNICAL AUDITOR ========================= */
function ingestCorpus_(body) {
  var id=body.id, name=body.name, docType=body.docType, mimeType=body.mimeType, data=body.dataBase64;
  if (!id) return { ok:false, error:'id is required' };
  if (!name) return { ok:false, error:'name is required' };
  if (!docType) return { ok:false, error:'docType is required' };
  if (!data) return { ok:false, error:'dataBase64 is required' };
  var validTypes = ['specification','code_of_practice','user_requirement'];
  if (validTypes.indexOf(docType) < 0) return { ok:false, error:'docType must be one of: ' + validTypes.join(', ') };
  var parent = parentFolder_(), projFolder = projectFolderById_(parent, id);
  if (!projFolder) return { ok:false, error:'Project not found: ' + id };
  var corpusFolder = ensureSubfolder_(projFolder, CORPUS_FOLDER_NAME);
  var bytes = Utilities.base64Decode(data);
  var blob = Utilities.newBlob(bytes, mimeType || 'application/octet-stream', name);
  var file = corpusFolder.createFile(blob);
  var meta = { fileId:file.getId(), name:name, docType:docType, mimeType:mimeType, ingestedAt:new Date().toISOString() };
  var metaName = name + '.meta.json';
  var existing = corpusFolder.getFilesByName(metaName);
  while (existing.hasNext()) existing.next().setTrashed(true);
  corpusFolder.createFile(metaName, JSON.stringify(meta, null, 2), 'application/json');
  return { ok:true, corpus:meta };
}
function listCorpus_(id) {
  if (!id) return { ok:false, error:'id is required' };
  var parent = parentFolder_(), projFolder = projectFolderById_(parent, id);
  if (!projFolder) return { ok:false, error:'Project not found: ' + id };
  var corpusFolder = directFolder_(projFolder, CORPUS_FOLDER_NAME);
  if (!corpusFolder) return { ok:true, corpus:[] };
  var corpus = [];
  var files = corpusFolder.getFilesByType('application/json');
  while (files.hasNext()) {
    var f = files.next();
    if (!f.getName().endsWith('.meta.json')) continue;
    try { corpus.push(JSON.parse(f.getBlob().getDataAsString())); } catch(e) {}
  }
  corpus.sort(function(a,b){ return a.ingestedAt.localeCompare(b.ingestedAt); });
  return { ok:true, corpus:corpus };
}
function listAuditResults_(id) {
  if (!id) return { ok:false, error:'id is required' };
  var parent = parentFolder_(), projFolder = projectFolderById_(parent, id);
  if (!projFolder) return { ok:false, error:'Project not found: ' + id };
  var auditFolder = directFolder_(projFolder, AUDIT_FOLDER_NAME);
  if (!auditFolder) return { ok:true, results:[] };
  var results = [];
  var files = auditFolder.getFiles();
  while (files.hasNext()) {
    var f = files.next();
    results.push({ fileId:f.getId(), name:f.getName(), createdAt:f.getDateCreated().toISOString() });
  }
  results.sort(function(a,b){ return b.createdAt.localeCompare(a.createdAt); });
  return { ok:true, results:results };
}
function audit_(body) {
  var id=body.id, reviewType=body.reviewType||'material_submittal',
      submissionName=body.submissionName||'submission', submissionMime=body.submissionMime||'application/pdf',
      submissionBase64=body.submissionBase64, corpusIds=body.corpusIds||[];
  if (!id) return { ok:false, error:'id is required' };
  if (!submissionBase64) return { ok:false, error:'submissionBase64 is required' };
  var parent = parentFolder_(), projFolder = projectFolderById_(parent, id);
  if (!projFolder) return { ok:false, error:'Project not found: ' + id };
  var corpusFolder = directFolder_(projFolder, CORPUS_FOLDER_NAME);
  var corpusContext = '';
  if (corpusFolder && corpusIds.length > 0) {
    corpusIds.forEach(function(fileId) {
      try {
        var file = DriveApp.getFileById(fileId);
        var mime = file.getMimeType();
        if (mime === 'application/pdf' || mime.indexOf('text') === 0)
          corpusContext += '\n\n--- REFERENCE: ' + file.getName() + ' ---\n' + file.getBlob().getDataAsString().substring(0, 8000);
      } catch(e) { corpusContext += '\n\n[Could not read: ' + fileId + ']'; }
    });
  }
  var reviewLabel = reviewType === 'drawing' ? 'Engineering Drawing' : 'Material Submittal';
  var prompt = 'You are a technical auditor for a public capital construction project. Review the submitted ' + reviewLabel +
    ' against the provided reference documents.\n\nREFERENCE DOCUMENTS:' + (corpusContext || ' [No corpus]') + '\n\n' +
    'SUBMISSION: ' + submissionName + '\n\nSTATUS DEFINITIONS:\n"Approved": fully complies.\n"Approved as Noted": exceeds requirement.\n"Rejected": does not meet minimum.\n"Remark": clarification required.\n\n' +
    'OUTPUT: Clean JSON array only. No markdown. Each element:\n{"item_no":N,"item_submitted":"...","remark":"...","citation":"...","status":"Approved|Approved as Noted|Rejected|Remark"}';
  var rawText = '';
  try {
    var isImage = (submissionMime === 'image/png' || submissionMime === 'image/jpeg' || submissionMime === 'image/gif' || submissionMime === 'image/webp');
    if (isImage) {
      rawText = openaiMultimodal_(prompt, submissionBase64, submissionMime, 2048);
    } else {
      var auditFolder2 = ensureSubfolder_(projFolder, AUDIT_FOLDER_NAME);
      var auditBytes = Utilities.base64Decode(submissionBase64);
      var auditBlob = Utilities.newBlob(auditBytes, submissionMime, submissionName);
      var tempAuditFile = auditFolder2.createFile(auditBlob);
      var auditOcrText = extractTextFromPDFViaDriveOCR_(tempAuditFile.getId());
      tempAuditFile.setTrashed(true);
      if (auditOcrText && auditOcrText.length > 100) {
        rawText = claudeChat_('You are a technical auditor. Return clean JSON array only. No markdown.', prompt + '\n\nSUBMISSION TEXT:\n' + auditOcrText.substring(0,12000), 2048, CLAUDE_MODEL_OPUS);
      } else {
        rawText = openaiMultimodal_(prompt, submissionBase64, submissionMime, 2048);
      }
    }
  } catch(e) { return { ok:false, error:'Audit AI call failed: ' + String(e) }; }
  var items = [];
  try {
    var cleaned2 = rawText.replace(/```json/g,'').replace(/```/g,'').trim();
    items = JSON.parse(cleaned2);
    if (!Array.isArray(items)) items = [items];
  } catch(e) { return { ok:false, error:'Failed to parse audit JSON: ' + String(e), raw:rawText.substring(0,500) }; }
  var timestamp = new Date().toISOString().replace(/[:.]/g,'-');
  var csvName = 'audit_' + reviewType + '_' + timestamp + '.csv';
  var csvLines = ['"Item No.","Item Submitted","Remark","Citation","Status"'];
  items.forEach(function(row) {
    csvLines.push(['"'+String(row.item_no||'').replace(/"/g,'""')+'"','"'+String(row.item_submitted||'').replace(/"/g,'""')+'"','"'+String(row.remark||'').replace(/"/g,'""')+'"','"'+String(row.citation||'').replace(/"/g,'""')+'"','"'+String(row.status||'').replace(/"/g,'""')+'"'].join(','));
  });
  var auditFolder3 = ensureSubfolder_(projFolder, AUDIT_FOLDER_NAME);
  auditFolder3.createFile(csvName, csvLines.join('\n'), 'text/csv');
  var counts = { Approved:0,'Approved as Noted':0,Rejected:0,Remark:0 };
  items.forEach(function(row){ if (counts.hasOwnProperty(row.status)) counts[row.status]++; else counts['Remark']++; });
  return { ok:true, projectId:id, reviewType:reviewType, submission:submissionName, timestamp:new Date().toISOString(), itemCount:items.length, summary:counts, items:items, csvName:csvName, csvContent:csvLines.join('\n') };
}
/* ===== v10.35: PORTFOLIO HEALTH PERSISTENCE (one JSON, event-driven) =====
   Written after an upload-triggered signal run; read by the Health dialog.
   Nothing recomputes on page load. */
function portfolioHealthFile_() {
  var parent = parentFolder_();
  var files = parent.getFilesByName('portfolio_health.json');
  return files.hasNext() ? files.next() : null;
}
function readPortfolioHealth_() {
  var f = portfolioHealthFile_();
  if (!f) return null;
  try { return JSON.parse(f.getBlob().getDataAsString()); } catch (e) { return null; }
}
function savePortfolioHealth_(body) {
  if (!body.health) return { ok: false, error: 'health payload required' };
  var health = body.health;
  // v10.36: the portfolio JSON is the single readable source for the chat —
  // embed the current project roster (id, name, sector, status) at save time.
  health.projects = listProjectsSlim_().map(function (p) {
    return { id: p.id, name: p.name, sector: p.sector, status: p.status, updatedAt: p.updatedAt };
  });
  health.savedAt = new Date().toISOString();
  health.trigger = body.trigger || 'upload';
  health.triggerProjectId = body.id || null;
  var content = JSON.stringify(health, null, 2);
  var f = portfolioHealthFile_();
  if (f) f.setContent(content);
  else parentFolder_().createFile('portfolio_health.json', content, 'application/json');
  return { ok: true, savedAt: health.savedAt };
}

/* ========================= CAT 8 — ML & AI PORTFOLIO ANALYSIS ========================= */
function portfolioAnalyze_(body) {
  var id = body.id, portfolio = body.portfolio || [];
  if (!id) return { ok:false, error:'id is required' };
  if (portfolio.length < 2) return { ok:true, id:id, insufficient_data:true, message:'Portfolio too small for anomaly detection — need at least 3 projects with signal data', results:{} };
  var vectors = portfolio.filter(function(p){ return p.cpi !== null && p.cpi !== undefined && p.spi !== null && p.spi !== undefined; })
    .map(function(p){ return { id:p.id, v:[p.cpi||1.0, p.spi||1.0, p.docRiskScore||0.0, (p.actualPctComplete||50)/100] }; });
  var current = portfolio.find(function(p){ return p.id === id; });
  if (!current || !current.cpi) return { ok:true, id:id, insufficient_data:true, message:'Current project has no signal data — upload EVM documents first', results:{} };
  var currentVec = [current.cpi||1.0, current.spi||1.0, current.docRiskScore||0.0, (current.actualPctComplete||50)/100];
  var n = vectors.length;
  if (n < 2) return { ok:true, id:id, insufficient_data:true, message:'Insufficient projects with signal data in portfolio', results:{} };
  var centroid = [0,0,0,0];
  vectors.forEach(function(v){ v.v.forEach(function(x,i){ centroid[i] += x/n; }); });
  var variance = [0,0,0,0];
  vectors.forEach(function(v){ v.v.forEach(function(x,i){ variance[i] += Math.pow(x-centroid[i],2)/n; }); });
  var stddev = variance.map(function(v){ return Math.sqrt(v)||0.001; });
  function mahalanobis(vec){ return Math.sqrt(vec.reduce(function(sum,x,i){ return sum+Math.pow((x-centroid[i])/stddev[i],2); },0)); }
  var allDists = vectors.map(function(v){ return mahalanobis(v.v); });
  var currentDist = mahalanobis(currentVec);
  var maxDist = Math.max.apply(null,allDists);
  var meanDist = allDists.reduce(function(a,b){return a+b;},0)/allDists.length;
  var threshold = meanDist + 1.5*stddev.reduce(function(a,b){return a+b;},0);
  var anomalyScore = Math.min(1, currentDist/(maxDist||1));
  var isoStatus = currentDist>threshold?'Red':currentDist>threshold*0.7?'Amber':currentDist>threshold*0.4?'Yellow':'Green';
  var isolationForest = { method_class:'Isolation_Forest', status_color:isoStatus, anomaly_score:Math.round(anomalyScore*100)/100, distance:Math.round(currentDist*100)/100, threshold:Math.round(threshold*100)/100, portfolio_size:n, is_anomaly:currentDist>threshold, evidence_metric:'Isolation Forest: anomaly score '+Math.round(anomalyScore*100)+'%' };
  var cpiRank = vectors.filter(function(v){return v.v[0]<=currentVec[0];}).length/n;
  var spiRank = vectors.filter(function(v){return v.v[1]<=currentVec[1];}).length/n;
  var compositeRank = (cpiRank+spiRank)/2;
  var outlierStatus = compositeRank<=0.15?'Red':compositeRank<=0.30?'Amber':compositeRank<=0.45?'Yellow':'Green';
  var portfolioOutlier = { method_class:'Portfolio_Outlier', status_color:outlierStatus, cpi_percentile:Math.round(cpiRank*100), spi_percentile:Math.round(spiRank*100), composite_percentile:Math.round(compositeRank*100), evidence_metric:'Portfolio percentile: '+Math.round(compositeRank*100)+'%' };
  var history = body.history || [], trajectoryStatus='Green', trajectoryDesc='No history available', trend=0;
  if (history.length >= 2) {
    var recent = history.slice(-3);
    var cpiValues = recent.map(function(h){ return h.signal_inputs?h.signal_inputs.cpi:null; }).filter(function(v){return v!==null;});
    if (cpiValues.length >= 2) {
      trend = (cpiValues[cpiValues.length-1]-cpiValues[0])/cpiValues.length;
      trajectoryStatus = trend>=0.01?'Green':trend>=-0.01?'Yellow':trend>=-0.03?'Amber':'Red';
      trajectoryDesc = 'CPI trend: '+(trend>=0?'+':'')+Math.round(trend*1000)/10+'% per period';
    }
  }
  var trajectoryClassifier = { method_class:'Trajectory_Classifier', status_color:trajectoryStatus, trend:Math.round(trend*1000)/1000, periods_analyzed:history.length, insufficient_data:history.length<2, evidence_metric:trajectoryDesc };
  var similarProjects = vectors.filter(function(v){ if(v.id===id)return false; return Math.sqrt(Math.pow(v.v[0]-currentVec[0],2)+Math.pow(v.v[1]-currentVec[1],2)+Math.pow(v.v[2]-currentVec[2],2))<0.15; });
  var patternStatus='Green', patternDesc='No similar distress pattern found in portfolio';
  if (similarProjects.length>0) { var avgCPI=similarProjects.reduce(function(s,v){return s+v.v[0];},0)/similarProjects.length; patternStatus=avgCPI<0.90?'Red':avgCPI<0.95?'Amber':'Yellow'; patternDesc=similarProjects.length+' project(s) show similar signal pattern'; }
  var crossProjectPattern = { method_class:'Cross_Project_Pattern', status_color:patternStatus, similar_project_count:similarProjects.length, evidence_metric:patternDesc };
  var scores=[anomalyScore,1-compositeRank,0.5];
  if (history.length>=2&&trend!==0) scores.push(Math.min(1,Math.abs(trend)*20));
  var compositeAnomaly=Math.round(scores.reduce(function(a,b){return a+b;},0)/scores.length*100)/100;
  var anomalyStatusFinal=compositeAnomaly>=0.70?'Red':compositeAnomaly>=0.50?'Amber':compositeAnomaly>=0.30?'Yellow':'Green';
  var anomalyScoreResult = { method_class:'Anomaly_Score', status_color:anomalyStatusFinal, composite_score:compositeAnomaly, evidence_metric:'Composite anomaly score: '+Math.round(compositeAnomaly*100)+'%' };
  return { ok:true, id:id, portfolio_size:n, results:{ cat8_1_isolation_forest:isolationForest, cat8_2_portfolio_outlier:portfolioOutlier, cat8_3_trajectory_classifier:trajectoryClassifier, cat8_4_cross_project_pattern:crossProjectPattern, cat8_5_anomaly_score:anomalyScoreResult }, timestamp:new Date().toISOString() };
}
/* ----------------------------- output --------------------------- */
function out_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(ContentService.MimeType.JSON);
}
/* ----------------------------- tests ---------------------------- */
function testHealth() { Logger.log(JSON.stringify(okHealth_(), null, 2)); }
function testClaude() { Logger.log('Claude Sonnet test result: ' + claudeChat_('You are a test assistant.','Respond with exactly: {"test":"ok"}',50,CLAUDE_MODEL_SONNET)); }
function testClaudeOpus() { Logger.log('Claude Opus test result: ' + claudeChat_('You are a test assistant.','Respond with exactly: {"test":"ok"}',50,CLAUDE_MODEL_OPUS)); }
function testClaudeKey() { var key=PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY'); Logger.log('Key exists: '+(key?'YES, length='+key.length:'NO - MISSING')); }
function testLib() { var lib=readLib_(); Logger.log('Lib files found: '+lib.length); lib.forEach(function(f){Logger.log(f.name+' — '+f.content.length+' chars');}); }
function seedDemoHistory(id, series) {
  var parent = parentFolder_(), folder = projectFolderById_(parent, id);
  if (!folder) { Logger.log('not found ' + id); return; }
  var project = readProjectJson_(folder);
  if (!project) { Logger.log('no json ' + id); return; }
  var historyFolder = directFolder_(folder, '_history') || folder.createFolder('_history');
  project.history = [];
  series.forEach(function(pt) {
    var snap = { period: pt.period, summary: { total_modules: null }, signal_inputs: { cpi: pt.cpi, spi: pt.spi } };
    var fn = pt.period + '_snapshot.json';
    var ex = historyFolder.getFilesByName(fn); while (ex.hasNext()) ex.next().setTrashed(true);
    historyFolder.createFile(Utilities.newBlob(JSON.stringify(snap, null, 2), 'application/json', fn));
    project.history.push({ period: pt.period, signal_inputs: { cpi: pt.cpi, spi: pt.spi } });
  });
  project.events = project.events || [];
  project.events.push({ event: 'history_seeded', periods: series.length, at: new Date().toISOString() });
  writeProjectJson_(folder, project);
  Logger.log('seeded ' + id + ' with ' + series.length + ' periods');
}
function seedDemoHistoryAll() {
  seedDemoHistory('14', [ {period:'2026-04',cpi:0.97,spi:0.97}, {period:'2026-05',cpi:0.95,spi:0.95}, {period:'2026-06',cpi:0.94,spi:0.93} ]);
  seedDemoHistory('10', [ {period:'2026-04',cpi:0.96,spi:0.97}, {period:'2026-05',cpi:0.95,spi:0.94}, {period:'2026-06',cpi:0.93,spi:0.94} ]);
  seedDemoHistory('11', [ {period:'2026-04',cpi:0.94,spi:0.95}, {period:'2026-05',cpi:0.92,spi:0.92}, {period:'2026-06',cpi:0.90,spi:0.90} ]);
}
function testPortfolioAnalyze() {
  var result = portfolioAnalyze_({
    id: '06',
    portfolio: [
      {id:'06',cpi:0.929,spi:0.911,docRiskScore:0.45,actualPctComplete:37},
      {id:'07',cpi:0.95,spi:0.93,docRiskScore:0.30,actualPctComplete:45},
      {id:'08',cpi:1.02,spi:1.01,docRiskScore:0.15,actualPctComplete:60}
    ],
    history: []
  });
  Logger.log(JSON.stringify(result, null, 2));
}
