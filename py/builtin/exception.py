try:
    BaseException = BaseException
except NameError:
    BaseException = Exception

try:
    GeneratorExit = GeneratorExit
except NameError:
    class GeneratorExit(Exception):
        """ This exception is never raised, it is there to make it possible to
        write code compatible with CPython 2.5 even in lower CPython
        versions."""
        pass
    GeneratorExit.__module__ = 'exceptions'
