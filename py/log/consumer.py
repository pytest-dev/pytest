import py
import sys

class File(object): 
    """ log consumer wrapping a file(-like) object
    """
    def __init__(self, f): 
        assert hasattr(f, 'write')
        assert isinstance(f, file) or not hasattr(f, 'open') 
        self._file = f 

    def __call__(self, msg): 
        """ write a message to the log """
        print >>self._file, str(msg)

class Path(object): 
    """ log consumer able to write log messages into
    """
    def __init__(self, filename, append=False, delayed_create=False,
            buffering=1): 
        self._append = append
        self._filename = filename
        self._buffering = buffering
        if not delayed_create:
            self._openfile()

    def _openfile(self):
        mode = self._append and 'a' or 'w'
        f = open(str(self._filename), mode, buffering=self._buffering)
        self._file = f

    def __call__(self, msg):
        """ write a message to the log """
        if not hasattr(self, "_file"):
            self._openfile()
        print >> self._file, msg

def STDOUT(msg): 
    """ consumer that writes to sys.stdout """
    print >>sys.stdout, str(msg) 

def STDERR(msg): 
    """ consumer that writes to sys.stderr """
    print >>sys.stderr, str(msg)

class Syslog:
    """ consumer that writes to the syslog daemon """

    for priority in "LOG_EMERG LOG_ALERT LOG_CRIT LOG_ERR LOG_WARNING LOG_NOTICE LOG_INFO LOG_DEBUG".split():
        try:
            exec("%s = py.std.syslog.%s" % (priority, priority))
        except AttributeError:
            pass
    
    def __init__(self, priority = None):
        self.priority = self.LOG_INFO
        if priority is not None:
            self.priority = priority

    def __call__(self, msg):
        """ write a message to the log """
        py.std.syslog.syslog(self.priority, str(msg))
        
    
def setconsumer(keywords, consumer): 
    """ create a consumer for a set of keywords """
    # normalize to tuples 
    if isinstance(keywords, str): 
        keywords = tuple(map(None, keywords.split()))
    elif hasattr(keywords, 'keywords'): 
        keywords = keywords.keywords 
    elif not isinstance(keywords, tuple): 
        raise TypeError("key %r is not a string or tuple" % (keywords,))
    if consumer is not None and not callable(consumer): 
        if not hasattr(consumer, 'write'): 
            raise TypeError("%r should be None, callable or file-like" % (consumer,))
        consumer = File(consumer)
    py.log.Producer(keywords).set_consumer(consumer)

