import os
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import py
from iniconfig import IniConfig
from iniconfig import ParseError

from .exceptions import UsageError
from _pytest.compat import TYPE_CHECKING
from _pytest.outcomes import fail

if TYPE_CHECKING:
    from . import Config


def exists(path, ignore=OSError):
    try:
        return path.check()
    except ignore:
        return False


def _parse_ini_config(path: py.path.local) -> py.iniconfig.IniConfig:
    """Parses the given generic '.ini' file using legacy IniConfig parser, returning
    the parsed object.

    Raises UsageError if the file cannot be parsed.
    """
    try:
        return py.iniconfig.IniConfig(path)
    except py.iniconfig.ParseError as exc:
        raise UsageError(str(exc))


def _parse_ini_config_from_pytest_ini(path: py.path.local) -> Optional[Dict[str, str]]:
    """Parses and validates a 'pytest.ini' file.

    If present, 'pytest.ini' files are always considered the source of truth of pytest
    configuration, even if empty or without a "[pytest]" section.
    """
    iniconfig = _parse_ini_config(path)
    if "pytest" in iniconfig:
        return dict(iniconfig["pytest"].items())
    else:
        return {}


def _parse_ini_config_from_tox_ini(path: py.path.local) -> Optional[Dict[str, str]]:
    """Parses and validates a 'tox.ini' file for pytest configuration.

    'tox.ini' files are only considered for pytest configuration if they contain a "[pytest]"
    section.
    """
    iniconfig = _parse_ini_config(path)
    if "pytest" in iniconfig:
        return dict(iniconfig["pytest"].items())
    else:
        return None


def _parse_ini_config_from_setup_cfg(path: py.path.local) -> Optional[Dict[str, str]]:
    """Parses and validates a 'setup.cfg' file for pytest configuration.

    'setup.cfg' files are only considered for pytest configuration if they contain a "[tool:pytest]"
    section.

    If a setup.cfg contains a "[pytest]" section, we raise a failure to indicate users that
    plain "[pytest]" sections in setup.cfg files is no longer supported (#3086).
    """
    iniconfig = _parse_ini_config(path)

    if "tool:pytest" in iniconfig.sections:
        return dict(iniconfig["tool:pytest"].items())
    elif "pytest" in iniconfig.sections:
        fail(CFG_PYTEST_SECTION.format(filename="setup.cfg"), pytrace=False)
    return None


def _parse_ini_config_from_pyproject_toml(
    path: py.path.local,
) -> Optional[Dict[str, Union[str, List[str]]]]:
    """Parses and validates a ``pyproject.toml`` file for pytest configuration.

    The ``[tool.pytest]`` table is used by pytest. If the file contains that section,
    it is used as the config file.

    Note: toml supports richer data types than ini files (strings, arrays, floats, ints, etc),
        however we need to convert all scalar values to str for compatibility with the rest
        of the configuration system, which expects strings only. We needed to change the
        handling of ini values in Config as to at least leave lists intact.
    """
    import toml

    config = toml.load(path)

    result = config.get("tool", {}).get("pytest", {}).get("ini_options", None)
    if result is not None:
        # convert all scalar values to strings for compatibility with other ini formats;
        # conversion to useful values is made by Config._getini
        def make_scalar(v: Any) -> Union[str, List[str]]:
            return v if isinstance(v, list) else str(v)

        return {k: make_scalar(v) for k, v in result.items()}
    else:
        return None


def getcfg(args):
    """
    Search the list of arguments for a valid ini-file for pytest,
    and return a tuple of (rootdir, inifile, cfg-dict).
    """
    ini_names_and_parsers = [
        ("pytest.ini", _parse_ini_config_from_pytest_ini),
        ("pyproject.toml", _parse_ini_config_from_pyproject_toml),
        ("tox.ini", _parse_ini_config_from_tox_ini),
        ("setup.cfg", _parse_ini_config_from_setup_cfg),
    ]
    args = [x for x in args if not str(x).startswith("-")]
    if not args:
        args = [py.path.local()]
    for arg in args:
        arg = py.path.local(arg)
        for base in arg.parts(reverse=True):
            for inibasename, parser in ini_names_and_parsers:
                p = base.join(inibasename)
                if p.isfile():
                    ini_config = parser(p)
                    if ini_config is not None:
                        return base, p, ini_config
    return None, None, None


