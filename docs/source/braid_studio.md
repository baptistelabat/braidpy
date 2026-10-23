# Braid Studio: braidpy on the web

Braid Studio is a web page where anyone can describe a braid — a braid word,
a kumihimo pattern, a disk braid, an Ashley sinnet, a horn gear braiding
machine — and see it laid and tightened in 3D, without installing anything.

This page says what it does and how to use it. How it is built is in the
developer guide.

## What it does

The page has a form and a 3D view.

- **Made by** picks the source: a braid word; a braid from the mobidai
  catalogue; an Ashley solid sinnet; a braiding machine; or a Jacquard lace
  machine. Kumihimo's
  `S`/`R` moves are out of the menu for now, but a link to one still makes
  it.
- A braid word starts from a list of examples — a plait, a twist, a flat
  four-strand braid, a two-ply, a rope — as the other sources start from
  their catalogues; changing the word makes it your own.
- Each source asks for what it needs: the word and the number of strands; the
  pattern and how often to repeat it; which braid, and for how many cycles.
  The advanced section sets the yarn diameter and how hard the yarns are
  pulled (the tightening steps; 0 lays them with no tension).
- A braid word is drawn as it is typed, as a 2D diagram — strands running
  down, the one passing behind broken where they cross — before the braid
  is made.
- A braid word can also be a **ring word**, its strands round a circle as
  on a marudai: `1` to `n - 1` cross neighbours as in a braid word, `n`
  crosses the last strand and the first, across the seam, and `n + 1` turns
  every strand one place round. It is drawn on a cylinder cut at the seam,
  and made on the marudai move by move as written. A turn carries every
  bobbin round together, passing nobody, the braid held: the yarns twist
  into a rope, each as far from its axis as the others.
- A braiding machine is drawn from above in the panel, as it starts: its
  gears, the contacts between them and every slot, its carriers on them.
  Click a slot to put a carrier on it or take it off, or type them in as
  `gear:slot`; **Its own loading** puts back the machine's. Two carriers on
  the same point are ringed at once. Carriers that meet as the machine turns
  stop the braiding there: the braid is what it made until then, the note
  says at which step and where, and the carriers that met are ringed where
  they started. Left as the machine loads itself, the loading is not
  written into the link.
- Its **handle** turns it, a step at a time: ▶ turns a step, smoothly, ◀
  turns it back, ⏮ goes back to step 0, and **Run** turns it until carriers
  meet, or until stopped. Carriers that meet stop the handle, ringed, at the
  step they met. What is turned is always the loading at step 0 — what the
  machine braids with — so a carrier put on a slot at a later step is loaded
  on the slot at step 0 that brings it there; taken off, the same.
  braidpy does the turning (`braidpy.horn_gear.handle`) and says where every
  slot and carrier is through each step: the same places as its plotly
  animation, so the page and Python agree. In Python,
  `Handle(machine).turn(5).figure()` is the same handle, drawn with plotly.
- A **Jacquard lace machine** (`braidpy.horn_gear.jacquard`) is a ring of
  gears driven by a punchcard rather than geared together: a bobbin sits in
  a notch, where two gears overlap, and the card says which gears turn at
  each step, the anticlockwise ones and then the clockwise ones. It is drawn,
  threaded by hand and turned by its handle as a braiding machine is. Its
  examples are a ring with every gear turning, as a tubular braider, and
  cards punched for braids of the catalogue — the Dutch braid, the plait,
  the weave of 3, two four-strand sinnets, a flat braid of 6
  ({func}`~braidpy.making.lace.lace_card`). Its word is read off the
  machine itself, a pass of the card a repeat
  ({func}`~braidpy.making.lace.ring_braid`), and the card is in the notes,
  as punched. The gears and the card of the machine chosen are shown, ready
  to change, as a sinnet's moves are: **Your own card…** takes an even
  number of gears and a card typed a step a line, the gears turning
  anticlockwise then those turning clockwise, a 0 or 1 a gear —
  `1000 0100`. A card that cannot drive the machine says why, in the panel.
