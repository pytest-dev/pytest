from _pytest._io.pprint import PrettyPrinter


def test_pformat_dispatch():
    printer = PrettyPrinter(width=5)
    assert printer.pformat("a") == "'a'"
    assert printer.pformat("a" * 10) == "'aaaaaaaaaa'"
    assert printer.pformat("foo bar") == "('foo '\n 'bar')"
