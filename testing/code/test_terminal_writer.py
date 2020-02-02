import re
from io import StringIO

import pytest
from _pytest._io import TerminalWriter


# TODO: move this and the other two related attributes from test_terminal.py into conftest as a
# fixture
COLORS = {
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "bold": "\x1b[1m",
    "reset": "\x1b[0m",
    "kw": "\x1b[94m",
    "hl-reset": "\x1b[39;49;00m",
    "function": "\x1b[92m",
    "number": "\x1b[94m",
    "str": "\x1b[33m",
    "print": "\x1b[96m",
}


@pytest.mark.parametrize(
    "has_markup, expected",
    [
        pytest.param(
            True, "{kw}assert{hl-reset} {number}0{hl-reset}\n", id="with markup"
        ),
        pytest.param(False, "assert 0\n", id="no markup"),
    ],
)
def test_code_highlight(has_markup, expected):
    f = StringIO()
    tw = TerminalWriter(f)
    tw.hasmarkup = has_markup
    tw._write_source(["assert 0"])
    assert f.getvalue() == expected.format(**COLORS)

    with pytest.raises(
        ValueError,
        match=re.escape("indents size (2) should have same size as lines (1)"),
    ):
        tw._write_source(["assert 0"], [" ", " "])