- A machine that braids round **cores** braids them in either as yarn, held
  at both ends and giving way between to the yarns pressing on it, or as
  rigid cores, straight; either way each core keeps its own place, where the
  machine lays it, and no yarn or other core ever passes through it.
- A disk braid — kumihimo, mobidai, a sinnet — is **made on a marudai**
  (`web/marudai.js`): the disk's own moves, one by one, each moved yarn
  laid over the others and drawn tight, as braid3dmin makes a braid. It is
  the closest to a real braid, sinnets taking the shapes of their
  cross-sections. A braid word is made there too, its strands rolled onto
  a ring of bobbins, the braid held. A machine's braid is tightened
  **sideways**, fast, keeping the pitch it was laid with. Under "Yarn and tightening", **Settle the
  yarns** can choose otherwise: sideways for a disk braid too, or, for any
  braid, by physics (`web/rope.js`, in beta) — each yarn an elastic
  chain of beads, clamped at the fell and fed from a bobbin, the braid
  beaten up until its crossings jam — or made crossing by crossing, with
  friction. The view follows each as it goes. A braid word to settle by
  physics is laid round a ring, as a disk braid is, each crossing two
  neighbours swapping places, the moves the marudai makes. A machine's
  braid and a braid word in a row are laid on a fell ring the size of the
  braid, as a braid really forms, not drawn in to a point: settled by
  physics, the yarns are held there apart, and keep the braid they were
  laid as. A machine braiding round rigid cores is only tightened sideways:
  the physics would bend them as yarns.
- A disk's top view is turned so its seam — where its numbering closes,
  between its first slot or space and its last — is up, away from you; a
  braid made on a marudai is turned to match, each yarn going to its
  carrier where the top view has it, and seen from the top view's bottom,
  the seam behind it. A braid word is seen half round, its ring's seam
  behind it too. A sinnet's disk shows its spaces as numbered sectors, as
  the book draws them.
- **Hanging** shows a braid hanging from its fell, as from a kumihimo disk
  or a marudai, or, unticked, rising from it, as from a braiding machine.
  Braids made on a marudai hang unless asked otherwise. Made, they show
  their yarns' tails too, as on a real marudai: up from the fell to the
  hole in a see-through mirror, flat across it, and over its edge towards
  their bobbins. The physics pulls each yarn at the hole, where the mirror
  takes the pull; the rest is drawn. The making shows as it goes — each
  yarn carried up over the others to its new place, drawn tight, the braid
  settling — and **Grow** replays it, move by move, before showing the
  braid made. Each moment is kept only as its yarns still free: a bead
  frozen into the braid moves only as the whole braid turns, so it is put
  back from the braid as made, turned back to where it was. Even a sinnet
  of 45 strands keeps some eighty moments within a few megabytes, made
  with the site. It is a half turn of the view
  about a level axis: the braid stays the braid it is, where only flipping
  its heights would show its mirror image.
- A disk braid or a sinnet can also be **your own**: choosing "Your own
  moves…" shows what the braid chosen before is made of — the slots its
  strands start in and its moves, or its spaces' counts and moves — ready to
  change, as text or by clicking on a drawing of the disk: a strand, then
  the slot it goes to (or a space, then the space a strand goes to).
  A kumihimo disk's braid, or an Ashley sinnet, shows what it is made of
  always, ready to change there: changing a move, its slots, its counts or
  its turn makes it your own, and the catalogued braid stays as it was, to
  choose again.
- The yarn diameter and the tightening steps, left empty, take the braid's
  own defaults, shown greyed with "default" once it is made; going into the
  field puts the default in, so that its arrows step from there. The
  marudai draws its yarns tight itself, without tightening steps.
- **Strands**, under the form, gives each strand its own colour, changed
  everywhere the braid is drawn. Strands of one colour are a **group**,
  listed above the strands with how many there are: pointing at a group
  shows its strands among the others, and changing its colour changes them
  all. A strand joins a group by taking its colour — the braid's own colours
  come first in the palette — and Ctrl-, Cmd- or Shift-clicking strands
  colours several at once. Groups are only colours, so the link says them as
  it says the colours.
