"""The registry of declared configuration settings.

Every setting a plugin declares -- with :meth:`Parser.addini
<pytest.Parser.addini>`, :meth:`Parser.addconfig <pytest.Parser.addconfig>` or
:meth:`Parser.addoption <pytest.Parser.addoption>` -- is recorded here as a
single :class:`Setting`, together with the sources allowed to set it. The
registry holds the *declarations*; the values resolved from them live on
``Config``.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
import dataclasses
import enum
import sys
import types
from typing import Any
from typing import ClassVar
from typing import final
from typing import Literal
from typing import TYPE_CHECKING
import warnings

from _pytest.config.findpaths import ConfigDict
from _pytest.config.findpaths import ConfigValue


if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Argument
    from _pytest.config.argparsing import IniType


@final
class Source(enum.Enum):
    """Where the value of a setting came from, or may come from."""

    #: The value registered as the setting's default.
    DEFAULT = "default"
    #: Another setting, named by ``Setting.fallback``.
    FALLBACK = "fallback"
    #: A configuration file.
    FILE = "file"
    #: An ``-o``/``--override-ini`` argument.
    OVERRIDE = "override"
    #: A command line option declared for this setting by ``addconfig``.
    CLI = "cli"
    #: A plain ``addoption`` command line option, parsed by argparse.
    ARGPARSE = "argparse"


@final
@dataclasses.dataclass
class Setting:
    """The declaration of a single configuration setting.

    Mutable, because one setting can accumulate several command line options:
    ``verbose`` is fed by ``-v``, ``-q`` and ``--verbosity``, and each
    registration adds to `cli` and to `settable_by`.
    """

    #: Canonical name, and the key this setting is stored under.
    name: str
    help: str | None
    #: The declared type, or ``None`` for an ``addoption``-only setting, whose
    #: value argparse produces and pytest does not coerce.
    type: IniType | None
    default: Any
    #: Settings to consult, in order, when this one is not configured.
    fallback: tuple[str, ...] = ()
    #: Additional configuration names resolving to this one.
    aliases: tuple[str, ...] = ()
    #: The sources allowed to set this setting.
    settable_by: frozenset[Source] = frozenset()
    #: The argparse ``dest`` of the command line options feeding this setting,
    #: which is `name` unless the two namespaces collided.
    dest: str | None = None
    #: Name of the option group, for ``--help``.
    group: str | None = None
    #: The command line options feeding this setting.
    cli: tuple[Argument, ...] = ()
    #: Where this setting was declared, as ``(filename, lineno)``. Kept for
    #: warnings, so that they point at the plugin rather than at pytest.
    declared_at: tuple[str, int] | None = None

    def conflicts_with(self, other: Setting) -> bool:
        """Whether re-registering `other` would change what this setting is.

        A plugin loaded twice, or `pytester` re-running a `conftest.py`,
        registers the same setting again; that is not a conflict.
        """
        return (
            self.type != other.type
            or self.default != other.default
            or self.fallback != other.fallback
            or self.aliases != other.aliases
        )

    @property
    def settable_from_file(self) -> bool:
        """Whether this setting can be written in a configuration file."""
        return Source.FILE in self.settable_by


@final
class SettingsRegistry:
    """The declared settings of one `Parser`.

    Keyed by canonical name. Command line options that do not correspond to a
    configuration setting are additionally reachable by their argparse
    ``dest``, which is the only handle they have.
    """

    def __init__(self) -> None:
        self._settings: dict[str, Setting] = {}
        #: Diagnostics found while declaring, to be issued once there is a
        #: configuration to issue them against. `pytest_addoption` is called
        #: historically, from `Config.__init__` and again for every plugin
        #: registered later, so warning where the problem is found would warn
        #: before the warning filters exist -- and, for a plugin, from inside
        #: the import-warning capture that swallows it.
        self._diagnostics: list[tuple[Setting, str]] = []
        #: Maps alias -> canonical name.
        self._aliases: dict[str, str] = {}
        #: Maps argparse dest -> setting, for every setting that has one.
        self._by_dest: dict[str, Setting] = {}

    def canonical(self, name: str) -> str:
        """Resolve an alias to the name it stands for."""
        return self._aliases.get(name, name)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.canonical(name) in self._settings

    def __getitem__(self, name: str) -> Setting:
        return self._settings[self.canonical(name)]

    def get(self, name: str) -> Setting | None:
        return self._settings.get(self.canonical(name))

    def __iter__(self) -> Iterator[str]:
        return iter(self._settings)

    def __len__(self) -> int:
        return len(self._settings)

    def by_dest(self, dest: str) -> Setting | None:
        return self._by_dest.get(dest)

    def add_config(
        self,
        name: str,
        help: str,
        type: IniType,
        default: Any,
        aliases: tuple[str, ...],
        fallback: tuple[str, ...],
    ) -> Setting:
        """Register a setting that a configuration file can set.

        Validation of `fallback` and of `aliases` happens in `Parser.addini`,
        which owns the error messages.
        """
        setting = Setting(
            name=name,
            help=help,
            type=type,
            default=default,
            fallback=fallback,
            aliases=aliases,
            settable_by=frozenset({Source.FILE, Source.OVERRIDE}),
            declared_at=_declaration_site(),
        )
        previous = self._settings.get(name)
        if (
            previous is not None
            # A command line option of the same name is a separate thing that
            # merely shares a name -- the pattern every plugin used before
            # `addconfig` existed -- not a conflicting re-declaration.
            and previous.settable_from_file
            and previous.conflicts_with(setting)
        ):
            where = (
                f" (already registered at {previous.declared_at[0]}:"
                f"{previous.declared_at[1]})"
                if previous.declared_at is not None
                else ""
            )
            self._diagnostics.append(
                (
                    setting,
                    f"Configuration option {name!r} is registered twice, with "
                    f"different definitions{where}; the later one wins. This "
                    "is usually a conflict between two plugins.",
                )
            )
        self._settings[name] = setting
        for alias in aliases:
            self._aliases[alias] = name
        return setting

    def add_option(
        self,
        argument: Argument,
        group: str | None,
        *,
        binds: str | None = None,
        setting_name: str | None = None,
    ) -> Setting:
        """Register, or extend, the setting a command line option feeds.

        :param binds:
            Name of the configuration setting this option sets, as passed by
            ``addconfig``. The option becomes another source for it rather
            than a setting of its own.
        :param setting_name:
            Name to register a command line only option under, when its
            ``dest`` is already taken by a configuration setting.

        A plain ``addoption`` option gets a setting of its own, named after
        its ``dest``. If that name is already a configuration setting -- as
        pytest's own ``markers`` linelist and ``--markers`` flag are, and as
        any plugin declaring an ini and an option separately is -- neither may
        take the other's name, so the option is registered under
        `setting_name`, or, without one, stays reachable only by its ``dest``.
        """
        dest = argument.dest
        existing = self._by_dest.get(dest)
        if existing is not None:
            # Another option string for a setting already registered, e.g.
            # `-q` after `-v`, or `--junit-xml` after `--junitxml`.
            existing.cli = (*existing.cli, argument)
            return existing

        if binds is not None:
            try:
                setting = self._settings[self.canonical(binds)]
            except KeyError:
                raise ValueError(
                    f"command line option {argument.names()[0]!r} sets the "
                    f"configuration option {binds!r}, which is not registered; "
                    "register it first"
                ) from None
            setting.settable_by |= {Source.CLI}
            setting.dest = dest
            setting.group = group
            setting.cli = (*setting.cli, argument)
            self._by_dest[dest] = setting
            return setting

        name = dest if setting_name is None else setting_name
        setting = Setting(
            name=name,
            help=None,
            type=None,
            default=argument.default,
            settable_by=frozenset({Source.ARGPARSE}),
            dest=dest,
            group=group,
            cli=(argument,),
        )
        self._by_dest[dest] = setting
        if name not in self._settings:
            self._settings[name] = setting
        return setting


@final
class _ConfigSettingsView(Mapping[str, Setting]):
    """The configuration-file settings of a registry, in declaration order.

    This is what ``Parser._inidict`` exposes: the settings a configuration
    file can set, without the command line only ones.
    """

    def __init__(self, registry: SettingsRegistry) -> None:
        self._registry = registry

    def __getitem__(self, name: str) -> Setting:
        setting = self._registry._settings[name]
        if not setting.settable_from_file:
            raise KeyError(name)
        return setting

    def __iter__(self) -> Iterator[str]:
        return (
            name
            for name, setting in self._registry._settings.items()
            if setting.settable_from_file
        )

    def __len__(self) -> int:
        return sum(
            1
            for setting in self._registry._settings.values()
            if setting.settable_from_file
        )


@final
@dataclasses.dataclass(frozen=True)
class CliEntry:
    """One setting value supplied on the command line.

    Kept in command line order, so that an ``-o`` argument and a command line
    option declared for the same setting compose the way the user wrote them.
    Also the channel a programmatic override uses, which is what the
    deprecated ``config.inicfg`` writes through.
    """

    #: The name as written; may be an alias, or not registered at all.
    name: str
    value: object
    source: Source
    #: The data model the value follows, as for `ConfigValue.mode`.
    mode: Literal["ini", "toml"] = "ini"
    #: The option string that supplied it, for error messages.
    option_string: str | None = None

    def as_config_value(self) -> ConfigValue:
        return ConfigValue(self.value, origin="override", mode=self.mode)


@final
class OptionsView(Mapping[str, Any]):
    """The command line options that are not configuration settings.

    Keyed by argparse ``dest``. These are the options declared with
    :meth:`Parser.addoption <pytest.Parser.addoption>` alone -- selecting what
    to run, entering a debugger, anything meaningless to write in a
    configuration file -- whose value argparse produces and pytest does not
    coerce. A setting is read from :class:`Settings` instead.
    """

    def __init__(self, registry: SettingsRegistry, config: Config) -> None:
        self._registry = registry
        self._config = config

    def _dests(self) -> Iterator[str]:
        return (
            dest
            for dest, setting in self._registry._by_dest.items()
            if Source.ARGPARSE in setting.settable_by
        )

    def __getitem__(self, dest: str) -> Any:
        setting = self._registry._by_dest.get(dest)
        if setting is None or Source.ARGPARSE not in setting.settable_by:
            raise KeyError(dest)
        try:
            return self._config.option.__dict__[dest]
        except KeyError:
            raise KeyError(dest) from None

    def __iter__(self) -> Iterator[str]:
        return self._dests()

    def __len__(self) -> int:
        return sum(1 for _ in self._dests())

    def spec(self, dest: str) -> Setting:
        """The declaration of one option."""
        setting = self._registry._by_dest.get(dest)
        if setting is None or Source.ARGPARSE not in setting.settable_by:
            raise KeyError(dest)
        return setting


@final
class Settings(Mapping[str, Any]):
    """The resolved values of the settings declared in a `SettingsRegistry`.

    The registry holds the declarations; this holds the layers a value can
    come from -- configuration files, and the ``-o`` overrides and command
    line options collected while parsing -- and resolves them, once, on first
    read.

    Iterating yields the canonical names of the settings a configuration file
    can set, in declaration order. Aliases are accepted by ``[]`` and ``in``
    but are not yielded, so that a listing does not name a setting twice.
    """

    def __init__(self, registry: SettingsRegistry, config: Config) -> None:
        self._registry = registry
        self._config = config
        #: Values read from configuration files.
        self._file: ConfigDict = {}
        #: Values supplied on the command line, in command line order.
        self._cli: list[CliEntry] = []
        #: Resolved values, by canonical name.
        self._cache: dict[str, Any] = {}
        #: The command line options that are not configuration settings.
        self.options = OptionsView(registry, config)

    def __getitem__(self, name: str) -> Any:
        canonical_name = self._registry.canonical(name)
        try:
            return self._cache[canonical_name]
        except KeyError:
            pass
        setting = self._registry.get(canonical_name)
        if setting is None or not setting.settable_from_file:
            raise KeyError(canonical_name)
        value = self._resolve(canonical_name, setting)
        self._cache[canonical_name] = value
        return value

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        setting = self._registry.get(name)
        return setting is not None and setting.settable_from_file

    def __iter__(self) -> Iterator[str]:
        return (
            name
            for name, setting in self._registry._settings.items()
            if setting.settable_from_file
        )

    def __len__(self) -> int:
        return sum(1 for _ in self)

    @property
    def aliases(self) -> Mapping[str, str]:
        """Maps each alias to the setting name it stands for."""
        return types.MappingProxyType(self._registry._aliases)

    def spec(self, name: str) -> Setting:
        """The declaration of one setting."""
        canonical_name = self._registry.canonical(name)
        setting = self._registry.get(canonical_name)
        if setting is None or not setting.settable_from_file:
            raise KeyError(canonical_name)
        return setting

    def resolved_from(self, name: str) -> str:
        """The name of the setting that supplied the value of this one.

        Its own name, unless it is not configured and a fallback of it is.
        """
        canonical_name = self._registry.canonical(name)
        setting = self.spec(canonical_name)
        if self.source_of(canonical_name) is not Source.FALLBACK:
            return canonical_name
        for target in setting.fallback:
            if self.is_configured(target):
                return self.resolved_from(target)
        return canonical_name  # pragma: no cover

    def unknown_names(self) -> set[str]:
        """Configured names that were never declared."""
        known = {
            name
            for name, setting in self._registry._settings.items()
            if setting.settable_from_file
        } | self._registry._aliases.keys()
        return self.configured.keys() - known

    @property
    def configured(self) -> ConfigDict:
        """Every configured value, command line beating configuration file."""
        merged = dict(self._file)
        for entry in self._cli:
            merged[entry.name] = entry.as_config_value()
        return merged

    def set_cli(self, entries: Sequence[CliEntry]) -> None:
        """Replace the command line layer.

        Options are registered in several rounds -- core plugins, then
        third-party plugins, then conftests -- and each round re-parses the
        whole command line, so a later round can only ever see more. Replacing
        keeps a flag registered by a late round from being dropped, without
        collecting an entry twice.
        """
        if list(entries) != self._cli:
            self._cli = list(entries)
            self._cache.clear()

    def add_entry(self, entry: CliEntry) -> None:
        """Append one value to the command line layer, overriding the rest."""
        self._cli.append(entry)
        self._cache.clear()

    def discard(self, name: str) -> None:
        """Drop every configured value for a name, from every layer."""
        self._file.pop(name, None)
        self._cli = [entry for entry in self._cli if entry.name != name]
        self._cache.clear()

    def _cli_entry(self, canonical_name: str) -> CliEntry | None:
        """The last command line value for a setting, if any."""
        for entry in reversed(self._cli):
            if self._registry.canonical(entry.name) == canonical_name:
                return entry
        return None

    def source_of(self, name: str) -> Source:
        """Where the value of a setting came from."""
        canonical_name = self._registry.canonical(name)
        setting = self._registry.get(canonical_name)
        if setting is None or not setting.settable_from_file:
            raise KeyError(canonical_name)
        entry = self._cli_entry(canonical_name)
        if entry is not None:
            return entry.source
        if self._candidates(canonical_name):
            return Source.FILE
        if any(self.is_configured(target) for target in setting.fallback):
            return Source.FALLBACK
        return Source.DEFAULT

    def _candidates(self, canonical_name: str) -> list[tuple[ConfigValue, bool]]:
        """Collect the configured values for a setting.

        Looks under the canonical name and under every alias of it; each
        candidate is ``(ConfigValue, is_canonical)``.
        """
        candidates = []
        if canonical_name in self._file:
            candidates.append((self._file[canonical_name], True))
        for alias, target in self._registry._aliases.items():
            if target == canonical_name and alias in self._file:
                candidates.append((self._file[alias], False))
        return candidates

    def is_configured(self, name: str) -> bool:
        """Whether a setting has a value from a config file or an override.

        True if the setting itself is set, or -- transitively -- if any
        setting it falls back to is. Terminates because `addini` only accepts
        an already-registered fallback, which rules out cycles.
        """
        canonical_name = self._registry.canonical(name)
        if self._cli_entry(canonical_name) is not None:
            return True
        if self._candidates(canonical_name):
            return True
        setting = self._registry.get(canonical_name)
        return setting is not None and any(
            self.is_configured(target) for target in setting.fallback
        )

    def _resolve(self, canonical_name: str, setting: Setting) -> Any:
        # The command line beats every configuration file, and among command
        # line values the last one written wins.
        entry = self._cli_entry(canonical_name)
        if entry is not None:
            assert setting.type is not None
            return self._config._coerce_setting(
                canonical_name, setting.type, entry.as_config_value(), setting.default
            )

        candidates = self._candidates(canonical_name)

        if not candidates:
            # Not configured: defer to the first fallback that is, and only
            # use the registered default if none of them is either.
            for target in setting.fallback:
                if self.is_configured(target):
                    value = self[target]
                    # Don't hand out the fallback's own cached container:
                    # `addinivalue_line` mutates what `getini` returns, which
                    # would otherwise write through into the fallback setting.
                    return list(value) if isinstance(value, list) else value
            return setting.default

        # The canonical name takes precedence over an alias of it.
        selected = max(candidates, key=lambda x: x[1])[0]
        # A setting a config file can set always has a type.
        assert setting.type is not None
        return self._config._coerce_setting(
            canonical_name, setting.type, selected, setting.default
        )


class OptionNamespace(argparse.Namespace):
    """The namespace behind ``config.option``.

    Values live in the instance ``__dict__``, as for a plain
    :class:`argparse.Namespace`, so ``vars()``, ``__dict__.update`` and
    ``copy.copy`` are unchanged.
    """

    #: Whether accessing a store-backed setting warns. Off while parsing,
    #: which sets these attributes itself, over and over.
    _warn_access: ClassVar[bool] = False


def make_option_namespace() -> OptionNamespace:
    """Build a namespace for one `Config`.

    A fresh subclass per `Config`, so that `install_option_property` can add a
    property for one setting without touching any other namespace.
    """
    cls: type[OptionNamespace] = type("Namespace", (OptionNamespace,), {})
    return cls()


def install_option_property(namespace: OptionNamespace, dest: str) -> None:
    """Make ``namespace.<dest>`` warn, without slowing down every other read.

    The value of a setting comes from the store, and ``config.option`` shows
    the resolved value as a convenience. Reading it there is deprecated, and
    writing it there does not change what the store resolves -- but only for
    the settings that have a store behind them, which is why this is a
    property on those names rather than a ``__getattr__`` paid for by every
    attribute of every namespace.
    """
    cls = type(namespace)
    if dest in cls.__dict__:
        return

    def get(self: OptionNamespace, dest: str = dest) -> Any:
        try:
            value = self.__dict__[dest]
        except KeyError:
            raise AttributeError(dest) from None
        if self._warn_access:
            _warn_option_access(dest, reading=True)
        return value

    def set(self: OptionNamespace, value: Any, dest: str = dest) -> None:
        if self._warn_access:
            _warn_option_access(dest, reading=False)
        self.__dict__[dest] = value

    def delete(self: OptionNamespace, dest: str = dest) -> None:
        del self.__dict__[dest]

    setattr(cls, dest, property(get, set, delete))


def _warn_option_access(dest: str, *, reading: bool) -> None:
    from _pytest.deprecated import OPTION_READ_FOR_SETTING
    from _pytest.deprecated import OPTION_WRITE_FOR_SETTING

    template = OPTION_READ_FOR_SETTING if reading else OPTION_WRITE_FOR_SETTING
    warnings.warn(template.format(name=dest), stacklevel=4)


def _declaration_site() -> tuple[str, int] | None:
    """Where the plugin called `addini`, for a warning to point at.

    The strings are taken now and the frame dropped: a frame kept alive here
    would keep a whole call stack alive with it.
    """
    # Skip this module and `argparsing`, so the site is the caller of
    # `addini` or `addconfig` rather than either of them.
    internal = {__name__, f"{__package__}.argparsing"}
    frame: types.FrameType | None = sys._getframe()
    while frame is not None and frame.f_globals.get("__name__") in internal:
        frame = frame.f_back
    if frame is None:  # pragma: no cover
        return None
    return frame.f_code.co_filename, frame.f_lineno
