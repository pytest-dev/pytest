from __future__ import annotations

import textwrap

from _pytest.pytester import Pytester


def run_import_class_test(pytester: Pytester, passed: int = 0, errors: int = 0) -> None:
    src_dir = pytester.mkdir("src")
    tests_dir = pytester.mkdir("tests")
    src_file = src_dir / "foo.py"

    src_file.write_text(
        textwrap.dedent("""\
    class Testament(object):
        def __init__(self):
            super().__init__()
            self.collections = ["stamp", "coin"]

        def personal_property(self):
            return [f"my {x} collection" for x in self.collections]
    """),
        encoding="utf-8",
    )

    test_file = tests_dir / "foo_test.py"
    test_file.write_text(
        textwrap.dedent("""\
    import sys
    import os

    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    sys.path.append(parent_dir)

    from src.foo import Testament

    class TestDomain:
        def test_testament(self):
            testament = Testament()
            assert testament.personal_property()
    """),
        encoding="utf-8",
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=passed, errors=errors)


def test_collect_imports_disabled(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        testpaths = "tests"
        collect_imported_tests = false
    """)

    run_import_class_test(pytester, passed=1)


def test_collect_imports_default(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        testpaths = "tests"
    """)

    run_import_class_test(pytester, errors=1)


def test_collect_imports_enabled(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        testpaths = "tests"
        collect_imported_tests = true
    """)

    run_import_class_test(pytester, errors=1)


def run_import_functions_test(
    pytester: Pytester, passed: int, errors: int, failed: int
) -> None:
    src_dir = pytester.mkdir("src")
    tests_dir = pytester.mkdir("tests")

    src_file = src_dir / "foo.py"

    # Note that these "tests" are should _not_ be treated as tests.
    # They are normal functions that happens to have test_* or *_test in the name.
    # Thus should _not_ be collected!
    src_file.write_text(
        textwrap.dedent("""\
        def test_function():
            some_random_computation = 5
            return some_random_computation

        def test_bar():
            pass
    """),
        encoding="utf-8",
    )

    test_file = tests_dir / "foo_test.py"

    # Inferred from the comment above, this means that there is _only_ one actual test
    # which should result in only 1 passing test being ran.
    test_file.write_text(
        textwrap.dedent("""\
    import sys
    import os

    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    sys.path.append(parent_dir)

    from src.foo import *

    class TestDomain:
        def test_important(self):
            res = test_function()
            if res == 5:
                pass

    """),
        encoding="utf-8",
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=passed, errors=errors, failed=failed)


def test_collect_function_imports_enabled(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        testpaths = "tests"
        collect_imported_tests = true
    """)

    run_import_functions_test(pytester, passed=2, errors=0, failed=1)


def test_collect_function_imports_disabled(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        # testpaths = "tests"
        collect_imported_tests = false
    """)

    run_import_functions_test(pytester, passed=1, errors=0, failed=0)


def test_behaviour_without_testpaths_set_and_false(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        collect_imported_tests = false
    """)

    run_import_functions_test(pytester, passed=1, errors=0, failed=0)


def test_behaviour_without_testpaths_set_and_true(pytester: Pytester) -> None:
    pytester.makeini("""
        [pytest]
        collect_imported_tests = true
    """)

    run_import_functions_test(pytester, passed=2, errors=0, failed=1)
