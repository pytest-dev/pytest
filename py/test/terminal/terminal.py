import py

from time import time as now
from py.__.test.terminal.out import getout 
from py.__.test.representation import Presenter
from py.__.test.outcome import Skipped, Passed, Failed
import py.__.test.custompdb

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
        self._opencollectors = []
        self.presenter = Presenter(self.out, config)

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
            if issubclass(cls, py.test.collect.Module):
                self.start_Module(colitem)
            elif issubclass(cls, py.test.collect.Item):
                self.start_Item(colitem)
            #for typ in py.std.inspect.getmro(cls):
            #    meth = getattr(self, 'start_%s' % typ.__name__, None)
            #    if meth:
            #        meth(colitem)
            #        break 
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
                    sum += len(list(colitem.join(sub)._tryiter()))
            except (SystemExit, KeyboardInterrupt): 
                raise 
            except: 
                self.out.write('[?]')
            else: 
                self.out.write('[%d] ' % sum) 
            return self.out.line 

    def start_Item(self, colitem): 
        if self.config.option.verbose >= 1: 
            if isinstance(colitem, py.test.collect.Item): 
                realpath, lineno = colitem._getpathlineno()
                location = "%s:%d" % (realpath.basename, lineno+1)
                self.out.write("%-20s %s " % (location, colitem._getmodpath()))
  
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
            if isinstance(outcome, Failed): 
                print "dispatching to ppdb", colitem
                self.repr_failure(colitem, outcome) 
                self.out.write('\n%s\n' % (outcome.excinfo.exconly(),))
                py.__.test.custompdb.post_mortem(outcome.excinfo._excinfo[2])
        if isinstance(colitem, py.test.collect.Module):
            resultstring = self.repr_progress_module_result(colitem, outcome)
            if resultstring:
                self.out.line(" - " + resultstring)
        if isinstance(colitem, py.test.collect.Item): 
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
        #if self._isremoteoption._fromremote:
        #    modes.insert(0, 'child process') 
        #else:
        #    modes.insert(0, 'inprocess')
        #mode = "/".join(modes)
        #self.out.line("testing-mode: %s" % mode)
        self.out.line("executable:   %s  (%s)" %
                          (py.std.sys.executable, repr_pythonversion()))
        rev = py.__package__.getrev()
        self.out.line("using py lib: %s <rev %s>" % (
                       py.path.local(py.__file__).dirpath(), rev))
    
        if self.config.option.traceconfig or self.config.option.verbose: 

            for x in colitems: 
                self.out.line("test target:  %s" %(x.fspath,))

            conftestmodules = self.config._conftest.getconftestmodules(None)
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
        Passed: '.',
        Skipped: 's',
        Failed: 'F',
    }
    namemap = {
        Passed: 'ok',
        Skipped: 'SKIP',
        Failed: 'FAIL',
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
        if isinstance(outcome, Failed):
            return "FAILED TO LOAD MODULE"
        elif isinstance(outcome, Skipped):
            return "skipped"
        elif not isinstance(outcome, (list, Passed)):
            return "?"

    # --------------------
    # summary information 
    # --------------------
    def summaryline(self): 
        outlist = []
        sum = 0
        for typ in Passed, Failed, Skipped:
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
        for colitem, outcome in self.getitemoutcomepairs(Skipped):
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
        l = self.getitemoutcomepairs(Failed)
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
            path, firstlineno = item._getpathlineno()
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
            traceback = ntraceback.filter()
        if not traceback: 
            self.out.line("empty traceback from item %r" % (item,)) 
            return
        handler = getattr(self.presenter, 'repr_failure_tb%s' % self.config.option.tbstyle)
        handler(item, excinfo, traceback, lambda : self.repr_out_err(item))

    def repr_out_err(self, colitem): 
        for parent in colitem.listchain(): 
            for name, obj in zip(['out', 'err'], parent._getouterr()): 
                if obj: 
                    self.out.sep("- ", "%s: recorded std%s" % (parent.name, name))
                    self.out.line(obj)

def repr_pythonversion():
    v = py.std.sys.version_info
    try:
        return "%s.%s.%s-%s-%s" % v
    except ValueError:
        return str(v)
