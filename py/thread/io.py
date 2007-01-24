
import thread

class ThreadOut(object): 
    """ A file like object that diverts writing operations 
        to per-thread writefuncs.  
        This is a py lib internal class and not meant for outer use
        or modification. 
    """
    def __new__(cls, obj, attrname): 
        """ Divert file output to per-thread writefuncs. 
            the given obj and attrname describe the destination 
            of the file.  
        """ 
        current = getattr(obj, attrname)
        if isinstance(current, cls): 
            current._used += 1
            return current 
        self = object.__new__(cls) 
        self._tid2out = {}
        self._used = 1 
        self._oldout = getattr(obj, attrname) 
        self._defaultwriter = self._oldout.write 
        self._address = (obj, attrname) 
        setattr(obj, attrname, self) 
        return self 

    def isatty(self): 
        # XXX 
        return False 

    def setdefaultwriter(self, writefunc): 
        self._defaultwriter = writefunc 

    def resetdefault(self): 
        self._defaultwriter = self._oldout.write

    def softspace(): 
        def fget(self): 
            return self._get()[0]
        def fset(self, value): 
            self._get()[0] = value 
        return property(fget, fset, None, "software attribute") 
    softspace = softspace()

    def deinstall(self): 
        self._used -= 1 
        x = self._used 
        if x <= 0: 
            obj, attrname = self._address 
            setattr(obj, attrname, self._oldout) 
        
    def setwritefunc(self, writefunc, tid=None): 
        assert callable(writefunc)
        if tid is None: 
            tid = thread.get_ident() 
        self._tid2out[tid] = [0, writefunc]

    def delwritefunc(self, tid=None, ignoremissing=True): 
        if tid is None: 
            tid = thread.get_ident() 
        try: 
            del self._tid2out[tid] 
        except KeyError: 
            if not ignoremissing: 
                raise 

    def _get(self): 
        tid = thread.get_ident() 
        try: 
            return self._tid2out[tid]
        except KeyError: 
            return getattr(self._defaultwriter, 'softspace', 0), self._defaultwriter 

    def write(self, data): 
        softspace, out = self._get() 
        out(data) 

    def flush(self): 
        pass 
   
