from sympy import symbols

t = symbols("t")
# Run tests with: uv run pytest /tests


# class TestProperties:
#     def test_alexander_polynomial(self, simple_braid):
#         """Test Alexander polynomial calculation"""
#         t = symbols("t")
#         poly = alexander_polynomial(Braid([1, 1, 1]))
#         assert simplify(poly - (t**2 - t + 1)) == 0
#
#     def test_conjugacy_class(self, conjugate_braids):
#         """Test conjugacy class generation"""
#         b1, b2 = conjugate_braids
#         class_b1 = conjugacy_class(b1)
#
#         # Both braids should be in each other's conjugacy class
#         assert b2 in class_b1
#
#     def test_garside_normal_form(self, simple_braid):
#         """Test Garside normal form calculation"""
#         pos, neg = garside_normal_form(simple_braid)
#         assert pos == [1, 2]
#         assert neg == [-1]
