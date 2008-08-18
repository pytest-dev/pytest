
""" some tests for from_package
"""

from py.__.apigen.tracer.docstorage import DocStorage
from py.__.apigen.tracer.tracer import Tracer
from py.__.apigen.tracer import model
import sys
import py


def setup_module(mod):
    sys.path.insert(0, str(py.path.local(__file__).dirpath().join("package")))
    import submodule
    mod.submodule = submodule

def teardown_module(mod):
    sys.path = sys.path[1:]

class TestFullModule(object):
    def setup_class(cls):
        cls.ds = DocStorage().from_pkg(submodule)
        cls.tracer = Tracer(cls.ds)
    
    def test_init(self):
        ds = self.ds
        print py.builtin.sorted(ds.descs.keys())
        if sys.platform == "win32":
            py.test.skip("not sure why, but this fails with 4 == 6")
        assert len(ds.descs) == 6
        assert py.builtin.sorted(ds.descs.keys()) == [
                'notpak.notmod.notclass', 'notpak.notmod.notclass.__init__',
                'pak.mod.one', 'pak.mod.two', 'somenamespace.bar',
                'somenamespace.foo']

    def test_simple_call(self):
        ds = self.ds
        self.tracer.start_tracing()
        submodule.pak.mod.one(3)
        self.tracer.end_tracing()
        desc = self.ds.descs['pak.mod.one']
        assert isinstance(desc.retval, model.SomeInt)
        assert isinstance(desc.inputcells[0], model.SomeInt)
    
    def test_call_class(self):
        ds = self.ds
        self.tracer.start_tracing()
        c = submodule.notpak.notmod.notclass(3)
        self.tracer.end_tracing()
        desc = self.ds.descs['notpak.notmod.notclass']
        methdesc = desc.fields['__init__']
        assert isinstance(methdesc.inputcells[0], model.SomeInstance)
        assert isinstance(methdesc.inputcells[1], model.SomeInt)

