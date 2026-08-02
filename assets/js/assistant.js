/* ============================================================
   Lin Project Radar — assistant.js
   Floating GUIDED HELP assistant, present on every page.
   SCRIPTED: answers come only from the curated knowledge base
   in knowledge.js (LIN_KNOWLEDGE). No LLM, no API call, no
   backend, no key. Out-of-scope questions get an honest
   "not in my script" answer pointing to the knowledge library.
   ============================================================ */

(function () {
  "use strict";

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const SUGGESTIONS = [
    "What are the platform's boundaries?",
    "Status of this project?",
    "Portfolio overview",
    "How does the fairness gate work?",
    "What is CUSUM?"
  ];

  /* ---------- live (still scripted) project & portfolio answers ----------
     These read the current synthetic data and decision.js output at answer
     time — no hard-coding, no LLM, no network. The phrasing is templated. */

  const SECTOR_LABEL = { design: "Design", construction: "Construction", combined: "Hybrid" };

  /* T12b. Server-created projects carry no sector and no reportingPeriod, so the old templates
     rendered "( sector, period undefined)" straight at the user. Absent fields are omitted rather
     than printed as empty or as the word undefined. */
  function sectorPhrase(p) {
    const sec = SECTOR_LABEL[p && p.sector] || (p && p.sector);
    return sec ? ` (${sec} sector)` : "";
  }
  function sectorPeriodPhrase(p) {
    const sec = SECTOR_LABEL[p && p.sector] || (p && p.sector);
    const per = p && p.reportingPeriod;
    const bits = [];
    if (sec) bits.push(`${sec} sector`);
    if (per) bits.push(`period ${per}`);
    return bits.length ? ` (${bits.join(", ")})` : "";
  }

  // T12b. Three states, not two, and the assistant now says plainly which one it is in.
  //
  // The old code asked hasSignals(p), the legacy client-side p.signals blob, and treated its
  // absence as "no signals yet, nothing has been ingested." That was wrong for a project the
  // server has already analysed: it carries a stored result, readable through LinResults and
  // getProjectFusion, and does not carry that blob. The assistant told the user a project was
  // unanalysed when it was not, using the retired "awaiting ingest" wording besides.
  //
  // The per-signal numbers below (CPI, SPI, the Monte Carlo percentiles, the CUSUM drift) are
  // read from that legacy blob and are NOT part of the stored server row in this form, so a
  // stored-only project cannot honestly be given them. Rather than inventing them or hiding the
  // status, the assistant says what it has and says what it does not have.
  function projectAnswer(p) {
    const legacy = !!(window.hasSignals && hasSignals(p));
    const stored = !!(window.LinResults && LinResults.hasResult(p));

    if (!legacy && !stored) {
      return {
        title: `${p.id}: awaiting analysis`,
        body: `${p.name}${sectorPhrase(p)} has not been analysed yet. Upload its documents to run extraction and computation. Nothing is fabricated until that has happened.`
      };
    }

    const d = deriveDecision(p);
    if (!legacy) {
      return {
        title: `${p.id}: status`,
        body: `${p.name}${sectorPeriodPhrase(p)}. ` +
          `Status ${d.healthState}, signal breakdown: ${d.conflictType}. ` +
          `Recommended action: ${d.action} Authority: ${d.authority}. ` +
          `Fairness gate: ${d.fairnessGateRequired ? "required before any formal action" : "not required"}. ` +
          `I do not have the per-signal figures (EVM, Monte Carlo, CUSUM, document risk) for this project; see its Detail page for the full signal ledger.`
      };
    }

    const s = p.signals;
    return {
      title: `${p.id}: status`,
      body: `${p.name}${sectorPeriodPhrase(p)}. ` +
        `Status ${d.healthState}, signal breakdown: ${d.conflictType}. ` +
        `Signals. EVM: ${s.evm.status} (CPI ${s.evm.cpi.toFixed(2)}, SPI ${s.evm.spi.toFixed(2)}); ` +
        `Monte Carlo: ${s.mc.status} (P80 EAC +${s.mc.p80eacOverrunPct.toFixed(1)}%, P(delay) ${s.mc.pMilestoneDelay.toFixed(2)}); ` +
        `CUSUM: ${s.cusum.status} (drift ${s.cusum.drift.toFixed(1)} vs threshold ${s.cusum.threshold.toFixed(1)}${s.cusum.breached ? ", breached" : ""}); ` +
        `document risk: ${s.doc.status} (score ${s.doc.score.toFixed(2)}). ` +
        `Recommended action: ${d.action} Authority: ${d.authority}. ` +
        `Fairness gate: ${d.fairnessGateRequired ? "required before any formal action" : "not required"}.`
    };
  }

  function portfolioAnswer() {
    // 5-state fused bands (Complete/Green/Yellow/Amber/Red); the signal-class
    // fallback may still emit "Red-review", which we fold into the Red tally.
    const counts = { "Complete": 0, "Green": 0, "Yellow": 0, "Amber": 0, "Red": 0 };
    const reds = [], gated = [];
    let empty = 0;
    LIN_PROJECTS.forEach((p) => {
      // T12b. A full row used to be counted here only if it carried the legacy p.signals blob
      // (hasSignals(p)); a project the server had analysed, without that blob, fell through to
      // the slim branch, found nothing there either, and was counted as awaiting analysis. It
      // now asks about the stored row directly. Slim rows are unaffected: they never carry
      // p.signals and were always meant to be read through slimStatusLabel.
      let label = null;
      if (window.LinResults && LinResults.hasResult(p)) {
        const d = deriveDecision(p);
        label = d.healthState;
        if (d.fairnessGateRequired) gated.push(p.id);
      } else if (p && p.slim && typeof slimStatusLabel === "function") {
        label = slimStatusLabel(p);           // null → genuinely not yet analysed
      }
      if (!label) { empty++; return; }
      const isRed = String(label).indexOf("Red") >= 0;
      const key = isRed ? "Red" : (counts[label] != null ? label : "Green");
      counts[key] = (counts[key] || 0) + 1;
      if (isRed) reds.push(p.id);
    });
    const archived = (window.LIN_ARCHIVED || []).length;
    const analysed = LIN_PROJECTS.length - empty;
    return {
      title: "Portfolio: status",
      body: `${LIN_PROJECTS.length} active project(s): ${empty} awaiting analysis, ${analysed} analysed` +
        `${archived ? ` (+${archived} archived)` : ""}. ` +
        `Of the analysed: ${counts["Complete"]} Complete, ${counts["Green"]} Green, ${counts["Yellow"]} Yellow, ${counts["Amber"]} Amber, ${counts["Red"]} Red. ` +
        `Red, escalation required: ${reds.length ? reds.join(", ") : "none"}. ` +
        `Fairness gate required: ${gated.length ? gated.join(", ") : "none"}. ` +
        `Every figure above is read from the stored server result at the moment you asked; a project awaiting analysis is never given a status it does not have.`
    };
  }

  function liveAnswer(q) {
    // explicit project code anywhere in the question
    // T12b. Was /syn-[a-z]{3}-\d{3}/i, which only matched the retired SYN-XXX-000 demo codes.
    // The server has issued "PRJ-" plus ten ULID characters since B7b (workspace.py), so asking
    // about any current project by its code fell straight through to "outside my script". Both
    // shapes are matched now, because archived SYN- projects may still exist.
    const idMatch = q.match(/prj-[0-9a-z]{6,12}/i) || q.match(/syn-[a-z]{3}-\d{3}/i);
    if (idMatch) {
      const id = idMatch[0].toUpperCase();
      const p = LIN_PROJECTS.find((x) => x.id === id);
      if (p) return projectAnswer(p);
      if ((window.LIN_ARCHIVED || []).some((x) => x.id === id)) {
        return { title: id, body: `${id} is currently archived. It is off the portfolio scope but can be restored.` };
      }
      return { title: id, body: `I don't have a project with code ${id} in the current portfolio.` };
    }
    // "this/selected/current/open project"
    if (/\b(this|selected|current|open)\s+project\b/.test(q) || /^project status/.test(q)) {
      const id = window.LinApp && LinApp.getSelectedId();
      const p = id && LIN_PROJECTS.find((x) => x.id === id);
      if (p) return projectAnswer(p);
    }
    // overall portfolio status
    if (/portfolio|overall|overview|how many|red.?review|fairness.?gated|summary of (the )?projects|status of (the )?projects/.test(q)) {
      return portfolioAnswer();
    }
    return null;
  }

  /* ---------- scripted matching over the knowledge base ---------- */

  function answer(query) {
    const q = query.toLowerCase().trim();
    if (!q) return null;

    // 0. live project / portfolio answers (scripted templates over live data)
    const live = liveAnswer(q);
    if (live) return live;

    // 1. topic match: score by whole-word keyword hits
    const wordHit = (k) => {
      const escd = k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return new RegExp(`\\b${escd}\\b`, "i").test(q);
    };
    let best = null, bestScore = 0;
    LIN_KNOWLEDGE.topics.forEach((t) => {
      let score = 0;
      t.keywords.forEach((k) => { if (wordHit(k)) score += k.length; });
      if (score > bestScore) { best = t; bestScore = score; }
    });
    if (best) return { title: best.title, body: best.body };

    // 2. term match: query mentions a defined term
    const term = LIN_KNOWLEDGE.terms.find((t) => {
      return t.term.toLowerCase().split("/").some((part) => {
        const p = part.trim();
        return p.length >= 3 && wordHit(p);
      });
    });
    if (term) return { title: term.term, body: `${term.definition} (${term.formula})` };

    // 3. honest out-of-scope, and what I do not know
    //
    // T12b. Was "PCEIF concepts, the five signals": a retired framework name, and a wrong
    // count. There are four signal classes: EVM, Monte Carlo, CUSUM, and document risk.
    return {
      title: "Outside my script",
      body: "I'm a scripted guide, not a model. I match your question against a written knowledge library and a few live project and portfolio lookups, and I answer only with what is written there or read from the stored server result. I have no access to anything outside this platform, I do not browse or fetch, and I cannot answer a question the library does not cover; this is one of those. Try the Knowledge page for the full reference (the four signal classes, the fairness gate, EVM, CUSUM, and Monte Carlo definitions, and how to use each page), or ask me one of the suggested questions."
    };
  }

  /* ---------- UI ---------- */

  // One line-art robot character that morphs between three activity states
  // (idle / listening / answering). Shared base: rounded head, two dot eyes,
  // antenna + tip, signal waves. Per-state accessories cross-fade (headset /
  // open book / speech bubbles). ALL animation is CSS/SMIL — JS only toggles
  // the is-idle / is-listening / is-answering state classes on the launcher.
  const ROBOT_SVG =
    '<svg class="la-robot" viewBox="0 0 64 64" aria-hidden="true" focusable="false">' +
      '<g class="bot-bob">' +
        // signal waves above the antenna (idle: slow pulse · answering: fast)
        '<g class="bot-waves">' +
          '<path class="bot-wave bot-wave-1" d="M26 9 A7 7 0 0 1 38 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
          '<path class="bot-wave bot-wave-2" d="M22.5 10.5 A10.5 10.5 0 0 1 41.5 10.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        '</g>' +
        // antenna
        '<line class="bot-antenna" x1="32" y1="18" x2="32" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        '<circle class="bot-antenna-tip" cx="32" cy="10" r="2" fill="currentColor"/>' +
        // IDLE accessory: headset arc + ear cups + mic boom
        '<g class="bot-acc bot-headset">' +
          '<path d="M18 30 A14 14 0 0 1 46 30" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>' +
          '<rect x="15" y="28" width="4.5" height="8" rx="2" fill="currentColor"/>' +
          '<rect x="44.5" y="28" width="4.5" height="8" rx="2" fill="currentColor"/>' +
          '<path d="M17.5 35 Q13.5 43 25 41" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
          '<circle cx="25" cy="41" r="2" fill="currentColor"/>' +
        '</g>' +
        // head
        '<rect class="bot-head" x="20" y="18" width="24" height="22" rx="6.5" fill="none" stroke="currentColor" stroke-width="2.2"/>' +
        // eyes (blink; look down while listening)
        '<g class="bot-eyes">' +
          '<circle class="bot-eye bot-eye-l" cx="27.5" cy="28" r="2.4" fill="currentColor"/>' +
          '<circle class="bot-eye bot-eye-r" cx="36.5" cy="28" r="2.4" fill="currentColor"/>' +
        '</g>' +
        // mouth: neutral + grin (grin fades in on hover/focus)
        '<path class="bot-mouth" d="M28 34.5 Q32 36.5 36 34.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        '<path class="bot-grin" d="M27 33.5 Q32 38.5 37 33.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
        // LISTENING accessory: open book with reading-sweep text rows
        '<g class="bot-acc bot-book">' +
          '<path d="M32 44 C28 42 23.5 41.8 19.5 42.3 L19.5 52 C23.5 51.5 28 51.8 32 53.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>' +
          '<path d="M32 44 C36 42 40.5 41.8 44.5 42.3 L44.5 52 C40.5 51.5 36 51.8 32 53.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>' +
          '<line x1="32" y1="44" x2="32" y2="53.2" stroke="currentColor" stroke-width="2"/>' +
          '<g class="bot-book-text" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">' +
            '<line class="bot-read bot-read-1" x1="22" y1="46.4" x2="29.5" y2="46.4"/>' +
            '<line class="bot-read bot-read-2" x1="22" y1="49.4" x2="29.5" y2="49.4"/>' +
            '<line class="bot-read bot-read-3" x1="34.5" y1="46.4" x2="42" y2="46.4"/>' +
            '<line class="bot-read bot-read-4" x1="34.5" y1="49.4" x2="42" y2="49.4"/>' +
          '</g>' +
        '</g>' +
        // ANSWERING accessory: two speech bubbles (dots + lines, alternating)
        '<g class="bot-acc bot-bubbles">' +
          '<g class="bot-bubble bot-bubble-1">' +
            '<path d="M45 19 h12 a3 3 0 0 1 3 3 v6 a3 3 0 0 1 -3 3 h-7 l-3 3 v-3 a3 3 0 0 1 -2 -3 v-6 a3 3 0 0 1 2 -3 z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>' +
            '<g fill="currentColor"><circle class="bot-dot bot-dot-1" cx="49" cy="25" r="1.3"/><circle class="bot-dot bot-dot-2" cx="53" cy="25" r="1.3"/><circle class="bot-dot bot-dot-3" cx="57" cy="25" r="1.3"/></g>' +
          '</g>' +
          '<g class="bot-bubble bot-bubble-2">' +
            '<path d="M19 33 h-12 a3 3 0 0 0 -3 3 v5 a3 3 0 0 0 3 3 h7 l3 3 v-3 a3 3 0 0 0 2 -3 v-5 a3 3 0 0 0 -2 -3 z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>' +
            '<g stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line class="bot-say bot-say-1" x1="7" y1="38" x2="16" y2="38"/><line class="bot-say bot-say-2" x1="7" y1="41" x2="13" y2="41"/></g>' +
          '</g>' +
        '</g>' +
      '</g>' +
    '</svg>';

  function buildWidget() {
    const wrap = document.createElement("div");
    wrap.id = "lin-assistant";
    wrap.innerHTML =
      `<button id="la-launcher" class="la-launcher is-idle" aria-expanded="false" aria-controls="la-panel"
               aria-label="Ask the assistant" title="Ask the assistant">
         <span class="la-greet" aria-hidden="true">Ask Assistant</span>
         <span class="la-invite" aria-hidden="true"></span>
         ${ROBOT_SVG}
       </button>
       <span id="la-live" class="la-sr-only" aria-live="polite"></span>
       <div id="la-panel" class="la-panel" role="dialog" aria-label="Opus Gubernatio assistant" hidden>
         <div class="la-head">
           <div><strong>Assistant</strong></div>
           <div class="la-head-actions">
             <button id="la-voice-toggle" class="la-icon-btn" type="button" aria-pressed="true" title="Speak answers aloud" hidden>
               <span class="la-voice-on" aria-hidden="true">🔊</span><span class="la-voice-off" aria-hidden="true">🔇</span>
             </button>
             <button id="la-close" class="la-close" aria-label="Close assistant">×</button>
           </div>
         </div>
         <div id="la-msgs" class="la-msgs" aria-live="polite">
           <div class="la-msg la-bot">
             <p>Ask me about the selected project's status, its signals, or the governance recommendation. I can explain the Monte Carlo forecast, CUSUM detection, and how a signal becomes a recommended action. I am scripted by design, not a live AI: I match your question against a written knowledge library and a few live project lookups, and where the library has no answer I say so rather than inventing one. Type a question or use the mic.</p>
           </div>
         </div>
         <div class="la-suggest">${SUGGESTIONS.map((s) => `<button class="la-chip">${esc(s)}</button>`).join("")}</div>
         <form id="la-form" class="la-form">
           <button id="la-mic" class="la-icon-btn la-mic" type="button" title="Ask by voice" aria-label="Ask by voice" hidden>🎙️</button>
           <input id="la-input" type="text" placeholder="Ask a question…" aria-label="Question for the assistant" maxlength="200" autocomplete="off" />
           <button type="submit" class="btn primary la-send">Ask</button>
         </form>
       </div>`;
    document.body.appendChild(wrap);

    const launcher = document.getElementById("la-launcher");
    const panel = document.getElementById("la-panel");
    const msgs = document.getElementById("la-msgs");
    const form = document.getElementById("la-form");
    const input = document.getElementById("la-input");
    const live = document.getElementById("la-live");

    /* ---------- robot state machine ----------
       Panel closed → always IDLE. Otherwise ANSWERING (a reply is in flight)
       wins over LISTENING (typing in the input), which wins over IDLE. JS only
       flips the state class; all motion is CSS. Screen-reader announcements go
       out politely via #la-live. */
    let answering = false;      // send → response finishes
    let typingActive = false;   // input focused + non-empty (debounced)
    let curState = "idle";
    function computeState() {
      if (panel.hidden) return "idle";
      if (answering) return "answering";
      if (typingActive) return "listening";
      return "idle";
    }
    function applyState() {
      const s = computeState();
      if (s === curState) return;
      curState = s;
      launcher.classList.remove("is-idle", "is-listening", "is-answering");
      launcher.classList.add("is-" + s);
      live.textContent = s === "listening" ? "Assistant is listening"
                       : s === "answering" ? "Assistant is answering" : "";
    }
    // one-shot flourishes (happy double-bob on success, head-shake on error)
    function flourish(cls) {
      launcher.classList.remove("la-happy", "la-shake");
      // reflow so re-adding the class restarts the animation
      void launcher.offsetWidth;
      launcher.classList.add(cls);
      setTimeout(() => launcher.classList.remove(cls), 700);
    }

    // Greeting: auto-show the "Ask Lin" bubble once per session, permanently
    // suppressed once the visitor has ever used the chat (localStorage).
    let chatUsed = false;
    try { chatUsed = localStorage.getItem("lin-chat-used") === "1"; } catch (e) {}
    function markChatUsed() {
      launcher.classList.remove("la-greeting");
      if (chatUsed) return;
      chatUsed = true;
      try { localStorage.setItem("lin-chat-used", "1"); } catch (e) {}
    }
    (function maybeGreet() {
      if (chatUsed) return;
      let greeted = false;
      try { greeted = sessionStorage.getItem("lin-greeted") === "1"; } catch (e) {}
      if (greeted) return;
      try { sessionStorage.setItem("lin-greeted", "1"); } catch (e) {}
      launcher.classList.add("la-greeting");
      setTimeout(() => launcher.classList.remove("la-greeting"), 6000);
    })();

    /* ---------- perch: the robot hops onto the open panel ----------
       Closed → the robot rests at its bottom-right corner. Open → it hops (CSS
       translate, 250ms) to perch on the panel's TOP-LEFT corner, half-overlapping
       the edge. Top-left keeps it clear of the close button (top-right) and the
       chat input/messages (below), and it stays perched as the panel grows.
       Desktop: it straddles the corner from up-and-left (clear of the "Lin"
       title, which is inset ~16px). Mobile (full-width panel): it shrinks to
       44px and sits just above the header's top edge at the left. Position is
       measured (panel height is dynamic) and re-run on open / resize / scroll /
       panel growth. */
    function perch() {
      const mobile = window.matchMedia("(max-width: 700px)").matches;
      launcher.classList.toggle("perched-mobile", mobile && !panel.hidden);
      if (panel.hidden) { launcher.style.transform = ""; return; }
      // The launcher's RESTING box is deterministic from its fixed CSS anchors
      // (right/bottom margins + size), so we compute it instead of measuring —
      // measuring while the .25s transform-transition is running would read a
      // mid-tween value. Only the panel is measured (it carries no transform),
      // so this always tracks the panel's LIVE top as it grows.
      const size = mobile ? 44 : 64;              // perched-mobile shrinks to 44
      const margin = mobile ? 16 : 22;            // matches .la-launcher right/bottom
      const restLeft = window.innerWidth - margin - size;
      const restTop = window.innerHeight - margin - size;
      const pr = panel.getBoundingClientRect();
      let targetLeft, targetTop;
      if (mobile) {
        // full-width panel: sit at the left, mostly above the header top edge
        // (only ~10px dips in, above the inset "Lin" title / controls)
        targetLeft = pr.left + 4;
        targetTop = pr.top - (size - 10);
      } else {
        // straddle the top-left corner from up-and-left: only the robot's
        // bottom-right ~14px overlaps the panel, clear of the inset "Lin" title
        targetLeft = pr.left - (size - 14);
        targetTop = pr.top - (size - 14);
      }
      // keep the robot fully on-screen on short/narrow windows
      targetLeft = Math.max(4, Math.min(targetLeft, window.innerWidth - size - 4));
      targetTop = Math.max(4, targetTop);
      launcher.style.transform = "translate(" + Math.round(targetLeft - restLeft) +
                                 "px, " + Math.round(targetTop - restTop) + "px)";
    }
    // keep the perch aligned as the panel grows / the viewport changes
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(() => { if (!panel.hidden) perch(); }).observe(panel);
    }
    window.addEventListener("resize", () => { if (!panel.hidden) perch(); }, { passive: true });
    window.addEventListener("scroll", () => { if (!panel.hidden) perch(); }, { passive: true });

    // populated by the idleInvitations() IIFE below: { onChatOpened, onManualClose }
    const inviteHooks = {};
    function toggle(open) {
      const wasOpen = !panel.hidden;
      const show = open !== undefined ? open : panel.hidden;
      panel.hidden = !show;
      launcher.setAttribute("aria-expanded", String(show));
      if (show) {
        launcher.classList.remove("la-greeting");
        input.focus();
        if (inviteHooks.onChatOpened) inviteHooks.onChatOpened();   // opening within an invite window counts as responding
      } else {
        typingActive = false;
        if (wasOpen && inviteHooks.onManualClose) inviteHooks.onManualClose();
      }
      perch();
      applyState();
    }

    // typing → LISTENING (debounced so it doesn't flicker per keystroke)
    let typeTimer = null;
    function evalTyping() {
      typingActive = !panel.hidden && document.activeElement === input &&
                     input.value.trim().length > 0;
      applyState();
    }
    input.addEventListener("input", () => { clearTimeout(typeTimer); typeTimer = setTimeout(evalTyping, 200); });
    input.addEventListener("focus", () => { clearTimeout(typeTimer); typeTimer = setTimeout(evalTyping, 200); });
    input.addEventListener("blur", () => { clearTimeout(typeTimer); typingActive = false; applyState(); });

    launcher.addEventListener("click", () => toggle());
    document.getElementById("la-close").addEventListener("click", () => toggle(false));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) toggle(false); });

    /* ===========================================================
       Idle invitations — the robot occasionally catches your eye
       -----------------------------------------------------------
       When the chat is CLOSED and the user is idle, the robot offers a
       short, CONTEXTUAL invitation in its bubble with a one-shot gesture,
       then returns to idle. Strict, mandatory timing contract (there is no
       user off-switch; the contract IS the restraint):
         • first invite only after >=45s idle AND >=60s after load
         • then no more than once per 4 min of continued idleness
         • bubble ~5s then fades; gesture plays once
         • HARD CAP 3 per session
         • 2 consecutive ignored (chat not opened within 20s) -> silent for the session
         • if the user ever manually closes the chat -> halve frequency + at most 1 more
         • never while any modal/loader/audit runs, chat open, an input is
           focused, or the tab is hidden; aborts instantly on any activity
       Reduced-motion: the bubble still appears, but with NO gesture (static
       robot) — documented choice; the invitation copy alone reads fine.
       =========================================================== */
    (function idleInvitations() {
      const inviteEl = launcher.querySelector(".la-invite");
      if (!inviteEl) return;
      const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const IDLE_MS = 45000, MIN_AFTER_LOAD_MS = 60000;
      const BASE_INTERVAL_MS = 240000, CLOSED_INTERVAL_MS = 480000;  // 4 min; 8 min after a manual close
      const BUBBLE_MS = 5000, IGNORE_MS = 20000, HARD_CAP = 3;

      const loadTime = Date.now();
      let lastActivity = Date.now();
      let lastInviteTime = 0;
      let shownCount = 0;
      let ignoredStreak = 0;
      let everManuallyClosed = false;
      let maxAfterClose = Infinity;   // set when the user first manually closes the chat
      let silenced = false;
      let bubbleVisible = false;
      let fadeTimer = null, ignoreTimer = null, gestureTimer = null;
      const usedLines = new Set();

      function hideBubble() {
        bubbleVisible = false;
        launcher.classList.remove("la-inviting");
        clearTimeout(fadeTimer); fadeTimer = null;
      }
      function stopGesture() {
        launcher.classList.remove("la-wave", "la-bow");
        clearTimeout(gestureTimer); gestureTimer = null;
      }
      // Abort on ANY user activity: bubble + gesture stop at once. The 20s
      // ignore window keeps running (aborting is not the same as responding).
      function abort() { if (bubbleVisible) { hideBubble(); stopGesture(); } }

      // Contextual copy from the CURRENT page/selection. Never the same line
      // twice a session; the first invite is always the plain "Can I help?".
      function pickMessage() {
        if (shownCount === 0 && !usedLines.has("Can I help?")) return "Can I help?";
        const page = (document.querySelector(".page:not([hidden])") || {}).dataset;
        const pageName = page && page.page;
        const cands = [];
        if (pageName === "handbook") {
          cands.push("Ask me how any module works.");
        } else if (pageName === "auditor") {
          cands.push("I can explain what the auditor checks.");
        } else {
          const id = window.LinApp && LinApp.getSelectedId && LinApp.getSelectedId();
          const proj = id && (window.LIN_PROJECTS || []).find((p) => p.id === id);
          if (pageName === "detail" && proj) {
            cands.push("Want a plain-English read on " + proj.name + "?");
            cands.push("I can explain what is driving this project's status.");
          } else if (proj) {
            cands.push("Want a plain-English read on " + proj.name + "?");
            cands.push("Ask me which projects need attention this week.");
          } else {
            cands.push("Ask me which projects need attention this week.");
            cands.push("I can answer about any project's status, signals, or governance decision.");
          }
        }
        cands.push("Can I help?");
        const fresh = cands.find((c) => !usedLines.has(c));
        return fresh || cands[0];
      }

      function playGesture() {
        if (reduceMotion) return;
        stopGesture();
        // first invite waves; subsequent alternate wave / small bow
        const cls = (shownCount % 2 === 0) ? "la-wave" : "la-bow";
        void launcher.offsetWidth;   // reflow so the one-shot restarts cleanly
        launcher.classList.add(cls);
        gestureTimer = setTimeout(() => launcher.classList.remove(cls), 900);
      }

      function showInvitation() {
        const msg = pickMessage();
        inviteEl.textContent = msg;
        usedLines.add(msg);
        bubbleVisible = true;
        launcher.classList.add("la-inviting");
        playGesture();
        shownCount++;
        lastInviteTime = Date.now();
        // announce politely for screen-reader users (no visual dependency)
        if (live) live.textContent = msg;
        clearTimeout(fadeTimer);
        fadeTimer = setTimeout(() => { hideBubble(); stopGesture(); }, BUBBLE_MS);
        clearTimeout(ignoreTimer);
        ignoreTimer = setTimeout(() => {
          ignoreTimer = null;
          ignoredStreak++;
          if (ignoredStreak >= 2) silenced = true;   // two ignored in a row -> done for the session
        }, IGNORE_MS);
      }

      // The user opened the chat — if that happened within an invitation's
      // 20s window it counts as responding: reset the ignored streak.
      function onChatOpened() {
        if (ignoreTimer) { clearTimeout(ignoreTimer); ignoreTimer = null; ignoredStreak = 0; }
        abort();
      }
      // Manual close: halve the frequency and allow at most one further invite.
      function onManualClose() {
        if (!everManuallyClosed) { everManuallyClosed = true; maxAfterClose = shownCount + 1; }
      }
      inviteHooks.onChatOpened = onChatOpened;
      inviteHooks.onManualClose = onManualClose;

      function canInvite() {
        if (silenced || shownCount >= HARD_CAP) return false;
        if (everManuallyClosed && shownCount >= maxAfterClose) return false;
        if (bubbleVisible) return false;
        if (!panel.hidden) return false;                 // chat open
        if (document.hidden) return false;               // tab hidden
        const ae = document.activeElement;
        if (ae && (ae.tagName === "INPUT" || ae.tagName === "TEXTAREA" || ae.tagName === "SELECT" || ae.isContentEditable)) return false;
        // any modal / loader / audit in flight — one DOM query each, no cross-module API:
        // .lwr covers upload/extraction/recompute/map-load working robots.
        if (document.querySelector(".app-modal-backdrop, .ds-modal-backdrop, .lwr, .aud-loading, #recompute-overlay:not([hidden])")) return false;
        return true;
      }

      function due() {
        const now = Date.now();
        if (now - lastActivity < IDLE_MS) return false;                 // not idle long enough
        if (shownCount === 0) return now - loadTime >= MIN_AFTER_LOAD_MS;
        const interval = everManuallyClosed ? CLOSED_INTERVAL_MS : BASE_INTERVAL_MS;
        return now - lastInviteTime >= interval;
      }

      // Activity resets the idle clock and aborts a visible invitation instantly.
      const onActivity = () => { lastActivity = Date.now(); abort(); };
      ["pointermove", "pointerdown", "keydown", "wheel", "touchstart", "scroll"].forEach((ev) =>
        document.addEventListener(ev, onActivity, { passive: true, capture: true }));
      document.addEventListener("visibilitychange", () => { if (document.hidden) abort(); });

      // Poll on a modest cadence; every gate is re-checked at fire time.
      setInterval(() => { if (canInvite() && due()) showInvitation(); }, 2500);
    })();

    /* ---------- voice OUT (text-to-speech) ---------- */
    const ttsOK = "speechSynthesis" in window && typeof window.SpeechSynthesisUtterance !== "undefined";
    let voiceOut = true;
    try { voiceOut = localStorage.getItem("lin-voice-out") !== "off"; } catch (e) {}
    const voiceToggle = document.getElementById("la-voice-toggle");
    function reflectVoiceToggle() {
      if (!voiceToggle) return;
      voiceToggle.setAttribute("aria-pressed", String(voiceOut));
      voiceToggle.classList.toggle("muted", !voiceOut);
      voiceToggle.title = voiceOut ? "Answers spoken aloud (tap to mute)" : "Answers muted (tap to speak)";
    }
    if (ttsOK && voiceToggle) {
      voiceToggle.hidden = false;
      reflectVoiceToggle();
      voiceToggle.addEventListener("click", () => {
        voiceOut = !voiceOut;
        try { localStorage.setItem("lin-voice-out", voiceOut ? "on" : "off"); } catch (e) {}
        if (!voiceOut) window.speechSynthesis.cancel();
        reflectVoiceToggle();
      });
    }
    function speak(text) {
      // Autoplay note: browsers may block the first utterance until the user
      // has interacted with the page; that's expected, not an error.
      if (!ttsOK || !voiceOut || !text) return;
      try {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(String(text));
        u.rate = 1.0; u.pitch = 1.0;
        window.speechSynthesis.speak(u);
      } catch (e) { /* non-fatal */ }
    }

    function addBot(html) {
      msgs.insertAdjacentHTML("beforeend", `<div class="la-msg la-bot"><p>${html}</p></div>`);
      msgs.scrollTop = msgs.scrollHeight;
    }
    function scripted(text) {
      const a = answer(text);
      return { html: `<strong>${esc(a.title)}.</strong> ${esc(a.body)}`, plain: `${a.title}. ${a.body}` };
    }

    // ANSWERING lasts from send until the reply lands; on success a happy
    // double-bob, on error a head-shake, then back to IDLE/LISTENING.
    function startAnswering() { markChatUsed(); typingActive = false; answering = true; applyState(); }
    function endAnswering(ok) {
      answering = false;
      flourish(ok ? "la-happy" : "la-shake");
      // re-evaluate typing (the visitor may already be typing the next question)
      evalTyping();
    }

    async function ask(text) {
      if (!text || !text.trim()) return;
      msgs.insertAdjacentHTML("beforeend", `<div class="la-msg la-user"><p>${esc(text)}</p></div>`);
      msgs.scrollTop = msgs.scrollHeight;
      startAnswering();

      // No backend configured → scripted answer only.
      if (!(window.LinStore && LinStore.configured && LinStore.configured())) {
        const s = scripted(text); addBot(s.html); speak(s.plain); endAnswering(true); return;
      }
      /* T12b. THE SCRIPTED ANSWER IS THE PRODUCT, NOT A DEGRADED FALLBACK.
         This used to call LinStore.chat() on every question, show "Thinking...", and then, when
         that call failed, append "(scripted fallback, AI unreachable)". The chat action is in
         DEFERRED_AI_ACTIONS server-side and answers "Action not implemented in this build"
         (facade.py), so the call could not succeed and the note was shown every single time. It
         told the user there is an AI assistant that is currently broken. There is not: this
         assistant is scripted by design, which is what its own file header has always said.
         Claiming a temporarily unavailable capability is worse than claiming none.

         The call is kept, because if the chat action is ever implemented this is where its answer
         arrives. What is removed is the pretence: no "Thinking..." for a request that is not
         expected to return, and no apologetic note on an answer that is exactly what the platform
         intends to give. */
      try {
        const id = window.LinApp && LinApp.getSelectedId ? LinApp.getSelectedId() : null;
        const answerText = await LinStore.chat(text, id);
        if (answerText && String(answerText).trim()) {
          addBot(esc(String(answerText))); speak(String(answerText));
        } else {
          const s = scripted(text); addBot(s.html); speak(s.plain);
        }
        endAnswering(true);
      } catch (e) {
        const s = scripted(text);
        addBot(s.html); speak(s.plain);
        endAnswering(true);
      }
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      ask(input.value);
      input.value = "";
    });

    wrap.querySelectorAll(".la-chip").forEach((c) =>
      c.addEventListener("click", () => ask(c.textContent)));

    /* ---------- voice IN (speech-to-text) ---------- */
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const mic = document.getElementById("la-mic");
    if (SR && mic) {
      mic.hidden = false;
      let recog = null, listening = false;
      mic.addEventListener("click", () => {
        if (listening && recog) { recog.stop(); return; }
        recog = new SR();
        recog.lang = "en-US"; recog.interimResults = false; recog.maxAlternatives = 1;
        recog.onstart = () => { listening = true; mic.classList.add("listening"); mic.title = "Listening… (tap to stop)"; input.placeholder = "Listening…"; };
        recog.onerror = () => { /* non-fatal: mic permission denied, no speech, etc. */ };
        recog.onend = () => { listening = false; mic.classList.remove("listening"); mic.title = "Ask by voice"; input.placeholder = "Ask a question…"; };
        recog.onresult = (ev) => {
          const said = ev.results[0][0].transcript;
          input.value = said;
          ask(said);            // same scripted answer path as typed questions
          input.value = "";
        };
        try { recog.start(); } catch (e) { /* already started */ }
      });
    }

    // public hook so other pages can open the assistant pre-filled and send
    // through the same scripted answer path.
    window.LinAssistant = {
      ask(question) { toggle(true); ask(question); }
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildWidget);
  } else {
    buildWidget();
  }
})();
