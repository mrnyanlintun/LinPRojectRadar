# The logo's radar sweep

## Where the logo appears

Six places. I searched for `logo.png` and `logo.svg` across every HTML, JS, CSS, JSON and Markdown
file in the repository rather than assuming.

| # | Location | File | Rendered at | Sweep added |
|---|---|---|---|---|
| 1 | Favicon | `index.html:40` | browser tab | **No, and it cannot be.** See below |
| 2 | Sign-in panel | `index.html:280` | 56 by 56 | Yes |
| 3 | Access-denied panel | `index.html:360` | 56 by 56 | Yes |
| 4 | Consent panel | `index.html:383` | 56 by 56 | Yes |
| 5 | Top bar | `index.html:422` | 96 tall, 104 wide | Yes |
| 6 | Icon dock emblem | `assets/js/app.js:2347` | 40 by 40, circle-cropped | Yes, replacing the one that was there |

**The favicon is the one place this cannot reach.** It is a `<link rel="icon">`, painted by the
browser as tab chrome. No CSS or SVG in the page can animate it, and the only way to make it move
would be to swap the `href` on a timer from JavaScript, which is an animation library in all but
name and would spin the tab icon of every open tab. Left alone deliberately.

**There is no separate loading screen.** The brief asked for "the loading state", so I looked for
one: `auth.js` has four screens (`lin-login`, `lin-access-denied`, `lin-consent`, `lin-app`), all
hidden until authentication resolves, and the first thing an unauthenticated visitor sees is the
sign-in panel, which is location 2. The only other loader on the site is the map's, which mounts
`LinWorkingRobot` and does not use the logo at all. So the loading state is covered, by covering
the sign-in panel.

**The dock already had a sweep, and it was a different design.** `.dock-emblem-sweep` turned a
quarter circle of `--phosphor` over the *whole* button, gold rim included. It has been replaced by
the shared `.logo-sweep`, so the site now has one sweep rather than two designs of one.

---

## Could I see it move? No.

**Compositing is unavailable in this container, so I did not observe the animation. I verified that
it is declared, correctly shaped and running; I did not verify that anything moves.**

Measured before making any claim, as instructed:

```
requestAnimationFrame frames in 1515 ms : 0        (0 fps)
document.visibilityState                : "hidden"
document.timeline.currentTime           : 0, 0, 0, 0   (four samples over 2.1 s)
animation.playState                     : "running"
animation.currentTime                   : 0, 0, 0, 0
computed transform                      : matrix(1,0,0,1,0,0) throughout
```

The browser has created the animation and reports it as running, but the document timeline is
frozen at zero and never advances, so no frame is ever produced. A screenshot attempt returns the
same verdict from the other side: *"the Browser pane is not displayed, so the page is not
compositing frames."*

This measurement is itself the proof that the check can fail, which is what the brief asked for: it
is not a check that passed, it is a check reporting the absence of motion in the exact condition
where motion is absent. A frame counter reads zero when nothing is drawn. It cannot be satisfied by
a page flattened to black, or by any static content, because it counts callbacks rather than
inspecting pixels.

What that leaves unverified, stated plainly: **that the sweep visually turns, at the right speed, in
the right direction, without tearing or banding.** Everything below is a DOM and CSS read, or an
offline render of the exact gradient. None of it is evidence of motion.

---

## What was built

An inert `<span class="logo-sweep">` inside a `<span class="logo-mark">` wrapper at each of the five
in-page locations, with one shared CSS rule. The image itself is untouched: `logo.png` is not
redrawn, regenerated, masked or patched.

**Geometry, measured from the artwork rather than guessed.** `logo.png` is 1531 by 1413. I found the
wheel's centre at 765, 705, which is the image centre to within a pixel, so the sweep centres on the
box with `inset: 0; margin: auto`. The dark radar face inside the gold ring has a radius of 400
image pixels, which is 56.6% of the image height. That is where the one magic number comes from, and
it is why the sweep stops at the face instead of turning over the gold.

The three panel logos are drawn into a 56 by 56 box with no `object-fit`, so the image is squashed
by its 1531:1413 aspect and the round face becomes a slight ellipse. A circle of the mean diameter
sits on it to within about a pixel, which is closer than a translucent glow can show, so those get
54.4% instead.

Measured in the live DOM:

| Site | Image box | Sweep | Circle | Centred on image | Animation | Inert |
|---|---|---|---|---|---|---|
| Sign-in | 56 x 56 | 30.5 | yes | yes | `logo-sweep 8s linear infinite` | yes |
| Access-denied | 56 x 56 | 30.5 | yes | yes | same | yes |
| Consent | 56 x 56 | 30.5 | yes | yes | same | yes |
| Top bar | 104 x 96 | 54.3 | yes | yes | same | yes |
| Dock emblem | 38.4 x 38.4 | 21.7 | yes | yes | same | yes |

A full revolution takes 8 seconds, linear, matching the duration the dock's previous sweep already
used.

**Colour is fixed, not themed.** It matches a raster that does not change with the theme, so it does
not use `--phosphor`. Matching the artwork was the instruction.

---

## The drawn wedge, and why this is a sweep line rather than a rotating quadrant

The brief said to stop rather than ship something that looks like two different sweeps. That case
was real, and it is worth recording what it looked like.

