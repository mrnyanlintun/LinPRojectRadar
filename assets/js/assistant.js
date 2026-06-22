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

  function buildWidget() {
    const wrap = document.createElement("div");
    wrap.id = "lin-assistant";
    wrap.innerHTML =
      `<button id="la-launcher" class="la-launcher" aria-expanded="false" aria-controls="la-panel"
               title="Ask Lin">
         <span aria-hidden="true">💬</span><span class="la-launcher-label">Ask Lin</span>
       </button>
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

    function toggle(open) {
      const show = open !== undefined ? open : panel.hidden;
      panel.hidden = !show;
      launcher.setAttribute("aria-expanded", String(show));
      if (show) input.focus();
    }

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

    async function ask(text) {
      if (!text || !text.trim()) return;
      msgs.insertAdjacentHTML("beforeend", `<div class="la-msg la-user"><p>${esc(text)}</p></div>`);
      msgs.scrollTop = msgs.scrollHeight;

      // No backend configured → scripted answer only.
      if (!(window.LinStore && LinStore.configured && LinStore.configured())) {
        const s = scripted(text); addBot(s.html); speak(s.plain); return;
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
      } catch (e) {
        thinking.remove();
        const s = scripted(text);
        addBot(s.html + ` <span class="la-fallback-note">(scripted fallback — AI unreachable)</span>`); speak(s.plain);
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
