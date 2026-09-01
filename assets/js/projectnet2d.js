/* ============================================================
   lin-project-radar — projectnet2d.js
   THE SIGNAL NETWORK, REBUILT IN THREE DIMENSIONS. Run 82, Part D.
   ============================================================ */

/* =================================================================================================
   WHAT WAS HERE BEFORE, AND WHY IT IS GONE RATHER THAN RESTYLED.

   The previous diagram drew Cost and EVM into Synthesis, Synthesis into Evidence and Governance,
   and Evidence into Decision. `buildGraph` invented that shape from the GROUP LETTER on each
   category -- "groupA -> synth, groupC -> synth, synth -> rest, rest[0] -> the others" -- and
   nothing in the architecture works that way. The owner's ruling is that it is not to be
   restyled, it is to be replaced. This file is the replacement.

   THE REAL STRUCTURE, AND WHERE IT IS DECLARED. `server/app/simulation/spec_apply.py`:

       PASS_ONE = ("A1", "A2", "A3", "A4", "A5", "A6", "C1")   seven; they read the DOCUMENTS
       PASS_TWO = ("B1", "B2", "B3", "B4")                     four;  they read what pass one produced

   Run 79 established that B3 is in PASS_TWO -- four pass-two categories, not three -- and that a
   pass-two category is handed `upstream_state_report`, which is a report on ALL of pass one. So
   the dependency is pass-one-category -> pass-two-category, and it is drawn ONLY from a pass-one
   category that actually produced a status, because a dependency edge from a category that
   produced nothing carried nothing. Everything with a stored status that the server's own
   projection marks `contributes_to_project_status` fuses to project health.

   `projectLevelCategories()` excludes D1 Portfolio Health as portfolio-level, leaving ELEVEN,
   which is the count the owner's specification names.

   -------------------------------------------------------------------------------------------
   THE OWNER'S SPECIFICATION: "The category view of the signal flow. The modules will show as the
   moons of the category planet with result colour. Space and planets, in 3D."

   Eleven category PLANETS, each carrying its own status colour, each with its own modules in
   ORBIT around it, each moon carrying the colour of its own reading. Pass one on the outer ring,
   pass two on the inner ring, project health at the centre of the system. Rendered by the same
   pure-canvas 3D projection idiom `charts3d.js` already uses in this repository (rotate about X
   and Y, then a perspective divide) -- NO WebGL and NO library, because the environment is
   offline and nothing 3D is vendored under assets/vendor.

   WHAT IT MAKES VISIBLE THAT NOTHING ELSE DOES, and both are the owner's words:
     * a category lit green with two lit moons and eight dark ones -- computed, on thin evidence.
       The planet's colour is the server's fused band; the moons are counted and drawn one by
       one, so the thinness is impossible to miss.
     * a category whose modules disagree -- nine green moons and one red -- visible at a glance.

   NO CONTROL IS ADDED, MOVED OR REMOVED. Run 74 removed the Signal Web sphere's five
   `[data-sphere-view]` buttons on the owner's ruling and they are NOT reintroduced. The system
   rotates by dragging on the canvas and zooms on the wheel -- the same two interactions this
   file already had, on the same canvas, with no DOM control of any kind. Nothing here creates a
   button, and a reader who never touches it sees a complete, labelled, legible diagram.

   -------------------------------------------------------------------------------------------
   THE FOUR STATES IN THIS VISUAL LANGUAGE, AND THEY ARE NOT MERGED (order section 5, and section
   10.3 fails the run for merging them). Three of them are dark, and three dark states that
   rendered identically would hide the difference between no evidence and a broken platform --
   which is exactly the confusion Part A exists to correct. So each gets its own geometry, not
   just its own shade:

     HAS A READING    a LIT body: filled in the band's colour, with a halo. data-state="computed"
     NOTHING TO       a DARK body, still in orbit: filled in the no-data slate with a solid rim.
       REPORT         Present, silent. data-state="abstained"
     NOT RELEVANT     OUTLINE ONLY, no body: a dashed ring with the background showing through,
                      in the site's own --status-notrelevant colour. Never called.
                      data-state="not_relevant"
     FAILED           drawn on the CATEGORY PLANET, which is filled red and struck through with a
                      cross, because that is where the platform stores a failure and, in the
                      owner's words, "it belongs on the category list where it gets dealt with".
                      It looks wrong on purpose. data-state="failed"

   A FIFTH, and it is not one of the four: NOT CALLED YET -- a dotted ring, no fill, no rim.
   No reading of any kind has been stored for it. Merging it into "nothing to report" would
   assert that the evidence was looked for and found missing, which nobody has established.

   THE ONE THING THE SERVER CANNOT TELL THIS CHART. `spec_apply.normalise_module` accepts only
   'computed' and 'abstained' from a specification, so THERE IS NO PER-MODULE FAILED STATE in the
   stored data at all: a FAILED row is written at CATEGORY level with an empty module list. A
   failed category's moons are therefore drawn as not called -- which is what they are, since the
   category failed before any of them reported -- and the failure is drawn, unmistakably, on the
   planet. Nothing is invented to fill the gap.

   "NOT RELEVANT" IS READ FROM THE TAXONOMY, NOT FROM A READING, and the distinction is the whole
   licence for drawing it. `window.isModuleSectorNA` and `window.isModuleDisabled` are static
   declarations about the PROJECT TYPE and about permanently disabled modules; they claim nothing
   about evidence and they are not a stored reading being manufactured in the client. Where the
   taxonomy makes no such declaration, this file does not invent one, and the module falls to one
   of the other states.

   NOTHING HERE COMPUTES A STATUS. Every planet's colour is the band the server fused and stored;
   every moon's colour is the band the server stored for that module; project health is
   `row.project_status`. `worst_band` is not re-implemented anywhere in this file.

   THE SCENE GRAPH IS QUERYABLE. `LinProjectNet2D.lastScene()` returns the bodies and edges the
   last frame was drawn from, so a check can assert on what was DRAWN rather than on the array it
   passed in -- and the canvas is still pixel-hashable on top of that.
   ============================================================================================== */

