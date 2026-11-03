from __future__ import annotations

import io
import json
from pathlib import Path
import pickle
import sys
from typing import Any

from _pytest._code import Code
from _pytest._code import ExceptionInfo
from _pytest._code import ExceptionRecord
from _pytest._code import Location
from _pytest._code import PytestTraceback
from _pytest._code import RECORD_SCHEMA_VERSION
from _pytest._code import Traceback
from _pytest._code import TracebackStyle
from _pytest._code.record import CAUSE_MESSAGE
from _pytest._code.record import CONTEXT_MESSAGE
from _pytest._code.record import MAX_STATEMENT_LINE_CHARS
from _pytest._code.record import MAX_STATEMENT_LINES
from _pytest._io import TerminalWriter
from _pytest.pytester import Pytester
import pytest


if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


def add_note(err: BaseException, msg: str) -> None:
    if sys.version_info < (3, 11):
        err.__notes__ = [*getattr(err, "__notes__", []), msg]  # type: ignore[attr-defined]
    else:
        err.add_note(msg)


class TestLocation:
    def test_unpacking_and_indexing(self) -> None:
        loc = Location(
            path=Path("foo/bar.py"),  # type: ignore[arg-type]
            lineno=42,
            message="ValueError: bad\ndetail",
        )
        assert loc.path == str(Path("foo/bar.py"))
        path, lineno, message = loc
        assert path == loc.path
        assert lineno == 42
        assert message == "ValueError: bad\ndetail"
        assert len(loc) == 3
        assert loc[0] == loc.path
        assert loc[1] == 42
        assert loc[2] == "ValueError: bad\ndetail"
        assert loc[:2] == (loc.path, 42)
        assert str(loc) == f"{loc.path}:42: ValueError: bad"

    def test_dict_and_pickle_roundtrip(self) -> None:
        loc = Location(path="test_mod.py", lineno=10, message="AssertionError")
        data = json.loads(json.dumps(loc.to_dict()))
        restored = Location.from_dict(data)
        assert restored == loc
        assert pickle.loads(pickle.dumps(loc)) == loc

    def test_toterminal(self, tw_mock: Any) -> None:
        loc = Location(path="mod.py", lineno=7, message="ValueError: line1\nline2")
        loc.toterminal(tw_mock)
        assert tw_mock.get_write_msg(0) == "mod.py"
        assert tw_mock.lines[1] == ":7: ValueError: line1"


