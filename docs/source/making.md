# Bridges between ways of braiding

braidpy makes a braid many ways: as a braid word, on a kumihimo disk, on
Ashley's stand, on a braiding machine, on a Jacquard lace machine. Each
already gives the braid it makes, as a braid word. A bridge goes the other
way: from a braid — a braid word, say — to how to make it another way.

Two braids are the same braid, for a bridge, when nothing braidpy measures
of their topology tells them apart ({func}`~braidpy.ring_program.same_braid`,
see {doc}`comparing_braids`): a way of making a braid need not make its very
word, only the same braid. Each bridge is checked by reading the braid back
off what it made, with the code that reads it off that way of making
braids, and comparing.

## Neighbours swapping places round a ring

A braid word, a kumihimo disk and a lace machine all make a braid by
moving strands round a ring of places, two neighbours at a time. A
{class}`~braidpy.ring_program.RingProgram` says so once, for all of them:

- the places round the ring, and which strand starts where — a place may be
  empty;
- rows of **swaps**: two neighbouring places exchanging what they hold, the
  swaps of a row sharing no place, so made at once. Two strands swapping
  make a crossing; a strand and an empty place make none, the strand only
  moving on by a place.

The ring is seen from above, from the side the braider works from on a
kumihimo disk, and the braid is made downwards, away from the eye, as it
hangs below a disk. Places are numbered clockwise from 0, the ring's seam
between the last and place 0, and the swap of place `p` exchanges places
`p` and `p + 1`. Its sign is the crossing's, as a braid word writes it:

- **+1**: the strand at `p + 1` goes first, anticlockwise, lifted over the
  one at `p` — over seen from above, so passing inside it, nearer the
  braid's axis — and the strand at `p` moves clockwise into the place it
  left. With the strands at places 1 to n counted from the seam, the
  positive swap of place `i - 1` is σᵢ.
- **−1**: the strand at `p` goes first, clockwise, over the one at `p + 1`:
  σᵢ⁻¹.

A swap with an empty place crosses nothing, and its sign changes nothing.

```python
from braidpy import Braid
from braidpy.ring_program import from_braid

plait = Braid((1, -2) * 3, 3)
program = from_braid(plait, n_places=6)  # three strands, three empty places
program.braid() == plait  # True: read back off its disk moves
program.disk()  # the same, as a disk's moves
```

A braid word becomes a ring program crossing by crossing
({func}`~braidpy.ring_program.from_braid`), the crossings packed into rows
where they commute. It is read back as a disk braid is
({func}`~braidpy.take_off.disk_annular_word`): a swap is the lifted strand
moved over its neighbour, then the neighbour into the place it left.

The ring has a seam, between its last place and its first. Strands carried
across it twist the braid below them, as carriers going round a tubular
braiding machine do: every strand once round the ring is a full twist. That
is still a braid, and often a shorter way to make one; but a braid word has
its strands in a row from the seam, so the bridges from a word keep them off
it for now, and make that very word. Shorter programs, going over the seam,
are for later.

## The Jacquard lace machine

braidpy's lace machine ({func}`~braidpy.horn_gear.jacquard.jacquard_lace_ring`)
is a ring of 2-slot gears. A bobbin sits in a **notch**, cut where two
neighbouring gears overlap, and a gear's half turn swaps the bobbins of its
two notches: the notches are the ring's places, a half turn a swap.

```python
from braidpy.bridges.lace import lace_braid, lace_card

plait = Braid((1, -2) * 6, 3)
card = lace_card(plait)
print(card.text())  # the punchcard, two lines a step, as animated
card.threading()  # where each strand's bobbin goes
lace_braid(card) == plait  # True: the card run on the machine
```

