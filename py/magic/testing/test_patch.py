from py.test import raises
from py.magic import patch, revert

def test_patch_revert():
    class a:
        pass
    raises(AttributeError, "patch(a, 'i', 42)")

    a.i = 42
    patch(a, 'i', 23)
    assert a.i == 23
    revert(a, 'i')
    assert a.i == 42

def test_double_patch():
    class a:
        i = 42
    assert patch(a, 'i', 2) == 42
    assert patch(a, 'i', 3) == 2
    assert a.i == 3
    assert revert(a, 'i') == 3
    assert a.i == 2
    assert revert(a, 'i') == 2
    assert a.i == 42

def test_valueerror():
    class a:
        i = 2
        pass
    raises(ValueError, "revert(a, 'i')")

