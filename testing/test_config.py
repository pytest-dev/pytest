import os
import re
import sys
import textwrap
from typing import Dict
from typing import List
from typing import Sequence

import py.path

import _pytest._code
import pytest
from _pytest.compat import importlib_metadata
from _pytest.config import _get_plugin_specs_as_list
from _pytest.config import _iter_rewritable_modules
from _pytest.config import Config
from _pytest.config import ConftestImportFailure
from _pytest.config import ExitCode
from _pytest.config.exceptions import UsageError
from _pytest.config.findpaths import determine_setup
from _pytest.config.findpaths import get_common_ancestor
from _pytest.config.findpaths import locate_config
from _pytest.pathlib import Path


class TestParseIni:
    @pytest.mark.parametrize(
        "section, filename", [("pytest", "pytest.ini"), ("tool:pytest", "setup.cfg")]
    )
    def test_getcfg_and_config(self, testdir, tmpdir, section, filename):
        sub = tmpdir.mkdir("sub")
        sub.chdir()
        tmpdir.join(filename).write(
            textwrap.dedent(
                """\
                [{section}]
                name = value
                """.format(
                    section=section
                )
            )
        )
        _, _, cfg = locate_config([sub])
        assert cfg["name"] == "value"
        config = testdir.parseconfigure(sub)
        assert config.inicfg["name"] == "value"

    def test_getcfg_empty_path(self):
        """correctly handle zero length arguments (a la pytest '')"""
        locate_config([""])

    def test_setupcfg_uses_toolpytest_with_pytest(self, testdir):
        p1 = testdir.makepyfile("def test(): pass")
        testdir.makefile(
            ".cfg",
            setup="""
                [tool:pytest]
                testpaths=%s
                [pytest]
                testpaths=ignored
        """
            % p1.basename,
        )
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(["*, configfile: setup.cfg, *", "* 1 passed in *"])
        assert result.ret == 0

    def test_append_parse_args(self, testdir, tmpdir, monkeypatch):
        monkeypatch.setenv("PYTEST_ADDOPTS", '--color no -rs --tb="short"')
        tmpdir.join("pytest.ini").write(
            textwrap.dedent(
                """\
                [pytest]
                addopts = --verbose
                """
            )
        )
        config = testdir.parseconfig(tmpdir)
        assert config.option.color == "no"
        assert config.option.reportchars == "s"
        assert config.option.tbstyle == "short"
        assert config.option.verbose

    def test_tox_ini_wrong_version(self, testdir):
        testdir.makefile(
            ".ini",
            tox="""
            [pytest]
            minversion=999.0
        """,
        )
        result = testdir.runpytest()
        assert result.ret != 0
        result.stderr.fnmatch_lines(
            ["*tox.ini: 'minversion' requires pytest-999.0, actual pytest-*"]
        )

    @pytest.mark.parametrize(
        "section, name",
        [("tool:pytest", "setup.cfg"), ("pytest", "tox.ini"), ("pytest", "pytest.ini")],
    )
    def test_ini_names(self, testdir, name, section):
        testdir.tmpdir.join(name).write(
            textwrap.dedent(
                """
            [{section}]
            minversion = 1.0
        """.format(
                    section=section
                )
            )
        )
        config = testdir.parseconfig()
        assert config.getini("minversion") == "1.0"

    def test_pyproject_toml(self, testdir):
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            minversion = "1.0"
        """
        )
        config = testdir.parseconfig()
        assert config.getini("minversion") == "1.0"

    def test_toxini_before_lower_pytestini(self, testdir):
        sub = testdir.tmpdir.mkdir("sub")
        sub.join("tox.ini").write(
            textwrap.dedent(
                """
            [pytest]
            minversion = 2.0
        """
            )
        )
        testdir.tmpdir.join("pytest.ini").write(
            textwrap.dedent(
                """
            [pytest]
            minversion = 1.5
        """
            )
        )
        config = testdir.parseconfigure(sub)
        assert config.getini("minversion") == "2.0"

    def test_ini_parse_error(self, testdir):
        testdir.tmpdir.join("pytest.ini").write("addopts = -x")
        result = testdir.runpytest()
        assert result.ret != 0
        result.stderr.fnmatch_lines(["ERROR: *pytest.ini:1: no section header defined"])

    @pytest.mark.xfail(reason="probably not needed")
    def test_confcutdir(self, testdir):
        sub = testdir.mkdir("sub")
        sub.chdir()
        testdir.makeini(
            """
            [pytest]
            addopts = --qwe
        """
        )
        result = testdir.inline_run("--confcutdir=.")
        assert result.ret == 0

    @pytest.mark.parametrize(
        "ini_file_text, invalid_keys, warning_output, exception_text",
        [
            (
                """
          [pytest]
          unknown_ini = value1
          another_unknown_ini = value2
          """,
                ["unknown_ini", "another_unknown_ini"],
                [
                    "=*= warnings summary =*=",
                    "*PytestConfigWarning:*Unknown config ini key: another_unknown_ini",
                    "*PytestConfigWarning:*Unknown config ini key: unknown_ini",
                ],
                "Unknown config ini key: another_unknown_ini",
            ),
            (
                """
          [pytest]
          unknown_ini = value1
          minversion = 5.0.0
          """,
                ["unknown_ini"],
                [
                    "=*= warnings summary =*=",
                    "*PytestConfigWarning:*Unknown config ini key: unknown_ini",
                ],
                "Unknown config ini key: unknown_ini",
            ),
            (
                """
          [some_other_header]
          unknown_ini = value1
          [pytest]
          minversion = 5.0.0
          """,
                [],
                [],
                "",
            ),
            (
                """
          [pytest]
          minversion = 5.0.0
          """,
                [],
                [],
                "",
            ),
            (
                """
          [pytest]
          conftest_ini_key = 1
          """,
                [],
                [],
                "",
            ),
        ],
    )
    def test_invalid_ini_keys(
        self, testdir, ini_file_text, invalid_keys, warning_output, exception_text
    ):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("conftest_ini_key", "")
        """
        )
        testdir.tmpdir.join("pytest.ini").write(textwrap.dedent(ini_file_text))

        config = testdir.parseconfig()
        assert sorted(config._get_unknown_ini_keys()) == sorted(invalid_keys)

        result = testdir.runpytest()
        result.stdout.fnmatch_lines(warning_output)

        if exception_text:
            with pytest.raises(pytest.fail.Exception, match=exception_text):
                testdir.runpytest("--strict-config")
        else:
            testdir.runpytest("--strict-config")

    @pytest.mark.parametrize(
        "ini_file_text, exception_text",
        [
            (
                """
          [pytest]
          required_plugins = fakePlugin1 fakePlugin2
          """,
                "Missing required plugins: fakePlugin1, fakePlugin2",
            ),
            (
                """
          [pytest]
          required_plugins = a pytest-xdist z
          """,
                "Missing required plugins: a, z",
            ),
            (
                """
          [pytest]
          required_plugins = a q j b c z
          """,
                "Missing required plugins: a, b, c, j, q, z",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist
          """,
                "",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist==1.32.0
          """,
                "",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist>1.0.0,<2.0.0
          """,
                "",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist~=1.32.0 pytest-xdist==1.32.0 pytest-xdist!=0.0.1 pytest-xdist<=99.99.0
            pytest-xdist>=1.32.0 pytest-xdist<9.9.9 pytest-xdist>1.30.0 pytest-xdist===1.32.0
          """,
                "",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist>9.9.9 pytest-xdist==1.32.0 pytest-xdist==8.8.8
          """,
                "Missing required plugins: pytest-xdist==8.8.8, pytest-xdist>9.9.9",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist==aegsrgrsgs pytest-xdist==-1 pytest-xdist>2.1.1,>3.0.0
          """,
                "Missing required plugins: pytest-xdist==-1, pytest-xdist==aegsrgrsgs, pytest-xdist>2.1.1,>3.0.0",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist== pytest-xdist<=
          """,
                "Missing required plugins: pytest-xdist<=, pytest-xdist==",
            ),
            (
                """
          [pytest]
          required_plugins = pytest-xdist= pytest-xdist<
          """,
                "Missing required plugins: pytest-xdist<, pytest-xdist=",
            ),
            (
                """
          [some_other_header]
          required_plugins = wont be triggered
          [pytest]
          minversion = 5.0.0
          """,
                "",
            ),
            (
                """
          [pytest]
          minversion = 5.0.0
          """,
                "",
            ),
        ],
    )
    def test_missing_required_plugins(self, testdir, ini_file_text, exception_text):
        pytest.importorskip("xdist")

        testdir.tmpdir.join("pytest.ini").write(textwrap.dedent(ini_file_text))
        testdir.monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD")

        if exception_text:
            with pytest.raises(pytest.fail.Exception, match=exception_text):
                testdir.parseconfig()
        else:
            testdir.parseconfig()


class TestConfigCmdlineParsing:
    def test_parsing_again_fails(self, testdir):
        config = testdir.parseconfig()
        pytest.raises(AssertionError, lambda: config.parse([]))

    def test_explicitly_specified_config_file_is_loaded(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("custom", "")
        """
        )
        testdir.makeini(
            """
            [pytest]
            custom = 0
        """
        )
        testdir.makefile(
            ".ini",
            custom="""
            [pytest]
            custom = 1
        """,
        )
        config = testdir.parseconfig("-c", "custom.ini")
        assert config.getini("custom") == "1"

        testdir.makefile(
            ".cfg",
            custom_tool_pytest_section="""
            [tool:pytest]
            custom = 1
        """,
        )
        config = testdir.parseconfig("-c", "custom_tool_pytest_section.cfg")
        assert config.getini("custom") == "1"

        testdir.makefile(
            ".toml",
            custom="""
                [tool.pytest.ini_options]
                custom = 1
                value = [
                ]  # this is here on purpose, as it makes this an invalid '.ini' file
            """,
        )
        config = testdir.parseconfig("-c", "custom.toml")
        assert config.getini("custom") == "1"

    def test_absolute_win32_path(self, testdir):
        temp_ini_file = testdir.makefile(
            ".ini",
            custom="""
            [pytest]
            addopts = --version
        """,
        )
        from os.path import normpath

        temp_ini_file = normpath(str(temp_ini_file))
        ret = pytest.main(["-c", temp_ini_file])
        assert ret == ExitCode.OK


class TestConfigAPI:
    def test_config_trace(self, testdir) -> None:
        config = testdir.parseconfig()
        values = []  # type: List[str]
        config.trace.root.setwriter(values.append)
        config.trace("hello")
        assert len(values) == 1
        assert values[0] == "hello [config]\n"

    def test_config_getoption(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addoption("--hello", "-X", dest="hello")
        """
        )
        config = testdir.parseconfig("--hello=this")
        for x in ("hello", "--hello", "-X"):
            assert config.getoption(x) == "this"
        pytest.raises(ValueError, config.getoption, "qweqwe")

    def test_config_getoption_unicode(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addoption('--hello', type=str)
        """
        )
        config = testdir.parseconfig("--hello=this")
        assert config.getoption("hello") == "this"

    def test_config_getvalueorskip(self, testdir):
        config = testdir.parseconfig()
        pytest.raises(pytest.skip.Exception, config.getvalueorskip, "hello")
        verbose = config.getvalueorskip("verbose")
        assert verbose == config.option.verbose

    def test_config_getvalueorskip_None(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addoption("--hello")
        """
        )
        config = testdir.parseconfig()
        with pytest.raises(pytest.skip.Exception):
            config.getvalueorskip("hello")

    def test_getoption(self, testdir):
        config = testdir.parseconfig()
        with pytest.raises(ValueError):
            config.getvalue("x")
        assert config.getoption("x", 1) == 1

    def test_getconftest_pathlist(self, testdir, tmpdir):
        somepath = tmpdir.join("x", "y", "z")
        p = tmpdir.join("conftest.py")
        p.write("pathlist = ['.', %r]" % str(somepath))
        config = testdir.parseconfigure(p)
        assert config._getconftest_pathlist("notexist", path=tmpdir) is None
        pl = config._getconftest_pathlist("pathlist", path=tmpdir)
        print(pl)
        assert len(pl) == 2
        assert pl[0] == tmpdir
        assert pl[1] == somepath

    def test_addini(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("myname", "my new ini value")
        """
        )
        testdir.makeini(
            """
            [pytest]
            myname=hello
        """
        )
        config = testdir.parseconfig()
        val = config.getini("myname")
        assert val == "hello"
        pytest.raises(ValueError, config.getini, "other")

    def make_conftest_for_pathlist(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("paths", "my new ini value", type="pathlist")
                parser.addini("abc", "abc value")
        """
        )

    def test_addini_pathlist_ini_files(self, testdir):
        self.make_conftest_for_pathlist(testdir)
        p = testdir.makeini(
            """
            [pytest]
            paths=hello world/sub.py
        """
        )
        self.check_config_pathlist(testdir, p)

    def test_addini_pathlist_pyproject_toml(self, testdir):
        self.make_conftest_for_pathlist(testdir)
        p = testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            paths=["hello", "world/sub.py"]
        """
        )
        self.check_config_pathlist(testdir, p)

    def check_config_pathlist(self, testdir, config_path):
        config = testdir.parseconfig()
        values = config.getini("paths")
        assert len(values) == 2
        assert values[0] == config_path.dirpath("hello")
        assert values[1] == config_path.dirpath("world/sub.py")
        pytest.raises(ValueError, config.getini, "other")

    def make_conftest_for_args(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("args", "new args", type="args")
                parser.addini("a2", "", "args", default="1 2 3".split())
        """
        )

    def test_addini_args_ini_files(self, testdir):
        self.make_conftest_for_args(testdir)
        testdir.makeini(
            """
            [pytest]
            args=123 "123 hello" "this"
            """
        )
        self.check_config_args(testdir)

    def test_addini_args_pyproject_toml(self, testdir):
        self.make_conftest_for_args(testdir)
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            args = ["123", "123 hello", "this"]
            """
        )
        self.check_config_args(testdir)

    def check_config_args(self, testdir):
        config = testdir.parseconfig()
        values = config.getini("args")
        assert values == ["123", "123 hello", "this"]
        values = config.getini("a2")
        assert values == list("123")

    def make_conftest_for_linelist(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("xy", "", type="linelist")
                parser.addini("a2", "", "linelist")
        """
        )

    def test_addini_linelist_ini_files(self, testdir):
        self.make_conftest_for_linelist(testdir)
        testdir.makeini(
            """
            [pytest]
            xy= 123 345
                second line
        """
        )
        self.check_config_linelist(testdir)

    def test_addini_linelist_pprojecttoml(self, testdir):
        self.make_conftest_for_linelist(testdir)
        testdir.makepyprojecttoml(
            """
            [tool.pytest.ini_options]
            xy = ["123 345", "second line"]
        """
        )
        self.check_config_linelist(testdir)

    def check_config_linelist(self, testdir):
        config = testdir.parseconfig()
        values = config.getini("xy")
        assert len(values) == 2
        assert values == ["123 345", "second line"]
        values = config.getini("a2")
        assert values == []

    @pytest.mark.parametrize(
        "str_val, bool_val", [("True", True), ("no", False), ("no-ini", True)]
    )
    def test_addini_bool(self, testdir, str_val, bool_val):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("strip", "", type="bool", default=True)
        """
        )
        if str_val != "no-ini":
            testdir.makeini(
                """
                [pytest]
                strip=%s
            """
                % str_val
            )
        config = testdir.parseconfig()
        assert config.getini("strip") is bool_val

    def test_addinivalue_line_existing(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("xy", "", type="linelist")
        """
        )
        testdir.makeini(
            """
            [pytest]
            xy= 123
        """
        )
        config = testdir.parseconfig()
        values = config.getini("xy")
        assert len(values) == 1
        assert values == ["123"]
        config.addinivalue_line("xy", "456")
        values = config.getini("xy")
        assert len(values) == 2
        assert values == ["123", "456"]

    def test_addinivalue_line_new(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("xy", "", type="linelist")
        """
        )
        config = testdir.parseconfig()
        assert not config.getini("xy")
        config.addinivalue_line("xy", "456")
        values = config.getini("xy")
        assert len(values) == 1
        assert values == ["456"]
        config.addinivalue_line("xy", "123")
        values = config.getini("xy")
        assert len(values) == 2
        assert values == ["456", "123"]

    def test_confcutdir_check_isdir(self, testdir):
        """Give an error if --confcutdir is not a valid directory (#2078)"""
        exp_match = r"^--confcutdir must be a directory, given: "
        with pytest.raises(pytest.UsageError, match=exp_match):
            testdir.parseconfig(
                "--confcutdir", testdir.tmpdir.join("file").ensure(file=1)
            )
        with pytest.raises(pytest.UsageError, match=exp_match):
            testdir.parseconfig("--confcutdir", testdir.tmpdir.join("inexistant"))
        config = testdir.parseconfig(
            "--confcutdir", testdir.tmpdir.join("dir").ensure(dir=1)
        )
        assert config.getoption("confcutdir") == str(testdir.tmpdir.join("dir"))

    @pytest.mark.parametrize(
        "names, expected",
        [
            # dist-info based distributions root are files as will be put in PYTHONPATH
            (["bar.py"], ["bar"]),
            (["foo/bar.py"], ["bar"]),
            (["foo/bar.pyc"], []),
            (["foo/__init__.py"], ["foo"]),
            (["bar/__init__.py", "xz.py"], ["bar", "xz"]),
            (["setup.py"], []),
            # egg based distributions root contain the files from the dist root
            (["src/bar/__init__.py"], ["bar"]),
            (["src/bar/__init__.py", "setup.py"], ["bar"]),
            (["source/python/bar/__init__.py", "setup.py"], ["bar"]),
        ],
    )
    def test_iter_rewritable_modules(self, names, expected):
        assert list(_iter_rewritable_modules(names)) == expected


class TestConfigFromdictargs:
    def test_basic_behavior(self, _sys_snapshot):
        option_dict = {"verbose": 444, "foo": "bar", "capture": "no"}
        args = ["a", "b"]

        config = Config.fromdictargs(option_dict, args)
        with pytest.raises(AssertionError):
            config.parse(["should refuse to parse again"])
        assert config.option.verbose == 444
        assert config.option.foo == "bar"
        assert config.option.capture == "no"
        assert config.args == args

    def test_invocation_params_args(self, _sys_snapshot) -> None:
        """Show that fromdictargs can handle args in their "orig" format"""
        option_dict = {}  # type: Dict[str, object]
        args = ["-vvvv", "-s", "a", "b"]

        config = Config.fromdictargs(option_dict, args)
        assert config.args == ["a", "b"]
        assert config.invocation_params.args == tuple(args)
        assert config.option.verbose == 4
        assert config.option.capture == "no"

    def test_inifilename(self, tmpdir):
        tmpdir.join("foo/bar.ini").ensure().write(
            textwrap.dedent(
                """\
                [pytest]
                name = value
                """
            )
        )

        inifile = "../../foo/bar.ini"
        option_dict = {"inifilename": inifile, "capture": "no"}

        cwd = tmpdir.join("a/b")
        cwd.join("pytest.ini").ensure().write(
            textwrap.dedent(
                """\
                [pytest]
                name = wrong-value
                should_not_be_set = true
                """
            )
        )
        with cwd.ensure(dir=True).as_cwd():
            config = Config.fromdictargs(option_dict, ())
            inipath = py.path.local(inifile)

        assert config.args == [str(cwd)]
        assert config.option.inifilename == inifile
        assert config.option.capture == "no"

        # this indicates this is the file used for getting configuration values
        assert config.inifile == inipath
        assert config.inicfg.get("name") == "value"
        assert config.inicfg.get("should_not_be_set") is None


def test_options_on_small_file_do_not_blow_up(testdir) -> None:
    def runfiletest(opts: Sequence[str]) -> None:
        reprec = testdir.inline_run(*opts)
        passed, skipped, failed = reprec.countoutcomes()
        assert failed == 2
        assert skipped == passed == 0

    path = testdir.makepyfile(
        """
        def test_f1(): assert 0
        def test_f2(): assert 0
    """
    )

    runfiletest([path])
    runfiletest(["-l", path])
    runfiletest(["-s", path])
    runfiletest(["--tb=no", path])
    runfiletest(["--tb=short", path])
    runfiletest(["--tb=long", path])
    runfiletest(["--fulltrace", path])
    runfiletest(["--traceconfig", path])
    runfiletest(["-v", path])
    runfiletest(["-v", "-v", path])


def test_preparse_ordering_with_setuptools(testdir, monkeypatch):
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    class EntryPoint:
        name = "mytestplugin"
        group = "pytest11"

        def load(self):
            class PseudoPlugin:
                x = 42

            return PseudoPlugin()

    class Dist:
        files = ()
        metadata = {"name": "foo"}
        entry_points = (EntryPoint(),)

    def my_dists():
        return (Dist,)

    monkeypatch.setattr(importlib_metadata, "distributions", my_dists)
    testdir.makeconftest(
        """
        pytest_plugins = "mytestplugin",
    """
    )
    monkeypatch.setenv("PYTEST_PLUGINS", "mytestplugin")
    config = testdir.parseconfig()
    plugin = config.pluginmanager.getplugin("mytestplugin")
    assert plugin.x == 42


def test_setuptools_importerror_issue1479(testdir, monkeypatch):
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    class DummyEntryPoint:
        name = "mytestplugin"
        group = "pytest11"

        def load(self):
            raise ImportError("Don't hide me!")

    class Distribution:
        version = "1.0"
        files = ("foo.txt",)
        metadata = {"name": "foo"}
        entry_points = (DummyEntryPoint(),)

    def distributions():
        return (Distribution(),)

    monkeypatch.setattr(importlib_metadata, "distributions", distributions)
    with pytest.raises(ImportError):
        testdir.parseconfig()


def test_importlib_metadata_broken_distribution(testdir, monkeypatch):
    """Integration test for broken distributions with 'files' metadata being None (#5389)"""
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    class DummyEntryPoint:
        name = "mytestplugin"
        group = "pytest11"

        def load(self):
            return object()

    class Distribution:
        version = "1.0"
        files = None
        metadata = {"name": "foo"}
        entry_points = (DummyEntryPoint(),)

    def distributions():
        return (Distribution(),)

    monkeypatch.setattr(importlib_metadata, "distributions", distributions)
    testdir.parseconfig()


@pytest.mark.parametrize("block_it", [True, False])
def test_plugin_preparse_prevents_setuptools_loading(testdir, monkeypatch, block_it):
    monkeypatch.delenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", raising=False)

    plugin_module_placeholder = object()

    class DummyEntryPoint:
        name = "mytestplugin"
        group = "pytest11"

        def load(self):
            return plugin_module_placeholder

    class Distribution:
        version = "1.0"
        files = ("foo.txt",)
        metadata = {"name": "foo"}
        entry_points = (DummyEntryPoint(),)

    def distributions():
        return (Distribution(),)

    monkeypatch.setattr(importlib_metadata, "distributions", distributions)
    args = ("-p", "no:mytestplugin") if block_it else ()
    config = testdir.parseconfig(*args)
    config.pluginmanager.import_plugin("mytestplugin")
    if block_it:
        assert "mytestplugin" not in sys.modules
        assert config.pluginmanager.get_plugin("mytestplugin") is None
    else:
        assert (
            config.pluginmanager.get_plugin("mytestplugin") is plugin_module_placeholder
        )


@pytest.mark.parametrize(
    "parse_args,should_load", [(("-p", "mytestplugin"), True), ((), False)]
)
def test_disable_plugin_autoload(testdir, monkeypatch, parse_args, should_load):
    class DummyEntryPoint:
        project_name = name = "mytestplugin"
        group = "pytest11"
        version = "1.0"

        def load(self):
            return sys.modules[self.name]

    class Distribution:
        metadata = {"name": "foo"}
        entry_points = (DummyEntryPoint(),)
        files = ()

    class PseudoPlugin:
        x = 42

        attrs_used = []

        def __getattr__(self, name):
            assert name == "__loader__"
            self.attrs_used.append(name)
            return object()

    def distributions():
        return (Distribution(),)

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setattr(importlib_metadata, "distributions", distributions)
    monkeypatch.setitem(sys.modules, "mytestplugin", PseudoPlugin())
    config = testdir.parseconfig(*parse_args)
    has_loaded = config.pluginmanager.get_plugin("mytestplugin") is not None
    assert has_loaded == should_load
    if should_load:
        assert PseudoPlugin.attrs_used == ["__loader__"]
    else:
        assert PseudoPlugin.attrs_used == []


def test_plugin_loading_order(testdir):
    """Test order of plugin loading with `-p`."""
    p1 = testdir.makepyfile(
        """
        def test_terminal_plugin(request):
            import myplugin
            assert myplugin.terminal_plugin == [False, True]
        """,
        **{
            "myplugin": """
            terminal_plugin = []

            def pytest_configure(config):
                terminal_plugin.append(bool(config.pluginmanager.get_plugin("terminalreporter")))

            def pytest_sessionstart(session):
                config = session.config
                terminal_plugin.append(bool(config.pluginmanager.get_plugin("terminalreporter")))
            """
        },
    )
    testdir.syspathinsert()
    result = testdir.runpytest("-p", "myplugin", str(p1))
    assert result.ret == 0


def test_cmdline_processargs_simple(testdir):
    testdir.makeconftest(
        """
        def pytest_cmdline_preparse(args):
            args.append("-h")
    """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*pytest*", "*-h*"])


def test_invalid_options_show_extra_information(testdir):
    """display extra information when pytest exits due to unrecognized
    options in the command-line"""
    testdir.makeini(
        """
        [pytest]
        addopts = --invalid-option
    """
    )
    result = testdir.runpytest()
    result.stderr.fnmatch_lines(
        [
            "*error: unrecognized arguments: --invalid-option*",
            "*  inifile: %s*" % testdir.tmpdir.join("tox.ini"),
            "*  rootdir: %s*" % testdir.tmpdir,
        ]
    )


@pytest.mark.parametrize(
    "args",
    [
        ["dir1", "dir2", "-v"],
        ["dir1", "-v", "dir2"],
        ["dir2", "-v", "dir1"],
        ["-v", "dir2", "dir1"],
    ],
)
def test_consider_args_after_options_for_rootdir(testdir, args):
    """
    Consider all arguments in the command-line for rootdir
    discovery, even if they happen to occur after an option. #949
    """
    # replace "dir1" and "dir2" from "args" into their real directory
    root = testdir.tmpdir.mkdir("myroot")
    d1 = root.mkdir("dir1")
    d2 = root.mkdir("dir2")
    for i, arg in enumerate(args):
        if arg == "dir1":
            args[i] = d1
        elif arg == "dir2":
            args[i] = d2
    with root.as_cwd():
        result = testdir.runpytest(*args)
    result.stdout.fnmatch_lines(["*rootdir: *myroot"])


def test_toolongargs_issue224(testdir):
    result = testdir.runpytest("-m", "hello" * 500)
    assert result.ret == ExitCode.NO_TESTS_COLLECTED


def test_config_in_subdirectory_colon_command_line_issue2148(testdir):
    conftest_source = """
        def pytest_addoption(parser):
            parser.addini('foo', 'foo')
    """

    testdir.makefile(
        ".ini",
        **{"pytest": "[pytest]\nfoo = root", "subdir/pytest": "[pytest]\nfoo = subdir"},
    )

    testdir.makepyfile(
        **{
            "conftest": conftest_source,
            "subdir/conftest": conftest_source,
            "subdir/test_foo": """\
            def test_foo(pytestconfig):
                assert pytestconfig.getini('foo') == 'subdir'
            """,
        }
    )

    result = testdir.runpytest("subdir/test_foo.py::test_foo")
    assert result.ret == 0


def test_notify_exception(testdir, capfd):
    config = testdir.parseconfig()
    with pytest.raises(ValueError) as excinfo:
        raise ValueError(1)
    config.notify_exception(excinfo, config.option)
    _, err = capfd.readouterr()
    assert "ValueError" in err

    class A:
        def pytest_internalerror(self):
            return True

    config.pluginmanager.register(A())
    config.notify_exception(excinfo, config.option)
    _, err = capfd.readouterr()
    assert not err

    config = testdir.parseconfig("-p", "no:terminal")
    with pytest.raises(ValueError) as excinfo:
        raise ValueError(1)
    config.notify_exception(excinfo, config.option)
    _, err = capfd.readouterr()
    assert "ValueError" in err


def test_no_terminal_discovery_error(testdir):
    testdir.makepyfile("raise TypeError('oops!')")
    result = testdir.runpytest("-p", "no:terminal", "--collect-only")
    assert result.ret == ExitCode.INTERRUPTED


def test_load_initial_conftest_last_ordering(_config_for_test):
    pm = _config_for_test.pluginmanager

    class My:
        def pytest_load_initial_conftests(self):
            pass

    m = My()
    pm.register(m)
    hc = pm.hook.pytest_load_initial_conftests
    values = hc._nonwrappers + hc._wrappers
    expected = ["_pytest.config", m.__module__, "_pytest.capture"]
    assert [x.function.__module__ for x in values] == expected


def test_get_plugin_specs_as_list() -> None:
    def exp_match(val: object) -> str:
        return (
            "Plugins may be specified as a sequence or a ','-separated string of plugin names. Got: %s"
            % re.escape(repr(val))
        )

    with pytest.raises(pytest.UsageError, match=exp_match({"foo"})):
        _get_plugin_specs_as_list({"foo"})  # type: ignore[arg-type]
    with pytest.raises(pytest.UsageError, match=exp_match({})):
        _get_plugin_specs_as_list(dict())  # type: ignore[arg-type]

    assert _get_plugin_specs_as_list(None) == []
    assert _get_plugin_specs_as_list("") == []
    assert _get_plugin_specs_as_list("foo") == ["foo"]
    assert _get_plugin_specs_as_list("foo,bar") == ["foo", "bar"]
    assert _get_plugin_specs_as_list(["foo", "bar"]) == ["foo", "bar"]
    assert _get_plugin_specs_as_list(("foo", "bar")) == ["foo", "bar"]


def test_collect_pytest_prefix_bug_integration(testdir):
    """Integration test for issue #3775"""
    p = testdir.copy_example("config/collect_pytest_prefix")
    result = testdir.runpytest(p)
    result.stdout.fnmatch_lines(["* 1 passed *"])


def test_collect_pytest_prefix_bug(pytestconfig):
    """Ensure we collect only actual functions from conftest files (#3775)"""

    class Dummy:
        class pytest_something:
            pass

    pm = pytestconfig.pluginmanager
    assert pm.parse_hookimpl_opts(Dummy(), "pytest_something") is None


class TestRootdir:
    def test_simple_noini(self, tmpdir):
        assert get_common_ancestor([tmpdir]) == tmpdir
        a = tmpdir.mkdir("a")
        assert get_common_ancestor([a, tmpdir]) == tmpdir
        assert get_common_ancestor([tmpdir, a]) == tmpdir
        with tmpdir.as_cwd():
            assert get_common_ancestor([]) == tmpdir
            no_path = tmpdir.join("does-not-exist")
            assert get_common_ancestor([no_path]) == tmpdir
            assert get_common_ancestor([no_path.join("a")]) == tmpdir

    @pytest.mark.parametrize(
        "name, contents",
        [
            pytest.param("pytest.ini", "[pytest]\nx=10", id="pytest.ini"),
            pytest.param(
                "pyproject.toml", "[tool.pytest.ini_options]\nx=10", id="pyproject.toml"
            ),
            pytest.param("tox.ini", "[pytest]\nx=10", id="tox.ini"),
            pytest.param("setup.cfg", "[tool:pytest]\nx=10", id="setup.cfg"),
        ],
    )
    def test_with_ini(self, tmpdir: py.path.local, name: str, contents: str) -> None:
        inifile = tmpdir.join(name)
        inifile.write(contents)

        a = tmpdir.mkdir("a")
        b = a.mkdir("b")
        for args in ([str(tmpdir)], [str(a)], [str(b)]):
            rootdir, parsed_inifile, _ = determine_setup(None, args)
            assert rootdir == tmpdir
            assert parsed_inifile == inifile
        rootdir, parsed_inifile, ini_config = determine_setup(None, [str(b), str(a)])
        assert rootdir == tmpdir
        assert parsed_inifile == inifile
        assert ini_config == {"x": "10"}

    @pytest.mark.parametrize("name", "setup.cfg tox.ini".split())
    def test_pytestini_overrides_empty_other(self, tmpdir: py.path.local, name) -> None:
        inifile = tmpdir.ensure("pytest.ini")
        a = tmpdir.mkdir("a")
        a.ensure(name)
        rootdir, parsed_inifile, _ = determine_setup(None, [str(a)])
        assert rootdir == tmpdir
        assert parsed_inifile == inifile

    def test_setuppy_fallback(self, tmpdir: py.path.local) -> None:
        a = tmpdir.mkdir("a")
        a.ensure("setup.cfg")
        tmpdir.ensure("setup.py")
        rootdir, inifile, inicfg = determine_setup(None, [str(a)])
        assert rootdir == tmpdir
        assert inifile is None
        assert inicfg == {}

    def test_nothing(self, tmpdir: py.path.local, monkeypatch) -> None:
        monkeypatch.chdir(str(tmpdir))
        rootdir, inifile, inicfg = determine_setup(None, [str(tmpdir)])
        assert rootdir == tmpdir
        assert inifile is None
        assert inicfg == {}

    @pytest.mark.parametrize(
        "name, contents",
        [
            # pytest.param("pytest.ini", "[pytest]\nx=10", id="pytest.ini"),
            pytest.param(
                "pyproject.toml", "[tool.pytest.ini_options]\nx=10", id="pyproject.toml"
            ),
            # pytest.param("tox.ini", "[pytest]\nx=10", id="tox.ini"),
            # pytest.param("setup.cfg", "[tool:pytest]\nx=10", id="setup.cfg"),
        ],
    )
    def test_with_specific_inifile(
        self, tmpdir: py.path.local, name: str, contents: str
    ) -> None:
        p = tmpdir.ensure(name)
        p.write(contents)
        rootdir, inifile, ini_config = determine_setup(str(p), [str(tmpdir)])
        assert rootdir == tmpdir
        assert inifile == p
        assert ini_config == {"x": "10"}

    def test_with_arg_outside_cwd_without_inifile(self, tmpdir, monkeypatch) -> None:
        monkeypatch.chdir(str(tmpdir))
        a = tmpdir.mkdir("a")
        b = tmpdir.mkdir("b")
        rootdir, inifile, _ = determine_setup(None, [str(a), str(b)])
        assert rootdir == tmpdir
        assert inifile is None

    def test_with_arg_outside_cwd_with_inifile(self, tmpdir) -> None:
        a = tmpdir.mkdir("a")
        b = tmpdir.mkdir("b")
        inifile = a.ensure("pytest.ini")
        rootdir, parsed_inifile, _ = determine_setup(None, [str(a), str(b)])
        assert rootdir == a
        assert inifile == parsed_inifile

    @pytest.mark.parametrize("dirs", ([], ["does-not-exist"], ["a/does-not-exist"]))
    def test_with_non_dir_arg(self, dirs, tmpdir) -> None:
        with tmpdir.ensure(dir=True).as_cwd():
            rootdir, inifile, _ = determine_setup(None, dirs)
            assert rootdir == tmpdir
            assert inifile is None

    def test_with_existing_file_in_subdir(self, tmpdir) -> None:
        a = tmpdir.mkdir("a")
        a.ensure("exist")
        with tmpdir.as_cwd():
            rootdir, inifile, _ = determine_setup(None, ["a/exist"])
            assert rootdir == tmpdir
            assert inifile is None


class TestOverrideIniArgs:
    @pytest.mark.parametrize("name", "setup.cfg tox.ini pytest.ini".split())
    def test_override_ini_names(self, testdir, name):
        section = "[pytest]" if name != "setup.cfg" else "[tool:pytest]"
        testdir.tmpdir.join(name).write(
            textwrap.dedent(
                """
            {section}
            custom = 1.0""".format(
                    section=section
                )
            )
        )
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("custom", "")"""
        )
        testdir.makepyfile(
            """
            def test_pass(pytestconfig):
                ini_val = pytestconfig.getini("custom")
                print('\\ncustom_option:%s\\n' % ini_val)"""
        )

        result = testdir.runpytest("--override-ini", "custom=2.0", "-s")
        assert result.ret == 0
        result.stdout.fnmatch_lines(["custom_option:2.0"])

        result = testdir.runpytest(
            "--override-ini", "custom=2.0", "--override-ini=custom=3.0", "-s"
        )
        assert result.ret == 0
        result.stdout.fnmatch_lines(["custom_option:3.0"])

    def test_override_ini_pathlist(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                parser.addini("paths", "my new ini value", type="pathlist")"""
        )
        testdir.makeini(
            """
            [pytest]
            paths=blah.py"""
        )
        testdir.makepyfile(
            """
            import py.path
            def test_pathlist(pytestconfig):
                config_paths = pytestconfig.getini("paths")
                print(config_paths)
                for cpf in config_paths:
                    print('\\nuser_path:%s' % cpf.basename)"""
        )
        result = testdir.runpytest(
            "--override-ini", "paths=foo/bar1.py foo/bar2.py", "-s"
        )
        result.stdout.fnmatch_lines(["user_path:bar1.py", "user_path:bar2.py"])

    def test_override_multiple_and_default(self, testdir):
        testdir.makeconftest(
            """
            def pytest_addoption(parser):
                addini = parser.addini
                addini("custom_option_1", "", default="o1")
                addini("custom_option_2", "", default="o2")
                addini("custom_option_3", "", default=False, type="bool")
                addini("custom_option_4", "", default=True, type="bool")"""
        )
        testdir.makeini(
            """
            [pytest]
            custom_option_1=custom_option_1
            custom_option_2=custom_option_2
        """
        )
        testdir.makepyfile(
            """
            def test_multiple_options(pytestconfig):
                prefix = "custom_option"
                for x in range(1, 5):
                    ini_value=pytestconfig.getini("%s_%d" % (prefix, x))
                    print('\\nini%d:%s' % (x, ini_value))
        """
        )
        result = testdir.runpytest(
            "--override-ini",
            "custom_option_1=fulldir=/tmp/user1",
            "-o",
            "custom_option_2=url=/tmp/user2?a=b&d=e",
            "-o",
            "custom_option_3=True",
            "-o",
            "custom_option_4=no",
            "-s",
        )
        result.stdout.fnmatch_lines(
            [
                "ini1:fulldir=/tmp/user1",
                "ini2:url=/tmp/user2?a=b&d=e",
                "ini3:True",
                "ini4:False",
            ]
        )

    def test_override_ini_usage_error_bad_style(self, testdir):
        testdir.makeini(
            """
            [pytest]
            xdist_strict=False
        """
        )
        result = testdir.runpytest("--override-ini", "xdist_strict", "True")
        result.stderr.fnmatch_lines(
            [
                "ERROR: -o/--override-ini expects option=value style (got: 'xdist_strict').",
            ]
        )

    @pytest.mark.parametrize("with_ini", [True, False])
    def test_override_ini_handled_asap(self, testdir, with_ini):
        """-o should be handled as soon as possible and always override what's in ini files (#2238)"""
        if with_ini:
            testdir.makeini(
                """
                [pytest]
                python_files=test_*.py
            """
            )
        testdir.makepyfile(
            unittest_ini_handle="""
            def test():
                pass
        """
        )
        result = testdir.runpytest("--override-ini", "python_files=unittest_*.py")
        result.stdout.fnmatch_lines(["*1 passed in*"])

    def test_addopts_before_initini(self, monkeypatch, _config_for_test, _sys_snapshot):
        cache_dir = ".custom_cache"
        monkeypatch.setenv("PYTEST_ADDOPTS", "-o cache_dir=%s" % cache_dir)
        config = _config_for_test
        config._preparse([], addopts=True)
        assert config._override_ini == ["cache_dir=%s" % cache_dir]

    def test_addopts_from_env_not_concatenated(self, monkeypatch, _config_for_test):
        """PYTEST_ADDOPTS should not take values from normal args (#4265)."""
        monkeypatch.setenv("PYTEST_ADDOPTS", "-o")
        config = _config_for_test
        with pytest.raises(UsageError) as excinfo:
            config._preparse(["cache_dir=ignored"], addopts=True)
        assert (
            "error: argument -o/--override-ini: expected one argument (via PYTEST_ADDOPTS)"
            in excinfo.value.args[0]
        )

    def test_addopts_from_ini_not_concatenated(self, testdir):
        """addopts from ini should not take values from normal args (#4265)."""
        testdir.makeini(
            """
            [pytest]
            addopts=-o
        """
        )
        result = testdir.runpytest("cache_dir=ignored")
        result.stderr.fnmatch_lines(
            [
                "%s: error: argument -o/--override-ini: expected one argument (via addopts config)"
                % (testdir.request.config._parser.optparser.prog,)
            ]
        )
        assert result.ret == _pytest.config.ExitCode.USAGE_ERROR

    def test_override_ini_does_not_contain_paths(self, _config_for_test, _sys_snapshot):
        """Check that -o no longer swallows all options after it (#3103)"""
        config = _config_for_test
        config._preparse(["-o", "cache_dir=/cache", "/some/test/path"])
        assert config._override_ini == ["cache_dir=/cache"]

    def test_multiple_override_ini_options(self, testdir):
        """Ensure a file path following a '-o' option does not generate an error (#3103)"""
        testdir.makepyfile(
            **{
                "conftest.py": """
                def pytest_addoption(parser):
                    parser.addini('foo', default=None, help='some option')
                    parser.addini('bar', default=None, help='some option')
            """,
                "test_foo.py": """
                def test(pytestconfig):
                    assert pytestconfig.getini('foo') == '1'
                    assert pytestconfig.getini('bar') == '0'
            """,
                "test_bar.py": """
                def test():
                    assert False
            """,
            }
        )
        result = testdir.runpytest("-o", "foo=1", "-o", "bar=0", "test_foo.py")
        assert "ERROR:" not in result.stderr.str()
        result.stdout.fnmatch_lines(["collected 1 item", "*= 1 passed in *="])


def test_help_via_addopts(testdir):
    testdir.makeini(
        """
        [pytest]
        addopts = --unknown-option-should-allow-for-help --help
    """
    )
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines(
        [
            "usage: *",
            "positional arguments:",
            # Displays full/default help.
            "to see available markers type: pytest --markers",
        ]
    )


def test_help_and_version_after_argument_error(testdir):
    testdir.makeconftest(
        """
        def validate(arg):
            raise argparse.ArgumentTypeError("argerror")

        def pytest_addoption(parser):
            group = parser.getgroup('cov')
            group.addoption(
                "--invalid-option-should-allow-for-help",
                type=validate,
            )
        """
    )
    testdir.makeini(
        """
        [pytest]
        addopts = --invalid-option-should-allow-for-help
    """
    )
    result = testdir.runpytest("--help")
    result.stdout.fnmatch_lines(
        [
            "usage: *",
            "positional arguments:",
            "NOTE: displaying only minimal help due to UsageError.",
        ]
    )
    result.stderr.fnmatch_lines(
        [
            "ERROR: usage: *",
            "%s: error: argument --invalid-option-should-allow-for-help: expected one argument"
            % (testdir.request.config._parser.optparser.prog,),
        ]
    )
    # Does not display full/default help.
    assert "to see available markers type: pytest --markers" not in result.stdout.lines
    assert result.ret == ExitCode.USAGE_ERROR

    result = testdir.runpytest("--version")
    result.stderr.fnmatch_lines(["pytest {}".format(pytest.__version__)])
    assert result.ret == ExitCode.USAGE_ERROR


def test_help_formatter_uses_py_get_terminal_width(monkeypatch):
    from _pytest.config.argparsing import DropShorterLongHelpFormatter

    monkeypatch.setenv("COLUMNS", "90")
    formatter = DropShorterLongHelpFormatter("prog")
    assert formatter._width == 90

    monkeypatch.setattr("_pytest._io.get_terminal_width", lambda: 160)
    formatter = DropShorterLongHelpFormatter("prog")
    assert formatter._width == 160

    formatter = DropShorterLongHelpFormatter("prog", width=42)
    assert formatter._width == 42


def test_config_does_not_load_blocked_plugin_from_args(testdir):
    """This tests that pytest's config setup handles "-p no:X"."""
    p = testdir.makepyfile("def test(capfd): pass")
    result = testdir.runpytest(str(p), "-pno:capture")
    result.stdout.fnmatch_lines(["E       fixture 'capfd' not found"])
    assert result.ret == ExitCode.TESTS_FAILED

    result = testdir.runpytest(str(p), "-pno:capture", "-s")
    result.stderr.fnmatch_lines(["*: error: unrecognized arguments: -s"])
    assert result.ret == ExitCode.USAGE_ERROR


def test_invocation_args(testdir):
    """Ensure that Config.invocation_* arguments are correctly defined"""

    class DummyPlugin:
        pass

    p = testdir.makepyfile("def test(): pass")
    plugin = DummyPlugin()
    rec = testdir.inline_run(p, "-v", plugins=[plugin])
    calls = rec.getcalls("pytest_runtest_protocol")
    assert len(calls) == 1
    call = calls[0]
    config = call.item.config

    assert config.invocation_params.args == (p, "-v")
    assert config.invocation_params.dir == Path(str(testdir.tmpdir))

    plugins = config.invocation_params.plugins
    assert len(plugins) == 2
    assert plugins[0] is plugin
    assert type(plugins[1]).__name__ == "Collect"  # installed by testdir.inline_run()

    # args cannot be None
    with pytest.raises(TypeError):
        Config.InvocationParams(args=None, plugins=None, dir=Path())  # type: ignore[arg-type] # noqa: F821


@pytest.mark.parametrize(
    "plugin",
    [
        x
        for x in _pytest.config.default_plugins
        if x not in _pytest.config.essential_plugins
    ],
)
def test_config_blocked_default_plugins(testdir, plugin):
    if plugin == "debugging":
        # Fixed in xdist master (after 1.27.0).
        # https://github.com/pytest-dev/pytest-xdist/pull/422
        try:
            import xdist  # noqa: F401
        except ImportError:
            pass
        else:
            pytest.skip("does not work with xdist currently")

    p = testdir.makepyfile("def test(): pass")
    result = testdir.runpytest(str(p), "-pno:%s" % plugin)

    if plugin == "python":
        assert result.ret == ExitCode.USAGE_ERROR
        result.stderr.fnmatch_lines(
            [
                "ERROR: not found: */test_config_blocked_default_plugins.py",
                "(no name '*/test_config_blocked_default_plugins.py' in any of [])",
            ]
        )
        return

    assert result.ret == ExitCode.OK
    if plugin != "terminal":
        result.stdout.fnmatch_lines(["* 1 passed in *"])

    p = testdir.makepyfile("def test(): assert 0")
    result = testdir.runpytest(str(p), "-pno:%s" % plugin)
    assert result.ret == ExitCode.TESTS_FAILED
    if plugin != "terminal":
        result.stdout.fnmatch_lines(["* 1 failed in *"])
    else:
        assert result.stdout.lines == []


class TestSetupCfg:
    def test_pytest_setup_cfg_unsupported(self, testdir):
        testdir.makefile(
            ".cfg",
            setup="""
            [pytest]
            addopts = --verbose
        """,
        )
        with pytest.raises(pytest.fail.Exception):
            testdir.runpytest()

    def test_pytest_custom_cfg_unsupported(self, testdir):
        testdir.makefile(
            ".cfg",
            custom="""
            [pytest]
            addopts = --verbose
        """,
        )
        with pytest.raises(pytest.fail.Exception):
            testdir.runpytest("-c", "custom.cfg")


class TestPytestPluginsVariable:
    def test_pytest_plugins_in_non_top_level_conftest_unsupported(self, testdir):
        testdir.makepyfile(
            **{
                "subdirectory/conftest.py": """
            pytest_plugins=['capture']
        """
            }
        )
        testdir.makepyfile(
            """
            def test_func():
                pass
        """
        )
        res = testdir.runpytest()
        assert res.ret == 2
        msg = "Defining 'pytest_plugins' in a non-top-level conftest is no longer supported"
        res.stdout.fnmatch_lines(
            [
                "*{msg}*".format(msg=msg),
                "*subdirectory{sep}conftest.py*".format(sep=os.sep),
            ]
        )

    @pytest.mark.parametrize("use_pyargs", [True, False])
    def test_pytest_plugins_in_non_top_level_conftest_unsupported_pyargs(
        self, testdir, use_pyargs
    ):
        """When using --pyargs, do not emit the warning about non-top-level conftest warnings (#4039, #4044)"""

        files = {
            "src/pkg/__init__.py": "",
            "src/pkg/conftest.py": "",
            "src/pkg/test_root.py": "def test(): pass",
            "src/pkg/sub/__init__.py": "",
            "src/pkg/sub/conftest.py": "pytest_plugins=['capture']",
            "src/pkg/sub/test_bar.py": "def test(): pass",
        }
        testdir.makepyfile(**files)
        testdir.syspathinsert(testdir.tmpdir.join("src"))

        args = ("--pyargs", "pkg") if use_pyargs else ()
        res = testdir.runpytest(*args)
        assert res.ret == (0 if use_pyargs else 2)
        msg = (
            msg
        ) = "Defining 'pytest_plugins' in a non-top-level conftest is no longer supported"
        if use_pyargs:
            assert msg not in res.stdout.str()
        else:
            res.stdout.fnmatch_lines(["*{msg}*".format(msg=msg)])

    def test_pytest_plugins_in_non_top_level_conftest_unsupported_no_top_level_conftest(
        self, testdir
    ):
        subdirectory = testdir.tmpdir.join("subdirectory")
        subdirectory.mkdir()
        testdir.makeconftest(
            """
            pytest_plugins=['capture']
        """
        )
        testdir.tmpdir.join("conftest.py").move(subdirectory.join("conftest.py"))

        testdir.makepyfile(
            """
            def test_func():
                pass
        """
        )

        res = testdir.runpytest_subprocess()
        assert res.ret == 2
        msg = "Defining 'pytest_plugins' in a non-top-level conftest is no longer supported"
        res.stdout.fnmatch_lines(
            [
                "*{msg}*".format(msg=msg),
                "*subdirectory{sep}conftest.py*".format(sep=os.sep),
            ]
        )

    def test_pytest_plugins_in_non_top_level_conftest_unsupported_no_false_positives(
        self, testdir
    ):
        testdir.makepyfile(
            "def test_func(): pass",
            **{
                "subdirectory/conftest": "pass",
                "conftest": """
                    import warnings
                    warnings.filterwarnings('always', category=DeprecationWarning)
                    pytest_plugins=['capture']
                    """,
            },
        )
        res = testdir.runpytest_subprocess()
        assert res.ret == 0
        msg = "Defining 'pytest_plugins' in a non-top-level conftest is no longer supported"
        assert msg not in res.stdout.str()


def test_conftest_import_error_repr(tmpdir):
    """
    ConftestImportFailure should use a short error message and readable path to the failed
    conftest.py file
    """
    path = tmpdir.join("foo/conftest.py")
    with pytest.raises(
        ConftestImportFailure,
        match=re.escape("RuntimeError: some error (from {})".format(path)),
    ):
        try:
            raise RuntimeError("some error")
        except Exception as exc:
            assert exc.__traceback__ is not None
            exc_info = (type(exc), exc, exc.__traceback__)
            raise ConftestImportFailure(path, exc_info) from exc
