"""
Tests for fixture functionality covering setup-teardown ordering of fixtures, including
parametrized fixtures and dynamically requested fixtures.
"""

from __future__ import annotations

from _pytest.pytester import Pytester
import pytest


def test_getfixturevalue_parametrized_dependency_tracked(pytester: Pytester) -> None:
    """
    Test that a fixture depending on a parametrized fixture via getfixturevalue
    is properly recomputed when the parametrized fixture changes (#14103).
    """
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.fixture(scope="session")
        def bar(request):
            return request.getfixturevalue("foo")

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_first(foo, bar):
            assert bar == 1

        @pytest.mark.parametrize("foo", [2], indirect=True)
        def test_second(foo, bar):
            assert bar == 2
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_first[1] ",
            "SETUP    S foo[1]",
            "SETUP    S bar (fixtures used: foo)",
            "        *test_first*",
            "TEARDOWN S bar",
            "TEARDOWN S foo[1]",
            "test_fixtures.py::test_second[2] ",
            "SETUP    S foo[2]",
            "SETUP    S bar (fixtures used: foo)",
            "        *test_second*",
            "TEARDOWN S bar",
            "TEARDOWN S foo[2]",
        ],
        consecutive=True,
    )


@pytest.mark.xfail(reason="#14095")
def test_fixture_override_finishes_dependencies(pytester: Pytester) -> None:
    """Test that a fixture gets recomputed if its dependency resolves to a different fixturedef (#14095)."""
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo():
            return "outer"

        @pytest.fixture(scope="session")
        def bar(foo):
            return f"dependent_{foo}"

        @pytest.fixture(scope="session")
        def baz(bar):
            return bar

        def test_before_class(baz):
            assert baz == "dependent_outer"

        class TestOverride:
            @pytest.fixture(scope="session")
            def foo(self):
                return "inner"

            def test_in_class(self, baz):
                assert baz == "dependent_inner"

        def test_after_class(baz):
            assert baz == "dependent_outer"
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=3)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_before_class ",
            "SETUP    S foo",
            "SETUP    S bar (fixtures used: foo)",
            "SETUP    S baz (fixtures used: bar)",
            "        *test_before_class*",
            "test_fixtures.py::TestOverride::test_in_class ",
            # baz and bar are recomputed because foo resolves to a different fixturedef.
            "TEARDOWN S baz",
            "TEARDOWN S bar",
            "SETUP    S foo",  # The inner foo.
            "SETUP    S bar (fixtures used: foo)",
            "SETUP    S baz (fixtures used: bar)",
            "        *test_in_class*",
            "test_fixtures.py::test_after_class ",
            # baz and bar are recomputed because foo resolves to a different fixturedef.
            "TEARDOWN S baz",
            "TEARDOWN S bar",
            "SETUP    S bar (fixtures used: foo)",
            "SETUP    S baz (fixtures used: bar)",
            "        *test_after_class*",
            "TEARDOWN S baz",
            "TEARDOWN S bar",
            "TEARDOWN S foo",
            "TEARDOWN S foo",
        ],
        consecutive=True,
    )


def test_override_fixture_with_new_parametrized_fixture(pytester: Pytester) -> None:
    """Test what happens when a cached fixture is overridden by a new parametrized fixture,
    and another fixture depends on it.

    This test verifies that:
    1. A fixture can be overridden by a parametrized fixture in a nested scope
    2. Dependent fixtures get recomputed because a dependency now resolves to a different fixturedef
    3. The outer fixture is not setup or finalized unnecessarily
    """
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            assert not hasattr(request, "param")
            return "outer"

        @pytest.fixture(scope="session")
        def bar(foo):
            return f"dependent_{foo}"

        def test_before_class(foo, bar):
            assert foo == "outer"
            assert bar == "dependent_outer"

        class TestOverride:
            @pytest.fixture(scope="session")
            def foo(self, request):
                return f"inner_{request.param}"

            @pytest.mark.parametrize("foo", [1], indirect=True)
            def test_in_class(self, foo, bar):
                assert foo == "inner_1"
                assert bar == "dependent_inner_1"
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_before_class ",
            "SETUP    S foo",
            "SETUP    S bar (fixtures used: foo)",
            "        test_fixtures.py::test_before_class (fixtures used: bar, foo, request)PASSED",
            "TEARDOWN S bar",
            "TEARDOWN S foo",
            "test_fixtures.py::TestOverride::test_in_class[1] ",
            "SETUP    S foo[1]",
            "SETUP    S bar (fixtures used: foo)",
            "        test_fixtures.py::TestOverride::test_in_class[1] (fixtures used: bar, foo, request)PASSED",
            "TEARDOWN S bar",
            "TEARDOWN S foo[1]",
        ],
        consecutive=True,
    )


