
class TestPyfuncHooks:
    def test_pyfunc_call(self, testdir):
        item = testdir.getitem("def test_func(): raise ValueError")
        config = item.config
        class MyPlugin1:
            def pytest_pyfunc_call(self, pyfuncitem, *args, **kwargs):
                raise ValueError
        class MyPlugin2:
            def pytest_pyfunc_call(self, pyfuncitem, *args, **kwargs):
                return True
        config.pluginmanager.register(MyPlugin1())
        config.pluginmanager.register(MyPlugin2())
        config.hook.pytest_pyfunc_call(pyfuncitem=item)
