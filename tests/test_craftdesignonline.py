from braidpy.craftdesignonline import BraidModel

loaded_braid = BraidModel.load_from_file("tests/abok3054.b3d")

assert loaded_braid.n_threads == 17
assert type(loaded_braid.thread_states) is list
assert type(loaded_braid.steps) is list
