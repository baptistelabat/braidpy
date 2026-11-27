# Changelog

What changed in each release of braidpy.

## 0.4.0 — 2026-11-27

braidpy tells braids apart by what they are, and makes them more ways.
Four kinds of "the same braid" — the same word, the same braid, the same
pattern repeated, the same knot or link — each with its own `==`; normal
forms of its own, Artin's and the band generators', so math-braid is no
longer needed; whether a braid is periodic, reducible or pseudo-Anosov.
Horn gear machines are written as their graphs, with split gears, cores and
axials anywhere, sized for their bobbins; a tube is made as a tube on a lace
machine; disk moves are made in band letters where that is quicker;
Ashley's sinnets come from the shape they take, and 37 more of his plat
sinnets join the catalogue. Braid Studio speaks French, makes braids round
a core, and steps through a disk's or a sinnet's moves. braidpy's names now
take American spelling (`color`, `center`, `catalog`), the old ones still
answering, with a warning.

### New

- 37 more of Ashley's plat sinnets as braid words (`braid_catalog.ASHLEY_PLATS`,
  #2976–#3019): French, flat, twill, duplex and doubled-edge sinnets led to
  the centre, and square, half-round, ellipse and round sinnets by the square
  sinnet's method, each written as the book gives its leads ("u3 o1", under
  three, over one) and made by `AshleyPlat`. What the book says of them holds:
  #3018 is #3001, #2989 divided equally is #3003 turned end for end, and #2999,
  #2965, #2967 and #2968 are the sinnets already catalogued.
- Which of periodic, reducible or pseudo-Anosov a braid is, on Braid
  Studio's card and in `tools.describe_braid` (`nielsen_thurston`): said
  of braids of few strands and crossings, the super summit set looked
  through only so far — past that, the card says it cannot tell.
- Whether a braid is reducible (`Braid.is_reducible`): some of its strands
  gathered into groups, fewer groups than strands, each running inside one
  tube, the tubes themselves free to braid — a round curve round consecutive
  strands, two of them at least, all but two at most, brought back to itself.
  Asked of the super summit set `conjugacy` computes, a reducible braid
  having a conjugate there that keeps a round curve (Benardete, Gutiérrez
  and Nitecki 1993; Calvez 2014, theorem 10).  With `Braid.is_periodic`,
  this says which of periodic, reducible or pseudo-Anosov a braid is.
- A machine's braid as a ring word round an axis
  (`braidpy.horn_gear.word.ring_word`): an axial, or any spot one could be
  fed at, the core the machine braids round if not said (`default_axis`).
  The turns are kept, so with the core kept as a strand
  (`annulus_braid.cored_word`) it is the braid the machine makes round a
  yarn fed there: a tube is not a flat braid curled up. `shortened()`
  shortens it, the relations read round the ring
  (`shortening.shortened_ring`, `annulus_braid.turns_last`).
- A tube made as a tube on a lace machine (`making.lace.ring_card`): a
  ring word's strands go round across the seam, a pass need not bring
  them home, and the card's braid round the core is the word's. A
  machine's tube is the fewest steps that repeat (`horn_gear.word.ring_unit`):
  2 of the 16-carrier tubular machine's 16. Braid Studio's **Make it as…**
  makes a braid made round a core so — a ring machine's, a ring word's —
  in far fewer steps (that machine: 5 a pass instead of 34), round a core
  of yarn. `RingProgram.ring_word` reads a program round its ring.
- Four kinds of "the same braid", each with its own `==` and hash
  (`braidpy.braid_word`, `braid_pattern`, `closed_braid`): `BraidWord`
  (`braid.word()`), the same crossings;
  `Braid`, the same braid; `BraidPattern` (`braid.pattern()`), the same
  braid made over and over, proven by conjugacy where it can be; and
  `ClosedBraid` (`braid.closed()`), the same knot or link, by its loops,
  linking numbers and Alexander polynomial, however many strands.
  `conjugacy.same_braid` is now `same_pattern`, which is what it tells;
  the old name is kept. The topology catalogue groups braids by pattern
  key, with the same 91 topologies as before.
- Catalogues from outside: a package of a site's own adds braids to
  braidpy's catalogues (`braidpy.catalog.extended`, entry points in
  the group `braidpy.catalogues`), as braid-designer adds machines of its
  own without braidpy knowing them. A profile's `packages` name the
  site's packages: the build runs braidpy with them, installs their
  wheels in the page, and merges the words of their braids from their own
  `locales/`. A profile must now give `packages`.
