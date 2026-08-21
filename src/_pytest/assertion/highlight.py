"""Highlighting helpers for assertion explanations.

Pygments markup is applied at terminal-display time, not when the explanation
is first built.  Comparison helpers wrap highlighted spans in private markers
so JUnit XML and other plain-text consumers can recover the original source
(including any escape sequences that belong to the values under test).
"""

from __future__ import annotations

import re
from typing import Literal

from _pytest.assertion._typing import _HighlightFunc


# Attribute set on AssertionError to keep the marked-up explanation after the
# public exception message has been stripped to plain text.
DEFERRED_HL_ATTR = "_pytest_deferred_hl"

# Marker protocol (SOH-delimited):
#   \x01p<source>\x01 / \x01d<source>\x01   start of a python/diff span
#   \x01P<source>\x01 / \x01D<source>\x01   continuation of the previous span
# A literal SOH in *source* is escaped as \x01\x02.
# Continuations exist so a multi-line ``highlighter()`` call can be split into
# lines and later re-joined, matching Pygments' whole-block colouring.
_START_CODE = {"python": "p", "diff": "d"}
_CONT_CODE = {"python": "P", "diff": "D"}
_CODE_TO_LEXER: dict[str, Literal["python", "diff"]] = {
    "p": "python",
    "P": "python",
    "d": "diff",
    "D": "diff",
}
_TAG_RE = re.compile(r"\x01([pdPD])((?:\x01\x02|[^\x01])*)\x01")


def dummy_highlighter(source: str, lexer: Literal["diff", "python"] = "python") -> str:
    """Dummy highlighter that returns the text unprocessed.

    Needed for _notin_text, as the diff gets post-processed to only show the "+" part.
    """
    return source


def deferred_highlighter(
    source: str, lexer: Literal["diff", "python"] = "python"
) -> str:
    """Wrap *source* in deferred-highlight markers instead of applying Pygments.

    Multi-line input is tagged per line (first line starts a span, the rest
    continue it) so later ``splitlines()`` keeps enough information to rebuild
    the original block.
    """
    if not source:
        return source
    try:
        start = _START_CODE[lexer]
        cont = _CONT_CODE[lexer]
    except KeyError:
        raise ValueError(f"unknown lexer: {lexer!r}") from None
    keep_nl = source.endswith("\n")
    tagged_lines: list[str] = []
    for i, line in enumerate(source.splitlines()):
        code = start if i == 0 else cont
        tagged_lines.append(f"\x01{code}{line.replace(chr(1), chr(1) + chr(2))}\x01")
    tagged = "\n".join(tagged_lines)
    if keep_nl:
        tagged += "\n"
    return tagged


def contains_deferred_highlight(text: str) -> bool:
    """Return whether *text* contains a highlight marker."""
    return "\x01" in text and _TAG_RE.search(text) is not None


def _unescape_source(escaped: str) -> str:
    return escaped.replace("\x01\x02", "\x01")


def strip_deferred_highlight(text: str) -> str:
    """Return *text* with deferred-highlight markers removed."""
    if "\x01" not in text:
        return text
    return _TAG_RE.sub(lambda m: _unescape_source(m.group(2)), text)


def resolve_highlight(text: str, highlighter: _HighlightFunc | None) -> str:
    """Replace deferred-highlight markers in *text*.

    If *highlighter* is ``None``, emit the original source of each span.
    Otherwise apply ``highlighter(source, lexer)`` to each span.  Consecutive
    continuation lines of the same lexer are highlighted as one block so the
    colours match a single original ``highlighter()`` call.
    """
    if "\x01" not in text:
        return text
    if highlighter is None:
        return strip_deferred_highlight(text)
    return _resolve_with_highlighter(text, highlighter)


def _resolve_with_highlighter(text: str, highlighter: _HighlightFunc) -> str:
    # Fast path: no multi-line continuation, highlight each span in place.
    if "\x01P" not in text and "\x01D" not in text:
        return _TAG_RE.sub(
            lambda m: highlighter(
                _unescape_source(m.group(2)), _CODE_TO_LEXER[m.group(1)]
            ),
            text,
        )

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        start = _first_tag(line)
        if start is None or start.isupper():
            out.append(_resolve_line(line, highlighter))
            i += 1
            continue
        lexer = _CODE_TO_LEXER[start]
        cont = _CONT_CODE[lexer]
        group = [line]
        i += 1
        while i < len(lines) and _first_tag(lines[i]) == cont:
            group.append(lines[i])
            i += 1
        out.append(_highlight_group(group, highlighter, lexer))
    return "".join(out)


def _first_tag(line: str) -> str | None:
    match = _TAG_RE.search(line)
    return match.group(1) if match else None


def _resolve_line(line: str, highlighter: _HighlightFunc) -> str:
    return _TAG_RE.sub(
        lambda m: highlighter(_unescape_source(m.group(2)), _CODE_TO_LEXER[m.group(1)]),
        line,
    )


def _highlight_group(
    lines: list[str], highlighter: _HighlightFunc, lexer: Literal["python", "diff"]
) -> str:
    """Highlight a start+continuation group as one Pygments input."""
    prefixes: list[str] = []
    bodies: list[str] = []
    suffixes: list[str] = []
    newlines: list[str] = []
    for line in lines:
        nl = "\n" if line.endswith("\n") else ""
        core = line[:-1] if nl else line
        match = _TAG_RE.search(core)
        if match is None:
            prefixes.append(core)
            bodies.append("")
            suffixes.append("")
            newlines.append(nl)
            continue
        prefixes.append(core[: match.start()])
        bodies.append(_unescape_source(match.group(2)))
        suffixes.append(core[match.end() :])
        newlines.append(nl)

    highlighted = highlighter("\n".join(bodies), lexer)
    hl_lines = highlighted.splitlines()
    rendered: list[str] = []
    for idx, (prefix, suffix, nl) in enumerate(
        zip(prefixes, suffixes, newlines, strict=True)
    ):
        hl = hl_lines[idx] if idx < len(hl_lines) else ""
        rendered.append(f"{prefix}{hl}{suffix}{nl}")
    if len(hl_lines) > len(lines):
        prefix = prefixes[-1] if prefixes else ""
        nl = newlines[-1] if newlines else "\n"
        for hl in hl_lines[len(lines) :]:
            rendered.append(f"{prefix}{hl}{nl}")
    return "".join(rendered)


def resolve_highlight_for_writer(text: str, tw: object) -> str:
    """Resolve markers for a terminal writer, or strip them for plain output.

    ``tw`` is untyped so tests can pass the lightweight ``TWMock``.
    """
    if not contains_deferred_highlight(text):
        return text
    hasmarkup = getattr(tw, "hasmarkup", False)
    code_highlight = getattr(tw, "code_highlight", True)
    highlight = getattr(tw, "_highlight", None)
    if hasmarkup and code_highlight and highlight is not None:
        return resolve_highlight(text, highlight)
    return strip_deferred_highlight(text)
