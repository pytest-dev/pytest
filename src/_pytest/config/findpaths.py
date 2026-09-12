from __future__ import annotations

from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import KW_ONLY
import os
from pathlib import Path
import sys
from typing import Literal
from typing import TypeAlias

import iniconfig

from .exceptions import UsageError
from _pytest.nodeid import NodeId
from _pytest.outcomes import fail
from _pytest.pathlib import absolutepath
from _pytest.pathlib import commonpath
from _pytest.pathlib import safe_exists


@dataclass(frozen=True)
class ConfigValue:
    """Represents a configuration value with its origin and parsing mode.

    This allows tracking whether a value came from a configuration file
    or from a CLI override (--override-ini), which is important for
    determining precedence when dealing with ini option aliases.

    The mode tracks the parsing mode/data model used for the value:
    - "ini": from INI files or [tool.pytest.ini_options], where the only
      supported value types are `str` or `list[str]`.
    - "toml": from TOML files (not in INI mode), where native TOML types
       are preserved.
    """

    value: object
    _: KW_ONLY
    origin: Literal["file", "override"]
    mode: Literal["ini", "toml"]


ConfigDict: TypeAlias = dict[str, ConfigValue]


def _parse_ini_config(path: Path) -> iniconfig.IniConfig:
    """Parse the given generic '.ini' file using legacy IniConfig parser, returning
    the parsed object.

    Raise UsageError if the file cannot be parsed.
    """
    try:
        return iniconfig.IniConfig(str(path))
    except iniconfig.ParseError as exc:
        raise UsageError(str(exc)) from exc


def _parse_toml_file(path: Path) -> dict[str, object]:
    """Parse the given '.toml' file, returning the decoded document.

    Raise UsageError if the file cannot be parsed.
    """
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    toml_text = path.read_text(encoding="utf-8")
    try:
        return tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as exc:
        raise UsageError(f"{path}: {exc}") from exc


def _load_pytest_ini(path: Path) -> ConfigDict | None:
    """Load a dedicated pytest INI file (``pytest.ini``/``.pytest.ini``).

    These files are always the source of configuration, even if they lack a
    ``[pytest]`` section, in which case an empty config is returned.
    """
    iniconfig = _parse_ini_config(path)

    if "pytest" in iniconfig:
        return {
            k: ConfigValue(v, origin="file", mode="ini")
            for k, v in iniconfig["pytest"].items()
        }
    return {}


def _load_ini_file(path: Path) -> ConfigDict | None:
    """Load a generic '.ini' file (e.g. ``tox.ini``).

    Only considered if it contains a ``[pytest]`` section.
    """
    iniconfig = _parse_ini_config(path)

    if "pytest" in iniconfig:
        return {
            k: ConfigValue(v, origin="file", mode="ini")
            for k, v in iniconfig["pytest"].items()
        }
    return None


def _load_cfg_file(path: Path) -> ConfigDict | None:
    """Load a '.cfg' file (e.g. ``setup.cfg``).

    Only considered if it contains a ``[tool:pytest]`` section.
    """
    iniconfig = _parse_ini_config(path)

    if "tool:pytest" in iniconfig.sections:
        return {
            k: ConfigValue(v, origin="file", mode="ini")
            for k, v in iniconfig["tool:pytest"].items()
        }
    elif "pytest" in iniconfig.sections:
        # If a setup.cfg contains a "[pytest]" section, we raise a failure to indicate users that
        # plain "[pytest]" sections in setup.cfg files is no longer supported (#3086).
        fail(CFG_PYTEST_SECTION.format(filename="setup.cfg"), pytrace=False)
    return None


def _config_from_pytest_table(
    path: Path, config: dict[str, object]
) -> ConfigDict | None:
    """Return the configuration in the ``[pytest]`` table of a parsed TOML
    document, or None if it has none.

    Raise UsageError for options written outside of any table, which is the
    usual way of getting the table wrong.
    """
    if "pytest" in config:
        # TOML mode - preserve native TOML types.
        return {
            k: ConfigValue(v, origin="file", mode="toml")
            for k, v in config["pytest"].items()  # type: ignore[attr-defined]
        }

    top_level_options = [
        key for key, value in config.items() if not isinstance(value, dict)
    ]
    if top_level_options:
        raise UsageError(
            f"{path}: pytest configuration must be under a "
            f"[pytest] table (found top-level options: "
            f"{', '.join(top_level_options)})"
        )
    return None


