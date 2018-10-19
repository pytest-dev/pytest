# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import sys

import six

import py
import pytest


@pytest.mark.skipif(
    not hasattr(py.path.local, "mksymlinkto"),
    reason="symlink not available on this platform",
)
def test_624(testdir):
    """
    Runs tests in the following directory tree:

        testdir/
          test_noop.py
          symlink-0 -> .
          symlink-1 -> .

    On Linux, the maximum number of symlinks in a path is 40, after which ELOOP
    is returned when trying to read the path. This means that if we walk the
    directory tree naively, following symlinks, naively, this will attempt to
    visit test_noop.py via 2 ** 41 paths:

        testdir/symlink-0/test_noop.py
        testdir/symlink-1/test_noop.py
        testdir/symlink-0/symlink-0/test_noop.py
        testdir/symlink-0/symlink-1/test_noop.py
        .. and eventually ..
        testdir/symlink-0/.. 2 ** 39 more combinations ../test_noop.py
        testdir/symlink-1/.. 2 ** 39 more combinations ../test_noop.py

    Instead, we should stop recursing when we reach a directory we've seen
    before.  In this test, this means visiting the test once at the root, and
    once via a symlink, then stopping.
    """

    test_noop_py = testdir.makepyfile(test_noop="def test_noop():\n    pass")

    # dummy check that we can actually create symlinks: on Windows `py.path.mksymlinkto` is
    # available, but normal users require special admin privileges to create symlinks.
    if sys.platform == "win32":
        try:
            (testdir.tmpdir / ".dummy").mksymlinkto(test_noop_py)
        except OSError as e:
            pytest.skip(six.text_type(e.args[0]))

    for i in range(2):
        (testdir.tmpdir / "symlink-{}".format(i)).mksymlinkto(testdir.tmpdir)

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)
