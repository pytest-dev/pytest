import py
from py.__.misc.warn import WarningBus
mypath = py.magic.autopath()

class TestWarningBus:
    def setup_method(self, method):
        self.wb = WarningBus()
        self.warnings = []
        self.wb.subscribe(self.warnings.append)

    def test_basic(self):
        self.wb.warn("hello")
        assert len(self.warnings) == 1
        self.wb.unsubscribe(self.warnings.append)
        self.wb.warn("this")
        assert len(self.warnings) == 1
        w = self.warnings[0]

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
        l = []
        self.wb.subscribe(l.append)
        def f():
            self.wb.warn("x", stacklevel=2)
        # 5
        # 6
        f()
        lno = self.test_stacklevel.im_func.func_code.co_firstlineno + 7
        warning = l[0]
        assert warning.lineno == lno

    def test_forwarding_to_warnings_module(self):
        self.wb._setforwarding()
        py.test.deprecated_call(self.wb.warn, "x")

    def test_apiwarn(self):
        self.wb.apiwarn("3.0", "xxx")
        warning = self.warnings[0] 
        assert warning.msg == "xxx (since version 3.0)"

def test_APIWARN():
    from py.__.misc.warn import APIWARN
    wb = APIWARN.im_self
    assert wb._forward in wb._eventbus._subscribers 
