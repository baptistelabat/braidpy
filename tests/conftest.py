import pytest
from braidpy import Braid


@pytest.fixture
def simple_braid():
    """A simple 3-strand braid with generators [1, 2, -1]"""
    return Braid([1, 2, -1], n_strands=3)


@pytest.fixture
def trivial_braid():
    """A trivial (identity) braid"""
    return Braid([], n_strands=3)


@pytest.fixture
def pure_braid():
    """A pure braid that returns to original position"""
    return Braid([1, -1, 2, -2], n_strands=3)


@pytest.fixture
def non_pure_braid():
    """A non-pure braid that doesn't return to original position"""
    return Braid([1, 2, 1], n_strands=3)
