# Developer guide

How braidpy is worked on: setting it up, the rules it is written by, its
tests, its documentation and its releases. Braid Studio, the web page, has a
page of its own: [Braid Studio's internals](braid_studio_internals.md).

```{toctree}
:maxdepth: 1

braid_studio_internals.md
```

## Setting up

From a clone of the repository (on the `develop` branch), with
[uv](https://docs.astral.sh/uv/), the project's package manager:

```sh
make install-uv            # uv itself, if missing
uv sync --all-extras --dev # braidpy, its extras and the tools to work on it
pre-commit install         # format and lint each commit
make help                  # every target, with what it does
```

The project's Python is in `.python-version`; every Python braidpy supports
is tested daily (see below).

## Where things are

- `src/braidpy/` — the library. A module per idea; each module's docstring
  says what it is for, and {doc}`reference` lists them by area.
- `web/` — Braid Studio: the page, its workers, and `build.py`, which makes
  the site.
- `tests/` — pytest tests; `tests/js/` runs the page's JavaScript in Node for
  them.
- `docs/source/` — these pages.
- `gen_docs_figures.py`, `gen_demos.py`, `gen_braid_geometry_demo.py` — the
  documentation's figures and the demo pages, drawn from braidpy itself.

## How braidpy is written

These are the rules braidpy is worked on by, for people and for Claude
alike; they are kept in `CLAUDE.md`, at the root of the repository.

```{include} ../../CLAUDE.md
:start-line: 1
:heading-offset: 1
```

Code and comments are in English, with Google-style docstrings and type
hints throughout.

## Tests and CI

- `make test` runs the quick tests, in parallel: every test but those marked
  `@pytest.mark.slow`, in a couple of minutes. CI runs them on every push.
- `make test-all` runs every test, as CI does daily on every Python
  supported, and on demand (`workflow_dispatch`).
- `make test-changed` runs only the tests touching code changed since they
  last ran (pytest-testmon).
- `make typecheck`, `make lint` and `make duplicates` check types, style and
  code copied rather than shared, in Python and JavaScript.
- `.github/workflows/braid_studio.yml` builds Braid Studio and makes a braid
  of every kind in a browser on every pull request touching braidpy or the
  page; on `develop` it publishes the site.

## Documentation

`make docs` builds these pages in `docs/build/html`, with Sphinx and MyST.
They are in three parts — the user manual, the theory manual and this
guide — and each page links to others rather than repeat them. The figures
are drawn by `gen_docs_figures.py` from braidpy's own functions: change one,
draw them again. `make doc-deploy` publishes the pages to GitHub Pages, under
the branch's name, or under the release's tag from `main`.

## Releasing

Releases are made by hand, from `main`:

1. Merge `develop` into `main`.
2. Set the version in `pyproject.toml`, and say what changed in the release's
   notes.
3. Tag the release with its version (`git tag 0.3.0`), as the earlier ones
   are, and push the tag.
4. Build and publish the package: `uv build`, then `uv publish` with a PyPI
   token.
5. Publish its documentation: `make doc-deploy`.
