from textwrap import dedent

import py

import pytest
from _pytest.config.findpaths import get_common_ancestor
from _pytest.config.findpaths import load_config_dict_from_file


class TestLoadConfigDictFromFile:
    def test_empty_pytest_ini(self, tmpdir):
        """pytest.ini files are always considered for configuration, even if empty"""
        fn = tmpdir.join("pytest.ini")
        fn.write("")
        assert load_config_dict_from_file(fn) == {}

    def test_pytest_ini(self, tmpdir):
        """[pytest] section in pytest.ini files is read correctly"""
        fn = tmpdir.join("pytest.ini")
        fn.write("[pytest]\nx=1")
        assert load_config_dict_from_file(fn) == {"x": "1"}

    def test_custom_ini(self, tmpdir):
        """[pytest] section in any .ini file is read correctly"""
        fn = tmpdir.join("custom.ini")
        fn.write("[pytest]\nx=1")
        assert load_config_dict_from_file(fn) == {"x": "1"}

    def test_custom_ini_without_section(self, tmpdir):
        """Custom .ini files without [pytest] section are not considered for configuration"""
        fn = tmpdir.join("custom.ini")
        fn.write("[custom]")
        assert load_config_dict_from_file(fn) is None

    def test_custom_cfg_file(self, tmpdir):
        """Custom .cfg files without [tool:pytest] section are not considered for configuration"""
        fn = tmpdir.join("custom.cfg")
        fn.write("[custom]")
        assert load_config_dict_from_file(fn) is None

    def test_valid_cfg_file(self, tmpdir):
        """Custom .cfg files with [tool:pytest] section are read correctly"""
        fn = tmpdir.join("custom.cfg")
        fn.write("[tool:pytest]\nx=1")
        assert load_config_dict_from_file(fn) == {"x": "1"}

    def test_unsupported_pytest_section_in_cfg_file(self, tmpdir):
        """.cfg files with [pytest] section are no longer supported and should fail to alert users"""
        fn = tmpdir.join("custom.cfg")
        fn.write("[pytest]")
        with pytest.raises(pytest.fail.Exception):
            load_config_dict_from_file(fn)

    def test_invalid_toml_file(self, tmpdir):
        """.toml files without [tool.pytest.ini_options] are not considered for configuration."""
        fn = tmpdir.join("myconfig.toml")
        fn.write(
            dedent(
                """
            [build_system]
            x = 1
            """
            )
        )
        assert load_config_dict_from_file(fn) is None

    def test_valid_toml_file(self, tmpdir):
        """.toml files with [tool.pytest.ini_options] are read correctly, including changing
        data types to str/list for compatibility with other configuration options."""
        fn = tmpdir.join("myconfig.toml")
        fn.write(
            dedent(
                """
            [tool.pytest.ini_options]
            x = 1
            y = 20.0
            values = ["tests", "integration"]
            name = "foo"
            """
            )
        )
        assert load_config_dict_from_file(fn) == {
            "x": "1",
            "y": "20.0",
            "values": ["tests", "integration"],
            "name": "foo",
        }


class TestCommonAncestor:
    def test_has_ancestor(self, tmpdir):
        fn1 = tmpdir.join("foo/bar/test_1.py").ensure(file=1)
        fn2 = tmpdir.join("foo/zaz/test_2.py").ensure(file=1)
        assert get_common_ancestor([fn1, fn2]) == tmpdir.join("foo")
        assert get_common_ancestor([py.path.local(fn1.dirname), fn2]) == tmpdir.join(
            "foo"
        )
        assert get_common_ancestor(
            [py.path.local(fn1.dirname), py.path.local(fn2.dirname)]
        ) == tmpdir.join("foo")
        assert get_common_ancestor([fn1, py.path.local(fn2.dirname)]) == tmpdir.join(
            "foo"
        )

    def test_single_dir(self, tmpdir):
        assert get_common_ancestor([tmpdir]) == tmpdir

    def test_single_file(self, tmpdir):
        fn = tmpdir.join("foo.py").ensure(file=1)
        assert get_common_ancestor([fn]) == tmpdir
