"""The registry of declared configuration settings.

Every setting a plugin declares -- with :meth:`Parser.addini
<pytest.Parser.addini>`, :meth:`Parser.addconfig <pytest.Parser.addconfig>` or
:meth:`Parser.addoption <pytest.Parser.addoption>` -- is recorded here as a
single :class:`Setting`, together with the sources allowed to set it. The
registry holds the *declarations*; the values resolved from them live on
``Config``.
"""

from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Mapping
import dataclasses
import enum
from typing import Any
from typing import final
from typing import TYPE_CHECKING


if TYPE_CHECKING:
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
