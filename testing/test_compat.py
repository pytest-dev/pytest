from _pytest.compat import is_generator


def test_is_generator():
    def zap():
        yield

    def foo():
        pass

    assert is_generator(zap)
    assert not is_generator(foo)
