# Vendored assets — sources, licences and sizes

Everything the platform loads at runtime is served from this directory. **Nothing loads from a
CDN.** The operational audience works on corporate networks that block them, and the repository
has been bitten by dependency availability twice. Anything added here must record its source and
licence below.

| File | Size | Source | Licence |
|---|---|---|---|
| `globe.gl.min.js` | 1,443 KB | [globe.gl](https://github.com/vasturiano/globe.gl) (bundles three.js) | MIT |
| `maplibre-gl.min.js` | 773 KB | [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js) | BSD-3-Clause |
| `maplibre-gl.min.css` | 64 KB | MapLibre GL JS | BSD-3-Clause |
| `pdf.min.js` | 313 KB | [PDF.js](https://github.com/mozilla/pdf.js) | Apache-2.0 |
| `pdf.worker.min.js` | 1,062 KB | PDF.js | Apache-2.0 |
| `xlsx.full.min.js` | 861 KB | [SheetJS](https://github.com/SheetJS/sheetjs) | Apache-2.0 |
| `earth-blue-marble-clouds.jpg` | 529 KB | NASA Blue Marble Next Generation — composited, see below | **Public domain** |
| `ne_110m_admin_0_countries.geojson` | 240 KB | [Natural Earth](https://www.naturalearthdata.com/) 1:110m Admin 0 Countries | **Public domain** |
| `fonts.css` + `fonts/*.woff2` (18 files) | 679 KB | Google Fonts — Archivo, Inter, IBM Plex Mono | **SIL Open Font License 1.1** |

Total: **5.9 MB**.

## The fonts, and why they are here

They used to load from `fonts.googleapis.com`, which is the same corporate-network argument that
got MapLibre, globe.gl, PDF.js and SheetJS vendored: on a blocked network the platform silently
fell back to system fonts and stopped looking like itself.

`fonts.css` was generated from the Google Fonts `css2` response for the exact families and weights
`index.html` already asked for — Archivo 500/700/800, Inter 400/500/600, IBM Plex Mono 400/500/600
— with the URLs rewritten to `fonts/`. All three families are SIL OFL 1.1.

**Latin and latin-ext only.** Google serves seven subsets (adding Cyrillic, Cyrillic-ext, Greek,
Greek-ext and Vietnamese), which would have been 45 files. The platform's audience is a US
institution and US federal and commercial projects, and latin-ext already covers European
diacritics, so the other five subsets would be dead weight. 18 files, 672 KB on disk.

The `unicode-range` declarations are preserved, so a browser downloads only the faces it needs:
measured on the sign-in page, **4 files / 142 KB** actually transfer, not all 18.

## Still off-origin, and why

Vendoring removed Google Fonts entirely. Two dependencies remain and neither can be vendored:

- **`accounts.google.com`** — required for Google sign-in. **Verified** that with the Google
  global absent the username and password form still renders, stays enabled and authenticates, so
  a blocked network does not lock anyone out.
- **`tiles.openfreemap.org`** — the tile source for the MapLibre map, which is the globe's
  fallback when WebGL is unavailable. Tiles are a live service and cannot be vendored. **Verified**
  that the failure path degrades to a muted panel reading "Map tiles unavailable: check
  connection" with the project list still present, not a blank panel. A 9-second watchdog in
  `app.js` covers the case where the style never loads.

## `earth-blue-marble-clouds.jpg` — how it was made

2048×1024 equirectangular, the 2K version. At the globe's rendered size — roughly 1,200 px — 2K
is visually indistinguishable from 8K and saves several megabytes, so the larger sets were not
considered further.

It is a composite of two NASA Visible Earth images, both public domain, screen-blended (clouds are
white on black, so screen is the physically sensible combination and needs no mask):

| Layer | Source |
|---|---|
| Terrain | `land_shallow_topo_2048.jpg` — NASA Visible Earth, image record **57752**, "Blue Marble: Land Surface, Shallow Water, and Shaded Topography" — 233 KB |
| Clouds | `cloud_combined_2048.jpg` — NASA Visible Earth, image record **57747** — 809 KB |

    https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/land_shallow_topo_2048.jpg
    https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57747/cloud_combined_2048.jpg

**Taken from NASA directly rather than from a JavaScript package.** The equivalent texture bundled
with `three-globe` is 1,427 KB for the same 2048×1024 image; NASA's own files composite to 529 KB
and carry an unambiguous provenance, which matters more here than the convenience.

**Clouds are baked in rather than rendered as a second sphere.** A separate cloud layer would cost
another 809 KB, a second sphere's geometry and an extra draw call, for a still image whose clouds
never move. Baking gives one texture, one sphere, no extra draw call.

The composite is reproducible: screen-blend the two files above, save at JPEG quality 82,
progressive. No other adjustment was applied — in particular the texture is **not** dimmed or
desaturated, for the reason recorded in `globe.js`: dimming does not solve marker legibility, it
only changes which status fails.

## `ne_110m_admin_0_countries.geojson` — how it was reduced

Natural Earth is public domain ("no permission needed"). The file is the standard 1:110m Admin 0
set as redistributed with globe.gl's examples, **stripped to geometry only**: every `properties`
object was discarded, since the abstract globe draws country outlines as dots and never reads a
country name. 177 features, 476 KB → 240 KB, with no change to what is rendered.

## Reference images are not assets

The stock photograph shown to the researcher carries a watermark and is **not** used anywhere.
Everything rendered comes from data or from the openly licensed sources recorded above.
