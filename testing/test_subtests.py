from __future__ import annotations

from pathlib import Path
import sys
from typing import Literal

import pytest


IS_PY311 = sys.version_info[:2] >= (3, 11)


@pytest.mark.parametrize("mode", ["normal", "xdist"])
class TestFixture:
    """Tests for ``subtests`` fixture."""

    @pytest.fixture
    def simple_script(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        assert i % 2 == 0
        """
        )

    def test_simple_terminal_normal(
        self,
        simple_script: None,
        pytester: pytest.Pytester,
        mode: Literal["normal", "xdist"],
    ) -> None:
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1", "-pxdist.plugin")
            expected_lines = ["1 worker [1 item]"]

        expected_lines += [
            "* test_foo [[]custom[]] (i=1) *",
            "* test_foo [[]custom[]] (i=3) *",
            "Contains 2 failed subtests",
            "* 3 failed, 3 subtests passed in *",
        ]
        result.stdout.fnmatch_lines(expected_lines)

    def test_simple_terminal_verbose(
        self,
        simple_script: None,
        pytester: pytest.Pytester,
        mode: Literal["normal", "xdist"],
    ) -> None:
        if mode == "normal":
            result = pytester.runpytest("-v")
            expected_lines = [
                "*collected 1 item",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=0) SUBPASSED *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=1) SUBFAILED *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=2) SUBPASSED *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=3) SUBFAILED *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=4) SUBPASSED *100%*",
                "test_simple_terminal_verbose.py::test_foo FAILED *100%*",
            ]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1", "-v", "-pxdist.plugin")
            expected_lines = [
                "1 worker [1 item]",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
            ]

        expected_lines += [
            "* test_foo [[]custom[]] (i=1) *",
            "* test_foo [[]custom[]] (i=3) *",
            "* 3 failed, 3 subtests passed in *",
        ]
        result.stdout.fnmatch_lines(expected_lines)

    def test_skip(
        self, pytester: pytest.Pytester, mode: Literal["normal", "xdist"]
    ) -> None:
        pytester.makepyfile(
            """
            import pytest
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        if i % 2 == 0:
                            pytest.skip('even number')
        """
        )
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1", "-pxdist.plugin")
            expected_lines = ["1 worker [1 item]"]
        expected_lines += ["* 1 passed, 3 skipped, 2 subtests passed in *"]
        result.stdout.fnmatch_lines(expected_lines)

    def test_xfail(
        self, pytester: pytest.Pytester, mode: Literal["normal", "xdist"]
    ) -> None:
        pytester.makepyfile(
            """
            import pytest
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        if i % 2 == 0:
                            pytest.xfail('even number')
        """
        )
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1", "-pxdist.plugin")
            expected_lines = ["1 worker [1 item]"]
        expected_lines += ["* 1 passed, 2 subtests passed, 3 subtests xfailed in *"]
        result.stdout.fnmatch_lines(expected_lines)

    def test_typing_exported(
        self, pytester: pytest.Pytester, mode: Literal["normal", "xdist"]
    ) -> None:
        pytester.makepyfile(
            """
            from pytest import Subtests

            def test_typing_exported(subtests: Subtests) -> None:
                assert isinstance(subtests, Subtests)
            """
        )
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1", "-pxdist.plugin")
            expected_lines = ["1 worker [1 item]"]
        expected_lines += ["* 1 passed *"]
        result.stdout.fnmatch_lines(expected_lines)

    def test_no_subtests_reports(
        self, pytester: pytest.Pytester, mode: Literal["normal", "xdist"]
    ) -> None:
        pytester.makepyfile(
            """
            import pytest

            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        pass
        """
        )
        # Without `--no-subtests-reports`, subtests are reported normally.
        result = pytester.runpytest("-v")
        result.stdout.fnmatch_lines(
            [
                "*collected 1 item*",
                "test_no_subtests_reports.py::test_foo * (i=0) SUBPASSED*",
                "*test_no_subtests_reports.py::test_foo PASSED*",
                "* 1 passed, 5 subtests passed in*",
            ]
        )

        # With `--no-subtests-reports`, passing subtests are no longer reported.
        result = pytester.runpytest("-v", "--no-subtests-reports")
        result.stdout.fnmatch_lines(
            [
                "*collected 1 item*",
                "*test_no_subtests_reports.py::test_foo PASSED*",
                "* 1 passed in*",
            ]
        )
        result.stdout.no_fnmatch_line("*SUBPASSED*")

        # Rewrite the test file so the tests fail. Even with the flag, failed subtests are still reported.
        pytester.makepyfile(
            """
            import pytest

            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        assert False
        """
        )
        result = pytester.runpytest("-v", "--no-subtests-reports")
        result.stdout.fnmatch_lines(
            [
                "*collected 1 item*",
                "test_no_subtests_reports.py::test_foo * (i=0) SUBFAILED*",
                "*test_no_subtests_reports.py::test_foo FAILED*",
                "* 6 failed in*",
            ]
        )


def test_subtests_and_parametrization(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize("x", [0, 1])
        def test_foo(subtests, x):
            for i in range(3):
                with subtests.test("custom", i=i):
                    assert i % 2 == 0
            assert x == 0
    """
    )
    result = pytester.runpytest("-v", "--no-subtests-reports")
    result.stdout.fnmatch_lines(
        [
            "test_subtests_and_parametrization.py::test_foo[[]0[]] [[]custom[]] (i=1) SUBFAILED*[[] 50%[]]",
            "test_subtests_and_parametrization.py::test_foo[[]0[]] FAILED              *[[] 50%[]]",
            "test_subtests_and_parametrization.py::test_foo[[]1[]] [[]custom[]] (i=1) SUBFAILED *[[]100%[]]",
            "test_subtests_and_parametrization.py::test_foo[[]1[]] FAILED              *[[]100%[]]",
            "Contains 1 failed subtest",
            "* 4 failed in *",
        ]
    )


