import py

class _pytestPlugin:
    def pytest_funcarg___pytest(self, pyfuncitem):
        return PytestArg(pyfuncitem)

class PytestArg:
    def __init__(self, pyfuncitem):
        self.pyfuncitem = pyfuncitem 

    def getcallrecorder(self, apiclass, pyplugins=None):
        if pyplugins is None:
            pyplugins = self.pyfuncitem.config.pytestplugins.pyplugins
        callrecorder = CallRecorder(pyplugins)
        callrecorder.start_recording(apiclass)
        self.pyfuncitem.addfinalizer(callrecorder.finalize)
        return callrecorder 


class ParsedCall:
    def __init__(self, name, locals):
        assert '_name' not in locals 
        self.__dict__.update(locals)
        self.__dict__.pop('self')
        self._name = name 

    def __repr__(self):
        d = self.__dict__.copy()
        del d['_name']
        return "<ParsedCall %r(**%r)>" %(self._name, d)

class CallRecorder:
    def __init__(self, pyplugins):
        self._pyplugins = pyplugins
        self.calls = []
        self._recorders = {}
        
    def start_recording(self, apiclass):
        assert apiclass not in self._recorders 
        class RecordCalls: 
            _recorder = self 
        for name, method in vars(apiclass).items():
            if name[0] != "_":
                setattr(RecordCalls, name, self._getcallparser(method))
        recorder = RecordCalls()
        self._recorders[apiclass] = recorder
        self._pyplugins.register(recorder)

    def finalize(self):
        for recorder in self._recorders.values():
            self._pyplugins.unregister(recorder)

    def recordsmethod(self, name):
        for apiclass in self._recorders:
            if hasattr(apiclass, name):
                return True

    def _getcallparser(self, method):
        name = method.__name__
        args, varargs, varkw, default = py.std.inspect.getargspec(method)
        assert args[0] == "self"
        fspec = py.std.inspect.formatargspec(args, varargs, varkw, default)
        # we use exec because we want to have early type
        # errors on wrong input arguments, using
        # *args/**kwargs delays this and gives errors
        # elsewhere
        exec py.code.compile("""
            def %(name)s%(fspec)s: 
                        self._recorder.calls.append(
                            ParsedCall(%(name)r, locals()))
        """ % locals())
        return locals()[name]

    def popcall(self, name):
        for i, call in py.builtin.enumerate(self.calls):
            if call._name == name:
                del self.calls[i]
                return call 
        raise ValueError("could not find call %r in %r" %(name, self.calls))

    def getcalls(self, names):
        if isinstance(names, str):
            names = names.split()
        for name in names:
            for cls in self._recorders:
                if name in vars(cls):
                    break
            else:
                raise ValueError("callname %r not found in %r" %(
                name, self._recorders.keys()))
        l = []
        for call in self.calls:
            if call._name in names:
                l.append(call)
        return l

def test_generic(plugintester):
    plugintester.apicheck(_pytestPlugin)

def test_callrecorder_basic():
    pyplugins = py._com.PyPlugins() 
    rec = CallRecorder(pyplugins)
    class ApiClass:
        def xyz(self, arg):
            pass
    rec.start_recording(ApiClass)
    pyplugins.call_each("xyz", 123)
    call = rec.popcall("xyz")
    assert call.arg == 123 
    assert call._name == "xyz"
    py.test.raises(ValueError, "rec.popcall('abc')")

def test_functional(testdir, linecomp):
    sorter = testdir.inline_runsource("""
        import py
        pytest_plugins="_pytest"
        def test_func(_pytest):
            class ApiClass:
                def xyz(self, arg):  pass 
            rec = _pytest.getcallrecorder(ApiClass)
            class Plugin:
                def xyz(self, arg):
                    return arg + 1
            rec._pyplugins.register(Plugin())
            res = rec._pyplugins.call_firstresult("xyz", 41)
            assert res == 42
    """)
    sorter.assertoutcome(passed=1)
