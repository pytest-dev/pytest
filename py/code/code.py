import py
from py.__.code import source

class Code(object):
    """ wrapper around Python code objects """
    def __init__(self, rawcode):
        rawcode = getattr(rawcode, 'im_func', rawcode)
        rawcode = getattr(rawcode, 'func_code', rawcode)
        self.raw = rawcode 
        try:
            self.filename = rawcode.co_filename
            self.firstlineno = rawcode.co_firstlineno - 1
            self.name = rawcode.co_name
        except AttributeError: 
            raise TypeError("not a code object: %r" %(rawcode,))
        
    def __eq__(self, other): 
        return self.raw == other.raw

    def __ne__(self, other):
        return not self == other

    def new(self, rec=False, **kwargs): 
        """ return new code object with modified attributes. 
            if rec-cursive is true then dive into code 
            objects contained in co_consts. 
        """ 
        names = [x for x in dir(self.raw) if x[:3] == 'co_']
        for name in kwargs: 
            if name not in names: 
                raise TypeError("unknown code attribute: %r" %(name, ))
        if rec: 
            newconstlist = []
            co = self.raw
            cotype = type(co)
            for c in co.co_consts:
                if isinstance(c, cotype):
                    c = self.__class__(c).new(rec=True, **kwargs) 
                newconstlist.append(c)
            return self.new(rec=False, co_consts=tuple(newconstlist), **kwargs) 
        for name in names:
            if name not in kwargs:
                kwargs[name] = getattr(self.raw, name)
        return py.std.new.code(
                 kwargs['co_argcount'],
                 kwargs['co_nlocals'],
                 kwargs['co_stacksize'],
                 kwargs['co_flags'],
                 kwargs['co_code'],
                 kwargs['co_consts'],
                 kwargs['co_names'],
                 kwargs['co_varnames'],
                 kwargs['co_filename'],
                 kwargs['co_name'],
                 kwargs['co_firstlineno'],
                 kwargs['co_lnotab'],
                 kwargs['co_freevars'],
                 kwargs['co_cellvars'],
        )

    def path(self):
        """ return a py.path.local object pointing to the source code """
        fn = self.raw.co_filename 
        try:
            return fn.__path__
        except AttributeError:
            p = py.path.local(self.raw.co_filename)
            if not p.check(file=1):
                # XXX maybe try harder like the weird logic 
                # in the standard lib [linecache.updatecache] does? 
                p = self.raw.co_filename
            return p
                
    path = property(path, None, None, "path of this code object")

    def fullsource(self):
        """ return a py.code.Source object for the full source file of the code
        """
        full, _ = source.findsource(self.raw)
        return full
    fullsource = property(fullsource, None, None,
                          "full source containing this code object")
    
    def source(self):
        """ return a py.code.Source object for the code object's source only
        """
        # return source only for that part of code
        return py.code.Source(self.raw)

    def getargs(self):
        """ return a tuple with the argument names for the code object
        """
        # handfull shortcut for getting args
        raw = self.raw
        return raw.co_varnames[:raw.co_argcount]

