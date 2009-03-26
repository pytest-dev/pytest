import py
from py.__.test import parseopt 

pytest_plugins = 'pytest_iocapture'

class TestParser:
    def test_init(self, stdcapture):
        parser = parseopt.Parser(usage="xyz")
        py.test.raises(SystemExit, 'parser.parse(["-h"])')
        out, err = stdcapture.reset()
        assert out.find("xyz") != -1

    def test_group_add_and_get(self):
        parser = parseopt.Parser()
        group = parser.addgroup("hello", description="desc")
        assert group.name == "hello"
        assert group.description == "desc"
        py.test.raises(ValueError, parser.addgroup, "hello")
        group2 = parser.getgroup("hello")
        assert group2 is group
        py.test.raises(ValueError, parser.getgroup, 'something')

    def test_group_addoption(self):
        group = parseopt.OptionGroup("hello")
        group.addoption("--option1", action="store_true")
        assert len(group.options) == 1
        assert isinstance(group.options[0], py.compat.optparse.Option)

    def test_group_shortopt_lowercase(self):
        parser = parseopt.Parser()
        group = parser.addgroup("hello")
        py.test.raises(ValueError, """
            group.addoption("-x", action="store_true")
        """)
        assert len(group.options) == 0
        group._addoption("-x", action="store_true")
        assert len(group.options) == 1

    def test_parser_addoption(self):
        parser = parseopt.Parser()
        group = parser.getgroup("custom options")
        assert len(group.options) == 0
        group.addoption("--option1", action="store_true")
        assert len(group.options) == 1

    def test_parse(self):
        parser = parseopt.Parser()
        parser.addoption("--hello", dest="hello", action="store")
        option, args = parser.parse(['--hello', 'world'])
        assert option.hello == "world"
        assert not args

    def test_parse(self):
        parser = parseopt.Parser()
        option, args = parser.parse([py.path.local()])
        assert args[0] == py.path.local()

    def test_parse_will_set_default(self):
        parser = parseopt.Parser()
        parser.addoption("--hello", dest="hello", default="x", action="store")
        option, args = parser.parse([])
        assert option.hello == "x"
        del option.hello
        args = parser.parse_setoption([], option)
        assert option.hello == "x"

    def test_parse_setoption(self):
        parser = parseopt.Parser()
        parser.addoption("--hello", dest="hello", action="store")
        parser.addoption("--world", dest="world", default=42)
        class A: pass
        option = A()
        args = parser.parse_setoption(['--hello', 'world'], option)
        assert option.hello == "world"
        assert option.world == 42
        assert not args

    def test_parse_defaultgetter(self):
        def defaultget(option):
            if option.type == "int":
                option.default = 42
            elif option.type == "string":
                option.default = "world"
        parser = parseopt.Parser(processopt=defaultget)
        parser.addoption("--this", dest="this", type="int", action="store")
        parser.addoption("--hello", dest="hello", type="string", action="store")
        parser.addoption("--no", dest="no", action="store_true")
        option, args = parser.parse([])
        assert option.hello == "world"
        assert option.this == 42
