# mypy: allow-untyped-defs
"""Implementation of the cache provider."""

# This plugin was not named "cache" to avoid conflicts with the external
# pytest-cache version.
from __future__ import annotations

from collections.abc import Generator
from collections.abc import Iterable
from collections.abc import Mapping
import dataclasses
import enum
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from typing import Any
from typing import final
from typing import Literal

from .pathlib import check_user_cache_root
from .pathlib import resolve_from_str
from .pathlib import rm_rf
from .pathlib import user_cache_root
from .reports import CollectReport
from _pytest import __version__
from _pytest import nodes
from _pytest._io import TerminalWriter
from _pytest.compat import assert_never
from _pytest.config import Config
from _pytest.config import ExitCode
from _pytest.config import hookimpl
from _pytest.config.argparsing import Parser
from _pytest.deprecated import check_ispytest
from _pytest.deprecated import TOX_ENV_DIR_CACHE_DIR
from _pytest.fixtures import fixture
from _pytest.fixtures import FixtureRequest
from _pytest.main import Session
from _pytest.nodes import Directory
from _pytest.nodes import File
from _pytest.reports import TestReport


CACHEDIR_FILES: dict[str, bytes] = {
    "README.md": b"""\
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.
""",
    ".gitignore": b"# Created by pytest automatically.\n*\n",
    "CACHEDIR.TAG": b"""\
Signature: 8a477f597d28d172789f06886806bc55
# This file is a cache directory tag created by pytest.
# For information about cache directory tags, see:
#	https://bford.info/cachedir/spec.html
""",
}


