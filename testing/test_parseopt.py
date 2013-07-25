import py, pytest
from _pytest import config as parseopt
from textwrap import dedent

class TestParser:
    def test_no_help_by_default(self, capsys):
        parser = parseopt.Parser(usage="xyz")
        pytest.raises(SystemExit, 'parser.parse(["-h"])')
        out, err = capsys.readouterr()
        assert err.find("error: unrecognized arguments") != -1

    def test_argument(self):
        with pytest.raises(parseopt.ArgumentError):
            # need a short or long option
            argument = parseopt.Argument()
        argument = parseopt.Argument('-t')
        assert argument._short_opts == ['-t']
        assert argument._long_opts == []
        assert argument.dest == 't'
        argument = parseopt.Argument('-t', '--test')
        assert argument._short_opts == ['-t']
        assert argument._long_opts == ['--test']
        assert argument.dest == 'test'
        argument = parseopt.Argument('-t', '--test', dest='abc')
        assert argument.dest == 'abc'

    def test_argument_type(self):
        argument = parseopt.Argument('-t', dest='abc', type='int')
        assert argument.type is int
        argument = parseopt.Argument('-t', dest='abc', type='string')
        assert argument.type is str
        argument = parseopt.Argument('-t', dest='abc', type=float)
        assert argument.type is float
        with pytest.raises(KeyError):
            argument = parseopt.Argument('-t', dest='abc', type='choice')
        argument = parseopt.Argument('-t', dest='abc', type='choice',
                                     choices=['red', 'blue'])
        assert argument.type is str

    def test_argument_processopt(self):
        argument = parseopt.Argument('-t', type=int)
        argument.default = 42
        argument.dest = 'abc'
        res = argument.attrs()
        assert res['default'] == 42
        assert res['dest'] == 'abc'
                    
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
        assert isinstance(group.options[0], parseopt.Argument)

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
        args = parser.parse(['--hello', 'world'])
        assert args.hello == "world"
        assert not getattr(args, parseopt.Config._file_or_dir)

    def test_parse2(self):
        parser = parseopt.Parser()
        args = parser.parse([py.path.local()])
        assert getattr(args, parseopt.Config._file_or_dir)[0] == py.path.local()

    def test_parse_will_set_default(self):
        parser = parseopt.Parser()
        parser.addoption("--hello", dest="hello", default="x", action="store")
        option = parser.parse([])
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

    def test_parse_special_destination(self):
        parser = parseopt.Parser()
        x = parser.addoption("--ultimate-answer", type=int)
        args = parser.parse(['--ultimate-answer', '42'])
        assert args.ultimate_answer == 42
        
    def test_parse_defaultgetter(self):
        def defaultget(option):
            if not hasattr(option, 'type'):
                return
            if option.type is int:
                option.default = 42
            elif option.type is str:
                option.default = "world"
        parser = parseopt.Parser(processopt=defaultget)
        parser.addoption("--this", dest="this", type="int", action="store")
        parser.addoption("--hello", dest="hello", type="string", action="store")
        parser.addoption("--no", dest="no", action="store_true")
        option = parser.parse([])
        assert option.hello == "world"
        assert option.this == 42
        assert option.no is False

@pytest.mark.skipif("sys.version_info < (2,5)")
def test_addoption_parser_epilog(testdir):
    testdir.makeconftest("""
        def pytest_addoption(parser):
            parser.hints.append("hello world")
            parser.hints.append("from me too")
    """)
    result = testdir.runpytest('--help')
    #assert result.ret != 0
    result.stdout.fnmatch_lines(["hint: hello world", "hint: from me too"])

