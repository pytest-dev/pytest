# -*- coding: utf-8 -*-
import sys
import os
import tempfile
import subprocess
import py
from py.__.execnet import serializer


def _find_version(suffix=""):
    name = "python" + suffix
    executable = py.path.local.sysfind(name)
    if executable is None:
        py.test.skip("can't find a %r executable" % (name,))
    return executable

def setup_module(mod):
    mod.TEMPDIR = py.path.local(tempfile.mkdtemp())
    if sys.version_info > (3, 0):
        mod._py3_wrapper = PythonWrapper(py.path.local(sys.executable))
        mod._py2_wrapper = PythonWrapper(_find_version())
    else:
        mod._py3_wrapper = PythonWrapper(_find_version("3"))
        mod._py2_wrapper = PythonWrapper(py.path.local(sys.executable))
    mod._old_pypath = os.environ.get("PYTHONPATH")
    pylib = str(py.path.local(py.__file__).dirpath().join(".."))
    os.environ["PYTHONPATH"] = pylib

def teardown_module(mod):
    TEMPDIR.remove(True)
    if _old_pypath is not None:
        os.environ["PYTHONPATH"] = _old_pypath


class PythonWrapper(object):

    def __init__(self, executable):
        self.executable = executable

    def dump(self, obj_rep):
        script_file = TEMPDIR.join("dump.py")
        script_file.write("""
from py.__.execnet import serializer
import sys
if sys.version_info > (3, 0): # Need binary output
    sys.stdout = sys.stdout.detach()
saver = serializer.Serializer(sys.stdout)
saver.save(%s)""" % (obj_rep,))
        return self.executable.sysexec(script_file)

    def load(self, data, option_args=""):
        script_file = TEMPDIR.join("load.py")
        script_file.write(r"""
from py.__.execnet import serializer
import sys
if sys.version_info > (3, 0):
    sys.stdin = sys.stdin.detach()
options = serializer.UnserializationOptions(%s)
loader = serializer.Unserializer(sys.stdin, options)
obj = loader.load()
sys.stdout.write(type(obj).__name__ + "\n")
sys.stdout.write(repr(obj))""" % (option_args,))
        popen = subprocess.Popen([str(self.executable), str(script_file)],
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        stdout, stderr = popen.communicate(data.encode("latin-1"))
        ret = popen.returncode
        if ret:
            raise py.process.cmdexec.Error(ret, ret, str(self.executable),
                                           stdout, stderr)
        return [s.decode("ascii") for s in stdout.splitlines()]

    def __repr__(self):
        return "<PythonWrapper for %s>" % (self.executable,)


def pytest_funcarg__py2(request):
    return _py2_wrapper

def pytest_funcarg__py3(request):
    return _py3_wrapper

def pytest_funcarg__dump(request):
    py_dump = request.getfuncargvalue(request.param[0])
    return py_dump.dump

def pytest_funcarg__load(request):
    py_dump = request.getfuncargvalue(request.param[1])
    return py_dump.load

def pytest_generate_tests(metafunc):
    if 'dump' in metafunc.funcargnames and 'load' in metafunc.funcargnames:
        pys = 'py2', 'py3'
        for dump in pys:
            for load in pys:
                metafunc.addcall(id='%s to %s'%(dump, load), param=(dump, load))


class TestSerializer:

    def test_int(self, dump, load):
        p = dump(4)
        tp, v = load(p)
        assert tp == "int"
        assert int(v) == 4

    def test_bigint_should_fail(self):
        py.test.raises(serializer.SerializationError,
                       serializer.Serializer(py.io.BytesIO()).save,
                       123456678900)

    def test_float(self, dump, load):
        p = dump(3.25)
        tp, v = load(p)
        assert tp == "float"
        assert v == "3.25"

    def test_bytes(self, py2, py3):
        p = py3.dump("b'hi'")
        tp, v = py2.load(p)
        assert tp == "str"
        assert v == "'hi'"
        tp, v = py3.load(p)
        assert tp == "bytes"
        assert v == "b'hi'"

    def check_sequence(self, val, tp_name, rep, dump, load):
        p = dump(val)
        tp , v = load(p)
        assert tp == tp_name
        assert v == rep

    def test_list(self, dump, load):
        self.check_sequence([1, 2, 3], "list", "[1, 2, 3]", dump, load)

    @py.test.mark.xfail
    # I'm not sure if we need the complexity.
    def test_recursive_list(self, py2, py3):
        l = [1, 2, 3]
        l.append(l)
        p = py2.dump(l)
        tp, rep = py2.load(l)
        assert tp == "list"

    def test_tuple(self, dump, load):
        self.check_sequence((1, 2, 3), "tuple", "(1, 2, 3)", dump, load)

    def test_dict(self, dump, load):
        p = dump({6 : 2, (1, 2, 3) : 32})
        tp, v = load(p)
        assert tp == "dict"
        # XXX comparing dict reprs
        assert v == "{6: 2, (1, 2, 3): 32}"

    def test_string(self, py2, py3):
        p = py2.dump("'xyz'")
        tp, s = py2.load(p)
        assert tp == "str"
        assert s == "'xyz'"
        tp, s = py3.load(p)
        assert tp == "bytes"
        assert s == "b'xyz'"
        tp, s = py3.load(p, "True")
        assert tp == "str"
        assert s == "'xyz'"
        p = py3.dump("'xyz'")
        tp, s = py2.load(p, True)
        assert tp == "str"
        assert s == "'xyz'"

    def test_unicode(self, py2, py3):
        p = py2.dump("u'hi'")
        tp, s = py2.load(p)
        assert tp == "unicode"
        assert s == "u'hi'"
        tp, s = py3.load(p)
        assert tp == "str"
        assert s == "'hi'"
        p = py3.dump("'hi'")
        tp, s = py3.load(p)
        assert tp == "str"
        assert s == "'hi'"
        tp, s = py2.load(p)
        assert tp == "unicode"
        assert s == "u'hi'"
