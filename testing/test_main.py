import argparse
from typing import Optional

import pytest
from _pytest.config import ExitCode
from _pytest.main import validate_basetemp
from _pytest.pytester import Testdir


@pytest.mark.parametrize(
    "ret_exc",
    (
        pytest.param((None, ValueError)),
        pytest.param((42, SystemExit)),
        pytest.param((False, SystemExit)),
    ),
)
def test_wrap_session_notify_exception(ret_exc, testdir):
    returncode, exc = ret_exc
    c1 = testdir.makeconftest(
        """
        import pytest

        def pytest_sessionstart():
            raise {exc}("boom")

        def pytest_internalerror(excrepr, excinfo):
            returncode = {returncode!r}
            if returncode is not False:
                pytest.exit("exiting after %s..." % excinfo.typename, returncode={returncode!r})
    """.format(
            returncode=returncode, exc=exc.__name__
        )
    )
    result = testdir.runpytest()
    if returncode:
        assert result.ret == returncode
    else:
        assert result.ret == ExitCode.INTERNAL_ERROR
    assert result.stdout.lines[0] == "INTERNALERROR> Traceback (most recent call last):"

    if exc == SystemExit:
        assert result.stdout.lines[-3:] == [
            'INTERNALERROR>   File "{}", line 4, in pytest_sessionstart'.format(c1),
            'INTERNALERROR>     raise SystemExit("boom")',
            "INTERNALERROR> SystemExit: boom",
        ]
    else:
        assert result.stdout.lines[-3:] == [
            'INTERNALERROR>   File "{}", line 4, in pytest_sessionstart'.format(c1),
            'INTERNALERROR>     raise ValueError("boom")',
            "INTERNALERROR> ValueError: boom",
        ]
    if returncode is False:
        assert result.stderr.lines == ["mainloop: caught unexpected SystemExit!"]
    else:
        assert result.stderr.lines == ["Exit: exiting after {}...".format(exc.__name__)]


@pytest.mark.parametrize("returncode", (None, 42))
def test_wrap_session_exit_sessionfinish(
    returncode: Optional[int], testdir: Testdir
) -> None:
    testdir.makeconftest(
        """
        import pytest
        def pytest_sessionfinish():
            pytest.exit(msg="exit_pytest_sessionfinish", returncode={returncode})
    """.format(
            returncode=returncode
        )
    )
    result = testdir.runpytest()
    if returncode:
        assert result.ret == returncode
    else:
        assert result.ret == ExitCode.NO_TESTS_COLLECTED
    assert result.stdout.lines[-1] == "collected 0 items"
    assert result.stderr.lines == ["Exit: exit_pytest_sessionfinish"]


@pytest.mark.parametrize("basetemp", ["foo", "foo/bar"])
def test_validate_basetemp_ok(tmp_path, basetemp, monkeypatch):
    monkeypatch.chdir(str(tmp_path))
    validate_basetemp(tmp_path / basetemp)


@pytest.mark.parametrize("basetemp", ["", ".", ".."])
def test_validate_basetemp_fails(tmp_path, basetemp, monkeypatch):
    monkeypatch.chdir(str(tmp_path))
    msg = "basetemp must not be empty, the current working directory or any parent directory of it"
    with pytest.raises(argparse.ArgumentTypeError, match=msg):
        if basetemp:
            basetemp = tmp_path / basetemp
        validate_basetemp(basetemp)


def test_validate_basetemp_integration(testdir):
    result = testdir.runpytest("--basetemp=.")
    result.stderr.fnmatch_lines("*basetemp must not be*")
