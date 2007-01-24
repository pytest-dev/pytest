
""" test source browser abilities
"""

from py.__.apigen.source.browser import parse_path, Class, Function, Method
import py

def test_browser():
    tmp = py.test.ensuretemp("sourcebrowser")
    tmp.ensure("a.py").write(py.code.Source("""
    def f():
        pass
    
    def g():
        pass
        
    class X:
        pass
        
    class Z(object):
        x = 1
        def zzz(self):
            1
            2
            3
            4
    """))
    mod = parse_path(tmp.join("a.py"))
    assert isinstance(mod.g, Function)
    assert isinstance(mod.Z, Class)
    py.test.raises(AttributeError, "mod.zzz")
    assert mod.g.firstlineno == 5
    assert mod.g.name == "g"
    assert mod.g.endlineno == 6
    assert mod.X.firstlineno == 8
    assert mod.X.endlineno == 9
    assert mod.Z.bases == ["object"]
    assert isinstance(mod.Z.zzz, Method)
    assert mod.Z.zzz.firstlineno == 13
    assert mod.Z.zzz.endlineno == 17

def test_if_browser():
    tmp = py.test.ensuretemp("sourcebrowser")
    tmp.ensure("b.py").write(py.code.Source("""
        if 1:
            def f():
                pass
        if 0:
            def g():
                pass
    """))
    mod = parse_path(tmp.join("b.py"))
    assert isinstance(mod.f, Function)
    py.test.raises(AttributeError, 'mod.g')

def test_bases():
    tmp = py.test.ensuretemp("sourcebrowser")
    tmp.ensure("c.py").write(py.code.Source("""
    import py
    class Dir(py.test.collect.Directory):
        pass
    """))
    mod = parse_path(tmp.join("c.py"))
    # if it does not rise it's ok for now
    #
    
def test_importing_goes_wrong():
    tmp = py.test.ensuretemp("sourcebrowserimport")
    tmp.ensure("x.py").write(py.code.Source("""
        import aslkdjaslkdjasdl
    """))
    mod = parse_path(tmp.join("x.py"))

    tmp.ensure("y.py").write(py.code.Source("""
        raise KeyboardInterrupt 
    """))
    py.test.raises(KeyboardInterrupt, 'parse_path(tmp.join("y.py"))')
    
    # if it does not rise it's ok for now
    #
