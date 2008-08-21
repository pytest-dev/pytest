"""Defines a safe repr function. This will always return a string of "reasonable" length
no matter what the object does in it's own repr function. Let's examine what can go wrong
in an arbitrary repr function.
The default repr will return something like (on Win32 anyway):
<foo.bar object at 0x008D5650>. Well behaved user-defined repr() methods will do similar.
The usual expectation is that repr will return a single line string.

1. However, the repr method can raise an exception of an arbitrary type.

Also, the return value may not be as expected:
 2. The return value may not be a string!
 3. The return value may not be a single line string, it may contain line breaks.
 4. The method may enter a loop and never return.
 5. The return value may be enormous, eg range(100000)
 
 The standard library has a nice implementation in the repr module that will do the job,
 but the exception
 handling is silent, so the the output contains no clue that repr() call raised an
 exception. I would like to be told if repr raises an exception, it's a serious error, so 
 a sublass of repr overrides the method that does repr for class instances."""


import repr
import __builtin__

 
class SafeRepr(repr.Repr):
    def __init__(self, *args, **kwargs):
        repr.Repr.__init__(self, *args, **kwargs)
        # Do we need a commandline switch for this?
        self.maxstring = 240 # 3 * 80 chars
        self.maxother = 160    # 2 * 80 chars

    def repr(self, x):
        return self._callhelper(repr.Repr.repr, self, x)

    def repr_instance(self, x, level):
        return self._callhelper(__builtin__.repr, x)
        
    def _callhelper(self, call, x, *args):
        try:
            # Try the vanilla repr and make sure that the result is a string
            s = call(x, *args)
        except (KeyboardInterrupt, MemoryError, SystemExit):
            raise
        except Exception ,e:
            try:
                exc_name = e.__class__.__name__
            except:
                exc_name = 'unknown'
            try:
                exc_info = str(e)
            except:
                exc_info = 'unknown'
            return '<[%s("%s") raised in repr()] %s object at 0x%x>' % \
                (exc_name, exc_info, x.__class__.__name__, id(x))
        except:
            try:
                name = x.__class__.__name__
            except:
                name = 'unknown'
            return '<[unknown exception raised in repr()] %s object at 0x%x>' % \
                (name, id(x))
        if len(s) > self.maxstring:
            i = max(0, (self.maxstring-3)//2)
            j = max(0, self.maxstring-3-i)
            s = s[:i] + '...' + s[len(s)-j:]
        return s


_repr = SafeRepr().repr
