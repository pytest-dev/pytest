"""Tests for the ``"definition"`` fixture scope.

A definition-scoped fixture is shared by all the (possibly parametrized)
invocations generated from one test definition. That needs the definition to be
a node of the collection tree, i.e. :confval:`collect_function_definition` set
to something other than the default ``hidden``.
"""

from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


def _enable_definition_nodes(pytester: Pytester) -> None:
    pytester.makeini("[pytest]\ncollect_function_definition = pedantic\n")


def test_shared_between_invocations_of_one_definition(pytester: Pytester) -> None:
    """One fixture instance per definition, not per invocation."""
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        setups = []

        @pytest.fixture(scope="definition")
        def counter(request):
            setups.append(request.node.nodeid)
            return len(setups)

        @pytest.mark.parametrize("n", [1, 2, 3])
        def test_a(counter, n):
            assert counter == 1

        @pytest.mark.parametrize("n", [1, 2])
        def test_b(counter, n):
            assert counter == 2

        def test_setups_are_per_definition():
            assert setups == [
                "test_shared_between_invocations_of_one_definition.py::test_a",
                "test_shared_between_invocations_of_one_definition.py::test_b",
            ]
        """
    )
    pytester.runpytest().assert_outcomes(passed=6)


def test_torn_down_when_definition_is_left(pytester: Pytester) -> None:
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        events = []

        @pytest.fixture(scope="definition")
        def res(request):
            events.append(f"setup {request.node.name}")
            yield
            events.append(f"teardown {request.node.name}")

        @pytest.mark.parametrize("n", [1, 2])
        def test_a(res, n):
            events.append(f"test_a{n}")

        @pytest.mark.parametrize("n", [1, 2])
        def test_b(res, n):
            events.append(f"test_b{n}")

        def test_order():
            assert events == [
                "setup test_a", "test_a1", "test_a2", "teardown test_a",
                "setup test_b", "test_b1", "test_b2", "teardown test_b",
            ]
        """
    )
    pytester.runpytest().assert_outcomes(passed=5)


def test_methods_of_a_class(pytester: Pytester) -> None:
    """Each method has its own definition, the class is still shared."""
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        definition_setups = []
        class_setups = []

        @pytest.fixture(scope="definition")
        def per_definition():
            definition_setups.append(1)

        @pytest.fixture(scope="class")
        def per_class():
            class_setups.append(1)

        class TestIt:
            @pytest.mark.parametrize("n", [1, 2])
            def test_a(self, per_definition, per_class, n):
                pass

            @pytest.mark.parametrize("n", [1, 2])
            def test_b(self, per_definition, per_class, n):
                pass

        def test_counts():
            assert len(definition_setups) == 2
            assert len(class_setups) == 1
        """
    )
    pytester.runpytest().assert_outcomes(passed=5)


def test_unavailable_without_definition_nodes(pytester: Pytester) -> None:
    """In the default ``hidden`` mode there is no node to anchor the scope on."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="definition")
        def res():
            return 1

        def test_it(res):
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            "*ScopeUnavailable: fixture 'res' needs the 'definition' scope, but"
            " *::test_it has no definition node in the collection tree.",
            "*set the collect_function_definition ini option to 'pedantic'*",
        ]
    )


def test_may_request_higher_scoped_fixture(pytester: Pytester) -> None:
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="module")
        def per_module():
            return 1

        @pytest.fixture(scope="definition")
        def per_definition(per_module):
            return per_module + 1

        def test_it(per_definition):
            assert per_definition == 2
        """
    )
    pytester.runpytest().assert_outcomes(passed=1)


def test_higher_scope_may_not_request_definition_scope(pytester: Pytester) -> None:
    """Class scope is higher than definition scope, so this is a ScopeMismatch."""
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="definition")
        def per_definition():
            return 1

        @pytest.fixture(scope="class")
        def per_class(per_definition):
            return per_definition

        def test_it(per_class):
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            "*ScopeMismatch: You tried to access the definition scoped fixture"
            " per_definition with a class scoped request object*"
        ]
    )


def test_definition_scope_may_request_function_scope_fails(
    pytester: Pytester,
) -> None:
    """Function scope is lower than definition scope."""
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def per_function():
            return 1

        @pytest.fixture(scope="definition")
        def per_definition(per_function):
            return per_function

        def test_it(per_definition):
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            "*ScopeMismatch: You tried to access the function scoped fixture"
            " per_function with a definition scoped request object*"
        ]
    )


def test_setup_show_marks_the_scope(pytester: Pytester) -> None:
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="definition")
        def res():
            return 1

        @pytest.mark.parametrize("n", [1, 2])
        def test_it(res, n):
            pass
        """
    )
    result = pytester.runpytest("--setup-show")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            "        SETUP    D res",
            "*test_it[[]1[]]*",
            "*test_it[[]2[]]*",
            "        TEARDOWN D res",
        ]
    )


def test_parametrize_with_definition_scope(pytester: Pytester) -> None:
    """A definition-scoped param is set up once per value within the definition."""
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        """
        import pytest

        events = []

        @pytest.fixture
        def outer(request):
            events.append(f"setup {request.param}")
            yield request.param
            events.append(f"teardown {request.param}")

        @pytest.mark.parametrize("outer", ["a", "b"], indirect=True, scope="definition")
        @pytest.mark.parametrize("inner", [1, 2])
        def test_it(outer, inner):
            events.append(f"{outer}{inner}")

        def test_order():
            assert events == [
                "setup a", "a1", "a2", "teardown a",
                "setup b", "b1", "b2", "teardown b",
            ]
        """
    )
    pytester.runpytest().assert_outcomes(passed=5)


def test_parametrize_with_definition_scope_needs_definition_nodes(
    pytester: Pytester,
) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize("x", [1, 2], scope="definition")
        def test_it(x):
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        [
            "*ScopeUnavailable: parametrize(scope='definition') in test_it needs"
            " the 'definition' scope*"
        ]
    )


def test_unknown_scope_still_rejected(pytester: Pytester) -> None:
    """Guard against the new scope name loosening validation."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="definitions")
        def res():
            return 1

        def test_it(res):
            pass
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*got an unexpected scope value 'definitions'*"])


@pytest.mark.parametrize("scope", ["session", "package", "module", "class"])
def test_definition_scoped_fixture_may_be_requested_by_tests(
    pytester: Pytester, scope: str
) -> None:
    """A definition-scoped fixture composes with every higher scope."""
    _enable_definition_nodes(pytester)
    pytester.makepyfile(
        f"""
        import pytest

        @pytest.fixture(scope="{scope}")
        def higher():
            return "{scope}"

        @pytest.fixture(scope="definition")
        def per_definition(higher):
            return higher

        @pytest.mark.parametrize("n", [1, 2])
        def test_it(per_definition, n):
            assert per_definition == "{scope}"
        """
    )
    pytester.runpytest().assert_outcomes(passed=2)
