import pytest
import sys

pytest_plugins = "pytester",

import os, py
pid = os.getpid()

def pytest_addoption(parser):
    parser.addoption('--lsof',
           action="store_true", dest="lsof", default=False,
           help=("run FD checks if lsof is available"))

def pytest_configure(config):
    config.addinivalue_line("markers",
        "multi(arg=[value1,value2, ...]): call the test function "
        "multiple times with arg=value1, then with arg=value2, ... "
    )
    if config.getvalue("lsof"):
        try:
            out = py.process.cmdexec("lsof -p %d" % pid)
        except py.process.cmdexec.Error:
            pass
        else:
            config._numfiles = len(getopenfiles(out))

#def pytest_report_header():
#    return "pid: %s" % os.getpid()

def getopenfiles(out):
    def isopen(line):
        return ("REG" in line or "CHR" in line) and (
            "deleted" not in line and 'mem' not in line and "txt" not in line)
    return [x for x in out.split("\n") if isopen(x)]

def check_open_files(config):
    out2 = py.process.cmdexec("lsof -p %d" % pid)
    lines2 = getopenfiles(out2)
    if len(lines2) > config._numfiles + 1:
        error = []
        error.append("***** %s FD leackage detected" %
    (len(lines2)-config._numfiles))
        error.extend(lines2)
        error.append(error[0])
        # update numfile so that the overall test run continuess
        config._numfiles = len(lines2)
        raise AssertionError("\n".join(error))

def pytest_runtest_setup(item):
    item._oldir = py.path.local()

def pytest_runtest_teardown(item, __multicall__):
    item._oldir.chdir()
    if hasattr(item.config, '_numfiles'):
        x = __multicall__.execute()
        check_open_files(item.config)
        return x

def pytest_generate_tests(metafunc):
    multi = getattr(metafunc.function, 'multi', None)
    if multi is not None:
        assert len(multi.kwargs) == 1
        for name, l in multi.kwargs.items():
            for val in l:
                metafunc.addcall(funcargs={name: val})
    elif 'anypython' in metafunc.funcargnames:
        for name in ('python2.4', 'python2.5', 'python2.6',
                     'python2.7', 'python3.1', 'pypy', 'jython'):
            metafunc.addcall(id=name, param=name)

# XXX copied from execnet's conftest.py - needs to be merged
winpymap = {
    'python2.7': r'C:\Python27\python.exe',
    'python2.6': r'C:\Python26\python.exe',
    'python2.5': r'C:\Python25\python.exe',
    'python2.4': r'C:\Python24\python.exe',
    'python3.1': r'C:\Python31\python.exe',
}

def getexecutable(name, cache={}):
    try:
        return cache[name]
    except KeyError:
        executable = py.path.local.sysfind(name)
        if executable:
            if name == "jython":
                import subprocess
                popen = subprocess.Popen([str(executable), "--version"],
                    universal_newlines=True, stderr=subprocess.PIPE)
                out, err = popen.communicate()
                if not err or "2.5" not in err:
                    executable = None
                if "2.5.2" in err:
                    executable = None # http://bugs.jython.org/issue1790
        cache[name] = executable
        return executable

def pytest_funcarg__anypython(request):
    name = request.param
    executable = getexecutable(name)
    if executable is None:
        if sys.platform == "win32":
            executable = winpymap.get(name, None)
            if executable:
                executable = py.path.local(executable)
                if executable.check():
                    return executable
        pytest.skip("no suitable %s found" % (name,))
    return executable
