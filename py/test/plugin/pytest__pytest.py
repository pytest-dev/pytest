import py

def pytest_funcarg___pytest(request):
    return PytestArg(request)

class PytestArg:
    def __init__(self, request):
        self.request = request 
        self.monkeypatch = self.request.getfuncargvalue("monkeypatch")
        self.comregistry = py._com.Registry()
        self.monkeypatch.setattr(py._com, 'comregistry', self.comregistry)

    def gethookrecorder(self, hookspecs, registry=None):
        if registry is not None:
            self.monkeypatch.setattr(py._com, 'comregistry', registry) 
            self.comregistry = registry 
        hookrecorder = HookRecorder(self.comregistry) 
        hookrecorder.start_recording(hookspecs)
        self.request.addfinalizer(hookrecorder.finish_recording)
        return hookrecorder 

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

class HookRecorder:
    def __init__(self, comregistry):
        self._comregistry = comregistry
        self.calls = []
        self._recorders = {}
        
    def start_recording(self, hookspecs):
        assert hookspecs not in self._recorders 
        class RecordCalls: 
            _recorder = self 
        for name, method in vars(hookspecs).items():
            if name[0] != "_":
                setattr(RecordCalls, name, self._makecallparser(method))
        recorder = RecordCalls()
        self._recorders[hookspecs] = recorder
        self._comregistry.register(recorder)
        self.hook = py._com.Hooks(hookspecs, registry=self._comregistry)

    def finish_recording(self):
        for recorder in self._recorders.values():
            self._comregistry.unregister(recorder)
        self._recorders.clear()

    def _makecallparser(self, method):
        name = method.__name__
        args, varargs, varkw, default = py.std.inspect.getargspec(method)
        if args and args[0] != "self":
            args.insert(0, 'self') 
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

    def popcall(self, name):
        for i, call in py.builtin.enumerate(self.calls):
            if call._name == name:
                del self.calls[i]
                return call 
        raise ValueError("could not find call %r" %(name, ))

    def getcall(self, name):
        l = self.getcalls(name)
        assert len(l) == 1, (name, l)
        return l[0]


def test_hookrecorder_basic():
    comregistry = py._com.Registry() 
    rec = HookRecorder(comregistry)
    class ApiClass:
        def xyz(self, arg):
            pass
    rec.start_recording(ApiClass)
    rec.hook.xyz(arg=123)
    call = rec.popcall("xyz")
    assert call.arg == 123 
    assert call._name == "xyz"
    py.test.raises(ValueError, "rec.popcall('abc')")

reg = py._com.comregistry
def test_functional_default(testdir, _pytest):
    assert _pytest.comregistry == py._com.comregistry 
    assert _pytest.comregistry != reg

def test_functional(testdir, linecomp):
    reprec = testdir.inline_runsource("""
        import py
        pytest_plugins="_pytest"
        def test_func(_pytest):
            class ApiClass:
                def xyz(self, arg):  pass 
            rec = _pytest.gethookrecorder(ApiClass)
            class Plugin:
                def xyz(self, arg):
                    return arg + 1
            rec._comregistry.register(Plugin())
            res = rec.hook.xyz(arg=41)
            assert res == [42]
    """)
    reprec.assertoutcome(passed=1)
