/* ============================================================
   Lin Project Radar — workingrobot.js
   ------------------------------------------------------------
   LinWorkingRobot — one reusable line-art "robot at work" loader,
   in the same visual language as the Ask Lin assistant robot
   (assistant.js): rounded head, two dot eyes, antenna + tip, thin
   currentColor strokes, theme-agnostic (colours via CSS vars, reads
   on light and dark). ALL motion is CSS — JS only mounts the markup,
   toggles a variant class, sets the determinate bar width, and flashes
   a one-shot completion tick. Reduced-motion collapses to a static
   pose + a progress bar / "Working…" text (no loops).

   API:
     const h = LinWorkingRobot.mount(el, { variant, message, progress, size });
     h.update({ message, progress });   // progress: 0..1, or null = indeterminate
     h.tick();                          // flash the completion check (per file)
     h.destroy();
   variant: 'extracting' | 'computing' | 'loading'
   size:    'sm' (~64px, inline) | 'md' (~140px, dialogs/overlays)
   ============================================================ */
(function () {
  "use strict";

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  // The seated robot at a console. Shared base (head/eyes/antenna/waves) matches
  // the Ask Lin robot; the desk, tapping hands, monitor mini-chart, and the
  // feeding page glyph are the "at work" additions. The mini-chart's redrawing
  // bars are what read as "calculating" rather than a generic spinner.
  const ROBOT_SVG =
    '<svg class="lwr-robot-svg" viewBox="0 0 120 96" aria-hidden="true" focusable="false">' +
      // ── monitor / console to the robot's left, with a live mini bar-chart ──
      '<g class="lwr-monitor">' +
        '<rect x="6" y="30" width="40" height="30" rx="3" fill="none" stroke="currentColor" stroke-width="2.2"/>' +
        '<line x1="26" y1="60" x2="26" y2="66" stroke="currentColor" stroke-width="2.2"/>' +
        '<line x1="18" y1="66" x2="34" y2="66" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>' +
        // redrawing bars (scaleY loop, staggered = a chart being recomputed)
        '<g class="lwr-bars" fill="currentColor">' +
          '<rect class="lwr-cbar lwr-cbar-1" x="11" y="40" width="4.5" height="14"/>' +
          '<rect class="lwr-cbar lwr-cbar-2" x="18.5" y="40" width="4.5" height="14"/>' +
          '<rect class="lwr-cbar lwr-cbar-3" x="26" y="40" width="4.5" height="14"/>' +
          '<rect class="lwr-cbar lwr-cbar-4" x="33.5" y="40" width="4.5" height="14"/>' +
        '</g>' +
        // scrolling tick row along the top of the screen (extra "calculating")
        '<g class="lwr-ticks" stroke="currentColor" stroke-width="1.4" stroke-linecap="round">' +
          '<line class="lwr-tickline" x1="10" y1="35" x2="42" y2="35"/>' +
        '</g>' +
      '</g>' +
      // ── the page that feeds INTO the console (extracting variant) ──
      '<g class="lwr-page">' +
        '<rect x="-14" y="38" width="13" height="16" rx="1.5" fill="var(--surface, #0b0e17)" stroke="currentColor" stroke-width="1.8"/>' +
        '<line x1="-11" y1="42" x2="-4" y2="42" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>' +
        '<line x1="-11" y1="46" x2="-4" y2="46" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>' +
        '<line x1="-11" y1="50" x2="-6" y2="50" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>' +
      '</g>' +
      // ── the robot, seated to the right, facing the console ──
      '<g class="lwr-bot">' +
        '<g class="lwr-bot-bob">' +
          // antenna + signal tip
          '<line class="lwr-antenna" x1="78" y1="20" x2="78" y2="13" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>' +
          '<circle class="lwr-antenna-tip" cx="78" cy="11" r="2.2" fill="currentColor"/>' +
          // head
          '<rect class="lwr-head" x="66" y="20" width="24" height="22" rx="6.5" fill="none" stroke="currentColor" stroke-width="2.2"/>' +
          // eyes (blink) — looking left toward the screen
          '<g class="lwr-eyes">' +
            '<circle class="lwr-eye lwr-eye-l" cx="72.5" cy="30" r="2.3" fill="currentColor"/>' +
            '<circle class="lwr-eye lwr-eye-r" cx="81.5" cy="30" r="2.3" fill="currentColor"/>' +
          '</g>' +
          '<path class="lwr-mouth" d="M74 36 Q78 38 82 36" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>' +
        '</g>' +
        // torso
        '<path class="lwr-torso" d="M68 44 h20 a4 4 0 0 1 4 4 v10 h-28 v-10 a4 4 0 0 1 4 -4 z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/>' +
        // tapping hands/arms on the desk (alternating bob)
        '<g class="lwr-arms" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none">' +
          '<path class="lwr-arm lwr-arm-l" d="M68 52 L58 60"/>' +
          '<path class="lwr-arm lwr-arm-r" d="M88 52 L98 60"/>' +
          '<circle class="lwr-hand lwr-hand-l" cx="57" cy="61" r="2.4" fill="currentColor" stroke="none"/>' +
          '<circle class="lwr-hand lwr-hand-r" cx="99" cy="61" r="2.4" fill="currentColor" stroke="none"/>' +
        '</g>' +
      '</g>' +
      // ── desk line the whole scene sits on ──
      '<line class="lwr-desk" x1="2" y1="64" x2="112" y2="64" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>' +
      // ── completion check tick (flashed by .tick(), per file / on done) ──
      '<path class="lwr-check" d="M96 20 l4 4 8 -9" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>' +
    '</svg>';

  function mount(el, opts) {
    opts = opts || {};
    if (!el) return noopHandle();
    const variant = ["extracting", "computing", "loading"].indexOf(opts.variant) >= 0 ? opts.variant : "loading";
    const size = opts.size === "sm" ? "sm" : "md";
    const determinate = typeof opts.progress === "number" && isFinite(opts.progress);

    const root = document.createElement("div");
    root.className = "lwr lwr-" + size + " lwr-" + variant + (determinate ? " lwr-determinate" : " lwr-indeterminate");
    root.setAttribute("role", "status");
    root.setAttribute("aria-live", "polite");
    root.innerHTML =
      '<div class="lwr-figure">' + ROBOT_SVG + '</div>' +
      '<div class="lwr-callout"><span class="lwr-msg">' + esc(opts.message || "Working…") + '</span></div>' +
      '<div class="lwr-progress"><div class="lwr-track"><div class="lwr-bar"></div></div>' +
        '<span class="lwr-rm-fallback">Working…</span></div>';
    el.appendChild(root);

    const msgEl = root.querySelector(".lwr-msg");
    const barEl = root.querySelector(".lwr-bar");
    let tickTimer = null;
    let destroyed = false;

    function setProgress(p) {
      const has = typeof p === "number" && isFinite(p);
      root.classList.toggle("lwr-determinate", has);
      root.classList.toggle("lwr-indeterminate", !has);
      if (has) {
        const pct = Math.max(0, Math.min(1, p)) * 100;
        barEl.style.width = pct.toFixed(1) + "%";
        root.setAttribute("aria-valuenow", Math.round(pct));
      } else {
        barEl.style.width = "";
        root.removeAttribute("aria-valuenow");
      }
    }
    if (determinate) setProgress(opts.progress);

    return {
      update(next) {
        if (destroyed || !next) return;
        if (next.message != null && msgEl) msgEl.textContent = String(next.message);
        if ("progress" in next) setProgress(next.progress);
      },
      // one-shot completion flash (per file, or on batch done)
      tick() {
        if (destroyed) return;
        root.classList.remove("lwr-ticking");
        void root.offsetWidth;                    // reflow so the animation restarts
        root.classList.add("lwr-ticking");
        clearTimeout(tickTimer);
        tickTimer = setTimeout(() => { if (!destroyed) root.classList.remove("lwr-ticking"); }, 900);
      },
      el: root,
      destroy() {
        if (destroyed) return;
        destroyed = true;
        clearTimeout(tickTimer);
        if (root.parentNode) root.parentNode.removeChild(root);
      }
    };
  }

  function noopHandle() {
    return { update() {}, tick() {}, destroy() {}, el: null };
  }

  window.LinWorkingRobot = { mount };
})();
