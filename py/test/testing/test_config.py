from __future__ import generators
import py

def test_tmpdir():
    d1 = py.test.ensuretemp('hello') 
    d2 = py.test.ensuretemp('hello') 
    assert d1 == d2
    assert d1.check(dir=1) 

def test_config_cmdline_options(): 
    o = py.test.ensuretemp('configoptions') 
    o.ensure("conftest.py").write(py.code.Source(""" 
        import py
        def _callback(option, opt_str, value, parser, *args, **kwargs):
            option.tdest = True
        Option = py.test.config.Option
        option = py.test.config.addoptions("testing group", 
            Option('-g', '--glong', action="store", default=42,
                   type="int", dest="gdest", help="g value."), 
            # XXX note: special case, option without a destination
            Option('-t', '--tlong', action="callback", callback=_callback,
                    help='t value'),
            )
        """))
    old = o.chdir() 
    try: 
        config = py.test.config._reparse(['-g', '17'])
    finally: 
        old.chdir() 
    assert config.option.gdest == 17 

def test_parsing_again_fails():
    dir = py.test.ensuretemp("parsing_again_fails")
    config = py.test.config._reparse([str(dir)])
    py.test.raises(AssertionError, "config.parse([])")

def test_config_getvalue_honours_conftest():
    o = py.test.ensuretemp('testconfigget') 
    o.ensure("conftest.py").write("x=1")
    o.ensure("sub", "conftest.py").write("x=2 ; y = 3")
    config = py.test.config._reparse([str(o)])
    assert config.getvalue("x") == 1
    assert config.getvalue("x", o.join('sub')) == 2
    py.test.raises(KeyError, "config.getvalue('y')")
    config = py.test.config._reparse([str(o.join('sub'))])
    assert config.getvalue("x") == 2
    assert config.getvalue("y") == 3
    assert config.getvalue("x", o) == 1
    py.test.raises(KeyError, 'config.getvalue("y", o)')


def test_siblingconftest_fails_maybe():
    from py.__.test import config
    cfg = config.Config()
    o = py.test.ensuretemp('siblingconftest')
    o.ensure("__init__.py")
    o.ensure("sister1", "__init__.py")
    o.ensure("sister1", "conftest.py").write(py.code.Source("""
        x = 2
    """))
        
    o.ensure("sister2", "__init__.py")
    o.ensure("sister2", "conftest.py").write(py.code.Source("""
        raise SyntaxError
    """))

    assert cfg.getvalue(path=o.join('sister1'), name='x') == 2
    old = o.chdir()
    try:
        print py.process.cmdexec("py.test sister1")
        o.join('sister1').chdir()
        print py.process.cmdexec("py.test") 
    finally:
        old.chdir()