def test_fixture_post_finalizer_hook_exception(pytester: Pytester) -> None:
    """Test that exceptions in pytest_fixture_post_finalizer hook are caught.

    Also verifies that the fixture cache is properly reset even when the
    post_finalizer hook raises an exception, so the fixture can be rebuilt
    in subsequent tests.
    """
    pytester.makeconftest(
        """
        import pytest

        def pytest_fixture_post_finalizer(fixturedef, request):
            if "test_first" in request.node.nodeid:
                raise RuntimeError("Error in post finalizer hook")

        @pytest.fixture
        def my_fixture(request):
            yield request.node.nodeid
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        def test_first(my_fixture):
            assert "test_first" in my_fixture

        def test_second(my_fixture):
            assert "test_second" in my_fixture
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2, errors=1)
    result.stdout.fnmatch_lines(
        [
            "*test_first*PASSED",
            "*test_first*ERROR",
            "*RuntimeError: Error in post finalizer hook*",
        ]
    )
    # Verify fixture is setup twice (rebuilt for test_second despite error).
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_first ",
            "        SETUP    F my_fixture",
            "        test_fixtures.py::test_first (fixtures used: my_fixture, request)PASSED",
            "test_fixtures.py::test_first ERROR",
            "test_fixtures.py::test_second ",
            "        SETUP    F my_fixture",
            "        test_fixtures.py::test_second (fixtures used: my_fixture, request)PASSED",
            "        TEARDOWN F my_fixture",
        ],
        consecutive=True,
    )


def test_parametrized_fixture_carries_over_unaware_item(pytester: Pytester) -> None:
    """Test that cached parametrized fixtures carry over non-fixture-aware test items.

    We disable test reordering to ensure tests run in the defined order.
    """
    pytester.makeconftest(
        """
        import pytest

        class MeaningOfLifeTest(pytest.Item):
            def runtest(self):
                return self.path.read_text(encoding="utf-8").strip() == "42"

        def pytest_collect_file(parent, file_path):
            if "meaning_of_life" in file_path.name:
                return MeaningOfLifeTest.from_parent(parent, path=file_path, name=file_path.stem)

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            original_items = items[:]
            yield
            items[:] = original_items

        @pytest.fixture(scope="session")
        def foo(request):
            return getattr(request, "param", None)
        """
    )
    pytester.makepyfile(
        test_1="""
        import pytest

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_first(foo):
            pass
        """
    )
    pytester.maketxtfile(test_2_meaning_of_life="42\n")
    pytester.makepyfile(
        test_3="""
        import pytest

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_third(foo):
            pass
        """
    )
    result = pytester.runpytest("-v", "--setup-only")
    result.stdout.fnmatch_lines(
        [
            "test_1.py::test_first[1] ",
            "SETUP    S foo[1]",
            "        test_1.py::test_first[1] (fixtures used: foo, request)",
            ".::test_2_meaning_of_life ",
            "        .::test_2_meaning_of_life",
            "test_3.py::test_third[1] ",
            "        test_3.py::test_third[1] (fixtures used: foo, request)",
            "TEARDOWN S foo[1]",
        ],
        consecutive=True,
    )


def test_fixture_rebuilt_when_param_appears(pytester: Pytester) -> None:
    """Test that fixtures are rebuilt when their parameter appears or disappears.

    We disable test reordering to ensure tests run in the defined order.
    """
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            original_items = items[:]
            yield
            items[:] = original_items
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return getattr(request, "param", None)

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_a(foo):
            assert foo == 1

        def test_b(foo):
            assert foo is None

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_c(foo):
            assert foo == 1

        def test_d(foo):
            assert foo is None
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=4)


def test_fixture_not_rebuilt_when_not_requested(pytester: Pytester) -> None:
    """Test that fixtures are NOT rebuilt when not requested in an intermediate test.

    This is a control test showing that when test_b doesn't access foo at all,
    the fixture remains cached and is not torn down/rebuilt.

    Scenario:
    1. test_a: fixture 'foo' is parametrized with value 1
    2. test_b: does NOT request fixture 'foo'
    3. test_c: fixture 'foo' is parametrized with value 1 (same as test_a)

    We disable test reordering to ensure tests run in the defined order.
    """
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            original_items = items[:]
            yield
            items[:] = original_items
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_a(foo):
            assert foo == 1

        def test_b():
            pass

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_c(foo):
            assert foo == 1
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=3)
    # Verify fixture is setup only once and carries over test_b.
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_a[1] ",
            "SETUP    S foo[1]",
            "        test_fixtures.py::test_a[1] (fixtures used: foo, request)PASSED",
            "test_fixtures.py::test_b ",
            "        test_fixtures.py::test_bPASSED",
            "test_fixtures.py::test_c[1] ",
            "        test_fixtures.py::test_c[1] (fixtures used: foo, request)PASSED",
            "TEARDOWN S foo[1]",
        ],
        consecutive=True,
    )


def test_cache_mismatch_error_on_sudden_getfixturevalue(pytester: Pytester) -> None:
    """Test cache key mismatch when accessing parametrized fixture via getfixturevalue.

    This test demonstrates that accessing a previously parametrized fixture via
    getfixturevalue without providing a parameter causes a cache key mismatch error.

    Scenario:
    1. test_a: fixture 'foo' is parametrized with value 1
    2. test_b: fixture 'foo' is accessed via getfixturevalue without parameter
    3. test_c: fixture 'foo' is parametrized again with value 1

    We disable test reordering to ensure tests run in the defined order.
    """
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            original_items = items[:]
            yield
            items[:] = original_items
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return getattr(request, 'param', 'default')

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_a(foo):
            assert foo == 1

        def test_b(request):
            value = request.getfixturevalue("foo")
            assert value is not None

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_c(foo):
            assert foo == 1
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2, failed=1)
    result.stdout.fnmatch_lines(
        [
            "*Parameter for the requested fixture changed unexpectedly*",
            "*test_b*",
            "*Requested fixture 'foo'*",
            "*Previous parameter value: 1",
            "*New parameter value: None",
        ]
    )
    # Verify fixture is NOT torn down during test_b failure.
    result.stdout.fnmatch_lines(
        [
            "SETUP    S foo[1]",
            "*test_a*PASSED",
            "*test_b*",
            "*test_b*FAILED",
            "*test_c*",
            "*test_c*PASSED",
            "TEARDOWN S foo[1]",
        ],
        consecutive=True,
    )


def test_cache_key_mismatch_error_on_unexpected_param_change(
    pytester: Pytester,
) -> None:
    """Test what happens when param changes unexpectedly, forcing a parametrized
    fixture to teardown during setup phase. In this case, the test that changed its
    parameter unexpectedly fails.
    """
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            # Disable built-in parametrized test reordering.
            original_items = items[:]
            yield
            items[:] = original_items

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_runtest_protocol(item, nextitem):
            # Manipulate callspec for test_b to cause unexpected param change.
            if item.name == "test_b[1]":
                # Change the parameter value after teardown check but before setup.
                item.callspec.params["foo"] = 999
            yield
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_a(foo):
            assert foo == 1

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_b(foo):
            assert foo == 1

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_c(foo):
            assert foo == 1
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2, errors=1)
    result.stdout.fnmatch_lines(
        [
            "*Parameter for the requested fixture changed unexpectedly*",
            "*test_b*",
            "*Requested fixture 'foo'*",
            "*Previous parameter value: 1",
            "*New parameter value: 999",
        ]
    )
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_a[1] ",
            "SETUP    S foo[1]",
            "        *test_a*PASSED",
            "test_fixtures.py::test_b[1] ERROR",
            "test_fixtures.py::test_c[1] ",
            "        *test_c*PASSED",
            "TEARDOWN S foo[1]",
        ],
        consecutive=True,
    )


def test_teardown_stale_fixtures_single_exception(pytester: Pytester) -> None:
    """Test that a single exception during stale fixture teardown is propagated."""
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def failing_fixture(request):
            yield request.param
            raise RuntimeError("Teardown error")

        @pytest.mark.parametrize("failing_fixture", [1], indirect=True)
        def test_first(failing_fixture):
            assert failing_fixture == 1

        @pytest.mark.parametrize("failing_fixture", [2], indirect=True)
        def test_second(failing_fixture):
            assert failing_fixture == 2
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2, errors=2)
    result.stdout.fnmatch_lines(
        [
            "*RuntimeError: Teardown error*",
            "*RuntimeError: Teardown error*",
        ]
    )
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_first[1] ",
            "SETUP    S failing_fixture[1]",
            "        *test_first*PASSED",
            "TEARDOWN S failing_fixture[1]",
            "*test_first*ERROR",
            "test_fixtures.py::*test_second* ",
            "SETUP    S failing_fixture[2]",
            "        *test_second*PASSED",
            "TEARDOWN S failing_fixture[2]",
            "*test_second*ERROR",
        ],
        consecutive=True,
    )


def test_teardown_stale_fixtures_multiple_exceptions(pytester: Pytester) -> None:
    """Test that multiple exceptions during stale fixture teardown are grouped."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(scope="session")
        def fixture_a(request):
            yield request.param
            raise RuntimeError("Error in fixture_a teardown")

        @pytest.fixture(scope="session")
        def fixture_b(request):
            yield request.param
            raise ValueError("Error in fixture_b teardown")

        @pytest.mark.parametrize("fixture_a,fixture_b", [(1, 1)], indirect=True)
        def test_first(fixture_a, fixture_b):
            assert fixture_a == 1
            assert fixture_b == 1

        @pytest.mark.parametrize("fixture_a,fixture_b", [(2, 2)], indirect=True)
        def test_second(fixture_a, fixture_b):
            assert fixture_a == 2
            assert fixture_b == 2
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=2, errors=2)
    # Should have errors with BaseExceptionGroup containing both exceptions.
    result.stdout.fnmatch_lines(
        [
            "*ExceptionGroup: errors while tearing down fixtures*",
            "*RuntimeError: Error in fixture_a teardown*",
            "*ValueError: Error in fixture_b teardown*",
        ]
    )


