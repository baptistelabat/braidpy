# Braid Studio: braidpy on the web

Braid Studio is a web page where anyone can describe a braid — a braid word,
a kumihimo pattern, a disk braid, an Ashley sinnet, a horn gear braiding
machine — and see it laid and tightened in 3D, without installing anything.

It lives in `web/`. This page is its plan: what it does, how it is built and
why, and what comes next.

## What it does

The page has a form and a 3D view.

- **Made by** picks the source: a braid word; kumihimo's `S`/`R` moves; a
  braid from the mobidai catalogue; an Ashley solid sinnet; or a braiding
  machine.
- Each source asks for what it needs: the word and the number of strands; the
  pattern and how often to repeat it; which braid, and for how many cycles.
  The advanced section sets the yarn diameter and how hard the yarns are
  pulled (the tightening steps; 0 lays them with no tension).
- A disk braid or a sinnet can also be **your own**: choosing "Your own
  moves…" shows what the braid chosen before is made of — the slots its
  strands start in and its moves, or its spaces' counts and moves — ready to
  change, as text or by clicking on a drawing of the disk: a strand, then
  the slot it goes to (or a space, then the space a strand goes to).
- The braid is drawn as tubes, one colour per yarn, and can be turned, zoomed
  and spun. **Grow** replays it being made, by the clock of whatever made
  it: the oldest rows first, carried up as the newest form at the fell. An
  inset shows what made it, seen from above, at the same instant — the disk
  with its strands as spokes, the machine's gears and carriers — and a
  disk's braid turns with the disk, each strand at the fell nearest its
  carrier.
- Beside it, what is known of the braid: its strands, crossings and word (its
  ring word too, for a disk braid), the permutation it makes, what it closes
  up into (a knot, or a link of so many pieces), its Garside normal form and
  full twists, how close the yarns come.
- The address bar always describes the braid shown, so **Copy link** shares
  it. **Save…** keeps a picture, the yarns as an STL file for 3D printing or
  an OBJ model, or their points as JSON.
- The last few braids made are kept: going back to one is instant.

## How it is built

**Everything runs in the browser.** braidpy itself — the same code, tested by
the same tests — runs in a Web Worker through [Pyodide](https://pyodide.org),
CPython compiled to WebAssembly. The page draws what it computes with
[three.js](https://threejs.org). There is no server to run: the site is
static files, published with the documentation.

```
 page (app.js) ── spec ──▶ worker (worker.js) ── braidpy.web.build(spec)
     ▲                                                   │
     └──────────── strands as points, word, … ◀──────────┘
     three.js tubes
```

- `src/braidpy/web.py` is everything the page asks of braidpy: `catalogue()`,
  what can be made, and `build(spec)`, the braid a description makes. Both
  answer in plain data, lists and numbers, so the page needs nothing of
  Python's to draw.
- `web/worker.js` loads Pyodide, numpy and sympy from Pyodide's CDN, and
  braidpy and math_braid as wheels from the site. It then answers each
  description with the braid.
- `web/app.js` builds the form from the catalogue, sends descriptions to the
  worker, and draws the answer.
- `web/build.py` assembles the site in `web/site/`. It copies the page and
  three.js, and builds the wheels, math_braid's from its source package,
  since PyPI has no wheel of it.
- `web/smoke_test.py` serves the site, opens it in a headless browser and
  makes a braid of every kind there.
- `.github/workflows/braid_studio.yml` builds and smoke-tests the site on
  every pull request touching braidpy or the page. On `develop`, it publishes
  the site to `gh-pages` under `studio/`, beside the documentation.

### Why not a JavaScript port, or a Python server?

| | Pyodide (chosen) | Port to JavaScript | Python server |
|---|---|---|---|
| One source of truth | yes: braidpy, tested | no: two implementations to keep in step | yes |
| Runs without a server | yes, static files | yes | no: hosting, scaling, cost |
| First visit | ~15 MB to download, then cached | small | small |
| Speed | numpy in WebAssembly: 1–10 s a braid | could be faster | fast, but a round trip |
| Effort | small, done | large: laying, tightening, every source | moderate, plus operations |

A port would make the page lighter, but every algorithm — reading moves into
crossings, laying, tightening, the Garside form — would then exist twice and
drift apart. Pyodide keeps the page exactly as right as braidpy is, and every
improvement to braidpy reaches the page by itself. Should speed ever matter
more than that, the one hot loop worth porting is the tightening (see below).

### Keeping it light

Drawing libraries — plotly, matplotlib, imageio — are tens of megabytes in a
browser, and the page does not need them: it draws with three.js. braidpy
therefore imports them only when something is drawn with them
(`braidpy.utils.lazy_module`), and a test checks that building any braid
loads none of them. The page loads numpy and sympy, plus networkx for the
machines, and only when one is first chosen.

## Trying it locally

```sh
cd web && npm install && cd ..        # three.js, once
python web/build.py                  # writes web/site/
python -m http.server -d web/site    # then open http://localhost:8000
```

or `make studio` and `make studio-serve`. To use a Pyodide of your own rather than its CDN, add
`?pyodide=<url of its full/ directory>` to the address.

## What comes next

Done so far, beyond making and drawing a braid: watching it being made with
what made it seen from above, the braid turning with its disk; your own disk
braids and sinnets, typed or clicked; the braid's closure, normal form and
full twists; a cache of recent braids; STL, OBJ and JSON export.

1. **Which way up.** A disk's braid is drawn growing up from the fell, as
   braidpy draws every braid it lays; a real kumihimo hangs below its disk.
   The two are mirror images. Drawn hanging, the braid would be the real one
   — and the sign of the words braidpy gives disk braids is worth settling
   at the same time (see the sinnet and mobidai conventions).
2. **Your own machines.** Gears and carriers placed by clicking, as a
   disk's moves are now.
3. **More about the braid.** Its Alexander polynomial — once braidpy's is
   mended: it fails on negative crossings, and takes the determinant of the
   Burau matrix rather than of the identity less it — and its closure drawn
   as a knot or link.
4. **Speed.** Tightening is the slow step, and the Garside form for big
   braids (beyond 12 strands it is not computed here). A coarse braid first,
   refined after; and, if needed, that one loop ported to JavaScript or
   WebGPU.
5. **Printable.** Tubes closed at their ends, and merged where they touch,
   for an STL a slicer takes as it is.
6. **Offline.** As a progressive web app, it could work with no connection
   once visited.