class TestRecordCapture:
    def test_simple_exception_record(self) -> None:
        def inner(x: int) -> int:
            y = x + 1
            raise ValueError(f"bad {y}")

        with pytest.raises(ValueError) as excinfo:
            inner(4)

        record = excinfo.record(showlocals=True, funcargs=True)
        assert record.type_name.endswith("ValueError")
        assert record.type_module == "builtins"
        assert record.qualified_type_name == "ValueError"
        assert record.message == "bad 5"
        assert record.exconly() == "ValueError: bad 5"
        assert record.crash is not None
        assert record.crash.path == __file__
        assert record.crash.message == "ValueError: bad 5"

        last_frame = record.frames[-1]
        assert not last_frame.hidden
        assert last_frame.short_function_name == "inner"
        assert last_frame.module == __name__
        assert last_frame.args == (("x", "4"),)
        assert last_frame.locals is not None
        assert last_frame.locals["x"] == "4"
        assert last_frame.locals["y"] == "5"
        assert any("raise ValueError" in line for line in last_frame.statement)
        line_idx = last_frame.lineno - last_frame.statement_lineno
        assert "raise ValueError" in last_frame.statement[line_idx]
        if sys.version_info >= (3, 11):
            assert last_frame.end_lineno is not None
            assert last_frame.colno is not None
            assert last_frame.end_colno is not None

    def test_assertion_striptext_at_record_time(self) -> None:
        x = 1
        with pytest.raises(AssertionError) as excinfo:
            assert x == 2

        record = excinfo.record()
        assert record.striptext == "AssertionError: "
        assert record.exconly(tryshort=True) == "assert 1 == 2"
        assert record.exconly(tryshort=False) == "AssertionError: assert 1 == 2"
        assert record.crash is not None
        assert record.crash.message == "assert 1 == 2"

        with pytest.raises(AssertionError) as explicit_info:
            raise AssertionError("custom message")

        explicit_record = explicit_info.record()
        assert explicit_record.striptext == ""
        assert (
            explicit_record.exconly(tryshort=True) == "AssertionError: custom message"
        )

    def test_hidden_frames_and_repr_style(self) -> None:
        def leaf() -> None:
            raise RuntimeError("boom")

        def hidden_helper() -> None:
            __tracebackhide__ = True
            leaf()

        def caller() -> None:
            hidden_helper()

        with pytest.raises(RuntimeError) as excinfo:
            caller()

        excinfo.traceback = Traceback(
            entry.with_repr_style("short") if entry.name == "caller" else entry
            for entry in excinfo.traceback
        )
        record = excinfo.record()
        by_name = {f.short_function_name: f for f in record.frames}
        assert by_name["hidden_helper"].hidden is True
        assert by_name["leaf"].hidden is False
        assert by_name["caller"].hidden is False
        assert by_name["caller"].repr_style == "short"

    def test_all_frames_hidden_crash_is_none(self) -> None:
        __tracebackhide__ = True

        def hidden_only() -> None:
            __tracebackhide__ = True
            raise ValueError("hidden")

        try:
            hidden_only()
        except ValueError as e:
            excinfo = ExceptionInfo.from_exception(e)

        record = excinfo.record()
        assert all(f.hidden for f in record.frames)
        assert record.crash is None

    def test_cause_and_context_chain_and_cycles(self) -> None:
        def root() -> None:
            raise KeyError("k")

        def mid() -> None:
            try:
                root()
            except KeyError as e:
                raise ValueError("v") from e

        def outer() -> None:
            try:
                mid()
            except ValueError:
                raise RuntimeError("r")  # noqa: B904

        with pytest.raises(RuntimeError) as excinfo:
            outer()

        record = excinfo.record()
        assert record.type_name == "RuntimeError"
        assert record.context is not None
        assert record.context.type_name == "ValueError"
        assert record.context.cause is not None
        assert record.context.cause.type_name == "KeyError"

        chain_list = list(record.iter_chain())
        assert [r.type_name for r, _ in chain_list] == [
            "KeyError",
            "ValueError",
            "RuntimeError",
        ]
        assert chain_list[0][1] == CAUSE_MESSAGE
        assert chain_list[1][1] == CONTEXT_MESSAGE
        assert chain_list[2][1] is None

        walked = [r.type_name for r in record.walk()]
        assert walked == ["RuntimeError", "ValueError", "KeyError"]

        # Cycle safety
        e1 = ValueError("1")
        e2 = RuntimeError("2")
        e1.__cause__ = e2
        e2.__cause__ = e1
        try:
            raise e1
        except ValueError:
            cyc_info = ExceptionInfo.from_current()

        cyc_record = cyc_info.record()
        assert cyc_record.cause is not None
        assert cyc_record.cause.cause is None

    def test_suppress_context_and_no_chain(self) -> None:
        def fail() -> None:
            try:
                raise ValueError("inner")
            except ValueError:
                raise RuntimeError("outer") from None

        with pytest.raises(RuntimeError) as excinfo:
            fail()

        rec = excinfo.record()
        assert rec.suppress_context is True
        assert rec.context is None
        assert len(list(rec.iter_chain())) == 1

    def test_exception_group_children_and_notes(self) -> None:
        v_err = ValueError("bad value")
        add_note(v_err, "value note")
        t_err = TypeError("bad type")
        inner_group = ExceptionGroup("inner", [t_err])
        outer_group = ExceptionGroup("outer", [v_err, inner_group])
        add_note(outer_group, "outer note 1")
        add_note(outer_group, "outer note 2")

        with pytest.raises(ExceptionGroup) as excinfo:
            raise outer_group

        record = excinfo.record()
        assert record.notes == ("outer note 1", "outer note 2")
        assert len(record.children) == 2
        assert record.children[0].type_name == "ValueError"
        assert record.children[0].notes == ("value note",)
        assert record.children[1].children[0].type_name == "TypeError"

        # Single sub-exception group short summary format
        single_group = ExceptionGroup("wrapped", [ValueError("only one")])
        with pytest.raises(ExceptionGroup) as single_info:
            raise single_group
        single_rec = single_info.record()
        assert (
            single_rec.exconly(tryshort=True)
            == "ValueError('only one') [single exception in ExceptionGroup]"
        )

    def test_syntax_error_details(self) -> None:
        try:
            compile("x = (\n", "broken.py", "exec")
        except SyntaxError:
            excinfo = ExceptionInfo.from_current()

        record = excinfo.record()
        assert record.syntax_error is not None
        assert record.syntax_error.filename == "broken.py"
        assert record.syntax_error.lineno == 1
        assert "broken.py" in record.exconly()
        assert "SyntaxError" in record.exconly()

    def test_recursion_index_recorded_only_for_recursion_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def rec(n: int) -> None:
            if n < 5:
                n += 1
            rec(n)

        with pytest.raises(RecursionError) as rec_info:
            rec(0)
        rec_record = rec_info.record()
        assert rec_record.recursion_index is not None

        def non_rec() -> None:
            raise RuntimeError("normal")

        with pytest.raises(RuntimeError) as norm_info:
            non_rec()
        monkeypatch.delattr(Traceback, "recursionindex")
        norm_record = norm_info.record()
        assert norm_record.recursion_index is None

    def test_pathological_statement_bounding(self) -> None:
        long_expr = " + ".join(["1"] * (MAX_STATEMENT_LINE_CHARS // 2))
        body_lines = [f"    x_{i} = {i}" for i in range(MAX_STATEMENT_LINES + 50)]
        body_lines.append(f"    y = {long_expr}")
        body_lines.append("    raise ValueError(y)")
        code_str = "def huge():\n" + "\n".join(body_lines) + "\n"
        ns: dict[str, Any] = {}
        exec(compile(code_str, "<huge>", "exec"), ns)
        with pytest.raises(ValueError) as excinfo:
            ns["huge"]()

        # Even if source is from a real file, verify FrameRecord bounding logic directly:
        from _pytest._code.source import Source

        fake_source = Source(code_str)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                Code,
                "fullsource",
                property(lambda self: fake_source),
            )
            record = excinfo.record()

        last_frame = record.frames[-1]
        assert len(last_frame.statement) <= MAX_STATEMENT_LINES
        assert all(
            len(line) <= MAX_STATEMENT_LINE_CHARS + 3 for line in last_frame.statement
        )
        line_idx = last_frame.lineno - last_frame.statement_lineno
        assert 0 <= line_idx < len(last_frame.statement)
        assert "raise ValueError(y)" in last_frame.statement[line_idx]

    def test_to_dict_from_dict_and_pickle_roundtrip(self) -> None:
        def cause_fn() -> None:
            raise KeyError("missing_key")

        def group_fn() -> None:
            try:
                cause_fn()
            except KeyError as e:
                eg = ExceptionGroup("multi", [ValueError("v1"), TypeError("t1")])
                add_note(eg, "group note")
                raise eg from e

        with pytest.raises(ExceptionGroup) as excinfo:
            group_fn()

        record = excinfo.record(showlocals=True, funcargs=True)
        payload = record.to_dict()
        assert payload["schema_version"] == RECORD_SCHEMA_VERSION

        # Round-trip through JSON text
        json_str = json.dumps(payload)
        loaded_dict = json.loads(json_str)
        restored = ExceptionRecord.from_dict(loaded_dict)
        assert restored == record
        assert restored.to_dict() == payload

        # Round-trip through pickle
        unpickled = pickle.loads(pickle.dumps(record))
        assert unpickled == record

        # Record is hashable (even with locals captured) for xdist dict keys
        assert isinstance(hash(record), int)

        # Compatibility properties on ExceptionRecord
        assert record.reprcrash == record.crash
        assert record.reprtraceback is not None
        assert len(record.chain) >= 1

        # Unsupported schema version raises ValueError
        bad_payload = dict(payload, schema_version=999)
        with pytest.raises(ValueError, match="schema_version"):
            ExceptionRecord.from_dict(bad_payload)

    def test_to_rich_trace(self) -> None:
        from rich.console import Console
        from rich.traceback import Traceback as RichTraceback

        def cause_fn(a: int) -> None:
            local_var = a * 2
            raise ValueError(f"cause {local_var}")

        def main_fn() -> None:
            try:
                cause_fn(21)
            except ValueError as e:
                err = RuntimeError("top failure")
                add_note(err, "top-only note")
                raise err from e

        with pytest.raises(RuntimeError) as excinfo:
            main_fn()

        record = excinfo.record(showlocals=True)
        trace = record.to_rich_trace()
        assert len(trace.stacks) == 2
        assert trace.stacks[0].exc_type == "RuntimeError"
        assert trace.stacks[0].exc_value == "top failure"
        assert trace.stacks[0].notes == ["top-only note"]
        assert trace.stacks[1].exc_type == "ValueError"
        assert trace.stacks[1].exc_value == "cause 42"
        assert trace.stacks[1].is_cause is True
        # Outer notes must not leak onto chained stacks
        assert trace.stacks[1].notes == []

        buf = io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False, color_system=None)
        console.print(RichTraceback(trace=trace, show_locals=True))
        output = buf.getvalue()
        assert "ValueError: cause 42" in output
        assert (
            "The above exception was the direct cause of the following exception:"
            in output
        )
        assert "RuntimeError: top failure" in output
        assert "top-only note" in output
        assert "local_var" in output