def test_request_stealing_then_getfixturevalue_on_parametrized(
    pytester: Pytester,
) -> None:
    """Golden test for the behavior of fixture dependency tracking when a fixture
    steals another fixture's request.

    This test demonstrates the behavior when:
    1. A session-scoped fixture returns its request object
    2. Another session-scoped fixture uses that request to call getfixturevalue
    3. The requested fixture is parametrized

    The current behavior is to allow this but skip fixture dependency tracking
    for when request object is used after its fixture setup completes.
    This could be detected and disallowed in the future.
    """
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def param_fixture(request):
            return request.param

        @pytest.fixture(scope="session")
        def request_provider(request):
            return request

        @pytest.fixture(scope="session")
        def dependent(request_provider):
            return request_provider.getfixturevalue("param_fixture")

        @pytest.mark.parametrize("param_fixture", [1], indirect=True)
        def test_first(dependent, param_fixture):
            assert param_fixture == 1
            assert dependent == 1

        @pytest.mark.parametrize("param_fixture", [2], indirect=True)
        def test_second(dependent, param_fixture):
            assert param_fixture == 2
            # Dependency of dependent on param_fixture is not tracked.
            assert dependent == 1
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_first[1] ",
            "SETUP    S request_provider",
            "SETUP    S param_fixture[1]",
            "SETUP    S dependent (fixtures used: request_provider)",
            "        *test_first*",
            # Dependency of dependent on param_fixture is not tracked.
            "TEARDOWN S param_fixture[1]",
            "test_fixtures.py::test_second[2] ",
            "SETUP    S param_fixture[2]",
            "        *test_second*",
            "TEARDOWN S param_fixture[2]",
            "TEARDOWN S dependent",
            "TEARDOWN S request_provider",
        ],
        consecutive=True,
    )


