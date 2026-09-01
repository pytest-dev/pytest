# mypy: allow-untyped-defs
from __future__ import annotations

import argparse
from collections.abc import Callable
from collections.abc import Sequence
import dataclasses
import os
import sys
import textwrap
import types
from typing import Any
from typing import final
from typing import get_args
from typing import get_origin
from typing import Literal
from typing import NamedTuple
from typing import NoReturn
from typing import TYPE_CHECKING
from typing import TypeAlias
from typing import Union

from .exceptions import UsageError
import _pytest._io
from _pytest.compat import NOTSET
from _pytest.deprecated import check_ispytest


if TYPE_CHECKING:
    from typing_extensions import TypeForm


FILE_OR_DIR = "file_or_dir"

#: The string tags accepted by :meth:`Parser.addini` for its ``type`` argument.
_IniTypeTag: TypeAlias = Literal[
    "string", "paths", "pathlist", "args", "linelist", "bool", "int", "float"
]

if TYPE_CHECKING:
    #: The forms accepted by :meth:`Parser.addini` for its ``type`` argument;
    #: ``None`` means ``"string"``.
    _IniTypeArg: TypeAlias = _IniTypeTag | TypeForm[bool | int | float | str] | None


@final
@dataclasses.dataclass(frozen=True)
class _IniLiteral:
    """The choices of an ini option registered with a ``Literal`` type."""

    choices: tuple[str, ...]


#: An ini option type, as stored internally after normalization: a single tag,
#: the choices of a ``Literal`` type, or a tuple of members meaning "accept a
#: value of any of these" (e.g. ``("int", "string")``, normalized from
#: ``int | str``).
IniType: TypeAlias = _IniTypeTag | _IniLiteral | tuple[_IniTypeTag | _IniLiteral, ...]


@final
class IniSpec(NamedTuple):
    """The registration of an ini option, as stored in `Parser._inidict`.

    A named tuple rather than a dataclass so that positional access to the
    first three fields keeps working. Note that unpacking the whole record
    into exactly three names no longer does, now that `fallback` exists.
    """

    help: str
    type: IniType
    default: Any
    #: Names of other ini options to consult, in order, when this one is not
    #: configured; the registered `default` applies only if none of them is.
    fallback: tuple[str, ...] = ()


#: Maps each string tag or plain Python type accepted by :meth:`Parser.addini`
#: for its ``type`` argument to the normalized string tag.
_INI_TYPES: dict[object, _IniTypeTag] = {tag: tag for tag in get_args(_IniTypeTag)} | {
    str: "string",
    bool: "bool",
    int: "int",
    float: "float",
}


def _ini_type_to_tag(name: str, type_: object) -> _IniTypeTag:
    """Normalize one member of an `addini(type=...)` argument to a string tag."""
    try:
        return _INI_TYPES[type_]
    except (KeyError, TypeError):  # TypeError: unhashable type_
        raise ValueError(
            f"invalid type for ini option {name!r}: {type_!r} (expected one of "
            f"{', '.join(repr(tag) for tag in get_args(_IniTypeTag))}, one of "
            "the types str, bool, int, float, a union of these types such as "
            "`int | str`, or a `Literal` of strings)"
        ) from None


def _ini_type_to_member(name: str, type_: object) -> _IniTypeTag | _IniLiteral:
    """Normalize one member of an `addini(type=...)` argument."""
    if get_origin(type_) is Literal:
        choices = get_args(type_)
        if not all(isinstance(choice, str) for choice in choices):
            raise ValueError(
                f"invalid type for ini option {name!r}: Literal choices "
                f"must be strings, got {choices!r}"
            )
        return _IniLiteral(choices)
    return _ini_type_to_tag(name, type_)


def _ini_type_repr(type: IniType) -> str:
    """Render an ini option type for --help output and error messages."""
    if isinstance(type, _IniLiteral):
        return " | ".join(repr(choice) for choice in type.choices)
    if isinstance(type, tuple):
        return " | ".join(_ini_type_repr(member) for member in type)
    return type


def _get_argparse_dest(opts: Sequence[str]) -> str:
    long_opts = [opt for opt in opts if opt.startswith("--")]
    opt = long_opts[0] if long_opts else opts[0]
    return opt.lstrip("-").replace("-", "_")


