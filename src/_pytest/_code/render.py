from __future__ import annotations

import dataclasses
from io import StringIO
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from _pytest._code.code import _byte_offset_to_character_offset
from _pytest._code.code import ExceptionChainRepr
from _pytest._code.code import ReprEntry
from _pytest._code.code import ReprEntryNative
from _pytest._code.code import ReprExceptionInfo
from _pytest._code.code import ReprFileLocation
from _pytest._code.code import ReprFuncArgs
from _pytest._code.code import ReprLocals
from _pytest._code.code import ReprTraceback
from _pytest._code.code import ReprTracebackNative
from _pytest._code.code import TracebackStyle
from _pytest._code.record import ExceptionRecord
from _pytest._code.record import FrameRecord
from _pytest._code.source import deindent
from _pytest._code.source import Source
from _pytest._io import TerminalWriter
from _pytest.pathlib import bestrelpath


if TYPE_CHECKING:
    from rich.console import Console
    from rich.console import ConsoleOptions
    from rich.console import RenderResult


_ALL_HIDDEN_MSG = (
    "All traceback entries are hidden. "
    "Pass `--full-trace` to see hidden and internal frames."
)


def _getindent(source: Source) -> int:
    try:
        s = str(source.getstatement(len(source) - 1))
    except KeyboardInterrupt:
        raise
    except BaseException:
        try:
            s = str(source[-1])
        except KeyboardInterrupt:
            raise
        except BaseException:
            return 0
    return 4 + (len(s) - len(s.lstrip()))


def _highlight_arrows_for_line(
    *,
    line: str,
    raw_line: str,
    lineno: int | None,
    end_lineno: int | None,
    colno: int | None,
    end_colno: int | None,
) -> list[str]:
    if lineno != end_lineno:
        return []
    if colno is None or end_colno is None:
        return []

    num_stripped_chars = len(raw_line) - len(line)
    start_char_offset = _byte_offset_to_character_offset(raw_line, colno)
    end_char_offset = _byte_offset_to_character_offset(raw_line, end_colno)
    num_carets = end_char_offset - start_char_offset
    if num_carets >= len(line.strip()):
        return []

    highlights = "    "
    highlights += " " * (start_char_offset - num_stripped_chars + 1)
    highlights += "^" * num_carets
    return [highlights]


