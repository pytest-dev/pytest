
""" This file intends to gather all methods of representing
failures/tracebacks etc. which should be used among
all terminal-based reporters. This methods should be general,
to allow further use outside the pylib
"""

import py
from py.__.code import safe_repr

class Presenter(object):
    """ Class used for presentation of various objects,
    sharing common output style
    """
    def __init__(self, out, config):
        """ out is a file-like object (we can write to it)
        """
        assert hasattr(out, 'write')
        self.out = out
        self.config = config

    def repr_source(self, source, marker=">", marker_location=-1):
        """ This one represents piece of source with possible
        marker at requested position
        """
        if isinstance(source, str):
            # why the hell, string is iterable?
            source = source.split("\n")
        if marker_location < 0:
            marker_location += len(source)
            if marker_location < 0:
                marker_location = 0
        if marker_location >= len(source):
            marker_location = len(source) - 1
        for i in range(len(source)):
            if i == marker_location:
                prefix = marker + "   "
            else:
                prefix = "    "
            self.out.line(prefix + source[i])

    def repr_item_info(self, item):
        """ This method represents py.test.Item info (path and module)
        """
        root = item.fspath 
        modpath = item._getmodpath() 
        try: 
            fn, lineno = item._getpathlineno() 
        except TypeError: 
            assert isinstance(item.parent, py.test.collect.Generator) 
            # a generative test yielded a non-callable 
            fn, lineno = item.parent._getpathlineno() 
        if root == fn:
            self.out.sep("_", "entrypoint: %s" %(modpath))
        else:
            self.out.sep("_", "entrypoint: %s %s" %(root.basename, modpath))

    def repr_failure_explanation(self, excinfo, source):
        try:
            s = str(source.getstatement(len(source)-1))
        except KeyboardInterrupt: 
            raise 
        except: 
            s = str(source[-1])
        indent = " " * (4 + (len(s) - len(s.lstrip())))
        # get the real exception information out 
        lines = excinfo.exconly(tryshort=True).split('\n')
        self.out.line('>' + indent[:-1] + lines.pop(0))
        for x in lines:
            self.out.line(indent + x)

    def getentrysource(self, entry):
        try:
            source = entry.getsource()
        except py.error.ENOENT:
            source = py.code.Source("[failure to get at sourcelines from %r]\n" % entry)
        return source.deindent()

    def repr_locals(self, f_locals):
        if self.config.option.showlocals:
            self.out.sep('- ', 'locals')
            for name, value in f_locals.items():
                if name == '__builtins__': 
                    self.out.line("__builtins__ = <builtins>")
                else:
                    # This formatting could all be handled by the _repr() function, which is 
                    # only repr.Repr in disguise, so is very configurable.
                    str_repr = safe_repr._repr(value)
                    if len(str_repr) < 70 or not isinstance(value,
                                                (list, tuple, dict)):
                        self.out.line("%-10s = %s" %(name, str_repr))
                    else:
                        self.out.line("%-10s =\\" % (name,))
                        py.std.pprint.pprint(value, stream=self.out)

    def repr_failure_tblong(self, item, excinfo, traceback, out_err_reporter):
        if not self.config.option.nomagic and excinfo.errisinstance(RuntimeError):
            recursionindex = traceback.recursionindex()
        else:
            recursionindex = None
        last = traceback[-1]
        first = traceback[0]
        for index, entry in py.builtin.enumerate(traceback): 
            if entry == first:
                if item: 
                    self.repr_item_info(item) 
                    self.out.line()
            else: 
                self.out.line("")
            source = self.getentrysource(entry)
            firstsourceline = entry.getfirstlinesource()
            marker_location = entry.lineno - firstsourceline
            if entry == last: 
                self.repr_source(source, 'E', marker_location)
                self.repr_failure_explanation(excinfo, source) 
            else:
                self.repr_source(source, '>', marker_location)
            self.out.line("") 
            self.out.line("[%s:%d]" %(entry.path, entry.lineno+1))
            self.repr_locals(entry.locals)

            # trailing info 
            if entry == last:
                out_err_reporter() 
                self.out.sep("_")
            else: 
                self.out.sep("_ ")
                if index == recursionindex:
                    self.out.line("Recursion detected (same locals & position)")
                    self.out.sep("!")
                    break 

    def repr_failure_tbshort(self, item, excinfo, traceback, out_err_reporter):
        # print a Python-style short traceback
        if not self.config.option.nomagic and excinfo.errisinstance(RuntimeError):
            recursionindex = traceback.recursionindex()
        else:
            recursionindex = None
        last = traceback[-1]
        first = traceback[0]
        self.out.line()
        for index, entry in py.builtin.enumerate(traceback):
            path = entry.path.basename
            firstsourceline = entry.getfirstlinesource()
            relline = entry.lineno - firstsourceline
            self.out.line('  File "%s", line %d, in %s' % (
                path, entry.lineno+1, entry.name))
            try:
                source = entry.getsource().lines
            except py.error.ENOENT:
                source = ["?"]
            else:
                try:
                    if len(source) > 1:
                        source = source[relline]
                except IndexError:
                    source = []
            if entry == last:
                if source:
                    self.repr_source(source, 'E')
                self.repr_failure_explanation(excinfo, source) 
            else:
                if source:
                    self.repr_source(source, ' ')
            self.repr_locals(entry.locals) 

            # trailing info 
            if entry == last:
                out_err_reporter()
                self.out.sep("_")
            else: 
                if index == recursionindex:
                    self.out.line("Recursion detected (same locals & position)")
                    self.out.sep("!")
                    break 

    # the following is only used by the combination '--pdb --tb=no'
    repr_failure_tbno = repr_failure_tbshort
