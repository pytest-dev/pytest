import pytest
import sys
import gc

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
            return line.startswith('f') and ("deleted" not in line and
                'mem' not in line and "txt" not in line and 'cwd' not in line)

        open_files = []

        for line in out.split("\n"):
            if isopen(line):
                fields = line.split('\0')
                fd = fields[0][1:]
                filename = fields[1][1:]
                if filename.startswith('/'):
                    open_files.append((fd, filename))

        return open_files

    def matching_platform(self):
        try:
            py.process.cmdexec("lsof -v")
        except py.process.cmdexec.Error:
            return False
        else:
            return True

    @pytest.hookimpl_opts(hookwrapper=True, tryfirst=True)
    def pytest_runtest_item(self, item):
        lines1 = self.get_open_files()
        yield
        if hasattr(sys, "pypy_version_info"):
            gc.collect()
        lines2 = self.get_open_files()

        new_fds = set([t[0] for t in lines2]) - set([t[0] for t in lines1])
        leaked_files = [t for t in lines2 if t[0] in new_fds]
        if leaked_files:
            error = []
            error.append("***** %s FD leakage detected" % len(leaked_files))
            error.extend([str(f) for f in leaked_files])
            error.append("*** Before:")
            error.extend([str(f) for f in lines1])
            error.append("*** After:")
            error.extend([str(f) for f in lines2])
            error.append(error[0])
            error.append("*** function %s:%s: %s " % item.location)
            pytest.fail("\n".join(error), pytrace=False)


def pytest_addoption(parser):
    parser.addoption('--lsof',
           action="store_true", dest="lsof", default=False,
           help=("run FD checks if lsof is available"))


def pytest_configure(config):
    if config.getvalue("lsof"):
        checker = LsofFdLeakChecker()
        if checker.matching_platform():
            config.pluginmanager.register(checker)


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
