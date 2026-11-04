# Making a braid on a marudai

Braid Studio makes a disk braid — a kumihimo or mobidai braid, an Ashley
sinnet, a braid word rolled onto a ring of bobbins — move by move, as it
would be made on a marudai: each moved yarn carried over the others to its
new place and drawn tight, the braid settling below. `web/marudai.js` does it
in the browser, and `braidpy.marudai` is the same algorithm in Python, to
read and to check it by.

The method is that of braid3dmin, a kumihimo simulation in three.js: yarns
as chains of beads, pulled by their bobbins, relaxed a bead at a time. This
page describes braidpy's own implementation of it, in its own terms; the code
is this project's own, and none of braid3dmin's is in it.

## The yarns

Each yarn is a chain of **beads** a unit apart and two units thick: a unit is
half a yarn diameter. Inside, lengths are in units and y is up; what comes
out is in yarn diameters, z up.

- **A link** between two beads of a yarn pulls them together only when it is
  stretched beyond a unit, as a rope does: a slack yarn pushes nothing.
- **Two beads** less than two units apart, of the same yarn or not, push each
  other apart. Links and contacts have the same stiffness (10).
- **A yarn's end** is drawn towards its **carrier**, on the rim of the
  marudai's mirror and above the braid's tip, by a constant pull (1.2): its
  bobbin. The carriers stand on a circle of radius 19 units, half the rim's
  reach (20) above the tip.

## A move

A move takes a yarn's end from its carrier to another, round the rim:

1. **Laid over the top.** The yarn's new stretch goes from where it leaves
   the braid up over everything in its way — a map of the yarns' heights
   says how high — and down to its new carrier, a bead a unit.
2. **Drawn tight.** The new stretch is then drawn as a string would go: each
   bead moved to between its neighbours or, where a yarn is in the way,
   round it, to whichever side has room.
3. **Relaxed.** The beads that moved are queued. One at a time, each is moved
   by the forces on it — its links, its contacts, its bobbin — by a step
   that shrinks as the relaxation goes on, and its neighbours and the beads
   near it are queued in turn. It stops when the queue dies down.

A move of more than nine tenths of a half turn goes in two halves, so that it
passes over what lies on its own side of the braid. When every yarn moves
alike, the disk itself turns: the braid turns with it, or, held, the bobbins
turn round it and twist the yarns in.

## The braid

- **Turning to balance.** Hanging free, after each move the braid turns
  about its axis until its yarns' ends pull it no way round: the angle is
  found by a search up to an eighth of a turn either way.
- **More than 30 yarns.** The method was made for marudai braids of a few
  dozen yarns at most. Beyond 30, two things change, and braids of 30 yarns
  or fewer are made exactly as before:
  - The yarns are tied round rings of at most 30, one ring 2 units under the
    next, the yarns taken in turn round the disk. A single ring, a third of
    a unit across per yarn, would be so wide that the yarns rose from it as
    a hollow tube and were never drawn into a braid.
  - Each yarn's pull on the braid is taken along its whole way, from the
    braid's tip out to its end, instead of along its last link alone. A
    link just laid can point any way, and with so many yarns the braid
    swung back and forth by more each move, then grew without end.

  ABOK #3063, #3077, #3079 and #3081 (31 to 45 strands) are then made a few
  diameters long. #3082 (61 strands) still is not: 61 yarns side by side do
  not fit round the carriers' circle.
- **Made, frozen.** Well behind each yarn's end — 40 beads behind the last
  that moved — the braid is made: its beads are frozen, and only the newest
  rows move. A frozen bead moves only as the whole braid turns.
- **Neighbours found in a grid.** Beads are kept in flat arrays, and a bead's
  neighbours are found in a grid of cells 2.6 units wide; the made braid,
  well below anything free, leaves the grid.

## What comes out

The yarns, cut at the braid's tip, and their tails from the tip out to their
carriers; how far the braid has turned; and, for Grow, the moments of the
making — each yarn carried over, drawn tight, the braid settled — kept as
their beads still free ([Braid Studio](braid_studio.md)).

How it compares with braid3dmin run on the same moves, and with the other
ways Braid Studio settles a braid, is in
[Settling a braid by physics](rope_physics.md), under "Made on a marudai, move by move".
