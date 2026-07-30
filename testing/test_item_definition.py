"""Tests for :class:`_pytest.nodes.ItemDefinition`.

The generic definition node lets a non-Python collector take part in
:hook:`pytest_generate_tests`: it declares the names it accepts, the hook
parametrizes it like any Python test, and the chosen values arrive on
``item.callspec.params``.
"""

from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


# A minimal non-Python collector: every whitespace-separated word in a ``.echo``
# file is a test definition that can be parametrized on "value".
ECHO_PLUGIN = """
from _pytest import nodes
import pytest


class EchoItem(pytest.Item):
    def __init__(self, *, spec, **kw):
        super().__init__(**kw)
        self.spec = spec

    def runtest(self):
        assert self.spec.get("value") != "bad", f"bad value in {self.name}"

    def reportinfo(self):
        return self.path, None, self.name


class EchoDefinition(nodes.ItemDefinition):
    parametrize_argnames = ("value",)

    def make_item(self, parent, *, name, callspec, nodeid, context):
        return EchoItem.from_parent(
            parent,
            name=name,
            nodeid=nodeid,
            spec=dict(callspec.params) if callspec is not None else {},
        )


class EchoFile(pytest.File):
    def collect(self):
        for word in self.path.read_text(encoding="utf-8").split():
            yield EchoDefinition.from_parent(self, name=word)


def pytest_collect_file(file_path, parent):
    if file_path.suffix == ".echo":
        return EchoFile.from_parent(parent, path=file_path)
"""


@pytest.fixture
def echo(pytester: Pytester) -> Pytester:
    pytester.makeconftest(ECHO_PLUGIN)
    pytester.makefile(".echo", things="alpha beta")
    return pytester


def test_definition_without_parametrization(echo: Pytester) -> None:
    """No parametrize() call: one item per definition, same name."""
    result = echo.runpytest("--collect-only", "-q")
    result.stdout.fnmatch_lines(["things.echo::alpha", "things.echo::beta"])
    echo.runpytest().assert_outcomes(passed=2)


def test_generate_tests_hook_parametrizes_the_definition(echo: Pytester) -> None:
    """An ordinary pytest_generate_tests impl works on a non-Python definition."""
    echo.makeconftest(
        ECHO_PLUGIN
        + """
def pytest_generate_tests(metafunc):
    if "value" in metafunc.fixturenames:
        metafunc.parametrize("value", ["good", "bad"])
"""
    )
    result = echo.runpytest("--collect-only", "-q")
    result.stdout.fnmatch_lines(
        [
            "things.echo::alpha[[]good[]]",
            "things.echo::alpha[[]bad[]]",
            "things.echo::beta[[]good[]]",
            "things.echo::beta[[]bad[]]",
        ]
    )
    result = echo.runpytest()
    result.assert_outcomes(passed=2, failed=2)
    result.stdout.fnmatch_lines(["*bad value in alpha[[]bad[]]*"])


def test_params_are_delivered_on_the_callspec(echo: Pytester) -> None:
    echo.makeconftest(
        ECHO_PLUGIN
        + """
def pytest_generate_tests(metafunc):
    metafunc.parametrize("value", ["good"])

def pytest_collection_modifyitems(items):
    for item in items:
        assert item.callspec.params == {"value": "good"}
        assert item.spec == {"value": "good"}
"""
    )
    echo.runpytest().assert_outcomes(passed=2)


def test_ids_and_marks_from_pytest_param(echo: Pytester) -> None:
    echo.makeconftest(
        ECHO_PLUGIN
        + """
import pytest

def pytest_generate_tests(metafunc):
    metafunc.parametrize(
        "value",
        [
            pytest.param("good", id="ok"),
            pytest.param("bad", marks=pytest.mark.skip(reason="nope")),
        ],
    )
"""
    )
    result = echo.runpytest("-v")
    result.assert_outcomes(passed=2, skipped=2)
    result.stdout.fnmatch_lines(["*things.echo::alpha[[]ok[]] PASSED*"])


def test_parametrize_of_undeclared_argname_is_rejected(echo: Pytester) -> None:
    echo.makeconftest(
        ECHO_PLUGIN
        + """
def pytest_generate_tests(metafunc):
    metafunc.parametrize("nope", [1])
"""
    )
    result = echo.runpytest()
    result.stdout.fnmatch_lines(
        ["*In things.echo::alpha: definition uses no argument 'nope'*"]
    )
    assert result.ret != 0


def test_parametrize_marker_on_the_definition(echo: Pytester) -> None:
    """Markers on the definition drive parametrization, as they do for Python."""
    echo.makeconftest(
        ECHO_PLUGIN
        + """
import pytest

def pytest_collectstart(collector):
    if isinstance(collector, EchoDefinition):
        collector.add_marker(pytest.mark.parametrize("value", ["good", "bad"]))
"""
    )
    result = echo.runpytest()
    result.assert_outcomes(passed=2, failed=2)


def test_item_selection_by_nodeid(echo: Pytester) -> None:
    echo.makeconftest(
        ECHO_PLUGIN
        + """
def pytest_generate_tests(metafunc):
    metafunc.parametrize("value", ["good", "bad"])
"""
    )
    result = echo.runpytest("things.echo::alpha[good]")
    result.assert_outcomes(passed=1)


def test_duplicate_parametrization_is_reported(echo: Pytester) -> None:
    echo.makeconftest(
        ECHO_PLUGIN
        + """
def pytest_generate_tests(metafunc):
    metafunc.parametrize("value", ["a"])
    metafunc.parametrize("value", ["b"])
"""
    )
    result = echo.runpytest()
    result.stdout.fnmatch_lines(["*duplicate parametrization of 'value'*"])
    assert result.ret != 0


def test_definition_node_is_a_collector(echo: Pytester) -> None:
    """The definition shows up in the tree between the file and the items."""
    result = echo.runpytest("--collect-only")
    result.stdout.fnmatch_lines(
        [
            "*<EchoFile things.echo>",
            "*<EchoDefinition alpha>",
            "*<EchoItem alpha>",
        ]
    )
