from dataclasses import dataclass
from dataclasses import field


@dataclass
class SimpleDataObject:
    field_a: int = field()
    field_b: int = field()


@dataclass
class ComplexDataObject2:
    field_a: SimpleDataObject = field()
    field_b: SimpleDataObject = field()


@dataclass
class ComplexDataObject:
    field_a: SimpleDataObject = field()
    field_b: ComplexDataObject2 = field()


def test_recursive_dataclasses():

    left = ComplexDataObject(
        SimpleDataObject(1, "b"),
        ComplexDataObject2(SimpleDataObject(1, "b"), SimpleDataObject(2, "c"),),
    )
    right = ComplexDataObject(
        SimpleDataObject(1, "b"),
        ComplexDataObject2(SimpleDataObject(1, "b"), SimpleDataObject(3, "c"),),
    )

    assert left == right
