from __future__ import annotations

import dataclasses
import io
import json
from pathlib import Path
import sys
from typing import Any

from rich.console import Console

from _pytest._code import ExceptionRecord
from _pytest._code import FrameRecord
from _pytest._code import Location
from _pytest._code import PytestTraceback
from _pytest._code import TracebackStyle
from _pytest._code.record import SyntaxErrorDetails
from _pytest._code.source import Source
from _pytest.doctest import ReprFailDoctest
from _pytest.fixtures import FixtureLookupErrorRepr
from _pytest.pytester import Pytester
from _pytest.reports import CollectErrorRepr
import pytest


def frame(**overrides: Any) -> FrameRecord:
    return dataclasses.replace(
        FrameRecord(
            path="snapshot.py",
            abspath=None,
            lineno=2,
            end_lineno=2,
            colno=11,
            end_colno=16,
            function="failure",
            module="snapshot",
            statement=("def failure():", "    return 1 / 0"),
            statement_lineno=1,
        ),
        **overrides,
    )


def rich_text(value: Any, width: int = 80) -> str:
    output = io.StringIO()
    Console(file=output, width=width).print(value)
    return output.getvalue()


def test_location_rich_multiline_message() -> None:
    rendered = rich_text(Location("snapshot.py", 2, "first line\nsecond line"))
    assert "snapshot.py:2: first line" in rendered
    assert "second line" not in rendered


def test_syntax_error_roundtrip_and_rich_details() -> None:
    with pytest.raises(SyntaxError) as excinfo:
        compile("x = (", "broken.py", "exec")
    record = excinfo.record()
    restored = ExceptionRecord.from_dict(json.loads(json.dumps(record.to_dict())))
    assert restored == record
    assert restored.syntax_error is not None
    assert restored.syntax_error.format_only("CustomSyntaxError").endswith(
        f"CustomSyntaxError: {record.message}"
    )
    rich_syntax = restored.to_rich_trace().stacks[0].syntax_error
    assert rich_syntax is not None
    assert rich_syntax.filename == "broken.py"
    assert rich_syntax.line == "x = (\n"


def test_syntax_error_details_without_message() -> None:
    details = SyntaxErrorDetails(None, None, None, None)
    assert SyntaxErrorDetails.from_dict(details.to_dict()) == details
    assert details.format_only("SyntaxError") == "SyntaxError: <no detail available>"


def test_unknown_frame_style_on_wire() -> None:
    data = frame().to_dict()
    data["repr_style"] = "unsupported"
    restored = FrameRecord.from_dict(data)
    assert restored.repr_style is None
    assert "return 1 / 0" in str(
        PytestTraceback(
            ExceptionRecord("ValueError", "builtins", "bad", frames=(restored,))
        )
    )


def test_walk_includes_group_children_and_their_chains() -> None:
    cause = ExceptionRecord("KeyError", "builtins", "cause")
    child = ExceptionRecord("ValueError", "builtins", "child", cause=cause)
    parent = ExceptionRecord("ExceptionGroup", "builtins", "group", children=(child,))
    assert list(parent.walk()) == [parent, child, cause]


@pytest.mark.parametrize("style", ["long", "short", "line", "native", "rich"])
@pytest.mark.parametrize("hidden", [False, True])
def test_sections_survive_every_rendering_entrypoint(
    style: TracebackStyle, hidden: bool
) -> None:
    record = ExceptionRecord(
        "ValueError",
        "builtins",
        "bad",
        frames=(frame(hidden=hidden),),
        sections=(("worker output", "captured at worker", "-"),),
    )
    renderer = PytestTraceback(record, style=style)
    renderer.addsection("controller output", "captured at controller", "=")
    for rendered in [str(renderer), str(renderer.to_repr()), rich_text(renderer)]:
        assert "captured at worker" in rendered
        assert "captured at controller" in rendered
        assert "ValueError: bad" in rendered
    if hidden and style in ("rich", "long", "short"):
        assert "All traceback entries are hidden" in str(renderer)
        assert "All traceback entries are hidden" in rich_text(renderer)


