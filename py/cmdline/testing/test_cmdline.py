from py.__.test.testing import suptest
from py.__.test.testing.acceptance_test import AcceptBase

class TestPyLookup(AcceptBase):
    def test_basic(self):
        p = self.makepyfile(hello="def x(): pass")
        result = self.runpybin("py.lookup", "pass")
        suptest.assert_lines_contain_lines(result.outlines, 
            ['%s:*def x(): pass' %(p.basename)]
        )

    def test_search_in_filename(self):
        p = self.makepyfile(hello="def x(): pass")
        result = self.runpybin("py.lookup", "hello")
        suptest.assert_lines_contain_lines(result.outlines, 
            ['*%s:*' %(p.basename)]
        )
        
