# mypy: allow-untyped-defs
from __future__ import annotations

import os
from pathlib import Path
import tempfile
from textwrap import dedent

from _pytest.config import UsageError
from _pytest.config.findpaths import determine_setup
from _pytest.config.findpaths import get_common_ancestor
from _pytest.config.findpaths import get_dirs_from_args
from _pytest.config.findpaths import is_fs_root
from _pytest.config.findpaths import load_config_dict_from_file
import pytest


class TestLoadConfigDictFromFile:
    def test_empty_pytest_ini(self, tmp_path: Path) -> None:
        """pytest.ini files are always considered for configuration, even if empty"""
        fn = tmp_path / "pytest.ini"
        fn.write_text("", encoding="utf-8")
        assert load_config_dict_from_file(fn) == {}

    def test_pytest_ini(self, tmp_path: Path) -> None:
        """[pytest] section in pytest.ini files is read correctly"""
        fn = tmp_path / "pytest.ini"
        fn.write_text("[pytest]\nx=1", encoding="utf-8")
        assert load_config_dict_from_file(fn) == {"x": "1"}

    def test_custom_ini(self, tmp_path: Path) -> None:
        """[pytest] section in any .ini file is read correctly"""
        fn = tmp_path / "custom.ini"
        fn.write_text("[pytest]\nx=1", encoding="utf-8")
        assert load_config_dict_from_file(fn) == {"x": "1"}

    def test_custom_ini_without_section(self, tmp_path: Path) -> None:
        """Custom .ini files without [pytest] section are not considered for configuration"""
        fn = tmp_path / "custom.ini"
        fn.write_text("[custom]", encoding="utf-8")
        assert load_config_dict_from_file(fn) is None

    def test_custom_cfg_file(self, tmp_path: Path) -> None:
        """Custom .cfg files without [tool:pytest] section are not considered for configuration"""
        fn = tmp_path / "custom.cfg"
        fn.write_text("[custom]", encoding="utf-8")
        assert load_config_dict_from_file(fn) is None

    def test_valid_cfg_file(self, tmp_path: Path) -> None:
        """Custom .cfg files with [tool:pytest] section are read correctly"""
        fn = tmp_path / "custom.cfg"
        fn.write_text("[tool:pytest]\nx=1", encoding="utf-8")
        assert load_config_dict_from_file(fn) == {"x": "1"}

    def test_unsupported_pytest_section_in_cfg_file(self, tmp_path: Path) -> None:
        """.cfg files with [pytest] section are no longer supported and should fail to alert users"""
        fn = tmp_path / "custom.cfg"
        fn.write_text("[pytest]", encoding="utf-8")
        with pytest.raises(pytest.fail.Exception):
            load_config_dict_from_file(fn)

    def test_invalid_toml_file(self, tmp_path: Path) -> None:
        """Invalid .toml files should raise `UsageError`."""
        fn = tmp_path / "myconfig.toml"
        fn.write_text("]invalid toml[", encoding="utf-8")
        with pytest.raises(UsageError):
            load_config_dict_from_file(fn)

    def test_custom_toml_file(self, tmp_path: Path) -> None:
        """.toml files without [tool.pytest.ini_options] are not considered for configuration."""
        fn = tmp_path / "myconfig.toml"
        fn.write_text(
            dedent(
                """
            [build_system]
            x = 1
            """
            ),
            encoding="utf-8",
        )
        assert load_config_dict_from_file(fn) is None

    def test_valid_toml_file(self, tmp_path: Path) -> None:
        """.toml files with [tool.pytest.ini_options] are read correctly, including changing
        data types to str/list for compatibility with other configuration options."""
        fn = tmp_path / "myconfig.toml"
        fn.write_text(
            dedent(
                """
            [tool.pytest.ini_options]
            x = 1
            y = 20.0
            values = ["tests", "integration"]
            name = "foo"
            heterogeneous_array = [1, "str"]
            """
            ),
            encoding="utf-8",
        )
        assert load_config_dict_from_file(fn) == {
            "x": "1",
            "y": "20.0",
            "values": ["tests", "integration"],
            "name": "foo",
            "heterogeneous_array": [1, "str"],
        }


