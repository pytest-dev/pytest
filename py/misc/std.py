
import sys

class Std(object):
    """ makes all standard python modules available as a lazily 
        computed attribute. 
    """ 

    def __init__(self):
        self.__dict__ = sys.modules

    def __getattr__(self, name):
        try:
            m = __import__(name)
        except ImportError:
            raise AttributeError("py.std: could not import %s" % name)
        return m

std = Std()