def _config_from_tool_pytest(
    path: Path, config: dict[str, object]
) -> ConfigDict | None:
    """Return the configuration in the ``[tool.pytest]`` tables of a parsed
    TOML document, or None if it has none."""
    tool_pytest = config.get("tool", {}).get("pytest", {})  # type: ignore[attr-defined]

    # Check for toml mode config: [tool.pytest] with content outside of ini_options.
    toml_config = {k: v for k, v in tool_pytest.items() if k != "ini_options"}
    # Check for ini mode config: [tool.pytest.ini_options].
    ini_config = tool_pytest.get("ini_options", None)

    if toml_config and ini_config:
        raise UsageError(
            f"{path}: Cannot use both [tool.pytest] (native TOML types) and "
            "[tool.pytest.ini_options] (string-based INI format) simultaneously. "
            "Please use [tool.pytest] with native TOML types (recommended) "
            "or [tool.pytest.ini_options] for backwards compatibility."
        )

    if toml_config:
        # TOML mode - preserve native TOML types.
        return {
            k: ConfigValue(v, origin="file", mode="toml")
            for k, v in toml_config.items()
        }

    if ini_config is not None:
        # INI mode - TOML supports richer data types than INI files, but we need to
        # convert all scalar values to str for compatibility with the INI system.
        def make_scalar(v: object) -> str | list[str]:
            return v if isinstance(v, list) else str(v)

        return {
            k: ConfigValue(make_scalar(v), origin="file", mode="ini")
            for k, v in ini_config.items()
        }

    return None


def _load_pytest_toml(path: Path) -> ConfigDict | None:
    """Load a dedicated pytest TOML file (``pytest.toml``/``.pytest.toml``).

    Configuration is read from the ``[pytest]`` table in TOML mode. These files
    are always the source of configuration, even if empty.
    """
    config = _config_from_pytest_table(path, _parse_toml_file(path))
    return config if config is not None else {}


def _load_custom_toml(path: Path) -> ConfigDict | None:
    """Load a TOML file with an arbitrary name, as passed via ``-c``.

    Such a file reads its configuration from ``[pytest]``, like ``pytest.toml``
    does -- the table pytest documents for its own files (#14705). The
    ``pyproject.toml`` tables ``[tool.pytest]``/``[tool.pytest.ini_options]``,
    which arbitrary TOML files used to be parsed with exclusively, keep
    working; using both styles in one file is an error.
    """
    document = _parse_toml_file(path)

    tool_pytest_config = _config_from_tool_pytest(path, document)
    if tool_pytest_config is None:
        return _config_from_pytest_table(path, document)

    if "pytest" in document:
        raise UsageError(
            f"{path}: Cannot use both [pytest] and [tool.pytest]/"
            "[tool.pytest.ini_options] in the same file. Please use [pytest], "
            "which is what pytest's own configuration files use; the "
            "[tool.pytest] tables are meant for pyproject.toml."
        )
    return tool_pytest_config


def _load_pyproject_toml(path: Path) -> ConfigDict | None:
    """Load a ``pyproject.toml``-style file.

    Configuration is read from ``[tool.pytest]`` (TOML mode) or
    ``[tool.pytest.ini_options]`` (INI mode).
    """
    return _config_from_tool_pytest(path, _parse_toml_file(path))


#: Loaders for the config files pytest discovers by name, in precedence order.
#:
#: This mapping is the single source of truth for both *which* files are
#: considered during rootdir discovery (see :func:`locate_config`) and *how*
#: each of them is parsed.
CONFIG_LOADERS_BY_NAME: dict[str, Callable[[Path], ConfigDict | None]] = {
    "pytest.toml": _load_pytest_toml,
    ".pytest.toml": _load_pytest_toml,
    "pytest.ini": _load_pytest_ini,
    ".pytest.ini": _load_pytest_ini,
    "pyproject.toml": _load_pyproject_toml,
    "tox.ini": _load_ini_file,
    "setup.cfg": _load_cfg_file,
}

