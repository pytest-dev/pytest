from __future__ import absolute_import, division, print_function
import sys
import py
import _pytest
import pytest
import os
import shutil

pytest_plugins = ("pytester",)


class Helper(object):
    def check_readme(self, testdir):
        config = testdir.parseconfigure()
        readme = config.cache._cachedir.join("README.md")
        return readme.isfile()


class TestReadme(Helper):
    def test_readme_passed(self, testdir):
        testdir.tmpdir.join("test_a.py").write(
            _pytest._code.Source(
                """
            def test_always_passes():
                assert 1
        """
            )
        )
        result = testdir.runpytest()
        assert self.check_readme(testdir) == True

    def test_readme_failed(self, testdir):
        testdir.tmpdir.join("test_a.py").write(
            _pytest._code.Source(
                """
            def test_always_passes():
                assert 0
        """
            )
        )
        result = testdir.runpytest()
        assert self.check_readme(testdir) == True
