
import py

import errno

def test_error_classes():
    for name in errno.errorcode.values():
        x = getattr(py.error, name)
        assert issubclass(x, py.error.Error)
        assert issubclass(x, EnvironmentError)

def test_unknown_error(): 
    num = 3999
    cls = py.error._geterrnoclass(num)
    assert cls.__name__ == 'UnknownErrno%d' % (num,) 
    assert issubclass(cls, py.error.Error)
    assert issubclass(cls, EnvironmentError)
    cls2 = py.error._geterrnoclass(num)
    assert cls is cls2