def test_line_rendering_without_frames() -> None:
    renderer = PytestTraceback(
        ExceptionRecord("ValueError", "builtins", "no traceback"), style="line"
    )
    renderer.addsection("output", "captured content")
    for rendered in [str(renderer), rich_text(renderer)]:
        assert "ValueError: no traceback" in rendered
        assert "captured content" in rendered


@pytest.mark.parametrize("style", ["long", "short"])
def test_record_with_unavailable_source_range(style: TracebackStyle) -> None:
    record = ExceptionRecord(
        "ValueError", "builtins", "bad", frames=(frame(lineno=100),)
    )
    rendered = str(PytestTraceback(record, style=style))
    assert "???" in rendered
    assert "snapshot.py:100" in rendered


def test_rendering_without_column_positions() -> None:
    record = ExceptionRecord(
        "ValueError", "builtins", "bad", frames=(frame(colno=None, end_colno=None),)
    )
    rendered = str(PytestTraceback(record))
    assert "return 1 / 0" in rendered
    assert "^" not in rendered


@pytest.mark.parametrize("recursion_index", [None, 1])
def test_recorded_recursion_elision(recursion_index: int | None) -> None:
    frames = tuple(frame(path=f"frame_{i}.py") for i in range(4))
    record = ExceptionRecord(
        "RecursionError",
        "builtins",
        "recursive call",
        frames=frames,
        recursion_index=recursion_index,
    )
    rendered = str(PytestTraceback(record))
    assert "frame_0.py" in rendered
    if recursion_index is None:
        assert "frame_3.py" in rendered
    else:
        assert "frame_3.py" not in rendered
        assert "Recursion detected" in rendered


def test_rich_frame_limit_preserves_first_and_last_frames() -> None:
    record = ExceptionRecord(
        "ValueError",
        "builtins",
        "bad",
        frames=tuple(frame(path=f"frame_{i}.py") for i in range(105)),
    )
    rendered = str(PytestTraceback(record, style="rich"))
    assert "5 frames hidden" in rendered
    assert "frame_0.py" in rendered
    assert "frame_104.py" in rendered
    assert "frame_52.py" not in rendered


def test_rich_frame_with_no_source_or_locals() -> None:
    record = ExceptionRecord(
        "ValueError", "builtins", "bad", frames=(frame(statement=()),)
    )
    rendered = str(PytestTraceback(record, style="rich"))
    assert "snapshot.py:2" in rendered
    assert "ValueError: bad" in rendered


def test_native_group_children_keep_their_chains_and_positions() -> None:
    cause = ExceptionRecord("KeyError", "builtins", "cause", frames=(frame(),))
    child = ExceptionRecord("ValueError", "builtins", "child", cause=cause)
    group = ExceptionRecord(
        "ExceptionGroup", "builtins", "group", frames=(frame(),), children=(child,)
    )
    rendered = str(PytestTraceback(group, style="native"))
    if sys.version_info >= (3, 11):
        assert "^^^^^" in rendered
    assert "direct cause" in rendered
    assert "KeyError: cause" in rendered
    assert "ValueError: child" in rendered


@pytest.mark.parametrize("statement", [(), ("",)])
def test_native_group_with_missing_or_blank_source(statement: tuple[str, ...]) -> None:
    child = ExceptionRecord("ValueError", "builtins", "child")
    group = ExceptionRecord(
        "ExceptionGroup",
        "builtins",
        "group",
        frames=(frame(statement=statement, statement_lineno=2),),
        children=(child,),
    )
    assert "ValueError: child" in str(PytestTraceback(group, style="native"))


def test_rich_wide_separator_and_long_arguments() -> None:
    record = ExceptionRecord(
        "ValueError",
        "builtins",
        "bad",
        frames=(
            frame(args=(("short", "1"), ("long", repr("x" * 100)))),
            frame(repr_style="short"),
            frame(repr_style="long"),
        ),
    )
    renderer = PytestTraceback(record, funcargs=True)
    renderer.addsection("captured", "content")
    rendered = rich_text(renderer, width=81)
    assert "short = 1" in rendered
    assert "long =" in rendered
    assert "captured" in rendered
    assert "content" in rendered
    assert "_ _ _" in rendered


