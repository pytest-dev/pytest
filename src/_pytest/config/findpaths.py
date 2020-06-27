import os
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import iniconfig
import py

from .exceptions import UsageError
from _pytest.compat import TYPE_CHECKING
from _pytest.outcomes import fail

if TYPE_CHECKING:
    from . import Config


def _parse_ini_config(path: py.path.local) -> iniconfig.IniConfig:
    """Parses the given generic '.ini' file using legacy IniConfig parser, returning
    the parsed object.

    Raises UsageError if the file cannot be parsed.
    """
    try:
        return iniconfig.IniConfig(path)
    except iniconfig.ParseError as exc:
        raise UsageError(str(exc)) from exc


def load_config_dict_from_file(
    filepath: py.path.local,
) -> Optional[Dict[str, Union[str, List[str]]]]:
    """Loads pytest configuration from the given file path, if supported.

    Return None if the file does not contain valid pytest configuration.
    """

    # configuration from ini files are obtained from the [pytest] section, if present.
    if filepath.ext == ".ini":
        iniconfig = _parse_ini_config(filepath)

        if "pytest" in iniconfig:
            return dict(iniconfig["pytest"].items())
        else:
            # "pytest.ini" files are always the source of configuration, even if empty
            if filepath.basename == "pytest.ini":
                return {}

    # '.cfg' files are considered if they contain a "[tool:pytest]" section
    elif filepath.ext == ".cfg":
        iniconfig = _parse_ini_config(filepath)

        if "tool:pytest" in iniconfig.sections:
            return dict(iniconfig["tool:pytest"].items())
        elif "pytest" in iniconfig.sections:
            # If a setup.cfg contains a "[pytest]" section, we raise a failure to indicate users that
            # plain "[pytest]" sections in setup.cfg files is no longer supported (#3086).
            fail(CFG_PYTEST_SECTION.format(filename="setup.cfg"), pytrace=False)

    # '.toml' files are considered if they contain a [tool.pytest.ini_options] table
    elif filepath.ext == ".toml":
        import toml

        config = toml.load(str(filepath))

        result = config.get("tool", {}).get("pytest", {}).get("ini_options", None)
        if result is not None:
            # TOML supports richer data types than ini files (strings, arrays, floats, ints, etc),
            # however we need to convert all scalar values to str for compatibility with the rest
            # of the configuration system, which expects strings only.
            def make_scalar(v: object) -> Union[str, List[str]]:
                return v if isinstance(v, list) else str(v)

            return {k: make_scalar(v) for k, v in result.items()}

    return None


def locate_config(
    args: Iterable[Union[str, py.path.local]]
) -> Tuple[
    Optional[py.path.local], Optional[py.path.local], Dict[str, Union[str, List[str]]],
]:
    """
    Search in the list of arguments for a valid ini-file for pytest,
    and return a tuple of (rootdir, inifile, cfg-dict).
    """
    config_names = [
        "pytest.ini",
        "pyproject.toml",
        "tox.ini",
        "setup.cfg",
    ]
    args = [x for x in args if not str(x).startswith("-")]
    if not args:
        args = [py.path.local()]
    for arg in args:
        arg = py.path.local(arg)
        for base in arg.parts(reverse=True):
            for config_name in config_names:
                p = base.join(config_name)
                if p.isfile():
                    ini_config = load_config_dict_from_file(p)
                    if ini_config is not None:
                        return base, p, ini_config
    return None, None, {}


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
) -> Tuple[py.path.local, Optional[py.path.local], Dict[str, Union[str, List[str]]]]:
    rootdir = None
    dirs = get_dirs_from_args(args)
    if inifile:
        inipath_ = py.path.local(inifile)
        inipath = inipath_  # type: Optional[py.path.local]
        inicfg = load_config_dict_from_file(inipath_) or {}
        if rootdir_cmd_arg is None:
            rootdir = get_common_ancestor(dirs)
    else:
        ancestor = get_common_ancestor(dirs)
        rootdir, inipath, inicfg = locate_config([ancestor])
        if rootdir is None and rootdir_cmd_arg is None:
            for possible_rootdir in ancestor.parts(reverse=True):
                if possible_rootdir.join("setup.py").exists():
                    rootdir = possible_rootdir
                    break
            else:
                if dirs != [ancestor]:
                    rootdir, inipath, inicfg = locate_config(dirs)
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
    assert rootdir is not None
    return rootdir, inipath, inicfg or {}
