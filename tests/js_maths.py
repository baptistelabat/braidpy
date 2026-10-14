# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The maths library as a Python port of a web/ script is given to check it
bead for bead against the JavaScript (tests/js/rounded.js): every result of
cos, sin, atan2 and asin rounded to single precision, as there, and
JavaScript's own ``Math.hypot``."""

import math
import struct
import types


def single(x):
    """x rounded to single precision, as JavaScript's ``Math.fround``."""
    return struct.unpack("f", struct.pack("f", x))[0]


def js_hypot(*values):
    """JavaScript's ``Math.hypot`` as V8 computes it: scaled by the largest,
    the squares summed with Kahan's compensation.  Not always correctly
    rounded, as Python's is; here only so that a port can be given the very
    numbers the JavaScript computes."""
    largest = max((abs(v) for v in values), default=0.0)
    if largest == 0:
        return 0.0
    total = compensation = 0.0
    for v in values:
        n = abs(v) / largest
        summand = n * n - compensation
        preliminary = total + summand
        compensation = (preliminary - total) - summand
        total = preliminary
    return math.sqrt(total) * largest


def rounded_math():
    """``math``, as the JavaScript rounded by tests/js/rounded.js has it."""
    rounded = types.SimpleNamespace(
        **{k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    )
    for name in ("cos", "sin", "atan2", "asin"):
        exact = getattr(math, name)
        setattr(rounded, name, lambda *a, f=exact: single(f(*a)))
    rounded.hypot = js_hypot
    return rounded
