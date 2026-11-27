# Developer guide

How braidpy is worked on: setting it up, the rules it is written by, its
tests, its documentation and its releases. Braid Studio, the web page, has a
page of its own: [Braid Studio's internals](braid_studio_internals.md).

```{toctree}
:maxdepth: 1

braid_studio_internals.md
private_sites.md
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
is tested daily (see below). It is 3.12, a version everything installs on
without building from source; CI runs the quick tests on the newest Python
supported.

## Where things are

- `src/braidpy/` — the library. A module per idea; each module's docstring
  says what it is for, and {doc}`reference` lists them by area.
- `web/` — Braid Studio: the page, its workers, and `build.py`, which makes
  the site.
- `tests/` — pytest tests; `tests/js/` runs the page's JavaScript in Node for
  them.
- `docs/source/` — these pages.
- `examples/` — short scripts using braidpy, and the console tour `make
  demo` runs.
- `scripts/` — the documentation's figures (`gen_docs_figures.py`) and the
  demo pages (`gen_demos.py`, `gen_braid_geometry_demo.py`), each run from
  the repository's root.

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
are drawn by `scripts/gen_docs_figures.py` from braidpy's own functions: change one,
draw them again. `make doc-deploy` publishes the pages to GitHub Pages, under
the branch's name, or under the release's tag from `main`.

## Releasing

A release needs `uv` (`uv sync` installs the documentation's Sphinx with the
`dev` group) and Node's `npx`, which fetches `gh-pages-multi` for the
documentation. Its steps, each by its own command, so that one failing
stops the rest:

1. **On `develop`, a release PR** sets the version in `pyproject.toml`,
   `server.json` (twice) and `uv.lock` (`uv lock`), and turns `CHANGELOG.md`'s
   "Unreleased" into the version and its date.
2. **Merge `develop` into `main`** by a pull request from `develop`, merged
   with a merge commit, not squashed, so that `main` keeps `develop`'s
   history.
3. **`make release`**, from `main` (`scripts/release.sh`). It checks
   everything before it changes anything, and stops at the first that
   fails, saying what to do:
   - that this is `main`, with nothing uncommitted;
   - that `main` fast-forwards to `origin/main`;
   - that `server.json` and `CHANGELOG.md` agree with `pyproject.toml`'s
     version;
   - that no tag of that version exists, here or on GitHub.

   Then it tags `main` with the version and pushes the tag. The release
   workflow (`release.yml`) builds the package and publishes it on PyPI,
   refusing a tag that is not `pyproject.toml`'s version.
4. **`make doc-deploy`**, from `main`, publishes the documentation under the
   release's tag.

If a tag went onto the wrong commit, nothing was published: the workflow
refused it. Take it away, here and on GitHub, and run `make release` again:

```sh
git tag -d 0.4.0
git push origin :refs/tags/0.4.0
```

A release is cut every two or three weeks while the API still moves: each
break costs less made sooner, and `CHANGELOG.md` is what the people using
braidpy read to follow it.
