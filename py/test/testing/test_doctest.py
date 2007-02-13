
import py
from py.__.test.doctest import DoctestText
from py.__.test.outcome import Skipped, Failed, Passed, Outcome

def test_simple_docteststring():
    testitem = DoctestText(name="dummy", parent=None)
    testitem._setcontent("""
    >>> i = 0
    >>> i + 1
    1
    """)
    res = testitem.run()
    assert res is None
    
def test_simple_docteststring_failing():
    testitem = DoctestText(name="dummy2", parent=None)
    testitem._setcontent("""
    >>> i = 0
    >>> i + 1
    2
    """)
    py.test.raises(Failed, "testitem.run()")
   

def test_collect_doctest_files_with_test_prefix():
    o = py.test.ensuretemp("testdoctest")
    checkfile = o.ensure("test_something.txt")
    o.ensure("whatever.txt")
    checkfile.write(py.code.Source("""
        alskdjalsdk
        >>> i = 5
        >>> i-1
        4
    """))
    for x in (o, checkfile): 
        #print "checking that %s returns custom items" % (x,) 
        config = py.test.config._reparse([x])
        col = config._getcollector(x)
        items = list(col._tryiter(py.test.collect.Item))
        assert len(items) == 1
        assert isinstance(items[0], DoctestText)
   
     