- The braid is drawn as tubes, one colour per yarn, and can be turned, zoomed
  and spun. **Grow** replays it being made, by the clock of whatever made
  it: the oldest rows first, carried up as the newest form at the fell. An
  inset shows what made it, seen from above, at the same instant — the disk
  with its strands as spokes, the machine's gears and carriers — and a
  disk's braid turns with the disk, each strand at the fell nearest its
  carrier.
- Over the view, in a card that folds away to its title, what is known of
  the braid: its strands; after how many of its words or cycles it is pure
  — every strand back where it started — how many were made, and so
  whether it is; its crossings and word (its ring word too, for a disk
  braid), the permutation it makes, what it closes up into (a knot, or a link of so many pieces), its Garside
  normal form and full twists, how close the yarns come.
  Long words show three lines; **Make from it** makes the braid again from
  its own word or ring word, as a braid word — the same braid, made on the
  marudai much as the disk made it — and **Copy** copies it. Under them,
  **Also made as** lists every other way the catalogues make the same braid
  — the plait typed as a word is also the three-carrier flat machine's — and
  **Nearest braids** the braids of the catalogues most like it, whatever
  makes them, each with how unlike it is; your own braid too, found by its
  fingerprint ({doc}`comparing_braids`). Each is a link that makes it. And
  **Make it as…** gives the braid made other ways ({doc}`making`): its
  moves on a kumihimo disk, to make; a lace machine's punchcard, to copy or
  download; and, when asked, a sinnet on Ashley's stand, to make. The
  braid is drawn in the middle of what the card leaves free.
- A braid word or ring word is made on the marudai hanging free, as a disk
  braid is; when the bobbins turn together it is held while they turn,
  twisting the yarns in, and a word of nothing but turns — a rope — is held
  all the while. Under "Yarn and tightening", **Twist, on the marudai**
  can choose otherwise: kept, the braid held throughout, so it never turns
  to balance and turning the bobbins together always twists the yarns in
  (a kumihimo's R moves too); or untwisted, the braid hanging free
  throughout, so the bobbins turning together carry it round with them and
  twist nothing in — a rope then comes straight back out, its yarns
  hanging straight and side by side, and the page says the braid is no
  longer the one its word says. Held, the yarns are laid
  out to their carriers and drawn tight after every move as when free; only
  while the bobbins turn together are they carried round, not over each
  other.
- **Twist** applies to each way of settling the yarns as it can: on a
  marudai, kept, held while the bobbins turn together, or untwisted;
  settled by physics, the end plate the braid is drawn off by held still
  (kept) or free to turn (untwisted); tightened sideways it is not offered,
  the yarns keeping the twist they were laid with.
- A sinnet's disk, to click your own moves on, is numbered as its top view
  is: anticlockwise from the top, the first space and the last meeting
  there.
- These choices offer no "automatic": each braid's own is selected and
  marked "(default)" — guessed from its source, then as it was made — and
  only one chosen otherwise goes into the link.
- The view's switches — tubes, spin, hanging, the top view and the
  cross-section — are in the toolbar's **View** menu.
- The address bar always describes the braid shown, so **Copy link** shares
  it. **Save…** keeps a picture, the yarns as an STL file for 3D printing or
  an OBJ model, or their points as JSON. A braid made on a disk can also be
  saved **for braid3dmin** (B3D): the braid as made move by move on the
  marudai, each yarn bead by bead, with its moves listed as braid3dmin
  lists them. When the disk turns with the braid on it, nothing moves
  against anything else, so braid3dmin has no step for it, and the angles
  that follow are counted from the braid.
- **Braid** makes the braid described. Asking for another while one is
  being made stops it at once: the yarns are settled in a worker of their
  own (`web/settle.js`), apart from braidpy's, which is ended and started
  again without reloading Python. On the marudai, asking for more of the
  same braid — more repeats or cycles — goes on from where it was left,
  making only the moves still to come, even while it is still being made;
  the note says from which move. **Reset** stops whatever is being made and
  forgets the marudai, so the next braid is made from the start.
- The last few braids made are kept: going back to one is instant.

How the page is built, how to run it locally and what comes next are in the
developer guide: [Braid Studio's internals](braid_studio_internals.md).
