from dataclasses import dataclass
from dataclasses import field
from typing import Union


@dataclass
class SimpleDataObject:
    field_a: int = field()
    field_b: str = field()


@dataclass
class ComplexDataObject:
    field_a: SimpleDataObject = field()
    field_b: SimpleDataObject = field()


@dataclass
class ComplexDataObject2:
    field_a: Union[SimpleDataObject, ComplexDataObject] = field()
    field_b: Union[SimpleDataObject, ComplexDataObject] = field()


@dataclass
class ComplexDataObject3:
    field_a: Union[SimpleDataObject, ComplexDataObject2] = field()
    field_b: Union[SimpleDataObject, ComplexDataObject2] = field()


def test_recursive_dataclasses():

    left = ComplexDataObject3(
        SimpleDataObject(1, "b"),
        ComplexDataObject2(
            ComplexDataObject(SimpleDataObject(3, "b"), SimpleDataObject(2, "c")),
            SimpleDataObject(2, "c"),
        ),
    )
    right = ComplexDataObject3(
        SimpleDataObject(1, "b"),
        ComplexDataObject2(
            ComplexDataObject(SimpleDataObject(1, "b"), SimpleDataObject(2, "c")),
            SimpleDataObject(3, "c"),
        ),
    )

    assert left == right
