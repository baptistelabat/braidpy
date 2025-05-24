import pytest
from braidpy import Braid, conjugate, power
from sympy import symbols, Matrix


# Run tests with: uv run pytest /tests


class TestBraid:
    def test_init(self):
        """Test braid initialization"""
        b = Braid([1, 2, -1], n_strands=3)
        assert b.generators == [1, 2, -1]
        assert b.n_strands == 3

        # Test generator inference
        b2 = Braid([1, 2, -1])
        assert b2.n_strands == 3

        # Test braid with zero generator
        bz = Braid([1, 2, 0, -1])
        assert bz.generators == [1, 2, 0, -1]
        assert bz.n_strands == 3

        # Test invalid generator
        with pytest.raises(ValueError):
            Braid([1, 3], n_strands=2)

    def test_repr(self):
        """Test braid representation"""
        b = Braid([1, 2, -1], n_strands=3)
        assert repr(b) == "Braid([1, 2, -1], n_strands=3)"

        # Test braid representation with zero generator
        b = Braid([1, 2, 0, -1], n_strands=3)
        assert repr(b) == "Braid([1, 2, 0, -1], n_strands=3)"

    def test_multiplication(self, simple_braid):
        """Test braid multiplication"""
        b = simple_braid
        b_squared = b * b
        assert b_squared.generators == [1, 2, -1, 1, 2, -1]
        assert b_squared.n_strands == 3

        # Test multiplication with different number of strands
        with pytest.raises(ValueError):
            b * Braid([1, 2, -1], n_strands=4)

    def test_inverse(self, simple_braid):
        """Test braid inverse"""
        b = simple_braid
        b_inv = b.inverse()
        assert b_inv.generators == [1, -2, -1]
        assert b_inv.n_strands == 3

    def test_pow(self):
        """Test braid power"""
        b1 = Braid([1], 3)
        assert (b1**2).word_eq(Braid([1, 1], 3))


    def test_writhe(self, simple_braid):
        """Test writhe calculation"""
        b = simple_braid
        assert b.writhe() == 1  # 1 + 1 - 1 = 1

    def test_permutation(self):
        """Test permutation calculation"""
        assert Braid([1, 2, - 3]).perm() == [2, 3, 4, 1]

    def test_trivial_braid(self, trivial_braid):
        """Test trivial braid properties"""
        assert trivial_braid.is_trivial()
        assert trivial_braid.perm() == [1, 2, 3]

    def test_to_matrix(self, simple_braid):
        """Test unreduced Burau matrix representation"""
        t = symbols('t')
        M = Matrix([
            [1 - t, t],
            [1, 0]
        ])
        assert Braid ([1]).to_matrix() == M
        M = Matrix([
            [1 - t, t, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])
        assert Braid([1], 3).to_matrix() == M


        M = Matrix([
        [  0,       1, 0],
        [1/t, 1 - 1/t, 0],
        [  0,       0, 1]])
        assert Braid ([-1],3).to_matrix() == M

        M = Matrix([
        [1,     0, 0],
        [0, 1 - t, t],
        [0,     1, 0]])
        assert Braid([2], 3).to_matrix() == M

        M = Matrix([
        [1,   0,         0],
        [0,   0,         1],
        [0, 1/t, 1 - 1/t]])
        assert Braid([-2], 3).to_matrix() == M

        # Unsure about this one
        M = Matrix([
        [1 - t,   0,       t],
        [    1,   0,       0],
        [    0, 1/t, 1 - 1/t]])
        assert Braid ([1, -2]).to_matrix() == M

    def test_to_reduced_matrix(self, simple_braid):
        """Test unreduced Burau matrix representation
        According to https://arxiv.org/pdf/1410.0849
        """
        t = symbols('t')
        M = Matrix([
            [-t, t],
            [-1, 1-1/t]])
        # assert Braid([1, -2]).to_reduced_matrix()==M

    def test_conjugate(self):
        """Test conjugacy class generation"""
        b1 = Braid([1], 3)
        b2 = Braid([2], 3)
        assert conjugate(b1,b2).word_eq(Braid([2, 1, -2], 3))

    def test_power(self):
        """Test conjugacy class generation"""
        b1 = Braid([1], 3)
        assert power(b1, 2).word_eq(Braid([1, 1], 3))

    def test_is_pure(self, pure_braid, non_pure_braid):
        """Test pure braid detection"""
        assert pure_braid.is_pure()
        assert not non_pure_braid.is_pure()

