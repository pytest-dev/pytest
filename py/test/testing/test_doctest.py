
import py
from py.__.test.outcome import Failed 
from py.__.test.testing.suptest import InlineCollection

def setup_module(mod):
    mod.tmp = py.test.ensuretemp(__name__) 

class TestDoctests(InlineCollection):
    def test_simple_docteststring(self):
        txtfile = self.maketxtfile(test_doc="""
            >>> i = 0
            >>> i + 1
            1
        """)
        config = self.parseconfig(txtfile)
        col = config.getfsnode(txtfile)
        testitem = col.join(txtfile.basename) 
        res = testitem.runtest()
        assert res is None
        

    def test_doctest_unexpected_exception(self):
        py.test.skip("implement nice doctest repr for unexpected exceptions")
        p = tmp.join("test_doctest_unexpected_exception")
        p.write(py.code.Source("""
            >>> i = 0
            >>> x
            2
        """))
        testitem = py.test.collect.DoctestFile(p).join(p.basename)
        excinfo = py.test.raises(Failed, "testitem.runtest()")
        repr = testitem.repr_failure(excinfo, ("", ""))
        assert repr.reprlocation 
