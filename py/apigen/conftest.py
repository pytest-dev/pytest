import py

class ConftestPlugin:
    def pytest_addoption(self, parser):
        parser.addoption('--webcheck',
               action="store_true", dest="webcheck", default=False,
               help="run XHTML validation tests"
        )
