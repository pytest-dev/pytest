from __future__ import annotations

from typing import Literal

from _pytest.assertion.highlight import contains_deferred_highlight
from _pytest.assertion.highlight import deferred_highlighter
from _pytest.assertion.highlight import resolve_highlight
from _pytest.assertion.highlight import resolve_highlight_for_writer
from _pytest.assertion.highlight import strip_deferred_highlight
from _pytest.assertion.rewrite import _assertion_error


def test_deferred_roundtrip_plain() -> None:
    tagged = deferred_highlighter("1 != 2")
    assert tagged != "1 != 2"
    assert contains_deferred_highlight(tagged)
    assert strip_deferred_highlight(tagged) == "1 != 2"


def test_deferred_preserves_escape_in_source() -> None:
    source = "\x1b[31mred\x1b[0m"
    tagged = deferred_highlighter(source)
    assert strip_deferred_highlight(tagged) == source
    assert "\x1b[31m" in strip_deferred_highlight(tagged)


def test_deferred_escapes_soh_in_source() -> None:
    source = "pre\x01post"
    tagged = deferred_highlighter(source)
    assert strip_deferred_highlight(tagged) == source


def test_deferred_tags_each_line() -> None:
    tagged = deferred_highlighter("- eggs\n+ spam", lexer="diff")
    assert strip_deferred_highlight(tagged) == "- eggs\n+ spam"
    assert tagged.count("\x01d") == 1
    assert tagged.count("\x01D") == 1


def test_resolve_highlight_applies_highlighter() -> None:
    seen: list[tuple[str, str]] = []

    def hl(source: str, lexer: Literal["diff", "python"] = "python") -> str:
        seen.append((source, lexer))
        return f"<{lexer}:{source}>"

    tagged = deferred_highlighter("1", lexer="python")
    assert resolve_highlight(tagged, hl) == "<python:1>"
    assert seen == [("1", "python")]


def test_resolve_highlights_multiline_as_one_block() -> None:
    seen: list[str] = []

    def hl(source: str, lexer: str = "python") -> str:
        seen.append(source)
        return "\n".join(f"<{line}>" for line in source.splitlines())

    tagged = deferred_highlighter("- eggs\n+ spam", lexer="diff")
    assert resolve_highlight(tagged, hl) == "<- eggs>\n<+ spam>"
    assert seen == ["- eggs\n+ spam"]


def test_assertion_error_message_is_plain() -> None:
    tagged = f"assert 1 == 2\n\n  At index 0 diff: {deferred_highlighter('1')} != {deferred_highlighter('2')}"
    err = _assertion_error(tagged)
    assert str(err) == "assert 1 == 2\n\n  At index 0 diff: 1 != 2"
    assert "\x01" not in str(err)


def test_resolve_for_writer_strips_without_markup() -> None:
    class Tw:
        hasmarkup = False
        code_highlight = True

        def _highlight(self, source: str, lexer: str = "python") -> str:
            return f"HL:{source}"

    tagged = deferred_highlighter("1")
    assert resolve_highlight_for_writer(tagged, Tw()) == "1"


def test_resolve_for_writer_highlights_with_markup() -> None:
    class Tw:
        hasmarkup = True
        code_highlight = True

        def _highlight(self, source: str, lexer: str = "python") -> str:
            return f"HL:{source}"

    tagged = deferred_highlighter("1")
    assert resolve_highlight_for_writer(tagged, Tw()) == "HL:1"
