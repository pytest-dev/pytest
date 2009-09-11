import py

def pytest_runtest_setup(item):
    if isinstance(item, py.test.collect.Function):
        mod = item.getparent(py.test.collect.Module).obj
        if hasattr(mod, 'hello'):
            py.builtin.print_("mod.hello", mod.hello)
