# -*- coding: utf8 -*-
from __future__ import unicode_literals

import sys

import pytest


WARNINGS_SUMMARY_HEADER = "warnings summary"


@pytest.fixture
def pyfile_with_warnings(testdir, request):
    """
    Create a test file which calls a function in a module which generates warnings.
    """
    testdir.syspathinsert()
    test_name = request.function.__name__
    module_name = test_name.lstrip("test_") + "_module"
    testdir.makepyfile(
        **{
            module_name: """
            import warnings
            def foo():
                warnings.warn(UserWarning("user warning"))
                warnings.warn(RuntimeWarning("runtime warning"))
                return 1
        """,
            test_name: """
            import {module_name}
            def test_func():
                assert {module_name}.foo() == 1
        """.format(
                module_name=module_name
            ),
        }
    )


@pytest.mark.filterwarnings("default")
def test_normal_flow(testdir, pyfile_with_warnings):
    """
    Check that the warnings section is displayed.
    """
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
            "*normal_flow_module.py:3: UserWarning: user warning",
            '*  warnings.warn(UserWarning("user warning"))',
            "*normal_flow_module.py:4: RuntimeWarning: runtime warning",
            '*  warnings.warn(RuntimeWarning("runtime warning"))',
            "* 1 passed, 2 warnings*",
        ]
    )


@pytest.mark.filterwarnings("always")
def test_setup_teardown_warnings(testdir, pyfile_with_warnings):
    testdir.makepyfile(
        """
        import warnings
        import pytest

        @pytest.fixture
        def fix():
            warnings.warn(UserWarning("warning during setup"))
            yield
            warnings.warn(UserWarning("warning during teardown"))

        def test_func(fix):
            pass
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
            "*test_setup_teardown_warnings.py:6: UserWarning: warning during setup",
            '*warnings.warn(UserWarning("warning during setup"))',
            "*test_setup_teardown_warnings.py:8: UserWarning: warning during teardown",
            '*warnings.warn(UserWarning("warning during teardown"))',
            "* 1 passed, 2 warnings*",
        ]
    )


@pytest.mark.parametrize("method", ["cmdline", "ini"])
def test_as_errors(testdir, pyfile_with_warnings, method):
    args = ("-W", "error") if method == "cmdline" else ()
    if method == "ini":
        testdir.makeini(
            """
            [pytest]
            filterwarnings= error
            """
        )
    result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines(
        [
            "E       UserWarning: user warning",
            "as_errors_module.py:3: UserWarning",
            "* 1 failed in *",
        ]
    )


@pytest.mark.parametrize("method", ["cmdline", "ini"])
def test_ignore(testdir, pyfile_with_warnings, method):
    args = ("-W", "ignore") if method == "cmdline" else ()
    if method == "ini":
        testdir.makeini(
            """
        [pytest]
        filterwarnings= ignore
        """
        )

    result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines(["* 1 passed in *"])
    assert WARNINGS_SUMMARY_HEADER not in result.stdout.str()


@pytest.mark.skipif(
    sys.version_info < (3, 0), reason="warnings message is unicode is ok in python3"
)
@pytest.mark.filterwarnings("always")
def test_unicode(testdir, pyfile_with_warnings):
    testdir.makepyfile(
        """
        # -*- coding: utf8 -*-
        import warnings
        import pytest


        @pytest.fixture
        def fix():
            warnings.warn(u"测试")
            yield

        def test_func(fix):
            pass
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
            "*test_unicode.py:8: UserWarning: \u6d4b\u8bd5*",
            "* 1 passed, 1 warnings*",
        ]
    )


