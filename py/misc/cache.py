"""
This module contains multithread-safe cache implementations.

All Caches have a

    __getitem__  and  getorbuild(key, builder) method

where the latter either just return a cached value or
first builds the value.

"""
import py
gettime = py.std.time.time

class WeightedCountingEntry(object):
    def __init__(self, value, oneweight):
        self.num = 1
        self._value = value
        self.oneweight = oneweight

    def weight():
        def fget(self):
            return (self.num * self.oneweight, self.num)
        return property(fget, None, None, "cumulative weight")
    weight = weight()

    def value():
        def fget(self):
            # you need to protect against mt-access at caller side!
            self.num += 1
            return self._value
        return property(fget, None, None)
    value = value()

    def __repr__(self):
        return "<%s weight=%s>" % (self.__class__.__name__, self.weight) 

class BasicCache(object):
    def __init__(self, maxentries=128):
        self.maxentries = maxentries
        self.prunenum = int(maxentries - maxentries/8)
        self._lock = py.std.threading.RLock()
        self._dict = {}

    def getentry(self, key):
        lock = self._lock
        lock.acquire()
        try:
            return self._dict.get(key, None)
        finally:
            lock.release()

    def putentry(self, key, entry):
        self._lock.acquire()
        try:
            self._prunelowestweight()
            self._dict[key] = entry
        finally:
            self._lock.release()

    def delentry(self, key, raising=False):
        self._lock.acquire()
        try:
            try:
                del self._dict[key]
            except KeyError:
                if raising:
                    raise
        finally:
            self._lock.release()

    def getorbuild(self, key, builder):
        entry = self.getentry(key)
        if entry is None:
            entry = self.build(key, builder)
        return entry.value

    def _prunelowestweight(self):
        """ prune out entries with lowest weight. """
        # note: must be called with acquired self._lock!
        numentries = len(self._dict)
        if numentries >= self.maxentries:
            # evict according to entry's weight
            items = [(entry.weight, key) for key, entry in self._dict.iteritems()]
            items.sort()
            index = numentries - self.prunenum
            if index > 0:
                for weight, key in items[:index]:
                    del self._dict[key]

class BuildcostAccessCache(BasicCache):
    """ A BuildTime/Access-counting cache implementation.
        the weight of a value is computed as the product of

            num-accesses-of-a-value * time-to-build-the-value

        The values with the least such weights are evicted
        if the cache maxentries threshold is superceded.
        For implementation flexibility more than one object
        might be evicted at a time.
    """
    # time function to use for measuring build-times
    _time = gettime

    def build(self, key, builder):
        start = self._time()
        val = builder()
        end = self._time()
        entry = WeightedCountingEntry(val, end-start)
        self.putentry(key, entry)
        return entry

class AgingCache(BasicCache):
    """ This cache prunes out cache entries that are too old.
    """
    def __init__(self, maxentries=128, maxseconds=10.0):
        super(AgingCache, self).__init__(maxentries)
        self.maxseconds = maxseconds

    def getentry(self, key):
        self._lock.acquire()
        try:
            try:
                entry = self._dict[key]
            except KeyError:
                entry = None
            else:
                if entry.isexpired():
                    del self._dict[key]
                    entry = None
            return entry
        finally:
            self._lock.release()

    def build(self, key, builder):
        ctime = gettime()
        val = builder()
        entry = AgingEntry(val, ctime + self.maxseconds)
        self.putentry(key, entry)
        return entry

class AgingEntry(object):
    def __init__(self, value, expirationtime):
        self.value = value
        self.weight = expirationtime

    def isexpired(self):
        t = py.std.time.time()
        return t >= self.weight 
