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
    config._basedir = py.path.local()
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
    if len(lines2) > config._numfiles + 3:
        error = []
        error.append("***** %s FD leackage detected" %
    (len(lines2)-config._numfiles))
        error.extend(lines2)
        error.append(error[0])
        # update numfile so that the overall test run continuess
        config._numfiles = len(lines2)
        raise AssertionError("\n".join(error))

def pytest_runtest_teardown(item, __multicall__):
    item.config._basedir.chdir()
    if hasattr(item.config, '_numfiles'):
        x = __multicall__.execute()
        check_open_files(item.config)
        return x

# XXX copied from execnet's conftest.py - needs to be merged
winpymap = {
    'python2.7': r'C:\Python27\python.exe',
    'python2.6': r'C:\Python26\python.exe',
    'python2.5': r'C:\Python25\python.exe',
    'python2.4': r'C:\Python24\python.exe',
    'python3.1': r'C:\Python31\python.exe',
    'python3.2': r'C:\Python32\python.exe',
    'python3.3': r'C:\Python33\python.exe',
    'python3.4': r'C:\Python34\python.exe',
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

@pytest.fixture(params=['python2.5', 'python2.6',
                        'python2.7', 'python3.2', "python3.3",
                        'pypy', 'jython'])
def anypython(request):
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