def test_stale_finalizer_not_invoked(pytester: Pytester) -> None:
    """Test that stale fixture finalizers are not invoked.

    Scenario:
    1. Fixture 'bar' depends on 'foo' via getfixturevalue in first evaluation;
       in a possible implementation, a finalizer is added to 'foo' to first destroy 'bar'
    2. Fixture 'bar' gets recomputed and no longer depends on 'foo'
    3. Fixture 'foo' gets finalized
    4. Without any measures to remove the stale finalizer, 'bar' would be finalized
       by the finalizer registered during step 1, even though 'bar' has been recomputed

    The test verifies that 'bar' is NOT finalized when 'foo' is finalized,
    because 'bar' was recomputed and the old finalizer should be ignored.
    """
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.fixture(scope="session")
        def bar(request):
            if request.param == 1:
                return request.getfixturevalue("foo")
            return "independent"

        @pytest.mark.parametrize("foo,bar", [(1, 1)], indirect=True)
        def test_first(foo, bar):
            assert foo == 1
            assert bar == 1

        @pytest.mark.parametrize("foo,bar", [(1, 2)], indirect=True)
        def test_second(foo, bar):
            assert foo == 1
            assert bar == "independent"

        @pytest.mark.parametrize("foo,bar", [(2, 2)], indirect=True)
        def test_third(foo, bar):
            assert foo == 2
            assert bar == "independent"
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=3)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_first[1-1] ",
            "SETUP    S foo[1]",
            "SETUP    S bar[1] (fixtures used: foo)",
            "        *test_first*PASSED",
            "TEARDOWN S bar[1]",
            "test_fixtures.py::test_second[1-2] ",
            "SETUP    S bar[2]",
            "        *test_second*PASSED",
            "TEARDOWN S foo[1]",
            # bar should NOT be torn down here.
            "test_fixtures.py::test_third[2-2] ",
            "SETUP    S foo[2]",
            "        *test_third*PASSED",
            "TEARDOWN S foo[2]",
            "TEARDOWN S bar[2]",
        ],
        consecutive=True,
    )