def get_common_ancestor(paths: Iterable[py.path.local]) -> py.path.local:
    common_ancestor = None
    for path in paths:
        if not path.exists():
            continue
        if common_ancestor is None:
            common_ancestor = path
        else:
            if path.relto(common_ancestor) or path == common_ancestor:
                continue
            elif common_ancestor.relto(path):
                common_ancestor = path
            else:
                shared = path.common(common_ancestor)
                if shared is not None:
                    common_ancestor = shared
    if common_ancestor is None:
        common_ancestor = py.path.local()
    elif common_ancestor.isfile():
        common_ancestor = common_ancestor.dirpath()
    return common_ancestor


def get_dirs_from_args(args: Iterable[str]) -> List[py.path.local]:
    def is_option(x: str) -> bool:
        return x.startswith("-")

    def get_file_part_from_node_id(x: str) -> str:
        return x.split("::")[0]

    def get_dir_from_path(path: py.path.local) -> py.path.local:
        if path.isdir():
            return path
        return py.path.local(path.dirname)

    # These look like paths but may not exist
    possible_paths = (
        py.path.local(get_file_part_from_node_id(arg))
        for arg in args
        if not is_option(arg)
    )

    return [get_dir_from_path(path) for path in possible_paths if path.exists()]


CFG_PYTEST_SECTION = "[pytest] section in {filename} files is no longer supported, change to [tool:pytest] instead."


def determine_setup(
    inifile: Optional[str],
    args: List[str],
    rootdir_cmd_arg: Optional[str] = None,
    config: Optional["Config"] = None,
) -> Tuple[py.path.local, Optional[str], Any]:
    dirs = get_dirs_from_args(args)
    if inifile:
        iniconfig = IniConfig(inifile)
        is_cfg_file = str(inifile).endswith(".cfg")
        sections = ["tool:pytest", "pytest"] if is_cfg_file else ["pytest"]
        for section in sections:
            try:
                inicfg = iniconfig[
                    section
                ]  # type: Optional[py.iniconfig._SectionWrapper]
                if is_cfg_file and section == "pytest" and config is not None:
                    fail(
                        CFG_PYTEST_SECTION.format(filename=str(inifile)), pytrace=False
                    )
                break
            except KeyError:
                inicfg = None
        if rootdir_cmd_arg is None:
            rootdir = get_common_ancestor(dirs)
    else:
        ancestor = get_common_ancestor(dirs)
        rootdir, inifile, inicfg = getcfg([ancestor])
        if rootdir is None and rootdir_cmd_arg is None:
            for possible_rootdir in ancestor.parts(reverse=True):
                if possible_rootdir.join("setup.py").exists():
                    rootdir = possible_rootdir
                    break
            else:
                if dirs != [ancestor]:
                    rootdir, inifile, inicfg = getcfg(dirs)
                if rootdir is None:
                    if config is not None:
                        cwd = config.invocation_dir
                    else:
                        cwd = py.path.local()
                    rootdir = get_common_ancestor([cwd, ancestor])
                    is_fs_root = os.path.splitdrive(str(rootdir))[1] == "/"
                    if is_fs_root:
                        rootdir = ancestor
    if rootdir_cmd_arg:
        rootdir = py.path.local(os.path.expandvars(rootdir_cmd_arg))
        if not rootdir.isdir():
            raise UsageError(
                "Directory '{}' not found. Check your '--rootdir' option.".format(
                    rootdir
                )
            )
    return rootdir, inifile, inicfg or {}
