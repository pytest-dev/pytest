from typing import List
from typing import Sequence

from py.io import TerminalWriter as BaseTerminalWriter  # noqa: F401


class TerminalWriter(BaseTerminalWriter):
    def _write_source(self, lines: List[str], indents: Sequence[str] = ()) -> None:
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

    def _highlight(self, source):
        """Highlight the given source code according to the "code_highlight" option"""
        if not self.hasmarkup:
            return source
        try:
            from pygments.formatters.terminal import TerminalFormatter
            from pygments.lexers.python import PythonLexer
            from pygments import highlight
        except ImportError:
            return source
        else:
            return highlight(source, PythonLexer(), TerminalFormatter(bg="dark"))