@final
class Parser:
    """Parser for command line arguments and config-file values.

    :ivar extra_info: Dict of generic param -> value to display in case
        there's an error processing the command line arguments.
    """

    def __init__(
        self,
        usage: str | None = None,
        processopt: Callable[[Argument], None] | None = None,
        *,
        prog: str | None = None,
        _ispytest: bool = False,
    ) -> None:
        check_ispytest(_ispytest)

        from _pytest._argcomplete import filescompleter

        self._processopt = processopt
        self.extra_info: dict[str, Any] = {}
        self.optparser = PytestArgumentParser(usage, self.extra_info, prog=prog)
        anonymous_arggroup = self.optparser.add_argument_group("Custom options")
        self._anonymous = OptionGroup(
            anonymous_arggroup, "_anonymous", self, _ispytest=True
        )
        self._groups = [self._anonymous]
        # Maps option strings -> dest, e.g. "-V" and "--version" to "version".
        self._opt2dest: dict[str, str] = {}
        file_or_dir_arg = self.optparser.add_argument(FILE_OR_DIR, nargs="*")
        file_or_dir_arg.completer = filescompleter  # type: ignore

        self._inidict: dict[str, IniSpec] = {}
        # Maps alias -> canonical name.
        self._ini_aliases: dict[str, str] = {}

    @property
    def prog(self) -> str:
        return self.optparser.prog

    @prog.setter
    def prog(self, value: str) -> None:
        self.optparser.prog = value

    def processoption(self, option: Argument) -> None:
        if self._processopt:
            if option.dest:
                self._processopt(option)

    def getgroup(
        self, name: str, description: str = "", after: str | None = None
    ) -> OptionGroup:
        """Get (or create) a named option Group.

        :param name: Name of the option group.
        :param description: Long description for --help output.
        :param after: Name of another group, used for ordering --help output.
        :returns: The option group.

        The returned group object has an ``addoption`` method with the same
        signature as :func:`parser.addoption <pytest.Parser.addoption>` but
        will be shown in the respective group in the output of
        ``pytest --help``.
        """
        for group in self._groups:
            if group.name == name:
                return group

        arggroup = self.optparser.add_argument_group(description or name)
        group = OptionGroup(arggroup, name, self, _ispytest=True)
        i = 0
        for i, grp in enumerate(self._groups):
            if grp.name == after:
                break
        self._groups.insert(i + 1, group)
        # argparse doesn't provide a way to control `--help` order, so must
        # access its internals ☹.
        self.optparser._action_groups.insert(i + 1, self.optparser._action_groups.pop())
        return group

    def addoption(self, *opts: str, **attrs: Any) -> None:
        """Register a command line option.

        :param opts:
            Option names, can be short or long options.
        :param attrs:
            Same attributes as the argparse library's :meth:`add_argument()
            <argparse.ArgumentParser.add_argument>` function accepts.

        After command line parsing, options are available on the pytest config
        object via ``config.option.NAME`` where ``NAME`` is usually set
        by passing a ``dest`` attribute, for example
        ``addoption("--long", dest="NAME", ...)``.
        """
        self._anonymous.addoption(*opts, **attrs)

    def parse(
        self,
        args: Sequence[str | os.PathLike[str]],
        namespace: argparse.Namespace | None = None,
    ) -> argparse.Namespace:
        """Parse the arguments.

        Unlike ``parse_known_args`` and ``parse_known_and_unknown_args``,
        raises PrintHelp on `--help` and UsageError on unknown flags

        :meta private:
        """
        from _pytest._argcomplete import try_argcomplete

        try_argcomplete(self.optparser)
        strargs = [os.fspath(x) for x in args]
        if namespace is None:
            namespace = argparse.Namespace()
        try:
            namespace._raise_print_help = True
            return self.optparser.parse_intermixed_args(strargs, namespace=namespace)
        finally:
            del namespace._raise_print_help

    def parse_known_args(
        self,
        args: Sequence[str | os.PathLike[str]],
        namespace: argparse.Namespace | None = None,
    ) -> argparse.Namespace:
        """Parse the known arguments at this point.

        :returns: An argparse namespace object.
        """
        return self.parse_known_and_unknown_args(args, namespace=namespace)[0]

    def parse_known_and_unknown_args(
        self,
        args: Sequence[str | os.PathLike[str]],
        namespace: argparse.Namespace | None = None,
    ) -> tuple[argparse.Namespace, list[str]]:
        """Parse the known arguments at this point, and also return the
        remaining unknown flag arguments.

        :returns:
            A tuple containing an argparse namespace object for the known
            arguments, and a list of unknown flag arguments.
        """
        strargs = [os.fspath(x) for x in args]
        if sys.version_info < (3, 12, 8) or (3, 13) <= sys.version_info < (3, 13, 1):
            # Older argparse have a bugged parse_known_intermixed_args.
            namespace, unknown = self.optparser.parse_known_args(strargs, namespace)
            assert namespace is not None
            file_or_dir = getattr(namespace, FILE_OR_DIR)
            unknown_flags: list[str] = []
            for arg in unknown:
                (unknown_flags if arg.startswith("-") else file_or_dir).append(arg)
            return namespace, unknown_flags
        else:
            return self.optparser.parse_known_intermixed_args(strargs, namespace)

    def addini(
        self,
        name: str,
        help: str,
        type: _IniTypeArg = None,
        default: Any = NOTSET,
        *,
        aliases: Sequence[str] = (),
        fallback: str | Sequence[str] = (),
    ) -> None:
        """Register a configuration file option.

        :param name:
            Name of the configuration.
        :param type:
            Type of the configuration. Can be:

                * ``string``: a string
                * ``bool``: a boolean
                * ``args``: a list of strings, separated as in a shell
                * ``linelist``: a list of strings, separated by line breaks
                * ``paths``: a list of :class:`pathlib.Path`, separated as in a shell
                * ``pathlist``: a list of ``py.path``, separated as in a shell
                * ``int``: an integer
                * ``float``: a floating-point number

                .. versionadded:: 8.4

                    The ``float`` and ``int`` types.

            For the scalar types, the plain Python type may be passed instead
            of the string tag: ``str``, ``bool``, ``int`` and ``float`` (for
            example ``type=int``). A union of these types accepts a value of
            any of its members, for example ``int | str``. In TOML
            configuration files the value may then be any of the member types;
            string-based formats (INI files, ``-o`` overrides) coerce it to the
            first member that accepts it.

            A ``Literal`` type of strings restricts the value to the given
            choices, for example ``Literal["auto", "long", "short"]``, and may
            also be a union member, for example ``int | Literal["auto"]``.
            Since the choices have no unambiguous implicit default, an
            explicit ``default`` must be passed.

            .. versionadded:: 9.2

                Passing a type expression such as ``int``, ``int | str``, or
                a ``Literal`` of strings.

            For ``paths`` and ``pathlist`` types, they are considered relative to the config-file.
            In case the execution is happening without a config-file defined,
            they will be considered relative to the current working directory (for example with ``--override-ini``).

            .. versionadded:: 7.0
                The ``paths`` variable type.

            .. versionadded:: 8.1
                Use the current working directory to resolve ``paths`` and ``pathlist`` in the absence of a config-file.

            Defaults to ``string`` if ``None`` or not passed.
        :param default:
            Default value if no config-file option exists but is queried.
        :param aliases:
            Additional names by which this option can be referenced.
            Aliases resolve to the canonical name.

            .. versionadded:: 9.0
                The ``aliases`` parameter.
        :param fallback:
            Name (or names, tried in order) of another registered option to
            consult when this one is not set in any configuration file and was
            not overridden on the command line. The registered ``default``
            applies only if no fallback is configured either.

            Unlike an alias, a fallback is a *different* option with its own
            help and its own value; it just supplies this option's value when
            this option says nothing. For example ``log_cli_format`` falls back
            to ``log_format``.

            Each fallback must already be registered and must have the same
            type as this option, which also makes fallback cycles impossible.

            .. versionadded:: 9.2
                The ``fallback`` parameter. It is experimental; its behaviour
                may change in future releases.

        The value of configuration keys can be retrieved via a call to
        :py:func:`config.getini(name) <pytest.Config.getini>`.
        """
        ini_type: IniType
        if type is None:
            ini_type = "string"
        elif get_origin(type) in (Union, types.UnionType):
            ini_type = tuple(
                _ini_type_to_member(name, member) for member in get_args(type)
            )
        else:
            ini_type = _ini_type_to_member(name, type)
        if default is NOTSET:
            if isinstance(ini_type, (tuple, _IniLiteral)):
                kind = "union" if isinstance(ini_type, tuple) else "Literal"
                raise ValueError(
                    f"ini option {name!r} has a {kind} type, which has no "
                    "implicit default; pass an explicit `default` to `addini`"
                )
            default = get_ini_default_for_type(ini_type)

        fallbacks = (fallback,) if isinstance(fallback, str) else tuple(fallback)
        for target in fallbacks:
            canonical = self._ini_aliases.get(target, target)
            try:
                target_spec = self._inidict[canonical]
            except KeyError:
                raise ValueError(
                    f"fallback {target!r} of ini option {name!r} is not "
                    "registered; register it first"
                ) from None
            if target_spec.type != ini_type:
                raise ValueError(
                    f"fallback {target!r} of ini option {name!r} has type "
                    f"{_ini_type_repr(target_spec.type)}, expected "
                    f"{_ini_type_repr(ini_type)}"
                )

        self._inidict[name] = IniSpec(help, ini_type, default, fallbacks)

        for alias in aliases:
            if alias in self._inidict:
                raise ValueError(
                    f"alias {alias!r} conflicts with existing configuration option"
                )
            if (already := self._ini_aliases.get(alias)) is not None:
                raise ValueError(f"{alias!r} is already an alias of {already!r}")
            self._ini_aliases[alias] = name

    def addconfig(
        self,
        name: str,
        help: str,
        type: _IniTypeArg = None,
        default: Any = NOTSET,
        *,
        aliases: Sequence[str] = (),
        fallback: str | Sequence[str] = (),
        cli: str | Sequence[str] = (),
        cli_value: str | None = None,
        cli_help: str | None = None,
        group: str | OptionGroup | None = None,
        metavar: str | None = None,
    ) -> None:
        """Register a configuration option, optionally with a command line
        option that sets it.

        This declares in one call what :meth:`addini` and :meth:`addoption`
        otherwise declare twice, in two APIs whose ``type`` arguments mean
        different things. The type is given once, and
        :func:`config.getini(name) <pytest.Config.getini>` is the only way the
        value is read -- the command line option overrides the configuration
        value rather than living in a separate namespace, so consuming code
        never has to consider which of the two the user used.

        :param name:
            Name of the configuration option. Also the ``dest`` of the command
            line option, so the value is additionally visible as
            ``config.option.<name>``.
        :param help:
            Description, used for both the configuration option and the command
            line option unless ``cli_help`` overrides the latter.
        :param type:
            Type of the value, as for :meth:`addini`.
        :param default:
            Default value, as for :meth:`addini`.
        :param aliases:
            Additional configuration names for this option, as for
            :meth:`addini`.
        :param fallback:
            Another registered option to take the value from when this one is
            not configured, as for :meth:`addini`.
        :param cli:
            Command line option string, or several of them (for example
            ``("--junitxml", "--junit-xml")``). If empty, no command line
            option is registered and this behaves exactly like :meth:`addini`.
        :param cli_help:
            Help for the command line option; defaults to ``help``.
        :param cli_value:
            Makes the command line option a flag taking no argument, which sets
            the configuration option to this value. Defaults to ``"true"`` for
            a ``bool`` option and to taking an argument otherwise.
        :param group:
            Option group for ``--help`` output, by name or as an
            :class:`OptionGroup`. Defaults to the anonymous group.
        :param metavar:
            Argument placeholder in ``--help`` output.

        .. versionadded:: 9.2

        .. note::

            This method is experimental; its behaviour and signature may change
            in future releases.
        """
        self.addini(
            name,
            help,
            type,
            default,
            aliases=aliases,
            fallback=fallback,
        )
        opts = (cli,) if isinstance(cli, str) else tuple(cli)
        if not opts:
            if cli_value is not None or cli_help is not None or metavar is not None:
                raise ValueError(
                    f"config option {name!r} has no `cli` option strings, so "
                    "`cli_value`, `cli_help` and `metavar` have no effect"
                )
            return

        if cli_value is None and self._inidict[name].type == "bool":
            cli_value = "true"

        attrs: dict[str, Any] = {
            "action": OverrideIniAction,
            "ini_option": name,
            "ini_value": cli_value,
            "dest": name,
            "help": help if cli_help is None else cli_help,
            # The value lives in the ini config; argparse must not seed
            # `config.option.<name>` with a second, competing default.
            "default": None,
        }
        if metavar is not None:
            attrs["metavar"] = metavar

        if group is None:
            target = self._anonymous
        elif isinstance(group, str):
            target = self.getgroup(group)
        else:
            target = group
        target.addoption(*opts, **attrs)


