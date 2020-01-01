import ast
import inspect
import linecache
import sys
import textwrap
import tokenize
import warnings
from ast import PyCF_ONLY_AST as _AST_FLAG
from bisect import bisect_right
from types import FrameType
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import py

from _pytest.compat import overload


class Source:
    """ an immutable object holding a source code fragment,
        possibly deindenting it.
    """

    _compilecounter = 0

    def __init__(self, *parts, **kwargs) -> None:
        self.lines = lines = []  # type: List[str]
        de = kwargs.get("deindent", True)
        for part in parts:
            if not part:
                partlines = []  # type: List[str]
            elif isinstance(part, Source):
                partlines = part.lines
            elif isinstance(part, (tuple, list)):
                partlines = [x.rstrip("\n") for x in part]
            elif isinstance(part, str):
                partlines = part.split("\n")
            else:
                partlines = getsource(part, deindent=de).lines
            if de:
                partlines = deindent(partlines)
            lines.extend(partlines)

    def __eq__(self, other):
        try:
            return self.lines == other.lines
        except AttributeError:
            if isinstance(other, str):
                return str(self) == other
            return False

    # Ignore type because of https://github.com/python/mypy/issues/4266.
    __hash__ = None  # type: ignore

    @overload
    def __getitem__(self, key: int) -> str:
        raise NotImplementedError()

    @overload  # noqa: F811
    def __getitem__(self, key: slice) -> "Source":  # noqa: F811
        raise NotImplementedError()

    def __getitem__(self, key: Union[int, slice]) -> Union[str, "Source"]:  # noqa: F811
        if isinstance(key, int):
            return self.lines[key]
        else:
            if key.step not in (None, 1):
                raise IndexError("cannot slice a Source with a step")
            newsource = Source()
            newsource.lines = self.lines[key.start : key.stop]
            return newsource

    def __iter__(self) -> Iterator[str]:
        return iter(self.lines)

    def __len__(self) -> int:
        return len(self.lines)

    def strip(self) -> "Source":
        """ return new source object with trailing
            and leading blank lines removed.
        """
        start, end = 0, len(self)
        while start < end and not self.lines[start].strip():
            start += 1
        while end > start and not self.lines[end - 1].strip():
            end -= 1
        source = Source()
        source.lines[:] = self.lines[start:end]
        return source

    def putaround(
        self, before: str = "", after: str = "", indent: str = " " * 4
    ) -> "Source":
        """ return a copy of the source object with
            'before' and 'after' wrapped around it.
        """
        beforesource = Source(before)
        aftersource = Source(after)
        newsource = Source()
        lines = [(indent + line) for line in self.lines]
        newsource.lines = beforesource.lines + lines + aftersource.lines
        return newsource

    def indent(self, indent: str = " " * 4) -> "Source":
        """ return a copy of the source object with
            all lines indented by the given indent-string.
        """
        newsource = Source()
        newsource.lines = [(indent + line) for line in self.lines]
        return newsource

    def getstatement(self, lineno: int) -> "Source":
        """ return Source statement which contains the
            given linenumber (counted from 0).
        """
        start, end = self.getstatementrange(lineno)
        return self[start:end]

    def getstatementrange(self, lineno: int):
        """ return (start, end) tuple which spans the minimal
            statement region which containing the given lineno.
        """
        if not (0 <= lineno < len(self)):
            raise IndexError("lineno out of range")
        ast, start, end = getstatementrange_ast(lineno, self)
        return start, end

    def deindent(self) -> "Source":
        """return a new source object deindented."""
        newsource = Source()
        newsource.lines[:] = deindent(self.lines)
        return newsource

    def isparseable(self, deindent: bool = True) -> bool:
        """ return True if source is parseable, heuristically
            deindenting it by default.
        """
        from parser import suite as syntax_checker

        if deindent:
            source = str(self.deindent())
        else:
            source = str(self)
        try:
            # compile(source+'\n', "x", "exec")
            syntax_checker(source + "\n")
        except KeyboardInterrupt:
            raise
        except Exception:
            return False
        else:
            return True

    def __str__(self) -> str:
        return "\n".join(self.lines)

    def compile(
        self,
        filename=None,
        mode="exec",
        flag: int = 0,
        dont_inherit: int = 0,
        _genframe: Optional[FrameType] = None,
    ):
        """ return compiled code object. if filename is None
            invent an artificial filename which displays
            the source/line position of the caller frame.
        """
        if not filename or py.path.local(filename).check(file=0):
            if _genframe is None:
                _genframe = sys._getframe(1)  # the caller
            fn, lineno = _genframe.f_code.co_filename, _genframe.f_lineno
            base = "<%d-codegen " % self._compilecounter
            self.__class__._compilecounter += 1
            if not filename:
                filename = base + "%s:%d>" % (fn, lineno)
            else:
                filename = base + "%r %s:%d>" % (filename, fn, lineno)
        source = "\n".join(self.lines) + "\n"
        try:
            co = compile(source, filename, mode, flag)
        except SyntaxError as ex:
            # re-represent syntax errors from parsing python strings
            msglines = self.lines[: ex.lineno]
            if ex.offset:
                msglines.append(" " * ex.offset + "^")
            msglines.append("(code was compiled probably from here: %s)" % filename)
            newex = SyntaxError("\n".join(msglines))
            newex.offset = ex.offset
            newex.lineno = ex.lineno
            newex.text = ex.text
            raise newex
        else:
            if flag & _AST_FLAG:
                return co
            lines = [(x + "\n") for x in self.lines]
            # Type ignored because linecache.cache is private.
            linecache.cache[filename] = (1, None, lines, filename)  # type: ignore
            return co