def _format_native_record_lines(
    rec: ExceptionRecord,
    *,
    show_hidden: bool,
    indent_prefix: str = "",
) -> list[str]:
    """Format an :class:`ExceptionRecord` in stdlib native / ExceptionGroup style."""
    lines: list[str] = []
    visible_frames = (
        list(rec.frames) if show_hidden else [f for f in rec.frames if not f.hidden]
    )

    if rec.children:
        if visible_frames:
            lines.append(
                f"{indent_prefix}  + Exception Group Traceback (most recent call last):\n"
            )
            for f in visible_frames:
                fname = f.abspath or f.path
                lines.append(
                    f'{indent_prefix}  |   File "{fname}", line {f.lineno}, in {f.short_function_name}\n'
                )
                line_idx = f.lineno - f.statement_lineno
                if 0 <= line_idx < len(f.statement):
                    raw_line = f.statement[line_idx]
                    stripped = raw_line.strip()
                    if stripped:
                        lines.append(f"{indent_prefix}  |     {stripped}\n")
                        if (
                            sys.version_info >= (3, 11)
                            and f.lineno == f.end_lineno
                            and f.colno is not None
                            and f.end_colno is not None
                        ):
                            carets = _highlight_arrows_for_line(
                                line=stripped,
                                raw_line=raw_line,
                                lineno=f.lineno,
                                end_lineno=f.end_lineno,
                                colno=f.colno,
                                end_colno=f.end_colno,
                            )
                            for c in carets:
                                lines.append(f"{indent_prefix}  | {c}\n")
        for exline in rec.exconly(tryshort=False).splitlines():
            lines.append(f"{indent_prefix}  | {exline}\n")

        for idx, child in enumerate(rec.children, 1):
            header = f"{idx:^18}" if idx >= 10 else f" {idx} ".center(36, "-")
            if idx == 1:
                lines.append(f"{indent_prefix}  +-+{header}\n")
            else:
                lines.append(f"{indent_prefix}    +{header}\n")
            child_chain = list(child.iter_chain())
            for chain_rec, chain_desc in child_chain:
                lines.extend(
                    _format_native_record_lines(
                        chain_rec,
                        show_hidden=show_hidden,
                        indent_prefix=indent_prefix + "  |",
                    )
                )
                if chain_desc is not None:
                    lines.append(f"{indent_prefix}    |\n")
                    lines.append(f"{indent_prefix}    | {chain_desc}\n")
                    lines.append(f"{indent_prefix}    |\n")
        lines.append(f"{indent_prefix}    +------------------------------------\n")
        return lines

    body_prefix = f"{indent_prefix}  " if indent_prefix else ""
    if visible_frames:
        lines.append(f"{body_prefix}Traceback (most recent call last):\n")
        for f in visible_frames:
            fname = f.abspath or f.path
            lines.append(
                f'{body_prefix}  File "{fname}", line {f.lineno}, in {f.short_function_name}\n'
            )
            line_idx = f.lineno - f.statement_lineno
            if 0 <= line_idx < len(f.statement):
                raw_line = f.statement[line_idx]
                stripped = raw_line.strip()
                if stripped:
                    lines.append(f"{body_prefix}    {stripped}\n")
                    if (
                        sys.version_info >= (3, 11)
                        and f.lineno == f.end_lineno
                        and f.colno is not None
                        and f.end_colno is not None
                    ):
                        carets = _highlight_arrows_for_line(
                            line=stripped,
                            raw_line=raw_line,
                            lineno=f.lineno,
                            end_lineno=f.end_lineno,
                            colno=f.colno,
                            end_colno=f.end_colno,
                        )
                        for c in carets:
                            lines.append(f"{body_prefix}{c}\n")

    for exline in rec.exconly(tryshort=False).splitlines():
        lines.append(f"{body_prefix}{exline}\n")
    return lines


