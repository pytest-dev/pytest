from __future__ import annotations

import sys
from typing import Literal

from _pytest.subtests import SubtestContext
from _pytest.subtests import SubtestReport
import pytest


IS_PY311 = sys.version_info[:2] >= (3, 11)


def test_failures(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "120")
    pytester.makepyfile(
        """
        def test_foo(subtests):
            with subtests.test("foo subtest"):
                assert False, "foo subtest failure"

        def test_bar(subtests):
            with subtests.test("bar subtest"):
                assert False, "bar subtest failure"
            assert False, "test_bar also failed"

        def test_zaz(subtests):
            with subtests.test("zaz subtest"):
                pass
        """
    )
    summary_lines = [
        "*=== FAILURES ===*",
        #
        "*___ test_foo [[]foo subtest[]] ___*",
        "*AssertionError: foo subtest failure",
        #
        "*___ test_foo ___*",
        "contains 1 failed subtest",
        #
        "*___ test_bar [[]bar subtest[]] ___*",
        "*AssertionError: bar subtest failure",
        #
        "*___ test_bar ___*",
        "*AssertionError: test_bar also failed",
        #
        "*=== short test summary info ===*",
        "SUBFAILED[[]foo subtest[]] test_*.py::test_foo - AssertionError*",
        "FAILED test_*.py::test_foo - contains 1 failed subtest",
        "SUBFAILED[[]bar subtest[]] test_*.py::test_bar - AssertionError*",
        "FAILED test_*.py::test_bar - AssertionError*",
    ]
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        [
            "test_*.py uFuF.    *     [[]100%[]]",
            *summary_lines,
            "* 4 failed, 1 passed in *",
        ]
    )

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "test_*.py::test_foo SUBFAILED[[]foo subtest[]]    *     [[] 33%[]]",
            "test_*.py::test_foo FAILED                        *     [[] 33%[]]",
            "test_*.py::test_bar SUBFAILED[[]bar subtest[]]    *     [[] 66%[]]",
            "test_*.py::test_bar FAILED                        *     [[] 66%[]]",
            "test_*.py::test_zaz SUBPASSED[[]zaz subtest[]]    *     [[]100%[]]",
            "test_*.py::test_zaz PASSED                        *     [[]100%[]]",
            *summary_lines,
            "* 4 failed, 1 passed, 1 subtests passed in *",
        ]
    )
    pytester.makeini(
        """
        [pytest]
        verbosity_subtests = 0
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "test_*.py::test_foo SUBFAILED[[]foo subtest[]]    *     [[] 33%[]]",
            "test_*.py::test_foo FAILED                        *     [[] 33%[]]",
            "test_*.py::test_bar SUBFAILED[[]bar subtest[]]    *     [[] 66%[]]",
            "test_*.py::test_bar FAILED                        *     [[] 66%[]]",
            "test_*.py::test_zaz PASSED                        *     [[]100%[]]",
            *summary_lines,
            "* 4 failed, 1 passed in *",
        ]
    )
    result.stdout.no_fnmatch_line("test_*.py::test_zaz SUBPASSED[[]zaz subtest[]]*")


def test_passes(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "120")
    pytester.makepyfile(
        """
        def test_foo(subtests):
            with subtests.test("foo subtest"):
                pass

        def test_bar(subtests):
            with subtests.test("bar subtest"):
                pass
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        [
            "test_*.py ..    *     [[]100%[]]",
            "* 2 passed in *",
        ]
    )

    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo SUBPASSED[[]foo subtest[]]      * [[] 50%[]]",
            "*.py::test_foo PASSED                          * [[] 50%[]]",
            "*.py::test_bar SUBPASSED[[]bar subtest[]]      * [[]100%[]]",
            "*.py::test_bar PASSED                          * [[]100%[]]",
            "* 2 passed, 2 subtests passed in *",
        ]
    )

    pytester.makeini(
        """
        [pytest]
        verbosity_subtests = 0
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo PASSED                          * [[] 50%[]]",
            "*.py::test_bar PASSED                          * [[]100%[]]",
            "* 2 passed in *",
        ]
    )
    result.stdout.no_fnmatch_line("*.py::test_foo SUBPASSED[[]foo subtest[]]*")
    result.stdout.no_fnmatch_line("*.py::test_bar SUBPASSED[[]bar subtest[]]*")


def test_skip(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "120")
    pytester.makepyfile(
        """
        import pytest
        def test_foo(subtests):
            with subtests.test("foo subtest"):
                pytest.skip("skip foo subtest")

        def test_bar(subtests):
            with subtests.test("bar subtest"):
                pytest.skip("skip bar subtest")
            pytest.skip("skip test_bar")
        """
    )
    result = pytester.runpytest("-ra")
    result.stdout.fnmatch_lines(
        [
            "test_*.py .s    *     [[]100%[]]",
            "*=== short test summary info ===*",
            "SKIPPED [[]1[]] test_skip.py:9: skip test_bar",
            "* 1 passed, 1 skipped in *",
        ]
    )

    result = pytester.runpytest("-v", "-ra")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo SUBSKIPPED[[]foo subtest[]] (skip foo subtest)  * [[] 50%[]]",
            "*.py::test_foo PASSED                                          * [[] 50%[]]",
            "*.py::test_bar SUBSKIPPED[[]bar subtest[]] (skip bar subtest)  * [[]100%[]]",
            "*.py::test_bar SKIPPED (skip test_bar)                         * [[]100%[]]",
            "*=== short test summary info ===*",
            "SUBSKIPPED[[]foo subtest[]] [[]1[]] *.py:*: skip foo subtest",
            "SUBSKIPPED[[]foo subtest[]] [[]1[]] *.py:*: skip bar subtest",
            "SUBSKIPPED[[]foo subtest[]] [[]1[]] *.py:*: skip test_bar",
            "* 1 passed, 3 skipped in *",
        ]
    )

    pytester.makeini(
        """
        [pytest]
        verbosity_subtests = 0
        """
    )
    result = pytester.runpytest("-v", "-ra")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo PASSED                          * [[] 50%[]]",
            "*.py::test_bar SKIPPED (skip test_bar)         * [[]100%[]]",
            "*=== short test summary info ===*",
            "* 1 passed, 1 skipped in *",
        ]
    )
    result.stdout.no_fnmatch_line("*.py::test_foo SUBPASSED[[]foo subtest[]]*")
    result.stdout.no_fnmatch_line("*.py::test_bar SUBPASSED[[]bar subtest[]]*")
    result.stdout.no_fnmatch_line(
        "SUBSKIPPED[[]foo subtest[]] [[]1[]] *.py:*: skip foo subtest"
    )
    result.stdout.no_fnmatch_line(
        "SUBSKIPPED[[]foo subtest[]] [[]1[]] *.py:*: skip test_bar"
    )


def test_xfail(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLUMNS", "120")
    pytester.makepyfile(
        """
        import pytest
        def test_foo(subtests):
            with subtests.test("foo subtest"):
                pytest.xfail("xfail foo subtest")

        def test_bar(subtests):
            with subtests.test("bar subtest"):
                pytest.xfail("xfail bar subtest")
            pytest.xfail("xfail test_bar")
        """
    )
    result = pytester.runpytest("-ra")
    result.stdout.fnmatch_lines(
        [
            "test_*.py .x    *     [[]100%[]]",
            "*=== short test summary info ===*",
            "* 1 passed, 1 xfailed in *",
        ]
    )

    result = pytester.runpytest("-v", "-ra")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo SUBXFAIL[[]foo subtest[]] (xfail foo subtest)    * [[] 50%[]]",
            "*.py::test_foo PASSED                                           * [[] 50%[]]",
            "*.py::test_bar SUBXFAIL[[]bar subtest[]] (xfail bar subtest)    * [[]100%[]]",
            "*.py::test_bar XFAIL (xfail test_bar)                           * [[]100%[]]",
            "*=== short test summary info ===*",
            "SUBXFAIL[[]foo subtest[]] *.py::test_foo - xfail foo subtest",
            "SUBXFAIL[[]bar subtest[]] *.py::test_bar - xfail bar subtest",
            "XFAIL *.py::test_bar - xfail test_bar",
            "* 1 passed, 3 xfailed in *",
        ]
    )

    pytester.makeini(
        """
        [pytest]
        verbosity_subtests = 0
        """
    )
    result = pytester.runpytest("-v", "-ra")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo PASSED                          * [[] 50%[]]",
            "*.py::test_bar XFAIL (xfail test_bar)         * [[]100%[]]",
            "*=== short test summary info ===*",
            "* 1 passed, 1 xfailed in *",
        ]
    )
    result.stdout.no_fnmatch_line(
        "SUBXFAIL[[]foo subtest[]] *.py::test_foo - xfail foo subtest"
    )
    result.stdout.no_fnmatch_line(
        "SUBXFAIL[[]bar subtest[]] *.py::test_bar - xfail bar subtest"
    )


def test_typing_exported(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        from pytest import Subtests

        def test_typing_exported(subtests: Subtests) -> None:
            assert isinstance(subtests, Subtests)
        """
    )
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*1 passed*"])


