# A site of your own, built from braidpy

How to run a second Braid Studio, under another name, showing braids and
machines that are not public, while every change made to braidpy reaches it.
This page is a proposal: the first step is done (the profile), the others are
to come.

## The idea: one engine, thin sites

braidpy and its Braid Studio stay public, here, and stay the only place the
engine, the pages and the build are changed. A private site is not a fork
but a small private repository that **uses** braidpy and adds only what is
its own:

```
braid-designer/              private
├── braidpy/                 this repository, a git submodule pinned to a commit
├── profile.toml             what the site calls itself, whom it credits
├── acme_braids/             a Python package: the customer's catalogues
├── pyproject.toml           acme_braids, with braidpy as a dependency
└── .github/workflows/site.yml
```

and builds the site with braidpy's own build:

```sh
python braidpy/web/build.py --profile profile.toml --out site
```

Taking braidpy's latest is moving the submodule to a newer commit (Dependabot
does it, as a pull request in the private repository, with its
`gitsubmodule` ecosystem). Nothing of braidpy is copied, so there is nothing
to merge: a fork, kept apart for long, would turn each update into conflicts
in the pages and the build, the files both sides change most.

## What makes it work

1. **The profile** — done. What the site calls itself, whom it credits and
   where it links are data (`web/profile.toml`), not words in the pages:
   `build.py --profile` fills the pages with another (see below).
2. **Catalogues from outside** — to come. The machines, disk braids, sinnets
   and words the studio offers come from braidpy's catalogues
   (`machine_catalog`, `mobidai_catalog`, `solid_sinnets_catalog`, the
   words' examples) through `braidpy.web.catalogue()`. A package of the
   site's own would add to them by
   [entry points](https://packaging.python.org/en/latest/specifications/entry-points/),
   a group `braidpy.catalogues` naming its `CATALOGUE`s of
   {class}`~braidpy.catalogue.Entry`, read by `braidpy.web` and by
   {mod}`braidpy.topology_catalog` beside their own. The build would put the
   package's wheel beside braidpy's (`wheels/manifest.json`), for Pyodide to
   install it too. braidpy gains a way in, and keeps no customer's name.
3. **A build per customer** — to come. A customer's braids are seen by
   whoever opens the site (see below), so each customer has a build of their
   own: the profile says which catalogues it carries, and each build goes to
   its own address.
4. **Pages leaner of their source** — optional. The pages ship as written,
   comments and all; minified, they would say less of where they come from.

## The profile

Every key is given, by every profile: a key added to braidpy's profile makes
another site's build stop until it decides that key too, rather than take
braidpy's value unseen.

| Key | braidpy's | What it is; empty to leave it out |
|---|---|---|
| `name` | Braid Studio | The site's name, in its titles and headings |
| `by`, `by_url` | braidpy, its repository | What computes it, credited in titles and text, and its link |
| `documentation`, `documentation_title` | `../`, braidpy's documentation | The documentation linked from the front page |
| `sponsor` | GitHub Sponsors | The studio's sponsor button |
| `indexed` | `true` | `false` asks search engines to leave the site out |

A site naming nothing of braidpy:

```toml
name = "Braid Designer"
by = ""
by_url = ""
documentation = ""
documentation_title = ""
sponsor = ""
indexed = false
```

In the pages, `{{key}}` is replaced by its value, and
`<!-- if key -->…<!-- end if -->` (or `if not key`) kept only when the key is
set; `tests/test_site_build.py` checks that such a site's pages name neither
braidpy, nor its repository, nor its sponsoring.

## What it hides, and what it cannot

**From search engines**: with `indexed = false`, every page asks not to be
indexed, and the site carries a `robots.txt` turning crawlers away (read only
at a host's root: serve the site at one). Search engines find sites through
links, too: link the private site from nowhere public, and give it an address
of its own, not one under braidpy's (a `github.io` address names its owner).

**The source, from a visitor**: not wholly. The site computes in the
browser, so the browser is sent braidpy itself, as a wheel of Python
modules, each beginning with its licence. Anyone opening the browser's tools
sees its files called `braidpy-….whl`, and can unpack them. The profile
takes braidpy's name off what the site shows; it cannot take it off what the
site sends. Only a site computing on a server of its own, sending pictures
and not the engine, would keep it all back, at the cost of a server and of
the page's speed.

**A customer's braids, from others**: whatever a build carries, whoever opens
it can read, so it carries one customer's braids (step 3), and sits behind a
login: a hosting service's access control (Cloudflare Access, Netlify's
password protection), or a server of one's own. GitHub Pages publishes a
private repository's site publicly, except on GitHub Enterprise Cloud.

## Licence

braidpy is under the Mozilla Public License 2.0, whose copyleft goes file by
file: files of the private site's own, its profile and its catalogues, may
stay closed. braidpy's own files, sent to the browser, stay under the MPL and
keep their notices, and a change to one of them must be open to those who
receive the site: one more reason to make every change to braidpy here,
upstream. (The author of a file may license it otherwise as well; files
others contributed stay under the MPL. This is not legal advice.)
