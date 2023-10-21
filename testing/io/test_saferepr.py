import sys
import textwrap
from collections import ChainMap
from collections import Counter
from collections import defaultdict
from collections import deque
from collections import OrderedDict
from dataclasses import dataclass
from types import MappingProxyType
from types import SimpleNamespace

import pytest
from _pytest._io.saferepr import _pformat_dispatch
from _pytest._io.saferepr import DEFAULT_REPR_MAX_SIZE
from _pytest._io.saferepr import saferepr
from _pytest._io.saferepr import saferepr_unlimited


def test_simple_repr():
    assert saferepr(1) == "1"
    assert saferepr(None) == "None"


def test_maxsize():
    s = saferepr("x" * 50, maxsize=25)
    assert len(s) == 25
    expected = repr("x" * 10 + "..." + "x" * 10)
    assert s == expected


def test_no_maxsize():
    text = "x" * DEFAULT_REPR_MAX_SIZE * 10
    s = saferepr(text, maxsize=None)
    expected = repr(text)
    assert s == expected


def test_maxsize_error_on_instance():
    class A:
        def __repr__(self):
            raise ValueError("...")

    s = saferepr(("*" * 50, A()), maxsize=25)
    assert len(s) == 25
    assert s[0] == "(" and s[-1] == ")"


def test_exceptions() -> None:
    class BrokenRepr:
        def __init__(self, ex):
            self.ex = ex

        def __repr__(self):
            raise self.ex

    class BrokenReprException(Exception):
        __str__ = None  # type: ignore[assignment]
        __repr__ = None  # type: ignore[assignment]

    assert "Exception" in saferepr(BrokenRepr(Exception("broken")))
    s = saferepr(BrokenReprException("really broken"))
    assert "TypeError" in s
    assert "TypeError" in saferepr(BrokenRepr("string"))

    none = None
    try:
        none()  # type: ignore[misc]
    except BaseException as exc:
        exp_exc = repr(exc)
    obj = BrokenRepr(BrokenReprException("omg even worse"))
    s2 = saferepr(obj)
    assert s2 == (
        "<[unpresentable exception ({!s}) raised in repr()] BrokenRepr object at 0x{:x}>".format(
            exp_exc, id(obj)
        )
    )


def test_baseexception():
    """Test saferepr() with BaseExceptions, which includes pytest outcomes."""

    class RaisingOnStrRepr(BaseException):
        def __init__(self, exc_types):
            self.exc_types = exc_types

        def raise_exc(self, *args):
            try:
                self.exc_type = self.exc_types.pop(0)
            except IndexError:
                pass
            if hasattr(self.exc_type, "__call__"):
                raise self.exc_type(*args)
            raise self.exc_type

        def __str__(self):
            self.raise_exc("__str__")

        def __repr__(self):
            self.raise_exc("__repr__")

    class BrokenObj:
        def __init__(self, exc):
            self.exc = exc

        def __repr__(self):
            raise self.exc

        __str__ = __repr__

    baseexc_str = BaseException("__str__")
    obj = BrokenObj(RaisingOnStrRepr([BaseException]))
    assert saferepr(obj) == (
        "<[unpresentable exception ({!r}) "
        "raised in repr()] BrokenObj object at 0x{:x}>".format(baseexc_str, id(obj))
    )
    obj = BrokenObj(RaisingOnStrRepr([RaisingOnStrRepr([BaseException])]))
    assert saferepr(obj) == (
        "<[{!r} raised in repr()] BrokenObj object at 0x{:x}>".format(
            baseexc_str, id(obj)
        )
    )

    with pytest.raises(KeyboardInterrupt):
        saferepr(BrokenObj(KeyboardInterrupt()))

    with pytest.raises(SystemExit):
        saferepr(BrokenObj(SystemExit()))

    with pytest.raises(KeyboardInterrupt):
        saferepr(BrokenObj(RaisingOnStrRepr([KeyboardInterrupt])))

    with pytest.raises(SystemExit):
        saferepr(BrokenObj(RaisingOnStrRepr([SystemExit])))

    with pytest.raises(KeyboardInterrupt):
        print(saferepr(BrokenObj(RaisingOnStrRepr([BaseException, KeyboardInterrupt]))))

    with pytest.raises(SystemExit):
        saferepr(BrokenObj(RaisingOnStrRepr([BaseException, SystemExit])))


def test_buggy_builtin_repr():
    # Simulate a case where a repr for a builtin raises.
    # reprlib dispatches by type name, so use "int".

    class int:
        def __repr__(self):
            raise ValueError("Buggy repr!")

    assert "Buggy" in saferepr(int())


def test_big_repr():
    from _pytest._io.saferepr import SafeRepr

    assert len(saferepr(range(1000))) <= len("[" + SafeRepr(0).maxlist * "1000" + "]")


def test_repr_on_newstyle() -> None:
    class Function:
        def __repr__(self):
            return "<%s>" % (self.name)  # type: ignore[attr-defined]

    assert saferepr(Function())


def test_unicode():
    val = "£€"
    reprval = "'£€'"
    assert saferepr(val) == reprval


def test_pformat_dispatch():
    assert _pformat_dispatch("a") == "'a'"
    assert _pformat_dispatch("a" * 10, width=5) == "'aaaaaaaaaa'"
    assert _pformat_dispatch("foo bar", width=5) == "('foo '\n 'bar')"


def test_broken_getattribute():
    """saferepr() can create proper representations of classes with
    broken __getattribute__ (#7145)
    """

    class SomeClass:
        def __getattribute__(self, attr):
            raise RuntimeError

        def __repr__(self):
            raise RuntimeError

    assert saferepr(SomeClass()).startswith(
        "<[RuntimeError() raised in repr()] SomeClass object at 0x"
    )


def test_saferepr_unlimited():
    dict5 = {f"v{i}": i for i in range(5)}
    assert saferepr_unlimited(dict5) == "{'v0': 0, 'v1': 1, 'v2': 2, 'v3': 3, 'v4': 4}"

    dict_long = {f"v{i}": i for i in range(1_000)}
    r = saferepr_unlimited(dict_long)
    assert "..." not in r
    assert "\n" not in r


def test_saferepr_unlimited_exc():
    class A:
        def __repr__(self):
            raise ValueError(42)

    assert saferepr_unlimited(A()).startswith(
        "<[ValueError(42) raised in repr()] A object at 0x"
    )


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
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 10),
                    reason="Not supported before python3.10",
                )
            ],
        ),
        pytest.param(
            DataclassWithOneItem(foo="bar"),
            """
            DataclassWithOneItem(
                foo='bar',
            )
            """,
            id="dataclass-one-item",
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 10),
                    reason="Not supported before python3.10",
                )
            ],
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
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 10),
                    reason="Not supported before python3.10",
                )
            ],
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
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 9),
                    reason="Not supported before python3.9",
                )
            ],
        ),
        pytest.param(
            SimpleNamespace(one=1),
            """
            namespace(
                one=1,
            )
            """,
            id="simplenamespace-one-item",
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 10),
                    reason="Different format before python3.10",
                )
            ],
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
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 10),
                    reason="Different format before python3.10",
                )
            ],
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
            marks=[
                pytest.mark.skipif(
                    sys.version_info[:2] < (3, 10),
                    reason="Not supported before python3.10",
                )
            ],
        ),
    ),
)
def test_consistent_pretty_printer(data, expected):
    assert _pformat_dispatch(data) == textwrap.dedent(expected).strip()
