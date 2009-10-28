""" log invocations of extension hooks to a file. """ 
import py

def pytest_addoption(parser):
    parser.addoption("--hooklog", dest="hooklog", default=None, 
        help="write hook calls to the given file.")

def pytest_configure(config):
    hooklog = config.getvalue("hooklog")
    if hooklog:
        config._hooklogfile = open(hooklog, 'w')
        config._hooklog_oldperformcall = config.hook._performcall
        config.hook._performcall = (lambda name, multicall: 
            logged_call(name=name, multicall=multicall, config=config))

def logged_call(name, multicall, config):
    f = config._hooklogfile
    f.write("%s(**%s)\n" % (name, multicall.kwargs))
    try:
        res = config._hooklog_oldperformcall(name=name, multicall=multicall)
    except:
        f.write("-> exception")
        raise
    f.write("-> %r" % (res,))
    return res

def pytest_unconfigure(config):
    try:
        del config.hook.__dict__['_performcall'] 
    except KeyError:
        pass
    else:
        config._hooklogfile.close()
