from __future__ import annotations

from collections import ChainMap
from collections import Counter
from collections import defaultdict
from collections import deque
from collections import OrderedDict
from dataclasses import dataclass
import textwrap
from types import MappingProxyType
from types import SimpleNamespace
from typing import Any

from _pytest._io.pprint import PrettyPrinter
import pytest


@dataclass
class EmptyDataclass:
    pass


@dataclass
class DataclassWithOneItem:
    foo: str


@dataclass
class DataclassWithTwoItems:
    foo: str
    bar: str


@pytest.mark.parametrize(
    ("data", "expected"),
    (
        pytest.param(
            EmptyDataclass(),
            "EmptyDataclass()",
            id="dataclass-empty",
        ),
        pytest.param(
            DataclassWithOneItem(foo="bar"),
            """
            DataclassWithOneItem(
                foo='bar',
            )
            """,
            id="dataclass-one-item",
        ),
        pytest.param(
            DataclassWithTwoItems(foo="foo", bar="bar"),
            """
            DataclassWithTwoItems(
                foo='foo',
                bar='bar',
            )
            """,
            id="dataclass-two-items",
        ),
        pytest.param(
            {},
            "{}",
            id="dict-empty",
        ),
        pytest.param(
            {"one": 1},
            """
            {
                'one': 1,
            }
            """,
            id="dict-one-item",
        ),
        pytest.param(
            {"one": 1, "two": 2},
            """
            {
                'one': 1,
                'two': 2,
            }
            """,
            id="dict-two-items",
        ),
        pytest.param(OrderedDict(), "OrderedDict()", id="ordereddict-empty"),
        pytest.param(
            OrderedDict({"one": 1}),
            """
            OrderedDict({
                'one': 1,
            })
            """,
            id="ordereddict-one-item",
        ),
        pytest.param(
            OrderedDict({"one": 1, "two": 2}),
            """
            OrderedDict({
                'one': 1,
                'two': 2,
            })
            """,
            id="ordereddict-two-items",
        ),
        pytest.param(
            [],
            "[]",
            id="list-empty",
        ),
        pytest.param(
            [1],
            """
            [
                1,
            ]
            """,
            id="list-one-item",
        ),
        pytest.param(
            [1, 2],
            """
            [
                1,
                2,
            ]
            """,
            id="list-two-items",
        ),
        pytest.param(
            tuple(),
            "()",
            id="tuple-empty",
        ),
        pytest.param(
            (1,),
            """
            (
                1,
            )
            """,
            id="tuple-one-item",
        ),
        pytest.param(
            (1, 2),
            """
            (
                1,
                2,
            )
            """,
            id="tuple-two-items",
        ),
        pytest.param(
            set(),
            "set()",
            id="set-empty",
        ),
        pytest.param(
            {1},
            """
            {
                1,
            }
            """,
            id="set-one-item",
        ),
        pytest.param(
            {1, 2},
            """
            {
                1,
                2,
            }
            """,
            id="set-two-items",
        ),
        pytest.param(
            MappingProxyType({}),
            "mappingproxy({})",
            id="mappingproxy-empty",
        ),
        pytest.param(
            MappingProxyType({"one": 1}),
            """
            mappingproxy({
                'one': 1,
            })
            """,
            id="mappingproxy-one-item",
        ),
        pytest.param(
            MappingProxyType({"one": 1, "two": 2}),
            """
            mappingproxy({
                'one': 1,
                'two': 2,
            })
            """,
            id="mappingproxy-two-items",
        ),
        pytest.param(
            SimpleNamespace(),
            "namespace()",
            id="simplenamespace-empty",
        ),
        pytest.param(
            SimpleNamespace(one=1),
            """
            namespace(
                one=1,
            )
            """,
            id="simplenamespace-one-item",
        ),
        pytest.param(
            SimpleNamespace(one=1, two=2),
            """
            namespace(
                one=1,
                two=2,
            )
            """,
            id="simplenamespace-two-items",
        ),
        pytest.param(
            defaultdict(str), "defaultdict(<class 'str'>, {})", id="defaultdict-empty"
        ),
        pytest.param(
            defaultdict(str, {"one": "1"}),
            """
            defaultdict(<class 'str'>, {
                'one': '1',
            })
            """,
            id="defaultdict-one-item",
        ),
        pytest.param(
            defaultdict(str, {"one": "1", "two": "2"}),
            """
            defaultdict(<class 'str'>, {
                'one': '1',
                'two': '2',
            })
            """,
            id="defaultdict-two-items",
        ),
        pytest.param(
            Counter(),
            "Counter()",
            id="counter-empty",
        ),
        pytest.param(
            Counter("1"),
            """
            Counter({
                '1': 1,
            })
            """,
            id="counter-one-item",
        ),
        pytest.param(
            Counter("121"),
            """
            Counter({
                '1': 2,
                '2': 1,
            })
            """,
            id="counter-two-items",
        ),
        pytest.param(ChainMap(), "ChainMap({})", id="chainmap-empty"),
        pytest.param(
            ChainMap({"one": 1, "two": 2}),
            """
            ChainMap(
                {
                    'one': 1,
                    'two': 2,
                },
            )
            """,
            id="chainmap-one-item",
        ),
        pytest.param(
            ChainMap({"one": 1}, {"two": 2}),
            """
            ChainMap(
                {
                    'one': 1,
                },
                {
                    'two': 2,
                },
            )
            """,
            id="chainmap-two-items",
        ),
        pytest.param(
            deque(),
            "deque([])",
            id="deque-empty",
        ),
        pytest.param(
            deque([1]),
            """
            deque([
                1,
            ])
            """,
            id="deque-one-item",
        ),
        pytest.param(
            deque([1, 2]),
            """
            deque([
                1,
                2,
            ])
            """,
            id="deque-two-items",
        ),
        pytest.param(
            deque([1, 2], maxlen=3),
            """
            deque(maxlen=3, [
                1,
                2,
            ])
            """,
            id="deque-maxlen",
        ),
        pytest.param(
            {
                "chainmap": ChainMap({"one": 1}, {"two": 2}),
                "counter": Counter("122"),
                "dataclass": DataclassWithTwoItems(foo="foo", bar="bar"),
                "defaultdict": defaultdict(str, {"one": "1", "two": "2"}),
                "deque": deque([1, 2], maxlen=3),
                "dict": {"one": 1, "two": 2},
                "list": [1, 2],
                "mappingproxy": MappingProxyType({"one": 1, "two": 2}),
                "ordereddict": OrderedDict({"one": 1, "two": 2}),
                "set": {1, 2},
                "simplenamespace": SimpleNamespace(one=1, two=2),
                "tuple": (1, 2),
            },
            """
            {
                'chainmap': ChainMap(
                    {
                        'one': 1,
                    },
                    {
                        'two': 2,
                    },
                ),
                'counter': Counter({
                    '2': 2,
                    '1': 1,
                }),
                'dataclass': DataclassWithTwoItems(
                    foo='foo',
                    bar='bar',
                ),
                'defaultdict': defaultdict(<class 'str'>, {
                    'one': '1',
                    'two': '2',
                }),
                'deque': deque(maxlen=3, [
                    1,
                    2,
                ]),
                'dict': {
                    'one': 1,
                    'two': 2,
                },
                'list': [
                    1,
                    2,
                ],
                'mappingproxy': mappingproxy({
                    'one': 1,
                    'two': 2,
                }),
                'ordereddict': OrderedDict({
                    'one': 1,
                    'two': 2,
                }),
                'set': {
                    1,
                    2,
                },
                'simplenamespace': namespace(
                    one=1,
                    two=2,
                ),
                'tuple': (
                    1,
                    2,
                ),
            }
            """,
            id="deep-example",
        ),
    ),
)
def test_consistent_pretty_printer(data: Any, expected: str) -> None:
    assert PrettyPrinter().pformat(data) == textwrap.dedent(expected).strip()


