"""Helper functions for writing to terminals and files."""
import os
import shutil
import sys
from typing import Callable
from typing import cast
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import TextIO

from colorama import ansi

from .wcwidth import wcswidth
from _pytest.compat import final

# This code was initially copied from py 1.8.1, file _io/terminalwriter.py.


def get_terminal_width() -> int:
    width, _ = shutil.get_terminal_size(fallback=(80, 24))

    # The Windows get_terminal_size may be bogus, let's sanify a bit.
    if width < 40:
        width = 80

    return width


def should_do_markup(file: TextIO) -> bool:
    if os.environ.get("PY_COLORS") == "1":
        return True
    if os.environ.get("PY_COLORS") == "0":
        return False
    if "NO_COLOR" in os.environ:
        return False
    if "FORCE_COLOR" in os.environ:
        return True
    return (
        hasattr(file, "isatty") and file.isatty() and os.environ.get("TERM") != "dumb"
    )


def _ansi_items(inst, transform: Callable[[str], str] = str.lower) -> Dict[str, str]:
    return {transform(name): cast(str, item) for name, item in vars(inst).items()}


ESC_TABLE = {
    **_ansi_items(ansi.Fore),
    **_ansi_items(ansi.Back, str.capitalize),
    **_ansi_items(ansi.Style),
    # wrongly named in pylib
    "purple": ansi.Fore.MAGENTA,
    "Purple": ansi.Back.MAGENTA,
    # missing, but hopefully unused
    "invert": ansi.code_to_chars(7),
    "blink": ansi.code_to_chars(5),
    # wrongly named in pylib
    "light": ansi.Style.DIM,
    "bold": ansi.Style.BRIGHT,
}
RESET = ansi.Style.RESET_ALL


@final
class TerminalWriter:
    hasmarkup: bool
    code_highlight: bool

    def __init__(
        self,
        file: Optional[TextIO] = None,
        dup=False,
        has_markup: Optional[bool] = None,
        code_highlight: bool = True,
    ) -> None:
        if file is None:
            file = sys.stdout
        if hasattr(file, "isatty") and file.isatty() and sys.platform == "win32":
            try:
                import colorama
            except ImportError:
                pass
            else:
                file = colorama.AnsiToWin32(file).stream
                assert file is not None
        self._file = file
        self.hasmarkup = should_do_markup(file) if has_markup is None else has_markup
        self._current_line = ""
        self._terminal_width: Optional[int] = None
        self.code_highlight = code_highlight

    @property
    def fullwidth(self) -> int:
        if self._terminal_width is not None:
            return self._terminal_width
        return get_terminal_width()

    @fullwidth.setter
    def fullwidth(self, value: int) -> None:
        self._terminal_width = value

    @property
    def width_of_current_line(self) -> int:
        """Return an estimate of the width so far in the current line."""
        return wcswidth(self._current_line)

    def markup(self, text: str, **markup: bool) -> str:
        unknown = markup.keys() - ESC_TABLE.keys()
        if unknown:
            raise ValueError(f"unknown markup: {unknown!r}")
        if self.hasmarkup:
            esc = "".join(ESC_TABLE[name] for name, on in markup.items() if on)
            if esc:
                text = esc + text + RESET
        return text

    def sep(
        self,
        sepchar: str,
        title: Optional[str] = None,
        fullwidth: Optional[int] = None,
        **markup: bool,
    ) -> None:
        if fullwidth is None:
            fullwidth = self.fullwidth
        # The goal is to have the line be as long as possible
        # under the condition that len(line) <= fullwidth.
        if sys.platform == "win32":
            # If we print in the last column on windows we are on a
            # new line but there is no way to verify/neutralize this
            # (we may not know the exact line width).
            # So let's be defensive to avoid empty lines in the output.
            fullwidth -= 1
        if title is not None:
            # we want 2 + 2*len(fill) + len(title) <= fullwidth
            # i.e.    2 + 2*len(sepchar)*N + len(title) <= fullwidth
            #         2*len(sepchar)*N <= fullwidth - len(title) - 2
            #         N <= (fullwidth - len(title) - 2) // (2*len(sepchar))
            N = max((fullwidth - len(title) - 2) // (2 * len(sepchar)), 1)
            fill = sepchar * N
            line = f"{fill} {title} {fill}"
        else:
            # we want len(sepchar)*N <= fullwidth
            # i.e.    N <= fullwidth // len(sepchar)
            line = sepchar * (fullwidth // len(sepchar))
        # In some situations there is room for an extra sepchar at the right,
        # in particular if we consider that with a sepchar like "_ " the
        # trailing space is not important at the end of the line.
        if len(line) + len(sepchar.rstrip()) <= fullwidth:
            line += sepchar.rstrip()

        self.line(line, **markup)

    def write(self, msg: str, *, flush: bool = False, **markup: bool) -> None:
        if msg:
            current_line = msg.rsplit("\n", 1)[-1]
            if "\n" in msg:
                self._current_line = current_line
            else:
                self._current_line += current_line

            msg = self.markup(msg, **markup)

            try:
                self._file.write(msg)
            except UnicodeEncodeError:
                # Some environments don't support printing general Unicode
                # strings, due to misconfiguration or otherwise; in that case,
                # print the string escaped to ASCII.
                # When the Unicode situation improves we should consider
                # letting the error propagate instead of masking it (see #7475
                # for one brief attempt).
                msg = msg.encode("unicode-escape").decode("ascii")
                self._file.write(msg)

            if flush:
                self.flush()

    def line(self, s: str = "", **markup: bool) -> None:
        self.write(s, **markup)
        self.write("\n")

    def flush(self) -> None:
        self._file.flush()

    def _write_source(self, lines: Sequence[str], indents: Sequence[str] = ()) -> None:
        """Write lines of source code possibly highlighted.

        Keeping this private for now because the API is clunky. We should discuss how
        to evolve the terminal writer so we can have more precise color support, for example
        being able to write part of a line in one color and the rest in another, and so on.
        """
        if indents and len(indents) != len(lines):
            raise ValueError(
                "indents size ({}) should have same size as lines ({})".format(
                    len(indents), len(lines)
                )
            )
        if not indents:
            indents = [""] * len(lines)
        source = "\n".join(lines)
        new_lines = self._highlight(source).splitlines()
        for indent, new_line in zip(indents, new_lines):
            self.line(indent + new_line)

    def _highlight(self, source: str) -> str:
        """Highlight the given source code if we have markup support."""
        from _pytest.config.exceptions import UsageError

        if not self.hasmarkup or not self.code_highlight:
            return source
        try:
            from pygments.formatters.terminal import TerminalFormatter
            from pygments.lexers.python import PythonLexer
            from pygments import highlight
            import pygments.util
        except ImportError:
            return source
        else:
            try:
                highlighted: str = highlight(
                    source,
                    PythonLexer(),
                    TerminalFormatter(
                        bg=os.getenv("PYTEST_THEME_MODE", "dark"),
                        style=os.getenv("PYTEST_THEME"),
                    ),
                )
                return highlighted
            except pygments.util.ClassNotFound:
                raise UsageError(
                    "PYTEST_THEME environment variable had an invalid value: '{}'. "
                    "Only valid pygment styles are allowed.".format(
                        os.getenv("PYTEST_THEME")
                    )
                )
            except pygments.util.OptionError:
                raise UsageError(
                    "PYTEST_THEME_MODE environment variable had an invalid value: '{}'. "
                    "The only allowed values are 'dark' and 'light'.".format(
                        os.getenv("PYTEST_THEME_MODE")
                    )
                )
