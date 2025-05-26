from dataclasses import dataclass


@dataclass(frozen=True)
class Strand:
    color: str
    name: str
    diameter: float


@dataclass(frozen=True)
class OrderedBraid:
    strands: list[Strand]


class FlatBraid(OrderedBraid):
    pass


class AnnulusBraid(OrderedBraid):
    pass
