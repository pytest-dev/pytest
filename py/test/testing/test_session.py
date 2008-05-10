import py
from setupdata import setup_module # sets up global 'tmpdir' 
from py.__.test.outcome import Skipped, Failed, Passed, Outcome
from py.__.test.terminal.out import getout
from py.__.test.repevent import ReceivedItemOutcome, SkippedTryiter,\
     FailedTryiter

implied_options = {
    '-v': 'verbose', 
    '-l': 'showlocals',
    #'--runbrowser': 'startserver and runbrowser', XXX starts browser
}

conflict_options = ('--looponfailing --pdb',
                    '--dist --pdb', 
                    '--exec=%s --pdb' % py.std.sys.executable,
                   )

def getoutcomes(all):
    return [i.outcome for i in all if isinstance(i, ReceivedItemOutcome)]
    

def getpassed(all):
    return [i for i in getoutcomes(all) if i.passed]

def getskipped(all):
    return [i for i in getoutcomes(all) if i.skipped] + \
           [i for i in all if isinstance(i, SkippedTryiter)]

def getfailed(all):
    return [i for i in getoutcomes(all) if i.excinfo] + \
           [i for i in all if isinstance(i, FailedTryiter)]

def test_conflict_options():
    for spec in conflict_options: 
        opts = spec.split()
        yield check_conflict_option, opts

def check_conflict_option(opts):
    print "testing if options conflict:", " ".join(opts)
    config = py.test.config._reparse(opts + [datadir/'filetest.py'])
    py.test.raises((ValueError, SystemExit), """
        config.initsession()
    """)
    
def test_implied_options():
    for key, expr in implied_options.items():
        yield check_implied_option, [key], expr

def check_implied_option(opts, expr):
    config = py.test.config._reparse(opts + [datadir/'filetest.py'])
    session = config.initsession()
    assert eval(expr, session.config.option.__dict__)

def test_default_session_options():
    for opts in ([], ['-l'], ['-s'], ['--tb=no'], ['--tb=short'], 
                 ['--tb=long'], ['--fulltrace'], ['--nomagic'], 
                 ['--traceconfig'], ['-v'], ['-v', '-v']):
        yield runfiletest, opts

def runfiletest(opts):
    config = py.test.config._reparse(opts + [datadir/'filetest.py'])
    all = []
    session = config.initsession()
    session.main(all.append)
    assert len(getfailed(all)) == 2 
    assert not getskipped(all)

def test_is_not_boxed_by_default():
    config = py.test.config._reparse([datadir])
    assert not config.option.boxed

class TestKeywordSelection: 
    def test_select_simple(self):
        def check(keyword, name):
            config = py.test.config._reparse([datadir/'filetest.py', 
                                                   '-s', '-k', keyword])
            all = []
            session = config._getsessionclass()(config)
            session.main(all.append)
            outcomes = [i for i in all if isinstance(i, ReceivedItemOutcome)]
            assert len(getfailed(all)) == 1 
            assert outcomes[0].item.name == name
            l = getskipped(all)
            assert len(l) == 1

        for keyword in ['test_one', 'est_on']:
            check(keyword, 'test_one')
        check('TestClass.test', 'test_method_one')

    def test_select_extra_keywords(self):
        o = tmpdir.ensure('selecttest', dir=1)
        tfile = o.join('test_select.py').write(py.code.Source("""
            def test_1():
                pass 
            class TestClass: 
                def test_2(self): 
                    pass
        """))
        conftest = o.join('conftest.py').write(py.code.Source("""
            import py
            class Class(py.test.collect.Class): 
                def _keywords(self):
                    return ['xxx', self.name]
        """))
        for keyword in ('xxx', 'xxx test_2', 'TestClass', 'xxx -test_1', 
                        'TestClass test_2', 'xxx TestClass test_2',): 
            config = py.test.config._reparse([o, '-s', '-k', keyword])
            all = []
            session = config._getsessionclass()(config)
            session.main(all.append)
            print "keyword", repr(keyword)
            l = getpassed(all)
            outcomes = [i for i in all if isinstance(i, ReceivedItemOutcome)]
            assert len(l) == 1
            assert outcomes[0].item.name == 'test_2'
            l = getskipped(all)
            assert l[0].item.name == 'test_1'

    def test_select_starton(self):
        config = py.test.config._reparse([datadir/'testevenmore.py', 
                                          '-j', '-k', "test_three"])
        all = []
        session = config._getsessionclass()(config)
        session.main(all.append)
        assert len(getpassed(all)) == 2
        assert len(getskipped(all)) == 2
        
   