@pytest.mark.skipif(
    sys.version_info >= (3, 0),
    reason="warnings message is broken as it is not str instance",
)
def test_py2_unicode(testdir, pyfile_with_warnings):
    if getattr(sys, "pypy_version_info", ())[:2] == (5, 9) and sys.platform.startswith(
        "win"
    ):
        pytest.xfail("fails with unicode error on PyPy2 5.9 and Windows (#2905)")
    testdir.makepyfile(
        """
        # -*- coding: utf8 -*-
        import warnings
        import pytest


        @pytest.fixture
        def fix():
            warnings.warn(u"测试")
            yield

        @pytest.mark.filterwarnings('always')
        def test_func(fix):
            pass
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
            "*test_py2_unicode.py:8: UserWarning: \\u6d4b\\u8bd5",
            '*warnings.warn(u"\u6d4b\u8bd5")',
            "*warnings.py:*: UnicodeWarning: Warning is using unicode non*",
            "* 1 passed, 2 warnings*",
        ]
    )


def test_py2_unicode_ascii(testdir):
    """Ensure that our warning about 'unicode warnings containing non-ascii messages'
    does not trigger with ascii-convertible messages"""
    testdir.makeini("[pytest]")
    testdir.makepyfile(
        """
        import pytest
        import warnings

        @pytest.mark.filterwarnings('always')
        def test_func():
            warnings.warn(u"hello")
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
            '*warnings.warn(u"hello")',
            "* 1 passed, 1 warnings in*",
        ]
    )