- Braid Studio in French, or another language: a profile's `language`
  (`web/profile.toml`) names the catalogue its pages are shown in,
  `web/locales/fr.toml` for French, each text braidpy writes in English,
  in Python or in the page, put into it as it is shown (`web/i18n.js`).
  A site opens in its profile's language, braidpy's in English,
  braid-designer's in French with `language = "fr"`; a menu at the top of
  each page switches between them there and then, the braid on show kept,
  and remembers the choice (or `?lang=fr` in a link). A profile must now
  give `language`.
- A design saved by braid3d (`.b3d`) read as a mobidai braid
  (`braidpy.b3d.mobidai_from_b3d`, `braidpy.web.from_b3d`): its yarns in
  their colours, its moves and its repeat, on a disk of as few slots as
  hold its yarns. In Braid Studio, **Import a braid3d design** under the
  mobidai braids fills your own with it and makes it. Ashley's #3054, as
  designed in braid3d, is the sinnet the catalogue has from his drawing;
  disk braids and sinnets saved for braid3d read back as the same braid.
  `braidpy.b3d` is braidpy's one reader of the format (`read_b3d`,
  `write_b3d`): `braidpy.craft_design_online` and its `BraidModel` are
  gone, and with them the dependency on `dataclasses-json`.
- A braid saved for braid3dmin writes, with each step, where the yarns are
  before it, as braid3dmin's own files do; and a strand moved half a turn
  or more, as kumihimo takes one across the disk, as two steps each less
  than half a turn, since a move's angles say only the short way round: it
  was written going the other way round. The angle of a disk's slot is
  one rule, `slotAngle` in `web/marudai.js` (`braidpy.marudai.slot_angle`),
  which `web/b3d.js` and `braidpy.b3d` use.
- Braid Studio built under another name, crediting and linking otherwise:
  what the site calls itself, whom it credits, where it links and whether
  search engines are welcome are a profile (`web/profile.toml`), and
  `web/build.py --profile` builds the site with another. With braidpy's
  own, the pages are as before. How a private site would build on braidpy
  without forking it: *A site of your own* in the developer guide. The
  studio no longer names braidpy while loading, nor in *Also made as*.
- The catalogue's horn gear machines written as their graphs, as a machine
  of your own is (`machine_catalog`): the gears that mesh, where they feed
  axial yarns, and, should it be given one, the carriers it starts with
  (`machine_from_graph(..., axials=, loading=)`,
  `described.read_axials`, `read_loading`, `BraidingMachine.with_loading`).
  `horn_gear.examples` builds them so. Each is the machine it was, with as
  many carriers, but its slots may be numbered from another one round and
  it loads itself: the tubular braids of 12 and 16 now start on other
  slots, and a loading written for a machine as it was may load it
  otherwise. The machines braiding
  several bands at once are built as before. A soutache's or princess
  braid's cords are named after their gear (`axial_A`).
- A machine written as its graph puts a gear's contacts where the layout
  has them whenever whole slots can say so exactly, and only otherwise as
  evenly as its slots allow: the ring of four gears now has each gear's
  contacts a slot apart, as they are, rather than two.
- Every place a horn gear machine could feed an axial yarn
  (`layout.axial_spots`: up each gear, down each ring of gears with room),
  drawn in Braid Studio on the machine: a click loads a spool there or
  takes it off (**Axial yarns**, `axials` in a link, `none` for none).
- Split gears in a machine of your own: a gear split into parts on one
  axle, written `A-B1 B2-C B1+B2`, in two parts or more (`H1+H2+H3`),
  anywhere in the graph; each part's neighbour stands where that part's
  horns come round. Every catalogued machine, the twin plait and the
  three-band machine among them, is written as its graph, and "Your own
  machine…" starts from any. A tree of gears now branches round a gear
  meshing with three or more, rather than piling them on one another; and
  a machine's yarns are drawn off fast enough that two passing the same
  point, as a split gear's parts' carriers do, are a diameter apart.
- A machine braiding round cores has a braid word: each core is a strand
  of it, standing still where it rises through the deck, which the
  carriers pass in front of or behind (`horn_gear.word.flat_word`,
  `annular_word`; they refused such machines). Soutache, princess and the
  triaxial braid now have their word, crossings and permutation in Braid
  Studio, and join the catalogue of braids by topology. Soutache's word
  read off the machine is the one read off its yarns hanging in space,
  cords and all.