A step of the card is two lines over the gears, as the machine reads it:
those to turn anticlockwise, then those to turn clockwise, the second half
a punch to the right of the first, as it is driven half a step later and as
the machine's animation draws it. A gear always
turns the same way, and neighbours turn opposite ways, so which bobbin
passes over is fixed by where the crossing is made: an anticlockwise gear
makes a positive crossing, a clockwise one a negative one. A braid word's
crossings come with any signs, anywhere, so the strands are kept side by
side with a notch to spare; when a crossing's sign is not its gear's, they
all move along one notch, into the spare one, crossing nobody, and every
gear under them is then of the other way. They only ever move between two
neighbouring positions, keeping off the ring's seam as a word's strands do
(see above), and end where they began, as a punchcard is run round and
round. The Dutch braid, whose signs
alternate as the gears do, needs no moving; the plait moves along at the
start and back at the end.

The card is checked on the machine itself
({func}`~braidpy.bridges.lace.lace_braid`): it is run, after each step every
bobbin is found in its notch, and each gear that turned must have swapped
its two. Every catalogue braid comes back exactly.

## A kumihimo disk

On a kumihimo disk (a mobidai, {mod}`braidpy.mobidai`) a move takes one
strand from a slot to another, the short way round, lifted over every
strand it passes. Each crossing becomes three moves, the strands kept two
slots apart — strand `k` from slot `2k + 3` — so every strand has an empty
slot either side of it: the strand lifted goes over its neighbour into the
empty slot beyond it, which is the crossing; the neighbour moves into the
place it left, and the lifted strand settles into the neighbour's old place,
neither crossing anything. A 32-slot disk takes up to 15 strands.

```python
from braidpy.bridges.disk import disk_braid, disk_moves

moves = disk_moves(plait)
moves.text()  # "5>2, 3>5, 2>3, 5>8, 7>5, 8>7, …"
disk_braid(moves) == plait  # True: read as braidpy reads any mobidai
moves.spec()  # the disk braid as Braid Studio makes it
```

## Ashley's stand

On Ashley's stand ({mod}`braidpy.ashley_solid_sinnet`) the strands lie in
spaces round the rim, and a move carries a strand from one space to another,
over every strand it passes: not a swap of neighbours. So the bridge
searches for a sinnet that makes the braid
({func}`~braidpy.bridges.ashley.ashley_sinnet`): the strands shared out
among the spaces, and a cycle of moves in which every space gives a strand
and receives one, as the book's sinnets do. Fewer spaces are tried first;
a sinnet is found when its braid has the topology wanted.

```python
from braidpy.bridges.ashley import ashley_sinnet, sinnet_spec

search = ashley_sinnet(plait)
search.sinnet.initial_counts_per_space, search.sinnet.moves
# ([2, 1], [(1, 2), (2, 1)]): Ashley's #2965
sinnet_spec(search.sinnet)  # the sinnet as Braid Studio makes it
```

Of the fifteen braid words Braid Studio offers, twelve are made by a sinnet
of this kind, found in under a second; among them the plait and the square
sinnet are found as Ashley's own #2965 and #2999. The other three, the weave
of 3 (#2973), the four-strand sinnet (#2974) and the four-strand flat, are
not: every sinnet of up to as many spaces as strands was tried — one strand
per space among them — and the nearest is given, with how far it is. What
rules them out is the sinnet's own rule, every space giving one strand and
taking one in a cycle, with no space empty.

Without that rule, any braid can be made on the stand
({func}`~braidpy.bridges.ashley.ashley_moves`): one strand per space with an
empty space after each, and each crossing made in three or four moves
through the empty spaces, every space then holding what it held before. It
is the braid itself, exactly, though not a sinnet of the book's kind.

```python
from braidpy.bridges.ashley import ashley_moves

weave = Braid((1, -2, -2, 1), 3)  # the weave of 3, #2973
made = ashley_moves(weave)
made.initial_counts_per_space  # [1, 0, 1, 0, 1, 0]
made.braid(1) == weave  # True
```

## In Braid Studio

Beside every braid it makes, Braid Studio's card offers **Make it as…**:
its repeating unit as moves on a kumihimo disk, a link that makes them;
as a lace machine's punchcard, to copy or download, with the notches to
thread; and, when asked, a sinnet on Ashley's stand, searched for in the
browser for a few seconds, a link that makes it — or the nearest, if no
sinnet makes the braid ({func}`~braidpy.bridges.for_page`,
{func}`~braidpy.bridges.sinnet_for_page`).
