from __future__ import annotations

import pytest


class TestNameOnly:
    def test_name_only_failures(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail1():
                assert False
            def test_fail2():
                assert False
            def test_pass():
                assert True
            """
        )
        result = pytester.runpytest("--name-only")
        result.stdout.fnmatch_lines(
            [
                "=* FAILURES *=",
                "test_fail1",
                "test_fail2",
                "=* short test summary info *=",
            ]
        )

        output = result.stdout.str()
        failures_part = output.split("FAILURES")[1].split("short test summary info")[0]
        assert "test_fail1" in failures_part
        assert "test_fail2" in failures_part
        assert "assert False" not in failures_part
        assert "E       assert False" not in failures_part

    def test_name_only_errors(self, pytester: pytest.Pytester) -> None:
        p = pytester.makepyfile(
            test_error="""
            import pytest
            @pytest.fixture
            def bad_fixture():
                raise RuntimeError("error in fixture")
            def test_error(bad_fixture):
                pass
        """
        )
        result = pytester.runpytest(p, "--name-only")
        result.stdout.fnmatch_lines(
            [
                "=* ERRORS *=",
                "ERROR at setup of test_error",
                "=* short test summary info *=",
                "ERROR test_error.py::test_error - RuntimeError: error in fixture",
            ]
        )
        output = result.stdout.str()
        errors_part = output.split("ERRORS")[1].split("short test summary info")[0]
        assert "ERROR at setup of test_error" in errors_part
        assert "RuntimeError: error in fixture" not in errors_part

    def test_name_only_collection_error(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_syntax():
                assert
            """
        )
        result = pytester.runpytest("--name-only")
        result.stdout.fnmatch_lines(
            [
                "=* ERRORS *=",
                "ERROR collecting test_name_only_collection_error.py",
                "=* short test summary info *=",
                "ERROR test_name_only_collection_error.py",
            ]
        )
        output = result.stdout.str()
        errors_part = output.split("ERRORS")[1].split("short test summary info")[0]
        assert "ERROR collecting test_name_only_collection_error.py" in errors_part
        assert "SyntaxError" not in errors_part

    def test_name_only_with_tb_line(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail():
                assert False
            """
        )
        result = pytester.runpytest("--name-only", "--tb=line")
        result.stdout.fnmatch_lines(
            [
                "=* FAILURES *=",
                "test_fail",
            ]
        )
        output = result.stdout.str()
        failures_part = output.split("FAILURES")[1].split("short test summary info")[0]
        assert "test_fail" in failures_part
        assert "assert False" not in failures_part

    def test_name_only_with_verbose(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail():
                assert False
            """
        )
        result = pytester.runpytest("--name-only", "-v")
        result.stdout.fnmatch_lines(
            [
                "=* FAILURES *=",
                "test_fail",
                "=* short test summary info *=",
            ]
        )
        output = result.stdout.str()
        failures_part = output.split("FAILURES")[1].split("short test summary info")[0]
        assert "test_fail" in failures_part
        assert "assert False" not in failures_part

    def test_name_only_with_show_capture_no(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_fail():
                print("captured output")
                assert False
            """
        )
        result = pytester.runpytest("--name-only", "--show-capture=no")
        result.stdout.fnmatch_lines(
            [
                "=* FAILURES *=",
                "test_fail",
                "=* short test summary info *=",
            ]
        )
        output = result.stdout.str()
        failures_part = output.split("FAILURES")[1].split("short test summary info")[0]
        assert "test_fail" in failures_part
        assert "assert False" not in failures_part
        assert "captured output" not in failures_part
