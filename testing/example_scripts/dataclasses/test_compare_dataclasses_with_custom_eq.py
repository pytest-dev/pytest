from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field


def test_dataclasses() -> None:
    @dataclass
    class SimpleDataObject:
        field_a: int = field()
        field_b: str = field()

        def __eq__(self, o: object, /) -> bool:
            return super().__eq__(o)

    left = SimpleDataObject(1, "b")
    right = SimpleDataObject(1, "c")

    assert left == right
