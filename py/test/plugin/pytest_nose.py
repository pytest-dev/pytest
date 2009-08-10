"""nose-compatibility plugin: allow to run nose test suites natively. 

This is an experimental plugin for allowing to run tests written 
in the 'nosetests' style with py.test.  
nosetests is a popular clone 
of py.test and thus shares some philosophy.  This plugin is an 
attempt to understand and neutralize differences.  It allows to 
run nosetests' own test suite and a number of other test suites 
without problems. 

Usage
-------------

If you type::

    py.test -p nose 

where you would type ``nosetests``, you can run your nose style tests.  
You might also try to run without the nose plugin to see where your test
suite is incompatible to the default py.test. 

To avoid the need for specifying a command line option you can set an environment 
variable::

    PYTEST_PLUGINS=nose  

or create a ``conftest.py`` file in your test directory or below::

    # conftest.py 
    pytest_plugins = "nose", 

If you find issues or have suggestions you may run:: 

    py.test -p nose --pastebin=all 

to create a URL of a test run session and send it with comments to the issue
tracker or mailing list. 

Known issues 
------------------

- nose-style doctests are not collected and executed correctly,
  also fixtures don't work. 

"""
import py
import inspect
import sys

def pytest_runtest_makereport(__call__, item, call):
    SkipTest = getattr(sys.modules.get('nose', None), 'SkipTest', None)
    if SkipTest:
        if call.excinfo and call.excinfo.errisinstance(SkipTest):
            # let's substitute the excinfo with a py.test.skip one 
            call2 = call.__class__(lambda: py.test.skip(str(call.excinfo.value)), call.when)
            call.excinfo = call2.excinfo 

def pytest_report_iteminfo(item):
    # nose 0.11.1 uses decorators for "raises" and other helpers. 
    # for reporting progress by filename we fish for the filename 
    if isinstance(item, py.test.collect.Function):
        obj = item.obj
        if hasattr(obj, 'compat_co_firstlineno'):
            fn = sys.modules[obj.__module__].__file__ 
            if fn.endswith(".pyc"):
                fn = fn[:-1]
            #assert 0
            #fn = inspect.getsourcefile(obj) or inspect.getfile(obj)
            lineno = obj.compat_co_firstlineno    
            return py.path.local(fn), lineno, obj.__module__
    
def pytest_runtest_setup(item):
    if isinstance(item, (py.test.collect.Function)):
        if isinstance(item.parent, py.test.collect.Generator):
            gen = item.parent 
            if not hasattr(gen, '_nosegensetup'):
                call_optional(gen.obj, 'setup')
                if isinstance(gen.parent, py.test.collect.Instance):
                    call_optional(gen.parent.obj, 'setup')
                gen._nosegensetup = True
        call_optional(item.obj, 'setup')

def pytest_runtest_teardown(item):
    if isinstance(item, py.test.collect.Function):
        call_optional(item.obj, 'teardown')
        #if hasattr(item.parent, '_nosegensetup'):
        #    #call_optional(item._nosegensetup, 'teardown')
        #    del item.parent._nosegensetup

def pytest_make_collect_report(collector):
    if isinstance(collector, py.test.collect.Generator):
        call_optional(collector.obj, 'setup')

def call_optional(obj, name):
    method = getattr(obj, name, None)
    if method:
        method()
