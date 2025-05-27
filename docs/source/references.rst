https://en.wikipedia.org/wiki/Braid_group

The largest piece of program I found is probably in Sage Math
However, due to GPL licensing, it is not planned to use here, but reading it might be very useful
https://doc.sagemath.org/html/en/reference/groups/sage/groups/braid.html

Visualization
----------------
https://pypi.org/project/braidvisualiser/
https://github.com/rexgreenway/braid-visualiser -> available on pypi, using this one for flat visualization
https://github.com/Denbox/Braid-Group-Visualization/blob/master/braid_visualization.py -> flat but poor crossing visualization
https://texdoc.org/serve/braids/0 -> package to draw braids in latex ! Quite impressive parametrization, might be good for documentation
https://github.com/loopspace/braids -> link to braid in latex repo

https://pypi.org/project/braidpy/ -> or own library !

Dehornoy: researcher and author of book "Le calcul des tresses". He gave several algorithms (handle reduction)
----------------
"Patrick Dehorney: A Fast Method for Comparing Braids."
https://dehornoy.lmno.cnrs.fr/programs.html -> Some old Pascal code
https://github.com/dehornoy/programs -> Original Pascal code in Docker
https://github.com/abhikpal/dehornoy -> handle reduction implemented by an indian student in Python
https://github.com/chesterelian/dehornoy --> obscur c++ program implementing handle reduction
https://github.com/jfromentin/gbraids --> Research on braid group with n=4. GPL/C++
    Handle reduction
    DynnikovCoordinates
    Dual generator
https://pure.tue.nl/ws/portalfiles/portal/67742824/630595-1.pdf -> a math paper on the way of Dehornoy


Github
----------------
https://pypi.org/project/math-braid
https://github.com/kuboon/math_braid.py -> python library available on pypi and implementing serious math. Let's test it
Last update 6 years ago. Documentation is scarce. No licence, so probably possible to use with wrapper or to move code in repo
# Artin generation. num should be from 1 to 3
Braid([1,2,3], 4)

# Band generation. num should be from 1 to 4
b = Braid([[3,1], [1,2]], 4); b
https://github.com/sagemath/sage/blob/develop/src/sage/groups/braid.py -> very good resource but GPL and sage is not usable in python
https://github.com/rexgreenway/alexander-data -> package to compute braid invariant but not available on pypi
https://github.com/leodana/TIPE/blob/master/programmes%20tresses.py

Matlab
----------------

Nice ressources with nice documentation implementing a variety of element, this library could host
https://arxiv.org/pdf/1410.0849
https://github.com/jeanluct/braidlab
https://github.com/jeanluct/braidlab/blob/master/doc/braidlab_guide.pdf

Knots
----------------
To go further (and some function of braids are used for knots).
https://github.com/Algebra8/Knots -> This project is named braidgenerator on pypi but not really interesting
https://algebra8.github.io/braidgenerator_doc.github.io/ -> Nice doc however

https://pypi.org/project/pyknotid/
https://github.com/SPOCKnots/pyknotid -> enable to create a knot from a braid word and do visualization and complex operations
https://github.com/SPOCKnots/pyknotid/blob/4d248ff32712702530e458b9dfa276038a5e61b2/pyknotid/spacecurves/spacecurve.py#L286

https://github.com/xcapaldi/tbkm -> random braid visualization in terminal
https://github.com/RafaelMri/Pyknots -> contains a step by step handle reduction algorithm
https://github.com/RafaelMri/Pyknots/blob/10254b7ea36e67544bf6867f88bad85b872ffa75/modules/braids.py#L11

https://www.youtube.com/watch?v=8DBhTXM_Br4

