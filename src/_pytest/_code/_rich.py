"""Rich traceback layout backed exclusively by captured frame source."""

from __future__ import annotations

from rich.columns import Columns
from rich.console import ConsoleRenderable
from rich.console import group
from rich.console import RenderResult
from rich.scope import render_scope
from rich.syntax import Syntax
from rich.text import Text
from rich.traceback import Stack
from rich.traceback import Trace
from rich.traceback import Traceback

from _pytest._code.code import _byte_offset_to_character_offset
from _pytest._code.record import ExceptionRecord
from _pytest._code.record import FrameRecord


class RecordedTraceback(Traceback):
    def __init__(
        self,
        record: ExceptionRecord,
        *,
        show_hidden: bool,
        chain: bool,
        show_locals: bool,
        width: int,
    ) -> None:
        trace = record.to_rich_trace(show_hidden=show_hidden, chain=chain)
        self._chain = chain
        super().__init__(trace=trace, show_locals=show_locals, width=width)
        self._sources: dict[int, FrameRecord] = {}
        self._bind_sources(record, trace, show_hidden=show_hidden)

    def _bind_sources(
        self, record: ExceptionRecord, trace: Trace, *, show_hidden: bool
    ) -> None:
        records = (
            list(reversed(list(record.iter_chain())))
            if self._chain
            else [(record, None)]
        )
        for (node, _), stack in zip(records, trace.stacks, strict=True):
            frames = [f for f in node.frames if show_hidden or not f.hidden]
            for frame, source in zip(stack.frames, frames, strict=True):
                self._sources[id(frame)] = source
            for child, child_trace in zip(node.children, stack.exceptions, strict=True):
                self._bind_sources(child, child_trace, show_hidden=show_hidden)

    @group()
    def _render_stack(self, stack: Stack) -> RenderResult:
        # Rich's default stack renderer reads linecache. Only the surrounding
        # layout is reused here; source and positions always come from the record.
        excluded = range(0)
        if self.max_frames and len(stack.frames) > self.max_frames:
            excluded = range(
                self.max_frames // 2, len(stack.frames) - self.max_frames // 2
            )
        for index, frame in enumerate(stack.frames):
            if index in excluded:
                if index == excluded.start:
                    yield Text(
                        f"... {len(excluded)} frames hidden ...",
                        justify="center",
                        style="traceback.error",
                    )
                continue
            if index:
                yield Text("")
            yield Text.assemble(
                (frame.filename, "pygments.string"),
                (f":{frame.lineno}", "pygments.number"),
                " in ",
                (frame.name, "pygments.function"),
            )
            source = self._sources[id(frame)]
            parts: list[ConsoleRenderable] = []
            if source.statement and not any(
                frame.filename.startswith(path) for path in self.suppress
            ):
                first = source.statement_lineno
                syntax = Syntax(
                    "\n".join(source.statement),
                    "python",
                    theme=self.theme,
                    line_numbers=True,
                    start_line=first,
                    line_range=(
                        max(1, source.lineno - first + 1 - self.extra_lines),
                        max(source.lineno, source.end_lineno or source.lineno)
                        - first
                        + 1
                        + self.extra_lines,
                    ),
                    highlight_lines={source.lineno},
                    word_wrap=self.word_wrap,
                    code_width=self.code_width,
                    indent_guides=self.indent_guides,
                    dedent=False,
                )
                if source.colno is not None and source.end_colno is not None:
                    last = source.end_lineno or source.lineno
                    for lineno in range(
                        max(first, source.lineno),
                        min(first + len(source.statement) - 1, last) + 1,
                    ):
                        line = source.statement[lineno - first]
                        start = (
                            _byte_offset_to_character_offset(line, source.colno)
                            if lineno == source.lineno
                            else len(line) - len(line.lstrip())
                        )
                        end = (
                            _byte_offset_to_character_offset(line, source.end_colno)
                            if lineno == last
                            else len(line)
                        )
                        syntax.stylize_range(
                            "traceback.error_range",
                            (lineno - first + 1, start),
                            (lineno - first + 1, end),
                        )
                parts.append(syntax)
            if self.show_locals and frame.locals:
                parts.append(
                    render_scope(
                        frame.locals,
                        title="locals",
                        indent_guides=self.indent_guides,
                        max_length=self.locals_max_length,
                        max_string=self.locals_max_string,
                        max_depth=self.locals_max_depth,
                        overflow=self.locals_overflow,
                    )
                )
            if parts:
                yield Columns(parts, padding=1)
