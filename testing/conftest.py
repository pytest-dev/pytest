import pytest
import sys

pytest_plugins = "pytester",

import os, py

class LsofFdLeakChecker(object):
    def get_open_files(self):
        out = self._exec_lsof()
        open_files = self._parse_lsof_output(out)
        return open_files

    def _exec_lsof(self):
        pid = os.getpid()
        return py.process.cmdexec("lsof -Ffn0 -p %d" % pid)

    def _parse_lsof_output(self, out):
        def isopen(line):
            return line.startswith('f') and (
                "deleted" not in line and 'mem' not in line and "txt" not in line and 'cwd' not in line)

        open_files = []

        for line in out.split("\n"):
            if isopen(line):
                fields = line.split('\0')
                fd = fields[0][1:]
                filename = fields[1][1:]
                if filename.startswith('/'):
                    open_files.append((fd, filename))

        return open_files


def pytest_addoption(parser):
    parser.addoption('--lsof',
           action="store_true", dest="lsof", default=False,
           help=("run FD checks if lsof is available"))

def pytest_runtest_setup(item):
    config = item.config
    config._basedir = py.path.local()
    if config.getvalue("lsof"):
        try:
            config._fd_leak_checker = LsofFdLeakChecker()
            config._openfiles = config._fd_leak_checker.get_open_files()
        except py.process.cmdexec.Error:
            pass

#def pytest_report_header():
#    return "pid: %s" % os.getpid()

def check_open_files(config):
    lines2 = config._fd_leak_checker.get_open_files()
    new_fds = set([t[0] for t in lines2]) - set([t[0] for t in config._openfiles])
    open_files = [t for t in lines2 if t[0] in new_fds]
    if open_files:
        error = []
        error.append("***** %s FD leakage detected" % len(open_files))
        error.extend([str(f) for f in open_files])
        error.append("*** Before:")
        error.extend([str(f) for f in config._openfiles])
        error.append("*** After:")
        error.extend([str(f) for f in lines2])
        error.append(error[0])
        raise AssertionError("\n".join(error))

def pytest_runtest_teardown(item, __multicall__):
    item.config._basedir.chdir()
    if hasattr(item.config, '_openfiles'):
        x = __multicall__.execute()
        check_open_files(item.config)
        return x

# XXX copied from execnet's conftest.py - needs to be merged
winpymap = {
    'python2.7': r'C:\Python27\python.exe',
    'python2.6': r'C:\Python26\python.exe',
    'python3.1': r'C:\Python31\python.exe',
    'python3.2': r'C:\Python32\python.exe',
    'python3.3': r'C:\Python33\python.exe',
    'python3.4': r'C:\Python34\python.exe',
    'python3.5': r'C:\Python35\python.exe',
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

@pytest.fixture(params=['python2.6', 'python2.7', 'python3.3', "python3.4",
                        'pypy', 'pypy3'])
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
