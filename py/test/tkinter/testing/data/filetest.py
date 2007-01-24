import py

def test_one(): 
    assert 42 == 42

class TestClass(object): 
    def test_method_one(self): 
        assert 42 == 42 

def test_print_and_fail():
    print 'STDOUT',
    print >>py.std.sys.stderr, 'STDERR',
    py.test.fail()
