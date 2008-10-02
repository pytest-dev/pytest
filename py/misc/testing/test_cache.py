import py
from py.__.misc.cache import BuildcostAccessCache, AgingCache

class BasicCacheAPITest:
    cache = None
    def test_getorbuild(self):
        val = self.cache.getorbuild(-42, lambda: 42)
        assert val == 42
        val = self.cache.getorbuild(-42, lambda: 23)
        assert val == 42

    def test_cache_get_key_error(self):
        assert self.cache.getentry(-23) == None

    def test_delentry_non_raising(self):
        val = self.cache.getorbuild(100, lambda: 100)
        self.cache.delentry(100)
        assert self.cache.getentry(100) is None

    def test_delentry_raising(self):
        val = self.cache.getorbuild(100, lambda: 100)
        self.cache.delentry(100)
        py.test.raises(KeyError, "self.cache.delentry(100, raising=True)")

class TestBuildcostAccess(BasicCacheAPITest):
    cache = BuildcostAccessCache(maxentries=128)

    def test_cache_works_somewhat_simple(self):
        cache = BuildcostAccessCache()
        # the default ._time() call used by
        # BuildcostAccessCache.build can 
        # result into time()-time() == 0 which makes the below
        # test fail randomly.  Let's rather use incrementing
        # numbers instead. 
        cache._time = py.std.itertools.count().next
        for x in range(cache.maxentries):
            y = cache.getorbuild(x, lambda: x)
            assert x == y
        for x in range(cache.maxentries):
            assert cache.getorbuild(x, None) == x
        for x in range(cache.maxentries/2):
            assert cache.getorbuild(x, None) == x
            assert cache.getorbuild(x, None) == x
            assert cache.getorbuild(x, None) == x
        val = cache.getorbuild(cache.maxentries * 2, lambda: 42)
        assert val == 42
        # check that recently used ones are still there
        # and are not build again
        for x in range(cache.maxentries/2):
            assert cache.getorbuild(x, None) == x
        assert cache.getorbuild(cache.maxentries*2, None) == 42


class TestAging(BasicCacheAPITest):
    maxsecs = 0.02
    cache = AgingCache(maxentries=128, maxseconds=maxsecs)

    def test_cache_eviction(self):
        self.cache.getorbuild(17, lambda: 17)
        endtime = py.std.time.time() + self.maxsecs * 10 
        while py.std.time.time() < endtime: 
            if self.cache.getentry(17) is None: 
                break 
            py.std.time.sleep(self.maxsecs*0.3) 
        else: 
            py.test.fail("waiting for cache eviction failed") 

def test_prune_lowestweight(): 
    maxsecs = 0.05 
    cache = AgingCache(maxentries=10, maxseconds=maxsecs)
    for x in range(cache.maxentries): 
        cache.getorbuild(x, lambda: x) 
    py.std.time.sleep(maxsecs*1.1) 
    cache.getorbuild(cache.maxentries+1, lambda: 42) 
