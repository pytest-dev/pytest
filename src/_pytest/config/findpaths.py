import os
import sys
import warnings
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

from .exceptions import UsageError
from _pytest.deprecated import SETUP_CFG_CONFIG
from _pytest.outcomes import fail
from _pytest.pathlib import absolutepath
from _pytest.pathlib import commonpath

if TYPE_CHECKING:
    from . import Config
    from iniconfig import IniConfig  # NOQA: F401

PARSE_RESULT = Optional[Dict[str, Union[str, List[str]]]]


def _parse_ini_config(path: Path) -> "IniConfig":
    """Parse the given generic '.ini' file using legacy IniConfig parser, returning
    the parsed object.

    Raise UsageError if the file cannot be parsed.
    """
    from iniconfig import IniConfig, ParseError  # NOQA: F811

    try:
        return IniConfig(os.fspath(path), data=path.read_text())
    except ParseError as exc:
        raise UsageError(str(exc)) from exc


def _parse_pytest_ini(path: Path) -> PARSE_RESULT:
    """Parse the legacy pytest.ini and return the contents of the pytest section

    if the file exists and lacks a pytest section, consider it empty"""
    iniconfig = _parse_ini_config(path)

    if "pytest" in iniconfig:
        return dict(iniconfig["pytest"].items())
    else:
        # "pytest.ini" files are always the source of configuration, even if empty.
        return {}


def _parse_ini_file(path: Path) -> PARSE_RESULT:
    """Parses .ini files with expected pytest.ini sections

    todo: investigate if tool:pytest should be added
    """
    iniconfig = _parse_ini_config(path)

    if "pytest" in iniconfig:
        return dict(iniconfig["pytest"].items())
    return None


def _parse_cfg_file(path: Path) -> PARSE_RESULT:
    """Parses .cfg files, specifically used for setup.cfg support

    tool:pytest as section name is required
    """

    iniconfig = _parse_ini_config(path)

    if "tool:pytest" in iniconfig.sections:

        if path.name == "setup.cfg":
            warnings.warn_explicit(
                SETUP_CFG_CONFIG, None, os.fspath(path), 0, module="pytest"
            )
        return dict(iniconfig["tool:pytest"].items())
    elif "pytest" in iniconfig.sections:
        # If a setup.cfg contains a "[pytest]" section, we raise a failure to indicate users that
        # plain "[pytest]" sections in setup.cfg files is no longer supported (#3086).
        fail(CFG_PYTEST_SECTION.format(filename="setup.cfg"), pytrace=False)
    else:
        return None


def _parse_pyproject_ini_options(
    path: Path,
) -> PARSE_RESULT:
    """Load backward compatible ini options from pyproject.toml"""

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    toml_text = filepath.read_text(encoding="utf-8")
    try:
        config = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as exc:
        raise UsageError(f"{filepath}: {exc}") from exc

    result = config.get("tool", {}).get("pytest", {}).get("ini_options", None)
    if result is not None:
        # TOML supports richer data types than ini files (strings, arrays, floats, ints, etc),
        # however we need to convert all scalar values to str for compatibility with the rest
        # of the configuration system, which expects strings only.
        def make_scalar(v: object) -> Union[str, List[str]]:
            return v if isinstance(v, list) else str(v)

        return {k: make_scalar(v) for k, v in result.items()}
    else:
        return None


CONFIG_LOADERS = {
    "pytest.ini": _parse_pytest_ini,
    ".pytest.ini": _parse_pytest_ini,
    "pyproject.toml": _parse_pyproject_ini_options,
    "tox.ini": _parse_ini_file,
    "setup.cfg": _parse_cfg_file,
}

CONFIG_SUFFIXES = {
    ".ini": _parse_ini_file,
    ".cfg": _parse_cfg_file,
    ".toml": _parse_pyproject_ini_options,
}


def load_config_dict_from_file(path: Path) -> PARSE_RESULT:
    """Load pytest configuration from the given file path, if supported.

    Return None if the file does not contain valid pytest configuration.
    """
    if path.name in CONFIG_LOADERS:
        return CONFIG_LOADERS[path.name](path)
    if path.suffix in CONFIG_SUFFIXES:
        return CONFIG_SUFFIXES[path.suffix](path)
    return None