def _make_cachedir(
    target: Path, extra_files: Mapping[str, bytes] | None = None
) -> None:
    """Create the pytest cache directory atomically with supporting files.

    Creates a temporary directory with README.md, .gitignore, and CACHEDIR.TAG,
    plus any ``extra_files``, then atomically renames it to the target
    location. If another process wins the race, the temporary directory is
    cleaned up.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="pytest-cache-files-", dir=target.parent))
    try:
        # Reset permissions to the default, see #12308.
        # Note: there's no way to get the current umask atomically, eek.
        umask = os.umask(0o022)
        os.umask(umask)
        path.chmod(0o777 - umask)

        for name, content in {**CACHEDIR_FILES, **(extra_files or {})}.items():
            path.joinpath(name).write_bytes(content)

        path.rename(target)
    except OSError as e:
        # If 2 concurrent pytests both race to the rename, the loser
        # gets "Directory not empty" from the rename. In this case,
        # everything is handled so just continue after cleanup.
        # On Windows, the error is a FileExistsError which translates to EEXIST.
        if e.errno not in (errno.ENOTEMPTY, errno.EEXIST):
            raise
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _project_key_path(rootpath: Path) -> str:
    """Normalised rootdir, as used to identify a project.

    Symlinks are resolved even though ``Config.rootpath`` itself is not:
    reaching one project through two paths must not give it two caches, which
    is the duplication the ``user`` policy exists to avoid. Cache *content* is
    unaffected either way, since node ids are stored relative to the rootdir.

    normcase matters on Windows, where two spellings differing only in case
    are one directory, and the casing varies with how the shell was launched.
    """
    return os.path.normcase(_realpath_or_self(str(rootpath)))


def _project_digest(rootpath: Path) -> str:
    """Digest identifying a project for the ``user`` cache policy."""
    key = _project_key_path(rootpath)
    return hashlib.sha256(key.encode("utf-8", "surrogatepass")).hexdigest()


def _user_cache_dir(config: Config) -> Path:
    root = user_cache_root()
    check_user_cache_root(root)

    digest = _project_digest(config.rootpath)
    # From the same normalised path as the digest, so that reaching a project
    # through a symlink gives the same directory name and not just the same
    # digest.
    label = _label(os.path.basename(_project_key_path(config.rootpath)))
    candidate = root / f"{label}-{digest[:16]}"

    existing = read_cache_info(candidate)
    if existing is None or existing.get("digest") in (None, digest):
        return candidate
    # A genuine 64-bit collision, or a hand-made directory. Deterministic and
    # stateless: no counters, no lock files.
    return root / f"{label}-{digest[:32]}"


def _tox_legacy_cache_dir(config: Config) -> Path | None:
    """The legacy ``$TOX_ENV_DIR/.pytest_cache`` location, if it applies.

    Only consulted by the ``local`` policy, so that setting ``cache_policy``
    explicitly is not silently overridden when running under tox.

    .. deprecated:: 9.2
        Superseded by :attr:`CacheScope.ENV`, which keeps ``--lf``/``--nf``/
        ``--sw`` state apart between environments without moving the cache
        directory - and does so for every tool rather than only for tox.
        Anyone who wants this exact location can spell it out as
        ``cache_dir = $TOX_ENV_DIR/.pytest_cache``.
    """
    tox_env_dir = os.environ.get("TOX_ENV_DIR")
    if not tox_env_dir:
        return None
    # Warnings raised during pytest_configure escape the reporter, so this has
    # to go through the config rather than warnings.warn.
    config.issue_config_time_warning(TOX_ENV_DIR_CACHE_DIR, stacklevel=3)
    return resolve_from_str(os.path.join(tox_env_dir, ".pytest_cache"), config.rootpath)


def _cache_policy(config: Config) -> str:
    """The effective cache policy, or ``explicit`` if ``cache_dir`` is set."""
    if config.getini("cache_dir"):
        return "explicit"
    policy: str = config.getini("cache_policy")
    return policy


def _resolve_cache_dir(config: Config) -> Path:
    """Determine the cache directory for a Config.

    The single place where the cache directory location is decided.

    ``cache_dir`` is an explicit path override and always wins; ``cache_policy``
    only decides the location when ``cache_dir`` is unset.
    """
    cache_dir = config.getini("cache_dir")
    if cache_dir:
        # resolve_from_str applies expanduser/expandvars.
        return resolve_from_str(cache_dir, config.rootpath)

    policy: str = config.getini("cache_policy")
    if policy == "local":
        legacy = _tox_legacy_cache_dir(config)
        if legacy is not None:
            return legacy
        return config.rootpath / ".pytest_cache"
    assert policy == "user", policy
    return _user_cache_dir(config)


class CacheScope(enum.Enum):
    """How far a cached value travels.

    Cached data is not always valid everywhere the project is: last-failed test
    ids, for instance, depend on what the interpreter in use actually collects.
    Rather than giving each environment a whole cache directory of its own,
    scoped values live in separate sub-directories of the one cache directory
    belonging to the project.

    .. versionadded:: 9.0
    """

    #: Valid for the project regardless of interpreter or environment.
    SHARED = "shared"
    #: Valid only for the running Python implementation and ``major.minor``
    #: version. The patch version is deliberately not part of this, so that an
    #: in-place upgrade does not invalidate the cache.
    PYTHON = "python"
    #: Valid only for the running environment, i.e. :data:`sys.prefix`.
    ENV = "env"


def _realpath_or_self(path: str) -> str:
    try:
        return os.path.realpath(path)
    except OSError:
        # E.g. a dead NFS mount. A stable-but-unresolved key beats crashing.
        return path


_LABEL_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _label(name: str, *, maxlen: int = 32) -> str:
    """Make ``name`` safe and readable as a single path component.

    A whitelist rather than a blacklist, so spaces, separators, colons and
    non-ASCII all collapse to ``-``. Leading dots are stripped so the result is
    not hidden. Callers always combine this with a digest, so losing
    information here is fine - and it also means Windows reserved device names
    (``CON``, ``NUL``, ...) are harmless, since the label is never the whole
    basename.
    """
    return _LABEL_UNSAFE.sub("-", name)[:maxlen].strip("-.") or "root"


def _scope_id(scope: CacheScope) -> str | None:
    """Return the sub-directory name for ``scope``, or None if unscoped."""
    if scope is CacheScope.SHARED:
        return None
    if scope is CacheScope.PYTHON:
        major, minor = sys.version_info[:2]
        return f"py-{_label(sys.implementation.name)}-{major}.{minor}"
    if scope is CacheScope.ENV:
        # normcase because on Windows `C:\Foo` and `c:\foo` are one directory
        # and the casing varies with how the shell was launched.
        prefix = os.path.normcase(_realpath_or_self(sys.prefix))
        digest = hashlib.sha256(prefix.encode("utf-8", "surrogatepass")).hexdigest()
        return f"env-{_label(os.path.basename(prefix), maxlen=16)}-{digest[:8]}"
    assert_never(scope)


def _scope_info(scope: CacheScope) -> dict[str, str]:
    """Describe ``scope`` for the cache metadata."""
    major, minor = sys.version_info[:2]
    info = {
        "scope": scope.value,
        "python": f"{sys.implementation.name}-{major}.{minor}",
    }
    if scope is CacheScope.ENV:
        # Recorded unresolved, i.e. as the user sees it, since this is what
        # gets shown when listing caches.
        info["prefix"] = sys.prefix
    return info


#: Name of the metadata file written at the top level of a cache directory.
#: Not dot-prefixed: someone browsing a cache directory far from the project it
#: belongs to needs to be able to see what it is for.
CACHE_INFO_NAME = "cache-info.json"

#: Version of the `cache-info.json` format. Readers must tolerate a missing,
#: unparsable or newer file, and still offer to remove the directory.
CACHE_INFO_SCHEMA = 1


def _now() -> float:
    """Indirection so that tests can freeze time."""
    return time.time()


def _write_json_atomic(path: Path, data: object) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    # A temp file in the same directory guarantees os.replace is atomic, as it
    # is then guaranteed to be on the same filesystem.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="UTF-8") as f:
            f.write(payload)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_cache_info(cachedir: Path) -> dict[str, Any] | None:
    """Read a cache directory's metadata, or None if it has none readable."""
    try:
        with (cachedir / CACHE_INFO_NAME).open("r", encoding="UTF-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


@final
@dataclasses.dataclass
class Cache:
    """Instance of the `cache` fixture."""

    _cachedir: Path = dataclasses.field(repr=False)
    _config: Config = dataclasses.field(repr=False)

    # Sub-directory under cache-dir for directories created by `mkdir()`.
    _CACHE_PREFIX_DIRS = "d"

    # Sub-directory under cache-dir for values created by `set()`.
    _CACHE_PREFIX_VALUES = "v"

    # Sub-directory under cache-dir holding one directory per non-shared
    # CacheScope, each with its own `d` and `v` sub-directories.
    _CACHE_PREFIX_SCOPES = "s"

    def __init__(
        self, cachedir: Path, config: Config, *, _ispytest: bool = False
    ) -> None:
        check_ispytest(_ispytest)
        self._cachedir = cachedir
        self._config = config
        # Scopes touched this session, and the set already recorded in the
        # metadata file, so a scope used later still gets recorded.
        self._used_scopes: dict[str, dict[str, str]] = {}
        self._recorded_scopes: frozenset[str] | None = None

    @classmethod
    def for_config(cls, config: Config, *, _ispytest: bool = False) -> Cache:
        """Create the Cache instance for a Config.

        :meta private:
        """
        check_ispytest(_ispytest)
        cachedir = _resolve_cache_dir(config)
        if config.getoption("cacheclear") and cachedir.is_dir():
            cls.clear_cache(cachedir, _ispytest=True)
        return cls(cachedir, config, _ispytest=True)

    @classmethod
    def clear_cache(cls, cachedir: Path, _ispytest: bool = False) -> None:
        """Clear the sub-directories used to hold cached directories and values.

        :meta private:
        """
        check_ispytest(_ispytest)
        for prefix in (
            cls._CACHE_PREFIX_DIRS,
            cls._CACHE_PREFIX_VALUES,
            cls._CACHE_PREFIX_SCOPES,
        ):
            d = cachedir / prefix
            if d.is_dir():
                rm_rf(d)

    @staticmethod
    def cache_dir_from_config(config: Config, *, _ispytest: bool = False) -> Path:
        """Get the path to the cache directory for a Config.

        :meta private:
        """
        check_ispytest(_ispytest)
        return _resolve_cache_dir(config)

    def warn(self, fmt: str, *, _ispytest: bool = False, **args: object) -> None:
        """Issue a cache warning.

        :meta private:
        """
        check_ispytest(_ispytest)
        import warnings

        from _pytest.warning_types import PytestCacheWarning

        warnings.warn(
            PytestCacheWarning(fmt.format(**args) if args else fmt),
            self._config.hook,
            stacklevel=3,
        )

    def _mkdir(self, path: Path) -> None:
        self._ensure_cache_dir_and_supporting_files()
        path.mkdir(exist_ok=True, parents=True)

    def _scope_root(self, scope: CacheScope) -> Path:
        scope_id = _scope_id(scope)
        if scope_id is None:
            return self._cachedir
        self._used_scopes[scope_id] = _scope_info(scope)
        return self._cachedir.joinpath(self._CACHE_PREFIX_SCOPES, scope_id)

    def mkdir(self, name: str, *, scope: CacheScope = CacheScope.SHARED) -> Path:
        """Return a directory path object with the given name.

        If the directory does not yet exist, it will be created. You can use
        it to manage files to e.g. store/retrieve database dumps across test
        sessions.

        .. versionadded:: 7.0

        :param name:
            Must be a string not containing a ``/`` separator.
            Make sure the name contains your plugin or application
            identifiers to prevent clashes with other cache users.
        :param scope:
            How far the directory's contents travel; see :class:`CacheScope`.
            Defaults to :attr:`CacheScope.SHARED`.

            .. versionadded:: 9.0
        """
        path = Path(name)
        if len(path.parts) > 1:
            raise ValueError("name is not allowed to contain path separators")
        res = self._scope_root(scope).joinpath(self._CACHE_PREFIX_DIRS, path)
        self._mkdir(res)
        return res

    def _getvaluepath(self, key: str, scope: CacheScope = CacheScope.SHARED) -> Path:
        return self._scope_root(scope).joinpath(self._CACHE_PREFIX_VALUES, Path(key))

    def get(self, key: str, default, *, scope: CacheScope = CacheScope.SHARED):
        """Return the cached value for the given key.

        If no value was yet cached or the value cannot be read, the specified
        default is returned.

        :param key:
            Must be a ``/`` separated value. Usually the first
            name is the name of your plugin or your application.
        :param default:
            The value to return in case of a cache-miss or invalid cache value.
        :param scope:
            Which scope to read the value from; see :class:`CacheScope`. Must
            match the scope it was written with. Defaults to
            :attr:`CacheScope.SHARED`.

            .. versionadded:: 9.0
        """
        path = self._getvaluepath(key, scope)
        try:
            with path.open("r", encoding="UTF-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            return default

    def set(
        self, key: str, value: object, *, scope: CacheScope = CacheScope.SHARED
    ) -> None:
        """Save value for the given key.

        :param key:
            Must be a ``/`` separated value. Usually the first
            name is the name of your plugin or your application.
        :param value:
            Must be of any combination of basic python types,
            including nested types like lists of dictionaries.
        :param scope:
            How far the value travels; see :class:`CacheScope`. Pin values
            which are not valid across interpreters or environments, such as
            collected test ids. Defaults to :attr:`CacheScope.SHARED`.

            .. versionadded:: 9.0
        """
        path = self._getvaluepath(key, scope)
        try:
            self._mkdir(path.parent)
        except OSError as exc:
            self.warn(
                f"could not create cache path {path}: {exc}",
                _ispytest=True,
            )
            return
        data = json.dumps(value, ensure_ascii=False, indent=2)
        try:
            f = path.open("w", encoding="UTF-8")
        except OSError as exc:
            self.warn(
                f"cache could not write path {path}: {exc}",
                _ispytest=True,
            )
        else:
            with f:
                f.write(data)

    def _cache_info(self, previous: dict[str, Any] | None) -> dict[str, Any]:
        """Build the metadata to record, merged over ``previous`` if any.

        Unknown keys in ``previous`` are preserved, so that a newer pytest's
        fields survive an older pytest touching the same directory.
        """
        now = _now()
        info: dict[str, Any] = dict(previous) if previous else {}
        info["schema"] = CACHE_INFO_SCHEMA
        policy = _cache_policy(self._config)
        info["policy"] = policy
        if policy == "user":
            # Recorded in full, so that a directory name collision can be
            # detected rather than silently sharing a cache.
            info["digest"] = _project_digest(self._config.rootpath)
        info["origin"] = {
            "rootdir": str(self._config.rootpath),
            "inipath": str(self._config.inipath) if self._config.inipath else None,
        }
        info["pytest_version"] = __version__
        info.setdefault("created_at", now)
        info["last_used_at"] = now

        recorded = info.get("scopes")
        scopes: dict[str, Any] = dict(recorded) if isinstance(recorded, dict) else {}
        for scope_id, scope_info in self._used_scopes.items():
            scopes[scope_id] = {**scope_info, "last_used_at": now}
        info["scopes"] = scopes
        return info

    def _ensure_cache_dir_and_supporting_files(self) -> None:
        """Create the cache dir, its supporting files and its metadata."""
        used_scopes = frozenset(self._used_scopes)
        if not self._cachedir.is_dir():
            info = json.dumps(self._cache_info(None), ensure_ascii=False, indent=2)
            _make_cachedir(self._cachedir, {CACHE_INFO_NAME: info.encode("UTF-8")})
        elif self._recorded_scopes != used_scopes:
            # Either the metadata has not been refreshed this session yet, or a
            # scope has been used since it last was. Note this also backfills
            # the file into cache directories created by an older pytest.
            try:
                _write_json_atomic(
                    self._cachedir / CACHE_INFO_NAME,
                    self._cache_info(read_cache_info(self._cachedir)),
                )
            except OSError:
                # Deliberately silent, unlike `set()`. The metadata only feeds
                # listing and pruning, so failing to write it costs the user
                # nothing they asked for - and whatever made it fail will have
                # made the actual cache writes warn already. Such a directory
                # simply lists as having no metadata.
                pass
        self._recorded_scopes = used_scopes


class LFPluginCollWrapper:
    def __init__(self, lfplugin: LFPlugin) -> None:
        self.lfplugin = lfplugin
        self._collected_at_least_one_failure = False

    @hookimpl(wrapper=True)
    def pytest_make_collect_report(
        self, collector: nodes.Collector
    ) -> Generator[None, CollectReport, CollectReport]:
        res = yield
        if isinstance(collector, Session | Directory):
            # Sort any lf-paths to the beginning.
            lf_paths = self.lfplugin._last_failed_paths

            # Use stable sort to prioritize last failed.
            def sort_key(node: nodes.Item | nodes.Collector) -> bool:
                return node.path in lf_paths

            res.result = sorted(
                res.result,
                key=sort_key,
                reverse=True,
            )

        elif isinstance(collector, File):
            if collector.path in self.lfplugin._last_failed_paths:
                result = res.result
                lastfailed = self.lfplugin.lastfailed

                # Only filter with known failures.
                if not self._collected_at_least_one_failure:
                    if not any(x.nodeid in lastfailed for x in result):
                        return res
                    self.lfplugin.config.pluginmanager.register(
                        LFPluginCollSkipfiles(self.lfplugin), "lfplugin-collskip"
                    )
                    self._collected_at_least_one_failure = True

                session = collector.session
                result[:] = [
                    x
                    for x in result
                    if x.nodeid in lastfailed
                    # Include any passed arguments (not trivial to filter).
                    or session.isinitpath(x.path)
                    # Keep all sub-collectors.
                    or isinstance(x, nodes.Collector)
                ]

        return res


class LFPluginCollSkipfiles:
    def __init__(self, lfplugin: LFPlugin) -> None:
        self.lfplugin = lfplugin

    @hookimpl
    def pytest_make_collect_report(
        self, collector: nodes.Collector
    ) -> CollectReport | None:
        if isinstance(collector, File):
            if collector.path not in self.lfplugin._last_failed_paths:
                self.lfplugin._skipped_files += 1

                return CollectReport(
                    collector.nodeid, "passed", longrepr=None, result=[]
                )
        return None


class LFPlugin:
    """Plugin which implements the --lf (run last-failing) option."""

    def __init__(self, config: Config) -> None:
        self.config = config
        active_keys = "lf", "failedfirst"
        self.active = any(config.getoption(key) for key in active_keys)
        assert config.cache
        self.lastfailed: dict[str, bool] = config.cache.get(
            "cache/lastfailed", {}, scope=CacheScope.ENV
        )
        self._previously_failed_count: int | None = None
        self._report_status: str | None = None
        self._skipped_files = 0  # count skipped files during collection due to --lf

        if config.getoption("lf"):
            self._last_failed_paths = self.get_last_failed_paths()
            config.pluginmanager.register(
                LFPluginCollWrapper(self), "lfplugin-collwrapper"
            )

    def get_last_failed_paths(self) -> set[Path]:
        """Return a set with all Paths of the previously failed nodeids and
        their parents."""
        rootpath = self.config.rootpath
        result = set()
        for nodeid in self.lastfailed:
            path = rootpath / nodeid.split("::")[0]
            result.add(path)
            result.update(path.parents)
        return {x for x in result if x.exists()}

    def pytest_report_collectionfinish(self) -> str | None:
        if self.active and self.config.get_verbosity() >= 0:
            return f"run-last-failure: {self._report_status}"
        return None

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        if (report.when == "call" and report.passed) or report.skipped:
            self.lastfailed.pop(report.nodeid, None)
        elif report.failed:
            self.lastfailed[report.nodeid] = True

    def pytest_collectreport(self, report: CollectReport) -> None:
        passed = report.outcome in ("passed", "skipped")
        if passed:
            if report.nodeid in self.lastfailed:
                self.lastfailed.pop(report.nodeid)
                self.lastfailed.update((item.nodeid, True) for item in report.result)
        else:
            self.lastfailed[report.nodeid] = True

    @hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection_modifyitems(
        self, config: Config, items: list[nodes.Item]
    ) -> Generator[None]:
        res = yield

        if not self.active:
            return res

        if self.lastfailed:
            previously_failed = []
            previously_passed = []
            for item in items:
                if item.nodeid in self.lastfailed:
                    previously_failed.append(item)
                else:
                    previously_passed.append(item)
            self._previously_failed_count = len(previously_failed)

            if not previously_failed:
                # Running a subset of all tests with recorded failures
                # only outside of it.
                self._report_status = (
                    f"{len(self.lastfailed)} known failures not in selected tests"
                )
            else:
                if self.config.getoption("lf"):
                    items[:] = previously_failed
                    config.hook.pytest_deselected(items=previously_passed)
                else:  # --failedfirst
                    items[:] = previously_failed + previously_passed

                noun = "failure" if self._previously_failed_count == 1 else "failures"
                suffix = " first" if self.config.getoption("failedfirst") else ""
                self._report_status = (
                    f"rerun previous {self._previously_failed_count} {noun}{suffix}"
                )

            if self._skipped_files > 0:
                files_noun = "file" if self._skipped_files == 1 else "files"
                self._report_status += f" (skipped {self._skipped_files} {files_noun})"
        else:
            self._report_status = "no previously failed tests, "
            if self.config.getoption("last_failed_no_failures") == "none":
                self._report_status += "deselecting all items."
                config.hook.pytest_deselected(items=items[:])
                items[:] = []
            else:
                self._report_status += "not deselecting items."

        return res

    def pytest_sessionfinish(self, session: Session) -> None:
        config = self.config
        if config.getoption("cacheshow") or hasattr(config, "workerinput"):
            return

        assert config.cache is not None
        saved_lastfailed = config.cache.get(
            "cache/lastfailed", {}, scope=CacheScope.ENV
        )
        if saved_lastfailed != self.lastfailed:
            config.cache.set("cache/lastfailed", self.lastfailed, scope=CacheScope.ENV)


class NFPlugin:
    """Plugin which implements the --nf (run new-first) option."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.active = config.option.newfirst
        assert config.cache is not None
        self.cached_nodeids = set(
            config.cache.get("cache/nodeids", [], scope=CacheScope.ENV)
        )

    @hookimpl(wrapper=True, tryfirst=True)
    def pytest_collection_modifyitems(self, items: list[nodes.Item]) -> Generator[None]:
        res = yield

        if self.active:
            new_items: dict[str, nodes.Item] = {}
            other_items: dict[str, nodes.Item] = {}
            for item in items:
                if item.nodeid not in self.cached_nodeids:
                    new_items[item.nodeid] = item
                else:
                    other_items[item.nodeid] = item

            items[:] = self._get_increasing_order(
                new_items.values()
            ) + self._get_increasing_order(other_items.values())
            self.cached_nodeids.update(new_items)
        else:
            self.cached_nodeids.update(item.nodeid for item in items)

        return res

    def _get_increasing_order(self, items: Iterable[nodes.Item]) -> list[nodes.Item]:
        return sorted(items, key=lambda item: item.path.stat().st_mtime, reverse=True)

    def pytest_sessionfinish(self) -> None:
        config = self.config
        if config.getoption("cacheshow") or hasattr(config, "workerinput"):
            return

        if config.getoption("collectonly"):
            return

        assert config.cache is not None
        config.cache.set(
            "cache/nodeids", sorted(self.cached_nodeids), scope=CacheScope.ENV
        )


def pytest_addoption(parser: Parser) -> None:
    """Add command-line options for cache functionality.

    :param parser: Parser object to add command-line options to.
    """
    group = parser.getgroup("general")
    group.addoption(
        "--lf",
        "--last-failed",
        action="store_true",
        dest="lf",
        help="Rerun only the tests that failed at the last run (or all if none failed)",
    )
    group.addoption(
        "--ff",
        "--failed-first",
        action="store_true",
        dest="failedfirst",
        help="Run all tests, but run the last failures first. "
        "This may re-order tests and thus lead to "
        "repeated fixture setup/teardown.",
    )
    group.addoption(
        "--nf",
        "--new-first",
        action="store_true",
        dest="newfirst",
        help="Run tests from new files first, then the rest of the tests "
        "sorted by file mtime",
    )
    group.addoption(
        "--cache-show",
        action="append",
        nargs="?",
        dest="cacheshow",
        help=(
            "Show cache contents, don't perform collection or tests. "
            "Optional argument: glob (default: '*')."
        ),
    )
    group.addoption(
        "--cache-clear",
        action="store_true",
        dest="cacheclear",
        help="Remove all cache contents at start of test run",
    )
    group.addoption(
        "--cache-list",
        action="store_true",
        dest="cachelist",
        help=(
            "List the cache directories under the user-level cache root, "
            "don't perform collection or tests."
        ),
    )
    # Empty by default so that "not configured" is detectable, in which case
    # cache_policy decides the location.
    parser.addini(
        "cache_dir",
        default="",
        help="Cache directory path; overrides cache_policy",
    )
    parser.addini(
        "cache_policy",
        type=Literal["local", "user"],
        default=os.environ.get("PYTEST_CACHE_POLICY") or "local",
        help=(
            "Where the cache directory lives: 'local' (rootdir/.pytest_cache) "
            "or 'user' (the platform's user cache directory, keyed by "
            "project). Ignored if cache_dir is set."
        ),
    )
    group.addoption(
        "--lfnf",
        "--last-failed-no-failures",
        action="store",
        dest="last_failed_no_failures",
        choices=("all", "none"),
        default="all",
        help="With ``--lf``, determines whether to execute tests when there "
        "are no previously (known) failures or when no "
        "cached ``lastfailed`` data was found. "
        "``all`` (the default) runs the full test suite again. "
        "``none`` just emits a message about no known failures and exits successfully.",
    )


def pytest_cmdline_main(config: Config) -> int | ExitCode | None:
    if config.option.cacheshow and not config.option.help:
        from _pytest.main import wrap_session

        return wrap_session(config, cacheshow)
    return None


@hookimpl(tryfirst=True)
def pytest_configure(config: Config) -> None:
    """Configure cache system and register related plugins.

    Creates the Cache instance and registers the last-failed (LFPlugin)
    and new-first (NFPlugin) plugins with the plugin manager.

    :param config: pytest configuration object.
    """
    config.cache = Cache.for_config(config, _ispytest=True)
    config.pluginmanager.register(LFPlugin(config), "lfplugin")
    config.pluginmanager.register(NFPlugin(config), "nfplugin")


@fixture
def cache(request: FixtureRequest) -> Cache:
    """Return a cache object that can persist state between testing sessions.

    cache.get(key, default)
    cache.set(key, value)

    Keys must be ``/`` separated strings, where the first part is usually the
    name of your plugin or application to avoid clashes with other cache users.

    Values can be any object handled by the json stdlib module.
    """
    assert request.config.cache is not None
    return request.config.cache


def pytest_report_header(config: Config) -> str | None:
    """Display cachedir with --cache-show and if non-default."""
    assert config.cache is not None
    cachedir = config.cache._cachedir
    # Compare the resolved path rather than the configured value, so that
    # setting cache_dir to the default explicitly is treated as the default.
    if config.option.verbose <= 0 and cachedir == config.rootpath / ".pytest_cache":
        return None

    # TODO: evaluate generating upward relative paths
    # starting with .., ../.. if sensible
    try:
        displaypath: Path | str = cachedir.relative_to(config.rootpath)
    except ValueError:
        # Not below the rootdir (#3745); show the absolute path.
        displaypath = cachedir

    # A plain string is returned to the hook caller, so the escapes have to be
    # applied here rather than via write_link(). The line is flushed with a
    # newline immediately, which resets the writer's width bookkeeping, so the
    # transient over-count does not affect anything downstream.
    if config.pluginmanager.get_plugin("terminalreporter") is not None:
        tw = config.get_terminal_writer()
        displaypath = tw.hyperlink(str(displaypath), cachedir.as_uri())
    return f"cachedir: {displaypath}"


def _cache_roots(basedir: Path) -> list[tuple[str | None, Path]]:
    """Yield ``(scope_id, root)`` for the shared scope and every scope present.

    ``scope_id`` is None for the shared scope. Scopes are read off the
    filesystem rather than from :class:`CacheScope`, so that scopes belonging
    to other environments are included.
    """
    roots: list[tuple[str | None, Path]] = [(None, basedir)]
    scopesdir = basedir / Cache._CACHE_PREFIX_SCOPES
    if scopesdir.is_dir():
        roots.extend((p.name, p) for p in sorted(scopesdir.iterdir()) if p.is_dir())
    return roots


def cacheshow(config: Config, session: Session) -> int:
    """Display cache contents when --cache-show is used.

    Shows cached values and directories matching the specified glob pattern
    (default: '*'). Displays cache location, cached test results, and
    any cached directories created by plugins.

    :param config: pytest configuration object.
    :param session: pytest session object.
    :returns: Exit code (0 for success).
    """
    from pprint import pformat

    assert config.cache is not None

    tw = TerminalWriter()
    tw.line("cachedir: " + str(config.cache._cachedir))
    if not config.cache._cachedir.is_dir():
        tw.line("cache is empty")
        return 0

    glob = config.option.cacheshow[0]
    if glob is None:
        glob = "*"

    dummy = object()
    basedir = config.cache._cachedir
    tw.sep("-", f"cache values for {glob!r}")
    for scope_id, root in _cache_roots(basedir):
        vdir = root / Cache._CACHE_PREFIX_VALUES
        if not vdir.is_dir():
            continue
        for valpath in sorted(x for x in vdir.rglob(glob) if x.is_file()):
            key = str(valpath.relative_to(vdir))
            if scope_id is not None:
                key = f"{key} ({scope_id})"
            # Read through the path rather than Cache.get, so that scopes
            # belonging to other environments are shown too.
            try:
                with valpath.open("r", encoding="UTF-8") as f:
                    val = json.load(f)
            except (ValueError, OSError):
                val = dummy
            if val is dummy:
                tw.line(f"{key} contains unreadable content, will be ignored")
            else:
                tw.line(f"{key} contains:")
                for line in pformat(val).splitlines():
                    tw.line("  " + line)

    ddirs = [root / Cache._CACHE_PREFIX_DIRS for _, root in _cache_roots(basedir)]
    if any(ddir.is_dir() for ddir in ddirs):
        tw.sep("-", f"cache directories for {glob!r}")
        for ddir in ddirs:
            if not ddir.is_dir():
                continue
            for p in sorted(ddir.rglob(glob)):
                if p.is_file():
                    key = str(p.relative_to(basedir))
                    tw.line(f"{key} is a file of length {p.stat().st_size}")
    return 0
