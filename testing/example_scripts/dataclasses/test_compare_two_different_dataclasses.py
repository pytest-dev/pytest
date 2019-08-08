from dataclasses import dataclass
from dataclasses import field


def test_comparing_two_different_data_classes():
    @dataclass
    class SimpleDataObjectOne:
        field_a: int = field()
        field_b: int = field()

    @dataclass
    class SimpleDataObjectTwo:
        field_a: int = field()
        field_b: int = field()

    left = SimpleDataObjectOne(1, "b")
    right = SimpleDataObjectTwo(1, "c")

    assert left != right
