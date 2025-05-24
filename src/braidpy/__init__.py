"""
BraidPy - A Python library for working with braids

This library provides tools for representing, manipulating, and analyzing braids.
It includes support for braid operations, visualization, and mathematical properties.
"""

from .braid import Braid
from .operations import multiply, conjugate, power
from .properties import *
from .visualization import *

__all__ = ["Braid"]
