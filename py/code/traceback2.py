from __future__ import generators 
import py
import sys

class TracebackEntry(object):
    """ a single entry in a traceback """
    
    exprinfo = None 

    def __init__(self, rawentry):
        self._rawentry = rawentry
        self.frame = py.code.Frame(rawentry.tb_frame)
        # Ugh. 2.4 and 2.5 differs here when encountering
        # multi-line statements. Not sure about the solution, but
        # should be portable
        self.lineno = rawentry.tb_lineno - 1
        self.relline = self.lineno - self.frame.code.firstlineno

    def __repr__(self):
        return "<TracebackEntry %s:%d>" %(self.frame.code.path, self.lineno+1)

    def statement(self):
        """ return a py.code.Source object for the current statement """
        source = self.frame.code.fullsource
        return source.getstatement(self.lineno)
    statement = property(statement, None, None,
                         "statement of this traceback entry.")

    def path(self):
        return self.frame.code.path
    path = property(path, None, None, "path to the full source code")

    def getlocals(self):
        return self.frame.f_locals
    locals = property(getlocals, None, None, "locals of underlaying frame")

    def reinterpret(self):
        """Reinterpret the failing statement and returns a detailed information
           about what operations are performed."""
        if self.exprinfo is None:
            from py.__.magic import exprinfo
            source = str(self.statement).strip()
            x = exprinfo.interpret(source, self.frame, should_fail=True)
            if not isinstance(x, str):
                raise TypeError, "interpret returned non-string %r" % (x,)
            self.exprinfo = x 
        return self.exprinfo

    def getfirstlinesource(self):
        return self.frame.code.firstlineno

    def getsource(self): 
        """ return failing source code. """
        source = self.frame.code.fullsource
        if source is None:
            return None
        start = self.getfirstlinesource()
        end = self.lineno
        try:
            _, end = source.getstatementrange(end) 
        except IndexError: 
            end = self.lineno + 1 
        # heuristic to stop displaying source on e.g. 
        #   if something:  # assume this causes a NameError
        #      # _this_ lines and the one 
               #        below we don't want from entry.getsource() 
        for i in range(self.lineno, end): 
            if source[i].rstrip().endswith(':'): 
                end = i + 1
                break 
        return source[start:end]
    source = property(getsource)

    def ishidden(self):
        """ return True if the current frame has a var __tracebackhide__ 
            resolving to True
            
            mostly for internal use
        """
        try: 
            return self.frame.eval("__tracebackhide__") 
        except (SystemExit, KeyboardInterrupt): 
            raise
        except:
            return False 

    def __str__(self): 
        try: 
            fn = str(self.path) 
        except py.error.Error: 
            fn = '???'
        name = self.frame.code.name 
        try: 
            line = str(self.statement).lstrip()
        except KeyboardInterrupt:
            raise
        except:
            line = "???"
        return "  File %r:%d in %s\n  %s\n" %(fn, self.lineno+1, name, line) 

    def name(self):
        return self.frame.code.raw.co_name
    name = property(name, None, None, "co_name of underlaying code")

class Traceback(list):
    """ Traceback objects encapsulate and offer higher level 
        access to Traceback entries.  
    """
    Entry = TracebackEntry 
    def __init__(self, tb):
        """ initialize from given python traceback object. """
        if hasattr(tb, 'tb_next'):
            def f(cur): 
                while cur is not None: 
                    yield self.Entry(cur)
                    cur = cur.tb_next 
            list.__init__(self, f(tb)) 
        else:
            list.__init__(self, tb)

    def cut(self, path=None, lineno=None, firstlineno=None):
        """ return a Traceback instance wrapping part of this Traceback

            by provding any combination of path, lineno and firstlineno, the
            first frame to start the to-be-returned traceback is determined

            this allows cutting the first part of a Traceback instance e.g.
            for formatting reasons (removing some uninteresting bits that deal
            with handling of the exception/traceback)
        """
        for x in self:
            if ((path is None or x.frame.code.path == path) and
                (lineno is None or x.lineno == lineno) and
                (firstlineno is None or x.frame.code.firstlineno == firstlineno)):
                return Traceback(x._rawentry)
        return self

    def __getitem__(self, key):
        val = super(Traceback, self).__getitem__(key)
        if isinstance(key, type(slice(0))):
            val = self.__class__(val)
        return val

    def filter(self, fn=lambda x: not x.ishidden()):
        """ return a Traceback instance with certain items removed

            fn is a function that gets a single argument, a TracebackItem
            instance, and should return True when the item should be added
            to the Traceback, False when not

            by default this removes all the TracebackItems which are hidden
            (see ishidden() above)
        """
        return Traceback(filter(fn, self))

    def getcrashentry(self):
        """ return last non-hidden traceback entry that lead
        to the exception of a traceback. 
        """
        tb = self.filter()
        if not tb:
            tb = self
        return tb[-1]

    def recursionindex(self):
        """ return the index of the frame/TracebackItem where recursion
            originates if appropriate, None if no recursion occurred
        """
        cache = {}
        for i, entry in py.builtin.enumerate(self):
            key = entry.frame.code.path, entry.lineno 
            #print "checking for recursion at", key
            l = cache.setdefault(key, [])
            if l: 
                f = entry.frame
                loc = f.f_locals
                for otherloc in l: 
                    if f.is_true(f.eval(co_equal, 
                        __recursioncache_locals_1=loc,
                        __recursioncache_locals_2=otherloc)):
                        return i 
            l.append(entry.frame.f_locals)
        return None

#    def __str__(self): 
#        for x in self
#        l = []
##        for func, entry in self._tblist: 
#            l.append(entry.display()) 
#        return "".join(l) 


co_equal = compile('__recursioncache_locals_1 == __recursioncache_locals_2',
                   '?', 'eval')