#: Fallback loaders keyed by suffix, for files that are not one of the names
#: above.
#:
#: These apply to files passed explicitly via ``-c``/``--config-file``, which
#: may have an arbitrary name. Names win over suffixes, so files with a
#: dedicated meaning keep their semantics wherever they are passed from.
CONFIG_LOADERS_BY_SUFFIX: dict[str, Callable[[Path], ConfigDict | None]] = {
    ".ini": _load_ini_file,
    ".cfg": _load_cfg_file,
    ".toml": _load_custom_toml,
}


def _get_config_loader(filepath: Path) -> Callable[[Path], ConfigDict | None] | None:
    """Return the loader responsible for the given path, if any."""
    loader = CONFIG_LOADERS_BY_NAME.get(filepath.name)
    if loader is None:
        loader = CONFIG_LOADERS_BY_SUFFIX.get(filepath.suffix)
    return loader


def load_config_dict_from_file(
    filepath: Path,
) -> ConfigDict | None:
    """Load pytest configuration from the given file path, if supported.

    Return None if the file does not contain valid pytest configuration.
    """
    loader = _get_config_loader(filepath)
    if loader is None:
        return None
    return loader(filepath)


def locate_config(
    invocation_dir: Path,
    args: Iterable[Path],
) -> tuple[Path | None, Path | None, ConfigDict, Sequence[str]]:
    """Search in the list of arguments for a valid ini-file for pytest,
    and return a tuple of (rootdir, inifile, cfg-dict, ignored-config-files), where
    ignored-config-files is a list of config basenames found that contain
    pytest configuration but were ignored."""
    config_names = list(CONFIG_LOADERS_BY_NAME)
    args = [x for x in args if not str(x).startswith("-")]
    if not args:
        args = [invocation_dir]
    found_pyproject_toml: Path | None = None
    ignored_config_files: list[str] = []

    for arg in args:
        argpath = absolutepath(arg)
        for base in (argpath, *argpath.parents):
            for index, (config_name, loader) in enumerate(
                CONFIG_LOADERS_BY_NAME.items()
            ):
                p = base / config_name
                if p.is_file():
                    if p.name == "pyproject.toml" and found_pyproject_toml is None:
                        found_pyproject_toml = p
                    ini_config = loader(p)
                    if ini_config is not None:
                        for remainder in config_names[index + 1 :]:
                            p2 = base / remainder
                            if (
                                p2.is_file()
                                and CONFIG_LOADERS_BY_NAME[remainder](p2) is not None
                            ):
                                ignored_config_files.append(remainder)
                        return base, p, ini_config, ignored_config_files
    if found_pyproject_toml is not None:
        return found_pyproject_toml.parent, found_pyproject_toml, {}, []
    return None, None, {}, []


def get_common_ancestor(
    invocation_dir: Path,
    paths: Iterable[Path],
) -> Path:
    common_ancestor: Path | None = None
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
        common_ancestor = invocation_dir
    elif common_ancestor.is_file():
        common_ancestor = common_ancestor.parent
    return common_ancestor


def get_dirs_from_args(args: Iterable[str]) -> list[Path]:
    def is_option(x: str) -> bool:
        return x.startswith("-")

    def get_dir_from_path(path: Path) -> Path:
        return path if path.is_dir() else path.parent

    # These look like paths but may not exist
    possible_paths = (
        absolutepath(NodeId.parse(arg).path) for arg in args if not is_option(arg)
    )

    return [get_dir_from_path(path) for path in possible_paths if safe_exists(path)]


def parse_override_ini(override_ini: Sequence[str] | None) -> ConfigDict:
    """Parse the -o/--override-ini command line arguments and return the overrides.

    :raises UsageError:
        If one of the values is malformed.
    """
    overrides = {}
    # override_ini is a list of "ini=value" options.
    # Always use the last item if multiple values are set for same ini-name,
    # e.g. -o foo=bar1 -o foo=bar2 will set foo to bar2.
    for ini_config in override_ini or ():
        try:
            key, user_ini_value = ini_config.split("=", 1)
        except ValueError as e:
            raise UsageError(
                f"-o/--override-ini expects option=value style (got: {ini_config!r})."
            ) from e
        else:
            overrides[key] = ConfigValue(user_ini_value, origin="override", mode="ini")
    return overrides