- Any horn gear machine, written as the gears that mesh: `A-B B-C C-D D-A`,
  a gear with its own slots `A:6` (`horn_gear.described.machine_from_graph`;
  `graph_of` writes a machine back so). Each gear's direction and contacts
  are worked out from the graph; a ring of an odd number of gears, or gears
  in separate machines, are refused saying why. In Braid Studio, **Your own
  machine…**, starting from the machine chosen before. Studio now reads a
  machine's braid round its ring whenever its gears make one, not by its
  name.
- A machine's carrier tracks in Braid Studio, as the demo draws them: on
  the machine to load, and in the view of it turning, each track in a
  colour of its own (`horn_gear.visualization.track_curves`, which the
  demo now draws its tracks with too). A machine's braid gives them in its
  timeline (`tracks`); otherwise every build is as before.
- Braid Studio's front page: every braid it offers as it comes, in a table
  to filter by name, by what makes it, by strands, by the loops it closes
  into and by writhe, each with a picture of it settled, its links (the
  book, videos, pages) and what else makes the same braid, and opened in
  the studio at once (`braidpy.web.braids`, `web/home.js`,
  `web/snapshots.py`). The studio itself is now `make.html`; old addresses
  naming a braid go on there.
- Each catalogued braid's links, as data: where it comes from and where it
  is shown made, each a title, a kind (book, article, video, page, post)
  and a web address (`catalog.Link`, `Entry.links`; `Entry.reference` is
  now the first link's title). The addresses that were in the catalogues'
  docstrings and notes are there now, and go out with the topology
  catalogue (`topology_catalog.export`), for Braid Studio to show.
- Tightening a braid as a window on an endless one rather than a piece
  held at both ends (`take_off.Periodic`, `tighten_yarns(periodic=...)`):
  the yarn leaving the fell end of the window runs on into the top of it,
  so the braid is not pinched where it was held. The window must be a
  whole number of periods; `take_off.Periodic.closing` finds the wrap a laid braid
  closes on. Without it, tightening is as before. In Braid Studio,
  **Sideways, endless** under *Settle the yarns* (`web/tighten.js`, tested
  against braidpy step for step).
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
  shown alone keeps its colour (`BraidingMachine.carrier_colors`).
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
- A sinnet from the shape it is to take, as Ashley draws it
  (`braidpy.making.ashley.sinnet_from_shape`): lines across the shape
  parallel to its sides, turning at the outline in bights, the bights the
  stand's spaces and the lines its moves, in the book's order or space by
  space. Triangles are the book's #3045, #3047, #3051 and #3059 exactly,
  #3049 with a strand more at each corner (`corner_spaces`), #3057 made
  space by space; flat oblongs, with their chisel edges, #3071 and #3072. A
  shape may turn back, as an L or a U, its lines cut in pieces, or have a
  hole, its bights numbered with the outline's, an inner one between two
  outer ones, so that the sinnet goes round the hole as a tube does. Its
  tracks (`shape_tracks`) can each be made the other way round. On a grid,
  a shape is its cells, squares, squares cut on their diagonals or
  triangles (`grid_shape`, `grid_outline`); on the diagonal grid its
  outline may run on a slant, its lines across and up (`grid_lines`): a
  square standing on a corner has the lines of #3073 and #3074, an oblong
  on a corner those of #3075.
- And back, from a sinnet's moves to its shape: the moves grouped by the
  direction of their lines (`move_groups`), the same at any size for shapes
  drawn on one principle, say the grid, and their number the size; the
  shapes of that grid with as many lines are kept if they join the very
  spaces the moves join (`shapes_from_moves`). Every shape on a grid comes
  back so, and the book's #3045 to #3051, #3059 and #3070 to #3075. The
  book's sinnets that a shape draws say so in the catalogue
  (`solid_sinnets_catalog.DRAWN`), and Braid Studio's list of shapes' braids
  is made from it.
- In Braid Studio, **Ashley's method, from a shape**: a grid, square,
  diamond or hexagonal, and a shape it offers to start from (an oblong, an
  L, a U, a hollow square; a square or an oblong on a corner; a triangle or
  a hexagon), or one of thirteen braids made so; drawn once made, its
  cells, tracks and spaces clicked to change the shape, turn a track round
  or add a strand.
- Two split gears may mesh once for each pairing of their parts
  (`A1-B1 A2-B2 A1+A2 B1+B2`), as a matrix of split gears wants: they touch
  at one contact, the pairing named first handing over at the end of each
  step, the next part way through it (`Connection.phase`). A carrier handed
  on twice in a step is stopped where it meets another.
- A machine is sized for its bobbins: drawn larger, sizes and places
  together, it keeps its carriers further apart in proportion
  (`horn_gear.take_off.clearance`, `Clearance.scale_for`). Braid Studio sizes every
  machine for bobbins of 20 mm (`Machine.bobbin_diameter_mm`) and says how
  large its horns, gears and deck come out; it stops a machine only where
  two carriers come to one point (`horn_gear.take_off.too_close`), which no size
  keeps apart.

### Changed

- braidpy's names are spelled in American English, as Python's and its
  libraries' are (`color`, `center`, `neighbor`, `catalog`) — one rule, no
  exceptions; prose may be British. A test keeps it so
  (`tests/test_spelling.py`). Renamed, the old names still answering with
  a `DeprecationWarning` (`braidpy._renamed`), each for the release that
  renames it and one more:
  `ashley_solid_sinnet.strand_colors`,
  `horn_gear.visualization.colored_tracks`, `horn_gear.word.deck_center`,
  `BraidingMachine.carrier_colors`, `StrandTrajectories.center`,
  `DescribedMachine(centers=)` and its `centers`, the `color=` of
  `BraidGrowth.traces`, and the attributes `b3d.Design.colors`,
  `CarriedBraid.colors` and `AnnularWord.center` (built with the old
  keyword, these three no longer are); the module `braidpy.catalogue` and
  `web.catalogue()` are `braidpy.catalog` and `web.catalog()`, the
  topology catalogue's `catalogue()` is `catalog()`, `similarity`'s
  `catalogue_braids()` is `catalog_braids()`, the mobidai catalogue's
  `CataloguedMobidai` and `CataloguedBraid` are `CatalogedMobidai` and
  `CatalogedBraid`, and each catalogue's `CATALOGUE` is `CATALOG`; the
  catalogue modules keep the names 0.3.0 shipped them — `braid_catalog`,
  `machine_catalog`, `mobidai_catalog`, `solid_sinnets_catalog` and
  `topology_catalog`. Braid Studio's links and the JSON its pages serve
  are unchanged, but the site writes its catalog as `catalog.json`,
  keeping `catalogue.json` beside it for the sites built before it (a few
  months, a release at least), each to be dropped in a later one.
- Braids are compared as patterns (`braidpy.braid_pattern`) where braidpy
  compares them: `BraidPattern.alike`, and `braid_pattern.alike(a, b)` for
  two braids, say nothing measured tells two patterns apart — fast, the
  fingerprints — where `==` proves it. The ways of making a braid, the
  Ashley search and `similarity.similar` check by it, with the same
  results as before. `ring_program.same_braid` is its old name, kept.
  `tools.compare_braids`, and so the MCP server, now also says whether
  two braids are `proven` the same pattern.
- Braids in band generators, braidpy's own
  (`braidpy.band_canonical_form`): `a_ts`, strands t and s crossing in
  front of those between, as round a kumihimo disk or a marudai. Birman,
  Ko and Lee's normal form (`Braid.get_band_canonical_factors`, before
  math-braid's: the same, checked against it, faster) and a braid as band
  letters (`Braid.band_word`, `artin_from_band`). Disk braids spell far
  shorter so: Kongo gumi on 8 strands, 81 crossings, is 43 band letters;
  the 16-strand disk braid, 351, is 117.
  Braid Studio's card gives a braid's band word where it is shorter than
  its word, as a disk braid's is, and Artin's word elsewhere; a band word
  can be typed too (layout **band**: `4:1 1:3`), and the MCP server's
  `describe_braid` gives it.
- A braid is made on a kumihimo disk in band letters where that takes
  fewer moves (`making.disk.disk_moves`): two strands far apart cross in
  three moves, lifted over those between, where crossings of neighbours
  take three each. Kongo gumi takes 129 moves instead of 243, the 12-strand
  disk braid 261 instead of 567, the 8-carrier tubular machine's 78 instead
  of 96; a braid no shorter so, as a flat machine's, is made as before,
  move for move. `band_canonical_form.band_letters` reads a word as band
  letters as it stands.
- braidpy no longer needs math-braid (PyPI 0.8, 2018, unmaintained): a
  braid's triviality, and so `==`, falls back on braidpy's own Garside
  normal form when handle reduction takes too long, and the page no longer
  installs it; the tests still check braidpy against it. The normal form
  (`artin_left_normal_form`, `left_weighted`) is the same, worked out
  another way: the half twists kept at the word's end, each factor made
  left-weighted with those before it in one pass back, the crossings each
  can begin and end with changed only where a crossing moves. Fifty times
  faster: ABOK #3082 on 61 strands against itself rewritten, three seconds
  (math-braid: seventeen).

- In a ring of gears timed so that every contact is on a horn
  (`described`, `layout.time_ring`), the parts of a split gear are
  stacked on their axle, each keeping its own time, the axle as large as
  one part; the bands they join are laid out each alone and put
  together, each split gear's parts half a pitch apart (or j/k of k).
  Two matrices of gears joined by split gears, the split ladder, now each
  braid as they do alone: 28 carriers rather than 14, clear of each other.
  Machines without split gears in a ring are as before.

- A sinnet whose strands all move to the right (`AshleySolidSinnet.all_right`),
  as the book's #3058, #3059 and #3066 to #3069 do: a strand from an even
  space is led anticlockwise too, still from the left of its space. The
  disk, its animation and the mobidai pattern go round as the book says;
  the braid is the same, a strand carried over all being free to swing
  over the top. #3057 and #3058, given one table in the book, now differ
  as the book has them, in this alone.

- Every contact of a horn gear machine hands over when a horn of each gear
  comes round to it: round a ring of six or eight gears of four slots, or a
  matrix of gears of several sizes, the gears are moved and sized so that
  they do (`layout.time_ring`), a contact handing over part way through a
  step where it must. tubular_12, tubular_16 and triaxial_16 build so, with
  the same carriers, period and braid.
- Gears in a ring are drawn to touch, those that do not mesh kept clear
  (`layout.ring_geometry`), rather than shrunk from a spring layout till no
  mesh was too long, which left gears of several sizes running through each
  other.
- A quantity not in SI units carries its unit in its name:
  `making.ashley_sinnet` and `making.sinnet_for_page` take `time_limit_s`.
- Leftovers removed: `braidpy.operations` (its one function, `conjugate(b,
  c)`, is `c * b * c.inverse()`), `braidpy.material_braid` (an early sketch;
  yarns with a thickness are `take_off`'s and `rope`'s), the empty
  `braid_catalog.triangle_sinnet_9` and `triangle_sinnet_10` (ABOK #3057,
  #3058 and #3045 are in `solid_sinnets_catalog`), and `src/braidpy/analytic/`,
  which held only a pointer to *Why there is no closed form*.

- `braidpy.take_off` is a package rather than one module of 1734 lines:
  the trajectories laid and the yarns (`paths`), laying (`laying`),
  contact between yarns (`contact`), tightening (`tighten`), drawing
  (`drawing`), where each source's strands go (`sources`) and a disk's
  braid laid round a ring (`ring`). Every name is imported from
  `braidpy.take_off` as before, and every braid Braid Studio makes with the
  site comes out the same.

### Fixed

- The nearness of a band's new axles to those placed, on a machine of
  split gears, comes out a plain float: it was numpy's, as `np.linalg.norm`
  gave it.
- `Braid.is_periodic()` answers the theorem it quoted: a braid is periodic
  when its nth power or its (n − 1)st power is a power of the half-twist
  Δ, read in the Garside canonical form.  It asked only whether such a
  power was pure, so σ₁² kept every strand's place and was said periodic,
  as was the catalogue's asymmetric_flat4, which is not; a rotation's
  braid, as σ₁σ₂ on three strands, is.
- `hash(Braid)` agrees with `==`: two words for one braid hash alike,
  so a braid is one key in a dict or a set however it is written. It
  hashed the word, while `==` compares the braid itself; it now hashes
  what every word for a braid shares (strands, exponent sum,
  permutation). `word_eq` still compares words.
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
- Two words of one long braid could have fingerprints apart, their
  polynomials sampled in floating point: fingerprints now compare the
  Burau matrix's characteristic polynomial computed exactly, modulo a prime
  (`burau_mod`).
- A word of tens of thousands of crossings overflowed its floating-point
  Burau matrix, and `fingerprint()` raised: the matrix is scaled down as it
  grows.
- A machine's flat word missed a carrier passing several others in one
  sample, every later crossing given to the wrong strands; and carriers
  crossing just as a period starts were counted at neither end (flat_4's
  word is twelve crossings, pure every period). A word is read over the
  loading's own period: flat_9's is 18 steps, not 180.
- Yarns passing nearly the same point, as on one split axle, are lifted by
  the take-off rather than drawn out a hundredfold to part them.
- A machine's carrier track is drawn round its loop once: on a machine with
  a long period, the points kept fell laps apart and were joined across the
  deck.

### Documentation

- *Laying out a horn gear machine*: how gears are placed, sized and timed,
  with figures and equations.

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
