# Changelog

What changed in each release of braidpy.

## Unreleased

### New

- Whether a braid is Brunnian: pure, and trivial once any one of its
  strands is taken out, as the Borromean rings' braid (`Braid.is_brunnian`,
  with `Braid.without_strand`; it raised NotImplementedError). Braid
  Studio's card says so of a pure braid.
- A braid made by its carriers (`braidpy.carried`): a horn gear machine's
  carriers go round at the machine's real size, each pulling its yarn at a
  steady tension up through a forming ring into the braid taken off above,
  the yarns held where they cross by friction. Drawn near, and to scale
  beside the machine (`examples/demo_carried.py`).
- A triaxial braid among the machines: the tubular braid of 16 round an
  axial yarn up each of its eight gears, as a triaxial braider feeds them
  up its hollow horn gear spindles (`horn_gear.triaxial_braid_16`; J. H.
  van Ravenhorst's thesis on the references page). At every axial the
  carriers going round one way pass it on one side and those going the
  other way on the other, so it lies between the two sets. Braid Studio
  says how many cores a machine braids round, where it said "a core" of
  the soutache's two cords and now these eight.
- A kumihimo or mobidai braid can be made round a core in Braid Studio,
  down the disk's middle, of yarn or rigid, as a machine's core is.
- The marudai makes a braid round a core: up the braid's axis, of yarn or
  rigid, each move passing beside it (`braidpy.marudai`, `web/marudai.js`).
  A disk braid, a lace braid made from its card, or a lace machine's round
  its core, is made on the marudai with it.
- A tubular machine, or a lace machine of six gears or more, can braid
  round a core in Braid Studio, of yarn or rigid, down the hole its ring of
  gears encloses (`horn_gear.ring_core`); soutache can braid without its
  cords. **Core** replaces **Cores**, which said only how stiff a machine's
  own cores were: links made with it make the same braid.
- A lace machine's braid can be made on a marudai in Braid Studio: the
  braid grows at the fell as the card turns the gears, each gear's turn its
  two notches swapping bobbins. Worked out from the card alone
  (`making.lace.card_program`), without building the machine or loading
  what it needs.
- The multiband machines draw every carrier of a band in that band's colour,
  so the bands can be told apart in the braid they make together; a band
  shown alone keeps its colour (`BraidingMachine.carrier_colours`).
- A line of horn gears that braids three bands at once: the 10-15-10
  machine of the Atelier de Tressage (`braidpy.horn_gear.multiband`). Where
  two bands meet, a six-horn gear is split between them, three horns each, so
  each band turns its carriers back on a gear of its own and the bands never
  meet. Its 35 carriers run the whole machine, shown in Braid Studio whole
  or a band at a time, with the smallest such machine beside it: two plaits
  braided at once on three gears, the middle one split.
- Braid Studio's **Make it as…** makes the braid on a lace machine too: the
  card it shows is a link to your own lace machine, loaded with that card and
  its bobbins, at an address of its own. Bobbins can be named by their
  notch, `A-B`, as the card names them.
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

- The package says where braidpy lives: its repository, documentation,
  Braid Studio, changelog and issues (`project.urls`), for PyPI to show.
  Modules that began with a form (file name, author, date) say what they
  hold instead; `horn_gear.multiband` is in the API reference; and the
  documentation's one link to a section, the marudai round a core, leads
  there.
- Tightening warns when a braid is laid too coarsely for it: it looks for
  contact between samples only, so two yarns whose sideways steps between
  two levels add up to two diameters can cross there unseen, as the
  three-band machine's did. A step of a diameter or more is warned of
  (`take_off.SAFE_STEP`, `longest_step`), for the page's tightening too.
  Every machine is laid well inside it; a two-strand word settled by
  physics, and a lace braid made on a marudai round a core, are not.
- Carriers no longer jump where a line of gears bends. On the three-band
  machine, folded round, and on the 12- and 16-carrier tubular braiders, a
  gear's horns turned rigidly cannot meet both its contacts, so a carrier
  was drawn jumping, by up to a third of a gear, as it was handed on. The
  jump left yarns too long between samples for tightening to see one pass
  through another, and at the three-band machine's seams, where the bands
  pull apart, the yarns twisted together there slipped through each other,
  so the bands came apart into three. Such a gear's horns are now drawn
  spread unevenly, the one at a contact always on it
  (`horn_gear.layout.slot_angles`, `GearAngles`): carriers are handed on
  where they are, and the bands stay one braid when tightened. Which
  carrier crosses which is unchanged; machines whose horns met their
  contacts are drawn as before.
- The 10-15-10 machine is loaded as its drawing is: each eight-horn gear
  carries one carrier each way, as drawn, where both went the same way
  (`MULTIBAND_10_15_10_LOADING`: G3 and G5 carry on slots 2 and 5, G10 and
  G12 on 1 and 4). Every other gear was already as drawn. The braid it
  makes changes; how the bands join does not.
- Braid Studio stepped a big machine's braid, the three-band machine's,
  badly: the page drew the whole braid again at every frame, even when
  nothing moved, so it was slow to answer, and the handle, pressed a few
  times meanwhile, then turned on by itself. The view is drawn only while
  something changes, and a press the page could not answer in time is let
  go. The slider under the view goes a sub-step at a time, an eighth of a
  machine's step or a disk's move, the arrow keys a sub-step and with
  Shift a step, and says which step it is at.
- Braid Studio's machine handle, held part way through a step (▸), went
  back to the step's start to turn it whole when pressed on, ▸ or ▶: it
  now turns on from where it is held.
- A Braid Studio link could carry colours for strands its braid does not
  have: colours chosen on a braid of twenty strands stayed when one of
  sixteen was made after it, and its link listed all twenty. They are let go
  once the braid is made, and empty places after the last colour are not
  written.
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
- A braid's fingerprint took a minute when its home braid was hundreds of
  repeats of a long unit (the three-band machine: 210 repeats of 34515
  crossings). Its linking numbers are now summed from the unit once, the
  repeats at once (`linking.linking_matrix(braid, repeats)`), and the Burau
  matrix is built a column update per crossing: five seconds.

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
