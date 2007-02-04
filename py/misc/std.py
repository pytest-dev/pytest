
import sys

class Std(object):
    """ (lazily) hook into the top-level standard library """

    def __init__(self):
        self.__dict__ = sys.modules

    def __getattr__(self, name):
        try:
            m = __import__(name)
        except ImportError:
            raise AttributeError("py.std: could not import %s" % name)
        return m

std = Std()
