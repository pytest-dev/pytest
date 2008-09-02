import py
from py.__.test.report.collectonly import CollectonlyReporter
from py.__.test import event
from py.__.test.testing.suptest import InlineCollection, popvalue
from py.__.test.testing.suptest import assert_stringio_contains_lines

class TestCollectonly(InlineCollection):
    def test_collectonly_basic(self):
        modcol = self.getmodulecol(configargs=['--collectonly'], source="""
            def test_func():
                pass
        """)
        stringio = py.std.cStringIO.StringIO()
        rep = CollectonlyReporter(modcol._config, out=stringio)
        indent = rep.indent
        rep.processevent(event.CollectionStart(modcol))
        s = popvalue(stringio)
        assert s == "<Module 'test_TestCollectonly_test_collectonly_basic.py'>"

        item = modcol.join("test_func")
        rep.processevent(event.ItemStart(item))
        s = popvalue(stringio)
        assert s.find("Function 'test_func'") != -1
        rep.processevent(event.CollectionReport(modcol, [], passed=""))
        assert rep.indent == indent 

    def test_collectonly_skipped_module(self):
        modcol = self.getmodulecol(configargs=['--collectonly'], source="""
            import py
            py.test.skip("nomod")
        """, withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = CollectonlyReporter(modcol._config, bus=self.session.bus, out=stringio)
        cols = list(self.session.genitems([modcol]))
        assert len(cols) == 0
        assert_stringio_contains_lines(stringio, """
            <Module 'test_TestCollectonly_test_collectonly_skipped_module.py'>
              !!! Skipped: 'nomod' !!!
        """)

    def test_collectonly_failed_module(self):
        modcol = self.getmodulecol(configargs=['--collectonly'], source="""
            raise ValueError(0)
        """, withsession=True)
        stringio = py.std.cStringIO.StringIO()
        rep = CollectonlyReporter(modcol._config, bus=self.session.bus, out=stringio)
        cols = list(self.session.genitems([modcol]))
        assert len(cols) == 0
        assert_stringio_contains_lines(stringio, """
            <Module 'test_TestCollectonly_test_collectonly_failed_module.py'>
              !!! ValueError: 0 !!!
        """)

