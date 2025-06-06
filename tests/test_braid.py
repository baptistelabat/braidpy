import pytest
from math_braid.canonical_factor import CanonicalFactor

from braidpy import Braid
from sympy import symbols, Matrix

from braidpy.operations import conjugate


# Run tests with: uv run pytest /tests


class TestBraid:
    def test_init(self):
        """Test braid initialization"""

        b = Braid([], 1)
        assert b.generators == []
        assert b.n_strands == 1

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

        # Test braid with empty step
        bz = Braid([1, 2, (), -1])
        assert bz.process == [1, 2, (), -1]
        assert bz.generators == [1, 2, -1]
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

    def test_length(self):
        """Test braid length"""
        b = Braid([1, 2, -1], n_strands=3)
        assert len(b) == 3

        # Test braid length with zero generator
        b = Braid([1, 2, 0, -1], n_strands=3)
        assert len(b) == 4

    def test_hash(self):
        """Test braid hash"""
        b = Braid([1, 2, -1], n_strands=3)
        b2 = Braid([1, 2, -1], n_strands=3).inverse().inverse()
        # Test braid length with zero generator
        bz = Braid([1, 2, 0, -1], n_strands=3)
        assert hash(b) != hash(bz)
        assert hash(b) == hash(b2)

    def test_wordeq(self):
        b = Braid([1, 2, -1], n_strands=3)
        b2 = Braid([1, 2, -1], n_strands=3).inverse().inverse()
        # Test braid length with zero generator
        bz = Braid([1, 2, 0, -1], n_strands=3)
        assert b.word_eq(b2)
        assert not bz.word_eq(b)

    def test_format(self):
        """Test braid format to any word convention"""
        b = Braid([1, 2, -1], n_strands=3)
        assert b.format() == "σ₁σ₂σ₁⁻¹"
        assert (
            b.format(
                generator_symbols="abc", inverse_generator_symbols="ABC", separator="."
            )
            == "a.b.A"
        )

        """Test when introducing neutral generator"""
        b = Braid([1, 2, 0, -1], n_strands=3)
        assert b.format() == "σ₁σ₂eσ₁⁻¹"
        assert (
            b.format(
                generator_symbols="abc",
                inverse_generator_symbols="ABC",
                separator=".",
                zero_symbol="#",
            )
            == "a.b.#.A"
        )

    def test_change_notation(self):
        b = Braid([], n_strands=3)
        assert b.format_to_notation("artin") == "e"
        assert b.format_to_notation("alpha") == "#"

        b = Braid([0], n_strands=3)
        assert b.format_to_notation("artin") == "e"
        assert b.format_to_notation("alpha") == "#"
        b = Braid([1, 2, -1, -2], n_strands=3)
        assert (
            b.format_to_notation("artin")
            == "s_{1}^{1.0} s_{2}^{1.0} s_{1}^{-1.0} s_{2}^{-1.0}"
        )
        assert b.format_to_notation("alpha") == "abAB"
        assert b.format_to_notation("default") == "<1 : 2 : -1 : -2>"

        b = Braid([1, 2, -1, 0, -2], n_strands=3)
        assert (
            b.format_to_notation("artin")
            == "s_{1}^{1.0} s_{2}^{1.0} s_{1}^{-1.0} e s_{2}^{-1.0}"
        )
        assert b.format_to_notation("alpha") == "abA#B"
        assert b.format_to_notation("default") == "<1 : 2 : -1 : 0 : -2>"
        with pytest.raises(NotImplementedError):
            assert b.format_to_notation("blabla") == "<1 : 2 : -1 : 0 : -2>"

    def test_draw(self):
        Braid([1, 2, -1, 0, -2], n_strands=3).draw()

    def test_no_zero(self):
        b = Braid([1, 2, 0, -1], n_strands=3)
        assert b.no_zero().word_eq(Braid([1, 2, -1], n_strands=3))

        b = Braid([0, 0, 0], n_strands=3)
        assert b.no_zero().word_eq(Braid([], n_strands=3))

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

        # using ~ notation
        b_inv = ~b
        assert b_inv.generators == [1, -2, -1]
        assert b_inv.n_strands == 3

    def test_flip(self):
        b = Braid([1, -2], 3)
        assert b.flip().word_eq(Braid([-(3 - 1), +(3 - 2)], 3))

    def test_up_side_down(self):
        b = Braid([1, -2], 3)
        assert (-b).word_eq(Braid([-1, 2], 3))
        assert b.up_side_down().word_eq(Braid([-1, 2], 3))

    def test_pow(self):
        """Test braid power"""
        b1 = Braid([1], 3)
        assert (b1**2).word_eq(Braid([1, 1], 3))
        assert (b1**-3).word_eq(Braid([-1, -1, -1], 3))
        assert (b1**0).word_eq(Braid([], 3))

    def test_writhe(self, simple_braid):
        """Test writhe calculation"""
        b = simple_braid
        assert b.writhe() == 1  # 1 + 1 - 1 = 1

    def test_canonical_form(self):
        f = Braid([]).get_canonical_factors()
        assert f.Ai == ()
        assert f.n_half_twist == 0
        assert f.n_strands == 1

        f = Braid([2, -1]).get_canonical_factors()
        assert isinstance(f.Ai[0], CanonicalFactor)
        assert f.Ai[0].array_form == [
            1,
            0,
            2,
        ]  # This describes the permutation of first and second strands
        assert f.Ai[1].array_form == [
            0,
            2,
            1,
        ]  # This describes the permutation of second and third strands
        assert f.n_half_twist == -1
        assert f.n_strands == 3

    def test_main_generator(self):
        b = Braid([])
        assert b.main_generator is None

        b = Braid([0])
        assert b.main_generator is None

        b = Braid([1, -2])
        assert b.main_generator == 1

        b = Braid([2, -2])
        assert b.main_generator == 2

        b = Braid([2, 0, -2])
        assert b.main_generator == 2

    def test_permutations(self):
        """Test permutation calculation"""
        permutations = [
            [1, 2, 3, 4],
            [2, 1, 3, 4],
            [2, 3, 1, 4],
            [2, 3, 4, 1],
            [2, 3, 4, 1],
        ]
        assert Braid([1, 2, -3, 0]).permutations(plot=True) == permutations

        (Braid([1, -2]) ** 3).permutations(plot=True) == [1, 2, 3]

    def test_permutation(self):
        """Test permutation calculation"""
        assert Braid([1, 2, -3]).perm() == [2, 3, 4, 1]

    def test_trivial_braid(self, trivial_braid):
        """Test trivial braid properties"""
        assert trivial_braid.is_trivial()
        assert trivial_braid.perm() == [1, 2, 3]

    def test_to_matrix(self, simple_braid):
        """Test unreduced Burau matrix representation"""
        t = symbols("t")
        M = Matrix([[1 - t, t], [1, 0]])
        assert Braid([1]).to_matrix() == M
        M = Matrix([[1 - t, t, 0], [1, 0, 0], [0, 0, 1]])
        assert Braid([1], 3).to_matrix() == M

        M = Matrix([[0, 1, 0], [1 / t, 1 - 1 / t, 0], [0, 0, 1]])
        assert Braid([-1], 3).to_matrix() == M

        M = Matrix([[1, 0, 0], [0, 1 - t, t], [0, 1, 0]])
        assert Braid([2], 3).to_matrix() == M

        M = Matrix([[1, 0, 0], [0, 0, 1], [0, 1 / t, 1 - 1 / t]])
        assert Braid([-2], 3).to_matrix() == M

        # Unsure about this one
        M = Matrix([[1 - t, 0, t], [1, 0, 0], [0, 1 / t, 1 - 1 / t]])
        assert Braid([1, -2]).to_matrix() == M

    @pytest.mark.skip(
        "reduced Burau matrix definition is ambiguous, skipping for now https://github.com/sagemath/sagetrac-mirror/commit/cf4f6407517615ad3bb95bf8bf752e01949b783a"
    )
    def test_to_reduced_matrix(self, simple_braid):
        """Test unreduced Burau matrix representation
        According to https://arxiv.org/pdf/1410.0849
        """
        t = symbols("t")
        M = Matrix([[-t, t], [-1, 1 - 1 / t]])
        assert Braid([1, -2]).to_reduced_matrix() == M

    def test_to_reduced_matrix_not_implemented(self, simple_braid):
        """Test unreduced Burau matrix representation not implemented error"""
        with pytest.raises(NotImplementedError):
            Braid([1, -2]).to_reduced_matrix()

    def test_conjugate(self):
        """Test conjugacy class generation"""
        b1 = Braid([1], 3)
        b2 = Braid([2], 3)
        assert conjugate(b1, b2).word_eq(Braid([2, 1, -2], 3))

    def test_is_reduced(self):
        assert not Braid([1, -1], 3).is_reduced()
        assert (Braid([1, -2], 3) ** 3).is_reduced()
        assert (Braid([], 3) ** 3).is_reduced()

    def test_is_pure(self, pure_braid, non_pure_braid):
        """Test pure braid detection"""
        assert pure_braid.is_pure()
        assert not non_pure_braid.is_pure()

    def test_is_palindromic(self):
        assert Braid([1, 2, 1]).is_palindromic()
        assert not Braid([1, 2, 2]).is_palindromic()

    def test_is_involutive(self):
        assert Braid([1, -1]).is_involutive()

    def draw(self):
        assert Braid([1, 2, 1]).draw() == Braid([1, 2, 1])

    def test_eq(self):
        # assert math_braid.braid.Braid([])==math_braid.braid.Braid([])
        assert Braid([]) == Braid([])
        assert Braid([0]) == Braid([0])
        assert Braid([1]) == Braid([1])
        assert Braid([10]) == Braid([10])

        # Check not equal with different number of strands
        assert not Braid([1], 2) == Braid([1], 3)

        # Check with zero
        assert Braid([1, 0, 3], 4) == Braid([1, 3], 4)

        # Test the Artin relations
        # relations I:
        assert Braid([1, 3], 4) == Braid([3, 1], 4)

        # relations II (Yang-Baxter equation)
        assert Braid([1, 2, 1], 3) == Braid([2, 1, 2], 3)

        # More test taken from math-braid
        assert Braid([1, 4, 4, 1], 7) == Braid([4, -5, 1, 1, 5, 4], 7)
        assert Braid([1, 4, 4, 1], 7) != Braid([4, -5, 1, 1, 6, 4], 7)

    def test_brunnian_not_implemented(self):
        with pytest.raises(NotImplementedError):
            Braid([]).is_brunnian()