class TestPytestTraceback:
    @pytest.mark.parametrize(
        "style",
        ("long", "short", "auto", "line", "no", "value", "native", "rich"),
    )
    def test_styles_render_and_parity(self, style: TracebackStyle) -> None:
        def leaf(x: int) -> None:
            y = x + 10
            assert y == 0, "expected zero"

        def caller() -> None:
            leaf(5)

        with pytest.raises(AssertionError) as excinfo:
            caller()

        record = excinfo.record(showlocals=True, funcargs=True)
        tb = PytestTraceback(record, style=style, showlocals=True)
        rendered = str(tb)

        if style == "no":
            assert "AssertionError: expected zero" in rendered
            assert "leaf" not in rendered
        elif style == "value":
            assert "expected zero" in rendered
        elif style == "line":
            assert f"{__file__}:" in rendered
            assert "AssertionError: expected zero" in rendered
        elif style in ("long", "short", "auto", "native", "rich"):
            assert "AssertionError" in rendered
            assert "expected zero" in rendered
            assert "leaf" in rendered

    def test_toterminal_long_matches_excinfo_getrepr(self, tw_mock: Any) -> None:
        __tracebackhide__ = True

        def g(x: int) -> None:
            raise ValueError(x)

        def f() -> None:
            g(3)

        with pytest.raises(ValueError) as excinfo:
            f()

        record = excinfo.record()
        tb = PytestTraceback(record, style="long")
        tb.toterminal(tw_mock)
        assert any("def f()" in str(line) for line in tw_mock.lines)
        assert any(">       g(3)" in str(line) for line in tw_mock.lines)
        assert any("E       ValueError: 3" in str(line) for line in tw_mock.lines)

    def test_record_toterminal_and_rich_console_protocol(self) -> None:
        from rich.console import Console

        def boom() -> None:
            raise RuntimeError("protocol test")

        with pytest.raises(RuntimeError) as excinfo:
            boom()

        record = excinfo.record()
        assert "RuntimeError: protocol test" in str(record)

        buf = io.StringIO()
        tw = TerminalWriter(file=buf)
        record.toterminal(tw)
        assert "RuntimeError: protocol test" in buf.getvalue()

        console_buf = io.StringIO()
        console = Console(
            file=console_buf, width=88, force_terminal=True, color_system="truecolor"
        )
        console.print(record)
        assert "RuntimeError: protocol test" in console_buf.getvalue()

    def test_to_repr_compat_shim(self) -> None:
        def inner() -> None:
            raise KeyError("k")

        def outer() -> None:
            try:
                inner()
            except KeyError as e:
                raise ValueError("v") from e

        with pytest.raises(ValueError) as excinfo:
            outer()

        record = excinfo.record(showlocals=True, funcargs=True)
        tb = PytestTraceback(record, style="long", showlocals=True)
        tb.addsection("Captured stdout", "hello world")
        repr_obj = tb.to_repr()
        assert repr_obj.reprcrash is not None
        assert repr_obj.reprcrash.message == "ValueError: v"
        assert ("Captured stdout", "hello world", "-") in repr_obj.sections
        text = str(repr_obj)
        assert "KeyError: 'k'" in text
        assert "ValueError: v" in text
        assert "The above exception was the direct cause" in text

    def test_tb_rich_cli(self, pytester: Pytester) -> None:
        pytester.makepyfile(
            """
            def helper(val):
                local_msg = f"bad {val}"
                raise ValueError(local_msg)

            def test_rich_failure():
                helper(42)
            """
        )
        result = pytester.runpytest("--tb=rich", "-l")
        assert result.ret == 1
        result.stdout.fnmatch_lines(
            [
                "*Traceback (most recent call last)*",
                "*in test_rich_failure*",
                "*in helper*",
                "*local_msg = 'bad 42'*",
                "*ValueError: bad 42*",
            ]
        )

    @pytest.mark.parametrize("tbstyle", ("long", "short", "line", "no"))
    def test_tb_style_preserves_frame_locations_and_record_14720(
        self, pytester: Pytester, tbstyle: str
    ) -> None:
        """Regression test for #14720: --tb=line and --tb=no must not lose frame locations or record data."""
        pytester.makepyfile(
            """
            def inner():
                raise ValueError("boom")

            def middle():
                inner()

            def test_a():
                middle()
            """
        )
        reprec = pytester.inline_run(f"--tb={tbstyle}")
        reports = [
            r for r in reprec.getreports("pytest_runtest_logreport") if r.when == "call"
        ]
        assert len(reports) == 1
        rep = reports[0]
        assert rep.failed
        longrepr = rep.longrepr
        assert longrepr is not None

        # 1. Existing plugins inspecting reprtraceback.reprentries[*].reprfileloc see all 3 located frames
        rt = getattr(longrepr, "reprtraceback", None)
        assert rt is not None
        entries = rt.reprentries
        assert len(entries) == 3
        located = [e for e in entries if getattr(e, "reprfileloc", None) is not None]
        assert len(located) == 3

        # 2. The full ExceptionRecord is attached to longrepr regardless of --tb
        record = getattr(longrepr, "record", None)
        assert isinstance(record, ExceptionRecord)
        visible_funcs = [f.short_function_name for f in record.frames if not f.hidden]
        assert visible_funcs == ["test_a", "middle", "inner"]
        assert all(f.statement for f in record.frames if not f.hidden)

        # 3. Under --tb=line and --tb=no, str(longrepr) stays compact
        if tbstyle in ("line", "no"):
            assert str(longrepr) == "E   ValueError: boom"
