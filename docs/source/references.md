# 🧶 Braid Group: Code Resources, Visualizations & Research

## 📘 General background wikis on braid theory

- [Braid on Wikipedia](https://en.wikipedia.org/wiki/Braid)
- [Braid group on Wikipedia](https://en.wikipedia.org/wiki/Braid_group)
- https://ncatlab.org/nlab/show/braid+group
- https://www.labri.fr/perso/marckert/poulalhon.pdf
- https://homepages.math.uic.edu/~jaca2009/notes/Meneses.pdf Maybe one of the best paper which is describing some
relationships between algebraic and geometric braid

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
---

## 📊 MATLAB / BraidLab
- [Braidlab PDF Guide](https://github.com/jeanluct/braidlab/blob/master/doc/braidlab_guide.pdf) which was published [arXiv:1410.0849 – Braidlab paper](https://arxiv.org/pdf/1410.0849)  
  - Matlab code is available [jeanluct/braidlab](https://github.com/jeanluct/braidlab)
  - Probably the best introduction to computation with braids
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