@dataclasses.dataclass
class PytestTraceback:
    """Rich renderable and TerminalWriter renderer over an :class:`ExceptionRecord`."""

    flow_marker: str = dataclasses.field(default=">", init=False, repr=False)
    fail_marker: str = dataclasses.field(default="E", init=False, repr=False)

    record: ExceptionRecord
    style: TracebackStyle = "long"
    showlocals: bool = False
    abspath: bool = False
    chain: bool = True
    truncate_locals: bool = True
    truncate_args: bool = True
    funcargs: bool = False
    show_hidden: bool = False
    sections: list[tuple[str, str, str]] = dataclasses.field(
        default_factory=list, repr=False
    )

    def addsection(self, name: str, content: str, sep: str = "-") -> None:
        self.sections.append((name, content, sep))

    def _all_sections(self) -> list[tuple[str, str, str]]:
        return [*self.record.sections, *self.sections]

    def _makepath(self, frame: FrameRecord) -> str:
        if self.abspath:
            return frame.abspath or frame.path
        if frame.abspath is not None:
            abs_path = Path(frame.abspath)
            try:
                np = bestrelpath(Path.cwd(), abs_path)
            except OSError:
                return frame.abspath
            if len(np) < len(frame.abspath):
                return np
            return frame.abspath
        return frame.path

    def _make_reprcrash(self, rec: ExceptionRecord) -> ReprFileLocation | None:
        loc = rec.crash
        if loc is None:
            return None
        return ReprFileLocation(loc.path, loc.lineno, loc.message)

    def _get_exconly_lines(
        self,
        rec: ExceptionRecord,
        *,
        indent: int = 4,
        markall: bool = False,
    ) -> list[str]:
        lines: list[str] = []
        indentstr = " " * indent
        exlines = rec.exconly(tryshort=True).split("\n")
        failindent = self.fail_marker + indentstr[1:]
        for line in exlines:
            lines.append(failindent + line)
            if not markall:
                failindent = indentstr
        return lines

    def _format_frame_source(
        self,
        frame: FrameRecord,
        *,
        rec_if_last: ExceptionRecord | None,
        short: bool,
    ) -> list[str]:
        lines: list[str] = []
        if not frame.statement:
            raw_lines = ["???"]
            deindented_lines = ["???"]
            line_index = 0
            end_line_index: int | None = None
            colno: int | None = None
            end_colno: int | None = None
        else:
            raw_lines = list(frame.statement)
            deindented_lines = deindent(raw_lines)
            line_index = frame.lineno - frame.statement_lineno
            if line_index < 0 or line_index >= len(deindented_lines):
                raw_lines = ["???"]
                deindented_lines = ["???"]
                line_index = 0
                end_line_index = None
                colno = None
                end_colno = None
            else:
                end_line_index = (
                    frame.end_lineno - frame.statement_lineno
                    if frame.end_lineno is not None
                    else None
                )
                colno = frame.colno
                end_colno = frame.end_colno

        space_prefix = "    "
        if short:
            stripped_line = deindented_lines[line_index].strip()
            lines.append(space_prefix + stripped_line)
            lines.extend(
                _highlight_arrows_for_line(
                    raw_line=raw_lines[line_index],
                    line=stripped_line,
                    lineno=line_index,
                    end_lineno=end_line_index,
                    colno=colno,
                    end_colno=end_colno,
                )
            )
        else:
            for line in deindented_lines[:line_index]:
                lines.append(space_prefix + line)
            lines.append(self.flow_marker + "   " + deindented_lines[line_index])
            lines.extend(
                _highlight_arrows_for_line(
                    raw_line=raw_lines[line_index],
                    line=deindented_lines[line_index],
                    lineno=line_index,
                    end_lineno=end_line_index,
                    colno=colno,
                    end_colno=end_colno,
                )
            )
            for line in deindented_lines[line_index + 1 :]:
                lines.append(space_prefix + line)

        if rec_if_last is not None:
            indent = 4 if short else _getindent(Source(deindented_lines))
            lines.extend(
                self._get_exconly_lines(rec_if_last, indent=indent, markall=True)
            )
        return lines

    def _repr_frame_entry(
        self,
        frame: FrameRecord | None,
        rec_if_last: ExceptionRecord | None,
        effective_style: TracebackStyle,
    ) -> ReprEntry:
        lines: list[str] = []
        style: TracebackStyle = (
            frame.repr_style
            if frame is not None and frame.repr_style is not None
            else effective_style
        )
        if style == "auto":
            style = "long"

        if style in ("short", "long") and frame is not None:
            short = style == "short"
            reprargs: ReprFuncArgs | None = None
            if not short and self.funcargs and frame.args is not None:
                reprargs = ReprFuncArgs(list(frame.args))

            lines.extend(
                self._format_frame_source(
                    frame,
                    rec_if_last=rec_if_last,
                    short=short,
                )
            )
            if short:
                message = f"in {frame.short_function_name}"
            else:
                message = rec_if_last.short_type_name if rec_if_last is not None else ""
            path = self._makepath(frame)
            reprfileloc = ReprFileLocation(path, frame.lineno, message)
            localsrepr: ReprLocals | None = None
            if self.showlocals and frame.locals is not None:
                local_lines = [
                    f"{name:<10} = {val}" for name, val in frame.locals.items()
                ]
                localsrepr = ReprLocals(local_lines)
            return ReprEntry(lines, reprargs, localsrepr, reprfileloc, style)
        elif style == "value":
            if rec_if_last is not None:
                lines.extend(rec_if_last.message.split("\n"))
            return ReprEntry(lines, None, None, None, style)
        else:
            if rec_if_last is not None:
                lines.extend(self._get_exconly_lines(rec_if_last, indent=4))
            return ReprEntry(lines, None, None, None, style)

    def _truncate_recursive_frames(
        self,
        rec: ExceptionRecord,
        frames: list[FrameRecord],
    ) -> tuple[list[FrameRecord], str | None]:
        max_frames = 10
        if rec.recursion_error is not None:
            extraline: str | None = (
                "!!! Recursion error detected, but an error occurred locating the origin of recursion.\n"
                "  The following exception happened when comparing locals in the stack frame:\n"
                f"    {rec.recursion_error}\n"
                f"  Displaying first and last {max_frames} stack frames out of {len(frames)}."
            )
            frames = frames[:max_frames] + frames[-max_frames:]
        elif rec.recursion_index is not None:
            extraline = "!!! Recursion detected (same locals & position)"
            frames = frames[: rec.recursion_index + 1]
        elif not self.show_hidden and len(frames) > 2 * max_frames:
            extraline = (
                "!!! Recursion error detected, but the origin of the recursion "
                "could not be located.\n"
                f"  Displaying first and last {max_frames} stack frames out of {len(frames)}.\n"
                "  Pass `--full-trace` to see all frames."
            )
            frames = frames[:max_frames] + frames[-max_frames:]
        else:
            extraline = None
        return frames, extraline

    def _repr_traceback_for_record(self, rec: ExceptionRecord) -> ReprTraceback:
        visible_frames = (
            list(rec.frames)
            if self.show_hidden
            else [f for f in rec.frames if not f.hidden]
        )

        if rec.short_type_name == "RecursionError" or rec.recursion_index is not None:
            visible_frames, extraline = self._truncate_recursive_frames(
                rec, visible_frames
            )
        else:
            extraline = None

        effective_tb_style: TracebackStyle = (
            "long" if self.style == "auto" else self.style
        )

        if not visible_frames:
            if extraline is None:
                extraline = _ALL_HIDDEN_MSG
            entries = [self._repr_frame_entry(None, rec, effective_tb_style)]
            return ReprTraceback(entries, extraline, style=effective_tb_style)

        if self.style == "value":
            entries = [self._repr_frame_entry(visible_frames[-1], rec, "value")]
            return ReprTraceback(entries, None, style="value")

        entries = []
        n_frames = len(visible_frames)
        for idx, frame in enumerate(visible_frames):
            is_last = idx == n_frames - 1
            entry_default_style = effective_tb_style
            if (
                self.style == "auto"
                and n_frames > 2
                and 0 < idx < n_frames - 1
                and frame.repr_style is None
            ):
                entry_default_style = "short"
            entries.append(
                self._repr_frame_entry(
                    frame,
                    rec if is_last else None,
                    entry_default_style,
                )
            )
        return ReprTraceback(entries, extraline, style=effective_tb_style)

    def _iter_chain_records(self) -> list[tuple[ExceptionRecord, str | None]]:
        if not self.chain:
            return [(self.record, None)]
        return list(self.record.iter_chain())

    def _render_rich_to_lines(self, width: int = 100) -> list[str]:
        from rich.console import Console
        from rich.traceback import Traceback as RichTraceback

        buf = StringIO()
        console = Console(
            file=buf,
            width=width,
            force_terminal=False,
            color_system=None,
        )
        tb = RichTraceback(
            trace=self.record.to_rich_trace(show_hidden=self.show_hidden),
            show_locals=self.showlocals,
            width=width,
        )
        console.print(tb)
        return buf.getvalue().splitlines(keepends=True)

    def to_repr(self) -> ReprExceptionInfo | ExceptionChainRepr:
        """Build a legacy :class:`ReprExceptionInfo` or :class:`ExceptionChainRepr` from the record."""
        if self.style == "native":
            native_lines: list[str] = []
            for rec, desc in self._iter_chain_records():
                native_lines.extend(
                    _format_native_record_lines(rec, show_hidden=self.show_hidden)
                )
                if desc is not None:
                    native_lines.append(f"\n{desc}\n\n")
            res_native = ReprExceptionInfo(
                reprtraceback=ReprTracebackNative(native_lines),
                reprcrash=self._make_reprcrash(self.record),
            )
            for name, content, sep in self._all_sections():
                res_native.addsection(name, content, sep)
            return res_native

        if self.style == "rich":
            visible_frames = (
                list(self.record.frames)
                if self.show_hidden
                else [f for f in self.record.frames if not f.hidden]
            )
            extraline = (
                _ALL_HIDDEN_MSG if (self.record.frames and not visible_frames) else None
            )
            rich_lines = self._render_rich_to_lines()
            res_rich = ReprExceptionInfo(
                reprtraceback=ReprTracebackNative(rich_lines, extraline=extraline),
                reprcrash=self._make_reprcrash(self.record),
            )
            for name, content, sep in self._all_sections():
                res_rich.addsection(name, content, sep)
            return res_rich

        repr_chain: list[tuple[ReprTraceback, ReprFileLocation | None, str | None]] = []
        for rec, description in self._iter_chain_records():
            if rec.children:
                visible = (
                    list(rec.frames)
                    if self.show_hidden
                    else [f for f in rec.frames if not f.hidden]
                )
                extraline = _ALL_HIDDEN_MSG if (rec.frames and not visible) else None
                group_lines = _format_native_record_lines(
                    rec, show_hidden=self.show_hidden
                )
                reprtraceback: ReprTraceback = ReprTracebackNative(
                    group_lines, extraline=extraline
                )
                reprcrash = self._make_reprcrash(rec)
            elif rec.frames or rec is self.record:
                reprtraceback = self._repr_traceback_for_record(rec)
                reprcrash = self._make_reprcrash(rec)
            else:
                no_tb_lines = [
                    f"{line}\n" for line in rec.exconly(tryshort=False).splitlines()
                ]
                reprtraceback = ReprTracebackNative(no_tb_lines)
                reprcrash = None

            repr_chain.append((reprtraceback, reprcrash, description))

        chain_repr = ExceptionChainRepr(repr_chain)
        for name, content, sep in self._all_sections():
            chain_repr.addsection(name, content, sep)
        return chain_repr

    def toterminal(self, tw: TerminalWriter) -> None:
        if self.style == "rich":
            from rich.console import Console
            from rich.traceback import Traceback as RichTraceback

            visible_frames = (
                list(self.record.frames)
                if self.show_hidden
                else [f for f in self.record.frames if not f.hidden]
            )
            buf = StringIO()
            console = Console(
                file=buf,
                width=tw.fullwidth,
                force_terminal=tw.hasmarkup,
                no_color=not tw.hasmarkup,
                color_system="standard" if tw.hasmarkup else None,
            )
            tb = RichTraceback(
                trace=self.record.to_rich_trace(show_hidden=self.show_hidden),
                show_locals=self.showlocals,
                width=tw.fullwidth,
            )
            console.print(tb)
            tw.write_raw(buf.getvalue())
            if self.record.frames and not visible_frames:
                tw.line(_ALL_HIDDEN_MSG)
            for name, content, sep in self._all_sections():
                tw.sep(sep, name)
                tw.line(content)
            return

        if self.style == "line":
            crash = self.record.crash
            if crash is not None:
                tw.line(str(crash))
            else:
                tw.line(self.record.exconly(tryshort=True))
            for name, content, sep in self._all_sections():
                tw.sep(sep, name)
                tw.line(content)
            return

        self.to_repr().toterminal(tw)

    def __str__(self) -> str:
        io = StringIO()
        tw = TerminalWriter(file=io)
        self.toterminal(tw)
        return io.getvalue().strip()

    def _render_entry_rich(
        self,
        entry: ReprEntry | ReprEntryNative,
        *,
        width: int,
    ) -> RenderResult:
        from rich.syntax import Syntax
        from rich.text import Text

        if isinstance(entry, ReprEntryNative):
            yield Text("".join(entry.lines).rstrip("\n"))
            return

        if entry.style == "value":
            for line in entry.lines:
                yield Text(line)
            return

        def render_entry_lines() -> RenderResult:
            if not entry.lines:
                return
            fail_prefix = f"{self.fail_marker}   "
            indent_size = len(fail_prefix)
            source_items: list[tuple[str, str]] = []
            failure_lines: list[str] = []
            for idx, line in enumerate(entry.lines):
                if line.startswith(fail_prefix):
                    failure_lines.extend(entry.lines[idx:])
                    break
                source_items.append((line[:indent_size], line[indent_size:]))

            for indent_str, code_line in source_items:
                syntax = Syntax(
                    code_line,
                    "python",
                    theme="ansi_dark",
                    background_color="default",
                )
                highlighted = syntax.highlight(code_line)
                highlighted.rstrip()
                prefix_style = "bold" if indent_str.startswith(self.flow_marker) else ""
                yield Text.assemble((indent_str, prefix_style), highlighted)

            for fline in failure_lines:
                yield Text(fline, style="bold red")

        def render_fileloc(loc: ReprFileLocation) -> Text:
            msg = loc.message
            i = msg.find("\n")
            if i != -1:
                msg = msg[:i]
            return Text.assemble((loc.path, "bold red"), f":{loc.lineno}: {msg}")

        if entry.style == "short":
            if entry.reprfileloc is not None:
                yield render_fileloc(entry.reprfileloc)
            yield from render_entry_lines()
            if entry.reprlocals is not None:
                for lline in entry.reprlocals.lines:
                    yield Text("        " + lline)
            return

        if entry.reprfuncargs is not None and entry.reprfuncargs.args:
            linesofar = ""
            for name, value in entry.reprfuncargs.args:
                ns = f"{name} = {value}"
                if len(ns) + len(linesofar) + 2 > width:
                    if linesofar:
                        yield Text(linesofar)
                    linesofar = ns
                else:
                    linesofar = f"{linesofar}, {ns}" if linesofar else ns
            if linesofar:
                yield Text(linesofar)
            yield Text("")

        yield from render_entry_lines()

        if entry.reprlocals is not None:
            yield Text("")
            for lline in entry.reprlocals.lines:
                yield Text(lline)

        if entry.reprfileloc is not None:
            if entry.lines:
                yield Text("")
            yield render_fileloc(entry.reprfileloc)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        from rich.text import Text
        from rich.traceback import Traceback as RichTraceback

        width = options.max_width or 80

        if self.style == "rich":
            visible_frames = (
                list(self.record.frames)
                if self.show_hidden
                else [f for f in self.record.frames if not f.hidden]
            )
            yield RichTraceback(
                trace=self.record.to_rich_trace(show_hidden=self.show_hidden),
                show_locals=self.showlocals,
                width=width,
            )
            if self.record.frames and not visible_frames:
                yield Text(_ALL_HIDDEN_MSG)
            for name, content, sep in self._all_sections():
                yield Text(f"{sep * 10} {name} {sep * 10}")
                yield Text(content)
            return

        if self.style == "line":
            crash = self.record.crash
            if crash is not None:
                msg = crash.message.splitlines()[0] if crash.message else ""
                yield Text.assemble((crash.path, "bold red"), f":{crash.lineno}: {msg}")
            else:
                yield Text(self.record.exconly(tryshort=True), style="bold red")
            return

        repr_obj = self.to_repr()
        chains: Sequence_Chain = (
            repr_obj.chain
            if isinstance(repr_obj, ExceptionChainRepr)
            else [(repr_obj.reprtraceback, repr_obj.reprcrash, None)]
        )
        for reprtraceback, _reprcrash, description in chains:
            for i, entry in enumerate(reprtraceback.reprentries):
                if entry.style == "long":
                    yield Text("")
                yield from self._render_entry_rich(entry, width=width)
                if i < len(reprtraceback.reprentries) - 1:
                    next_entry = reprtraceback.reprentries[i + 1]
                    if entry.style == "long" or (
                        entry.style == "short" and next_entry.style == "long"
                    ):
                        sep_line = ReprTraceback.entrysep * (
                            width // len(ReprTraceback.entrysep)
                        )
                        if (
                            len(sep_line) + len(ReprTraceback.entrysep.rstrip())
                            <= width
                        ):
                            sep_line += ReprTraceback.entrysep.rstrip()
                        yield Text(sep_line)
            if reprtraceback.extraline:
                yield Text(reprtraceback.extraline)
            if description is not None:
                yield Text("")
                yield Text(description, style="yellow")

        for name, content, sep in repr_obj.sections:
            n = max((width - len(name) - 2) // (2 * len(sep)), 1)
            fill = sep * n
            yield Text(f"{fill} {name} {fill}")
            yield Text(content)


if TYPE_CHECKING:
    from collections.abc import Sequence

    Sequence_Chain = Sequence[tuple[ReprTraceback, ReprFileLocation | None, str | None]]