#
# public API shortcut functions
#


def compile_(source, filename=None, mode="exec", flags: int = 0, dont_inherit: int = 0):
    """ compile the given source to a raw code object,
        and maintain an internal cache which allows later
        retrieval of the source code for the code object
        and any recursively created code objects.
    """
    if isinstance(source, ast.AST):
        # XXX should Source support having AST?
        return compile(source, filename, mode, flags, dont_inherit)
    _genframe = sys._getframe(1)  # the caller
    s = Source(source)
    co = s.compile(filename, mode, flags, _genframe=_genframe)
    return co


def getfslineno(obj):
    """ Return source location (path, lineno) for the given object.
    If the source cannot be determined return ("", -1).

    The line number is 0-based.
    """
    from .code import Code

    try:
        code = Code(obj)
    except TypeError:
        try:
            fn = inspect.getsourcefile(obj) or inspect.getfile(obj)
        except TypeError:
            return "", -1

        fspath = fn and py.path.local(fn) or None
        lineno = -1
        if fspath:
            try:
                _, lineno = findsource(obj)
            except IOError:
                pass
    else:
        fspath = code.path
        lineno = code.firstlineno
    assert isinstance(lineno, int)
    return fspath, lineno


#
# helper functions
#


def findsource(obj) -> Tuple[Optional[Source], int]:
    try:
        sourcelines, lineno = inspect.findsource(obj)
    except Exception:
        return None, -1
    source = Source()
    source.lines = [line.rstrip() for line in sourcelines]
    return source, lineno


def getsource(obj, **kwargs) -> Source:
    from .code import getrawcode

    obj = getrawcode(obj)
    try:
        strsrc = inspect.getsource(obj)
    except IndentationError:
        strsrc = '"Buggy python version consider upgrading, cannot get source"'
    assert isinstance(strsrc, str)
    return Source(strsrc, **kwargs)


def deindent(lines: Sequence[str]) -> List[str]:
    return textwrap.dedent("\n".join(lines)).splitlines()


def get_statement_startend2(lineno: int, node: ast.AST) -> Tuple[int, Optional[int]]:
    import ast

    # flatten all statements and except handlers into one lineno-list
    # AST's line numbers start indexing at 1
    values = []  # type: List[int]
    for x in ast.walk(node):
        if isinstance(x, (ast.stmt, ast.ExceptHandler)):
            values.append(x.lineno - 1)
            for name in ("finalbody", "orelse"):
                val = getattr(x, name, None)  # type: Optional[List[ast.stmt]]
                if val:
                    # treat the finally/orelse part as its own statement
                    values.append(val[0].lineno - 1 - 1)
    values.sort()
    insert_index = bisect_right(values, lineno)
    start = values[insert_index - 1]
    if insert_index >= len(values):
        end = None
    else:
        end = values[insert_index]
    return start, end


def getstatementrange_ast(
    lineno: int,
    source: Source,
    assertion: bool = False,
    astnode: Optional[ast.AST] = None,
) -> Tuple[ast.AST, int, int]:
    if astnode is None:
        content = str(source)
        # See #4260:
        # don't produce duplicate warnings when compiling source to find ast
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            astnode = compile(content, "source", "exec", _AST_FLAG)

    start, end = get_statement_startend2(lineno, astnode)
    # we need to correct the end:
    # - ast-parsing strips comments
    # - there might be empty lines
    # - we might have lesser indented code blocks at the end
    if end is None:
        end = len(source.lines)

    if end > start + 1:
        # make sure we don't span differently indented code blocks
        # by using the BlockFinder helper used which inspect.getsource() uses itself
        block_finder = inspect.BlockFinder()
        # if we start with an indented line, put blockfinder to "started" mode
        block_finder.started = source.lines[start][0].isspace()
        it = ((x + "\n") for x in source.lines[start:end])
        try:
            for tok in tokenize.generate_tokens(lambda: next(it)):
                block_finder.tokeneater(*tok)
        except (inspect.EndOfBlock, IndentationError):
            end = block_finder.last + start
        except Exception:
            pass

    # the end might still point to a comment or empty line, correct it
    while end:
        line = source.lines[end - 1].lstrip()
        if line.startswith("#") or not line:
            end -= 1
        else:
            break
    return astnode, start, end
