"""

Exception Info representation + formatting 

"""
import py
from py.__.code import safe_repr
from sys import exc_info 

class ExceptionInfo(object):
    """ wraps sys.exc_info() objects and offers
        help for navigating the traceback.
    """
    _striptext = '' 
    def __init__(self, tup=None, exprinfo=None):
        # NB. all attributes are private!  Subclasses or other
        #     ExceptionInfo-like classes may have different attributes.
        if tup is None:
            tup = exc_info()
            if exprinfo is None and isinstance(tup[1], py.magic.AssertionError):
                exprinfo = tup[1].msg
                if exprinfo and exprinfo.startswith('assert '):
                    self._striptext = 'AssertionError: '
        self._excinfo = tup
        self.type, self.value, tb = self._excinfo
        self.typename = self.type.__name__
        self.traceback = py.code.Traceback(tb) 

    def __repr__(self):
        return "<ExceptionInfo %s tblen=%d>" % (self.typename, len(self.traceback))

    def exconly(self, tryshort=False): 
        """ return the exception as a string
        
            when 'tryshort' resolves to True, and the exception is a
            py.magic.AssertionError, only the actual exception part of
            the exception representation is returned (so 'AssertionError: ' is
            removed from the beginning)
        """
        lines = py.std.traceback.format_exception_only(self.type, self.value)
        text = ''.join(lines)
        if text.endswith('\n'):
            text = text[:-1]
        if tryshort: 
            if text.startswith(self._striptext): 
                text = text[len(self._striptext):]
        return text

    def errisinstance(self, exc): 
        """ return True if the exception is an instance of exc """
        return isinstance(self.value, exc) 

    def _getreprcrash(self):
        exconly = self.exconly(tryshort=True)
        entry = self.traceback.getcrashentry()
        path, lineno = entry.path, entry.lineno
        reprcrash = ReprFileLocation(path, lineno+1, exconly)
        return reprcrash

    def getrepr(self, showlocals=False, style="long", tbfilter=True, funcargs=False):
        """ return str()able representation of this exception info.
            showlocals: show locals per traceback entry 
            style: long|short|no traceback style 
            tbfilter: hide entries (where __tracebackhide__ is true)
        """
        fmt = FormattedExcinfo(showlocals=showlocals, style=style, 
                               tbfilter=tbfilter, funcargs=funcargs)
        return fmt.repr_excinfo(self)

    def __str__(self):
        entry = self.traceback[-1]
        loc = ReprFileLocation(entry.path, entry.lineno + 1, self.exconly())
        return str(loc)

class FormattedExcinfo(object):
    """ presenting information about failing Functions and Generators. """ 
    # for traceback entries 
    flow_marker = ">"    
    fail_marker = "E"
    
    def __init__(self, showlocals=False, style="long", tbfilter=True, funcargs=False):
        self.showlocals = showlocals
        self.style = style
        self.tbfilter = tbfilter
        self.funcargs = funcargs

    def _getindent(self, source):
        # figure out indent for given source 
        try:
            s = str(source.getstatement(len(source)-1))
        except KeyboardInterrupt: 
            raise 
        except:
            try:
                s = str(source[-1])
            except:
                return 0
        return 4 + (len(s) - len(s.lstrip()))

    def _getentrysource(self, entry):
        source = entry.getsource()
        if source is not None:
            source = source.deindent()
        return source
    
    def _saferepr(self, obj):
        return safe_repr._repr(obj)

    def repr_args(self, entry):
        if self.funcargs:
            args = []
            for argname, argvalue in entry.frame.getargs():
                args.append((argname, self._saferepr(argvalue)))
            return ReprFuncArgs(args)

    def get_source(self, source, line_index=-1, excinfo=None):
        """ return formatted and marked up source lines. """
        lines = []
        if source is None:
            source = py.code.Source("???")
            line_index = 0 
        if line_index < 0:
            line_index += len(source)
        for i in range(len(source)):
            if i == line_index:
                prefix = self.flow_marker + "   "
            else:
                prefix = "    "
            line = prefix + source[i]
            lines.append(line)
        if excinfo is not None:
            indent = self._getindent(source)
            lines.extend(self.get_exconly(excinfo, indent=indent, markall=True))
        return lines

    def get_exconly(self, excinfo, indent=4, markall=False):
        lines = []
        indent = " " * indent 
        # get the real exception information out 
        exlines = excinfo.exconly(tryshort=True).split('\n')
        failindent = self.fail_marker + indent[1:]
        for line in exlines:
            lines.append(failindent + line)
            if not markall:
                failindent = indent 
        return lines

    def repr_locals(self, locals):
        if self.showlocals: 
            lines = []
            items = locals.items()
            items.sort()
            for name, value in items:
                if name == '__builtins__': 
                    lines.append("__builtins__ = <builtins>")
                else:
                    # This formatting could all be handled by the _repr() function, which is 
                    # only repr.Repr in disguise, so is very configurable.
                    str_repr = self._saferepr(value)
                    #if len(str_repr) < 70 or not isinstance(value,
                    #                            (list, tuple, dict)):
                    lines.append("%-10s = %s" %(name, str_repr))
                    #else:
                    #    self._line("%-10s =\\" % (name,))
                    #    # XXX
                    #    py.std.pprint.pprint(value, stream=self.excinfowriter)
            return ReprLocals(lines)

    def repr_traceback_entry(self, entry, excinfo=None):
        # excinfo is not None if this is the last tb entry 
        source = self._getentrysource(entry)
        if source is None:
            source = py.code.Source("???")
            line_index = 0
        else:
            line_index = entry.lineno - entry.getfirstlinesource()

        lines = []
        if self.style == "long":
            reprargs = self.repr_args(entry) 
            lines.extend(self.get_source(source, line_index, excinfo))
            message = excinfo and excinfo.typename or ""
            filelocrepr = ReprFileLocation(entry.path, entry.lineno+1, message)
            localsrepr =  self.repr_locals(entry.locals)
            return ReprEntry(lines, reprargs, localsrepr, filelocrepr)
        else: 
            if self.style == "short":
                line = source[line_index].lstrip()
                lines.append('  File "%s", line %d, in %s' % (
                    entry.path.basename, entry.lineno+1, entry.name))
                lines.append("    " + line) 
            if excinfo: 
                lines.extend(self.get_exconly(excinfo, indent=4))
            return ReprEntry(lines, None, None, None)

    def repr_traceback(self, excinfo): 
        traceback = excinfo.traceback 
        if self.tbfilter:
            traceback = traceback.filter()
        recursionindex = None
        if excinfo.errisinstance(RuntimeError):
            recursionindex = traceback.recursionindex()
        last = traceback[-1]
        entries = []
        extraline = None
        for index, entry in py.builtin.enumerate(traceback): 
            einfo = (last == entry) and excinfo or None
            reprentry = self.repr_traceback_entry(entry, einfo)
            entries.append(reprentry)
            if index == recursionindex:
                extraline = "!!! Recursion detected (same locals & position)"
                break
        return ReprTraceback(entries, extraline, style=self.style)

    def repr_excinfo(self, excinfo):
        reprtraceback = self.repr_traceback(excinfo)
        reprcrash = excinfo._getreprcrash()
        return ReprExceptionInfo(reprtraceback, reprcrash)

