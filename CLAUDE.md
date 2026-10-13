# braidpy: working notes for Claude

## Before writing anything, look for it

Most things braidpy needs already exist somewhere in it. Search first (by
name and by idea: `git grep`, the module docstrings), and extend what is
there rather than write a second one. Places that have been rewritten by
mistake before:

| Need | Already in |
|---|---|
| Read a braid word from text | `braidword.parse_word` |
| Permutation, purity, cycles, closing repeats | `pure_braid` |
| Ring words, turns, `solid_word` / `ring_moves` | `annulus_braid` |
| Lay a word as curves or points, read a word back | `parametric_strand` (`strand_paths`, `sample_strands`, `SampledStrand`), `symmetric_braid.braid_word` |
| Linking numbers, from a word or from yarns | `linking` |
| Colours, Plotly play/pause controls | `utils.PALETTE`, `utils.play_controls` |
| A catalogue of braids | `catalogue.Entry`, each catalogue's `CATALOGUE` |
| Defaults and limits for the web page | `web/_settings.py` |

## Rules

- **One implementation.** Do not copy code between modules, nor between
  Python and JavaScript. `make duplicates` checks both and runs in CI.
- **JavaScript only where the browser needs speed.** When a Python algorithm
  must also run in the page (as `web/tighten.js` does `take_off.tighten_yarns`),
  the Python is the reference and a test runs both and compares them
  (`tests/test_tighten_js.py`). JavaScript test cases run only what is
  JavaScript's: geometry going in and checks coming out are done in Python,
  with braidpy (`tests/test_rope.py`).
- **Documentation links, it does not restate.** If a method is described on
  one page, other pages link to it and say only what differs.
- **Data apart from code.** Defaults, limits, titles and catalogues are data
  (`web/_settings.py`, the `CATALOGUE`s), not literals inside functions.
- **Refactoring keeps results.** Check outputs are the same before and after
  (for `braidpy.web`, the same JSON for every build); say so in the PR, and
  say what changes when something does.
- **Commit only what you mean to.** `git add` named paths, never a whole
  directory: `web/site/` and `web/node_modules/` are build output.

## Before pushing

```sh
make lint && make typecheck && make test && make duplicates
```