def test_works_with_filterwarnings(testdir):
    """Ensure our warnings capture does not mess with pre-installed filters (#2430)."""
    testdir.makepyfile(
        """
        import warnings

        class MyWarning(Warning):
            pass

        warnings.filterwarnings("error", category=MyWarning)

        class TestWarnings(object):
            def test_my_warning(self):
                try:
                    warnings.warn(MyWarning("warn!"))
                    assert False
                except MyWarning:
                    assert True
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*== 1 passed in *"])


@pytest.mark.parametrize("default_config", ["ini", "cmdline"])
def test_filterwarnings_mark(testdir, default_config):
    """
    Test ``filterwarnings`` mark works and takes precedence over command line and ini options.
    """
    if default_config == "ini":
        testdir.makeini(
            """
            [pytest]
            filterwarnings = always
        """
        )
    testdir.makepyfile(
        """
        import warnings
        import pytest

        @pytest.mark.filterwarnings('ignore::RuntimeWarning')
        def test_ignore_runtime_warning():
            warnings.warn(RuntimeWarning())

        @pytest.mark.filterwarnings('error')
        def test_warning_error():
            warnings.warn(RuntimeWarning())

        def test_show_warning():
            warnings.warn(RuntimeWarning())
    """
    )
    result = testdir.runpytest("-W always" if default_config == "cmdline" else "")
    result.stdout.fnmatch_lines(["*= 1 failed, 2 passed, 1 warnings in *"])


def test_non_string_warning_argument(testdir):
    """Non-str argument passed to warning breaks pytest (#2956)"""
    testdir.makepyfile(
        """
        import warnings
        import pytest

        def test():
            warnings.warn(UserWarning(1, u'foo'))
    """
    )
    result = testdir.runpytest("-W", "always")
    result.stdout.fnmatch_lines(["*= 1 passed, 1 warnings in *"])


def test_filterwarnings_mark_registration(testdir):
    """Ensure filterwarnings mark is registered"""
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.filterwarnings('error')
        def test_func():
            pass
    """
    )
    result = testdir.runpytest("--strict")
    assert result.ret == 0


@pytest.mark.filterwarnings("always")
def test_warning_captured_hook(testdir):
    testdir.makeconftest(
        """
        from _pytest.warnings import _issue_config_warning
        def pytest_configure(config):
            _issue_config_warning(UserWarning("config warning"), config)
    """
    )
    testdir.makepyfile(
        """
        import pytest, warnings

        warnings.warn(UserWarning("collect warning"))

        @pytest.fixture
        def fix():
            warnings.warn(UserWarning("setup warning"))
            yield 1
            warnings.warn(UserWarning("teardown warning"))

        def test_func(fix):
            warnings.warn(UserWarning("call warning"))
            assert fix == 1
        """
    )

    collected = []

    class WarningCollector:
        def pytest_warning_captured(self, warning_message, when, item):
            imge_name = item.name if item is not None else ""
            collected.append((str(warning_message.message), when, imge_name))

    result = testdir.runpytest(plugins=[WarningCollector()])
    result.stdout.fnmatch_lines(["*1 passed*"])

    expected = [
        ("config warning", "config", ""),
        ("collect warning", "collect", ""),
        ("setup warning", "runtest", "test_func"),
        ("call warning", "runtest", "test_func"),
        ("teardown warning", "runtest", "test_func"),
    ]
    assert collected == expected


@pytest.mark.filterwarnings("always")
def test_collection_warnings(testdir):
    """
    Check that we also capture warnings issued during test collection (#3251).
    """
    testdir.makepyfile(
        """
        import warnings

        warnings.warn(UserWarning("collection warning"))

        def test_foo():
            pass
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
            "*collection_warnings.py:3: UserWarning: collection warning",
            '  warnings.warn(UserWarning("collection warning"))',
            "* 1 passed, 1 warnings*",
        ]
    )


@pytest.mark.filterwarnings("always")
def test_mark_regex_escape(testdir):
    """@pytest.mark.filterwarnings should not try to escape regex characters (#3936)"""
    testdir.makepyfile(
        r"""
        import pytest, warnings

        @pytest.mark.filterwarnings(r"ignore:some \(warning\)")
        def test_foo():
            warnings.warn(UserWarning("some (warning)"))
    """
    )
    result = testdir.runpytest()
    assert WARNINGS_SUMMARY_HEADER not in result.stdout.str()


@pytest.mark.filterwarnings("default")
@pytest.mark.parametrize("ignore_pytest_warnings", ["no", "ini", "cmdline"])
def test_hide_pytest_internal_warnings(testdir, ignore_pytest_warnings):
    """Make sure we can ignore internal pytest warnings using a warnings filter."""
    testdir.makepyfile(
        """
        import pytest
        import warnings

        warnings.warn(pytest.PytestWarning("some internal warning"))

        def test_bar():
            pass
    """
    )
    if ignore_pytest_warnings == "ini":
        testdir.makeini(
            """
            [pytest]
            filterwarnings = ignore::pytest.PytestWarning
        """
        )
    args = (
        ["-W", "ignore::pytest.PytestWarning"]
        if ignore_pytest_warnings == "cmdline"
        else []
    )
    result = testdir.runpytest(*args)
    if ignore_pytest_warnings != "no":
        assert WARNINGS_SUMMARY_HEADER not in result.stdout.str()
    else:
        result.stdout.fnmatch_lines(
            [
                "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
                "*test_hide_pytest_internal_warnings.py:4: PytestWarning: some internal warning",
                "* 1 passed, 1 warnings *",
            ]
        )


class TestDeprecationWarningsByDefault:
    """
    Note: all pytest runs are executed in a subprocess so we don't inherit warning filters
    from pytest's own test suite
    """

    def create_file(self, testdir, mark=""):
        testdir.makepyfile(
            """
            import pytest, warnings

            warnings.warn(DeprecationWarning("collection"))

            {mark}
            def test_foo():
                warnings.warn(PendingDeprecationWarning("test run"))
        """.format(
                mark=mark
            )
        )

    def test_shown_by_default(self, testdir):
        self.create_file(testdir)
        result = testdir.runpytest_subprocess()
        result.stdout.fnmatch_lines(
            [
                "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
                "*test_shown_by_default.py:3: DeprecationWarning: collection",
                "*test_shown_by_default.py:7: PendingDeprecationWarning: test run",
                "* 1 passed, 2 warnings*",
            ]
        )

    def test_hidden_by_ini(self, testdir):
        self.create_file(testdir)
        testdir.makeini(
            """
            [pytest]
            filterwarnings = once::UserWarning
        """
        )
        result = testdir.runpytest_subprocess()
        assert WARNINGS_SUMMARY_HEADER not in result.stdout.str()

    def test_hidden_by_mark(self, testdir):
        """Should hide the deprecation warning from the function, but the warning during collection should
        be displayed normally.
        """
        self.create_file(
            testdir, mark='@pytest.mark.filterwarnings("once::UserWarning")'
        )
        result = testdir.runpytest_subprocess()
        result.stdout.fnmatch_lines(
            [
                "*== %s ==*" % WARNINGS_SUMMARY_HEADER,
                "*test_hidden_by_mark.py:3: DeprecationWarning: collection",
                "* 1 passed, 1 warnings*",
            ]
        )

    def test_hidden_by_cmdline(self, testdir):
        self.create_file(testdir)
        result = testdir.runpytest_subprocess("-W", "once::UserWarning")
        assert WARNINGS_SUMMARY_HEADER not in result.stdout.str()

    def test_hidden_by_system(self, testdir, monkeypatch):
        self.create_file(testdir)
        monkeypatch.setenv(str("PYTHONWARNINGS"), str("once::UserWarning"))
        result = testdir.runpytest_subprocess()
        assert WARNINGS_SUMMARY_HEADER not in result.stdout.str()