class Repr:
    def __str__(self):
        tw = py.io.TerminalWriter(stringio=True)
        self.toterminal(tw)
        return tw.stringio.getvalue().strip()

    def __repr__(self):
        return "<%s instance at %0x>" %(self.__class__, id(self))

class ReprExceptionInfo(Repr):
    def __init__(self, reprtraceback, reprcrash):
        self.reprtraceback = reprtraceback
        self.reprcrash = reprcrash 
        self.sections = []

    def addsection(self, name, content, sep="-"):
        self.sections.append((name, content, sep))

    def toterminal(self, tw):
        self.reprtraceback.toterminal(tw)
        for name, content, sep in self.sections:
            tw.sep(sep, name)
            tw.line(content)
    
class ReprTraceback(Repr):
    entrysep = "_ "

    def __init__(self, reprentries, extraline, style):
        self.reprentries = reprentries
        self.extraline = extraline
        self.style = style

    def toterminal(self, tw):
        sepok = False 
        for entry in self.reprentries:
            if self.style == "long":
                if sepok:
                    tw.sep(self.entrysep)
                tw.line("")
            sepok = True
            entry.toterminal(tw)
        if self.extraline:
            tw.line(self.extraline)

class ReprEntry(Repr):
    localssep = "_ "

    def __init__(self, lines, reprfuncargs, reprlocals, filelocrepr):
        self.lines = lines
        self.reprfuncargs = reprfuncargs
        self.reprlocals = reprlocals 
        self.reprfileloc = filelocrepr

    def toterminal(self, tw):
        if self.reprfuncargs:
            self.reprfuncargs.toterminal(tw)
        for line in self.lines:
            red = line.startswith("E   ") 
            tw.line(tw.markup(bold=True, red=red, text=line))
        if self.reprlocals:
            #tw.sep(self.localssep, "Locals")
            tw.line("")
            self.reprlocals.toterminal(tw)
        if self.reprfileloc:
            tw.line("")
            self.reprfileloc.toterminal(tw)

    def __str__(self):
        return "%s\n%s\n%s" % ("\n".join(self.lines), 
                               self.reprlocals, 
                               self.reprfileloc)

class ReprFileLocation(Repr):
    def __init__(self, path, lineno, message):
        self.path = str(path)
        self.lineno = lineno
        self.message = message

    def toterminal(self, tw):
        # filename and lineno output for each entry,
        # using an output format that most editors unterstand
        msg = self.message 
        i = msg.find("\n")
        if i != -1:
            msg = msg[:i] 
        tw.line("%s:%s: %s" %(self.path, self.lineno, msg))

class ReprLocals(Repr):
    def __init__(self, lines):
        self.lines = lines 

    def toterminal(self, tw):
        for line in self.lines:
            tw.line(line)

class ReprFuncArgs(Repr):
    def __init__(self, args):
        self.args = args

    def toterminal(self, tw):
        if self.args:
            linesofar = ""
            for name, value in self.args:
                ns = "%s = %s" %(name, value)
                if len(ns) + len(linesofar) + 2 > tw.fullwidth:
                    if linesofar:
                        tw.line(linesofar)
                    linesofar =  ns 
                else:
                    if linesofar:
                        linesofar += ", " + ns
                    else:
                        linesofar = ns
            if linesofar:
                tw.line(linesofar)
            tw.line("")