def test_rich_location_uses_first_message_line(monkeypatch: pytest.MonkeyPatch) -> None:
    from _pytest._code.code import ReprEntry
    from _pytest._code.code import ReprFileLocation

    location = ReprFileLocation("file.py", 2, "first\nsecond", _ispytest=True)
    renderer = PytestTraceback(
        ExceptionRecord("ValueError", "builtins", "bad", frames=(frame(),))
    )
    repr_obj = renderer.to_repr()
    entry = repr_obj.reprtraceback.reprentries[-1]
    assert isinstance(entry, ReprEntry)
    entry.reprfileloc = location
    monkeypatch.setattr(renderer, "to_repr", lambda: repr_obj)
    rendered = rich_text(renderer)
    assert "file.py:2: first" in rendered
    assert "second" not in rendered


def test_empty_and_legacy_doctest_locations() -> None:
    from _pytest._code.code import ReprFileLocation

    assert ReprFailDoctest([]).crash is None
    legacy = ReprFileLocation("doctest.txt", 3, "failure", _ispytest=True)
    assert ReprFailDoctest([(legacy, ["details"])]).crash == Location(
        "doctest.txt", 3, "failure"
    )


@pytest.mark.parametrize("kind", ["doctest", "fixture", "collect"])
def test_failure_records_ignore_incomplete_sections(kind: str) -> None:
    record: Any
    if kind == "doctest":
        record = ReprFailDoctest([(Location("test.txt", 3, "bad"), ["details"])])
    elif kind == "fixture":
        record = FixtureLookupErrorRepr("test.py", 2, [], "missing fixture", "missing")
    else:
        record = CollectErrorRepr("collection failed")
    data = record.to_dict()
    data["sections"] = [["incomplete"], ["output", "content", "-"]]
    if kind == "doctest":
        data["reprlocation_lines"].append(None)
    restored = type(record).from_dict(data)
    assert restored.sections == [("output", "content", "-")]
    assert "content" in rich_text(restored)


def test_empty_source_indentation_fallback() -> None:
    from _pytest._code.render import _getindent

    assert _getindent(Source()) == 0


def test_default_rendering_survives_an_unavailable_working_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from _pytest._code import render

    def unavailable(*args: Any) -> str:
        raise OSError("working directory removed")

    record = ExceptionRecord(
        "ValueError", "builtins", "bad", frames=(frame(abspath="/tmp/snapshot.py"),)
    )
    monkeypatch.setattr(render, "bestrelpath", unavailable)
    assert "/tmp/snapshot.py:2" in str(PytestTraceback(record))


@pytest.mark.parametrize(
    "notes", [None, {}, "invalid", b"invalid"], ids=["none", "mapping", "str", "bytes"]
)
def test_invalid_exception_notes_are_ignored(notes: Any) -> None:
    error = ValueError("bad")
    setattr(error, "__notes__", notes)
    with pytest.raises(ValueError) as excinfo:
        raise error
    assert excinfo.record().notes == ()


def test_unprintable_note_uses_safe_repr() -> None:
    class Note:
        def __str__(self) -> str:
            raise ValueError("broken note")

        def __repr__(self) -> str:
            return "<note repr>"

    error = ValueError("bad")
    setattr(error, "__notes__", [Note()])
    with pytest.raises(ValueError) as excinfo:
        raise error
    assert excinfo.record().notes == ("<note repr>",)


def test_legacy_httperror_missing_notes() -> None:
    from email.message import Message
    from urllib.error import HTTPError

    class LegacyHTTPError(HTTPError):
        def __getattr__(self, name: str) -> Any:
            if name == "__notes__":
                raise KeyError(name)
            return super().__getattr__(name)

    error = LegacyHTTPError("https://example.test", 404, "not found", Message(), None)
    assert not hasattr(error, "missing_field")
    with pytest.raises(HTTPError) as excinfo:
        raise error
    if sys.version_info < (3, 12):
        assert excinfo.record().notes == ()
    else:
        with pytest.raises(KeyError, match="__notes__"):
            excinfo.record()


def test_unknown_exception_module(monkeypatch: pytest.MonkeyPatch) -> None:
    class UnknownError(Exception):
        pass

    monkeypatch.setattr(UnknownError, "__module__", None)
    with pytest.raises(UnknownError) as excinfo:
        raise UnknownError("bad")
    assert excinfo.record().type_module == "<unknown>"