class TestCommonAncestor:
    def test_has_ancestor(self, tmp_path: Path) -> None:
        fn1 = tmp_path / "foo" / "bar" / "test_1.py"
        fn1.parent.mkdir(parents=True)
        fn1.touch()
        fn2 = tmp_path / "foo" / "zaz" / "test_2.py"
        fn2.parent.mkdir(parents=True)
        fn2.touch()
        cwd = Path.cwd()
        assert get_common_ancestor(cwd, [fn1, fn2]) == tmp_path / "foo"
        assert get_common_ancestor(cwd, [fn1.parent, fn2]) == tmp_path / "foo"
        assert get_common_ancestor(cwd, [fn1.parent, fn2.parent]) == tmp_path / "foo"
        assert get_common_ancestor(cwd, [fn1, fn2.parent]) == tmp_path / "foo"

    def test_single_dir(self, tmp_path: Path) -> None:
        assert get_common_ancestor(Path.cwd(), [tmp_path]) == tmp_path

    def test_single_file(self, tmp_path: Path) -> None:
        fn = tmp_path / "foo.py"
        fn.touch()
        assert get_common_ancestor(Path.cwd(), [fn]) == tmp_path


def test_get_dirs_from_args(tmp_path):
    """get_dirs_from_args() skips over non-existing directories and files"""
    fn = tmp_path / "foo.py"
    fn.touch()
    d = tmp_path / "tests"
    d.mkdir()
    option = "--foobar=/foo.txt"
    # xdist uses options in this format for its rsync feature (#7638)
    xdist_rsync_option = "popen=c:/dest"
    assert get_dirs_from_args(
        [str(fn), str(tmp_path / "does_not_exist"), str(d), option, xdist_rsync_option]
    ) == [fn.parent, d]


@pytest.mark.parametrize(
    "path, expected",
    [
        pytest.param(
            f"e:{os.sep}", True, marks=pytest.mark.skipif("sys.platform != 'win32'")
        ),
        (f"{os.sep}", True),
        (f"e:{os.sep}projects", False),
        (f"{os.sep}projects", False),
    ],
)
def test_is_fs_root(path: Path, expected: bool) -> None:
    assert is_fs_root(Path(path)) is expected


class TestDetermineSetup:
    def test_ignore_setup_py_in_temp_dir(self, tmp_path: Path) -> None:
        """Test that setup.py in the temp directory is ignored for rootdir detection.
        
        This addresses issue #13822 where a setup.py file in /tmp would cause
        pytest to incorrectly identify /tmp as the rootdir.
        """
        # Check if /tmp/setup.py exists (it should for this test to be meaningful)
        real_temp_dir = Path(tempfile.gettempdir())
        temp_setup_file = real_temp_dir / "setup.py"
        temp_setup_existed = temp_setup_file.exists()
        
        # Ensure setup.py exists in temp directory for the test
        if not temp_setup_existed:
            temp_setup_file.write_text("# temp setup.py for test")
        
        try:
            # Create a project directory that would be inside temp hierarchy
            # Simulate a pytest temp directory structure 
            project_dir = tmp_path / "project"
            project_dir.mkdir()
            
            test_file = project_dir / "test_example.py"
            test_file.write_text("def test_example(): pass")
            
            # Test case: running pytest from a directory that could traverse up to /tmp
            # If our fix is working, it should NOT use /tmp as rootdir even though 
            # /tmp/setup.py exists
            rootdir, inipath, inicfg, ignored = determine_setup(
                inifile=None,
                args=[str(test_file)],
                rootdir_cmd_arg=None,
                invocation_dir=project_dir,
            )
            
            # The rootdir should not be the temp directory, even if setup.py exists there
            assert rootdir != real_temp_dir
            # Should default to the project directory or its parent
            assert rootdir in (project_dir, project_dir.parent)
            
        finally:
            # Clean up the temp setup.py if we created it
            if not temp_setup_existed and temp_setup_file.exists():
                temp_setup_file.unlink()
    
    def test_normal_setup_py_detection_still_works(self, tmp_path: Path) -> None:
        """Test that normal setup.py detection still works after our fix."""
        # Create a project with setup.py
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        
        setup_file = project_dir / "setup.py" 
        setup_file.write_text("from setuptools import setup; setup()")
        
        test_file = project_dir / "test_example.py"
        test_file.write_text("def test_example(): pass")
        
        # Test that setup.py is still found normally
        rootdir, inipath, inicfg, ignored = determine_setup(
            inifile=None,
            args=[str(test_file)],
            rootdir_cmd_arg=None,
            invocation_dir=project_dir,
        )
        
        assert rootdir == project_dir