def locate_config(
    args: List[Path],
) -> Tuple[Optional[Path], Optional[Path], Dict[str, Union[str, List[str]]]]:
    """Search in the list of arguments for a valid ini-file for pytest,
    and return a tuple of (rootdir, inifile, cfg-dict)."""

    if not args:
        args = [Path.cwd()]
    for arg in args:
        argpath = absolutepath(arg)
        for base in (argpath, *argpath.parents):
            for config_name, loader in CONFIG_LOADERS.items():
                p = base / config_name
                if p.is_file():
                    config = loader(p)
                    if config is not None:
                        return base, p, config
    return None, None, {}


def get_common_ancestor(paths: Iterable[Path]) -> Path:
    common_ancestor: Optional[Path] = None
    for path in paths:
        if not path.exists():
            continue
        if common_ancestor is None:
            common_ancestor = path
        else:
            if common_ancestor in path.parents or path == common_ancestor:
                continue
            elif path in common_ancestor.parents:
                common_ancestor = path
            else:
                shared = commonpath(path, common_ancestor)
                if shared is not None:
                    common_ancestor = shared
    if common_ancestor is None:
        common_ancestor = Path.cwd()
    elif common_ancestor.is_file():
        common_ancestor = common_ancestor.parent
    return common_ancestor


def get_dirs_from_args(args: Iterable[str]) -> List[Path]:
    def is_option(x: str) -> bool:
        return x.startswith("-")

    def get_file_part_from_node_id(x: str) -> str:
        return x.split("::")[0]

    def get_dir_from_path(path: Path) -> Path:
        if path.is_dir():
            return path
        return path.parent

    def safe_exists(path: Path) -> bool:
        # This can throw on paths that contain characters unrepresentable at the OS level,
        # or with invalid syntax on Windows (https://bugs.python.org/issue35306)
        try:
            return path.exists()
        except OSError:
            return False

    # These look like paths but may not exist
    possible_paths = (
        absolutepath(get_file_part_from_node_id(arg))
        for arg in args
        if not is_option(arg)
    )

    return [get_dir_from_path(path) for path in possible_paths if safe_exists(path)]


CFG_PYTEST_SECTION = "[pytest] section in {filename} files is no longer supported, change to [tool:pytest] instead."


def determine_setup(
    inifile: Optional[str],
    args: Sequence[str],
    rootdir_cmd_arg: Optional[str] = None,
    config: Optional["Config"] = None,
) -> Tuple[Path, Optional[Path], Dict[str, Union[str, List[str]]]]:
    rootdir = None
    dirs = get_dirs_from_args(args)
    if inifile:
        inipath_ = absolutepath(inifile)
        inipath: Optional[Path] = inipath_
        inicfg = load_config_dict_from_file(inipath_) or {}
        if rootdir_cmd_arg is None:
            rootdir = inipath_.parent
    else:
        ancestor = get_common_ancestor(dirs)
        rootdir, inipath, inicfg = locate_config([ancestor])
        if rootdir is None and rootdir_cmd_arg is None:
            for possible_rootdir in (ancestor, *ancestor.parents):
                if (possible_rootdir / "setup.py").is_file():
                    rootdir = possible_rootdir
                    break
            else:
                if dirs != [ancestor]:
                    rootdir, inipath, inicfg = locate_config(dirs)
                if rootdir is None:
                    if config is not None:
                        cwd = config.invocation_params.dir
                    else:
                        cwd = Path.cwd()
                    rootdir = get_common_ancestor([cwd, ancestor])
                    is_fs_root = os.path.splitdrive(str(rootdir))[1] == "/"
                    if is_fs_root:
                        rootdir = ancestor
    if rootdir_cmd_arg:
        rootdir = absolutepath(os.path.expandvars(rootdir_cmd_arg))
        if not rootdir.is_dir():
            raise UsageError(
                "Directory '{}' not found. Check your '--rootdir' option.".format(
                    rootdir
                )
            )
    assert rootdir is not None
    return rootdir, inipath, inicfg or {}
