"""

   Pickling support for two processes that want to exchange 
   *immutable* object instances.  Immutable in the sense 
   that the receiving side of an object can modify its 
   copy but when it sends it back the original sending 
   side will continue to see its unmodified version
   (and no actual state will go over the wire).

   This module also implements an experimental 
   execnet pickling channel using this idea. 

"""

from cStringIO import StringIO
from pickle import Pickler, Unpickler
import py
from py.__.execnet.channel import Channel
import os
#debug = open("log-mypickle-%d" % os.getpid(), 'w')

class MyPickler(Pickler):
    """ Pickler with a custom memoize()
        to take care of unique ID creation. 
        See the usage in ImmutablePickler
        XXX we could probably extend Pickler 
            and Unpickler classes to directly
            update the other'S memos. 
    """
    def __init__(self, file, protocol, uneven):
        Pickler.__init__(self, file, protocol)
        self.uneven = uneven
        
    def memoize(self, obj):
        if self.fast:
            return
        assert id(obj) not in self.memo
        memo_len = len(self.memo)
        key = memo_len * 2 + self.uneven
        self.write(self.put(key))
        self.memo[id(obj)] = key, obj

class ImmutablePickler:
    def __init__(self, uneven, protocol=0):
        """ ImmutablePicklers are instantiated in Pairs. 
            The two sides need to create unique IDs
            while pickling their objects.  This is
            done by using either even or uneven 
            numbers, depending on the instantiation
            parameter.
        """
        self._picklememo = {}
        self._unpicklememo = {}
        self._protocol = protocol
        self.uneven = uneven and 1 or 0

    def selfmemoize(self, obj):
        # this is for feeding objects to ourselfes
        # which be the case e.g. if you want to pickle 
        # from a forked process back to the original 
        f = StringIO()
        pickler = MyPickler(f, self._protocol, uneven=self.uneven)
        pickler.memo = self._picklememo
        pickler.memoize(obj)
        self._updateunpicklememo()

    def dumps(self, obj):
        f = StringIO()
        pickler = MyPickler(f, self._protocol, uneven=self.uneven)
        pickler.memo = self._picklememo
        pickler.dump(obj)
        self._updateunpicklememo()
        #print >>debug, "dumped", obj 
        #print >>debug, "picklememo", self._picklememo
        return f.getvalue()

    def loads(self, string):
        f = StringIO(string)
        unpickler = Unpickler(f)
        unpickler.memo = self._unpicklememo
        res = unpickler.load()
        self._updatepicklememo()
        #print >>debug, "loaded", res
        #print >>debug, "unpicklememo", self._unpicklememo
        return res

    def _updatepicklememo(self):
        for x, obj in self._unpicklememo.items():
            self._picklememo[id(obj)] = (int(x), obj)

    def _updateunpicklememo(self):
        for key,obj in self._picklememo.values():
            key = str(key)
            if key in self._unpicklememo:
                assert self._unpicklememo[key] is obj
            self._unpicklememo[key] = obj

NO_ENDMARKER_WANTED = object()

class UnpickleError(Exception):
    """ Problems while unpickling. """
    def __init__(self, formatted):
        self.formatted = formatted
        Exception.__init__(self, formatted)
    def __str__(self):
        return self.formatted

class PickleChannel(object):
    """ PickleChannels wrap execnet channels 
        and allow to send/receive by using
        "immutable pickling". 
    """
    _unpicklingerror = None
    def __init__(self, channel):
        self._channel = channel
        # we use the fact that each side of a 
        # gateway connection counts with uneven
        # or even numbers depending on which 
        # side it is (for the purpose of creating
        # unique ids - which is what we need it here for)
        uneven = channel.gateway._channelfactory.count % 2 
        self._ipickle = ImmutablePickler(uneven=uneven) 
        self.RemoteError = channel.RemoteError

    def send(self, obj):
        if not isinstance(obj, Channel):
            pickled_obj = self._ipickle.dumps(obj)
            self._channel.send(pickled_obj)
        else:
            self._channel.send(obj)

    def receive(self):
        pickled_obj = self._channel.receive()
        return self._unpickle(pickled_obj)

    def _unpickle(self, pickled_obj):
        if isinstance(pickled_obj, self._channel.__class__):
            return pickled_obj
        return self._ipickle.loads(pickled_obj)

    def _getremoteerror(self):
        return self._unpicklingerror or self._channel._getremoteerror()

    def close(self):
        return self._channel.close()

    def isclosed(self):
        return self._channel.isclosed()

    def waitclose(self, timeout=None):
        return self._channel.waitclose(timeout=timeout)

    def setcallback(self, callback, endmarker=NO_ENDMARKER_WANTED):
        if endmarker is NO_ENDMARKER_WANTED:
            def unpickle_callback(pickled_obj):
                obj = self._unpickle(pickled_obj)
                callback(obj)
            self._channel.setcallback(unpickle_callback)
            return
        uniqueendmarker = object()
        def unpickle_callback(pickled_obj):
            if pickled_obj is uniqueendmarker:
                return callback(endmarker)
            try:
                obj = self._unpickle(pickled_obj)
            except KeyboardInterrupt:
                raise
            except:
                excinfo = py.code.ExceptionInfo()
                formatted = str(excinfo.getrepr(showlocals=True,funcargs=True))
                self._unpicklingerror = UnpickleError(formatted)
                callback(endmarker)
            else:
                callback(obj)
        self._channel.setcallback(unpickle_callback, uniqueendmarker)
