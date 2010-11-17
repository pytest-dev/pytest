import py, pytest
from _pytest import config as parseopt
from textwrap import dedent

class TestParser:
    def test_no_help_by_default(self, capsys):
        parser = parseopt.Parser(usage="xyz")
        pytest.raises(SystemExit, 'parser.parse(["-h"])')
        out, err = capsys.readouterr()
        assert err.find("no such option") != -1

    def test_group_add_and_get(self):
        parser = parseopt.Parser()
        group = parser.getgroup("hello", description="desc")
        assert group.name == "hello"
        assert group.description == "desc"

    def test_getgroup_simple(self):
        parser = parseopt.Parser()
        group = parser.getgroup("hello", description="desc")
        assert group.name == "hello"
        assert group.description == "desc"
        group2 = parser.getgroup("hello")
        assert group2 is group

    def test_group_ordering(self):
        parser = parseopt.Parser()
        group0 = parser.getgroup("1")
        group1 = parser.getgroup("2")
        group1 = parser.getgroup("3", after="1")
        groups = parser._groups
        groups_names = [x.name for x in groups]
        assert groups_names == list("132")

    def test_group_addoption(self):
        group = parseopt.OptionGroup("hello")
        group.addoption("--option1", action="store_true")
        assert len(group.options) == 1
        assert isinstance(group.options[0], py.std.optparse.Option)

    def test_group_shortopt_lowercase(self):
        parser = parseopt.Parser()
        group = parser.getgroup("hello")
        pytest.raises(ValueError, """
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


@pytest.mark.skipif("sys.version_info < (2,5)")
def test_addoption_parser_epilog(testdir):
    testdir.makeconftest("""
        def pytest_addoption(parser):
            parser.hints.append("hello world")
    """)
    result = testdir.runpytest('--help')
    #assert result.ret != 0
    result.stdout.fnmatch_lines(["*hint: hello world*"])