def get_ini_default_for_type(type: _IniTypeTag) -> Any:
    """
    Used by addini to get the default value for a given config option type, when
    default is not supplied.
    """
    if type in ("paths", "pathlist", "args", "linelist"):
        return []
    elif type == "bool":
        return False
    elif type == "int":
        return 0
    elif type == "float":
        return 0.0
    else:
        return ""


class Argument:
    """An option defined in an OptionGroup."""

    def __init__(self, action: argparse.Action) -> None:
        self._action = action

    def attrs(self) -> dict[str, Any]:
        return self._action.__dict__

    def names(self) -> Sequence[str]:
        return self._action.option_strings

    @property
    def dest(self) -> str:
        return self._action.dest

    @property
    def default(self) -> Any:
        return self._action.default

    @property
    def type(self) -> Any | None:
        return self._action.type

    def __repr__(self) -> str:
        action = getattr(self, "_action", None)
        if action is None:
            return "Argument(<uninitialized>)"
        args: list[str] = []
        args += ["opts: " + repr(self.names())]
        args += ["dest: " + repr(self.dest)]
        if action.type:
            args += ["type: " + repr(self.type)]
        args += ["default: " + repr(self.default)]
        return "Argument({})".format(", ".join(args))


class OptionGroup:
    """A group of options shown in its own section."""

    def __init__(
        self,
        arggroup: argparse._ArgumentGroup,
        name: str,
        parser: Parser | None,
        _ispytest: bool = False,
    ) -> None:
        check_ispytest(_ispytest)
        self._arggroup = arggroup
        self.name = name
        self.options: list[Argument] = []
        self.parser = parser

    def addoption(self, *opts: str, **attrs: Any) -> None:
        """Add an option to this group.

        If a shortened version of a long option is specified, it will
        be suppressed in the help. ``addoption('--twowords', '--two-words')``
        results in help showing ``--two-words`` only, but ``--twowords`` gets
        accepted **and** the automatic destination is in ``args.twowords``.

        :param opts:
            Option names, can be short or long options.
            Note that lower-case short options (e.g. `-x`) are reserved.
        :param attrs:
            Same attributes as the argparse library's :meth:`add_argument()
            <argparse.ArgumentParser.add_argument>` function accepts.
        """
        conflict = set(opts).intersection(
            name for opt in self.options for name in opt.names()
        )
        if conflict:
            raise ValueError(f"option names {conflict} already added")

        if self.parser and "dest" not in attrs:
            dest = _get_argparse_dest(opts)
            for group in self.parser._groups:
                for option in group.options:
                    if option.dest == dest:
                        raise ValueError(
                            f"option dest {dest!r} already used by "
                            f"{option.names()!r} (this is the option that maps to "
                            f"dest {dest!r}); pass dest={dest!r} explicitly "
                            "to share the destination"
                        )
        self._addoption_inner(opts, attrs, allow_reserved=False)

    def _addoption(self, *opts: str, **attrs: Any) -> None:
        """Like addoption(), but also allows registering short lower case options (e.g. -x),
        which are reserved for pytest core."""
        self._addoption_inner(opts, attrs, allow_reserved=True)

    def _addoption_inner(
        self, opts: tuple[str, ...], attrs: dict[str, Any], allow_reserved: bool
    ) -> None:
        if not allow_reserved:
            for opt in opts:
                if len(opt) >= 2 and opt[0] == "-" and opt[1].islower():
                    raise ValueError("lowercase short options are reserved")

        action = self._arggroup.add_argument(*opts, **attrs)
        option = Argument(action)
        self.options.append(option)
        if self.parser:
            for name in option.names():
                self.parser._opt2dest[name] = option.dest
            self.parser.processoption(option)


class PytestArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        usage: str | None,
        extra_info: dict[str, str],
        *,
        prog: str | None = None,
    ) -> None:
        super().__init__(
            usage=usage,
            prog=prog,
            add_help=False,
            formatter_class=DropShorterLongHelpFormatter,
            allow_abbrev=False,
            fromfile_prefix_chars="@",
        )
        # extra_info is a dict of (param -> value) to display if there's
        # an usage error to provide more contextual information to the user.
        self.extra_info = extra_info

    def error(self, message: str) -> NoReturn:
        """Transform argparse error message into UsageError."""
        # TODO(py313): Replace with `exit_on_error=False`. Note that while it
        # was added in Python 3.9, it was broken until 3.13 (cpython#121018).
        msg = f"{self.prog}: error: {message}"
        if self.extra_info:
            msg += "\n" + "\n".join(
                f"  {k}: {v}" for k, v in sorted(self.extra_info.items())
            )
        raise UsageError(self.format_usage() + msg)


class DropShorterLongHelpFormatter(argparse.HelpFormatter):
    """Shorten help for long options that differ only in extra hyphens.

    - Collapse **long** options that are the same except for extra hyphens.
    - Shortcut if there are only two options and one of them is a short one.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Use more accurate terminal width.
        if "width" not in kwargs:
            kwargs["width"] = _pytest._io.get_terminal_width()
        super().__init__(*args, **kwargs)

    def _format_action_invocation(self, action: argparse.Action) -> str:
        orgstr = super()._format_action_invocation(action)
        if orgstr and orgstr[0] != "-":  # only optional arguments
            return orgstr
        options = orgstr.split(", ")
        if len(options) == 2 and (len(options[0]) == 2 or len(options[1]) == 2):
            # a shortcut for '-h, --help' or '--abc', '-a'
            return orgstr
        return_list = []
        short_long: dict[str, str] = {}
        for option in options:
            if len(option) == 2 or option[2] == " ":
                continue
            assert option.startswith("--"), (
                f'long optional argument without "--": [{option}]'
            )
            xxoption = option[2:]
            shortened = xxoption.replace("-", "")
            if shortened not in short_long or len(short_long[shortened]) < len(
                xxoption
            ):
                short_long[shortened] = xxoption
        # now short_long has been filled out to the longest with dashes
        # **and** we keep the right option ordering from add_argument
        for option in options:
            if len(option) == 2 or option[2] == " ":
                return_list.append(option)
            if option[2:] == short_long.get(option.replace("-", "")):
                return_list.append(option.replace(" ", "=", 1))
        return ", ".join(return_list)

    def _split_lines(self, text: str, width: int) -> list[str]:
        """Wrap lines after splitting on original newlines.

        This allows to have explicit line breaks in the help text.
        """
        lines = []
        for line in text.splitlines():
            lines.extend(textwrap.wrap(line.strip(), width))
        return lines


class OverrideIniAction(argparse.Action):
    """Argparse action that makes a CLI option equivalent to overriding a
    configuration option.

    This can simplify things since code only needs to inspect the config option
    and not consider the CLI flag.

    Two shapes, chosen by whether ``ini_value`` is given:

    * with ``ini_value``, the option is a flag taking no argument, and sets the
      config option to that fixed value (e.g. ``--strict-markers``);
    * without it, the option takes one argument, and sets the config option to
      it (e.g. ``--log-cli-format=FORMAT``).

    The override is appended to ``override_ini``, the same list ``-o`` writes
    to, so the two compose in command line order and the value goes through
    exactly the same coercion as one written in a config file.
    """

    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        nargs: int | str | None = None,
        *args,
        ini_option: str,
        ini_value: str | None = None,
        **kwargs,
    ) -> None:
        if ini_value is None:
            if nargs is None:
                nargs = 1
            elif nargs != 1:
                raise ValueError(
                    "OverrideIniAction takes exactly one argument unless "
                    "`ini_value` makes it a flag"
                )
        else:
            nargs = 0
        super().__init__(option_strings, dest, nargs, *args, **kwargs)
        self.ini_option = ini_option
        self.ini_value = ini_value

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None = None,
        option_string: str | None = None,
    ) -> None:
        if self.ini_value is not None:
            value = self.ini_value
            # Keep behaving like `store_true` for `config.option.<dest>`.
            setattr(namespace, self.dest, True)
        else:
            if isinstance(values, str):
                value = values
            else:
                assert values is not None
                value = str(values[0])
            setattr(namespace, self.dest, value)
        current_overrides = getattr(namespace, "override_ini", None)
        if current_overrides is None:
            current_overrides = []
        current_overrides.append(f"{self.ini_option}={value}")
        setattr(namespace, "override_ini", current_overrides)
