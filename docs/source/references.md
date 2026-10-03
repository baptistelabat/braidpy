# 🧶 Braid Group: Code Resources, Visualizations & Research

## 📘 General background wikis on braid theory

- [Braid on Wikipedia](https://en.wikipedia.org/wiki/Braid)
- [Braid group on Wikipedia](https://en.wikipedia.org/wiki/Braid_group)
- https://ncatlab.org/nlab/show/braid+group
- https://www.labri.fr/perso/marckert/poulalhon.pdf
- https://homepages.math.uic.edu/~jaca2009/notes/Meneses.pdf Maybe one of the best paper which is describing some
relationships between algebraic and geometric braid
- blob:https://github.com/8f3cf57d-953c-4b95-b920-e561721cbdbd
- https://github.com/louisepb/TexGen
- https://mathcenter.oxford.emory.edu/site/math108/braid_arithmetic/
- https://eprints.nottingham.ac.uk/76624/1/Thompson%2C%20Matthew%2C%2014343257%2C%20corrections.pdf
- https://jsphdms.github.io/2023/01/06/knots.html
---

## 🧮 SageMath Implementation

> The most comprehensive implementation is in **SageMath**, but due to its **GPL license**, it won't be integrated here.
> However, having a look to the functions implemented gives a good idea of how wide this domain is.

- [SageMath Braid Group Documentation](https://doc.sagemath.org/html/en/reference/groups/sage/groups/braid.html)

---

## 🎨 Visualization Tools

- [rexgreenway/braid-visualiser](https://github.com/rexgreenway/braid-visualiser) – Flat diagram visualization, available on [PyPI](https://pypi.org/project/braidvisualiser/)  -> used by braidpy   
- ([Denbox/Braid-Group-Visualization](https://github.com/Denbox/Braid-Group-Visualization/blob/master/braid_visualization.py) – Flat diagram but lacks good crossing visuals  )
- [loopspace/braids](https://github.com/loopspace/braids) [LaTeX braids package](https://texdoc.org/serve/braids/0) – LaTeX-based braid rendering available on github. Impressive customization, good for documentation  
  (https://github.com/BnZel/poses_and_braids)
  (https://github.com/isaac-art/BraidLab) More of an art work
- https://github.com/rpitasky/typst-braid
- https://github.com/joeLepper/braider?tab=readme-ov-file Node. Demo https://braider.surge.sh/
- https://github.com/byorgey/braids
- https://github.com/lightningund/braid
- https://github.com/christian-oudard/logo -> interesting
- https://github.com/the-bakery/braided > protoype to edit graphically a braid diagram in web browser
- https://github.com/WhimsicalDragon/BraidMaker (weird)
- https://github.com/Sonicpineapple/Braids another online braid editor
- https://github.com/textiles-lab/show-braid
- https://github.com/mweitzel/braid html braid generator from word
- A more general way to store and visualize different textiles https://github.com/virtualtextiles/pytexlib
Alternative Python library:

- [braidpy (PyPI)](https://pypi.org/project/braidpy/)

---

## 🧠 Dehornoy’s Work

Author of _"Le calcul des tresses"_, Dehornoy contributed several algorithms like handle reduction.

- 📄 "Patrick Dehornoy: A Fast Method for Comparing Braids"  
- [Old Pascal Code](https://dehornoy.lmno.cnrs.fr/programs.html)  
- [Dockerized Pascal Source](https://github.com/dehornoy/programs)  
- [Python handle reduction](https://github.com/abhikpal/dehornoy)  
- [C++ handle reduction](https://github.com/chesterelian/dehornoy)  
- [gbraids – Research with n=4](https://github.com/jfromentin/gbraids)  
    - Handle reduction  
    - DynnikovCoordinates  
    - Dual generator  
- [TU/e paper on Dehornoy](https://pure.tue.nl/ws/portalfiles/portal/67742824/630595-1.pdf)
- https://github.com/jfromentin/handle

---

## 🐍 Python Libraries (GitHub & PyPI)


- [kuboon/math_braid.py](https://github.com/kuboon/math_braid.py)  is available on [PyPI](https://pypi.org/project/math-braid)  
    - Last updated 6 years ago  
    - Scarce documentation but test in doctest 
    - BSD license (usable with wrapper or code import)  
    - Examples:

      ```python
      # Artin generation (num = 1 to 3)
      Braid([1, 2, 3], 4)

      # Band generation (num = 1 to 4)
      b = Braid([[3, 1], [1, 2]], 4)
      ```
- [rexgreenway/alexander-data](https://github.com/rexgreenway/alexander-data) – Invariant calculation (not on PyPI)  
- [leodana/TIPE](https://github.com/leodana/TIPE/blob/master/programmes%20tresses.py) – Dense, untested student code  
https://github.com/stla/braids
- https://github.com/MarkCBell/flipper?tab=readme-ov-file - probably very powerful, but a bit abstract
- https://github.com/mateosi98/Unknotting-Braids
- https://github.com/GriffinKowash/Cable-braids/tree/main
- https://github.com/iowyth/harmonic-braider
---

## 📊 MATLAB / BraidLab
- [Braidlab PDF Guide](https://github.com/jeanluct/braidlab/blob/master/doc/braidlab_guide.pdf) which was published [arXiv:1410.0849 – Braidlab paper](https://arxiv.org/pdf/1410.0849)  
  - Matlab code is available [jeanluct/braidlab](https://github.com/jeanluct/braidlab)
  - Probably the best introduction to computation with braids
---
## Julia
https://github.com/jwvictor/Braids.jl

---

## Haskell
https://hackage.haskell.org/package/combinat-0.2.8.2/docs/Math-Combinat-Groups-Braid.html#v:-61--61-

---

https://github.com/jeanluct/cbraid?tab=readme-ov-file
## 🪢 Knots & Related Libraries

Braid functions are often used in knot theory.

- [Algebra8/Knots](https://github.com/Algebra8/Knots)  
  - Project name: `braidgenerator` on PyPI  
  - Not very useful  
- [Documentation Site](https://algebra8.github.io/braidgenerator_doc.github.io/) – Well made

### Knot libraries:

- [pyknotid (PyPI)](https://pypi.org/project/pyknotid/)  
- [SPOCKnots/pyknotid](https://github.com/SPOCKnots/pyknotid)  
  - Convert braid word → knot  
  - Advanced visualizations  
  - [Relevant code line](https://github.com/SPOCKnots/pyknotid/blob/4d248ff32712702530e458b9dfa276038a5e61b2/pyknotid/spacecurves/spacecurve.py#L286)

- [xcapaldi/tbkm](https://github.com/xcapaldi/tbkm) – Random braid visualization in terminal  
- [RafaelMri/Pyknots](https://github.com/RafaelMri/Pyknots)  
  - Step-by-step handle reduction  
  - [Braid code reference](https://github.com/RafaelMri/Pyknots/blob/10254b7ea36e67544bf6867f88bad85b872ffa75/modules/braids.py#L11)

---

## 📺 Video Resource

- [YouTube: Braids Explained](https://www.youtube.com/watch?v=8DBhTXM_Br4)

---
## Braid patterns (1/1, 2/2, 3/3, milanaise)

A braid *pattern* names how many opposing yarns each yarn passes over and
under. It describes the **interlacing**, not the machine: the same machine can
produce several patterns.

| Pattern | Notation | Each yarn crosses | Note |
|---|---|---|---|
| Diamond | 1/1 | over 1, under 1 | plain-weave equivalent; most dimensionally stable |
| Regular (plain) | 2/2 | over 2, under 2 | 2/2 twill repeat |
| Hercules | 3/3 | over 3, under 3 | least stable of the three |
| Milanaise | 3/1 | 3 threads over 1 | thick, asymmetric; 1920s neckties, tricolour slider on French mayors' sashes |

- [ScienceDirect — Triaxial braid overview](https://www.sciencedirect.com/topics/engineering/triaxial-braid)
  — diamond/regular/Hercules definitions and relative stability.
- [L'Atelier de Tressage — la tresse plate](https://www.atelierdetressage.paris/tresse-plate/)
  — French flat-braid designs (uni, chiné, grappé, damier, pied-de-poule,
  diagonal, milanaise). Flat looms run 7–121 fuseaux, single circuit.
- [Meubliz — définition d'une milanaise](https://www.meubliz.com/definition/milanaise/)

> ⚠️ **The names collide between industries.** In composites, *diamond* = 1/1
> and *regular* = 2/2. In medical wire braiding, *regular* = 1-under-2-over-2
> and *diamond* = 2-under-2-over-2. Always state which convention is meant.
>
> - [Teleflex Medical OEM — braid patterns](https://www.teleflexmedicaloem.com/get-to-know-us/medtec-resources/braid-patterns/)
> - [MMBT — herringbone, diamond and half-load explained](https://mmbt.us/blogs/news/braid-patterns-in-mmbt-fine-wire-medical-braiders-herringbone-diamond-and-half-load-explained)

### What actually sets the pattern

At least three independent levers, only the first of which is carrier placement:

1. **How many carriers are mounted.** *Half load* is a standard named setup:
   half the carriers, alternating gaps, giving a one-over-one/one-under-one
   structure with better flexibility and torque (Teleflex, MMBT). The French
   *diagonal* design is the same idea — "one spindle out of 2 is mounted".
2. **Gearing ratio.** MMBT: for diamond and half-load the machine "runs at half
   speed. Horn gears turn twice per pick" — the ratio of gear rotation to
   take-up changes the interlacing, not just the braid angle.
3. **Yarns per carrier.** Two yarns in one carrier read as a 2/2 crossing.

Note a vocabulary trap for `horn_gear`: a maypole machine with N carriers has
**2N slots**, because only one of the two slots meeting at a contact may be
occupied. So the industry's *full load* is this package's 50% ceiling, and the
empty slots at full load are mechanism, not choice. *Half load* is 25% of slots.

### Maypole machine simulation (closest prior art to `horn_gear`)

- [Discrete simulation of maypole braiding machines to create collision-free
  braiding programmes](https://www.sciencedirect.com/science/article/pii/S2405844025012988)
  (2025) — enumerating collision-free carrier arrangements. Paywalled.
- [Kyosev & Gleßner, *Extended horn gears in 3D maypole braiding*](https://journals.sagepub.com/doi/full/10.1177/2515221118786741)
  (2018, open access) — horn gear arrangement, transfer places, floating length.

### Soutache

- [Soutache (Wikipedia)](https://en.wikipedia.org/wiki/Soutache) — a narrow flat
  herringbone braid "created by weaving a decorative thread around and between
  **two parallel cords**, completely covering the cores". Two cores, which is
  what `soutache_braid()` models as two `Axial` columns.

---
## Braiding machine control
https://github.com/stiganielsen/BraidOMatic
https://github.com/Brandon-Key5113/BraidyBunch
https://github.com/LJYJYN/Braiding-APP
https://pubs.rsc.org/en/content/articlelanding/2024/sm/d3sm01732j

## Braiding machine 3d printing
https://www.thingiverse.com/thing:2843159
https://github.com/manoharan-lab/arbitrary-topology-stl
https://github.com/sapphire-arches/braiding-machine
https://github.com/EricLarueMartin/FourWireBraidingMachine
https://github.com/sandy9159/DIY-mini-braiding-machine
https://github.com/tforgrave/braider_project

## Kumihimo braiding machine
https://www.youtube.com/watch?v=wdiRZvdyO5A 

## Braiding simulation
https://github.com/ElsevierSoftwareX/SOFTX-D-17-00056
https://github.com/louisepb/TexGen
