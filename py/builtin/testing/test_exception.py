import py

def test_BaseException():
    assert issubclass(IndexError, py.builtin.BaseException)
    assert issubclass(Exception, py.builtin.BaseException)
    assert issubclass(KeyboardInterrupt, py.builtin.BaseException)

    class MyRandomClass(object):
        pass
    assert not issubclass(MyRandomClass, py.builtin.BaseException)

    assert py.builtin.BaseException.__module__ == 'exceptions'
    assert Exception.__name__ == 'Exception'


def test_GeneratorExit():
    assert py.builtin.GeneratorExit.__module__ == 'exceptions'
    assert issubclass(py.builtin.GeneratorExit, Exception)
