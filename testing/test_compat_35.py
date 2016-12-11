from _pytest.compat import is_generator


def test_is_generator_py35():
    async def foo():
        await foo()

    async def bar():
        pass

    assert not is_generator(foo)
    assert not is_generator(bar)
