import py
import sys

pytest_plugins = "pytester",
collect_ignore = ['../build', '../doc/_build']

rsyncdirs = ['conftest.py', '../pytest', '../doc', '.']

import os, py
pid = os.getpid()

def pytest_addoption(parser):
    parser.addoption('--lsof',
           action="store_true", dest="lsof", default=False,
           help=("run FD checks if lsof is available"))

def pytest_configure(config):
    if config.getvalue("lsof"):
        try:
            out = py.process.cmdexec("lsof -p %d" % pid)
        except py.process.cmdexec.Error:
            pass
        else:
            config._numfiles = getopenfiles(out)

#def pytest_report_header():
#    return "pid: %s" % os.getpid()

def getopenfiles(out):
    def isopen(line):
        return ("REG" in line or "CHR" in line) and (
            "deleted" not in line and 'mem' not in line)
    return len([x for x in out.split("\n") if isopen(x)])

def pytest_unconfigure(config, __multicall__):
    if not hasattr(config, '_numfiles'):
        return
    __multicall__.execute()
    out2 = py.process.cmdexec("lsof -p %d" % pid)
    len2 = getopenfiles(out2)
    assert len2 < config._numfiles + 7, out2


def pytest_generate_tests(metafunc):
    multi = getattr(metafunc.function, 'multi', None)
    if multi is not None:
        assert len(multi.kwargs) == 1
        for name, l in multi.kwargs.items():
            for val in l:
                metafunc.addcall(funcargs={name: val})
    elif 'anypython' in metafunc.funcargnames:
        for name in ('python2.4', 'python2.5', 'python2.6',
                     'python2.7', 'python3.1', 'pypy-c', 'jython'):
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
        py.test.skip("no %s found" % (name,))
    return executable
