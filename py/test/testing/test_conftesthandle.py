import py
from py.__.test.conftesthandle import Conftest

class TestConftestValueAccessGlobal:
    def setup_class(cls):
        # if we have "global" conftests (i.e. no __init__.py
        # and thus no further import scope) it should still all work 
        # because "global" conftests are imported with a
        # mangled module name (related to their actual path) 
        cls.basedir = d = py.test.ensuretemp(cls.__name__)
        d.ensure("adir/conftest.py").write("a=1 ; Directory = 3")
        d.ensure("adir/b/conftest.py").write("b=2 ; a = 1.5")

    def test_basic_init(self):
        conftest = Conftest()
        conftest.setinitial([self.basedir.join("adir")])
        assert conftest.rget("a") == 1

    def test_immediate_initialiation_and_incremental_are_the_same(self):
        conftest = Conftest()
        snap0 = len(conftest._path2confmods)
        conftest.getconftestmodules(self.basedir)
        snap1 = len(conftest._path2confmods)
        #assert len(conftest._path2confmods) == snap1 + 1
        conftest.getconftestmodules(self.basedir.join('adir'))
        assert len(conftest._path2confmods) == snap1 + 1
        conftest.getconftestmodules(self.basedir.join('b'))
        assert len(conftest._path2confmods) == snap1 + 2

    def test_default_Module_setting_is_visible_always(self):
        for path in self.basedir.parts():
            conftest = Conftest(path) 
            #assert conftest.lget("Module") == py.test.collect.Module
            assert conftest.rget("Module") == py.test.collect.Module

    def test_default_has_lower_prio(self):
        conftest = Conftest(self.basedir.join("adir"))
        assert conftest.rget('Directory') == 3
        #assert conftest.lget('Directory') == py.test.collect.Directory 
        
    def test_value_access_not_existing(self):
        conftest = Conftest(self.basedir)
        py.test.raises(KeyError, "conftest.rget('a')")
        #py.test.raises(KeyError, "conftest.lget('a')")

    def test_value_access_by_path(self):
        conftest = Conftest(self.basedir)
        assert conftest.rget("a", self.basedir.join('adir')) == 1
        #assert conftest.lget("a", self.basedir.join('adir')) == 1
        assert conftest.rget("a", self.basedir.join('adir', 'b')) == 1.5 
        #assert conftest.lget("a", self.basedir.join('adir', 'b')) == 1
        #assert conftest.lget("b", self.basedir.join('adir', 'b')) == 2
        #assert py.test.raises(KeyError, 
        #    'conftest.lget("b", self.basedir.join("a"))'
        #)

    def test_value_access_with_init_one_conftest(self):
        conftest = Conftest(self.basedir.join('adir'))
        assert conftest.rget("a") == 1
        #assert conftest.lget("a") == 1

    def test_value_access_with_init_two_conftests(self):
        conftest = Conftest(self.basedir.join("adir", "b"))
        conftest.rget("a") == 1.5
        #conftest.lget("a") == 1
        #conftest.lget("b") == 1

    def test_value_access_with_confmod(self):
        topdir = self.basedir.join("adir", "b")
        topdir.ensure("xx", dir=True)
        conftest = Conftest(topdir)
        mod, value = conftest.rget_with_confmod("a", topdir)
        assert  value == 1.5
        path = py.path.local(mod.__file__)
        assert path.dirpath() == self.basedir.join("adir", "b")
        assert path.purebasename == "conftest"

class TestConftestValueAccessInPackage(TestConftestValueAccessGlobal):
    def setup_class(cls):
        TestConftestValueAccessGlobal.__dict__['setup_class'](cls)
        d = cls.basedir 
        d.ensure("adir/__init__.py")
        d.ensure("adir/b/__init__.py")
        

        
        
        

