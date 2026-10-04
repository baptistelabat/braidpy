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
- The braid is drawn as tubes, one colour per yarn, and can be turned, zoomed
  and spun. **Grow** replays it being made: the oldest rows first, carried up
  as the newest form at the fell.
- Beside it, what is known of the braid: its strands, crossings and word (its
  ring word too, for a disk braid), the permutation it makes, how close the
  yarns come.
- The address bar always describes the braid shown, so **Copy link** shares
  it; **Save PNG** keeps a picture.

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

1. **Watch it being made.** The disk seen from above — kumihimo, mobidai,
   sinnet, machine — animated beside the braid, in step with it, as the
   Plotly pages already do; braidpy already computes the trajectories.
2. **Your own patterns.** Moves typed in, for a mobidai (slot to slot) or a
   sinnet (counts per space and moves), as easily as a word is now; then a
   disk to click on.
3. **More about the braid.** Its Garside normal form and full twists, its
   Alexander polynomial, its closure as a knot or link — all computed by
   braidpy already.
4. **Speed.** Tightening is the slow step. Cache what was made; compute a
   coarse braid first and refine it; and, if needed, port that one loop to
   JavaScript or WebGPU.
5. **Out of the browser.** Export the yarns as OBJ or STL for 3D printing, or
   as the points themselves.
6. **Offline.** As a progressive web app, it could work with no connection
   once visited.
