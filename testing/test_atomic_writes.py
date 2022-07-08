"""
Module copied over from https://github.com/untitaker/python-atomicwrites, which has become
unmaintained.

Since then, we have made changes to simplify the code, focusing on pytest's use-case.
"""
import errno
import os
from pathlib import Path

import pytest
from _pytest.atomic_writes import atomic_write


def test_atomic_write(tmp_path: Path) -> None:
    fname = tmp_path.joinpath("ha")
    for i in range(2):
        with atomic_write(str(fname), overwrite=True) as f:
            f.write("hoho")

    with pytest.raises(OSError) as excinfo:
        with atomic_write(str(fname), overwrite=False) as f:
            f.write("haha")

    assert excinfo.value.errno == errno.EEXIST

    assert fname.read_text() == "hoho"
    assert len(list(tmp_path.iterdir())) == 1


def test_teardown(tmp_path: Path) -> None:
    fname = tmp_path.joinpath("ha")
    with pytest.raises(AssertionError):
        with atomic_write(str(fname), overwrite=True):
            assert False

    assert not list(tmp_path.iterdir())


def test_replace_simultaneously_created_file(tmp_path: Path) -> None:
    fname = tmp_path.joinpath("ha")
    with atomic_write(str(fname), overwrite=True) as f:
        f.write("hoho")
        fname.write_text("harhar")
        assert fname.read_text() == "harhar"
    assert fname.read_text() == "hoho"
    assert len(list(tmp_path.iterdir())) == 1


def test_dont_remove_simultaneously_created_file(tmp_path: Path) -> None:
    fname = tmp_path.joinpath("ha")
    with pytest.raises(OSError) as excinfo:
        with atomic_write(str(fname), overwrite=False) as f:
            f.write("hoho")
            fname.write_text("harhar")
            assert fname.read_text() == "harhar"

    assert excinfo.value.errno == errno.EEXIST
    assert fname.read_text() == "harhar"
    assert len(list(tmp_path.iterdir())) == 1


# Verify that nested exceptions during rollback do not overwrite the initial
# exception that triggered a rollback.
def test_open_reraise(tmp_path: Path) -> None:
    fname = tmp_path.joinpath("ha")
    with pytest.raises(AssertionError):
        aw = atomic_write(str(fname), overwrite=False)
        with aw:
            # Mess with internals, so commit will trigger a ValueError. We're
            # testing that the initial AssertionError triggered below is
            # propagated up the stack, not the second exception triggered
            # during commit.
            aw.rollback = lambda: 1 / 0
            # Now trigger our own exception.
            assert False, "Intentional failure for testing purposes"


def test_atomic_write_in_pwd(tmp_path: Path) -> None:
    orig_curdir = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        fname = "ha"
        for i in range(2):
            with atomic_write(str(fname), overwrite=True) as f:
                f.write("hoho")

        with pytest.raises(OSError) as excinfo:
            with atomic_write(str(fname), overwrite=False) as f:
                f.write("haha")

        assert excinfo.value.errno == errno.EEXIST

        with open(fname) as f:
            assert f.read() == "hoho"
        assert len(list(tmp_path.iterdir())) == 1
    finally:
        os.chdir(orig_curdir)
