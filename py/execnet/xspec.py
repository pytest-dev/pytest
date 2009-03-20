
import py

class XSpec:
    """ Execution Specification: key1=value1//key2=value2 ... 
        * keys need to be unique within the specification scope 
        * neither key nor value are allowed to contain "//"
        * keys are not allowed to contain "=" 
        * keys are not allowed to start with underscore 
        * if no "=value" is given, assume a boolean True value 
    """
    def __init__(self, *strings):
        for string in strings:
            for keyvalue in string.split("//"):
                i = keyvalue.find("=")
                if i == -1:
                    setattr(self, keyvalue, True)
                else:
                    setattr(self, keyvalue[:i], keyvalue[i+1:])

    def __getattr__(self, name):
        if name[0] == "_":
            raise AttributeError(name) 
        return None

def makegateway(spec):
    pass

    
