import sys
import py
from _pytest.assertion.util import BuiltinAssertionError
u = py.builtin._totext


class AssertionError(BuiltinAssertionError):
    def __init__(self, *args):
        BuiltinAssertionError.__init__(self, *args)
        if args:
            # on Python2.6 we get len(args)==2 for: assert 0, (x,y)
            # on Python2.7 and above we always get len(args) == 1
            # with args[0] being the (x,y) tuple.
            if len(args) > 1:
                toprint = args
            else:
                toprint = args[0]
            try:
                self.msg = u(toprint)
            except Exception:
                self.msg = u(
                    "<[broken __repr__] %s at %0xd>"
                    % (toprint.__class__, id(toprint)))
        else:
            f = py.code.Frame(sys._getframe(1))
            try:
                source = f.code.fullsource
                if source is not None:
                    try:
                        source = source.getstatement(f.lineno, assertion=True)
                    except IndexError:
                        source = None
                    else:
                        source = str(source.deindent()).strip()
            except py.error.ENOENT:
                source = None
                # this can also occur during reinterpretation, when the
                # co_filename is set to "<run>".
            if source:
                self.msg = reinterpret(source, f, should_fail=True)
            else:
                self.msg = "<could not determine information>"
            if not self.args:
                self.args = (self.msg,)

if sys.version_info > (3, 0):
    AssertionError.__module__ = "builtins"
    reinterpret_old = "old reinterpretation not available for py3"
else:
    from _pytest.assertion.oldinterpret import interpret as reinterpret_old
if sys.version_info >= (2, 6) or (sys.platform.startswith("java")):
    from _pytest.assertion.newinterpret import interpret as reinterpret
else:
    reinterpret = reinterpret_old
