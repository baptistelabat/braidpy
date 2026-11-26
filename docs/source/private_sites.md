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
2. **Catalogues from outside** — done. The machines, disk braids and
   sinnets the studio offers come from braidpy's catalogues
   (`machine_catalog`, `mobidai_catalog`, `solid_sinnets_catalog`), each
   extended with what installed packages add to it
   ({func}`~braidpy.catalogue.extended`): a package of the site's own names,
   by [entry points](https://packaging.python.org/en/latest/specifications/entry-points/)
   in the group `braidpy.catalogues`, a dict of
   {class}`~braidpy.catalogue.Entry` to add to a catalogue, by its module
   name. The profile's `packages` name the site's packages, and the build
   runs braidpy with them, so that the page, the braids made with the site
   and the catalogue of braids by topology all have their braids, and puts
   each package's wheel beside braidpy's (`wheels/manifest.json`), for
   Pyodide to install it too. braidpy gains a way in, and keeps no
   customer's name (see below).
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
| `language` | `en` | The language its pages open in, as `web/locales/` names it (see below) |
| `packages` | none | The site's own packages, folders from the profile's: their braids join braidpy's catalogues (see below) |
| `indexed` | `true` | `false` asks search engines to leave the site out |

A site naming nothing of braidpy:

```toml
name = "Braid Designer"
by = ""
by_url = ""
documentation = ""
documentation_title = ""
sponsor = ""
language = "fr"
packages = []
indexed = false
```

In the pages, `{{key}}` is replaced by its value, and
`<!-- if key -->…<!-- end if -->` (or `if not key`) kept only when the key is
set; `tests/test_site_build.py` checks that such a site's pages name neither
braidpy, nor its repository, nor its sponsoring.

## Braids of the site's own

A site's package is an ordinary Python package beside its profile:

```
designer/
├── pyproject.toml
├── locales/fr.toml           the words of its braids, in French
└── designer_braids/__init__.py
```

```toml
# pyproject.toml
[project]
name = "designer-braids"
version = "0.1"

[project.entry-points."braidpy.catalogues"]
machine_catalog = "designer_braids:MACHINES"
```

```python
# designer_braids/__init__.py
from braidpy.catalogue import Entry
from braidpy.horn_gear.described import machine_from_graph

MACHINES = {
    "my_matrix": Entry("Matrix of gears", lambda: machine_from_graph("A0-A1 …")),
}
```

with `packages = ["designer"]` in the profile. A lace machine is added the
same way, under the name `lace_machines`, as a dict of `Entry` making a
`braidpy.machine_catalog.LaceRing`: its gears, its card (a card typed as
Braid Studio takes it is read by `braidpy.making.lace.read_card`) and the
notches threaded. Its machines are listed after
braidpy's, as if braidpy had them: shown, made, premade, catalogued by
topology. A name braidpy has already is refused. The package imports from
braidpy what its braids need, but not the catalogue it adds to, which
reads it as it loads. The words of its braids, in another language, are
in its own `locales/<code>.toml`, merged with braidpy's when the page is
built: braidpy's catalogue of words names none of them.

## In another language

braidpy writes English, in Python and in the page alike. The page puts
each text into the language chosen as it shows it (`web/i18n.js`), from a
catalogue of the texts by their English: `web/locales/fr.toml` for
French, every catalogue there written into the page by `build.py` as
`locale.js`. Neither braidpy's Python nor its JavaScript changes: an
English sentence is the key to its translation, wherever it is made.

A site opens in its profile's language (`language = "fr"`). A menu at the
top of each page offers every language the site has, each by its own name
(a catalogue's translation of "English"), and switches the page there and
then: each text keeps its English, and is put into the new language from
it, so nothing is made again — the braid on show stays as it is. The
choice is kept for the next visit, in the browser, and a link can give one
as `?lang=en` or `?lang=fr`.

```toml
"Strands" = "Brins"
"Kongo gumi" = "Kongo gumi"
# {} any words, themselves looked up; {#} a number.
"{}, {#} cycles" = "{}, {} cycles"
# {1}, {2}… where the words come in another order.
"ABOK #{#}, {#}-strand {}" = "ABOK n° {1}, tresse {3} à {2} brins"
```

A text is looked up whole, then against the patterns, those ending in
words of their own first, and the first whose words all translate is
taken. What the catalogue lacks stays in English, and is listed for
whoever completes it: in the browser's console,
`[...untranslated].join("\n")`. What is read back from the page is read
in English (`englishText`), and what is drawn rather than written is drawn
again when the language changes (the `language` event). An element marked `translate="no"` keeps
its words, as a book's title among a braid's links. The page is hidden
until its first pass is done, so nothing is seen in English first.

`tests/test_i18n_js.py` runs the translator in Node: every text of the
pages and every braid the studio offers must be in the French catalogue,
and every translation must use the words its English leaves open. A
sentence added to braidpy is added to the catalogue too, or stays in
English on a French site until it is.

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
