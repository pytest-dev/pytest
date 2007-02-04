
class Message(object):
    def __init__(self, processor, *args): 
        self.content = args 
        self.processor = processor
        self.keywords = (processor.logger._ident, 
                         processor.name)

    def strcontent(self):
        return " ".join(map(str, self.content))

    def strprefix(self):
        return '[%s] ' % ":".join(map(str, self.keywords))

    def __str__(self):
        return self.strprefix() + self.strcontent() 
        
class Processor(object):
    def __init__(self, logger, name, consume): 
        self.logger = logger 
        self.name = name
        self.consume = consume 

    def __call__(self, *args): 
        try:
            consume = self.logger._override
        except AttributeError:
            consume = self.consume
        if consume is not None: 
            msg = Message(self, *args) 
            consume(msg) 

class Logger(object):
    _key2logger = {}

    def __init__(self, ident):
        self._ident = ident 
        self._key2logger[ident] = self 
        self._keywords = () 

    def set_sub(self, **kwargs): 
        for name, value in kwargs.items():
            self._setsub(name, value) 

    def ensure_sub(self, **kwargs): 
        for name, value in kwargs.items():
            if not hasattr(self, name):
                self._setsub(name, value) 

    def set_override(self, consumer):
        self._override = lambda msg: consumer(msg)

    def del_override(self):
        try:
            del self._override 
        except AttributeError:
            pass

    def _setsub(self, name, dest): 
        assert "_" not in name 
        setattr(self, name, Processor(self, name, dest))

def get(ident="global", **kwargs): 
    """ return the Logger with id 'ident', instantiating if appropriate """
    try:
        log = Logger._key2logger[ident]
    except KeyError:
        log = Logger(ident)
    log.ensure_sub(**kwargs)
    return log 

