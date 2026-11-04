# Braid Studio's internals

How [Braid Studio](braid_studio.md) is built: braidpy in the browser, the
page's modules and workers, the site and how it is published.

## How it is built

**Everything runs in the browser.** braidpy itself — the same code, tested by
the same tests — runs in a Web Worker through [Pyodide](https://pyodide.org),
CPython compiled to WebAssembly. The page draws what it computes with
[three.js](https://threejs.org). There is no server to run: the site is
static files, published with the documentation.

```
 page (app.js) ── spec ──▶ worker (worker.js) ── braidpy.web.build(spec)
     ▲                                                   │
     │      ◀──── the braid as laid, as points ──────────┘
     │                          │
     │                          ▼
     └── as it settles ── settle worker (settle.js): tighten.js, rope.js,
     three.js tubes                     form.js or marudai.js
```

- `braidpy.web` is everything the page asks of braidpy: `catalogue()`,
  what can be made, and `build(spec)`, the braid a description makes. Both
  answer in plain data, lists and numbers, so the page needs nothing of
  Python's to draw. It is a module per source — `disks`, `words`,
  `machines` — beside what they share: reading descriptions (`_spec`), the
  result and its timeline (`_result`), and what is known of a braid
  (`_info`).
- `web/worker.js` loads Pyodide and numpy from Pyodide's CDN, and braidpy
  and math_braid as wheels from the site. It then answers each description:
  braidpy lays the yarns, the page shows them at once, and the settle
  worker, `web/settle.js`, settles them: sideways (`web/tighten.js`), on a
  marudai (`web/marudai.js`), or by physics (`web/rope.js`, `web/form.js`).
- `web/tighten.js` is `braidpy.take_off.tighten_yarns`, step for step, in
  JavaScript. Tightening is the one slow part of making a braid: its inner
  loop runs over a hundred thousand pairs of samples hundreds of times, and
  as numpy calls in WebAssembly each pass pays a price that compiled
  JavaScript does not. It is some 20 times faster there. braidpy stays the
  reference: a test tightens the same braid both ways, and they agree to
  the last digits for the first tens of steps, and come out as tight and as
  clear as each other after hundreds.
- The page is in modules, `web/app.js` loading them: the form (`fields.js`,
  with `diagram.js`, `machine.js` and `editor.js` for drawing a word,
  loading a machine and editing a disk's moves), the braid asked for in the
  address (`spec.js`), the workers (`workers.js`), the braid's own defaults
  (`defaults.js`), the 3D view (`scene.js`) and its insets (`insets.js`), the
  info card (`info.js`) and the view's controls (`controls.js`).
- `web/build.py` assembles the site in `web/site/`. It copies the page, each
  of its files naming the others with the page's version, so a browser never
  mixes old files with new ones, and three.js; builds the wheels, math_braid's from its source package,
  since PyPI has no wheel of it; and writes `catalogue.json`, what the page
  can make, and `topologies.json`, the catalogue of braids by topology, made
  once here rather than in every browser.
- `web/smoke_test.py` serves the site, opens it in a headless browser and
  makes a braid of every kind there.
- `.github/workflows/braid_studio.yml` builds and smoke-tests the site on
  every pull request touching braidpy or the page. On `develop`, it publishes
  the site to `gh-pages` under `studio/`, beside the documentation; on the
  branch it lists beside `develop`, under `studio-beta/`.

### Why not a JavaScript port, or a Python server?

| | Pyodide (chosen) | Port to JavaScript | Python server |
|---|---|---|---|
| One source of truth | yes: braidpy, tested | no: two implementations to keep in step | yes |
| Runs without a server | yes, static files | yes | no: hosting, scaling, cost |
| First visit | ~15 MB to download, then cached | small | small |
| Speed | ~1 s a braid, tightening in JavaScript | as fast | fast, but a round trip |
| Effort | small, done | large: laying, tightening, every source | moderate, plus operations |

A port would make the page lighter, but every algorithm — reading moves into
crossings, laying, tightening, the Garside form — would then exist twice and
drift apart. Pyodide keeps the page exactly as right as braidpy is, and every
improvement to braidpy reaches the page by itself. The one exception is the
tightening, the hot loop, ported to JavaScript and tested against braidpy.

### Keeping it light

Drawing libraries — plotly, matplotlib, imageio — are tens of megabytes in a
browser, and the page does not need them: it draws with three.js. braidpy
therefore imports them only when something is drawn with them
(`braidpy.utils.lazy_module`), and so with sympy and math_braid, seconds to
import in a browser and needed only for Burau matrices and comparing braids;
a test checks that building any braid loads none of them. The page loads
numpy, plus networkx for the machines when one is first chosen.

A first visit still downloads some 9 MB, compressed: Python itself (3 MB),
its standard library (2 MB), numpy (3 MB), braidpy and three.js. The
browser keeps them — Pyodide's CDN lets it for a year — so a later visit
starts from its cache, and shows a braid in some three seconds, most of it
Python starting. So that the downloads overlap rather than follow one
another, braidpy's worker is started by the page's first lines, before
three.js and the page's own modules load, and it fetches numpy, braidpy and
the catalogue by topology while Python starts. The form does not wait for
Python at all: what the page can make — every source, its braids and
defaults — is written with the site (`catalogue.json`), so the menu and
fields are there at once, and a braid chosen before Python is ready is the
one made when it is.


Every braid the page offers as it comes — each catalogued braid, each braid
word example — is also made once, when the site is built
({func}`~braidpy.web.premade`), and kept with it, laid as braidpy lays it for
the page to tighten. Chosen as it comes, such a braid is shown at once, before
Python has started, and its kin and other ways follow when Python is ready;
changed in any way, it is made in the page. That spares a visitor what the
biggest braids cost to lay — a sinnet of 36 strands took a minute natively,
many in the browser. Each is settled with the site too, by the page's own
settling run in Node (`web/settle_node.js`): on a marudai if it is made move
by move, sideways if not, as the page would settle it. Chosen as it comes, it
is shown settled at once, rather than after the minutes its tightening takes
in the browser; a twist or another settling asked for is done in the page.
Settled braids are kept in `web/.settled`, filed under a hash of the settling
code and of the braid laid, so a build settles only what changed; without
Node, braids are kept laid only. `python web/build.py --no-premade` leaves
them all out, to try the page sooner.

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

1. **Your own machines.** Gears and carriers placed by clicking, as a
   disk's moves are now.
2. **More about the braid.** Its Alexander polynomial — once braidpy's is
   mended: it fails on negative crossings, and takes the determinant of the
   Burau matrix rather than of the identity less it — and its closure drawn
   as a knot or link.
3. **Speed for big braids.** With the tightening in JavaScript, an 8-strand
   braid takes well under a second; a 22-strand sinnet still takes several,
   and its time grows with the strands squared. That is where the GPU
   earns its keep: WebGPU compute shaders running the contact pushes over
   every pair at once, several rounds per dispatch so the page is not
   waiting on each, with the JavaScript kept for browsers without WebGPU.
   The Garside form for big braids (beyond 12 strands it is not computed
   here) is the other slow step.
4. **Printable.** Tubes closed at their ends, and merged where they touch,
   for an STL a slicer takes as it is.
5. **Offline.** As a progressive web app, it could work with no connection
   once visited.
