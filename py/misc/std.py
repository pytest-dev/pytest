
import sys

class Std(object):
    """ lazily import standard modules """
    def __init__(self):
        self.__dict__ = sys.modules

    def __getattr__(self, name):
        return __import__(name)

std = Std()
