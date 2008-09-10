import py, sys
from py.__.test.event import EventBus

class Warning(py.std.exceptions.DeprecationWarning):
    def __init__(self, msg, path, lineno):
        self.msg = msg
        self.path = path
        self.lineno = lineno 
    def __repr__(self):
        return "%s:%d: %s" %(self.path, self.lineno+1, self.msg)
    def __str__(self):
        return self.msg 

class WarningBus(object):
    def __init__(self):
        self._eventbus = EventBus()

    def subscribe(self, callable):
        self._eventbus.subscribe(callable)

    def unsubscribe(self, callable):
        self._eventbus.unsubscribe(callable)

    def _setforwarding(self):
        self._eventbus.subscribe(self._forward)
    def _forward(self, warning):
        py.std.warnings.warn_explicit(warning, category=Warning, 
            filename=str(warning.path), 
            lineno=warning.lineno,
            registry=py.std.warnings.__dict__.setdefault(
                "__warningsregistry__", {})
        )
        
    def apiwarn(self, startversion, msg, stacklevel=1):
        # below is mostly COPIED from python2.4/warnings.py's def warn()
        # Get context information
        msg = "%s (since version %s)" %(msg, startversion)
        self.warn(msg, stacklevel=stacklevel+1)

    def warn(self, msg, stacklevel=1):
        try:
            caller = sys._getframe(stacklevel)
        except ValueError:
            globals = sys.__dict__
            lineno = 1
        else:
            globals = caller.f_globals
            lineno = caller.f_lineno
        if '__name__' in globals:
            module = globals['__name__']
        else:
            module = "<string>"
        filename = globals.get('__file__')
        if filename:
            fnl = filename.lower()
            if fnl.endswith(".pyc") or fnl.endswith(".pyo"):
                filename = filename[:-1]
        else:
            if module == "__main__":
                try:
                    filename = sys.argv[0]
                except AttributeError:
                    # embedded interpreters don't have sys.argv, see bug #839151
                    filename = '__main__'
            if not filename:
                filename = module
        path = py.path.local(filename)
        warning = Warning(msg, path, lineno)
        self._eventbus.notify(warning)

# singleton api warner for py lib 
apiwarner = WarningBus()
apiwarner._setforwarding()
APIWARN = apiwarner.apiwarn
