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


def test_dict_preserves_insertion_order() -> None:
    """Test that dictionary keys maintain insertion order, not alphabetical.

    Relates to issue #13503 - dicts should preserve insertion order
    since Python 3.7+, not sort alphabetically.
    """
    # Create dict with non-alphabetical insertion order
    d = {}
    d["z"] = 1
    d["a"] = 2
    d["m"] = 3

    result = PrettyPrinter().pformat(d)

    # Verify the keys appear in insertion order (z, a, m)
    z_pos = result.index("'z'")
    a_pos = result.index("'a'")
    m_pos = result.index("'m'")

    # z should appear before a, and a before m
    assert z_pos < a_pos < m_pos, (
        f"Expected insertion order z<a<m, got positions: z={z_pos}, a={a_pos}, m={m_pos}"
    )

    # Also verify expected format
    expected = textwrap.dedent("""
    {
        'z': 1,
        'a': 2,
        'm': 3,
    }
    """).strip()
    assert result == expected


def test_dict_insertion_order_with_depth() -> None:
    """Test dict insertion order in _safe_repr (used with maxlevels/depth).
    
    This test ensures the _safe_repr method also preserves insertion order
    when it formats dicts at maximum depth levels.
    """
    # Create nested dict structure with non-alphabetical keys
    d = {"z": {"inner": 1}, "a": {"inner": 2}, "m": {"inner": 3}}
    
    # Use depth parameter to trigger _safe_repr path
    pp = PrettyPrinter(depth=1)
    result = pp.pformat(d)
    
    # Verify insertion order is preserved (z before a before m)
    z_pos = result.index("'z'")
    a_pos = result.index("'a'")
    m_pos = result.index("'m'")
    assert z_pos < a_pos < m_pos, (
        f"Expected insertion order z<a<m in _safe_repr, got: z={z_pos}, a={a_pos}, m={m_pos}"
    )
