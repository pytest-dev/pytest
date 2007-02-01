import py
import sys

callcapture = py.io.StdCapture.call

def setup_module(mod): 
    mod.tempdir = py.test.ensuretemp("py.log-test") 
    mod.logstate = py.log._getstate()

def teardown_module(mod): 
    py.log._setstate(mod.logstate) 

class TestLogProducer: 
    def setup_method(self, meth): 
        self.state = py.log._getstate() 

    def teardown_method(self, meth): 
        py.log._setstate(self.state) 

    def test_producer_repr(self): 
        d = py.log.default 
        assert repr(d).find('default') != -1

    def test_produce_one_keyword(self): 
        l = []
        py.log.setconsumer('s1', l.append) 
        py.log.Producer('s1')("hello world") 
        assert len(l) == 1
        msg = l[0]
        assert msg.content().startswith('hello world') 
        assert msg.prefix() == '[s1] ' 
        assert str(msg) == "[s1] hello world"

    def test_producer_class(self): 
        p = py.log.Producer('x1') 
        l = []
        py.log.setconsumer(p.keywords, l.append) 
        p("hello") 
        assert len(l) == 1
        assert len(l[0].keywords) == 1
        assert 'x1' == l[0].keywords[0]

    def test_producer_caching(self):
        p = py.log.Producer('x1')
        x2 = p.x2
        assert x2 is p.x2

class TestLogConsumer: 
    def setup_method(self, meth): 
        self.state = py.log._getstate() 
    def teardown_method(self, meth): 
        py.log._setstate(self.state) 

    def test_log_none(self): 
        log = py.log.Producer("XXX")
        l = []
        py.log.setconsumer('XXX', l.append)
        log("1")
        assert l 
        l[:] = []
        py.log.setconsumer('XXX', None) 
        log("2")
        assert not l 

    def test_log_default_stdout(self):
        res, out, err = callcapture(py.log.default, "hello")
        assert out.strip() == "[default] hello" 

    def test_simple_consumer_match(self): 
        l = []
        py.log.setconsumer("x1", l.append)
        p = py.log.Producer("x1 x2")
        p("hello")
        assert l
        assert l[0].content() == "hello"

    def test_simple_consumer_match_2(self): 
        l = []
        p = py.log.Producer("x1 x2")
        p.set_consumer(l.append) 
        p("42")
        assert l
        assert l[0].content() == "42"

    def test_no_auto_producer(self):
        p = py.log.Producer('x')
        py.test.raises(AttributeError, "p._x") 
        py.test.raises(AttributeError, "p.x_y")

    def test_setconsumer_with_producer(self): 
        l = []
        p = py.log.Producer("hello")
        py.log.setconsumer(p, l.append)
        p("world")
        assert str(l[0]) == "[hello] world"

    def test_multi_consumer(self): 
        l = []
        py.log.setconsumer("x1", l.append)
        py.log.setconsumer("x1 x2", None) 
        p = py.log.Producer("x1 x2")
        p("hello")
        assert not l
        py.log.Producer("x1")("hello")
        assert l
        assert l[0].content() == "hello"

    def test_log_stderr(self):
        py.log.setconsumer("default", py.log.STDERR) 
        res, out, err = callcapture(py.log.default, "hello")
        assert not out
        assert err.strip() == '[default] hello'

    def test_log_file(self):
        custom_log = tempdir.join('log.out')
        py.log.setconsumer("default", open(str(custom_log), 'w', buffering=0))
        py.log.default("hello world #1") 
        assert custom_log.readlines() == ['[default] hello world #1\n']

        py.log.setconsumer("default", py.log.Path(custom_log, buffering=0))
        py.log.default("hello world #2") 
        assert custom_log.readlines() == ['[default] hello world #2\n'] # no append by default!
        
    def test_log_file_append_mode(self):
        logfilefn = tempdir.join('log_append.out')

        # The append mode is on by default, so we don't need to specify it for File
        py.log.setconsumer("default", py.log.Path(logfilefn, append=True, 
                                                    buffering=0))
        assert logfilefn.check()
        py.log.default("hello world #1") 
        lines = logfilefn.readlines() 
        assert lines == ['[default] hello world #1\n']
        py.log.setconsumer("default", py.log.Path(logfilefn, append=True,
                                                    buffering=0))
        py.log.default("hello world #1") 
        lines = logfilefn.readlines() 
        assert lines == ['[default] hello world #1\n', 
                         '[default] hello world #1\n']

    def test_log_file_delayed_create(self):
        logfilefn = tempdir.join('log_create.out')

        py.log.setconsumer("default", py.log.Path(logfilefn,
                                        delayed_create=True, buffering=0))
        assert not logfilefn.check()
        py.log.default("hello world #1") 
        lines = logfilefn.readlines() 
        assert lines == ['[default] hello world #1\n']

    def test_keyword_based_log_files(self):
        logfiles = []
        keywords = 'k1 k2 k3'.split()
        for key in keywords: 
            path = tempdir.join(key)
            py.log.setconsumer(key, py.log.Path(path, buffering=0))
      
        py.log.Producer('k1')('1')
        py.log.Producer('k2')('2')
        py.log.Producer('k3')('3')

        for key in keywords: 
            path = tempdir.join(key)
            assert path.read().strip() == '[%s] %s' % (key, key[-1])

    # disabled for now; the syslog log file can usually be read only by root
    # I manually inspected /var/log/messages and the entries were there
    def no_test_log_syslog(self):
        py.log.setconsumer("default", py.log.Syslog())
        py.log.default("hello world #1") 

    # disabled for now until I figure out how to read entries in the
    # Event Logs on Windows
    # I manually inspected the Application Log and the entries were there
    def no_test_log_winevent(self):
        py.log.setconsumer("default", py.log.WinEvent())
        py.log.default("hello world #1") 

    # disabled for now until I figure out how to properly pass the parameters
    def no_test_log_email(self):
        py.log.setconsumer("default", py.log.Email(mailhost="gheorghiu.net",
                                                   fromaddr="grig",
                                                   toaddrs="grig",
                                                   subject = "py.log email"))
        py.log.default("hello world #1") 
