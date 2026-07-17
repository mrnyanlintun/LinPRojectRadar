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
    "What is PCEIF?",
    "Status of this project?",
    "Portfolio overview",
    "How does the fairness gate work?",
    "What is CUSUM?"
  ];

  /* ---------- live (still scripted) project & portfolio answers ----------
     These read the current synthetic data and decision.js output at answer
     time — no hard-coding, no LLM, no network. The phrasing is templated. */

  const SECTOR_LABEL = { design: "Design", construction: "Construction", combined: "Hybrid" };

  function projectAnswer(p) {
    if (!(window.hasSignals && hasSignals(p))) {
      return {
        title: `${p.id} — awaiting ingest`,
        body: `${p.name} (${SECTOR_LABEL[p.sector] || p.sector} sector) has no signals yet. Populate its signals on Manage Projects (or the Ingest panel on its Detail page) to run the Monte Carlo forecast, CUSUM monitor, document-risk extraction, and the PCEIF decision. Nothing is fabricated until inputs are ingested.`
      };
    }
    const d = deriveDecision(p);
    const s = p.signals;
    return {
      title: `${p.id} — live status`,
      body: `${p.name} (${SECTOR_LABEL[p.sector] || p.sector} sector, period ${p.reportingPeriod}). ` +
        `Derived state ${d.healthState}, conflict "${d.conflictType}". ` +
        `Signals — EVM: ${s.evm.status} (CPI ${s.evm.cpi.toFixed(2)}, SPI ${s.evm.spi.toFixed(2)}); ` +
        `Monte Carlo: ${s.mc.status} (P80 EAC +${s.mc.p80eacOverrunPct.toFixed(1)}%, P(delay) ${s.mc.pMilestoneDelay.toFixed(2)}); ` +
        `CUSUM: ${s.cusum.status} (drift ${s.cusum.drift.toFixed(1)} vs threshold ${s.cusum.threshold.toFixed(1)}${s.cusum.breached ? ", BREACHED" : ""}); ` +
        `document risk: ${s.doc.status} (score ${s.doc.score.toFixed(2)}). ` +
        `Recommended action: ${d.action} Authority: ${d.authority}. ` +
        `Fairness gate: ${d.fairnessGateRequired ? "REQUIRED before any formal action" : "not required"}. ` +
        `(Computed live from the synthetic data by decision.js.)`
    };
  }

  function portfolioAnswer() {
    // 5-state fused bands (Complete/Green/Yellow/Amber/Red); the signal-class
    // fallback may still emit "Red-review", which we fold into the Red tally.
    const counts = { "Complete": 0, "Green": 0, "Yellow": 0, "Amber": 0, "Red": 0 };
    const reds = [], gated = [];
    let empty = 0;
    LIN_PROJECTS.forEach((p) => {
      if (!(window.hasSignals && hasSignals(p))) { empty++; return; }
      const d = deriveDecision(p);
      const isRed = d.healthState === "Red" || d.healthState === "Red-review";
      const key = isRed ? "Red" : d.healthState;
      counts[key] = (counts[key] || 0) + 1;
      if (isRed) reds.push(p.id);
      if (d.fairnessGateRequired) gated.push(p.id);
    });
    const archived = (window.LIN_ARCHIVED || []).length;
    const populated = LIN_PROJECTS.length - empty;
    return {
      title: "Portfolio — live status",
      body: `${LIN_PROJECTS.length} active project(s): ${empty} awaiting ingest, ${populated} populated` +
        `${archived ? ` (+${archived} archived)` : ""}. ` +
        `Of the populated: ${counts["Complete"]} Complete, ${counts["Green"]} Green, ${counts["Yellow"]} Yellow, ${counts["Amber"]} Amber, ${counts["Red"]} Red. ` +
        `Red (escalation): ${reds.length ? reds.join(", ") : "none"}. ` +
        `Fairness gate required: ${gated.length ? gated.join(", ") : "none"}. ` +
        `(Computed live from the current synthetic data; empty projects are never given a fabricated status.)`
    };
  }

  function liveAnswer(q) {
    // explicit project code anywhere in the question
    const idMatch = q.match(/syn-[a-z]{3}-\d{3}/i);
    if (idMatch) {
      const id = idMatch[0].toUpperCase();
      const p = LIN_PROJECTS.find((x) => x.id === id);
      if (p) return projectAnswer(p);
      if ((window.LIN_ARCHIVED || []).some((x) => x.id === id)) {
        return { title: id, body: `${id} is currently archived — it is off the portfolio scope but recoverable on the Manage Projects page.` };
      }
      return { title: id, body: `I don't have a project with code ${id} in the current synthetic portfolio.` };
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

    // 3. honest out-of-scope
    return {
      title: "Outside my script",
      body: "I'm a scripted guide — I only answer from this demo's knowledge library (PCEIF concepts, the five signals, the fairness gate, EVM/CUSUM/Monte Carlo definitions, and how to use each page). Try the Knowledge page for the full reference, or ask me one of the suggested questions."
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
               aria-label="Ask Lin — assistant" title="Ask Lin">
         <span class="la-greet" aria-hidden="true">Ask Lin</span>
         ${ROBOT_SVG}
       </button>
       <span id="la-live" class="la-sr-only" aria-live="polite"></span>
       <div id="la-panel" class="la-panel" role="dialog" aria-label="Lin assistant" hidden>
         <div class="la-head">
           <div><strong>Lin</strong></div>
           <div class="la-head-actions">
             <button id="la-voice-toggle" class="la-icon-btn" type="button" aria-pressed="true" title="Speak answers aloud" hidden>
               <span class="la-voice-on" aria-hidden="true">🔊</span><span class="la-voice-off" aria-hidden="true">🔇</span>
             </button>
             <button id="la-close" class="la-close" aria-label="Close assistant">×</button>
           </div>
         </div>
         <div id="la-msgs" class="la-msgs" aria-live="polite">
           <div class="la-msg la-bot">
             <p>Ask me about the selected project's cost and schedule performance, signal analysis, and governance decision. I can explain the Monte Carlo forecast, CUSUM detection, PCEIF concepts, and the signal-to-action framework. Type a question or use the mic.</p>
           </div>
         </div>
         <div class="la-suggest">${SUGGESTIONS.map((s) => `<button class="la-chip">${esc(s)}</button>`).join("")}</div>
         <form id="la-form" class="la-form">
           <button id="la-mic" class="la-icon-btn la-mic" type="button" title="Ask by voice" aria-label="Ask by voice" hidden>🎙️</button>
           <input id="la-input" type="text" placeholder="Ask about the demo…" aria-label="Question for the Lin assistant" maxlength="200" autocomplete="off" />
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
      live.textContent = s === "listening" ? "Lin is listening"
                       : s === "answering" ? "Lin is answering" : "";
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

    function toggle(open) {
      const show = open !== undefined ? open : panel.hidden;
      panel.hidden = !show;
      launcher.setAttribute("aria-expanded", String(show));
      if (show) { launcher.classList.remove("la-greeting"); input.focus(); }
      else { typingActive = false; }
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
      // Live AI answer via Groq (scoped to the open project), with scripted fallback.
      const thinking = document.createElement("div");
      thinking.className = "la-msg la-bot la-thinking";
      thinking.innerHTML = "<p><em>Thinking…</em></p>";
      msgs.appendChild(thinking); msgs.scrollTop = msgs.scrollHeight;
      try {
        const id = window.LinApp && LinApp.getSelectedId ? LinApp.getSelectedId() : null;
        const answerText = await LinStore.chat(text, id);
        thinking.remove();
        if (answerText && String(answerText).trim()) {
          addBot(esc(String(answerText))); speak(String(answerText));
        } else {
          const s = scripted(text); addBot(s.html + ` <span class="la-fallback-note">(scripted fallback)</span>`); speak(s.plain);
        }
        endAnswering(true);
      } catch (e) {
        thinking.remove();
        const s = scripted(text);
        addBot(s.html + ` <span class="la-fallback-note">(scripted fallback — AI unreachable)</span>`); speak(s.plain);
        endAnswering(false);
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
        recog.onend = () => { listening = false; mic.classList.remove("listening"); mic.title = "Ask by voice"; input.placeholder = "Ask about the demo…"; };
        recog.onresult = (ev) => {
          const said = ev.results[0][0].transcript;
          input.value = said;
          ask(said);            // same Groq chat path as typed questions
          input.value = "";
        };
        try { recog.start(); } catch (e) { /* already started */ }
      });
    }

    // public hook so other pages (e.g. Knowledge "Ask the AI") can open the
    // assistant pre-filled and send through the same live chat + fallback path.
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