class TestTerminalSession:
    def mainsession(self, *args):
        from py.__.test.session import Session
        from py.__.test.terminal.out import getout
        config = py.test.config._reparse(list(args))
        all = []
        session = Session(config)
        session.main(all.append)
        return session, all

    def test_terminal(self): 
        session, all = self.mainsession(datadir / 'filetest.py')
        outcomes = getoutcomes(all)
        assert len(getfailed(all)) == 2

    def test_syntax_error_module(self): 
        session, all = self.mainsession(datadir / 'syntax_error.py')
        l = getfailed(all)
        assert len(l) == 1
        out = l[0].excinfo.exconly()
        assert out.find(str('syntax_error.py')) != -1
        assert out.find(str('not python')) != -1

    def test_exit_first_problem(self): 
        session, all = self.mainsession("--exitfirst", 
                                        datadir / 'filetest.py')
        assert session.config.option.exitfirst
        assert len(getfailed(all)) == 1 
        assert not getpassed(all)

    def test_generator_yields_None(self): 
        o = tmpdir.ensure('generatornonetest', dir=1)
        tfile = o.join('test_generatornone.py')
        tfile.write(py.code.Source("""
            def test_1():
                yield None 
        """))
        session, all = self.mainsession(o) 
        #print out
        failures = getfailed(all)
        out = failures[0].excinfo.exconly()
        i = out.find('TypeError') 
        assert i != -1 

    def test_capturing_hooks_simple(self): 
        o = tmpdir.ensure('capturing', dir=1)
        tfile = o.join('test_capturing.py').write(py.code.Source("""
            import py
            print "module level output"
            def test_capturing():
                print 42
                print >>py.std.sys.stderr, 23 
            def test_capturing_error():
                print 1
                print >>py.std.sys.stderr, 2
                raise ValueError
        """))
        conftest = o.join('conftest.py').write(py.code.Source("""
            import py
            class Function(py.test.collect.Function): 
                def startcapture(self): 
                    self._mycapture = None
                    
                def finishcapture(self): 
                    self._testmycapture = None
        """))
        session, all = self.mainsession(o)
        l = getpassed(all)
        outcomes = getoutcomes(all)
        assert len(l) == 1
        item = all[3].item # item is not attached to outcome, but it's the
        # started before
        assert hasattr(item, '_testmycapture')
        print item._testmycapture

        assert isinstance(item.parent, py.test.collect.Module)

    def test_raises_output(self): 
        o = tmpdir.ensure('raisestest', dir=1)
        tfile = o.join('test_raisesoutput.py')
        tfile.write(py.code.Source("""
            import py
            def test_raises_doesnt():
                py.test.raises(ValueError, int, "3")
        """))
        session, all = self.mainsession(o)
        outcomes = getoutcomes(all)
        out = outcomes[0].excinfo.exconly()
        if not out.find("DID NOT RAISE") != -1: 
            print out
            py.test.fail("incorrect raises() output") 

    def test_order_of_execution(self): 
        o = tmpdir.ensure('ordertest', dir=1)
        tfile = o.join('test_orderofexecution.py')
        tfile.write(py.code.Source("""
            l = []
            def test_1():
                l.append(1)
            def test_2():
                l.append(2)
            def test_3():
                assert l == [1,2]
            class Testmygroup:
                reslist = l
                def test_1(self):
                    self.reslist.append(1)
                def test_2(self):
                    self.reslist.append(2)
                def test_3(self):
                    self.reslist.append(3)
                def test_4(self):
                    assert self.reslist == [1,2,1,2,3]
        """))

        session, all = self.mainsession(o)
        assert len(getfailed(all)) == 0 
        assert len(getpassed(all)) == 7 
        # also test listnames() here ... 

    def test_nested_import_error(self): 
        o = tmpdir.ensure('Ians_importfailure', dir=1) 
        tfile = o.join('test_import_fail.py')
        tfile.write(py.code.Source("""
            import import_fails
            def test_this():
                assert import_fails.a == 1
        """))
        o.join('import_fails.py').write(py.code.Source("""
            import does_not_work 
            a = 1
        """))
        session, all = self.mainsession(o)
        l = getfailed(all)
        assert len(l) == 1 
        out = l[0].excinfo.exconly()
        assert out.find('does_not_work') != -1 

    def test_safe_repr(self):
        session, all = self.mainsession(datadir/'brokenrepr.py')
        #print 'Output of simulated "py.test brokenrepr.py":'
        #print all

        l = getfailed(all)
        assert len(l) == 2
        out = l[0].excinfo.exconly()
        assert out.find("""[Exception("Ha Ha fooled you, I'm a broken repr().") raised in repr()]""") != -1 #'
        out = l[1].excinfo.exconly()
        assert out.find("[unknown exception raised in repr()]") != -1
        
def test_skip_reasons():
    tmp = py.test.ensuretemp("check_skip_reasons")
    tmp.ensure("test_one.py").write(py.code.Source("""
        import py
        def test_1():
            py.test.skip(py.test.broken('stuff'))
        
        def test_2():
            py.test.skip(py.test.notimplemented('stuff'))
    """))
    tmp.ensure("__init__.py")
    config = py.test.config._reparse([tmp])
    all = []
    session = config.initsession()
    session.main(all.append)
    skips = getskipped(all)
    assert len(skips) == 2
    assert str(skips[0].skipped.value) == 'Broken: stuff'
    assert str(skips[1].skipped.value) == 'Not implemented: stuff'
    
