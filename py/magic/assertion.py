import __builtin__, sys
import py
from py.__.magic import exprinfo

BuiltinAssertionError = __builtin__.AssertionError

class AssertionError(BuiltinAssertionError):
    def __init__(self, *args):
        BuiltinAssertionError.__init__(self, *args)
        if args: 
            try:
                self.msg = str(args[0])
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.msg = "<[broken __repr__] %s at %0xd>" %(
                    args[0].__class__, id(args[0]))
            
        else: 
            f = sys._getframe(1)
            try:
                source = py.code.Frame(f).statement
                source = str(source.deindent()).strip()
            except py.error.ENOENT:
                source = None
                # this can also occur during reinterpretation, when the
                # co_filename is set to "<run>".
            if source:
                self.msg = exprinfo.interpret(source, f, should_fail=True)
                if not self.args:
                    self.args = (self.msg,)
            else:
                self.msg = None

def invoke():
    py.magic.patch(__builtin__, 'AssertionError', AssertionError)
def revoke():
    py.magic.revert(__builtin__, 'AssertionError')
