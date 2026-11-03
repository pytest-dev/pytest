from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Mapping
import dataclasses
from traceback import format_exception_only
from typing import Any
from typing import Final
from typing import Literal
from typing import overload
from typing import TYPE_CHECKING

from _pytest._io import TerminalWriter


if TYPE_CHECKING:
    import rich.traceback


RECORD_SCHEMA_VERSION: Final[int] = 1

# Bounds for eager source statement capture on pathological frames (e.g.
# huge generated functions or module-level tracebacks spanning thousands of
# lines).
MAX_STATEMENT_LINES: Final[int] = 200
MAX_STATEMENT_LINE_CHARS: Final[int] = 4096

CAUSE_MESSAGE: Final[str] = (
    "The above exception was the direct cause of the following exception:"
)
CONTEXT_MESSAGE: Final[str] = (
    "During handling of the above exception, another exception occurred:"
)


@dataclasses.dataclass(frozen=True)
class Location:
    """A message at a 1-based file location (``<path>:<lineno>: <message>``).

    Replaces ``ReprFileLocation`` and unpacks as a ``(path, lineno, message)``
    3-tuple for compatibility with legacy skip location tuples.
    """

    path: str
    lineno: int
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", str(self.path))

    def __iter__(self) -> Iterator[str | int]:
        yield self.path
        yield self.lineno
        yield self.message

    def __len__(self) -> int:
        return 3

    @overload
    def __getitem__(self, index: Literal[0, 2]) -> str: ...

    @overload
    def __getitem__(self, index: Literal[1]) -> int: ...

    @overload
    def __getitem__(self, index: int) -> str | int: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[str | int, ...]: ...

    def __getitem__(self, index: int | slice) -> str | int | tuple[str | int, ...]:
        return (self.path, self.lineno, self.message)[index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "lineno": self.lineno,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Location:
        return cls(
            path=str(data["path"]),
            lineno=int(data["lineno"]),
            message=str(data["message"]),
        )

    def toterminal(self, tw: TerminalWriter) -> None:
        msg = self.message
        i = msg.find("\n")
        if i != -1:
            msg = msg[:i]
        tw.write(self.path, bold=True, red=True)
        tw.line(f":{self.lineno}: {msg}")

    def __str__(self) -> str:
        msg = self.message
        i = msg.find("\n")
        if i != -1:
            msg = msg[:i]
        return f"{self.path}:{self.lineno}: {msg}"


@dataclasses.dataclass(frozen=True)
class SyntaxErrorDetails:
    """Structured details captured from a :class:`SyntaxError` instance."""

    filename: str | None
    lineno: int | None
    offset: int | None
    text: str | None
    end_lineno: int | None = None
    end_offset: int | None = None
    msg: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "lineno": self.lineno,
            "offset": self.offset,
            "text": self.text,
            "end_lineno": self.end_lineno,
            "end_offset": self.end_offset,
            "msg": self.msg,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SyntaxErrorDetails:
        return cls(
            filename=data.get("filename"),
            lineno=data.get("lineno"),
            offset=data.get("offset"),
            text=data.get("text"),
            end_lineno=data.get("end_lineno"),
            end_offset=data.get("end_offset"),
            msg=str(data.get("msg", "")),
        )

    def format_only(self, qualified_type_name: str) -> str:
        """Format this syntax error using stdlib ``format_exception_only`` rules."""
        err = SyntaxError(self.msg)
        err.filename = self.filename
        err.lineno = self.lineno
        err.offset = self.offset
        err.text = self.text
        if self.end_lineno is not None:
            err.end_lineno = self.end_lineno
        if self.end_offset is not None:
            err.end_offset = self.end_offset
        lines = format_exception_only(SyntaxError, err)
        if lines and qualified_type_name != "SyntaxError":
            last = lines[-1]
            if last.startswith("SyntaxError"):
                lines[-1] = qualified_type_name + last.removeprefix("SyntaxError")
        return "".join(lines).rstrip()


@dataclasses.dataclass(frozen=True)
class FrameRecord:
    """Plain-data snapshot of a single traceback frame."""

    path: str
    abspath: str | None
    lineno: int
    end_lineno: int | None
    colno: int | None
    end_colno: int | None
    function: str
    module: str | None
    statement: tuple[str, ...]
    statement_lineno: int
    locals: Mapping[str, str] | None = None
    args: tuple[tuple[str, str], ...] | None = None
    hidden: bool = False
    repr_style: Literal["short", "long"] | None = None

    @property
    def short_function_name(self) -> str:
        """Function ``co_name`` (last component of ``function`` qualname)."""
        return self.function.rsplit(".", 1)[-1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "abspath": self.abspath,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "colno": self.colno,
            "end_colno": self.end_colno,
            "function": self.function,
            "module": self.module,
            "statement": list(self.statement),
            "statement_lineno": self.statement_lineno,
            "locals": dict(self.locals) if self.locals is not None else None,
            "args": [list(item) for item in self.args]
            if self.args is not None
            else None,
            "hidden": self.hidden,
            "repr_style": self.repr_style,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FrameRecord:
        raw_locals = data.get("locals")
        raw_args = data.get("args")
        raw_style = data.get("repr_style")
        if raw_style not in ("short", "long", None):
            raw_style = None
        return cls(
            path=str(data["path"]),
            abspath=str(data["abspath"]) if data.get("abspath") is not None else None,
            lineno=int(data["lineno"]),
            end_lineno=int(data["end_lineno"])
            if data.get("end_lineno") is not None
            else None,
            colno=int(data["colno"]) if data.get("colno") is not None else None,
            end_colno=int(data["end_colno"])
            if data.get("end_colno") is not None
            else None,
            function=str(data["function"]),
            module=str(data["module"]) if data.get("module") is not None else None,
            statement=tuple(str(line) for line in data.get("statement", ())),
            statement_lineno=int(data["statement_lineno"]),
            locals={str(k): str(v) for k, v in raw_locals.items()}
            if isinstance(raw_locals, Mapping)
            else None,
            args=tuple((str(k), str(v)) for k, v in raw_args)
            if raw_args is not None
            else None,
            hidden=bool(data.get("hidden", False)),
            repr_style=raw_style,
        )


@dataclasses.dataclass(frozen=True)
class ExceptionRecord:
    """Plain-data, serializable snapshot of an exception, its frames, chain, and group children."""

    type_name: str
    type_module: str
    message: str
    notes: tuple[str, ...] = ()
    syntax_error: SyntaxErrorDetails | None = None
    frames: tuple[FrameRecord, ...] = ()
    cause: ExceptionRecord | None = None
    context: ExceptionRecord | None = None
    suppress_context: bool = False
    children: tuple[ExceptionRecord, ...] = ()
    sections: tuple[tuple[str, str, str], ...] = ()
    recursion_index: int | None = None
    striptext: str = ""

    @property
    def short_type_name(self) -> str:
        """Unqualified ``__name__`` of the exception type."""
        return self.type_name.rsplit(".", 1)[-1]

    @property
    def qualified_type_name(self) -> str:
        """Exception type name prefixed with module when not in ``builtins``/``__main__``."""
        if self.type_module in ("builtins", "__main__", "<unknown>", ""):
            return self.type_name
        return f"{self.type_module}.{self.type_name}"

    def _single_subexception_leaf(self) -> ExceptionRecord | None:
        if len(self.children) != 1:
            return None
        child = self.children[0]
        if child.children:
            return child._single_subexception_leaf()
        return child

    def exconly(self, *, tryshort: bool = False) -> str:
        """Format the exception type, message, syntax error details, and notes."""
        if (
            tryshort
            and self.children
            and (leaf := self._single_subexception_leaf()) is not None
        ):
            leaf_repr = (
                f"{leaf.short_type_name}({leaf.message!r})"
                if leaf.message
                else f"{leaf.short_type_name}()"
            )
            return f"{leaf_repr} [single exception in {self.short_type_name}]"

        if self.syntax_error is not None:
            base = self.syntax_error.format_only(self.qualified_type_name)
        else:
            qtype = self.qualified_type_name
            if self.message:
                base = f"{qtype}: {self.message}"
            else:
                base = qtype

        if tryshort and self.striptext:
            base = base.removeprefix(self.striptext)

        if self.notes:
            note_lines: list[str] = []
            for note in self.notes:
                note_lines.extend(note.splitlines() or [""])
            return "\n".join([base, *note_lines]).rstrip()

        return base.rstrip()

    @property
    def crash(self) -> Location | None:
        """Last non-hidden frame location paired with the short exception message."""
        for frame in reversed(self.frames):
            if not frame.hidden:
                return Location(
                    path=frame.abspath or frame.path,
                    lineno=frame.lineno,
                    message=self.exconly(tryshort=True),
                )
        return None

    def walk(self) -> Iterator[ExceptionRecord]:
        """Yield this record and all reachable cause, context, and child records in pre-order."""
        yield self
        if self.cause is not None:
            yield from self.cause.walk()
        if self.context is not None and not self.suppress_context:
            yield from self.context.walk()
        for child in self.children:
            yield from child.walk()

    def iter_chain(self) -> Iterator[tuple[ExceptionRecord, str | None]]:
        """Yield ``(record, description)`` along the active cause/context chain, oldest first."""
        chain_items: list[tuple[ExceptionRecord, str | None]] = []
        cur: ExceptionRecord | None = self
        description: str | None = None
        while cur is not None:
            chain_items.append((cur, description))
            if cur.children:
                break
            if cur.cause is not None:
                description = CAUSE_MESSAGE
                cur = cur.cause
            elif cur.context is not None and not cur.suppress_context:
                description = CONTEXT_MESSAGE
                cur = cur.context
            else:
                cur = None
        chain_items.reverse()
        yield from chain_items

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RECORD_SCHEMA_VERSION,
            "type_name": self.type_name,
            "type_module": self.type_module,
            "message": self.message,
            "notes": list(self.notes),
            "syntax_error": self.syntax_error.to_dict()
            if self.syntax_error is not None
            else None,
            "frames": [frame.to_dict() for frame in self.frames],
            "cause": self.cause.to_dict() if self.cause is not None else None,
            "context": self.context.to_dict() if self.context is not None else None,
            "suppress_context": self.suppress_context,
            "children": [child.to_dict() for child in self.children],
            "sections": [list(sec) for sec in self.sections],
            "recursion_index": self.recursion_index,
            "striptext": self.striptext,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExceptionRecord:
        version = data.get("schema_version", RECORD_SCHEMA_VERSION)
        if version != RECORD_SCHEMA_VERSION:
            raise ValueError(f"Unsupported ExceptionRecord schema_version: {version!r}")

        raw_syntax = data.get("syntax_error")
        raw_cause = data.get("cause")
        raw_context = data.get("context")
        raw_recursion = data.get("recursion_index")

        return cls(
            type_name=str(data["type_name"]),
            type_module=str(data["type_module"]),
            message=str(data["message"]),
            notes=tuple(str(n) for n in data.get("notes", ())),
            syntax_error=SyntaxErrorDetails.from_dict(raw_syntax)
            if isinstance(raw_syntax, Mapping)
            else None,
            frames=tuple(
                FrameRecord.from_dict(f)
                for f in data.get("frames", ())
                if isinstance(f, Mapping)
            ),
            cause=cls.from_dict(raw_cause) if isinstance(raw_cause, Mapping) else None,
            context=cls.from_dict(raw_context)
            if isinstance(raw_context, Mapping)
            else None,
            suppress_context=bool(data.get("suppress_context", False)),
            children=tuple(
                cls.from_dict(c)
                for c in data.get("children", ())
                if isinstance(c, Mapping)
            ),
            sections=tuple(
                (str(s[0]), str(s[1]), str(s[2]))
                for s in data.get("sections", ())
                if len(s) == 3
            ),
            recursion_index=int(raw_recursion) if raw_recursion is not None else None,
            striptext=str(data.get("striptext", "")),
        )

    def to_rich_trace(self, *, show_hidden: bool = False) -> rich.traceback.Trace:
        """Convert this record into a :class:`rich.traceback.Trace`."""
        from rich import pretty
        from rich.traceback import _SyntaxError
        from rich.traceback import Frame as RichFrame
        from rich.traceback import Stack as RichStack
        from rich.traceback import Trace as RichTrace

        stacks: list[RichStack] = []
        cur: ExceptionRecord | None = self
        is_cause = False

        while cur is not None:
            rich_syntax: _SyntaxError | None = None
            if cur.syntax_error is not None:
                rich_syntax = _SyntaxError(
                    offset=cur.syntax_error.offset or 0,
                    filename=cur.syntax_error.filename or "?",
                    lineno=cur.syntax_error.lineno or 0,
                    line=cur.syntax_error.text or "",
                    msg=cur.syntax_error.msg,
                    notes=list(cur.notes),
                )

            visible_frames = (
                list(cur.frames)
                if show_hidden
                else [f for f in cur.frames if not f.hidden]
            )
            rich_frames: list[RichFrame] = []
            for f in visible_frames:
                last_instruction: tuple[tuple[int, int], tuple[int, int]] | None = None
                if (
                    f.end_lineno is not None
                    and f.colno is not None
                    and f.end_colno is not None
                ):
                    last_instruction = (
                        (f.lineno, f.colno),
                        (f.end_lineno, f.end_colno),
                    )
                line_idx = f.lineno - f.statement_lineno
                failing_line = (
                    f.statement[line_idx].strip()
                    if 0 <= line_idx < len(f.statement)
                    else ""
                )
                rich_locals = (
                    {k: pretty.Node(value_repr=v) for k, v in f.locals.items()}
                    if f.locals is not None
                    else None
                )
                rich_frames.append(
                    RichFrame(
                        filename=f.abspath or f.path or "?",
                        lineno=f.lineno,
                        name=f.function,
                        line=failing_line,
                        locals=rich_locals,
                        last_instruction=last_instruction,
                    )
                )

            stack = RichStack(
                exc_type=cur.qualified_type_name,
                exc_value=cur.message,
                syntax_error=rich_syntax,
                is_cause=is_cause,
                frames=rich_frames,
                notes=list(cur.notes),
                is_group=bool(cur.children),
                exceptions=[
                    child.to_rich_trace(show_hidden=show_hidden)
                    for child in cur.children
                ],
            )
            stacks.append(stack)

            if cur.children:
                break
            if cur.cause is not None:
                is_cause = True
                cur = cur.cause
            elif cur.context is not None and not cur.suppress_context:
                is_cause = False
                cur = cur.context
            else:
                cur = None

        return RichTrace(stacks=stacks)