**A full-quadrant overlay was built first and it does not work.** The artwork's wedge is a bright
quarter of the radar face, from twelve o'clock round to three o'clock. Rotating a second quadrant of
the same size above it means that at every angle except the start you see two equally large bright
blocks in different places. Rendered at 96 pixels and inspected, at 150 degrees of rotation the
drawn quadrant sits in the upper right and the overlay sits across the bottom left: two sweeps on
one instrument. That is the thing the brief said not to ship, and I did not ship it.

**What I tried before settling.** Masking or patching out the drawn quadrant was rejected because
the face under it is not flat: it carries range arcs, tick marks and coloured returns that the rest
of the face does not have, so covering it means repainting that content, which is redrawing the
artwork. A darken-the-quadrant plus brighten-the-sweep pair using blend modes was rejected for the
same reason, since a uniform multiply would flatten those returns and leave a visible seam.

**What reconciles.** A narrow leading edge with a short fading tail, rather than a block. It does not
compete with the drawn quadrant because it is not the same kind of shape: the moving bright line
reads as the sweep, and the drawn quadrant reads as the sector it has lit. That is what a plan
position indicator actually looks like, and it is the only version of this that works without
touching the image. Rendered offline at 96, 56 and 40 pixels across five rotations to confirm it
before shipping.

**One correction found by that rendering.** The first gradient gave the bright core half a degree,
which is arithmetically honest and invisible: at the dock's eleven pixel radius, half a degree is a
tenth of a pixel, so it anti-aliased away and the logo simply looked static. The shipped core is ten
degrees, about two pixels at the smallest size. There is a note in the CSS not to narrow it back
without checking at 40 pixels rather than 96.

---

## Constraints

- **CSS only.** One `conic-gradient` and one `@keyframes`. No canvas, no library, no new file, no
  network request. Nothing was added to `assets/vendor/`.
- **No layout shift.** Verified by measuring the sign-in panel and the logo box with the overlays in
  the DOM and again with them detached: 698.3 px and 56 x 56 at 52.8 px from the top, both times,
  identical to the decimal.
- **No pointer capture.** `pointer-events: none`, and hit-tested: `document.elementFromPoint` at the
  centre of the logo returns the `IMG`, not the sweep.
- **The image is the fallback.** The sweep is a separate empty span. With every overlay stripped from
  the DOM, all four in-page images still render at their correct boxes and report
  `naturalWidth 1531`. If a browser cannot paint a conic gradient the span paints nothing and the
  logo is exactly as it was.
- **Reduced motion is respected**, and the resting position is deliberate. The sweep's start angle is
  the three o'clock radius, which is exactly where the artwork's own bright edge is drawn, so a
  reader who has asked for less motion sees the logo as the illustrator drew it rather than a sweep
  frozen at an arbitrary angle.
- **No user-facing strings were added**, so there is nothing to check for em dashes or module ids.
  The two new elements carry `aria-hidden="true"` and no text.

---

## Verification

Every check below was proven able to fail by injecting the fault it exists to catch, confirming the
fault actually applied, then restoring and confirming the baseline came back.

| Check | Fault injected | Went red | Baseline restored |
|---|---|---|---|
| Overlay present at all four in-page sites | one overlay removed from the DOM | yes | yes |
| Animation declared, infinite, on every site | `animation: none !important` | yes | yes |
| Overlay does not take the pointer | `pointer-events: auto !important` | yes | yes |
| Overlay has no layout influence | forced in-flow with a definite size | yes | yes |
| Reduced-motion rule present | the rule deleted from the CSSOM | yes | yes |

**One fault silently failed to apply, and that is worth recording.** The layout check first refused
to go red under `position: static !important`, which looked like a weak check. It was a weak *fault*:
the overlay is a `<span>`, so as a static inline box `width` and `height` do not apply to it and it
collapsed to zero, occupying no space and shifting nothing. The corrected fault adds
`display: block` and a definite size; the panel then grows from 698.3 to 738.3 px, exactly the 40 px
injected, and the check goes red. I asserted that the panel height actually changed before believing
the result. Without that assertion this would have been recorded as a check that cannot fail.

That failure mode also says something reassuring about the overlay: because it is a span, losing
`position: absolute` alone would not shift the layout either.

### Suites

- **Server: 28 suites, 1517 checks, 0 failures**, against a throwaway SQLite built by
  `alembic upgrade head`. Never pointed at production. Re-run after merging `origin/main` at
  `769ff39`, which landed the export workbook while this was in progress and moved the counts.
- **`tests_render.html` 49/49** and **`tests.html` 51/51**, in the browser. Neither exercises the
  logo, but `tests_render.html` loads `app.js`, which this change edits.
- No console errors on the page.

---

## Files changed

- `assets/css/radar.css` — the shared `.logo-mark` and `.logo-sweep` rules, the keyframes, the
  reduced-motion rule, and removal of the dock's separate sweep.
- `index.html` — the wrapper and overlay at the four in-page sites.
- `assets/js/app.js` — one class name on the dock emblem's existing span.

`logo.png` is unchanged.

## What I could not establish

- **That the sweep turns.** No compositing in this container, so no frame was ever painted and the
  animation clock never advanced. The declaration is verified; the motion is not.
- **How it looks in each of the three themes on a real screen.** The sweep's colour is fixed and does
  not vary by theme, and the artwork does not either, so I expect no interaction, but I could not
  look at it.
- **Whether the ten degree bright core is the right weight to Lin's eye.** It is a judgement about a
  logo, made from offline renders at the three real display sizes, and it is one number in one CSS
  rule if it wants changing.