def test_subtests_fail_top_level_test(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        def test_foo(subtests):
            for i in range(3):
                with subtests.test("custom", i=i):
                    assert i % 2 == 0
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "* 2 failed, 2 subtests passed in *",
        ]
    )


def test_subtests_do_not_overwrite_top_level_failure(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest

        def test_foo(subtests):
            for i in range(3):
                with subtests.test("custom", i=i):
                    assert i % 2 == 0
            assert False, "top-level failure"
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*AssertionError: top-level failure",
            "* 2 failed, 2 subtests passed in *",
        ]
    )


@pytest.mark.parametrize("flag", ["--last-failed", "--stepwise"])
def test_subtests_last_failed_step_wise(pytester: pytest.Pytester, flag: str) -> None:
    """Check that --last-failed and --step-wise correctly rerun tests with failed subtests."""
    pytester.makepyfile(
        """
        import pytest

        def test_foo(subtests):
            for i in range(3):
                with subtests.test("custom", i=i):
                    assert i % 2 == 0
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "* 2 failed, 2 subtests passed in *",
        ]
    )

    result = pytester.runpytest("-v", flag)
    result.stdout.fnmatch_lines(
        [
            "* 2 failed, 2 subtests passed in *",
        ]
    )


class TestUnittestSubTest:
    """Test unittest.TestCase.subTest functionality."""

    @pytest.fixture
    def simple_script(self, pytester: pytest.Pytester) -> Path:
        return pytester.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            self.assertEqual(i % 2, 0)

            if __name__ == '__main__':
                main()
        """
        )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_simple_terminal_normal(
        self,
        simple_script: Path,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        suffix = ".test_foo" if IS_PY311 else ""
        if runner == "unittest":
            result = pytester.run(sys.executable, simple_script)
            result.stderr.fnmatch_lines(
                [
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=1)",
                    "AssertionError: 1 != 0",
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=3)",
                    "AssertionError: 1 != 0",
                    "Ran 1 test in *",
                    "FAILED (failures=2)",
                ]
            )
        else:
            if runner == "pytest-normal":
                result = pytester.runpytest(simple_script)
                expected_lines = ["collected 1 item"]
            else:
                assert runner == "pytest-xdist"
                pytest.importorskip("xdist")
                result = pytester.runpytest(simple_script, "-n1", "-pxdist.plugin")
                expected_lines = ["1 worker [1 item]"]
            result.stdout.fnmatch_lines(
                [
                    *expected_lines,
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed, 3 subtests passed in *",
                ]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_simple_terminal_verbose(
        self,
        simple_script: Path,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        suffix = ".test_foo" if IS_PY311 else ""
        if runner == "unittest":
            result = pytester.run(sys.executable, simple_script, "-v")
            result.stderr.fnmatch_lines(
                [
                    f"test_foo (__main__.T{suffix}) ... ",
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=1)",
                    "AssertionError: 1 != 0",
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=3)",
                    "AssertionError: 1 != 0",
                    "Ran 1 test in *",
                    "FAILED (failures=2)",
                ]
            )
        else:
            if runner == "pytest-normal":
                result = pytester.runpytest(simple_script, "-v")
                expected_lines = [
                    "*collected 1 item",
                    "test_simple_terminal_verbose.py::T::test_foo [[]custom[]] (i=1) SUBFAILED *100%*",
                    "test_simple_terminal_verbose.py::T::test_foo [[]custom[]] (i=3) SUBFAILED *100%*",
                    "test_simple_terminal_verbose.py::T::test_foo PASSED *100%*",
                ]
            else:
                assert runner == "pytest-xdist"
                pytest.importorskip("xdist")
                result = pytester.runpytest(
                    simple_script, "-n1", "-v", "-pxdist.plugin"
                )
                expected_lines = [
                    "1 worker [1 item]",
                    "*gw0*100%* SUBFAILED test_simple_terminal_verbose.py::T::test_foo*",
                    "*gw0*100%* SUBFAILED test_simple_terminal_verbose.py::T::test_foo*",
                    "*gw0*100%* PASSED test_simple_terminal_verbose.py::T::test_foo*",
                ]
            result.stdout.fnmatch_lines(
                [
                    *expected_lines,
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed, 3 subtests passed in *",
                ]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_skip(
        self,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        p = pytester.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            if i % 2 == 0:
                                self.skipTest('even number')

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = pytester.runpython(p)
            result.stderr.fnmatch_lines(["Ran 1 test in *", "OK (skipped=3)"])
        else:
            pytest.xfail("Not producing the expected results (#13756)")
            result = pytester.runpytest(p)  # type:ignore[unreachable]
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 skipped, 1 passed in *"]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    @pytest.mark.xfail(reason="Not producing the expected results (#13756)")
    def test_xfail(
        self,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        p = pytester.makepyfile(
            """
            import pytest
            from unittest import expectedFailure, TestCase, main

            class T(TestCase):
                @expectedFailure
                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            if i % 2 == 0:
                                raise pytest.xfail('even number')

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = pytester.runpython(p)
            result.stderr.fnmatch_lines(["Ran 1 test in *", "OK (expected failures=3)"])
        else:
            result = pytester.runpytest(p)
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 xfailed, 1 passed in *"]
            )

    @pytest.mark.parametrize("runner", ["pytest-normal"])
    def test_only_original_skip_is_called(
        self,
        pytester: pytest.Pytester,
        monkeypatch: pytest.MonkeyPatch,
        runner: Literal["pytest-normal"],
    ) -> None:
        """Regression test for pytest-dev/pytest-subtests#173."""
        monkeypatch.setenv("COLUMNS", "200")
        p = pytester.makepyfile(
            """
            import unittest
            from unittest import TestCase, main

            @unittest.skip("skip this test")
            class T(unittest.TestCase):
                def test_foo(self):
                    assert 1 == 2

            if __name__ == '__main__':
                main()
        """
        )
        result = pytester.runpytest(p, "-v", "-rsf")
        result.stdout.fnmatch_lines(
            ["SKIPPED [1] test_only_original_skip_is_called.py:6: skip this test"]
        )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_skip_with_failure(
        self,
        pytester: pytest.Pytester,
        monkeypatch: pytest.MonkeyPatch,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        monkeypatch.setenv("COLUMNS", "200")
        p = pytester.makepyfile(
            """
            import pytest
            from unittest import expectedFailure, TestCase, main

            class T(TestCase):
                def test_foo(self):
                    for i in range(10):
                        with self.subTest("custom message", i=i):
                            if i < 4:
                                self.skipTest(f"skip subtest i={i}")
                            assert i < 4

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = pytester.runpython(p)
            if sys.version_info < (3, 11):
                result.stderr.re_match_lines(
                    [
                        r"FAIL: test_foo \(__main__\.T\) \[custom message\] \(i=4\).*",
                        r"FAIL: test_foo \(__main__\.T\) \[custom message\] \(i=9\).*",
                        r"Ran 1 test in .*",
                        r"FAILED \(failures=6, skipped=4\)",
                    ]
                )
            else:
                result.stderr.re_match_lines(
                    [
                        r"FAIL: test_foo \(__main__\.T\.test_foo\) \[custom message\] \(i=4\).*",
                        r"FAIL: test_foo \(__main__\.T\.test_foo\) \[custom message\] \(i=9\).*",
                        r"Ran 1 test in .*",
                        r"FAILED \(failures=6, skipped=4\)",
                    ]
                )
        elif runner == "pytest-normal":
            result = pytester.runpytest(p, "-v", "-rsf")
            result.stdout.re_match_lines(
                [
                    r"test_skip_with_failure.py::T::test_foo \[custom message\] \(i=0\) SUBSKIPPED \(skip subtest i=0\) .*",  # noqa: E501
                    r"test_skip_with_failure.py::T::test_foo \[custom message\] \(i=3\) SUBSKIPPED \(skip subtest i=3\) .*",  # noqa: E501
                    r"test_skip_with_failure.py::T::test_foo \[custom message\] \(i=4\) SUBFAILED .*",
                    r"test_skip_with_failure.py::T::test_foo \[custom message\] \(i=9\) SUBFAILED .*",
                    "test_skip_with_failure.py::T::test_foo PASSED .*",
                    r"[custom message] (i=0) SUBSKIPPED [1] test_skip_with_failure.py:5: skip subtest i=0",
                    r"[custom message] (i=0) SUBSKIPPED [1] test_skip_with_failure.py:5: skip subtest i=3",
                    r"[custom message] (i=4) SUBFAILED test_skip_with_failure.py::T::test_foo"
                    r" - AssertionError: assert 4 < 4",
                    r"[custom message] (i=9) SUBFAILED test_skip_with_failure.py::T::test_foo"
                    r" - AssertionError: assert 9 < 4",
                    r".* 6 failed, 1 passed, 4 skipped in .*",
                ]
            )
        else:
            pytest.xfail("Not producing the expected results (#13756)")
            result = pytester.runpytest(p)  # type:ignore[unreachable]
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 skipped, 1 passed in *"]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_skip_with_failure_and_non_subskip(
        self,
        pytester: pytest.Pytester,
        monkeypatch: pytest.MonkeyPatch,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        monkeypatch.setenv("COLUMNS", "200")
        p = pytester.makepyfile(
            """
            import pytest
            from unittest import expectedFailure, TestCase, main

            class T(TestCase):
                def test_foo(self):
                    for i in range(10):
                        with self.subTest("custom message", i=i):
                            if i < 4:
                                self.skipTest(f"skip subtest i={i}")
                            assert i < 4
                    self.skipTest(f"skip the test")

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = pytester.runpython(p)
            if sys.version_info < (3, 11):
                result.stderr.re_match_lines(
                    [
                        r"FAIL: test_foo \(__main__\.T\) \[custom message\] \(i=4\).*",
                        r"FAIL: test_foo \(__main__\.T\) \[custom message\] \(i=9\).*",
                        r"Ran 1 test in .*",
                        r"FAILED \(failures=6, skipped=5\)",
                    ]
                )
            else:
                result.stderr.re_match_lines(
                    [
                        r"FAIL: test_foo \(__main__\.T\.test_foo\) \[custom message\] \(i=4\).*",
                        r"FAIL: test_foo \(__main__\.T\.test_foo\) \[custom message\] \(i=9\).*",
                        r"Ran 1 test in .*",
                        r"FAILED \(failures=6, skipped=5\)",
                    ]
                )
        elif runner == "pytest-normal":
            result = pytester.runpytest(p, "-v", "-rsf")
            # The `(i=0)` is not correct but it's given by pytest `TerminalReporter` without `--no-fold-skipped`
            result.stdout.re_match_lines(
                [
                    r"test_skip_with_failure_and_non_subskip.py::T::test_foo \[custom message\] \(i=4\) SUBFAILED .*",
                    r"test_skip_with_failure_and_non_subskip.py::T::test_foo SKIPPED \(skip the test\)",
                    r"\[custom message\] \(i=0\) SUBSKIPPED \[1\] test_skip_with_failure_and_non_subskip.py:5:"
                    r" skip subtest i=3",
                    r"\[custom message\] \(i=0\) SUBSKIPPED \[1\] test_skip_with_failure_and_non_subskip.py:5:"
                    r" skip the test",
                    r"\[custom message\] \(i=4\) SUBFAILED test_skip_with_failure_and_non_subskip.py::T::test_foo",
                    r".* 6 failed, 5 skipped in .*",
                ]
            )
            # Check with `--no-fold-skipped` (which gives the correct information).
            if sys.version_info >= (3, 10) and pytest.version_tuple[:2] >= (8, 3):
                result = pytester.runpytest(p, "-v", "--no-fold-skipped", "-rsf")
                result.stdout.re_match_lines(
                    [
                        r"test_skip_with_failure_and_non_subskip.py::T::test_foo \[custom message\] \(i=4\) SUBFAILED .*",  # noqa: E501
                        r"test_skip_with_failure_and_non_subskip.py::T::test_foo SKIPPED \(skip the test\).*",
                        r"\[custom message\] \(i=3\) SUBSKIPPED test_skip_with_failure_and_non_subskip.py::T::test_foo"
                        r" - Skipped: skip subtest i=3",
                        r"SKIPPED test_skip_with_failure_and_non_subskip.py::T::test_foo - Skipped: skip the test",
                        r"\[custom message\] \(i=4\) SUBFAILED test_skip_with_failure_and_non_subskip.py::T::test_foo",
                        r".* 6 failed, 5 skipped in .*",
                    ]
                )
        else:
            pytest.xfail("Not producing the expected results (#13756)")
            result = pytester.runpytest(p)  # type:ignore[unreachable]
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 skipped, 1 passed in *"]
            )


class TestCapture:
    def create_file(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
                    import sys
                    def test(subtests):
                        print()
                        print('start test')

                        with subtests.test(i='A'):
                            print("hello stdout A")
                            print("hello stderr A", file=sys.stderr)
                            assert 0

                        with subtests.test(i='B'):
                            print("hello stdout B")
                            print("hello stderr B", file=sys.stderr)
                            assert 0

                        print('end test')
                        assert 0
                """
        )

    def test_capturing(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*__ test (i='A') __*",
                "*Captured stdout call*",
                "hello stdout A",
                "*Captured stderr call*",
                "hello stderr A",
                "*__ test (i='B') __*",
                "*Captured stdout call*",
                "hello stdout B",
                "*Captured stderr call*",
                "hello stderr B",
                "*__ test __*",
                "*Captured stdout call*",
                "start test",
                "end test",
            ]
        )

    def test_no_capture(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest("-s")
        result.stdout.fnmatch_lines(
            [
                "start test",
                "hello stdout A",
                "uhello stdout B",
                "uend test",
                "*__ test (i='A') __*",
                "*__ test (i='B') __*",
                "*__ test __*",
            ]
        )
        result.stderr.fnmatch_lines(["hello stderr A", "hello stderr B"])

    @pytest.mark.parametrize("fixture", ["capsys", "capfd"])
    def test_capture_with_fixture(
        self, pytester: pytest.Pytester, fixture: Literal["capsys", "capfd"]
    ) -> None:
        pytester.makepyfile(
            rf"""
            import sys

            def test(subtests, {fixture}):
                print('start test')

                with subtests.test(i='A'):
                    print("hello stdout A")
                    print("hello stderr A", file=sys.stderr)

                out, err = {fixture}.readouterr()
                assert out == 'start test\nhello stdout A\n'
                assert err == 'hello stderr A\n'
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*1 passed*",
            ]
        )


class TestLogging:
    def create_file(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import logging

            def test_foo(subtests):
                logging.info("before")

                with subtests.test("sub1"):
                    print("sub1 stdout")
                    logging.info("sub1 logging")
                    logging.debug("sub1 logging debug")

                with subtests.test("sub2"):
                    print("sub2 stdout")
                    logging.info("sub2 logging")
                    logging.debug("sub2 logging debug")
                    assert False
            """
        )

    def test_capturing_info(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest("--log-level=INFO")
        result.stdout.fnmatch_lines(
            [
                "*___ test_foo [[]sub2[]] __*",
                "*-- Captured stdout call --*",
                "sub2 stdout",
                "*-- Captured log call ---*",
                "INFO     * before",
                "INFO     * sub1 logging",
                "INFO     * sub2 logging",
                "*== short test summary info ==*",
            ]
        )
        result.stdout.no_fnmatch_line("sub1 logging debug")
        result.stdout.no_fnmatch_line("sub2 logging debug")

    def test_capturing_debug(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest("--log-level=DEBUG")
        result.stdout.fnmatch_lines(
            [
                "*___ test_foo [[]sub2[]] __*",
                "*-- Captured stdout call --*",
                "sub2 stdout",
                "*-- Captured log call ---*",
                "INFO     * before",
                "INFO     * sub1 logging",
                "DEBUG    * sub1 logging debug",
                "INFO     * sub2 logging",
                "DEBUG    * sub2 logging debug",
                "*== short test summary info ==*",
            ]
        )

    def test_caplog(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import logging

            def test(subtests, caplog):
                caplog.set_level(logging.INFO)
                logging.info("start test")

                with subtests.test("sub1"):
                    logging.info("inside %s", "subtest1")

                assert len(caplog.records) == 2
                assert caplog.records[0].getMessage() == "start test"
                assert caplog.records[1].getMessage() == "inside subtest1"
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*1 passed*",
            ]
        )

    def test_no_logging(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import logging

            def test(subtests):
                logging.info("start log line")

                with subtests.test("sub passing"):
                    logging.info("inside %s", "passing log line")

                with subtests.test("sub failing"):
                    logging.info("inside %s", "failing log line")
                    assert False

                logging.info("end log line")
            """
        )
        result = pytester.runpytest("-p no:logging")
        result.stdout.fnmatch_lines(
            [
                "*2 failed, 1 subtests passed in*",
            ]
        )
        result.stdout.no_fnmatch_line("*root:test_no_logging.py*log line*")


class TestDebugging:
    """Check --pdb support for subtests fixture and TestCase.subTest."""

    class _FakePdb:
        """Fake debugger class implementation that tracks which methods were called on it."""

        quitting: bool = False
        calls: list[str] = []

        def __init__(self, *_: object, **__: object) -> None:
            self.calls.append("init")

        def reset(self) -> None:
            self.calls.append("reset")

        def interaction(self, *_: object) -> None:
            self.calls.append("interaction")

    @pytest.fixture(autouse=True)
    def cleanup_calls(self) -> None:
        self._FakePdb.calls.clear()

    def test_pdb_fixture(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            """
            def test(subtests):
                with subtests.test():
                    assert 0
            """
        )
        self.runpytest_and_check_pdb(pytester, monkeypatch)

    def test_pdb_unittest(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            """
            from unittest import TestCase
            class Test(TestCase):
                def test(self):
                    with self.subTest():
                        assert 0
            """
        )
        self.runpytest_and_check_pdb(pytester, monkeypatch)

    def runpytest_and_check_pdb(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Install the fake pdb implementation in _pytest.subtests so we can reference
        # it in the command line (any module would do).
        import _pytest.subtests

        monkeypatch.setattr(
            _pytest.subtests, "_CustomPdb", self._FakePdb, raising=False
        )
        result = pytester.runpytest("--pdb", "--pdbcls=_pytest.subtests:_CustomPdb")

        # Ensure pytest entered in debugging mode when encountering the failing
        # assert.
        result.stdout.fnmatch_lines("*entering PDB*")
        assert self._FakePdb.calls == ["init", "reset", "interaction"]


def test_exitfirst(pytester: pytest.Pytester) -> None:
    """Validate that when passing --exitfirst the test exits after the first failed subtest."""
    pytester.makepyfile(
        """
        def test_foo(subtests):
            with subtests.test("sub1"):
                assert False

            with subtests.test("sub2"):
                assert False
        """
    )
    result = pytester.runpytest("--exitfirst")
    assert result.parseoutcomes()["failed"] == 2
    result.stdout.fnmatch_lines(
        [
            "*[[]sub1[]] SUBFAILED test_exitfirst.py::test_foo - assert False*",
            "FAILED test_exitfirst.py::test_foo - assert False",
            "* stopping after 2 failures*",
        ],
        consecutive=True,
    )
    result.stdout.no_fnmatch_line("*sub2*")  # sub2 not executed.


def test_do_not_swallow_pytest_exit(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        def test(subtests):
            with subtests.test():
                pytest.exit()

        def test2(): pass
        """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "* _pytest.outcomes.Exit *",
            "* 1 failed in *",
        ]
    )


def test_nested(pytester: pytest.Pytester) -> None:
    """
    Currently we do nothing special with nested subtests.

    This test only sediments how they work now, we might reconsider adding some kind of nesting support in the future.
    """
    pytester.makepyfile(
        """
        import pytest
        def test(subtests):
            with subtests.test("a"):
                with subtests.test("b"):
                    assert False, "b failed"
                assert False, "a failed"
        """
    )
    result = pytester.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "[b] SUBFAILED test_nested.py::test - AssertionError: b failed",
            "[a] SUBFAILED test_nested.py::test - AssertionError: a failed",
            "* 3 failed in *",
        ]
    )