(function () {
  "use strict";

  /* RUN 90. THE POPULATION IS THE SIX WEIGHTED PERFORMANCE CATEGORIES, AND NOTHING ELSE.

     The owner's ruling, Run 90 section 2. Data Integrity, Signal Synthesis, Evidence Combination,
     Regulatory and Authority Thresholds and Decision Optimisation all still run and still inform
     the recommendation; none of them renders here. Retired modules do not appear at all -- not
     dimmed, not greyed, not present-and-inactive.

     BOTH POPULATIONS ARE THE REGISTRY'S, AT RUNTIME. `window.performanceCategories()` in
     taxonomy.js filters the GENERATED roster; that roster is written by
     `server/tools/build_client_taxonomy.py` from `registry.service_index()`, so a module carrying
     the `RETIRED ` note on its registry row is already absent from `cat.modules` and this file
     never has to know which they are. Nothing hand-maintained is consulted, which is how the
     counts drifted before Run 89.

     WHAT WENT WITH THE OTHER FIVE CATEGORIES. Run 82's pass-one -> pass-two dependency edges,
     which existed only to draw a Group A / Group C category feeding a Group B one. No pass-two
     category is drawn any more, so every such edge would have had a missing endpoint. They are
     removed rather than left to draw nothing. */

  function colors() {
    var c = window.LIN_STATUS_COLORS || {};
    return {
      Green: c.Green || "#2ee66b", Yellow: c.Yellow || "#ffe066",
      Amber: c.Amber || "#ff8c1a", Red: c.Red || "#ff3b30",
      Complete: c.Complete || "#4ea0ff", None: c.None || "#26344f",
      NotRelevant: c.NotRelevant || "#5b3dd6"
    };
  }
  /* ═══ RUN 94, SECTION 5. THE SITE'S OWN PALETTE, READ AT RUNTIME. ══════════════════════
     NOTHING IS INVENTED AND NOTHING IS ADDED TO THE THEME. Every colour below is a CSS custom
     property already declared in assets/css/radar.css, read with getComputedStyle off <body>,
     so the chart re-themes with the page. That is also the only way the requirement can hold
     across more than one theme: `server/app/theme.py` THEMES is ("plain","light","newyork",
     "maria") -- four storable themes, plus `dark` (Gotham), archived there but still rendering
     if forced -- and each redeclares these tokens with different values.

     The literals in the `||` arms are the values Run 90 had hard-coded. They are kept as a
     last-ditch fallback for a script-order failure in which getComputedStyle returns nothing,
     and they are NOT a second palette: on any real page the token wins. */
  var TOKENS = ["--page-bg", "--surface", "--surface-soft", "--line", "--line-strong",
                "--text", "--heading", "--muted", "--faint", "--accent",
                "--status-nodata", "--status-notrelevant-text"];
  function theme() {
    var out = {}, cs = null;
    try { cs = window.getComputedStyle(document.body); } catch (e) { cs = null; }
    TOKENS.forEach(function (k) {
      var v = "";
      if (cs) { try { v = String(cs.getPropertyValue(k) || "").trim(); } catch (e) { v = ""; } }
      out[k] = v;
    });
    return {
      pageBg:  out["--page-bg"]      || "#080d18",
      surface: out["--surface"]      || "#0b0e17",
      soft:    out["--surface-soft"] || "#111d31",
      line:    out["--line"]         || "#3a4a66",
      lineStrong: out["--line-strong"] || "#41506d",
      text:    out["--text"]         || "#e6edf9",
      /* NOT USED FOR ANY INK. FINDING, RUN 94: `--heading` is redeclared on `maria` and on
         :root only. The `newyork` and `dark` blocks override `--text` but NOT `--heading`, so
         on those two themes --heading resolves to the :root (Fairbanks) value #0f1216 -- near
         black -- and the words PROJECT STATUS rendered near-black on a near-black scrim. That
         was MEASURED in the rendered canvas PNG at 1280px on NYC, and it is the exact
         legibility Run 90 needed three iterations for. The token is read and reported; the ink
         comes from `--text`, which every theme block does redeclare. This is a defect in
         radar.css, NOT fixed here: fixing it would move a theme token, which section 5.3
         requires be declared, and section 6 does not put the stylesheet in scope. */
      heading: out["--heading"]      || "#e6edf9",
      muted:   out["--muted"]        || "#93a3bf",
      faint:   out["--faint"]        || "#7c8aa5"
    };
  }
  /* A CSS colour to {r,g,b,a}. Handles the three forms the theme blocks actually use --
     #rgb, #rrggbb and rgb()/rgba() -- and returns null for anything else rather than guessing. */
  function rgb(c) {
    c = String(c || "").trim();
    var m = /^#([0-9a-f]{3})$/i.exec(c);
    if (m) return { r: parseInt(m[1][0]+m[1][0],16), g: parseInt(m[1][1]+m[1][1],16),
                    b: parseInt(m[1][2]+m[1][2],16), a: 1 };
    m = /^#([0-9a-f]{6})$/i.exec(c);
    if (m) return { r: parseInt(m[1].slice(0,2),16), g: parseInt(m[1].slice(2,4),16),
                    b: parseInt(m[1].slice(4,6),16), a: 1 };
    m = /^rgba?\(([^)]+)\)$/i.exec(c);
    if (m) {
      var q = m[1].split(/[,\s\/]+/).filter(Boolean).map(parseFloat);
      if (q.length >= 3) return { r: q[0], g: q[1], b: q[2], a: q.length > 3 ? q[3] : 1 };
    }
    return null;
  }
  function alpha(c, a) {
    var v = rgb(c); if (!v) return c;
    return "rgba(" + Math.round(v.r) + "," + Math.round(v.g) + "," + Math.round(v.b) + "," + a + ")";
  }
  /* Blend toward white (t>0) or black (t<0). USED ONLY FOR SHADING A SPHERE, never to state a
     band: the body's dominant fill and its rim are always the exact band colour the rest of the
     interface uses, and only the terminator between them is mixed. */
  function shade(c, t) {
    var v = rgb(c); if (!v) return c;
    var to = t >= 0 ? 255 : 0, k = Math.abs(t);
    return "rgb(" + Math.round(v.r + (to - v.r) * k) + ","
                  + Math.round(v.g + (to - v.g) * k) + ","
                  + Math.round(v.b + (to - v.b) * k) + ")";
  }
  /* Is the page's own ground dark? The scene sits IN the page, so its shading has to know
     which way "lighter" is. Read from the theme, not assumed. */
  /* THE INK THE THEME ITSELF PRESCRIBES FOR TEXT SITTING ON A BAND. radar.css declares
     --status-ink-complete / green / yellow / amber (#0b1220 on the dark themes) and
     --status-ink-red (#f5f8ff); a planet's key is printed ON its band colour, so it must use
     the theme's own ink for that band rather than a white this file chose. */
  function inkFor(band) {
    var s = String(band || "").toLowerCase(), k = null;
    if (s.indexOf("red") >= 0) k = "red";
    else if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) k = "amber";
    else if (s.indexOf("yellow") >= 0) k = "yellow";
    else if (s.indexOf("green") >= 0) k = "green";
    else if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) k = "complete";
    var v = "";
    if (k) {
      try { v = String(window.getComputedStyle(document.body)
                       .getPropertyValue("--status-ink-" + k) || "").trim(); } catch (e) { v = ""; }
    }
    return v || "#ffffff";
  }
  function isDarkGround(TH) {
    var v = rgb(TH.pageBg);
    if (!v) return true;
    return (0.2126 * v.r + 0.7152 * v.g + 0.0722 * v.b) < 128;
  }

  function bandColor(band) {
    var C = colors(), s = String(band || "").toLowerCase();
    if (!s) return null;
    if (s.indexOf("complete") >= 0 || s.indexOf("blue") >= 0) return C.Complete;
    if (s.indexOf("green") >= 0) return C.Green;
    if (s.indexOf("yellow") >= 0 || s.indexOf("light-amber") >= 0) return C.Yellow;
    if (s.indexOf("amber") >= 0 || s.indexOf("orange") >= 0) return C.Amber;
    if (s.indexOf("red") >= 0) return C.Red;
    return null;
  }

  /* ------------------------------------------------------- 3D projection (charts3d idiom) --- */
  function rX(p, a) { return { x: p.x, y: p.y * Math.cos(a) - p.z * Math.sin(a), z: p.y * Math.sin(a) + p.z * Math.cos(a) }; }
  function rY(p, a) { return { x: p.x * Math.cos(a) + p.z * Math.sin(a), y: p.y, z: -p.x * Math.sin(a) + p.z * Math.cos(a) }; }
  /* NAMED `project3d`, NOT `project`. `render(container, project)` takes a PROJECT as its second
     argument, and a projection function called `project` was shadowed by it inside render() --
     the browser check caught exactly that, as "project is not a function", with an empty scene
     graph and an unchanged pixel hash. */
  function project3d(p, fov, cx, cy, zoom) {
    var z = p.z + fov; if (z < 1) z = 1;
    var s = (fov / z) * zoom;
    return { x: cx + p.x * s, y: cy + p.y * s, s: s, z: p.z };
  }

  /* ------------------------------------------------------------------------- the model ----- */
  function projectCategories() {
    if (window.performanceCategories) {
      try { return window.performanceCategories() || []; } catch (e) { /* fall through */ }
    }
    /* The same rule, inline, if taxonomy.js did not load its accessors: group A, project level.
       NOT a written-out list of six keys, so this arm cannot drift from the roster either. */
    return (window.LIN_CATEGORIES || []).filter(function (c) {
      return c && c.group === "A";  // RUN 97: no category is portfolio-level any more
    });
  }
  function storedRow(project) {
    try { return (window.LinResults && LinResults.rowFor(project)) || null; }
    catch (e) { return null; }
  }

  /* EVERY BODY IN THE SYSTEM, WITH THE STATE THE SERVER STORED. Read, never derived. The order
     of the tests matters and is the same order the Signal Flow uses, so the two charts can never
     disagree about a module: not relevant first (a declaration about the project type, which no
     reading can contradict), then a stored reading, then a stored abstention, then nothing. */
  function buildSystem(project, row) {
    var cats = projectCategories();
    var byId = Object.create(null), abst = Object.create(null);
    ((row && row.module_results) || []).forEach(function (m) { if (m && m.module_id) byId[m.module_id] = m; });
    ((row && row.abstained) || []).forEach(function (a) { if (a && a.module_id) abst[a.module_id] = a; });
    var cs = (row && row.category_statuses) || {};

    /* ═══ RUN 94b, SECTION 4. ONE COLOUR PER MODULE, HERE TOO. ═════════════════════════
       The same generator the Signal Flow uses, fed the same roster in the same order
       (`performanceCategories()`, then each category's own module order), so a module carries
       ONE identity colour across both charts and a reader can move between them. Generated
       from the roster at runtime; nothing is written by hand, and the generator keeps every
       identity colour at least dE*ab 25 from every band colour, so a moon's rim can never be
       mistaken for a verdict. THE STATE DISTINCTIONS ARE UNCHANGED: what the fill, the halo,
       the dash and the line width say is exactly what Run 90 established; only the rim's HUE
       is now the module's own. */
    var MOON_KEYS = [];
    cats.forEach(function (cat) {
      (cat.modules || []).forEach(function (m) { MOON_KEYS.push(m.module_id); });
    });
    var MOON_PAL = window.LIN_IDENTITY_PALETTE
      ? window.LIN_IDENTITY_PALETTE(MOON_KEYS, 'module') : null;
    LAST_PALETTE = MOON_PAL;
    function moonColour(id, fallback) {
      return (MOON_PAL && MOON_PAL.byKey && MOON_PAL.byKey[id]) || fallback;
    }

    var planets = cats.map(function (cat) {
      var e = cs[cat.key] || null;
      var moons = (cat.modules || []).map(function (m) {
        var na = false;
        try {
          na = !!((window.isModuleDisabled && window.isModuleDisabled(m.method_class))
                  || (window.isModuleSectorNA && window.isModuleSectorNA(m.method_class, project)));
        } catch (err) { na = false; }
        if (na) return { id: m.module_id, name: m.name, state: "not_relevant", band: null, display: null, reason: null, color: moonColour(m.module_id, null) };
        if (byId[m.module_id]) {
          var r = byId[m.module_id];
          /* RUN 90, THE COMMON CASE AND THE ONE THAT WAS WRONG. A module that COMPUTED and
             asserted NO BAND is the calibration-pending population -- 31 of them at Run 89 --
             and it is not an error. `bandColor(null)` returns null, and the moon painter used
             to fall back to `C.Complete`, so every one of them was drawn BLUE: a reading that
             asserted nothing rendered as the Complete band. `computed_unbanded` is that state,
             named, and it is drawn UNLIT. It stays distinguishable from `failed` and from
             `abstained`, which is what section 3.3 asks for. */
          var _band = r.band || r.status_color || null;
          return { id: m.module_id, name: m.name,
                   state: bandColor(_band) ? "computed" : "computed_unbanded",
                   band: _band,
                   display: (r.display != null ? r.display : r.value),
                   reason: r.evidence_metric || r.narrative || null,
                   color: moonColour(m.module_id, null) };
        }
        if (abst[m.module_id]) {
          return { id: m.module_id, name: m.name, state: "abstained", band: null, display: null,
                   reason: abst[m.module_id].reason || null, color: moonColour(m.module_id, null) };
        }
        return { id: m.module_id, name: m.name, state: "not_called", band: null, display: null, reason: null, color: moonColour(m.module_id, null) };
      });
      return {
        key: cat.key, name: cat.name,
        pass: 1,
        state: e ? (e.state || null) : "not_called",
        status: e ? (e.status || null) : null,
        contributes: !!(e && e.contributes_to_project_status),
        reason: e ? (e.reason || null) : null,
        moons: moons,
        lit: moons.filter(function (m) { return m.state === "computed"; }).length,
        total: moons.length
      };
    });

    /* THE EDGES, AND EVERY ONE OF THEM IS A DEPENDENCY THAT EXISTS.
         pass one -> pass two   only from a pass-one category that PRODUCED A STATUS. That is
                                exactly what `upstream_state_report` carries; a pass-one category
                                that produced nothing hands pass two nothing, and drawing the
                                line would draw a dependency that conveyed no finding.
         category -> health     only where the server stored a status AND its own projection row
                                says the category votes. */
    var edges = [];
    planets.forEach(function (p) {
      if (p.status && p.contributes) edges.push({ from: p.key, to: "__health__", kind: "fuse", band: p.status });
    });
    return { planets: planets, edges: edges, health: (row && row.project_status) || null };
  }

  /* --------------------------------------------------------------- positions in the system -- */
  function placeSystem(sys) {
    /* RUN 90, SECTION 3.4. ORBIT RADIUS CARRIES NO MEANING, AND NEITHER DOES ANYTHING ELSE
       GEOMETRIC. The owner has ruled radius arbitrary: the orbits are spaced for legibility only.

       WHAT WAS REMOVED, because it did encode something and therefore looked like it meant
       something. Run 82 set `p.radius = 20 + min(10, p.total * 0.9)` -- planet SIZE was the
       module count. It set the moon ring at `p.radius + 16 + min(16, p.total * 1.1)` -- orbit
       RADIUS was the module count again. And it set `rate = 0.34 / sqrt(p.total)` -- orbital
       SPEED was the module count a third time. All three are now constants. A reader can no
       longer draw a wrong inference from a big planet, a wide orbit or a slow moon, because
       every planet is the same size, every ring is the same width and every moon turns at the
       same rate. The count is still stated, in words, under each planet and in the note.

       THE SIX SIT ON ONE RING. There is no second ring, because there is no second population
       left to put on it. */
    /* THE THREE CONSTANTS. Sized in the browser at 1280px and 1024px, not guessed: at
       RING = 260 with a 24-unit planet the six planets and their moon rings overlapped the sun
       and each other, and the sun's own label was unreadable behind A1 and A4. Widening the
       ring and shrinking the bodies separates them. This is a LEGIBILITY decision, which is the
       only thing section 3.4 permits a radius to be chosen for. */
    var PLANET_RADIUS = 17;      /* constant: size encodes nothing */
    var RING = 430;              /* constant: radius encodes nothing */
    sys.planets.forEach(function (p, i) {
      var a = (i / Math.max(1, sys.planets.length)) * Math.PI * 2;
      /* ITERATION 3, AND IT IS A LEGIBILITY FIX MEASURED IN THE BROWSER, NOT A GUESS.
         With the ring lying deep in z (0.72 of R) the near half of it projected in FRONT of the
         sun: at 1280px, A1 and A4 sat on top of the centre and the words PROJECT STATUS / the
         no-posture status were unreadable behind them -- on the very state the order says to get
         right first. The ring is now close to the screen plane, so it projects as a wide, flat
         ellipse with the sun inside it and nothing in front of it. Radius is unchanged and
         still constant; only the PLANE the ring lies in moved. */
      p.pos = { x: Math.cos(a) * RING, y: Math.sin(a) * RING * 0.34, z: Math.sin(a) * RING * 0.16 };
      p.radius = PLANET_RADIUS;
    });
    /* THE MOONS. A ring around the planet, tilted out of the planet's own plane so the far side
       is visibly behind it and the count can be read. Nothing about the placement encodes a
       value; only colour and geometry do. */
    sys.planets.forEach(function (p) {
      var mr = p.radius + 46;   /* constant: the moon ring is the same width on every planet */
      p.moons.forEach(function (m, i) {
        /* RUN 83, PART C. THE ORBIT IS STORED, NOT THE POINT. Run 82 froze each moon at one
           angle; the owner asked for orbital motion. `orbit` carries the ring radius, the
           moon's phase on that ring, and its angular rate. `orbitAt(t)` is the only thing that
           turns those into a position, and it is called once per moon per frame.

           THE RATE ENCODES NOTHING. It is a function of the planet's roster size alone -- a
           bigger family turns slower, so a crowded ring stays readable -- and never of a band,
           a state or a value. Speed must not be mistaken for a reading. */
        m.orbit = {
          r: mr,
          phase: (i / Math.max(1, p.moons.length)) * Math.PI * 2
                 + (p.key.charCodeAt(1) || 0) * 0.3,
          rate: 0.22   /* constant: every moon turns at the same rate; speed encodes nothing */
        };
        m.pos = orbitAt(p, m, 0);
      });
    });
    sys.healthPos = { x: 0, y: 0, z: 0 };
    return sys;
  }

  /* ONE MOON'S POSITION AT TIME `t` SECONDS. The ring is tilted out of the planet's own plane
     (0.34 in y, 0.86 in z) exactly as Run 82 placed it, so the far half of the orbit passes
     visibly behind the planet and the count can still be read. Only the angle moves. */
  function orbitAt(p, m, t) {
    var a = m.orbit.phase + t * m.orbit.rate;
    return { x: p.pos.x + Math.cos(a) * m.orbit.r,
             y: p.pos.y + Math.sin(a) * m.orbit.r * 0.34 - 4,
             z: p.pos.z + Math.sin(a) * m.orbit.r * 0.86 };
  }

  /* ------------------------------------------------------------------------- the drawing --- */
  var LAST_SCENE = null;
  /* RUN 94b. The identity palette the last build actually used, so a check reads the object
     the chart drew with instead of recomputing one. */
  var LAST_PALETTE = null;

  function render(container, project) {
    if (!container) return;
    container.innerHTML =
      '<div class="projnet2d-wrap"><canvas class="projnet2d-canvas"></canvas></div>'
      + '<p class="projnet2d-note"></p>';
    var wrap = container.querySelector(".projnet2d-wrap");
    var canvas = container.querySelector(".projnet2d-canvas");
    var note = container.querySelector(".projnet2d-note");
    if (!canvas || !wrap) return;
    var ctx = canvas.getContext("2d");
    var C = colors();

    var row = storedRow(project);
    var sys = placeSystem(buildSystem(project, row));

    var totalModules = 0, litModules = 0, unbanded = 0, dark = 0, na = 0, notCalled = 0;
    sys.planets.forEach(function (p) {
      totalModules += p.total; litModules += p.lit;
      p.moons.forEach(function (m) {
        if (m.state === "computed_unbanded") unbanded++;
        else if (m.state === "abstained") dark++;
        else if (m.state === "not_relevant") na++;
        else if (m.state === "not_called") notCalled++;
      });
    });
    var litCats = sys.planets.filter(function (p) { return p.status; }).length;
    var failedCats = sys.planets.filter(function (p) { return p.state === "failed"; });

    /* THE FIGURES IN WORDS, BESIDE THE PICTURE. The owner reads this on a phone; a drawing that
       states no figure is not a report. Nothing here is a control. */
    note.textContent =
      litCats + " of " + sys.planets.length + " performance categories carry a posture. "
      + litModules + " of " + totalModules + " modules in service assert a band; "
      + unbanded + " computed without asserting one, "
      + dark + " have nothing to report, " + na + " are not relevant to this project, and "
      + notCalled + " have not been called. "
      + (failedCats.length
          ? failedCats.length + " category (" + failedCats.map(function (p) { return p.key; }).join(", ")
            + ") failed and is struck through. "
          : "")
      + "Project health: " + (sys.health || "no status") + ".";
    container.setAttribute("data-modules", String(totalModules));
    container.setAttribute("data-modules-lit", String(litModules));
    container.setAttribute("data-modules-unbanded", String(unbanded));
    container.setAttribute("data-modules-dark", String(dark));
    container.setAttribute("data-modules-na", String(na));
    container.setAttribute("data-modules-notcalled", String(notCalled));
    container.setAttribute("data-categories", String(sys.planets.length));
    container.setAttribute("data-categories-lit", String(litCats));
    container.setAttribute("data-edges", String(sys.edges.length));
    container.setAttribute("data-health", String(sys.health || "none"));

    var rx = -0.44, ry = 0.55, zoom = 1;
    var size = { w: 0, h: 0 };

    function resize() {
      var dpr = window.devicePixelRatio || 1;
      var r = wrap.getBoundingClientRect();
      size.w = Math.max(320, Math.round(r.width || 900));
      size.h = Math.max(360, Math.round(Math.min(620, (r.width || 900) * 0.62)));
      canvas.width = Math.round(size.w * dpr);
      canvas.height = Math.round(size.h * dpr);
      canvas.style.width = size.w + "px";
      canvas.style.height = size.h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function tf(p) {
      var fov = Math.min(size.w, size.h) * 1.55;
      return project3d(rX(rY(p, ry), rx), fov, size.w / 2, size.h / 2, zoom);
    }

    /* THE CLOCK. `orbitT` is seconds of orbital time, advanced by the animation loop and by
       nothing else. A drag, a wheel or a resize redraws at the SAME `orbitT`, so interacting
       with the chart never jumps the moons. */
    var orbitT = 0;

    function draw() {
      if (!size.w) resize();
      /* Re-read the palette every frame: the theme switcher changes it under a live canvas. */
      var TH = theme(), DARK = isDarkGround(TH);
      C = colors();
      /* Re-place every moon for this instant. Sixty-three cosines and sines per frame; this is
         the whole cost of the animation and it is measured in the report. */
      sys.planets.forEach(function (p) {
        p.moons.forEach(function (m) { m.pos = orbitAt(p, m, orbitT); });
      });
      /* RUN 95. `labels` is the drawn category-name label for each planet, recorded in the
         scene graph exactly as `bodies` and `edges` are, so a check can assert on the TEXT A
         READER ACTUALLY SEES rather than on the presence of a string in the source file.
         "the file does not contain A5.2" is worth nothing; "no planet was labelled Systems
         and Dynamics" is the real assertion. */
      /* Break a label on spaces to at most `maxLines` lines that each measure under `maxW`,
         measured with the real font through `measureText` rather than by counting characters.
         The last line keeps whatever remains: a name is never cut, because a cut category name
         is one the reader still cannot resolve. */
      function wrapLabel(ctx2, text, font, maxW, maxLines) {
        var prev = ctx2.font;
        ctx2.font = font;
        var words = String(text).split(/\s+/).filter(Boolean);
        var lines = [];
        var cur = "";
        for (var i = 0; i < words.length; i++) {
          var trial = cur ? cur + " " + words[i] : words[i];
          if (cur && ctx2.measureText(trial).width > maxW && lines.length < maxLines - 1) {
            lines.push(cur); cur = words[i];
          } else {
            cur = trial;
          }
        }
        if (cur) lines.push(cur);
        ctx2.font = prev;
        return lines.length ? lines : [String(text)];
      }

      var scene = { bodies: [], edges: [], labels: [] };
      ctx.clearRect(0, 0, size.w, size.h);

      /* ═══ RUN 94, SECTION 4.2. THE FIELD THE SYSTEM SITS IN. ═══════════════════════════
         STILL NOT A STARFIELD. Run 90's reason stands and is not softened: a random speck
         would be mistaken for a body, and a body is a module. What replaces the flat black is
         a DEPTH WASH -- one radial gradient, brightest at the centre of the system and falling
         to the page's own ground at the corners, plus a soft vignette. It states nothing. It
         is the same wash whatever the row says, on every project, and it is drawn from the
         page's own --surface / --page-bg tokens, so on Fairbanks and Miami the field is light
         and on Gotham and NYC it is dark. The picture is no longer drained; the ABSENCE that
         has to stay visible is a property of one body, and it is drawn on that body. */
      var cxw = size.w / 2, cyw = size.h / 2, rad = Math.max(size.w, size.h) * 0.78;
      var wash = ctx.createRadialGradient(cxw, cyw * 0.92, 0, cxw, cyw, rad);
      wash.addColorStop(0, alpha(DARK ? shade(TH.surface, 0.10) : TH.surface, 1));
      wash.addColorStop(0.55, alpha(TH.surface, 1));
      wash.addColorStop(1, alpha(DARK ? shade(TH.pageBg, -0.25) : TH.pageBg, 1));
      ctx.fillStyle = wash;
      ctx.fillRect(0, 0, size.w, size.h);
      /* A single faint horizon band, so the scene has a floor to sit on rather than floating in
         a void. It marks nothing: it is at a fixed fraction of the canvas, not at any body. */
      var hz = ctx.createLinearGradient(0, cyw * 0.55, 0, size.h);
      hz.addColorStop(0, alpha(TH.line, 0));
      hz.addColorStop(0.62, alpha(TH.line, DARK ? 0.16 : 0.10));
      hz.addColorStop(1, alpha(TH.line, 0));
      ctx.fillStyle = hz; ctx.fillRect(0, 0, size.w, size.h);

      var hp = tf(sys.healthPos);
      var byKey = Object.create(null);
      sys.planets.forEach(function (p) { byKey[p.key] = p; });

      /* EDGES FIRST, so bodies sit on top of them. */
      sys.edges.forEach(function (e) {
        var a = byKey[e.from], b = e.to === "__health__" ? null : byKey[e.to];
        if (!a) return;
        var pa = tf(a.pos), pb = b ? tf(b.pos) : hp;
        var col = bandColor(e.band) || C.Complete;
        ctx.strokeStyle = col;
        ctx.globalAlpha = e.kind === "fuse" ? 0.55 : 0.3;
        ctx.lineWidth = e.kind === "fuse" ? 1.8 : 1.1;
        ctx.beginPath(); ctx.moveTo(pa.x, pa.y); ctx.lineTo(pb.x, pb.y); ctx.stroke();
        ctx.globalAlpha = 1;
        scene.edges.push({ from: e.from, to: e.to, kind: e.kind, band: e.band || null,
                           x1: Math.round(pa.x), y1: Math.round(pa.y),
                           x2: Math.round(pb.x), y2: Math.round(pb.y) });
      });

      /* THE SUN: THE PROJECT STATUS, AND IT IS UNLIT WHEN THE PLATFORM CANNOT CERTIFY ONE.

         Run 89 made the no-posture word a real status: any of the required core A1, A2, A3,
         A4, A6 without a posture and the platform issues no band at all. That word -- since
         Run 106, "Awaiting analysis" -- is deliberately absent from `fusion.BAND_SEVERITY`,
         so `bandColor()` returns null for it
         by the same route it returns null for a missing status -- nothing here tests for the
         word. On most current rows this is the state, so it is the one drawn first and
         deliberately: A DARK CENTRE, with a corona only when a band was actually issued. */
      var hcol = bandColor(sys.health);
      var sunR = 26 * hp.s * 1.6;
      if (hcol) {
        /* RUN 94. A CORONA WITH FALL-OFF, not one flat disc of colour. Three stops instead of
           two, so the light reads as light. The band colour itself is unchanged: stop 0 IS the
           status token, and it is the same hex the status pill carries elsewhere. */
        var sgrd = ctx.createRadialGradient(hp.x, hp.y, sunR * 0.6, hp.x, hp.y, sunR * 3.0);
        sgrd.addColorStop(0, alpha(hcol, 0.85));
        sgrd.addColorStop(0.35, alpha(hcol, 0.30));
        sgrd.addColorStop(1, alpha(hcol, 0));
        ctx.beginPath(); ctx.arc(hp.x, hp.y, sunR * 3.0, 0, Math.PI * 2);
        ctx.fillStyle = sgrd; ctx.fill();
        var sbody = ctx.createRadialGradient(hp.x - sunR * 0.3, hp.y - sunR * 0.35, sunR * 0.08,
                                             hp.x, hp.y, sunR);
        sbody.addColorStop(0, shade(hcol, 0.55));
        sbody.addColorStop(0.45, hcol);
        sbody.addColorStop(1, shade(hcol, -0.28));
        ctx.beginPath(); ctx.arc(hp.x, hp.y, sunR, 0, Math.PI * 2);
        ctx.fillStyle = sbody; ctx.fill();
        ctx.strokeStyle = hcol; ctx.lineWidth = 2; ctx.stroke();
      } else {
        /* UNLIT, AND IT STAYS UNLIT. Run 90's rule: with no posture the platform has issued no
           band, so the centre carries no band colour and no corona of any kind. It is drawn
           from the theme's own no-data surface and dashed rim, which is what makes it read as
           an absence in the site's own language rather than as a fifth quiet band. */
        ctx.beginPath(); ctx.arc(hp.x, hp.y, sunR, 0, Math.PI * 2);
        ctx.fillStyle = DARK ? shade(TH.surface, -0.35) : shade(TH.soft, -0.06); ctx.fill();
        ctx.strokeStyle = TH.lineStrong; ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]); ctx.stroke(); ctx.setLineDash([]);
      }
      scene.bodies.push({ kind: "health", key: "__health__",
                          state: hcol ? "lit" : "unlit",
                          status: sys.health || null, x: Math.round(hp.x), y: Math.round(hp.y),
                          r: Math.round(sunR) });

      /* BODIES, PAINTER'S ORDER: everything sorted back to front so the far side of a ring is
         drawn first and is genuinely behind. */
      var drawables = [];
      sys.planets.forEach(function (p) {
        drawables.push({ t: "planet", p: p, z: rX(rY(p.pos, ry), rx).z });
        p.moons.forEach(function (m) {
          drawables.push({ t: "moon", p: p, m: m, z: rX(rY(m.pos, ry), rx).z });
        });
      });
      drawables.sort(function (a, b) { return b.z - a.z; });

      drawables.forEach(function (d) {
        if (d.t === "planet") {
          var p = d.p, q = tf(p.pos), r = p.radius * q.s * 1.5;
          var col = bandColor(p.status);
          var failed = p.state === "failed";
          if (failed) {
            ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, Math.PI * 2);
            ctx.fillStyle = C.Red; ctx.globalAlpha = 0.92; ctx.fill(); ctx.globalAlpha = 1;
            ctx.strokeStyle = C.Red; ctx.lineWidth = 2.4; ctx.stroke();
            /* IT LOOKS WRONG ON PURPOSE, and by geometry as well as colour. */
            ctx.strokeStyle = inkFor("red"); ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(q.x - r * 0.7, q.y - r * 0.7); ctx.lineTo(q.x + r * 0.7, q.y + r * 0.7);
            ctx.moveTo(q.x + r * 0.7, q.y - r * 0.7); ctx.lineTo(q.x - r * 0.7, q.y + r * 0.7);
            ctx.stroke();
          } else if (col) {
            /* RUN 94, SECTION 4.1. A LIT PLANET IS A SPHERE, NOT A FLAT DISC. One glow pass with
               fall-off, then a limb-shaded body: the light comes from the upper left on EVERY
               body, identically, so the shading is depth and nothing else. The dominant fill and
               the rim are the exact band colour the status pill uses; only the terminator is
               mixed, which is why a reader never has to learn a second colour language. */
            var grd = ctx.createRadialGradient(q.x, q.y, r * 0.7, q.x, q.y, r * 2.3);
            grd.addColorStop(0, alpha(col, 0.42));
            grd.addColorStop(0.4, alpha(col, 0.16));
            grd.addColorStop(1, alpha(col, 0));
            ctx.beginPath(); ctx.arc(q.x, q.y, r * 2.3, 0, Math.PI * 2);
            ctx.fillStyle = grd; ctx.fill();
            var body = ctx.createRadialGradient(q.x - r * 0.34, q.y - r * 0.38, r * 0.05,
                                                q.x, q.y, r);
            body.addColorStop(0, shade(col, 0.45));
            body.addColorStop(0.42, col);
            body.addColorStop(1, shade(col, -0.32));
            ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, Math.PI * 2);
            ctx.fillStyle = body; ctx.fill();
            ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.stroke();
          } else {
            /* RUN 90, SECTION 3.2. A CATEGORY CARRYING NO POSTURE MUST NOT READ AS ANY BAND.
               No fill of any band colour, no corona, and a dashed neutral rim in every case --
               Run 82 dashed it only when the category had never been called, which left a
               category that WAS called and produced no posture drawn with a solid rim that
               read like a quiet fifth band. Both are the same fact to a reader: not assessed. */
            /* RUN 94 keeps this exactly as Run 90 ruled it, and only re-sources the two
               colours from the theme. NO band fill, NO corona, NO sphere shading -- a
               not-assessed planet must not gain the presence the lit ones just gained, because
               that presence is what "lit" now means. It is a flat, hollow, dashed outline on
               the page's own surface: visibly a body, visibly not reporting. */
            ctx.beginPath(); ctx.arc(q.x, q.y, r, 0, Math.PI * 2);
            ctx.fillStyle = DARK ? shade(TH.surface, 0.06) : shade(TH.soft, -0.03);
            ctx.fill();
            ctx.strokeStyle = TH.lineStrong; ctx.lineWidth = 1.3;
            ctx.setLineDash([4, 4]);
            ctx.stroke(); ctx.setLineDash([]);
          }
          /* RUN 95, SECTION 4.1. EVERY PLANET CARRIES ITS CATEGORY'S NAME.
             The owner: "Nobody reads A3 and knows it means Cost Risk." Before this run the
             only label a planet had was its key, drawn inside the disc, and a reader had to
             already know the taxonomy to read the chart at all.

             THE NAME IS DRAWN BELOW THE PLANET, NOT INSIDE IT, and that is a layout decision
             rather than a compromise. A planet's MODEL radius is 17px and the same for every
             body -- one value, so that nothing is encoded in size -- and "Cost & EVM
             Performance" cannot be set inside 34px at a legible size at any weight. Shrinking
             the type until it fits would make the label unreadable, and growing the disc would
             start encoding something in a radius that must encode nothing. The space beneath
             the body is free, is already used for the banded count, and is where the reader's
             eye goes next.

             IT WRAPS RATHER THAN TRUNCATING. `wrapLabel` breaks on spaces to at most two
             lines against a real `measureText` width, so a long name is set on two lines
             instead of being cut with an ellipsis. A truncated category name is a name the
             reader still cannot resolve, which is the defect this fixes. The key stays inside
             the disc, small: it is the identifier, it is what the ledger and the exports use,
             and dropping it would break the reader's path between the surfaces.

             The count and the not-assessed line move down by the height the name occupies, so
             nothing overlaps at either rendered width. */
          ctx.fillStyle = failed ? inkFor("red") : (col ? inkFor(p.status) : TH.text);
          ctx.font = "700 10px system-ui, sans-serif"; ctx.textAlign = "center";
          ctx.fillText(p.key, q.x, q.y + 3.5);

          var nameLines = wrapLabel(ctx, String(p.name || p.key),
                                    "700 11px system-ui, sans-serif", 132, 2);
          ctx.font = "700 11px system-ui, sans-serif";
          ctx.fillStyle = failed ? inkFor("red") : (col ? inkFor(p.status) : TH.text);
          var ny = q.y + r + 13;
          nameLines.forEach(function (ln, li) { ctx.fillText(ln, q.x, ny + li * 12); });
          var below = ny + nameLines.length * 12;

          ctx.font = "9px system-ui, sans-serif"; ctx.fillStyle = TH.muted;
          ctx.fillText(p.lit + " of " + p.total + " banded", q.x, below);
          if (!col && !failed) {
            ctx.fillStyle = TH.faint;
            ctx.fillText("not assessed", q.x, below + 11);
          }
          scene.labels.push({ key: p.key, name: String(p.name || ""),
                              lines: nameLines.slice(), x: q.x, y: ny });
          /* RUN 90. `baseR` and `orbitR` are the MODEL radii, before the perspective divide.
             They are in the scene graph so a check can prove the constraint the order actually
             states -- that size and orbit radius encode nothing -- from what was drawn. The
             DRAWN radius legitimately differs body to body because a body further from the
             camera is smaller; that is depth, and it is not a reading. A check that asserted
             on the drawn radius would fail a correct chart, which is how this run first
             mis-measured it. */
          scene.bodies.push({ kind: "planet", key: p.key, pass: p.pass, baseR: p.radius,
                              state: failed ? "failed" : (p.status ? "computed" : (p.state || "not_called")),
                              status: p.status || null, lit: p.lit, total: p.total,
                              x: Math.round(q.x), y: Math.round(q.y), r: Math.round(r) });
        } else {
          var m = d.m, mq = tf(m.pos), mr = Math.max(2.2, 5.2 * mq.s * 1.5);
          /* RUN 94b, SECTION 4. THE MODULE'S OWN COLOUR, ON EVERY MOON, IN EVERY STATE.
             `m.color` is generated from the roster at runtime (see buildSystem) and is never
             within dE*ab 25 of a band colour. It is applied to the RIM only. The five states
             keep exactly the distinctions Run 90 established -- filled and haloed in the BAND
             colour for a module that asserted one, a plain rimmed body for one that computed
             and asserted none, a dark filled body for an abstention, a dashed outline for a
             module not relevant to this project, a dotted one for a module never called -- so
             the state is still read off fill, halo and dash, and identity off hue. Before this,
             every unbanded moon was drawn in a theme grey: 36 of the 42 rendered as pale
             outlines on a pale ground and the owner reported seeing no moons at all. */
          var midc = m.color || null;
          if (m.state === "computed") {
            var mc = bandColor(m.band) || C.Complete;
            /* A LIT BODY, with a halo so it reads as lit and not merely coloured. */
            var mg = ctx.createRadialGradient(mq.x, mq.y, mr * 0.5, mq.x, mq.y, mr * 2.8);
            mg.addColorStop(0, alpha(mc, 0.40));
            mg.addColorStop(1, alpha(mc, 0));
            ctx.beginPath(); ctx.arc(mq.x, mq.y, mr * 2.8, 0, Math.PI * 2);
            ctx.fillStyle = mg; ctx.fill();
            var mb = ctx.createRadialGradient(mq.x - mr * 0.35, mq.y - mr * 0.4, mr * 0.05,
                                              mq.x, mq.y, mr);
            mb.addColorStop(0, shade(mc, 0.5)); mb.addColorStop(0.45, mc);
            mb.addColorStop(1, shade(mc, -0.3));
            ctx.beginPath(); ctx.arc(mq.x, mq.y, mr, 0, Math.PI * 2);
            ctx.fillStyle = mb; ctx.fill();
            /* The rim is the module's identity; the body and halo stay the BAND colour, so
               the verdict is still read off the fill and never off the rim. */
            ctx.strokeStyle = midc || mc; ctx.lineWidth = 1.2; ctx.globalAlpha = 0.95;
            ctx.stroke(); ctx.globalAlpha = 1;
          } else if (m.state === "computed_unbanded") {
            /* RUN 90. COMPUTED, AND ASSERTED NO BAND. Visible and UNLIT: a body with a rim, no
               fill of any band colour and no halo, so it can never be read as Complete or as
               any other band. It is drawn LARGER and with a brighter rim than an abstention,
               because a figure was produced here and nothing was produced there. */
            ctx.beginPath(); ctx.arc(mq.x, mq.y, mr, 0, Math.PI * 2);
            ctx.fillStyle = DARK ? shade(TH.surface, 0.10) : shade(TH.soft, -0.02); ctx.fill();
            /* The rim is --muted, not --text: at --text the unbanded moons rendered as bright
               white rings that read as LIT. They must be visible and unlit. --muted still
               outranks the abstention's --faint, which is Run 90's stated ordering. */
            ctx.strokeStyle = midc || TH.muted; ctx.lineWidth = 1.6; ctx.stroke();
          } else if (m.state === "abstained") {
            /* DARK, STILL IN ORBIT: a filled body with a solid rim. Present, silent. */
            ctx.beginPath(); ctx.arc(mq.x, mq.y, mr * 0.92, 0, Math.PI * 2);
            ctx.fillStyle = C.None; ctx.fill();
            ctx.strokeStyle = midc || TH.faint; ctx.lineWidth = 1.2; ctx.stroke();
          } else if (m.state === "not_relevant") {
            /* OUTLINE ONLY, NO BODY. Never called; does not apply to this project type. */
            ctx.beginPath(); ctx.arc(mq.x, mq.y, mr, 0, Math.PI * 2);
            ctx.strokeStyle = midc || C.NotRelevant; ctx.lineWidth = 1.3;
            ctx.setLineDash([2, 2]); ctx.stroke(); ctx.setLineDash([]);
          } else {
            /* NOT CALLED: dotted, no fill, no rim. Distinct from both dark states above. */
            ctx.beginPath(); ctx.arc(mq.x, mq.y, mr * 0.85, 0, Math.PI * 2);
            ctx.strokeStyle = midc || TH.line; ctx.lineWidth = 1.1;
            ctx.setLineDash([1, 2.2]); ctx.stroke(); ctx.setLineDash([]);
          }
          scene.bodies.push({ kind: "moon", key: m.id, category: d.p.key, state: m.state,
                              identityColor: midc,
                              orbitR: m.orbit.r, orbitRate: m.orbit.rate,
                              band: m.band || null, x: Math.round(mq.x), y: Math.round(mq.y),
                              r: Math.round(mr * 10) / 10 });
        }
      });

      /* THE SUN'S WORDS ARE PAINTED LAST, OVER EVERYTHING. A planet in front of the centre
         used to cover them. The reader must always be able to read the status, and on most
         current rows that word is "Awaiting analysis" (Run 106 goal two; it was
         "Indeterminate" until the owner ruled the seventh word out). */
      ctx.textAlign = "center";
      ctx.fillStyle = alpha(TH.surface, 0.86);
      var lw = Math.max(ctx.measureText("PROJECT STATUS").width,
                        ctx.measureText(String(sys.health || "no status")).width) + 16;
      ctx.fillRect(hp.x - lw / 2, hp.y - 18, lw, 36);
      ctx.fillStyle = TH.text; ctx.font = "600 12px system-ui, sans-serif";
      ctx.fillText("PROJECT STATUS", hp.x, hp.y - 4);
      ctx.fillStyle = hcol || TH.muted;
      ctx.fillText(String(sys.health || "no status"), hp.x, hp.y + 12);

      ctx.textAlign = "left";
      LAST_SCENE = scene;
      container.setAttribute("data-scene-bodies", String(scene.bodies.length));
      container.setAttribute("data-scene-edges", String(scene.edges.length));
    }

    /* -------------------------------------------------- interaction: NO DOM CONTROL ADDED --- */
    var dragging = false, lx = 0, ly = 0;
    function onWheel(e) {
      e.preventDefault();
      zoom = Math.max(0.55, Math.min(2.6, zoom * (e.deltaY < 0 ? 1.09 : 0.92)));
      draw();
    }
    function onDown(e) { dragging = true; lx = e.clientX; ly = e.clientY; canvas.style.cursor = "grabbing"; }
    function onMove(e) {
      if (!dragging) return;
      ry += (e.clientX - lx) * 0.006;
      rx += (e.clientY - ly) * 0.006;
      rx = Math.max(-1.35, Math.min(1.35, rx));
      lx = e.clientX; ly = e.clientY;
      draw();
    }
    function onUp() { dragging = false; canvas.style.cursor = "grab"; }
    function onResize() { resize(); draw(); }
    function cleanup() {
      if (raf) { window.cancelAnimationFrame(raf); raf = 0; }
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("resize", onResize);
    }
    canvas.addEventListener("wheel", onWheel, { passive: false });
    canvas.addEventListener("mousedown", onDown);
    canvas.style.cursor = "grab";
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("resize", onResize);
    /* A detached canvas means the detail page was re-rendered — self-clean and stop. */
    var tick = setInterval(function () {
      if (!document.body.contains(canvas)) { cleanup(); clearInterval(tick); }
    }, 2000);

    resize();
    draw();
    /* One re-measure after layout settles, so a canvas mounted inside a section that was
       display:none when this ran is not left drawn at the wrong size. */
    setTimeout(function () { resize(); draw(); }, 60);

    /* ------------------------------------------------------------------- THE ANIMATION ---
       ORBITAL MOTION, AND THE THREE THINGS THAT STOP IT.

       1. `prefers-reduced-motion: reduce`. The chart renders once, complete, and never moves.
          Every figure and every state is still drawn; the order's constraint 4 says reduce the
          animation rather than the information, and a person who has asked their operating
          system for stillness has asked for exactly that reduction.
       2. The canvas leaving the document. The detail page re-renders on every period change;
          a loop left running against a detached canvas is a leak.
       3. The tab being hidden. `requestAnimationFrame` already throttles there, but the frame
          budget check below would otherwise read a throttled frame as a slow one.

       THE FRAME BUDGET, AND WHAT IT DEGRADES TO. If the mean frame time over a rolling window
       exceeds 24ms -- roughly 40fps -- the loop drops to redrawing every OTHER frame, and if it
       is still over budget after that, every fourth. The information never changes: the same
       eleven planets, the same sixty-three moons, the same edges, the same note. Only the
       number of redraws falls. That is the order's constraint 4 followed literally.

       NOTHING HERE COMPUTES. `orbitT` moves an angle. No band, no state, no value and no edge
       is a function of it. */
    var reduce = false;
    try {
      reduce = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    } catch (e) { reduce = false; }
    container.setAttribute("data-animated", reduce ? "reduced" : "orbiting");

    var raf = 0, prev = 0, frames = 0, acc = 0, skip = 1, phase = 0;
    function loop(ts) {
      if (!document.body.contains(canvas)) { cleanup(); return; }
      raf = window.requestAnimationFrame(loop);
      if (!prev) { prev = ts; return; }
      var dt = ts - prev; prev = ts;
      if (dt > 250) return;                       /* tab was hidden; not a slow frame */
      orbitT += dt / 1000;
      phase = (phase + 1) % skip;
      if (phase !== 0) return;
      draw();
      acc += dt; frames++;
      if (frames >= 45) {
        var mean = acc / frames;
        if (mean > 24 && skip < 4) skip *= 2;
        else if (mean < 12 && skip > 1) skip /= 2;
        container.setAttribute("data-frame-ms", String(Math.round(mean * 10) / 10));
        container.setAttribute("data-frame-skip", String(skip));
        acc = 0; frames = 0;
      }
    }
    if (!reduce) raf = window.requestAnimationFrame(loop);
  }

  window.LinProjectNet2D = {
    render: render,
    /* THE SCENE GRAPH THE LAST FRAME WAS DRAWN FROM. Exposed so a check can assert on what was
       drawn rather than on the model it was given -- the canvas equivalent of reading the DOM. */
    lastScene: function () { return LAST_SCENE; },
    lastPalette: function () { return LAST_PALETTE; }
  };
})();
