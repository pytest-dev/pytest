import py

pytest_plugins = "pytester", "plugintester"

class ConftestPlugin: 
    def pytest_collect_file(self, path, parent):
        if path.basename.startswith("pytest_") and path.ext == ".py":
            mod = parent.Module(path, parent=parent)
            return mod

