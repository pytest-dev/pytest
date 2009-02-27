import py

def pytest_pyfuncarg_pickletransport(pyfuncitem):
    return PickleTransport()

class PickleTransport:
    def __init__(self):
        from py.__.test.dsession.mypickle import ImmutablePickler
        self.p1 = ImmutablePickler(uneven=0)
        self.p2 = ImmutablePickler(uneven=1)

    def p1_to_p2(self, obj):
        return self.p2.loads(self.p1.dumps(obj))

    def p2_to_p1(self, obj):
        return self.p1.loads(self.p2.dumps(obj))

    def unifyconfig(self, config):
        p2config = self.p1_to_p2(config)
        p2config._initafterpickle(config.topdir)
        return p2config

class TestPickling:

    def test_pickle_config(self, pickletransport):
        config1 = py.test.config._reparse([])
        p2config = pickletransport.unifyconfig(config1)
        assert p2config.topdir == config1.topdir
        config_back = pickletransport.p2_to_p1(p2config)
        assert config_back is config1

    def test_pickle_module(self, testdir, pickletransport):
        modcol1 = testdir.getmodulecol("def test_one(): pass")
        pickletransport.unifyconfig(modcol1._config) 

        modcol2a = pickletransport.p1_to_p2(modcol1)
        modcol2b = pickletransport.p1_to_p2(modcol1)
        assert modcol2a is modcol2b

        modcol1_back = pickletransport.p2_to_p1(modcol2a)
        assert modcol1_back

    def test_pickle_func(self, testdir, pickletransport):
        modcol1 = testdir.getmodulecol("def test_one(): pass")
        pickletransport.unifyconfig(modcol1._config) 
        item = modcol1.collect_by_name("test_one")
        item2a = pickletransport.p1_to_p2(item)
        assert item is not item2a # of course
        assert item2a.name == item.name
        modback = pickletransport.p2_to_p1(item2a.parent)
        assert modback is modcol1

