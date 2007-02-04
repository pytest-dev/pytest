"""
py lib's basic logging/tracing functionality 

    EXPERIMENTAL EXPERIMENTAL EXPERIMENTAL (especially the dispatching) 

WARNING: this module is not allowed to contain any 'py' imports, 
         Instead, it is very self-contained and should not depend on 
         CPython/stdlib versions, either.  One reason for these 
         restrictions is that this module should be sendable
         via py.execnet across the network in an very early phase.  
"""

class Message(object): 
    def __init__(self, keywords, args): 
        self.keywords = keywords 
        self.args = args 

    def content(self): 
        return " ".join(map(str, self.args))

    def prefix(self): 
        return "[%s] " % (":".join(self.keywords))

    def __str__(self): 
        return self.prefix() + self.content() 

class Producer(object):
    """ Log producer API which sends messages to be logged
        to a 'consumer' object, which then prints them to stdout,
        stderr, files, etc.
    """
    
    Message = Message  # to allow later customization 
    keywords2consumer = {}

    def __init__(self, keywords): 
        if isinstance(keywords, str): 
            keywords = tuple(keywords.split())
        self.keywords = keywords

    def __repr__(self):
        return "<py.log.Producer %s>" % ":".join(self.keywords) 

    def __getattr__(self, name):
        if '_' in name: 
            raise AttributeError, name
        producer = self.__class__(self.keywords + (name,))
        setattr(self, name, producer)
        return producer 
    
    def __call__(self, *args):
        """ write a message to the appropriate consumer(s) """
        func = self.get_consumer(self.keywords)
        if func is not None: 
            func(self.Message(self.keywords, args))
   
    def get_consumer(self, keywords): 
        """ return a consumer matching keywords
        
            tries to find the most suitable consumer by walking, starting from
            the back, the list of keywords, the first consumer matching a
            keyword is returned (falling back to py.log.default)
        """
        for i in range(len(self.keywords), 0, -1): 
            try: 
                return self.keywords2consumer[self.keywords[:i]]
            except KeyError: 
                continue
        return self.keywords2consumer.get('default', default_consumer)

    def set_consumer(self, consumer): 
        """ register a consumer matching our own keywords """
        self.keywords2consumer[self.keywords] = consumer 

default = Producer('default')

def _getstate(): 
    return Producer.keywords2consumer.copy()

def _setstate(state): 
    Producer.keywords2consumer.clear()
    Producer.keywords2consumer.update(state) 

def default_consumer(msg): 
    """ the default consumer, prints the message to stdout (using 'print') """
    print str(msg) 

Producer.keywords2consumer['default'] = default_consumer 
