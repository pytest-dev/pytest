import py

pytest_plugins = "pytester"

def pytest_collect_file(path, parent):
    if path.basename.startswith("pytest_") and path.ext == ".py":
        mod = parent.Module(path, parent=parent)
        return mod

# decorate testdir to contain plugin under test 
def pytest_funcarg__testdir(request):
    testdir = request.getfuncargvalue("testdir")
    #for obj in (request.cls, request.module):
    #    if hasattr(obj, 'testplugin'): 
    #        testdir.plugins.append(obj.testplugin)
    #        break
    #else:
    modname = request.module.__name__.split(".")[-1] 
    if modname.startswith("pytest_"):
        testdir.plugins.append(vars(request.module))
        testdir.plugins.append(modname) 
    #elif modname.startswith("test_pytest"):
    #    pname = modname[5:]
    #    assert pname not in testdir.plugins
    #    testdir.plugins.append(pname) 
    #    #testdir.plugins.append(vars(request.module))
    else:
        pass # raise ValueError("need better support code")
    return testdir