def test_capture_when_relative_path_resolution_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from _pytest._code import code

    with pytest.raises(ValueError) as excinfo:
        raise ValueError("bad")

    def unavailable(*args: Any) -> str:
        raise OSError("working directory removed")

    monkeypatch.setattr(code, "bestrelpath", unavailable)
    assert excinfo.record().frames[-1].path == str(Path(__file__))


def test_capture_keeps_builtins_as_a_placeholder() -> None:
    namespace: dict[str, Any] = {}
    with pytest.raises(ValueError) as excinfo:
        exec('raise ValueError("bad")', namespace)
    snapshot = excinfo.record(showlocals=True).frames[-1]
    assert snapshot.locals is not None
    assert snapshot.locals["__builtins__"] == "<builtins>"


def test_exconly_single_nested_exception_group() -> None:
    if sys.version_info < (3, 11):
        from exceptiongroup import ExceptionGroup
    else:
        from builtins import ExceptionGroup

    with pytest.raises(ExceptionGroup) as excinfo:
        raise ExceptionGroup("outer", [ExceptionGroup("inner", [ValueError("bad")])])
    assert (
        excinfo.exconly(tryshort=True)
        == "ValueError('bad') [single exception in ExceptionGroup]"
    )


@pytest.mark.parametrize("metadata", ["globals", "locals", "positions"])
def test_capture_degrades_when_frame_metadata_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    metadata: str,
) -> None:
    from types import SimpleNamespace

    from _pytest._code.code import Frame
    from _pytest._code.code import TracebackEntry

    with pytest.raises(ValueError) as excinfo:
        raise ValueError("bad")

    def unavailable(*args: Any) -> Any:
        raise ValueError("metadata unavailable")

    with monkeypatch.context() as patch:
        if metadata == "globals":
            patch.setattr(Frame, "f_globals", property(unavailable))
        elif metadata == "locals":
            patch.setattr(TracebackEntry, "locals", property(unavailable))
        else:
            patch.setattr(
                TracebackEntry,
                "get_python_framesummary",
                lambda entry: SimpleNamespace(
                    lineno=None, end_lineno=None, colno=None, end_colno=None
                ),
            )
        record = excinfo.record(showlocals=True, tbfilter=lambda info: info.traceback)
    assert record.message == "bad"
    last = record.frames[-1]
    assert last.lineno == excinfo.traceback[-1].lineno + 1
    if metadata == "globals":
        assert last.module is None
    elif metadata == "locals":
        assert last.locals == {}
    else:
        assert last.end_lineno is None
        assert last.colno is None


def test_capture_source_changed_to_invalid_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from _pytest._code import code
    from _pytest._code.code import TracebackEntry

    with pytest.raises(ValueError) as excinfo:
        raise ValueError("bad")

    def invalid_source(*args: Any, **kwargs: Any) -> Any:
        raise SyntaxError("file edited during capture")

    monkeypatch.setattr(code, "getstatementrange_ast", invalid_source)
    monkeypatch.setattr(
        TracebackEntry,
        "get_python_framesummary",
        lambda entry: SimpleNamespace(
            lineno=None, end_lineno=None, colno=None, end_colno=None
        ),
    )
    record = excinfo.record()
    assert "raise ValueError" in record.frames[-1].statement[-1]


def test_source_indentation_preserves_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from _pytest._code.render import _getindent

    def interrupt(*args: Any) -> Any:
        raise KeyboardInterrupt

    monkeypatch.setattr(Source, "getstatement", interrupt)
    with pytest.raises(KeyboardInterrupt):
        _getindent(Source("pass"))


def test_source_indentation_fallback_preserves_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from _pytest._code.render import _getindent

    def invalid(*args: Any) -> Any:
        raise ValueError("source unavailable")

    def interrupt(*args: Any) -> Any:
        raise KeyboardInterrupt

    monkeypatch.setattr(Source, "getstatement", invalid)
    monkeypatch.setattr(Source, "__getitem__", interrupt)
    with pytest.raises(KeyboardInterrupt):
        _getindent(Source("pass"))