def test_fixture_teardown_when_not_requested_but_param_changes(
    pytester: Pytester,
) -> None:
    """Test when a parametrized fixture gets torn down when not requested by intermediate test.

    This test demonstrates a surprising but necessary behavior:
    When a parametrized fixture is not requested by an intermediate test, and
    the next test requests it with a different parameter, the fixture gets torn down
    at the end of the intermediate test.
    """
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            # Disable built-in parametrized test reordering.
            original_items = items[:]
            yield
            items[:] = original_items
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_a(foo):
            assert foo == 1

        def test_b():
            pass

        @pytest.mark.parametrize("foo", [2], indirect=True)
        def test_c(foo):
            assert foo == 2
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=3)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_a[1] ",
            "SETUP    S foo[1]",
            "        *test_a*PASSED",
            "test_fixtures.py::test_b ",
            "        *test_b*PASSED",
            # foo[1] is torn down here, at the end of test_b.
            "TEARDOWN S foo[1]",
            "test_fixtures.py::test_c[2] ",
            "SETUP    S foo[2]",
            "        *test_c*PASSED",
            "TEARDOWN S foo[2]",
        ],
        consecutive=True,
    )


def test_fixture_teardown_with_reordered_tests(pytester: Pytester) -> None:
    """Test that fixture teardown works correctly when tests are reordered at runtime.

    This test verifies that the fixture teardown mechanism doesn't hard rely on the
    ordering of tests from the collection stage. Tests are collected in one order
    but executed in a different order via a custom pytest_runtestloop hook.

    Collection order: test_a, test_b, test_c
    Execution order: test_a, test_c, test_b
    """
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(wrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(items):
            # Disable built-in parametrized test reordering.
            original_items = items[:]
            yield
            items[:] = original_items

        @pytest.hookimpl(tryfirst=True)
        def pytest_runtestloop(session):
            # Reorder tests at runtime: test_a, test_c, test_b.
            items = list(session.items)
            assert len(items) == 3
            # Swap test_b and test_c.
            items[1], items[2] = items[2], items[1]
            for i, item in enumerate(items):
                nextitem = items[i + 1] if i + 1 < len(items) else None
                item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)
            return True
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_a(foo):
            assert foo == 1

        @pytest.mark.parametrize("foo", [1], indirect=True)
        def test_b(foo):
            assert foo == 1

        @pytest.mark.parametrize("foo", [2], indirect=True)
        def test_c(foo):
            assert foo == 2
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=3)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_a[1] ",
            "SETUP    S foo[1]",
            "        *test_a*PASSED",
            # foo[1] is torn down here because test_c needs foo[2].
            "TEARDOWN S foo[1]",
            "test_fixtures.py::test_c[2] ",
            "SETUP    S foo[2]",
            "        *test_c*PASSED",
            "TEARDOWN S foo[2]",
            "test_fixtures.py::test_b[1] ",
            "SETUP    S foo[1]",
            "        *test_b*PASSED",
            "TEARDOWN S foo[1]",
        ],
        consecutive=True,
    )