def test_subtests_and_parametrization(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COLUMNS", "120")
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
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo[[]0[]] SUBFAILED[[]custom[]] (i=1) *[[] 50%[]]",
            "*.py::test_foo[[]0[]] FAILED                      *[[] 50%[]]",
            "*.py::test_foo[[]1[]] SUBFAILED[[]custom[]] (i=1) *[[]100%[]]",
            "*.py::test_foo[[]1[]] FAILED                      *[[]100%[]]",
            "contains 1 failed subtest",
            "* 4 failed, 4 subtests passed in *",
        ]
    )

    pytester.makeini(
        """
        [pytest]
        verbosity_subtests = 0
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*.py::test_foo[[]0[]] SUBFAILED[[]custom[]] (i=1) *[[] 50%[]]",
            "*.py::test_foo[[]0[]] FAILED                      *[[] 50%[]]",
            "*.py::test_foo[[]1[]] SUBFAILED[[]custom[]] (i=1) *[[]100%[]]",
            "*.py::test_foo[[]1[]] FAILED                      *[[]100%[]]",
            "contains 1 failed subtest",
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

    def test_failures(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COLUMNS", "120")
        pytester.makepyfile(
            """
            from unittest import TestCase

            class T(TestCase):
                def test_foo(self):
                    with self.subTest("foo subtest"):
                        assert False, "foo subtest failure"

                def test_bar(self):
                    with self.subTest("bar subtest"):
                        assert False, "bar subtest failure"
                    assert False, "test_bar also failed"

                def test_zaz(self):
                    with self.subTest("zaz subtest"):
                        pass
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "* 3 failed, 2 passed in *",
            ]
        )

    def test_passes(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COLUMNS", "120")
        pytester.makepyfile(
            """
            from unittest import TestCase

            class T(TestCase):
                def test_foo(self):
                    with self.subTest("foo subtest"):
                        pass

                def test_bar(self):
                    with self.subTest("bar subtest"):
                        pass

                def test_zaz(self):
                    with self.subTest("zaz subtest"):
                        pass
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "* 3 passed in *",
            ]
        )

    def test_skip(
        self,
        pytester: pytest.Pytester,
    ) -> None:
        pytester.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            if i % 2 == 0:
                                self.skipTest('even number')
        """
        )
        # This output might change #13756.
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["* 1 passed in *"])

    def test_non_subtest_skip(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COLUMNS", "120")
        pytester.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    with self.subTest(msg="subtest"):
                        assert False, "failed subtest"
                    self.skipTest('non-subtest skip')
        """
        )
        # This output might change #13756.
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "SUBFAILED[[]subtest[]] test_non_subtest_skip.py::T::test_foo*",
                "* 1 failed, 1 skipped in *",
            ]
        )

    def test_xfail(
        self,
        pytester: pytest.Pytester,
    ) -> None:
        pytester.makepyfile(
            """
            import pytest
            from unittest import expectedFailure, TestCase

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
        # This output might change #13756.
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(["* 1 xfailed in *"])

    def test_only_original_skip_is_called(
        self,
        pytester: pytest.Pytester,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Regression test for pytest-dev/pytest-subtests#173."""
        monkeypatch.setenv("COLUMNS", "120")
        pytester.makepyfile(
            """
            import unittest
            from unittest import TestCase

            @unittest.skip("skip this test")
            class T(unittest.TestCase):
                def test_foo(self):
                    assert 1 == 2
        """
        )
        result = pytester.runpytest("-v", "-rsf")
        result.stdout.fnmatch_lines(
            ["SKIPPED [1] test_only_original_skip_is_called.py:6: skip this test"]
        )

    def test_skip_with_failure(
        self,
        pytester: pytest.Pytester,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("COLUMNS", "120")
        pytester.makepyfile(
            """
            import pytest
            from unittest import TestCase

            class T(TestCase):
                def test_foo(self):
                    with self.subTest("subtest 1"):
                        self.skipTest(f"skip subtest 1")
                    with self.subTest("subtest 2"):
                        assert False, "fail subtest 2"
            """
        )

        result = pytester.runpytest("-ra")
        result.stdout.fnmatch_lines(
            [
                "*.py u.                                                           *            [[]100%[]]",
                "*=== short test summary info ===*",
                "SUBFAILED[[]subtest 2[]] *.py::T::test_foo - AssertionError: fail subtest 2",
                "* 1 failed, 1 passed in *",
            ]
        )

        result = pytester.runpytest("-v", "-ra")
        result.stdout.fnmatch_lines(
            [
                "*.py::T::test_foo SUBSKIPPED[[]subtest 1[]] (skip subtest 1)      *            [[]100%[]]",
                "*.py::T::test_foo SUBFAILED[[]subtest 2[]]                        *            [[]100%[]]",
                "*.py::T::test_foo PASSED                                          *            [[]100%[]]",
                "SUBSKIPPED[[]subtest 1[]] [[]1[]] *.py:*: skip subtest 1",
                "SUBFAILED[[]subtest 2[]] *.py::T::test_foo - AssertionError: fail subtest 2",
                "* 1 failed, 1 passed, 1 skipped in *",
            ]
        )

        pytester.makeini(
            """
            [pytest]
            verbosity_subtests = 0
            """
        )
        result = pytester.runpytest("-v", "-ra")
        result.stdout.fnmatch_lines(
            [
                "*.py::T::test_foo SUBFAILED[[]subtest 2[]]                        *            [[]100%[]]",
                "*.py::T::test_foo PASSED                                          *            [[]100%[]]",
                "*=== short test summary info ===*",
                r"SUBFAILED[[]subtest 2[]] *.py::T::test_foo - AssertionError: fail subtest 2",
                r"* 1 failed, 1 passed in *",
            ]
        )
        result.stdout.no_fnmatch_line(
            "*.py::T::test_foo SUBSKIPPED[[]subtest 1[]] (skip subtest 1) * [[]100%[]]"
        )
        result.stdout.no_fnmatch_line(
            "SUBSKIPPED[[]subtest 1[]] [[]1[]] *.py:*: skip subtest 1"
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

    @pytest.mark.parametrize("mode", ["fd", "sys"])
    def test_capturing(self, pytester: pytest.Pytester, mode: str) -> None:
        self.create_file(pytester)
        result = pytester.runpytest(f"--capture={mode}")
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
                "*2 failed in*",
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
            "SUBFAILED*[[]sub1[]] *.py::test_foo - assert False*",
            "FAILED *.py::test_foo - assert False",
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
            "SUBFAILED[b] test_nested.py::test - AssertionError: b failed",
            "SUBFAILED[a] test_nested.py::test - AssertionError: a failed",
            "* 3 failed in *",
        ]
    )


def test_serialization() -> None:
    from _pytest.subtests import pytest_report_from_serializable
    from _pytest.subtests import pytest_report_to_serializable

    report = SubtestReport(
        "test_foo::test_foo",
        ("test_foo.py", 12, ""),
        keywords={},
        outcome="passed",
        when="call",
        longrepr=None,
        context=SubtestContext(msg="custom message", kwargs=dict(i=10)),
    )
    data = pytest_report_to_serializable(report)
    assert data is not None
    new_report = pytest_report_from_serializable(data)
    assert new_report is not None
    assert new_report.context == SubtestContext(msg="custom message", kwargs=dict(i=10))