@pytest.mark.parametrize("style", ["no", "value"])
@pytest.mark.parametrize("hidden", [False, True])
def test_legacy_formatter_compact_styles(style: TracebackStyle, hidden: bool) -> None:
    from _pytest._code.code import ExceptionInfoFormatter

    __tracebackhide__ = hidden
    with pytest.raises(ValueError) as excinfo:
        raise ValueError("compact failure")
    rendered = str(ExceptionInfoFormatter(style=style).repr_traceback(excinfo))
    assert "compact failure" in rendered
    if hidden:
        assert "All traceback entries are hidden" in rendered


def test_empty_legacy_entry_and_oversized_arguments_render_consistently() -> None:
    from rich.console import Group

    from _pytest._code.code import ReprEntry
    from _pytest._code.code import ReprFileLocation
    from _pytest._code.code import ReprFuncArgs
    from _pytest._io import TerminalWriter

    renderer = PytestTraceback(ExceptionRecord("ValueError", "builtins", "bad"))
    location = ReprFileLocation("file.py", 2, "failure", _ispytest=True)
    arguments = ReprFuncArgs([("long", repr("x" * 100))], _ispytest=True)
    entry = ReprEntry([], arguments, None, location, "long", _ispytest=True)
    rendered = rich_text(Group(*renderer._render_entry_rich(entry, width=40)))
    assert "file.py:2: failure" in rendered
    assert "long =" in rendered
    assert "file.py:2: failure" in str(entry)
    output = io.StringIO()
    entry.toterminal(TerminalWriter(output))
    assert "file.py:2: failure" in output.getvalue()


@pytest.mark.parametrize("style", ["auto", "short", "rich"])
@pytest.mark.parametrize("full_trace", [False, True])
def test_node_default_style_selection(
    pytester: Pytester, style: str, full_trace: bool
) -> None:
    item = pytester.getitem("def test_func(): pass")
    item.config.option.tbstyle = style
    item.config.option.fulltrace = full_trace
    with pytest.raises(ValueError) as excinfo:
        raise ValueError("style selection")
    explicit_style: TracebackStyle | None = (
        "rich" if full_trace and style == "rich" else None
    )
    rendered = str(item._repr_failure_py(excinfo, style=explicit_style))
    assert "ValueError: style selection" in rendered
    if style == "rich":
        assert "Traceback (most recent call last)" in rendered


def test_legacy_report_roundtrip_without_an_attached_record() -> None:
    from _pytest._code.code import ReprExceptionInfo
    from _pytest._code.code import ReprTracebackNative
    from _pytest.reports import TestReport

    representation = ReprExceptionInfo(
        ReprTracebackNative(["ValueError: legacy plugin\n"], _ispytest=True),
        None,
        _ispytest=True,
    )
    report = TestReport(
        nodeid="test.py::test",
        location=("test.py", 0, "test"),
        keywords={},
        outcome="failed",
        longrepr=representation,
        when="call",
    )
    wire = json.loads(json.dumps(report._to_json()))
    assert "record" not in wire["longrepr"]
    restored = TestReport._from_json(wire)
    assert restored.longreprtext == report.longreprtext


def test_group_with_a_cyclic_children_property() -> None:
    if sys.version_info < (3, 11):
        from exceptiongroup import ExceptionGroup
    else:
        from builtins import ExceptionGroup

    class CyclicGroup(ExceptionGroup[Exception]):
        @property
        def exceptions(self) -> tuple[Exception, ...]:
            return (self,)

    with pytest.raises(CyclicGroup) as excinfo:
        raise CyclicGroup("cycle", [ValueError("child")])
    record = excinfo.record()
    assert record.children == ()
    assert ExceptionRecord.from_dict(json.loads(json.dumps(record.to_dict()))) == record


@pytest.mark.parametrize("statement", [("", ""), ("   ", "   ")])
def test_native_traceback_with_blank_source(statement: tuple[str, ...]) -> None:
    record = ExceptionRecord(
        "ValueError", "builtins", "bad", frames=(frame(statement=statement),)
    )
    rendered = str(PytestTraceback(record, style="native"))
    assert "ValueError: bad" in rendered
    assert "snapshot.py" in rendered
