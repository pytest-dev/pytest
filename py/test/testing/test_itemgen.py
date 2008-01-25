
import py
from py.__.test.session import itemgen
from py.__.test import repevent

class TestItemgen:
    def setup_class(cls):
        tmp = py.test.ensuretemp('itemgentest')
        tmp.ensure("__init__.py")
        tmp.ensure("test_one.py").write(py.code.Source("""
        def test_one():
            pass

        class TestX:
            def test_method_one(self):
                pass

        class TestY(TestX):
            pass
        """))
        tmp.ensure("test_two.py").write(py.code.Source("""
        import py
        py.test.skip('xxx')
        """))
        tmp.ensure("test_three.py").write("xxxdsadsadsadsa")
        cls.tmp = tmp
        
    def test_itemgen(self):
        l = []
        colitems = [py.test.collect.Directory(self.tmp)]
        gen = itemgen(None, colitems, l.append)
        items = [i for i in gen]
        assert len([i for i in l if isinstance(i, repevent.SkippedTryiter)]) == 1
        assert len([i for i in l if isinstance(i, repevent.FailedTryiter)]) == 1
        assert len(items) == 3
        assert items[0].name == 'test_one'
        assert items[1].name == 'test_method_one'
        assert items[2].name == 'test_method_one'
        
