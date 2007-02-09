
""" webtest
"""

import py

try:
    from pypy.translator.js.main import rpython2javascript
    from pypy.translator.js import commproxy
    
    commproxy.USE_MOCHIKIT = False
except ImportError:
    py.test.skip("PyPy not found")

def setup_module(mod):
    from py.__.test.rsession.web import TestHandler as _TestHandler
    from py.__.test.rsession.web import MultiQueue
    mod._TestHandler = _TestHandler
    mod.MultiQueue = MultiQueue

def test_js_generate():
    from py.__.test.rsession import webjs
    from py.__.test.rsession.web import FUNCTION_LIST, IMPORTED_PYPY
    
    source = rpython2javascript(webjs, FUNCTION_LIST)
    assert source

def test_parse_args():
    class TestTestHandler(_TestHandler):
        def __init__(self):
            pass
    h = TestTestHandler()
    assert h.parse_args('foo=bar') == {'foo': 'bar'}
    assert h.parse_args('foo=bar%20baz') == {'foo': 'bar baz'}
    assert h.parse_args('foo%20bar=baz') == {'foo bar': 'baz'}
    assert h.parse_args('foo=bar%baz') == {'foo': 'bar\xbaz'}
    py.test.raises(ValueError, 'h.parse_args("foo")')

class TestMultiQueue(object):
    def test_get_one_sessid(self):
        mq = MultiQueue()
        mq.put(1)
        result = mq.get(1234)
        assert result == 1

    def test_get_two_sessid(self):
        mq = MultiQueue()
        mq.put(1)
        result = mq.get(1234)
        assert result == 1
        mq.put(2)
        result = mq.get(1234)
        assert result == 2
        result = mq.get(5678)
        assert result == 1
        result = mq.get(5678)
        assert result == 2

    def test_get_blocking(self):
        import thread
        result = []
        def getitem(mq, sessid):
            result.append(mq.get(sessid))
        mq = MultiQueue()
        thread.start_new_thread(getitem, (mq, 1234))
        assert not result
        mq.put(1)
        py.std.time.sleep(0.1)
        assert result == [1]

    def test_empty(self):
        mq = MultiQueue()
        assert mq.empty()
        mq.put(1)
        assert not mq.empty()
        result = mq.get(1234)
        result == 1
        assert mq.empty()
        mq.put(2)
        result = mq.get(4567)
        assert result == 1
        result = mq.get(1234)
        assert result == 2
        assert not mq.empty()
        result = mq.get(4567)
        assert result == 2
        assert mq.empty()

