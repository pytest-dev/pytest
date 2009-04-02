import py
from py.__.misc.warn import WarningPlugin
mypath = py.magic.autopath()

class TestWarningPlugin:
    def setup_method(self, method):
        self.bus = py._com.PyPlugins()
        self.wb = WarningPlugin(self.bus)
        self.bus.register(self)
        self.warnings = []

    def pyevent__WARNING(self, warning):
        self.warnings.append(warning)

    def test_event_generation(self):
        self.wb.warn("hello")
        assert len(self.warnings) == 1

    def test_location(self):
        self.wb.warn("again")
        warning = self.warnings[0] 
        lno = self.test_location.im_func.func_code.co_firstlineno + 1
        assert warning.lineno == lno
        assert warning.path == mypath 
        locstr = "%s:%d: " %(mypath, lno+1,)
        assert repr(warning).startswith(locstr)
        assert str(warning) == warning.msg 

    def test_stacklevel(self):
        def f():
            self.wb.warn("x", stacklevel=2)
        # 3
        # 4
        f()
        lno = self.test_stacklevel.im_func.func_code.co_firstlineno + 5
        warning = self.warnings[0]
        assert warning.lineno == lno

    def test_forwarding_to_warnings_module(self):
        py.test.deprecated_call(self.wb.warn, "x")

    def test_apiwarn(self):
        self.wb.apiwarn("3.0", "xxx")
        warning = self.warnings[0] 
        assert warning.msg == "xxx (since version 3.0)"

def test_default():
    from py.__.misc.warn import APIWARN
    assert py._com.pyplugins.isregistered(APIWARN.im_self)
