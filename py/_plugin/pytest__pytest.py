import py

from py._test.pluginmanager import HookRelay

def pytest_funcarg___pytest(request):
    return PytestArg(request)

class PytestArg:
    def __init__(self, request):
        self.request = request 

    def gethookrecorder(self, hook):
        hookrecorder = HookRecorder(hook._registry)
        hookrecorder.start_recording(hook._hookspecs)
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
    def __init__(self, registry):
        self._registry = registry
        self.calls = []
        self._recorders = {}
        
    def start_recording(self, hookspecs):
        if not isinstance(hookspecs, (list, tuple)):
            hookspecs = [hookspecs]
        for hookspec in hookspecs:
            assert hookspec not in self._recorders 
            class RecordCalls: 
                _recorder = self 
            for name, method in vars(hookspec).items():
                if name[0] != "_":
                    setattr(RecordCalls, name, self._makecallparser(method))
            recorder = RecordCalls()
            self._recorders[hookspec] = recorder
            self._registry.register(recorder)
        self.hook = HookRelay(hookspecs, registry=self._registry, 
            prefix="pytest_")

    def finish_recording(self):
        for recorder in self._recorders.values():
            self._registry.unregister(recorder)
        self._recorders.clear()

    def _makecallparser(self, method):
        name = method.__name__
        args, varargs, varkw, default = py.std.inspect.getargspec(method)
        if not args or args[0] != "self":
            args.insert(0, 'self') 
        fspec = py.std.inspect.formatargspec(args, varargs, varkw, default)
        # we use exec because we want to have early type
        # errors on wrong input arguments, using
        # *args/**kwargs delays this and gives errors
        # elsewhere
        exec (py.code.compile("""
            def %(name)s%(fspec)s: 
                        self._recorder.calls.append(
                            ParsedCall(%(name)r, locals()))
        """ % locals()))
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
        for i, call in enumerate(self.calls):
            if call._name == name:
                del self.calls[i]
                return call 
        raise ValueError("could not find call %r" %(name, ))

    def getcall(self, name):
        l = self.getcalls(name)
        assert len(l) == 1, (name, l)
        return l[0]

