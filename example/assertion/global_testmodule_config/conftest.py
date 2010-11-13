import py
mydir = py.path.local(__file__).dirpath()

def pytest_runtest_setup(item):
    if isinstance(item, pytest.Function):
        if not item.fspath.relto(mydir):
            return
        mod = item.getparent(pytest.Module).obj
        if hasattr(mod, 'hello'):
            py.builtin.print_("mod.hello", mod.hello)