class TestPformatLines:
    """``pformat_lines`` returns the pretty-printed lines, pulling from
    the lazy formatter only until a line/char budget is reached so an
    input a downstream truncator will clip anyway is never fully built.
    """

    def test_no_budget_matches_pformat_splitlines(self) -> None:
        pp = PrettyPrinter()
        data = list(range(50))
        assert pp.pformat_lines(data) == pp.pformat(data).splitlines()

    def test_under_budget_is_complete_and_a_prefix(self) -> None:
        # When the whole thing fits, the result is the full pformat,
        # regardless of how the budget was reached.
        pp = PrettyPrinter()
        data = list(range(5))
        full = pp.pformat(data).splitlines()
        assert pp.pformat_lines(data, max_lines=11) == full
        assert pp.pformat_lines(data, max_chars=10_000) == full

    def test_line_budget_stops_early(self) -> None:
        pp = PrettyPrinter()
        # 50 scalars, one per line, budget well below 50.
        full = pp.pformat(list(range(50))).splitlines()
        lines = pp.pformat_lines(list(range(50)), max_lines=11)
        assert len(lines) <= 11 + 1  # budget, plus a trailing partial line
        # everything but the last line (which may stop mid-line) is a
        # prefix of the full output
        assert lines[:-1] == full[: len(lines) - 1]

    def test_char_budget_stops_early(self) -> None:
        # A *flat* container of huge strings has few lines but explodes on
        # chars; a line-only budget wouldn't stop it. The char budget must.
        pp = PrettyPrinter()
        data = ["x" * 100_000, "y" * 100_000, "z" * 100_000]
        lines = pp.pformat_lines(data, max_chars=640)
        assert sum(len(line) for line in lines) < 200_000  # bailed, didn't format all 3

    def test_nested_element_respects_line_budget(self) -> None:
        # ``len(object)`` is only a *lower* bound on the line count: a
        # single nested element expands to many lines. The lazy pull must
        # stop regardless of the container's element count.
        pp = PrettyPrinter()
        for data in ([{i: "x" * 40 for i in range(50)}], {1: list(range(100))}):
            lines = pp.pformat_lines(data, max_lines=11)
            assert len(lines) <= 11 + 1

    def test_nested_dataclass_element_respects_line_budget(self) -> None:
        @dataclass
        class Many:
            a: int
            b: int
            c: int
            d: int
            e: int
            f: int
            g: int
            h: int

        pp = PrettyPrinter()
        lines = pp.pformat_lines([Many(*range(8))], max_lines=4)
        assert len(lines) <= 4 + 1
        assert len(lines) < len(pp.pformat([Many(*range(8))]).splitlines())

    def test_sized_non_iterable_does_not_raise(self) -> None:
        class Sized:
            def __len__(self) -> int:
                return 3  # pragma: no cover - exists only to make the type Sized

        pp = PrettyPrinter()
        obj = Sized()
        assert pp.pformat_lines(obj, max_lines=5) == pp.pformat(obj).splitlines()


def test_pformat_sorts_heterogeneous_set() -> None:
    # The set sort tries a natural sort first and falls back to a key
    # that compares the element types' names only for unorderable
    # mixes; both must succeed.
    pp = PrettyPrinter()
    assert pp.pformat({3, 1, 2}) == "{\n    1,\n    2,\n    3,\n}"
    # Mixed unorderable types must not raise; the fallback orders by type
    # name (ints before strs), then by value.
    assert pp.pformat({1, "a", 2, "b"}) == "{\n    1,\n    2,\n    'a',\n    'b',\n}"