CFG_PYTEST_SECTION = "[pytest] section in {filename} files is no longer supported, change to [tool:pytest] instead."


def determine_setup(
    *,
    inifile: str | None,
    override_ini: Sequence[str] | None,
    args: Sequence[str],
    rootdir_cmd_arg: str | None,
    invocation_dir: Path,
) -> tuple[Path, Path | None, ConfigDict, Sequence[str]]:
    """Determine the rootdir, inifile and ini configuration values from the
    command line arguments.

    :param inifile:
        The `--inifile` command line argument, if given.
    :param override_ini:
        The -o/--override-ini command line arguments, if given.
    :param args:
        The free command line arguments.
    :param rootdir_cmd_arg:
        The `--rootdir` command line argument, if given.
    :param invocation_dir:
        The working directory when pytest was invoked.

    :raises UsageError:
    """
    rootdir = None
    dirs = get_dirs_from_args(args)
    ignored_config_files: Sequence[str] = []

    if inifile:
        inipath_ = absolutepath(inifile)
        if not inipath_.exists():
            raise UsageError(
                f"Config file '{inipath_}' not found. "
                f"Check your '-c/--config-file' option."
            )
        if inipath_.is_dir():
            raise UsageError(
                f"Config file '{inipath_}' is a directory. "
                f"Check your '-c/--config-file' option."
            )
        inipath: Path | None = inipath_
        loader = _get_config_loader(inipath_)
        if loader is not None:
            inicfg = loader(inipath_) or {}
        elif inipath_.is_file():
            supported = ", ".join(sorted(CONFIG_LOADERS_BY_SUFFIX))
            raise UsageError(
                f"Config file '{inipath_}' has an unsupported format. "
                f"Supported extensions are: {supported}."
            )
        else:
            # A file pytest has no loader for is an error, but a path that is
            # not a regular file to begin with cannot hold configuration at
            # all: it is the way to ask for no configuration, as with
            # ``--config-file=/dev/null``.
            inicfg = {}
        if rootdir_cmd_arg is None:
            if inipath_.is_file():
                rootdir = inipath_.parent
            else:
                # Such a path also says nothing about where the project lives,
                # so the rootdir must not be derived from it -- otherwise
                # ``--config-file=/dev/null`` roots at ``/dev`` and the cache
                # plugin warns that it cannot write ``/dev/.pytest_cache``
                # (#11502).
                rootdir = get_common_ancestor(invocation_dir, dirs)
                if is_fs_root(rootdir):
                    rootdir = invocation_dir
    else:
        ancestor = get_common_ancestor(invocation_dir, dirs)
        rootdir, inipath, inicfg, ignored_config_files = locate_config(
            invocation_dir, [ancestor]
        )
        if rootdir is None and rootdir_cmd_arg is None:
            for possible_rootdir in (ancestor, *ancestor.parents):
                if (possible_rootdir / "setup.py").is_file():
                    rootdir = possible_rootdir
                    break
            else:
                if dirs != [ancestor]:
                    rootdir, inipath, inicfg, _ = locate_config(invocation_dir, dirs)
                if rootdir is None:
                    rootdir = get_common_ancestor(
                        invocation_dir, [invocation_dir, ancestor]
                    )
                    if is_fs_root(rootdir):  # pragma: no cover
                        rootdir = ancestor
    if rootdir_cmd_arg:
        rootdir = absolutepath(os.path.expandvars(rootdir_cmd_arg))
        if not rootdir.is_dir():
            raise UsageError(
                f"Directory '{rootdir}' not found. Check your '--rootdir' option."
            )

    ini_overrides = parse_override_ini(override_ini)
    inicfg.update(ini_overrides)

    assert rootdir is not None
    return rootdir, inipath, inicfg, ignored_config_files


def is_fs_root(p: Path) -> bool:
    r"""
    Return True if the given path is pointing to the root of the
    file system ("/" on Unix and "C:\\" on Windows for example).
    """
    return os.path.splitdrive(str(p))[1] == os.sep
