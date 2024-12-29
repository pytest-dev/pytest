"""Core implementation of the testing process: init, session, runtest loop."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from collections.abc import Set as AbstractSet
import dataclasses
import fnmatch
import functools
import importlib
import importlib.util
import os
from pathlib import Path
import sys
from typing import final
from typing import Literal
from typing import overload
from typing import TYPE_CHECKING
import warnings

import pluggy

from _pytest import nodes
import _pytest._code
from _pytest.config import Config
from _pytest.config import directory_arg
from _pytest.config import ExitCode
from _pytest.config import hookimpl
from _pytest.config import PytestPluginManager
from _pytest.config import UsageError
from _pytest.config.argparsing import Parser
from _pytest.config.compat import PathAwareHookProxy
from _pytest.outcomes import exit
from _pytest.pathlib import absolutepath
from _pytest.pathlib import bestrelpath
from _pytest.pathlib import fnmatch_ex
from _pytest.pathlib import safe_exists
from _pytest.pathlib import scandir
from _pytest.reports import CollectReport
from _pytest.reports import TestReport
from _pytest.runner import collect_one_node
from _pytest.runner import SetupState
from _pytest.warning_types import PytestWarning


if TYPE_CHECKING:
    from typing_extensions import Self

    from _pytest.fixtures import FixtureManager


def pytest_addoption(parser: Parser) -> None:
    parser.addini(
        "norecursedirs",
        "Directory patterns to avoid for recursion",
        type="args",
        default=[
            "*.egg",
            ".*",
            "_darcs",
            "build",
            "CVS",
            "dist",
            "node_modules",
            "venv",
            "{arch}",
        ],
    )
    parser.addini(
        "testpaths",
        "Directories to search for tests when no files or directories are given on the "
        "command line",
        type="args",
        default=[],
    )
    parser.addini(
        "collect_imported_tests",
        "Whether to collect tests in imported modules outside `testpaths`",
        type="bool",
        default=True,
    )
    group = parser.getgroup("general", "Running and selection options")
    group._addoption(
        "-x",
        "--exitfirst",
        action="store_const",
        dest="maxfail",
        const=1,
        help="Exit instantly on first error or failed test",
    )
    group = parser.getgroup("pytest-warnings")
    group.addoption(
        "-W",
        "--pythonwarnings",
        action="append",
        help="Set which warnings to report, see -W option of Python itself",
    )
    parser.addini(
        "filterwarnings",
        type="linelist",
        help="Each line specifies a pattern for "
        "warnings.filterwarnings. "
        "Processed after -W/--pythonwarnings.",
    )
    group._addoption(
        "--maxfail",
        metavar="num",
        action="store",
        type=int,
        dest="maxfail",
        default=0,
        help="Exit after first num failures or errors",
    )
    group._addoption(
        "--strict-config",
        action="store_true",
        help="Any warnings encountered while parsing the `pytest` section of the "
        "configuration file raise errors",
    )
    group._addoption(
        "--strict-markers",
        action="store_true",
        help="Markers not registered in the `markers` section of the configuration "
        "file raise errors",
    )
    group._addoption(
        "--strict",
        action="store_true",
        help="(Deprecated) alias to --strict-markers",
    )
    group._addoption(
        "-c",
        "--config-file",
        metavar="FILE",
        type=str,
        dest="inifilename",
        help="Load configuration from `FILE` instead of trying to locate one of the "
        "implicit configuration files.",
    )
    group._addoption(
        "--continue-on-collection-errors",
        action="store_true",
        default=False,
        dest="continue_on_collection_errors",
        help="Force test execution even if collection errors occur",
    )
    group._addoption(
        "--rootdir",
        action="store",
        dest="rootdir",
        help="Define root directory for tests. Can be relative path: 'root_dir', './root_dir', "
        "'root_dir/another_dir/'; absolute path: '/home/user/root_dir'; path with variables: "
        "'$HOME/root_dir'.",
    )

    group = parser.getgroup("collect", "collection")
    group.addoption(
        "--collectonly",
        "--collect-only",
        "--co",
        action="store_true",
        help="Only collect tests, don't execute them",
    )
    group.addoption(
        "--pyargs",
        action="store_true",
        help="Try to interpret all arguments as Python packages",
    )
    group.addoption(
        "--ignore",
        action="append",
        metavar="path",
        help="Ignore path during collection (multi-allowed)",
    )
    group.addoption(
        "--ignore-glob",
        action="append",
        metavar="path",
        help="Ignore path pattern during collection (multi-allowed)",
    )
    group.addoption(
        "--deselect",
        action="append",
        metavar="nodeid_prefix",
        help="Deselect item (via node id prefix) during collection (multi-allowed)",
    )
    group.addoption(
        "--confcutdir",
        dest="confcutdir",
        default=None,
        metavar="dir",
        type=functools.partial(directory_arg, optname="--confcutdir"),
        help="Only load conftest.py's relative to specified dir",
    )
    group.addoption(
        "--noconftest",
        action="store_true",
        dest="noconftest",
        default=False,
        help="Don't load any conftest.py files",
    )
    group.addoption(
        "--keepduplicates",
        "--keep-duplicates",
        action="store_true",
        dest="keepduplicates",
        default=False,
        help="Keep duplicate tests",
    )
    group.addoption(
        "--collect-in-virtualenv",
        action="store_true",
        dest="collect_in_virtualenv",
        default=False,
        help="Don't ignore tests in a local virtualenv directory",
    )
    group.addoption(
        "--import-mode",
        default="prepend",
        choices=["prepend", "append", "importlib"],
        dest="importmode",
        help="Prepend/append to sys.path when importing test modules and conftest "
        "files. Default: prepend.",
    )
    parser.addini(
        "consider_namespace_packages",
        type="bool",
        default=False,
        help="Consider namespace packages when resolving module names during import",
    )

    group = parser.getgroup("debugconfig", "test session debugging and configuration")
    group.addoption(
        "--basetemp",
        dest="basetemp",
        default=None,
        type=validate_basetemp,
        metavar="dir",
        help=(
            "Base temporary directory for this test run. "
            "(Warning: this directory is removed if it exists.)"
        ),
    )


def validate_basetemp(path: str) -> str:
    """
    Validate the provided `basetemp` path to ensure it is not empty, 
    the current working directory (cwd), or any ancestor of the cwd.

    Args:
        path (str): The path to validate.

    Returns:
        str: The validated path.

    Raises:
        argparse.ArgumentTypeError: If the path is invalid.
    """
    # GH 7119: Issue reference for additional context on the validation requirements.
    msg = "basetemp must not be empty, the current working directory or any parent directory of it"

    # Ensure the path is not empty.
    if not path:
        raise argparse.ArgumentTypeError(msg)

    def is_ancestor(base: Path, query: Path) -> bool:
        """
        Check if `query` is an ancestor of `base`.

        Args:
            base (Path): The base path to compare.
            query (Path): The potential ancestor path.

        Returns:
            bool: True if `query` is an ancestor of `base`, False otherwise.
        """
        if base == query:
            return True
        return query in base.parents

    # Ensure the path is not an ancestor of the current working directory (cwd).
    if is_ancestor(Path.cwd(), Path(path).absolute()):
        raise argparse.ArgumentTypeError(msg)

    # Check symlinks to ensure the resolved path is not an ancestor of cwd.
    if is_ancestor(Path.cwd().resolve(), Path(path).resolve()):
        raise argparse.ArgumentTypeError(msg)

    return path


def wrap_session(
    config: Config, doit: Callable[[Config, Session], int | ExitCode | None]
) -> int | ExitCode:
    """
    Run the main pytest session while managing initialization, 
    cleanup, and error handling.

    Args:
        config (Config): The pytest configuration object.
        doit (Callable): A callable that performs the main logic of the session.

    Returns:
        int | ExitCode: The exit status of the pytest session.
    """
    session = Session.from_config(config)  # Create a session from the configuration.
    session.exitstatus = ExitCode.OK
    initstate = 0  # Track initialization progress for error handling.

    try:
        try:
            config._do_configure()  # Configure pytest.
            initstate = 1
            config.hook.pytest_sessionstart(session=session)  # Trigger session start hooks.
            initstate = 2
            session.exitstatus = doit(config, session) or 0  # Run the main logic.
        except UsageError:
            session.exitstatus = ExitCode.USAGE_ERROR
            raise
        except Failed:
            session.exitstatus = ExitCode.TESTS_FAILED
        except (KeyboardInterrupt, exit.Exception):
            # Handle user interruption or pytest-specific exit exceptions.
            excinfo = _pytest._code.ExceptionInfo.from_current()
            exitstatus: int | ExitCode = ExitCode.INTERRUPTED
            if isinstance(excinfo.value, exit.Exception):
                if excinfo.value.returncode is not None:
                    exitstatus = excinfo.value.returncode
                if initstate < 2:
                    sys.stderr.write(f"{excinfo.typename}: {excinfo.value.msg}\n")
            config.hook.pytest_keyboard_interrupt(excinfo=excinfo)
            session.exitstatus = exitstatus
        except BaseException:
            # Handle unexpected exceptions.
            session.exitstatus = ExitCode.INTERNAL_ERROR
            excinfo = _pytest._code.ExceptionInfo.from_current()
            try:
                config.notify_exception(excinfo, config.option)
            except exit.Exception as exc:
                if exc.returncode is not None:
                    session.exitstatus = exc.returncode
                sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
            else:
                if isinstance(excinfo.value, SystemExit):
                    sys.stderr.write("mainloop: caught unexpected SystemExit!\n")
    finally:
        # Cleanup logic and session finalization.
        excinfo = None  # Explicitly break reference cycle.
        os.chdir(session.startpath)  # Restore original working directory.
        if initstate >= 2:
            try:
                config.hook.pytest_sessionfinish(
                    session=session, exitstatus=session.exitstatus
                )
            except exit.Exception as exc:
                if exc.returncode is not None:
                    session.exitstatus = exc.returncode
                sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        config._ensure_unconfigure()  # Ensure proper unconfiguration.

    return session.exitstatus


def pytest_cmdline_main(config: Config) -> int | ExitCode:
    """
    Main entry point for the pytest command line interface.

    Args:
        config (Config): The pytest configuration object.

    Returns:
        int | ExitCode: The exit status of the pytest session.
    """
    return wrap_session(config, _main)
    def pytest_collection(session: Session) -> None:
    """
    Trigger the collection process for the current test session.

    Args:
        session (Session): The pytest session object containing collected items.
    """
    session.perform_collect()


def pytest_runtestloop(session: Session) -> bool:
    """
    Execute the main loop for running tests.

    Handles the execution of collected test items and manages interrupts
    or failures during the process.

    Args:
        session (Session): The pytest session object.

    Returns:
        bool: True if collection-only mode is active; otherwise, execution continues.

    Raises:
        session.Interrupted: If collection errors or a manual stop condition occurs.
        session.Failed: If a stopping failure condition is met.
    """
    # Check for test collection failures and handle user-configured continuation.
    if session.testsfailed and not session.config.option.continue_on_collection_errors:
        raise session.Interrupted(
            f"{session.testsfailed} error{'s' if session.testsfailed != 1 else ''} during collection"
        )

    # Return early if only collecting tests, not running them.
    if session.config.option.collectonly:
        return True

    # Iterate through collected items and execute each test.
    for i, item in enumerate(session.items):
        nextitem = session.items[i + 1] if i + 1 < len(session.items) else None
        item.config.hook.pytest_runtest_protocol(item=item, nextitem=nextitem)

        # Handle failure or stop conditions.
        if session.shouldfail:
            raise session.Failed(session.shouldfail)
        if session.shouldstop:
            raise session.Interrupted(session.shouldstop)
    return True


def _in_venv(path: Path) -> bool:
    """
    Check if the given path is the root of a virtual environment.

    This is done by verifying the existence of the `pyvenv.cfg` file or
    a `conda-meta/history` file in the given path.

    Args:
        path (Path): The directory path to check.

    Returns:
        bool: True if the directory is part of a virtual environment; False otherwise.

    Exceptions:
        OSError: If an OS-level error occurs during the check.
    """
    try:
        return (
            path.joinpath("pyvenv.cfg").is_file()
            or path.joinpath("conda-meta", "history").is_file()
        )
    except OSError:
        return False


def pytest_ignore_collect(collection_path: Path, config: Config) -> bool | None:
    """
    Determine if a given path should be ignored during test collection.

    This considers various factors such as ignored paths, virtual environments,
    and configured patterns to avoid during collection.

    Args:
        collection_path (Path): The path to check for collection exclusion.
        config (Config): The pytest configuration object.

    Returns:
        bool | None: True if the path should be ignored, False if it should not,
                     or None if no definitive decision can be made.
    """
    # Ignore `__pycache__` directories as they do not contain tests.
    if collection_path.name == "__pycache__":
        return True

    # Retrieve and check paths configured to be ignored.
    ignore_paths = config._getconftest_pathlist(
        "collect_ignore", path=collection_path.parent
    )
    # Check for paths to be ignored
ignore_paths = ignore_paths or []  # If ignore_paths is empty, assign an empty list.
excludeopt = config.getoption("ignore")  # Get ignore options from command-line settings
if excludeopt:
    # Add additional paths to ignore_paths
    ignore_paths.extend(absolutepath(x) for x in excludeopt)

# If the collection path is in the ignore paths, we ignore it
if collection_path in ignore_paths:
    return True

# Check for glob patterns for paths to be ignored
ignore_globs = config._getconftest_pathlist(
    "collect_ignore_glob", path=collection_path.parent
)
ignore_globs = ignore_globs or []  # If ignore_globs is empty, assign an empty list.
excludeglobopt = config.getoption("ignore_glob")  # Get ignore_glob options from command-line settings
if excludeglobopt:
    # Add glob patterns to ignore_globs
    ignore_globs.extend(absolutepath(x) for x in excludeglobopt)

# If the collection path matches any of the glob patterns, we ignore it
if any(fnmatch.fnmatch(str(collection_path), str(glob)) for glob in ignore_globs):
    return True

# Check if the path is within a virtual environment
allow_in_venv = config.getoption("collect_in_virtualenv")
if not allow_in_venv and _in_venv(collection_path):
    return True

# If the collection path is a directory, check for directory ignore patterns
if collection_path.is_dir():
    norecursepatterns = config.getini("norecursedirs")  # Get directory ignore patterns
    if any(fnmatch_ex(pat, collection_path) for pat in norecursepatterns):
        return True

# If none of the above conditions match, collect the path
return None

# Function for collecting directories
def pytest_collect_directory(
    path: Path, parent: nodes.Collector
) -> nodes.Collector | None:
    """
    Collect files in a directory and return a collector for the directory.

    Args:
        path (Path): The directory path to collect from.
        parent (nodes.Collector): The parent collector.

    Returns:
        nodes.Collector | None: The directory collector or None if no collection happens.
    """
    return Dir.from_parent(parent, path=path)

# Function to modify the list of collected items based on deselect prefixes
def pytest_collection_modifyitems(items: list[nodes.Item], config: Config) -> None:
    """
    Modify collected items based on deselect prefixes.

    Args:
        items (list): The list of collected test items.
        config (Config): The pytest configuration object.

    Returns:
        None: Modifies the list in place.
    """
    deselect_prefixes = tuple(config.getoption("deselect") or [])  # Get deselect prefixes
    if not deselect_prefixes:
        return

    remaining = []
    deselected = []
    for colitem in items:
        # If the item matches a deselect prefix, remove it from the selected list
        if colitem.nodeid.startswith(deselect_prefixes):
            deselected.append(colitem)
        else:
            remaining.append(colitem)

    # If items were deselected, notify and update the list
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining  # Update the list of items

# Proxy class for managing filesystem hook calls
class FSHookProxy:
    def __init__(
        self,
        pm: PytestPluginManager,
        remove_mods: AbstractSet[object],
    ) -> None:
        """
        Proxy class for managing the file system hook calls.

        Args:
            pm (PytestPluginManager): The pytest plugin manager.
            remove_mods (AbstractSet[object]): Set of plugins to remove.
        """
        self.pm = pm
        self.remove_mods = remove_mods

    def __getattr__(self, name: str) -> pluggy.HookCaller:
        """
        Dynamically retrieves hook calls for the given name.

        Args:
            name (str): The name of the hook to retrieve.

        Returns:
            pluggy.HookCaller: The hook caller for the given hook.
        """
        x = self.pm.subset_hook_caller(name, remove_plugins=self.remove_mods)
        self.__dict__[name] = x
        return x

# Exception class for interrupted test runs
class Interrupted(KeyboardInterrupt):
    """Signals that the test run was interrupted."""

    __module__ = "builtins"  # For py3.

class Failed(Exception):
    """Signals a stop as failed test run."""

# Cache class for storing best relative paths for improved performance
@dataclasses.dataclass
class _bestrelpath_cache(dict[Path, str]):
    """
    Cache for storing best relative paths for improved performance.

    Attributes:
        path (Path): The base path for calculating relative paths.
    """
    __slots__ = ("path",)

    path: Path

    def __missing__(self, path: Path) -> str:
        """
        Retrieves the best relative path for a given path.

        Args:
            path (Path): The path to calculate the relative path for.

        Returns:
            str: The best relative path.
        """
        r = bestrelpath(self.path, path)
        self[path] = r
        return r

# Directory collector class for collecting files in a directory
@final
class Dir(nodes.Directory):
    """Collector of files in a file system directory.

    .. versionadded:: 8.0

    .. note::
        This collector is responsible for gathering all files within a directory.
    """
# Check if collection path should be ignored based on patterns
ignore_paths = ignore_paths or []  # If ignore_paths is empty, assign an empty list.
excludeopt = config.getoption("ignore")  # Get the ignore option from command-line arguments.
if excludeopt:
    # Add additional paths to the ignore_paths list
    ignore_paths.extend(absolutepath(x) for x in excludeopt)

# If the collection path is in the ignore paths, we return True to indicate it should be ignored.
if collection_path in ignore_paths:
    return True

# Check for ignore glob patterns
ignore_globs = config._getconftest_pathlist(
    "collect_ignore_glob", path=collection_path.parent
)
ignore_globs = ignore_globs or []  # If ignore_globs is empty, assign an empty list.
excludeglobopt = config.getoption("ignore_glob")  # Get the ignore glob option from command-line arguments.
if excludeglobopt:
    # Add additional glob patterns to the ignore_globs list.
    ignore_globs.extend(absolutepath(x) for x in excludeglobopt)

# If the collection path matches any ignore glob pattern, we return True to ignore it.
if any(fnmatch.fnmatch(str(collection_path), str(glob)) for glob in ignore_globs):
    return True

# Check if the path is inside a virtual environment
allow_in_venv = config.getoption("collect_in_virtualenv")
if not allow_in_venv and _in_venv(collection_path):
    return True

# If the collection path is a directory, check if it matches the norecurse patterns.
if collection_path.is_dir():
    norecursepatterns = config.getini("norecursedirs")  # Get the norecurse patterns from configuration.
    if any(fnmatch_ex(pat, collection_path) for pat in norecursepatterns):
        return True

# If none of the above conditions are met, return None to indicate the path should be collected.
return None

# Function to collect directories from the filesystem.
def pytest_collect_directory(
    path: Path, parent: nodes.Collector
) -> nodes.Collector | None:
    """
    Collects files from the specified directory and returns a collector for that directory.

    Args:
        path (Path): The directory path to collect files from.
        parent (nodes.Collector): The parent collector object.

    Returns:
        nodes.Collector | None: Returns a directory collector or None if no files are collected.
    """
    return Dir.from_parent(parent, path=path)

# Function to modify collected items based on deselection criteria.
def pytest_collection_modifyitems(items: list[nodes.Item], config: Config) -> None:
    """
    Modify the collected items list based on deselection prefixes from the command line.

    Args:
        items (list): The list of collected test items.
        config (Config): The pytest configuration object.

    Returns:
        None: This function modifies the items list in place.
    """
    deselect_prefixes = tuple(config.getoption("deselect") or [])  # Get deselect prefixes from the config.
    if not deselect_prefixes:
        return

    remaining = []
    deselected = []
    for colitem in items:
        # If an item matches a deselect prefix, move it to the deselected list.
        if colitem.nodeid.startswith(deselect_prefixes):
            deselected.append(colitem)
        else:
            remaining.append(colitem)

    # If any items were deselected, update the list and notify through the pytest hook.
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining  # Update the items list with the remaining items.

# Proxy class to manage hook calls related to filesystem operations.
class FSHookProxy:
    def __init__(
        self,
        pm: PytestPluginManager,
        remove_mods: AbstractSet[object],
    ) -> None:
        """
        Proxy class to manage hook calls related to the file system.

        Args:
            pm (PytestPluginManager): The pytest plugin manager.
            remove_mods (AbstractSet[object]): A set of plugins to remove.
        """
        self.pm = pm
        self.remove_mods = remove_mods

    def __getattr__(self, name: str) -> pluggy.HookCaller:
        """
        Retrieves hook callers dynamically based on the hook name.

        Args:
            name (str): The name of the hook to retrieve.

        Returns:
            pluggy.HookCaller: The hook caller associated with the given hook name.
        """
        x = self.pm.subset_hook_caller(name, remove_plugins=self.remove_mods)
        self.__dict__[name] = x
        return x

# Exception class to handle interrupted test runs.
class Interrupted(KeyboardInterrupt):
    """Signals that the test run was interrupted."""

    __module__ = "builtins"  # For Python 3.

class Failed(Exception):
    """Signals that the test run should stop due to a failed test."""

# Cache class for storing and retrieving best relative paths to optimize performance.
@dataclasses.dataclass
class _bestrelpath_cache(dict[Path, str]):
    """
    Cache for storing best relative paths to optimize performance.

    Attributes:
        path (Path): The base path used for calculating relative paths.
    """
    __slots__ = ("path",)

    path: Path

    def __missing__(self, path: Path) -> str:
        """
        Retrieves the best relative path for a given path.

        Args:
            path (Path): The path for which to compute the best relative path.

        Returns:
            str: The best relative path.
        """
        r = bestrelpath(self.path, path)  # Calculate the best relative path.
        self[path] = r  # Store the result in the cache.
        return r

# Class for collecting files in a directory (extends nodes.Directory).
@final
class Dir(nodes.Directory):
    """Collector for files in a filesystem directory.

    .. versionadded:: 8.0

    .. note::
        This collector is responsible for gathering all files within a directory.
    """




    @classmethod
    def from_parent(  # type: ignore[override]
        cls,
        parent: nodes.Collector,
        *,
        path: Path,
    ) -> Self:
        """The public constructor.

        :param parent: The parent collector of this Dir.
        :param path: The directory's path.
        :type path: pathlib.Path
        """
        return super().from_parent(parent=parent, path=path)

    def collect(self) -> Iterable[nodes.Item | nodes.Collector]:
        config = self.config
        col: nodes.Collector | None
        cols: Sequence[nodes.Collector]
        ihook = self.ihook
        for direntry in scandir(self.path):
            if direntry.is_dir():
                path = Path(direntry.path)
                if not self.session.isinitpath(path, with_parents=True):
                    if ihook.pytest_ignore_collect(collection_path=path, config=config):
                        continue
                col = ihook.pytest_collect_directory(path=path, parent=self)
                if col is not None:
                    yield col

            elif direntry.is_file():
                path = Path(direntry.path)
                if not self.session.isinitpath(path):
                    if ihook.pytest_ignore_collect(collection_path=path, config=config):
                        continue
                cols = ihook.pytest_collect_file(file_path=path, parent=self)
                yield from cols


@final
class Session(nodes.Collector):
    """The root of the collection tree.

    ``Session`` collects the initial paths given as arguments to pytest.
    """

    Interrupted = Interrupted
    Failed = Failed
    # Set on the session by runner.pytest_sessionstart.
    _setupstate: SetupState
    # Set on the session by fixtures.pytest_sessionstart.
    _fixturemanager: FixtureManager
    exitstatus: int | ExitCode

    def __init__(self, config: Config) -> None:
        super().__init__(
            name="",
            path=config.rootpath,
            fspath=None,
            parent=None,
            config=config,
            session=self,
            nodeid="",
        )
        self.testsfailed = 0
        self.testscollected = 0
        self._shouldstop: bool | str = False
        self._shouldfail: bool | str = False
        self.trace = config.trace.root.get("collection")
        self._initialpaths: frozenset[Path] = frozenset()
        self._initialpaths_with_parents: frozenset[Path] = frozenset()
        self._notfound: list[tuple[str, Sequence[nodes.Collector]]] = []
        self._initial_parts: list[CollectionArgument] = []
        self._collection_cache: dict[nodes.Collector, CollectReport] = {}
        self.items: list[nodes.Item] = []

        self._bestrelpathcache: dict[Path, str] = _bestrelpath_cache(config.rootpath)

        self.config.pluginmanager.register(self, name="session")

    @classmethod
    def from_config(cls, config: Config) -> Session:
        session: Session = cls._create(config=config)
        return session

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} {self.name} "
            f"exitstatus=%r "
            f"testsfailed={self.testsfailed} "
            f"testscollected={self.testscollected}>"
        ) % getattr(self, "exitstatus", "<UNSET>")

    @property
    def shouldstop(self) -> bool | str:
        return self._shouldstop

    @shouldstop.setter
    def shouldstop(self, value: bool | str) -> None:
        # The runner checks shouldfail and assumes that if it is set we are
        # definitely stopping, so prevent unsetting it.
        if value is False and self._shouldstop:
            warnings.warn(
                PytestWarning(
                    "session.shouldstop cannot be unset after it has been set; ignoring."
                ),
                stacklevel=2,
            )
            return
        self._shouldstop = value

    @property
    def shouldfail(self) -> bool | str:
        return self._shouldfail

    @shouldfail.setter
    def shouldfail(self, value: bool | str) -> None:
        # The runner checks shouldfail and assumes that if it is set we are
        # definitely stopping, so prevent unsetting it.
        if value is False and self._shouldfail:
            warnings.warn(
                PytestWarning(
                    "session.shouldfail cannot be unset after it has been set; ignoring."
                ),
                stacklevel=2,
            )
            return
        self._shouldfail = value

    @property
    def startpath(self) -> Path:
        """The path from which pytest was invoked.

        .. versionadded:: 7.0.0
        """
        return self.config.invocation_params.dir

    def _node_location_to_relpath(self, node_path: Path) -> str:
        # bestrelpath is a quite slow function.
        return self._bestrelpathcache[node_path]

    @hookimpl(tryfirst=True)
    def pytest_collectstart(self) -> None:
        if self.shouldfail:
            raise self.Failed(self.shouldfail)
        if self.shouldstop:
            raise self.Interrupted(self.shouldstop)

    @hookimpl(tryfirst=True)
    def pytest_runtest_logreport(self, report: TestReport | CollectReport) -> None:
        if report.failed and not hasattr(report, "wasxfail"):
            self.testsfailed += 1
            maxfail = self.config.getvalue("maxfail")
            if maxfail and self.testsfailed >= maxfail:
                self.shouldfail = f"stopping after {self.testsfailed} failures"

    pytest_collectreport = pytest_runtest_logreport

    def isinitpath(
        self,
        path: str | os.PathLike[str],
        *,
        with_parents: bool = False,
    ) -> bool:
        """Is path an initial path?

        An initial path is a path explicitly given to pytest on the command
        line.

        :param with_parents:
            If set, also return True if the path is a parent of an initial path.

        .. versionchanged:: 8.0
            Added the ``with_parents`` parameter.
        """
        # Optimization: Path(Path(...)) is much slower than isinstance.
        path_ = path if isinstance(path, Path) else Path(path)
        if with_parents:
            return path_ in self._initialpaths_with_parents
        else:
            return path_ in self._initialpaths

    def gethookproxy(self, fspath: os.PathLike[str]) -> pluggy.HookRelay:
        # Optimization: Path(Path(...)) is much slower than isinstance.
        path = fspath if isinstance(fspath, Path) else Path(fspath)
        pm = self.config.pluginmanager
        # Check if we have the common case of running
        # hooks with all conftest.py files.
        my_conftestmodules = pm._getconftestmodules(path)
        remove_mods = pm._conftest_plugins.difference(my_conftestmodules)
        proxy: pluggy.HookRelay
        if remove_mods:
            # One or more conftests are not in use at this path.
            proxy = PathAwareHookProxy(FSHookProxy(pm, remove_mods))  # type: ignore[arg-type,assignment]
        else:
            # All plugins are active for this fspath.
            proxy = self.config.hook
        return proxy

    def _collect_path(
        self,
        path: Path,
        path_cache: dict[Path, Sequence[nodes.Collector]],
    ) -> Sequence[nodes.Collector]:
        """Create a Collector for the given path.

        `path_cache` makes it so the same Collectors are returned for the same
        path.
        """
        if path in path_cache:
            return path_cache[path]

        if path.is_dir():
            ihook = self.gethookproxy(path.parent)
            col: nodes.Collector | None = ihook.pytest_collect_directory(
                path=path, parent=self
            )
            cols: Sequence[nodes.Collector] = (col,) if col is not None else ()

        elif path.is_file():
            ihook = self.gethookproxy(path)
            cols = ihook.pytest_collect_file(file_path=path, parent=self)

        else:
            # Broken symlink or invalid/missing file.
            cols = ()

        path_cache[path] = cols
        return cols

    @overload
    def perform_collect(
        self, args: Sequence[str] | None = ..., genitems: Literal[True] = ...
    ) -> Sequence[nodes.Item]: ...

    @overload
    def perform_collect(
        self, args: Sequence[str] | None = ..., genitems: bool = ...
    ) -> Sequence[nodes.Item | nodes.Collector]: ...

    def perform_collect(
        self, args: Sequence[str] | None = None, genitems: bool = True
    ) -> Sequence[nodes.Item | nodes.Collector]:
        """Perform the collection phase for this session.

        This is called by the default :hook:`pytest_collection` hook
        implementation; see the documentation of this hook for more details.
        For testing purposes, it may also be called directly on a fresh
        ``Session``.

        This function normally recursively expands any collectors collected
        from the session to their items, and only items are returned. For
        testing purposes, this may be suppressed by passing ``genitems=False``,
        in which case the return value contains these collectors unexpanded,
        and ``session.items`` is empty.
        """
        if args is None:
            args = self.config.args

        self.trace("perform_collect", self, args)
        self.trace.root.indent += 1

        hook = self.config.hook

        self._notfound = []
        self._initial_parts = []
        self._collection_cache = {}
        self.items = []
        items: Sequence[nodes.Item | nodes.Collector] = self.items
        try:
            initialpaths: list[Path] = []
            initialpaths_with_parents: list[Path] = []
            for arg in args:
                collection_argument = resolve_collection_argument(
                    self.config.invocation_params.dir,
                    arg,
                    as_pypath=self.config.option.pyargs,
                )
                self._initial_parts.append(collection_argument)
                initialpaths.append(collection_argument.path)
                initialpaths_with_parents.append(collection_argument.path)
                initialpaths_with_parents.extend(collection_argument.path.parents)
            self._initialpaths = frozenset(initialpaths)
            self._initialpaths_with_parents = frozenset(initialpaths_with_parents)

            rep = collect_one_node(self)
            self.ihook.pytest_collectreport(report=rep)
            self.trace.root.indent -= 1
            if self._notfound:
                errors = []
                for arg, collectors in self._notfound:
                    if collectors:
                        errors.append(
                            f"not found: {arg}\n(no match in any of {collectors!r})"
                        )
                    else:
                        errors.append(f"found no collectors for {arg}")

                raise UsageError(*errors)

            if not genitems:
                items = rep.result
            else:
                if rep.passed:
                    for node in rep.result:
                        self.items.extend(self.genitems(node))

            self.config.pluginmanager.check_pending()
            hook.pytest_collection_modifyitems(
                session=self, config=self.config, items=items
            )
        finally:
            self._notfound = []
            self._initial_parts = []
            self._collection_cache = {}
            hook.pytest_collection_finish(session=self)

        if genitems:
            self.testscollected = len(items)

        return items

    def _collect_one_node(
        self,
        node: nodes.Collector,
        handle_dupes: bool = True,
    ) -> tuple[CollectReport, bool]:
        if node in self._collection_cache and handle_dupes:
            rep = self._collection_cache[node]
            return rep, True
        else:
            rep = collect_one_node(node)
            self._collection_cache[node] = rep
            return rep, False

    def collect(self) -> Iterator[nodes.Item | nodes.Collector]:
        # This is a cache for the root directories of the initial paths.
        # We can't use collection_cache for Session because of its special
        # role as the bootstrapping collector.
        path_cache: dict[Path, Sequence[nodes.Collector]] = {}

        pm = self.config.pluginmanager

        for collection_argument in self._initial_parts:
            self.trace("processing argument", collection_argument)
            self.trace.root.indent += 1

            argpath = collection_argument.path
            names = collection_argument.parts
            module_name = collection_argument.module_name

            # resolve_collection_argument() ensures this.
            if argpath.is_dir():
                assert not names, f"invalid arg {(argpath, names)!r}"

            paths = [argpath]
            # Add relevant parents of the path, from the root, e.g.
            #   /a/b/c.py -> [/, /a, /a/b, /a/b/c.py]
            if module_name is None:
                # Paths outside of the confcutdir should not be considered.
                for path in argpath.parents:
                    if not pm._is_in_confcutdir(path):
                        break
                    paths.insert(0, path)
            else:
                # For --pyargs arguments, only consider paths matching the module
                # name. Paths beyond the package hierarchy are not included.
                module_name_parts = module_name.split(".")
                for i, path in enumerate(argpath.parents, 2):
                    if i > len(module_name_parts) or path.stem != module_name_parts[-i]:
                        break
                    paths.insert(0, path)

            # Start going over the parts from the root, collecting each level
            # and discarding all nodes which don't match the level's part.
            any_matched_in_initial_part = False
            notfound_collectors = []
            work: list[tuple[nodes.Collector | nodes.Item, list[Path | str]]] = [
                (self, [*paths, *names])
            ]
            while work:
                matchnode, matchparts = work.pop()

                # Pop'd all of the parts, this is a match.
                if not matchparts:
                    yield matchnode
                    any_matched_in_initial_part = True
                    continue

                # Should have been matched by now, discard.
                if not isinstance(matchnode, nodes.Collector):
                    continue

                # Collect this level of matching.
                # Collecting Session (self) is done directly to avoid endless
                # recursion to this function.
                subnodes: Sequence[nodes.Collector | nodes.Item]
                if isinstance(matchnode, Session):
                    assert isinstance(matchparts[0], Path)
                    subnodes = matchnode._collect_path(matchparts[0], path_cache)
                else:
                    # For backward compat, files given directly multiple
                    # times on the command line should not be deduplicated.
                    handle_dupes = not (
                        len(matchparts) == 1
                        and isinstance(matchparts[0], Path)
                        and matchparts[0].is_file()
                    )
                    rep, duplicate = self._collect_one_node(matchnode, handle_dupes)
                    if not duplicate and not rep.passed:
                        # Report collection failures here to avoid failing to
                        # run some test specified in the command line because
                        # the module could not be imported (#134).
                        matchnode.ihook.pytest_collectreport(report=rep)
                    if not rep.passed:
                        continue
                    subnodes = rep.result

                # Prune this level.
                any_matched_in_collector = False
                for node in reversed(subnodes):
                    # Path part e.g. `/a/b/` in `/a/b/test_file.py::TestIt::test_it`.
                    if isinstance(matchparts[0], Path):
                        is_match = node.path == matchparts[0]
                        if sys.platform == "win32" and not is_match:
                            # In case the file paths do not match, fallback to samefile() to
                            # account for short-paths on Windows (#11895).
                            same_file = os.path.samefile(node.path, matchparts[0])
                            # We don't want to match links to the current node,
                            # otherwise we would match the same file more than once (#12039).
                            is_match = same_file and (
                                os.path.islink(node.path)
                                == os.path.islink(matchparts[0])
                            )

                    # Name part e.g. `TestIt` in `/a/b/test_file.py::TestIt::test_it`.
                    else:
                        # TODO: Remove parametrized workaround once collection structure contains
                        # parametrization.
                        is_match = (
                            node.name == matchparts[0]
                            or node.name.split("[")[0] == matchparts[0]
                        )
                    if is_match:
                        work.append((node, matchparts[1:]))
                        any_matched_in_collector = True

                if not any_matched_in_collector:
                    notfound_collectors.append(matchnode)

            if not any_matched_in_initial_part:
                report_arg = "::".join((str(argpath), *names))
                self._notfound.append((report_arg, notfound_collectors))

            self.trace.root.indent -= 1

    def genitems(self, node: nodes.Item | nodes.Collector) -> Iterator[nodes.Item]:
        self.trace("genitems", node)
        if isinstance(node, nodes.Item):
            node.ihook.pytest_itemcollected(item=node)
            yield node
        else:
            assert isinstance(node, nodes.Collector)
            keepduplicates = self.config.getoption("keepduplicates")
            # For backward compat, dedup only applies to files.
            handle_dupes = not (keepduplicates and isinstance(node, nodes.File))
            rep, duplicate = self._collect_one_node(node, handle_dupes)
            if duplicate and not keepduplicates:
                return
            if rep.passed:
                for subnode in rep.result:
                    yield from self.genitems(subnode)
            if not duplicate:
                node.ihook.pytest_collectreport(report=rep)


def search_pypath(module_name: str) -> str | None:
    """Search sys.path for the given a dotted module name, and return its file
    system path if found."""
    try:
        spec = importlib.util.find_spec(module_name)
    # AttributeError: looks like package module, but actually filename
    # ImportError: module does not exist
    # ValueError: not a module name
    except (AttributeError, ImportError, ValueError):
        return None
    if spec is None or spec.origin is None or spec.origin == "namespace":
        return None
    elif spec.submodule_search_locations:
        return os.path.dirname(spec.origin)
    else:
        return spec.origin


@dataclasses.dataclass(frozen=True)
class CollectionArgument:
    """A resolved collection argument."""

    path: Path
    parts: Sequence[str]
    module_name: str | None


def resolve_collection_argument(
    invocation_path: Path, arg: str, *, as_pypath: bool = False
) -> CollectionArgument:
    """Parse path arguments optionally containing selection parts and return (fspath, names).

    Command-line arguments can point to files and/or directories, and optionally contain
    parts for specific tests selection, for example:

        "pkg/tests/test_foo.py::TestClass::test_foo"

    This function ensures the path exists, and returns a resolved `CollectionArgument`:

        CollectionArgument(
            path=Path("/full/path/to/pkg/tests/test_foo.py"),
            parts=["TestClass", "test_foo"],
            module_name=None,
        )

    When as_pypath is True, expects that the command-line argument actually contains
    module paths instead of file-system paths:

        "pkg.tests.test_foo::TestClass::test_foo"

    In which case we search sys.path for a matching module, and then return the *path* to the
    found module, which may look like this:

        CollectionArgument(
            path=Path("/home/u/myvenv/lib/site-packages/pkg/tests/test_foo.py"),
            parts=["TestClass", "test_foo"],
            module_name="pkg.tests.test_foo",
        )

    If the path doesn't exist, raise UsageError.
    If the path is a directory and selection parts are present, raise UsageError.
    """
    base, squacket, rest = str(arg).partition("[")
    strpath, *parts = base.split("::")
    if parts:
        parts[-1] = f"{parts[-1]}{squacket}{rest}"
    module_name = None
    if as_pypath:
        pyarg_strpath = search_pypath(strpath)
        if pyarg_strpath is not None:
            module_name = strpath
            strpath = pyarg_strpath
    fspath = invocation_path / strpath
    fspath = absolutepath(fspath)
    if not safe_exists(fspath):
        msg = (
            "module or package not found: {arg} (missing __init__.py?)"
            if as_pypath
            else "file or directory not found: {arg}"
        )
        raise UsageError(msg.format(arg=arg))
    if parts and fspath.is_dir():
        msg = (
            "package argument cannot contain :: selection parts: {arg}"
            if as_pypath
            else "directory argument cannot contain :: selection parts: {arg}"
        )
        raise UsageError(msg.format(arg=arg))
    return CollectionArgument(
        path=fspath,
        parts=parts,
        module_name=module_name,
    )
