# -*- coding: utf-8 -*-
import shutil
import py
from py.__.execnet import serializer

def setup_module(mod):
    mod._save_python3 = serializer._INPY3

def teardown_module(mod):
    serializer._setup_version_dependent_constants()

def _dump(obj):
    stream = py.io.BytesIO()
    saver = serializer.Serializer(stream)
    saver.save(obj)
    return stream.getvalue()

def _load(serialized, str_coerion):
    stream = py.io.BytesIO(serialized)
    opts = serializer.UnserializationOptions(str_coerion)
    unserializer = serializer.Unserializer(stream, opts)
    return unserializer.load()

def _run_in_version(is_py3, func, *args):
    serializer._INPY3 = is_py3
    serializer._setup_version_dependent_constants()
    try:
        return func(*args)
    finally:
        serializer._INPY3 = _save_python3

def dump_py2(obj):
    return _run_in_version(False, _dump, obj)

def dump_py3(obj):
    return _run_in_version(True, _dump, obj)

def load_py2(serialized, str_coercion=False):
    return _run_in_version(False, _load, serialized, str_coercion)

def load_py3(serialized, str_coercion=False):
    return _run_in_version(True, _load, serialized, str_coercion)

try:
    bytes
except NameError:
    bytes = str


def pytest_funcarg__py2(request):
    return _py2_wrapper

def pytest_funcarg__py3(request):
    return _py3_wrapper

class TestSerializer:

    def test_int(self):
        for dump in dump_py2, dump_py3:
            p = dump_py2(4)
            for load in load_py2, load_py3:
                i = load(p)
                assert isinstance(i, int)
                assert i == 4
            py.test.raises(serializer.SerializationError, dump, 123456678900)

    def test_bytes(self):
        for dump in dump_py2, dump_py3:
            p = dump(serializer._b('hi'))
            for load in load_py2, load_py3:
                s = load(p)
                assert isinstance(s, serializer.bytes)
                assert s == serializer._b('hi')

    def check_sequence(self, seq):
        for dump in dump_py2, dump_py3:
            p = dump(seq)
            for load in load_py2, load_py3:
                l = load(p)
                assert l == seq

    def test_list(self):
        self.check_sequence([1, 2, 3])

    @py.test.mark.xfail
    # I'm not sure if we need the complexity.
    def test_recursive_list(self):
        l = [1, 2, 3]
        l.append(l)
        self.check_sequence(l)

    def test_tuple(self):
        self.check_sequence((1, 2, 3))

    def test_dict(self):
        for dump in dump_py2, dump_py3:
            p = dump({"hi" : 2, (1, 2, 3) : 32})
            for load in load_py2, load_py3:
                d = load(p, True)
                assert d == {"hi" : 2, (1, 2, 3) : 32}

    def test_string(self):
        py.test.skip("will rewrite")
        p = dump_py2("xyz")
        s = load_py2(p)
        assert isinstance(s, str)
        assert s == "xyz"
        s = load_py3(p)
        assert isinstance(s, bytes)
        assert s == serializer.b("xyz")
        p = dump_py2("xyz")
        s = load_py3(p, True)
        assert isinstance(s, serializer._unicode)
        assert s == serializer.unicode("xyz")
        p = dump_py3("xyz")
        s = load_py2(p, True)
        assert isinstance(s, str)
        assert s == "xyz"

    def test_unicode(self):
        py.test.skip("will rewrite")
        for dump, uni in (dump_py2, serializer._unicode), (dump_py3, str):
            p = dump(uni("xyz"))
            for load in load_py2, load_py3:
                s = load(p)
                assert isinstance(s, serializer._unicode)
                assert s == serializer._unicode("xyz")
