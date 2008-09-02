"""
    test support code
 
    makeuniquepyfile(source) generates a per-test-run-unique directory and test_*.py file 

    for analyzing events an EventSorter instance is returned for both of: 
    * events_from_cmdline(args): inprocess-run of cmdline invocation
    * events_from_session(session): inprocess-run of given session
    
    eventappender(config): for getting all events in a list: 
"""
import py
from py.__.test import event
from fnmatch import fnmatch

def eventappender(session):
    l = []
    def app(ev):
        print ev
        l.append(ev)
    session.bus.subscribe(app)
    return l 

def initsorter_from_cmdline(args=None):
    if args is None: 
        args = []
    config = py.test.config._reparse(args)
    session = config.initsession()
    sorter = EventSorter(config, session)
    return sorter 

def getcolitems(config):
    return [config.getfsnode(arg) for arg in config.args]

def events_from_cmdline(args=None):
    sorter = initsorter_from_cmdline(args)
    sorter.session.main(getcolitems(sorter.session.config))
    return sorter 

def events_from_runsource(source):
    source = py.code.Source(source)
    tfile = makeuniquepyfile(source) 
    return events_from_cmdline([tfile])

def events_from_session(session):
    sorter = EventSorter(session.config, session)
    session.main(getcolitems(session.config))
    return sorter 

class EventSorter(object):
    def __init__(self, config, session=None):
        self.config = config
        self.session = session
        self.cls2events = d = {}
        def app(event):
            print "[event]", event
            for cls in py.std.inspect.getmro(event.__class__):
                if cls is not object: 
                    d.setdefault(cls, []).append(event) 
        session.bus.subscribe(app)

    def get(self, cls):
        return self.cls2events.get(cls, [])

    def listoutcomes(self):
        passed = []
        skipped = []
        failed = []
        for ev in self.get(event.ItemTestReport):
            if ev.passed: 
                passed.append(ev) 
            elif ev.skipped: 
                skipped.append(ev) 
            elif ev.failed:
                failed.append(ev) 
        return passed, skipped, failed 

    def countoutcomes(self):
        return map(len, self.listoutcomes())

    def assertoutcome(self, passed=0, skipped=0, failed=0):
        realpassed, realskipped, realfailed = self.listoutcomes()
        assert passed == len(realpassed)
        assert skipped == len(realskipped)
        assert failed == len(realfailed)

    def getfailedcollections(self):
        l = []
        for ev in self.get(event.CollectionReport):
            if ev.failed:
               l.append(ev) 
        return l

    def getreport(self, inamepart): 
        """ return a testreport whose dotted import path matches """
        l = []
        for rep in self.get(event.ItemTestReport):
            if inamepart in rep.colitem.listnames():
                l.append(rep)
        if len(l) != 1:
            raise ValueError("did not find exactly one testreport"
                             "found" + str(l))
        return l[0]
            

counter = py.std.itertools.count().next
def makeuniquepyfile(source):
    dirname = "test_%d" %(counter(),)
    tmpdir = py.test.ensuretemp(dirname) 
    p = tmpdir.join(dirname + ".py")
    assert not p.check()
    p.write(py.code.Source(source))
    print "created test file", p
    p.dirpath("__init__.py").ensure() 
    return p

def getItemTestReport(source, tb="long"):
    tfile = makeuniquepyfile(source)
    sorter = events_from_cmdline([tfile, "--tb=%s" %tb])
    # get failure base info 
    failevents = sorter.get(event.ItemTestReport)
    assert len(failevents) == 1
    return failevents[0],tfile

def assert_lines_contain_lines(lines1, lines2):
    """ assert that lines2 are contained (linearly) in lines1. 
        return a list of extralines found.
    """
    __tracebackhide__ = True
    if isinstance(lines2, str):
        lines2 = py.code.Source(lines2)
    if isinstance(lines2, py.code.Source):
        lines2 = lines2.strip().lines

    extralines = []
    lines1 = lines1[:]
    nextline = None
    for line in lines2:
        nomatchprinted = False
        while lines1:
            nextline = lines1.pop(0)
            if line == nextline:
                print "exact match:", repr(line)
                break 
            elif fnmatch(nextline, line):
                print "fnmatch:", repr(line)
                print "   with:", repr(nextline)
                break
            else:
                if not nomatchprinted:
                    print "nomatch:", repr(line)
                    nomatchprinted = True
                print "    and:", repr(nextline)
            extralines.append(nextline)
        else:
            if line != nextline:
                #__tracebackhide__ = True
                raise AssertionError("expected line not found: %r" % line)
    extralines.extend(lines1)
    return extralines 

# XXX below some code to help with inlining examples 
#     as source code.  
#
class FileCreation(object):
    def setup_method(self, method):
        self.tmpdir = py.test.ensuretemp("%s_%s" % 
            (self.__class__.__name__, method.__name__))
    def makepyfile(self, **kwargs):
        return self._makefile('.py', **kwargs)
    def maketxtfile(self, **kwargs):
        return self._makefile('.txt', **kwargs)
    def _makefile(self, ext, **kwargs):
        ret = None
        for name, value in kwargs.iteritems():
            p = self.tmpdir.join(name).new(ext=ext)
            source = py.code.Source(value)
            p.write(str(py.code.Source(value)).lstrip())
            if ret is None:
                ret = p
        return ret 

    def parseconfig(self, *args):
        return py.test.config._reparse(list(args))
 
class InlineCollection(FileCreation):
    """ helps to collect and run test functions inlining other test functions. """

    def getmodulecol(self, source, configargs=(), withsession=False):
        self.tmpdir.ensure("__init__.py")
        kw = {"test_" + self.tmpdir.basename: py.code.Source(source).strip()}
        path = self.makepyfile(**kw)
        self.config = self.parseconfig(path, *configargs)
        if withsession:
            self.session = self.config.initsession()
        return self.config.getfsnode(path)

    def getitems(self, source):
        modulecol = self.getmodulecol(source)
        return modulecol.collect()

    def getitem(self, source, funcname="test_func"):
        modulecol = self.getmodulecol(source)
        item = modulecol.join(funcname) 
        assert item is not None, "%r item not found in module:\n%s" %(funcname, source)
        return item 

    def runitem(self, func, funcname="test_func", **runnerargs):
        item = self.getitem(func, funcname=funcname)
        runner = self.getrunner()
        return runner(item, **runnerargs)

class InlineSession(InlineCollection):
    def parse_and_run(self, *args):
        config = self.parseconfig(*args)
        session = config.initsession()
        sorter = EventSorter(config, session)
        session.main()
        return sorter

def popvalue(stringio):
    value = stringio.getvalue().rstrip()
    stringio.truncate(0)
    return value

def assert_stringio_contains_lines(stringio, tomatchlines):
    stringio.seek(0)
    l = stringio.readlines()
    l = map(str.rstrip, l)
    assert_lines_contain_lines(l, tomatchlines)
