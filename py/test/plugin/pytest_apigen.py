import py

class ApigenPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup("apigen options")
        group.addoption('--apigen', action="store_true", dest="apigen",
                help="generate api documentation")
        #group.addoption('--apigenpath',
        #       action="store", dest="apigenpath",
        #       default="../apigen", 
        #       type="string",
        #       help="relative path to apigen doc output location (relative from py/)")
        #group.addoption('--docpath',
        #       action='store', dest='docpath',
        #       default="doc", type='string',
        #       help="relative path to doc output location (relative from py/)")

    def pytest_configure(self, config):
        if config.option.apigen:
            from py.__.apigen.tracer.tracer import Tracer, DocStorage
            self.pkgdir = py.path.local(config.args[0]).pypkgpath()
            apigenscriptpath = py.path.local(py.__file__).dirpath("apigen", "apigen.py")
            apigenscript = apigenscriptpath.pyimport()
            if not hasattr(apigenscript, 'get_documentable_items'):
                raise NotImplementedError("%r needs to provide get_documentable_items" %(
                    apigenscriptpath,))
            self.apigenscript = apigenscript
            pkgname, items = apigenscript.get_documentable_items(self.pkgdir)
            self.docstorage = DocStorage().from_dict(items,
                                                     module_name=pkgname)
            self.tracer = Tracer(self.docstorage)

    def pytest_pyfunc_call(self, pyfuncitem, args, kwargs):
        if hasattr(self, 'tracer'):
            self.tracer.start_tracing()
            try:
                pyfuncitem.obj(*args, **kwargs)
            finally:
                self.tracer.end_tracing()
            return True

    def pytest_terminal_summary(self, terminalreporter):
        if hasattr(self, 'tracer'):
            tr = terminalreporter
            from py.__.apigen.tracer.docstorage import DocStorageAccessor
            terminalreporter.write_sep("=", "apigen: building documentation")
            #assert hasattr(tr.config.option, 'apigenpath')
            capture = py.io.StdCaptureFD()
            try:
                self.apigenscript.build(
                    tr.config, 
                    self.pkgdir, 
                    DocStorageAccessor(self.docstorage),
                    capture)
            finally:
                capture.reset()
            terminalreporter.write_line("apigen build completed")

def test_generic(plugintester):
    plugintester.apicheck(ApigenPlugin)

def test_functional_simple(testdir):
    sub = testdir.tmpdir.mkdir("test_simple")
    sub.join("__init__.py").write(py.code.Source("""
        from py import initpkg 
        initpkg(__name__, exportdefs={
            'simple.f': ('./test_simple.py', 'f',),
        })
    """))
    pyfile = sub.join("test_simple.py")
    pyfile.write(py.code.Source("""
        def f(arg):
            pass
        def test_f():
            f(42)
    """))
    testdir.makepyfile(conftest="pytest_plugins='apigen'")
    result = testdir.runpytest(pyfile, "--apigen")
    result.stdout.fnmatch_lines([
            "*apigen: building documentation*", 
            "apigen build completed", 
    ])