def test_fixture_post_finalizer_called_once(pytester: Pytester) -> None:
    """Test that pytest_fixture_post_finalizer is called only once per fixture teardown.

    When a fixture depends on multiple parametrized fixtures and all their parameters
    change at the same time, the dependent fixture should be torn down only once,
    and pytest_fixture_post_finalizer should be called only once for it.
    """
    pytester.makeconftest(
        """
        import pytest

        finalizer_calls = []

        def pytest_fixture_post_finalizer(fixturedef, request):
            finalizer_calls.append(fixturedef.argname)

        @pytest.fixture(autouse=True)
        def check_finalizer_calls(request):
            yield
            # After each test, verify no duplicate finalizer calls.
            if finalizer_calls:
                assert len(finalizer_calls) == len(set(finalizer_calls)), (
                    f"Duplicate finalizer calls detected: {finalizer_calls}"
                )
                finalizer_calls.clear()
        """
    )
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.fixture(scope="session")
        def bar(request):
            return request.param

        @pytest.fixture(scope="session")
        def baz(foo, bar):
            return f"{foo}-{bar}"

        @pytest.mark.parametrize("foo,bar", [(1, 1)], indirect=True)
        def test_first(foo, bar, baz):
            assert foo == 1
            assert bar == 1
            assert baz == "1-1"

        @pytest.mark.parametrize("foo,bar", [(2, 2)], indirect=True)
        def test_second(foo, bar, baz):
            assert foo == 2
            assert bar == 2
            assert baz == "2-2"
        """
    )
    result = pytester.runpytest("-v")
    # The test passes, which means no duplicate finalizer calls were detected
    # by the check_finalizer_calls autouse fixture.
    result.assert_outcomes(passed=2)


def test_parametrized_fixtures_teardown_in_reverse_setup_order(
    pytester: Pytester,
) -> None:
    """Test that when multiple parametrized fixtures change at the same time, they are torn down in reverse setup order.

    When two parametrized fixtures both change their parameters between tests,
    they should be torn down in the reverse order of their setup.
    """
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="session")
        def foo(request):
            return request.param

        @pytest.fixture(scope="session")
        def bar(request):
            return request.param

        @pytest.mark.parametrize("foo,bar", [(1, 1)], indirect=True)
        def test_first(foo, bar):
            assert foo == 1
            assert bar == 1

        @pytest.mark.parametrize("foo,bar", [(2, 2)], indirect=True)
        def test_second(foo, bar):
            assert foo == 2
            assert bar == 2
        """
    )
    result = pytester.runpytest("-v", "--setup-show")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::test_first[1-1] ",
            "SETUP    S foo[1]",
            "SETUP    S bar[1]",
            "        *test_first*PASSED",
            # Teardown in reverse setup order: bar first, then foo.
            "TEARDOWN S bar[1]",
            "TEARDOWN S foo[1]",
            "test_fixtures.py::test_second[2-2] ",
            "SETUP    S foo[2]",
            "SETUP    S bar[2]",
            "        *test_second*PASSED",
            "TEARDOWN S bar[2]",
            "TEARDOWN S foo[2]",
        ],
        consecutive=True,
    )


def test_parametrized_fixture_teardown_order_with_mixed_scopes(
    pytester: Pytester,
) -> None:
    """Test teardown order when parametrized fixtures are mixed with regular fixtures.

    When a function-scoped, parametrized session-scoped, and class-scoped fixtures
    are all torn down at the same time, parametrized fixtures are considered to be
    between function-scoped and class-scoped in teardown order.
    """
    pytester.makepyfile(
        test_fixtures="""
        import pytest

        @pytest.fixture(scope="function")
        def func_fixture():
            yield "func"

        @pytest.fixture(scope="session")
        def session_param_fixture(request):
            yield request.param

        @pytest.fixture(scope="class")
        def class_fixture():
            yield "class"

        class TestClass:
            @pytest.mark.parametrize("session_param_fixture", [1], indirect=True)
            def test_first(self, func_fixture, session_param_fixture, class_fixture):
                pass

        @pytest.mark.parametrize("session_param_fixture", [2], indirect=True)
        def test_second(session_param_fixture):
            pass
        """
    )
    result = pytester.runpytest("-v", "--setup-plan")
    result.stdout.fnmatch_lines(
        [
            "test_fixtures.py::TestClass::test_first[1] ",
            "SETUP    S session_param_fixture[1]",
            "      SETUP    C class_fixture",
            "        SETUP    F func_fixture",
            "        *test_first*",
            "        TEARDOWN F func_fixture",
            # Parametrized fixture torn down between function and class fixtures.
            "TEARDOWN S session_param_fixture[1]",
            "      TEARDOWN C class_fixture",
            "test_fixtures.py::test_second[2] ",
            "SETUP    S session_param_fixture[2]",
            "        *test_second*",
            "TEARDOWN S session_param_fixture[2]",
        ],
        consecutive=True,
    )
