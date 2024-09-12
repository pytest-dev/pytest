from __future__ import annotations

import textwrap


def test_discover_imports_enabled(pytester):
    src_dir = pytester.mkdir("src")
    tests_dir = pytester.mkdir("tests")
    pytester.makeini("""
        [pytest]
        testpaths = "tests"
        discover_imports = true
    """)

    src_file = src_dir / "foo.py"

    src_file.write_text(
        textwrap.dedent("""\
    class TestClass(object):
        def __init__(self):
            super().__init__()

        def test_foobar(self):
            return true
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

    from src.foo import TestClass

    class TestDomain:
        def test_testament(self):
            testament = TestClass()
            pass
    """),
        encoding="utf-8",
    )

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)


def test_discover_imports_disabled(pytester):
    src_dir = pytester.mkdir("src")
    tests_dir = pytester.mkdir("tests")
    pytester.makeini("""
        [pytest]
        testpaths = "tests"
        discover_imports = false
    """)

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
    result.assert_outcomes(passed=1)
