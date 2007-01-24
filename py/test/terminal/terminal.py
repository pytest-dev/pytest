import py

from time import time as now
Item = py.test.Item
from py.__.test.terminal.out import getout 
import py.__.code.safe_repr

def getrelpath(source, dest): 
    base = source.common(dest)
    if not base: 
        return None 
    # with posix local paths '/' is always a common base
    relsource = source.relto(base)
    reldest = dest.relto(base)
    n = relsource.count(source.sep)
    target = dest.sep.join(('..', )*n + (reldest, ))
    return target 

from py.__.test.session import Session

class TerminalSession(Session): 
    def __init__(self, config, file=None): 
        super(TerminalSession, self).__init__(config) 
        if file is None: 
            file = py.std.sys.stdout 
        self._file = file
        self.out = getout(file) 
        self._started = {}
        self._opencollectors = []

    def main(self): 
        if self.config.option._remote: 
            from py.__.test.terminal import remote 
            return remote.main(self.config, self._file, self.config._origargs)
        else: 
            return super(TerminalSession, self).main() 

    # ---------------------
    # PROGRESS information 
    # ---------------------
   
    def start(self, colitem):
        super(TerminalSession, self).start(colitem) 
        if self.config.option.collectonly: 
            cols = self._opencollectors
            self.out.line('    ' * len(cols) + repr(colitem))
            cols.append(colitem) 
        else: 
            cls = getattr(colitem, '__class__', None)
            if cls is None:
                return
            for typ in py.std.inspect.getmro(cls):
                meth = getattr(self, 'start_%s' % typ.__name__, None)
                if meth:
                    meth(colitem)
                    break 
            colitem.start = py.std.time.time() 

    def start_Module(self, colitem): 
        if self.config.option.verbose == 0: 
            abbrev_fn = getrelpath(py.path.local('.xxx.'), colitem.fspath)
            self.out.write('%s' % (abbrev_fn, ))
        else: 
            self.out.line()
            self.out.line("+ testmodule: %s" % colitem.fspath) 

    def startiteration(self, colitem, subitems): 
        if (isinstance(colitem, py.test.collect.Module) 
            and self.config.option.verbose == 0 
            and not self.config.option.collectonly): 
            try: 
                sum = 0
                for sub in subitems: 
                    sum += len(list(colitem.join(sub).tryiter()))
            except (SystemExit, KeyboardInterrupt): 
                raise 
            except: 
                self.out.write('[?]')
            else: 
                self.out.write('[%d] ' % sum) 
            return self.out.line 

    def start_Item(self, colitem): 
        if self.config.option.verbose >= 1: 
            if isinstance(colitem, py.test.Item): 
                realpath, lineno = colitem.getpathlineno()
                location = "%s:%d" % (realpath.basename, lineno+1)
                self.out.write("%-20s %s " % (location, colitem.getmodpath()))
  
    def finish(self, colitem, outcome):
        end = now()
        super(TerminalSession, self).finish(colitem, outcome) 
        if self.config.option.collectonly: 
            cols = self._opencollectors 
            last = cols.pop()
            #assert last == colitem, "expected %r, got %r" %(last, colitem)
            return
        colitem.elapsedtime = end - colitem.start 
        if self.config.option.usepdb:
            if isinstance(outcome, Item.Failed): 
                print "dispatching to ppdb", colitem
                self.repr_failure(colitem, outcome) 
                import pdb
                self.out.write('\n%s\n' % (outcome.excinfo.exconly(),))
                pdb.post_mortem(outcome.excinfo._excinfo[2])
        if isinstance(colitem, py.test.collect.Module):
            resultstring = self.repr_progress_module_result(colitem, outcome)
            if resultstring:
                self.out.line(" - " + resultstring)
        if isinstance(colitem, py.test.Item): 
            if self.config.option.verbose >= 1: 
                resultstring = self.repr_progress_long_result(colitem, outcome)
                resultstring += " (%.2f)" % (colitem.elapsedtime,)
                self.out.line(resultstring) 
            else:
                c = self.repr_progress_short_result(colitem, outcome)
                self.out.write(c) 


    # -------------------
    # HEADER information 
    # -------------------
    def header(self, colitems): 
        super(TerminalSession, self).header(colitems) 
        self.out.sep("=", "test process starts")
        option = self.config.option 
        modes = []
        for name in 'looponfailing', 'exitfirst', 'nomagic': 
            if getattr(option, name): 
                modes.append(name) 
        if option._fromremote:
            modes.insert(0, 'child process') 
        else:
            modes.insert(0, 'inprocess')
        mode = "/".join(modes)
        self.out.line("testing-mode: %s" % mode)
        self.out.line("executable:   %s  (%s)" %
                          (py.std.sys.executable, repr_pythonversion()))
        rev = py.__package__.getrev()
        self.out.line("using py lib: %s <rev %s>" % (
                       py.path.local(py.__file__).dirpath(), rev))
    
        if self.config.option.traceconfig or self.config.option.verbose: 

            for x in colitems: 
                self.out.line("test target:  %s" %(x.fspath,))

            conftestmodules = self.config.conftest.getconftestmodules(None)
            for i,x in py.builtin.enumerate(conftestmodules): 
                self.out.line("initial conf %d: %s" %(i, x.__file__)) 

            #for i, x in py.builtin.enumerate(py.test.config.configpaths):
            #    self.out.line("initial testconfig %d: %s" %(i, x))
            #additional = py.test.config.getfirst('additionalinfo')
            #if additional:
            #    for key, descr in additional():
            #        self.out.line("%s: %s" %(key, descr))
        self.out.line() 
        self.starttime = now()
  
    # -------------------
    # FOOTER information 
    # -------------------
 
    def footer(self, colitems):
        super(TerminalSession, self).footer(colitems) 
        self.endtime = now()
        self.out.line() 
        self.skippedreasons()
        self.failures()
        self.summaryline()

    # --------------------
    # progress information 
    # --------------------
    typemap = {
        Item.Passed: '.',
        Item.Skipped: 's',
        Item.Failed: 'F',
    }
    namemap = {
        Item.Passed: 'ok',
        Item.Skipped: 'SKIP',
        Item.Failed: 'FAIL',
    }

    def repr_progress_short_result(self, item, outcome):
        for outcometype, char in self.typemap.items():
            if isinstance(outcome, outcometype):
                return char
        else:
            #raise TypeError, "not an Outomce instance: %r" % (outcome,)
            return '?'

    def repr_progress_long_result(self, item, outcome):
        for outcometype, char in self.namemap.items():
            if isinstance(outcome, outcometype):
                return char
        else:
            #raise TypeError, "not an Outcome instance: %r" % (outcome,)
            return 'UNKNOWN'

    def repr_progress_module_result(self, item, outcome):
        if isinstance(outcome, py.test.Item.Failed):
            return "FAILED TO LOAD MODULE"
        elif isinstance(outcome, py.test.Item.Skipped):
            return "skipped"
        elif not isinstance(outcome, (list, py.test.Item.Passed)):
            return "?"

    # --------------------
    # summary information 
    # --------------------
    def summaryline(self): 
        outlist = []
        sum = 0
        for typ in Item.Passed, Item.Failed, Item.Skipped:
            l = self.getitemoutcomepairs(typ)
            if l:
                outlist.append('%d %s' % (len(l), typ.__name__.lower()))
            sum += len(l)
        elapsed = self.endtime-self.starttime
        status = "%s" % ", ".join(outlist)
        self.out.sep('=', 'tests finished: %s in %4.2f seconds' %
                         (status, elapsed))

    def getlastvisible(self, sourcetraceback): 
        traceback = sourcetraceback[:]
        while traceback: 
            entry = traceback.pop()
            try: 
                x = entry.frame.eval("__tracebackhide__") 
            except: 
                x = False 
            if not x: 
                return entry 
        else: 
            return sourcetraceback[-1]
        
    def skippedreasons(self):
        texts = {}
        for colitem, outcome in self.getitemoutcomepairs(Item.Skipped):
            raisingtb = self.getlastvisible(outcome.excinfo.traceback) 
            fn = raisingtb.frame.code.path
            lineno = raisingtb.lineno
            d = texts.setdefault(outcome.excinfo.exconly(), {})
            d[(fn,lineno)] = outcome 
                
        if texts:
            self.out.line()
            self.out.sep('_', 'reasons for skipped tests')
            for text, dict in texts.items():
                for (fn, lineno), outcome in dict.items(): 
                    self.out.line('Skipped in %s:%d' %(fn, lineno+1))
                self.out.line("reason: %s" % text) 
                self.out.line()

    def failures(self):
        if self.config.option.tbstyle == 'no':
            return   # skip the detailed failure reports altogether
        l = self.getitemoutcomepairs(Item.Failed)
        if l: 
            self.out.sep('_')
            for colitem, outcome in l: 
                self.repr_failure(colitem, outcome) 

    def repr_failure(self, item, outcome): 
        excinfo = outcome.excinfo 
        traceback = excinfo.traceback
        #print "repr_failures sees item", item
        #print "repr_failures sees traceback"
        #py.std.pprint.pprint(traceback)
        if item and not self.config.option.fulltrace: 
            path, firstlineno = item.getpathlineno()
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
            traceback = ntraceback.filter()
        if not traceback: 
            self.out.line("empty traceback from item %r" % (item,)) 
            return
        handler = getattr(self, 'repr_failure_tb%s' % self.config.option.tbstyle)
        handler(item, excinfo, traceback)

    def repr_failure_tblong(self, item, excinfo, traceback):
        if not self.config.option.nomagic and excinfo.errisinstance(RuntimeError):
            recursionindex = traceback.recursionindex()
        else:
            recursionindex = None
        last = traceback[-1]
        first = traceback[0]
        for index, entry in py.builtin.enumerate(traceback): 
            if entry == first: 
                if item: 
                    self.repr_failure_info(item, entry) 
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
            self.out.line("[%s:%d]" %(entry.frame.code.path, entry.lineno+1))  
            self.repr_locals(entry) 

            # trailing info 
            if entry == last: 
                #if item: 
                #    self.repr_failure_info(item, entry) 
                self.repr_out_err(item) 
                self.out.sep("_")
            else: 
                self.out.sep("_ ")
                if index == recursionindex:
                    self.out.line("Recursion detected (same locals & position)")
                    self.out.sep("!")
                    break 

    def repr_failure_tbshort(self, item, excinfo, traceback):
        # print a Python-style short traceback
        if not self.config.option.nomagic and excinfo.errisinstance(RuntimeError):
            recursionindex = traceback.recursionindex()
        else:
            recursionindex = None
        last = traceback[-1]
        first = traceback[0]
        self.out.line()
        for index, entry in py.builtin.enumerate(traceback): 
            code = entry.frame.code
            self.out.line('  File "%s", line %d, in %s' % (
                code.raw.co_filename, entry.lineno+1, code.raw.co_name))
            try:
                fullsource = entry.frame.code.fullsource
            except py.error.ENOENT:
                source = ["?"]
            else:
                try:
                    source = [fullsource[entry.lineno].lstrip()]
                except IndexError:
                    source = []
            if entry == last:
                if source:
                    self.repr_source(source, 'E')
                self.repr_failure_explanation(excinfo, source) 
            else:
                if source:
                    self.repr_source(source, ' ')
            self.repr_locals(entry) 

            # trailing info 
            if entry == last: 
                #if item: 
                #    self.repr_failure_info(item, entry) 
                self.repr_out_err(item) 
                self.out.sep("_")
            else: 
                if index == recursionindex:
                    self.out.line("Recursion detected (same locals & position)")
                    self.out.sep("!")
                    break 

    # the following is only used by the combination '--pdb --tb=no'
    repr_failure_tbno = repr_failure_tbshort

    def repr_failure_info(self, item, entry): 
        root = item.fspath 
        modpath = item.getmodpath() 
        try: 
            fn, lineno = item.getpathlineno() 
        except TypeError: 
            assert isinstance(item.parent, py.test.collect.Generator) 
            # a generative test yielded a non-callable 
            fn, lineno = item.parent.getpathlineno() 
        # hum, the following overloads traceback output 
        #if fn != entry.frame.code.path or \
        #   entry.frame.code.firstlineno != lineno: 
        #    self.out.line("testcode: %s:%d" % (fn, lineno+1)) 
        if root == fn: 
            self.out.sep("_", "entrypoint: %s" %(modpath))
        else:
            self.out.sep("_", "entrypoint: %s %s" %(root.basename, modpath))

    def getentrysource(self, entry):
        try: 
            source = entry.getsource() 
        except py.error.ENOENT:
            source = py.code.Source("[failure to get at sourcelines from %r]\n" % entry)
        return source.deindent()

    def repr_source(self, source, marker=">", marker_location=-1):
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
        return

        # XXX reinstate the following with a --magic option? 
        # the following line gets user-supplied messages (e.g.
        # for "assert 0, 'custom message'")
        msg = getattr(getattr(excinfo, 'value', ''), 'msg', '') 
        info = None
        if not msg: 
            special = excinfo.errisinstance((SyntaxError, SystemExit, KeyboardInterrupt))
            if not self.config.option.nomagic and not special: 
                try: 
                    info = excinfo.traceback[-1].reinterpret() # very detailed info
                except KeyboardInterrupt:
                    raise
                except:
                    if self.config.option.verbose >= 1:
                        self.out.line("[reinterpretation traceback]")
                        py.std.traceback.print_exc(file=py.std.sys.stdout)
                    else:
                        self.out.line("[reinterpretation failed, increase "
                                      "verbosity to see details]")
        # print reinterpreted info if any 
        if info: 
            lines = info.split('\n') 
            self.out.line('>' + indent[:-1] + lines.pop(0)) 
            for x in lines: 
                self.out.line(indent + x) 

    def repr_out_err(self, colitem): 
        for parent in colitem.listchain(): 
            for name, obj in zip(['out', 'err'], parent.getouterr()): 
                if obj: 
                    self.out.sep("- ", "%s: recorded std%s" % (parent.name, name))
                    self.out.line(obj)
            
    def repr_locals(self, entry): 
        if self.config.option.showlocals:
            self.out.sep('- ', 'locals')
            for name, value in entry.frame.f_locals.items():
                if name == '__builtins__': 
                    self.out.line("__builtins__ = <builtins>")
                else:
                    # This formatting could all be handled by the _repr() function, which is 
                    # only repr.Repr in disguise, so is very configurable.
                    str_repr = py.__.code.safe_repr._repr(value)
                    if len(str_repr) < 70 or not isinstance(value,
                                                (list, tuple, dict)):
                        self.out.line("%-10s = %s" %(name, str_repr))
                    else:
                        self.out.line("%-10s =\\" % (name,))
                        py.std.pprint.pprint(value, stream=self.out)

def repr_pythonversion():
    v = py.std.sys.version_info
    try:
        return "%s.%s.%s-%s-%s" % v
    except ValueError:
        return str(v)
