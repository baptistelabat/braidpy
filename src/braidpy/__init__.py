"""
BraidPy - A Python library for working with braids

This library provides tools for representing, manipulating, and analyzing braids.
It includes support for braid operations, visualization, and mathematical properties.
"""

from .braid import Braid
from .properties import (
    alexander_polynomial as alexander_polynomial,
    conjugacy_class as conjugacy_class,
    garside_normal_form as garside_normal_form,
)
from .visualization import plot_braid as plot_braid

__all__ = ["Braid"]
