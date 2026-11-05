# Changelog

What changed in each release of braidpy.

## Unreleased

### New

- A line of horn gears that braids three bands at once: the 10-15-10
  machine of the Atelier de Tressage (`braidpy.horn_gear.multiband`). Where
  two bands meet, a six-horn gear is split between them, three horns each, so
  each band turns its carriers back on a gear of its own and the bands never
  meet. Its 35 carriers run the whole machine; each band can be shown on its
  own in Braid Studio.
- Four kumihimo disk braids shared by Richard Buenger: edo yatsu, naiki,
  hira-naiki and uneri-maru-genji (`braidpy.mobidai_catalog`).
- Braid Studio steps through a disk's or a sinnet's moves, as through a
  machine's: ⏮ ◀ ▶ ⏭ or the caret in the moves typed show the strands after
  any move, without undoing it. A move clicked goes in at the cursor.
- Whether two braids are the same braid however written, proven rather than
  measured: `braidpy.conjugacy.same_braid` decides conjugacy by the super
  summit set. It proves edo yatsu and ABOK #3070 different, and the flat
  braid of 6 and ABOK #3021.

### Fixed

- Braids were taken for the same braid when their Alexander polynomial
  vanished and the rest of their fingerprint agreed: edo yatsu with ABOK
  #3070, and the flat braid of 6 with ABOK #3021. The fingerprint now holds
  the characteristic polynomial of the braid's Burau matrix too
  (`properties.burau_polynomial_on_circle`), which tells them apart.
- A braid with a long home braid, read from another starting point, could
  seem another braid: the Alexander polynomial was taken from the Burau
  matrix raised to the repeats, whose entries reach 1e19 for ABOK #3057, and
  lost the digits it cancelled. It is now taken from the matrix's
  eigenvalues, as the Burau polynomial is.

## 0.3.0 — 2026-10-24

braidpy grows from braid words to the braids people make: on braiding and
lace machines, kumihimo disks, a marudai and Ashley's stand, laid and
settled in 3D, compared by their topology, and shown in Braid Studio, in the
browser.

### New

- **Braid Studio**, a web page where braidpy runs in the browser: describe a
  braid — a word, a kumihimo or mobidai pattern, an Ashley sinnet, a braiding
  or lace machine — and see it laid, tightened and made in 3D, with nothing
  installed. The braids it offers are made and settled with the site, and
  shown at once. A braid made on a disk can be saved for braid3dmin (B3D),
  bead for bead, its moves as braid3dmin lists them.
- **Braiding machines** (`braidpy.horn_gear`): horn gear (maypole) machines,
  flat, tubular and soutache, and the Jacquard lace machine driven by its
  punchcard; their tracks, collisions, threading and animation, and their
  handle turned by hand.
- **Kumihimo and mobidai disks**, animated from above, and **43 of Ashley's
  solid sinnets** (ABOK #2965–#3082), each worked on its stand, with its
  braid word and its mobidai pattern.
- **A braid made move by move on a marudai** (`braidpy.marudai`), each yarn
  carried over the others and drawn tight.
- **Ways of making a braid** (`braidpy.making`): from a braid word to how to make it — moves
  on a kumihimo disk, a Jacquard lace punchcard, a sinnet on Ashley's stand —
  each checked by reading the braid back off what it makes.
- **Comparing braids** (`braidpy.similarity`, `braidpy.topology_catalog`): a
  fingerprint that does not change however a braid is written, the braids
  most like one, and a catalogue of braids by topology with every way of
  making each.
- **The shape of a braid**: laid in 3D as it comes off whatever made it, and
  tightened; closed forms for the shapes that have one (a laid rope, a
  braided tube, the flat braid); yarns settled by their own physics
  (`braidpy.rope`, `braidpy.form`), in Python and in the page.
- **For AI assistants**: `braidpy.tools`, a few questions answered in plain
  data, and `braidpy-mcp`, an MCP server offering them (`pip install
  "braidpy[mcp]"`).
- Linking numbers, pure braids and their closures, full twists, the braid
  word read in any of its notations (`braidword.parse_word`).
- `braidpy.__version__`.

### Changed

These may need changes to code using 0.2.2.

- **Drawing is an extra**: matplotlib, plotly and imageio are installed with
  `pip install "braidpy[viz]"`; `pyqt6` and `tornado` are no longer
  required. braidpy alone installs in 100 MB rather than 489 MB, and a
  drawing library missing says what to install.
- **Python 3.10 to 3.15** are supported, and tested daily.
- The 2D braid diagram is drawn by braidpy itself, in its own colours.
- `GarsideCanonicalFactors.n_half_twist` counts half twists (it counted full
  ones).
- Handle reduction (`braidpy.handles_reduction`) has a new interface.
- `Braid ==` and `is_trivial()` are decided by handle reduction, math-braid's
  normal form only when it is slow: faster on most braids.
- Drawing libraries, sympy and math-braid are imported only when used.
- `braidpy.ordered_strands`, a stub nothing used, is removed.
- `double_flat3` makes ABOK 2971 by default; `parallel=True`, asking for
  ABOK 2972, raises `NotImplementedError`, as 2972 is not made yet.

### Fixed

- Comparing a braid with the trivial braid crashed; `is_trivial()` looked
  only at the word, so `σ₁σ₁⁻¹` was not trivial.
- Parametric strands stopped short of their end.
- The documentation's 3D example passed a braid where an amplitude was
  expected (issue #8).
- Sinnets of more than 30 strands, made on a marudai, grew hundreds of yarn
  diameters long instead of a few.
- `double_flat3(parallel=True)` gave ABOK 2971, not the 2972 it asked for.
- `braidpy-mcp` without the `mcp` extra ended in a traceback; it now says
  what to install.

### Documentation

- In three parts: a user manual, a theory manual and a developer guide, with
  an API reference covering every module.

## 0.2.2

The release before these notes were kept: braids as words in Artin's
generators, their operations and properties, handle reduction, and their
drawing in the console, in 2D and in 3D.
